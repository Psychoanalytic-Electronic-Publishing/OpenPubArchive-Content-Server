#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

#  This test module is in development...

import sys
sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../../app')

from starlette.testclient import TestClient

import unittest
from localsecrets import TESTUSER, TESTPW, SECRET_KEY, ALGORITHM
import jwt
from datetime import datetime
import opasAPISupportLib
import opasConfig

from testConfig import base_api, base_plus_endpoint_encoded
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
        This library function is not currently used in the server, but is potentially still useful.
        """
        data = opasAPISupportLib.get_article_data("ANIJP-DE.009.0189A", fields=None)
        # Confirm that the request-response cycle completed successfully.
        assert (data.documentList.responseInfo.fullCount == 1)
        assert (data.documentList.responseSet[0].documentID == 'ANIJP-DE.009.0189A')
        
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