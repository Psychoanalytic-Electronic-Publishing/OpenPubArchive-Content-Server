#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger()

import requests
import unittest
import time
from localsecrets import API_KEY_NAME, AUTH_KEY_NAME, API_KEY, PADS_TEST_ID, PADS_TEST_PW, PDF_ORIGINALS_PATH, PADS_TEST_ID2, PADS_TEST_PW2, use_server
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, test_login

# Login!
sessID, headers, session_info = test_login(username=PADS_TEST_ID2, password=PADS_TEST_PW2)

if use_server == 5:
    from localsecrets import PADS_TEST_ID3, PADS_TEST_PW3
    sessID, headers, session_info = test_login(username=PADS_TEST_ID3, password=PADS_TEST_PW3)

class TestReports(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
          
    """   

    #TODO: Later these will need to be done while logged in.
    
    def test01_session_log_report_daterange(self):
        # note api_key is required, but already in headers
        from datetime import date, timedelta
        dt1 = date.today() - timedelta(4)
        dt2 = date.today()
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?limit=10&startdate={dt1}&enddate={dt2}')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        assert(response_info["count"] >= 1)

    def test01b_session_log_report_matchstr(self):
        # note api_key is required, but already in headers
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?limit=10&matchstr=/v2/Documents/Abstract')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        assert(response_info["count"] >= 1)

    def test01b_session_log_report_download(self):
        # note api_key is required, but already in headers
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?limit=10&matchstr=/v2/Documents/Abstract&download=true')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        assert (response.headers["content-disposition"] == 'attachment; filename=vw_reports_session_activity.csv')

    def test02_document_view__log_report(self):
        # note api_key is required, but already in headers
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Document-View-Log?limit=10&offset=5')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        assert(response_info["count"] >= 1)

    def test03_document_view__stat_report(self):
        # note api_key is required, but already in headers
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Document-View-Stat?limit=10')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        assert(response_info["count"] >= 1)

    def test04_user_searches_report(self):
        # note api_key is required, but already in headers
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/User-Searches?limit=10')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        assert(response_info["count"] >= 1)

    def test05_session_log_report_endpointid(self):
        # note api_key is required, but already in headers
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?limit=10&endpointidlist=31,32')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        assert(response_info["count"] >= 1)
        
    def test06_session_log_report_like_pads(self):
        # note api_key is required, but already in headers
        from datetime import date, timedelta
        dt = date.today() - timedelta(14)
        print('Current Date :', date.today())
        print('14 days before Current Date :', dt)
        ts = time.time()
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?startdate={dt}&limit=100000&offset=0&download=false&sortorder=asc')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        print (f"Watched: Admin Report Query Complete. Time={time.time() - ts}")
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        print (f'Count Retrieved: {response_info["count"]}')
        print (f'Fullcount Retrieved: {response_info["fullCount"]}')
        if use_server == 5:
            assert(response_info["count"] >= 50000)
        else:
            assert(response_info["count"] >= 100)
            


if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")