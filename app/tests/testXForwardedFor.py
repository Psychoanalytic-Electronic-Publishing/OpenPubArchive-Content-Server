#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests
import logging
import localsecrets

logger = logging.getLogger(__name__)

import opasConfig

no_session = True
import unitTestConfig
from unitTestConfig import base_plus_endpoint_encoded, headers, UNIT_TEST_CLIENT_ID

class TestXForwardedFor(unittest.TestCase):
    """
    Test passing through of X-Forwarded-For
    """   
    def test_1_get_document(self):
        # sessID, headers, session_info = unitTestConfig.test_login()
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/PCT.011.0171A/')
        # this has to be a group account and an IP that's allowed in a group acct.
        headers[opasConfig.X_FORWARDED_FOR] = localsecrets.MYIP
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        # this document should be available
        assert(response_set[0]["accessLimited"] == False)
        print (response_set)

       
if __name__ == '__main__':
    unittest.main()    