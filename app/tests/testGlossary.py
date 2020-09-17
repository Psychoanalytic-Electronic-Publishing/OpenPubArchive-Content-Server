#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

#  This test module is in development...

import sys
import os.path

folder = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
if folder == "tests": # testing from within WingIDE, default folder is tests
    sys.path.append('../libs')
    sys.path.append('../config')
    sys.path.append('../../app')
else: # python running from should be within folder app
    sys.path.append('./libs')
    sys.path.append('./config')

from starlette.testclient import TestClient

import unittest
from localsecrets import TESTUSER, TESTPW, SECRET_KEY, ALGORITHM
import opasAPISupportLib

from unitTestConfig import base_api, base_plus_endpoint_encoded
from main import app 

client = TestClient(app)

class TestGlossary(unittest.TestCase):
    """
    Test of wingware testing
    """   

    def test_0_glossary_search(self):
        """
        """
        response = client.get(base_api + '/v2/Database/Glossary/Search/?fulltext1="freudian slip"')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 1)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)

        response = client.get(base_api + '/v2/Database/Glossary/Search/?fulltext1=unconcious')
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
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={TESTUSER}&password={TESTPW}')
        response = client.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Glossary/WALLERSTEIN, ROBERT S/?termidtype=Group')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = client.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        print (response_set)

    def test_1b_get_glossary_endpoint_GROUP(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={TESTUSER}&password={TESTPW}')
        response = client.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Glossary/ANXIETY/?termidtype=Group')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = client.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 7)
        print (response_set)
        
    def test_1c_get_glossary_endpoint_NAME(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={TESTUSER}&password={TESTPW}')
        response = client.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Glossary/WHEELWRIGHT, JOSEPH BALCH (1906-99)/?termidtype=Name')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = client.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        print (response_set)
        
    def test_1c2_get_glossary_endpoint_NAME(self):
        # try with lower case
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={TESTUSER}&password={TESTPW}')
        response = client.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Glossary/wheelwright, JOSEPH BALCH (1906-99)/?termidtype=Name')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = client.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        print (response_set)

    def test_1d_get_glossary_endpoint_ID(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={TESTUSER}&password={TESTPW}')
        response = client.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Glossary/YP0017805628220.001/?termidtype=ID')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = client.get(full_URL)
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
