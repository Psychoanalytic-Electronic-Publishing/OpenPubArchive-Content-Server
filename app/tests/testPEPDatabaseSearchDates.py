#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestDatabaseSearchDates(unittest.TestCase):
    def test_3a_search_year(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?startyear=1932') # in 1932
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print(response_info["fullCount"])
        assert(response_info["fullCount"] >= 687)
        
    def test_3b_search_year(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?startyear=1932-1933')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print(response_info["fullCount"])
        assert(response_info["fullCount"] >= 1454)

    def test_3c_search_year(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?startyear=<1908')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print(response_info["fullCount"])
        assert(response_info["fullCount"] >= 799)
        
    def test_3c2_search_year(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?startyear*&endyear=1908')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print(response_info["fullCount"])
        assert(response_info["fullCount"] >= 966)

    def test_3d_search_year(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?startyear=>2019')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print(response_info["fullCount"])
        assert(response_info["fullCount"] >= 750)

    def test_3d2_search_year(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?startyear=2019&endyear=*')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print(response_info["fullCount"])
        assert(response_info["fullCount"] >= 2311)

    def test_4a_search_year(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?startyear=1908&endyear=1909')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print(response_info["fullCount"])
        assert(response_info["fullCount"] >= 386)
        
    def test_4b_search_year(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?startyear=*&endyear=1944')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print(response_info["fullCount"])
        assert(response_info["fullCount"] >= 19598)
        
    def test_4c_search_year(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?endyear=1909')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print(response_info["fullCount"])
        assert(response_info["fullCount"] >= 1185)
        
    def test_4d_search_year(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?startyear=1932&endyear=1944')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print(response_info["fullCount"])
        assert(response_info["fullCount"] >= 7337)

    def test_4d_search_bad_year(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?startyear=19')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print(response_info["fullCount"])
        assert(response_info["fullCount"] >= 7337)

if __name__ == '__main__':
    unittest.main()
    