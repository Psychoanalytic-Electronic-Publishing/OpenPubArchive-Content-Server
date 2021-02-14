#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers

class TestSearchParagraphs(unittest.TestCase):
    def test_search_para_1a(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/SearchParagraphs/?sourcecode=SE&paratext=disorder and mind')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] == 11) 
        # print (response_set[0])

    def test_search_para_2a(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/SearchParagraphs/?sourcecode=SE&paratext=mental disorder')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f"Count: {response_info['count']}")
        assert(response_info["fullCount"] == 21)
        # print (response_set[0])

    def test_search_para_2b(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/SearchParagraphs/?sourcecode=SE&paratext=body and mind')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f"Count: {response_info['count']}")
        assert(response_info["fullCount"] == 35)
        # print (response_set[0])

    def test_search_para_3(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/SearchParagraphs/?sourcecode=SE&paratext=mind&parascope=dreams')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] == 1)
        # print (response_set[0])

    def test_search_para_3b(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/SearchParagraphs/?sourcecode=SE&paratext=mind&parascope=dreams&similarcount=4')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] == 1)
        try:
            length = len(response_set[0]["similarityMatch"]["similarDocs"]["SE.004.R0009A"])
        except KeyError:
            length = len(response_set[1]["similarityMatch"]["similarDocs"]["SE.004.R0009A"])            
            
        assert(length == 4)


if __name__ == '__main__':
    unittest.main()
