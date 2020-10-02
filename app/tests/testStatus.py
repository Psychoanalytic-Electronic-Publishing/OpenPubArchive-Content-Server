#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

#  This test module is in development...

import sys
import os.path
from localsecrets import PADS_TEST_ID, PADS_TEST_PW

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
from localsecrets import TESTUSER, TESTPW
from unitTestConfig import base_api, base_plus_endpoint_encoded
from main import app
import opasConfig

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
        assert(r["username"] == opasConfig.USER_NOT_LOGGED_IN_NAME)
        # logout
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Logout')
        response = client.get(full_URL)
        # login 
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={PADS_TEST_ID}&password={PADS_TEST_PW}')
        response = client.get(full_URL)
        # now check who I am
        response = client.get(base_api + '/v2/Session/WhoAmI/')
        # Confirm that the request-response cycle completed successfully.
        r = response.json()
        assert(r["username"] == PADS_TEST_ID)
       
if __name__ == '__main__':
    unittest.main()    