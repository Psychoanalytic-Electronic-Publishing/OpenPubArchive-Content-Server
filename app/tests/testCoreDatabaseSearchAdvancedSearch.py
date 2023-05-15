#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestDatabaseSearchAdvancedSearch(unittest.TestCase):
    def test_10_schema_fields(self):
        """
        Use equivalent field names in field search per schemaMap USERVARIATION2SOLR_MAP
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=FA&smarttext=type:(ART OR COM)')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["fullCount"])
        assert(response_info["fullCount"] >= 2)
        # print (response_set[0])

        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=PEPGRANTVS&smarttext=type:VID')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["fullCount"])
        assert(response_info["fullCount"] >= 2)
        print (response_set[0])

        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=author:Kahr')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["fullCount"])
        assert(response_info["fullCount"] >= 1)
        print (response_set[0])

if __name__ == '__main__':
    unittest.main()
    