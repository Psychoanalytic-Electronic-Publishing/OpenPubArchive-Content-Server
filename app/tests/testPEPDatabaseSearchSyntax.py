#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import opasCentralDBLib
import starlette.status as httpCodes
import models

import requests
import unitTestConfig
from unitTestConfig import base_plus_endpoint_encoded, headers
session_info = unitTestConfig.get_session_info_for_test()
from opasQueryHelper import parse_search_query_parameters, parse_to_query_term_list, parse_search_query_parameters 
from opasPySolrLib import search_text_qs

ocd = opasCentralDBLib.opasCentralDB()
fulltext1 = [
               ("dreams_xml:mother AND father AND authors:David Tuckett AND Nadine Levinson", 0), 
               ('text:("mother love"~25) AND dreams_xml:("father love"~25)', 4), # (switching quote types for testing)
               ('text:(love AND hate)', 11210),
               ('text:(love AND -hate)', 26675),
               ('text:("love hate"~25)', 6977),
               ('text:(love OR hate AND emotions)', 4763),
               ('text:love', 37813),
               ('text:"hate emotions"~25', 553),
               ('text:(love OR "hate emotions"~25)', 37861),
               ("dreams_xml:(mother AND father) AND text:fight", 36), 
               ("mother AND father", 30000), # was 31294, latest db disagrees, 2021-01-25
               ("mother OR father", 51432), # was 52273, latest db disagrees 2021-01-25
               ("mother AND father OR son", 45487), # was 46389, latest db disagrees 2021-01-25
               ("mother AND father AND child", 26149), # was 27087, latest db disagrees 2021-01-25
               ("mother AND father AND -child", 4207), 
               ("mother AND father", 30000), 
               ("mother AND -father", 15074), # was 15095, latest db disagrees 2021-01-25
               ("dreams_xml:(mother AND father)", 135), # was 140, latest db disagrees at 139 2022-03-23
               ("dreams_xml:(mother AND -father)", 253), # was 255
               ("dreams_xml:(mother AND (father OR son))", 140), # was 142
               ("dreams_xml:(mother AND father AND child)", 35), #  was 36
               ("dreams_xml:(mother AND father AND -child)", 104), 
               ("'adoptive mother' AND father", 810), # was 817
               ("'adoptive mother' OR father", 1142),
               ("'adoptive mother' AND father OR son", 987), #  was 992
               ("'adoptive mother' AND father AND child", 785),  # was 795
               ("'adoptive mother' AND father AND -child", 22), 
               ("'adoptive mother' AND father", 810), # was 817
               ("'adoptive mother' AND -father", 175),
               ("dreams_xml:((mother AND father) OR (mother AND son))", 140), # was 397
               ("dreams_xml:(mother AND father OR mother AND son)", 39), 
               ("dreams_xml:(mother AND son)", 39), # was 397
            ]

class TestDatabaseSearchSyntax(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    def test_00_qt_parsing(self):
        for n, expected_count in fulltext1:
            term_list = parse_to_query_term_list(n)
            solr_query_term_list = models.SolrQueryTermList(qt=term_list)
            solr_query_spec = parse_search_query_parameters(solrQueryTermList=solr_query_term_list, art_level=1)
            full_URL = base_plus_endpoint_encoded('/v2/Database/Search/')
            response = requests.post(full_URL, headers=headers, json={"qtermlist": solr_query_term_list.dict()})
            assert(response.ok == True)
            r = response.json()
            response_info = r["documentList"]["responseInfo"]
            response_set = r["documentList"]["responseSet"]
            print (f"Search: {n}, expected count: {expected_count}, full count: {response_info['fullCount']}")
            assert response_info["fullCount"] >= expected_count, (n, f"Expected: {expected_count} vs FullCount: {response_info['fullCount']}, solr_q={solr_query_spec.solrQuery.searchQ}") # just make sure there's a count
            
    def test_01_simple_syntax(self):
        """
        Test query formation via parse_search_query_parameters
        """
        for n, expected_count in fulltext1:
            solr_query_spec = parse_search_query_parameters(fulltext1=n, art_level=1)
            # print (solr_query_spec.solrQuery.searchQ)
            ret_val, ret_status = search_text_qs(solr_query_spec,
                                                 limit=1,
                                                 offset=0, 
                                                 session_info=session_info
                                                 )
            #  if there's a Solr server error in the call, it returns a non-200 ret_status[0]
            assert(ret_status[0] == httpCodes.HTTP_200_OK)
            full_count = ret_val.documentList.responseInfo.fullCount
            print (f"Checking query:{n}; count: {full_count} vs expected: {expected_count}\n")
            assert expected_count <= full_count
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")