#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
# Disable many annoying pylint messages, warning me about variable naming for example.
# yes, in my Solr code I'm caught between two worlds of snake_case and camelCase.

""" 
OPAS - opasSolrLoadSupport  

"""
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2021.0416.1" 

import sys
sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')

import os
from datetime import datetime
import time
import string
import re
import urllib.request, urllib.parse, urllib.error
import random

import lxml
from lxml import etree
parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=False)
import html

# import pymysql
import mysql.connector

import localsecrets
# import config
import opasConfig
# import configLib.opasCoreConfig
import opasGenSupportLib as opasgenlib
import opasXMLHelper as opasxmllib
import loaderConfig

import logging
logger = logging.getLogger(__name__)

def read_stopwords(): 
    with open(localsecrets.HIGHLIGHT_STOP_WORDS_FILE) as f:
        stopWordList = f.read().splitlines()
    
    stopPattern = "<[ib]>[A-Z]</[ib]>"
    for n in stopWordList:
        stopPattern += f"|<[ib]>{n}</[ib]>"

    ret_val = re.compile(stopPattern, re.IGNORECASE)
    return ret_val

# Module Globals
rc_stopword_match = read_stopwords() # returns compile re for matching stopwords 

#------------------------------------------------------------------------------------------------------------
#  Support functions
#------------------------------------------------------------------------------------------------------------
def non_empty_string(strval): 
    try:
        return strval if strval != "" else None
    except Exception as e:
        return None  # note if type is not string, it returns None

def strip_tags(value, compiled_tag_pattern):
    """
    Strip tags matching the compiled_tag_pattern.
    
    """
    ret_val = value
    m = compiled_tag_pattern.match(value)
    if m:
        ret_val = m.group("word")
        if ret_val == None:
            ret_val = "pagebreak"
        ret_val = ret_val.translate(str.maketrans('','', '!"#$%&\'()*+,./:;<=>?@[\\]^_`{|}~'))

    return ret_val

def remove_values_from_terms_highlighted_list(the_list, remove_stop_words=True, start_tag_pattern = "<(i|b|bi|bui|fi|impx[^>]*?)>", end_tag_pattern="</(i|b|bi|bui|impx|fi)>"):
    """
    Using the list of stop words read in at initialization, remove these from the words used for highlighted lists.
    
    >> remove_values_from_terms_highlighted_list(["<i>not</i>","<i>is</i>","<i>and</i>", "<i>she</i>", "<i>The Interpretation of Dreams</i>", "<i>will</i>", "<i>I</i>", "<i>be</i>" ])
    ['The Interpretation of Dreams']
    """
    stripPattern = f".*<pb>.*|({start_tag_pattern}[\s\n\t]*)+(?P<word>[^<]+?)[\s\n]*({end_tag_pattern})+"
    cStripPattern = re.compile(stripPattern, re.IGNORECASE)
    # passing the compiled pattern saves from recompiling for every value in function
    if remove_stop_words:
        return [strip_tags(value, compiled_tag_pattern = cStripPattern) for value in the_list if not rc_stopword_match.match(value)]
    else:
        return [strip_tags(value, compiled_tag_pattern = cStripPattern) for value in the_list]


class BiblioEntry(object):
    """
    An entry from a documents bibliography.
    
    Used to populate the MySQL table api_biblioxml for statistical gathering
       and the Solr core pepwebrefs for searching in special cases.
    
    """
    def __init__(self, artInfo, ref):
        self.ref_entry_xml = etree.tostring(ref, with_tail=False)
        if self.ref_entry_xml is not None:
            self.ref_entry_xml = self.ref_entry_xml.decode("utf8") # convert from bytes
        self.ref_entry_text = opasxmllib.xml_elem_or_str_to_text(ref)
        self.art_id = artInfo.art_id
        self.art_year_int = artInfo.art_year_int
        self.ref_local_id= opasxmllib.xml_get_element_attr(ref, "id")
        self.ref_id = artInfo.art_id + "." + self.ref_local_id
        self.ref_title = opasxmllib.xml_get_subelement_textsingleton(ref, "t")
        self.ref_title = self.ref_title[:1023]
        self.pgrg = opasxmllib.xml_get_subelement_textsingleton(ref, "pp")
        self.pgrg = opasgenlib.first_item_grabber(self.pgrg, re_separator_ptn=";|,", def_return=self.pgrg)
        self.pgrg = self.pgrg[:23]
        self.rx = opasxmllib.xml_get_element_attr(ref, "rx", default_return=None)
        self.rxcf = opasxmllib.xml_get_element_attr(ref, "rxcf", default_return=None) # related rx
        if self.rx is not None:
            self.rx_sourcecode = re.search("(.*?)\.", self.rx, re.IGNORECASE).group(1)
        else:
            self.rx_sourcecode = None
        self.volume = opasxmllib.xml_get_subelement_textsingleton(ref, "v")
        self.volume = self.volume[:23]
        self.source_title = opasxmllib.xml_get_subelement_textsingleton(ref, "j")
        self.publishers = opasxmllib.xml_get_subelement_textsingleton(ref, "bp")
        self.publishers = self.publishers[:254]
        if self.publishers != "":
            self.source_type = "book"
        else:
            self.source_type = "journal"

        if self.source_type == "book":
            self.year_of_publication = opasxmllib.xml_get_subelement_textsingleton(ref, "bpd")
            if self.year_of_publication == "":
                self.year_of_publication = opasxmllib.xml_get_subelement_textsingleton(ref, "y")
            if self.source_title is None or self.source_title == "":
                # sometimes has markup
                self.source_title = opasxmllib.xml_get_direct_subnode_textsingleton(ref, "bst")  # book title
        else:
            self.year_of_publication = opasxmllib.xml_get_subelement_textsingleton(ref, "y")
         
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
                logger.warning("no match %s/%s/%s" % (self.year_of_publication, ref, e))
            
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
            self.year_int = "Null"
            
        self.author_name_list = [etree.tostring(x, with_tail=False).decode("utf8") for x in ref.findall("a") if x is not None]
        self.authors_xml = '; '.join(self.author_name_list)
        self.authors_xml = self.authors_xml[:2040]
        self.author_list = [opasxmllib.xml_elem_or_str_to_text(x) for x in ref.findall("a") if opasxmllib.xml_elem_or_str_to_text(x) is not None]  # final if x gets rid of any None entries which can rarely occur.
        self.author_list_str = '; '.join(self.author_list)
        self.author_list_str = self.author_list_str[:2040]
#------------------------------------------------------------------------------------------------------
class ArticleInfo(object):
    """
    An entry from a documents metadata.
    
    Used to populate the MySQL table api_articles for relational type querying
       and the Solr core pepwebdocs for full-text searching (and the majority of
       client searches.

    """
    def __init__(self, sourceinfodb_data, pepxml, art_id, logger, verbose=None):
        # let's just double check artid!
        self.art_id = None
        self.art_id_from_filename = art_id # file name will always already be uppercase (from caller)
        self.bk_subdoc = None
        self.bk_seriestoc = None
        self.verbose = verbose

        # Just init these.  Creator will set based on filename
        self.file_classification = None
        self.file_size = 0  
        self.filedatetime = ""
        self.filename = ""

        # now, the rest of the variables we can set from the data
        self.processed_datetime = datetime.utcfromtimestamp(time.time()).strftime(opasConfig.TIME_FORMAT_STR)
        try:
            self.art_id = opasxmllib.xml_xpath_return_textsingleton(pepxml, "//artinfo/@id", None)
            if self.art_id is None:
                self.art_id = self.art_id_from_filename
            else:
                # just to watch for xml keying or naming errors
                if self.art_id_from_filename != self.art_id:
                    logger.warning("File name ID tagged and artID disagree.  %s vs %s", self.art_id, self.art_id_from_filename)
                    self.art_id = self.art_id_from_filename
                    
            # make sure it's uppercase
            self.art_id = self.art_id.upper()
                
        except Exception as err:
            logger.error("Issue reading file's article id. (%s)", err)

        # Containing Article data
        #<!-- Common fields -->
        #<!-- Article front matter fields -->
        #---------------------------------------------
        artinfo_xml = pepxml.xpath("//artinfo")[0] # grab full artinfo node, so it can be returned in XML easily.
        self.artinfo_xml = etree.tostring(artinfo_xml).decode("utf8")
        self.src_code = pepxml.xpath("//artinfo/@j")[0]
        self.src_code = self.src_code.upper()  # 20191115 - To make sure this is always uppercase
        self.embargo = pepxml.xpath("//artinfo/@embargo")
        self.embargotype = pepxml.xpath("//artinfo/@embargotype")
        
        if 1: # vol info (just if'd for folding purposes)
            vol_actual = opasxmllib.xml_xpath_return_textsingleton(pepxml, '//artinfo/artvol/@actual', default_return=None)
            self.art_vol_str = opasxmllib.xml_xpath_return_textsingleton(pepxml, '//artinfo/artvol/node()', default_return=None)
            m = re.match("(\d+)([A-Z]*)", self.art_vol_str)
            if m is None:
                logger.error(f"ArticleInfoError: Bad Vol # in element content: {self.art_vol_str}")
                m = re.match("(\d+)([A-z\-\s]*)", vol_actual)
                if m is not None:
                    self.art_vol_int = m.group(1)
                    logger.error(f"ArticleInfoError: Recovered Vol # from actual attr: {self.art_vol_int}")
                else:
                    raise ValueError("ArticleInfoError: Severe Error in art_vol")
            else:
                self.art_vol_int = m.group(1)
                if len(m.groups()) == 2:
                    art_vol_suffix = m.group(2)
    
            # now convert to int
            try:
                self.art_vol_int = int(self.art_vol_int)
            except ValueError:
                logger.warning(f"Can't convert art_vol to int: {self.art_vol_int} Error: {e}")
                art_vol_suffix = self.art_vol_int[-1]
                art_vol_ints = re.findall(r'\d+', self.art_vol_str)
                if len(art_vol_ints) >= 1:
                    self.art_vol_int = art_vol_ints[1]
                    self.art_vol_int = int(self.art_vol_int)
            except Exception as e:
                logger.warning(f"Can't convert art_vol to int: {self.art_vol_int} Error: {e}")
    
            if vol_actual is not None:
                self.art_vol_str = vol_actual
                  
        try: #  lookup source in db
            if self.src_code in ["ZBK", "IPL", "NLP"]:
                self.src_prodkey = pepsrccode = f"{self.src_code}%03d" % self.art_vol_int
                self.src_type = "book"
            else:
                self.src_prodkey = pepsrccode = f"{self.src_code}"

            self.src_title_abbr = sourceinfodb_data[pepsrccode].get("sourcetitleabbr", None)
            self.src_title_full = sourceinfodb_data[pepsrccode].get("sourcetitlefull", None)
            self.src_embargo = sourceinfodb_data[pepsrccode].get("wall", None)
            if self.src_code in ["GW", "SE"]:
                self.src_type = "book"
            else:
                self.src_type = sourceinfodb_data[pepsrccode].get("product_type", None)  # journal, book, video...
                
        except KeyError as err:
            self.src_title_abbr = None
            self.src_title_full = None
            self.src_type = "book"
            self.src_embargo = None
            logger.error("ArticleInfoError: Source %s not found in source info db.  Assumed to be an offsite book.  Or you can add to the api_productbase table in the RDS/MySQL DB", self.src_code)
        except Exception as err:
            logger.error("ArticleInfoError: Problem with this files source info. File skipped. (%s)", err)
            #processingErrorCount += 1
            return
            
        self.art_issue = opasxmllib.xml_xpath_return_textsingleton(pepxml, '//artinfo/artiss/node()', default_return=None)
        self.art_issue_title = opasxmllib.xml_xpath_return_textsingleton(pepxml, '//artinfo/artissinfo/isstitle/node()', default_return=None)
        # special sequential numbering for issues used by journals like fa (we code it simply as artnbr in xml)
        self.art_issue_seqnbr = opasxmllib.xml_xpath_return_textsingleton(pepxml, '//artinfo/artnbr/node()', default_return=None)
        
        self.art_year_str = opasxmllib.xml_xpath_return_textsingleton(pepxml, '//artinfo/artyear/node()', default_return=None)
        m = re.match("(?P<yearint>[0-9]{4,4})(?P<yearsuffix>[a-zA-Z])?(\s*\-\s*)?((?P<year2int>[0-9]{4,4})(?P<year2suffix>[a-zA-Z])?)?", self.art_year_str)
        if m is not None:
            self.art_year = m.group("yearint")
            self.art_year_int = int(m.group("yearint"))
        else:
            try:
                art_year_for_int = re.sub("[^0-9]", "", self.art_year)
                self.art_year_int = int(art_year_for_int)
            except ValueError as err:
                logger.error("Error converting art_year to int: %s", self.art_year)
                self.art_year_int = 0


        artInfoNode = pepxml.xpath('//artinfo')[0]
        self.art_type = opasxmllib.xml_get_element_attr(artInfoNode, "arttype", default_return=None)
        self.art_vol_title = opasxmllib.xml_xpath_return_textsingleton(pepxml, '//artinfo/artvolinfo/voltitle/node()', default_return=None)
        if self.art_vol_title is None:
            # try attribute for value (lower priority than element above)
            self.art_vol_title = opasxmllib.xml_get_element_attr(artInfoNode, "voltitle", default_return=None)

        # m = re.match("(?P<volint>[0-9]+)(?P<volsuffix>[a-zA-Z])", self.art_vol)
        m = re.match("(?P<volint>[0-9]+)(?P<volsuffix>[a-zA-Z])?(\s*\-\s*)?((?P<vol2int>[0-9]+)(?P<vol2suffix>[a-zA-Z])?)?", str(self.art_vol_str))
        if m is not None:
            self.art_vol_suffix = m.group("volsuffix")
            # self.art_vol = m.group("volint")
        else:
            self.art_vol_suffix = None
            
        if self.verbose and self.art_vol_title is not None:
            print (f"   ...Volume title: {self.art_vol_title}")
    
        if self.verbose and self.art_issue_title is not None:
            print (f"   ...Issue title: {self.art_issue_title}")
            
        self.art_doi = opasxmllib.xml_get_element_attr(artInfoNode, "doi", default_return=None) 
        self.art_issn = opasxmllib.xml_get_element_attr(artInfoNode, "ISSN", default_return=None) 
        self.art_isbn = opasxmllib.xml_get_element_attr(artInfoNode, "ISBN", default_return=None) 
        self.art_orig_rx = opasxmllib.xml_get_element_attr(artInfoNode, "origrx", default_return=None) 
        self.start_sectname = opasxmllib.xml_get_element_attr(artInfoNode, "newsecnm", default_return=None)
        if self.start_sectname is None:
            #  look in newer, tagged, data
            self.start_sectname = opasxmllib.xml_xpath_return_textsingleton(pepxml, '//artsectinfo/secttitle/node()', default_return=None)
        
        self.art_pgrg = opasxmllib.xml_get_subelement_textsingleton(artInfoNode, "artpgrg", default_return=None)  # note: getSingleSubnodeText(pepxml, "artpgrg")
        self.art_pgstart, self.art_pgend = opasgenlib.pgrg_splitter(self.art_pgrg)

        try:
            self.art_pgcount = int(pepxml.xpath("count(//pb)")) # 20200506
        except Exception as e:
            self.art_pgcount = 0
            
        self.art_kwds = opasxmllib.xml_xpath_return_textsingleton(pepxml, "//artinfo/artkwds/node()", None)
        
        # ************* new counts! 20210413 *******************************************
        try:
            if self.art_kwds is not None:
                self.art_kwds_count = self.art_kwds.count(",") + 1 # 20210413
            else:
                self.art_kwds_count = 0
        except Exception as e:
            self.art_kwds_count = 0

        # art_abs_count
        try:
            self.art_abs_count = int(pepxml.xpath("count(//abs)"))
        except Exception as e:
            self.art_abs_count  = 0

        # art_ftns_count_count 
        try:
            self.art_ftns_count = int(pepxml.xpath("count(//ftn)")) # 20210413
        except Exception as e:
            self.art_ftns_count = 0

        # art_paras_count
        try:
            self.art_paras_count = int(pepxml.xpath("count(//p)")) # 20210413
        except Exception as e:
            self.art_paras_count = 0

        # art_headings_count
        try:
            self.art_headings_count = int(pepxml.xpath("count(//*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6])")) # 20210413
        except Exception as e:
            self.art_headings_count = 0

        # art_terms_count
        try:
            self.art_terms_count = int(pepxml.xpath('count(//impx[@type="TERM2"])')) # 20210413
        except Exception as e:
            self.art_terms_count = 0

        # art_dreams_count
        try:
            self.art_dreams_count = int(pepxml.xpath("count(//dream)")) # 20210413
        except Exception as e:
            self.art_dreams_count = 0

        # art_dialogs_count
        try:
            self.art_dialogs_count = int(pepxml.xpath("count(//dialog)")) # 20210413
        except Exception as e:
            self.art_dialogs_count = 0

        # art_notes_count
        try:
            self.art_notes_count = int(pepxml.xpath("count(//note)")) # 20210413
        except Exception as e:
            self.art_notes_count = 0

        # art_poems_count
        try:
            self.art_poems_count = int(pepxml.xpath("count(//poem)")) # 20210413
        except Exception as e:
            self.art_poems_count = 0
            
        # art_citations_count
        try:
            self.art_citations_count = int(pepxml.xpath("count(//bx)")) # 20210413
        except Exception as e:
            self.art_citations_count = 0
        
        # art_quotes_count
        try:
            self.art_quotes_count = int(pepxml.xpath("count(//quote)")) # 20210413
        except Exception as e:
            self.art_quotes_count = 0

        try:
            self.art_tblcount = int(pepxml.xpath("count(//tbl)")) # 20200922
        except Exception as e:
            self.art_tblcount = 0

        try:
            self.art_figcount = int(pepxml.xpath("count(//figure)")) # 20200922
        except Exception as e:
            self.art_figcount = 0
            
        # art_chars_count
        try:
            self.art_chars_count = int(pepxml.xpath("string-length(normalize-space(//node()))"))
        except Exception as e:
            self.art_chars_count  = 0

        try:
            self.art_chars_no_spaces_count = int(pepxml.xpath("string-length(translate(normalize-space(//node()),' ',''))"))
        except Exception as e:
            self.art_chars_no_spaces_count  = 0

        try:
            self.art_words_count = self.art_chars_count - self.art_chars_no_spaces_count + 1
        except Exception as e:
            self.art_words_count  = 0

        # ************* end of counts! 20210413 *******************************************

        self.art_graphic_list = pepxml.xpath('//graphic//@source')
        #if self.art_graphic_list != []:
            #print (f"Graphics found: {self.art_graphic_list}")
        
        if self.art_pgstart is not None:
            self.art_pgstart_prefix, self.art_pgstart, self.pgstart_suffix = opasgenlib.pgnum_splitter(self.art_pgstart)
        else:
            self.art_pgstart_prefix, self.art_pgstart, self.pgstart_suffix = (None, None, None)
            
        if self.art_pgend is not None:
            self.pgend_prefix, self.art_pgend, self.pgend_suffix = opasgenlib.pgnum_splitter(self.art_pgend)
        else:
            self.pgend_prefix, self.art_pgend, self.pgend_suffix = (None, None, None)

        self.art_title = opasxmllib.xml_get_subelement_textsingleton(artInfoNode, "arttitle", skip_tags=["ftnx"])
        if self.art_title == "-": # weird title in ANIJP-CHI
            self.art_title = ""

        self.art_subtitle = opasxmllib.xml_get_subelement_textsingleton(artInfoNode, 'artsub')
        if self.art_subtitle == "":
            pass
        elif self.art_subtitle is None:
            self.art_subtitle = ""
        else:
            #self.artSubtitle = ''.join(etree.fromstring(self.artSubtitle).itertext())
            if self.art_title != "":
                self.art_subtitle = ": " + self.art_subtitle
                self.art_title = self.art_title + self.art_subtitle
            else:
                self.art_title = self.art_subtitle
                self.art_subtitle = ""
                
        self.art_lang = pepxml.xpath('//pepkbd3/@lang')
        
        if self.art_lang == []:
            self.art_lang = [opasConfig.DEFAULT_DATA_LANGUAGE_ENCODING]

        try:
            self.art_lang = self.art_lang[0].lower()
        except:
            logger.warning(f"art_lang value error: {self.art_lang}")
            self.art_lang = opasConfig.DEFAULT_DATA_LANGUAGE_ENCODING
        
        self.author_xml_list = pepxml.xpath('//artinfo/artauth/aut')
        self.author_xml = opasxmllib.xml_xpath_return_xmlsingleton(pepxml, '//artinfo/artauth')
        self.authors_bibliographic, self.author_list, self.authors_bibliographic_list = opasxmllib.authors_citation_from_xmlstr(self.author_xml, listed=True)
        self.art_auth_citation = self.authors_bibliographic
        self.art_auth_citation_list = self.authors_bibliographic_list
        # ToDo: I think I should add an author ID to bib aut too.  But that will have
        #  to wait until later.
        # TODO: fix PEP2XML--in cases like AJRPP.004.0273A it put Anonymous in the authindexid.
        self.art_author_id_list = opasxmllib.xml_xpath_return_textlist(pepxml, '//artinfo/artauth/aut[@listed="true"]/@authindexid')
        self.art_authors_count = len(self.author_list)
        if self.art_author_id_list == []: # no authindexid
            logger.warning("This document %s does not have an author list; may be missing authindexids" % art_id)
            self.art_author_id_list = self.author_list

        self.art_author_ids_str = ", ".join(self.art_author_id_list)
        self.art_auth_mast, self.art_auth_mast_list = opasxmllib.author_mast_from_xmlstr(self.author_xml, listed=True)
        self.art_auth_mast_unlisted_str, self.art_auth_mast_unlisted_list = opasxmllib.author_mast_from_xmlstr(self.author_xml, listed=False)
        self.art_auth_count = len(self.author_xml_list)
        self.art_author_lastnames = opasxmllib.xml_xpath_return_textlist(pepxml, '//artinfo/artauth/aut[@listed="true"]/nlast')
        
        self.art_all_authors = self.art_auth_mast + " (" + self.art_auth_mast_unlisted_str + ")"

        self.issue_id_str = f"<issue_id><src>{self.src_code}</src><yr>{self.art_year}</yr><vol>{self.art_vol_str}</vol><iss>{self.art_issue}</iss></issue_id>"
        try:
            if self.src_title_full is not None:
                safe_src_title_full = html.escape(self.src_title_full)
            else:
                logger.warning(f"Source title full is None")
                safe_src_title_full = ''

        except Exception as e:
            logger.error(f"ArticleInfoError: Source title escape error: {e}")
            safe_src_title_full = ''
            
        try:
            if self.art_title is not None:
                safe_art_title = html.escape(self.art_title)
            else:
                logger.warning(f"Art title is None")
                safe_art_title = ''

        except Exception as e:
            logger.error(f"ArticleInfoError: Art title escape error: {e}")
            safe_art_title = ''

        try:
            if self.art_pgrg is not None:
                safe_art_pgrg = html.escape(self.art_pgrg)
            else:
                logger.warning(f"Art title is None")
                safe_art_pgrg = ''

        except Exception as e:
            logger.error(f"ArticleInfoError: Art PgRg escape error: {e}")
            safe_art_pgrg = ''
            
        # Usually we put the abbreviated title here, but that won't always work here.
        self.art_citeas_xml = u"""<p class="citeas"><span class="authors">%s</span> (<span class="year">%s</span>) <span class="title">%s</span>. <span class="sourcetitle">%s</span> <span class="vol">%s</span>:<span class="pgrg">%s</span></p>""" \
            %                   (self.authors_bibliographic,
                                 self.art_year,
                                 safe_art_title,
                                 safe_src_title_full,
                                 self.art_vol_int,
                                 safe_art_pgrg
                                )
        
        self.art_citeas_text = opasxmllib.xml_elem_or_str_to_text(self.art_citeas_xml)
        art_qual_node = pepxml.xpath("//artinfo/artqual")
        if art_qual_node != []:
            self.art_qual = opasxmllib.xml_get_element_attr(art_qual_node[0], "rx", default_return=None)
        else:
            self.art_qual = pepxml.xpath("//artbkinfo/@extract")
            if self.art_qual == []:
                self.art_qual = None 

        # will be None if not a book extract
        # self.art_qual = None
        if self.art_qual is not None:
            if isinstance(self.art_qual, list):
                self.art_qual = str(self.art_qual[0])
                
            if self.art_qual != self.art_id:
                self.bk_subdoc = True
            else:
                self.bk_subdoc = False
        else:
            self.bk_subdoc = False           

        refs = pepxml.xpath("/pepkbd3//be")
        self.bib_authors = []
        self.bib_rx = []
        self.bib_title = []
        self.bib_journaltitle = []
        
        for x in refs:
            try:
                if x.attrib["rx"] is not None:
                    self.bib_rx.append(x.attrib["rx"])
            except:
                pass
            journal = x.find("j")
            if journal is not None:
                journal_lc = opasxmllib.xml_elem_or_str_to_text(journal).lower()
                journal_lc = journal_lc.translate(str.maketrans('', '', string.punctuation))
                self.bib_journaltitle.append(journal_lc)

            title = x.find("t")
            # bib article titles for faceting, get rid of punctuation variations
            if title is not None:
                bib_title = opasxmllib.xml_elem_or_str_to_text(title)
                bib_title = bib_title.lower()
                bib_title = bib_title.translate(str.maketrans('', '', string.punctuation))
                self.bib_title.append(opasxmllib.xml_elem_or_str_to_text(title))

            title = x.find("bst")
            # bib source titles for faceting, get rid of punctuation variations
            # cumulate these together with article title
            if title is not None:
                bib_title = opasxmllib.xml_elem_or_str_to_text(title)
                bib_title = bib_title.lower()
                bib_title = bib_title.translate(str.maketrans('', '', string.punctuation))
                self.bib_title.append(bib_title)

            auths = x.findall("a")
            for y in auths:
                if opasxmllib.xml_elem_or_str_to_text(x) is not None:
                    self.bib_authors.append(opasxmllib.xml_elem_or_str_to_text(y))
        
        self.ref_count = len(refs )
        # clear it, we aren't saving it.
        refs  = None
        
        self.bk_info_xml = opasxmllib.xml_xpath_return_xmlsingleton(pepxml, "/pepkbd3//artbkinfo") # all book info in instance
        # break it down a bit for the database
        self.main_toc_id = opasxmllib.xml_xpath_return_textsingleton(pepxml, "/pepkbd3//artbkinfo/@extract", None)
        self.bk_title = opasxmllib.xml_xpath_return_textsingleton(pepxml, "/pepkbd3//bktitle", None)
        self.bk_publisher = opasxmllib.xml_xpath_return_textsingleton(pepxml, "/pepkbd3//bkpubandloc", None)
        self.bk_seriestoc = opasxmllib.xml_xpath_return_textsingleton(pepxml, "/pepkbd3//artbkinfo/@seriestoc", None)
        self.bk_next_id = opasxmllib.xml_xpath_return_textsingleton(pepxml, "//artbkinfo/@next", None)
        # hard code special cases SE/GW if they are not covered by the instances
        if self.bk_seriestoc is None:
            if self.src_code == "SE":
                self.bk_seriestoc = "SE.000.0000A"
            if self.src_code == "GW":
                self.bk_seriestoc = "GW.000.0000A"
#------------------------------------------------------------------------------------------------------
def get_file_dates_solr(solrcore, filename=None):
    """
    Fetch the article dates
    """
    ret_val = {}
    max_rows = 1000000

    basename = os.path.basename(filename)

    # these legal file name chars are special chars to Solr, so escape them!
    b_escaped = basename.translate(str.maketrans({"(":  r"\(", 
                                                  ")":  r"\)", 
                                                  "-":  r"\-", 
                                                  ":":  r"\:", 
                                                  }))    

    getFileInfoSOLR = f'art_level:1 && file_name:"{b_escaped}"'

    try:
        results = solrcore.search(getFileInfoSOLR, fl="art_id, file_name, file_last_modified, timestamp", rows=max_rows)
    except Exception as e:
        msg = f"FileDatesError: Solr Query: {e}"
        logger.error(msg)
        # let me know whatever the logging is!
        if opasConfig.LOCAL_TRACE: print (msg)
    else:
        if results.hits > 0:
            ret_val = results.docs
        else:
            ret_val = {}

    return ret_val
#------------------------------------------------------------------------------------------------------
def process_article_for_glossary_core(pepxml, artInfo, solr_gloss, fileXMLContents, verbose=None):
    """
    Process the special PEP Glossary documents.  These are linked to terms in the document
       as popups.
    """
    ret_val = False
    glossary_groups = pepxml.xpath("/pepkbd3//dictentrygrp")  
    group_count = len(glossary_groups)
    msg = f"   ...Processing XML for Glossary Core. File has {group_count} groups."
    logger.info(msg)
    if verbose:
        print (msg)

    # processedFilesCount += 1

    all_dict_entries = []
    for glossary_group in glossary_groups:
        glossary_group_xml = etree.tostring(glossary_group, with_tail=False)
        glossary_group_id = opasxmllib.xml_get_element_attr(glossary_group, "id")
        glossary_group_term = opasxmllib.xml_get_subelement_textsingleton(glossary_group, "term")
        glossary_group_also = opasxmllib.xml_get_subelement_xmlsingleton(glossary_group, "dictalso")
        if glossary_group_also == "":
            glossary_group_also = None
        logger.info("Processing Term: %s" % glossary_group_term)
        # count_terms += 1
        dict_entries = glossary_group.xpath("dictentry")  
        group_term_count = len(dict_entries)
        counter = 0
        for dict_entry in dict_entries:
            counter += 1
            this_dict_entry = {}
            dict_entry_id = glossary_group_id + ".{:03d}".format(counter)
            dict_entry_term = opasxmllib.xml_get_subelement_textsingleton(dict_entry, "term")
            if dict_entry_term == "":
                dict_entry_term = glossary_group_term
            dict_entry_term_type = dict_entry.xpath("term/@type")  
            if dict_entry_term_type != []:
                dict_entry_term_type = dict_entry_term_type[0]
            else:
                dict_entry_term_type = "term"
            
            dict_entry_src = opasxmllib.xml_get_subelement_textsingleton(dict_entry, "src")
            dict_entry_also = opasxmllib.xml_get_subelement_xmlsingleton(dict_entry, "dictalso")
            if dict_entry_also == "":
                dict_entry_also = None
            dict_entry_def = opasxmllib.xml_get_subelement_xmlsingleton(dict_entry, "def")
            dict_entry_def_rest = opasxmllib.xml_get_subelement_xmlsingleton(dict_entry, "defrest")
            this_dict_entry = {
                "term_id"             : dict_entry_id,
                "group_id"            : glossary_group_id,
                "art_id"              : artInfo.art_id,
                "term"                : dict_entry_term,
                "term_type"           : dict_entry_term_type,
                "term_source"         : dict_entry_src,
                "term_also"           : dict_entry_also,
                "term_def_xml"        : dict_entry_def,
                "term_def_rest_xml"   : dict_entry_def_rest,
                "group_name"          : glossary_group_term,
                "group_also"          : glossary_group_also,
                "group_term_count"    : group_term_count,
                "text"                : str(glossary_group_xml, "utf8"),
                "file_name"           : artInfo.filename,
                "timestamp"           : artInfo.processed_datetime,
                "file_last_modified"  : artInfo.filedatetime
            }
            all_dict_entries.append(this_dict_entry)

    # We collected all the dictentries for the group.  Now lets save the whole shebang
    try:
        response_update = solr_gloss.add(all_dict_entries)  # lets hold off on the , _commit=True)

        if not re.search('"status">0</int>', response_update):
            logger.info(response_update)
        ret_val = True

    except Exception as err:
        logger.error("GlossaryError: Solr exception %s", err)

    return ret_val    
#------------------------------------------------------------------------------------------------------
def process_article_for_doc_core(pepxml, artInfo, solrcon, file_xml_contents, include_paras=False, verbose=None):
    """
    Extract and load data for the full-text core.  Whereas in the Refs core each
      Solr document is a reference, here each Solr document is a PEP Article.

      This core contains bib entries too, but not subfields.

      TODO: Originally, this core supported each bibliography record in its own
            json formatted structure, saved in a single field.  However, when
            the code was switched from PySolr to Solrpy this had to be removed,
            since Solrpy prohibits this for some reason.  Need to raise this
            as a case on the issues board for Solrpy.

    """
    ret_val = False
    msg = f"   ...Processing XML for Docs Core."
    logger.info(msg)
    if verbose:
        print (msg)

    art_lang = pepxml.xpath('//@lang')
    if art_lang == []:
        art_lang = ['en']
    
    body_xml = opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//body", default_return=None)
    appxs_xml = opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//appxs", default_return=None)

    # see if this is an offsite article
    if artInfo.file_classification == opasConfig.DOCUMENT_ACCESS_OFFSITE:
        # certain fields should not be stored in returnable areas.  So full-text searchable special field for that.
        offsite_contents = True
        offsite_ref =  """<p>This article or book is available online on a non-PEP website. 
                            Click <a href="//www.doi.org/%s" target="_blank">here</a> to open that website 
                            in another window or tab.
                            </p>
                        """ % urllib.parse.quote(artInfo.art_doi)
        summaries_xml = f"""<abs>
                            {offsite_ref}
                            </abs>
                         """
        excerpt = excerpt_xml = abstracts_xml = summaries_xml
    else:
        offsite_contents = False
        summaries_xml = opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//summaries", default_return=None)
        abstracts_xml = opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//abs", default_return=None)
        # multiple data fields, not needed, search children instead, which allows search by para
        excerpt = None
        excerpt_xml = None
        if artInfo.art_type == opasConfig.ARTINFO_ARTTYPE_TOC_INSTANCE: # "TOC"
            # put the whole thing in the abstract!  Requires some extra processing though
            #heading = opasxmllib.get_running_head( source_title=artInfo.src_title_abbr,
                                                   #pub_year=artInfo.art_year,
                                                   #vol=artInfo.art_vol,
                                                   #issue=artInfo.art_issue,
                                                   #pgrg=artInfo.art_pgrg,
                                                   #ret_format="HTML"
                                                   #)
            #pepxml.remove(pepxml.find('artinfo'))
            #pepxml.remove(pepxml.find('meta'))
            excerpt_xml = pepxml
            excerpt = opasxmllib.xml_str_to_html(excerpt_xml, transformer_name=opasConfig.TRANSFORMER_XMLTOHTML_EXCERPT)
            # excerpt = re.sub("\[\[RunningHead\]\]", f"{heading}", excerpt, count=1)
            
        else:
            # copy abstract or summary to excerpt, if not there, then generate it.
            # this is so that an app can rely on excerpt to have the abstract or excerpt (or summary)
            # TODO: later consider we could just put the excerpt in abstract instead, and make abstract always HTML.
            #       but for now, I like to be able to distinguish an original abstract from a generated one.
            if abstracts_xml is not None:
                excerpt_xml = abstracts_xml[0]
            elif summaries_xml is not None:
                excerpt_xml = summaries_xml[0]
            else:
                excerpt_xml = opasxmllib.get_first_page_excerpt_from_doc_root(pepxml)

            excerpt = opasxmllib.xml_str_to_html(excerpt_xml, document_id=artInfo.art_id)
                
    excerpt_xml = opasxmllib.xml_elem_or_str_to_xmlstring(excerpt_xml, None)
    
    # include_paras is now False by default...only include for special source codes.
    # this of course affects the ability for the server to search by "true" paragraphs.  To enable this feature
    # you must load with command line option includeparas=True
    if include_paras == True or artInfo.src_code in loaderConfig.SRC_CODES_TO_INCLUDE_PARAS:
        children = doc_children() # new instance, reset child counter suffix
        children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist_withinheritance(pepxml, "//body//p|//body//p2", attr_to_find="lang"),
                              parent_id=artInfo.art_id,
                              parent_tag="p_body",
                              default_lang=art_lang[0])
        children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist_withinheritance(pepxml, "//h1|//h2|//h3|//h4|//h5|//h6", attr_to_find="lang"),
                              parent_id=artInfo.art_id,
                              parent_tag="p_heading",
                              default_lang=art_lang[0])
        children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist_withinheritance(pepxml, "//quote//p|//quote//p2", attr_to_find="lang"),
                              parent_id=artInfo.art_id,
                              parent_tag="p_quote",
                              default_lang=art_lang[0])
        children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist_withinheritance(pepxml, "//dream//p|//dream//p2", attr_to_find="lang"),
                              parent_id=artInfo.art_id,
                              parent_tag="p_dream",
                              default_lang=art_lang[0])
        children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist_withinheritance(pepxml, "//poem//p|//poem//p2", attr_to_find="lang"),
                              parent_id=artInfo.art_id,
                              parent_tag="p_poem",
                              default_lang=art_lang[0])
        children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist_withinheritance(pepxml, "//note//p|//note//p2", attr_to_find="lang"),
                              parent_id=artInfo.art_id,
                              parent_tag="p_note",
                              default_lang=art_lang[0])
        children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist_withinheritance(pepxml, "//dialog//p|//dialog//p2", attr_to_find="lang"),
                              parent_id=artInfo.art_id,
                              parent_tag="p_dialog",
                              default_lang=art_lang[0])
        children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist_withinheritance(pepxml, "//panel//p|//panel//p2", attr_to_find="lang"),
                              parent_id=artInfo.art_id,
                              parent_tag="p_panel",
                              default_lang=art_lang)
        children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist_withinheritance(pepxml, "//caption//p", attr_to_find="lang"),
                              parent_id=artInfo.art_id,
                              parent_tag="p_caption",
                              default_lang=art_lang[0])
        children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist_withinheritance(pepxml, "//bib//be|//binc", attr_to_find="lang"),
                              parent_id=artInfo.art_id,
                              parent_tag="p_bib",
                              default_lang=art_lang[0])
        children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist_withinheritance(pepxml, "//appxs//p|//appxs//p2", attr_to_find="lang"),
                              parent_id=artInfo.art_id,
                              parent_tag="p_appxs",
                              default_lang=art_lang[0])
        # summaries and abstracts
        children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist_withinheritance(pepxml, "//summaries//p|//summaries//p2|//abs//p|//abs//p2", attr_to_find="lang"),
                              parent_id=artInfo.art_id,
                              parent_tag="p_summaries",
                              default_lang=art_lang[0])

        child_list = children.child_list
        # indented status
        msg = f"      -->Adding children, tags/counts: {children.tag_counts}"
        logger.info(msg)
        if verbose:
            print (msg)
    else:
        child_list = None
        
    art_kwds_str = opasgenlib.string_to_list(artInfo.art_kwds)
    terms_highlighted = opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//body/*/b|//body/*/i|//body/*/bi|//body/*/bui")
                        #opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//body/*/i") 
    terms_highlighted = remove_values_from_terms_highlighted_list(terms_highlighted)
    # include pep dictionary marked words
    glossary_terms_list = opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//body/*/impx")
    # strip the tags, but keep stop words
    glossary_terms_list = remove_values_from_terms_highlighted_list(glossary_terms_list, remove_stop_words=False)
    
    glossary_group_terms = pepxml.xpath("//body/*/impx/@grpname")
    glossary_group_terms_list = []
    if glossary_group_terms is not None:
        for n in glossary_group_terms:
            glossary_group_terms_list += opasgenlib.string_to_list(n, sep=";")
    freuds_italics = opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//body/*/fi", default_return=None)
    if freuds_italics is not None:
        freuds_italics = remove_values_from_terms_highlighted_list(freuds_italics)

    if artInfo.art_title is not None:
        title_str = artInfo.art_title.translate(str.maketrans('', '', string.punctuation)) # remove all punct for sorting
    else:
        title_str = None

    vol_title = non_empty_string(artInfo.art_vol_title)
    if vol_title is not None:
        vol_title_str = vol_title.translate(str.maketrans('', '', string.punctuation))
    else:
        vol_title_str = None
        
    bk_title_xml = opasxmllib.xml_xpath_return_xmlsingleton(pepxml, "//artbkinfo/bktitle", default_return = None)
    if bk_title_xml is not None:
        bk_title = opasxmllib.xml_string_to_text(bk_title_xml)
        bk_title_str = bk_title.translate(str.maketrans('', '', string.punctuation)), # remove all punct for sorting
    else:
        bk_title_str = None

    if artInfo.src_title_full is not None:
        art_sourcetitlefull_str = artInfo.src_title_full.translate(str.maketrans('', '', string.punctuation)) # remove all punct for sorting,
    else:
        art_sourcetitlefull_str = None
        
    bk_title_series_xml = opasxmllib.xml_xpath_return_xmlsingleton(pepxml, "//bktitle", default_return = None)
    if bk_title_series_xml is not None:
        bk_title_series = opasxmllib.xml_string_to_text(bk_title_series_xml)
        bk_title_series_str = bk_title_series.translate(str.maketrans('', '', string.punctuation))
    else:
        bk_title_series_str = None
        
    if artInfo.art_issue_title is not None:
        art_issue_title_str = artInfo.art_issue_title.translate(str.maketrans('', '', string.punctuation))
    else:
        art_issue_title_str = None
    
    new_rec = {
                "id": artInfo.art_id,                                         # important =  note this is unique id for every reference
                "art_id" : artInfo.art_id,                                    # important
                "art_embargo" : artInfo.embargo,                              # limit display if true (e.g., IJPOpen removed articles)
                "art_embargotype" : artInfo.embargotype,
                "title" : artInfo.art_title,                                  # important
                "title_str" : title_str, # remove all punct, this is only used for sorting
                "art_title_xml" : opasxmllib.xml_xpath_return_xmlsingleton(pepxml, "//arttitle", default_return = None),
                "art_title_str" : title_str, # remove all punct, this is only used for sorting
                "art_sourcecode" : artInfo.src_code,                 # important
                "art_sourcetitleabbr" : artInfo.src_title_abbr,
                "art_sourcetitlefull" : artInfo.src_title_full,
                "art_sourcetitlefull_str" : art_sourcetitlefull_str, # remove all punct for sorting,
                "art_sourcetype" : artInfo.src_type,
                "art_product_key" : artInfo.src_prodkey,
                # abstract_xml and summaries_xml should not be searched, but useful for display without extracting
                "abstract_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//abs", default_return = None),
                "summaries_xml" : summaries_xml,
                "art_excerpt" : excerpt,
                "art_excerpt_xml" : excerpt_xml,
                # very important field for displaying the whole document or extracting parts
                "text_xml" : file_xml_contents,                                # important
                "art_offsite" : offsite_contents, #  true if it's offsite
                "author_bio_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//nbio", default_return = None),
                "author_aff_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//autaff", default_return = None),
                "bk_title_xml" : bk_title_xml,
                "bk_title_str" : bk_title_str, # remove all punct for sorting
                "bk_subdoc" : artInfo.bk_subdoc,
                "art_info_xml" : artInfo.artinfo_xml,
                "bk_alsoknownas_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//artbkinfo/bkalsoknownas", default_return = None),
                "bk_editors_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//bkeditors", default_return = None),
                "bk_seriestitle_xml" : bk_title_series_xml,
                "bk_seriestitle_str" : bk_title_series_str, # remove all punct for sorting,,,
                "bk_series_toc_id" : artInfo.bk_seriestoc,
                "bk_main_toc_id" : artInfo.main_toc_id,
                "bk_next_id" : artInfo.bk_next_id,
                "caption_text_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml,"//caption", default_return = None),
                "caption_title_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//ctitle", default_return = None),
                "headings_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//h1|//h2|//h3|//h4|//h5|//h6", default_return = None), # reinstated 2020-08-14
                "meta_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//meta", default_return = None),
                "text_xml" : file_xml_contents,
                "timestamp" : artInfo.processed_datetime,                     # important
                "file_last_modified" : artInfo.filedatetime,
                "file_classification" : non_empty_string(artInfo.file_classification),
                "file_size" : artInfo.file_size,
                "file_name" : artInfo.filename,
                "art_subtitle_xml" : opasxmllib.xml_xpath_return_xmlsingleton(pepxml, "//artsub", default_return = None),
                "art_citeas_xml" : artInfo.art_citeas_xml,
                #"art_cited_all" : cited_counts.countAll,
                #"art_cited_5" : cited_counts.count5,
                #"art_cited_10" : cited_counts.count10,
                #"art_cited_20" : cited_counts.count20,
                "body_xml" : body_xml[0],
                "appxs_xml": appxs_xml, # list
                "authors" :  artInfo.author_list, # artInfo.art_all_authors,
                "art_authors" : artInfo.author_list,
                "art_authors_count" : artInfo.art_authors_count,
                "art_authors_mast" : non_empty_string(artInfo.art_auth_mast),
                "art_authors_mast_list" : non_empty_string(artInfo.art_auth_mast_list),
                "art_authors_mast_list_strings" : non_empty_string(artInfo.art_auth_mast_list),
                # next two fields may be temp, but I want to compare mast to ids
                "art_authors_ids" : artInfo.art_author_id_list,
                "art_authors_ids_str" : non_empty_string(artInfo.art_author_ids_str),
                # end insertion ################################################
                "art_authors_citation" : non_empty_string(artInfo.art_auth_citation),
                "art_authors_citation_list" : non_empty_string(artInfo.art_auth_citation_list),
                "art_authors_unlisted" : non_empty_string(artInfo.art_auth_mast_unlisted_str),
                "art_authors_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//aut", default_return = None),
                "art_year" : non_empty_string(artInfo.art_year),
                "art_year_int" : artInfo.art_year_int,
                "art_vol" : artInfo.art_vol_int,
                "art_vol_suffix" : non_empty_string(artInfo.art_vol_suffix),
                "art_vol_title" : vol_title,
                "art_vol_title_str" : vol_title_str, # remove all punct for sorting
                "art_pgrg" : non_empty_string(artInfo.art_pgrg),
                "art_pgcount" : artInfo.art_pgcount,
                "art_tblcount" : artInfo.art_tblcount,
                "art_figcount" : artInfo.art_figcount,
                "art_kwds_count" : artInfo.art_kwds_count,
                "art_abs_count" : artInfo.art_abs_count,
                "art_ftns_count" : artInfo.art_ftns_count,
                "art_paras_count" : artInfo.art_paras_count,
                "art_headings_count" : artInfo.art_headings_count,
                "art_terms_count" : artInfo.art_terms_count,
                "art_dreams_count" : artInfo.art_dreams_count,
                "art_dialogs_count" : artInfo.art_dialogs_count,
                "art_notes_count" : artInfo.art_notes_count,
                "art_poems_count" : artInfo.art_poems_count,
                "art_citations_count" : artInfo.art_citations_count,
                "art_quotes_count" : artInfo.art_quotes_count,
                "art_chars_count" : artInfo.art_chars_count,
                "art_chars_no_spaces_count" : artInfo.art_chars_no_spaces_count,
                "art_words_count" : artInfo.art_words_count,
                "art_graphic_list" : artInfo.art_graphic_list,
                "reference_count" : artInfo.ref_count,
                "art_iss" : artInfo.art_issue,
                "art_iss_title" : artInfo.art_issue_title,
                "art_iss_title_str" : art_issue_title_str, # remove all punct for sorting
                "art_iss_seqnbr" : artInfo.art_issue_seqnbr, # sequential issue numbering 1-n from start by some journals
                "art_doi" : artInfo.art_doi,
                "art_lang" : artInfo.art_lang,
                "art_issn" : artInfo.art_issn,
                "art_isbn" : artInfo.art_isbn,
                "art_origrx" : artInfo.art_orig_rx,
                "art_qual" : artInfo.art_qual,
                "art_kwds" : artInfo.art_kwds, # pure search field, but maybe not as good as str
                "art_kwds_str" : art_kwds_str, # list, multivalue field for faceting
                "glossary_terms": glossary_terms_list,
                "glossary_group_terms": glossary_group_terms_list,
                "freuds_italics": freuds_italics,
                "art_type" : artInfo.art_type,
                "art_newsecnm" : artInfo.start_sectname,
                "terms_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//impx[@type='TERM2']", default_return=None),
                "terms_highlighted" : terms_highlighted,
                "dialogs_spkr" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//dialog/spkr/node()", default_return=None),
                "panels_spkr" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//panel/spkr", default_return=None),
                "poems_src" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//poem/src/node()", default_return=None), # multi
                "dialogs_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//dialog", default_return=None), # multi
                "dreams_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//dream", default_return=None), # multi
                "notes_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//note", default_return=None),
                "panels_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//panel", default_return=None),
                "poems_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//poem", default_return=None), # multi
                "quotes_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//quote", default_return=None), # multi
                "references_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//be|binc", default_return=None), # multi
                "tables_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//tbl", default_return=None), # multi
                "bk_pubyear" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//bkpubyear/node()", default_return=None), # multi
                "bib_authors" : artInfo.bib_authors,
                "bib_title" : artInfo.bib_title,
                "bib_journaltitle" : artInfo.bib_journaltitle,
                "bib_rx" : artInfo.bib_rx,
                "art_level" : 1,
                "meta_marked_corrections" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//cgrp[contains(@type,'era')]", default_return=None), # multi,
                #"art_para" : parasxml, 
                "_doc" : child_list  # children.child_list
              }

    #experimental paras save
    # parasxml_update(parasxml, solrcon, artInfo)
    # format for pysolr (rather than solrpy, supports nesting)
    try:
        solrcon.add([new_rec], commit=False)
    except Exception as err:
        #processingErrorCount += 1
        errStr = "SolrDocsError: Art:%s: Err:%s" % (artInfo.art_id, err)
        logger.error(errStr)
        if opasConfig.LOCAL_TRACE: print (errStr)
        # ret_val = False
    else:
        ret_val = True # ok!
        
    return ret_val

class doc_children(object):
    """
    Create an list of child strings to be used as the Solr nested document.
    The parent_tag allows different groups of subelements to be added and separately searchable.
    
    """
    def __init__(self):
        self.count = 0
        self.child_list = []
        self.tag_counts = {}
        
    def add_children(self, stringlist, parent_id, parent_tag=None, level=2, default_lang=None):
        """
        params:
         - stringlist is typically going to be the return of an xpath expression on an xml instance
         - parent_id is the typically going to be the Solr ID of the parent, and this is suffixed
                     to produce a similar but unique id for the child
         - parent_tag for indicating where this was located in the main instance, e.g., references, dreams, etc.
         - level for creating children at different levels (even if in the same object)
        """
        for n in stringlist:
            self.count += 1
            try:
                self.tag_counts[parent_tag] += 1
            except: # initialize
                self.tag_counts[parent_tag] = 1
            
            # special attr handling.  Later look and see if this is slowing us down...
            currelem = etree.fromstring(n, parser=parser)
            lang = currelem.attrib.get("lang", default_lang)
            para_lgrid = currelem.attrib.get("lgrid", None)
            para_lgrx = currelem.attrib.get("lgrx", None)
            if para_lgrx is not None:
                para_lgrx = [item.strip() for item in para_lgrx.split(',')]
                
            self.child_list.append({"id": parent_id + f".{self.count}",
                                    "para_art_id": parent_id,
                                    "art_level": level,
                                    "parent_tag": parent_tag,
                                    "lang": lang,
                                    "para": n,
                                    "para_lgrid" : para_lgrid,
                                    "para_lgrx" : para_lgrx
                                  })
        return self.count

#------------------------------------------------------------------------------------------------------
def process_info_for_author_core(pepxml, artInfo, solrAuthor, verbose=None):
    """
    Get author data and write a record for each author in each document.  Hence an author
       of multiple articles will be listed multiple times, once for each article.  But
       this core will let us research by individual author, including facets.
       
    """
    #------------------------------------------------------------------------------------------------------
    # update author data
    #<!-- ID = PEP articleID + authorID -->
    
    ret_val = False
    msg = f"   ...Processing XML for Author Core."
    logger.info(msg)
    if verbose:
        print (msg)
    
    try:
        # Save author info in database
        authorPos = 0
        for author in artInfo.author_xml_list:
            authorID = author.attrib.get('authindexid', None)
            if authorID is None:
                authorID = opasxmllib.authors_citation_from_xmlstr(author)
                try:
                    authorID = authorID[0]
                except:
                    authorID = "GenID" + "%05d" % random.randint(1, 5000)
            authorListed = author.attrib.get('listed', "true")
            if authorListed.lower() == "true":
                authorPos += 1
            authorRole = author.attrib.get('role', None)
            authorXML = opasxmllib.xml_elem_or_str_to_xmlstring(author)
            authorDocid = artInfo.art_id + "." + ''.join(e for e in authorID if e.isalnum())
            authorBio = opasxmllib.xml_xpath_return_textsingleton(author, "nbio")
            try:
                authorAffID = author.attrib['affid']
            except KeyError as e:
                authorAffil = None  # see if the add still takes!
            else:
                authorAffil = pepxml.xpath('//artinfo/artauth/autaff[@affid="%s"]' % authorAffID)
                authorAffil = etree.tostring(authorAffil[0]).decode("utf-8")

            adoc = []
            adoc.append({
                "id": authorDocid,         # important =  note this is unique id for every author + artid
                "art_id": artInfo.art_id,
                "title": artInfo.art_title,
                "authors": artInfo.art_author_id_list,
                "art_author_id": authorID,
                "art_author_listed": authorListed,
                "art_author_pos_int": authorPos,
                "art_author_role": authorRole,
                "art_author_bio": authorBio,
                "art_author_affil_xml": authorAffil,
                "art_year_int": artInfo.art_year_int,
                "art_sourcetype": artInfo.src_type,
                "art_sourcetitlefull": artInfo.src_title_full,
                "art_citeas_xml": artInfo.art_citeas_xml,
                "art_author_xml": authorXML,
                "file_last_modified": artInfo.filedatetime,
                "file_classification": artInfo.file_classification,
                "file_name": artInfo.filename,
                "timestamp": artInfo.processed_datetime  # When batch was entered into core
            })
               
            try:  
                response_update = solrAuthor.add(adoc)
                
                if not re.search('"status":0', response_update):
                    msg = "AuthorCoreError: Save error for %s: %s (%s)" % (artInfo.art_id, err, response_update)
                    logger.error(msg)
                    if opasConfig.LOCAL_TRACE: print (msg)
            except Exception as err:
                #processingErrorCount += 1
                errStr = "AuthorCoreError: Exception for %s: %s" % (artInfo.art_id, err)
                if opasConfig.LOCAL_TRACE: print (errStr)
                logger.error(errStr)
            else:
                ret_val = True # ok!
                

    except Exception as err:
        #processingErrorCount += 1
        errStr = "AuthorCoreError: Exception for %s: %s" % (artInfo.art_id, err)
        if opasConfig.LOCAL_TRACE: print (errStr)
        logger.error(errStr)

    return ret_val
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
    insert_if_not_exists = r"""REPLACE
                               INTO api_biblioxml (
                                    art_id,
                                    bib_local_id,
                                    art_year,
                                    bib_rx,
                                    bib_sourcecode, 
                                    bib_rxcf, 
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
                                    full_ref_xml,
                                    full_ref_text
                                    )
                                values (%(art_id)s,
                                        %(ref_local_id)s,
                                        %(art_year_int)s,
                                        %(rx)s,
                                        %(rx_sourcecode)s,
                                        %(rxcf)s,
                                        %(author_list_str)s,
                                        %(authors_xml)s,
                                        %(ref_title)s,
                                        %(source_type)s,
                                        %(source_title)s,
                                        %(pgrg)s,
                                        %(year_of_publication)s,
                                        %(year_of_publication_int)s,
                                        %(volume)s,
                                        %(publishers)s,
                                        %(ref_entry_xml)s,
                                        %(ref_entry_text)s
                                        );
                            """
    query_param_dict = bib_entry.__dict__
    # need to remove lists, even if they are not used.
    del query_param_dict["author_list"]
    del query_param_dict["author_name_list"]

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
def add_article_to_api_articles_table(ocd, art_info, verbose=None):
    """
    Adds the article data from a single document to the api_articles table in mysql database opascentral.
    
    This database table is used as the basis for
     
    Note: This data is in addition to the Solr pepwebdocs core which is added elsewhere.  The SQL table is
          currently primarily used for the crosstabs rather than API queries, since the Solr core is more
          easily joined with other Solr cores in queries.  (TODO: Could later experiment with bridging Solr/SQL.)
      
    """
    ret_val = False
    msg = f"   ...Processing metadata for Articles DB."
    logger.info(msg)
    if verbose:
        print (msg)
    
    ocd.open_connection(caller_name="processArticles")
    
    # reduce object
  
    insert_if_not_exists = r"""REPLACE
                               INTO api_articles (
                                    art_id,
                                    art_doi,
                                    art_type,
                                    art_lang,
                                    art_kwds,
                                    art_auth_mast,
                                    art_auth_citation,
                                    art_title,
                                    src_title_abbr,
                                    src_code,
                                    art_year,
                                    art_vol,
                                    art_vol_str,
                                    art_vol_suffix,
                                    art_issue,
                                    art_pgrg,
                                    art_pgstart,
                                    art_pgend,
                                    main_toc_id,
                                    start_sectname,
                                    bk_info_xml,
                                    bk_title,
                                    bk_publisher,
                                    art_citeas_xml,
                                    art_citeas_text,
                                    ref_count,
                                    filename,
                                    filedatetime
                                    )
                                values (
                                        %(art_id)s,
                                        %(art_doi)s,
                                        %(art_type)s,
                                        %(art_lang)s,
                                        %(art_kwds)s,
                                        %(art_auth_mast)s,
                                        %(art_auth_citation)s,
                                        %(art_title)s,
                                        %(src_title_abbr)s,
                                        %(src_code)s,
                                        %(art_year)s,
                                        %(art_vol_int)s,
                                        %(art_vol_str)s,
                                        %(art_vol_suffix)s,
                                        %(art_issue)s,
                                        %(art_pgrg)s,
                                        %(art_pgstart)s,
                                        %(art_pgend)s,
                                        %(main_toc_id)s,
                                        %(start_sectname)s,
                                        %(bk_info_xml)s,
                                        %(bk_title)s,
                                        %(bk_publisher)s,
                                        %(art_citeas_xml)s,
                                        %(art_citeas_text)s,
                                        %(ref_count)s,
                                        %(filename)s,
                                        %(filedatetime)s
                                        );
                            """

    query_params = {
        "art_id": art_info.art_id,
        "art_doi": art_info.art_doi,
        "art_type": art_info.art_type,
        "art_lang":  art_info.art_lang,
        "art_kwds":  art_info.art_kwds,
        "art_auth_mast":  art_info.art_auth_mast,
        "art_auth_citation": art_info.art_auth_citation, 
        "art_title":  art_info.art_title,
        "src_title_abbr":  art_info.src_title_abbr,  
        "src_code":  art_info.src_code,  
        "art_year":  art_info.art_year,
        "art_vol_int":  art_info.art_vol_int,
        "art_vol_str":  art_info.art_vol_str,
        "art_vol_suffix":  art_info.art_vol_suffix,
        "art_issue":  art_info.art_issue,
        "art_pgrg":  art_info.art_pgrg,
        "art_pgstart":  art_info.art_pgstart,
        "art_pgend":  art_info.art_pgend,
        "main_toc_id":  art_info.main_toc_id,
        "start_sectname":  art_info.start_sectname,
        "bk_info_xml":  art_info.bk_info_xml,
        "bk_title":  art_info.bk_title,
        "bk_publisher":  art_info.bk_publisher,
        "art_citeas_xml":  art_info.art_citeas_xml,
        "art_citeas_text":  art_info.art_citeas_text,
        "ref_count":  art_info.ref_count,
        "filename":  art_info.filename,
        "filedatetime": art_info.filedatetime
    }

    # string entries above must match an attr of the art_info instance.
    #query_param_dict = art_info.__dict__.copy()
    # the element objects in the author_xml_list cause an error in the action query 
    # even though that dict entry is not used.  So removed in a copy.
    #query_param_dict["author_xml_list"] = None
        
    try:
        res = ocd.do_action_query(querytxt=insert_if_not_exists, queryparams=query_params)
    except Exception as e:
        errStr = f"AddToArticlesDBError: insert error {e}"
        logger.error(errStr)
        if opasConfig.LOCAL_TRACE: print (errStr)
    else:
        ret_val = True
        
    try:
        ocd.db.commit()
        ocd.close_connection(caller_name="processArticles")
    except mysql.connector.Error as e:
        errStr = f"SQLDatabaseError: Commit failed! {e}"
        logger.error(errStr)
        if opasConfig.LOCAL_TRACE: print (errStr)
        ret_val = False
    
    return ret_val  # return True for success

#------------------------------------------------------------------------------------------------------
def add_to_tracker_table(ocd, art_id, verbose=None):
    """
    Adds the article data from a single document to the tracker table in mysql database opascentral.
    
    If the article is added successfully, that means it's a new article...never seen before.
    Return True so it can be logged.
    Else return False, and it will not be logged as database update.

    >>> import opasCentralDBLib
    >>> ocd =  opasCentralDBLib.opasCentralDB()
    >>> add_to_tracker_table(ocd, "AI.001.0001A") # already in table so should return false
    False
    """
    ret_val = False
    caller_name = "add_to_tracker_table"
    ocd.open_connection(caller_name=caller_name)
    insert_if_not_exists = r"""INSERT
                               INTO article_tracker (art_id)
                               values (
                                        %(art_id)s
                                      );
                            """

    # string entries above must match an attr of the art_info instance.
    query_param_dict = {}
    # the element objects in the author_xml_list cause an error in the action query 
    # even though that dict entry is not used.  So removed in a copy.
    query_param_dict["art_id"] = art_id
        
    try:
        res = ocd.do_action_query_silent(querytxt=insert_if_not_exists, queryparams=query_param_dict)
    except Exception as e:
        pass # normal
    else:
        ret_val = True
        
    try:
        ocd.db.commit()
        ocd.close_connection(caller_name=caller_name)
    except mysql.connector.Error as e:
        errStr = f"SQLDatabaseError: Commit failed! {e}"
        logger.error(errStr)
        if opasConfig.LOCAL_TRACE: print (errStr)
        ret_val = False
    
    return ret_val  # return True for success

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
