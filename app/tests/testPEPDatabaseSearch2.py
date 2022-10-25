#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant

import unittest
import requests
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, get_headers_not_logged_in

# Get session, but not logged in.
headers = get_headers_not_logged_in()

class Test_PEPOnly_DatabaseSearch(unittest.TestCase):
    def test_database_search_volume_issue_fields(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=IJP&volume=(034S)&limit=10&offset=0')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 5)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)

        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=IJP&volume=34S&limit=10&offset=0')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 5)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)

        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=IJP&volume=034&issue=S&limit=10&offset=0')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 5)
        assert(r['documentList']['responseSet'][0]['issue'] == 'Supplement')
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)

        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=FA&volume=001C&limit=10&offset=0')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 6)
        assert(r['documentList']['responseSet'][0]['issue'] == '3')

        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=FA&volume=001&issue=C&limit=10&offset=0')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 6)
        assert(r['documentList']['responseSet'][0]['issue'] == '3')


if __name__ == '__main__':
    unittest.main()
