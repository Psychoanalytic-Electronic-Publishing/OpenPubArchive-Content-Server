#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

#  This test module is in development...

import sys
import os.path
import logging

logger = logging.getLogger(__name__)

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
from unitTestConfig import base_api, base_plus_endpoint_encoded
from localsecrets import PADS_TEST_ID, PADS_TEST_PW, PADS_BASED_CLIENT_IDS

import requests
from datetime import datetime
import opasAPISupportLib
#import opasConfig
#import opasQueryHelper
import opasCentralDBLib
import opasDocPermissions

#import models
# from main import app

# client = TestClient(app)

ocd = opasCentralDBLib.opasCentralDB()

# Login!
resp = opasDocPermissions.pads_login(username=PADS_TEST_ID, password=PADS_TEST_PW)
# Confirm that the request-response cycle completed successfully.
sessID = resp.SessionId
headers = {"client-session":sessID, "client-id": "0", "Content-Type":"application/json"}

class TestConcordance(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    def test1_get_para_translation(self):
        """
        """
        data = opasAPISupportLib.documents_get_concordance_paras("SEXixa5")
        # Confirm that the request-response cycle completed successfully.
        para_info = data.documents.responseSet[0].docChild
        para = para_info['para']
        print (para)
        assert (len(para) > 0)
        # check to make sure a known value is among the data returned
        
    def test2_concordance_endpoint(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Documents/Concordance/?paralangid=SEXixa5')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        r = response.json()
        para_cordance = r['documents']['responseSet'][0]['docChild']
        # Confirm that the request-response cycle completed successfully.
        para = para_cordance['para']
        print (para)
        assert (len(para) > 0)
        # check to make sure a known value is among the data returned
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")