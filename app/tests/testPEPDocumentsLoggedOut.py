#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import logging
logger = logging.getLogger(__name__)

import unittest
import requests
from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
import opasAPISupportLib
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestDocumentsDocumentsLoggedOut(unittest.TestCase):
    """
    Tests for basic login and Download
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    def test_1_get_document_logged_out_verify_only_abstract_return(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/PCT.011.0171A/')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        # this document should not be available
        assert(response_info["count"] == 1)
        assert(response_set[0]["accessLimited"] == True)
        assert(len(response_set[0]["abstract"]) == len(response_set[0]["document"])) 
    
    # then one logged out
    def test_2_get_document_logged_out_verify_only_abstract_return(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/JOAP.063.0667A')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"]
        assert(response_info["count"] == 1)
        assert(response_set[0]["accessLimited"] == True)
        assert(len(response_set[0]["abstract"]) == len(response_set[0]["document"])) 


if __name__ == '__main__':
    unittest.main()    