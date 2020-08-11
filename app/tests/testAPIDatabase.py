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
# from localsecrets import TESTUSER, TESTPW, SECRET_KEY, ALGORITHM
# import jwt
# from datetime import datetime

from unitTestConfig import base_api, base_plus_endpoint_encoded
from main import app

client = TestClient(app)

class TestDatabaseSearch(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_v1_database_search_fulltext(self):
        response = client.get(base_api + '/v1/Database/Search/?fulltext1=phlebotomy&limit=5&sort')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] >= 2)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)
        response = client.get(base_api + '/v1/Database/Search/?title=psychoanalysis&journal=CPS&startyear=1990&endyear=1995&fulltext1="child%20abuse"&sort=citeCount&limit=10&offset=0')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 3)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)
       
    def test_v2_database_search_fulltext(self):
        response = client.get(base_api + '/v2/Database/Search/?title=psychoanalysis&sourcecode=CPS&startyear=1990-1993&fulltext1="child%20abuse"&sort=citeCount&limit=10&offset=0')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] >= 1)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)
        response = client.get(base_api + '/v2/Database/Search/?title=psychoanalysis&sourcecode=CPS&startyear=1990&endyear=1995&fulltext1="child%20abuse"&sort=citeCount&limit=10&offset=0')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 3)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)

    def test_v2_database_search_author(self):
        response = client.get(base_api + '/v2/Database/Search/?author=freud&sourcecode=IJP&startyear=1990-1993&limit=10&offset=0')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 1)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)
        response = client.get(base_api + '/v2/Database/Search/?author=freud&limit=10&offset=0')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['count'] == 10)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == False)

    def test_v2_database_search_synonyms(self):
        response = client.get(base_api + '/v2/Database/Search/?sourcecode=BAP&fulltext1=text:bisexuality&sort=citeCount&limit=10&offset=0')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 14)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == False)
        response = client.get(base_api + '/v2/Database/Search/?synonyms=true&sourcecode=BAP&fulltext1=text:bisexuality&sort=citeCount&limit=10&offset=0')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 78)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == False)

    def test_v2_database_search_citedcount(self):
        response = client.get(base_api + '/v2/Database/Search/?citecount=6%20TO%2010&sourcecode=IJP%20OR%20APA&startyear=1990&endyear=2010&paratext=theoretical%20underpinnings&sort=citeCount&limit=10&offset=0')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] >= 3)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)
       

    def test_2_pubs_authornames(self):
        """
        Get Author Pubs For Matching Author Names
        /v1​/Authors​/Publications​/{authorNamePartial}​/
        """
        response = client.get(base_api + '/v2/Authors/Publications/maslow, a.*/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['authorPubList']['responseInfo']['fullCount']} Count complete: {r['authorPubList']['responseInfo']['fullCountComplete']}")
        assert(r['authorPubList']['responseInfo']['fullCount'] == 3)
        
        # Doesn't return an error, returns 0 matches.
        response = client.get(base_api + '/v2/Authors/Publications/Flintstone, Fred.*/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json() 
        print (f"Count: {r['authorPubList']['responseInfo']['fullCount']} Count complete: {r['authorPubList']['responseInfo']['fullCountComplete']}")
        assert(r['authorPubList']['responseInfo']['fullCount'] == 0)
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")