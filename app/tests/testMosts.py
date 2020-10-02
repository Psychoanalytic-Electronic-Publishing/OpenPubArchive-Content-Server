#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

#  This test module is in development...

import sys
import os.path
import logging

logger = logging.getLogger(__name__)

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
from localsecrets import TESTUSER, TESTPW, SECRET_KEY, ALGORITHM
# import jwt
from datetime import datetime

from unitTestConfig import base_api, base_plus_endpoint_encoded
from main import app

client = TestClient(app)

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
        response = client.get(base_api + '/v2/Database/MostViewed/')
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
        # request login to the API server
        response = client.get(base_api + '/v2/Database/MostViewed/?pubperiod=30&author=tuck%2A&viewperiod=4&limit=5')
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
        # Try it with variations of the sourcetype to test new robust argument values
        response = client.get(base_api + '/v2/Database/MostViewed/?pubperiod=0')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

        response = client.get(base_api + '/v2/Database/MostViewed/?pubperiod=30&sourcetype=v')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

        response = client.get(base_api + '/v2/Database/MostViewed/?pubperiod=30&sourcetype=j')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

        response = client.get(base_api + '/v2/Database/MostViewed/?pubperiod=30&sourcetype=b')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

        response = client.get(base_api + '/v2/Database/MostViewed/?pubperiod=30&sourcetype=x')
        #  let's fail
        r = response.json()
        assert(response.ok == False)

        response = client.get(base_api + '/v2/Database/MostViewed/?pubperiod=30&sourcetype=videos&viewperiod=4&limit=5')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

        response = client.get(base_api + '/v2/Database/MostViewed/?pubperiod=30&sourcetype=vids&viewperiod=4&limit=5')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

        response = client.get(base_api + '/v2/Database/MostViewed/?pubperiod=30&sourcetype=vxds&viewperiod=4&limit=5')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_0_mostviewed_videos(self):
        """
        """
        # request login to the API server
        response = client.get(base_api + '/v2/Database/MostViewed/?pubperiod=30&sourcetype=videostream&viewperiod=4&limit=5')
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
        response = client.get(base_api + '/v2/Database/MostViewed/?pubperiod=30&sourcetype=vid&viewperiod=4&limit=5')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_0_most_cited(self):
        """
        """
        response = client.get(base_api + '/v2/Database/MostCited/')
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
        response = client.get(base_api + '/v2/Database/MostCited/?similarcount=3')
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
        response = client.get(base_api + '/v2/Database/MostCited/?download=True')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        #r = response.json()
        #print (r)

    def test_0_most_viewed_download(self):
        # see if it can correctly return moreLikeThese
        response = client.get(base_api + '/v2/Database/MostViewed/?download=True')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        #r = response.json()
        #print (r)

    def test_0_most_cited_for_source(self):
        """
        """
        response = client.get(base_api + '/v2/Database/MostCited/?limit=5&sourcecode=PAQ')
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
        response = client.get(base_api + '/v2/Database/MostCited/?pubperiod=20&author=Benjamin&limit=5')
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
        response = client.get(base_api + '/v2/Database/WhatsNew/?days_back=90')
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r['whatsNew']['responseInfo']['listType'] == 'newlist')
        #assert(r["db_server_ok"] == True)
        print (f"{r['whatsNew']['responseInfo']['limit']}")
        print (r)

    def test_00_most_cited_direct(self):
        """
        """
        import opasQueryHelper
        import opasAPISupportLib
        solr_query_spec = \
            opasQueryHelper.parse_search_query_parameters(citecount="5 in ALL", 
                                                          source_name=None,
                                                          source_code=None,
                                                          source_type=None, 
                                                          author=None,
                                                          title=None,
                                                          startyear=None,
                                                          highlighting_max_snips=0, 
                                                          abstract_requested=False,
                                                          similar_count=0
                                                          )
    
        r, status = opasAPISupportLib.search_stats_for_download(solr_query_spec)
        print (r)

    def test_00_most_cited_direct_simple(self):
        """
        """
        import opasQueryHelper
        import opasAPISupportLib
        solr_query_spec = \
            opasQueryHelper.parse_search_query_parameters(citecount="5", 
                                                          source_name=None,
                                                          source_code=None,
                                                          source_type=None, 
                                                          author=None,
                                                          title=None,
                                                          startyear=None,
                                                          highlighting_max_snips=0, 
                                                          abstract_requested=False,
                                                          similar_count=0
                                                          )
    
        r, status = opasAPISupportLib.search_stats_for_download(solr_query_spec)
        print (r)

if __name__ == '__main__':
    unittest.main()
    client.close()
    