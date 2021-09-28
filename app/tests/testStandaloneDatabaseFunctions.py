#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import opasAPISupportLib
import opasConfig
import opasQueryHelper
import opasCentralDBLib
import models

ocd = opasCentralDBLib.opasCentralDB()

class TestStandaloneDatabaseFunctions(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """

    def test_get_articles_newer_than(self):
        data = ocd.get_articles_newer_than(days_back=30)
        print (data)
        
    def test_get_articles_newer_than_2(self):
        data = ocd.get_articles_newer_than(days_back=10)
        print (data)
        
    def test_get_articles_newer_than_3(self):
        data = ocd.get_articles_newer_than(days_back=5)
        print (data)

if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")