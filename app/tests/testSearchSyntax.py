#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

#  This test module is in development...

import sys
import os.path

import opasDocPermissions as opasDocPerm

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
import jwt
from datetime import datetime
import opasAPISupportLib
import opasQueryHelper
import opasCentralDBLib
import starlette.status as httpCodes
import models

from unitTestConfig import base_api, base_plus_endpoint_encoded
# from main import app

# client = TestClient(app)
# sample URL from client
# https://stage-api.pep-web.rocks/v2/Database/Search/?abstract=true&facetfields=art_year_int,art_views_last12mos,art_cited_5,art_authors,art_lang,art_type,art_sourcetype,art_sourcetitleabbr,glossary_group_terms,art_kwds_str&facetlimit=15&facetmincount=1&fulltext1=text:("mother love"~25) AND dreams_xml:("father love"~25)&limit=20&offset=0&parascope=dreams&synonyms=false
# https://stage-api.pep-web.rocks/v2/Database/Search/?fulltext1=text:("mother love"~25) AND dreams_xml:("father love"~25)
ocd = opasCentralDBLib.opasCentralDB()
fulltext1 = [
               ("dreams_xml:mother and father and authors:David Tuckett and Nadine Levinson", 0), 
               ('text:("mother love"~25) AND dreams_xml:("father love"~25)', 4), # (switching quote types for testing)
               ('text:(love and hate)', 1138),
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
    
    def test_000_qt_parsing(self):
        for n, expected_count in fulltext1:
            term_list = opasQueryHelper.parse_to_query_term_list(n)
            solr_query_term_list = models.SolrQueryTermList(qt=term_list)
            solr_query_spec = opasQueryHelper.parse_search_query_parameters(solrQueryTermList=solr_query_term_list, art_level=1)
            print (solr_query_spec.solrQuery.searchQ)
            ret_val, ret_status = opasAPISupportLib.search_text_qs(solr_query_spec,
                                                                   limit=1,
                                                                   offset=0
                                                                   )
            #  if there's a Solr server error in the call, it returns a non-200 ret_status[0]
            assert(ret_status[0] == httpCodes.HTTP_200_OK)
            print (ret_val.documentList.responseInfo.fullCount)
            assert(expected_count <= ret_val.documentList.responseInfo.fullCount)
            
        
    def test_00_simple_syntax(self):
        """
        Test query formation via parse_search_query_parameters
        """
        for n, expected_count in fulltext1:
            solr_query_spec = opasQueryHelper.parse_search_query_parameters(fulltext1=n, art_level=1)
            print (solr_query_spec.solrQuery.searchQ)
            ret_val, ret_status = opasAPISupportLib.search_text_qs(solr_query_spec,
                                                                   limit=1,
                                                                   offset=0
                                                                   )
            #  if there's a Solr server error in the call, it returns a non-200 ret_status[0]
            assert(ret_status[0] == httpCodes.HTTP_200_OK)
            print (ret_val.documentList.responseInfo.fullCount)
            assert(expected_count <= ret_val.documentList.responseInfo.fullCount)
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")