#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Updates:
#  2022-10-25 - Set to use only sample data

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

import unittest

from starlette.testclient import TestClient

from unitTestConfig import base_plus_endpoint_encoded, headers, test_login
# from localsecrets import PADS_TEST_ID, PADS_TEST_PW, PADS_BASED_CLIENT_IDS, AUTH_KEY_NAME

from main import app
client = TestClient(app)

# Login!
sessID, headers, session_info = session_id = test_login()
    
class TestClientLogin(unittest.TestCase):

    def test_client_login_document_access(self):
        # Login to PaDS with test account and then check responses to mostCited for access.
        # 2020-11-06 change document...too many requests for the same as on the home page of the new PEP-Web
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/BIP.001.0342A/')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = client.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        assert(response_set[0]["accessLimited"] == False)


if __name__ == '__main__':
    unittest.main()
