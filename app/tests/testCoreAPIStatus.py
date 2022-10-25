#!/usr/bin/env python
# -*- coding: utf-8 -*-

from localsecrets import PADS_TEST_ID, PADS_TEST_PW

import unittest
import requests
import opasConfig
import sys
from datetime import datetime

from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, test_login

# Login!
sessID, headers, session_info = test_login()


class TestAPIStatus(unittest.TestCase):
    """
    Tests for status endpoints 
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    Checks the API status
    Checks that all database segments have been loaded (all other tests depend on this)
        # has archive been loaded
        # has current been loaded
        # has special been loaded
        # has free been loaded
        # has offsite been loaded
        # have stats been run
    """   

    def test_v2_api_status(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Api/Status/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    # 
    # Though not testing the API per se, the following ensures in this early test whether all the components of the database have been fully loaded.
    # 
       
if __name__ == '__main__':
    unittest.main()    