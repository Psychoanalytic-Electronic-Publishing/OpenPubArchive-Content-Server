#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestDatabaseOpenURL(unittest.TestCase):
    def test_search_issn(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?issn=2472-6982')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_set[0]["issn"] == '2472-6982')

    def test_search_eissn(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?eissn=2472-6982')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_set[0]["issn"] == '2472-6982')

    def test_search_title(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?title=*family*')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)

    def test_search_stitle(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?stitle="Couple and Family*"')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        print (response_set[0]["PEPCode"])
        assert(response_info["count"] >= 1)

    # atitle: str=Query(None, title=opasConfig.TITLE_TITLE, description=opasConfig.DESCRIPTION_TITLE),
    
    def test_search_aufirst(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?aufirst=A. Chris')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 2)
        assert('Chris' in response_set[0]["authorMast"])

    def test_search_aulast(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?aulast=Heath')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        print (response_set[0]["authorMast"])
        assert(response_set[0]["authorMast"][0:14] == 'A. Chris Heath')

    def test_search_volume(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?volume=1')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)
        assert(response_set[0]["vol"] == '1')

    def test_search_issue(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?issue=1')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 3)
        assert(response_set[0]["issue"] == '1')

    def test_search_spage(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?spage=1')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)

    def test_search_epage(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?epage=168')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)
        assert(response_set[0]["pgEnd"] == '168')

    def test_search_pages(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?pages=3')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)
        assert(response_set[0]["pgStart"] == '3')

        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?pages=158-168')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_set[0]["pgStart"] == '158')
        assert(response_set[0]["pgEnd"] == '168')

        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?pages=158-')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_set[0]["pgStart"] == '158')

        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?pages=-168')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)
        assert(response_set[0]["pgEnd"] == '168')

    def test_search_date(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?date=2021')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)

    def test_search_artnum(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?artnum=BAP.013.*')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)
        assert(response_set[0]["PEPCode"] == 'BAP')
        assert(response_set[0]["vol"] == '013')

    def test_search_artnum(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?artnum=PEPGRANTVS.001.*&sort=author')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)
        assert(response_set[0]["PEPCode"] == 'PEPGRANTVS')

    def test_search_date_sort_offset(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?date=2015&sort=author&limit=2&offset=2')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)

    def test_search_isbn(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/OpenURL/?isbn=0674154231')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        assert(response_info["count"] >= 1)


if __name__ == '__main__':
    unittest.main()
    