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

            >>> jrnlData = PEPJournalData()
            >>> jrnlData.journalCodes()
            ['PAQ', 'ANIJP-IT', 'FA', 'FD', 'PAH', 'PPSY', 'CPS', 'MPSA', 'SPR', 'RIP', 'ANIJP-DE', 'AOP', 'NP', 'BAFC', 'GW', 'JEP', 'ANRP', 'JCPTX', 'JAA', 'RPSA', 'IJPSP', 'SE', 'PPTX', 'IFP', 'BAP', 'PCS', 'PCAS', JOAP', 'PCT', 'AIM', 'JCP', 'ANIJP-FR', 'SGS', 'JICAP', 'GAP', 'IRP', 'PD', 'PDPSY', 'PI', 'BIP', 'IJAPS', 'AJP', 'RBP', 'CJP', 'PPERSP', 'IJP', 'APA', 'PSC', 'PSAR', 'PSP', 'PSW']
        """
        retVal = [*self.sourceData]
        return retVal
    
    def volyears(self, source_code):
        """
        Returns a list of tuples with vol, year  for a journal code

            >>> jrnlData = PEPJournalData()
            >>> jrnlData.volyears("PPTX")
            [(1, 1985), (2, 1986), (3, 1987), (3, 1988), (4, 1989), (5, 1990), (5, 1991), (6, 1992), (7, 1993), (8, 1994), (9, 1995), (10, 1996), (11, 1997), (12, 1998), (13, 1999), (14, 2000), (15, 2001), (16, 2002), (17, 2003), (18, 2004), (19, 2005), (20, 2006), (21, 2007), (22, 2008), (23, 2009), (24, 2010), (25, 2011), (26, 2012), (27, 2013), (28, 2014), (29, 2015), (30, 2016), (31, 2017), (32, 2018), (33, 2019)]

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
    for n in j:
        print (n)
    print (f"{len(j)} journals")
    doctest.testmod()
    sys.exit()



