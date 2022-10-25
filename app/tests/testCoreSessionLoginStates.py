#!/usr/bin/env python
# -*- coding: utf-8 -*-

from starlette.testclient import TestClient

import unittest
import requests
from localsecrets import PADS_TEST_ID, PADS_TEST_PW, PADS_TEST_ARCHIVEANDCURRENT, PADS_TEST_ARCHIVEANDCURRENT_PW

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in, test_logout
# Get session, but not logged in.
headers = get_headers_not_logged_in()
orig_session_id = "123"

class TestSessionLogin(unittest.TestCase):
    """
    Tests for basic login and Logout
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    def test_00_search_not_logged_in(self):
        # Send a request to the API server and store the response.
        # ### OR #####
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=unconscious&abstract=true')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        abstr = response_set[0].get("abstract", None)
        assert(abstr is not None)
    
    def test_01_login(self):
        global orig_session_id
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={PADS_TEST_ARCHIVEANDCURRENT}&password={PADS_TEST_ARCHIVEANDCURRENT_PW}&client-id=4')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        orig_session_id =  r["session_id"]

        # now Check if we are logged in!
        full_URL = base_plus_endpoint_encoded('/v2/Session/WhoAmI/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()

    def test_02_get_document(self):
        global orig_session_id
        print (f"Session ID: {orig_session_id}")
        print (f"headers: {headers}")
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/CFP.007.0001A/')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        # this document should be available
        assert(response_set[0]["accessLimited"] == False)
        print (response_set[0]["document"][0:600])
        
    def test_03_logout(self):
        global orig_session_id
        print (f"Session ID: {orig_session_id}")
        print (f"headers: {headers}")
        #  logout
        full_URL = base_plus_endpoint_encoded('/v2/Session/Logout/')
        headers["client-session"] = orig_session_id
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r["authenticated"] == False)

    def test_04_get_document(self):
        global orig_session_id
        print (f"Session ID: {orig_session_id}")
        print (f"headers: {headers}")
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/CFP.007.0001A/')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        # this document should not be available
        assert(response_set[0]["accessLimited"] == True)  # Not logged in
        print (response_set[0]["document"][0:600])

               
if __name__ == '__main__':
    unittest.main()    