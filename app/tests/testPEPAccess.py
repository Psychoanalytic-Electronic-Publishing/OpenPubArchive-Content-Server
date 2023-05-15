#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

import unittest
import requests
import localsecrets
import pprint
import sys

# import opasDocPermissions
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, test_login, test_logout, get_headers_not_logged_in

# Login!
sessID, headers, session_info = test_login(username=localsecrets.PADS_TEST_ARCHIVEONLY, password=localsecrets.PADS_TEST_ARCHIVEONLY_PW)

FUTURE_DOC = None # "PCAS.008.0003A"
global message_collection
global pp
pp = pprint.PrettyPrinter(indent=5, width=70) # , stream=sys.stderr) # , sort_dicts=True) sort_dicts requires py 3.8
message_collection = {}

class TestAccess(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    userid = localsecrets.PADS_TEST_ARCHIVEONLY
    userpw = localsecrets.PADS_TEST_ARCHIVEONLY_PW
    usertype = "Registered user"
    print (f"Login PADS_TEST_ARCHIVEONLY! {userid} - {usertype}")
    sessID, headers, session_info = test_login(username=userid, password=userpw)
    search_term = "test"

    def test_001B_download_embargoed_document_PDF(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDF/APA.068.0027A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        assert(response.ok == False)

    def test_001C_download_embargoed_document_PDF_ORIG(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFOrig/IJPOPEN.004.0013A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        assert(response.ok == False)

    def test_001C_download_embargoed_document_EPUB(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/EPUB/IJPOPEN.004.0013A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        assert(response.ok == False)

    # Download restricted files (currently long books)
    def test_001D_download_prohibited_documentPDF_ORIG_Page_Restricted(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFOrig/SE.004.R0009A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        assert(response.ok == False)

    def test_001D_download_prohibited_document_PDF(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDF/SE.004.R0009A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        assert(response.ok == False)

    def test_001D_download_prohibited_document_EPUB(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/EPUB/SE.004.R0009A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        assert(response.ok == False)

    def test_001D_download_prohibited_document_PDF_EXCEPTION(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDF/SE.004.R0009A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        assert(response.ok == False)
        usertype = "prohibited.download.pdflong"
        message_collection[usertype] = {r["detail"]}

    def test_001D_download_prohibited_document_PDFORIG_EXCEPTION(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFOrig/SE.004.R0009A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        assert(response.ok == False)
        usertype = "prohibited.download.pdforig"
        message_collection[usertype] = {r["detail"]}

    def test_001D_download_prohibited_document_EPUB_EXCEPTION(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/EPUB/SE.004.R0009A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        assert(response.ok == False)
        usertype = "prohibited.download.epub"
        message_collection[usertype] = {r["detail"]}

    def test_002A_Future_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFORIG/PPC.004.0026A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        assert(response.ok == False)
        usertype = "future.download"
        message_collection[usertype] = {r["detail"]}
        

    def test_002B_Current_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFORIG/JICAP.020.0015A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        assert(response.ok == False)
        usertype = "subs.current.download"
        message_collection[usertype] = {r["detail"]}

    # now let's get back some errors
    def test_010A_nonexistent_session(self):
        full_URL = base_plus_endpoint_encoded(f"/v2/Documents/Document/IJP.056.0303A/?return_format=XML")
        headers = {f"client-session":f"123456789",
                   "client-id": UNIT_TEST_CLIENT_ID, 
                   "Content-Type":"application/json",
                   localsecrets.API_KEY_NAME: localsecrets.API_KEY}
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        assert(response.ok == False)

    def test_010B_nonexistent_document(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/APA.064E.6666A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        assert(response.ok == False)

    def test_010C_nonexistent_document_download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFOrig/APA.064E.6666A/')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r["detail"])
        assert(response.ok == False)
    
if __name__ == '__main__':
    unittest.main()
    print (message_collection)
    pp.pprint(message_collection)