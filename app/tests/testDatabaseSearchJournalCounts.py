#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestDatabaseSearchJournalCounts(unittest.TestCase):
    def test_1a_search_sourcecodes(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?art_sourcecode=ADPSA') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["fullCount"])
        assert(response_info["fullCount"] >= 291)
        
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?art_sourcecode=IJPSPPSC') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["fullCount"])
        assert(response_info["fullCount"] >= 158)

    def test_2a_sourcecode_facets(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=art_sourcecode') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["art_sourcecode"])
        assert(response_info["fullCount"] >= 291)
        


if __name__ == '__main__':
    unittest.main()
    