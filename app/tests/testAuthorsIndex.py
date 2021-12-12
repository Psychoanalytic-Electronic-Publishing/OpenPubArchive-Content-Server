#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests
from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestAuthorsIndex(unittest.TestCase):
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
        assert(r['authorIndex']['responseSet'][0]['publicationsURL'][0:33] == '/v2/Authors/Publications/tuckett,')
       
        full_URL = base_plus_endpoint_encoded('/v2/Authors/Index/Maslo/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        assert(r['authorIndex']['responseSet'][0]['publicationsURL'] == '/v2/Authors/Publications/maslow, a. h./')

        
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")