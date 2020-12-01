#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers

class TestSearch(unittest.TestCase):
    def test_search_viewed_count_1a(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewcount=2&sourcecode=IJP')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] >= 0) # just make sure there's a count
        print (response_set)

    def test_search_viewed_count_1b(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewcount=1')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] >= 0) # just make sure there's a count
        print (response_set)

    def test_search_viewed_count_1c(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewcount=1&fulltext1=feel')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        #"Watching to see how long a query can be here, since the mysql part generates a list of ids OR'd together"
        qlen = len(r["documentList"]["responseInfo"]["scopeQuery"][0][1])
        print (f"MySQL QueryLen: {qlen}")
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] >= 0) # just make sure there's a count
        print (response_set)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewcount=3&fulltext1=feel')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] >= 0) # just make sure there's a count
        print (response_set)

    def test_search_author_and_journalcode_and_text_and_citecount(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=tuckett&citecount=3')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] >= 0) # just make sure there's a count
        print (response_set)
        
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
        assert(response_info["fullCount"] >= 95 and response_info["fullCount"] <= 115) # range just to give it some upper slack for new data

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
        assert(response_info["fullCount"] >= 475 and response_info["fullCount"] <= 525) # range just to give it some upper slack for new data

    def test_2c_example_fulltext1_search_types(self):
        """
        """
        # this is interpreted as an OR boolean
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1="Eitingon or Model"~25')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        v1_count = response_info["fullCount"]
        print (f'v1 Count (fulltext1="Eitingon or Model"~25): {v1_count}')
        assert(response_info["fullCount"] >= 31379 and response_info["fullCount"] <= 34000) # range just to give it some upper slack for new data
        # this is interpreted as a phrase
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=body:"Eitingon or Model"')
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
        print (response_info["description"], f'v3 Count (smarttext="Eitingon or Model"): {v3_count}')
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
        print (response_info["fullCount"])
        assert(response_info["fullCount"] >= 1724 and response_info["fullCount"] <= 2200) # range just to give it some upper slack for new data

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
        assert(response_info["fullCount"] >= 114 and response_info["fullCount"] <= 144)        

if __name__ == '__main__':
    unittest.main()
