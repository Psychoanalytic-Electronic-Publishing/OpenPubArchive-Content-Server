#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Updates:
#  2022-10-25 - Set to use only sample data

import unittest
import requests
from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestAuthorsIndex(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.

    2022-10-25 These tests only require the Opas sample data to be loaded
    """   

    def test_01_index_authornamepartial(self):
        """
        Get Author Index For Matching Author Names
        /v1/Authors/Index/{authorNamePartial}/
        """
        full_URL = base_plus_endpoint_encoded('/v2/Authors/Index/Heath/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["authorIndex"]["responseInfo"]
        response_set = r["authorIndex"]["responseSet"][0]
        assert response_info["count"] >= 4, response_info["count"]
       
    def test_02_index_authornamepartial(self):
        full_URL = base_plus_endpoint_encoded('/v2/Authors/Index/Kahr/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["authorIndex"]["responseInfo"]
        response_set = r["authorIndex"]["responseSet"][0]
        assert(response_set['publicationsURL'] == '/v2/Authors/Publications/kahr, brett/')
        
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")