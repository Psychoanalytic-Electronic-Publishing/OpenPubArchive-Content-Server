#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326

""" 
OPAS - General Support Function Library

2019.0614.1 - Python 3.7 compatible
    
"""
from typing import Union, Optional, Tuple
import sys
import re
import string
import logging
logger = logging.getLogger(__name__)

from lxml import etree
import opasXMLHelper as opasxmllib
import time
from datetime import datetime, timedelta
import calendar
import email.utils

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

def uppercase_andornot(string):
    ret_val = " ".join([x.upper() if x in ("or", "and", "not") else x for x in re.split("\s+(and|or|not)\s+", string)])
    return ret_val
    
def pgrg_splitter(pgRg):
    """
    Break up a stored page range into its components.
    
    >>> pgrg_splitter("1-5")
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
    
def format_http_timestamp(ts: Union[int, float, tuple, time.struct_time, datetime]) -> str:
    """Formats a timestamp in the format used by HTTP.
    The argument may be a numeric timestamp as returned by `time.time`,
    a time tuple as returned by `time.gmtime`, or a `datetime.datetime`
    object.
    >>> format_http_timestamp(1359312200)
    'Sun, 27 Jan 2013 18:43:20 GMT'
    """
    if isinstance(ts, (int, float)):
        time_num = ts
    elif isinstance(ts, (tuple, time.struct_time)):
        time_num = calendar.timegm(ts)
    elif isinstance(ts, datetime):
        time_num = calendar.timegm(ts.utctimetuple())
    else:
        raise TypeError(f'unknown timestamp type: {repr(ts)}')
    return email.utils.formatdate(time_num, usegmt=True)

def derive_author_mast(authorIDList):
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