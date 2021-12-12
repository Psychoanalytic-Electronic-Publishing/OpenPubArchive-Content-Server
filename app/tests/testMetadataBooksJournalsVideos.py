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

class TestMetadataBooksJournalsVideos(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    """   

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
        
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Books/?sourcecode=GW')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseSet'][0]["accessClassification"] == "archive")

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
        assert(r['sourceInfo']['responseSet'][0]["accessClassification"] == "archive")

        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Journals/?sourcecode=IJPOPen')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseInfo']['count'] == 1)
        assert(r['sourceInfo']['responseSet'][0]["accessClassification"] == "special")

    def test_10_meta_videos(self):
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Videos/?sourcecode=PEPGRANTVS')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseInfo']['count'] == 1)
        assert(r['sourceInfo']['responseSet'][0]["accessClassification"] == "archive")
    
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")