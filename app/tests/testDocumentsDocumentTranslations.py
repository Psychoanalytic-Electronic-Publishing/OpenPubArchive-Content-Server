#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import logging
import opasConfig

logger = logging.getLogger(__name__)

import unittest
import requests

from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, test_login
import opasAPISupportLib

# Login!
sessID, headers, session_info = test_login()

class TestGetDocumentTranslations(unittest.TestCase):
    """
    Tests for fields containing document translations in document record
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    doc_with_translations = 'ANIJP-DE.001.0127A'
    def test_0_fetch_article_with_translations(self):
        """
        Retrieve a known article with translations; make sure it returns the right number or more.
        """
        # this newer function includes the search parameters if there were some
        print (f"Current Session: ")
        data = opasAPISupportLib.documents_get_document(self.doc_with_translations, session_info=session_info, option_flags=opasConfig.OPTION_2_RETURN_TRANSLATION_SET)
        # Confirm that the request-response cycle completed successfully.
        assert data.documents.responseInfo.fullCount == 1, f"Document {self.doc_with_translations} not found"
        assert len(data.documents.responseSet[0].translationSet) >= 3, f"Document {self.doc_with_translations} has too few translations returned"

    def test_api_translation_request(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/{self.doc_with_translations}/?translations=true')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        data = r["documents"]["responseSet"] 
        assert len(data[0]["translationSet"]) >= 3, f"Document {self.doc_with_translations} has two few translations returned"

    def test_api_translation_request_alt(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/{self.doc_with_translations}/?specialoptions=2')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        data = r["documents"]["responseSet"] 
        assert len(data[0]["translationSet"]) >= 3, f"Document {self.doc_with_translations} has two few translations returned"

if __name__ == '__main__':
    unittest.main()    