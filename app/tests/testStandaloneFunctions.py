#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

#  This test module is in development...

import sys
import os.path

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
    
    def test_0_get_most_viewed(self):
        for i in range(5): # view periods 0-4
            print (f"view period: {i}")
            count, most_viewed = ocd.get_most_viewed(view_period=i,
                                                     source_code="IJP",
                                                     source_type="journals", 
                                                     limit=150
                                                    )  # (most viewed)
            assert (count >= 0)
            #print (f"Count: {count}")
            #print (f"MostViewed: {most_viewed}")
        
        for name in ["freud", "winnicott", "feld"]: 
            count, most_viewed = ocd.get_most_viewed(author=name, 
                                                     view_period='last12months',
                                                     limit=150
                                                    )  # (most viewed)
            
            print (f"Name/Count: {name}/{count}")
            if name == "freud":
                assert (count >= 1)
            elif name == "winnicott":
                assert (count >= 2)
            elif name == "winni":
                assert (count >= 2)
            elif name == "feld":
                assert (count >= 0)
                
            print (most_viewed)

    def test_0_parseToSolrQuery(self):
        """
        Test query formation via parse_search_query_parameters
        
        # Note: AS OF 2020-06-23:
           artLevel=2 is NO LONGER implied if field is para (compare to test_0b)
           The parent is NO LONGER IMPLIED
          ** BE EXPLICIT ***
        """
        test1 =  models.SolrQueryTermList(
                    query = [
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
            query = [
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
            query = [
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
            query = [
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

    def test_1b_get_article_data(self):
        """
        Retrieve an article; make sure it's there and the abstract len is not 0
        """
        # This old function wasn't used by the code otherwise so removed this call
        #  it retrieves an article but doesn't include search highlighting.
        # data = opasAPISupportLib.get_article_data("ANIJP-DE.009.0189A", fields=None)
        # this newer function includes the search parameters if there were some
        data = opasAPISupportLib.documents_get_document("LU-AM.029B.0202A")
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
        assert (data[0] >= 90)
        # check to make sure a known value is among the data returned
        dataList = [d['documentID'] for d in data[1] if 'documentID' in d]
        assert ('IPSAVS.001A.0001A' in dataList)
        data = opasAPISupportLib.metadata_get_source_by_type(src_type="journal")
        dataList = [d.PEPCode for d in data.sourceInfo.responseSet]
        assert ('PAQ' in dataList)
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")