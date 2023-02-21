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

import signal


class TestSolrRecsWthoutArtID(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """

    def test_query_solr_erroneous_records_seen_in_some_builds(self):
        # 2023-01-21 Seen some records without an art_id but not the subpara kind from SE and GW.
        #  not sure where they come from but this will check for them.
        # Shouldn't return any records.
        r1, status = search_text(query="-art_id:* AND -id:GW* AND -id:SE*")
        r1_count = r1.documentList.responseInfo.fullCount
        assert(r1_count == 0)
                
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")