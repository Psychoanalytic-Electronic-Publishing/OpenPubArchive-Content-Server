#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import opasCentralDBLib

ocd = opasCentralDBLib.opasCentralDB()

class TestStandaloneCrosstabFunctions(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """

    def test_get_most_viewed_crosstab(self):
        # this is used to load db data into Solr, so test call (not load)
        rows, data = ocd.get_most_viewed_crosstab(limit=10)
        count = 1
        for m in data:
            print (m)
            count += 1
            if count > 10:
                break
    
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")