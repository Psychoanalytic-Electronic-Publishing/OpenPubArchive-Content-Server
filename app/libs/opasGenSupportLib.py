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
import localsecrets

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2021.01.09"
__status__      = "Development"

class DocumentID(object):
    """
    Document ID and Volume ID recognition and normalization.
    
    Input Error Tolerance (new).  Hope it turns out to be a good idea
      it is nice to have all callers use proper case and precision (leading zeros)
      but mainly done to tolerate errors in the XML
      
      - Now case insensitive (all resulting IDs are uppercase)
      - Tolerates missing leading zeros and corrects
    
    >>> DocumentID('LU-AM.005I.0025A.FIG001.jpg')
    LU-AM.005I.0025A
    >>> DocumentID('LU-AM.005I.0025A.FIG001')
    LU-AM.005I.0025A
    >>> DocumentID('LU-AM.005I.0025A.FIG 1')
    LU-AM.005I.0025A
    >>> DocumentID('AOP.001.0138.jpg')
    AOP.001.0138A
    >>> DocumentID('APA.01.00590.FIG 1.jpg')
    APA.001.0059A
    >>> DocumentID('APA.05.00050.FIG 12.jpg')
    APA.005.0005A

    >>> DocumentID('ZBK.074.R0007A')
    ZBK.074.R0007A
    >>> DocumentID('zbk.074.r0007a')
    ZBK.074.R0007A
    >>> DocumentID('ANIJP-FR.27.0001.PR0027')
    ANIJP-FR.027.0001A.PR0027
    >>> DocumentID('anijp-fr.27.0001.pr27')
    ANIJP-FR.027.0001A.PR0027
    >>> DocumentID('anijp-fr.27.01.pr27')
    ANIJP-FR.027.0001A.PR0027
    >>> DocumentID('ANIJP-FR.27.0001.P0027')
    ANIJP-FR.027.0001A.P0027
    >>> DocumentID('ANIJP-FR.27.0001')
    ANIJP-FR.027.0001A
    >>> DocumentID('IJP.027C.0001')
    IJP.027C.0001A
    >>> DocumentID('IJP.027.0001')
    IJP.027.0001A
    >>> DocumentID('IJP.027.0001B')
    IJP.027.0001B
    >>> DocumentID('ANIJP-FR.027.0001')
    ANIJP-FR.027.0001A
    >>> DocumentID('IJP.027A')
    IJP.027A
    >>> DocumentID('IJP.27')
    IJP.027
    >>> DocumentID('IJP.7.7')
    IJP.007.0007A
    >>> DocumentID('ijp.7.7')
    IJP.007.0007A

    """
    # document id regex
    rxdocidc = re.compile("(?P<docid>(?P<journalcode>[A-Z\_\-]{2,15})\.(?P<volume>[0-9]{1,3})(?P<volsuffix>[A-M]|S?)\.(?P<pageextratype>(NP)?)(?P<pagestarttype>[R]?)(?P<pagestart>[0-9]{1,4})(?P<pagevariant>[A-Z]?))(\.P(?P<pagejumptype>[R]?)(?P<pagejump>[0-9]{1,4}))?", flags=re.I)
    # vol id regex
    rxvolc = re.compile("(?P<docid>(?P<journalcode>[A-Z\_\-]{2,15})\.(?P<volume>[0-9]{1,3})(?P<volsuffix>[A-M]|S?))", flags=re.I)
    def __init__(self, document_id):
        #  See https://docs.google.com/document/d/1QmRG6MnM1jJOEq9irqCyoEY6Bt4U3mm8FY6TtZSt3-Y/edit#heading=h.mv7bvgdg7i7h for document ID information
        dirname, basename = os.path.split(document_id)
        if dirname is not None:
            document_id = basename
        self.document_id = None
        self.document_id_pagejump = None
        self.jrnlvol_id = None
        self.volume_id = None
        self.pagejump_id = None
        
        # m = re.match("(?P<docid>(?P<journalcode>[A-Z\_\-]{2,15})\.(?P<volume>[0-9]{1,3})(?P<volsuffix>[A-F]?)\.(?P<pagestarttype>[R]?)(?P<pagestart>[0-9]{1,4})(?P<pagevariant>[A-Z]?))(\.P(?P<pagejumptype>[R]?)(?P<pagejump>[0-9]{1,4}))?", document_id)
        m = self.rxdocidc.match(document_id)
        if m is not None:
            # use groupdict so we can set default for non participating groups
            m_groups = m.groupdict(default="")
            # journal code, volume, and pagestart cannot be None if we get here.  It matches
            self.docid_input = m_groups.get("docid")
            self.journal_code = m_groups.get("journalcode").upper()
            self.vol_suffix = m_groups.get("volsuffix").upper()
               
            self.volume = m_groups.get("volume")
            if self.volume != '':
                self.volume = f"{int(self.volume):03}"

            # self.volume can't be None and must be numeric or it wouldn't match pattern, so no worries
            self.volume_id = f"{self.volume}{self.vol_suffix}"

            self.page_start = m_groups.get("pagestart")
            if self.page_start != '':
                self.page_start = f"{int(self.page_start):04}"
                
            self.page_start_type_code = m_groups.get("pagestarttype").upper()
            if self.page_start_type_code == "R":
                self.page_start_type = "Roman"
            else:
                self.page_start_type = "Arabic"
                self.page_start_type_code = ""
                
            self.page_jump_type_code = m_groups.get("pagejumptype").upper()
            if self.page_jump_type_code == "R":
                self.page_jump_type = "Roman"
            else:
                self.page_jump_type = "Arabic"
                self.page_jump_type_code = ""

            self.page_extra_type = m_groups.get("pageextratype").upper()
            if self.page_extra_type != "NP":
                self.page_extra_type = ""
                
            # if there's an optional page number to jump too (P prefixed page number, not part of document ID per se)
            self.pagejump = m_groups.get("pagejump")
            if self.pagejump != '':
                self.pagejump = f"{int(self.pagejump):04}"
                self.pagejump_id  = f"P{self.page_jump_type_code}{self.pagejump}"

            self.page_variant = m_groups.get("pagevariant").upper()
            if self.page_variant == '':
                self.page_variant = 'A'

            # self.page_start can't be None or it wouldn't match pattern, so no worries
            self.page_start_id = f"{self.page_start_type_code}{self.page_start}{self.page_variant}"
            
            # normalized documentID
            self.document_id = f"{self.journal_code}.{self.volume_id}.{self.page_extra_type}{self.page_start_id}"
            self.jrnlvol_id = f"{self.journal_code}.{self.volume_id}"
            if self.pagejump != '':
                self.document_id_pagejump = f"{self.document_id}.{self.pagejump_id}"
        else:
            # m = re.match("(?P<docid>(?P<journalcode>[A-Z]{2,12})\.(?P<volume>[0-9]{1,3})(?P<volsuffix>[A-F]?))", document_id)
            m = self.rxvolc.match(document_id)
            if m is not None:
                m_groups = m.groupdict(default="")
                # this is a journal.vol id
                self.docid_input = m_groups.get("docid")
                self.journal_code = m_groups.get("journalcode").upper()
                self.vol_suffix = m_groups.get("volsuffix").upper()
                self.volume = m_groups.get("volume")
                if self.volume != '':
                    # self.volume can't be None and must be numeric or it wouldn't match pattern, so no worries
                    self.volume_id = f"{int(self.volume):03}{self.vol_suffix}"
                    self.jrnlvol_id = f"{self.journal_code}.{self.volume_id}"

    def __repr__(self):
        if self.document_id_pagejump is not None:
            return self.document_id_pagejump
        elif self.document_id is not None:
            return self.document_id
        elif self.jrnlvol_id is not None:
            return self.jrnlvol_id
        else:
            return "DocumentID Not recognized"

    def is_document_id(self):
        if self.document_id_pagejump is not None or self.document_id is not None:
            return True
        else:
            return False

    def is_jrnlvol_id(self):
        if self.jrnlvol_id is not None:
            return True
        else:
            return False

class FileInfo(object):
    def __init__(self, filename): 
        """
        Get the date that a file was last modified
        """
        self.filename = filename
        self.timestamp_str = datetime.utcfromtimestamp(os.path.getmtime(filename)).strftime(localsecrets.TIME_FORMAT_STR)
        self.timestamp_obj = datetime.strptime(self.timestamp_str, localsecrets.TIME_FORMAT_STR)
        self.fileSize = os.path.getsize(filename)
        self.buildDate = time.time()

def year_grabber(year_str: str):
    """
    From a string containing a year, possibly more than one, pull out the first.
    
    >>> year_grabber("1948194819491949195019501951")
    '1948'
    
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
    # pgParts = pgrg_str.split("-")
    # pgParts = re.split("[-–—]") # split for dash or ndash
    pgParts = [n.strip() for n in re.split("[-–—]", pgrg_str)]
    try:
        pgStart = pgParts[0]
    except IndexError as e:
        pgStart = None
    try:
        pgEnd = pgParts[1]
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
                logger.warning("Could not derive Author Mast name")
            
        retVal = authorMast.strip()

    return retVal
#-----------------------------------------------------------------------------
def string_to_list(strlist: str, sep=","):
    """
    Convert a comma separated string to a python list,
    removing extra white space between items.

    Returns list, even if strlist is the empty string
    EXCEPT if you pass None in.
    
    (2020-08-13 Moved from opasAPISupportLib since a general function)

    >>> string_to_list(strlist="term")
    ['term']

    >>> string_to_list(strlist="A, B, C, D")
    ['A', 'B', 'C', 'D']

    >>> string_to_list(strlist="A; B, C; D", sep=";")
    ['A', 'B, C', 'D']

    >>> string_to_list(strlist="")
    []

    >>> string_to_list(strlist=None)

    """
    if strlist is None:
        ret_val = None
    elif strlist == '':
        ret_val = []
    else: # always return a list
        ret_val = []
        try:
            if sep in strlist:
                # change str with cslist to python list
                ret_val = re.sub(f"\s*{sep}\s*", sep, strlist)
                ret_val = ret_val.split(sep)
            else:
                # cleanup whitespace around str
                ret_val = [re.sub("\s*(?P<field>[\S ]*)\s*", "\g<field>", strlist)]
        except Exception as e:
            logger.error(f"Error in string_to_list - {e}")

    return ret_val

def not_empty(arg):
    if arg is not None and arg != "":
        return True
    else:
        return False

def in_quotes(arg):
    """
    If string is quoted (must be at start and at end), return true
    
    >>> in_quotes('"animal or vegetable"')
    True
    >>> in_quotes('animal or vegetable')
    False
    >>> in_quotes("'animal or vegetable'")
    True
    
    """
    try:
        if isinstance(arg, str):
            if re.match(r"\s*([\"\']).*?\1\s*", arg):
                return True
            else:
                return False
        else:
            return False
    except Exception as e:
        logger.error(f"Exception {e}")
        return False

def in_brackets(arg):
    """
    If string is in brackets (must be at start and at end), return true
    
    >>> in_brackets('[("animal or vegetable")]')
    True
    >>> in_brackets('[(animal or vegetable)]')
    True
    >>> in_brackets("[('animal or vegetable')]")
    True
    >>> in_brackets("animal or vegetable")
    False
    >>> in_brackets("animal [(or)] vegetable")
    False
    >>> in_brackets("[animal (or)] vegetable")
    False
    
    """
    try:
        if isinstance(arg, str):
            if re.match(r"\[.*\]$", arg):
                return True
            else:
                return False
        else:
            return False
    except Exception as e:
        logger.error(f"Exception {e}")
        return False

def groups_balanced(arg):
    """
    Match [, {, and ( for balance
    
    >>> groups_balanced("(a) and (b)")
    True
    >>> groups_balanced("((a) and (b))")
    True
    >>> groups_balanced("((a) and (b)")
    False
    >>> groups_balanced(" [a] and [b]   ")
    True
    >>> groups_balanced("((a) and [(b)])")
    True
    >>> groups_balanced("((a) and [(b))]")
    False
    
    """
    arg = arg.strip()
    open_list = ["(", "[", "{"]
    close_list = [")", "]", "}"]    
    stack = []
    for i in arg:
        if i in open_list:
            stack.append(i)
        elif i in close_list:
            pos = close_list.index(i)
            if ((len(stack) > 0) and
                (open_list[pos] == stack[len(stack)-1])):
                stack.pop()
            else:
                return False

    if len(stack) == 0:
        return True
    else:
        return False

def parens_balanced(arg):
    arg = arg.strip()
    open_list = ["("]
    close_list = [")"]    
    stack = []
    for i in arg:
        if i in open_list:
            stack.append(i)
        elif i in close_list:
            pos = close_list.index(i)
            if ((len(stack) > 0) and
                (open_list[pos] == stack[len(stack)-1])):
                stack.pop()
            else:
                return False
            
    if len(stack) == 0:
        return True
    else:
        return False

def parens_outer(arg):
    """
    >>> parens_outer("(a) and (b)")
    False
    >>> parens_outer("((a) and (b))")
    True
    >>> parens_outer(" (a) and (b)   ")
    False
    >>> parens_outer("   ((a) and (b))    ")
    True
    """
    try:
        arg_stripped = arg.strip()
        if arg_stripped[0] == "(" and arg_stripped[-1] == ")":
            # should not be balanced now if there are outer ()
            return parens_balanced(arg_stripped[1:-1])
        else:
            return False
    except:
        return False
        
def in_parens(arg):
    """
    If string is in parens (must be at start and at end), return true
    
    >>> in_parens('("animal or vegetable")')
    True
    >>> in_parens('(animal or vegetable)')
    True
    >>> in_parens("('animal or vegetable')")
    True
    >>> in_parens("animal or vegetable")
    False
    >>> in_parens("animal (or) vegetable")
    False
    
    """
    try:
        if isinstance(arg, str):
            if re.match(r"\(.*\)$", arg):
                return True
            else:
                return False
        else:
            return False
    except Exception as e:
        logger.error(f"Exception {e}")
        return False

def one_term(arg):
    """
    >>> one_term("dog cat")
    False
    
    >>> one_term("dog")
    True
    
    >>> one_term("dog123rdd39--==")
    True
    """
    ret_val = True
    std_arg = arg
    if not isinstance(arg, str):
        try:
            std_arg = str(arg)
        except Exception as e:
            logger.warning(f"Error converting non-string term {e}. Perhaps data type issue.")
        else:
            std_arg = None

    if std_arg is not None:
        try:
            if " " not in arg:
                ret_val = True
            else:
                ret_val = False
        except Exception as e:
            logger.warning(f"Error checking one term {e}. Perhaps data type issue.")
        
    return ret_val

def is_boolean(arg):
    """
    Must be uppercase
    >>> is_boolean("a AND b")
    True
    
    >>> is_boolean("a OR b")
    True

    >>> is_boolean("a || b && cc")
    True

    >>> is_boolean("aor b")
    False
    
    """
    try:
        if isinstance(arg, str):
            if re.search(r"\s(AND|OR|\&\&|\|\)\s)", arg): 
                return True
            else:
                return False
        else:
            return False
    except Exception as e:
        logger.error(f"Exception {e}")
        return False

def range_list(arg):
    """
    Take a list of Solr like ranges, and return a boolean list of them
    The list can be embedded with almost any separator, e.g.:
        10 TO 20, 30 TO 40
        or
        10 to 20 OR 30 to 40
    
    >>> range_list("10 TO 20, 20 TO 30, 50 to 60" )
    '[10 TO 20] OR [20 TO 30] OR [50 TO 60]'

    >>> range_list("10 TO 20 OR 20 TO 30 or 50 to 60" )
    '[10 TO 20] OR [20 TO 30] OR [50 TO 60]'

    >>> range_list("10 TO 20" )
    '[10 TO 20]'
    
    >>> range_list("100 TO *" )
    '[100 TO *]'
    
    >>> range_list("* TO 100" )
    '[* TO 100]'
    
    >>> range_list("10 TO 20 OR 20 TO 30 or 50 to *" )
    '[10 TO 20] OR [20 TO 30] OR [50 TO *]'

    >>> range_list("10")
    ''

    """
    ret_val = ""
    mp2 = "(([0-9]+|\*) TO ([0-9]+|\*))"    
    ranges = re.findall(mp2, arg, flags=re.I)
    if len(ranges) > 0:
        range_list = ""
        for n in ranges:
            if range_list != "":
                range_list += " OR "
            range_list += f"[{n[0].upper()}]"
        ret_val = range_list
        ret_val = ret_val.strip(" ")

    return ret_val

#-----------------------------------------------------------------------------
def is_empty(arg):
    if arg is None or arg == "":
        return True
    else:
        return False


#----------------------------------------------------------------------------
def get_author_list_comma_separated(no_spaces_cited_list):
    """
    
      >>> test="Goldberg,E.L.,Myers,W.A.,Zeifman,I."
      >>> get_author_list_comma_separated(test)
      [('Goldberg,E.L.', 'Goldberg', 'E.L.'), ('Myers,W.A.', 'Myers', 'W.A.'), ('Zeifman,I.', 'Zeifman', 'I.')]
      >>> test="Goldberg,E.L."
      >>> get_author_list_comma_separated(test)
      [('Goldberg,E.L.', 'Goldberg', 'E.L.')]
      >>> test="Goldberg,E.L.,Myers,W.A. and Zeifman,I."
      >>> get_author_list_comma_separated(test)
      [('Goldberg,E.L.', 'Goldberg', 'E.L.'), ('Myers,W.A.', 'Myers', 'W.A.'), ('Zeifman,I.', 'Zeifman', 'I.')]
      >>> test="Goldberg, E.L., Myers,W.A., Zeifman,I."
      >>> get_author_list_comma_separated(test)
      [('Goldberg,E.L.', 'Goldberg', 'E.L.'), ('Myers,W.A.', 'Myers', 'W.A.'), ('Zeifman,I.', 'Zeifman', 'I.')]
      >>> test="Goldberg,E.L.Myers,W.A.Zeifman,I."
      >>> get_author_list_not_comma_separated(test)
      [('Goldberg,E.L.', 'Goldberg', 'E.L.'), ('Myers,W.A.', 'Myers', 'W.A.'), ('Zeifman,I.', 'Zeifman', 'I.')]
      
    """

    if " " in no_spaces_cited_list:
        no_spaces_cited_list = re.sub(" ", "", no_spaces_cited_list)
        
    rxpat = "(([^,]+?),((?:[A-Z]\.){1,3})(?:,|and)?)+?"

    ret_val = re.findall(rxpat, no_spaces_cited_list)
    # just first ones:
    # ret_val0 = [x[0][-1] for x in ret_val]
    return ret_val


#----------------------------------------------------------------------------
def get_author_list_not_comma_separated(no_spaces_cited_list):
    """
    
      >>> test="Goldberg,E.L.Myers,W.A.Zeifman,I."
      >>> get_author_list_not_comma_separated(test)
      [('Goldberg,E.L.', 'Goldberg', 'E.L.'), ('Myers,W.A.', 'Myers', 'W.A.'), ('Zeifman,I.', 'Zeifman', 'I.')]
      >>> test="Goldberg,E.L."
      >>> get_author_list_not_comma_separated(test)
      [('Goldberg,E.L.', 'Goldberg', 'E.L.')]
      >>> test="Goldberg, E.L. Myers,W.A. Zeifman,I."
      >>> get_author_list_not_comma_separated(test)
      [('Goldberg,E.L.', 'Goldberg', 'E.L.'), ('Myers,W.A.', 'Myers', 'W.A.'), ('Zeifman,I.', 'Zeifman', 'I.')]
      
    """

    if " " in no_spaces_cited_list:
        no_spaces_cited_list = re.sub(" ", "", no_spaces_cited_list)
        
    rxpat = "(([^,]+?),((?:[A-Z]\.){1,3}))+?"

    ret_val = re.findall(rxpat, no_spaces_cited_list)

    return ret_val

#----------------------------------------------------------------------------
def get_author_list_and_separated(cited_list):
    """
    
      >>> test="Goldberg,E.L. and Zeifman,I."
      >>> get_author_list_and_separated(test)
      [('Goldberg,E.L.', '', ''), ('Zeifman,I.', '', '')]
      >>> test="Goldberg,E.L."
      >>> get_author_list_and_separated(test)
      [('Goldberg,E.L.', '', '')]
      
      >>> test="Goldberg, E.L. and Myers,W.A. and Zeifman,I."
      >>> get_author_list_and_separated(test)
      [('Goldberg, E.L.', '', ''), ('Myers,W.A.', '', ''), ('Zeifman,I.', '', '')]
      
      >>> test="Eugene L. Goldberg, Wayne A. Myers and Israel Zeifman"
      >>> get_author_list_and_separated(test)
      [('Goldberg, E.L.', '', ''), ('Myers,W.A.', '', ''), ('Zeifman,I.', '', '')]
      

    """
    ret_val = None

    if " and " in cited_list:
        ret_val = cited_list.split(" and ")
    elif " AND " in cited_list:
        ret_val = cited_list.split(" and ")
    else:
        ret_val = cited_list.split(" ")
        
    if " " in ret_val:
        ret_val = re.sub(" ", "", ret_val)
    
    if ret_val is not None:
        ret_val = [(x, '', '') for x in ret_val]
        
    return ret_val

def another_citation_parser(arg):
    """
      >>> test="Eugene L. Goldberg, Wayne A. Myers and Israel Zeifman"
      >>> another_citation_parser(test)
      ['Eugene L. Goldberg', ' Wayne A. Myers', 'Israel Zeifman']
      
      >>> test="Goldberg, E.L. and Myers,W.A. and Zeifman,I."
      >>> another_citation_parser(test)

    """
    # are there initials?
    pat1 = "(\w{2,}\s(:?(\w\.)*?)?\s\w{3,})+"
    pat2 = "(?:and\s)((\w{2,}\s(?:(\w\.){0,2}\s?)\w{3,}))"
    names = re.split(",|\s+and\s+", arg, re.I)
    print (names)
    ret_val1 = re.findall(pat1, arg, flags=re.I)
    ret_val2 = re.findall(pat2, arg, flags=re.I)
    return ret_val1, ret_val2
    
def split_long_lines(line, maxlen, splitter_ptn, joiner_ptn):
    if len(line) > maxlen:
        ret_val = joiner_ptn.join(re.split(splitter_ptn, line))
        #print (f"Split Line of len {len(line)}: {line}")
    else:
        ret_val = line 
        #print (f"No split for line of len {len(line)}: {line}")
        
    return ret_val

# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    print ("Running in Python %s" % sys.version_info[0])
   
    import doctest
    doctest.testmod()    
    print ("opasGenSupportLib Tests Completed")
    