#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import logging
logger = logging.getLogger(__name__)

import unittest
import requests

import opasDocPermissions
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, test_login

# Login!
sessID, headers, session_info = test_login()

class TestGetDocumentSearchRemoveNuisanceHits(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """

    def test_search_fulltext0(self):
        full_URL = base_plus_endpoint_encoded(f"/v2/Documents/Document/AIM.051.0247A/?formatrequested=XML&search='&fulltext1=text%3A(%22anxiety+hysteria%22~25)&highlightlimit=5&limit=20&offset=0&sort=author&synonyms=false'")
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        # print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"]
        match_count = response_set[0]["hitCount"]
        assert(match_count >= 1)
        print (response_set[0]["document"][:1000])
    
    def test_2_get_document_with_search_context(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/IRP.002.0199A/?return_format=XML&search=%27%3Ffacetfields%3Dart_year_int%252Cart_views_last12mos%252Cart_cited_5%252Cart_authors%252Cart_lang%252Cart_type%252Cart_sourcetype%252Cart_sourcetitleabbr%252Cglossary_group_terms%252Cart_kwds_str%26facetlimit%3D15%26facetmincount%3D1%26highlightlimit%3D5%26synonyms%3Dfalse%26fulltext1%3Din%2Bhis%2Banalytic%2Befforts%27')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        # print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"]
        match_count = response_set[0]["hitCount"]
        assert(match_count >= 1)
        print (response_set[0]["document"][:1000])


if __name__ == '__main__':
    unittest.main()    