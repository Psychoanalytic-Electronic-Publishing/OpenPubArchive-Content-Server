#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
from __future__ import print_function

import json
import os.path

SOURCEINFODBFILENAME = 'PEPSourceInfo.json'
scriptSourcePath = os.path.dirname(os.path.realpath(__file__))
dbPath = os.path.join(scriptSourcePath, SOURCEINFODBFILENAME)

class SourceInfoDB (object):
    def __init__(self, journalInfoFile=dbPath):
        self.journalInfoFile = journalInfoFile
        self.sourceData = self.readSourceInfoDB(journalInfoFile)
        
    def readSourceInfoDB(self, journalInfoFile):
        """
        The source info DB is a journal basic info "database" in json
        
        Read as is since this JSON file can be simply and quickly exported
             from the PEP issn table in mySQL used in data conversion
    
        """
        retVal = {}
        with open(journalInfoFile) as f:
            journalInfo = json.load(f)
    
        # turn it into a in-memory dictionary indexed by jrnlcode;
        # in 2019, note that there are only 111 records
        for n in journalInfo["RECORDS"]:
            retVal[n["pepsrccode"]] = n
    
        return retVal

def main():
    
    # test load
    myDb = SourceInfoDB()
    print (myDb.sourceData["AJP"])
    
    
if __name__ == "__main__":
    main()
    