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
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, test_login

# Login!
sessID, headers, session_info = test_login()

class TestDownload(unittest.TestCase):
    """
    Tests for basic login and Download
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.   
    """   
    def test_1_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDFORIG/IJP.077.0217A/')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_2_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDF/IFP.017.0240A/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_2B_Download(self):
        # has grraphics
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/PDF/APA.007.0035A/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
       

    def test_3_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/EPUB/IJPSP.009.0324A/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_4_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Downloads/HTML/IJPSP.009.0324A/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_5_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Database/MostCited/?download=true')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_6_Download(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Database/MostViewed/?download=true')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

if __name__ == '__main__':
    unittest.main()    