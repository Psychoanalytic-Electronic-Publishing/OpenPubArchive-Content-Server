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
from localsecrets import TESTUSER, TESTPW, SECRET_KEY, ALGORITHM
import jwt
from datetime import datetime

from testConfig import base_api, base_plus_endpoint_encoded

class TestAPIResponses(unittest.TestCase):
    """
    Tests for basic login and Logout
    
    Note that tests are performed in alphabetical order, hence the function naming with forced order in the names.
    
    """
    def test_0_server_status(self):
        # Send a request to the API server and store the response.
        response = requests.get(base_api + '/v2/Admin/Status/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r["text_server_ok"] == True)
        assert(r["db_server_ok"] == True)
        print (r)

    def test_a0_good_login(self):
        full_URL = base_plus_endpoint_encoded(f'/v1/Login/?grant_type=password&username={TESTUSER}&password={TESTPW}')
        response = requests.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        access_token = r["access_token"]
        session_id =  r["session_id"]
        decoded_access_token = jwt.decode(access_token,
                                          key=SECRET_KEY,
                                          algorithms=ALGORITHM
                                         )
        expires_time = datetime.fromtimestamp(decoded_access_token['exp'])
        orig_session_id = decoded_access_token['orig_session_id']
        assert(r["authenticated"] == True)
        assert(session_id == orig_session_id)       

    def test_a1_logout(self):
        full_URL = base_plus_endpoint_encoded(f'/v1/Logout/')
        response = requests.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["licenseInfo"]["responseInfo"]
        response_set = r["licenseInfo"]["responseSet"]
        assert(r["loggedIn"] == True)

    def test_a2_bad_login(self):
        full_URL = base_plus_endpoint_encoded(f'/v1/Login/?grant_type=password&username={TESTUSER}&password="notthepassword"')
        response = requests.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["licenseInfo"]["responseInfo"]
        response_set = r["licenseInfo"]["responseSet"]
        assert(r["loggedIn"] == True)

    def test_a4_who_am_i(self):
        full_URL = base_plus_endpoint_encoded('/v2/Admin/WhoAmI/')
        response = requests.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["licenseInfo"]["responseInfo"]
        assert(r["opasSessionID"] is not None)
        print (r)

    def test_d_get_license_status(self):
        # Send a request to the API server and store the response.
        response = requests.get(base_api + '/v1/License/Status/Login/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["licenseInfo"]["responseInfo"]
        response_set = r["licenseInfo"]["responseSet"]
        print (response_info)
       
if __name__ == '__main__':
    unittest.main()    