#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Updates:
#  2020-04-06 - Testing tightened to be exact.
#  2020-04-30 - Added test 8x to test source info retrieval with wildcards

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
import unitTestConfig
from unitTestConfig import base_api, base_plus_endpoint_encoded
import opasCentralDBLib
from main import app

client = TestClient(app)

class TestMetadata(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_0_meta_volumes_db(self):
        # New method to bring back lists of volumes, including all, or all of one type, or all of one type and code.
        ocd = opasCentralDBLib.opasCentralDB()
        count, vols = ocd.get_volumes(source_code=None, source_type=None)
        print (f"DB All Vols Count {count}")
        assert(count >= unitTestConfig.VOL_COUNT_ALL_VOLUMES)
        
        # ---------------------------------------------------------------------------------------
        source_type = "book"
        source_code = None       
        count, vols = ocd.get_volumes(source_code=source_code, source_type=source_type)
        print (f"DB {source_type} Vol Count {count}")
        assert(count >= unitTestConfig.VOL_COUNT_ALL_BOOKS)
        # ---------------------------------------------------------------------------------------
        source_type = "book"
        source_code = "GW"
        count, vols = ocd.get_volumes(source_code=source_code, source_type=source_type)
        print (f"DB {source_type} {source_code} Vol Count {count}")
        assert(count >= unitTestConfig.VOL_COUNT_GW)
        # ---------------------------------------------------------------------------------------
        source_type = "journal"
        source_code = None
        count, vols = ocd.get_volumes(source_code=source_code, source_type=source_type)
        print (f"DB {source_type} Vol Count {count}")
        assert(count >= unitTestConfig.VOL_COUNT_ALL_JOURNALS)
        # ---------------------------------------------------------------------------------------
        source_type = "journal"
        source_code = "IJPSP"
        count, vols = ocd.get_volumes(source_code=source_code, source_type=source_type)
        print (f"DB {source_type} {source_code} Vol Count {count}")
        assert(count == unitTestConfig.VOL_COUNT_IJPSP)
        # ---------------------------------------------------------------------------------------
        source_type = "videostream"
        source_code = None
        count, vols = ocd.get_volumes(source_code=source_code, source_type=source_type)
        print (f"DB {source_type} Vol Count {count}")
        assert(count >= unitTestConfig.VOL_COUNT_VIDEOS)
        # ---------------------------------------------------------------------------------------
        source_type = "videostream"
        source_code = "PEPVS"
        count, vols = ocd.get_volumes(source_code=source_code, source_type=source_type)
        print (f"DB {source_type} {source_code} Vol Count {count}")
        assert(count >= unitTestConfig.VOL_COUNT_VIDEOS_PEPVS)
        
    def test_0_meta_volumes_api(self):
        """
        Journal Volumes Lists for a source
        ​/v2​/Metadata​/Volumes​/
        Arguments: sourcetype and sourcecode used.
        
        """
        # ---------------------------------------------------------------------------------------
        # Version 1 style, for backwards compat. only. sourcecode REQUIRED.  
        # ---------------------------------------------------------------------------------------
        response = client.get(base_api + '/v1/Metadata/Volumes/IJPSP') 
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        print (f"IJPSP Vol Count: {r['volumeList']['responseInfo']['fullCount']}")
        assert(r['volumeList']['responseInfo']['fullCount'] == unitTestConfig.VOL_COUNT_IJPSP) 
        # ---------------------------------------------------------------------------------------
        # Version 2 style, better, including sourcetype support
        # ---------------------------------------------------------------------------------------
        response = client.get(base_api + '/v2/Metadata/Volumes/?sourcetype=book') #  all books
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        print (f"Book Count: {r['volumeList']['responseInfo']['fullCount']}")
        assert(r['volumeList']['responseInfo']['fullCount'] == unitTestConfig.VOL_COUNT_ALL_BOOKS) 
        # ---------------------------------------------------------------------------------------
        response = client.get(base_api + '/v2/Metadata/Volumes/?sourcetype=journal') #  all journals
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['volumeList']['responseInfo']['fullCount'] >= unitTestConfig.VOL_COUNT_ALL_JOURNALS) 
        # ---------------------------------------------------------------------------------------
        response = client.get(base_api + '/v2/Metadata/Volumes/?sourcetype=videostream') #  all videos
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['volumeList']['responseInfo']['fullCount'] == unitTestConfig.VOL_COUNT_VIDEOS)
        # ---------------------------------------------------------------------------------------
        response = client.get(base_api + '/v2/Metadata/Volumes/?sourcecode=ZBK')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['volumeList']['responseInfo']['fullCount'] == unitTestConfig.VOL_COUNT_ZBK) 
        # ---------------------------------------------------------------------------------------
        response = client.get(base_api + '/v2/Metadata/Volumes/?sourcecode=IJPSP')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['volumeList']['responseInfo']['fullCount'] == unitTestConfig.VOL_COUNT_IJPSP) # 11
        # ---------------------------------------------------------------------------------------
        response = client.get(base_api + '/v2/Metadata/Volumes/?sourcecode=GW')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['volumeList']['responseInfo']['fullCount'] == unitTestConfig.VOL_COUNT_GW) # 18 vols of GW
        # ---------------------------------------------------------------------------------------
        response = client.get(base_api + '/v2/Metadata/Volumes/?sourcecode=SE')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['volumeList']['responseInfo']['fullCount'] == unitTestConfig.VOL_COUNT_SE) # 18 vols of SE
        # ---------------------------------------------------------------------------------------
        response = client.get(base_api + '/v2/Metadata/Volumes/?sourcecode=IPL')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['volumeList']['responseInfo']['fullCount'] == unitTestConfig.VOL_COUNT_IPL) # 22 vols of IPL
        # ---------------------------------------------------------------------------------------
        # try an error
        response = client.get(base_api + '/v2/Metadata/Volumes/?sourcecode=IJPNOT')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == False)
        r = response.json()
        assert(r["detail"] == "Failure: Bad SourceCode IJPNOT")
        # ---------------------------------------------------------------------------------------
        # all journals and videos 
        # (books not included, ***perhaps this option should not exist since it seems inconsistent ***.)
        response = client.get(base_api + '/v2/Metadata/Volumes/') 
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['volumeList']['responseInfo']['fullCount'] >= unitTestConfig.VOL_COUNT_ALL_VOLUMES) # count of journal and video volumes
        

    def test_1_meta_contents_for_source(self):
        """
        Journal Content Lists for a source
        /v1/Metadata/Contents/{SourceCode}/
        """
        response = client.get(base_api + '/v2/Metadata/Contents/BJP/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        print(r['documentList']['responseInfo']['fullCount']) # 2735
        assert(r['documentList']['responseInfo']['fullCount'] == unitTestConfig.ARTICLE_COUNT_BJP)
        # print ("test_metadata_journals complete.")
       
    def test_2_meta_contents_source_volume(self):
        """
        Journal Content Lists for a source and vol
        ​/v1​/Metadata​/Contents​/{SourceCode}​/{SourceVolume}​/
        """
        response = client.get(base_api + '/v2/Metadata/Contents/BJP/1/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['documentList']['responseInfo']['fullCount'] == unitTestConfig.ARTICLE_COUNT_VOL1_BJP)

        response = client.get(base_api + '/v2/Metadata/Contents/IJP/1/?limit=1')
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
        print(r['sourceInfo']['responseInfo']['fullCount']) 
        assert(r['sourceInfo']['responseInfo']['fullCount'] == unitTestConfig.VIDEOSOURCECOUNT)

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
        print (f"Journal Count: {r['sourceInfo']['responseInfo']['fullCount']}")
        assert(r['sourceInfo']['responseInfo']['fullCount'] >= unitTestConfig.JOURNALCOUNT)

        # try with src code parameter
        response = client.get(base_api + '/v1/Metadata/Journals/?journal=BJP&limit=1')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        print (f"Journal title: {r['sourceInfo']['responseSet'][0]['title']}")
        assert(r['sourceInfo']['responseSet'][0]['title'] == 'British Journal of Psychotherapy')

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
        print (f"Book Count: {r['sourceInfo']['responseInfo']['fullCount']}")
        assert(r['sourceInfo']['responseInfo']['fullCount'] >= unitTestConfig.BOOKCOUNT)

    def test_7_meta_sourcenames(self):
        """
        List of names for a specific source
        /v1/Metadata/{SourceType}/{SourceCode}/
        """
        response = client.get(base_api + '/v2/Metadata/Journals/IJPSP/')
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
        
    def test_8_meta_all_sources(self):
        """
        List of names for a specific source
        /v1/Metadata/{SourceType}/{SourceCode}/
        """
        response = client.get(base_api + '/v2/Metadata/*/*/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseInfo']['count'] == 193)

    def test_8b_meta_all_sources(self):
        """
        List of names for a specific source
        /v1/Metadata/{SourceType}/{SourceCode}/
        """
        response = client.get(base_api + '/v2/Metadata/*/IJP/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseInfo']['count'] == 1)
    
    def test_8b2_meta_all_sources(self):
        """
        List of names for a specific source, a book, but not spec'd as book
        /v1/Metadata/{SourceType}/{SourceCode}/
        """
        # get all the PEP Codes
        response = client.get(base_api + '/v2/Metadata/*/*/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        pep_codes = []
        for n in r['sourceInfo']['responseSet']:
            pep_codes.append(n['PEPCode'])
        # Now test to make sure they can be read (if there's missing data in the product table, can cause error)
        for n in pep_codes:
            response = client.get(base_api + f'/v2/Metadata/*/{n}/')
            # Confirm that the request-response cycle completed successfully.
            assert(response.ok == True)
            # test return
            r = response.json()
            assert(r['sourceInfo']['responseInfo']['count'] == 1)

    def test_8c_meta_all_sources_nonsense(self):
        """
        List of names for a source that doesn't match the type
        /v1/Metadata/{SourceType}/{SourceCode}/
        """
        response = client.get(base_api + '/v2/Metadata/Books/IJP/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseInfo']['count'] == 0)
    def test_8d_meta_all_sourcetype_nonsense(self):
        """
        List of names for a source for an unknown type
        /v1/Metadata/{SourceType}/{SourceCode}/
        
        Currently: just changes to Journal, maybe should change to "*"
        """
        response = client.get(base_api + '/v2/Metadata/Garbage/*/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseInfo']['count'] != 0)
        response = client.get(base_api + '/v2/Metadata/Garbage/IJP/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseInfo']['count'] == 1)
        response = client.get(base_api + '/v2/Metadata/Garbage/GW/')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseInfo']['count'] == 1)
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")