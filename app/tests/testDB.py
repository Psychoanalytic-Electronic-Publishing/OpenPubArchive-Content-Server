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
        assert(timing < 0.1)
    
    def test_count_open_sessions(self):
        ocd = opasCentralDB()
        count = ocd.count_open_sessions()
        assert(count > 0)

    def test_opasdb_getsources(self):
        ocd = opasCentralDB()
        sources = ocd.get_sources()
        assert(sources[0] > 100)
        sources = ocd.get_sources(source_code="IJP")
        assert(sources[0] == 1)
        sources = ocd.get_sources(src_type="journal")
        assert(sources[0] > 70)
           
        
if __name__ == '__main__':
    unittest.main()    