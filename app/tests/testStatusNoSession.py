#!/usr/bin/env python
# -*- coding: utf-8 -*-

from localsecrets import PADS_TEST_ID, PADS_TEST_PW

import unittest
import requests
import opasConfig

from unitTestConfig import base_plus_endpoint_encoded, headers

class TestStatusNoSession(unittest.TestCase):
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
        print (r)
        
        # Run it again...see what it does.  Does it pick up the same session from the cookie?
        full_URL = base_plus_endpoint_encoded('/v2/Session/Status/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r["text_server_ok"] == True)
        assert(r["db_server_ok"] == True)
        print (r)
       
if __name__ == '__main__':
    unittest.main()    