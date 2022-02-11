#!/usr/bin/env python
# -*- coding: utf-8 -*-

from starlette.testclient import TestClient

import unittest
import requests
from localsecrets import PADS_TEST_ID, PADS_TEST_PW

from unitTestConfig import base_plus_endpoint_encoded, headers

class TestSessionLoginLogout(unittest.TestCase):
    """
    Tests for basic login and Logout
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    
    def test_0_login_logout(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={PADS_TEST_ID}&password={PADS_TEST_PW}&client-id=4')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

        # now Check if we are logged in!
        full_URL = base_plus_endpoint_encoded('/v2/Session/WhoAmI/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        orig_session_id =  r["session_id"]

        full_URL = base_plus_endpoint_encoded('/v2/Session/Logout/')
        headers["client-session"] = orig_session_id
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r["authenticated"] == False)
       
if __name__ == '__main__':
    unittest.main()    