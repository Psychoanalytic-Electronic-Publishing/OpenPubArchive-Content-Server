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

class TestGetDocumentSearchRemoveNuisanceHits(unittest.TestCase):
    """
    Tests for basic login and Download
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    
    def test_2_get_document_with_search_context(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/PSC.034.0085A/?search=smarttext=sing%20a%20song%20of%20sixpence')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"]
        match_count = len(re.findall("#@@@@", response_set[0].document))
        assert(match_count >= 1)
        print (response_set[0].document[:1000])


if __name__ == '__main__':
    unittest.main()    