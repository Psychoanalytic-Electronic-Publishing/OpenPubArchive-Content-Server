#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path

folder = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
if folder == "tests": # testing from within WingIDE, default folder is tests
    sys.path.append('../libs')
    sys.path.append('../config')
    sys.path.append('../../app')
else: # python running from should be within folder app
    sys.path.append('./libs')
    sys.path.append('./config')

import unittest
from datetime import datetime
import opasCentralDBLib

from unitTestConfig import base_api, base_plus_endpoint_encoded

class TestSQLStructure(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.   
    """
    def test_1_testviews(self):
        ocd = opasCentralDBLib.opasCentralDB()
        dbok = ocd.open_connection(caller_name="test_views") # make sure connection is open
        assert (dbok == True)
        # Configuration Check: Development, xps->opastest2, xps->opascentral
        # 21 tables, 48 views
        tables = [
                  # 14 runtime tables (used by api/server)
                  "api_articles",
                  "api_articles_removed", 
                  "api_biblioxml2", 
                  "api_client_apps",
                  "api_client_configs",
                  "api_docviews",
                  "api_endpoints",
                  "api_messages",
                  "api_productbase",
                  "api_session_endpoints",
                  "api_session_endpoints_not_logged_in", 
                  "api_sessions",
                  "article_tracker",
                  "artstat",
                  # 7 opasloader tables
                  "opasloader_glossary_group_ids", # (used indirectly by vw_opasloader_glossary_group_terms)
                  "opasloader_glossary_terms", # (used indirectly by vw_interactive_glossary_details and vw_opasloader_glossary_group_terms)
                  "opasloader_gwpageconcordance", 
                  "opasloader_gwseparaconcordance", 
                  "opasloader_gwtitleconcordance",
                  "opasloader_refcorrections", 
                  "opasloader_splitbookpages",
                  # 7 vws used by api/server, directly and indirectly)
                  "vw_api_jrnl_vols", 
                  "vw_api_messages",
                  "vw_api_productbase", 
                  "vw_api_productbase_instance_counts", 
                  "vw_api_sourceinfodb",
                  "vw_instance_counts_books", #  (used indirectly, by vw_api_productbase_instance_counts)
                  "vw_instance_counts_src",   #  (used indirectly, by vw_api_productbase_instance_counts)
                  # 6 vw_interactive views
                  "vw_interactive_active_sessions",               # deprecated
                  "vw_interactive_biblio_checker",
                  "vw_interactive_glossary_details", # not used in code
                  "vw_interactive_latest_session_activity", # not used in code
                  "vw_interactive_stat_bibliolinks",
                  "vw_interactive_table_counts", 
                  # 4 vw_opasloader
                  "vw_opasloader_article_firstsectnames",
                  "vw_opasloader_article_sectnames",
                  "vw_opasloader_glossary_group_terms", # used in PEPGlossaryRecognitionEngine
                  "vw_opasloader_splitbookpages", # table opasloader_splitbookpages used directly (but keep view for later)
                  # 18 vw_reports views
                  "vw_reports_charcounts",
                  "vw_reports_charcounts_details",
                  "vw_reports_charcounts_sub_books_bysrccode",
                  "vw_reports_charcounts_sub_books_byvol",
                  "vw_reports_charcounts_sub_books_selectioncriteria",
                  "vw_reports_charcounts_sub_booksall", 
                  "vw_reports_charcounts_sub_byjournalyear", 
                  "vw_reports_charcounts_sub_jrnl_selectioncriteria", 
                  "vw_reports_charcounts_sub_jrnlgroups", 
                  "vw_reports_document_activity", 
                  "vw_reports_document_views", 
                  "vw_reports_session_activity",
                  "vw_reports_session_activity_desc", 
                  "vw_reports_session_activity_not_logged_in", 
                  "vw_reports_session_activity_not_logged_in_desc", 
                  "vw_reports_session_activity_with_null_user_id", 
                  "vw_reports_session_activity_with_user_id", 
                  "vw_reports_user_searches",
                  #  13 vw_stat views
                  "vw_stat_cited_crosstab2",
                  "vw_stat_cited_crosstab_with_details2",
                  "vw_stat_cited_in_all_years2",
                  "vw_stat_cited_in_last_10_years2",
                  "vw_stat_cited_in_last_20_years2",
                  "vw_stat_cited_in_last_5_years2",
                  "vw_stat_docviews_crosstab",
                  "vw_stat_docviews_last12months",
                  "vw_stat_docviews_lastcalyear", 
                  "vw_stat_docviews_lastmonth",
                  "vw_stat_docviews_lastsixmonths",
                  "vw_stat_docviews_lastweek",    # (used indirectly, in vw_stat_docviews_crosstab)                 
                  "vw_stat_most_viewed",
                  # "vw_stat_to_update_solr_docviews" # not used in code 2023-05-26
                  # "opasloader_splitbookpages_static", 
                  # "vw_reports_session_activity_desc",
                  # "vw_reports_session_activity_not_logged_in_desc", 
                  # "vw_api_productbase",               # deprecated view (use ..._instance_counts)
                  # "vw_api_volume_limits",             # deprecated
                  # "vw_interactive_latest_session_activity",
                  # "vw_stat_to_update_solr_docviews",  # deprecated
                  # "vw_stat_docviews_lastcalyear" # for now, nothing from last year
                  ]

        for table in tables:              
            curs = ocd.db.cursor(buffered=True, dictionary=True)
            sql = f"SELECT * from {table} LIMIT 10;" 
            try:
                curs.execute(sql)
                row_count = curs.rowcount
                val_str = f"Found {row_count} rows (limit was 10)"
                print (val_str)
                sourceData = curs.fetchall()
                assert (len(sourceData) >= 1)
            except AssertionError as e:
                print (f"Assertion error for table/view: {table}: {val_str}")
            except Exception as e:
                print (f"Exception: can't query table/view {table} ({e}")
                assert (False)

        ocd.close_connection(caller_name="test_views") # make sure connection is closed

        
        
if __name__ == '__main__':
    
    unittest.main()
    print ("Tests Complete.")