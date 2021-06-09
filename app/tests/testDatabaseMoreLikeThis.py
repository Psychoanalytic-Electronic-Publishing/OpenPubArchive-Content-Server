#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers

class TestDatabaseMoreLikeThis(unittest.TestCase):
    def test_search_morelike_1a(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/MoreLikeThis/?morelikethis=AOP.016.0171A&similarcount=4')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        assert(response_info["count"] == 1)
        response_set = r["documentList"]["responseSet"] 
        similar = response_set[0]["similarityMatch"]["similarDocs"]["AOP.016.0171A"]
        for n in similar:
            print (n)
        print (f"Similar Count: {len(similar)}")
        assert(len(similar) == 4)
        

if __name__ == '__main__':
    unittest.main()
