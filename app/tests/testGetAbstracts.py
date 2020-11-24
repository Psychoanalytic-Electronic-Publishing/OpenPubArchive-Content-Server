#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID

class TestGetAbstracts(unittest.TestCase):
    """
    Tests for basic login and Download
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    
    def test_1a_get_abstract_html(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Abstracts/IFP.017.0240A?similarcount=4')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        abstract = response_set[0]["abstract"]
        print (abstract)
       
    def test_1a_get_abstract_xml(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Abstracts/IFP.017.0240A?similarcount=4&return_format=XML')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        abstract = response_set[0]["abstract"]
        print (abstract)
       
    def test_1a_get_abstract_textonly(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Abstracts/IFP.017.0240A?similarcount=4&return_format=TEXTONLY')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        abstract = response_set[0]["abstract"]
        print (abstract)
       
    def test_2a_get_multiple_abstracts(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Abstracts/IFP.017')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        print(response_info["fullCount"])
        assert(response_info["fullCount"] == 36)
        
    def test_2a_get_abstract_permissions(self):
        from localsecrets import PADS_TEST_ID, PADS_TEST_PW
        # login
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={"test1"}&password={PADS_TEST_PW}')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        headers["client-session"] = r["session_id"]

        full_URL = base_plus_endpoint_encoded(f'/v2/Database/Search/?abstract=true&formatrequested=XML&fulltext1=art_qual%3A(%22PAQ.085.0885A%22)&synonyms=false')
        response = requests.get(full_URL, headers=headers)
        r1 = response.json()
        response_info = r1["documentList"]["responseInfo"]
        response_set = r1["documentList"]["responseSet"]
        doc_of_interest = r1["documentList"]["responseSet"][4]
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

if __name__ == '__main__':
    unittest.main()    