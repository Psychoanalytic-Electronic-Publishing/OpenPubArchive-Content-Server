#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

import sys
sys.path.append('../libs')
sys.path.append('../config')
import unittest
import requests
from requests.utils import requote_uri
import urllib

# base_api = "http://stage.pep.gvpi.net/api"
base_api = "http://127.0.0.1:9100"

def base_plus_endpoint_encoded(endpoint):
    # ret_val = baseAPI + urllib.parse.quote_plus(endpoint, safe="/")
    ret_val = base_api + endpoint
    return ret_val

class TestLoginResponses(unittest.TestCase):
    def test_server_status(self):
        # Send a request to the API server and store the response.
        response = requests.get(base_api + '/v2/Admin/Status/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
        assert(r["text_server_ok"] == True)
        assert(r["db_server_ok"] == True)

    def test_get_login_good(self):
        return True
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v1/Login/?grant_type=password&username=gvpi&password=fish88')
        response = requests.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        print (response.ok)
        assert(response.ok == True)
        full_URL = base_plus_endpoint_encoded('/v1/Logout/')
        response = requests.get(full_URL, headers={"content-type":"application/json"})
        # Confirm that the request-response cycle completed successfully.
        print (response.ok)
        assert(response.ok == False)

    def test_who_am_i(self):
        return True
        full_URL = base_plus_endpoint_encoded('/v1/Login/?grant_type=password&username=gvpi&password=fish88')
        response = requests.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        print (response.ok)
        assert(response.ok == True)
        r = response.json()
        # Send a request to the API server and store the response.
        response2 = requests.get(base_api + '/v2/Admin/WhoAmI/')
        # Confirm that the request-response cycle completed successfully.
        assert(response2.ok == True)
        r2 = response2.json()
        assert(r2["opasSessionID"] is not None)

    def test_get_license_status(self):
        # Send a request to the API server and store the response.
        response = requests.get(base_api + '/v1/License/Status/Login/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        responseInfo = r["licenseInfo"]["responseInfo"]
        responseSet = r["licenseInfo"]["responseSet"]
        print (responseSet)

    def test_get_login_bad(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v1/Login/?grant_type=password&username=xyz&password=bull')
        response = requests.get(full_URL)
        assert(response.ok == False)
        r = response.json()
        loginReturnItem = r["loginReturnItem"]
        print (responseSet)

        
if __name__ == '__main__':
    unittest.main()    