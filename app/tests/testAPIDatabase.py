#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from unitTestConfig import base_api, base_plus_endpoint_encoded, headers

class TestDatabaseSearch(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_v2_database_search_fulltext(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?title=psychoanalysis&sourcecode=CPS&startyear=1990-1993&fulltext1="child%20abuse"&sort=citeCount&limit=10&offset=0')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] >= 1)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?title=psychoanalysis&sourcecode=CPS&startyear=1990&endyear=1995&fulltext1="child%20abuse"&sort=citeCount&limit=10&offset=0')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 3)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)

    def test_v2_database_search_author(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=freud&sourcecode=IJP&startyear=1990-1993&limit=10&offset=0')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 1)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=freud&limit=10&offset=0')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['count'] == 10)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == False)

    def test_v2_database_search_synonyms(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=BAP&fulltext1=text:bisexuality&sort=citeCount&limit=10&offset=0')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 14)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == False)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?synonyms=true&sourcecode=BAP&fulltext1=text:bisexuality&sort=citeCount&limit=10&offset=0')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 78)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == False)

    def test_v2_database_search_citedcount(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?citecount=6 TO 10 IN 10&sourcecode=IJP OR APA&startyear=1990&endyear=2010&fulltext1="theoretical underpinnings"&sort=citeCount&limit=10&offset=0')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] >= 3)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)

    def test_2_pubs_authornames(self):
        """
        Get Author Pubs For Matching Author Names
        /v1​/Authors​/Publications​/{authorNamePartial}​/
        """
        full_URL = base_plus_endpoint_encoded('/v2/Authors/Publications/maslow, a.*/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['authorPubList']['responseInfo']['fullCount']} Count complete: {r['authorPubList']['responseInfo']['fullCountComplete']}")
        assert(r['authorPubList']['responseInfo']['fullCount'] == 3)
        
        # Doesn't return an error, returns 0 matches.
        full_URL = base_plus_endpoint_encoded('/v2/Authors/Publications/Flintstone, Fred.*/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json() 
        print (f"Count: {r['authorPubList']['responseInfo']['fullCount']} Count complete: {r['authorPubList']['responseInfo']['fullCountComplete']}")
        assert(r['authorPubList']['responseInfo']['fullCount'] == 0)
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")