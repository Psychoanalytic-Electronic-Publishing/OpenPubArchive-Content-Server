#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from localsecrets import PADS_TEST_ID, PADS_TEST_PW

import opasDocPermissions
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, BOOKCOUNT, ALL_SOURCES_COUNT

# login
pads_session_info = opasDocPermissions.authserver_login(username=PADS_TEST_ID, password=PADS_TEST_PW)
session_info = opasDocPermissions.get_authserver_session_info(pads_session_info.SessionId, client_id=UNIT_TEST_CLIENT_ID, pads_session_info=pads_session_info)
# Confirm that the request-response cycle completed successfully.
session_id = pads_session_info.SessionId
headers = {f"client-session":f"{session_id}","client-id": UNIT_TEST_CLIENT_ID}
import logging
logger = logging.getLogger(__name__)

class TestZimulateExternalClient(unittest.TestCase):
    """
    Tests for status endpoints 
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_1_session_status(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Session/Status/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        assert(r["text_server_ok"] == True)
        assert(r["db_server_ok"] == True)
        print (r)

    def test_2_session_whoami(self):
        # Send a request to the API server and store the response.
        full_URL = base_plus_endpoint_encoded('/v2/Session/WhoAmI/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
    
    def test_3_metadata_books(self):
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Books/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        print (f"Book Count: {r['sourceInfo']['responseInfo']['fullCount']}")
        assert(r['sourceInfo']['responseInfo']['fullCount'] >= BOOKCOUNT)

    def test_7_meta_get_sourcenames(self):
        """
        List of names for a specific source
        /v2/Metadata/{SourceType}/{SourceCode}/
        """
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Journals/?sourcecode=IJPSP')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseInfo']['fullCount'] == 1)
        assert(r['sourceInfo']['responseSet'][0]['displayTitle'] == 'International Journal of Psychoanalytic Self Psychology')
        
    def test_8_meta_all_sources(self):
        """
        List of names for a specific source
        /v2/Metadata/{SourceType}/{SourceCode}/
        """
        full_URL = base_plus_endpoint_encoded('/v1/Metadata/*/*/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        count = r['sourceInfo']['responseInfo']['count']
        print (f"Count {count}")
        assert(count >= ALL_SOURCES_COUNT)

    def test_9_pubs_authornames(self):
        """
        Get Author Pubs For Matching Author Names
        /v1​/Authors​/Publications​/{authorNamePartial}​/
        """
        full_URL = base_plus_endpoint_encoded('/v2/Authors/Publications/maslow, a.*/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['authorPubList']['responseInfo']['fullCount']} Count complete: {r['authorPubList']['responseInfo']['fullCountComplete']}")
        assert(r['authorPubList']['responseInfo']['fullCount'] == 3)

    def test_10_get_term_counts(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/TermCounts/?termlist=fear,loathing,elections')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["termIndex"]["responseInfo"]
        response_set = r["termIndex"]["responseSet"] 
        assert(response_set[0]["termCount"] >= 3)
        print (response_set)
        
    def test_11_get_most_viewed(self):
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
                count = r['documentList']['responseSet'][0]['stat'].get('art_views_last12mos')
                print (f"ReturnedData: {r['documentList']['responseSet'][0]['stat'].get('art_views_last12mos')}")
                if count is not None:
                    assert(count >= 0)
            except:
                logger.warning("No stat in return...has solrUpdateData been run on this database?")
            assert(r['documentList']['responseInfo']['count'] <= r['documentList']['responseInfo']['limit'])
        else:
            print("Test skipped...no view data currently available.")

    def test_12_get_most_cited(self):
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

    def test_13_search_wildcard(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=gre?nfield')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] >= 7)
        # print (response_set)
        # Confirm that the request-response cycle completed successfully.

    def test_14_get_abstract(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Abstracts/IFP.017.0240A?similarcount=4')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        print (response_set)

    def test_15_get_document_with_similarcount(self):
        """
        Since no login or authorization, should just return abstract
        """
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/JOAP.063.0667A/?search=?journal=&fulltext1=mother love&sort=citeCount&similarcount=2')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"] 
        assert(response_info["count"] == 1)
        print (response_set)

       
if __name__ == '__main__':
    unittest.main()    