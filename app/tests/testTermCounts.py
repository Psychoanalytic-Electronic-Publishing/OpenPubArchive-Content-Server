#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers
from opasPySolrLib import get_term_index

# two libs for the same function, different restrictions
import opasSolrPyLib # eventually, we may want to get rid of this.
import opasPySolrLib

class TestTermSearch(unittest.TestCase):
    def test_0a_searchanalysis(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/SearchAnalysis/?author=greenfield')
        response = requests.get(full_URL, headers=headers)
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
        response = requests.get(full_URL, headers=headers)
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
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["termIndex"]["responseInfo"]
        response_set = r["termIndex"]["responseSet"] 
        assert(response_set[0]["termCount"] >= 3000)
        print (response_set)
    
    def test_1a_termlist(self):
        # test both library methods and check for equality.
        tests = ["jealous", "incest", "moth", "dog", "cat"]
        term_list1 = opasSolrPyLib.get_term_count_list(tests)
        assert(len(term_list1) > 0)
        for k,c in term_list1.items():
            print (f"{k} - {c}")
        
        term_list2 = opasPySolrLib.get_term_count_list(tests)
        assert(len(term_list2) > 0)
        for k,c in term_list2.items():
            print (f"{k} - {c}")
            
        for k,c in term_list2.items():
            # should match counts
            print (k, term_list1[k])
            assert c == term_list1[k], (f"{k} - {c}")
            
    def test_2a_termcsvlist(self):
        # test both library methods and check for equality.
        tests = "freud, heart, mother, moth"
        term_list1 = opasSolrPyLib.get_term_count_list(tests)
        assert(len(term_list1) > 0)
        for k,c in term_list1.items():
            print (f"{k} - {c}")

        term_list2 = opasPySolrLib.get_term_count_list(tests)
        assert(len(term_list2) > 0)
        for k,c in term_list2.items():
            print (f"{k} - {c}")

        for k,c in term_list2.items():
            # should match counts
            print (k, term_list1[k])
            assert c == term_list1[k], (f"{k} - {c}")

    def test_2b_termlist(self):
        # only SolrPyLib supports wildcards.
        # Note use of SolrPy here.
        tests = ["jea?ous?", "inc*", "m?th*"]
        term_list1 = opasSolrPyLib.get_term_count_list(tests)
        assert(len(term_list1) > 0)
        for k,c in term_list1.items():
            print (f"{k} - {c}")

if __name__ == '__main__':
    unittest.main()
    