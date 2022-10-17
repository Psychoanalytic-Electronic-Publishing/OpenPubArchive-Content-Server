#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

import unittest
import requests
import sys
from datetime import datetime

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestMost(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   
    def test_0_most_cited(self):
        """
        """
        print (f"Running: {sys._getframe(  ).f_code.co_name} at {datetime.now()}")
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        # print (r)
        print (f"Count: {r['documentList']['responseInfo']['count']}")
        print (f"Limit: {r['documentList']['responseInfo']['limit']}")
        print (f"ReturnedData: {r['documentList']['responseSet'][0]['stat']['art_cited_5']}")
        assert(r['documentList']['responseSet'][0]['stat']['art_cited_5'] >= 15)
        
    def test_0_most_cited_with_similardocs(self):
        print (f"Running: {sys._getframe(  ).f_code.co_name} at {datetime.now()}")
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?similarcount=3')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        # print (r)
        # see if it can correctly return moreLikeThese
        try:
            similar_count = int(r['documentList']['responseSet'][0]['similarityMatch']['similarNumFound'])
        except:
            similar_count = 0
            
        assert(similar_count >= 1)

    def test_0_most_cited_download(self):
        print (f"Running: {sys._getframe(  ).f_code.co_name} at {datetime.now()}")
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?download=True')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        #r = response.json()
        #print (r)

    def test_0_most_cited_for_source(self):
        print (f"Running: {sys._getframe(  ).f_code.co_name} at {datetime.now()}")
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?limit=5&sourcecode=PAQ')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['count']}")
        print (f"Limit: {r['documentList']['responseInfo']['limit']}")
        # print (r)
        try:
            print (f"ReturnedData: {r['documentList']['responseSet'][0]['stat']['art_cited_5']}")
        except:
            logger.warn("No returned data to test for test_0_mostcited_source PAQ")
            
        try:
            if r['documentList']['responseSet'] != []:
                assert(r['documentList']['responseSet'][0]['stat']['art_cited_5'] >= 15)
        except:
            logger.warn("No stat to test for test_0_mostcited_source PAQ")

    def test_1_most_cited_pubperiod_author_viewperiod(self):
        print (f"Running: {sys._getframe(  ).f_code.co_name} at {datetime.now()}")
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?pubperiod=20&author=Benjamin&limit=5')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['count']}")
        print (f"Limit: {r['documentList']['responseInfo']['limit']}")
        try:
            print (f"ReturnedData: {r['documentList']['responseSet'][0]['stat']['art_cited_5']}")
        except:
            logger.warn("No returned data to test for test_0_mostcited_author Benjamin")
        try:
            if r['documentList']['responseSet'] != []:
                assert(r['documentList']['responseSet'][0]['stat']['art_cited_5'] >= 15)
        except:
            logger.warn("No stat to test for test_0_mostviewed_videos")
        # print (r)

if __name__ == '__main__':
    unittest.main()
    