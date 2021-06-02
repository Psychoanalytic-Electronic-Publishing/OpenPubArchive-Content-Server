#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant

import re
import logging
import opasAPISupportLib
logger = logging.getLogger(__name__)

import unittest
import requests

import opasDocPermissions
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, test_login

# Login!
sessID, headers, session_info = test_login()

class TestAdvancedSearch(unittest.TestCase):
    
    def test_search_fulltext1(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/AdvancedSearch/?advanced_query=art_type:(SUP OR TOC)')
        response = requests.post(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)
        print (response_set[0])


if __name__ == '__main__':
    unittest.main()
    