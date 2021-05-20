#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers

class TestSorts(unittest.TestCase):
    def test_sort_sourcecode(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=OPUS&sort=vol desc')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_set[0]["vol"] == '9')
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=OPUS&sort=vol asc')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_set[0]["vol"] == '1')

    def test_sort_doctype(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=OPUS&sort=doctype desc')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_set[0]["docType"] == 'SUP')
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=OPUS&sort=doctype asc')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_set[0]["docType"] == 'ART')

    def test_sort_doctype(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=OPUS&sort=art_figcount desc')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_set[0]["stat"]["art_fig_count"] >= 1)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=OPUS&sort=art_figcount asc')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_set[0]["stat"]["art_fig_count"] == 0)

    def test_sort_wordcount(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=erection&sort=words desc')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_set[0]["stat"]["art_words_count"] >= 20000)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=erection&sort=words asc')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_set[0]["stat"]["art_words_count"] <= 10000)



if __name__ == '__main__':
    unittest.main()
    