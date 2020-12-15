#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers

class TestSearchBooleans(unittest.TestCase):
    def test_01_search_fulltext1_with_client_id(self):
        # Send a request to the API server and store the response.
        # ### OR #####
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=Mother+or+Father')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)

    def test_01_search_fulltext1_no_client_id(self):
        
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=Mother+or+Father')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        print (r)
        

if __name__ == '__main__':
    unittest.main()
    