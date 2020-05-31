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
    def test_0a_possible_error(self): 
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewperiod=&fulltext1=cried&sort=rank&limit=15&offset=0')
        response = requests.get(full_URL)
        assert(response.ok == True) # rank is accepted, same as score
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] >= 6)
        #print (response_set)
        for n in response_set:
            print (n["documentRef"])
        # Confirm that the request-response cycle completed successfully.
        
    def test_0b_parameter_error(self):
        # bad boolean parameter
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewperiod=&fulltext1=cried&sort=rank&synonyms=WTF')
        response = requests.get(full_URL)
        assert(response.ok == False)
        r = response.json()

    def test_0b_good_language_code(self):
        # bad boolean parameter
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=cried&sourcelangcode=en')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()

    def test_0b_bad_language_code(self):
        # bad boolean parameter
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewperiod=&fulltext1=cried&sourcelangcode=e')
        response = requests.get(full_URL)
        assert(response.ok == False)
        r = response.json()

    def test_1a_search_mixedcase(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=Greenfield')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] >= 6)
        #print (response_set)
        for n in response_set:
            print (n["documentRef"])
        # Confirm that the request-response cycle completed successfully.

    def test_1b_search_lowercase(self):
        full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=greenfield')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] >= 6)
        print (response_set)
        # Confirm that the request-response cycle completed successfully.

    def test_1c_search_wildcard(self):
        full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=gre?nfield')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] >= 7)
        # print (response_set)
        # Confirm that the request-response cycle completed successfully.

    def test_search_journalcode(self):
        full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=tuckett&journal=IJP')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] >= 13)
        print (response_set)

    def test_search_author_and_journalcode(self):
        full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=tuckett&journal=IJP&text=economics')
        response = requests.get(full_URL)
        r = response.json()
        assert(response.ok == True)
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] >= 13)
        print (response_set)

    def test_search_author_and_journalcode_and_text(self):
        full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=tuckett&text=economics&citecount=6')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] >= 4)
        print (response_set)

    def test_search_author_and_journalcode_and_text_and_citecount(self):
        full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=tuckett&citecount=3')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] >= 7)
        print (response_set)

if __name__ == '__main__':
    unittest.main()
    