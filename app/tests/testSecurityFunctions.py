#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

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

import unittest
import requests
# from requests.utils import requote_uri
# import urllib

from unitTestConfig import base_api, base_plus_endpoint_encoded
from localsecrets import TESTUSER, TESTPW, SECRET_KEY, ALGORITHM
import timeit
# import opasDocPermissions as opasDocPerm

class TestSecurityFunctions(unittest.TestCase):

    def test_0a_pads_tests(self):
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
        

    def test_1a_get_term_index_timing_Pads(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={TESTUSER}&password={TESTPW}')
        response = requests.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_1b_get_term_index_timing_noPads(self):
        #full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={TESTUSER}&password={TESTPW}')
        #response = requests.get(full_URL)
        ## Confirm that the request-response cycle completed successfully.
        #assert(response.ok == True)
        test = 'response = requests.get(full_URL)'
        setup = "import requests; from unitTestConfig import base_plus_endpoint_encoded; full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?limit=99')"
        timing = timeit.timeit(test, setup, number=1)
        print (f"timing return 99 documents: {timing}")
        assert(timing < 7)
        test = 'response = requests.get(full_URL)'
        setup = "import requests; from unitTestConfig import base_plus_endpoint_encoded; full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?limit=101')"
        timing = timeit.timeit(test, setup, number=1)
        print (f"timing return 101 documents (no pads): {timing}")
        assert(timing < 7)



if __name__ == '__main__':
    unittest.main()
