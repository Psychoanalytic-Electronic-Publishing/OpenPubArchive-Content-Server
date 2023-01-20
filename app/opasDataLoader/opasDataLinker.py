#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#Copyright 2012-2018 Neil R. Shapiro

"""
"""
import sys
sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')

# import string, sys, copy, re
import logging
logger = logging.getLogger(__name__)
# from io import StringIO
import re
import time

import opasGenSupportLib as opasgenlib
from loggingDebugStream import log_everywhere_if

import opasBiblioSupport
import opasPySolrLib
from opasLocator import Locator
import opasCentralDBLib
#import opasXMLHelper
import opasXMLProcessor
import opasConfig
#import opasArticleIDSupport
import models
import PEPJournalData
import PEPBookInfo

gDbg1 = 0	# details
gDbg2 = 1	# High level

LOWER_RELEVANCE_LIMIT = 35

ocd = opasCentralDBLib.opasCentralDB()
import lxml.etree as ET
import lxml
sqlSelect = ""
parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
max_display_len_cf_articles = 90

def is_in_pep(bib_entry):
    source 
    
def find_related_articles(ref, art_or_source_title,
                          query_target="art_title_xml",
                          max_words=opasConfig.MAX_WORDS,
                          min_words=opasConfig.MIN_WORDS,
                          word_len=opasConfig.MIN_WORD_LEN,
                          max_cf_list=opasConfig.MAX_CF_LIST):
    """
    Search for related articles and add to rxcf of reference
    
    """
    # title is either bib_entry.art_title_xml or bib_entry.source_title
    ret_val = [] # rxcf
    prev_rxcf = None
    title_words = re.findall(r'\b\w{%s,}\b' % word_len, art_or_source_title)[:max_words]
    if len(title_words) >= min_words:
        safe_title_words = " AND ".join(title_words)
        query = f"{query_target}:({safe_title_words})"
        result = opasPySolrLib.search_text(query=query, limit=10, offset=0, full_text_requested=False)
        
        if result[1][0] == 200:
            if gDbg2:
                title_list = [item.title for item in result[0].documentList.responseSet[0:max_cf_list]]
                if title_list != []:
                    print (f"\t\t\t...Article title first {len(title_words)} words of len {word_len} for search: {safe_title_words} from title:{art_or_source_title}")
                    for n in title_list:
                        print (f"\t\t\t\t...cf Article Title: {n[:max_display_len_cf_articles]}")
                        
            ret_val = [item.documentID for item in result[0].documentList.responseSet[0:max_cf_list]]
            try:
                prev_rxcf = ref.attrib["rxcf"]
            except Exception:
                pass

            if len(ret_val) > 0 and prev_rxcf is None:
                ref.attrib["rxcf"] = ",".join(ret_val)
                compare_to = f"\t\t\t...Journal title compare to: {ref.attrib['rxcf']}"
                log_everywhere_if(gDbg2, level="debug", msg=compare_to)
            elif prev_rxcf is not None:
                ref.attrib["rxcf"] = prev_rxcf + "," + ",".join(ret_val)
                compare_to = f"\t\t\t...Journal title compare to: {ref.attrib['rxcf']}"
                log_everywhere_if(gDbg2, level="debug", msg=compare_to)
                
        else:
            log_everywhere_if(gDbg1, level="debug", msg=result[1][1])
    elif gDbg2:
        print (f"\t\t\t...Skipped cf search (too few words): {title_words}")

    return ret_val
#------------------------------------------------------------------------------------------------------
                  
#------------------------------------------------------------------------------------------------------
def xxupdate_bincs(parsed_xml, artInfo, ocd, pretty_print=False, verbose=False):
    """
    Walk through the content looking for binc update rx and rxcf links in the XML, using heuristics if necessary. 
    """
    known_books = PEPBookInfo.PEPBookInfo()
    
    # add links to biblio entries, rx to be
    bibReferences = parsed_xml.xpath("/pepkbd3//binc")
    count = len(bibReferences)
    if count > 0:
        if verbose: print(f"\t...Examining {count} inclusion refs (binc) for links (rx) and related titles (rxcf).")
        #processedFilesCount += 1
        bib_total_reference_count = 0
        for parsed_ref in bibReferences:
            # bib_entry_text = ''.join(ref.itertext())
            bib_pgstart = None
            bib_pgend = None
            # compare_to = ""
            ref_id = parsed_ref.attrib.get("id", None)
            if ref_id is None:
                if gDbg1:
                    print (f"\t\t...Skipping attempted link of {ET.tostring(parsed_ref)}")
                continue # no id, minor instance, skip
            # see if it's already in table
            bib_saved_entry_tuple = ocd.get_references_from_biblioxml_table(article_id=artInfo.art_id, ref_local_id=ref_id)
            if bib_saved_entry_tuple is not None and bib_saved_entry_tuple != []:
                bib_saved_entry = bib_saved_entry_tuple[0]
            else:
                bib_saved_entry = models.Biblioxml()
            
            # merge record info
            bib_total_reference_count += 1
            bib_entry = opasBiblioSupport.BiblioEntry(artInfo.art_id, ref_or_parsed_ref=parsed_ref)
            #if bib_entry.sourcecode is None:
                #if isinstance(bib_entry.source_title, str) and not opasgenlib.is_empty(bib_entry.source_title):
                    #bib_entry.sourcecode, dummy, dummy = gJrnlData.getPEPJournalCode(strText=bib_entry.source_title) 

            try:
                if not opasgenlib.is_empty(bib_entry.pgrg):
                    bib_pgstart, bib_pgend = bib_entry.pgrg.split("-")
            except ValueError as e:
                if not opasgenlib.is_empty(bib_entry.pgrg):
                    bib_pgstart = bib_entry.pgrg
                    bib_pgend = bib_entry.pgrg
                else:
                    bib_pgstart = ""
                    bib_pgend = ""
                
            if not bib_entry.ref_is_book: # journal or other
                if opasgenlib.is_empty(bib_entry.sourcecode):
                    if bib_entry.ref_title:
                        # find and store rxcf for related articles (side effect of function)
                        if gDbg2 and verbose: print (f"\t...Finding related articles for bibliography based on ref_title")
                        # called routine updates ref if found
                        rxcf = find_related_articles(parsed_ref,
                                                     art_or_source_title=bib_entry.ref_title,
                                                     query_target="art_title_xml",
                                                     max_words=opasConfig.MAX_WORDS,
                                                     min_words=opasConfig.MIN_WORDS,
                                                     word_len=opasConfig.MIN_WORD_LEN,
                                                     max_cf_list=opasConfig.MAX_CF_LIST)                        
                    else:
                        locator = None
                        msg = f"\t\t\t...Skipped: {bib_saved_entry}"
                        log_everywhere_if(gDbg2, level="debug", msg=msg)                            
                    
                else: # if not opasgenlib.is_empty(bib_entry.sourcecode):
                    locator = Locator(strLocator=None,
                                       jrnlCode=bib_entry.sourcecode, 
                                       jrnlVolSuffix="", 
                                       jrnlVol=bib_entry.volume, 
                                       jrnlIss=None, 
                                       pgVar="A", 
                                       pgStart=bib_pgstart, 
                                       jrnlYear=bib_entry.year, 
                                       localID=ref_id, 
                                       keepContext=1, 
                                       forceRoman=False, 
                                       notFatal=True, 
                                       noStartingPageException=True, 
                                       filename=artInfo.filename)
                    # need to check if it's whole, and if it works, but for now.
                    if locator.valid == 0:
                        msg = f"\t\t\t...Bib ID {ref_id} does not have enough info to link. {bib_entry.year}.{bib_entry.volume}.{bib_pgstart}"
                        log_everywhere_if(gDbg2, level="info", msg=msg)
                        continue
                        
                    parsed_ref.attrib["rx"] = locator.articleID()
                    search_str = f"//binc[@id='{ref_id}']"
                    msg = f"\t\t\t...Matched Journal {opasxmllib.xml_xpath_return_xmlstringlist(parsed_xml, search_str)[0]}"
                    log_everywhere_if(gDbg2, level="debug", msg=msg)

                
            else:
                bk_locator_str, match_val, whatever = known_books.getPEPBookCodeStr(bib_entry.ref_entry_text)
                if bk_locator_str is not None:
                    parsed_ref.attrib["rx"] = bk_locator_str 
                    search_str = f"//binc[@id='{ref_id}']"
                    msg = f"\t\t\t...Matched Book {match_val}. {opasxmllib.xml_xpath_return_xmlstringlist(parsed_xml, search_str)[0]}"
                    log_everywhere_if(gDbg2, level="info", msg=msg)
                    
                else:
                    # see if we have info to link SE/GW etc., these are in a sense like journals
                    pep_ref = False
                    if PEPJournalData.PEPJournalData.rgxSEPat2.match(bib_entry.source_title) or PEPJournalData.PEPJournalData.rgxSEPat.match(bib_entry.source_title):
                        pep_ref = True
                        bib_entry.sourcecode = "SE"
                    elif PEPJournalData.PEPJournalData.rgxGWPat2.match(bib_entry.source_title):
                        pep_ref = True
                        bib_entry.sourcecode = "GW"
                    
                    #try checking this anyway!
                    if bib_entry.source_title:
                        # find_related_articles assigns to ref attrib rxcf (hence no need to use return val)
                        if gDbg2 and verbose: print (f"\t...Finding related articles for bibliography based on source_title")
                        # called routine updates ref if found
                        rxcf = find_related_articles(parsed_ref,
                                                     art_or_source_title=bib_entry.source_title,
                                                     query_target="art_title_xml",
                                                     max_words=opasConfig.MAX_WORDS,
                                                     min_words=opasConfig.MIN_WORDS,
                                                     word_len=opasConfig.MIN_WORD_LEN,
                                                     max_cf_list=opasConfig.MAX_CF_LIST)

                        if rxcf == [] and bib_entry.ref_title:
                            rxcf = find_related_articles(parsed_ref,
                                                         art_or_source_title=bib_entry.ref_title,
                                                         query_target="art_title_xml",
                                                         max_words=opasConfig.MAX_WORDS,
                                                         min_words=opasConfig.MIN_WORDS,
                                                         word_len=opasConfig.MIN_WORD_LEN,
                                                         max_cf_list=opasConfig.MAX_CF_LIST)
                            
                            
                    # elif bib_entry.ref
    
                    if pep_ref:
                        locator = Locator(strLocator=None,
                                           jrnlCode=bib_entry.sourcecode, 
                                           jrnlVolSuffix="", 
                                           jrnlVol=bib_entry.volume, 
                                           jrnlIss=None, 
                                           pgVar="A", 
                                           pgStart=bib_pgstart, 
                                           jrnlYear=bib_entry.year, 
                                           localID=ref_id, 
                                           keepContext=1, 
                                           forceRoman=False, 
                                           notFatal=True, 
                                           noStartingPageException=True, 
                                           filename=artInfo.filename)
                        # check locator
                        if locator is not None:
                            base_info = opasPySolrLib.get_base_article_info_by_id(locator)
                            if base_info is None:
                                # try without page number
                                locator = Locator(strLocator=None,
                                                   jrnlCode=bib_entry.sourcecode, 
                                                   jrnlVolSuffix="", 
                                                   jrnlVol=bib_entry.volume, 
                                                   jrnlIss=None, 
                                                   jrnlYear=bib_entry.year, 
                                                   localID=ref_id, 
                                                   keepContext=1, 
                                                   forceRoman=False, 
                                                   notFatal=True, 
                                                   noStartingPageException=True, 
                                                   filename=artInfo.filename)
                                # recheck locator
                                base_info = opasPySolrLib.get_base_article_info_by_id(locator)
                                
                            if base_info is not None:
                                parsed_ref.attrib["rx"] = locator.articleID()
                                search_str = f"//binc[@id='{ref_id}']"
                                msg = f"\t\t\t...Matched Book {match_val}. {opasxmllib.xml_xpath_return_xmlstringlist(parsed_xml, search_str)[0]}"
                                log_everywhere_if(gDbg2, level="debug", msg=msg)
                            else:
                                log_everywhere_if(gDbg2, level="debug", msg=f"didn't find this: {bib_entry.sourcecode}")
                            
                        
                    else:     
                        locator = None
                        msg = f"\t\t\t...Skipped: {bib_entry.ref_entry_text}"
                        log_everywhere_if(gDbg2, level="debug", msg=msg)

#------------------------------------------------------------------------------------------------------
def xx_identify_ref(ref, artInfo, ocd, pretty_print=False, verbose=False):
    """
    For the arg ref, find matching articles via Solr search
     of the title, year and author.
     and return a matched rx and confidence
     and a list of possible matches, rxcf, and confidences.
    """

    # add links to biblio entries, rx to be
    # merge record info
    bib_entry = opasBiblioSupport.BiblioEntry(artInfo.art_id, ref_or_parsed_ref=ref)
    #if bib_entry.sourcecode is None:
        #if isinstance(bib_entry.source_title, str) and not opasgenlib.is_empty(bib_entry.source_title):
            #bib_entry.sourcecode, dummy, dummy = gJrnlData.getPEPJournalCode(strText=bib_entry.source_title) 

    try:
        if not opasgenlib.is_empty(bib_entry.pgrg):
            bib_pgstart, bib_pgend = bib_entry.pgrg.split("-")
    except ValueError as e:
        if not opasgenlib.is_empty(bib_entry.pgrg):
            bib_pgstart = bib_entry.pgrg
            bib_pgend = bib_entry.pgrg
        else:
            bib_pgstart = ""
            bib_pgend = ""
        
    if not bib_entry.ref_is_book: # journal or other
        if opasgenlib.is_empty(bib_entry.sourcecode):
            # there's no source code
            if bib_entry.ref_title:
                # find and store rxcf for related articles (side effect of function)
                if gDbg2 and verbose: print (f"\t...Finding related articles for bibliography based on ref_title")
                # called routine updates ref if found
                rxcf = opasXMLProcessor.find_related_articles(ref,
                                             art_or_source_title=bib_entry.ref_title,
                                             query_target="art_title_xml",
                                             max_words=opasConfig.MAX_WORDS,
                                             min_words=opasConfig.MIN_WORDS,
                                             word_len=opasConfig.MIN_WORD_LEN,
                                             max_cf_list=opasConfig.MAX_CF_LIST)                        
            else:
                locator = None
                msg = f"\t\t\t...Skipped: {bib_saved_entry}"
                log_everywhere_if(gDbg2, level="debug", msg=msg)                            
            
        else: # there's a source code
            locator = Locator(strLocator=None,
                               jrnlCode=bib_entry.sourcecode, 
                               jrnlVolSuffix="", 
                               jrnlVol=bib_entry.volume, 
                               jrnlIss=None, 
                               pgVar="A", 
                               pgStart=bib_pgstart, 
                               jrnlYear=bib_entry.year, 
                               localID=ref_id, 
                               keepContext=1, 
                               forceRoman=False, 
                               notFatal=True, 
                               noStartingPageException=True) #, 
                               #filename=artInfo.filename)
                               
            # need to check if it's whole, and if it works, but for now.
            if locator.valid == 0:
                msg = f"\t\t\t...Bib ID {ref_id} does not have enough info to link. {bib_entry.year}.{bib_entry.volume}.{bib_pgstart}"
                log_everywhere_if(gDbg2, level="info", msg=msg)
            else:
                ref.attrib["rx"] = locator.articleID()
                search_str = f"//be[@id='{ref_id}']"
                msg = f"\t\t\t...Matched Journal {opasxmllib.xml_xpath_return_xmlstringlist(parsed_xml, search_str)[0]}"
                log_everywhere_if(gDbg2, level="debug", msg=msg)

    else: # this is a book
        bk_locator_str, match_val, whatever = known_books.getPEPBookCodeStr(bib_entry.ref_entry_text)
        if bk_locator_str is not None:
            ref.attrib["rx"] = bk_locator_str 
            search_str = f"//be[@id='{ref_id}']"
            msg = f"\t\t\t...Matched Book {match_val}. {opasxmllib.xml_xpath_return_xmlstringlist(parsed_xml, search_str)[0]}"
            log_everywhere_if(gDbg2, level="info", msg=msg)
            
        else:
            # see if we have info to link SE/GW etc., these are in a sense like journals
            pep_ref = False
            if PEPJournalData.PEPJournalData.rgxSEPat2.search(bib_entry.ref_entry_text):
                pep_ref = True
                bib_entry.sourcecode = "SE"
            elif PEPJournalData.PEPJournalData.rgxGWPat2.search(bib_entry.ref_entry_text):
                pep_ref = True
                bib_entry.sourcecode = "GW"
            
            #try checking this anyway!
            if bib_entry.source_title:
                # find_related_articles assigns to ref attrib rxcf (hence no need to use return val)
                if gDbg2 and verbose: print (f"\t...Finding related articles for bibliography rxcf based on source_title: {bib_entry.source_title}")
                # called routine updates ref if found
                rxcf = find_related_articles(ref,
                                             art_or_source_title=bib_entry.source_title,
                                             query_target="art_title_xml",
                                             max_words=opasConfig.MAX_WORDS,
                                             min_words=opasConfig.MIN_WORDS,
                                             word_len=opasConfig.MIN_WORD_LEN,
                                             max_cf_list=opasConfig.MAX_CF_LIST)

            if not rxcf and bib_entry.ref_title:
                if gDbg2 and verbose: print (f"\t...Finding related articles for bibliography rxcf based on ref_title: {bib_entry.ref_title}")
                rxcf = find_related_articles(ref,
                                             art_or_source_title=bib_entry.ref_title,
                                             query_target="art_title_xml",
                                             max_words=opasConfig.MAX_WORDS,
                                             min_words=opasConfig.MIN_WORDS,
                                             word_len=opasConfig.MIN_WORD_LEN,
                                             max_cf_list=opasConfig.MAX_CF_LIST)
                    
                    
            # elif bib_entry.ref

            if pep_ref:
                locator = Locator(strLocator=None,
                                   jrnlCode=bib_entry.sourcecode, 
                                   jrnlVolSuffix="", 
                                   jrnlVol=bib_entry.volume, 
                                   jrnlIss=None, 
                                   pgVar="A", 
                                   pgStart=bib_pgstart, 
                                   jrnlYear=bib_entry.year, 
                                   localID=ref_id, 
                                   keepContext=1, 
                                   forceRoman=False, 
                                   notFatal=True, 
                                   noStartingPageException=True, 
                                   filename=artInfo.filename)
                # check locator
                if locator is not None:
                    base_info = opasPySolrLib.get_base_article_info_by_id(locator)
                    if base_info is None:
                        # try without page number
                        locator = Locator(strLocator=None,
                                           jrnlCode=bib_entry.sourcecode, 
                                           jrnlVolSuffix="", 
                                           jrnlVol=bib_entry.volume, 
                                           jrnlIss=None, 
                                           jrnlYear=bib_entry.year, 
                                           localID=ref_id, 
                                           keepContext=1, 
                                           forceRoman=False, 
                                           notFatal=True, 
                                           noStartingPageException=True, 
                                           filename=artInfo.filename)
                        # recheck locator
                        base_info = opasPySolrLib.get_base_article_info_by_id(locator)
                        
                    if base_info is not None:
                        ref.attrib["rx"] = locator.articleID()
                        search_str = f"//be[@id='{ref_id}']"
                        msg = f"\t\t\t...Matched Book {match_val}. {opasxmllib.xml_xpath_return_xmlstringlist(parsed_xml, search_str)[0]}"
                        log_everywhere_if(gDbg2, level="debug", msg=msg)
                    else:
                        log_everywhere_if(gDbg2, level="debug", msg=f"didn't find this: {bib_entry.sourcecode}")
                    
                
            else:     
                locator = None
                msg = f"\t\t\t...Skipped: {bib_entry.ref_entry_text}"
                log_everywhere_if(gDbg2, level="debug", msg=msg)

#------------------------------------------------------------------------------------------------------
def find_matching_pep_articles(bib_entry, 
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
        authors = bib_entry.author_list_str
        if authors:
            authors = opasgenlib.removeAllPunct(authors, punct_set=solr_adverse_punct_set)
            query = query + f" AND authors:{authors}"
    
        #title_words = re.findall(r'\b\w{%s,}\b' % word_len, art_or_source_title)[:max_words]
            
        if bib_entry.year_int:
            query = query + f" AND art_year:{bib_entry.year_int}"
    
        if bib_entry.volume and not bib_entry.ref_is_book:
            # list of last name of authors with AND, search field art_authors_xml
            query = query + f" AND art_vol:{opasgenlib.removeAllPunct(bib_entry.volume, punct_set=solr_adverse_punct_set)}"
    
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

def walk_through_reference_set(ocd=ocd,
                               sql_set_select = "select * from api_biblioxml where bib_rx is NULL",
                               set_description = "All"
                               ):
    """
    """
    fname = "walk_through_reference_set"
    ocd.open_connection(caller_name=fname) # make sure connection is open
    ret_val = None
    #artInfo = opasArticleIDSupport.ArticleInfo(art_id="IJP.100.0001A",
                                               #art_year="2022")
    
    if ocd.db is not None:
        # rows = self.SQLSelectGenerator(sqlSelect)
        curs = ocd.db.cursor(buffered=True, dictionary=True)
        curs.execute(sql_set_select)
        warnings = curs.fetchwarnings()
        if warnings:
            for warning in warnings:
                logger.warning(warning)
                
        counter = 0
        for row in curs.fetchall():
            counter += 1
            fullref = row['full_ref_xml']
            art_id = row["art_id"]
            art_year = row["art_year"]
            bib_local_id = row["bib_local_id"]
            # parsed_ref = ET.parse(StringIO(fullref), parser=parser)
            parsed_ref = ET.fromstring(fullref, parser=parser)
            bib_entry = opasBiblioSupport.BiblioEntry(art_id, ref_or_parsed_ref=parsed_ref)
            author_list = bib_entry.author_list_str
            
            if bib_entry.ref_is_book:
                source_title = title
            #else:
                #source_title = book_title

            rx, rx_confidence, rxcfs, rxcfs_confidence, \
                title_list = find_matching_pep_articles(bib_entry, verbose=True)
            if len(rxcfs) >= 1:
                # we have a close match?
                if rx_confidence > .69:
                    rx = rx
                    print (f"\t...{rx} considered a match. Updating record.")
                    success = ocd.update_biblioxml_record_links(art_id, bib_local_id,
                                                          rx=rx,
                                                          rx_confidence=rx_confidence,
                                                          rxcfs=', '.join([str(item) for item in rxcfs]),
                                                          rxcfs_confidence=max(rxcfs_confidence),
                                                          verbose=True)
                else:
                    print (f"\t...Potential matches {source_title}: {rxcfs}")
                    success = ocd.update_biblioxml_record_links(art_id, bib_local_id,
                                                          rxcfs=', '.join([str(item) for item in rxcfs]),
                                                          rxcfs_confidence=max(rxcfs_confidence),
                                                          verbose=True)
        
    ocd.close_connection(caller_name=fname) # make sure connection is closed
    
    # return session model object
    return ret_val # None or Session Object

def clean_reference_links(ocd=ocd,
                          sql_set_select = "select * from api_biblioxml where bib_rx is not NULL",
                          set_description = "All"
                          ):
    """
    """
    fname = "clean_reference_links"
    ocd.open_connection(caller_name=fname) # make sure connection is open
    ret_val = None
    #artInfo = opasArticleIDSupport.ArticleInfo(art_id="IJP.100.0001A",
                                               #art_year="2022")
    
    if ocd.db is not None:
        # rows = self.SQLSelectGenerator(sqlSelect)
        curs = ocd.db.cursor(buffered=True, dictionary=True)
        curs.execute(sql_set_select)
        warnings = curs.fetchwarnings()
        if warnings:
            for warning in warnings:
                logger.warning(warning)
                
        counter = 0
        for row in curs.fetchall():
            counter += 1
            art_id = row["art_id"]
            bib_local_id = row["bib_local_id"]
            bib_rx = row["bib_rx"]
            if bib_rx:
                if not ocd.article_exists(bib_rx):
                    print (f"\t...{art_id}/{bib_local_id} - {bib_rx} doesn't exist. Updating record.")
                    success = ocd.update_biblioxml_record_links(art_id, bib_local_id,
                                                          rx=None,
                                                          rx_confidence=0,
                                                          verbose=True)

    ocd.close_connection(caller_name=fname) # make sure connection is closed
    
    # return session model object
    return ret_val # None or Session Object

def fix_pgstart_errors_in_reflinks(ocd=ocd,
                                   sql_set_select = "select * from api_biblioxml where bib_rx is not NULL",
                                   set_description = "All"
                                   ):
    """
    """
    fname = "find_start_page_errors"
    ocd.open_connection(caller_name=fname) # make sure connection is open
    ret_val = None
    #artInfo = opasArticleIDSupport.ArticleInfo(art_id="IJP.100.0001A",
                                               #art_year="2022")
    
    if ocd.db is not None:
        # rows = self.SQLSelectGenerator(sqlSelect)
        curs = ocd.db.cursor(buffered=True, dictionary=True)
        curs.execute(sql_set_select)
        warnings = curs.fetchwarnings()
        if warnings:
            for warning in warnings:
                logger.warning(warning)
                
        counter = 0
        for row in curs.fetchall():
            art_id = row["art_id"]
            bib_local_id = row["bib_local_id"]
            bib_rx = row["bib_rx"]
            full_ref_text = row["full_ref_text"]
            if bib_rx:
                if not ocd.article_exists(bib_rx):
                    try:
                        newLocator = Locator(bib_rx)
                        newLocator.pgStart -= 1
                        if ocd.article_exists(str(newLocator)):
                            # correct it
                            print (f"\t...{art_id}/{bib_local_id} - {bib_rx} doesn't exist. Chgto:{newLocator} for {full_ref_text}.")
                            success = ocd.update_biblioxml_record_links(art_id, bib_local_id,
                                                                  rx=str(newLocator),
                                                                  rx_confidence=.97,
                                                                  verbose=False)
                            counter += 1
                            time.sleep(.175)
                            
                    except Exception as e:
                        msg = f"Error updating locator and/or biblioxml record (from bib_rx:{bib_rx}): {e}"
                        log_everywhere_if(True, "warning", msg)
                    
    print (f"Corrected {counter} biblioxml records where rx was off by one page!")
    ocd.close_connection(caller_name=fname) # make sure connection is closed
    
    # return session model object
    return ret_val # None or Session Object

if __name__ == "__main__":

    if 0:
        set1 = "select * from api_biblioxml where bib_rx is NULL and bib_authors like '%Freud%'"
        walk_through_reference_set(ocd, sql_set_select=set1, set_description="Freud")
    elif 0:
        set1 = "select * from api_biblioxml where bib_rx is not NULL and bib_authors like '%Freud%'"
        clean_reference_links(ocd, set1)
    elif 1:
        set1 = "select * from api_biblioxml where bib_rx is not NULL;"
        fix_pgstart_errors_in_reflinks(ocd, set1)
    else:
        import doctest
        doctest.testmod(optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
    
    print ("Fini. Tests or Processing complete.")