#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers
import opasAPISupportLib
import opasConfig
import opasQueryHelper
import opasCentralDBLib
import opasGenSupportLib
import models
import opasPySolrLib
from opasPySolrLib import search_text

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
        r1, status = search_text(query="mother and milk or father and child")
        r1_count = r1.documentList.responseInfo.fullCount
        r2, status = search_text(query="mother milk or father and child")
        r2_count = r2.documentList.responseInfo.fullCount
        assert(r1_count == r2_count)
        r3, status = search_text(query="mother milk or (father and child)")
        r3_count = r3.documentList.responseInfo.fullCount
        assert(r1_count == r3_count)
        
    def test_query_equivalence2(self):
        r1, status = search_text(query="'mother milk' or father and child")
        r1_count = r1.documentList.responseInfo.fullCount
        r2, status = search_text(query="'mother milk' or (father and child)")
        r2_count = r2.documentList.responseInfo.fullCount
        assert(r1_count == r2_count)
        r3, status = search_text(query="father child or 'mother milk'")
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

    def test_2_metadata_get_video_source_error(self):
        """
        Test
          1) list of video returns for metadata_get_videos
          2) List of sources by type
          3) 
        """
        data = opasPySolrLib.metadata_get_videos(src_type="Videos", pep_code=123)
        # Confirm that the request-response cycle completed successfully.
        # check to make sure a known value is among the data returned
        dataList = [d.PEPCode for d in data[1] if 'documentID' in d]
        assert (len(dataList) is 0)
        
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
        data = opasAPISupportLib.documents_get_concordance_paras("SEXixa5", ret_format="html")
        # Confirm that the request-response cycle completed successfully.
        para_info = data.documents.responseSet[0].docChild
        para = para_info['para']
        print (para)
        assert (len(para) > 0)
        # check to make sure a known value is among the data returned

    def test_4_document_id_matching(self):
        """
        """
        DocumentID = [
                      ('LU-AM.005I.0025A.FIG001.jpg', 'LU-AM.005I.0025A'),  
                      (' LU-AM.005I.0025A.FIG001.jpg ', 'LU-AM.005I.0025A'),  
                      ('LU-AM.005I.0025A.FIG001', 'LU-AM.005I.0025A'),   
                      ('zbk.074.r0007a', 'ZBK.074.R0007A'), 
                      ('ANIJP-FR.27.0001.PR0027', 'ANIJP-FR.027.0001A.PR0027'), 
                      ('anijp-fr.27.0001.pr27',  'ANIJP-FR.027.0001A.PR0027'), 
                      ('anijp-fr.27.01.pr27', 'ANIJP-FR.027.0001A.PR0027'), 
                      ('ANIJP-FR.27.0001.P0027', 'ANIJP-FR.027.0001A.P0027'), 
                      ('ANIJP-FR.27.0001','ANIJP-FR.027.0001A'), 
                      ('IJP.027C.0001','IJP.027C.0001A'), 
                      ('IJP.027.0001','IJP.027.0001A'), 
                      ('IJP.027.0001B    ','IJP.027.0001B'), 
                      ('ANIJP-FR.027.0001', 'ANIJP-FR.027.0001A'), 
                      ('IJP.027A', 'IJP.027A'), 
                      ('IJP.27', 'IJP.027'), 
                      ('IJP.7.7', 'IJP.007.0007A'), 
                      ('ijp.7.7', 'IJP.007.0007A'), 
                      ]
        for n in DocumentID:
            document_id = opasGenSupportLib.DocumentID(n[0])
            print (f"[{document_id}]=={n[1]}")
            assert (str(document_id) == n[1])
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")