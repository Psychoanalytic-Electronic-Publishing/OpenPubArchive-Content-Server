#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID

class TestDocumentsAbstracts(unittest.TestCase):
    """
    Tests for basic login and Download
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    
    def test_1a_get_abstract_html_not_logged_in(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Abstracts/IFP.017.0240A?similarcount=4')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        abstract = response_set[0]["abstract"]
        print (f"Abstract Length: {len(abstract)}")
       
    def test_1a_get_abstract_logged_in(self):
        # login
        from localsecrets import PADS_TEST_ARCHIVEONLY, PADS_TEST_ARCHIVEONLY_PW
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={PADS_TEST_ARCHIVEONLY}&password={PADS_TEST_ARCHIVEONLY_PW}')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        headers["client-session"] = r["session_id"]
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Abstracts/IFP.017.0240A?similarcount=4')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        abstract = response_set[0]["abstract"]
        assert(response_set[0]["pdfOriginalAvailable"] == True)
        print (f"Abstract Length: {len(abstract)}")
        #print (abstract)

    def test_1a_get_abstract_html_not_logged_in(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Abstracts/IFP.017.0240A?similarcount=4')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        abstract = response_set[0]["abstract"]
        print (f"Abstract Length: {len(abstract)}")
        #print (abstract)
       
    def test_1a_get_abstract_xml(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Abstracts/IFP.017.0240A?similarcount=4&return_format=XML')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        abstract = response_set[0]["abstract"]
        print (f"Abstract Length: {len(abstract)}")
        #print (abstract)
       
    def test_1a_get_abstract_textonly(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Abstracts/IFP.017.0240A?similarcount=4&return_format=TEXTONLY')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        abstract = response_set[0]["abstract"]
        print (f"Abstract Length: {len(abstract)}")
        #print (abstract)
       
    def test_2a_get_multiple_abstracts(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Abstracts/IFP.017')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        print(response_info["fullCount"])
        assert(response_info["fullCount"] == 36)
        
    def test_2a_get_abstract_permissions(self):
        from localsecrets import PADS_TEST_ARCHIVEONLY, PADS_TEST_ARCHIVEONLY_PW,  AUTH_KEY_NAME
        # login
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={PADS_TEST_ARCHIVEONLY}&password={PADS_TEST_ARCHIVEONLY_PW}')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        headers["client-session"] = r["session_id"]
        headers[AUTH_KEY_NAME] = "true"

        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Abstracts/PAQ.085.0885A')
        response = requests.get(full_URL, headers=headers)
        r1 = response.json()
        response_info = r1["documents"]["responseInfo"]
        response_set = r1["documents"]["responseSet"]
        doc_of_interest = r1["documents"]["responseSet"][0]
        # Abstract requests no longer return permissions
        accessChecked = doc_of_interest["accessChecked"]
        assert (accessChecked == True)
        accessLimited = doc_of_interest["accessLimited"]
        assert (accessLimited == False)
        
            
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/PAQ.085.0851A/?similarcount=5&return_format=XML')
        response = requests.get(full_URL, headers=headers)
        r2 = response.json()
        response_info = r2["documents"]["responseInfo"]
        response_set = r2["documents"]["responseSet"]
        doc_of_interest = r2["documents"]["responseSet"][0]
        accessLimited = doc_of_interest["accessLimited"]
        assert (accessLimited == False)
        assert(response_set[0]["pdfOriginalAvailable"] == True)

if __name__ == '__main__':
    unittest.main()    