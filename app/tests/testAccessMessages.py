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
sessID, headers, session_info = test_login(username=localsecrets.PADS_TEST_ID2, password=localsecrets.PADS_TEST_PW3)

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
        print(response_set["accessClassification"])
        print(response_set["accessLimitedReason"])
        print(response_set["accessLimitedDescription"])

    def test_001A_get_future_document(self):
        # Try to return current content, should only return abstract
        full_URL = base_plus_endpoint_encoded(f"/v2/Documents/Document/JPT.005.0065A/?return_format=XML")
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r["detail"])
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"][0]
        assert (response_set["accessLimited"] == True)   

    def test_001A_get_marked_embargoed_document(self):
        # Try to return current content, should only return abstract
        full_URL = base_plus_endpoint_encoded(f"/v2/Documents/Document/JPT.005.0065A/?return_format=XML")
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r["detail"])
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"][0]
        assert (response_set["accessLimited"] == True)   

    def test_001A_download_embargoed_document_PDF(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDF/IJP.102.0006A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])

    def test_001A_download_embargoed_document_PDF_ORIG(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFOrig/IJP.102.0006A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])

    def test_001D_nonexistent_document(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/APA.064E.6666A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])

    def test_001D_nonexistent_document_download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFOrig/APA.064E.6666A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])

    def test_002A_Future_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFORIG/PPC.004.0026A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        assert(response.ok == False)

    def test_002B_Current_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFORIG/IJP.102.0006A/')
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