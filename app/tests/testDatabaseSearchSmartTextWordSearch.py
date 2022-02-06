#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class testDatabaseSearchSmartTextWordSearch(unittest.TestCase):
    def test_1a_phrase_search_with_wildcards(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext="Interpret* symbol"~25')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        full_count = response_info["fullCount"]
        assert(response_info["fullCount"] >= 1), full_count
        #print (response_set)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Interpret* symbol')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        full_count2 = response_info["fullCount"]
        assert(full_count == full_count2), (full_count, full_count2)
        # print (response_set)
    
    def test_1a_literal_search_with_wildcards(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext="Car? Gr?nt"~25')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        assert(response_info["fullCount"] >= 45)
        print (response_set)
    
    def test_1a_boolean_word_search(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=love AND hate AND (joy OR sorrow) ')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        assert(response_info["fullCount"] >= 1500)
        print (response_set)

    def test_1a_one_word_search(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=regretable') # misspelled, so only a few
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        assert(response_info["fullCount"] >= 5)
        print (response_set)

    def test_1a_one_word_search_wildcard(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=regre?table') # should take care of spelling error
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        assert(response_info["fullCount"] >= 5)
        print (response_set)

    def test_1a_one_word_search_with_wildcard(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=regretabl*') # misspelled, so only a few
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        assert(response_info["fullCount"] >= 12)
        print (response_set)

    def test_1a_boolean_ignored_phrase_search(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext="love OR hate"')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        assert(response_info["fullCount"] >= 15)
        print (response_set)

    def test_1a_boolean_word_search2(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=love AND sex')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        count1 = response_info["fullCount"]
        print (f'Smarttext: {response_info["description"]} Count: {count1}')
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=love AND NOT sex')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        count2 = response_info["fullCount"]
        print (f'Smarttext: {response_info["description"]} Count: {count2}')
        assert(count2 > count1)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=love AND NOT love')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        count2 = response_info["fullCount"]
        print (f'Smarttext: {response_info["description"]} Count: {count2}')
        assert(count2 == 0)
        print (response_set)

    def test_1b_3_word_search(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Psychoanalysis Treatment of headaches')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["fullCount"])
        assert(response_info["count"] >= 1)
        print (response_set[0])

    def test_2a_dts_example_searches(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Evenly Suspended Attention')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["fullCount"])
        assert(response_info["count"] >= 1)
        print (response_set[0])


if __name__ == '__main__':
    unittest.main()
    