#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
""" 
OPAS - XML Builder/Update Library

Update function to process a keyed/converted XML file for data needed to load into Solr, for runtime use.

Can optionally
- write to XML output build (e.g., EXP_ARCH1)
- Load directly into Solr/RDS without writing the EXP_ARCH1 processed file.
    
"""
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2022, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2022.1128/v.1.0.103"  # recorded in xml processed pepkbd3 procby
__status__      = "Development"

programNameShort = "opasXMLProcessor"

gDbg1 = False # display errors on stdout
gDbg2 = False # processing details

import logging
logger = logging.getLogger(programNameShort)

from loggingDebugStream import log_everywhere_if    # log as usual, but if first arg is true, also put to stdout for watching what's happening

import lxml.etree as ET
import sys
import re
import json

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

import opasXMLHelper as opasxmllib

#from opasFileSupport import FileInfo
import opasXMLPEPAuthorID
import models
import opasLocator
from opasLocator import Locator
import opasGenSupportLib as opasgenlib
import loaderConfig
import opasSolrLoadSupport
import PEPBookInfo
import opasXMLPEPAuthorID 
import PEPGlossaryRecognitionEngine
import opasXMLSplitBookSupport  # Module not done and may not be needed.
import opasLocalID
import opasPySolrLib

import opasConfig
import opasDocuments
import PEPJournalData
import opasXMLParaLanguageConcordance

global gJrnlData
try:  # see if it's been defined.
    a = gJrnlData
except:
    gJrnlData = PEPJournalData.PEPJournalData()

glossEngine = PEPGlossaryRecognitionEngine.GlossaryRecognitionEngine(gather=False)
max_display_len_cf_articles = 90

#----------------------------------------------------------------------------------------------------------------
def add_page_number_markup(parsed_xml):
    """
    Walk through page number "n" elements, and record page number sequence.  Add the next page number to
       the nextpgnum attribute of the n element.
    """

    nodes = parsed_xml.xpath("//n")
    ret_val = len(nodes)

    if gDbg2: print("\t...Adding Page Number Attributes")

    lastPage = None
    
    # Walk through page number "n" elements in reverse, and record page number sequencing
    for node in reversed(nodes):
        n = node.text
        pg_number = opasDocuments.PageNumber(n)
        # record the new pagenumber for the next node
        if lastPage is not None:
            node.attrib["nextpgnum"] = lastPage

        lastPage = pg_number.format()

    return ret_val

#----------------------------------------------------------------------------------------------------------------
def add_base_id_to_local_ids(parsed_xml, xpathid, xpathref, base_id, verbose=False):
    """
    This addss the article base id to local IDs found in the specified xpath.
    
    UNUSED - Delete in late January
    """
    
    nodes = parsed_xml.xpath(xpathid) # e.g., "//be | //binc | //note | //ftn"
    ret_val = len(nodes)

    global gDbg1, gDbg2
    if verbose:
        print ("\t...Adding base ids.")
    else:
        gDbg1 = False
        gDbg2 = False
    
    count = 0
    change_count = 0
    for node in nodes:
        node_id = node.attrib.get("id", None)
        if node_id is not None:
            if base_id not in node_id:
                count += 1
                new_node_id = base_id + "." + node_id
                node.attrib["id"] = new_node_id
                # change any references to this id
                ref_nodes = parsed_xml.xpath(xpathref)
                for n in ref_nodes:
                    if n == node_id:
                        container_node = n.getparent()
                        container_node.attrib["r"] = new_node_id
                        change_count += 1
                        log_everywhere_if(gDbg2, level="info", msg=f"\t\t\t...Expanded id: {node_id} to {new_node_id}")

    print (f"Found {count} id nodes, updated {change_count} nodes")
    ret_val = change_count

    # return node count
    return ret_val

#----------------------------------------------------------------------------------------------------------------
def normalize_local_ids(parsed_xml, verbose=False):
    """
    This normalizes local IDs, currently it standardizes the number of leading zeros and the prefixes used.
    
    It's not clear if this is needed in the current online-only conversion process, and as always, has a risk
    in dealing with non-standard input.  Therefore, it's currently not in use.
    
    UNUSED - Delete in late January
    
    """
    
    nodes = parsed_xml.xpath("//be | //binc | //note | //ftn")
    ret_val = len(nodes)

    global gDbg1, gDbg2
    if verbose:
        print ("\t...Normalizing local ids.")
    else:
        gDbg1 = False
        gDbg2 = False
    
    for node in nodes:
        noteid = node.attrib.get("id", None)
        if noteid is not None:
            nodeid_normal = str(opasLocalID.LocalID(noteid))
            if nodeid_normal != noteid and nodeid_normal != "":
                log_everywhere_if(gDbg2, level="info", msg=f"\t\t\t...Normalized id: {noteid} to {nodeid_normal}")
                node.attrib["id"] = nodeid_normal

    # return node count
    return ret_val

#----------------------------------------------------------------------------------------------------------------
def pgnbr_add_next_attrib(parsed_xml):
    """
    Walk through page number "n" elements, and record page number sequence.  Add the next page number to
       the nextpgnum attribute of the n element.
    """

    # Walk through page number "n" elements, and record page number sequence
    n_nodes = parsed_xml.findall("**/n")
    lastPage = None
    count = 0
    # walk through the nodes backwards.
    for node in n_nodes[::-1]: # backwards
        pgNumber = opasDocuments.PageNumber(node.text)
        if lastPage is not None:
            node.set("nextpgnum", lastPage)
            node.set("prefixused", lastPrefix)
            count += 1
        # record the new pagenumber for the next node
        lastPage = pgNumber.format()
        lastPrefix = pgNumber.pgPrefix

    return count

#------------------------------------------------------------------------------------------------------
def find_related_articles(ref, art_or_source_title, query_target="art_title_xml", max_words=opasConfig.MAX_WORDS, min_words=opasConfig.MIN_WORDS, word_len=opasConfig.MIN_WORD_LEN, max_cf_list=opasConfig.MAX_CF_LIST):
    """
    Search for related articles and add to rxcf of reference
    
    """
    # title is either bib_entry.art_title_xml or bib_entry.source_title
    ret_val = rxcf = []
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

    return ret_val
    
#------------------------------------------------------------------------------------------------------
def pgx_add_rx_jump_via_biblio_entry(parsed_xml, ocd, artInfo, split_book_data=None, verbose=False):
    """
    Look for pgx links which reference the bibliography and link to the referenced
      source page number
    """
    global gDbg1, gDbg2
    if not verbose:
        gDbg1 = False
        gDbg2 = False
    
    #bxRefR = ""
    #bxRefRX = ""
    #bibRef = None
    #pgLink = None
    #jrnlCode = artInfo.src_code
    vol = artInfo.art_vol_str
    aLoc = Locator(artInfo.art_id)

    #  PGX ATTRIBUTES OF INTEREST:
    #     r = Internal Biblio ID Only, if required above (Differs from other
    #             cross-refernces for this reason)
    #
    #     re = External Biblio LocalID, the biblio ID of the biblio record
    #             in a split book where the biblio is in an external instance.
    #             (While a bit awkward to have this separate, this allows the
    #              parser to enforce referential integrity for at least the internal ones).
    #
    #     rx = Full locator to page, if supplied, overrides any computed or implied ref

    # Walk through pgx elements, and fix locators
    pgx_links = parsed_xml.xpath("/pepkbd3//pgx")
    ret_val = 0
    pgxlink_type = "BIBPGLINK"
        
    for pgx in pgx_links:
        r_attr = pgx.attrib.get("r", None)
        if r_attr is not None:
            pg_num = pgx.text
            if pg_num is not None:
                pg_numeric = pg_num.isnumeric()
                if opasgenlib.not_empty(r_attr) and pg_numeric:
                    if r_attr[0] == "B":
                        # bib...get linked rx, if there is one
                        bib_node = parsed_xml.xpath(f'//be[@id="{r_attr}"]')
                        if len(bib_node) == 1:
                            rx = bib_node[0].attrib.get("rx", None)
                            if rx is not None:
                                pgx.attrib["rx"] = rx + f".P{pg_num}"
                                pgx.attrib["type"] = pgxlink_type
                                ret_val += 1
            else:
                logger.warning("pgx does not have a page number reference.")
        else:
            logger.warning("pgx does not have link information.")
                    
    if verbose and ret_val:
        print(f"\t...Found biblo based page links. {ret_val} external pgx links added.")

    return ret_val

#------------------------------------------------------------------------------------------------------
def pgx_add_rx_split_book_links(parsed_xml, ocd, artInfo, split_book_data=None, verbose=False):
    """
    Deal with pgx links within split books
    
    UNUSED - Delete in late January
    
    """
    ret_val = 0
    pgx_links = parsed_xml.xpath("/pepkbd3//pgx") 
    logger.info("\t...Processing page links.")
    for pgx in pgx_links:
        inst = split_book_data.get_splitbook_page_instance(book_code=artInfo.src_code, vol=artInfo.art_vol_str, page_id=pgx.text, vol_suffix=artInfo.art_vol_suffix)
        if gDbg2:
            print (f"Split book info: {pgx.text}, {pgx.attrib}, {inst}")
            
        if inst is not None and pgx.attrib.get("rx", None) is None:
            if gDbg2: print (f"Setting TOC page link: {pgx.text}, {pgx.attrib}, {inst}")
            loc = Locator(inst)
            pgx.attrib["rx"] = str(loc) + ".P" + opasDocuments.PageNumber(pgx.text).pageID()
            ret_val += 1

    return ret_val

#------------------------------------------------------------------------------------------------------
def pgx_add_rx_book_links(parsed_xml, ocd, artInfo, split_book_data=None, verbose=False):
    """
    Deal with pgx links within books
    """
    global gDbg1, gDbg2
    if not verbose:
        gDbg1 = False
        gDbg2 = False
    
    jrnlCode = artInfo.src_code
    vol = artInfo.art_vol_str
    aLoc = Locator(artInfo.art_id)
    ret_val = 0
    pgxlink_type = "BIBPGLINKBOOKS"

    if aLoc.isBook():
        split_book_data = opasXMLSplitBookSupport.SplitBookData(database_connection=ocd)
        pgx_links = parsed_xml.xpath("/pepkbd3//pgx")
        if verbose:
            print(f"\t...Processing book page links. {len(pgx_links)} pgx links found.")
            
        for pgx in pgx_links:
            if pgx.attrib.get("type", "") == "BIBPGLINK":
                continue
            #parentNameElem = pgx.getparent()
            grp_ancestor_list = pgx.xpath("ancestor::grp")
            if len(grp_ancestor_list) > 0:
                grp_ancestor = grp_ancestor_list[0]
                grp_type = grp_ancestor.attrib.get("name", None)
                if grp_type is not None:
                    grp_type = grp_type.upper()
                    if grp_type in ["TOC", "INDEX"]:
                        pgxlink_type = "INDEX" # for TOC or an INDEX
                    else:
                        pgxlink_type = grp_type
                
            current_rx_link = pgx.attrib.get("rx", None)
            if current_rx_link is None: # otherwise, no need to do
                ret_val += 1
                fulltext = opasxmllib.xml_elem_or_str_to_text(pgx) # x.find("pgx")
                fulltext_cleaned = fulltext.split("-")[0]
                fulltext_cleaned = opasgenlib.removeAllPunct(fulltext_cleaned)
                fulltext_cleaned = opasDocuments.PageNumber(fulltext_cleaned)
                fulltext_cleaned = fulltext_cleaned.format(keyword=fulltext_cleaned.LOCALID)
                split_inst_from_fulltext = split_book_data.get_splitbook_page_instance(book_code=jrnlCode, vol=vol, vol_suffix=artInfo.art_vol_suffix, page_id=fulltext_cleaned)
                if split_inst_from_fulltext is None:
                    splitLoc = opasLocator.Locator(jrnlCode=jrnlCode, jrnlVol=vol, jrnlVolSuffix=artInfo.art_vol_suffix, pgStart="1", art_info=artInfo, ocd=ocd)
                    local = splitLoc.localID(fulltext_cleaned).upper()
                    pgx.attrib["rx"] = local
                    pgx.attrib["type"] = pgxlink_type
                    log_everywhere_if(gDbg2, level="info", msg=f"\t\t\t...Reference to non-Split Book. Set link (type={pgxlink_type}) including local to: {local}")
                else:
                    splitLoc = opasLocator.Locator(split_inst_from_fulltext, ocd=ocd)
                    #print (splitLoc, SEPage)
                    local = splitLoc.localID(fulltext_cleaned).upper()
                    pgx.attrib["rx"] = local
                    pgx.attrib["type"] = pgxlink_type
                    log_everywhere_if(gDbg2, level="info", msg=f"\t\t\t...Reference to Split Book. Set link (type={pgxlink_type}) including local to: {local}")
            else:
                log_everywhere_if(gDbg2, level="info", msg=f"\t\t\t...Rx link for pgx already set: {current_rx_link}")

    return ret_val
#------------------------------------------------------------------------------------------------------
def update_biblio(parsed_xml, artInfo, ocd, pretty_print=False, verbose=False):
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
                    if bib_entry.ref_title:
                        # find and store rxcf for related articles (side effect of function)
                        if gDbg2 and verbose: print (f"\t...Finding related articles for bibliography based on ref_title")
                        # called routine updates ref if found
                        rxcf = find_related_articles(ref,
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
                        
                    ref.attrib["rx"] = locator.articleID()
                    search_str = f"//be[@id='{ref_id}']"
                    msg = f"\t\t\t...Matched Journal {opasxmllib.xml_xpath_return_xmlstringlist(parsed_xml, search_str)[0]}"
                    log_everywhere_if(gDbg2, level="debug", msg=msg)

                
            else:
                bk_locator_str, match_val, whatever = known_books.getPEPBookCodeStr(bib_entry.ref_entry_text)
                if bk_locator_str is not None:
                    ref.attrib["rx"] = bk_locator_str 
                    search_str = f"//be[@id='{ref_id}']"
                    msg = f"\t\t\t...Matched Book {match_val}. {opasxmllib.xml_xpath_return_xmlstringlist(parsed_xml, search_str)[0]}"
                    log_everywhere_if(gDbg2, level="info", msg=msg)
                    
                else:
                    # see if we have info to link SE/GW etc., these are in a sense like journals
                    pep_ref = False
                    if PEPJournalData.PEPJournalData.rgxSEPat2.match(bib_entry.source_title):
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
                        rxcf = find_related_articles(ref,
                                                     art_or_source_title=bib_entry.source_title,
                                                     query_target="art_title_xml",
                                                     max_words=opasConfig.MAX_WORDS,
                                                     min_words=opasConfig.MIN_WORDS,
                                                     word_len=opasConfig.MIN_WORD_LEN,
                                                     max_cf_list=opasConfig.MAX_CF_LIST)

                        if rxcf == [] and bib_entry.ref_title:
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

def add_pagenbrs_to_splitbook_table(parsed_xml, artInfo, ocd, split_book_data, pretty_print=False, verbose=False):
    """
    Record the page numbers to the database splitbook table (for split books only)
    """
    if artInfo.is_splitbook:
        pagebreaks = [pbk.text for pbk in parsed_xml.xpath("//n")]
        nodes = parsed_xml.xpath("//bib")
        if len(nodes)>0:
            has_biblio = 1
        else:
            has_biblio = 0

        if artInfo.is_maintoc:
            has_toc = 1
        else:
            has_toc = len(parsed_xml.xpath('//grp[@name="TOC"]'))
        
        if verbose:
            print (f"\t...split book: adding page info for {artInfo.art_id} to the database split book page tracking table")
            
        for pgnum in pagebreaks:
            page_id = opasDocuments.PageNumber(pgNum=pgnum).pageID()
            split_book_data.add_splitbook_page_record(artInfo.art_id,
                                                      page_id=page_id, 
                                                      has_biblio=has_biblio, 
                                                      has_toc=has_toc, 
                                                      full_filename=artInfo.filename
                                                      )

def tag_keywords(parsed_xml, artInfo, ocd, pretty_print=False, verbose=False):
    """
    Keywords in KBD3 instances are cs lists, tag each term
    """
    nodes = parsed_xml.xpath("/pepkbd3//artkwds") # PYXTree.getElements(ALL, E("artkwds"), childSpec=E("impx"), notChild=1)
    # PYXTree.keywordListImpx = None
    for node in nodes:
        markedup_list = []
        try:
            keywords = node.text.split(",")
        except Exception as e:
            if node.text is None:
                msg = f"Keyword list may already be marked up with impx. Leaving as is: {ET.tostring(node)}"
                print (msg)
            else:
                logger.warning(f"Error handling Keyword list {e}. Leaving as is.")
        else:
            if verbose:
                print (f"\t...Keyword markup added: {node.text}")
            count = len(keywords)
            for keyword in keywords:
                markup = f'<impx type="KEYWORD">{keyword.strip()}</impx>'
                markedup_list.append(markup)
    
            if count > 0:
                keyword_str = "".join(markedup_list)
                keywords = f"<artkwds>{keyword_str}</artkwds>"
                newnode = ET.XML(keywords)
                try:
                    node.getparent().replace(node, newnode)
                except Exception as e:
                    logger.warning(f"Can't replace artkwds node {e}")
    
def update_artinfo_in_instance(parsed_xml, artInfo, ocd, pretty_print=False, verbose=False):
    """
    Using the database info (e.g., products table), supplement update the article information
       in the XML
       
    """
    parsed_xml.attrib["procby"] = f"{programNameShort}.{__version__}"
    xml_artinfo = parsed_xml.find("artinfo")
    source_row = ocd.get_sources(src_code=artInfo.src_prodkey, get_counts=False)

    try:
        source_info = source_row[1][0]
        # gather info needed about source
        if artInfo.src_code is not None:
            if source_info["ISSN"] is not None:
                xml_artinfo.attrib["ISSN"] = source_info["ISSN"]
            else:
                if artInfo.art_issn is not None:
                    xml_artinfo.attrib["ISSN"] = artInfo.art_issn
                else:
                    # logic changed 2022-09-30 to prioritize existing isbn, and then isbn-10 from 
                    # the productbase (like the local process I ran)
                    if artInfo.art_isbn is not None:
                        xml_artinfo.attrib["ISBN"] = artInfo.art_isbn
                    elif source_info["ISBN-10"] is not None:
                        xml_artinfo.attrib["ISBN"] = source_info["ISBN-10"]
                    elif source_info["ISBN-13"] is not None:
                        xml_artinfo.attrib["ISBN"] = source_info["ISBN-13"]
                    else:
                        logger.warning(f"Source Code: {artInfo.src_code} but no ISSN or ISBN")

    except Exception as e:
        print (e)
    
    if artInfo.art_id is not None: xml_artinfo.set("id", artInfo.art_id)
    if artInfo.art_type is not None: xml_artinfo.set("arttype", artInfo.art_type)
    if artInfo.start_sectname is not None: xml_artinfo.set("newsecnm", artInfo.start_sectname)
    if artInfo.start_sectlevel is not None: xml_artinfo.set("newseclevel", artInfo.start_sectlevel)
    if artInfo.art_vol_suffix is not None:
        xml_artvol = parsed_xml.xpath("//artvol")
        if xml_artvol != []:
            artvol = xml_artvol[0]
            actual = str(artInfo.art_vol_int)
            artvol.text = actual + artInfo.art_vol_suffix
            # GW keeps the suffix in the actual attribute.
            if artInfo.art_vol_suffix == "S" and artInfo.src_code == "GW":
                artvol.attrib["actual"] = artvol.text
            else:
                artvol.attrib["actual"] = actual
                
            if verbose:
                print (f"\t...Volume suffix required: set in XML to {artvol.text} and attrib 'actual' to {actual}")

    artbkinfo = parsed_xml.xpath("//artbkinfo")
    if artbkinfo != []:
        artbkinfo = artbkinfo[0]
        artbkinfo_next = artbkinfo.attrib.get("next", None)
        artbkinfo_prev = artbkinfo.attrib.get("prev", None)
        artbkinfo_extract = artbkinfo.attrib.get("extract", None)
        
        if artbkinfo_next is not None:
            artbkinfo_next = str(opasLocator.Locator(artbkinfo_next))
            artbkinfo.set("next", artbkinfo_next)
        if artbkinfo_prev is not None:
            artbkinfo_prev = str(opasLocator.Locator(artbkinfo_prev))
            artbkinfo.set("prev", artbkinfo_prev)
        if artbkinfo_extract is not None:
            artbkinfo_extract = str(opasLocator.Locator(artbkinfo_extract))
            artbkinfo.set("extract", artbkinfo_extract)
        
    xml_artauth = parsed_xml.findall("artinfo/artauth")
    for art_auth in xml_artauth:
        art_auth.set("hidden", art_auth.get("hidden", "false"))

    xml_artauth_aut = parsed_xml.xpath("//aut")
    for aut in xml_artauth_aut:
        # print(aut)
        if aut.attrib.get("authindexid", None) is None:
            author_id = opasXMLPEPAuthorID.getStandardAuthorID(nfirst=aut.findtext("nfirst"), nmid=aut.findtext("nmid"), nlast=aut.findtext("nlast"))
            aut.set("authindexid", author_id)
            # set default attributes if not seet
            aut.set("listed", aut.get("listed", "true"))
            aut.set("role", aut.get("role", "author"))
        
#------------------------------------------------------------------------------------------------------
def xml_update(parsed_xml, artInfo, ocd, add_glossary_list=False, markup_terms=True,
               pretty_print=False, verbose=False, no_database_update=False):
    """
    Driving Logic to convert KBD3 to EXP_ARCH1 per PEP requirements
    """
    
    ret_val = None
    ret_status = True

    global gDbg1, gDbg2
    if not verbose:
        gDbg1 = False
        gDbg2 = False
    #else:
        #print ("\t...Converting! Keyboarded XML to processed/precompiled XML.")
        
    # write issn and id to artinfo
    update_artinfo_in_instance(parsed_xml, artInfo, ocd)
    
    tag_keywords(parsed_xml, artInfo, ocd, pretty_print=False, verbose=False)
    
    # normalize local ids by adding base id to local ids.
    #     Not needed with current client for some impx rx values:
    #     glossary references.  They work with just the id. see PEPGRANTVS.001.0003A for examples
    #     UNUSED - Delete in late January with functions
    # add_base_id_to_local_ids(parsed_xml, xpathid="//be", xpathref="//bx/@r", base_id=artInfo.art_id, verbose=verbose)
    # normalize_local_ids(parsed_xml, verbose=verbose)
    
    # add nextpgnum with id to n, possibly filling in prefixused
    pgnbr_add_next_attrib(parsed_xml)

    # Walk through biblio, add links
    if not no_database_update:
        update_biblio(parsed_xml, artInfo, ocd, verbose=verbose)
    
    # Add page number markup (next and prev page info on page breaks)
    add_page_number_markup(parsed_xml)

    # Get split book table info from db
    split_book_data = opasXMLSplitBookSupport.SplitBookData(database_connection=ocd)
    
    # if this is a split book, add pg numbers to split book table
    if not no_database_update:
        add_pagenbrs_to_splitbook_table(parsed_xml, artInfo, ocd, split_book_data, verbose=verbose)
            
    # ------------------------------------------------------
    #  pgx (link) handling routines
    # ------------------------------------------------------
    
    # add pgx links for books and if necessary to split book instances
    if artInfo.src_is_book or artInfo.src_code in loaderConfig.NON_BOOK_SRC_CODES_FOR_PGX_LINKING:
        pgx_add_rx_book_links(parsed_xml, ocd, artInfo=artInfo,
                              split_book_data=split_book_data, verbose=verbose)
        
    # pgxPreProcessing(parsed_xml, ocd, artInfo=artInfo, split_book_data=split_book_data, verbose=verbose)

    pgx_add_rx_jump_via_biblio_entry(parsed_xml, ocd, artInfo=artInfo, split_book_data=split_book_data, verbose=verbose)
    
    # now the doGlossaryMarkup returns a dictionary of terms and counts, so potentially a term list could be appended to
    #  the xml rather than, or in addition to, marking up the terms within.
    total_count, term_dict = glossEngine.doGlossaryMarkup(parsed_xml, pretty_print=pretty_print, markup_terms=markup_terms, verbose=verbose)
    if add_glossary_list:
        parser = ET.XMLParser(encoding='utf-8', recover=True, resolve_entities=False, load_dtd=False)
        term_json = json.dumps(term_dict)
        pep_addon = f'<unit type="glossary_term_dict"><!-- {term_json} --></unit>'
        new_unit = ET.fromstring(pep_addon, parser)
        parsed_xml.append(new_unit)
    
    web_links = parsed_xml.xpath("/pepkbd3//autaff//url") 
    logger.info("\t...Processing url links.")
    for url in web_links:
        urltext = "mailto:" + url.text
        url.tag = "webx"
        url.attrib["url"] = urltext
    
    # if doc part of SE/GW this section adds related IDs for the GW and SE concordance feature.
    if artInfo.src_code in ["GW", "SE"]:
        if verbose: print (f"\t...Starting SE/GW Concordance Tagging")
        paraGWSEConcordance = opasXMLParaLanguageConcordance.PEPGWSEParaConcordance(ocd=ocd)
        paraGWSEConcordance.addRelatedIDs(parsed_xml=parsed_xml, artInfo=artInfo, verbose=verbose) # pass in database instance
    
    ret_val = parsed_xml

    return ret_val, ret_status

