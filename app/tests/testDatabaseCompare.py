#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from .utilityCompareTables import compareTables
#import compareTables

class TestDoDatabaseCompare(unittest.TestCase):
    """
    Runs the database compare program, which makes sure the configured tables
      are the same across development, test, and production databases
    
    """

    def test_1a(self):
        """
        """
        ret_val = compareTables.compare_tables()
        if ret_val > 0:
            print (80*"=")
            print (30*"*FINAL*")
            print ("Table differences found!")
        assert(ret_val == 0)
        
    def test_2(self):
        ret_val = compareTables.compare_critical_columns("api_productbase","basecode", "active")
        assert(ret_val == 0)

if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")