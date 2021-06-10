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

class TestMetadataContents(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    """   

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