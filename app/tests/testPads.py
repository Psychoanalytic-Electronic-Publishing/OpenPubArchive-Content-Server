#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

import sys
import os.path
import logging
logger = logging.getLogger(__name__)

folder = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
if folder == "tests": # testing from within WingIDE, default folder is tests
    sys.path.append('../libs')
    sys.path.append('../config')
    sys.path.append('../../app')
else: # python running from should be within folder app
    sys.path.append('./libs')
    sys.path.append('./config')

import unittest
import requests
# from requests.utils import requote_uri
# import urllib

from unitTestConfig import base_api, base_plus_endpoint_encoded
from localsecrets import TESTUSER, TESTPW, SECRET_KEY, ALGORITHM
from localsecrets import PADS_TEST_ID, PADS_TEST_PW, PADS_BASED_CLIENT_IDS

import timeit
import opasDocPermissions as opasDocPerm
import json
from models import PadsSessionInfo
from opasConfig import AUTH_ABSTRACT_VIEW_REQUEST
global session_id

class TestPadsEndpoints(unittest.TestCase):

    def test_0a_pads_tests(self):
        # Login to PaDS with test account and then check responses to mostCited for access.
        response = opasDocPerm.pads_login()
        if response["ReasonStr"] is None:
            response["ReasonStr"] = ""
        pads_session = PadsSessionInfo(**response)
        assert (pads_session.HasSubscription == True)
        assert (pads_session.IsValidLogon == True)
        assert (pads_session.IsValidUserName == True)
        assert (pads_session.ReasonId == 200)
        
        ## Confirm that the request-response cycle completed successfully.
        try:
            session_id = response["SessionId"]
        except:
            err = f"PaDS response error: {response}"
            logger.error(err)
            print (err)
            assert(False)
        else:
            authorized, resp = opasDocPerm.pads_permission_check(session_id=session_id,
                                                                 doc_id="AJRPP.002.0349A",
                                                                 doc_year="2008",
                                                                 reason_for_check=AUTH_ABSTRACT_VIEW_REQUEST)

            # if this is True, then as long as session_info is valid, it won't need to check again
            # if accessLimited is ever True again, e.g., now a different type of document, it will check again.
            # should markedly decrease the number of calls to PaDS to check.
            
            a = resp.get("HasArchiveAccess", True)
            b = resp.get("HasCurrentAccess", True)
            #assert(r['documentList']['responseSet'][0].get("accessLimited", None) == False)




if __name__ == '__main__':
    unittest.main()
