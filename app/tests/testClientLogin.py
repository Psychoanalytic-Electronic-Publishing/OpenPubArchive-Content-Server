#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

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
import requests
# from requests.utils import requote_uri
# import urllib

from starlette.testclient import TestClient

from unitTestConfig import base_api, base_plus_endpoint_encoded
from localsecrets import TESTUSER, TESTPW, SECRET_KEY, ALGORITHM
from localsecrets import PADS_TEST_ID, PADS_TEST_PW, PADS_BASED_CLIENT_IDS

import timeit
import opasDocPermissions as opasDocPerm
import json

from main import app
client = TestClient(app)

class TestClientLogin(unittest.TestCase):

    def test_client_login_document_access(self):
        # Login to PaDS with test account and then check responses to mostCited for access.
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
            full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/IJP.077.0217A/')
            # local, this works...but fails in the response.py code trying to convert self.status to int.
            response = client.get(full_URL, headers={"client-session": f"{sessID}", "client-id": "2"})
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
