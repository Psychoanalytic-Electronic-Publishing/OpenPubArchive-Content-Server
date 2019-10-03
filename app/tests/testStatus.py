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

baseAPI = "http://stage.pep.gvpi.net/api"
baseAPI = "http://127.0.0.1:8000"

def basePlusEndpointEncoded(endpoint):
    #retVal = baseAPI + urllib.parse.quote_plus(endpoint, safe="/")
    retVal = baseAPI + endpoint
    return retVal

class TestAPIResponses(unittest.TestCase):
    def test_server_status(self):
        # Send a request to the API server and store the response.
        response = requests.get(baseAPI + '/v1/Status/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
        assert(r["text_server_ok"] == True)
        assert(r["db_server_ok"] == True)

    def test_who_am_i(self):
        # Send a request to the API server and store the response.
        response = requests.get(baseAPI + '/v1/WhoAmI/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_get_most_cited(self):
        # Send a request to the API server and store the response.
        response = requests.get(baseAPI + '/v1/Database/MostCited/?period=5')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_get_license_status(self):
        # Send a request to the API server and store the response.
        response = requests.get(baseAPI + '/v1/License/Status/Login/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_get_login_good(self):
        # Send a request to the API server and store the response.
        fullURL = basePlusEndpointEncoded('/v1/Login/?grant_type=password&username=gvpi&password=fish88')
        response = requests.get(fullURL)
        # Confirm that the request-response cycle completed successfully.
        print (response.ok)
        assert(response.ok == True)
        fullURL = basePlusEndpointEncoded('/v1/Logout/')
        response = requests.get(fullURL, headers={"content-type":"application/json"})
        # Confirm that the request-response cycle completed successfully.
        print (response.ok)
        assert(response.ok == False)

    def test_get_login_bad(self):
        # Send a request to the API server and store the response.
        fullURL = basePlusEndpointEncoded('/v1/Login/?grant_type=password&username=xyz&password=bull')
        response = requests.get(fullURL)
        assert(response.ok == False)

    def test_search_mixedcase(self):
        # Send a request to the API server and store the response.
        fullURL = basePlusEndpointEncoded('/v1/Database/Search/?author=Tuckett')
        response = requests.get(fullURL)
        r = response.json()
        print (r)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)


    def test_search_lowercase(self):
        fullURL = basePlusEndpointEncoded('/v1/Database/Search/?author=tuckett')
        response = requests.get(fullURL)
        r = response.json()
        print (r)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_search_journalcode(self):
        fullURL = basePlusEndpointEncoded('/v1/Database/Search/?author=tuckett&journal=IJP')
        response = requests.get(fullURL)
        r = response.json()
        print (r)
        assert(response.ok == True)

    def test_search_author_and_journalcode(self):
        fullURL = basePlusEndpointEncoded('/v1/Database/Search/?author=tuckett&journal=IJP&text=economics')
        response = requests.get(fullURL)
        r = response.json()
        print (r)
        assert(response.ok == True)

    def test_search_author_and_journalcode_and_text(self):
        fullURL = basePlusEndpointEncoded('/v1/Database/Search/?author=tuckett&journal=IJP&text=economics&citecount=3')
        response = requests.get(fullURL)
        r = response.json()
        print (r)
        assert(response.ok == True)

    def test_search_author_and_journalcode_and_text_and_citecount(self):
        fullURL = basePlusEndpointEncoded('/v1/Database/Search/?author=tuckett&journal=IJP&text=economics&citecount=3')
        response = requests.get(fullURL)
        r = response.json()
        print (r)
        assert(response.ok == True)

    def testOpasDB(self):
        import secrets
        from opasCentralDBLib import opasCentralDB, API_AUTHORS_INDEX
        ocd = opasCentralDB()
        randomSessionID = secrets.token_urlsafe(16)
        success, sessionInfo = ocd.saveSession(sessionID=randomSessionID)
        assert(sessionInfo.authenticated == False)
        sessionInfo = ocd.getSessionFromDB(sessionID=randomSessionID)
        assert(sessionInfo.authenticated == False)
        status = ocd.recordSessionEndpoint(sessionID=randomSessionID, apiEndpointID=API_AUTHORS_INDEX, documentID="IJP.001.0001A", statusMessage="Testing")
        assert(status == 1)
        ocd.updateDocumentViewCount("IJP.001.0001A")
        status = ocd.endSession(sessionInfo.session_id)
        assert(status == True)

    def testOpasDB_getSources(self):
        from opasCentralDBLib import opasCentralDB
        ocd = opasCentralDB()
        sources = ocd.getSources()
        assert(len(sources)>10)
        source =  ocd.getSources(source="IJP")
        assert(len(source)==1)
        sources2 =  ocd.getSources(sourceType="journal")
        assert(len(sources2)>10)
        
        
        
        
if __name__ == '__main__':
    unittest.main()    