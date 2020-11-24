#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import opasQueryHelper
import opasCentralDBLib
import starlette.status as httpCodes
import models
from opasPySolrLib import search_text, search_text_qs

import requests
from unitTestConfig import base_plus_endpoint_encoded, headers, session_id, session_info

ocd = opasCentralDBLib.opasCentralDB()
fulltext1 = [
               ("dreams_xml:mother and father and authors:David Tuckett and Nadine Levinson", 0), 
               ('text:("mother love"~25) AND dreams_xml:("father love"~25)', 4), # (switching quote types for testing)
               ('text:(love and hate)', 1135),
               ('text:(love and -hate)', 26675),
               ('text:("love hate"~25)', 6977),
               ('text:(love or hate and emotions)', 4763),
               ('text:love', 37813),
               ('text:"hate emotions"~25', 553),
               ('text:(love or "hate emotions"~25)', 37861),
               ("dreams_xml:(mother and father) AND text:fight", 39), 
               ("mother and father", 31294),
               ("mother or father", 52273),
               ("mother and father or son", 46389), 
               ("mother and father and child", 27087), 
               ("mother and father and -child", 4207), 
               ("mother and father", 31294), 
               ("mother and -father", 15095),
               ("dreams_xml:(mother and father)", 142), 
               ("dreams_xml:(mother and -father)", 255),
               ("dreams_xml:(mother and son)", 397), 
               ("dreams_xml:(mother and (father or son))", 142), 
               ("dreams_xml:(mother and father or mother and son)", 142), 
               ("dreams_xml:((mother and father) or (mother and son))", 397), 
               ("dreams_xml:(mother and father and child)", 38), 
               ("dreams_xml:(mother and father and -child)", 104), 
               ("'adoptive mother' and father", 817),
               ("'adoptive mother' or father", 1142),
               ("'adoptive mother' and father or son", 992), 
               ("'adoptive mother' and father and child", 795), 
               ("'adoptive mother' and father and -child", 22), 
               ("'adoptive mother' and father", 817), 
               ("'adoptive mother' and -father", 175),
            ]

class TestSearchSyntax(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    def test_00_qt_parsing(self):
        for n, expected_count in fulltext1:
            term_list = opasQueryHelper.parse_to_query_term_list(n)
            solr_query_term_list = models.SolrQueryTermList(qt=term_list)
            solr_query_spec = opasQueryHelper.parse_search_query_parameters(solrQueryTermList=solr_query_term_list, art_level=1)
            print (solr_query_spec.solrQuery.searchQ)
            full_URL = base_plus_endpoint_encoded('/v2/Database/Search/')
            response = requests.post(full_URL, headers=headers, json={"qtermlist": solr_query_term_list.dict()})
            assert(response.ok == True)
            r = response.json()
            response_info = r["documentList"]["responseInfo"]
            response_set = r["documentList"]["responseSet"] 
            assert(response_info["fullCount"] >= expected_count) # just make sure there's a count
            
            #ret_val, ret_status = search_text_qs(solr_query_spec,
                                                    #limit=1,
                                                    #offset=0,
                                                    #session_info=session_info
                                                    #)
            #  if there's a Solr server error in the call, it returns a non-200 ret_status[0]
            #assert(ret_status[0] == httpCodes.HTTP_200_OK)
            #print (ret_val.documentList.responseInfo.fullCount)
            #assert(expected_count <= ret_val.documentList.responseInfo.fullCount)
            
        
    def test_01_simple_syntax(self):
        """
        Test query formation via parse_search_query_parameters
        """
        for n, expected_count in fulltext1:
            solr_query_spec = opasQueryHelper.parse_search_query_parameters(fulltext1=n, art_level=1)
            print (solr_query_spec.solrQuery.searchQ)
            ret_val, ret_status = search_text_qs(solr_query_spec,
                                                 limit=1,
                                                 offset=0, 
                                                 session_info=session_info
                                                 )
            #  if there's a Solr server error in the call, it returns a non-200 ret_status[0]
            assert(ret_status[0] == httpCodes.HTTP_200_OK)
            print (ret_val.documentList.responseInfo.fullCount)
            assert(expected_count <= ret_val.documentList.responseInfo.fullCount)
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")