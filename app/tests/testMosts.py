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

from unitTestConfig import base_api, base_plus_endpoint_encoded
from main import app

client = TestClient(app)

class TestMost(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_0_most_downloaded(self):
        """
        """
        # request login to the API server
        response = client.get(base_api + '/v2/Database/MostViewed/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['count']}")
        print (f"Limit: {r['documentList']['responseInfo']['limit']}")
        print (f"Count: {r['documentList']['responseSet'][0]['stat']['downloads_last12months']}")
        assert(r['documentList']['responseInfo']['count'] == r['documentList']['responseInfo']['limit'])
        assert(r['documentList']['responseSet'][0]['stat']['downloads_last12months'] > 0)
        #assert(r["text_server_ok"] == True)
        #assert(r["db_server_ok"] == True)
        print (r)
       
    def test_0_most_downloaded_pubperiod_author_viewperiod(self):
        """
        """
        # request login to the API server
        response = client.get(base_api + '/v2/Database/MostViewed/?pubperiod=30&author=tuck%2A&viewperiod=4&limit=5')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['count']}")
        print (f"Limit: {r['documentList']['responseInfo']['limit']}")
        assert(r['documentList']['responseSet'][0]['stat']['downloads_last12months'] > 0)
        #assert(r["text_server_ok"] == True)
        #assert(r["db_server_ok"] == True)
        print (r)

    def test_0_most_cited(self):
        """
        """
        # request login to the API server
        response = client.get(base_api + '/v2/Database/MostCited/?limit=5')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['count']}")
        print (f"Limit: {r['documentList']['responseInfo']['limit']}")
        print (f"Limit: {r['documentList']['responseSet'][0]['stat']['art_cited_5']}")
        assert(r['documentList']['responseSet'][0]['stat']['art_cited_5'] > 15)
        #assert(r["text_server_ok"] == True)
        #assert(r["db_server_ok"] == True)
        print (r)

    def test_1_most_cited_pubperiod_author_viewperiod(self):
        """
        """
        # request login to the API server
        response = client.get(base_api + '/v2/Database/MostCited/?pubperiod=20&author=Benjamin&limit=5')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['count']}")
        print (f"Limit: {r['documentList']['responseInfo']['limit']}")
        print (f"Limit: {r['documentList']['responseSet'][0]['stat']['art_cited_5']}")
        assert(r['documentList']['responseSet'][0]['stat']['art_cited_5'] > 15)
        #assert(r["text_server_ok"] == True)
        #assert(r["db_server_ok"] == True)
        print (r)

    def test_0_whats_new(self):
        """
        """
        # request login to the API server
        response = client.get(base_api + '/v1/Database/WhatsNew/?days_back=90')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r['whatsNew']['responseInfo']['listType'] == 'newlist')
        #assert(r["db_server_ok"] == True)
        print (f"{r['whatsNew']['responseInfo']['limit']}")
        print (r)

if __name__ == '__main__':
    unittest.main()
    client.close()
    