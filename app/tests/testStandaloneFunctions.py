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
import opasConfig
import opasQueryHelper
import opasCentralDBLib
import models

from unitTestConfig import base_api, base_plus_endpoint_encoded
# from main import app

# client = TestClient(app)

ocd = opasCentralDBLib.opasCentralDB()

class TestStandaloneFunctions(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """

    def test_year_arg_parser_(self):
        resp = opasQueryHelper.year_arg_parser("1980-1989 OR 2000-2010")
        print (resp)
    
    def test_cleanup_query_(self):
        resp = opasQueryHelper.cleanup_solr_query("freud, sigmund OR grotstein, james s")
        print (resp)
        resp = opasQueryHelper.cleanup_solr_query("author: freud, sigmund OR grotstein, james s")
        print (resp)
        resp = opasQueryHelper.cleanup_solr_query("(freud, sigmund OR grotstein, james s)")
        print (resp)
        
    def test_query_equivalence(self):
        r1, status = opasAPISupportLib.search_text(query="mother and milk or father and child")
        r1_count = r1.documentList.responseInfo.fullCount
        r2, status = opasAPISupportLib.search_text(query="mother milk or father and child")
        r2_count = r2.documentList.responseInfo.fullCount
        assert(r1_count == r2_count)
        r3, status = opasAPISupportLib.search_text(query="mother milk or (father and child)")
        r3_count = r3.documentList.responseInfo.fullCount
        assert(r1_count == r3_count)
        
    def test_query_equivalence2(self):
        r1, status = opasAPISupportLib.search_text(query="'mother milk' or father and child")
        r1_count = r1.documentList.responseInfo.fullCount
        r2, status = opasAPISupportLib.search_text(query="'mother milk' or (father and child)")
        r2_count = r2.documentList.responseInfo.fullCount
        assert(r1_count == r2_count)
        r3, status = opasAPISupportLib.search_text(query="father child or 'mother milk'")
        r3_count = r3.documentList.responseInfo.fullCount
        assert(r1_count == r3_count)
    
    def test_0_parseToSolrQuery(self):
        """
        Test query formation via parse_search_query_parameters
        
        # Note: AS OF 2020-06-23:
           artLevel=2 is NO LONGER implied if field is para (compare to test_0b)
           The parent is NO LONGER IMPLIED
          ** BE EXPLICIT ***
        """
        test1 =  models.SolrQueryTermList(
                    qt = [
                               {
                                 "words":"child abuse",
                                 "field": "para",
                                 "synonyms": "true",
                               }
                    ]
                )
        resp = opasQueryHelper.parse_search_query_parameters(solrQueryTermList=test1)
        assert (resp.solrQuery.searchQ == "(para_syn:(child abuse))")

    def test_0b_parseToSolrQuery(self):
        """
        Test query formation via parse_search_query_parameters
        """
        test1 =  models.SolrQueryTermList(
            artLevel = 2, 
            qt = [
                        {
                          "words":"child abuse",
                          "parent": "doc",
                          "field": "para",
                          "synonyms": "true",
                        }
                     ]
            )
        resp = opasQueryHelper.parse_search_query_parameters(solrQueryTermList=test1)
        assert (resp.solrQuery.searchQ == "{!parent which='art_level:1'} art_level:2 && ((parent_tag:(p_body || p_summaries || p_appxs) && para_syn:(child abuse)))")

    def test_0c_parseToSolrQuery(self):
        """
        Test query formation via parse_search_query_parameters
        """
        test1 =  models.SolrQueryTermList(
            artLevel = 2, 
            qt = [
                        {
                          "words":"excited",
                          "parent": "doc",
                          "field": "para",
                          "synonyms": "true",
                        },
                        {
                          "words":"asylum",
                          "parent": "doc",
                          "field": "para",
                          "synonyms": "false",
                        }
                        
                     ]
            )
        resp = opasQueryHelper.parse_search_query_parameters(solrQueryTermList=test1)
        assert (resp.solrQuery.searchQ == "{!parent which='art_level:1'} art_level:2 && ((parent_tag:(p_body || p_summaries || p_appxs) && para_syn:(excited)) && (parent_tag:(p_body || p_summaries || p_appxs) && para:(asylum)))")

    def test_0d_parseToSolrQuery(self):
        """
        Test query formation via parse_search_query_parameters
        """
        test1 =  models.SolrQueryTermList(
            artLevel = 2, 
            qt = [
                        {
                          "words":"mother became pale",
                          "parent": "doc",
                          "field": "para",
                          "synonyms": "false",
                        }
                     ]
            )
        resp = opasQueryHelper.parse_search_query_parameters(solrQueryTermList=test1)
        assert (resp.solrQuery.searchQ == "{!parent which='art_level:1'} art_level:2 && ((parent_tag:(p_body || p_summaries || p_appxs) && para:(mother became pale)))")

    def test_1a_get_article_abstract_data(self):
        """
        Retrieve an article; make sure it's there and the abstract len is not 0
        """
        # This old function wasn't used by the code otherwise so removed this call
        #  it retrieves an article but doesn't include search highlighting.
        # data = opasAPISupportLib.get_article_data("ANIJP-DE.009.0189A", fields=None)
        # this newer function includes the search parameters if there were some
        data = opasAPISupportLib.documents_get_abstracts("LU-AM.029B.0202A")
        # Confirm that the request-response cycle completed successfully.
        assert (data.documents.responseInfo.fullCount == 1)
        assert (data.documents.responseSet[0].documentID == 'LU-AM.029B.0202A')
        assert (len(data.documents.responseSet[0].abstract)) > 0

    def test_2_metadata_get_sources(self):
        """
        Test
          1) list of video returns for metadata_get_videos
          2) List of sources by type
          3) 
        """
        data = opasAPISupportLib.metadata_get_videos(src_type="Videos", pep_code=None, limit=opasConfig.DEFAULT_LIMIT_FOR_METADATA_LISTS, offset=0)
        # Confirm that the request-response cycle completed successfully.
        # check to make sure a known value is among the data returned
        dataList = [d['documentID'] for d in data[1] if 'documentID' in d]
        assert ('IPSAVS.001A.0001A' in dataList)
        data = opasAPISupportLib.metadata_get_source_info(src_type="journal")
        dataList = [d.PEPCode for d in data.sourceInfo.responseSet]
        assert ('PAQ' in dataList)
        data = opasAPISupportLib.metadata_get_source_info(src_type="book")
        dataList = [d.PEPCode for d in data.sourceInfo.responseSet]
        assert ('ZBK075' in dataList)
        
    def test_3_get_para_translation(self):
        """
        """
        data = opasAPISupportLib.documents_get_concordance_paras("SEXixa5")
        # Confirm that the request-response cycle completed successfully.
        para_info = data.documents.responseSet[0].docChild
        para = para_info['para']
        print (para)
        assert (len(para) > 0)
        # check to make sure a known value is among the data returned
        
    def test_3b_get_para_translation(self):
        """
        """
        response = opasDocPerm.pads_login()
        ## Confirm that the request-response cycle completed successfully.
        try:
            sessID = response["SessionId"]
        except:
            err = f"PaDS response error: {response}"
            logger.error(err)
            print (err)
            assert(False)
        else:
            data = opasAPISupportLib.documents_get_concordance_paras("SEXixa5", ret_format="html")
            # Confirm that the request-response cycle completed successfully.
            para_info = data.documents.responseSet[0].docChild
            para = para_info['para']
            print (para)
            assert (len(para) > 0)
            # check to make sure a known value is among the data returned
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")