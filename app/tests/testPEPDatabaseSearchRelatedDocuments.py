#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests
import opasPySolrLib

# from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, test_login
# Login!
sessID, headers, session_info = test_login()


class TestDatabaseSearchRelatedDocuments(unittest.TestCase):
    def test_search_relateddocuments_1a(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/RelatedToThis/?relatedToThis=IJP.078.0335A&sort=score%20desc&abstract=false&formatrequested=HTML&limit=15&offset=0')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert response_info["count"] >= 2, f"Expected Count >= 2, Count: {response_info['count']}"
        
    def test_search_relateddocuments_1b(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/RelatedToThis/?relatedToThis=ZBK.025.0028A&sort=score%20desc&abstract=false&formatrequested=HTML&limit=15&offset=0')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert response_info["count"] >= 15, f"Expected Count >= 15, Count: {response_info['count']}"
        
    def test_search_relateddocuments_1c(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/RelatedToThis/?relatedToThis=IJP.078.0173A&sort=score%20desc&abstract=false&formatrequested=HTML&limit=15&offset=0')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert response_info["count"] == 0, f"Expected Count == 0, Count: {response_info['count']}"

    def test_search_relateddocuments_1d(self):
        related, related_id_list = opasPySolrLib.get_articles_related_to_current_via_artqual(art_id = "LU-AM.032B.0155A")
        assert len(related) == 0, related_id_list
        related, related_id_list = opasPySolrLib.get_articles_related_to_current_via_artqual(art_id = "IJP.078.0335A")
        assert len(related) >= 3, related_id_list

if __name__ == '__main__':
    unittest.main()
