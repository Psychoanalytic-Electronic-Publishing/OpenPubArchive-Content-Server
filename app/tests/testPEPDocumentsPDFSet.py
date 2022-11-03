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
        "CPS.053.0602A",
        "CPS.041.0651A",
        "CPS.041.0021A",
        "IJPSPPSC.015.0320A", # small margins!
        "ADPSA.013.0232A",
        "AJP.078.0421A", 
        "AJRPP.014.0001A", 
        "ANIJP-CHI.001.0018A", 
        "ANIJP-DE.013.0059A", 
        "ANIJP-FR.2017.0149A", 
        "ANIJP-TR.001.0053A", 
        "ANRP.001.0007A", 
        "APA.059.0166A", 
        "APM.032.0077A", 
        "BAFC.015.0147A", # line "border" around page
        "BIP.077.0182A", 
        "BJP.035.0179A", 
        "CJP.024.0142A", 
        "DR.015.0056A", 
        "FA.013a.0096A", 
        "fd.021a.0011a",
        "IFP.024.0063A", # small margins!
        "IJAPS.012.0304A", # small margins!
        "IJP.080.1260A", # small margins!
        "IJP-ES.002.1359A", # no margins!
        "JAA.028.0483A", # small margins!
        "JICAP.016.0189A", #  small margins!
        "JOAP.063.0692A", # no top margin!
        "MPSA.025.0279A", # line "border" around page
        "NP.017.0053A", #  small margins!
        "PAH.015.0110A",
        "PD.004.0583A",
        "PSC.069.0146A", # stuff at the very bottom
        "PSP.016.0103A", # crooked scans, can be towards bottom
        "RBP.032.0043A", # line "border" around page
        "RPP-CS.012A.0072A", # stuff at the very bottom
        "SGS.018.0251A", #  small margins!
        "TVPA.021.0321A", # stuff at the very bottom
    ]
    
    def test_1_Download_orig(self):
        tempdir = tempfile.gettempdir()
        os.chdir(tempdir)
        for testArticle in self.testArticlesAllFormats:
            print (f"Downloading original formats for: {testArticle}.")
            try:
                full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFORIG/{testArticle}/')
                response = requests.get(full_URL, headers=headers)
                    
                #opener = urllib.request.build_opener()
                #headerlist = [(k, v) for k, v in headers.items()]
                #opener.addheaders = headerlist
                #urllib.request.install_opener(opener)        
                #fullfilename = os.path.join(tempdir, testArticle + ".orig.pdf")
                #response = urllib.request.urlretrieve(full_URL, filename=fullfilename)
                # Confirm that the request-response cycle completed successfully.
                #assert(response[1]["content-type"] == 'application/pdf')
            except Exception as e:
                print (f"{testArticle} not available in that format.")
            else:
                print (f"Downloads complete for {testArticle} in folder {tempdir}. Ready for manual evaluation.")
                
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