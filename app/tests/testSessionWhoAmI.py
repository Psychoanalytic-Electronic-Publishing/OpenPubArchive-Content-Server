#!/usr/bin/env python
# -*- coding: utf-8 -*-

from localsecrets import PADS_TEST_ID, PADS_TEST_PW

import unittest
import requests
import opasConfig

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestSessionWhoAmI(unittest.TestCase):
    """
    Tests for WhoAmI endpoint
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_v2_session_whoami(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Logout')
        response = requests.get(full_URL, headers=headers)
        full_URL = base_plus_endpoint_encoded('/v2/Session/WhoAmI/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
        # assert(r["user_id"] == 0)
        try:
            if r["user_type"] != "Group": # when ip login is enabled
                assert(r["authenticated"] == False) # was not ip authenticated
            else:
                assert(r["authenticated"] == True) # was ip authenticated
        except Exception as e:
            # must not be IP authenticated (and not logged in)
            print (f"PaDS exception: {e}")
            # must not be logged in
            assert (r["is_valid_login"] == False)
            
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