#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers

class TestAPIStatus(unittest.TestCase):
    """
    Tests for status endpoints 
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    Checks the API status
    
    This endpoint is a low overhead function and suitable as a heartbeat check.
    """   

    def test_v2_api_status(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Api/Status/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert response.ok == True
        r = response.json()
        print (f'opasVersion: {r["opas_version"]}, time: {r["timeStamp"]}')
        assert r.get("opas_version") is not None
       
if __name__ == '__main__':
    unittest.main()    