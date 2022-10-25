#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

import unittest
import requests
import sys
from datetime import datetime
import time

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

def display_endpoint_time(request, ts, level="info", trace=False):
    text = f"***{request} response time: {time.time() - ts}***"
    print(text)            

class TestMost(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_1_most_viewed_cache(self):
        """
        Test mostviewed calls with caching
        """
        print (f"Running: {sys._getframe(  ).f_code.co_name} at {datetime.now()}")
        ts = time.time()
        request = '/v2/Database/MostViewed/?&limit=10&viewperiod=2'
        full_URL = base_plus_endpoint_encoded(request)
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        display_endpoint_time(request, ts=ts, level="info")

        request = '/v2/Database/MostViewed/?&limit=10&viewperiod=2'
        full_URL = base_plus_endpoint_encoded(request)
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        display_endpoint_time(request, ts=ts, level="info")

        request = '/v2/Database/MostViewed/?&limit=10&viewperiod=2'
        full_URL = base_plus_endpoint_encoded(request)
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        display_endpoint_time(request, ts=ts, level="info")

if __name__ == '__main__':
    unittest.main()
    client.close()
    