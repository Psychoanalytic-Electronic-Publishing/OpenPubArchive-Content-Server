#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant

import unittest
import requests

from unitTestConfig import base_api, base_plus_endpoint_encoded, headers

class TestSmartSearch(unittest.TestCase):
    def test_1a_boolean_word_search(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=love or hate')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        assert(response_info["fullCount"] >= 15)
        print (response_set)

    def test_1a_boolean_ignored_phrase_search(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext="love or hate"')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        assert(response_info["fullCount"] >= 15)
        print (response_set)

    def test_1a_boolean_word_search2(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=love and sex')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        count1 = response_info["fullCount"]
        print (f'Smarttext: {response_info["description"]}')
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=love and NOT sex')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        count2 = response_info["fullCount"]
        print (f'Smarttext: {response_info["description"]}')
        assert(count2 > count1)
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
    