#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from unitTestConfig import base_api, base_plus_endpoint_encoded, headers

class TestDatabaseSearchFacets(unittest.TestCase):
    def test_1a_facet_art_sourcecode(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=art_sourcecode') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["art_sourcecode"])
        assert(response_info["fullCount"] >= 130000)
        assert(response_info["facetCounts"]["facet_fields"]["art_sourcecode"]["PAQ"] >= 16989)
        assert(response_info["facetCounts"]["facet_fields"]["art_sourcecode"]["IJP"] >= 11721)
        assert(response_info["facetCounts"]["facet_fields"]["art_sourcecode"]["RFP"] >= 8775)
        assert(response_info["facetCounts"]["facet_fields"]["art_sourcecode"]["PSYCHE"] >= 8521)
        assert(response_info["facetCounts"]["facet_fields"]["art_sourcecode"]["PSAR"] >= 6778)
        assert(response_info["facetCounts"]["facet_fields"]["art_sourcecode"]["APA"] >= 5453)
        assert(response_info["facetCounts"]["facet_fields"]["art_sourcecode"]["ZBK"] >= 4010)
        assert(response_info["facetCounts"]["facet_fields"]["art_sourcecode"]["JOAP"] >= 3994)
        assert(response_info["facetCounts"]["facet_fields"]["art_sourcecode"]["RPSA"] >= 3892)
        assert(response_info["facetCounts"]["facet_fields"]["art_sourcecode"]["REVAPA"] >= 3490)
        assert(response_info["facetCounts"]["facet_fields"]["art_sourcecode"]["AJP"] >= 3236)
        assert(response_info["facetCounts"]["facet_fields"]["art_sourcecode"]["PSU"] >= 2885)
        
    def test_1b_facet_art_kwds_multi(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=art_kwds_str, art_kwds, terms_highlighted') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["art_kwds_str"])
        print(response_info["facetCounts"]["facet_fields"]["art_kwds"])
        print(response_info["facetCounts"]["facet_fields"]["terms_highlighted"])
        assert(response_info["fullCount"] >= 135000)
        assert(response_info["facetCounts"]["facet_fields"]["art_kwds_str"]["psychoanalysis"] >= 30)

    def test_1b_facet_bib_title(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=bib_title&limit=60') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["bib_title"])
        assert(response_info["fullCount"] >= 135000)
        assert(response_info["facetCounts"]["facet_fields"]["bib_title"]["standard edition"] >= 7808)

    def test_1c_facet_art_lang(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=art_lang') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["art_lang"])
        assert(response_info["fullCount"] >= 135000)
        assert(response_info["facetCounts"]["facet_fields"]["art_lang"]["en"] >= 7808)
        

    def test_1c_facet_art_type(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=art_type') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["art_type"])
        assert(response_info["fullCount"] >= 135000)
        assert(response_info["facetCounts"]["facet_fields"]["art_type"]["REV"] >= 36556)

    def test_1c_facet_art_year(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=art_year') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["art_year"])
        assert(response_info["fullCount"] >= 135000)
        assert(response_info["facetCounts"]["facet_fields"]["art_year"]["2015"] >= 2598)

    def test_1c_facet_art_sourcetype_multi(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=art_sourcetype,art_type') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["art_sourcetype"])
        print(response_info["facetCounts"]["facet_fields"]["art_type"])
        assert(response_info["fullCount"] >= 135000)

    def test_1c_facet_art_authors(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=art_authors') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["art_authors"])
        assert(response_info["fullCount"] >= 135000)

    def test_1c_facet_glossary_terms(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=glossary_terms') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["glossary_terms"])
        assert(response_info["fullCount"] >= 135000)

    def test_1c_facet_glossary_group_terms(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=glossary_group_terms') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["glossary_group_terms"])
        assert(response_info["fullCount"] >= 135000)

    def test_1c_facet_freuds_italics(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=freuds_italics') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["freuds_italics"])
        assert(response_info["fullCount"] >= 135000)

    def test_1c_facet_reference_count(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=reference_count') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["reference_count"])
        assert(response_info["fullCount"] >= 135000)

    def test_1c_facet_bib_authors(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=bib_authors') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["bib_authors"])
        assert(response_info["fullCount"] >= 135000)

    def test_1c_facet_tagline(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=tagline') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["tagline"])
        assert(response_info["fullCount"] >= 135000)

    def test_1c_facet_title(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=title') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["title"])
        assert(response_info["fullCount"] >= 135000)

    def test_1c_facet_journals(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?facetfields=title') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print(response_info["facetCounts"]["facet_fields"]["title"])
        assert(response_info["fullCount"] >= 135000)

if __name__ == '__main__':
    unittest.main()
    