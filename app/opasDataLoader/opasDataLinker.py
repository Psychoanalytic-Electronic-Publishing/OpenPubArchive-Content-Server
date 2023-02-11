#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#Copyright 2012-2018 Neil R. Shapiro

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2023"
__license__     = "Apache 2.0"
__version__     = "2023.0211/v1.0.007"   
__status__      = "Development"

programNameShort = "opasDataLinker"

border = 80 * "*"
print (f"""\n
        {border}
            {programNameShort} - Open Publications-Archive Server (OPAS) Reference Linker
                            Version {__version__}
        {border}
        """)

help_text = (
    fr""" 
        - Read the api_biblioxml table and link articles in PEP.
        
        Example Invocation:
                $ python opasDataLinker.py
                
        Important option choices:
         -h, --help         List all help options
         -a                 Process all records
         --key:             Do just records with the specified PEP locator (e.g., --key AIM.076.0309A)
""")
    
import sys
sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')

# import string, sys, copy, re
import logging
logger = logging.getLogger(__name__)
# import re
# import time
from optparse import OptionParser
from loggingDebugStream import log_everywhere_if

import opasConfig
# import opasGenSupportLib as opasgenlib
import opasBiblioSupport
import opasCentralDBLib
import PEPBookInfo
known_books = PEPBookInfo.PEPBookInfo()

# import opasPySolrLib
# from opasLocator import Locator
#import opasXMLHelper
# import opasXMLProcessor
#import opasArticleIDSupport
# import models
# import PEPJournalData
# import PEPReferenceParserStr

gDbg1 = 0	# details
gDbg2 = 1	# High level

LOWER_RELEVANCE_LIMIT = 35

ocd = opasCentralDBLib.opasCentralDB()
import lxml.etree as ET
import lxml
sqlSelect = ""

def walk_through_reference_set(ocd=ocd,
                               sql_set_select = "select * from api_biblioxml where art_id='CPS.031.0617A' and ref_local_id='B022'",
                               set_description = "All",
                               verbose=True
                               ):
    """
    >> walk_set = "SingleTest1", "select * from api_biblioxml where art_id='CPS.031.0617A' and ref_local_id='B024'"
    >> walk_through_reference_set(ocd, sql_set_select=walk_set[1], set_description=walk_set[0])

    >> walk_set = "SingleTest1", "select * from api_biblioxml where art_id='CPS.031.0617A' and ref_local_id='B022'"
    >> walk_through_reference_set(ocd, sql_set_select=walk_set[1], set_description=walk_set[0])

    >> walk_set = "Freud", "select * from api_biblioxml where ref_rx is NULL and ref_authors like '%Freud%' and ref_rx_confidence=0"
    >> walk_through_reference_set(ocd, sql_set_select=walk_set[1], set_description=walk_set[0])
    
    """
    fname = "walk_through_reference_set"
    ocd.open_connection(caller_name=fname) # make sure connection is open
    ret_val = None
    #artInfo = opasArticleIDSupport.ArticleInfo(art_id="IJP.100.0001A",
                                               #art_year="2022")
    
    parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
    if ocd.db is not None:
        # rows = self.SQLSelectGenerator(sqlSelect)
        biblio_entries = ocd.get_references_select_biblioxml(sql_set_select)
        counter = 0
        for ref_model in biblio_entries:
            counter += 1
            print (80*"-")
            print (f"{counter} Analyzing {ref_model.art_id}/{ref_model.ref_local_id}: {ref_model.ref_xml}")
            parsed_ref = ET.fromstring(ref_model.ref_xml, parser=parser)
            bib_entry = opasBiblioSupport.BiblioEntry(ref_model.art_id, db_bib_entry=ref_model)
            art_id = bib_entry.art_id
            if bib_entry.ref_rx is None:
                if verbose: print (f"Ref text: {bib_entry.ref_text}")
                bib_match = bib_entry.lookup_title_in_db(ocd)
                bib_match = bib_entry.identify_heuristic(verbose=verbose)
                if bib_match.ref_rx is not None:
                    if verbose: print (f"\t...Matched Reference ID: {bib_match.ref_rx} Confidence {bib_match.ref_rx_confidence} Link Updated: {bib_match.link_updated}")
                # to watch
                #if verbose: time.sleep(.5) # Pause
            else:
                if verbose: print (f"Checking ref_rx from xml for accuracy")
                bib_match = bib_entry.compare_to_database(ocd)
                bib_match = bib_entry.lookup_more_exact_artid_in_db(ocd)
                if verbose: print (f"\t...Reference ID: {bib_entry.ref_rx} Confidence {bib_entry.ref_rx_confidence} Link Updated: {bib_match.link_updated} Record Updated: {bib_match.record_updated}")
                #if ref_rx is not None:
                    #success = bib_entry.update_db_links(art_id,
                                                        #local_id,
                                                       #verbose=True)

            if bib_entry.ref_rx is None and bib_match.ref_rx is not None:
                bib_entry.update_bib_entry(bib_match)

            if bib_entry.link_updated or bib_entry.record_updated:
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
                if bib_entry.record_updated or bib_match.link_updated:
                    if bib_match.link_updated:
                        print (f"\t...{match1} {match2} considered a match ({bib_match.ref_link_source}) Updating DB record.")
                    else:
                        print (f"\t...Record updated. Updating DB record.")
                    success = ocd.save_ref_to_biblioxml_table(bib_entry)                

                #if bib_match.link_updated or bib_entry.record_updated:
                    #success = ocd.update_biblioxml_links(bib_entry.art_id,
                                                         #bib_entry.ref_local_id,
                                                         #bib_entry=bib_match, 
                                                         #rx=bib_match.ref_rx,
                                                         #rx_confidence=bib_match.ref_rx_confidence,
                                                         #rxcfs=bib_match.ref_rxcf,
                                                         #rxcfs_confidence=bib_match.ref_rxcf_confidence,
                                                         #rx_link_source=bib_match.link_source,
                                                         #ref_xml=bib_match.ref_xml
                                                        #)
        
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

def test_runs():
    do_walk_set = True
    do_clean = False
    do_doctest = False
    walk_set = [
                  ("Freud", "select * from api_biblioxml where ref_rx is NULL and ref_authors like '%Freud%' and ref_rx_confidence=0"),
                  ("FreudTest", "select * from api_biblioxml where art_id LIKE 'APA.017.0421A'")
               ]
        
    if do_walk_set:
        walk_through_reference_set(ocd, set_description=walk_set[1][0], sql_set_select=walk_set[1][1])

    if do_clean:
        clean_set = "Freud", "select * from api_biblioxml where ref_rx is not NULL and ref_authors like '%Freud%'"
        clean_reference_links(ocd, clean_set[1])
    
    if do_doctest:
        import doctest
        doctest.testmod(optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
    
    print ("Fini. Tests or Processing complete.")
    
# -------------------------------------------------------------------------------------------------------
# run it!
if __name__ == "__main__":
    global options  # so the information can be used in support functions

    options = None
    parser = OptionParser(usage="%prog [options] - PEP Data Linker", version=f"%prog ver. {__version__}")

    parser.add_option("-a", "--all", action="store_true", dest="process_all", default=False,
                      help="Option to force all records to be checked.")

    parser.add_option("--after", dest="added_after", default=None,
                      help="Check records created or modifed after this datetime (use YYYY-MM-DD format).")

    parser.add_option("--key", dest="file_key", default=None,
                      help="Key for a single file to load, e.g., AIM.076.0269A.  Use in conjunction with --sub for faster processing of single files on AWS")

    parser.add_option("-l", "--loglevel", dest="logLevel", default=logging.ERROR,
                      help="Level at which events should be logged (DEBUG, INFO, WARNING, ERROR")

    # --load option still the default.  Need to keep for backwards compatibility, at least for now (7/2022)

    parser.add_option("--test", dest="testmode", action="store_true", default=False,
                      help="Run Doctests")

    parser.add_option("--verbose", action="store_true", dest="display_verbose", default=False,
                      help="Display status and operational timing info as load progresses.")

    (options, args) = parser.parse_args()
    # set toplevel logger to specified loglevel
    logger = logging.getLogger()
    logger.setLevel(options.logLevel)
    # get local logger
    logger = logging.getLogger(programNameShort)
    
    print (help_text)

    process_matching_query = "select * from api_biblioxml where art_id RLIKE '%s'"
    process_bydate_afer_query = """select * from api_biblioxml as bib, api_articles as art
                                   where bib.art_id=art.art_id
                                   and art.last_update >= '%s'"""
    
    if options.testmode:
        import doctest
        doctest.testmod()
        print ("Fini. opasDataLoader Tests complete.")
        sys.exit()

    if options.file_key:
        query = process_matching_query % options.file_key

    if options.process_all:
        query = process_matching_query % '.*'

    if options.added_after:
        query = process_bydate_afer_query % options.added_after

        
        
    walk_through_reference_set(ocd, set_description=f"Key: {options.file_key}", sql_set_select=query)
    print ("Finished!")
        