#!/usr/bin/env python
# -*- coding: utf-8 -*-

from localsecrets import PADS_TEST_ID, PADS_TEST_PW

import unittest
import requests
import opasConfig

from unitTestConfig import base_plus_endpoint_encoded, headers

class TestStatus(unittest.TestCase):
    """
    Tests for status endpoints 
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_v2_api_status(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Api/Status/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_v2_session_status(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Session/Status/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r["text_server_ok"] == True)
        assert(r["db_server_ok"] == True)
        print (r)

    def test_v2_session_whoami(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Session/WhoAmI/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
        # assert(r["user_id"] == 0)
        assert(r["username"] == opasConfig.USER_NOT_LOGGED_IN_NAME)
        # logout
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Logout')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r)
        # login 
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={PADS_TEST_ID}&password={PADS_TEST_PW}')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r)
        headers["client-session"] = r["session_id"]
        # now check who I am
        full_URL = base_plus_endpoint_encoded('/v2/Session/WhoAmI/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        r = response.json()
        print (r)
        assert(r["username"] == PADS_TEST_ID)
       
if __name__ == '__main__':
    unittest.main()    