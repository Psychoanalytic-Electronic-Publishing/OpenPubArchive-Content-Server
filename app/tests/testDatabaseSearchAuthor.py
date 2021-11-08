#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant

import unittest
import requests
import urllib.parse

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestDatabaseSearchAuthor(unittest.TestCase):
    def test_search_facets1_base(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=Ithier&facetquery=art_authors:"bournova, klio"')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] == 1)

    def test_search_facets1_quotes(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author="Béatrice Ithier"&facetquery=art_authors:"bournova, klio"')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] == 1)

    def test_search_facets1_parens(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author="Béatrice Ithier"&facetquery=art_authors:"bournova, klio"')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] == 1)

    def test_search_facets1_multi1(self):
        encodedarg = urllib.parse.quote_plus("David Tuckett")
        encodedarg2 = urllib.parse.quote_plus('art_sourcetitleabbr:("Int. J. Psychoanal." OR "Int. Rev. Psycho-Anal." OR "Brit. J. Psychother.") AND art_authors:("taffler, richard" OR "amati mehler, jacqueline")')
        full_URL = base_plus_endpoint_encoded(f"/v2/Database/Search/?author={encodedarg}&facetquery={encodedarg2}")
        print (f"Full URL: {full_URL}")
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] == 2)

    def test_search_facets1_multi2(self):
        encodedarg = urllib.parse.quote_plus("David Tuckett OR Peter Fonagy")
        encodedarg2 = urllib.parse.quote_plus('art_sourcetitleabbr:("Int. J. Psychoanal." OR "Int. Rev. Psycho-Anal." OR "Brit. J. Psychother.") AND art_authors:("taffler, richard" OR "amati mehler, jacqueline")')
        full_URL = base_plus_endpoint_encoded(f"/v2/Database/Search/?author={encodedarg}&facetquery={encodedarg2}")
        print (f"Full URL: {full_URL}")
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] == 2)

    def test_search_facets1_fullnames(self):
        encodedarg = urllib.parse.quote_plus("((Ithier, Béatrice) && (bournova, klio))")
        full_URL = base_plus_endpoint_encoded(f'/v2/Database/Search/?author={encodedarg}')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] == 1)

    def test_search_facets1_initialed(self):
        encodedarg = urllib.parse.quote_plus('"Ithier, B."')
        full_URL = base_plus_endpoint_encoded(f'/v2/Database/Search/?author={encodedarg}')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] >= 22)

        encodedarg = urllib.parse.quote_plus('(Ithier, B.)')
        full_URL = base_plus_endpoint_encoded(f'/v2/Database/Search/?author={encodedarg}')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] >= 22)

        encodedarg = urllib.parse.quote_plus('("Ithier, B.")')
        full_URL = base_plus_endpoint_encoded(f'/v2/Database/Search/?author={encodedarg}')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] >= 22)

    def test_search_facets2a(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=cooper AND cooper, steven h. OR cooper, steven')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] > 60 and response_info["fullCount"] < 80)
  
    def test_search_facets2b(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=(cooper AND cooper, steven h. OR (cooper, steven))')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] > 60 and response_info["fullCount"] < 80)

    def test_search_author_forward(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author="Moshe Spero"')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        assert(response.ok == True)
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] >= 1)
        print (response_set[0])

    def test_search_author_forward_order_with_quotes(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author="Moshe Spero"')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        assert(response.ok == True)
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] >= 1)
        print (response_set[0])

    def test_search_author_citation_order(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=Spero, Moshe')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        assert(response.ok == True)
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] >= 1)
        print (response_set[0])


    def test_search_author_citation_order_inits(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=Spero, M. H.')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        assert(response.ok == True)
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] >= 1)
        print (response_set[0])

    def test_search_author_citation_order_inits_wildcard(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author="Spero, M.*"')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        assert(response.ok == True)
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] >= 1)
        print (response_set[0])

    def test_1a_search_mixedcase(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=Greenfield')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] >= 6)
        #print (response_set)
        for n in response_set:
            print (n["documentRef"])
        # Confirm that the request-response cycle completed successfully.

    def test_1b_search_lowercase(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=greenfield')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] >= 6)
        print (response_set[0])
        # Confirm that the request-response cycle completed successfully.

    def test_1c_search_wildcard(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=gre?nfield')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] >= 7)
        # print (response_set)
        # Confirm that the request-response cycle completed successfully.

    def test_search_journalcode(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=Bollas&sourcecode=AOP')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] == 2)
        print (response_set[0])

if __name__ == '__main__':
    unittest.main()
    