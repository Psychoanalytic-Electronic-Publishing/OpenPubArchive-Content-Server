#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger()

import unittest
import requests
import localsecrets
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, test_login

# Login!
sessID, headers, session_info = test_login(username=localsecrets.PADS_TEST_ID2, password=localsecrets.PADS_TEST_PW2)

class TestAdminLogLevel(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
          
    The logger tests won't work because the loglevel in the server doesn't
    seem to affect the test client logging.
    """   

    #TODO: Later these will need to be done while logged in.
    
    def test00_loglevel_warning(self):
        full_URL = base_plus_endpoint_encoded('/v2/Admin/LogLevel/?level=WARN')
        response = requests.put(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        assert ("WARNING" in r) # WARNING

    def test01_loglevel_error(self):
        full_URL = base_plus_endpoint_encoded('/v2/Admin/LogLevel/?level=ERROR')
        response = requests.put(full_URL, headers=headers)
        assert(response.ok == True)      
        r = response.json()
        assert ("ERROR" in r)

    def test02_loglevel_debug(self):
        full_URL = base_plus_endpoint_encoded('/v2/Admin/LogLevel/?level=DEBUG')
        response = requests.put(full_URL, headers=headers)
        assert(response.ok == True)      
        r = response.json()
        assert ("DEBUG" in r)
        # set client log level now!

    # last test--leave it on info
    def test03_loglevel_info(self):
        full_URL = base_plus_endpoint_encoded('/v2/Admin/LogLevel/?level=INFO')
        response = requests.put(full_URL, headers=headers)
        assert(response.ok == True)      
        r = response.json()
        assert ("INFO" in r) 
        

if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")