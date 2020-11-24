#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers

class TestSearchMoreLikeThis(unittest.TestCase):
    def test_search_morelike_1a(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/SearchParagraphs/?sourcecode=AOP&paratext=mind&parascope=dreams&similarcount=4')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] == 2)
        try:
            length = len(response_set[0]["similarityMatch"]["similarDocs"]["AOP.016.0171A"])
        except KeyError:
            length = len(response_set[1]["similarityMatch"]["similarDocs"]["AOP.016.0171A"])            
            
        assert(length == 4)
        

if __name__ == '__main__':
    unittest.main()
