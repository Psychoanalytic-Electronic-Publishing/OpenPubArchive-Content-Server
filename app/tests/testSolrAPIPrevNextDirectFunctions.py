#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests of the OPAS functions which depend on the Solr API.  (Direct, rather than Endpoint calls)

"""
#2020-08-24 Changed numeric counts to symbols from unitTestConfig

import unittest
import unitTestConfig
from unitTestConfig import base_plus_endpoint_encoded, headers
import opasPySolrLib
from opasCentralDBLib import opasCentralDB

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
        assert (prev_vol, match_vol, next_vol) == ({'value': '3', 'count': 44}, {'value': '4', 'count': 61}, {'value': '5', 'count': 48})
        
    def test_1D_get_next_and_prev_vol_6(self):
        prev_vol, match_vol, next_vol = opasPySolrLib.metadata_get_next_and_prev_vols(source_code="GAP", source_vol="6")
        assert (prev_vol, match_vol, next_vol) == ({'value': '5', 'count': 17}, {'value': '6', 'count': 12}, None)
            
    def test_1E_get_next_and_prev_vol_1(self):
        prev_vol, match_vol, next_vol = opasPySolrLib.metadata_get_next_and_prev_vols(source_code="GAP", source_vol="1")
        assert (prev_vol, match_vol, next_vol) == (None, {'value': '1', 'count': 16}, {'value': '2', 'count': 19})

    def test_1F_get_next_and_prev_vol_3(self):
        prev_vol, match_vol, next_vol = opasPySolrLib.metadata_get_next_and_prev_vols(source_code="GAP", source_vol="3")
        assert (prev_vol, match_vol, next_vol) == ({'value': '2', 'count': 19}, {'value': '3', 'count': 20}, {'value': '4', 'count': 25})

    def test_1G_get_next_and_prev_vol_10(self):
        prev_vol, match_vol, next_vol = opasPySolrLib.metadata_get_next_and_prev_vols(source_code="GAP", source_vol="10")
        assert (prev_vol, match_vol, next_vol) == (None, None, None)

    def test_1H_get_next_and_prev_vol_50(self):
        prev_vol, match_vol, next_vol = opasPySolrLib.metadata_get_next_and_prev_vols(source_code="JBP", source_vol="50")
        assert (prev_vol, match_vol, next_vol) == ({'value': '49', 'count': 7}, {'value': '50', 'count': 13}, {'value': '51', 'count': 8})

    def test_2_get_next_and_prev_articles(self):
        prev_art, match_art, next_art = opasPySolrLib.metadata_get_next_and_prev_articles(art_id="IJPSP.004.0445A")
        assert (prev_art, match_art, next_art) == ({'art_id': 'IJPSP.004.0432A', 'art_sourcecode': 'IJPSP', 'art_vol': '4', 'art_year': '2009', 'art_iss': '4'}, {'art_id': 'IJPSP.004.0445A', 'art_sourcecode': 'IJPSP', 'art_vol': '4', 'art_year': '2009', 'art_iss': '4'}, {'art_id': 'IJPSP.004.0449A', 'art_sourcecode': 'IJPSP', 'art_vol': '4', 'art_year': '2009', 'art_iss': '4'})
    
    def test_3_get_document_info(self):
        opasPySolrLib.document_get_info('PEPGRANTVS.001.0009A', fields='art_year, art_id, file_classification')
        {'art_year': '2015', 'art_id': 'PEPGRANTVS.001.0009A', 'file_classification': 'free'}
        
    def test_1I_get_next_and_prev_vol_100(self):
        prev_vol, match_vol, next_vol = opasPySolrLib.metadata_get_next_and_prev_vols(source_code="IJP", source_vol="100")
        assert (prev_vol, match_vol, next_vol) == ({'value': '99', 'count': 132}, {'value': '100', 'count': 144}, {'value': '101', 'count': 130})
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")