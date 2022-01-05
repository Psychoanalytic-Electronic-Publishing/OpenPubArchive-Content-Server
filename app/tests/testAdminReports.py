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
# set log level to error
full_URL = base_plus_endpoint_encoded('/v2/Admin/LogLevel/?level=ERROR')
response = requests.put(full_URL, headers=headers)

class TestReports(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
          
    """   

    #TODO: Later these will need to be done while logged in.
    
    def test01_session_log_report_daterange(self):
        # note api_key is required, but already in headers
        import datetime
        from datetime import date, timedelta
        dt1 = date.today() - timedelta(2)
        dt2 = date.today()
        dt3 = datetime.datetime.now() - timedelta(4)
        dt4 = datetime.datetime.now()
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?limit=10&startdate={dt1}&enddate={dt2}')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        assert(response_info["count"] >= 1)
        # note api_key is required, but already in headers
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?limit=10&startdate={dt3}&enddate={dt4}')
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
        print (f"Watched: Admin Report Query Complete. Asc Sort.  Time={time.time() - ts}")
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        print (f'Count Retrieved: {response_info["count"]}')
        print (f'Fullcount Retrieved: {response_info["fullCount"]}')
        if use_server == 5:
            assert(response_info["count"] >= 50000)
        else:
            assert(response_info["count"] >= 100)
            
        #  try descending (these now 2021-01-03 use different views to optimize the query using USE INDEX ( `fk_last_update` ) and built in orderby needed for query optiimization )
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?startdate={dt}&limit=100000&offset=0&download=false&sortorder=desc')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        print (f"Watched: Admin Report Query Complete. Desc Sort. Time={time.time() - ts}")
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        print (f'Count Retrieved: {response_info["count"]}')
        print (f'Fullcount Retrieved: {response_info["fullCount"]}')
        if use_server == 5:
            assert(response_info["count"] >= 50000)
        else:
            assert(response_info["count"] >= 100)

    def test07_session_log_report_dateformats(self):
        # note api_key is required, but already in headers
        import datetime
        from datetime import date, timedelta
        dt1 = datetime.datetime.now() - timedelta(10)
        dt2 = datetime.datetime.now() - timedelta(7)
        dt3 = datetime.datetime.now() - timedelta(days=10, hours=6)
        df1 = dt1.strftime("%Y-%m-%d")
        print (df1)
        df1b = dt1.strftime("%Y%m%d")
        print (df1b)
        df2 = dt2.strftime("%Y-%m-%d")
        print (df2)
        df3 = dt3.strftime("%Y-%m-%d %H:%M:%S")
        print (df3)
        df4 = dt3.strftime("%Y%m%d%H%M%S")
        print (df4)

        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?limit=10&startdate={df1}&enddate={df2}')
        print (full_URL)
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        assert(response_info["count"] >= 1)

        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?limit=10&startdate={df1}&enddate={df3}')
        print (full_URL)
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        assert(response_info["count"] >= 1)

        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?limit=10&startdate={df1}&enddate={df4}')
        print (full_URL)
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        assert(response_info["count"] >= 1)

        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?limit=10&startdate={df1b}&enddate={df4}')
        print (full_URL)
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        assert(response_info["count"] >= 1)

    def test08_session_log_report_dateformats_not_logged_in(self):
        # note api_key is required, but already in headers
        import datetime
        from datetime import date, timedelta
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?limit=100&loggedinrecords=False&sort=ASC&getfullcount=True')
        print (full_URL)
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        assert(response_info["count"] >= 1)

        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?limit=10&loggedinrecords=False&sort=DESC')
        print (full_URL)
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        assert(response_info["count"] >= 1)           


if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")