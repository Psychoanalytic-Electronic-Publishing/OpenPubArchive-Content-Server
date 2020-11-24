#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests
from unitTestConfig import base_plus_endpoint_encoded, headers

class TestAPIAuthors(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    """   

    def test_index_authornamepartial(self):
        """
        Get Author Index For Matching Author Names
        /v1/Authors/Index/{authorNamePartial}/
        """
        full_URL = base_plus_endpoint_encoded('/v2/Authors/Index/Tuckett/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        assert(r['authorIndex']['responseSet'][0]['publicationsURL'][0:33] == '/v1/Authors/Publications/tuckett,')
       
        full_URL = base_plus_endpoint_encoded('/v2/Authors/Index/Maslo/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        assert(r['authorIndex']['responseSet'][0]['publicationsURL'] == '/v1/Authors/Publications/maslow, a. h./')

    def test_publications_authornames(self):
        """
        Get Author Pubs For Matching Author Names
        /v1​/Authors​/Publications​/{authorNamePartial}​/
        """
        full_URL = base_plus_endpoint_encoded('/v2/Authors/Publications/maslow, a.*/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        assert(r['authorPubList']['responseInfo']['fullCount'] == 3)
        
        # Doesn't return an error, returns 0 matches.
        full_URL = base_plus_endpoint_encoded('/v2/Authors/Publications/Flintstone, Fred.*/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json() 
        assert(r['authorPubList']['responseInfo']['fullCount'] == 0)
        
        # try a regex wildcard search (regex wildcards permitted anywhere EXCEPT the end of the name, since that's done automatically)
        full_URL = base_plus_endpoint_encoded('/v2/Authors/Publications/tu[ckl].*tt/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        assert(r['authorPubList']['responseInfo']['fullCount'] >= 60)
        
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")