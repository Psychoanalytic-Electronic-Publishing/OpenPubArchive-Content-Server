#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Updates:
#  2020-04-06 - Testing tightened to be exact.
#  2020-04-30 - Added test 8x to test source info retrieval with wildcards

import unittest
import requests
import unitTestConfig
from unitTestConfig import base_plus_endpoint_encoded, headers

# import opasCentralDBLib

class TestMetadata(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    """   

    #def test_0_meta_volumes_db(self):
        ## New method to bring back lists of volumes, including all, or all of one type, or all of one type and code.
        #ocd = opasCentralDBLib.opasCentralDB()
        #count, vols = ocd.get_volumes(source_code=None, source_type=None)
        #print (f"DB All Vols Count {count}")
        #assert(count >= unitTestConfig.VOL_COUNT_ALL_VOLUMES)
        
        ## ---------------------------------------------------------------------------------------
        #source_type = "book"
        #source_code = None       
        #count, vols = ocd.get_volumes(source_code=source_code, source_type=source_type)
        #print (f"DB {source_type} Vol Count {count}")
        #assert(count >= unitTestConfig.VOL_COUNT_ALL_BOOKS)
        ## ---------------------------------------------------------------------------------------
        #source_type = "book"
        #source_code = "GW"
        #count, vols = ocd.get_volumes(source_code=source_code, source_type=source_type)
        #print (f"DB {source_type} {source_code} Vol Count {count}")
        #assert(count >= unitTestConfig.VOL_COUNT_GW)
        ## ---------------------------------------------------------------------------------------
        #source_type = "journal"
        #source_code = None
        #count, vols = ocd.get_volumes(source_code=source_code, source_type=source_type)
        #print (f"DB {source_type} Vol Count {count}")
        #assert(count >= unitTestConfig.VOL_COUNT_ALL_JOURNALS)
        ## ---------------------------------------------------------------------------------------
        #source_type = "journal"
        #source_code = "IJPSP"
        #count, vols = ocd.get_volumes(source_code=source_code, source_type=source_type)
        #print (f"DB {source_type} {source_code} Vol Count {count}")
        #assert(count == unitTestConfig.VOL_COUNT_IJPSP)
        ## ---------------------------------------------------------------------------------------
        #source_type = "videostream"
        #source_code = None
        #count, vols = ocd.get_volumes(source_code=source_code, source_type=source_type)
        #print (f"DB {source_type} Vol Count {count}")
        #assert(count >= unitTestConfig.VOL_COUNT_VIDEOS)
        ## ---------------------------------------------------------------------------------------
        #source_type = "videostream"
        #source_code = "PEPVS"
        #count, vols = ocd.get_volumes(source_code=source_code, source_type=source_type)
        #print (f"DB {source_type} {source_code} Vol Count {count}")
        #assert(count >= unitTestConfig.VOL_COUNT_VIDEOS_PEPVS)
        
    def test_0_meta_volumes_api_book(self): 
        # ---------------------------------------------------------------------------------------
        # Version 2 style, better, including sourcetype support
        # ---------------------------------------------------------------------------------------
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Volumes/?sourcetype=book') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        print (f"Book Count: {r['volumeList']['responseInfo']['fullCount']}")
        assert(r['volumeList']['responseInfo']['fullCount'] >= unitTestConfig.VOL_COUNT_ALL_BOOKS) 

    def test_0_meta_volumes_api_journal(self): 
        # ---------------------------------------------------------------------------------------
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Volumes/?sourcetype=journal') #  all journals
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        print (f"Journal Vol Count: {r['volumeList']['responseInfo']['fullCount']}")
        assert(r['volumeList']['responseInfo']['fullCount'] >= unitTestConfig.VOL_COUNT_ALL_JOURNALS) 

    def test_0_meta_volumes_api_videostream(self): 
        # ---------------------------------------------------------------------------------------
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Volumes/?sourcetype=videostream') #  all videos
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        print (f"Video Source Count: {r['volumeList']['responseInfo']['fullCount']}")
        assert(r['volumeList']['responseInfo']['fullCount'] == unitTestConfig.VOL_COUNT_VIDEOS)

    def test_0_meta_volumes_api_ZBK(self): 
        # ---------------------------------------------------------------------------------------
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Volumes/?sourcecode=ZBK')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        print (f"ZBK Volume Count: {r['volumeList']['responseInfo']['fullCount']}")
        assert(r['volumeList']['responseInfo']['fullCount'] >= unitTestConfig.VOL_COUNT_ZBK) 

    def test_0_meta_volumes_api_IJPSP(self): 
        # ---------------------------------------------------------------------------------------
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Volumes/?sourcecode=IJPSP')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['volumeList']['responseInfo']['fullCount'] == unitTestConfig.VOL_COUNT_IJPSP) # 11

    def test_0_meta_volumes_api_GW(self): 
        # ---------------------------------------------------------------------------------------
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Volumes/?sourcecode=GW')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        print (f"GW Volume Count: {r['volumeList']['responseInfo']['fullCount']}")
        assert(r['volumeList']['responseInfo']['fullCount'] == unitTestConfig.VOL_COUNT_GW) # 18 vols of GW

    def test_0_meta_volumes_api_SE(self): 
        # ---------------------------------------------------------------------------------------
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Volumes/?sourcecode=SE')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        print (f"SE Volume Count: {r['volumeList']['responseInfo']['fullCount']}")
        assert(r['volumeList']['responseInfo']['fullCount'] == unitTestConfig.VOL_COUNT_SE + 1) # 24 vols of SE + new overview vol 0

    def test_0_meta_volumes_api_IPL(self): 
        # ---------------------------------------------------------------------------------------
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Volumes/?sourcecode=IPL')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        print (f"IPL Volume Count: {r['volumeList']['responseInfo']['fullCount']}")
        assert(r['volumeList']['responseInfo']['fullCount'] == unitTestConfig.VOL_COUNT_IPL) # 22 vols of IPL

    def test_0_meta_volumes_api_NLP(self): 
        # ---------------------------------------------------------------------------------------
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Volumes/?sourcecode=NLP')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        print (f"IPL Volume Count: {r['volumeList']['responseInfo']['fullCount']}")
        assert(r['volumeList']['responseInfo']['fullCount'] == unitTestConfig.VOL_COUNT_NLP) # 22 vols of IPL


    def test_0_meta_volumes_api_error(self): 
        # ---------------------------------------------------------------------------------------
        # try an error
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Volumes/?sourcecode=IJPNOT')
        response = requests.get(full_URL, headers=headers)
        assert(response.status_code == 400)
        r = response.json()
        assert(r["detail"] == "Failure: Bad SourceCode IJPNOT")

    def test_0_meta_volumes_api_ALL(self): 
        # ---------------------------------------------------------------------------------------
        # all journals and videos 
        # (books not included, ***perhaps this option should not exist since it seems inconsistent ***.)
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Volumes/') 
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['volumeList']['responseInfo']['fullCount'] >= unitTestConfig.VOL_COUNT_ALL_VOLUMES) # count of journal and video volumes
        

    def test_1_meta_contents_for_source(self):
        """
        Journal Content Lists for a source
        /v2/Metadata/Contents/{SourceCode}/
        """
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Contents/BJP/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        print(r['documentList']['responseInfo']['fullCount']) # 2735
        assert(r['documentList']['responseInfo']['fullCount'] >= unitTestConfig.ARTICLE_COUNT_BJP)
        # print ("test_metadata_journals complete.")
       
    def test_1B_meta_contents_for_source(self):
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Contents/FA/14/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        print(r['documentList']['responseInfo']['fullCount']) 
        # print ("test_metadata_journals complete.")
        # Check this TOC items
        assert(r['documentList']['responseSet'][6]["documentID"] == "FA.014A.0104A")
        assert(r['documentList']['responseSet'][6]["issueTitle"] == "No. 64")
        assert(r['documentList']['responseSet'][6]["issueSeqNbr"] == "64")
        assert(r['documentList']['responseSet'][6]["pgStart"] == "104")
        
        
    def test_2_meta_contents_source_volume(self):
        """
        Journal Content Lists for a source and vol
        ​/v1​/Metadata​/Contents​/{SourceCode}​/{SourceVolume}​/
        """
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Contents/BJP/1/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['documentList']['responseInfo']['fullCount'] == unitTestConfig.ARTICLE_COUNT_VOL1_BJP)

        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Contents/IJP/1/?limit=1')
        # Confirm that the request-response cycle completed successfully.
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        assert(r['documentList']['responseSet'][0]['documentID'] == 'IJP.001.0001A')
        assert(r['documentList']['responseSet'][0]['pgRg'] == '1-2')

    def test_3_meta_video_sources(self):
        """
        List of video sources (not individual videos, EXCEPT if specified by parameter)
        /v2/Metadata/Videos/
        """
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Videos/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        print(r['sourceInfo']['responseInfo']['fullCount']) 
        assert(r['sourceInfo']['responseInfo']['fullCount'] == unitTestConfig.VIDEOSOURCECOUNT)

        # try with src code parameter
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Videos/?SourceCode=AFCVS&limit=1')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseSet'][0]['title'] == 'Anna Freud Center Video Collection')

    def test_3B_meta_videostreams(self):
        """
        List of video sources (not individual videos, EXCEPT if specified by parameter)
        /v2/Metadata/Videos/
        """
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Videos/?streams=False')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        print(r['sourceInfo']['responseInfo']['fullCount'])
        # give it a range, so we don't have to adjust all the time
        assert(r['sourceInfo']['responseInfo']['fullCount'] >= unitTestConfig.VIDEOCOUNT and r['sourceInfo']['responseInfo']['fullCount'] <= unitTestConfig.VIDEOCOUNT + 15)

        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Videos/?streams=True')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        print(r['sourceInfo']['responseInfo']['fullCount']) 
        assert(r['sourceInfo']['responseInfo']['fullCount'] == unitTestConfig.VIDEOSOURCECOUNT)

        # test default streams parameter (which is streams=True)
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Videos/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        print(r['sourceInfo']['responseInfo']['fullCount']) 
        assert(r['sourceInfo']['responseInfo']['fullCount'] == unitTestConfig.VIDEOSOURCECOUNT)

    def test_6_meta_book_names(self):
        """
        List of book names
        /v2/Metadata/Books/
        """
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Books/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        print (f"Book Count: {r['sourceInfo']['responseInfo']['fullCount']}")
        assert(r['sourceInfo']['responseInfo']['fullCount'] >= unitTestConfig.BOOKCOUNT)

    def test_9_meta_journals(self):
        """
        List of names for a specific source
        /v2/Metadata/Journals/
        """
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Journals/?sourcecode=IJP')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseInfo']['count'] == 1)

        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Videos/?sourcecode=PEPGRANTVS')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseInfo']['count'] == 1)
    
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")