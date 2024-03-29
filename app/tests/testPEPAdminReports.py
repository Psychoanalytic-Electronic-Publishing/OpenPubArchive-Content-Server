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

def save_report(response):
    content_disposition = response.headers['content-disposition']
    # Split the content disposition header on the `;` delimiter.
    content_disposition_parts = content_disposition.split(';')
    # Get the value of the `filename` parameter.
    filename = content_disposition_parts[1].split('=')[1]        
    attachment = response.content
    # Open a file to write the attachment to.
    with open(filename, 'wb') as f:
        # Write the attachment to the file.
        f.write(attachment)        

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
        dt2 = date.today() + timedelta(1)
        dt3 = datetime.datetime.now() - timedelta(4)
        dt4 = datetime.datetime.now() + timedelta(1)
        print (f"Dates dt1:{dt1} dt2:{dt2} dt3:{dt3} dt4:{dt4}")
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?limit=10&startdate={dt1}&enddate={dt2}')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        assert(response_info["count"] >= 0)
        # note api_key is required, but already in headers
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?limit=10&startdate={dt3}&enddate={dt4}')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        assert(response_info["count"] >= 0)
        assert(response_set[0]["row"]["return_status_code"] == 200) # to validate content is in record

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
        assert(response_set[0]["row"]["return_status_code"] == 200) # to validate content is in record

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
        assert response_set[0]["row"]["type"] in ["Document", "EPUB", "PDF"], response_set[0]["row"]["type"] 

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
        assert(response_set[0]["row"]["views"] >= 1)  # to validate content is in record

    def test04_user_searches_report(self):
        # note api_key is required, but already in headers
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?abstract=true&facetfields=art_year_int%2Cart_views_last12mos%2Cart_cited_5%2Cart_authors%2Cart_lang%2Cart_type%2Cart_sourcetype%2Cart_sourcetitleabbr%2Cglossary_group_terms%2Cart_kwds_str&facetlimit=15&facetmincount=1&formatrequested=XML&fulltext1=text%3A(%22anxiety+hysteria%22~25)&highlightlimit=5&limit=20&offset=0&sort=author&synonyms=false')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/User-Searches?limit=10')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        assert(response_info["count"] >= 1)
        assert(response_set[0]["row"]["return_status_code"] == 200)

    def test05_session_log_report_endpointid(self):
        # note api_key is required, but already in headers
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?limit=10&endpointidlist=7,41')
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
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?startdate={dt}&limit=100000&offset=0&download=false&sortorder=asc&getfullcount=True')
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
            assert(response_info["count"] >= 10)
            
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
            assert(response_info["count"] >= 10)

    def test07_session_log_report_dateformats(self):
        # note api_key is required, but already in headers
        import datetime
        from datetime import timedelta
        dt1 = datetime.datetime.now() - timedelta(30)
        dt2 = datetime.datetime.now() + timedelta(1)
        df1 = dt1.strftime("%Y-%m-%d")
        print (df1)
        df1a = dt1.strftime("%Y%m%d%H%M%S")
        print (df1a)
        df1b = dt1.strftime("%Y%m%d")
        print (df1b)
        df1c = dt1.strftime("%Y-%m-%d %H:%M:%S")
        print (df1c)
        df2 = dt2.strftime("%Y-%m-%d")
        print (df2)
        df2b = dt2.strftime("%Y%m%d%H%M%S")
        print (df2b)
        df2c = dt2.strftime("%Y-%m-%d %H:%M:%S")
        print (df2c)

        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?limit=10&startdate={df1}&enddate={df2}')
        print (full_URL)
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        print (response_info["count"])
        assert(response_info["count"] >= 1)

        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?limit=10&startdate={df1a}&enddate={df2b}')
        print (full_URL)
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        if (response_info["count"]) >= 1: # make sure there are hits, then try different formats together
            full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?limit=10&startdate={df1a}&enddate={df2c}')
            print (full_URL)
            response = requests.get(full_URL, headers=headers)
            assert(response.ok == True)
            # these don't get affected by the level.
            r = response.json()
            response_info = r["report"]["responseInfo"]
            response_set = r["report"]["responseSet"]
            print (response_info["count"])
            assert(response_info["count"] >= 1)

            full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?limit=10&startdate={df1c}&enddate={df2c}')
            print (full_URL)
            response = requests.get(full_URL, headers=headers)
            assert(response.ok == True)
            # these don't get affected by the level.
            r = response.json()
            response_info = r["report"]["responseInfo"]
            response_set = r["report"]["responseSet"]
            print (response_info["count"])
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

    def test09a_document_char_counts_report(self):
        # data return (non-download) version
        # note api_key is required, but already in headers
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Character-Count-Report?limit=100&offset=0&getfullcount=false&download=false')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        response_info = r["report"]["responseInfo"]
        response_set = r["report"]["responseSet"]
        assert(response_info["count"] >= 1)
        assert(response_set[0]["row"]["jrnlgrpname"] == 'ADPSA')  # to validate content is in record
        
    def test09_document_char_counts_report_download(self):
        # note api_key is required, but already in headers
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Character-Count-Report?getfullcount=false&download=true')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        content_disposition = response.headers['content-disposition']
        print (content_disposition)
        assert (content_disposition[0:10] == 'attachment')
        save_report(response)

    def test10_document_char_counts_details_report_download(self):
        # note api_key is required, but already in headers
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Character-Count-Details-Report?getfullcount=false&download=true&limit=10000')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        content_disposition = response.headers['content-disposition']
        print (content_disposition)
        assert (content_disposition[0:10] == 'attachment')
        save_report(response)

    def test11_document_char_counts_book_details_report_download(self):
        # note api_key is required, but already in headers
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Character-Count-Details-Book-Report?getfullcount=false&download=true&limit=10000')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        content_disposition = response.headers['content-disposition']
        print (content_disposition)
        assert (content_disposition[0:10] == 'attachment')
        save_report(response)
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")