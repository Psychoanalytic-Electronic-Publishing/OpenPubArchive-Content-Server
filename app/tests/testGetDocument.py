#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import logging
import opasAPISupportLib
logger = logging.getLogger(__name__)

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers
from localsecrets import PADS_TEST_ID, PADS_TEST_PW

# login
full_URL = base_plus_endpoint_encoded(f'/v2/Session/Login/?grant_type=password&username={PADS_TEST_ID}&password={PADS_TEST_PW}')
response = requests.get(full_URL, headers=headers)
r = response.json()
headers["client-session"] = r["session_id"]

class TestGetDocuments(unittest.TestCase):
    """
    Tests for basic login and Download
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    def test_0_get_document_with_hits(self):
        search = 'search=fulltext1=%22Evenly%20Suspended%20Attention%22~25&viewperiod=4&formatrequested=HTML&highlightlimit=5&facetmincount=1&facetlimit=15&sort=score%20desc&limit=15'
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/PCT.011.0171A?{search}')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"]
        doc = response_set[0]["document"]
        matches = re.findall("\<span class\=\'searchhit\'\>(.*?)\</span\>", doc)
        assert(len(matches) >= 90)

    def test_1_get_document(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/IJP.077.0217A/')
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

    def test_2_get_document_with_search_context(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/JOAP.063.0667A/?search=?journal=&fulltext1=mother love&sort=citeCount')
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

    def test_2_get_document_with_similarcount(self):
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

    def test_1_fetch_article(self):
        """
        Retrieve an article; make sure it's there and the abstract len is not 0
        """
        # This old function wasn't used by the code otherwise so removed this call
        #  it retrieves an article but doesn't include search highlighting.
        # data = opasAPISupportLib.get_article_data("ANIJP-DE.009.0189A", fields=None)
        # this newer function includes the search parameters if there were some
        data = opasAPISupportLib.documents_get_document("LU-AM.029B.0202A")
        # Confirm that the request-response cycle completed successfully.
        if data is None:
            print ("Data not found")
            assert ("doc not found" == True)
        else:
            assert (data.documents.responseInfo.fullCount == 1)
            assert (data.documents.responseSet[0].documentID == 'LU-AM.029B.0202A')
            assert (len(data.documents.responseSet[0].abstract)) > 0

    def test_3_get_document_logged_out_verify_only_abstract_return(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Session/Logout')
        response = requests.get(full_URL, headers=headers)
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Document/JOAP.063.0667A')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documents"]["responseInfo"]
        response_set = r["documents"]["responseSet"]
        assert(response_info["count"] == 1)
        assert(response_set[0]["accessLimited"] == True)
        assert(len(response_set[0]["abstract"]) == len(response_set[0]["document"])) 


if __name__ == '__main__':
    unittest.main()    