#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

import unittest
import requests
import localsecrets

import opasDocPermissions
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, test_login 

# Login!
sessID, headers, session_info = test_login(username=localsecrets.PADS_TEST_ID, password=localsecrets.PADS_TEST_PW)

class TestAccessMessageDisplay_To_INSPECT_MANUALLY(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    print ("These tests will always pass barring an exception encountered.  The return data is for human inspection.")
    search_term = "test"
    # now let's get back some errors
    def test_001A_get_current_document(self):
        # Try to return current content, should only return abstract
        full_URL = base_plus_endpoint_encoded(f"/v2/Documents/Document/AJP.080.0001A/?return_format=XML")
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"][0]
        assert (response_set["accessLimited"] == True)
        assert (response_set["accessClassification"] == 'current')
        print(f'Classification: {response_set["accessClassification"]}')
        print(f'Reason: {response_set["accessLimitedReason"]}')
        print(f'Description: {response_set["accessLimitedDescription"]}')

    def test_001A_get_future_document(self):
        # Try to return current content, should only return abstract
        full_URL = base_plus_endpoint_encoded(f"/v2/Documents/Document/JPT.005.0065A/?return_format=XML")
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"][0]
        assert (response_set["accessLimited"] == True)   
        assert (response_set["accessClassification"] == 'future')
        print(f'Classification: {response_set["accessClassification"]}')
        print(f'Reason: {response_set["accessLimitedReason"]}')
        print(f'Description: {response_set["accessLimitedDescription"]}')

    def test_001A_get_marked_embargoed_document(self):
        # Try to return current content, should only return abstract
        full_URL = base_plus_endpoint_encoded(f"/v2/Documents/Document/IJPOPEN.004.0013A/?return_format=XML")
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"][0]
        print(f'Classification: {response_set["accessClassification"]}')
        print(f'Reason: {response_set["accessLimitedReason"]}')
        print(f'Description: {response_set["accessLimitedDescription"]}')

    # Embargoed files (removed IJPOPen for example, xml flag:embargo=true)
    def test_001B_download_embargoed_document_PDF(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDF/IJPOPEN.004.0013A/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == False)

    def test_001C_download_embargoed_document_PDF_ORIG(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFOrig/IJPOPEN.004.0013A/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == False)

    def test_001C_download_embargoed_document_EPUB(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/EPUB/IJPOPEN.004.0013A/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == False)

    # Download restricted files (currently long books)
    def test_001D_download_prohibited_documentPDF_ORIG_Page_Restricted(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFOrig/SE.004.R0009A/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == False)

    def test_001D_download_prohibited_document_PDF(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDF/IPL.064.0001A/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == False)

    def test_001D_download_prohibited_document_PDF(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFOrig/IPL.064.0001A/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == False)

    def test_001D_download_prohibited_document_EPUB(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/EPUB/IPL.064.0001A/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == False)

    def test_001D_download_prohibited_document_PDF_EXCEPTION(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDF/IPL.064.0001A/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == False)

    def test_001D_download_prohibited_document_PDF_EXCEPTION(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFOrig/IPL.064.0001A/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == False)

    def test_001D_download_prohibited_document_EPUB_EXCEPTION(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/EPUB/IPL.064.0001A/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == False)

    def test_001D_nonexistent_document(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/APA.064E.6666A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        assert(response.ok == False)

    def test_001D_nonexistent_document_download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFOrig/APA.064E.6666A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        assert(response.ok == False)

    def test_002A_Future_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFORIG/PPC.004.0026A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        assert(response.ok == False)

    def test_002B_Current_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFORIG/JICAP.020.0015A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        assert(response.ok == False)

    def test_001D_nonexistent_session(self):
        full_URL = base_plus_endpoint_encoded(f"/v2/Documents/Document/IJP.056.0303A/?return_format=XML")
        headers = {f"client-session":f"123456789",
                   "client-id": UNIT_TEST_CLIENT_ID, 
                   "Content-Type":"application/json",
                   localsecrets.API_KEY_NAME: localsecrets.API_KEY}
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        
if __name__ == '__main__':
    unittest.main()    