#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers

class TestSearchOpenURL(unittest.TestCase):
    
    
    def test_search_issn(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?issn=1018-2756')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_set[0]["issn"] == '1018-2756')

    def test_search_eissn(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?eissn=1018-2756')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_set[0]["issn"] == '1018-2756')

    def test_search_isbn(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?isbn=0422725501')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)

    def test_search_title(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?title=*ego*')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)

    def test_search_stitle(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?stitle=International Journal*')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)
        assert(response_set[0]["PEPCode"] == 'IJP')

    # atitle: str=Query(None, title=opasConfig.TITLE_TITLE, description=opasConfig.DESCRIPTION_TITLE),
    
    def test_search_aufirst(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?aufirst=David')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 100)
        assert(response_set[0]["authorMast"][0:5] == 'David')

    def test_search_aulast(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?aulast=Tuckett')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_set[0]["authorMast"] == 'David Tuckett')

    def test_search_volume(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?volume=101')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)
        assert(response_set[0]["vol"] == '101')

    def test_search_issue(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?issue=4')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)
        assert(response_set[0]["issue"] == '4')

    def test_search_spage(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?spage=5')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)

    def test_search_epage(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?epage=49')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)
        assert(response_set[0]["pgEnd"] == '49')

    def test_search_pages(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?pages=31')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)
        assert(response_set[0]["pgStart"] == '31')

        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?pages=22-49')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_set[0]["pgStart"] == '22')
        assert(response_set[0]["pgEnd"] == '49')

        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?pages=79-')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_set[0]["pgStart"] == '79')

        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?pages=-49')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)
        assert(response_set[0]["pgEnd"] == '49')

    def test_search_date(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?date=2021')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)

    def test_search_artnum(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?artnum=IJP.100.*')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)
        assert(response_set[0]["PEPCode"] == 'IJP')
        assert(response_set[0]["vol"] == '100')

    def test_search_artnum(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?artnum=PB.010.*&sort=author')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)
        assert(response_set[0]["PEPCode"] == 'PB')

    def test_search_date_sort_offset(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?date=1999&sort=author&limit=2&offset=2')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)


if __name__ == '__main__':
    unittest.main()
    