#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
logger = logging.getLogger(__name__)

from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID
from localsecrets import PADS_TEST_ID, PADS_TEST_PW, PADS_BASED_CLIENT_IDS

import opasDocPermissions
from opasConfig import AUTH_ABSTRACT_VIEW_REQUEST

class TestPadsEndpoints(unittest.TestCase):

    def test_00a_pads_tests(self):
        global session_id
        # Login to PaDS with test account and then check responses to mostCited for access.
        # session_info, pads_session_info = opasDocPermissions.pads_get_session(session_id=session_id)
        session_info = opasDocPermissions.get_authserver_session_info(session_id=session_id, client_id=UNIT_TEST_CLIENT_ID)
        
        print (session_info.session_id)
        assert(session_info.session_id is not None)
        
    def test_0a_pads_tests(self):
        global session_id
        # Login to PaDS with test account and then check responses to mostCited for access.
        pads_session_info = opasDocPermissions.authserver_login(username=PADS_TEST_ID, password=PADS_TEST_PW)
        session_info = opasDocPermissions.get_authserver_session_info(pads_session_info.SessionId, client_id=UNIT_TEST_CLIENT_ID, pads_session_info=pads_session_info)
        assert (pads_session_info.HasSubscription == True)
        assert (pads_session_info.IsValidLogon == True)
        assert (pads_session_info.IsValidUserName == True)
        assert (pads_session_info.ReasonId == 200)
        
        ## Confirm that the request-response cycle completed successfully.
        try:
            session_id = session_info.session_id
        except:
            err = f"PaDS response error: {pads_session_info}"
            logger.error(err)
            print (err)
            assert(False)
        else:
            authorized, resp = opasDocPermissions.authserver_permission_check(session_id=session_id,
                                                                        doc_id="AJRPP.002.0349A",
                                                                        doc_year="2008",
                                                                        reason_for_check=AUTH_ABSTRACT_VIEW_REQUEST)

            # if this is True, then as long as session_info is valid, it won't need to check again
            # if accessLimited is ever True again, e.g., now a different type of document, it will check again.
            # should markedly decrease the number of calls to PaDS to check.
            
            assert(resp.HasArchiveAccess == True)
            assert(resp.HasCurrentAccess == False)
            #assert(r['documentList']['responseSet'][0].get("accessLimited", None) == False)

    def test_1_session_info(self):
        session_info = opasDocPermissions.get_base_session_info()
        print (session_info)


if __name__ == '__main__':
    unittest.main()
