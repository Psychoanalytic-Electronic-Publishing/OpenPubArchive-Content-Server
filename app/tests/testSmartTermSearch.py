#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant

# Third-party imports...
#from nose.tools import assert_true

import sys
import os.path

folder = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
if folder == "tests": # testing from within WingIDE, default folder is tests
    sys.path.append('../libs')
    sys.path.append('../config')
    sys.path.append('../../app')
else: # python running from should be within folder app
    sys.path.append('./libs')
    sys.path.append('./config')

import unittest
import requests
#from requests.utils import requote_uri
#import urllib

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
        assert(response_info["fullCount"] >= 15)
        print (response_set)

    def test_1a_boolean_word_search2(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=love and sex')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        count1 = response_info["fullCount"]
        reason = response_info["description"]
        print (reason)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=love and not sex')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        count2 = response_info["fullCount"]
        reason = response_info["description"]
        print (reason)
        assert(count2 < count1)
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
        print (response_info["fullCount"])
        assert(response_info["count"] >= 1)
        print (response_set[0])


if __name__ == '__main__':
    unittest.main()
    