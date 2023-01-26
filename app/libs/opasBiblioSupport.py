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

gDbg2 = False
gDbg3 = True

parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=False)

from pydantic import BaseModel, Field # removed Field, causing an error on AWS

#import localsecrets
import opasConfig
import opasGenSupportLib as opasgenlib
import opasXMLHelper as opasxmllib
# import opasCentralDBLib
import opasPySolrLib

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

def check_for_known_books(ref_text):
    ret_val = known_books.getPEPBookCodeStr(ref_text)
    if ret_val[0] is not None:
        ret_val[2] = "pattern"

    return ret_val


def check_for_vol_suffix(ocd, loc_str, verbose):
    ret_val = None
    newloc = Locator(loc_str)
    if newloc.jrnlVol[-1].isnumeric():
        newloc.jrnlVol.volSuffix = "%"
        new_loc_str = newloc.articleID()
        new_locs = ocd.article_exists(new_loc_str)
        if len(new_locs) == 1:
            ret_val = new_locs[0][0]
            log_everywhere_if(verbose, level="info", msg=f"\t\t...Bib ID with vol variant found.  Returning it: {ret_val}.")
        else:
            log_everywhere_if(verbose, level="info", msg=f"\t\t...Bib ID {ref_id} ref rx: {loc_str} doesn't exist and {new_loc_str} has multiple possibilities.")

    return ret_val    

def check_for_page_start(ocd, loc_str, page_offset=-1, verbose=False):
    ret_val = None
    newloc = Locator(loc_str)
    newloc.pgStart += page_offset
    if newloc.isValid():
        new_loc_str = newloc.articleID()
        new_locs = ocd.article_exists(new_loc_str)
        if len(new_locs) == 1:
            ret_val = new_locs[0][0]
            log_everywhere_if(verbose, level="info", msg=f"\t\t...Bib ID with page-1 found.  Returning it: {ret_val}.")

    return ret_val    

def strip_extra_spaces(textstr:str):
    if textstr is not None:
        ret_val = textstr.strip()
        ret_val = re.sub(" +", " ", ret_val)
    else:
        ret_val = None

    return ret_val

#------------------------------------------------------------------------------------------------------
def find_matching_articles(bib_entry, 
                           query_target="art_title_xml",
                           max_words=opasConfig.MAX_WORDS,
                           min_words=opasConfig.MIN_WORDS,
                           word_len=opasConfig.MIN_WORD_LEN,
                           max_cf_list=opasConfig.MAX_CF_LIST,
                           verbose=False):
    """
    For the parsed_ref, find matching articles via
     Solr search of the title, year and author.
       and return a matched rx and confidence
       and a list of possible matches, rxcf, and confidences.
    
    """
    # title is either bib_entry.art_title_xml or bib_entry.source_title
    rx = None
    rxcfs = []
    rx_confidence = None
    rxcfs_confidence = []
    title_list = []
    solr_adverse_punct_set = [':', '"', "'", "[", "]", r"/"]
    if bib_entry.ref_is_book:
        art_or_source_title = bib_entry.source_title
    else:
        art_or_source_title = bib_entry.ref_title
    
    # prev_rxcf = None
    if art_or_source_title:
        art_or_source_title = opasgenlib.removeAllPunct(art_or_source_title, punct_set=[',', '.', ':', ';', '(', ')', '\t', r'/', '"', "'", "[", "]"])
        query = f"{query_target}:({art_or_source_title})"
        authors = bib_entry.ref_authors
        if authors:
            authors = opasgenlib.removeAllPunct(authors, punct_set=solr_adverse_punct_set)
            query = query + f" AND authors:{authors}"
    
        #title_words = re.findall(r'\b\w{%s,}\b' % word_len, art_or_source_title)[:max_words]
            
        if bib_entry.ref_year_int:
            query = query + f" AND art_year:{bib_entry.ref_year_int}"
    
        if bib_entry.ref_volume and not bib_entry.ref_is_book:
            # list of last name of authors with AND, search field art_authors_xml
            query = query + f" AND art_vol:{opasgenlib.removeAllPunct(bib_entry.ref_volume, punct_set=solr_adverse_punct_set)}"
    
        if gDbg2: print (f"Solr Query: {query}")
        result, return_status = opasPySolrLib.search_text(query=query, limit=10, offset=0, full_text_requested=False, req_url=opasConfig.CACHEURL)
        if return_status[0] == 200:
            result_count = result.documentList.responseInfo.count
            if result_count > 0 and result_count < 10:
                rxcfs = [item.documentID for item in result.documentList.responseSet[0:max_cf_list]]
                rxcfs_confidence = []
                title_list = []
                for item in result.documentList.responseSet[0:max_cf_list]:
                    similarity_score = opasgenlib.similarityText(art_or_source_title, item.title)
                    rxcfs_confidence.append(similarity_score)
                    title_list.append({
                                        "score": min(.99, round(similarity_score, 2)),
                                        "art_title": item.title,
                                        "rx": item.documentID,
                                        "source_title": {art_or_source_title},
                                       }
                                     )
                    
                title_list = sorted(title_list, key=lambda d: d["score"], reverse=True)
                rx_confidence = title_list[0]["score"]
                rx = title_list[0]["rx"]
                rxcfs = [item["rx"] for item in title_list]
                rxcfs_confidence = [item["score"] for item in title_list]
                
                
                #if title_list != []:
                
                    #if verbose: print (f"\t\t\t...Article title first {len(title_words)} words of len {word_len} for search: {query} from title:{art_or_source_title}")
                    #for n in title_list:
                        #if verbose: print (f"\t\t\t\t...cf Article Title: {n[:max_display_len_cf_articles]}")
                            
            else:
                if verbose: print (f"Not Found: {bib_entry.ref_entry_text}")
        else:
            log_everywhere_if(True, "warning", return_status)

    return rx, rx_confidence, rxcfs, rxcfs_confidence, title_list

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

    >>> check_for_page_start(ocd, "AIM.014.0194A", page_offset=-1)
    'AIM.014.0193A'
    
    >>> check_for_page_start(ocd, "AIM.014.0192A", page_offset=1)
    'AIM.014.0193A'
    
    >>> be_journal = BiblioEntry(art_id="IJPOPEN.003.0061A", ref_or_parsed_ref='<be label="34)" id="B034"><a><l>Joseph</l>, B.</a> (<y>1982</y>). <t>Addiction to Near-Death.</t> In: <bst>Psychic Equilibrium and Psychic Change</bst>. Hove:<bp>Routledge</bp>, <bpd>1989</bpd>.</be>')
    >>> be_journal.ref_rx
    'NLP.009.0001A'
    
    >>> result = be_journal.compare_to_database(ocd)
    >>> result[0]
    'NLP.009.0001A'
    
    >>> be_journal = BiblioEntry(art_id="AIM.014.0193A", ref_or_parsed_ref='<be label="7" id="B007"><a>S. <l>Freud</l></a>, <t>&#8216;The Theme of the Three Caskets&#8217;,</t> <bst>Standard Edition</bst> <v>12</v>.</be>')
    >>> be_journal.ref_rx
    'SE.012.0289A'
    
    >>> result = be_journal.compare_to_database(ocd)
    >>> result[0]
    'SE.012.0289A'
    
    >>> be_journal = BiblioEntry(art_id="AIM.013.0319A", ref_or_parsed_ref='<be label="33" id="B033"><a>S. <l>Freud</l></a>, <bst>New Introductory Lectures on Psychoanalysis</bst>, <bp>Hogarth Press</bp>, London, <bpd>1933</bpd>, p. <pp>106</pp>.</be>')
    >>> be_journal.ref_rx
    
    
    >>> result = be_journal.compare_to_database(ocd)
    >>> result[0]
    'SE.022.0001A'

    >>> be_journal = BiblioEntry(art_id="ANIJP-TR.007.0157A", ref_or_parsed_ref='<be id="B008"><a><l>Freud</l>, S.</a>, (<y>1917</y>), <t>“Mourning and melancholia”,</t> <bst>SE</bst> <v>14</v>, <pp>242-58</pp>.</be>')
    >>> be_journal.ref_rx
    
    
    >>> result = be_journal.compare_to_database(ocd)
    >>> result[0]
    'SE.014.0242A'

    >>> ref = '<be id="B018"><a><l>Ogden</l>, TH.</a>, (<y>2004a</y>), <t>“An introduction to the reading of Bion”,</t> <j>Int J Psychoanal</j>, <v>85</v>: <pp>285-300</pp>.</be>'
    >>> parsed_ref = etree.fromstring(ref, parser=parser)
    >>> be_journal = BiblioEntry(art_id="ANIJP-TR.007.0157A", ref_or_parsed_ref=parsed_ref)
    >>> result = be_journal.compare_to_database(ocd)
    >>> result[0], result[1]
    ('IJP.085.0285A', 0.98)
    
    >>> ref = '<be id="B070"><a><l>Money-Kyrle</l>, R.</a> (<y>1968</y>). <t>Cognitive development.</t> <j>The International Journal of Psycho-Analysis</j>, <v>49</v>, <pp>691-698</pp>.</be>'
    >>> parsed_ref = etree.fromstring(ref, parser=parser)
    >>> be_journal = BiblioEntry(art_id="ANIJP-TR.007.0157A", ref_or_parsed_ref=parsed_ref)
    >>> be_journal.identify_nonheuristic(ocd)
    'IJP.049.0691A'

    >>> be_journal = BiblioEntry(art_id="FA.013A.0120A", ref_or_parsed_ref='<be id="B009"><a><l>Sternberg</l>, J</a> &amp; <a><l>Scott</l>, A</a> (<y>2009</y>) <t>Editorial.</t> <j>British Journal of Psychotherapy</j>, <v>25</v> (<bs>2</bs>): <pp>143-5</pp>.</be>')
    >>> be_journal.identify_nonheuristic(ocd)
    'BJP.025.0143A'

    >>> ref = '<be id="B0006" reftype="journal" class="mixed-citation"><a class="western"><l>Beebe</l>, B.</a>, &amp; <a class="western"> <l>Lachmann</l>, F.</a> (<y>2002</y>). <t class="article-title">Organizing principles of interaction from infant research and the lifespan prediction of attachment: Application to adult treatment</t>. <j>Journal of Infant, Child, and Adolescent Psychotherapy</j>, <v> 2</v>(<bs>4</bs>), <pp>61 - 89</pp>&#8211;. doi:<webx type="doi">10.1080/15289168.2002.10486420</webx></be>'
    >>> parsed_ref = etree.fromstring(ref, parser=parser)
    >>> be_journal = BiblioEntry(art_id="FA.013A.0120A", ref_or_parsed_ref=parsed_ref)
    >>> be_journal.identify_nonheuristic(ocd)
    'JICAP.002D.0061A'
    
    """
    # Transitional, until I change this class to the model
    art_id: str = Field(None)
    ref_local_id: str = Field(None)
    art_year: int = Field(0)              # containing article year
    ref_rx: str = Field(None)
    ref_rx_confidence: float = Field(0)
    ref_rxcf: str = Field(None)
    ref_rxcf_confidence: float = Field(0)
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
    ref_pgrg: str = Field(None)
    ref_doi: Optional[str]
    ref_title: str = Field(None)
    ref_year: str = Field(None)
    ref_year_int: Optional[int]
    ref_volume: str = Field(None)
    ref_volume_int: Optional[int]
    ref_volume_isroman: bool = Field(False, title="True if bib_volume is roman")
    ref_publisher: str = Field(None)
    ref_in_pep: bool = Field(False, title="Indicates this is a PEP reference")
    link_source: str = Field(None, title="Source of rx link, 'xml', 'database', or 'pattern'")
    link_updated: bool = Field(False, title="Indicates whether the data was corrected during load. If so, may need to update DB.  See link_source for method")
    last_update: datetime = Field(None)
    
    def __init__(self, art_id, art_year=None, ref_or_parsed_ref=None, db_bib_entry=[], verbose=False):
        # allow either string xml ref or parsed ref
        if ref_or_parsed_ref is None:
            raise ValueError("You must provide a ref or parsed ref")

        if isinstance(ref_or_parsed_ref, str):
            parsed_ref = etree.fromstring(ref_or_parsed_ref, parser=parser)
            ref_entry_xml = ref_or_parsed_ref
        elif isinstance(ref_or_parsed_ref, object):
            parsed_ref = ref_or_parsed_ref
            ref_entry_xml = etree.tostring(parsed_ref, with_tail=False)
            ref_entry_xml = ref_entry_xml.decode("utf8") # convert from bytes
        else:
            raise TypeError("arg must be str or etree")
            
        self.art_id = art_id
        self.ref_local_id = opasxmllib.xml_get_element_attr(parsed_ref, "id")
        self.ref_id = art_id + "." + self.ref_local_id
        
        self.art_year = art_year
        if art_year is not None:
            try:
                self.art_year_int = int(art_year)
            except Exception as e:
                self.art_year_int = 0

        if ref_entry_xml is not None:
            ref_entry_xml = re.sub(" +", " ", ref_entry_xml)
        self.ref_xml = ref_entry_xml

        ref_text = opasxmllib.xml_elem_or_str_to_text(parsed_ref)
        ref_text = strip_extra_spaces(ref_text)
        self.ref_text = ref_text
        
        if not db_bib_entry:
            self.last_update = datetime.today()
            self.ref_rx = opasxmllib.xml_get_element_attr(parsed_ref, "rx", default_return=None)
            self.ref_rx_confidence = 0
            self.ref_rxcf = opasxmllib.xml_get_element_attr(parsed_ref, "rxcf", default_return=None) # related rx
            self.ref_rxcf_confidence = 0
        else:
            self.last_update = db_bib_entry.last_update 
            self.ref_rx = db_bib_entry[0].ref_rx
            self.ref_rx_confidence = db_bib_entry[0].ref_rx_confidence
            self.ref_rxcf = db_bib_entry[0].ref_rxcf
            self.ref_rxcf_confidence = db_bib_entry[0].ref_rxcf_confidence          
            
        ref_title = opasxmllib.xml_get_subelement_textsingleton(parsed_ref, "t")
        if ref_title:
            ref_title = strip_extra_spaces(ref_title)
            ref_title = ref_title[:1023]
        self.ref_title = ref_title
        
        self.ref_pgrg = opasxmllib.xml_get_subelement_textsingleton(parsed_ref, "pp")
        self.ref_pgrg = opasgenlib.first_item_grabber(self.ref_pgrg, re_separator_ptn=";|,", def_return=self.ref_pgrg)
        self.ref_pgrg = self.ref_pgrg[:23]
        if self.ref_pgrg == None:
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

        self.ref_volume = opasxmllib.xml_get_subelement_textsingleton(parsed_ref, "v")
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

        self.ref_publisher = opasxmllib.xml_get_subelement_textsingleton(parsed_ref, "bp")
        self.ref_publisher = self.ref_publisher[:254]
        journal_title = opasxmllib.xml_get_subelement_textsingleton(parsed_ref, "j")
        book_title = opasxmllib.xml_get_subelement_textsingleton(parsed_ref, "bst")
        self.ref_sourcetitle = None
        if journal_title in ("Ges. Schr.", ):
            book_title = journal_title
            journal_title = None

        if (book_title or self.ref_publisher) and not journal_title:
            self.ref_is_book = True
            self.ref_sourcetype = "book"
            self.sourcetitle = book_title  # book title
          
        elif journal_title:
            self.ref_sourcetype = "journal"
            self.ref_is_book = False
            self.ref_sourcetitle = journal_title
        else:
            self.ref_sourcetype = "unknown"
            self.ref_is_book = False
            self.ref_sourcetitle = f"{journal_title} / {book_title}"

        if self.ref_is_book:
            # see if we have info to link SE/GW etc., these are in a sense like journals
            if opasgenlib.is_empty(self.ref_sourcecode):
                if PEPJournalData.PEPJournalData.rgxSEPat2.search(self.ref_text):
                    self.ref_in_pep = True
                    self.sourcecode = "SE"
                elif PEPJournalData.PEPJournalData.rgxGWPat2.search(self.ref_text):
                    self.ref_in_pep = True
                    self.sourcecode = "GW"
            
            year_of_publication = opasxmllib.xml_get_subelement_textsingleton(parsed_ref, "bpd")
            if year_of_publication == "":
                year = opasxmllib.xml_get_subelement_textsingleton(parsed_ref, "y")
                year_of_publication = opasgenlib.removeAllPunct(year) # punct_set=[',', '.', ':', ';', '(', ')', '\t', r'/', '"', "'", "[", "]"])
            if self.ref_sourcetitle is None or self.ref_sourcetitle == "":
                ## sometimes has markup
                self.ref_sourcetitle = book_title  # book title (bst)
        else:
            year_of_publication = opasxmllib.xml_get_subelement_textsingleton(parsed_ref, "y")
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
                logger.warning("no match %s/%s/%s" % (year_of_publication, parsed_ref, e))
            
        if year_of_publication != "" and year_of_publication is not None:
            year_of_publication = re.sub("[^0-9]", "", year_of_publication)

        self.ref_year = year_of_publication
        if self.ref_year != "" and self.ref_year is not None:
            try:
                self.ref_year_int = int(self.ref_year[0:4])
            except ValueError as e:
                logger.error("Error converting year_of_publication to int: %s / %s.  (%s)" % (self.year, self.ref_xml, e))
            except Exception as e:
                logger.error("Error trying to find untagged bib year in %s (%s)" % (self.ref_xml, e))
                
        else:
            self.ref_year_int = 0
            
        author_name_list = [etree.tostring(x, with_tail=False).decode("utf8") for x in parsed_ref.findall("a") if x is not None]
        self.ref_authors_xml = '; '.join(author_name_list)
        self.ref_authors_xml = self.ref_authors_xml[:2040]
        author_list = [opasxmllib.xml_elem_or_str_to_text(x) for x in parsed_ref.findall("a") if opasxmllib.xml_elem_or_str_to_text(x) is not None]  # final if x gets rid of any None entries which can rarely occur.
        self.ref_authors = '; '.join(author_list)
        self.ref_authors = self.ref_authors[:2040]
        self.ref_doi = parsed_ref.findtext("webx[@type='doi']")

        if self.ref_rx is None:
            ref_rx, ref_rx_confidence, whatever = known_books.getPEPBookCodeStr(self.ref_text)
            if ref_rx is not None:
                self.ref_rx = ref_rx
                self.ref_rx_confidence = ref_rx_confidence
                self.ref_in_pep = True
                self.link_updated = True
                self.link_source = "pattern"

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
        if gDbg2:
            log_everywhere_if(self.rx, "debug", f"\t\t...BibEntry linked to {self.rx} loaded")

    #------------------------------------------------------------------------------------------------------------
    def identify_nonheuristic(self, ocd, pretty_print=False, verbose=False):
        """
          (Heuristic Search is now a separate process to optimize speed.)
        """
    
        pep_ref = False
        art_id = self.art_id
        ref_id = self.ref_local_id
        ret_val = None
        
        if self.ref_rx is None:
            # still no known rx
            if self.ref_is_book:
                bk_locator_str, match_val, whatever = known_books.getPEPBookCodeStr(self.ref_text)
                if bk_locator_str is not None:
                    self.rx = bk_locator_str 
                    search_str = f"//be[@id='{ref_id}']"
                    msg = f"\t\t\t...Matched Book {match_val}. {opasxmllib.xml_xpath_return_xmlstringlist(parsed_xml, search_str)[0]}"
                    log_everywhere_if(gDbg2, level="info", msg=msg)
                else:
                    # see if we have info to link SE/GW etc., these are in a sense like journals
                    pep_ref = False
                    if PEPJournalData.PEPJournalData.rgxSEPat2.search(self.ref_text):
                        pep_ref = True
                        self.sourcecode = "SE"
                    elif PEPJournalData.PEPJournalData.rgxGWPat2.search(self.ref_text):
                        pep_ref = True
                        self.sourcecode = "GW"
            
            if not self.ref_rx and self.ref_sourcecode:
                if not opasgenlib.is_empty(self.ref_pgrg):
                    try:
                        bib_pgstart, bib_pgend = self.ref_pgrg.split("-")
                    except Exception as e:
                        bib_pgstart = self.ref_pgrg
                else:
                    if self.ref_is_book:
                        bib_pgstart = 0
                    else:
                        bib_pgstart = bib_pgend = None
                
                if bib_pgstart or self.ref_is_book:
                    locator = Locator(strLocator=None,
                                      jrnlCode=self.ref_sourcecode, 
                                      jrnlVolSuffix="", 
                                      jrnlVol=self.ref_volume, 
                                      jrnlIss=None, 
                                      pgVar="A", 
                                      pgStart=bib_pgstart, 
                                      jrnlYear=self.ref_year, 
                                      localID=ref_id, 
                                      keepContext=1, 
                                      forceRoman=False, 
                                      notFatal=True, 
                                      noStartingPageException=True, 
                                      #filename=artInfo.filename
                                      )
                    if locator.valid != 0:
                        pep_ref = True
                        loc_str = str(locator)
                        if ocd.article_exists(loc_str):
                            msg = f"\t\t...Locator verified {loc_str}"
                            log_everywhere_if(verbose, level="debug", msg=msg)
                            ret_val = self.ref_rx = loc_str
                        else:
                            # see if there's a vol variant
                            loc_str = locator.articleID()
                            newloc = check_for_vol_suffix(ocd, loc_str, verbose)
                            if newloc is not None:
                                ret_val = self.ref_rx = newloc
                                self.ref_confidence = opasConfig.RX_CONFIDENCE_PROBABLE
                                self.link_updated = True
                else:
                    locator = None

                if locator is None or locator.valid == 0:
                    msg = f"\t\t...Bib ID {ref_id} not enough info {self.sourcecode}.{self.volume}.{bib_pgstart} {self.ref_text}"
                    log_everywhere_if(verbose, level="info", msg=msg[:opasConfig.MAX_LOGMSG_LEN])
                elif not pep_ref:
                    pass

        return ret_val

    def parse_nonxml_reference(self, ref_text, verbose=False):
        #Reusable Patterns (should not have group names)
        pass

    def compare_to_database(self, ocd, verbose=False):
        """
        Compare the rx for this with the Database table api_biblioxml stored ref_rx and ref_rx_confidence
        Return the best version.
        """
        art_id = self.art_id
        ref_rx = self.ref_rx    
        ref_rx_confidence = int(self.ref_rx_confidence)
        ref_source = "self"
        ref_obj = self
        
        ref_id = self.ref_local_id
        if ref_rx is not None:
            ref_rx = Locator(ref_rx).articleID()
    
        list_of_models = ocd.get_references_from_biblioxml_table(art_id)
        if list_of_models:
            api_biblioxml_dict_of_models = {x.ref_local_id: x for x in list_of_models}
        else:
            api_biblioxml_dict_of_models = {}

        bib_refdb_model = api_biblioxml_dict_of_models.get(ref_id)
        if bib_refdb_model.ref_rx:
            if bib_refdb_model.ref_rx_confidence > ref_rx_confidence:
                ref_rx = Locator(bib_refdb_model.ref_rx).articleID()
                ref_rx_confidence = bib_refdb_model.ref_rx_confidence
                ref_obj = bib_refdb_model
                ref_source = "api_biblioxml"
        
        ret_val = ref_rx, ref_rx_confidence, ref_source, ref_obj
        return ret_val

    def try_again(self, parsed_ref):
        art_id = self.art_id
        ref_rx = self.ref_rx    
        ref_rx_confidence = int(self.ref_rx_confidence)
        ref_source = "self"
        ref_obj = self
        
        ref_id = self.ref_local_id
        
        if not ref_rx:
            # still no rx
            if self.ref_is_book:
                bk_locator_str, match_val, whatever = known_books.getPEPBookCodeStr(self.ref_text)
                if bk_locator_str is not None:
                    ref.attrib["rx"] = bk_locator_str
                    search_str = f"//be[@id='{ref_id}']"
                    msg = f"\t\t\t...Matched Book {match_val}. {opasxmllib.xml_xpath_return_xmlstringlist(parsed_xml, search_str)[0]}"
                    log_everywhere_if(gDbg2, level="info", msg=msg)
                    
                else:
                    # see if we have info to link SE/GW etc., these are in a sense like journals
                    pep_ref = False
                    if PEPJournalData.PEPJournalData.rgxSEPat2.search(bib_entry.ref_text):
                        pep_ref = True
                        bib_entry.sourcecode = "SE"
                    elif PEPJournalData.PEPJournalData.rgxGWPat2.search(bib_entry.ref_text):
                        pep_ref = True
                        bib_entry.sourcecode = "GW"
            
            if not ref.attrib.get("rx") and bib_entry.ref_sourcecode:
                if not opasgenlib.is_empty(bib_entry.ref_pgrg):
                    try:
                        bib_pgstart, bib_pgend = bib_entry.ref_pgrg.split("-")
                    except Exception as e:
                        bib_pgstart = bib_entry.ref_pgrg
                else:
                    if bib_entry.ref_is_book:
                        bib_pgstart = 0
                    else:
                        bib_pgstart = bib_pgend = None
                
                if bib_pgstart or bib_entry.ref_is_book:
                    locator = Locator(strLocator=None,
                                      jrnlCode=bib_entry.ref_sourcecode, 
                                      jrnlVolSuffix="", 
                                      jrnlVol=bib_entry.ref_volume, 
                                      jrnlIss=None, 
                                      pgVar="A", 
                                      pgStart=bib_pgstart, 
                                      jrnlYear=bib_entry.ref_year, 
                                      localID=ref_id, 
                                      keepContext=1, 
                                      forceRoman=False, 
                                      notFatal=True, 
                                      noStartingPageException=True, 
                                      filename=artInfo.filename)
                    if locator.valid:
                        if ocd.article_exists(locator):
                            pep_ref = True
                        else:
                            pep_ref = False
                else:
                    locator = None

                if locator is None or locator.valid == 0:
                    msg = f"\t\t...Bib ID {ref_id} not enough info {bib_entry.ref_sourcecode}.{bib_entry.ref_volume}.{bib_pgstart} {bib_entry.ref_text}"
                    log_everywhere_if(verbose, level="info", msg=msg)
                elif not pep_ref:
                    pass
                else:
                    ref.attrib["rx"] = locator.articleID()
                    ref.attrib["rx_conf"] = str(0.99)
                    search_str = f"//be[@id='{ref_id}']"
                    msg = f"\t\t...Matched Journal {opasxmllib.xml_xpath_return_xmlstringlist(parsed_xml, search_str)[0]}"
                    log_everywhere_if(verbose, level="debug", msg=msg)
        
    def dummy(self): 

        bib_refdb_model = ocd.api_biblioxml_dict_of_models.get(ref_id)

        if bib_refdb_model.ref_rx:
            bib_refdb_model.ref_rx = Locator(bib_refdb_model.ref_rx).articleID()
            bib_refdb_model.ref_rx_confidence = bib_refdb_model.ref_rx_confidence
        
        
        # compare to database anyway
        if bib_refdb_model:
            if bib_refdb_model.ref_rx:
                bib_refdb_model.ref_rx = Locator(bib_refdb_model.ref_rx).articleID()
                bib_refdb_model.ref_rx_confidence = bib_refdb_model.ref_rx_confidence
                bib_refdb_slice = opasgenlib.text_slice(bib_refdb_model.ref_text)
            if ref_rx:
                if bib_refdb_model.ref_rx:
                    if bib_refdb_model.ref_rx != ref_rx and bib_refdb_model.ref_rx_confidence == 1:
                        # change ref, confidence is certain in db
                        ref.attrib["rx"] = bib_refdb_model.ref_rx
                        ref.attrib["rxconf"] = str(bib_refdb_model.ref_rx_confidence)
                        if verbose: print (f"\t\t...dict ({bib_refdb_model.ref_rx} {bib_refdb_model.ref_rx_confidence}) overrides rx: {ref_rx} {bib_refdb_slice}")
                    elif bib_refdb_model.ref_rx != ref_rx and bib_refdb_model.ref_rx_confidence > ref_rx_confidence:
                        #keep separate from above case for debugging and improvement
                        log_everywhere_if(gDbg3,
                                          level="info",
                                          msg=f"\t\t...Repl, rx with db (conf: {ref_rx_confidence}/{bib_refdb_model.ref_rx_confidence} {bib_refdb_slice}")
                        ref.attrib["rx"] = bib_refdb_model.ref_rx
                        ref.attrib["rxconf"] = str(bib_refdb_model.ref_rx_confidence)
                        
            elif bib_refdb_model.ref_rx and bib_refdb_model.ref_rx_confidence != opasConfig.RX_CONFIDENCE_THIS_IS_NOT_THE_REFERENCE:
                if ocd.article_exists(bib_refdb_model.ref_rx):
                    if verbose: print (f"\t\t...Bib ID {ref_id} Bib_dict used: {bib_refdb_model.ref_rx} {bib_refdb_slice}")
                    ref.attrib["rx"] = bib_refdb_model.ref_rx
                    ref.attrib["rxconf"] = str(bib_refdb_model.ref_rx_confidence)
                else:
                    if ocd.update_biblioxml_links(bib_refdb_model.art_id, bib_refdb_model.ref_local_id, rx=bib_refdb_model.ref_rx, rx_confidence=opasConfig.RX_CONFIDENCE_THIS_IS_NOT_THE_REFERENCE):
                        rx, rx_confidence, rxcfs, rxcfs_confidence, \
                            title_list = find_matching_articles(bib_entry)
                            
                        if rx_confidence is not None and rx_confidence > opasConfig.RX_CONFIDENCE_PAGE_ADJUSTED:
                            if verbose: print (f"\t\t...Bib ID {ref_id} Bib_dict used: {bib_refdb_model.ref_rx} {bib_refdb_slice}")
                            ref.attrib["rx"] = rx
                            ref.attrib["rxconf"] = str(rx_confidence)
                            log_everywhere_if(True, level="warning",
                                              msg=f"\t\t...BAD rx {bib_refdb_model.ref_rx} in db{bib_refdb_model.ref_rx} in db dict: {bib_refdb_model.art_id}.{bib_refdb_model.ref_local_id}. Found heuristic replacement {rx}, {rx_confidence} for now: Found heuristic replacement for now: {opasgenlib.text_slice(title_list[0], chr_count=40)}")
                        else:
                            rx2, rx2_confidence, rxcfs2, rxcfs_confidence2, \
                                title_list2 = find_matching_articles(bib_refdb_model)
                            if rx_confidence is not None and rx2_confidence > opasConfig.RX_CONFIDENCE_PAGE_ADJUSTED:
                                if verbose: print (f"\t\t...Bib ID {ref_id} Bib_dict used: {bib_refdb_model.ref_rx} {bib_refdb_slice}")
                                ref.attrib["rx"] = rx2
                                ref.attrib["rxconf"] = str(rx2_confidence)
                                log_everywhere_if(True, level="warning",
                                                  msg=f"\t\t...BAD rx {bib_refdb_model.ref_rx} in db dict: {bib_refdb_model.art_id}.{bib_refdb_model.ref_local_id}. Found heuristic replacement {rx2}, {rx2_confidence} for now: {opasgenlib.text_slice(title_list2[0], chr_count=40)}")
                            else:
                                print (bib_entry.ref_text)
                                log_everywhere_if(True, level="warning",
                                                  msg=f"\t\t...Reset BAD rx {bib_refdb_model.ref_rx} in db dict: {bib_refdb_model.art_id}.{bib_refdb_model.ref_local_id} {opasgenlib.text_slice(bib_refdb_model.ref_text, chr_count=40)}")
        
        if not ref.attrib.get("rx"):
            # still no rx
            if bib_entry.ref_is_book:
                bk_locator_str, match_val, whatever = known_books.getPEPBookCodeStr(bib_entry.ref_text)
                if bk_locator_str is not None:
                    ref.attrib["rx"] = bk_locator_str
                    search_str = f"//be[@id='{ref_id}']"
                    msg = f"\t\t\t...Matched Book {match_val}. {opasxmllib.xml_xpath_return_xmlstringlist(parsed_xml, search_str)[0]}"
                    log_everywhere_if(gDbg2, level="info", msg=msg)
                    
                else:
                    # see if we have info to link SE/GW etc., these are in a sense like journals
                    pep_ref = False
                    if PEPJournalData.PEPJournalData.rgxSEPat2.search(bib_entry.ref_text):
                        pep_ref = True
                        bib_entry.sourcecode = "SE"
                    elif PEPJournalData.PEPJournalData.rgxGWPat2.search(bib_entry.ref_text):
                        pep_ref = True
                        bib_entry.sourcecode = "GW"
            
            if not ref.attrib.get("rx") and bib_entry.ref_sourcecode:
                if not opasgenlib.is_empty(bib_entry.ref_pgrg):
                    try:
                        bib_pgstart, bib_pgend = bib_entry.ref_pgrg.split("-")
                    except Exception as e:
                        bib_pgstart = bib_entry.ref_pgrg
                else:
                    if bib_entry.ref_is_book:
                        bib_pgstart = 0
                    else:
                        bib_pgstart = bib_pgend = None
                
                if bib_pgstart or bib_entry.ref_is_book:
                    locator = Locator(strLocator=None,
                                      jrnlCode=bib_entry.ref_sourcecode, 
                                      jrnlVolSuffix="", 
                                      jrnlVol=bib_entry.ref_volume, 
                                      jrnlIss=None, 
                                      pgVar="A", 
                                      pgStart=bib_pgstart, 
                                      jrnlYear=bib_entry.ref_year, 
                                      localID=ref_id, 
                                      keepContext=1, 
                                      forceRoman=False, 
                                      notFatal=True, 
                                      noStartingPageException=True, 
                                      filename=artInfo.filename)
                    if locator.valid:
                        if ocd.article_exists(locator):
                            pep_ref = True
                        else:
                            pep_ref = False
                else:
                    locator = None

                if locator is None or locator.valid == 0:
                    msg = f"\t\t...Bib ID {ref_id} not enough info {bib_entry.ref_sourcecode}.{bib_entry.ref_volume}.{bib_pgstart} {bib_entry.ref_text}"
                    log_everywhere_if(verbose, level="info", msg=msg)
                elif not pep_ref:
                    pass
                else:
                    ref.attrib["rx"] = locator.articleID()
                    ref.attrib["rx_conf"] = str(0.99)
                    search_str = f"//be[@id='{ref_id}']"
                    msg = f"\t\t...Matched Journal {opasxmllib.xml_xpath_return_xmlstringlist(parsed_xml, search_str)[0]}"
                    log_everywhere_if(verbose, level="debug", msg=msg)

        return ret_val        
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
