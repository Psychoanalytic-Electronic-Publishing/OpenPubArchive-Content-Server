#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests
import opasAPISupportLib
import logging

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestSetLogLevel(unittest.TestCase):
    """
    Tests for LogLevel endpoint
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_v2_get_log_level_1(self):
        levels = {10: "DEBUG", 20: "INFO", 30: "WARNING", 40: "ERROR", 50: "CRITICAL"}
        logger = logging.getLogger() # Get root logger
        curr_level = levels.get(logger.level, str(logger.level))
        print (curr_level)
        
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/LogLevel')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        print (response.status_code)
        assert (response.status_code == 405) # rejected

    def test_v2_set_log_level_2(self):
        logger = logging.getLogger() # Get root logger
        curr_level = logger.level
        print (f"Current Level: {curr_level}")
        # Send a request to the API server and store the response.
        new_level = opasAPISupportLib.set_log_level(level_int=curr_level+10)
        # Confirm that the request-response cycle completed successfully.
        assert(new_level == curr_level + 10)
        print (f"New Level: {new_level}")
        assert(new_level != curr_level)
       
if __name__ == '__main__':
    unittest.main()    