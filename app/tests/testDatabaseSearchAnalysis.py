#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
import opasAPISupportLib
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestDatabaseSearchAnalysis(unittest.TestCase):
    """
    Tests use 'out of circulation' journals to try and create counts that persist over time
       even as the database is updated
    """
    def test_v2_searchanalysis(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/SearchAnalysis/?author=rangell&fulltext1=transference&sourcecode=AOP')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["termIndex"]["responseInfo"]
        response_set = r["termIndex"]["responseSet"] 
        print (f"Term: {response_set[0]['term']} Count: {response_set[0]['termCount']}")
        assert(response_set[0]["termCount"] >= 38847)
        print (f"Term: {response_set[1]['term']} Count: {response_set[1]['termCount']}")
        assert(response_set[1]["termCount"] >= 132)
        print (f"Term: {response_set[2]['term']} Count: {response_set[2]['termCount']}")
        assert(response_set[1]["termCount"] >= 1)
        # Confirm that the request-response cycle completed successfully.       

    def test_v2_searchanalysis_author_and_journalcode(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/SearchAnalysis/?author=tuckett&sourcecode=AOP')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["termIndex"]["responseInfo"]
        response_set = r["termIndex"]["responseSet"]
        print (f"Term: {response_set[0]['term']} Count: {response_set[0]['termCount']}")
        term0 = r["termIndex"]["responseSet"][0]["term"]
        assert(r["termIndex"]["responseSet"][0]["termCount"] >= 630)
        term1 = r["termIndex"]["responseSet"][1]["term"]
        print (f"Term: {response_set[1]['term']} Count: {response_set[1]['termCount']}")
        assert(r["termIndex"]["responseSet"][1]["termCount"] >= 59)
        print (term0)
        assert(term0 == '(AOP) (in source)')

    def test_v2_searchanalysis_author_and_journalcode_and_paratext(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/SearchAnalysis/?sourcecode=BAP&fulltext1="freud psychoanalysis"~25')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        assert(response.ok == True)
        #print (r)
        response_info = r["termIndex"]["responseInfo"]
        response_set = r["termIndex"]["responseSet"]
        print (f"Term: {response_set[0]['term']} Count: {response_set[0]['termCount']}")
        print (f"Term: {response_set[1]['term']} Count: {response_set[1]['termCount']}")
        term0 = r["termIndex"]["responseSet"][0]["term"]
        assert(term0 == '"freud psychoanalysis"~25 (in text)')
        assert(r["termIndex"]["responseSet"][0]["termCount"] >= 19000)
        term1 = r["termIndex"]["responseSet"][1]["term"]
        assert(term1 == '(BAP) (in source)')
        assert(r["termIndex"]["responseSet"][1]["termCount"] >= 403)

    def test_v2_searchanalysis_author_and_journalcode_and_text(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/SearchAnalysis/?sourcecode=PCT&citecount=3')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["termIndex"]["responseInfo"]
        response_set = r["termIndex"]["responseSet"] 
        print (f"Term: {response_set[0]['term']} Count: {response_set[0]['termCount']}")
        print (f"Term: {response_set[1]['term']} Count: {response_set[1]['termCount']}")
        term0 = r["termIndex"]["responseSet"][0]["term"]
        assert(term0 == '(PCT) (in source)')
        assert(r["termIndex"]["responseSet"][0]["termCount"] == 482)
        term1 = r["termIndex"]["responseSet"][1]["term"]
        print ("Term1=", term1)
        assert(term1 == '[3 TO *] (in cited, cited in the last 5 years)')
        print (r["termIndex"]["responseSet"][1]["termCount"])
        assert(r["termIndex"]["responseSet"][1]["termCount"] >= 3000)

    def test_v2_searchanalysis_author_and_journalcode_and_text_and_articletype(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/SearchAnalysis/?volume=2')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["termIndex"]["responseInfo"]
        response_set = r["termIndex"]["responseSet"] 
        print (f"Term: {response_set[0]['term']} Count: {response_set[0]['termCount']}")
        term0 = r["termIndex"]["responseSet"][0]["term"]
        assert(r["termIndex"]["responseSet"][0]["termCount"] >= 2622)

if __name__ == '__main__':
    unittest.main()
    