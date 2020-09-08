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

from unitTestConfig import base_api, base_plus_endpoint_encoded
from localsecrets import TESTUSER, TESTPW, SECRET_KEY, ALGORITHM
from localsecrets import PADS_TEST_ID, PADS_TEST_PW, PADS_BASED_CLIENT_IDS

import timeit
import opasDocPermissions as opasDocPerm
import json

class TestSecurityFunctions(unittest.TestCase):

    def test_0a_pads_tests(self):
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
            full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?limit=99')
            response = requests.get(full_URL, headers={"client-session":sessID, "client-id": "2", "Content-Type":"application/json"})
            # Confirm that the request-response cycle completed successfully.
            r = response.json()
            print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
            # PaDS ID provided has peparchive!
            assert(r['documentList']['responseSet'][0].get("accessLimited", None) == False)

    def test_0b_no_pads_tests(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={TESTUSER}&password={TESTPW}')
        response = requests.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?limit=25')
        response = requests.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseSet'][0].get("accessLimited", None) == True)
        

    def test_1a_timing_Pads(self):
        #full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={TESTUSER}&password={TESTPW}')
        #response = requests.get(full_URL)
        ## Confirm that the request-response cycle completed successfully.
        #assert(response.ok == True)
        response = opasDocPerm.pads_login()
        ## Confirm that the request-response cycle completed successfully.
        sessID = response.get("SessionId", None)
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
            
    def test_1b_get_term_index_timing_noPads(self):
            test = 'response = requests.get(full_URL)'
            setup = "import requests; from unitTestConfig import base_plus_endpoint_encoded; full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?limit=99')"
            timing = timeit.timeit(test, setup, number=1)
            print (f"timing return 99 documents: {timing}")
            assert(timing < 7)
            setup = "import requests; from unitTestConfig import base_plus_endpoint_encoded; full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?limit=101')"
            timing = timeit.timeit(test, setup, number=1)
            print (f"timing return 101 documents (no pads): {timing}")
            assert(timing < 7)            

        ##full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={TESTUSER}&password={TESTPW}')
        ##response = requests.get(full_URL)
        ### Confirm that the request-response cycle completed successfully.
        ##assert(response.ok == True)
        #test = 'response = requests.get(full_URL)'
        #setup = "import requests; from unitTestConfig import base_plus_endpoint_encoded; full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?limit=99')"
        #timing = timeit.timeit(test, setup, number=1)
        #print (f"timing return 99 documents: {timing}")
        #assert(timing < 7)
        #test = 'response = requests.get(full_URL)'
        #setup = "import requests; from unitTestConfig import base_plus_endpoint_encoded; full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?limit=101')"
        #timing = timeit.timeit(test, setup, number=1)
        #print (f"timing return 101 documents (no pads): {timing}")
        #assert(timing < 7)



if __name__ == '__main__':
    unittest.main()
