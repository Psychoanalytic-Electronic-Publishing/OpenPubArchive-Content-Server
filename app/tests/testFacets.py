#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

import sys
import os.path

folder = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
if folder == "tests": # testing from within WingIDE, default folder is tests
    sys.path.append('../libs')
    sys.path.append('../config')
    sys.path.append('../../app')
else: # python running from should be within folder app
    sys.path.append('./libs')
    sys.path.append('./config')

import unittest
import requests
from requests.utils import requote_uri
import urllib

from unitTestConfig import base_api, base_plus_endpoint_encoded

class TestSearch(unittest.TestCase):
    def test_1a_facet_art_sourcecode(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=art_sourcecode') 
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["art_sourcecode"])
        assert(response_info["fullCount"] >= 291)
        
    def test_1b_facet_art_kwds_str(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=art_kwds_str, art_kwds') 
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["art_kwds_str"])
        assert(response_info["fullCount"] >= 291)

    def test_1c_facet_art_lang(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=art_lang') 
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["art_lang"])
        assert(response_info["fullCount"] >= 291)

    def test_1c_facet_art_type(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=art_type') 
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["art_type"])
        assert(response_info["fullCount"] >= 291)

    def test_1c_facet_art_year(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=art_year') 
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["art_year"])
        assert(response_info["fullCount"] >= 291)

    def test_1c_facet_art_sourcetype(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=art_sourcetype') 
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["art_sourcetype"])
        assert(response_info["fullCount"] >= 291)

    def test_1c_facet_art_authors(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=art_authors') 
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["art_authors"])
        assert(response_info["fullCount"] >= 291)

if __name__ == '__main__':
    unittest.main()
    