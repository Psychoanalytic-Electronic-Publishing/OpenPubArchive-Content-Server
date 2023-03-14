#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestDatabaseSearchSpecialCases(unittest.TestCase):
    def test_2_example_fulltext1_search_types(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1="Eitingon Model"~25')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        print (response_info["fullCount"])
        assert(response_info["fullCount"] >= 143)

    def test_2a_example_fulltext1_search_types(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1="Eitingon Model"')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        print (response_info["fullCount"])
        assert(response_info["fullCount"] >= 95 and response_info["fullCount"] <= 155) # range just to give it some upper slack for new data

    def test_2b_example_fulltext1_search_types(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1="Eitingon and Model"~25')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        print (response_info["fullCount"])
        assert(response_info["fullCount"] >= 134 and response_info["fullCount"] <= 199) # range just to give it some upper slack for new data

    def test_2c_example_fulltext1_search_types(self):
        """
        """
        # this is interpreted as proximity search now (2021-04-01)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1="Eitingon or Model"~25')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        v1_count = response_info["fullCount"]
        print (f'v1 Count (fulltext1="Eitingon or Model"~25): {v1_count}')
        assert(response_info["fullCount"] >= 31 and response_info["fullCount"] <= 45) # range just to give it some upper slack for new data
        # this is interpreted as a phrase
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=body_xml:"Eitingon or Model"')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        v2_count = response_info["fullCount"]
        print (f'v2 Count (fulltext1="Eitingon or Model"): {v2_count}')
        # this should be a phrase as well
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext="Eitingon or Model"')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        v3_count = response_info["fullCount"]
        print (response_info["description"], f'v3 Count (smarttext=Eitingon or Model): {v3_count}')
        assert(v3_count == v2_count)


    def test_2d_example_fulltext1_search_types(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=Eitingon and -Model')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert response_info["fullCount"] >= 1724 and response_info["fullCount"] <= 2200, response_info["fullCount"] # range just to give it some upper slack for new data

    def test_2e_example_fulltext1_search_types(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1="Eitingon Model"~4')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        print (response_info["fullCount"])
        assert response_info["fullCount"] >= 130 and response_info["fullCount"] <= 165, f"Count: {response_info['fullCount']}" # just make sure there's a count


if __name__ == '__main__':
    unittest.main()
