#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

import unittest
import requests
import opasQueryHelper
import opasAPISupportLib

from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_info

class TestMost(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_100_most_cited_direct(self):
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
                                                          limit=200
                                                          )
    
        r, status = opasAPISupportLib.search_stats_for_download(solr_query_spec)
        print (r)

    def test_100_most_cited_direct_simple(self):
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
                                                          limit=200
                                                          )
    
        r, status = opasAPISupportLib.search_stats_for_download(solr_query_spec, session_info=session_info)
        print (r)

if __name__ == '__main__':
    unittest.main()
    client.close()
    