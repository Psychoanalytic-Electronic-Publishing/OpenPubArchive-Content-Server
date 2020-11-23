#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests of the OPAS functions which depend on the Solr API.  (Direct, rather than Endpoint calls)

"""
#2020-08-24 Changed numeric counts to symbols from unitTestConfig

import unittest
import opasAPISupportLib
import opasPySolrLib
from opasCentralDBLib import opasCentralDB
import unitTestConfig
from unitTestConfig import base_plus_endpoint_encoded, headers, session_id, session_info

class TestSolrAPIPrevNextDirectFunctions(unittest.TestCase):
    """
    Tests of functions getting the metadata from solr rather than the database
    
    """
    def test_0_min_max_from_db(self):
        ocd = opasCentralDB()
        ret_val = ocd.get_min_max_volumes("FD")
        print (ret_val)

    def test_1A_get_next_and_prev_vols_4(self):
        prev_vol, match_vol, next_vol = opasPySolrLib.metadata_get_next_and_prev_vols(source_code="IJPSP", source_vol="4")
        print (prev_vol, match_vol, next_vol)

    def test_1D_get_next_and_prev_vol_6(self):
        prev_vol, match_vol, next_vol = opasPySolrLib.metadata_get_next_and_prev_vols(source_code="GAP", source_vol="6")
        print (prev_vol, match_vol, next_vol)

    def test_1E_get_next_and_prev_vol_1(self):
        prev_vol, match_vol, next_vol = opasPySolrLib.metadata_get_next_and_prev_vols(source_code="GAP", source_vol="1")
        print (prev_vol, match_vol, next_vol)

    def test_1F_get_next_and_prev_vol_3(self):
        prev_vol, match_vol, next_vol = opasPySolrLib.metadata_get_next_and_prev_vols(source_code="GAP", source_vol="3")
        print (prev_vol, match_vol, next_vol)

    def test_1F_get_next_and_prev_vol_10(self):
        prev_vol, match_vol, next_vol = opasPySolrLib.metadata_get_next_and_prev_vols(source_code="GAP", source_vol="10")
        print (prev_vol, match_vol, next_vol)

    def test_2_get_next_and_prev_articles(self):
        prev_art, match_art, next_art = opasPySolrLib.metadata_get_next_and_prev_articles(art_id="IJPSP.004.0445A")
        print (prev_art, match_art, next_art)
    
    def test_3_get_document_info(self):
        opasPySolrLib.document_get_info('PEPGRANTVS.001.0009A', fields='art_year, art_id, file_classification')
        {'art_year': '2015', 'art_id': 'PEPGRANTVS.001.0009A', 'file_classification': 'free'}
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")