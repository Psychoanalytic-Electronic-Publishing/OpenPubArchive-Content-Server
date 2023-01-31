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
known_books = PEPBookInfo.PEPBookInfo()
import PEPReferenceParserStr

gDbg1 = 0	# details
gDbg2 = 1	# High level

LOWER_RELEVANCE_LIMIT = 35

ocd = opasCentralDBLib.opasCentralDB()
import lxml.etree as ET
import lxml
sqlSelect = ""
parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)

def walk_through_reference_set(ocd=ocd,
                               sql_set_select = "select * from api_biblioxml where art_id='CPS.031.0617A'",
                               set_description = "All"
                               ):
    """
    >> walk_set = "SingleTest1", "select * from api_biblioxml where art_id='CPS.031.0617A' and ref_local_id='B024'"
    >> walk_through_reference_set(ocd, sql_set_select=walk_set[1], set_description=walk_set[0])

    >>> walk_set = "SingleTest1", "select * from api_biblioxml where art_id='CPS.031.0617A'"
    >>> walk_through_reference_set(ocd, sql_set_select=walk_set[1], set_description=walk_set[0])

    >> walk_set = "Freud", "select * from api_biblioxml where ref_rx is NULL and ref_authors like '%Freud%'"
    >> walk_through_reference_set(ocd, sql_set_select=walk_set[1], set_description=walk_set[0])
    
    """
    fname = "walk_through_reference_set"
    ocd.open_connection(caller_name=fname) # make sure connection is open
    ret_val = None
    #artInfo = opasArticleIDSupport.ArticleInfo(art_id="IJP.100.0001A",
                                               #art_year="2022")
    
    if ocd.db is not None:
        # rows = self.SQLSelectGenerator(sqlSelect)
        biblio_entries = ocd.get_references_select_biblioxml(sql_set_select)
        counter = 0
        for ref in biblio_entries:
            counter += 1
            print (ref.ref_text)
            parsed_ref = ET.fromstring(ref.ref_xml, parser=parser)
            bib_entry = opasBiblioSupport.BiblioEntry(ref.art_id, db_bib_entry=ref)
            art_id = bib_entry.art_id
            if bib_entry.ref_rx is None:
                print (bib_entry.ref_text)
                bib_match = bib_entry.lookup_title_in_db(ocd)
                if bib_match.ref_rx is None:
                    bib_match = bib_entry.identify_heuristic()
                else:
                    print (f"\t..Reference ID: {bib_match.ref_rx} Confidence {bib_match.ref_rx_confidence} Link Updated: link")
                    #time.sleep(2)
            else:
                bib_match = bib_entry.compare_to_database(ocd)
                bib_match = bib_entry.lookup_more_exact_artid_in_db(ocd)
                print (f"\t..Reference ID: {bib_entry.ref_rx} Confidence {bib_entry.ref_rx_confidence} Link Updated: link")
                #if ref_rx is not None:
                    #success = bib_entry.update_db_links(art_id,
                                                        #local_id,
                                                       #verbose=True)

            if bib_entry.ref_rx is None and bib_match.ref_rx is not None:
                bib_entry.update_bib_entry(bib_match)

            if bib_entry.link_updated:
                # make sure database isn't better
                bib_match = bib_entry.compare_to_database(ocd)
                bib_match = bib_entry.lookup_more_exact_artid_in_db(ocd)
                if bib_match.ref_rx is not None:
                    match1 = f"rx: {bib_match.ref_rx} "
                else:
                    match1 = ""
                if bib_match.ref_rxcf is not None:
                    match2 = f"rxcf: {bib_match.ref_rxcf} "
                else:
                    match2 = ""
                print (f"\t...{match1} {match2} considered a match ({bib_match.link_source}) Updating DB record.")
                if bib_match.link_source != "database" and bib_match.link_updated == True:
                    success = ocd.update_biblioxml_links(bib_entry.art_id,
                                                         bib_entry.ref_local_id,
                                                         bib_entry=bib_match, 
                                                         #rx=bib_match.ref_rx,
                                                         #rx_confidence=bib_match.ref_rx_confidence,
                                                         #rxcfs=bib_match.ref_rxcf,
                                                         #rxcfs_confidence=bib_match.ref_rxcf_confidence,
                                                         #rx_link_source=bib_match.link_source,
                                                         #ref_xml=bib_match.ref_xml
                                                        )
        
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
                    success = ocd.update_biblioxml_links(art_id, bib_local_id,
                                                          rx=None,
                                                          rx_confidence=0,
                                                          verbose=True)

    ocd.close_connection(caller_name=fname) # make sure connection is closed
    
    # return session model object
    return ret_val # None or Session Object

# --------------------------------------------------------------------------------------------
# TBD: These next two routines should now be handled automatically by biblioxml.  
#    Delete in a future build after confirming
# 
# --------------------------------------------------------------------------------------------
#def check_for_locator_page_mismatch(self, rx: str, rx_confidence: float):
    #ret_val = (1, rx, rx_confidence)
    #if rx_confidence == .99:
        #ret_val = (1, rx, opasConfig.RX_CONFIDENCE_EXISTS)
    #elif rx_confidence != 1:
        #ret_val = (1, rx, opasConfig.RX_CONFIDENCE_EXISTS)
        #if not self.article_exists(rx):
            #newLocator = Locator(rx)
            #if newLocator.articleID() is not None:
                #newLocator.pgStart -= 1
                #if self.article_exists(str(newLocator)):
                    #ret_val = (2, newLocator.articleID(), opasConfig.RX_CONFIDENCE_PAGE_ADJUSTED)
                #else:
                    #ret_val = (0, rx, rx_confidence)
            #else:
                #ret_val = (0, rx, rx_confidence)
                
    ## validation check values:
    ## 0 = Not valid, No fix  
    ## 1 = Already correct
    ## 2 = Fixed page mismatch, 
    #return ret_val # (validation check, locator, confidence)

#def fix_pgstart_errors_in_reflinks(ocd=ocd,
                                   #sql_set_select = "select * from api_biblioxml where ref_rx is not NULL",
                                   #set_description = "All"
                                   #):
    #"""
    #Checks for a bad locator and tries to fix it if
      #it's a page start error.  Otherwise leaves it alone
    
    #"""
    #fname = "find_start_page_errors"
    #ocd.open_connection(caller_name=fname) # make sure connection is open
    #ret_val = 0
    ##artInfo = opasArticleIDSupport.ArticleInfo(art_id="IJP.100.0001A",
                                               ##art_year="2022")
    
    #if ocd.db is not None:
        ## rows = self.SQLSelectGenerator(sqlSelect)
        #curs = ocd.db.cursor(buffered=True, dictionary=True)
        #curs.execute(sql_set_select)
        #warnings = curs.fetchwarnings()
        #if warnings:
            #for warning in warnings:
                #logger.warning(warning)
        
        #rows = curs.fetchall()
        #print (f"Checking {len(rows)} rows")
        #for row in rows:
            #art_id = row["art_id"]
            #ref_local_id = row["ref_local_id"]
            #ref_rx = row["ref_rx"]
            #ref_rx_confidence = row["ref_rx_confidence"]
            #ref_text = row["ref_text"]
            #if ref_rx:
                #result, rx, rx_confidence = check_for_locator_page_mismatch(ref_rx, ref_rx_confidence)
                #if result == 2:
                    ## correct it
                    #print (f"\t...{art_id}/{ref_local_id} - {ref_rx} doesn't exist. Chgto:{newLocator} for {ref_text}.")
                    #success = ocd.update_biblioxml_links(art_id, ref_local_id,
                                                          #rx=str(rx),
                                                          #rx_confidence=rx_confidence,
                                                          #verbose=False)
                    #ret_val += 1
                #elif result == 1:
                    #if rx_confidence != ref_rx_confidence:
                        #success = ocd.update_biblioxml_links(art_id, ref_local_id,
                                                              #rx=str(rx),
                                                              #rx_confidence=rx_confidence,
                                                              #verbose=False)
                        ##print (f"Updated {rx_confidence} != {ref_rx_confidence}")
                        
                    
    #print (f"Corrected {ret_val} biblioxml records where rx was off by one page!")
    #ocd.close_connection(caller_name=fname) # make sure connection is closed
    
    ## return session model object
    #return ret_val # number of updated rows
# --------------------------------------------------------------------------------------------
# End TBD
# --------------------------------------------------------------------------------------------

if __name__ == "__main__":

    do_walk_set = False
    do_clean = False
    do_doctest = True

    if do_walk_set:
        walk_through_reference_set(ocd, sql_set_select=walk_set[1], set_description=walk_set[0])

    if do_clean:
        clean_set = "Freud", "select * from api_biblioxml where ref_rx is not NULL and ref_authors like '%Freud%'"
        clean_reference_links(ocd, clean_set[1])
    
    if do_doctest:
        import doctest
        doctest.testmod(optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
    
    print ("Fini. Tests or Processing complete.")