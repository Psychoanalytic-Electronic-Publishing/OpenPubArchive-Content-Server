#!/usr/bin/env python
# -*- coding: utf-8 -*-

from localsecrets import PADS_TEST_ID, PADS_TEST_PW

import unittest
import requests
import opasConfig
import sys
from datetime import datetime

from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, test_login

# Login!
sessID, headers, session_info = test_login()


class TestAPIStatus(unittest.TestCase):
    """
    Tests for status endpoints 
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    Checks the API status
    Checks that all database segments have been loaded (all other tests depend on this)
        # has archive been loaded
        # has current been loaded
        # has special been loaded
        # has free been loaded
        # has offsite been loaded
        # have stats been run
    """   

    def test_v2_api_status(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Api/Status/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    # 
    # Though not testing the API per se, the following ensures in this early test whether all the components of the database have been fully loaded.
    # 
    def test_v2_loaded_all_database_segments(self):
        # test (before going through all the other tests, that critical build aspects, including stats have been run)
        
        # has archive been loaded
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/IJP.016.0096A/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        print ("Checking PEPArchive")
        assert(response_info["count"] == 1)
        print ("OK")
        
        # has current been loaded
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/IJP.103.0046A/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        print ("Checking PEPCurrent")
        assert(response_info["count"] == 1)
        print ("OK")
        
        # have pep free docs been loaded?
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/PEPGRANTVS.001.0004A.xml/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        print ("Checking PEPFree")
        assert(response_info["count"] == 1)
        print ("OK")

        # has special been loaded
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/IJPOPEN.003.0004A/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        print ("Checking IJPOpen")
        assert(response_info["count"] == 1)
        print ("OK")

        # have pep offsite docs been loaded?        
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/OAJPSI.116.0322A/')
        print ("Checking offsite docs")
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        print ("OK")
        
        # has the glossary been loaded?
        full_URL = base_plus_endpoint_encoded('/v2/Database/Glossary/Search/?fulltext1=consciousness')
        print ("Checking the glossary")
        # Confirm that the request-response cycle completed successfully.
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] >= 21)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == False)

        # have stats been run?
        print (f"Running: {sys._getframe(  ).f_code.co_name} at {datetime.now()}")
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print ("Checking if stats have been run")
        # print (r)
        print (f"Count: {r['documentList']['responseInfo']['count']}")
        print (f"Limit: {r['documentList']['responseInfo']['limit']}")
        print (f"ReturnedData: {r['documentList']['responseSet'][0]['stat']['art_cited_5']}")
        assert(r['documentList']['responseSet'][0]['stat']['art_cited_5'] >= 15)       
        print ("OK")

       
if __name__ == '__main__':
    unittest.main()    