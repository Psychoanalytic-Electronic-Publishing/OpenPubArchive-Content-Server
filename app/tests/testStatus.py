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

class TestStatus(unittest.TestCase):
    """
    Tests for status endpoints 
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_0_server_status(self):
        # Send a request to the API server and store the response.
        response = client.get(base_api + '/v2/Session/Status/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r["text_server_ok"] == True)
        assert(r["db_server_ok"] == True)
        print (r)

    def test_1_get_license_status(self):
        # Send a request to the API server and store the response.
        response = client.get(base_api + '/v1/License/Status/Login/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["licenseInfo"]["responseInfo"]
        response_set = r["licenseInfo"]["responseSet"]
        print (response_info)
       
if __name__ == '__main__':
    unittest.main()    