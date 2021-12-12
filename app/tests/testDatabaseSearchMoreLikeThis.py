#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestDatabaseSearchMoreLikeThis(unittest.TestCase):
    def test_search_morelike_1a(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=AOP&fulltext1=mind&parascope=dreams&similarcount=4')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert response_info["count"] >= 15, f"Expected Count >= 15, Count: {response_info['count']}"
        first_key = list(response_set[0]["similarityMatch"]["similarDocs"].keys())[0]
        length = len(list(response_set[0]["similarityMatch"]["similarDocs"].values())[0])
        assert length >= 2, f"Expected Values: Count >= 2, First Key: {first_key}, Count: {length}" 

    def test_search_morelike_2a(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/MoreLikeThis/?morelikethis=IJP.078.0335A')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert response_info["count"] == 1, f"Expected Count == 1, Count: {response_info['count']}"
        first_key = list(response_set[0]["similarityMatch"]["similarDocs"].keys())[0]
        length = len(list(response_set[0]["similarityMatch"]["similarDocs"].values())[0])
        assert length >= 4, f"Expected Values: Count >= 4, First Key: {first_key}, Count: {length}" 
        

if __name__ == '__main__':
    unittest.main()
