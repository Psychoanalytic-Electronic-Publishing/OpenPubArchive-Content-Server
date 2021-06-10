#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant

import logging
logger = logging.getLogger(__name__)

import unittest
import requests

from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID

class TestDatabaseAdvancedSearch(unittest.TestCase):
    
    def test_search_advanced1(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/AdvancedSearch/?advanced_query=art_type:(SUP OR TOC)')
        response = requests.post(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)
        print (response_set[0])

    def test_search_advanced2(self):
        # query using user friendly field name
        full_URL = base_plus_endpoint_encoded('/v2/Database/AdvancedSearch/?advanced_query=authors:Tuckett')
        response = requests.post(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["fullCount"] >= 50)
        print (response_set[0])

    def test_search_advanced3(self):
        # query using user boolean with multiple fields
        full_URL = base_plus_endpoint_encoded('/v2/Database/AdvancedSearch/?advanced_query=authors:(Tuckett AND Fonagy) OR authors:(Levinson, N*)')
        response = requests.post(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["fullCount"] >= 2)
        print (response_set[0])

    def test_search_advanced4(self):
        # query using user boolean with parens
        full_URL = base_plus_endpoint_encoded('/v2/Database/AdvancedSearch/?advanced_query=text:(Monkey AND NOT singer OR delusional AND NOT (science OR toy OR wrench OR rat OR back OR mate OR survey))')
        response = requests.post(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["fullCount"] >= 3 and response_info["fullCount"] < 6)
        print (response_set[0])

    def test_search_advanced5(self):
        # query using paragraph search (only applies to Freud SE and GW currently)
        full_URL = base_plus_endpoint_encoded('/v2/Database/AdvancedSearch/?advanced_query={!parent which="art_level:1"} art_level:2 AND parent_tag:p_dream')
        response = requests.post(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["fullCount"] >= 1)
        print (response_set[0])

    def test_search_advanced6(self):
        # query for body summaries or appendixes paragraphs containing "asylum" and "house" within the same paragraph and bring back the document info.
        # note this only applies to Freud SE and GW since paragraphs are only indexed within those.
        # originally all documents were index that way but now paragraph proximity is simulated via ~25 (within 25 words) instead
        # the first part: {!parent which="art_level:1"} tells Solr to only bring back the level 1 info (the document info)
        full_URL = base_plus_endpoint_encoded('/v2/Database/AdvancedSearch/?advanced_query={!parent which="art_level:1"} parent_tag:(p_body || p_summaries || p_appxs) && para:(asylum house)')
        response = requests.post(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["fullCount"] >= 1)
        print (response_set[0])




if __name__ == '__main__':
    unittest.main()
    