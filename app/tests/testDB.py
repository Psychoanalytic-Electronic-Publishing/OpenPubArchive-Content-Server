#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

import sys
sys.path.append('../libs')
sys.path.append('../config')
import unittest
import requests
from requests.utils import requote_uri
import urllib

from testConfig import base_api, base_plus_endpoint_encoded

class TestDatabase(unittest.TestCase):
    def test_count_open_sessions(self):
        from opasCentralDBLib import opasCentralDB
        ocd = opasCentralDB()
        count = ocd.count_open_sessions()
        assert(count > 0)

    def test_opasdb_getsources(self):
        from opasCentralDBLib import opasCentralDB
        ocd = opasCentralDB()
        sources = ocd.get_sources()
        assert(sources[0] > 100)
        sources = ocd.get_sources(source="IJP")
        assert(sources[0] == 1)
        sources = ocd.get_sources(source_type="journal")
        assert(sources[0] > 70)
       
       
        
if __name__ == '__main__':
    unittest.main()    