#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

import unittest
import requests
import localsecrets
import pprint
import sys

# import opasDocPermissions
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, test_login, test_logout, get_headers_not_logged_in

# Login!
sessID, headers, session_info = test_login(username=localsecrets.PADS_TEST_ARCHIVEONLY, password=localsecrets.PADS_TEST_ARCHIVEONLY_PW)

FUTURE_DOC = None # "PCAS.008.0003A"
global message_collection
global pp
pp = pprint.PrettyPrinter(indent=5, width=70) # , stream=sys.stderr) # , sort_dicts=True) sort_dicts requires py 3.8
message_collection = {}

class TestAccessMessagesArchiveAndCurrentINSPECTMANUALLY(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    userid = localsecrets.PADS_TEST_ARCHIVEANDCURRENT
    userpw = localsecrets.PADS_TEST_ARCHIVEANDCURRENT_PW
    usertype = "All Access user"
    print (f"Login PADS_TEST_ARCHIVEANDCURRENT! {userid} - {usertype}")
    sessID, headers, session_info = test_login(username=userid, password=userpw)
    search_term = "test"
    message_collection[usertype] = {}

    def test_001A_get_pepspecial_permission_manually_proof_messages(self):
        # global message_collection
        # Try to return IJPOPEN
        # ijpopen document
        full_URL = base_plus_endpoint_encoded(f"/v2/Documents/Document/IJPOPEN.004.0008A/?return_format=XML")
        response = requests.get(full_URL, headers=self.headers)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"][0]
        print(f'Classification: {response_set["accessClassification"]}')
        print(f'Reason:\n   {response_set["accessLimitedReason"]}\n')
        print(f'Description: {response_set["accessLimitedDescription"]}\n')
        print(f'DebugMessage: {response_set["accessLimitedDebugMsg"]}\n')
        assert response_set["accessLimited"] == True
        assert response_set["accessClassification"] == 'special', response_set["accessClassification"]
        message_collection[self.usertype][response_set["accessClassification"]] = \
            f'Reason:\n   {response_set["accessLimitedReason"]}\n'

    def test_002A_get_pepcurrent_permission_manually_proof_messages(self):
        # pepcurrent document
        full_URL = base_plus_endpoint_encoded(f"/v2/Documents/Document/AJP.080.0001A/?return_format=XML")
        response = requests.get(full_URL, headers=self.headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"][0]
        print(f'Classification: {response_set["accessClassification"]}\n')
        print(f'Reason:\n   {response_set["accessLimitedReason"]}\n')
        print(f'Description: {response_set["accessLimitedDescription"]}\n')
        print(f'DebugMessage: {response_set["accessLimitedDebugMsg"]}\n')
        assert response_set["accessLimited"] == False
        assert response_set["accessClassification"] == 'current'
        access_class = response_set["accessClassification"]
        print (f"Access Classification: {access_class}")
        print (f"Message_Collection Dict: {message_collection[self.usertype]}")
        message_collection[self.usertype][response_set["accessClassification"]] = \
            f'Reason:\n   {response_set["accessLimitedReason"]}\n'

    def test_003A_get_peparchive_permission_manually_proof_message(self):
        # peparchive document
        full_URL = base_plus_endpoint_encoded(f"/v2/Documents/Document/AJP.024.0017A/?return_format=XML")
        response = requests.get(full_URL, headers=self.headers)
        # Confirm that the request-response cycle completed successfully.
        assert response.ok == True
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"][0]
        print(f'Classification: {response_set["accessClassification"]}\n')
        print(f'Reason:\n   {response_set["accessLimitedReason"]}\n')
        print(f'Description: {response_set["accessLimitedDescription"]}\n')
        print(f'DebugMessage: {response_set["accessLimitedDebugMsg"]}\n')
        assert response_set["accessLimited"] == False
        assert response_set["accessClassification"] == 'archive', response_set["accessClassification"]
        message_collection[self.usertype][response_set["accessClassification"]] = \
            f'Reason:\n   {response_set["accessLimitedReason"]}\n'

    def test_004A_get_pepfree_permission_manually_proof_messages(self):
        # free document
        full_URL = base_plus_endpoint_encoded(f"/v2/Documents/Document/PEPGRANTVS.001.0007A/?return_format=XML")
        response = requests.get(full_URL, headers=self.headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"][0]
        print(f'Classification: {response_set["accessClassification"]}\n')
        print(f'Reason:\n   {response_set["accessLimitedReason"]}\n')
        print(f'Description: {response_set["accessLimitedDescription"]}\n')
        print(f'DebugMessage: {response_set["accessLimitedDebugMsg"]}\n')
        assert response_set["accessLimited"] == False
        assert response_set["accessClassification"] == 'free', response_set["accessClassification"]
        message_collection[self.usertype][response_set["accessClassification"]] = \
            f'Reason:\n   {response_set["accessLimitedReason"]}\n'      
    
if __name__ == '__main__':
    unittest.main()
    #print (message_collection)
    # pp.pprint(message_collection)