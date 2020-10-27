#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests of the new 2020-08-23 CRUD endpoints for storage of global admin configurations
  by the Admin Mode (or Admin APP)
"""
import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, session_id, headers
from localsecrets import API_KEY, API_KEY_NAME

import opasDocPermissions
from localsecrets import PADS_TEST_ID, PADS_TEST_PW

# login
session_info, pads_response = opasDocPermissions.pads_login(username=PADS_TEST_ID, password=PADS_TEST_PW, session_id=session_id)
# Confirm that the request-response cycle completed successfully.
session_id = session_info.session_id
headers = {f"client-session":f"{session_id}",
           "client-id": "4"
           }


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
        full_URL = base_plus_endpoint_encoded('/v2/Client/Configuration/')
        response = requests.post(full_URL, 
                                 headers={"client-id": client_id, API_KEY_NAME: API_KEY},
                                 json=testbody)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert (r == testbody)

        #  try to update -- Fail
        full_URL = base_plus_endpoint_encoded('/v2/Client/Configuration/')
        response = requests.post(full_URL, 
                                 headers={"client-id": client_id, API_KEY_NAME: API_KEY},
                                 json=testbody2)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == False)
        assert(response.status_code == 409)

    def test_1_del(self):
        client_id = "2"
        full_URL = base_plus_endpoint_encoded('/v2/Client/Configuration/')
        response = requests.delete(full_URL,
                                   headers={"client-id": client_id, API_KEY_NAME: API_KEY}, 
                                   params={'configname': test_config_name})
        assert(response.ok == True)
        r = response.json()

    def test_2_put_and_get(self):
        # save the settings
        client_id = "2"
        session_id = "abc"
        full_URL = base_plus_endpoint_encoded('/v2/Client/Configuration/')
        response = requests.put(full_URL,
                                headers={"client-id":client_id, "session-id":session_id, API_KEY_NAME: API_KEY},
                                json=testbody)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        print ("Put OK")
        r = response.json()
        assert (r == testbody)
        print ("Put Echo Testbody OK")

        # Update the settings - Succeed
        full_URL = base_plus_endpoint_encoded('/v2/Client/Configuration/')
        response = requests.put(full_URL,
                                headers={"client-id":client_id, "session-id":session_id, API_KEY_NAME: API_KEY},
                                json=testbody2)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        print ("Update Put OK")

        # delete the settings
        full_URL = base_plus_endpoint_encoded('/v2/Client/Configuration/')
        response = requests.get(full_URL,
                                 headers={"client-id":client_id, "session-id":session_id, API_KEY_NAME: API_KEY}, 
                                 params={'configname': "test_client_test_0"})
        assert(response.ok == True)
        print ("Get OK")
        r = response.json()

        full_URL = base_plus_endpoint_encoded('/v2/Client/Configuration/')
        response = requests.delete(full_URL,
                                   headers={"client-id":client_id, "session-id":session_id, API_KEY_NAME: API_KEY}, 
                                   params={'configname': test_config_name})
        assert(response.ok == True)
        r = response.json()
        print ("Delete OK")
        


if __name__ == '__main__':
    unittest.main()
