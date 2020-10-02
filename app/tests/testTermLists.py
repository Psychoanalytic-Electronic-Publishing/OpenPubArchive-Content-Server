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
import opasAPISupportLib

class TestTermSearch(unittest.TestCase):

    def test_0a_searchanalysis(self):
        full_URL = base_plus_endpoint_encoded('/v1/Database/SearchAnalysis/?author=greenfield')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["termIndex"]["responseInfo"]
        response_set = r["termIndex"]["responseSet"] 
        assert(response_set[0]["termCount"] >= 6)
        print (response_set)
        # Confirm that the request-response cycle completed successfully.
        
    def test_0a_termcounts(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/TermCounts/?termlist=motherhood, fatherhood, child')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        print (r)
        #[   {'field': 'text', 'term': 'motherhood', 'termCount': 3510},
        #    {'field': 'text', 'term': 'fatherhood', 'termCount': 946}, 
        #    {'field': 'text', 'term': 'child', 'termCount': 69933}, 
        #    {'field': 'art_sourcetitlefull', 'term': 'journal', 'termCount': 51701}
        #]
        response_info = r["termIndex"]["responseInfo"]
        response_set = r["termIndex"]["responseSet"] 
        assert(response_set[0]["termCount"] >= 2600)
        print (response_set)
        # Confirm that the request-response cycle completed successfully.
        full_URL = base_plus_endpoint_encoded('/v2/Database/TermCounts/?termlist=mother')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["termIndex"]["responseInfo"]
        response_set = r["termIndex"]["responseSet"] 
        assert(response_set[0]["termCount"] >= 3000)
        print (response_set)
        
    
    def test_1a_termlist(self):
        tests = ["jealous", "incest", "moth", "dog", "cat"]
        term_list = opasAPISupportLib.get_term_count_list(tests)
        assert(len(term_list) > 0)
        for k,c in term_list.items():
            print (f"{k} - {c}")
        
    def test_1b_termlist(self):
        tests = ["jea?ous?", "inc*", "m?th*"]
        term_list = opasAPISupportLib.get_term_count_list(tests)
        assert(len(term_list) > 0)
        for k,c in term_list.items():
            print (f"{k} - {c}")

    def test_2a_termcsvlist(self):
        terms = "freud, heart, mother, moth"
        term_list = opasAPISupportLib.get_term_count_list(terms)
        assert(len(term_list) > 0)
        for k,c in term_list.items():
            print (f"{k} - {c}")

    #def test_1c_search_wildcard(self):
        #full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=gre?nfield')
        #response = requests.get(full_URL)
        #assert(response.ok == True)
        #r = response.json()
        #print (r)
        #response_info = r["documentList"]["responseInfo"]
        #response_set = r["documentList"]["responseSet"] 
        #assert(response_info["fullCount"] >= 7)
        ## print (response_set)
        ## Confirm that the request-response cycle completed successfully.


if __name__ == '__main__':
    unittest.main()
    