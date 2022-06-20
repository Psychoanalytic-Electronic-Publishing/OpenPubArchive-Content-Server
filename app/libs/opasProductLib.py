#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import logging
logger = logging.getLogger(__name__)

# import fnmatch

# import os.path
from contextlib import closing
import opasCentralDBLib

class SourceInfoDB(object):
    def __init__(self):
        self.sourceData = {}
        ocd = opasCentralDBLib.opasCentralDB()
        recs = ocd.get_productbase_data()
        for n in recs:
            try:
                self.sourceData[n["pepsrccode"]] = n
            except KeyError:
                logger.error("Missing Source Code Value in %s" % n)

    def lookupSourceCode(self, sourceCode):
        """
        Returns the dictionary entry for the source code or None
          if it doesn't exist.
        """
        dbEntry = self.sourceData.get(sourceCode, None)
        retVal = dbEntry
        return retVal

    def journalCodes(self):
        """
        Returns a list of all journalcodes
        Note: Test results need updating whenever new journal codes are included.

            >>> jrnlData = SourceInfoDB()
            >>> jrnlData.journalCodes()[:25]
            ['ADPSA', 'AFCVS', 'AIM', 'AJP', 'AJRPP', 'ANIJP-CHI', 'ANIJP-DE', 'ANIJP-EL', 'ANIJP-FR', 'ANIJP-IT', 'ANIJP-TR', 'ANRP', 'AOP', 'APA', 'APM', 'APS', 'BAFC', 'BAP', 'BIP', 'BJP', 'BPSIVS', 'CFP', 'CJP', 'CPS', 'DR']
        """
        retVal = [*self.sourceData]
        return retVal
    
    def volyears(self, source_code):
        """
        Returns a list of tuples with vol, year  for a journal code

            >>> jrnlData = SourceInfoDB()
            >>> jrnlData.volyears("PPTX")[:26]
            [(1, 1985), (2, 1986), (3, 1987), (3, 1988), (4, 1989), (5, 1990), (5, 1991), (6, 1992), (7, 1993), (8, 1994), (9, 1995), (10, 1996), (11, 1997), (12, 1998), (13, 1999), (14, 2000), (15, 2001), (16, 2002), (17, 2003), (18, 2004), (19, 2005), (20, 2006), (21, 2007), (22, 2008), (23, 2009), (24, 2010)]
        """
        retVal = []
        source_code = source_code.upper()
        ocd = opasCentralDBLib.opasCentralDB()
        recs = ocd.get_journal_vols(source_code)
        for rec in recs:
            try:
                retVal.append((rec["art_vol"], rec["art_year"]))
            except:
                print (f"Source Code not found:{source_code}")

        return retVal

#==================================================================================================
# Main Standalone (Test) Routines
#==================================================================================================
if __name__ == "__main__":

    import sys
    import doctest

    j = SourceInfoDB().journalCodes()
    #for n in j:
        #print (n)
    print (f"{len(j)} journals")
    doctest.testmod()
    print ("All Tests Complete")
    sys.exit()



