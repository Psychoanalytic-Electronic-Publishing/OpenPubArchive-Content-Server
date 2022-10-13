#!/usr/bin/env python
# -*- coding: utf-8 -*-

from localsecrets import PADS_TEST_ID, PADS_TEST_PW

import unittest
import requests
import opasConfig

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestSessionStatus(unittest.TestCase):
    """
    Tests for status endpoints 
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_v2_session_status(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Session/Status/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r["text_server_ok"] == True)
        assert(r["db_server_ok"] == True)
        #print (r)

    def test_v2_session_whoami(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Logout')
        response = requests.get(full_URL, headers=headers)
        full_URL = base_plus_endpoint_encoded('/v2/Session/WhoAmI/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        #print (r)
        # assert(r["user_id"] == 0)
        try:
            if r.get("user_type") != "Group": # when ip login is enabled
                assert(r.get("authenticated") == False or r.get("authenticated") is None) # was not ip authenticated
            else:
                assert(r.get("authenticated") == True) # was ip authenticated
        except Exception as e:
            # must not be IP authenticated (and not logged in)
            print (f"PaDS exception: {e}")
            # must not be logged in
            assert (r["is_valid_login"] == False)
            
        # logout
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Logout')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        #print (r)
        # login 
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={PADS_TEST_ID}&password={PADS_TEST_PW}&client-id=4')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        #print (r)
        headers["client-session"] = r["session_id"]
        # now check who I am
        full_URL = base_plus_endpoint_encoded('/v2/Session/WhoAmI/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        r = response.json()
        #print (r)
        assert(r["username"].lower() == PADS_TEST_ID.lower())


    def test_v2_other_client_logout(self):
        headers = get_headers_not_logged_in()
        # now check who I am
        full_URL = base_plus_endpoint_encoded('/v2/Session/WhoAmI/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        r = response.json()
        #print (r)
        assert(r["username"] == opasConfig.USER_NOT_LOGGED_IN_NAME)
        #  this should logout of the database, but not send a message to PaDS
        full_URL = base_plus_endpoint_encoded('/v2/Session/Logout/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r["authenticated"] == False)
       
if __name__ == '__main__':
    unittest.main()    