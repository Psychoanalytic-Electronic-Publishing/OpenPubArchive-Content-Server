#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326

""" 
OPAS - General Support Function Library

General purpose functions, e.g., string conversion (convenience) functions

"""
# 2019.0614.1 - Python 3.7 compatible
# 2020.0229.1 - pgnum_splitter added
   

from typing import Union, Optional, Tuple
import sys
import os.path
import re
import logging
logger = logging.getLogger(__name__)

import time
from datetime import datetime
import calendar
import email.utils

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2020.02.29"
__status__      = "Development"

# Python program to convert Roman Numerals 
# to Numbers 
  
# This function returns value of each Roman symbol 

def get_mod_date(file_path):
    """
    Get the date that a file was last modified
    """
    retVal = None
    try:
        retVal = os.path.getmtime(file_path)
    except IOError:
        # try where the script is running from instead.
        logger.info("%s not found.", file_path)
    except Exception as e:
        logger.fatal("%s.", e)

    return retVal

  
def roman_to_decimal(the_str: str) -> int:
    """
    Roman to Decimal from GeeksforGeeks
    
    >>> roman_to_decimal("MCMIV")
    1904
    
    >>> roman_to_decimal("vii")
    7

    >>> roman_to_decimal("42")
    42

    """
    def roman_letter_value(r):
        r = r.upper()
        
        if (r == 'I'): 
            return 1
        if (r == 'V'): 
            return 5
        if (r == 'X'): 
            return 10
        if (r == 'L'): 
            return 50
        if (r == 'C'): 
            return 100
        if (r == 'D'): 
            return 500
        if (r == 'M'): 
            return 1000
        return -1

    ret_val = 0
    i = 0
    try:
        ret_val = int(the_str)
    except ValueError as e:
        # must be roman, continue
        convert = True
    else:
        convert = False
        
  
    if convert:
        while (i < len(the_str)): 
      
            # Getting value of symbol s[i] 
            s1 = roman_letter_value(the_str[i]) 
      
            if (i+1 < len(the_str)): 
      
                # Getting value of symbol s[i+1] 
                s2 = roman_letter_value(the_str[i+1]) 
      
                # Comparing both values 
                if (s1 >= s2): 
      
                    # Value of current symbol is greater 
                    # or equal to the next symbol 
                    ret_val = ret_val + s1 
                    i = i + 1
                else: 
      
                    # Value of current symbol is greater 
                    # or equal to the next symbol 
                    ret_val = ret_val + s2 - s1 
                    i = i + 2
            else: 
                ret_val = ret_val + s1 
                i = i + 1
  
    return ret_val

def year_grabber(year_str: str):
    """
    From a string containing a year, possibly more than one, pull out the first.
    
    >>> year_grabber("abs1987")
    '1987'

    >>> year_grabber("1987a")
    '1987'
    
    >>> year_grabber("<y>1916&#8211;1917[1915&#8211;1917]</y>")
    '1916'
    
    """
    m = re.search(r"(?P<theyear>[12][0-9]{3,3})(.*)?", year_str)
    if m is not None:
        ret_val = m.group("theyear")
    else:
        ret_val = None

    return ret_val    
    
def first_item_grabber(the_str: str, re_separator_ptn=";|\-|&#8211;|,|\|", def_return=None):
    """
    From a string containing more than one item separated by separators, grab the first.
    
    >>> first_item_grabber("1987, A1899")
    '1987'

    >>> first_item_grabber("1987;A1899")
    '1987'
    
    >>> first_item_grabber("1916&#8211;1917[1915&#8211;1917]")
    '1916'
    
    """
    ret_val = re.split(re_separator_ptn, the_str)
    if ret_val != []:
        ret_val = ret_val[0]
    else:
        ret_val = def_return

    return ret_val    
    
    
def uppercase_andornot(boolean_str: str) -> str:
    ret_val = " ".join([x.upper() if x in ("or", "and", "not") else x for x in re.split("\s+(and|or|not)\s+", boolean_str)])
    return ret_val
    
def pgnum_splitter(pgnbr_str: str) -> tuple:
    """
    Break up a page number into alpha prefix, page number, alpha suffix
    
    >>> pgnum_splitter("RP007A")
    ('RP', 7, 'A')
    >>> pgnum_splitter("7")
    (None, 7, None)
    >>> pgnum_splitter("NP007Ba")
    ('NP', 7, 'Ba')
    
    """
    ret_val = (None, pgnbr_str, None)
    m = re.match("(?P<pgprefix>[A-z]{1,3})?(?P<pgnbr>[0-9]{1,8})(?P<pgsuffix>[A-z]{1,2})?", pgnbr_str)
    if m is not None:
        ret_val = m.groups()
        if ret_val[1] is not None:
            ret_val = ret_val[0], int(ret_val[1]), ret_val[2]
    return ret_val

def pgrg_splitter(pgrg_str: str) -> tuple:
    """
    Break up a stored page range into its components.
    
    >>> pgrg_splitter("1-5")
    ('1', '5')
    
    """
    retVal = (None, None)
    pgParts = pgrg_str.split("-")
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