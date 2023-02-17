#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#Copyright 2012-2018 Neil R. Shapiro

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2023"
__license__     = "Apache 2.0"
__version__     = "2023.0216/v1.0.008"   
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
import time
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
        cumulative_time_start = time.time()
        # rows = self.SQLSelectGenerator(sqlSelect)
        biblio_entries = ocd.get_references_select_biblioxml(sql_set_select)
        print (f"Scanning {len(biblio_entries)} references in api_biblioxml to find new links.")
        counter = 0
        updated_record_count = 0
        for ref_model in biblio_entries:
            reference_time_start = time.time()
            counter += 1
            print (80*"-")
            one_line_text = ""
            if ref_model.ref_text:
                one_line_text = ref_model.ref_text.replace('\n', '')
            last_updated = ref_model.last_update.strftime("%m/%d/%Y")
            print (f"{counter}:Analyzing Record Last Updated:{last_updated} ID:{ref_model.art_id}/{ref_model.ref_local_id}\nRef:{one_line_text}")
            # parsed_ref = ET.fromstring(ref_model.ref_xml, parser=parser)
            bib_entry = opasBiblioSupport.BiblioEntry(ref_model.art_id, db_bib_entry=ref_model, verbose=verbose)
            art_id = bib_entry.art_id
            if not bib_entry.ref_title:
                # ignore this one from now on
                if verbose: print (f"\t...No title found, ignoring this one from now on.")
                bib_entry.ref_rx_confidence = opasConfig.RX_CONFIDENCE_NEVERMORE
                bib_entry.link_updated = True                        
            else:
                if bib_entry.ref_rx is None:
                    if verbose and bib_entry.ref_text:
                        one_line_text = bib_entry.ref_text.replace('\n','')
                    bib_entry.lookup_title_in_db(ocd)
                    bib_entry.identify_heuristic(verbose=verbose)
                    if bib_entry.ref_rx is not None:
                        if verbose: print (f"\t...Matched Reference ID: {bib_entry.ref_rx} Confidence {bib_entry.ref_rx_confidence} Link Updated: {bib_match.link_updated}")
                elif bib_entry.ref_rx == .01:
                    if verbose: print (f"\t...Skipping Marked 'RX_CONFIDENCE_NEVERMORE (.01)' Reference ID: {bib_match.ref_rx} Confidence {bib_match.ref_rx_confidence}")
                else:
                    if verbose: print (f"Checking ref_rx from xml for accuracy")
                    bib_entry.compare_to_database(ocd)
                    bib_entry.lookup_more_exact_artid_in_db(ocd)
                    if verbose: print (f"\t...Reference ID: {bib_entry.ref_rx} Confidence {bib_entry.ref_rx_confidence} Link Updated: {bib_entry.link_updated} Record Updated: {bib_entry.record_updated}")

                if bib_entry.ref_rx is None and bib_entry.ref_rx is not None:
                    bib_entry.update_bib_entry(bib_entry)

            if bib_entry.link_updated or bib_entry.record_updated:
                updated_record_count += 1
                if bib_entry.link_updated:
                    print (f"\t...Links updated.  Updating DB: rx:{bib_entry.ref_rx} rxcf{bib_entry.ref_rxcf} source: ({bib_entry.ref_link_source})")
                else:
                    print (f"\t...Record updated. Updating DB.")
                success = ocd.save_ref_to_biblioxml_table(bib_entry)                
                if options.display_verbose: print(f"\t...Time: {time.time() - reference_time_start:.4f} seconds.")
                
    ocd.close_connection(caller_name=fname) # make sure connection is closed
    timeEnd = time.time()
    elapsed_seconds = timeEnd-cumulative_time_start # actual processing time going through files
    elapsed_minutes = elapsed_seconds / 60
    if counter > 0:
        msg = f"Files per elapsed min: {counter/elapsed_minutes:.4f}"
        logger.info(msg)
        print (msg)
    
    print (80 * "-")
    msg = f"Finished! {updated_record_count} records updated from {counter} references. Total scan/update time: {elapsed_seconds:.2f} secs ({elapsed_minutes:.2f} minutes.) "
    logger.info(msg)
    print (msg)
    
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
                      help="Check art biblios created or modifed after this datetime (use YYYY-MM-DD format).")

    parser.add_option("--before", dest="scanned_before", default=None,
                      help="Check records scanned before this datetime (use YYYY-MM-DD format).")

    parser.add_option("--key", dest="file_key", default=None,
                      help="Key for a single file to load, e.g., AIM.076.0269A.  Use in conjunction with --sub for faster processing of single files on AWS")

    parser.add_option("-u", "--unlinked", action="store_true", dest="unlinked_refs", default=False,
                      help="Check unlinked references")

    parser.add_option("-l", "--loglevel", dest="logLevel", default=logging.ERROR,
                      help="Level at which events should be logged (DEBUG, INFO, WARNING, ERROR")

    parser.add_option("--where", dest="where_condition", default=None,
                      help="Add your own SQL clause to the search of api_biblioxml")

    parser.add_option("-r", "--reverse", dest="run_in_reverse", action="store_true", default=False,
                      help="Whether to run the selected files in reverse order of last update (otherwise by art_id/local_id)")

    # --load option still the default.  Need to keep for backwards compatibility, at least for now (7/2022)

    parser.add_option("--test", dest="testmode", action="store_true", default=False,
                      help="Run Doctests")

    parser.add_option("--verbose", action="store_true", dest="display_verbose", default=True,
                      help="Display status and operational timing info as load progresses.")

    (options, args) = parser.parse_args()
    # set toplevel logger to specified loglevel
    logger = logging.getLogger()
    logger.setLevel(options.logLevel)
    # get local logger
    logger = logging.getLogger(programNameShort)
    
    if options.display_verbose: print (help_text)
    if options.unlinked_refs:
        print ("Checking only unlinked--rx and rxcf--records.")
        unlinked_ref_clause = 'and ref_rx is Null and ref_rxcf is Null'
    else:
        unlinked_ref_clause = ''

    skip_for_incremental_scans = "and skip_incremental_scans is NULL"

    biblio_refs_matching_artid = f"""select *
                                     from api_biblioxml
                                     where art_id RLIKE '%s'
                                     and ref_rx_confidence != {opasConfig.RX_CONFIDENCE_NEVERMORE}
                                     {skip_for_incremental_scans}
                                     {unlinked_ref_clause}
                                     %s
                                  """
    
    biblios_for_articles_after = f"""select *
                                     from api_biblioxml as bib, api_articles as art
                                     where bib.art_id=art.art_id
                                     {skip_for_incremental_scans}
                                     and art.last_update >= '%s'
                                     and ref_rx_confidence != {opasConfig.RX_CONFIDENCE_NEVERMORE}
                                     {unlinked_ref_clause}
                                     %s
                                  """
    
    biblio_refs_updated_before = f"""select *
                                     from api_biblioxml as bib
                                     where bib.last_update < '%s'
                                     {skip_for_incremental_scans}
                                     and ref_rx_confidence != {opasConfig.RX_CONFIDENCE_NEVERMORE}
                                     {unlinked_ref_clause}
                                     %s
                                  """

    biblio_refs_advanced_query = f"""select *
                                     from api_biblioxml as bib
                                     where ref_rx_confidence != {opasConfig.RX_CONFIDENCE_NEVERMORE}
                                     {skip_for_incremental_scans}
                                     {unlinked_ref_clause}
                                     %s
                                  """
    
    if options.run_in_reverse:
        print ("Scanning records by last update--oldest first.")
        addon_to_query = "order by last_update ASC" # oldest first
    else:
        addon_to_query = "order by art_id ASC, ref_local_id ASC"

    if options.testmode:
        import doctest
        doctest.testmod()
        print ("Fini. opasDataLoader Tests complete.")
        sys.exit()

    if options.file_key:
        query = biblio_refs_matching_artid % (options.file_key, addon_to_query)

    if options.process_all:
        query = biblio_refs_matching_artid % ('.*', addon_to_query)

    if options.added_after:
        query = biblios_for_articles_after % (options.added_after, addon_to_query)

    if options.scanned_before:
        query = biblio_refs_updated_before % (options.scanned_before, addon_to_query)
        
    if options.unlinked_refs:
        query = biblio_refs_updated_before % (options.scanned_before, addon_to_query)

    if options.where_condition:
        query = biblio_refs_advanced_query % (f" AND {options.where_condition}")
    
    walk_through_reference_set(ocd, set_description=f"Key: {options.file_key}", sql_set_select=query)
    print ("Finished!")
    