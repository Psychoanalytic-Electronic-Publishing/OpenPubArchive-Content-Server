#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests of the new 2020-08-23 CRUD endpoints for storage of global admin configurations
  by the Admin Mode (or Admin APP)
"""
import unittest
import requests
import models
import json
import http

from unitTestConfig import base_plus_endpoint_encoded, session_id, headers, session_id, UNIT_TEST_CLIENT_ID
from localsecrets import API_KEY, API_KEY_NAME

import opasDocPermissions
from localsecrets import PADS_TEST_ID, PADS_TEST_PW
client_id = UNIT_TEST_CLIENT_ID

# login
pads_session_info = opasDocPermissions.authserver_login(username=PADS_TEST_ID, password=PADS_TEST_PW, session_id=session_id)
# saves to db, but clearly we're not using this here
session_info = opasDocPermissions.get_authserver_session_info(pads_session_info.SessionId, client_id, pads_session_info=pads_session_info)
# Confirm that the request-response cycle completed successfully.
session_id = session_info.session_id
headers = {f"client-session":f"{session_id}",
           "client-id": client_id,
           "Content-Type":"application/json",
           API_KEY_NAME: API_KEY
           }

test_config_name = "test_client_test"
test_config_name_1 = f"{test_config_name}_1"
test_config_name_2 = f"{test_config_name}_2"
# test_config_name_strlist = f"{test_config_name_0}, {test_config_name_1}"
config_settings_1 =  {"a": 1, "b": 2, "c": 8}
config_settings_2 =  {"a": 2, "b": 4, "c": 8}

testbody1 = {
    "configName": test_config_name_1,
    "configSettings": config_settings_1
  }

testbody2 = {
    "configName": test_config_name_2,
    "configSettings": config_settings_2
  }

testlist_single1 = {"configList": [testbody1]}
testlist_single2 = {"configList": [testbody2]}
testlist_double = {"configList": [testbody1, testbody2]}

class TestClientConfig(unittest.TestCase):
    """
    Client Config is a database storage location clients can use to store the global config info
      (customization settings.)  Not used by the OPAS server...just there for clients.
    
    Calls require an API key and the client-id in the header.  /
    Some calls require a parameter with the config name.
    
    """   
    def test_0_get(self):
        # save the settings
        full_URL = base_plus_endpoint_encoded('/v2/Client/Configuration/')
        response = requests.put(full_URL,
                                headers=headers,
                                json=testlist_double)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert (r == testlist_double)
        print ("Put OK: ", r)

        # fetch one of the settings
        full_URL = base_plus_endpoint_encoded('/v2/Client/Configuration/')
        response = requests.get(full_URL,
                                headers=headers,
                                params={'configname': test_config_name_1})
        assert(response.ok == True)
        #print(headers["client-session"])
        r = response.json()
        assert (r == {'configList': [{'configName': test_config_name_1, 'configSettings': config_settings_1}]})
        print ("Get OK: ", r)

        # fetch both of the settings
        full_URL = base_plus_endpoint_encoded('/v2/Client/Configuration/')
        response = requests.get(full_URL,
                                headers=headers,
                                params={'configname': f"{test_config_name_1}, {test_config_name_2}"})
        assert(response.ok == True)
        #print(headers["client-session"])
        r = response.json()
        #assert (r == {'configList': [{'configName': 'test_client_test_1', 'configSettings': {'a': 1, 'b': 2, 'c': 8}}, {'configName': 'test_client_test_2', 'configSettings': {'a': 2, 'b': 4, 'c': 8}}]})
        assert (r == {'configList': [{'configName': test_config_name_1, 'configSettings': config_settings_1}, {'configName': test_config_name_2, 'configSettings': config_settings_2}]})
        print ("Get OK: ", r)

    def test_0_post(self):
        """
        """
        # make sure both are not there:
        full_URL = base_plus_endpoint_encoded('/v2/Client/Configuration/')
        response = requests.delete(full_URL,
                                   headers=headers,
                                   params={'configname': f"{test_config_name_1}, {test_config_name_2}"}
                                   )

        # now post the list 
        response = requests.post(full_URL, 
                                 headers=headers,
                                 json=testlist_double)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        assert(response.status_code == 201)
        
        r = response.json()
        assert (r == testlist_double)
        print ("Post OK: ", r)

    def test_0B_post_double(self):
        """
        """
        # make sure both are not there:
        full_URL = base_plus_endpoint_encoded('/v2/Client/Configuration/')
        response = requests.delete(full_URL,
                                   headers=headers,
                                   params={'configname': f"{test_config_name_1}, {test_config_name_2}"}
                                   )

        # now post the list 
        response = requests.post(full_URL, 
                                 headers=headers,
                                 json=testlist_double)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        assert(response.status_code == 201)
        r = response.json()
        assert (r == testlist_double)
        print ("Post OK: ", r)
        
        # now post the list again
        response = requests.post(full_URL, 
                                 headers=headers,
                                 json=testlist_double)
        # item already exists, so return a conflict.
        assert(response.status_code == 409)

    def test_0D_put_double(self):
        """
        """
        # make sure both are not there:
        full_URL = base_plus_endpoint_encoded('/v2/Client/Configuration/')
        response = requests.delete(full_URL,
                                   headers=headers,
                                   params={'configname': f"{test_config_name_1}, {test_config_name_2}"}
                                   )

        # now post the list 
        response = requests.put(full_URL, 
                                headers=headers,
                                json=testlist_double)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        assert(response.status_code == 201)
        r = response.json()
        assert (r == testlist_double)
        # print ("Put OK: ", r)
        
        # now put the list again
        response = requests.put(full_URL, 
                                headers=headers,
                                json=testlist_double)
        # item already exists, so return a conflict.
        assert(response.status_code == 200)

    def test_2_put_and_get(self):
        # save the settings (whole list)
        full_URL = base_plus_endpoint_encoded('/v2/Client/Configuration/')
        response = requests.put(full_URL,
                                headers=headers,
                                json=testlist_double)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert (r == testlist_double)
        print ("Put list OK: ", r)

        # Update the settings - Succeed
        full_URL = base_plus_endpoint_encoded('/v2/Client/Configuration/')
        response = requests.put(full_URL,
                                headers=headers,
                                json=testlist_double)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        print ("Update list Put OK: ", r)

        # get one of the settings
        full_URL = base_plus_endpoint_encoded('/v2/Client/Configuration/')
        response = requests.get(full_URL,
                                headers=headers,
                                params={'configname': f"{test_config_name_1}"})
        assert(response.ok == True)
        r = response.json()
        assert (r == {'configList': [{'configName': test_config_name_1, 'configSettings': config_settings_1}]})
        print ("Get updated config1 from list OK: ", r)

        # get the other settings
        full_URL = base_plus_endpoint_encoded('/v2/Client/Configuration/')
        response = requests.get(full_URL,
                                headers=headers,
                                params={'configname': f"{test_config_name_2}"})
        assert(response.ok == True)
        r = response.json()
        print (r)
        assert (r == {'configList': [{'configName': test_config_name_2, 'configSettings': config_settings_2}]})
        print ("Get updated config2 from list OK: ", r)

        # get both of the settings
        full_URL = base_plus_endpoint_encoded('/v2/Client/Configuration/')
        response = requests.get(full_URL,
                                headers=headers,
                                params={'configname': f"{test_config_name_1}, {test_config_name_2}"})
        assert(response.ok == True)
        r = response.json()
        assert (r == {'configList': [{'configName': test_config_name_1, 'configSettings': config_settings_1}, {'configName': test_config_name_2, 'configSettings': config_settings_2}]})
        print ("Get updated both configs from list OK: ", r)

    def test_3_post_fail(self):
        #  try to update -- Fail
        full_URL = base_plus_endpoint_encoded('/v2/Client/Configuration/')
        response = requests.post(full_URL, 
                                 headers=headers,
                                 json=testlist_double)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == False)
        assert(response.status_code == 409)

    def test_4_del_and_cleanup(self):
        full_URL = base_plus_endpoint_encoded('/v2/Client/Configuration/')
        # create test records, if not there
        response = requests.put(full_URL,
                                headers=headers,
                                json=testlist_double)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        response = requests.delete(full_URL,
                                   headers=headers,
                                   params={'configname': test_config_name_1})
        assert(response.ok == True)
        r = response.json()
        #print (r)
        assert (r == {'configList': [{'configName': test_config_name_1, 'configSettings': config_settings_1}]})
        response = requests.delete(full_URL,
                                   headers=headers,
                                   params={'configname': test_config_name_2})
        assert(response.ok == True)
        r = response.json()
        assert (r == {'configList': [{'configName': test_config_name_2, 'configSettings': config_settings_2}]})

        # First create, then delete both at once
        response = requests.put(full_URL,
                                headers=headers,
                                json=testlist_double)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        print ("Update list in order to test delete, Put OK: ", r)
        
        response = requests.delete(full_URL,
                                   headers=headers,
                                   params={'configname': f"{test_config_name_1}, {test_config_name_2}"}
                                  )
        assert(response.ok == True)
        r = response.json()
        #print (r)
        assert (r == {'configList': [{'configName': test_config_name_1, 'configSettings': config_settings_1}, {'configName': test_config_name_2, 'configSettings': config_settings_2}]})
        print ("Update list Del OK: ", r)



if __name__ == '__main__':
    unittest.main()
