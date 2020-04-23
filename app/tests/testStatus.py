#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

#  This test module is in development...

import sys
import os.path
from localsecrets import TESTUSER, TESTPW, SECRET_KEY, ALGORITHM

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

class TestStatus(unittest.TestCase):
    """
    Tests for status endpoints 
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_v2_session_status(self):
        # Send a request to the API server and store the response.
        response = client.get(base_api + '/v2/Session/Status/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r["text_server_ok"] == True)
        assert(r["db_server_ok"] == True)
        print (r)

    def test_v2_session_whoami(self):
        # Send a request to the API server and store the response.
        response = client.get(base_api + '/v2/Session/WhoAmI/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r["user_id"] == 0)
        assert(r["username"] == "NotLoggedIn")
        full_URL = base_plus_endpoint_encoded(f'/v1/Login/?grant_type=password&username={TESTUSER}&password={TESTPW}')
        response = client.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        response = client.get(base_api + '/v2/Session/WhoAmI/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r["user_id"] == 2000)
        assert(r["username"] == "testAccount001")
        print (r)

    def test_v1_license_status_login(self):
        # Send a request to the API server and store the response.
        response = client.get(base_api + '/v1/License/Status/Login/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["licenseInfo"]["responseInfo"]
        response_set = r["licenseInfo"]["responseSet"]
        assert (response_info["loggedIn"] == False)
        print (response_info)
        assert (response_set is None)
       
if __name__ == '__main__':
    unittest.main()    