#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#Copyright 2012-2018 Neil R. Shapiro

"""
"""

# import string, sys, copy, re
import logging
logger = logging.getLogger(__name__)
# from io import StringIO

import opasGenSupportLib as opasgenlib
from loggingDebugStream import log_everywhere_if

import opasSolrLoadSupport
# import opasDocuments
import opasPySolrLib
from opasLocator import Locator
import opasCentralDBLib
import opasXMLHelper
import opasXMLProcessor
import opasConfig
import models

gDbg1 = 0	# details
gDbg2 = 1	# High level

LOWER_RELEVANCE_LIMIT = 35

ocd = opasCentralDBLib.opasCentralDB()
import lxml.etree as ET
import lxml
sqlSelect = ""
parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)

#------------------------------------------------------------------------------------------------------
def old_update_biblio(parsed_xml, artInfo, ocd, pretty_print=False, verbose=False):
    """
    Walk through the biblio records and update rx and rxcf links in the XML, using heuristics if necessary. 
    """

    known_books = PEPBookInfo.PEPBookInfo()
    
    # add links to biblio entries, rx to be
    if artInfo.ref_count > 0:
        bibReferences = parsed_xml.xpath("/pepkbd3//be")  # this is the second time we do this (also in artinfo, but not sure or which is better per space vs time considerations)
        if verbose: print("\t...Examining %s references for links (rx) and related titles (rxcf)." % (artInfo.ref_count))
        #processedFilesCount += 1
        bib_total_reference_count = 0
        for ref in bibReferences:
            # bib_entry_text = ''.join(ref.itertext())
            bib_pgstart = None
            bib_pgend = None
            # compare_to = ""
            ref_id = ref.attrib["id"]
            # see if it's already in table
            bib_saved_entry_tuple = ocd.get_references_from_biblioxml_table(article_id=artInfo.art_id, ref_local_id=ref_id)
            if bib_saved_entry_tuple is not None and bib_saved_entry_tuple != []:
                bib_saved_entry = bib_saved_entry_tuple[0]
            else:
                bib_saved_entry = models.Biblioxml()
            
            # merge record info
            bib_total_reference_count += 1
            bib_entry = opasSolrLoadSupport.BiblioEntry(artInfo, ref)
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
                                       noStartingPageException=True, 
                                       filename=artInfo.filename)
                    # need to check if it's whole, and if it works, but for now.
                    if locator.valid == 0:
                        msg = f"\t\t\t...Bib ID {ref_id} does not have enough info to link. {bib_entry.year}.{bib_entry.volume}.{bib_pgstart}"
                        log_everywhere_if(gDbg2, level="info", msg=msg)
                        continue
                        
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
def search_for_referenced_article(ref, art_or_source_title, query_target="art_title_xml", max_words=opasConfig.MAX_WORDS, min_words=opasConfig.MIN_WORDS, word_len=opasConfig.MIN_WORD_LEN, max_cf_list=opasConfig.MAX_CF_LIST):
    """
    Search for related articles and add to rxcf of reference
    
    """
    # title is either bib_entry.art_title_xml or bib_entry.source_title
    rxcf = []
    prev_rxcf = None
    query = f"{query_target}:({art_or_source_title})"
    authors = ref.xpath("//a")
    if authors:
        # list of last name of authors with AND, search field art_authors_xml
        author1 = ET.tostring(authors[0]).decode("utf8")
        query = query + f" AND authors:{author1}"
        
    years = ref.xpath("//y")
    if years:
        # list of last name of authors with AND, search field art_authors_xml
        year = ET.tostring(years[0]).decode("utf8")
        query = query + f" AND art_year:{year}"

    vols = ref.xpath("//v")
    if vols:
        # list of last name of authors with AND, search field art_authors_xml
        vol = ET.tostring(vols[0]).decode("utf8")
        query = query + f" AND art_year:{vol}"

    result = opasPySolrLib.search_text(query=query, limit=10, offset=0, full_text_requested=False)
        
    if result[1][0] == 200:
        if gDbg2:
            title_list = [item.title for item in result[0].documentList.responseSet[0:max_cf_list]]
            if title_list != []:
                print (f"\t\t\t...Article title first {len(title_words)} words of len {word_len} for search: {safe_title_words} from title:{art_or_source_title}")
                for n in title_list:
                    print (f"\t\t\t\t...cf Article Title: {n[:max_display_len_cf_articles]}")
                        
            rxcf = [item.documentID for item in result[0].documentList.responseSet[0:max_cf_list]]
            try:
                prev_rxcf = ref.attrib["rxcf"]
            except Exception:
                pass

            if len(rxcf) > 0 and prev_rxcf is None:
                ref.attrib["rxcf"] = ",".join(rxcf)
                compare_to = f"\t\t\t...Journal title compare to: {ref.attrib['rxcf']}"
                log_everywhere_if(gDbg2, level="debug", msg=compare_to)
            elif prev_rxcf is not None:
                ref.attrib["rxcf"] = prev_rxcf + "," + ",".join(rxcf)
                compare_to = f"\t\t\t...Journal title compare to: {ref.attrib['rxcf']}"
                log_everywhere_if(gDbg2, level="debug", msg=compare_to)
                
        else:
            log_everywhere_if(gDbg1, level="debug", msg=result[1][1])
    elif gDbg2:
        print (f"\t\t\t...Skipped cf search (too few words): {title_words}")

    return rxcf

def walk_through_references(ocd=ocd):
    """
    >>> walk_through_references()
    """
    fname = "walk_through_references"
    ocd.open_connection(caller_name=fname) # make sure connection is open
    ret_val = None
    sqlSelect = "select * from api_biblioxml where bib_rx is NULL"
    if ocd.db is not None:
        # rows = self.SQLSelectGenerator(sqlSelect)
        curs = ocd.db.cursor(buffered=True, dictionary=True)
        curs.execute(sqlSelect)
        warnings = curs.fetchwarnings()
        if warnings:
            for warning in warnings:
                logger.warning(warning)
                
        counter = 0
        for row in curs.fetchall():
            counter += 1
            fullref = row['full_ref_xml']
            # parsed_ref = ET.parse(StringIO(fullref), parser=parser)
            parsed_ref = ET.fromstring(fullref, parser=parser)
            authors = parsed_ref.xpath("//a")
            author_list = ""
            if authors:
                for n in authors:
                    author_list += ''.join(n.itertext())
                    break
            else:
                continue

            vols = parsed_ref.xpath("//v")
            pages = parsed_ref.xpath("//pp")
            years = parsed_ref.xpath("//y")
            book_title = parsed_ref.xpath("//bst")
            titles = parsed_ref.xpath("//t")
            if titles:
                title = titles[0].text
            else:
                title = ""
                
            plain_text = opasXMLHelper.xml_elem_or_str_to_text(fullref)
            # print (f"Looking for: {plain_text}")
            # look in articles table
            art_search = f"""
            select art_id, art_citeas_text, art_citeas_xml, match(art_citeas_text) against ("{title}") AS Relevance
            from api_articles 
            where match(art_citeas_text) against  ("{title}");
            """
            article_matches = ocd.get_select_as_list_of_dicts(art_search)
            article_matches = article_matches[:100]
            if article_matches:
                for n in article_matches:
                    xml_citation = n["art_citeas_xml"]
                    text_citation = n["art_citeas_text"]
                    if n["Relevance"] >= LOWER_RELEVANCE_LIMIT:
                        if author_list in xml_citation:
                            print (f"Looking for: {plain_text}")
                            print (f"\t...{n['art_id']}:%{n['Relevance']:.2f} - {text_citation}")
                            break
                    else:
                        break
                    
        
    ocd.close_connection(caller_name=fname) # make sure connection is closed
    
    # return session model object
    return ret_val # None or Session Object

if __name__ == "__main__":

    if 1:
        walk_through_references()
    else:
        import doctest
        doctest.testmod(optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
        print ("Fini. Tests complete.")