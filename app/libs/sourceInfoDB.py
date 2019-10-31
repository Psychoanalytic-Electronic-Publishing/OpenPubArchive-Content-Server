#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
from __future__ import print_function

import sys
sys.path.append('../libs')

import json
import os.path

import PEPSourceDBData

# scriptSourcePath = os.path.dirname(os.path.realpath(__file__))

class SourceInfoDB (object):
    def __init__(self):
        self.sourceData = {}
        
        for n in PEPSourceDBData.pepsourceInfoRecords:
            try:
                self.sourceData[n["pepsrccode"]] = n
            except KeyError as e:
                print ("Missing Source Code Value in %s" % n)

    def lookupSourceCode(self, sourceCode):
        """
        Returns the dictionary entry for the source code or None
          if it doesn't exist.
        """
        dbEntry = self.sourceData.get(sourceCode, None)
        retVal = dbEntry
        return retVal
        

def main():
    import sys
    print ("Running in Python %s" % sys.version_info[0])
    # test load
    myDb = SourceInfoDB()
    print (myDb.sourceData["ANIJP-EL"])
    for key, item in myDb.sourceData.items():
        #print (key, item)
        print (item["sourcetitlefull"], item["publisher"])
    
    
if __name__ == "__main__":
    main()
    