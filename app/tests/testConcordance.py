#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)

from localsecrets import PADS_TEST_ID, PADS_TEST_PW

import unittest
from unitTestConfig import base_plus_endpoint_encoded, headers, session_id

import requests
import opasAPISupportLib
import opasDocPermissions

# Login!
session_info, pads_response = opasDocPermissions.pads_login(username=PADS_TEST_ID, password=PADS_TEST_PW, session_id=session_id)
# Confirm that the request-response cycle completed successfully.
session_id = session_info.session_id
headers = {"client-session":session_id, "client-id": "0", "Content-Type":"application/json"}

class TestConcordance(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    def test1_get_para_translation(self):
        """
        """
        data = opasAPISupportLib.documents_get_concordance_paras("SEXixa5")
        # Confirm that the request-response cycle completed successfully.
        para_info = data.documents.responseSet[0].docChild
        para = para_info['para']
        print (para)
        assert (len(para) > 0)
        # check to make sure a known value is among the data returned
        
    def test2_concordance_endpoint(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Documents/Concordance/?paralangid=SEXixa5')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        r = response.json()
        para_cordance = r['documents']['responseSet'][0]['docChild']
        # Confirm that the request-response cycle completed successfully.
        para = para_cordance['para']
        print (para)
        assert (len(para) > 0)
        # check to make sure a known value is among the data returned
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")