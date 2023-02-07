#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
# Disable many annoying pylint messages, warning me about variable naming for example.
# yes, in my Solr code I'm caught between two worlds of snake_case and camelCase.

""" 
OPAS - opasBiblioSupport

Support for information contained in references in bibliographies.

Module Assumptions:

   BibEntry class is general to accommodate be, maybe binc (TBD)

   During a compile to EXP_ARCH files from KBD files:
      - we want to do the minimum for speed.
      - we need to check if the DB has an overriding locator
      - we need to check to ensure all locator's (rx) exist
   
   During a "load" from EXP_ARCH compiled files:
      - we want to do the minimum for speed.
      - we need to check if the DB has an overriding locator
      - we need to check to ensure all locator's (rx) exist

"""
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2022, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"

import sys
sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')

import os
from datetime import datetime
import string
import re
import statistics
from typing import List, Generic, TypeVar, Optional
import models

import lxml
from lxml import etree
import roman
import jellyfish

import logging
logger = logging.getLogger(__name__)
from loggingDebugStream import log_everywhere_if    # log as usual, but if first arg is true, also put to stdout for watching what's happening

gDbg2 = True
gDbg3 = True

parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=False)

from pydantic import BaseModel, Field # removed Field, causing an error on AWS

#import localsecrets
import opasConfig
import opasGenSupportLib as opasgenlib
import opasXMLHelper as opasxmllib
import opasCentralDBLib
ocd = opasCentralDBLib.opasCentralDB()

import opasPySolrLib

# import opasLocator
# import opasArticleIDSupport
# import modelsOpasCentralPydantic
from opasLocator import Locator
from opasLocalID import LocalID

# new for processing code
import PEPJournalData
jrnlData = PEPJournalData.PEPJournalData()
import PEPBookInfo
known_books = PEPBookInfo.PEPBookInfo()
from PEPReferenceParserStr import StrReferenceParser
SPECIAL_BOOK_NAMES = ("Ges. Schr.", )

#------------------------------------------------------------------------------------------------------------
#  Support functions
#------------------------------------------------------------------------------------------------------------

#------------------------------------------------------------------------------------------------------
def get_reference_correction(ocd, article_id, ref_local_id=None, verbose=None):
    """
    Temporary:
       Return a single reference from the opasloader_refcorrections table in opascentral
    
    TBD: This is an old table we used instead of editing all the old XML files to add in
         markup on non-PEP references.  These references should at some point
         be merged with the xml files and deprecating the table.
    
    >>> import opasCentralDBLib
    >>> ocd = opasCentralDBLib.opasCentralDB()  
    >>> corrected_bibentry = get_reference_correction(ocd, 'CPS.031.0617A', 'B0021')
    >>> corrected_bibentry.ref_xml[:120]
    '<be id = "B021"><a><l>Freud</l>, A.</a> <y>1936</y> <bst>The ego and the mechanisms of defense</bst> New York: <bp>Inter'
    """
    
    # The local_ids in the the correction table and the xml are 4 digits, rather than 3, which is what the biblioxml table has.
    local_id = LocalID(ref_local_id)
    ref_local_id = local_id.localIDStr
    
    ret_val = None
        
    select = f"""SELECT * from opasloader_refcorrections
                 WHERE art_id = '{article_id}'
                 and ref_local_id = '{ref_local_id}'
                 """

    results = ocd.get_select_as_list_of_models(select, model=models.Biblioxml)
    
    if results:
        ret_val = results[0]
    
    # return a single model (record) or None if not in the table
    return ret_val  # return True for success

#------------------------------------------------------------------------------------------------------
def check_for_known_books(ref_text):
    ret_val = known_books.getPEPBookCodeStr(ref_text)
    if ret_val[0] is not None:
        ret_val[2] = "pattern"

    return ret_val

#------------------------------------------------------------------------------------------------------
def check_for_vol_suffix(ocd, loc_str, verbose):
    ret_val = None
    newloc = Locator(loc_str)
    if newloc.validate():
        if newloc.jrnlVol[-1].isnumeric():
            newloc.jrnlVol.volSuffix = "%"
            new_loc_str = newloc.articleID()
            new_locs = ocd.article_exists(new_loc_str)
            if len(new_locs) == 1:
                ret_val = new_locs[0][0]
                log_everywhere_if(verbose, level="info", msg=f"\t\tCorrecting Bib ID with vol variant: {ret_val}.")

    return ret_val    

#------------------------------------------------------------------------------------------------------
def check_for_page_start(ocd, loc_str, page_offset=-1, verbose=False):
    ret_val = None
    newloc = Locator(loc_str)
    if newloc.validate():
        try:
            newloc.pgStart += page_offset
        except Exception as e:
            log_everywhere_if(verbose, "info", f"Bad locator {loc_str}")
        else:
            if newloc.isValid():
                new_loc_str = newloc.articleID()
                new_locs = ocd.article_exists(new_loc_str)
                if len(new_locs) == 1:
                    ret_val = new_locs[0][0]
                    log_everywhere_if(verbose, level="info", msg=f"\t\tCorrecting Bib ID with page-1: {ret_val}.")
                #else:
                    #log_everywhere_if(verbose, "warning", f"Bad locator in reference {loc_str}->{new_loc_str}(article doesn't exist)")
    return ret_val    

#------------------------------------------------------------------------------------------------------
def strip_extra_spaces(textstr:str):
    if textstr is not None:
        ret_val = textstr.strip()
        ret_val = re.sub(" +", " ", ret_val)
    else:
        ret_val = None

    return ret_val

#------------------------------------------------------------------------------------------------------
# BiblioMatch Class
#------------------------------------------------------------------------------------------------------
class BiblioMatch(object):
    ref_rx: str = Field(None)
    ref_rx_confidence: float = Field(0, title="Confidence level of assigned rx. Manual QA = 1, code parsed = .99, Heuristic = .1 to .97")
    ref_rxcf: str = Field(None, title="List of possible article ID codes for this reference")
    ref_rxcf_confidence: float = Field(0, title="Max confidence level of rxcf codes")
    ref_xml: str = Field(None)
    ref_exists: bool = Field(False, title="Indicates this ref link has been verified")
    link_source: str = Field(None, title="Source of rx link, 'xml', 'database', or 'pattern'")
    link_updated: bool = Field(False, title="Indicates whether the data was corrected during load. If so, may need to update DB.  See link_source for method")
    record_updated: bool = Field(False, title="Indicates whether the data was corrected during load. If so, may need to update DB.")
    last_update: datetime = Field(None)
    
    def __init__(self, bib_entry=None, verbose=False):
        if bib_entry:
            self.__dict__ = bib_entry.__dict__.copy()    # just a shallow copy

    def __str__(self):
        #return f"{self.ref_rx}, {self.ref_rx_confidence}, {self.link_updated}, '{self.ref_rxcf}', {self.ref_rxcf_confidence}"
        return str(self.__dict__)
    
    def __repr__(self):
        # return f"{self.ref_rx}, {self.ref_rx_confidence}, {self.link_updated}, '{self.ref_rxcf}', {self.ref_rxcf_confidence}"
        return str(self.__dict__)
        #return self.ref_rx, self.ref_rx_confidence, self.link_updated, self.ref_rxcf, self.ref_rxcf_confidence
        

#------------------------------------------------------------------------------------------------------------
#  BiblioEntry Class
#------------------------------------------------------------------------------------------------------------
class BiblioEntry(object):
    """
    An entry from a documents bibliography.
    
    Used to populate the MySQL table api_biblioxml for statistical gathering
       and the Solr core pepwebrefs for searching in special cases.
       
    >>> import opasCentralDBLib
    >>> ocd = opasCentralDBLib.opasCentralDB()  
   
    >>> be_journal = BiblioEntry(art_id="CPS.031.0617A", ref_or_parsed_ref='<be lang="en" id="B024">Freud, S. 1905 On psychotherapy Standard Edition 7</be>')
    >>> be_journal.ref_rx

    >>> be_journal = BiblioEntry(art_id="CPS.031.0617A", ref_or_parsed_ref='<be lang="en" id="B054">Klein, M. 1946 Notes on some schizoid mechanisms In:The writings of Melanie Klein Ed. R.E. Money-Kyrle et al. London: Hogarth Press, 1975</be>')
    >>> be_journal.ref_rx
    
    
    >>> check_for_page_start(ocd, "AIM.014.0194A", page_offset=-1)
    'AIM.014.0193A'
    
    >>> check_for_page_start(ocd, "AIM.014.0192A", page_offset=1)
    'AIM.014.0193A'
    
    #Bad reference
    >>> be_journal = BiblioEntry(art_id="JICAP.019.0358A", ref_or_parsed_ref='<be id="B0036" reftype="journal" class="mixed-citation"><a><l>Ramires</l>, V. R. R.</a>, <a><l>Godinho</l>, L. R.</a>, &amp; <a> <l>Goodman</l>, G.</a> (<y>2017</y>). <t class="article-title">The therapeutic process of a child diagnosed with disruptive mood dysregulation disorder</t>. <j>Psychoanalytic Psychology</j>, <v> 34</v>(<bs>4</bs>), <pp>pap0000134</pp>. <webx type="url" url="https://doi.org/10.1037/pap0000134">https://doi.org/10.1037/pap0000134</webx></be>')
    >>> be_journal.ref_rx
    'PPSY.034.0134A'
        
    """
    # Transitional, until I change this class to the model
    art_id: str = Field(None)
    ref_local_id: str = Field(None)
    art_year: int = Field(0)              # containing article year
    ref_rx: str = Field(None)
    ref_rx_confidence: float = Field(0)
    ref_rxp: str = Field(None, title="Previous system method to correct rx value without overwriting.  Will now use to figure correct rx")
    ref_rxp_confidence: float = Field(0, title="rxp confidence value")
    ref_rxcf: str = Field(None, title="list of possible related references, with confidence appended to each via :")
    ref_rxcf_confidence: float = Field(0, title="maximum rxcf confidence value from list")
    ref_sourcecode: str = None
    ref_authors: str = Field(None)
    ref_authors_xml: str = Field(None)
    ref_articletitle: str = Field(None)
    ref_text: str = Field(None)
    ref_sourcetype: str = Field(None)
    ref_is_book: bool = Field(False)
    ref_sourcetitle: str = Field(None)
    ref_authors_xml: str = Field(None)
    ref_xml: str = Field(None)
    ref_pgrg: str = Field("")
    ref_pgstart: str = Field("")
    ref_doi: Optional[str]
    ref_title: str = Field(None)
    ref_year: str = Field(None)
    ref_year_int: Optional[int]
    ref_volume: str = Field(None)
    ref_volume_int: Optional[int]
    ref_volume_isroman: bool = Field(False, title="True if bib_volume is roman")
    ref_publisher: str = Field(None)
    ref_in_pep: bool = Field(False, title="Indicates this is a PEP reference")
    ref_exists: bool = Field(False, title="Indicates this ref link has been verified")
    link_source: str = Field(None, title="Source of rx link, 'xml', 'database', or 'pattern'")
    link_updated: bool = Field(False, title="Indicates whether the data was corrected during load. If so, may need to update DB.")
    record_updated: bool = Field(False, title="Indicates whether the data was corrected during load. If so, may need to update DB.")
    parsed_ref:etree = Field(None)
    last_update: datetime = Field(None)
    
    def __init__(self, art_id, art_year=None, ref_or_parsed_ref=None, db_bib_entry=None, verbose=False):
        self.link_source = None
        self.link_updated = False
        self.ref_in_pep = False
        self.ref_pgstart = ""
        self.ref_pgrg = ""
        self.ref_exists = False

        # allow either string xml ref or parsed ref
        if ref_or_parsed_ref is None and not db_bib_entry:
            raise ValueError("You must provide a ref or parsed ref")
        elif db_bib_entry:
            self.__dict__ = db_bib_entry.__dict__.copy()    # just a shallow copy
            ref_or_parsed_ref = self.ref_xml

        if isinstance(ref_or_parsed_ref, str):
            parsed_ref = etree.fromstring(ref_or_parsed_ref, parser=parser)
            ref_entry_xml = ref_or_parsed_ref
            self.ref_xml = ref_entry_xml
        elif isinstance(ref_or_parsed_ref, object):
            parsed_ref = ref_or_parsed_ref
            ref_entry_xml = etree.tostring(parsed_ref, with_tail=False)
            ref_entry_xml = ref_entry_xml.decode("utf8") # convert from bytes
            self.ref_xml = ref_entry_xml
        else:
            raise TypeError("arg must be str or etree")
           
        self.art_id = art_id
        self.ref_local_id = opasxmllib.xml_get_element_attr(parsed_ref, "id")
        self.ref_id = art_id + "." + self.ref_local_id
        
        # see if the xml for this has been replaced.
        ref_corrected_entry = get_reference_correction(ocd, art_id, self.ref_local_id)
        if ref_corrected_entry:
            self.ref_text = ref_corrected_entry.ref_text
            self.ref_xml = ref_corrected_entry.ref_xml
            parsed_ref = etree.fromstring(ref_corrected_entry.ref_xml, parser=parser)
            self.record_updated = True
        else:
            self.record_updated = False
            
        self.parsed_ref = parsed_ref
        self.ref_xml = re.sub(" +", " ", self.ref_xml)
        self.art_year = art_year
        if art_year is not None:
            try:
                self.art_year_int = int(art_year)
            except Exception as e:
                self.art_year_int = 0

        ref_text = opasxmllib.xml_elem_or_str_to_text(self.parsed_ref)
        ref_text = strip_extra_spaces(ref_text)
        self.ref_text = ref_text
        
        if not db_bib_entry:
            self.last_update = datetime.today()
            self.ref_rx = opasxmllib.xml_get_element_attr(self.parsed_ref, "rx", default_return=None)
            self.ref_rx_confidence = 0
            self.ref_rxcf = opasxmllib.xml_get_element_attr(self.parsed_ref, "rxcf", default_return=None) # related rx
            self.ref_rxcf_confidence = 0
        else:
            self.last_update = db_bib_entry.last_update 
            self.ref_rxp = None
            self.ref_rxp_confidence = 0
            self.ref_rx = db_bib_entry.ref_rx
            self.ref_rx_confidence = db_bib_entry.ref_rx_confidence
            self.ref_rxcf = db_bib_entry.ref_rxcf
            self.ref_rxcf_confidence = db_bib_entry.ref_rxcf_confidence          
            
        self.ref_rxp = opasxmllib.xml_get_element_attr(self.parsed_ref, "rxp", default_return=None)
        self.ref_rxp_confidence = opasxmllib.xml_get_element_attr(self.parsed_ref, "rxps", default_return=None)
        if self.ref_rxp and not self.ref_rx:
            self.ref_rx = self.ref_rxp
            self.ref_rxcf_confidence = self.ref_rxp_confidence
            self.ref_rxp = None
            self.ref_rxp_confidence = None
            self.link_updated = True
            self.ref_in_pep = True
        
        self.ref_pgrg = opasxmllib.xml_get_subelement_textsingleton(self.parsed_ref, "pp")
        self.ref_pgrg = opasgenlib.first_item_grabber(self.ref_pgrg, re_separator_ptn=";|,", def_return=self.ref_pgrg)
        self.ref_pgrg = opasgenlib.trimLeadingNonDigits(self.ref_pgrg)
        self.ref_pgrg = self.ref_pgrg[:23]
        
        if self.ref_pgrg:
            # try to find it in reference text?
            pass
        
        self.ref_sourcecode = ""
        self.ref_sourcetype = ""
        self.ref_is_book = False
        # self.art_year = 0 # artInfo.art_year_int
        
        if self.ref_rx is not None:
            self.ref_rx_sourcecode = re.search("(.*?)\.", self.ref_rx, re.IGNORECASE).group(1)
        else:
            self.ref_rx_sourcecode = None

        self.ref_volume = opasxmllib.xml_get_subelement_textsingleton(self.parsed_ref, "v")
        self.ref_volume = self.ref_volume[:23]
        if self.ref_volume:
            self.ref_volume_isroman = opasgenlib.is_roman_str(self.ref_volume.upper())
            if self.ref_volume_isroman:
                try:
                    self.ref_volume_int = roman.fromRoman(self.ref_volume.upper()) # use roman lib which generates needed exception
                except Exception as e:
                    self.ref_volume_isroman = False
                    try:
                        self.ref_volume_int = int(self.ref_volume)
                    except Exception as e:
                        log_everywhere_if(True, "warning", msg=f"BibEntry vol {self.ref_volume} is neither roman nor int {e}")
                        self.volume_int = 0
            else:
                if self.ref_volume.isnumeric():
                    self.ref_volume_int = int(self.ref_volume)
                else:
                    self.ref_volume_int = 0
        else:
            self.ref_volume_int = 0
            self.ref_volume_isroman = False

        self.ref_publisher = opasxmllib.xml_get_subelement_textsingleton(self.parsed_ref, "bp")
        self.ref_publisher = self.ref_publisher[:254]
        journal_title = opasxmllib.xml_get_subelement_textsingleton(self.parsed_ref, "j")
        book_title = opasxmllib.xml_get_subelement_textsingleton(self.parsed_ref, "bst")
        self.ref_sourcetitle = None
        # worth the check here for books since not all books are tagged.
        book_markup = self.parsed_ref.xpath("//bst|bp|bsy|bpd")
        journal = self.parsed_ref.xpath("//j")

        # special book handling
        if journal_title in SPECIAL_BOOK_NAMES:
            book_title = journal_title
            journal_title = None
            # set below since now we have book_title and not journal title
            #self.ref_is_book = True
            #self.ref_sourcetype = "book"

        if (book_markup or book_title or self.ref_publisher) and not journal_title:
            self.ref_is_book = True
            self.ref_sourcetype = "book"
            self.sourcetitle = book_title  # book title
        elif journal_title or journal:
            self.ref_sourcetype = "journal"
            self.ref_is_book = False
            self.ref_sourcetitle = journal_title
        else:
            self.ref_sourcetype = "unknown"
            self.ref_is_book = False
            self.ref_sourcetitle = f"{journal_title} / {book_title}"

        # see if we have info to link SE/GW etc., these are in a sense like journals
        if opasgenlib.is_empty(self.ref_sourcecode):
            if PEPJournalData.PEPJournalData.rgxSEPat2.search(self.ref_text):
                self.ref_in_pep = True
                self.ref_sourcecode = "SE"
                self.ref_is_book = True
            elif PEPJournalData.PEPJournalData.rgxGWPat2.search(self.ref_text):
                self.ref_in_pep = True
                self.ref_sourcecode = "GW"
                self.ref_is_book = True
        
        if self.ref_is_book:
            year_of_publication = opasxmllib.xml_get_subelement_textsingleton(self.parsed_ref, "bpd")
            if year_of_publication == "":
                year = opasxmllib.xml_get_subelement_textsingleton(self.parsed_ref, "y")
                year_of_publication = opasgenlib.remove_all_punct(year) # punct_set=[',', '.', ':', ';', '(', ')', '\t', r'/', '"', "'", "[", "]"])
            if self.ref_sourcetitle is None or self.ref_sourcetitle == "":
                ## sometimes has markup
                self.ref_sourcetitle = book_title  # book title (bst)
        else:
            year_of_publication = opasxmllib.xml_get_subelement_textsingleton(self.parsed_ref, "y")
            sourcecode, dummy, dummy = jrnlData.getPEPJournalCode(self.ref_sourcetitle)
            if sourcecode is not None:
                self.ref_sourcecode = sourcecode
                #if rx_sourcecode is None and self.ref_sourcecode is not None:
                    #rx_sourcecode = self.ref_sourcecode
                #if rx_sourcecode != self.ref_sourcecode:
                    #logger.warning(f"Parsed title source code {self.ref_sourcetitle} does not match rx_sourcecode {self.ref_sourcecode}")
                
        if year_of_publication != "":
            # make sure it's not a range or list of some sort.  Grab first year
            year_of_publication = opasgenlib.year_grabber(year_of_publication)
        else:
            # try to match
            try:
                m = re.search(r"\(([A-z]*\s*,?\s*)?([12][0-9]{3,3}[abc]?)\)", self.ref_xml)
                if m is not None:
                    year_of_publication = m.group(2)
            except Exception as e:
                logger.warning("no match %s/%s/%s" % (year_of_publication, self.parsed_ref, e))
            
        if year_of_publication != "" and year_of_publication is not None:
            year_of_publication = re.sub("[^0-9]", "", year_of_publication)

        self.ref_year = year_of_publication
        if self.ref_year != "" and self.ref_year is not None:
            try:
                self.ref_year_int = int(self.ref_year[0:4])
            except ValueError as e:
                logger.error("Error converting year_of_publication to int: %s / %s.  (%s)" % (self.ref_year, self.ref_xml, e))
            except Exception as e:
                logger.error("Error trying to find untagged bib year in %s (%s)" % (self.ref_xml, e))
                
        else:
            self.ref_year_int = 0
            
        ref_title = opasxmllib.xml_get_subelement_textsingleton(self.parsed_ref, "t")
        if ref_title:
            ref_title = strip_extra_spaces(ref_title)
            ref_title = ref_title[:1023]
            self.ref_title = ref_title
        else:
            # if it's PEP reference, try harder using a string parse to get the title and link
            # otherwise, wait for it to be updated by opasDataLinker.
            if self.ref_in_pep:
                parsed_str = StrReferenceParser()
                ref_rx = parsed_str.parse_str(self.ref_text)
                if ref_rx:
                    if self.ref_rx is None:
                        self.ref_rx = ref_rx
                    if parsed_str.bib_authors:
                        ref_title = self.ref_text.replace(parsed_str.bib_authors, "")
                    if parsed_str.bib_volume:
                        ref_title = ref_title.replace(str(parsed_str.bib_volume), "")
                    if parsed_str.bib_year:
                        ref_title = ref_title.replace(str(parsed_str.bib_year), "")
                    if parsed_str.bib_sourcetitle:
                        ref_title = ref_title.replace(str(parsed_str.bib_sourcetitle), "")
                    ref_title = ref_title.strip()
                    self.ref_title = ref_title
                else:
                    self.ref_title = ""
            else:
                self.ref_title = ""
        
        author_name_list = [etree.tostring(x, with_tail=False).decode("utf8") for x in self.parsed_ref.findall("a") if x is not None]
        self.ref_authors_xml = '; '.join(author_name_list)
        self.ref_authors_xml = self.ref_authors_xml[:2040]
        author_list = [opasxmllib.xml_elem_or_str_to_text(x) for x in self.parsed_ref.findall("a") if opasxmllib.xml_elem_or_str_to_text(x) is not None]  # final if x gets rid of any None entries which can rarely occur.
        self.ref_authors = '; '.join(author_list)
        self.ref_authors = self.ref_authors[:2040]
        self.ref_doi = self.parsed_ref.findtext("webx[@type='doi']")

        # self.ref = models.Biblioxml(art_id = art_id,
                                    #ref_local_id = self.ref_local_id, 
                                    #art_year = self.ref_year_int, 
                                    #ref_rx = self.ref_rx, 
                                    #ref_rx_confidence = self.ref_rx_confidence, 
                                    #ref_rxcf = self.ref_rxcf, 
                                    #ref_rxcf_confidence = self.ref_rxcf_confidence, 
                                    #ref_sourcecode = self.ref_sourcecode, 
                                    #ref_authors = self.ref_authors, 
                                    #ref_articletitle = self.ref_title, 
                                    #title = self.ref_title, 
                                    #ref_text = self.ref_text, 
                                    #ref_sourcetype = self.ref_sourcetype, 
                                    #ref_sourcetitle = self.ref_sourcetitle, 
                                    #ref_authors_xml = self.ref_authors_xml, 
                                    #ref_xml = self.ref_xml, 
                                    #ref_pgrg = self.ref_pgrg, 
                                    #doi = self.ref_doi, 
                                    #ref_year = self.ref_year, 
                                    #ref_year_int = self.ref_year_int, 
                                    #ref_volume = self.ref_volume,
                                    #ref_volume_int = self.ref_volume_int,
                                    #ref_volume_isroman=self.ref_volume_isroman, 
                                    #ref_publisher = self.ref_publisher, 
                                    #last_update = self.last_update                               
                                    #)
        try:
            self.identify_nonheuristic(verbose=verbose)
        except:
            log_everywhere_if(verbose, "debug", f"Biblio Entry ID issues {art_id, self.ref_local_id}")
        else:
            if gDbg2:
                log_everywhere_if(self.ref_rx, "debug", f"\t\t...BibEntry linked to {self.ref_rx} loaded")

    #------------------------------------------------------------------------------------------------------------
    def update_bib_entry(self, bib_match, verbose=False):
        if bib_match:
            self.__dict__ = bib_match.__dict__.copy()    # just a shallow copy
    #------------------------------------------------------------------------------------------------------------
    def update_db_links(self, art_id, local_id, verbose=False):
        """
        
        """
        ret_val = False
        caller_name = "update_biblioxml_record"
        msg = f"\t...Updating biblio record to add rx and rx_confidence."
        log_everywhere_if(verbose, "info", msg)
        
        if self.link_updated:
            if self.record_updated is not None:
                sqlcpy = f"""
                            UPDATE api_biblioxml
                                SET ref_xml = %s,
                                    ref_rx = %s,
                                    ref_rx_confidence = %s,
                                    ref_rxcf = %s,
                                    ref_rxcf_confidence = %s
                                    ref_link_source = %s
                                WHERE art_id = %s
                                AND ref_local_id = %s
                          """
                
                query_params = (self.ref_xml, 
                                self.ref_rx,
                                self.ref_rx_confidence,
                                self.ref_rxcf,
                                self.ref_rxcf_confidence,
                                self.link_source, 
                                art_id,
                                local_id)
            elif self.ref_rx is not None and self.ref_rxcf is not None:
                sqlcpy = f"""
                            UPDATE api_biblioxml
                                SET ref_rx = %s,
                                    ref_rx_confidence = %s,
                                    ref_rxcf = %s,
                                    ref_rxcf_confidence = %s
                                    ref_link_source = %s
                                WHERE art_id = %s
                                AND ref_local_id = %s
                          """
                
                query_params = (self.ref_rx,
                                self.ref_rx_confidence,
                                self.ref_rxcf,
                                self.ref_rxcf_confidence,
                                self.link_source, 
                                art_id,
                                local_id)
            elif self.ref_rx is not None:
                sqlcpy = f"""
                            UPDATE api_biblioxml
                                SET ref_rx = %s,
                                    ref_rx_confidence = %s,
                                    ref_link_source = %s
                                WHERE art_id = %s
                                AND ref_local_id = %s
                          """
                
                query_params = (self.ref_rx,
                                self.ref_rx_confidence,
                                self.link_source, 
                                art_id,
                                local_id)
                
            elif self.ref_rxcf is not None:
                sqlcpy = f"""
                            UPDATE api_biblioxml
                                SET ref_rxcf = %s,
                                    ref_rxcf_confidence = %s,
                                    ref_link_source = %s
                                WHERE art_id = %s
                                AND ref_local_id = %s
                          """
                query_params = (self.ref_rxcf,
                                self.ref_rxcf_confidence,
                                self.link_source, 
                                art_id,
                                local_id)
            else:
                sqlcpy = None
                
            if sqlcpy is not None:
                try:
                    # commit automatically handled by do_action_query
                    res = ocd.do_action_query(querytxt=sqlcpy, queryparams=query_params)
                except Exception as e:
                    errStr = f"{caller_name}: update error {e}"
                    logger.error(errStr)
                    if opasConfig.LOCAL_TRACE: print (errStr)
                else:
                    ret_val = True
            else:
                ret_val = False
        
        return ret_val

    #------------------------------------------------------------------------------------------------------------
    def identify_nonheuristic(self, pretty_print=False, verbose=False):
        """
          (Heuristic Search is now a separate process to optimize speed.)
          
          returns ref_rx, ref_rxconfidence, link_updated
          
          >>> import opasCentralDBLib
          >>> ocd = opasCentralDBLib.opasCentralDB()  

          >>> ref = '<be id="B0006" reftype="journal" class="mixed-citation"><a class="western"><l>Beebe</l>, B.</a>, &amp; <a class="western"> <l>Lachmann</l>, F.</a> (<y>2002</y>). <t class="article-title">Organizing principles of interaction from infant research and the lifespan prediction of attachment: Application to adult treatment</t>. <j>Journal of Infant, Child, and Adolescent Psychotherapy</j>, <v> 2</v>(<bs>4</bs>), <pp>61 - 89</pp>&#8211;. doi:<webx type="doi">10.1080/15289168.2002.10486420</webx></be>'
          >>> parsed_ref = etree.fromstring(ref, parser=parser)
          >>> be_journal = BiblioEntry(art_id="FA.013A.0120A", ref_or_parsed_ref=parsed_ref)
          >>> be_journal.ref_rx, be_journal.ref_rx_confidence, be_journal.link_source
          ('JICAP.002D.0061A', 0.91, 'variation')
          >>> # reset them if in database or pattern per above
          >>> be_journal.ref_rx = None
          >>> be_journal.ref_rx_confidence = 0
          >>> be_journal.identify_nonheuristic(ocd)
          {'ref_rx': 'JICAP.002D.0061A', 'ref_rx_confidence': 0.91, 'link_updated': True, 'link_source': 'variation', 'ref_rxcf': None, 'ref_rxcf_confidence': 0}

          >>> ref = '<be id="B070"><a><l>Money-Kyrle</l>, R.</a> (<y>1968</y>). <t>Cognitive development.</t> <j>The International Journal of Psycho-Analysis</j>, <v>49</v>, <pp>691-698</pp>.</be>'
          >>> parsed_ref = etree.fromstring(ref, parser=parser)
          >>> be_journal = BiblioEntry(art_id="ANIJP-TR.007.0157A", ref_or_parsed_ref=parsed_ref)
          >>> be_journal.ref_rx, be_journal.ref_rx_confidence, be_journal.link_source
          ('IJP.049.0691A', 0.91, 'pattern')
          >>> # reset them if in database or pattern per above
          >>> be_journal.ref_rx = None
          >>> be_journal.ref_rx_confidence = 0
          >>> be_journal.identify_nonheuristic(ocd)
          {'ref_rx': 'IJP.049.0691A', 'ref_rx_confidence': 0.91, 'link_updated': True, 'link_source': 'pattern', 'ref_rxcf': None, 'ref_rxcf_confidence': 0}
      
          >>> be_journal = BiblioEntry(art_id="FA.013A.0120A", ref_or_parsed_ref='<be id="B009"><a><l>Sternberg</l>, J</a> &amp; <a><l>Scott</l>, A</a> (<y>2009</y>) <t>Editorial.</t> <j>British Journal of Psychotherapy</j>, <v>25</v> (<bs>2</bs>): <pp>143-5</pp>.</be>')
          >>> be_journal.ref_rx, be_journal.ref_rx_confidence, be_journal.link_source
          ('BJP.025.0143A', 0.91, 'pattern')
          >>> # reset them if in database or pattern per above
          >>> be_journal.ref_rx = None
          >>> be_journal.ref_rx_confidence = 0
          >>> be_journal.identify_nonheuristic(ocd)
          {'ref_rx': 'BJP.025.0143A', 'ref_rx_confidence': 0.91, 'link_updated': True, 'link_source': 'pattern', 'ref_rxcf': None, 'ref_rxcf_confidence': 0}

          >>> ref = '<be label="19" id="B019"><a><l>Freud</l></a>, <bst>Beyond the Pleasure Principle</bst> (London, <y>1950</y>), pp. <pp>17</pp> ff.</be>'
          >>> be_journal = BiblioEntry(art_id="FA.013A.0120A", ref_or_parsed_ref=ref)
          >>> be_journal.ref_rx, be_journal.ref_rx_confidence, be_journal.link_source
          (None, 0, None)
          >>> # reset them if in database or pattern per above
          >>> be_journal.ref_rx = None
          >>> be_journal.ref_rx_confidence = 0
          >>> be_journal.identify_nonheuristic()
          {'ref_rx': None, 'ref_rx_confidence': 0, 'link_updated': False, 'link_source': None, 'ref_rxcf': None, 'ref_rxcf_confidence': 0}
        """
    
        pep_ref = False
        ref_id = self.ref_local_id
        ret_val = None, None
        link_updated = self.link_updated
        
        if self.ref_rx is None:
            # still no known rx
            if self.ref_is_book:
                loc_str, match_val, whatever = known_books.getPEPBookCodeStr(self.ref_text)
                if loc_str is not None:
                    self.ref_rx = loc_str 
                    self.ref_rx_confidence = opasConfig.RX_CONFIDENCE_PROBABLE
                    self.link_source = opasConfig.RX_LINK_SOURCE_PATTERN
                    msg = f"\t\t\t...Matched Book {match_val}."
                    log_everywhere_if(verbose, level="debug", msg=msg)
            
            if self.ref_sourcecode and not link_updated:
                if not opasgenlib.is_empty(self.ref_pgrg):
                    try:
                        self.ref_pgstart, bib_pgend = self.ref_pgrg.split("-")
                    except Exception as e:
                        self.ref_pgstart = self.ref_pgrg
                else:
                    if self.ref_is_book:
                        self.ref_pgstart = 0
                    else:
                        self.ref_pgstart = bib_pgend = None
                
                if self.ref_pgstart or self.ref_is_book:
                    locator = Locator(strLocator=None,
                                      jrnlCode=self.ref_sourcecode, 
                                      jrnlVolSuffix="", 
                                      jrnlVol=self.ref_volume, 
                                      jrnlIss=None, 
                                      pgVar="A", 
                                      pgStart=self.ref_pgstart, 
                                      jrnlYear=self.ref_year, 
                                      localID=ref_id, 
                                      keepContext=1, 
                                      forceRoman=False, 
                                      notFatal=True, 
                                      noStartingPageException=True, 
                                      #filename=artInfo.filename
                                      )
                    
                    if locator.valid:
                        pep_ref = True
                        loc_str = str(locator)
                        if ocd.article_exists(loc_str):
                            msg = f"\t\t...Locator verified {loc_str}"
                            log_everywhere_if(verbose, level="debug", msg=msg)
                            self.ref_rx = loc_str
                            self.ref_exists = True
                            self.ref_rx_confidence = opasConfig.RX_CONFIDENCE_PROBABLE
                            link_updated = True
                            self.link_source = opasConfig.RX_LINK_SOURCE_PATTERN
                        else:
                            # see if there's a vol variant
                            self.ref_exists = False
                            loc_str = locator.articleID()
                            newloc = check_for_page_start(ocd, loc_str, verbose=False) # log it here, not there
                            if newloc is not None:
                                msg = f"\t\t...Page start fix: chgd {loc_str} to {newloc} in ref"
                                log_everywhere_if(verbose, level="debug", msg=msg)
                                self.ref_rx = newloc
                                self.ref_rx_confidence = opasConfig.RX_CONFIDENCE_PROBABLE
                                link_updated = True
                                self.link_source = opasConfig.RX_LINK_SOURCE_VARIATION
                            else:
                                newloc = check_for_vol_suffix(ocd, loc_str, verbose=False) # log it here, not there
                                if newloc is not None:
                                    msg = f"\t\t...VolSuffix missing: chgd {loc_str} to {newloc} in ref"
                                    log_everywhere_if(verbose, level="debug", msg=msg)
                                    self.ref_rx = newloc
                                    self.ref_rx_confidence = opasConfig.RX_CONFIDENCE_PROBABLE
                                    link_updated = True
                                    self.link_source = opasConfig.RX_LINK_SOURCE_VARIATION
                else:
                    locator = None

                if self.ref_in_pep and not self.ref_exists:
                    if locator.valid == 0:
                        msg = f"\t\tBib ID {ref_id} loc not valid {locator.articleID()} (components: {self.ref_sourcecode}/{self.ref_volume}/{self.ref_pgstart}) {opasgenlib.text_slice(self.ref_text, start_chr_count=25, end_chr_count=50)}"
                    else:
                        msg = f"\t\tBib ID {ref_id} loc valid {locator.articleID()} but doesn't exist (components: {self.ref_sourcecode}/{self.ref_volume}/{self.ref_pgstart}) {opasgenlib.text_slice(self.ref_text, start_chr_count=25, end_chr_count=50)}"
                        log_everywhere_if(verbose, level="info", msg=msg[:opasConfig.MAX_LOGMSG_LEN])
        
        self.link_updated = link_updated
        #ret_val = self.ref_rx, self.ref_rx_confidence, self.link_updated
        ret_val = BiblioMatch()
        ret_val.ref_exists = self.ref_exists
        ret_val.ref_rx = self.ref_rx
        ret_val.ref_rx_confidence = self.ref_rx_confidence
        ret_val.link_updated = self.link_updated
        ret_val.link_source = self.link_source
        ret_val.ref_rxcf = self.ref_rxcf
        ret_val.ref_rxcf_confidence = self.ref_rxcf_confidence
        
        return ret_val

    #------------------------------------------------------------------------------------------------------------
    def identify_heuristic(self, 
                           query_target="art_title_xml",
                           max_words=opasConfig.MAX_WORDS,
                           min_words=opasConfig.MIN_WORDS,
                           word_len=opasConfig.MIN_WORD_LEN,
                           max_cf_list=opasConfig.MAX_CF_LIST,
                           verbose=False):
        """
        For the current biblioentry, find matching articles via
         Solr search of the title, year and author.
           and return a matched rx and confidence
           and a list of possible matches, rxcf, and confidences.

        >>> import opasCentralDBLib
        >>> ocd = opasCentralDBLib.opasCentralDB()  

        >>> ref = '<be label="19" id="B019"><a><l>Freud</l></a>, <bst>Beyond the Pleasure Principle</bst> (London, <y>1950</y>), pp. <pp>17</pp> ff.</be>'
        >>> be_journal = BiblioEntry(art_id="FA.013A.0120A", ref_or_parsed_ref=ref)
        >>> be_journal.ref_rx, be_journal.ref_rx_confidence, be_journal.link_source
        (None, 0, None)
        >>> # reset them if in database or pattern per above
        >>> be_journal.ref_rx = None
        >>> be_journal.ref_rx_confidence = 0
        >>> be_journal.identify_heuristic()
        {'ref_rx': 'SE.018.0001A', 'ref_rx_confidence': 0.83, 'link_updated': True, 'link_source': 'heuristic', 'ref_rxcf': 'PAH.017.0151A:0.53', 'ref_rxcf_confidence': 0.53}

        
        """
        # title is either bib_entry.art_title_xml or bib_entry.source_title
        rx_confidence = 0
        title_list = []
        solr_adverse_punct_set = ':\"\'\,/'
        if self.ref_is_book:
            art_or_source_title = self.ref_sourcetitle
        else:
            art_or_source_title = self.ref_title
        
        # prev_rxcf = None
        if not opasgenlib.is_empty(art_or_source_title):
            art_or_source_title = opasgenlib.remove_all_punct(art_or_source_title)
            art_or_source_title = art_or_source_title.strip()
            if art_or_source_title:
                query = f"{query_target}:({art_or_source_title})"
            else:
                query = ""
                
            authors = self.ref_authors
            if authors:
                authors = opasgenlib.remove_all_punct(authors)
                if query == "":
                    query = f"authors:{authors}"
                else:
                    query = query + f" AND authors:{authors}"
        
            #title_words = re.findall(r'\b\w{%s,}\b' % word_len, art_or_source_title)[:max_words]
                
            #if self.ref_year_int:
                #query = query + f" AND art_year:{self.ref_year_int}"
        
            if self.ref_volume and not self.ref_is_book:
                # list of last name of authors with AND, search field art_authors_xml
                query = query + f" AND art_vol:{self.ref_volume_int}"
        
            if gDbg2: print (f"Solr Query: {query}")
            result, return_status = opasPySolrLib.search_text(query=query, limit=10, offset=0, full_text_requested=False, req_url=opasConfig.CACHEURL)
            if return_status[0] == 200:
                result_count = result.documentList.responseInfo.count
                if result_count > 0 and result_count < opasConfig.HEURISTIC_SEARCH_MAX_COUNT:
                    #rxcfs = [item.documentID for item in result.documentList.responseSet[0:max_cf_list]]
                    #rxcfs_confidence = []
                    title_list = []
                    for item in result.documentList.responseSet[0:max_cf_list]:
                        similarity_score_title = opasgenlib.similarityText(art_or_source_title, item.title)
                        similarity_score_ref = opasgenlib.similarityText(self.ref_text, item.documentRef)
                        # rxcfs_confidence.append(similarity_score)
                        locator = Locator(item.documentID)
                        type_match = locator.isBook() and self.ref_is_book
                        similarity_score = statistics.mean((similarity_score_title, similarity_score_ref, type_match))
                        if similarity_score_title > .70:
                            title_list.append({ "score": min(.99,
                                                             round(similarity_score, 2)),
                                                "art_title": item.title,
                                                "rx": item.documentID,
                                                "source_title": {art_or_source_title}, } )
                            
                    if title_list:
                        title_list = sorted(title_list, key=lambda d: d["score"], reverse=True)
                        rx_confidence = title_list[0]["score"]
                        if rx_confidence > .70:
                            self.ref_rx = title_list[0]["rx"]
                            self.ref_rx_confidence = rx_confidence # opasConfig.RX_CONFIDENCE_PROBABLE
                            self.link_updated = True
                            self.link_source = opasConfig.RX_LINK_SOURCE_TITLE_HEURISTIC
                            title_list = title_list[1:]
                            
                        if title_list: # take the rest as rxcf
                                self.ref_rxcf = [f'{item["rx"]}:{item["score"]}' for item in title_list]
                                self.ref_rxcf = self.ref_rxcf[:opasConfig.HEURISTIC_SEARCH_LIST_MAX_LEN]
                                self.ref_rxcf = ", ".join(self.ref_rxcf)
                                self.ref_rxcf_confidence = max([item["score"] for item in title_list])
                                self.link_updated = True
                                self.link_source = opasConfig.RX_LINK_SOURCE_HEURISTIC
                else:
                    if verbose: print (f"Not Found: {self.ref_entry_text}")
            else:
                log_everywhere_if(True, "warning", return_status)
    
        # ret_val = self.ref_rx, self.ref_rx_confidence, self.link_updated, self.ref_rxcf, self.ref_rxcf_confidence
        ret_val = BiblioMatch()
        ret_val.ref_rx = self.ref_rx
        ret_val.ref_rx_confidence = self.ref_rx_confidence
        ret_val.link_updated = self.link_updated
        ret_val.link_source = self.link_source
        ret_val.ref_rxcf = self.ref_rxcf
        ret_val.ref_rxcf_confidence = self.ref_rxcf_confidence
        
        return ret_val

    #------------------------------------------------------------------------------------------------------------
    def lookup_title_in_db(self, ocd, pub_type_match_required=True, verbose=False):
        """
        Try to match the title in the Database
        >>> import opasCentralDBLib
        >>> ocd = opasCentralDBLib.opasCentralDB()  

        >>> be_journal = BiblioEntry(art_id="AIM.013.0319A", ref_or_parsed_ref='<be label="33" id="B033"><a>S. <l>Freud</l></a>, <bst>New Introductory Lectures on Psychoanalysis</bst>, <bp>Hogarth Press</bp>, London, <bpd>1933</bpd>, p. <pp>106</pp>.</be>')
        >>> be_journal.ref_rx
        
        >>> result = be_journal.lookup_title_in_db(ocd)
        >>> result
        {'ref_rx': 'SE.022.0001A', 'ref_rx_confidence': 0.82, 'link_updated': True, 'link_source': 'title and year', 'ref_rxcf': None, 'ref_rxcf_confidence': 0}
        
        >>> # wrong page number supplied below, so no RX at first.  Then we look up title
        >>> be_journal = BiblioEntry(art_id="ANIJP-TR.007.0157A", ref_or_parsed_ref='<be id="B008"><a><l>Freud</l>, S.</a>, (<y>1917</y>), <t>“Mourning and melancholia”,</t> <bst>SE</bst> <v>14</v>, <pp>242-58</pp>.</be>')
        >>> be_journal.ref_rx   

        >>> result = be_journal.lookup_title_in_db(ocd)
        >>> result
        {'ref_rx': 'SE.014.0237A', 'ref_rx_confidence': 0.89, 'link_updated': True, 'link_source': 'title and year', 'ref_rxcf': None, 'ref_rxcf_confidence': 0}

        """
        ret_val = None
        if not opasgenlib.is_empty(self.ref_title):
            ref_title = opasgenlib.remove_all_punct(self.ref_title)
        else:
            ref_title = opasgenlib.remove_all_punct(self.ref_sourcetitle)

        # try to record and avoid conditions of false positive matches on tile
        exception_condition = len(ref_title) < 15 and self.ref_is_book
            
        if not exception_condition:
            select = f"""SELECT art_id,
                                art_year,
                                art_auth_citation,
                                art_citeas_text,
                                bk_info_xml,
                                soundex('{ref_title}') as ref_title_soundex,
                                soundex(art_title) as title_soundex,
                                art_title
                         from api_articles
                         where art_title sounds like '{ref_title}'
                         """
            results = ocd.get_select_as_list(select)
            if results:
                for result in results:
                    ret_val = result[0]
                    art_author_citation = result[2]
                    art_citation = result[3]
                    ref_year = result[1]
                    article_is_book = result[4]
                    if self.ref_is_book and article_is_book or pub_type_match_required == False:
                        pub_type_match = True
                    else:
                        pub_type_match = False
                    
                    #ref_title_soundex = result[5]
                    #title_soundex = result[6]
                    #title_soundex_confidence = opasgenlib.similarityText(title_soundex, ref_title_soundex)
                    art_title = result[7]
                    art_title = opasgenlib.remove_all_punct(art_title)

                    title_confidence = opasgenlib.similarityText(art_title, ref_title)
                    year_confidence = opasgenlib.similarityText(str(self.ref_year), str(ref_year))
                    author_confidence = opasgenlib.similarityText(self.ref_authors, art_author_citation)
                    full_citation_confidence = opasgenlib.similarityText(self.ref_text, art_citation)
                    
                    weighted_confidence = (title_confidence + year_confidence + author_confidence + full_citation_confidence) / 4
                    
                    if pub_type_match and title_confidence > .9 and  author_confidence > 0.7 and year_confidence > 0.7 and full_citation_confidence > 0.5:
                        self.ref_rx = ret_val
                        if ref_year == self.ref_year_int:
                            self.ref_rx_confidence = round(weighted_confidence, 2)
                            self.link_updated = True
                            self.link_source = opasConfig.RX_LINK_SOURCE_TITLE_AND_YEAR                            
                            break
                        else:
                            self.ref_rx_confidence = round(weighted_confidence, 2)
                            self.link_updated = True
                            self.link_source = opasConfig.RX_LINK_SOURCE_TITLE
                            break
                    else:
                        continue
            else:
                ret_val = None
        
        #ret_val = self.ref_rx, self.ref_rx_confidence, self.link_updated
        ret_val = BiblioMatch()
        ret_val.ref_rx = self.ref_rx
        ret_val.ref_rx_confidence = self.ref_rx_confidence
        ret_val.link_updated = self.link_updated
        ret_val.link_source = self.link_source
        ret_val.ref_rxcf = self.ref_rxcf
        ret_val.ref_rxcf_confidence = self.ref_rxcf_confidence
        ret_val.ref_xml = self.ref_xml
        
        return ret_val  

    #------------------------------------------------------------------------------------------------------------
    def lookup_more_exact_artid_in_db(self, ocd):
        """
        >>> import opasCentralDBLib
        >>> ocd = opasCentralDBLib.opasCentralDB()  
        
        >>> be_journal = BiblioEntry(art_id="AIM.014.0193A", ref_or_parsed_ref='<be label="7" id="B007"><a>S. <l>Freud</l></a>, <t>&#8216;The Theme of the Three Caskets&#8217;,</t> <bst>Standard Edition</bst> <v>12</v>.</be>')
        >>> be_journal.ref_rx
        'SE.012.0000A'
        >>> result = be_journal.lookup_more_exact_artid_in_db(ocd)
        >>> result
        {'ref_rx': 'SE.012.0289A', 'ref_rx_confidence': 0.91, 'link_updated': True, 'link_source': 'title', 'ref_rxcf': None, 'ref_rxcf_confidence': 0}
        
        >>> result = be_journal.compare_to_database(ocd)
        >>> result
        {'ref_rx': 'SE.012.0289A', 'ref_rx_confidence': 0.98, 'link_updated': True, 'link_source': 'database', 'ref_rxcf': None, 'ref_rxcf_confidence': 0}
    
        >>> be_journal = BiblioEntry(art_id="PAQ.084.0589A", ref_or_parsed_ref='<be id="B034"><a><l>Freud</l>, S.</a> (<y>1937</y>). <t>Analysis terminable and interminable.</t> <bst>S. E.</bst>, <v>23</v>.</be>')
        >>> be_journal.ref_rx
        'SE.023.0000A'
        
        >>> result = be_journal.lookup_more_exact_artid_in_db(ocd)
        >>> result
        {'ref_rx': 'SE.023.0209A', 'ref_rx_confidence': 0.99, 'link_updated': True, 'link_source': 'title', 'ref_rxcf': None, 'ref_rxcf_confidence': 0}
        """
        ret_val = self.ref_rx
        if self.ref_rx is not None:
            ref_id_parts = self.ref_rx.split('.')
            art_id_prefix_match = f"{ref_id_parts[0]}.{ref_id_parts[1]}.%"
            like_clause = f"AND art_id LIKE '{art_id_prefix_match}'"
        else:
            like_clause = ""
        
        if not opasgenlib.is_empty(self.ref_title):
            ref_title = self.ref_title
        else:
            ref_title = self.ref_sourcetitle
        try:
            ref_title = opasgenlib.remove_all_punct(ref_title, additional_chars="\t/,[]‘’1234567890")
        except Exception as e:
            ref_title = ref_title               
        
        ret_val = self.ref_rx
        if ref_title is not None:
            select = f"""SELECT art_id,
                                art_year,
                                art_title,
                                art_auth_citation,
                                soundex(art_title) as soundex1,
                                soundex('{ref_title}') as soundex2
                         FROM api_articles
                         WHERE
                              art_title sounds like '{ref_title}'
                              {like_clause};
                      """

            results = ocd.get_select_as_list(select)
            if results:
                ret_val = results[0][0]
                ref_year = results[0][1]
                art_title = results[0][2]
                self.ref_rx = ret_val
                art_auth_citaton = results[0][3]
                author_similarity = opasgenlib.similarityText(art_auth_citaton, self.ref_authors)
                title_similarity = opasgenlib.similarityText(art_title, ref_title)
                self.link_updated = True
                self.link_source = opasConfig.RX_LINK_SOURCE_TITLE
                if ref_year == self.ref_year_int and author_similarity > .80 and title_similarity > .80:
                    self.ref_rx_confidence = opasConfig.RX_CONFIDENCE_AUTO_POSITIVE
                else:
                    self.ref_rx_confidence = opasConfig.RX_CONFIDENCE_PROBABLE
        
        #ret_val = self.ref_rx, self.ref_rx_confidence, self.link_updated
        ret_val = BiblioMatch()
        ret_val.ref_rx = self.ref_rx
        ret_val.ref_rx_confidence = self.ref_rx_confidence
        ret_val.link_updated = self.link_updated
        ret_val.link_source = self.link_source
        ret_val.ref_rxcf = self.ref_rxcf
        ret_val.ref_rxcf_confidence = self.ref_rxcf_confidence
        ret_val.ref_xml = self.ref_xml
        return ret_val  
                
    #------------------------------------------------------------------------------------------------------------
    def compare_to_database(self, ocd, verbose=False):
        """
        Compare the rx for this with the Database table api_biblioxml stored ref_rx and ref_rx_confidence
        Update the object links if database is a higher confidence level
        
        Return the final ref_rx or None if it's not available in either place
        
        >>> import opasCentralDBLib
        >>> ocd = opasCentralDBLib.opasCentralDB()  

        >>> ref = '<be id="B018"><a><l>Ogden</l>, TH.</a>, (<y>2004a</y>), <t>“An introduction to the reading of Bion”,</t> <j>Int J Psychoanal</j>, <v>85</v>: <pp>285-300</pp>.</be>'
        >>> parsed_ref = etree.fromstring(ref, parser=parser)
        >>> be_journal = BiblioEntry(art_id="ANIJP-TR.007.0157A", ref_or_parsed_ref=parsed_ref)
        >>> be_journal.ref_rx
        'IJP.085.0285A'
        >>> result = be_journal.compare_to_database(ocd)
        >>> result
        {'ref_rx': 'IJP.085.0285A', 'ref_rx_confidence': 0.98, 'link_updated': True, 'link_source': 'database', 'ref_rxcf': None, 'ref_rxcf_confidence': 0}
    
        >>> be_journal = BiblioEntry(art_id="IJPOPEN.003.0061A", ref_or_parsed_ref='<be label="34)" id="B034"><a><l>Joseph</l>, B.</a> (<y>1982</y>). <t>Addiction to Near-Death.</t> In: <bst>Psychic Equilibrium and Psychic Change</bst>. Hove:<bp>Routledge</bp>, <bpd>1989</bpd>.</be>')
        >>> be_journal.ref_rx
        'NLP.009.0001A'
        >>> result = be_journal.compare_to_database(ocd)
        >>> result
        {'ref_rx': 'NLP.009.0001A', 'ref_rx_confidence': 0.98, 'link_updated': True, 'link_source': 'database', 'ref_rxcf': None, 'ref_rxcf_confidence': 0}


        """
        # ret_val = self.ref_rx, self.ref_rx_confidence, self.link_updated
        ret_val = False
        db_bibref = ocd.get_references_from_biblioxml_table(self.art_id, self.ref_local_id)
        
        if db_bibref:
            bib_refdb_model = db_bibref[0]   
            if bib_refdb_model.ref_rx:
                if bib_refdb_model.ref_rx_confidence > self.ref_rx_confidence:
                    # make sure it's clean
                    loc_str = Locator(bib_refdb_model.ref_rx).articleID()
                    if ocd.article_exists(loc_str):
                        self.ref_exists = True
                        self.ref_rx = loc_str
                        self.ref_rx_confidence = bib_refdb_model.ref_rx_confidence
                        self.link_updated = True
                        self.link_source = opasConfig.RX_LINK_SOURCE_DB
                        ret_val = True
                        #ret_val = self.ref_rx, self.ref_rx_confidence, self.link_updated

            if bib_refdb_model.ref_rxcf:
                if bib_refdb_model.ref_rxcf_confidence > self.ref_rxcf_confidence:
                    # make sure it's clean
                    self.ref_rxcf = bib_refdb_model.ref_rxcf
                    self.ref_rxcf_confidence = bib_refdb_model.ref_rxcf_confidence
                    self.link_updated = True
                    self.link_source = opasConfig.RX_LINK_SOURCE_DB
                    ret_val = True
                    #ret_val = self.ref_rx, self.ref_rx_confidence, self.link_updated
   

        return ret_val

#------------------------------------------------------------------------------------------------------------
def get_ref_correction(self, ocd, verbose=False):
    """
    Compare the rx for this with the Database table api_biblioxml stored ref_rx and ref_rx_confidence
    Update the object links if database is a higher confidence level
    
    Return the final ref_rx or None if it's not available in either place
    
    >>> import opasCentralDBLib
    >>> ocd = opasCentralDBLib.opasCentralDB()  

    >>> ref = '<be id="B018"><a><l>Ogden</l>, TH.</a>, (<y>2004a</y>), <t>“An introduction to the reading of Bion”,</t> <j>Int J Psychoanal</j>, <v>85</v>: <pp>285-300</pp>.</be>'
    >>> parsed_ref = etree.fromstring(ref, parser=parser)
    >>> be_journal = BiblioEntry(art_id="ANIJP-TR.007.0157A", ref_or_parsed_ref=parsed_ref)
    >>> be_journal.ref_rx
    'IJP.085.0285A'
    >>> result = be_journal.compare_to_database(ocd)
    >>> result
    {'ref_rx': 'IJP.085.0285A', 'ref_rx_confidence': 0.98, 'link_updated': True, 'link_source': 'database', 'ref_rxcf': None, 'ref_rxcf_confidence': 0}


    """
    if self.ref_rx is not None or self.ref_rxcf is not None:
        db_bibref = ocd.get_reference_correction(self.art_id, self.ref_local_id)
    
    return ret_val


#------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.path.append('./config') 

    print (40*"*", "opasBiblioSupport Tests", 40*"*")
    print ("Running in Python %s" % sys.version_info[0])
    logger = logging.getLogger(__name__)
    # extra logging for standalong mode 
    logger.setLevel(logging.WARN)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARN)
    # create formatter
    formatter = logging.Formatter('%(asctime)s %(name)s %(lineno)d - %(levelname)s %(message)s')    
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)

    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
    print ("All tests complete!")
    print ("Fini")
