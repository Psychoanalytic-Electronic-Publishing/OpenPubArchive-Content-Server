#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger()

import unittest
import requests
from unitTestConfig import base_plus_endpoint_encoded, headers

class TestAdmin(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
          
    The logger tests won't work because the loglevel in the server doesn't
    seem to affect the test client logging.
    """   

    #TODO: Later these will need to be done while logged in.
    
    def test00_admin_sitemap(self):
        full_URL = base_plus_endpoint_encoded('/v2/Admin/Sitemap/?path=c:\\windows\\temp&max_records=5000&size=1000')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        

if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")