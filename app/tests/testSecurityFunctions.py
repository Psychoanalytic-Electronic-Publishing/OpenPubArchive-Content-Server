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
import timeit

import opasDocPermissions
from unitTestConfig import base_api, base_plus_endpoint_encoded
from localsecrets import PADS_TEST_ID, PADS_TEST_PW

# Login!
resp = opasDocPermissions.pads_login(username=PADS_TEST_ID, password=PADS_TEST_PW)
# Confirm that the request-response cycle completed successfully.
sessID = resp.SessionId
headers = {f"client-session":f"{sessID}",
           "client-id": "0"
           }

class TestSecurityFunctions(unittest.TestCase):

    def test_0a_pads_tests(self):
        # Login to PaDS with test account and then check responses to mostCited for access.
        if sessID is None:
            logger.error(f"PaDS Login error in test: {response}")
            assert(False)
        else:
            full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?limit=99')
            response = requests.get(full_URL, headers={"client-session":sessID, "client-id": "2", "Content-Type":"application/json"})
            # Confirm that the request-response cycle completed successfully.
            r = response.json()
            print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
            # PaDS ID provided has peparchive!
            assert(r['documentList']['responseSet'][0].get("accessLimited", None) == False)

    def test_1a_timing_Pads(self):
        if sessID is None:
            logger.error(f"PaDS Login error in test: {response}")
            assert(False)
        else:
            headers = '"client-session":"%s", "client-id": "2"' % sessID
            test = 'response = requests.get(full_URL, headers={%s})' % headers
            setup = "import requests; from unitTestConfig import base_plus_endpoint_encoded; full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?limit=99')"
            timing = timeit.timeit(test, setup, number=1)
            print (f"timing return 99 documents: {timing}")
            assert(timing < 7.5)
            setup = "import requests; from unitTestConfig import base_plus_endpoint_encoded; full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?limit=101')"
            timing = timeit.timeit(test, setup, number=1)
            print (f"timing return 101 documents (no pads): {timing}")
            assert(timing < 7.5)            
            
    def test_1b_get_search(self):
        if sessID is None:
            logger.error(f"PaDS Login error in test: {response}")
            assert(False)
        else:
            headers = '"client-session":"%s", "client-id": "2"' % sessID
            test = 'response = requests.get(full_URL, headers={%s})' % headers
            setup = "import requests; from unitTestConfig import base_plus_endpoint_encoded; full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Freud&limit=99')"
            timing = timeit.timeit(test, setup, number=1)
            print (f"timing return 99 documents: {timing}")
            assert(timing < 19)
            setup = "import requests; from unitTestConfig import base_plus_endpoint_encoded; full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Freud&limit=101')"
            timing = timeit.timeit(test, setup, number=1)
            print (f"timing return 101 documents (no pads): {timing}")
            assert(timing < 19)            

if __name__ == '__main__':
    unittest.main()
