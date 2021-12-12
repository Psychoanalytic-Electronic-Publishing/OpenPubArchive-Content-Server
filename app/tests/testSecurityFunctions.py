#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests
import timeit
import logging
logger = logging.getLogger(__name__)

import opasDocPermissions
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, test_login
from localsecrets import PADS_TEST_ID, PADS_TEST_PW

# Login!
session_id, headers, session_info = test_login()

class TestSecurityFunctions(unittest.TestCase):

    def test_0a_pads_tests(self):
        # Login to PaDS with test account and then check responses to mostCited for access.
        if session_id is None:
            logger.error(f"PaDS Login error in test")
            assert(False)
        else:
            full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?limit=10')
            response = requests.get(full_URL, headers=headers)
            # Confirm that the request-response cycle completed successfully.
            r = response.json()
            print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
            # PaDS ID provided has peparchive!
            # 20211008 Access to items in result list is no longer checked...only when one item is returned.
            assert(r['documentList']['responseSet'][0].get("accessChecked", None) == False)
            #assert(r['documentList']['responseSet'][0].get("accessLimited", None) == True)

    def test_1a_timing_Pads(self):
        if session_id is None:
            logger.error(f"PaDS Login error in test")
            assert(False)
        else:
            headers = '"client-session":"%s", "client-id": "4"' % session_id
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
        if session_id is None:
            logger.error(f"PaDS Login error in test")
            assert(False)
        else:
            headers = '"client-session":"%s", "client-id": "4"' % session_id
            test = 'response = requests.get(full_URL, headers={%s})' % headers
            setup = "import requests; from unitTestConfig import base_plus_endpoint_encoded; full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Freud&limit=99')"
            timing = timeit.timeit(test, setup, number=1)
            print (f"timing return 99 documents: {timing}")
            assert(timing < 19)
            
            setup = "import requests; from unitTestConfig import base_plus_endpoint_encoded; full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Freud&limit=101')"
            timing = timeit.timeit(test, setup, number=1)
            print (f"timing return 101 documents (no pads): {timing}")
            assert(timing < 19)            

    def test_1c_get_search_logged_out(self): 
        global session_id
        opasDocPermissions.authserver_logout(session_id)
        headers = '"client-id": "4"' #  no session id
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
