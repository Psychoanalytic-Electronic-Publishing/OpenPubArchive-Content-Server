#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

#  This test module is in development...

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


from starlette.testclient import TestClient

import unittest
from localsecrets import TESTUSER, TESTPW, SECRET_KEY, ALGORITHM
import jwt
from datetime import datetime
import opasAPISupportLib
import opasConfig
import opasQueryHelper
import models
import opasCentralDBLib
import opasFileSupport
import pymysql

from unitTestConfig import base_api, base_plus_endpoint_encoded
# from main import app

# client = TestClient(app)

class TestSQLStructure(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.   
    """
    def test_1_testviews(self):
        ocd = opasCentralDBLib.opasCentralDB()
        dbok = ocd.open_connection(caller_name="test_get_productbase_data") # make sure connection is open
        assert (dbok == True)
        tables = ["vw_products_flattened",
                  "vw_active_sessions",
                  "vw_api_product_list_with_basecodes",
                  "vw_api_session_endpoints_with_descriptor ",
                  "vw_api_sourceinfodb",
                  "vw_api_user",
                  "vw_api_user_subscriptions_with_basecodes",
                  "vw_latest_session_activity",
                  "vw_products_with_productbase",
                  "vw_stat_cited_crosstab",
                  "vw_stat_cited_in_all_years",
                  "vw_stat_cited_in_last_5_years",
                  "vw_stat_cited_in_last_10_years",
                  "vw_stat_cited_in_last_20_years",
                  "vw_stat_docviews_crosstab",
                  "vw_stat_docviews_last12months",
                  "vw_stat_docviews_lastcalyear",
                  "vw_stat_docviews_lastmonth",
                  "vw_stat_docviews_lastsixmonths",
                  "vw_stat_docviews_lastweek",
                  "vw_stat_most_viewed",
                  "vw_subscriptions",
                  "vw_user_active_subscriptions",
                  "vw_user_active_subscriptions",
                  "vw_user_referred",
                  "vw_user_referrer_account_management",
                  "vw_user_session_activity",
                  "vw_user_subscriptions_products"
                  ]

        for table in tables:              
            curs = ocd.db.cursor(pymysql.cursors.DictCursor)
            sql = f"SELECT * from {table} LIMIT 10;" 
            try:
                cursed = curs.execute(sql)
                print (f"Found {cursed} rows (limit was 10)")
                sourceData = curs.fetchall()
                assert (len(sourceData) >= 1)
            except:
                print (f"Exception: can't query table {table}")
                assert (False)

        ocd.close_connection(caller_name="test_get_productbase_data") # make sure connection is closed

        
        
if __name__ == '__main__':
    
    unittest.main()
    print ("Tests Complete.")