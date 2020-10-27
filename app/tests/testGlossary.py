#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from localsecrets import PADS_TEST_ID, PADS_TEST_PW

import opasAPISupportLib
import opasDocPermissions

from unitTestConfig import base_plus_endpoint_encoded, headers, session_id


# login
session_info, pads_response = opasDocPermissions.pads_login(username=PADS_TEST_ID, password=PADS_TEST_PW, session_id=session_id)
# Confirm that the request-response cycle completed successfully.
session_id = pads_response.SessionId
headers = {f"client-session":f"{session_id}",
           "client-id": "4"
           }

class TestGlossary(unittest.TestCase):
    """
    """   

    def test_0_glossary_search(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Glossary/Search/?fulltext1="freudian slip"')
        # Confirm that the request-response cycle completed successfully.
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 1)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)

        full_URL = base_plus_endpoint_encoded('/v2/Database/Glossary/Search/?fulltext1=unconcious')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 1)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)
       
    def test_00_get_glossary(self):
        ret = opasAPISupportLib.documents_get_glossary_entry("YN0019667860580", term_id_type="ID", retFormat="html") 
        print (ret)

    def test_1a_get_glossary_endpoint_GROUP(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Glossary/WALLERSTEIN, ROBERT S/?termidtype=Group')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        print (response_set)

    def test_1b_get_glossary_endpoint_GROUP(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Glossary/ANXIETY/?termidtype=Group')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 7)
        print (response_set)
        
    def test_1c_get_glossary_endpoint_NAME(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Glossary/WHEELWRIGHT, JOSEPH BALCH (1906-99)/?termidtype=Name')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        print (response_set)
        
    def test_1c2_get_glossary_endpoint_NAME(self):
        # Confirm that the request-response cycle completed successfully.
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Glossary/wheelwright, JOSEPH BALCH (1906-99)/?termidtype=Name')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        print (response_set)

    def test_1d_get_glossary_endpoint_ID(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Glossary/YP0017805628220.001/?termidtype=ID')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        print (response_set)
        
if __name__ == '__main__':
    unittest.main()
