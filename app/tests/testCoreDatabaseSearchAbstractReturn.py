#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestDatabaseSearchAbstractReturn(unittest.TestCase):
    def test_01_search_abstract_on(self):
        # Send a request to the API server and store the response.
        # ### OR #####
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=transformation&abstract=true')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        abstr = response_set[0].get("abstract", None)
        assert(abstr is not None)

    def test_01_search_abstract_on_xml(self):
        # Send a request to the API server and store the response.
        # ### OR #####
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=transformation&abstract=true&formatrequested=XML')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        abstr = response_set[0].get("abstract", None)
        assert("pepkbd3" in abstr)

    def test_01_search_abstract_off(self):
        # Send a request to the API server and store the response.
        # ### OR #####
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=transformation&abstract=false')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        abstr = response_set[0].get("abstract", None)
        assert(abstr is None)

    def test_01_search_abstract_default_off(self):
        # Send a request to the API server and store the response.
        # ### OR #####
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=transformation')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        abstr = response_set[0].get("abstract", None)
        assert(abstr is None)
        

if __name__ == '__main__':
    unittest.main()
    