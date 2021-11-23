#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import logging
import opasAPISupportLib
logger = logging.getLogger(__name__)

import unittest
import requests

import opasDocPermissions
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, test_login

# Login!
sessID, headers, session_info = test_login()

class TestDocumentsDocumentDisplayMessages(unittest.TestCase):
    """
    Tests for basic login and Download
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
          
    Many of the tests are display, since text in the DB can change.
       The assertions will check the general functioning with a limited set.
       Manually inspect the others for correct operation
    
    """
    
    search_term = "test"
    available_content = "This archive content is available for you to access."
    summary_content = "This is a summary excerpt from the full document. "

    def test_show_messages(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/APA.064E.NP0001A/')
        print ("Archive: " + full_URL)
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        print (response_info)
        assert (response_set[0]["accessLimitedDescription"] == self.available_content)
        assert (response_set[0]["accessLimitedReason"] == self.available_content)

        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/AIM.077.0009A/')
        print ("Current: " + full_URL)
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        print (response_info)
        assert (response_set[0]["accessLimitedDescription"] == self.summary_content)

        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/PCAS.024.0091A/')
        print ("Future: " + full_URL)
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert (response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert (response_set[0]["accessLimitedDescription"] == self.summary_content)
        print (response_set[0]["accessLimitedReason"])

        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/IJPOPEN.008.0001A/')
        print ("IJPOPEN: " + full_URL)
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        print (response_info)
        assert (response_set[0]["accessLimitedDescription"] == self.summary_content)
        print (response_set[0]["accessLimitedReason"])
        print (response_set[0]["accessLimitedPubLink"])
        print (response_set[0]["accessLimitedDebugMsg"])

if __name__ == '__main__':
    unittest.main()    