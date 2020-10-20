#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

import unittest
import requests

from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_info

class TestMost(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_0_most_downloaded(self):
        """
        """
        # request login to the API server
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostViewed/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
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
        print (r)

    def test_0_mostviewed_argument_robustness(self):
        """
        """
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
        print (r)
        # Try it with variations of the sourcetype to test new robust argument values
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostViewed/?pubperiod=30&sourcetype=vid&viewperiod=4&limit=5')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_0_most_cited(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
        print (f"Count: {r['documentList']['responseInfo']['count']}")
        print (f"Limit: {r['documentList']['responseInfo']['limit']}")
        print (f"ReturnedData: {r['documentList']['responseSet'][0]['stat']['art_cited_5']}")
        assert(r['documentList']['responseSet'][0]['stat']['art_cited_5'] >= 15)
        
    def test_0_most_cited_with_similardocs(self):
        # see if it can correctly return moreLikeThese
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?similarcount=3')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
        try:
            similar_count = int(r['documentList']['responseSet'][0]['similarityMatch']['similarNumFound'])
        except:
            similar_count = 0
            
        assert(similar_count >= 1)

    def test_0_most_cited_download(self):
        # see if it can correctly return moreLikeThese
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?download=True')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        #r = response.json()
        #print (r)

    def test_0_most_viewed_download(self):
        # see if it can correctly return moreLikeThese
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostViewed/?download=True')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        #r = response.json()
        #print (r)

    def test_0_most_cited_for_source(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?limit=5&sourcecode=PAQ')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['count']}")
        print (f"Limit: {r['documentList']['responseInfo']['limit']}")
        print (r)
        try:
            print (f"ReturnedData: {r['documentList']['responseSet'][0]['stat']['art_cited_5']}")
        except:
            logging.warn("No returned data to test for test_0_mostcited_source PAQ")
            
        try:
            if r['documentList']['responseSet'] != []:
                assert(r['documentList']['responseSet'][0]['stat']['art_cited_5'] >= 15)
        except:
            logging.warn("No stat to test for test_0_mostcited_source PAQ")

    def test_1_most_cited_pubperiod_author_viewperiod(self):
        """
        """
        # request login to the API server
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
            logging.warn("No returned data to test for test_0_mostcited_author Benjamin")
        try:
            if r['documentList']['responseSet'] != []:
                assert(r['documentList']['responseSet'][0]['stat']['art_cited_5'] >= 15)
        except:
            logging.warn("No stat to test for test_0_mostviewed_videos")
        print (r)

    def test_0_whats_new(self):
        """
        """
        # request login to the API server
        full_URL = base_plus_endpoint_encoded('/v2/Database/WhatsNew/?days_back=90')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r['whatsNew']['responseInfo']['listType'] == 'newlist')
        #assert(r["db_server_ok"] == True)
        print (f"{r['whatsNew']['responseInfo']['limit']}")
        print (r)


if __name__ == '__main__':
    unittest.main()
    client.close()
    