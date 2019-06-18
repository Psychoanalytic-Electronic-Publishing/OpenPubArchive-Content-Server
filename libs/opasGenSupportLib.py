#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326

""" 
OPAS - General Support Function Library

2019.0614.1 - Python 3.7 compatible
    
"""
import sys
import string
import logging
from lxml import etree
import opasXMLHelper as opasxmllib

pyVer = 2
if (sys.version_info > (3, 0)):
    # Python 3 code in this block
    from io import StringIO
    pyVer = 3
else:
    # Python 2 code in this block
    import StringIO

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2019.6.15"
__status__      = "Development"


def getFirstValueOfDictItemList(dictName, keyName):
    """
    Get the first value of dictName[keyname] if it's a list
    Dictionary value fetch with error trapping. 
    
    >>> testVar = {}
    >>> testVar["item"] = ["1", "2", "3"]
    >>> getFirstValueOfDictItemList(testVar, "item")
    '1'
    >>> testVar["item"] = "1"
    >>> getFirstValueOfDictItemList(testVar, "item")
    '1'
    
    """
    retVal = None
    dictVal = dictName.get(keyName, None)
    if dictVal is not None:
        try:
            retVal = dictVal[0]
        except IndexError as e:
            print (e)
            if isinstance(dictVal, "<class 'str'>"):
                retVal = dictVal
            
    return retVal

def pgRgSplitter(pgRg):
    """
    Break up a stored page range into its components.
    
    >>> pgRgSplitter("1-5")
    ('1', '5')
    
    """
    retVal = (None, None)
    pgParts = pgRg.split("-")
    try:
        pgStart = pgParts[0]
        pgStart = pgStart.strip()
    except IndexError as e:
        pgStart = None
    try:
        pgEnd = pgParts[1]
        pgEnd = pgEnd.strip()
    except IndexError as e:
        pgEnd = None

    retVal = (pgStart, pgEnd)    
    return retVal
    

def deriveAuthorMast(authorIDList):
    """
    """
    
    retVal = ""
    authorMast = ""
    authCount = 0
    if authorIDList is not None:
        authTotalCount = len(authorIDList)
        for aut in authorIDList:
            authCount += 1
            try:
                authNamed = aut.split(",")
                authNamed.reverse()
                authMastName = " ".join(authNamed)
                if authCount == authTotalCount and authTotalCount > 1:
                    authorMast += " and " + authMastName
                elif authCount > 1:
                    authorMast += ", " + authMastName    
                else:
                    authorMast += authMastName    
            except Exception as e:
                authorMast += aut
                logging.warning("Could not derive Author Mast name")
            
        retVal = authorMast.strip()

    return retVal

# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    print ("Running in Python %s" % sys.version_info[0])
   
    import doctest
    doctest.testmod()    
    print ("Tests Completed")