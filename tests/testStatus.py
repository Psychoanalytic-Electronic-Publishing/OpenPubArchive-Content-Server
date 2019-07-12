#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

import unittest
import requests
baseAPI = "http://127.0.0.1:8000"

class TestAPIResponses(unittest.TestCase):
    def test_server_status(self):
        # Send a request to the API server and store the response.
        response = requests.get(baseAPI + '/v1/Status/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
        assert(r["text_server_ok"] == True)
        assert(r["db_server_ok"] == True)

    def test_who_am_i(self):
        # Send a request to the API server and store the response.
        response = requests.get(baseAPI + '/v1/WhoAmI/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_get_license_status(self):
        # Send a request to the API server and store the response.
        response = requests.get(baseAPI + '/v1/License/Status/Login/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_get_login(self):
        # Send a request to the API server and store the response.
        response = requests.get(baseAPI + '/v1/Login/?grant_type=password&username=gvpi&password=fish88')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        response = requests.get(baseAPI + '/v1/Logout/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        response = requests.get(baseAPI + '/v1/Login/?grant_type=password&username=xyz&password=bull')
        assert(response.ok == False)

    def test_search(self):
        # Send a request to the API server and store the response.
        response = requests.get('​/v1​/Database​/Search​/?author=Tuckett')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        response = requests.get('/v1/Logout/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        response = requests.get('/v1/Login/?grant_type=password&username=xyz&password=bull')
        assert(response.ok == False)

        
if __name__ == '__main__':
    unittest.main()    