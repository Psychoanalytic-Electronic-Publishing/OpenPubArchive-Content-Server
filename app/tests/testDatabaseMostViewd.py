#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

import unittest
import requests
import sys
from datetime import datetime
import time

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestMost(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_0_client_init_set_test(self):
        """
        Test calls made by typical client (e.g., Gavant)
        """
        print (f"Running: {sys._getframe(  ).f_code.co_name} at {datetime.now()}")
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostViewed/?formatrequested=XML&limit=10&viewperiod=2')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)

        full_URL = base_plus_endpoint_encoded('/v2/Database/WhatsNew/?days_back=30&limit=10')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?formatrequested=XML&limit=10&period=all')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)

    def test_0_most_downloaded(self):
        print (f"Running: {sys._getframe(  ).f_code.co_name} at {datetime.now()}")
        # request login to the API server
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostViewed/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        # print (r)
        print (f"Count: {r['documentList']['responseInfo']['count']}")
        print (f"Limit: {r['documentList']['responseInfo']['limit']}")
        if r['documentList']['responseInfo']['count'] > 0:
            try:
                print (f"ReturnedData: {r['documentList']['responseSet'][0]['stat']['art_views_last12mos']}")
                assert(r['documentList']['responseSet'][0]['stat']['art_views_last12mos'] >= 0)
            except:
                logger.warning("No stat in return...has solrUpdateData been run on this database?")
            assert(r['documentList']['responseInfo']['count'] <= r['documentList']['responseInfo']['limit'])
        else:
            print("Test skipped...no view data currently available.")
        #assert(r["text_server_ok"] == True)
        #assert(r["db_server_ok"] == True)
       
    def test_0_most_downloaded_pubperiod_author_viewperiod(self):
        """
        """
        print (f"Running: {sys._getframe(  ).f_code.co_name} at {datetime.now()}")
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostViewed/?pubperiod=30&author=tuck%2A&viewperiod=4&limit=5')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['count']}")
        print (f"Limit: {r['documentList']['responseInfo']['limit']}")
        #sometimes no data there
        if r['documentList']['responseSet'] != []:
            try:
                print (f"ReturnedData: {r['documentList']['responseSet'][0]['stat']['art_views_last12mos']}")
                assert(r['documentList']['responseSet'][0]['stat']['art_views_last12mos'] >= 0)
            except:
                logger.warning("No stat in return...has solrUpdateData been run on this database?")

        #assert(r["text_server_ok"] == True)
        #assert(r["db_server_ok"] == True)
        # print (r)

    def test_0_mostviewed_argument_robustness(self):
        print (f"Running: {sys._getframe(  ).f_code.co_name} at {datetime.now()}")
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostViewed/?pubperiod=0')
        response = requests.get(full_URL, headers=headers)
        # Try it with variations of the sourcetype to test new robust argument values
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

        full_URL = base_plus_endpoint_encoded('/v2/Database/MostViewed/?pubperiod=30&sourcetype=v')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

        full_URL = base_plus_endpoint_encoded('/v2/Database/MostViewed/?pubperiod=30&sourcetype=j')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

        full_URL = base_plus_endpoint_encoded('/v2/Database/MostViewed/?pubperiod=30&sourcetype=b')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

        full_URL = base_plus_endpoint_encoded('/v2/Database/MostViewed/?pubperiod=30&sourcetype=x')
        response = requests.get(full_URL, headers=headers)
        #  let's fail
        r = response.json()
        assert(response.ok == False)

        full_URL = base_plus_endpoint_encoded('/v2/Database/MostViewed/?pubperiod=30&sourcetype=videos&viewperiod=4&limit=5')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

        full_URL = base_plus_endpoint_encoded('/v2/Database/MostViewed/?pubperiod=30&sourcetype=vids&viewperiod=4&limit=5')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

        full_URL = base_plus_endpoint_encoded('/v2/Database/MostViewed/?pubperiod=30&sourcetype=vxds&viewperiod=4&limit=5')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_0_mostviewed_videos(self):
        """
        """
        print (f"Running: {sys._getframe(  ).f_code.co_name} at {datetime.now()}")
        # request login to the API server
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostViewed/?pubperiod=30&sourcetype=videostream&viewperiod=4&limit=5')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['count']}")
        print (f"Limit: {r['documentList']['responseInfo']['limit']}")
        #sometimes no data there
        try:
            if r['documentList']['responseSet'] != []:
                assert(r['documentList']['responseSet'][0]['stat']['art_views_last12mos'] > 0)
        except:
            logging.warn("No stat to test for test_0_mostviewed_videos")
            
        #assert(r["text_server_ok"] == True)
        #assert(r["db_server_ok"] == True)
        # print (r)
        # Try it with variations of the sourcetype to test new robust argument values
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostViewed/?pubperiod=30&sourcetype=vid&viewperiod=4&limit=5')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        
    def test_0_most_viewed_download(self):
        print (f"Running: {sys._getframe(  ).f_code.co_name} at {datetime.now()}")
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostViewed/?download=True')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        #r = response.json()
        #print (r)

if __name__ == '__main__':
    unittest.main()
    client.close()
    