#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests of the new 2020-08-23 CRUD endpoints for storage of global admin configurations
  by the Admin Mode (or Admin APP)
"""
import sys
import os.path

folder = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
if folder == "tests": # testing from within WingIDE, default folder is tests
    sys.path.append('../libs')
    sys.path.append('../config')
    sys.path.append('../../app')
else: # python running from should be within folder app
    sys.path.append('./libs')
    sys.path.append('./config')

from starlette.testclient import TestClient

import unittest
#from localsecrets import TESTUSER, TESTPW, SECRET_KEY, ALGORITHM
#import jwt
#from datetime import datetime

from unitTestConfig import base_api, base_plus_endpoint_encoded
from main import app #  this causes wingware not to finish running the test.  Perhaps it's running the server?
from localsecrets import API_KEY, API_KEY_NAME

client = TestClient(app)
testbody = {
    "configName": "test_client_test_0",
    "configSettings": {"a": 1, "b": 2, "c": 8}
  }

testbody2 = {
    "configName": "test_client_test_0",
    "configSettings": {"a": 2, "b": 4, "c": 8}
  }

test_config_name = "test_client_test_0"

class TestClientConfig(unittest.TestCase):
    """
    Client Config is a database storage location clients can use to store the global config info
      (customization settings.)  Not used by the OPAS server...just there for clients.
    
    Calls require an API key and the client-id in the header.  /
    Some calls require a parameter with the config name.
    
    """   
    def test_0_post(self):
        """
        """
        import opasCentralDBLib

        ocd = opasCentralDBLib.opasCentralDB()
        # make sure it's not there:
        client_id = "2"
        ocd.del_client_config(client_id, test_config_name)
    
        response = client.post(base_api + '/v2/Client/Configuration/',
                               headers={"client-id": client_id, API_KEY_NAME: API_KEY},
                               json=testbody)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert (r == testbody)

        #  try to update -- Fail
        response = client.post(base_api + '/v2/Client/Configuration/',
                               headers={"client-id": client_id, API_KEY_NAME: API_KEY},
                               json=testbody2)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == False)
        assert(response.status_code == 409)

    def test_1_del(self):
        client_id = "2"
        response = client.delete(base_api + '/v2/Client/Configuration/',
                                 headers={"client-id": client_id, API_KEY_NAME: API_KEY}, 
                                 params={'configname': test_config_name})
        assert(response.ok == True)
        r = response.json()

    def test_2_put_and_get(self):
        # save the settings
        client_id = "2"
        session_id = "abc"
        response = client.put(base_api + '/v2/Client/Configuration/',
                               headers={"client-id":client_id, "session-id":session_id, API_KEY_NAME: API_KEY},
                               json=testbody)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        print ("Put OK")
        r = response.json()
        assert (r == testbody)
        print ("Put Echo Testbody OK")

        # Update the settings - Succeed
        response = client.put(base_api + '/v2/Client/Configuration/',
                               headers={"client-id":client_id, "session-id":session_id, API_KEY_NAME: API_KEY},
                               json=testbody2)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        print ("Update Put OK")

        # delete the settings
        response = client.get(base_api + '/v2/Client/Configuration/',
                                 headers={"client-id":client_id, "session-id":session_id, API_KEY_NAME: API_KEY}, 
                                 params={'configname': "test_client_test_0"})
        assert(response.ok == True)
        print ("Get OK")
        r = response.json()

        response = client.delete(base_api + '/v2/Client/Configuration/',
                                 headers={"client-id":client_id, "session-id":session_id, API_KEY_NAME: API_KEY}, 
                                 params={'configname': test_config_name})
        assert(response.ok == True)
        r = response.json()
        print ("Delete OK")
        


if __name__ == '__main__':
    unittest.main()
