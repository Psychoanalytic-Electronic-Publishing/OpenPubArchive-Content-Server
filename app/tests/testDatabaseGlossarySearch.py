#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant

import logging
logger = logging.getLogger(__name__)

import unittest
import requests

from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID

class TestDatabaseGlossarySearch(unittest.TestCase):

    def test_0_glossary_search(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Glossary/Search/?fulltext1="freudian slip"')
        # Confirm that the request-response cycle completed successfully.
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 1)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)

        full_URL = base_plus_endpoint_encoded('/v2/Database/Glossary/Search/?fulltext1=unconcious')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 1)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)
               
if __name__ == '__main__':
    unittest.main()
