#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

#  This test module is in development...

import sys
import os.path
import logging
import opasDocPermissions

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
from localsecrets import PADS_TEST_ID, PADS_TEST_PW
# import jwt
from datetime import datetime

from unitTestConfig import base_api, base_plus_endpoint_encoded
from main import app

client = TestClient(app)
resp = opasDocPermissions.pads_login(username=PADS_TEST_ID, password=PADS_TEST_PW)
# Confirm that the request-response cycle completed successfully.
sessID = resp.SessionId
headers = {f"client-session":f"{sessID}",
           "client-id": "2"
           }

class TestDownload(unittest.TestCase):
    """
    Tests for basic login and Download
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.   
    """   
    def test_1_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFORIG/IJP.077.0217A/')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = client.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_2_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDF/IFP.017.0240A/')
        response = client.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
       
    def test_3_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/EPUB/IJPSP.009.0324A/')
        response = client.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_4_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/HTML/IJPSP.009.0324A/')
        response = client.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_5_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Database/MostCited/?download=true')
        response = client.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_6_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Database/MostViewed/?download=true')
        response = client.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

if __name__ == '__main__':
    unittest.main()    