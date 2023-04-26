#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestDatabaseSearchSpecialCases(unittest.TestCase):
    def test_search_viewed_count_1a(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewcount=2&sourcecode=IJP')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] >= 0) # just make sure there's a count
        #print (response_set)

    def test_search_viewed_count_1b(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewcount=1')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] >= 0) # just make sure there's a count
        #print (response_set)

    def test_search_viewed_count_1c(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewcount=1&fulltext1=feel')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        #"Watching to see how long a query can be here, since the mysql part generates a list of ids OR'd together"
        qlen = len(r["documentList"]["responseInfo"]["scopeQuery"][0]["filterQ"])
        print (f"MySQL QueryLen: {qlen}")
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] >= 0) # just make sure there's a count
        #print (response_set)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewcount=3&fulltext1=feel')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] >= 0) # just make sure there's a count
        #print (response_set)

    def test_search_viewed_count_3_ranges(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewcount=2 TO 10&sourcecode=IJP')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert response_info["count"] >= 0, f"Count: {response_info['count']}" # just make sure there's a count
        #print (response_set)

    def test_search_viewed_count_3b_ranges(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewcount=5 TO 30&pubperiod=100')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert response_info["count"] >= 1,  f"Count: {response_info['count']}"
        #print (response_set)

    def test_search_viewed_count_3c_ranges_last6months(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewcount=5 TO 30 IN last6months&pubperiod=100')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert response_info["count"] >= 1, f"Count: {response_info['count']}" # just make sure there's a count
        #print (response_set)

    def test_search_viewed_count_3d_ranges_lastmonth(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewcount=2 TO 30 IN lastmonth')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert response_info["count"] >= 1, f"Count: {response_info['count']}" # just make sure there's a count
        #print (response_set)

    def test_search_viewed_count_3e_ranges_lastcalendaryear(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewcount=1 TO 30 IN lastcalendaryear')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert response_info["count"] >= 0, f"Count: {response_info['count']}" # just make sure there's a count
        #print (response_set)

    def test_search_viewed_count_3f_ranges_with_viewperiod(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewcount=5 TO 30&viewperiod=4')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert response_info["count"] >= 1, f"Count: {response_info['count']}" # just make sure there's a count
        #print (response_set)


if __name__ == '__main__':
    unittest.main()
