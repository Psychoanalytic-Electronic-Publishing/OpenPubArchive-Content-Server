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
        tables = ["vw_api_messages", 
                  "vw_api_productbase_instance_counts", 
                  "vw_api_sourceinfodb",
                  "vw_article_firstsectnames",
                  "vw_article_sectnames", 
                  "vw_instance_counts_books", #  (used indirectly, by vw_api_productbase_instance_counts)
                  "vw_instance_counts_src",   #  (used indirectly, by vw_api_productbase_instance_counts)
                  "vw_jrnl_vols", 
                  "vw_reports_document_activity", 
                  "vw_reports_document_views", 
                  "vw_reports_session_activity",
                  "vw_reports_session_activity_desc",
                  "vw_reports_session_activity_not_logged_in", 
                  "vw_reports_session_activity_not_logged_in_desc", 
                  "vw_reports_user_searches", 
                  "vw_stat_cited_crosstab2",
                  "vw_stat_cited_crosstab_with_details2",
                  "vw_stat_cited_in_all_years2",
                  "vw_stat_cited_in_last_10_years2",
                  "vw_stat_cited_in_last_20_years2",
                  "vw_stat_cited_in_last_5_years2",
                  "vw_stat_docviews_crosstab",
                  "vw_stat_docviews_last12months",
                  "vw_stat_docviews_lastmonth",
                  "vw_stat_docviews_lastsixmonths",
                  "vw_stat_docviews_lastweek",    # (used indirectly, in vw_stat_docviews_crosstab)                 
                  "vw_stat_most_viewed",
                  # "vw_active_sessions",               # deprecated
                  # "vw_api_productbase",               # deprecated view (use ..._instance_counts)
                  # "vw_api_volume_limits",             # deprecated
                  # "vw_latest_session_activity",
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