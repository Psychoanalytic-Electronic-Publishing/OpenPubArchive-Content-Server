#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

#  This test module is in development...

import opasDocPermissions
import requests

import logging
logger = logging.getLogger(__name__)

import unittest
from localsecrets import PADS_TEST_ID, PADS_TEST_PW

from unitTestConfig import base_api, base_plus_endpoint_encoded

session_info, pads_response = opasDocPermissions.pads_login(username=PADS_TEST_ID, password=PADS_TEST_PW)
# Confirm that the request-response cycle completed successfully.
sessID = session_info.session_id
headers = {f"client-session":f"{sessID}",
           "client-id": "4"
           }

class TestDocumentImageFetch(unittest.TestCase):
    """
    Tests for image fetch
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.   
    """   
    def test_0_Image(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Image/bannerIJPLogo.gif/')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_1_Image(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Image/infoicon.gif/')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)


if __name__ == '__main__':
    unittest.main()    