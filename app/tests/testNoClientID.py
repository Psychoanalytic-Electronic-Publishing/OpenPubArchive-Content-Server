#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import datetime

logger = logging.getLogger(__name__)

from localsecrets import PADS_TEST_ID, PADS_TEST_PW

import unittest
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID

import requests
import opasDocPermissions

# Login!
pads_session_info = opasDocPermissions.authserver_login(username=PADS_TEST_ID, password=PADS_TEST_PW)
session_info = opasDocPermissions.get_authserver_session_info(pads_session_info.SessionId, client_id=UNIT_TEST_CLIENT_ID, pads_session_info=pads_session_info)
session_id = session_info.session_id
headers = {"client-session":session_id, "client-id": UNIT_TEST_CLIENT_ID, "Content-Type":"application/json"}

class TestSearchBooleans(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    def test_01_search_fulltext1_with_client_id(self):
        # Send a request to the API server and store the response.
        # ### OR #####
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=Mother+or+Father')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)

    def test_02_search_fulltext1_no_client_id(self):
        
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=Mother+or+Father')
        headers = {f"client-session":session_id,
                   "client-id": "", 
                   "Content-Type":"application/json"}
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == False)
        r = response.json()
        print (r)
        
    def test_03_search_fulltext1_no_client_id(self):
        
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=Mother+or+Father')
        headers = {f"client-session":session_id,
                   "client-id": None, # client ID recorded as 666 in this case
                   "Content-Type":"application/json"}
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)

    def test_04_search_fulltext1_no_client_id(self):
        
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=Mother+or+Father')
        headers = {f"client-session": "", 
                   "client-id": None, # client ID recorded as 666 in this case
                   "Content-Type":"application/json"}
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        print (r)
        assert(response.ok == True) # ok now for no client id

if __name__ == '__main__':
    unittest.main()
    