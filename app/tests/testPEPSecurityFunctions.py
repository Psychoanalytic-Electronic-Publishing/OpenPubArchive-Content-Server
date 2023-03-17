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
