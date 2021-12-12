#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true
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

import unittest
#import requests
#from requests.utils import requote_uri
#import urllib

from unitTestConfig import base_api, base_plus_endpoint_encoded
from opasCentralDBLib import opasCentralDB

class TestDatabase(unittest.TestCase):
    def test_0_art_year(self):
        ocd = opasCentralDB()
        year = ocd.get_article_year("FD.026.0007A")
        assert(year == 2020)
    
    def test_1_art_year(self):
        import timeit
        timing = timeit.timeit('artyear = ocd.get_article_year("FD.026.0007A")', setup='from opasCentralDBLib import opasCentralDB; ocd = opasCentralDB()', number=10)
        print (f"timing: {timing}")
        assert(timing < 2.3) # 10 times slower running DB/Solr on AWS
    
    def test_count_open_sessions(self):
        ocd = opasCentralDB()
        count = ocd.count_open_sessions()
        assert(count > 0)

    def test_opasdb_getsources(self):
        ocd = opasCentralDB()
        sources = ocd.get_sources()
        assert(sources[0] > 100)
        sources = ocd.get_sources(src_code="IJP")
        assert(sources[0] == 1)
        sources = ocd.get_sources(src_type="journal")
        assert(sources[0] > 70)
        sources = ocd.get_sources(src_type="videos")
        assert(sources[0] >= 12)

    def test_opasdb_getsourcetypes(self):
        ocd = opasCentralDB()
        sources = ocd.get_sources()
        assert(sources[0] > 100)
        # unlike the API higher level function, both of these src_types--videos and stream--return streams on this direct call
        #  because the database vw_api_productbase_instance_counts view only has the stream information.
        #  see testAPIMetadata.test_3B_meta_videostreams to see the difference which is driven by
        #  query parameter streams
        sources = ocd.get_sources(src_type="videos")
        assert(sources[0] >= 12)
        sources = ocd.get_sources(src_type="stream")
        assert(sources[0] >= 12)

    # no longer applicable
    #def test_opasdb_abuse_too_many_opens(self):
        #fname = "test_code_abuse"
        #ocd = opasCentralDB()
        #assert(ocd.unpaired_connection_count == 0)
        #ocd.close_connection(caller_name=fname) # connection not yet open, no effect
        #assert(ocd.unpaired_connection_count == 0)
        #ocd.close_connection(caller_name=fname) # connection not yet open, no effect
        #assert(ocd.unpaired_connection_count == 0)
        #ocd.open_connection(caller_name=fname) # connection not yet open, opens it
        #assert(ocd.unpaired_connection_count == 0) # ok
        #ocd.open_connection(caller_name=fname) # second open!
        #assert(ocd.unpaired_connection_count == 1) # log unpaired open
        #ocd.open_connection(caller_name=fname)  
        #assert(ocd.unpaired_connection_count == 2) # another unpaired open
        #ocd.close_connection(caller_name=fname) # should close the open connection
        #ocd.close_connection(caller_name=fname) # no effect
        #ocd.close_connection(caller_name=fname) # no effect
        #assert(ocd.connected == False)
        #ocd.open_connection(caller_name=fname)  
        #assert(ocd.unpaired_connection_count == 0) # open
        #ocd.open_connection(caller_name=fname)  
        #assert(ocd.unpaired_connection_count == 1) # unpaired open
          
        
if __name__ == '__main__':
    unittest.main()    