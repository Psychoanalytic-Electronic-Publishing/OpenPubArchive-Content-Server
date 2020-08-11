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
import opasCentralDBLib
import models

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
        assert(count == 11)

    def test_1_get_source_list_ZBK(self):
        """
        Retrieve an article; make sure it's there and the abstract len is not 0
        """
        # This old function wasn't used by the code otherwise so removed this call
        #  it retrieves an article but doesn't include search highlighting.
        # data = opasAPISupportLib.get_article_data("ANIJP-DE.009.0189A", fields=None)
        # this newer function includes the search parameters if there were some
        data = opasAPISupportLib.metadata_get_volumes(source_code="ZBK", source_type="book")
        count = data.volumeList.responseInfo.count
        assert(count == 72)

    def test_1_get_source_list_IPL(self):
        data = opasAPISupportLib.metadata_get_volumes(source_code="SE", source_type="book")
        count = data.volumeList.responseInfo.count
        assert(count == 24)

    def test_1_get_source_list_gw(self):
        data = opasAPISupportLib.metadata_get_volumes(source_code="GW", source_type="book")
        count = data.volumeList.responseInfo.count
        assert(count == 18)

    def test_1_get_source_list_book(self):
        data = opasAPISupportLib.metadata_get_volumes(source_type="book")
        count = data.volumeList.responseInfo.count
        assert(count == 142)

    def test_1_get_source_list_NLP(self):
        data = opasAPISupportLib.metadata_get_volumes(source_code="NLP") # , source_type="book")
        count = data.volumeList.responseInfo.count
        assert(count == 6)

    def test_1_get_source_list_books(self):
        data = opasAPISupportLib.metadata_get_volumes(source_code="IPL", source_type="book")
        count = data.volumeList.responseInfo.count
        assert(count == 22)

    def test_1_get_source_list_IMAGO(self):
        data = opasAPISupportLib.metadata_get_volumes(source_code="IMAGO")
        count = data.volumeList.responseInfo.count
        assert(count == 23)

    def test_1_get_source_list_PCT(self):
        data = opasAPISupportLib.metadata_get_volumes(source_code="PCT")
        count = data.volumeList.responseInfo.count
        assert(count == 26)

    def test_1_get_source_list_AOP(self):
        data = opasAPISupportLib.metadata_get_volumes(source_code="AOP")
        count = data.volumeList.responseInfo.count
        assert(count == 34)

    def test_1d_get_source_list_journal(self):
        data = opasAPISupportLib.metadata_get_volumes(source_type="journal")
        count = data.volumeList.responseInfo.count
        assert(count >= 2491)
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")