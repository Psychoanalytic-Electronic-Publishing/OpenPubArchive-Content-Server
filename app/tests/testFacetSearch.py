#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests
import urllib.parse

from unitTestConfig import base_api, base_plus_endpoint_encoded, headers

class TestFacetSearch(unittest.TestCase):
    def test_2a_facet_search_author(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=Tuckett&facetquery=art_sourcecode:APA&facetfields=art_sourcecode') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["art_sourcecode"])

    def test_2a_facet_search_author_views(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=Tuckett&facetquery=art_views_last12mos:1&facetfields=art_views_last12mos') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["art_views_last12mos"])

    def test_2a_facet_search_author_citations(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=Tuckett&facetquery=art_cited_5:1&facetfields=art_cited_5') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["art_cited_5"])

    def test_2a_facet_search_author_views(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=Tuckett&facetquery=art_cited_5:1&facetfields=art_cited_5') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["art_cited_5"])



if __name__ == '__main__':
    unittest.main()
    