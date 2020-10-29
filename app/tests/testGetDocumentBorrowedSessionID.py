#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import opasAPISupportLib
logger = logging.getLogger(__name__)
import opasDocPermissions

import unittest
import requests

from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID
from localsecrets import PADS_TEST_ID, PADS_TEST_PW, APIURL

class TestGetDocumentsTrySession(unittest.TestCase):
    """
    """
    def test_1_get_document(self):
        # user will not be authenticated. Only abstract returned.
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/IJP.077.0217A/')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"]
        assert(response_info["count"] == 1)
        document = response_set[0]["document"]
        abstr = response_set[0]["abstract"]
        dlen = len(document)
        alen = len(abstr)
        print (f"Abstract size: {alen}; Doc size: {dlen}; Document only returned abstract (indicates no user permissions): {alen==dlen}")
        assert(alen == dlen)
        
    def test_2_get_document_another_user(self):
        # login
        # session_info, pads_session_info = opasDocPermissions.pads_get_session()
        session_info = opasDocPermissions.get_full_session_info(session_id=None, client_id=headers["client-id"])
        
        session_id = session_info.session_id        
        headers["client-session"] = session_id
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={PADS_TEST_ID}&password={PADS_TEST_PW}')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        headers["client-session"] = r["session_id"]
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/APA.007.0035A/')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"]
        assert(response_info["count"] == 1)
        document = response_set[0]["document"]
        abstr = response_set[0]["abstract"]
        dlen = len(document)
        alen = len(abstr)
        print (f"Abstract size: {alen}; Doc size: {dlen}; Logged in user full document return: {alen!=dlen}")
        assert(alen != dlen)
        


if __name__ == '__main__':
    unittest.main()    