#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

import sys
sys.path.append('../libs')
sys.path.append('../config')

import unittest
import requests
from requests.utils import requote_uri
import urllib

from testConfig import base_api, base_plus_endpoint_encoded

class TestSearch(unittest.TestCase):
    def test_search_mixedcase(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=Tuckett')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] == 15)
        print (response_set)
        # Confirm that the request-response cycle completed successfully.

    def test_search_lowercase(self):
        full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=tuckett')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] == 15)
        print (response_set)
        # Confirm that the request-response cycle completed successfully.

    def test_search_journalcode(self):
        full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=tuckett&journal=IJP')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] == 15)
        print (response_set)

    def test_search_author_and_journalcode(self):
        full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=tuckett&journal=IJP&text=economics')
        response = requests.get(full_URL)
        r = response.json()
        assert(response.ok == True)
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] == 15)
        print (response_set)

    def test_search_author_and_journalcode_and_text(self):
        full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=tuckett&journal=IJP&text=economics&citecount=3')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] == 10)
        print (response_set)

    def test_search_author_and_journalcode_and_text_and_citecount(self):
        full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=tuckett&journal=IJP&text=economics&citecount=3')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] == 10)
        print (response_set)

       
        
if __name__ == '__main__':
    unittest.main()    