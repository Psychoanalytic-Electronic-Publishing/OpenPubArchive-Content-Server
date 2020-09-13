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
        
if __name__ == '__main__':
    unittest.main()
