#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Updates:
#  2020-04-06 - Testing tightened to be exact.
#  2020-04-30 - Added test 8x to test source info retrieval with wildcards

import unittest
import requests
import unitTestConfig
from unitTestConfig import base_plus_endpoint_encoded, headers

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