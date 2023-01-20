#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
# Disable many annoying pylint messages, warning me about variable naming for example.
# yes, in my Solr code I'm caught between two worlds of snake_case and camelCase.

""" 
OPAS - opasBiblioSupport

Support for information contained in references in bibliographies.

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
from typing import List, Generic, TypeVar, Optional
import models

import lxml
from lxml import etree
import roman

import logging
logger = logging.getLogger(__name__)
from loggingDebugStream import log_everywhere_if    # log as usual, but if first arg is true, also put to stdout for watching what's happening
gDbg2 = True

parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=False)

from pydantic import BaseModel, Field # removed Field, causing an error on AWS

#import localsecrets
import opasConfig
import opasGenSupportLib as opasgenlib
import opasXMLHelper as opasxmllib
import opasCentralDBLib
# import opasLocator
# import opasArticleIDSupport
# import modelsOpasCentralPydantic
from opasLocator import Locator
# new for processing code
import PEPJournalData
jrnlData = PEPJournalData.PEPJournalData()
import PEPBookInfo
known_books = PEPBookInfo.PEPBookInfo()

#------------------------------------------------------------------------------------------------------------
#  Support functions
#------------------------------------------------------------------------------------------------------------
def strip_extra_spaces(textstr:str):
    if textstr is not None:
        ret_val = textstr.strip()
        ret_val = re.sub(" +", " ", ret_val)
    else:
        ret_val = None

    return ret_val

#------------------------------------------------------------------------------------------------------------
#  BiblioEntry Class
#------------------------------------------------------------------------------------------------------------
class BiblioEntry(object):
    """
    An entry from a documents bibliography.
    
    Used to populate the MySQL table api_biblioxml for statistical gathering
       and the Solr core pepwebrefs for searching in special cases.
       
    >>> ocd = opasCentralDBLib.opasCentralDB()  

    >>> ref = '<be id="B070"><a><l>Money-Kyrle</l>, R.</a> (<y>1968</y>). <t>Cognitive development.</t> <j>The International Journal of Psycho-Analysis</j>, <v>49</v>, <pp>691-698</pp>.</be>'
    >>> parsed_ref = etree.fromstring(ref, parser=parser)
    >>> be_journal = BiblioEntry("ANIJP-TR.007.0157A", parsed_ref)
    >>> rx = be_journal.identify_nonheuristic(ocd)
    >>> be_journal.rx
    'IJP.049.0691A'

    >>> be_journal = BiblioEntry("FA.013A.0120A", '<be id="B009"><a><l>Sternberg</l>, J</a> &amp; <a><l>Scott</l>, A</a> (<y>2009</y>) <t>Editorial.</t> <j>British Journal of Psychotherapy</j>, <v>25</v> (<bs>2</bs>): <pp>143-5</pp>.</be>')
    >>> rx = be_journal.identify_nonheuristic(ocd)
    >>> be_journal.rx
    'BJP.025.0143A'

    >>> ref = '<be id="B0006" reftype="journal" class="mixed-citation"><a class="western"><l>Beebe</l>, B.</a>, &amp; <a class="western"> <l>Lachmann</l>, F.</a> (<y>2002</y>). <t class="article-title">Organizing principles of interaction from infant research and the lifespan prediction of attachment: Application to adult treatment</t>. <j>Journal of Infant, Child, and Adolescent Psychotherapy</j>, <v> 2</v>(<bs>4</bs>), <pp>61 - 89</pp>&#8211;. doi:<webx type="doi">10.1080/15289168.2002.10486420</webx></be>'
    >>> parsed_ref = etree.fromstring(ref, parser=parser)
    >>> be_journal = BiblioEntry("FA.013A.0120A", parsed_ref)
    >>> rx = be_journal.identify_nonheuristic(ocd)
    >>> be_journal.rx
    'JICAP.002.0061A'
    
    
    """
    art_id: str = Field(None)
    bib_local_id: str = Field(None)
    art_year: Optional[int]
    bib_rx: str = Field(None)
    bib_rx_confidence: float = Field(0)
    bib_rxcf: str = Field(None)
    bib_rxcf_confidence: float = Field(0)
    bib_sourcecode: str = None
    bib_authors: str = Field(None)
    bib_articletitle: str = Field(None)
    title: str = Field(None)
    full_ref_text: str = Field(None)
    bib_sourcetype: str = Field(None)
    bib_sourcetitle: str = Field(None)
    bib_authors_xml: str = Field(None)
    full_ref_xml: str = Field(None)
    bib_pgrg: str = Field(None)
    doi: Optional[str]
    bib_year: str = Field(None)
    bib_year_int: Optional[int]
    bib_volume: str = Field(None)
    bib_volume_int: Optional[int]
    bib_volume_isroman: bool = Field(False, title="True if bib_volume is roman")
    bib_publisher: str = Field(None)
    last_update: datetime = Field(None)
    
    def __init__(self, art_id, ref_or_parsed_ref, db_bib_entry=[]):
        
        # allow either string xml ref or parsed ref
        if isinstance(ref_or_parsed_ref, str):
            parsed_ref = etree.fromstring(ref_or_parsed_ref, parser=parser)
            self.ref_entry_xml = ref_or_parsed_ref
        elif isinstance(ref_or_parsed_ref, object):
            parsed_ref = ref_or_parsed_ref
            self.ref_entry_xml = etree.tostring(parsed_ref, with_tail=False)
            self.ref_entry_xml = self.ref_entry_xml.decode("utf8") # convert from bytes
        else:
            raise TypeError("arg must be str or etree")
            
        if self.ref_entry_xml is not None:
            self.ref_entry_xml = re.sub(" +", " ", self.ref_entry_xml)
            
        if not db_bib_entry:
            self.last_update = datetime.today()
            self.rx = opasxmllib.xml_get_element_attr(parsed_ref, "rx", default_return=None)
            self.rx_confidence = 0
            self.rxcf = opasxmllib.xml_get_element_attr(parsed_ref, "rxcf", default_return=None) # related rx
            self.rxcf_confidence = 0
        else:
            self.last_update = db_bib_entry.last_update 
            self.rx = db_bib_entry[0].bib_rx
            self.rx_confidence = db_bib_entry[0].bib_rx_confidence
            self.rxcf = db_bib_entry[0].bib_rxcf
            self.rxcf_confidence = db_bib_entry[0].bib_rxcf_confidence          
            
        self.ref_entry_text = opasxmllib.xml_elem_or_str_to_text(parsed_ref)
        self.ref_entry_text = strip_extra_spaces(self.ref_entry_text)
        self.art_id = art_id
        self.sourcecode = ""
        self.ref_source_type = ""
        self.ref_is_book = False
        # self.art_year_int = 0 # artInfo.art_year_int
        self.ref_local_id= opasxmllib.xml_get_element_attr(parsed_ref, "id")
        self.ref_id = art_id + "." + self.ref_local_id
        self.ref_title = opasxmllib.xml_get_subelement_textsingleton(parsed_ref, "t")
        if self.ref_title:
            self.ref_title = strip_extra_spaces(self.ref_title)
            self.ref_title = self.ref_title[:1023]
        self.bib_articletitle = self.ref_title
        self.pgrg = opasxmllib.xml_get_subelement_textsingleton(parsed_ref, "pp")
        self.pgrg = opasgenlib.first_item_grabber(self.pgrg, re_separator_ptn=";|,", def_return=self.pgrg)
        self.pgrg = self.pgrg[:23]
        if self.pgrg == None:
            # try to find it in reference text?
            pass
        
        #self.rx = opasxmllib.xml_get_element_attr(ref, "rx", default_return=None)
        #self.rxcf = opasxmllib.xml_get_element_attr(ref, "rxcf", default_return=None) # related rx
        if self.rx is not None:
            self.rx_sourcecode = re.search("(.*?)\.", self.rx, re.IGNORECASE).group(1)
        else:
            self.rx_sourcecode = None
        self.volume = opasxmllib.xml_get_subelement_textsingleton(parsed_ref, "v")
        self.volume = self.volume[:23]
        if self.volume:
            self.volume_isroman = opasgenlib.is_roman_str(self.volume.upper())
            if self.volume_isroman:
                try:
                    self.volume_int = roman.fromRoman(self.volume.upper()) # use roman lib which generates needed exception
                except Exception as e:
                    self.volume_isroman = False
                    try:
                        self.volume_int = int(self.volume)
                    except Exception as e:
                        log_everywhere_if(True, "warning", msg=f"BibEntry vol {self.volume} is neither roman nor int {e}")
                        self.volume_int = 0
            else:
                if self.volume.isnumeric():
                    self.volume_int = int(self.volume)
                else:
                    self.volume_int = 0
        else:
            self.volume_int = 0
            self.volume_isroman = False

        self.publishers = opasxmllib.xml_get_subelement_textsingleton(parsed_ref, "bp")
        self.publishers = self.publishers[:254]
        journal_title = opasxmllib.xml_get_subelement_textsingleton(parsed_ref, "j")
        book_title = opasxmllib.xml_get_subelement_textsingleton(parsed_ref, "bst")
        if journal_title in ("Ges. Schr.", ):
            book_title = journal_title
            journal_title = None

        bk_locator_str, match_val, whatever = known_books.getPEPBookCodeStr(self.ref_entry_text)
        
        if (book_title or self.publishers) and not journal_title:
            self.ref_is_book = True
            self.ref_source_type = "book"
            self.source_title = book_title  # book title
            
        elif journal_title:
            self.ref_source_type = "journal"
            self.ref_is_book = False
            self.source_title = journal_title
        else:
            self.ref_source_type = "unknown"
            self.ref_is_book = False
            self.source_title = f"{journal_title} / {book_title}"

        if self.ref_is_book:
            self.year_of_publication = opasxmllib.xml_get_subelement_textsingleton(parsed_ref, "bpd")
            if self.year_of_publication == "":
                year = opasxmllib.xml_get_subelement_textsingleton(parsed_ref, "y")
                self.year_of_publication = opasgenlib.removeAllPunct(year) # punct_set=[',', '.', ':', ';', '(', ')', '\t', r'/', '"', "'", "[", "]"])
            if self.source_title is None or self.source_title == "":
                ## sometimes has markup
                self.source_title = book_title  # book title (bst)
        else:
            self.year_of_publication = opasxmllib.xml_get_subelement_textsingleton(parsed_ref, "y")
            sourcecode, dummy, dummy = jrnlData.getPEPJournalCode(self.source_title)
            if sourcecode is not None:
                self.sourcecode = sourcecode
                if self.rx_sourcecode is None and self.sourcecode is not None:
                    self.rx_sourcecode = self.sourcecode
                if self.rx_sourcecode != self.sourcecode:
                    logger.warning(f"Parsed title source code {self.source_title} does not match rx_sourcecode {self.rx_sourcecode}")
                
        if self.year_of_publication != "":
            # make sure it's not a range or list of some sort.  Grab first year
            self.year_of_publication = opasgenlib.year_grabber(self.year_of_publication)
        else:
            # try to match
            try:
                m = re.search(r"\(([A-z]*\s*,?\s*)?([12][0-9]{3,3}[abc]?)\)", self.ref_entry_xml)
                if m is not None:
                    self.year_of_publication = m.group(2)
            except Exception as e:
                logger.warning("no match %s/%s/%s" % (self.year_of_publication, parsed_ref, e))
            
        self.year_of_publication_int = 0
        if self.year_of_publication != "" and self.year_of_publication is not None:
            self.year_of_publication = re.sub("[^0-9]", "", self.year_of_publication)
            if self.year_of_publication != "" and self.year_of_publication is not None:
                try:
                    self.year_of_publication_int = int(self.year_of_publication[0:4])
                except ValueError as e:
                    logger.error("Error converting year_of_publication to int: %s / %s.  (%s)" % (self.year_of_publication, self.ref_entry_xml, e))
                except Exception as e:
                    logger.error("Error trying to find untagged bib year in %s (%s)" % (self.ref_entry_xml, e))
            else:
                logger.warning("Non-numeric year of pub: %s" % (self.ref_entry_xml))

        self.year = self.year_of_publication

        if self.year != "" and self.year is not None:
            self.year_int = int(self.year)
        else:
            self.year_int = None
            
        self.author_name_list = [etree.tostring(x, with_tail=False).decode("utf8") for x in parsed_ref.findall("a") if x is not None]
        self.authors_xml = '; '.join(self.author_name_list)
        self.authors_xml = self.authors_xml[:2040]
        self.author_list = [opasxmllib.xml_elem_or_str_to_text(x) for x in parsed_ref.findall("a") if opasxmllib.xml_elem_or_str_to_text(x) is not None]  # final if x gets rid of any None entries which can rarely occur.
        self.author_list_str = '; '.join(self.author_list)
        self.bib_authors = self.author_list_str = self.author_list_str[:2040]
        self.ref_doi = parsed_ref.findtext("webx[@type='doi']")


        self.ref = models.Biblioxml(art_id = art_id,
                                    bib_local_id = self.ref_id, 
                                    art_year = self.year_int, 
                                    bib_rx = self.rx, 
                                    bib_rx_confidence = self.rx_confidence, 
                                    bib_rxcf = self.rxcf, 
                                    bib_rxcf_confidence = self.rxcf_confidence, 
                                    bib_sourcecode = self.sourcecode, 
                                    bib_authors = self.bib_authors, 
                                    bib_articletitle = self.ref_title, 
                                    title = self.ref_title, 
                                    full_ref_text = self.ref_entry_text, 
                                    bib_sourcetype = self.ref_source_type, 
                                    bib_sourcetitle = self.source_title, 
                                    bib_authors_xml = self.authors_xml, 
                                    full_ref_xml = self.ref_entry_xml, 
                                    bib_pgrg = self.pgrg, 
                                    doi = self.ref_doi, 
                                    bib_year = self.year, 
                                    bib_year_int = self.year_int, 
                                    bib_volume = self.volume,
                                    bib_volume_int = self.volume_int,
                                    bib_volume_isroman=self.volume_isroman, 
                                    bib_publisher = self.publishers, 
                                    last_update = self.last_update                               
                                    )

        log_everywhere_if(self.rx, "debug", f"\t\t...BibEntry {self.rx} loaded")

    #------------------------------------------------------------------------------------------------------------
    def identify_nonheuristic(self, ocd, pretty_print=False, verbose=False):
        """
          (Heuristic Search is now a separate process to optimize speed.)
        """
    
        pep_ref = False
        art_id = self.art_id
        ref_id = self.ref_local_id
        ret_val = None
        
        # load biblio records for this artid to see if we have the info needed
        bibs_from_db = ocd.get_references_from_biblioxml_table(article_id=art_id, ref_local_id=ref_id)
        if bibs_from_db:
            biblioxml_from_db = bibs_from_db[0]
            ret_val = self.rx = biblioxml_from_db.bib_rx
                
        if ret_val is None:
            # still no known rx
            if self.ref_is_book:
                bk_locator_str, match_val, whatever = known_books.getPEPBookCodeStr(self.ref_entry_text)
                if bk_locator_str is not None:
                    self.rx = bk_locator_str 
                    search_str = f"//be[@id='{ref_id}']"
                    msg = f"\t\t\t...Matched Book {match_val}. {opasxmllib.xml_xpath_return_xmlstringlist(parsed_xml, search_str)[0]}"
                    log_everywhere_if(gDbg2, level="info", msg=msg)
                else:
                    # see if we have info to link SE/GW etc., these are in a sense like journals
                    pep_ref = False
                    if PEPJournalData.PEPJournalData.rgxSEPat2.search(self.ref_entry_text):
                        pep_ref = True
                        self.sourcecode = "SE"
                    elif PEPJournalData.PEPJournalData.rgxGWPat2.search(self.ref_entry_text):
                        pep_ref = True
                        self.sourcecode = "GW"
            
            if not self.rx and self.sourcecode:
                if not opasgenlib.is_empty(self.pgrg):
                    try:
                        bib_pgstart, bib_pgend = self.pgrg.split("-")
                    except Exception as e:
                        bib_pgstart = self.pgrg
                else:
                    if self.ref_is_book:
                        bib_pgstart = 0
                    else:
                        bib_pgstart = bib_pgend = None
                
                if bib_pgstart or self.ref_is_book:
                    locator = Locator(strLocator=None,
                                      jrnlCode=self.sourcecode, 
                                      jrnlVolSuffix="", 
                                      jrnlVol=self.volume, 
                                      jrnlIss=None, 
                                      pgVar="A", 
                                      pgStart=bib_pgstart, 
                                      jrnlYear=self.year, 
                                      localID=ref_id, 
                                      keepContext=1, 
                                      forceRoman=False, 
                                      notFatal=True, 
                                      noStartingPageException=True, 
                                      #filename=artInfo.filename
                                      )
                    if locator.valid != 0:
                        pep_ref = True
                        ret_val = self.rx = str(locator)
                        msg = f"\t\t...Locator extracted {self.rx}"
                        log_everywhere_if(verbose, level="debug", msg=msg)
                        
                else:
                    locator = None

                if locator is None or locator.valid == 0:
                    msg = f"\t\t...Bib ID {ref_id} not enough info {self.sourcecode}.{self.volume}.{bib_pgstart} {self.ref_entry_text}"
                    log_everywhere_if(verbose, level="info", msg=msg)
                elif not pep_ref:
                    pass

        return ret_val

    def parse_nonxml_reference(self, ref_text, verbose=False):
        #Reusable Patterns (should not have group names)
        pass
        
#------------------------------------------------------------------------------------------------------
def add_reference_to_biblioxml_table(ocd, artInfo, bib_entry, verbose=None):
    """
    Adds the bibliography data from a single document to the biblioxml table in mysql database opascentral.
    
    This database table is used as the basis for the cited_crosstab views, which show most cited articles
      by period.  It replaces fullbiblioxml which was being imported from the non-OPAS document database
      pepa1db, which is generated during document conversion from KBD3 to EXP_ARCH1.  That was being used
      as an easy bridge to start up OPAS.
      
    Note: This data is in addition to the Solr pepwebrefs (biblio) core which is added elsewhere.  The SQL table is
          primarily used for the cross-tabs, since the Solr core is more easily joined with
          other Solr cores in queries.  (TODO: Could later experiment with bridging Solr/SQL.)
          
    Note: More info than needed for crosstabs is captured to this table, but that's as a bridge
          to potential future uses.
          
          TODO: Finish redefining crosstab queries to use this base table.
      
    """
    ret_val = False
    
    #if bib_entry.rx is None or bib_entry.rxcf is None:
        ## Read from the current table
        # old_bib_entry = ocd.get_references_from_biblioxml_table(article_id=bib_entry.art_id, ref_local_id=bib_entry.ref_id)
        #if bib_entry.rx is None:
            #bib_entry.rx = old_bib_entry.rx
            #bib_entry.bib_rx_confidence = old_bib_entry.bib_rx_confidence 

        #if bib_entry.rxcf is None:
            #bib_entry.rx = old_bib_entry.rxcf
            #bib_entry.bib_rxcf_confidence = old_bib_entry.bib_rxcf_confidence 

    if bib_entry.rx_confidence is None:
        bib_entry.rx_confidence = 0
        
    if bib_entry.rxcf_confidence is None:
        bib_entry.rxcf_confidence = 0

    insert_if_not_exists = r"""REPLACE
                               INTO api_biblioxml (
                                    art_id,
                                    bib_local_id,
                                    art_year,
                                    bib_rx,
                                    bib_rx_confidence,
                                    bib_sourcecode, 
                                    bib_rxcf, 
                                    bib_rxcf_confidence,
                                    bib_authors, 
                                    bib_authors_xml, 
                                    bib_articletitle, 
                                    bib_sourcetype, 
                                    bib_sourcetitle, 
                                    bib_pgrg, 
                                    bib_year, 
                                    bib_year_int, 
                                    bib_volume, 
                                    bib_publisher,
                                    doi,
                                    full_ref_xml,
                                    full_ref_text
                                    )
                                values (%(art_id)s,
                                        %(ref_local_id)s,
                                        %(year_int)s,
                                        %(rx)s,
                                        %(rx_confidence)s,
                                        %(rx_sourcecode)s,
                                        %(rxcf)s,
                                        %(rxcf_confidence)s,
                                        %(author_list_str)s,
                                        %(authors_xml)s,
                                        %(ref_title)s,
                                        %(ref_source_type)s,
                                        %(source_title)s,
                                        %(pgrg)s,
                                        %(year_of_publication)s,
                                        %(year_of_publication_int)s,
                                        %(volume)s,
                                        %(publishers)s,
                                        %(ref_doi)s,
                                        %(ref_entry_xml)s,
                                        %(ref_entry_text)s
                                        );
                            """
    query_param_dict = bib_entry.__dict__
    # need to remove lists, even if they are not used.
    del query_param_dict["author_list"]
    del query_param_dict["author_name_list"]
    del query_param_dict["ref"]

    res = ""
    try:
        res = ocd.do_action_query(querytxt=insert_if_not_exists, queryparams=query_param_dict)
    except Exception as e:
        errStr = f"AddToBiblioDBError: insert (returned {res}) error {e}"
        logger.error(errStr)
        if opasConfig.LOCAL_TRACE: print (errStr)
        
    else:
        ret_val = True
        
    return ret_val  # return True for success

#------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.path.append('./config') 

    print (40*"*", "opasLoadSupportLib Tests", 40*"*")
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
