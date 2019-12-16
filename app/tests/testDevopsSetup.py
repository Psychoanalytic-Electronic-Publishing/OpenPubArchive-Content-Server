#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

#  This test module is in development...

import sys
import os.path
import unittest

folder = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
if folder == "tests": # testing from within WingIDE, default folder is tests
    sys.path.append('../libs')
    sys.path.append('../config')
    sys.path.append('../../app')
else: # python running from should be within folder app
    sys.path.append('./libs')
    sys.path.append('./config')

# from main import app
from config.localsecrets import * 

class TestDevopsSetup(unittest.TestCase):
    """
    Tests for constants
    
    """   
    def test_0_(self):
        assert(API_PORT_MAIN is not None)
        assert(COOKIE_DOMAIN is not None)
        assert(BASEURL is not None)
        assert(SOLRURL is not None)
        assert(SOLRUSER is not None or SOLRUSER is None) # None for no user id needed
        assert(SOLRPW is not None or SOLRPW is None) # None if no user or password needed
        assert(DBPORT is not None)
        assert(DBHOST is not None)
        assert(DBUSER is not None)
        assert(DBPW is not None)
        assert(DBNAME is not None)
        assert(SSH_HOST is not None or SSH_HOST is None)
        #try:
            #a = API_PORT_MAIN
            #b = COOKIE_DOMAIN 
            #c = BASEURL
            #c = SOLRURL
            #c = SOLRUSER
            #c = SOLRPW
            #c = DBPORT
            #c = DBHOST
            #c = DBUSER
            #c = DBPW
            #c = DBPORT 
            #c = DBHOST
            #c = DBUSER
            #c = DBPW
            #c = DBNAME
            #c = SSH_HOST 

       
if __name__ == '__main__':
    unittest.main()    