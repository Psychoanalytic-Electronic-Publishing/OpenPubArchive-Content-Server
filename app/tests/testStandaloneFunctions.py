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

from unitTestConfig import base_api, base_plus_endpoint_encoded
from main import app

client = TestClient(app)

class TestStandaloneFunctions(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_1_get_article_data(self):
        """
        Retrieve an article; make sure it's there and the abstract len is not 0
        """
        # This old function wasn't used by the code otherwise so removed this call
        #  it retrieves an article but doesn't include search highlighting.
        # data = opasAPISupportLib.get_article_data("ANIJP-DE.009.0189A", fields=None)
        # this newer function includes the search parameters if there were some
        data = opasAPISupportLib.documents_get_document("ANIJP-DE.009.0189A")
        # Confirm that the request-response cycle completed successfully.
        assert (data.documents.responseInfo.fullCount == 1)
        assert (data.documents.responseSet[0].documentID == 'ANIJP-DE.009.0189A')
        assert (len(data.documents.responseSet[0].abstract)) > 0

    def test_2_metadata_get_sources(self):
        """
        Test
          1) list of video returns for metadata_get_videos
          2) List of sources by type
          3) 
        """
        data = opasAPISupportLib.metadata_get_videos(src_type="Videos", pep_code=None, limit=opasConfig.DEFAULT_LIMIT_FOR_METADATA_LISTS, offset=0)
        # Confirm that the request-response cycle completed successfully.
        assert (data[0] >= 90)
        # check to make sure a known value is among the data returned
        dataList = [d['documentID'] for d in data[1] if 'documentID' in d]
        assert ('IPSAVS.001A.0001A' in dataList)
        data = opasAPISupportLib.metadata_get_source_by_type(src_type="journal")
        dataList = [d.PEPCode for d in data.sourceInfo.responseSet]
        assert ('PAQ' in dataList)
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")