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

from testConfig import base_api, base_plus_endpoint_encoded
from main import app

client = TestClient(app)

class TestAPIDatabase(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_1_database_search(self):
        """
        Get Author Index For Matching Author Names
        /v1/Authors/Index/{authorNamePartial}/
        """
        response = client.get(base_api + '/v1/Database/Search/?fulltext1=phlebotomy&limit=5&sort')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r['documentList']['responseInfo']['fullCount'] >= 2)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)
       
        response = client.get(base_api + '/v1/Authors/Index/Maslo/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        # Expected:
        #  {'authorIndex': {'responseInfo': {'count': 2, 'limit': 15, 'offset': 0, 'fullCountComplete': True, 'listType': 'authorindex', 'scopeQuery': 'Terms: maslo', 
        #                                    'request': 'http://127.0.0.1:9100/v1/Authors/Index/Maslo/', 'solrParams': {'terms_fl': 'art_author_id', 'terms_prefix': 'maslo', 'terms_sort': 'index', 'terms_limit': 15, 'fl': '*,score', 'version': 2.2, 'wt': 'xml'}, 'timeStamp': '2019-10-28T15:15:03Z'}, 
        #                   'responseSet': [{'authorID': 'maslow, a. h.', 'publicationsURL': '/v1/Authors/Publications/maslow, a. h./', 'publicationsCount': 1}, 
        #                                   {'authorID': 'maslow, abraham h.', 'publicationsURL': '/v1/Authors/Publications/maslow, abraham h./', 'publicationsCount': 2}]}}
        assert(r['authorIndex']['responseSet'][0]['publicationsURL'] == '/v1/Authors/Publications/maslow, a. h./')

    def test_2_pubs_authornames(self):
        """
        Get Author Pubs For Matching Author Names
        /v1​/Authors​/Publications​/{authorNamePartial}​/
        """
        response = client.get(base_api + '/v1/Authors/Publications/maslow, a.*/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r['authorPubList']['responseInfo']['fullCount'] == 3)
        
        # Doesn't return an error, returns 0 matches.
        response = client.get(base_api + '/v1/Authors/Publications/Flintstone, Fred.*/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json() 
        assert(r['authorPubList']['responseInfo']['fullCount'] == 0)
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")