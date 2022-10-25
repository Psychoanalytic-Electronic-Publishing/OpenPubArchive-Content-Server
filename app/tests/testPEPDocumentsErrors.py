#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import logging
logger = logging.getLogger(__name__)

import unittest
import requests
import localsecrets

from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, test_login

# Login!
sessID, headers, session_info = test_login()

class TestDocumentsDocumentErrors(unittest.TestCase):
    """
    Tests for basic login and Download
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    
    search_term = "test"
    # good example (from testGetDocument)
    def test_001A_get_document_with_hits(self):
        # test with real client example
        search_param = f"?facetfields=art_year_int,art_views_last12mos,art_cited_5,art_authors,art_lang,art_type,art_sourcetype,art_sourcetitleabbr,glossary_group_terms,art_kwds_str&facetlimit=15&facetmincount=1&highlightlimit=4&synonyms=false&fulltext1={self.search_term}"
        search_param_encoded = requests.utils.quote(search_param)
        full_URL = base_plus_endpoint_encoded(f"/v2/Documents/Document/IJP.056.0303A/?return_format=XML&search={search_param_encoded}")
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"]
        assert(response_info["count"] == 1)
        termCount = r["documents"]["responseSet"][0]["termCount"]
        term = r["documents"]["responseSet"][0]["term"]
        print (f"Term: {term} / TermCount: {termCount}")
        assert (term == f"SearchHits(text:{self.search_term})")
        assert(termCount > 0)

    # now let's get back some errors
    def test_001B_get_embargoed_document(self):
        # Try to return current content, should only return abstract
        full_URL = base_plus_endpoint_encoded(f"/v2/Documents/Document/AJP.080.0001A/?return_format=XML")
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"]
        assert(response_info["count"] == 1)
        # should be classified as current content
        assert(response_set[0]["accessLimitedClassifiedAsCurrentContent"] == True)
        # we should not have access
        assert(response_set[0]["accessLimited"] == True)
        # see "why" -- it's current content
    

    def test_001C_nonexistent_document(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/APA.064E.6666A/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.status_code == 404)
        assert(response.reason == "Not Found")

    def test_001D_nonexistent_session(self):
        search_param = f"?facetfields=art_year_int,art_views_last12mos,art_cited_5,art_authors,art_lang,art_type,art_sourcetype,art_sourcetitleabbr,glossary_group_terms,art_kwds_str&facetlimit=15&facetmincount=1&highlightlimit=4&synonyms=false&fulltext1={self.search_term}"
        search_param_encoded = requests.utils.quote(search_param)
        full_URL = base_plus_endpoint_encoded(f"/v2/Documents/Document/IJP.056.0303A/?return_format=XML&search={search_param_encoded}")
        headers = {f"client-session":f"123456789",
                   "client-id": UNIT_TEST_CLIENT_ID, 
                   "Content-Type":"application/json",
                   localsecrets.API_KEY_NAME: localsecrets.API_KEY}
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        print(response.status_code)
        assert(response.status_code == 424)
        print (response.reason)
        assert(response.reason == "Failed Dependency")
        
if __name__ == '__main__':
    unittest.main()    