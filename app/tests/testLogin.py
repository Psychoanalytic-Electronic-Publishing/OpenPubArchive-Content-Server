#!/usr/bin/env python
# -*- coding: utf-8 -*-

from starlette.testclient import TestClient

import unittest
import requests
from localsecrets import PADS_TEST_ID, PADS_TEST_PW

from unitTestConfig import base_plus_endpoint_encoded, headers

class TestLogin(unittest.TestCase):
    """
    Tests for basic login and Logout
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    
    def test_0_login(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={PADS_TEST_ID}&password={PADS_TEST_PW}&client-id=0')
        response = requests.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

        # now Check if we are logged in!
        full_URL = base_plus_endpoint_encoded('/v2/Session/WhoAmI/')
        response = requests.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        orig_session_id =  r["session_id"]

        full_URL = base_plus_endpoint_encoded('/v2/Session/Logout/')
        response = requests.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r["licenseInfo"]["responseInfo"]["loggedIn"] == False)

        full_URL = base_plus_endpoint_encoded('/v2/Session/WhoAmI/')
        response = requests.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        new_session_id =  r["session_id"]
        assert(new_session_id != orig_session_id)
        

    def test_2_bad_login(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={PADS_TEST_ID}&password="notthepassword"')
        response = requests.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        status_code = response.status_code
        assert(status_code == 401) # Unauthorized Error

        full_URL = base_plus_endpoint_encoded('/v2/Session/WhoAmI/')
        response = requests.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
       
if __name__ == '__main__':
    unittest.main()    