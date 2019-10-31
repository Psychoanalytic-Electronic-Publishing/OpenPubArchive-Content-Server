#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

#  This test module is in development...

import sys
sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../../app')

from starlette.testclient import TestClient

import unittest
from localsecrets import TESTUSER, TESTPW, SECRET_KEY, ALGORITHM
import jwt
from datetime import datetime

from testConfig import base_api, base_plus_endpoint_encoded
from main import app

client = TestClient(app)

class TestLogin(unittest.TestCase):
    """
    Tests for basic login and Logout
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    
    def test_0_login(self):
        full_URL = base_plus_endpoint_encoded(f'/v1/Login/?grant_type=password&username={TESTUSER}&password={TESTPW}')
        response = client.get(full_URL)
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
        print (decoded_access_token )

        # now Check if we are logged in!
        full_URL = base_plus_endpoint_encoded('/v1/Admin/WhoAmI/')
        response = client.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        access_token = r["access_token"]
        session_id =  r["session_id"]
        assert(session_id == orig_session_id)       
        decoded_access_token = jwt.decode(access_token,
                                          key=SECRET_KEY,
                                          algorithms=ALGORITHM
                                         )
        print (decoded_access_token )
        assert(r["authenticated"] == True)

    def test_1_logout(self):
        full_URL = base_plus_endpoint_encoded(f'/v1/Logout/')
        response = client.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["licenseInfo"]["responseInfo"]
        response_set = r["licenseInfo"]["responseSet"]
        assert(r["licenseInfo"]["responseInfo"]["loggedIn"] == False)

        full_URL = base_plus_endpoint_encoded('/v1/Admin/WhoAmI/')
        response = client.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        access_token = r["access_token"]
        session_id =  r["session_id"]
        assert(access_token is None)
        
        if access_token is not None:
            decoded_access_token = jwt.decode(access_token,
                                              key=SECRET_KEY,
                                              algorithms=ALGORITHM
                                             )
            print (decoded_access_token )

    def test_2_bad_login(self):
        full_URL = base_plus_endpoint_encoded(f'/v1/Login/?grant_type=password&username={TESTUSER}&password="notthepassword"')
        response = client.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        access_token = r["access_token"]
        session_id =  r["session_id"]
        assert(access_token == '')

        full_URL = base_plus_endpoint_encoded('/v1/Admin/WhoAmI/')
        response = client.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        access_token = r["access_token"]
        session_id =  r["session_id"]

        if access_token is not None:
            decoded_access_token = jwt.decode(access_token,
                                              key=SECRET_KEY,
                                              algorithms=ALGORITHM
                                             )
            print (decoded_access_token )
       
if __name__ == '__main__':
    unittest.main()    