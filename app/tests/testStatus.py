#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

import sys
sys.path.append('../libs')
sys.path.append('../config')
import unittest
import requests
from requests.utils import requote_uri
import urllib

# base_api = "http://stage.pep.gvpi.net/api"
base_api = "http://127.0.0.1:9100"

def base_plus_endpoint_encoded(endpoint):
    # ret_val = baseAPI + urllib.parse.quote_plus(endpoint, safe="/")
    ret_val = base_api + endpoint
    return ret_val

class TestAPIResponses(unittest.TestCase):
    def test_server_status(self):
        # Send a request to the API server and store the response.
        response = requests.get(base_api + '/v2/Admin/Status/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
        assert(r["text_server_ok"] == True)
        assert(r["db_server_ok"] == True)

    def test_get_login_good(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v1/Login/?grant_type=password&username=gvpi&password=fish88')
        response = requests.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        print (response.ok)
        assert(response.ok == True)
        full_URL = base_plus_endpoint_encoded('/v1/Logout/')
        response = requests.get(full_URL, headers={"content-type":"application/json"})
        # Confirm that the request-response cycle completed successfully.
        print (response.ok)
        assert(response.ok == False)

    def test_who_am_i(self):
        full_URL = base_plus_endpoint_encoded('/v1/Login/?grant_type=password&username=gvpi&password=fish88')
        response = requests.get(full_URL)
        # Confirm that the request-response cycle completed successfully.
        print (response.ok)
        assert(response.ok == True)
        r = response.json()
        # Send a request to the API server and store the response.
        response2 = requests.get(base_api + '/v2/Admin/WhoAmI/')
        # Confirm that the request-response cycle completed successfully.
        assert(response2.ok == True)
        r2 = response2.json()
        assert(r2["opasSessionID"] is not None)

    def test_get_most_cited(self):
        # Send a request to the API server and store the response.
        response = requests.get(base_api + '/v1/Database/MostCited/?period=5')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_get_license_status(self):
        # Send a request to the API server and store the response.
        response = requests.get(base_api + '/v1/License/Status/Login/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_get_login_bad(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v1/Login/?grant_type=password&username=xyz&password=bull')
        response = requests.get(full_URL)
        assert(response.ok == False)

    def test_search_mixedcase(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=Tuckett')
        response = requests.get(full_URL)
        r = response.json()
        print (r)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_search_lowercase(self):
        full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=tuckett')
        response = requests.get(full_URL)
        r = response.json()
        print (r)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_search_journalcode(self):
        full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=tuckett&journal=IJP')
        response = requests.get(full_URL)
        r = response.json()
        print (r)
        assert(response.ok == True)

    def test_search_author_and_journalcode(self):
        full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=tuckett&journal=IJP&text=economics')
        response = requests.get(full_URL)
        r = response.json()
        print (r)
        assert(response.ok == True)

    def test_search_author_and_journalcode_and_text(self):
        full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=tuckett&journal=IJP&text=economics&citecount=3')
        response = requests.get(full_URL)
        r = response.json()
        print (r)
        assert(response.ok == True)

    def test_search_author_and_journalcode_and_text_and_citecount(self):
        full_URL = base_plus_endpoint_encoded('/v1/Database/Search/?author=tuckett&journal=IJP&text=economics&citecount=3')
        response = requests.get(full_URL)
        r = response.json()
        print (r)
        assert(response.ok == True)

    def test_opasdb(self):
        import secrets
        from opasCentralDBLib import opasCentralDB, API_AUTHORS_INDEX
        ocd = opasCentralDB()
        random_session_id = secrets.token_urlsafe(16)
        success, session_info = ocd.save_session(session_id=random_session_id)
        assert(session_info.authenticated == False)
        session_info = ocd.get_session_from_db(session_id=random_session_id)
        assert(session_info.authenticated == False)
        status = ocd.record_session_endpoint(session_info=session_info, api_endpoint_id=API_AUTHORS_INDEX, document_id="IJP.001.0001A", status_message="Testing")
        assert(status == 1)
        ocd.update_document_view_count("IJP.001.0001A")
        status = ocd.end_session(session_info.session_id)
        assert(status == True)

    def test_opasdb_getsources(self):
        from opasCentralDBLib import opasCentralDB
        ocd = opasCentralDB()
        sources = ocd.get_sources()
        assert(sources[0] > 100)
        sources = ocd.get_sources(source="IJP")
        assert(sources[0] == 1)
        sources = ocd.get_sources(source_type="journal")
        assert(sources[0] > 70)
       
        
if __name__ == '__main__':
    unittest.main()    