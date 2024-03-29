#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests
import logging
import errorMessages

logger = logging.getLogger(__name__)

import unitTestConfig
from unitTestConfig import base_plus_endpoint_encoded, headers, UNIT_TEST_CLIENT_ID

no_session = True
client_only_headers = {"client-id": UNIT_TEST_CLIENT_ID}
bad_client_headers = {"client-id": ""}
no_client_headers = {"client-id": None}

class TestsWithoutClientSession(unittest.TestCase):
    """
    Tests for status endpoints 
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_0_api_status(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Api/Status/')
        response = requests.get(full_URL, headers=client_only_headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_1_session_status(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Session/Status/')
        response = requests.get(full_URL, headers=client_only_headers) # caller has client ID only
        r = response.json()
        assert(r["text_server_ok"] == True)
        assert(r["db_server_ok"] == True)
        #print (r)

    def test_2_session_whoami(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Session/WhoAmI/')
        response = requests.get(full_URL, headers=client_only_headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
    
    def test_3_metadata_books(self):
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Books/')
        response = requests.get(full_URL, headers=client_only_headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        print (f"Book Count: {r['sourceInfo']['responseInfo']['fullCount']}")
        assert r['sourceInfo']['responseInfo']['fullCount'] >= unitTestConfig.BOOKCOUNT

    def test_9_pubs_authornames(self):
        """
        Get Author Pubs For Matching Author Names
        /v2/Authors​/Publications​/{authorNamePartial}​/
        """
        full_URL = base_plus_endpoint_encoded('/v2/Authors/Publications/maslow, a.*/')
        response = requests.get(full_URL, headers=client_only_headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['authorPubList']['responseInfo']['fullCount']} Count complete: {r['authorPubList']['responseInfo']['fullCountComplete']}")
        assert r['authorPubList']['responseInfo']['fullCount'] == 3, r['authorPubList']['responseInfo']['fullCount'] == 3

    def test_9b_pubs_authornames(self):
        """
        Get Author Pubs For Matching Author Names
        /v1​/Authors​/Publications​/{authorNamePartial}​/
        """
        # try a regex wildcard search (regex wildcards permitted anywhere EXCEPT the end of the name, since that's done automatically)
        # Last name starts in he, followed by a or l, ending in n or y
        full_URL = base_plus_endpoint_encoded('/v2/Authors/Publications/he[al][^\s,]+[ny]/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        assert r['authorPubList']['responseInfo']['fullCount'] >= 2, r['authorPubList']['responseInfo']['fullCount']

    def test_10_get_term_counts(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/TermCounts/?termlist=fear,loathing,elections')
        response = requests.get(full_URL)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["termIndex"]["responseInfo"]
        response_set = r["termIndex"]["responseSet"] 
        assert(response_set[0]["termCount"] >= 3)
        #print (response_set)
        
    def test_11_get_most_viewed(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostViewed/')
        response = requests.get(full_URL, headers=client_only_headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        #print (r)
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

    def test_12_get_most_cited(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/')
        response = requests.get(full_URL, headers=client_only_headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        #print (r)
        print (f"Count: {r['documentList']['responseInfo']['count']}")
        print (f"Limit: {r['documentList']['responseInfo']['limit']}")
        print (f"ReturnedData (art_cited_5): {r['documentList']['responseSet'][0]['stat']['art_cited_5']}")
        assert r['documentList']['responseSet'][0]['stat']['art_cited_5'] >= 15

    def test_13_search_wildcard(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=gre?nfield')
        response = requests.get(full_URL, headers=client_only_headers)
        assert(response.ok == True)
        r = response.json()
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert response_info["fullCount"] >= 7, response_info["fullCount"]
        print (f"Fullcount: {response_info['fullCount']}")
        # print (response_set)
        # Confirm that the request-response cycle completed successfully.

    def test_14_get_abstract(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Abstracts/IFP.017.0240A?similarcount=4')
        response = requests.get(full_URL, headers=client_only_headers)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert response_info["count"] == 1, response_info["count"]
        print (response_set[0]['abstract'])

    def test_15_get_document_with_similarcount(self):
        """
        Since no login or authorization, should just return abstract
        """
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/JOAP.063.0667A/?search=?journal=&fulltext1=mother love&sort=citeCount&similarcount=2')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=client_only_headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert response_info["count"] == 1, response_info["count"]
        print (response_info)

    def test_16B_get_abstract_client_id_param(self):
        # this method of client-id should be ok.
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Abstracts/IFP.017.0240A?similarcount=4&client-id=4')
        response = requests.get(full_URL)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)

    def test_16C_get_abstract_bad_client_id(self):
        # client-id must be numeric
        logger.error("Note: Error expected below: The caller has not provided sufficient identification. Sending bad (alpha) client ID.")
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Abstracts/IFP.017.0240A?similarcount=4&client-id=BAD_CLIENT_ID_TEST')
        response = requests.get(full_URL)
        r = response.json()
        assert r["detail"] == errorMessages.ERR_MSG_CALLER_IDENTIFICATION_ERROR, r["detail"] 
        assert response.status_code == 428, response.status_code

    def test_17_get_abstract_bad_client_id_func(self):
        logger.error("Note: Error expected below: The caller has not provided sufficient identification. Sending WITHOUT ANY client ID.")
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Abstracts/IFP.017.0240A?similarcount=4')
        print (f"Headers: {no_client_headers}")
        response = requests.get(full_URL, headers=no_client_headers)
        r = response.json()
        assert r["detail"] == errorMessages.ERR_MSG_CALLER_IDENTIFICATION_ERROR, r["detail"] 
        assert response.status_code == 428, response.status_code
       
if __name__ == '__main__':
    unittest.main()    