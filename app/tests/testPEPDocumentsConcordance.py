#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import datetime

logger = logging.getLogger(__name__)

from localsecrets import PADS_TEST_ID, PADS_TEST_PW

import unittest
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID

import requests
import opasAPISupportLib
import opasDocPermissions

# Login!
pads_session_info = opasDocPermissions.authserver_login(username=PADS_TEST_ID, password=PADS_TEST_PW)
session_info = opasDocPermissions.get_authserver_session_info(pads_session_info.SessionId, client_id=UNIT_TEST_CLIENT_ID, pads_session_info=pads_session_info)
# Confirm that the request-response cycle completed successfully.
session_id = session_info.session_id
headers = {"client-session":session_id, "client-id": UNIT_TEST_CLIENT_ID, "Content-Type":"application/json"}

class TestDocumentsConcordance(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    def test1_get_para_translation(self):
        """
        """
        ts = datetime.datetime.now()
        data = opasAPISupportLib.documents_get_concordance_paras("SEXixa5", session_info=session_info)
        # Confirm that the request-response cycle completed successfully.
        para_info = data.documents.responseSet[0].docChild
        para = para_info['para']
        print (f"Time: {datetime.datetime.now()-ts}")
        print (para)
        assert (len(para) > 0)
        # check to make sure a known value is among the data returned
        
    def test2_concordance_endpoint(self):
        """
        """
        ts = datetime.datetime.now()
        full_URL = base_plus_endpoint_encoded('/v2/Documents/Concordance?paralangid=SEXixa5')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        r = response.json()
        para_cordance = r['documents']['responseSet'][0]['docChild']
        # Confirm that the request-response cycle completed successfully.
        para = para_cordance['para']
        print (f"Time: {datetime.datetime.now()-ts}")
        print (para)
        assert (len(para) > 0)
        # check to make sure a known value is among the data returned

    def test3_concordance_both_args(self):
        """
        """
        ts = datetime.datetime.now()
        full_URL = base_plus_endpoint_encoded('/v2/Documents/Concordance?paralangid=SEA3a24&paralangrx=GWS31a30')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        r = response.json()
        para_cordance = r['documents']['responseSet'][0]['docChild']
        # Confirm that the request-response cycle completed successfully.
        para = para_cordance['para']
        print (f"Time: {datetime.datetime.now()-ts}")
        print (para)
        assert (len(para) > 0)
        full_URL = base_plus_endpoint_encoded('/v2/Documents/Concordance?paralangrx=GWS31a30')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        r = response.json()
        para_cordance = r['documents']['responseSet'][0]['docChild']
        # Confirm that the request-response cycle completed successfully.
        para = para_cordance['para']
        print (f"Time: {datetime.datetime.now()-ts}")
        print (para)
        assert (len(para) > 0)
        # also test document field, that's what the client uses.
        document_para_cordance_copy = r['documents']['responseSet'][0]['document']
        # Confirm that the request-response cycle completed successfully.
        assert (len(document_para_cordance_copy) > 0)
        

    def test4_concordance_list(self):
        """
        """
        ts = datetime.datetime.now()
        full_URL = base_plus_endpoint_encoded('/v2/Documents/Concordance?paralangrx=GWS387a3, GWS387a4, GWS480a2')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        r = response.json()
        assert (len(r['documents']['responseSet']) >= 4)


        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")