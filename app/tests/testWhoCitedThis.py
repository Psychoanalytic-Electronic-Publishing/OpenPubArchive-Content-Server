#!/usr/bin/env python
# -*- coding: utf-8 -*-

from localsecrets import PADS_TEST_ID, PADS_TEST_PW

import unittest
import requests
import opasConfig

from unitTestConfig import base_plus_endpoint_encoded, headers

class TestWhoCitedThis(unittest.TestCase):
    """
    Tests for WhoCitedThis endpoint
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_search_who_cited_this_1a(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/WhoCitedThis/?citedid=AOP.016.0171A')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] == 2)

    def test_search_who_cited_this_1b(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/WhoCitedThis/?citedid=IJP.078.1071A')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] >= 15)

    def test_search_who_cited_this_1c(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/WhoCitedThis/?citedid=IJP.078.1071A&pubperiod=3')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] >= 8)


    def test_search_who_cited_this_1d(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/WhoCitedThis/?citedid=IJP.078.1071A&pubperiod=2')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f"Count: {response_info['count']}")
        assert(response_info["count"] >= 3)


if __name__ == '__main__':
    unittest.main()    