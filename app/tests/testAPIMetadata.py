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

import unitTestConfig
from unitTestConfig import base_api, base_plus_endpoint_encoded
from main import app

client = TestClient(app)

class TestMetadata(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_1_meta_contents_for_source(self):
        """
        Journal Content Lists for a source
        /v1/Metadata/Contents/{SourceCode}/
        """
        response = client.get(base_api + '/v1/Metadata/Contents/BJP/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['documentList']['responseInfo']['fullCount'] >= 2634)
        # print ("test_metadata_journals complete.")
       
    def test_2_meta_contents_source_volume(self):
        """
        Journal Content Lists for a source and vol
        ​/v1​/Metadata​/Contents​/{SourceCode}​/{SourceVolume}​/
        """
        response = client.get(base_api + '/v1/Metadata/Contents/BJP/1/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['documentList']['responseInfo']['fullCount'] == 49)

        response = client.get(base_api + '/v1/Metadata/Contents/IJP/1/?limit=1')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['documentList']['responseSet'][0]['documentID'] == 'IJP.001.0001A')
        assert(r['documentList']['responseSet'][0]['pgRg'] == '1-2')

    def test_3_meta_video_sources(self):
        """
        List of video sources (not individual videos, EXCEPT if specified by parameter)
        /v1/Metadata/Videos/
        """
        response = client.get(base_api + '/v1/Metadata/Videos/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseInfo']['fullCount'] >= unitTestConfig.VIDEOSOURCECOUNT)

        # try with src code parameter
        response = client.get(base_api + '/v1/Metadata/Videos/?SourceCode=AFCVS&limit=1')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseSet'][0]['title'] == 'Anna Freud Center Video Collection')

    def test_4_meta_journal_sources(self):
        """
        List of journal sources (not individual journals)
        /v1/Metadata/Journals/

        """
        response = client.get(base_api + '/v1/Metadata/Journals/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseInfo']['fullCount'] >= unitTestConfig.JOURNALCOUNT)

        response = client.get(base_api + '/v1/Metadata/Journals/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseInfo']['fullCount'] >= unitTestConfig.JOURNALCOUNT)

        # try with src code parameter
        response = client.get(base_api + '/v1/Metadata/Journals/?journal=BJP&limit=1')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseSet'][0]['title'] == 'British Journal of Psychotherapy')

    def test_5_meta_volumes(self):
        """
        List of volumes for a source
        /v1/Metadata/Volumes/{SourceCode}/
        """
        response = client.get(base_api + '/v1/Metadata/Volumes/IJPSP/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        # Expect:
        # {'volumeList': 
        #     {'responseInfo': {'count': 17, 'limit': 100, 'offset': 0, 'fullCount': 17, 'fullCountComplete': True,  
        #                       'listType':'volumelist', 
        #                       'request': 'http://127.0.0.1:9100/v1/Metadata/Volumes/IJPSP/', 'timeStamp': '2019-10-28T04:44:22Z'}, 
        #      'responseSet': [{'PEPCode': 'IJPSP', 'vol': '1', 'year': '2006'}, 
        #                      {'PEPCode': 'IJPSP', 'vol': '2', 'year': '2007'}, 
        #                      ...
        #                      {'PEPCode': 'IJPSP', 'vol': '11', 'year': '2016'}, 
        #                      {'PEPCode': 'IJPSP', 'vol': '11D', 'year': '2016'}]}}
        assert(r['volumeList']['responseInfo']['fullCount'] == 17)
        # try an error
        response = client.get(base_api + '/v1/Metadata/Volumes/IJPNOT/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == False)
        # test return
        r = response.json()

    def test_6_meta_book_names(self):
        """
        List of book names
        /v1/Metadata/Books/
        """
        response = client.get(base_api + '/v1/Metadata/Books/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseInfo']['fullCount'] >= unitTestConfig.BOOKCOUNT)

    def test_7_meta_sourcenames(self):
        """
        List of names for a specific source
        /v1/Metadata/{SourceType}/{SourceCode}/
        """
        response = client.get(base_api + '/v1/Metadata/Journals/IJPSP/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        # Expect: {'sourceInfo': 
        #           {'responseInfo': {'count': 1, 'limit': 200, 'offset': 0, 'fullCount': 1, 'fullCountComplete': True, 'listLabel': 'journal List', 
        #                             'listType': 'sourceinfolist', 'scopeQuery': '*', 'request': 'http://127.0.0.1:9100/v1/Metadata/Journals/IJPSP/', 
        #                             'timeStamp': '2019-10-28T12:56:12Z'}, 
        #            'responseSet': [{'sourceType': 'journal', 'PEPCode': 'IJPSP', 'bookCode': None, 'documentID': None, 
        #                                           'bannerURL': 'http://development.org/images/bannerIJPSP.logo.gif', 
        #                                           'displayTitle': 'International Journal of Psychoanalytic Self Psychology', 
        #                                           'srcTitle': 'International Journal of Psychoanalytic Self Psychology', 
        #                                           'title': 'International Journal of Psychoanalytic Self Psychology', 
        #                                           'authors': None, 'pub_year': None, 'abbrev': 'Int. J. Psychoanal. Self Psychol.', 'ISSN': '1555-1024', 'language': 'EN', 
        #                                           'yearFirst': '2006', 'yearLast': '2016', 'embargoYears': '3'}]}}
        assert(r['sourceInfo']['responseInfo']['fullCount'] == 1)
        assert(r['sourceInfo']['responseSet'][0]['displayTitle'] == 'International Journal of Psychoanalytic Self Psychology')
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")