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
import requests
from localsecrets import TESTUSER, TESTPW, SECRET_KEY, ALGORITHM
#import jwt
from datetime import datetime
import opasAPISupportLib
#import opasConfig
#import opasQueryHelper
import opasCentralDBLib
import opasDocPermissions as opasDocPerm

#import models
# from main import app

# client = TestClient(app)

ocd = opasCentralDBLib.opasCentralDB()

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
        response = opasDocPerm.pads_login()
        ## Confirm that the request-response cycle completed successfully.
        try:
            sessID = response["SessionId"]
        except:
            err = f"PaDS response error: {response}"
            logger.error(err)
            print (err)
            assert(False)
        else:
            full_URL = base_plus_endpoint_encoded('/v2/Documents/Concordance/?paralangid=SEXixa5')
            response = requests.get(full_URL, headers={"client-session":sessID, "client-id": "2", "Content-Type":"application/json"})
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