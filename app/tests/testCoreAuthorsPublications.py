#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Updates:
#  2022-10-25 - Set to use only sample data

import unittest
import requests
from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestAuthorsPublications(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.

    2022-10-25 These tests only require the Opas sample data to be loaded    
    """   

    def test_2_pubs_authornames(self):
        """
        Get Author Pubs For Matching Author Names
        /v1​/Authors​/Publications​/{authorNamePartial}​/
        """
        full_URL = base_plus_endpoint_encoded('/v2/Authors/Publications/heath, a. chris/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['authorPubList']['responseInfo']['fullCount']} Count complete: {r['authorPubList']['responseInfo']['fullCountComplete']}")
        assert(r['authorPubList']['responseInfo']['fullCount'] >= 3)
        
        # Doesn't return an error, returns 0 matches.
        full_URL = base_plus_endpoint_encoded('/v2/Authors/Publications/Flintstone, Fred.*/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json() 
        print (f"Count: {r['authorPubList']['responseInfo']['fullCount']} Count complete: {r['authorPubList']['responseInfo']['fullCountComplete']}")
        assert(r['authorPubList']['responseInfo']['fullCount'] == 0)
    
    def test_publications_authornames(self):
        """
        Get Author Pubs For Matching Author Names
        /v1​/Authors​/Publications​/{authorNamePartial}​/
        """
        # try a regex wildcard search (regex wildcards permitted anywhere EXCEPT the end of the name, since that's done automatically)
        full_URL = base_plus_endpoint_encoded('/v2/Authors/Publications/he[af].*h/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        assert(r['authorPubList']['responseInfo']['fullCount'] >= 2)
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")