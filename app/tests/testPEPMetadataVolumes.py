#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Updates:
#  2020-04-06 - Testing tightened to be exact.
#  2020-04-30 - Added test 8x to test source info retrieval with wildcards

import unittest
import requests
import unitTestConfig
from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

# import opasCentralDBLib

class TestMetadataVolumes(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    """   
        
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
        # Reminder: Requires load of offsite ZBKs to pass
        # ---------------------------------------------------------------------------------------
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Volumes/?sourcecode=ZBK')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        assert r['volumeList']['responseInfo']['fullCount'] >= unitTestConfig.VOL_COUNT_ZBK, f"{r['volumeList']['responseInfo']['fullCount']} should be >= {unitTestConfig.VOL_COUNT_ZBK}"

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
        assert(r['volumeList']['responseInfo']['fullCount'] == unitTestConfig.VOL_COUNT_SE + 1) # 24 vols of SE, plus vTOC

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
           
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")