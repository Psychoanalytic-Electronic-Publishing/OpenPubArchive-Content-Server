#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, test_login
import opasAPISupportLib
import opasConfig
import opasCentralDBLib
import opasPySolrLib
import models


# Login!
sessID, headers, session_info = test_login()

ocd = opasCentralDBLib.opasCentralDB()

class TestPySolrBasedFunctions(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
   
    def test_1_metadata_get_videos(self):
        """
        Test
          1) list of video returns for metadata_get_videos
          2) List of sources by type
          3) 
        """
        data = opasPySolrLib.metadata_get_videos(src_type="Videos", pep_code=None, limit=opasConfig.DEFAULT_LIMIT_FOR_METADATA_LISTS, offset=0)
        # Confirm that the request-response cycle completed successfully.
        # check to make sure a known value is among the data returned
        dataList = [d['documentID'] for d in data[1] if 'documentID' in d]
        assert ('IPSAVS.001A.0001A' in dataList)
        data = opasAPISupportLib.metadata_get_source_info(src_type="videos")
        dataList = [d.documentID for d in data.sourceInfo.responseSet]
        assert ('IPSAVS.001A.0001A' in dataList)
        data = opasAPISupportLib.metadata_get_source_info(src_type="journal")
        dataList = [d.PEPCode for d in data.sourceInfo.responseSet]
        assert ('PAQ' in dataList)
        data = opasAPISupportLib.metadata_get_source_info(src_type="book")
        dataList = [d.PEPCode for d in data.sourceInfo.responseSet]
        assert ('ZBK075' in dataList)      

    # ################################################################################
    # The following tests are for functions not in PySolrLib, but they call important 
    #    functions for searching there, e.g.,
    #      search_stats_for_download
    #      search_text_qs
    # ################################################################################
    
    def test_2_get_vols(self):
        data = opasPySolrLib.metadata_get_volumes(source_type="journal")
        assert(len(data.volumeList.responseSet) > 2400)

    def test_3_get_most_viewed(self):
        # not in PySolrLib, but calls important functions for searching there.
        # make sure to look back a lot of years, because for testing, we just need data
        data, ret_status = opasPySolrLib.document_get_most_viewed(publication_period=100)
        assert (ret_status == (200, 'OK'))
        assert(data.documentList.responseInfo.fullCount > 1)
        
    def test_4_get_most_cited(self):
        data, ret_status = opasAPISupportLib.database_get_most_cited()
        assert (ret_status == (200, 'OK'))
        assert(data.documentList.responseInfo.fullCount > 1)

    def test_1_fetch_article(self):
        print (f"Current Session: ")
        data = opasAPISupportLib.documents_get_document("LU-AM.029B.0202A", session_info=session_info)
        # Confirm that the request-response cycle completed successfully.
        if data is None:
            print ("Data not found")
            assert ("doc not found" == True)
        else:
            assert (data.documents.responseInfo.fullCount == 1)
            assert (data.documents.responseSet[0].documentID == 'LU-AM.029B.0202A')
            assert (len(data.documents.responseSet[0].abstract)) > 0
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")