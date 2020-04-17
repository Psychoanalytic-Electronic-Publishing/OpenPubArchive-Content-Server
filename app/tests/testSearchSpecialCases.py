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
    def test_search_viewed_count_1a(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewcount=2&sourcecode=IJP')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] >= 0) # just make sure there's a count
        print (response_set)

    def test_search_viewed_count_1b(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewcount=1')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] >= 0) # just make sure there's a count
        print (response_set)

    def test_search_viewed_count_1c(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewcount=1&fulltext1=feel')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        print (r)
        #"Watching to see how long a query can be here, since the mysql part generates a list of ids OR'd together"
        qlen = len(r["documentList"]["responseInfo"]["scopeQuery"][0][1])
        print (f"MySQL QueryLen: {qlen}")
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] >= 0) # just make sure there's a count
        print (response_set)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewcount=3&fulltext1=feel')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] >= 0) # just make sure there's a count
        print (response_set)

    def test_search_author_and_journalcode_and_text_and_citecount(self):
        full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=tuckett&citecount=3')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] >= 0) # just make sure there's a count
        print (response_set)

if __name__ == '__main__':
    unittest.main()
