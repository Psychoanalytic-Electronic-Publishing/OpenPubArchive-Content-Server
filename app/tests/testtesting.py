#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

#  This test module is in development...

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

#from unitTestConfig import base_api, base_plus_endpoint_encoded
from main import app #  this causes wingware not to finish running the test.  Perhaps it's running the server?

class TestTesting(unittest.TestCase):
    """
    Test of wingware testing
    """   

    def test_0_most_downloaded(self):
        """
        """
        # request login to the API server
        response = '/v1/Database/MostDownloaded/'
        assert (response is not None)
        # Confirm that the request-response cycle completed successfully.
        #assert(r["text_server_ok"] == True)
        #assert(r["db_server_ok"] == True)
        print (response)
       

if __name__ == '__main__':
    unittest.main()
