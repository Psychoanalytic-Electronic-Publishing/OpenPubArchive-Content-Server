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
        response = client.get(base_api + '/v1/Database/MostDownloaded/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r['documentList']['responseInfo']['count'] == r['documentList']['responseInfo']['limit'])
        #assert(r["text_server_ok"] == True)
        #assert(r["db_server_ok"] == True)
        print (r)
       
    def test_0_most_cited(self):
        """
        """
        # request login to the API server
        response = client.get(base_api + '/v1/Database/MostDownloaded/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r['documentList']['responseInfo']['count'] == r['documentList']['responseInfo']['limit'])
        #assert(r["text_server_ok"] == True)
        #assert(r["db_server_ok"] == True)
        print (r)

    def test_0_whats_new(self):
        """
        """
        # request login to the API server
        response = client.get(base_api + '/v1/Database/WhatsNew/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r['whatsNew']['responseInfo']['count'] == r['whatsNew']['responseInfo']['limit'])
        #assert(r["db_server_ok"] == True)
        print (r)

if __name__ == '__main__':
    unittest.main()    