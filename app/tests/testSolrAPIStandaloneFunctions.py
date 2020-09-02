#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests of the OPAS functions which depend on the Solr API.  (Direct, rather than Endpoint calls)

"""
#2020-08-24 Changed numeric counts to symbols from unitTestConfig

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


# from starlette.testclient import TestClient

import unittest
# from localsecrets import TESTUSER, TESTPW, SECRET_KEY, ALGORITHM
# import jwt
# from datetime import datetime
import opasAPISupportLib
# import opasConfig
import unitTestConfig
import opasQueryHelper
import opasCentralDBLib
# import models

from unitTestConfig import base_api, base_plus_endpoint_encoded
# from main import app

# client = TestClient(app)

ocd = opasCentralDBLib.opasCentralDB()

class TestSolrAPIStandaloneFunctions(unittest.TestCase):
    """
    Tests of functions getting the metadata from solr rather than the database
    
    
    """
    
    def test_1_get_source_list_IJPSP(self):
        data = opasAPISupportLib.metadata_get_volumes(source_code="IJPSP")
        count = data.volumeList.responseInfo.count
        assert(count == unitTestConfig.VOL_COUNT_IJPSP)

    def test_1_get_source_list_ZBK(self):
        """
        Retrieve an article; make sure it's there and the abstract len is not 0
        """
        # This old function wasn't used by the code otherwise so removed this call
        #  it retrieves an article but doesn't include search highlighting.
        # data = opasAPISupportLib.get_article_data("ANIJP-DE.009.0189A", fields=None)
        # this newer function includes the search parameters if there were some
        data = opasAPISupportLib.metadata_get_volumes(source_code="ZBK", source_type="book")
        count = data.volumeList.responseInfo.fullCount
        assert(count == unitTestConfig.VOL_COUNT_ZBK)

    def test_1_get_source_list_SE(self):
        data = opasAPISupportLib.metadata_get_volumes(source_code="SE", source_type="book")
        count = data.volumeList.responseInfo.fullCount
        assert(count == unitTestConfig.VOL_COUNT_SE or count == unitTestConfig.VOL_COUNT_SE + 1)# series TOC adds one

    def test_1_get_source_list_gw(self):
        data = opasAPISupportLib.metadata_get_volumes(source_code="GW", source_type="book")
        count = data.volumeList.responseInfo.fullCount
        print (f"Count {count}")
        assert(count == unitTestConfig.VOL_COUNT_GW)

    def test_1_get_source_list_gw_with_head(self):
        data = opasAPISupportLib.metadata_get_volumes(source_code="GW")
        count = data.volumeList.responseInfo.fullCount
        print (f"Count {count}")
        assert(count == unitTestConfig.VOL_COUNT_GW or count == unitTestConfig.VOL_COUNT_GW + 1)# series TOC adds one

    def test_1_get_source_list_book(self):
        data = opasAPISupportLib.metadata_get_volumes(source_type="book")
        count = data.volumeList.responseInfo.fullCount
        assert(count >= unitTestConfig.VOL_COUNT_ALL_BOOKS)

    def test_1_get_source_list_NLP(self):
        data = opasAPISupportLib.metadata_get_volumes(source_code="NLP") # , source_type="book")
        count = data.volumeList.responseInfo.fullCount
        assert(count == 6)

    def test_1_get_source_list_books(self):
        data = opasAPISupportLib.metadata_get_volumes(source_code="IPL", source_type="book*")
        count = data.volumeList.responseInfo.fullCount
        assert(count == unitTestConfig.VOL_COUNT_IPL)

    def test_1_get_source_list_IMAGO(self):
        data = opasAPISupportLib.metadata_get_volumes(source_code="IMAGO")
        count = data.volumeList.responseInfo.fullCount
        assert(count == unitTestConfig.VOL_COUNT_IMAGO)

    def test_1_get_source_list_PCT(self):
        data = opasAPISupportLib.metadata_get_volumes(source_code="PCT")
        count = data.volumeList.responseInfo.fullCount
        assert(count == unitTestConfig.VOL_COUNT_PCT)

    def test_1_get_source_list_AOP(self):
        data = opasAPISupportLib.metadata_get_volumes(source_code="AOP")
        count = data.volumeList.responseInfo.fullCount
        assert(count == unitTestConfig.VOL_COUNT_AOP)

    def test_1d_get_source_list_journal(self):
        data = opasAPISupportLib.metadata_get_volumes(source_type="journal")
        count = data.volumeList.responseInfo.fullCount
        assert(count >= unitTestConfig.VOL_COUNT_ALL_JOURNALS)
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")