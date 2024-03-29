#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

import unittest
# import requests
from unitTestConfig import headers, session_id, test_login
import opasQueryHelper
import opasPySolrLib

# Login!
sessID, headers, session_info = test_login()

class TestOpasQueryHelperMostsCalls(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   
    def test_0_most_cited_direct_with_similarity(self):
        """
        """
        solr_query_spec = \
            opasQueryHelper.parse_search_query_parameters(citecount="5 in ALL", 
                                                          source_name=None,
                                                          source_code=None,
                                                          source_type=None, 
                                                          author=None,
                                                          title=None,
                                                          startyear=None,
                                                          highlightlimit=0, 
                                                          abstract_requested=False,
                                                          similar_count=5,
                                                          limit=25
                                                          )
    
        r, status = opasPySolrLib.search_stats_for_download(solr_query_spec,
                                                            limit=100)
        assert r.documentList.responseInfo.fullCount > 13000, r.documentList.responseInfo.fullCount


    def test_1_most_cited_direct(self):
        """
        """
        solr_query_spec = \
            opasQueryHelper.parse_search_query_parameters(citecount="5 in ALL", 
                                                          source_name=None,
                                                          source_code=None,
                                                          source_type=None, 
                                                          author=None,
                                                          title=None,
                                                          startyear=None,
                                                          highlightlimit=0, 
                                                          abstract_requested=False,
                                                          similar_count=0,
                                                          limit=25
                                                          )
    
        r, status = opasPySolrLib.search_stats_for_download(solr_query_spec,
                                                            limit=100)
        assert r.documentList.responseInfo.fullCount > 13000, r.documentList.responseInfo.fullCount

    def test_3_most_cited_direct_simple(self):
        """
        """
        solr_query_spec = \
            opasQueryHelper.parse_search_query_parameters(citecount="5", 
                                                          source_name=None,
                                                          source_code=None,
                                                          source_type=None, 
                                                          author=None,
                                                          title=None,
                                                          startyear=None,
                                                          highlightlimit=0, 
                                                          abstract_requested=False,
                                                          similar_count=0,
                                                          limit=25
                                                          )
    
        r, status = opasPySolrLib.search_stats_for_download(solr_query_spec,
                                                            session_info=session_info,
                                                            limit=100)
        assert r.documentList.responseInfo.fullCount > 1200, r.documentList.responseInfo.fullCount

    def test_3_most_cited_direct_simple2(self):
        """
        """
        solr_query_spec = \
            opasQueryHelper.parse_search_query_parameters(citecount="5 IN 10", 
                                                          source_name=None,
                                                          source_code=None,
                                                          source_type=None, 
                                                          author=None,
                                                          title=None,
                                                          startyear=None,
                                                          highlightlimit=0, 
                                                          abstract_requested=False,
                                                          similar_count=0,
                                                          limit=25
                                                          )
    
        r, status = opasPySolrLib.search_stats_for_download(solr_query_spec,
                                                            session_info=session_info,
                                                            limit=100)
        assert r.documentList.responseInfo.fullCount > 1500, r.documentList.responseInfo.fullCount

if __name__ == '__main__':
    unittest.main()
    client.close()
    