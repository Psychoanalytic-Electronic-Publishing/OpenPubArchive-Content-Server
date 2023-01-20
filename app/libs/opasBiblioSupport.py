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

    >> ref = '<be id="B070"><a><l>Money-Kyrle</l>, R.</a> (<y>1968</y>). <t>Cognitive development.</t> <j>The International Journal of Psycho-Analysis</j>, <v>49</v>, <pp>691-698</pp>.</be>'
    >> parsed_ref = etree.fromstring(ref, parser=parser)
    >> be_journal = BiblioEntry(art_id="ANIJP-TR.007.0157A", ref_or_parsed_ref=parsed_ref)
    >> be_journal.identify_nonheuristic(ocd)
    'IJP.049.0691A'

    >> be_journal = BiblioEntry(art_id="FA.013A.0120A", ref_or_parsed_ref='<be id="B009"><a><l>Sternberg</l>, J</a> &amp; <a><l>Scott</l>, A</a> (<y>2009</y>) <t>Editorial.</t> <j>British Journal of Psychotherapy</j>, <v>25</v> (<bs>2</bs>): <pp>143-5</pp>.</be>')
    >> be_journal.identify_nonheuristic(ocd)
    'BJP.025.0143A'

    >> ref = '<be id="B0006" reftype="journal" class="mixed-citation"><a class="western"><l>Beebe</l>, B.</a>, &amp; <a class="western"> <l>Lachmann</l>, F.</a> (<y>2002</y>). <t class="article-title">Organizing principles of interaction from infant research and the lifespan prediction of attachment: Application to adult treatment</t>. <j>Journal of Infant, Child, and Adolescent Psychotherapy</j>, <v> 2</v>(<bs>4</bs>), <pp>61 - 89</pp>&#8211;. doi:<webx type="doi">10.1080/15289168.2002.10486420</webx></be>'
    >> parsed_ref = etree.fromstring(ref, parser=parser)
    >> be_journal = BiblioEntry(art_id="FA.013A.0120A", ref_or_parsed_ref=parsed_ref)
    >> rx = be_journal.identify_nonheuristic(ocd)
    'JICAP.002.0061A'
    
    
    """
    # Transitional, until I change this class to the model
    art_id: str = Field(None)
    ref_local_id: str = Field(None)
    art_year: Optional[int]              # containing article year
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
    last_update: datetime = Field(None)
    
    def __init__(self, art_id, ref_or_parsed_ref, db_bib_entry=[], verbose=False):
        # allow either string xml ref or parsed ref
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
        # self.art_year_int = 0 # artInfo.art_year_int
        
        if self.ref_rx is not None:
            self.ref_rx_sourcecode = re.search("(.*?)\.", self.rx, re.IGNORECASE).group(1)
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
                        log_everywhere_if(True, "warning", msg=f"BibEntry vol {self.volume} is neither roman nor int {e}")
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
        if journal_title in ("Ges. Schr.", ):
            book_title = journal_title
            journal_title = None

        if (book_title or self.ref_publisher) and not journal_title:
            self.ref_is_book = True
            self.ref_sourcetype = "book"
            self.sourcetitle = book_title  # book title
            bk_locator_str, match_val, whatever = known_books.getPEPBookCodeStr(self.ref_text)
            
        elif journal_title:
            self.ref_sourcetype = "journal"
            self.ref_is_book = False
            self.ref_sourcetitle = journal_title
        else:
            self.ref_sourcetype = "unknown"
            self.ref_is_book = False
            self.ref_sourcetitle = f"{journal_title} / {book_title}"

        if self.ref_is_book:
            year_of_publication = opasxmllib.xml_get_subelement_textsingleton(parsed_ref, "bpd")
            if year_of_publication == "":
                year = opasxmllib.xml_get_subelement_textsingleton(parsed_ref, "y")
                year_of_publication = opasgenlib.removeAllPunct(year) # punct_set=[',', '.', ':', ';', '(', ')', '\t', r'/', '"', "'", "[", "]"])
            if self.ref_sourcetitle is None or self.ref_sourcetitle == "":
                ## sometimes has markup
                self.source_title = book_title  # book title (bst)
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
                logger.error("Error converting year_of_publication to int: %s / %s.  (%s)" % (self.year_of_publication, self.ref_entry_xml, e))
            except Exception as e:
                logger.error("Error trying to find untagged bib year in %s (%s)" % (self.ref_entry_xml, e))
                
        else:
            self.ref_year_int = 0
            
        self.author_name_list = [etree.tostring(x, with_tail=False).decode("utf8") for x in parsed_ref.findall("a") if x is not None]
        self.ref_authors_xml = '; '.join(self.author_name_list)
        self.ref_authors_xml = self.ref_authors_xml[:2040]
        author_list = [opasxmllib.xml_elem_or_str_to_text(x) for x in parsed_ref.findall("a") if opasxmllib.xml_elem_or_str_to_text(x) is not None]  # final if x gets rid of any None entries which can rarely occur.
        self.ref_authors = '; '.join(author_list)
        self.ref_authors = self.ref_authors[:2040]
        self.ref_doi = parsed_ref.findtext("webx[@type='doi']")

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
        
        # load biblio record for this artid to see if we have the info needed
        bibs_from_db = get_ref_from_db(ocd, art_id, ref_local_id=ref_id)
        if bibs_from_db:
            biblioxml_from_db = bibs_from_db
            ret_val = self.rx = biblioxml_from_db.ref_rx
                
        if ret_val is None:
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
                        ret_val = self.rx = str(locator)
                        msg = f"\t\t...Locator extracted {self.rx}"
                        log_everywhere_if(verbose, level="debug", msg=msg)
                        
                else:
                    locator = None

                if locator is None or locator.valid == 0:
                    msg = f"\t\t...Bib ID {ref_id} not enough info {self.sourcecode}.{self.volume}.{bib_pgstart} {self.ref_text}"
                    log_everywhere_if(verbose, level="info", msg=msg)
                elif not pep_ref:
                    pass

        return ret_val

    def parse_nonxml_reference(self, ref_text, verbose=False):
        #Reusable Patterns (should not have group names)
        pass

#------------------------------------------------------------------------------------------------------
def save_ref_to_biblioxml_table(ocd, bib_entry, verbose=None):
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
          
    >>> ocd = opasCentralDBLib.opasCentralDB()
    >>> art_id="FA.013A.0120A"
    >>> ref_local_id='B009'
    >>> bib_entry = get_ref_from_db(ocd, art_id=art_id, ref_local_id=ref_local_id)
    >>> success = save_ref_to_biblioxml_table(ocd, bib_entry=bib_entry, verbose=True)
    
      
    """
    ret_val = False
    
    if bib_entry.ref_rx is None or bib_entry.ref_rxcf is None:
        # Read from the current table
        current_db_entry = get_ref_from_db(ocd,
                                        art_id=bib_entry.art_id,
                                        ref_local_id=bib_entry.ref_local_id)
        if current_db_entry is not None:
            if bib_entry.ref_rx is None:
                bib_entry.ref_rx = current_db_entry.ref_rx
                bib_entry.ref_rx_confidence = current_db_entry.ref_rx_confidence
            elif current_db_entry.ref_rx_confidence > bib_entry.ref_rx_confidence:
                bib_entry.ref_rx = current_db_entry.ref_rx
                bib_entry.ref_rx_confidence = current_db_entry.ref_rx_confidence
    
            if bib_entry.ref_rxcf is None:
                bib_entry.ref_rxcf = current_db_entry.ref_rxcf
                bib_entry.ref_rxcf_confidence = current_db_entry.ref_rxcf_confidence 
            elif current_db_entry.ref_rxcf_confidence > bib_entry.ref_rxcf_confidence:
                bib_entry.ref_rxcf = current_db_entry.ref_rxcf
                bib_entry.ref_rxcf_confidence = current_db_entry.ref_rxcf_confidence

    if bib_entry.ref_rx_confidence is None:
        bib_entry.ref_rx_confidence = 0
        
    if bib_entry.ref_rxcf_confidence is None:
        bib_entry.ref_rxcf_confidence = 0

    insert_if_not_exists = r"""REPLACE
                               INTO api_biblioxml (
                                    art_id,
                                    ref_local_id,
                                    art_year,
                                    ref_rx,
                                    ref_rx_confidence,
                                    ref_sourcecode, 
                                    ref_rxcf, 
                                    ref_rxcf_confidence,
                                    ref_authors, 
                                    ref_authors_xml, 
                                    ref_title, 
                                    ref_sourcetype, 
                                    ref_sourcetitle, 
                                    ref_pgrg, 
                                    ref_year, 
                                    ref_year_int, 
                                    ref_volume, 
                                    ref_publisher,
                                    ref_doi,
                                    ref_xml,
                                    ref_text
                                    )
                                values (%(art_id)s,
                                        %(ref_local_id)s,
                                        %(art_year)s,
                                        %(ref_rx)s,
                                        %(ref_rx_confidence)s,
                                        %(ref_sourcecode)s,
                                        %(ref_rxcf)s,
                                        %(ref_rxcf_confidence)s,
                                        %(ref_authors)s,
                                        %(ref_authors_xml)s,
                                        %(ref_title)s,
                                        %(ref_sourcetype)s,
                                        %(ref_sourcetitle)s,
                                        %(ref_pgrg)s,
                                        %(ref_year)s,
                                        %(ref_year_int)s,
                                        %(ref_volume)s,
                                        %(ref_publisher)s,
                                        %(ref_doi)s,
                                        %(ref_xml)s,
                                        %(ref_text)s
                                        );
                            """
    query_param_dict = bib_entry.__dict__
    # need to remove lists, even if they are not used.
    #del query_param_dict["author_list"]
    #del query_param_dict["author_name_list"]
    #del query_param_dict["ref"]

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

#------------------------------------------------------------------------------------------------------
def get_ref_from_db(ocd, art_id, ref_local_id, verbose=None):
    """
    Return a reference model from the api_biblioxml table in opascentral
    
    >>> ocd = opasCentralDBLib.opasCentralDB()
    >>> ref=get_ref_from_db(ocd, art_id="FA.013A.0120A", ref_local_id='B009')
    >>> ref.ref_rx
    'BJP.025.0143A'
    
    """
    ret_val = None

    select = f"""SELECT * from api_biblioxml
                 WHERE art_id = '{art_id}'
                 AND ref_local_id = '{ref_local_id}'
                 """

    results = ocd.get_select_as_list_of_models(select, model=models.Biblioxml)
    if results:
        ret_val = results[0]

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
