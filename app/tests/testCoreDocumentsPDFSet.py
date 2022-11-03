#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

#  This test module is in development...

import opasDocPermissions
import requests
import urllib
import tempfile
import os

import logging
logger = logging.getLogger(__name__)

import unittest
from localsecrets import PADS_TEST_ID, PADS_TEST_PW, PDF_ORIGINALS_PATH, PADS_TEST_ID2, PADS_TEST_PW2
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, test_login

# Login!
sessID, headers, session_info = test_login(username=PADS_TEST_ID2, password=PADS_TEST_PW2)

import opasPySolrLib

class TestDocumentDownloadSetForInspection(unittest.TestCase):
    """
    Tests to create a set of downloaded PDFs and EPubs to be inspected for presentation issues.
    
    Test results are not automated...this automates the production of test materials only.
    Results are stored in the system temp folder/directory
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.   
    """
    
    testArticlesAllFormats = [
        "PEPGRANTVS.001.0004A",
        "BAFC.012.0071A"
    ]
    
    def test_1_Download_generated(self):
        tempdir = tempfile.gettempdir()
        os.chdir(tempdir)
        for testArticle in self.testArticlesAllFormats:
            print (f"Downloading generated format for: {testArticle}.")
            try:
                full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDF/{testArticle}/')
                response = requests.get(full_URL, headers=headers)
                    
            except Exception as e:
                print (f"{testArticle} not available in that format.")
            else:
                print (f"Downloads complete for {testArticle} in folder {tempdir}. Ready for manual evaluation.")
                
    def test_1_Download_epub(self):
        tempdir = tempfile.gettempdir()
        os.chdir(tempdir)
        for testArticle in self.testArticlesAllFormats:
            print (f"Downloading generated format for: {testArticle}.")
            try:
                full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/EPUB/{testArticle}/')
                response = requests.get(full_URL, headers=headers)
                    
            except Exception as e:
                print (f"{testArticle} not available in that format.")
            else:
                print (f"Downloads complete for {testArticle} in folder {tempdir}. Ready for manual evaluation.")

if __name__ == '__main__':
    unittest.main()    