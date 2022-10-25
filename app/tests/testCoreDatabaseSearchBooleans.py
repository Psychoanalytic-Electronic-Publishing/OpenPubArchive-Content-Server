#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestDatabaseSearchBooleans(unittest.TestCase):
    def test_01_search_fulltext1_booleans_relative_test(self):
        # Send a request to the API server and store the response.
        # ### OR #####
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=Mother+or+Father')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        bool_or = response_info["fullCount"]
        print(f"bool_or {bool_or}")
        assert(bool_or >= 10)

        # ### AND #####
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=Mother+and+Father')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        bool_and = response_info["fullCount"]
        print(f"bool_and {bool_and} < bool_or {bool_or}")
        assert(bool_and < bool_or)
        
        # ### NOT #####
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=Mother+not+Father')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        bool_not = response_info["fullCount"]
        print(f"bool_not {bool_not} < bool_or {bool_or}")
        assert(bool_not < bool_or)
        

if __name__ == '__main__':
    unittest.main()
    