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

class TestMetadataVideos(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    """   

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
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")