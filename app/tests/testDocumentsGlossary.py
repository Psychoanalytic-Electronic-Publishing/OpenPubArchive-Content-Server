#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

#  This test module is in development...

import opasAPISupportLib
import requests

import logging
logger = logging.getLogger(__name__)

import unittest
from localsecrets import PADS_TEST_ID, PADS_TEST_PW, PDF_ORIGINALS_PATH
from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestDocumentsGlossary(unittest.TestCase):
    def test_00_get_glossary(self):
        ret = opasAPISupportLib.documents_get_glossary_entry("YN0019667860580", term_id_type="ID", retFormat="html") 
        print (ret)

    def test_1a_get_glossary_endpoint_GROUP(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Glossary/WALLERSTEIN, ROBERT S/?termidtype=Group')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        print (response_set)

    def test_1b_get_glossary_endpoint_GROUP(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Glossary/ANXIETY/?termidtype=Group&recordperterm=True')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] >= 7) # chg from 7 to 10, since expanded group search to also search names
        print (response_set)
        
    def test_1c_get_glossary_endpoint_NAME(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Glossary/WHEELWRIGHT, JOSEPH BALCH (1906-99)/?termidtype=Name')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        print (response_set)
        
    def test_1c2_get_glossary_endpoint_NAME(self):
        # Confirm that the request-response cycle completed successfully.
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Glossary/wheelwright, JOSEPH BALCH (1906-99)/?termidtype=Name')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        print (response_set)

    def test_1d_get_glossary_endpoint_ID(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Glossary/YP0017805628220.001/?termidtype=ID')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        print (response_set)
        
if __name__ == '__main__':
    unittest.main()
