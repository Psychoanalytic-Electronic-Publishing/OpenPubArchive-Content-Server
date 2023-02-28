#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

#  This test module is in development...

import opasDocPermissions
import requests

import logging
logger = logging.getLogger(__name__)

import unittest
from localsecrets import PADS_TEST_ID, PADS_TEST_PW, PDF_ORIGINALS_PATH
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, test_login

# Login!
sessID, headers, session_info = test_login()

class TestdocumentsDownload(unittest.TestCase):
    """
    Tests for basic login and Download
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.   
    """
    
    def test_0_fileexists(self):
        import opasFileSupport
        import localsecrets
        flex_fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY,
                                                 secret=localsecrets.S3_SECRET,
                                                 root=localsecrets.PDF_ORIGINALS_PATH) # important to use this path, not the XML one!
        document_id = "RPSA.047.0605A"
        filename = flex_fs.get_download_filename(filespec=document_id, path=localsecrets.PDF_ORIGINALS_PATH, year="2001", ext=".PDF")
        if filename is None:
            print (f"file {document_id} doesn't exist")
        else:
            print (f"file {filename} exists")

        assert(filename is not None)
        assert(opasFileSupport.file_exists(document_id, year="2001", ext=".PDF") == True)
        
        document_id = "RPSA.047.0605B"
        filename = flex_fs.get_download_filename(filespec=document_id, path=localsecrets.PDF_ORIGINALS_PATH, year="2001", ext=".PDF")
        if filename is None:
            print (f"file {document_id} doesn't exist")
        else:
            print (f"file {filename} exists")

        assert(filename is None)
        assert(opasFileSupport.file_exists(document_id, year="2001", ext=".PDF") == False)
            
    
    def test_1_PDFOrig_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFORIG/IJP.077.0217A/')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_2_PDF_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDF/IFP.017.0240A/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_2B_PDF_Download(self):
        # has grraphics
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDF/APA.007.0035A/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
       
    def test_2B_PDF_Download2(self):
        # has grraphics
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDF/BAP.013.0720A/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
       
    def test_2C_PDF_Download(self):
        import opasPySolrLib
        doc = opasPySolrLib.prep_document_download(document_id = "IFP.017.0240A",
                                                   session_info=session_info, 
                                                   ret_format="PDF",
                                                   base_filename="test",
                                                   flex_fs=None,
                                                   page=240, 
                                                   page_limit=2)        
        # Confirm that the request-response cycle completed successfully.
        assert(doc is not None)

    def test_2D_PDF_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDF/IFP.017.0240A/?pageoffset=3&pagelimit=3')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)

    def test_2D2_PDF_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDF/IFP.017.0240A/?page=240&pagelimit=3')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)

    def test_3_EPUB_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/EPUB/BAP.013.0720A/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_4_HTML_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/HTML/BAP.013.0720A/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_5_Most_Cited_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Database/MostCited/?download=true')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_6_Most_Viewed_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Database/MostViewed/?download=true')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_7a_PDFOrig_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFORIG/ANIJP-DE.001.0107A/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_8_PDFOrig_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFORIG/IJP.041.0335A/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_9_PDFOrig_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFORIG/ANIJP-CHI.001.0018A/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_10_Disallowed_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFORIG/pi.041.0138a/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        assert(response.ok == False)

    def test_11_PDFOrig_Download_Embargoed(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFORIG/PPC.003.0001A/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == False)

    def test_12_No_Downloads(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Abstracts/SE.001.0073A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        downloads = (r["documents"]["responseSet"][0]["downloads"])
        # Confirm that the request-response cycle completed successfully.
        assert(downloads == True)

    def test_12_Ok_Downloads(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Abstracts/IJP.041.0335A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        downloads = (r["documents"]["responseSet"][0]["downloads"])
        # Confirm that the request-response cycle completed successfully.
        assert(downloads == True)

    def test_14_PDF_Download_Book(self):
        # has grraphics
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDF/SE.001.0073A/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

if __name__ == '__main__':
    unittest.main()    