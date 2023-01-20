#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326

""" 
OPAS - General Support Function Library

General purpose functions, e.g., string conversion (convenience) functions

2022-06-10 - Integrated functions from PEPXML...
             Still in progress, need to convert to snake_case too!

"""
# 2022.0101.1 - New date (str) to mysql function
# 2019.0614.1 - Python 3.7 compatible
# 2020.0229.1 - pgnum_splitter added

from typing import Union # , Optional, Tuple
import sys
import os.path
import re
import logging
import numbers
logger = logging.getLogger(__name__)

import time
from datetime import datetime
import datetime as dtime
from dateutil import parser
import calendar
import email.utils
import opasConfig
# import roman
import difflib
from lxml import etree


__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2022.06.07"
__status__      = "Development"

# defs needed for old code merge (at end)

reverseStr = lambda s: ''.join([s[i] for i in range(len(s)-1, -1, -1)])	# from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/119029

rgxNumStrSplit = re.compile("(?P<str1>[A-Z\-]*)(?P<num>[0-9]+)(?P<str2>[A-Z\-]*)", re.IGNORECASE)
rgxTrim = re.compile("^\s+(?P<cleanStr>.*?)\s+$")

#----------------------------------------------------------------------------------------
def	do_escapes(data, hasEscapes=0):
    ret_val = data
    if ret_val != None:
        if hasEscapes==0:
            if re.search(r'\\',	ret_val)	is not None:
                ret_val = re.sub(r'\\', r'\\\\',	ret_val)
        if re.search(r'"',	ret_val)	is not None:
            ret_val = re.sub(r'(?P<pre>([^\\]|\A))"', r'\1\\"', ret_val)
        # if doubled, take care of second one here, and first in next set
        # This extra effort has to be done because you have to watch for
        # already-escaped slashes!
        if re.search(r"''", ret_val) is not None:
            ret_val = re.sub(r"''",	r"'\\'", ret_val)
        if re.search(r"'", ret_val) is not None:
            ret_val = re.sub(r"(?P<pre>([^\\]|\A))'", r"\1\\'", ret_val)
    return ret_val

#----------------------------------------------------------------------------------------
def	do_re_escapes(data):
    """
    Escape periods and other regular expression chars in data
    """
    if data is not None:
        ret_val = re.escape(data)
    else:
        ret_val = ""

    return ret_val

class DocumentID(object):
    """
    Document ID and Volume ID recognition and normalization.

    Input Error Tolerance (new).  Hope it turns out to be a good idea
      it is nice to have all callers use proper case and precision (leading zeros)
      but mainly done to tolerate errors in the XML

      - Now case insensitive (all resulting IDs are uppercase)
      - Tolerates missing leading zeros and corrects

    >>> DocumentID(' LU-AM.005I.0025A.FIG001.jpg ')
    LU-AM.005I.0025A
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
    # document id regex (Note:Volume ID can be year, so 4 characters 2021-07-06)
    rxdocidc = re.compile("(?P<docid>\s*(?P<journalcode>[A-Z\_\-]{2,15})\.(?P<volume>[0-9]{1,4})(?P<volsuffix>[A-Z]?)\.(?P<pageextratype>(NP)?)(?P<pagestarttype>[R]?)(?P<pagestart>[0-9]{1,4})(?P<pagevariant>[A-Z]?))(\.P(?P<pagejumptype>[R]?)(?P<pagejump>[0-9]{1,4}))?\s*", flags=re.I)
    # vol id regex
    rxvolc = re.compile("(?P<docid>(?P<journalcode>[A-Z\_\-]{2,15})\.(?P<volume>[0-9]{1,4})(?P<volsuffix>[A-Z]?))", flags=re.I)
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

        # m = re.match("(?P<docid>\s*(?P<journalcode>[A-Z\_\-]{2,15})\.(?P<volume>[0-9]{1,3})(?P<volsuffix>[A-F]?)\.(?P<pagestarttype>[R]?)(?P<pagestart>[0-9]{1,4})(?P<pagevariant>[A-Z]?))(\.P(?P<pagejumptype>[R]?)(?P<pagejump>[0-9]{1,4}))?\s*", document_id)
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

    def get_page_number(self, default=None):
        "Returns the page number STR"
        if self.page_start is None:
            if default is None:
                logger.error(f"Document {self.document_id} does not have a parsable page_start")
                return '1' 
            else:
                return default
        else:
            pg_start = self.page_start.lstrip("0")
            return pg_start

class FileInfo(object):
    def __init__(self, filename): 
        """
        Get the date that a file was last modified
        """
        self.filename = filename
        self.timestamp_str = datetime.utcfromtimestamp(os.path.getmtime(filename)).strftime(opasConfig.TIME_FORMAT_STR)
        self.timestamp_obj = datetime.strptime(self.timestamp_str, opasConfig.TIME_FORMAT_STR)
        self.fileSize = os.path.getsize(filename)
        self.buildDate = time.time()

#-----------------------------------------------------------------------------
def add_smart_quote_search(search_value):
    ret_val = search_value

    if opasConfig.SMARTQUOTE_EXTENSION:
        # if there's an old style (typed) single quote, search for both smart and typed single quote
        bools = ["&&", "||", "AND", "OR"]
        if search_value is not None:
            if "'" in search_value:
                ret_val = re.sub("'", '’', search_value)
                if ret_val != search_value:
                    if any(boolstr in search_value for boolstr in bools):
                        ret_val = f"({ret_val})" # add parens
                        search_value = f"({search_value})"
                    # for now search both ways!
                    ret_val = f"({ret_val} || {search_value})"
            elif '’' in search_value:
                ret_val = re.sub('’', "'", search_value)
                if ret_val != search_value:
                    if any(boolstr in search_value for boolstr in bools):
                        ret_val = f"({ret_val})" # add parens
                        search_value = f"({search_value})"
                    # for now search both ways!
                    ret_val = f"({ret_val} || {search_value})"

    return ret_val        


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

def utctimestampstr_to_timestamp(timestampstr: str):
    """
    Convert UTC timestamp string to UTC timestamp
    
    >>> utctimestampstr_to_timestamp('2023-01-09T23:10:33Z')
    datetime.datetime(2023, 1, 9, 23, 10, 33, tzinfo=datetime.timezone.utc)
    
    """
    TIME_FORMAT='%Y-%m-%dT%H:%M:%S'
    ret_val = datetime.strptime(timestampstr, TIME_FORMAT + '%z')
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
    ret_val = (None, None)
    # pgParts = pgrg_str.split("-")
    # pgParts = re.split("[-–—]") # split for dash or ndash
    try:
        pgParts = [n.strip() for n in re.split("[-–—]", pgrg_str)]
    except:
        logger.error(f"pgrg_splitter: bad input: {pgrg_str}")
        ret_val = (None, None)
    else:
        try:
            pgStart = pgParts[0]
        except IndexError as e:
            logger.debug(f"pgrg_splitter (arg={pgrg_str}): pgStart index error: {e} PGParts: {pgParts}")
            pgStart = None
        try:
            pgEnd = pgParts[1]
        except IndexError as e:
            logger.debug(f"pgrg_splitter (arg={pgrg_str}): pgEnd index error: {e} PGParts: {pgParts}")
            pgEnd = None

    ret_val = (pgStart, pgEnd)    
    return ret_val

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
    ret_val = ""
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
                logger.error("Could not derive Author Mast name")

        ret_val = authorMast.strip()

    return ret_val
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

def datestr2mysql(date_text):
    dt = parser.parse(date_text)
    if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
        # no time included
        pass
    ret_val = dt.strftime("%Y%m%d%H%M%S")
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

#-----------------------------------------------------------------------------
def force_string_return_from_various_return_types(text_str, min_length=5):
    """
    Sometimes the return isn't a string (it seems to often be "bytes") 
      and depending on the schema, from Solr it can be a list.  And when it
      involves lxml, it could even be an Element node or tree.

    This checks the type and returns a string, converting as necessary.

    >>> force_string_return_from_various_return_types(["this is really a list",], min_length=5)
    'this is really a list'

    """
    ret_val = None
    if text_str is not None:
        if isinstance(text_str, str):
            if len(text_str) > min_length:
                # we have an abstract
                ret_val = text_str
        elif isinstance(text_str, list):
            if text_str == []:
                ret_val = None
            else:
                ret_val = text_str[0]
                if ret_val == [] or ret_val == '[]':
                    ret_val = None
        else:
            logger.error("Type mismatch on Solr Data. forceStringReturn ERROR: %s", type(ret_val))

        try:
            if isinstance(ret_val, etree._Element):
                ret_val = etree.tostring(ret_val)

            if isinstance(ret_val, bytes) or isinstance(ret_val, bytearray):
                logger.error("Byte Data")
                ret_val = ret_val.decode("utf8")
        except Exception as e:
            err = "forceStringReturn Error forcing conversion to string: %s / %s" % (type(ret_val), e)
            logger.error(err)

    return ret_val        

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
            logger.error(f"Error converting non-string term {e}. Perhaps data type issue.")
        else:
            std_arg = None

    if std_arg is not None:
        try:
            if " " not in arg:
                ret_val = True
            else:
                ret_val = False
        except Exception as e:
            logger.error(f"Error checking one term {e}. Perhaps data type issue.")

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
def default(val, defVal):

    if val != None:
        return val
    else:
        return defVal

#-----------------------------------------------------------------------------
def is_empty(arg):
    if arg is None:
        return True
    
    if not isinstance(arg, numbers.Number):
        if len(arg) == 0:
            return True
        else:
            return False
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

def split_long_lines(line, maxlen, splitter_ptn, joiner_ptn):
    if len(line) > maxlen:
        ret_val = joiner_ptn.join(re.split(splitter_ptn, line))
        #print (f"Split Line of len {len(line)}: {line}")
    else:
        ret_val = line 
        #print (f"No split for line of len {len(line)}: {line}")

    return ret_val

# ----------------------------------------------------------------------------------------
# the following routines from older codebase
# ----------------------------------------------------------------------------------------
def removeTrailingPunctAndSpaces(input_str, punct_set=[',', '.', ' ', ':', ';', ')', '\t', '"', "'"]):
    # Beginning in Python 2.2.3 you can do this
    #ret_val = input_str.rstrip(",.\t ")
    ret_val = ""
    if not is_empty(input_str):
        ret_val = input_str.rstrip()
        if ret_val != None and len(ret_val) > 0:
            while ret_val[-1] in punct_set:
                ret_val = ret_val[:-1]
                ret_val = ret_val.rstrip()

    return ret_val

# ----------------------------------------------------------------------------------------
def removeLetterPrefixAndSuffix(strArg):
    """
    >>> removeLetterPrefixAndSuffix("23f")
    ('', '23', 'f')
    """
    retValPrefix = ""
    retValBase = strArg
    retValSuffix = ""
    if isinstance(strArg, str):
        m = rgxNumStrSplit.match(strArg)
        if m != None:
            retValPrefix = m.group("str1")
            retValBase = m.group("num")
            retValSuffix = m.group("str2")
    retVal = (retValPrefix, retValBase, retValSuffix)
    return retVal

# ----------------------------------------------------------------------------------------
def removeLeadingPunctAndSpaces(input_str, punct_set=[',', '.', ' ', ':', ';', '(', '\t', '"', "'"]):
    # Beginning in Python 2.2.3 you can do this
    #ret_val = string.rstrip(input_str, ",.\t ")
    ret_val = ""
    if not is_empty(input_str):
        ret_val = input_str.lstrip()
        if ret_val != None and len(ret_val) > 0:
            while ret_val[0:1] in punct_set:
                ret_val = ret_val[1:]
                ret_val = ret_val.lstrip()

    return ret_val

# ----------------------------------------------------------------------------------------
def removeAllPunct(input_str, punct_set=[',', '.', ':', ';', '(', ')', '\t', r'/', '"', "'", "[", "]"]):
    # Beginning in Python 2.2.3 you can do this
    #ret_val = string.rstrip(input_str, ",.\t ")
    ret_val = ""
    if not is_empty(input_str):
        try:
            for n in input_str:
                if n not in punct_set:
                    ret_val = ret_val + n
        except Exception as e:
            print (f"Error: {e}")

    return ret_val

# --------------------------------------------------------------------------------
def removeExtraSpaces(self, s):
    """
    Remove Extra Spaces between Words

    removeExtraSpaces(word)
    Removes extra spaces between words and lead and trail space
    """
    s = "".join(s.split())
    return s

# ----------------------------------------------------------------------------------------
def trimPunctAndSpaces(input_str, punct_set=[',', '.', ' ', ':', ';', ')', '(', '\t', '"', "'"]):
    ret_val = removeLeadingPunctAndSpaces(input_str, punct_set)
    ret_val = removeTrailingPunctAndSpaces(ret_val, punct_set)
    return ret_val

#============================================================================================
def atoiYear(strArg):
    ret_val = 0
    if is_empty(strArg):
        ret_val = 0
    else:
        if isinstance(strArg, str):  # supports string and unicode Was if type(strArg) == type(""):
            strArg = trimPunctAndSpaces(strArg)
            if len(strArg) > 4:
                m = re.match("[^0-9]*?(?P<year>[1-2][0-9]{3,3})[^0-9]*?", strArg)
                if m != None:
                    ret_val = m.group("year")
                else:
                    ret_val = 0
            else:
                ret_val = strArg

            try:
                ret_val = int(ret_val)
            except Exception as e:
                print (f"Error: {e}")
                ret_val = 0
        else:
            ret_val = strArg

    return ret_val

# -------------------------------------------------------------------------------------------------------
def atoiNotEmpty(str_arg):
    ret_val = 0

    if type(str_arg) == type(1):
        # already a number
        ret_val = str_arg
    else:
        try:
            ret_val = int(str_arg)
        except:
            dummy1, numArg, dummy2 = removeLetterPrefixAndSuffix(str_arg)
            try:
                ret_val = int(numArg)
            except:
                #log_error("Bad value for atoi '%s'" % str_arg, displayAlso=1)
                ret_val = 0

    return ret_val

#----------------------------------------------------------------------------------------
def isAllDigits( str_arg ):
    """ Is the given string composed entirely of digits?  (convenience function for python isdigit)"""
    return str_arg.isdigit()

#----------------------------------------------------------------------------------------
def isNumeric(str_arg: str):
    """
    Is the string all numeric? (convenience function for python isdigit)
    """
    ret_val = False
    if isinstance(str_arg, str):
        ret_val = str_arg.isdigit()
    else:
        try:
            if str(str_arg).isdigit():
                ret_val = True
            elif isinstance(str_arg, int):
                ret_val = True
            else:
                logger.warning(f"{str_arg} arg is not string {type(str_arg)}")
        except Exception as e:
            logger.warning(f"{str_arg} arg is not string {type(str_arg)} {e}")
    
    return ret_val

#----------------------------------------------------------------------------------------
def trimNonDigits( str_arg ):
    """
    Trim off any leading or trailing non-digits.

    >>> trimNonDigits("ABC123E")
    '123'

    """
    retVal = trimLeadingNonDigits(str_arg)
    retVal = trimTrailingNonDigits(retVal)
    return retVal

#----------------------------------------------------------------------------------------
def trimLeadingNonDigits( str_arg ):
    """
    Remove leading characters that aren't digits

    >>> trimLeadingNonDigits("ABC123EFG")
    '123EFG'

    """
    retVal = str_arg
    pat = "[^A-z]"
    if str_arg is not None:
        if not isAllDigits(str_arg):
            list_split = re.split(pat, str_arg)
            retVal = str_arg[len(list_split[0]):]

    return retVal

#----------------------------------------------------------------------------------------
def trimTrailingNonDigits( str_arg ):
    """
    Remove Trailing characters that aren't digits

    >>> trimTrailingNonDigits("ABC123EFG")
    'ABC123'

    """

    retVal = str_arg
    if str_arg != None:
        retVal = reverseStr(str_arg)
        retVal = trimLeadingNonDigits(retVal)
        retVal = reverseStr(retVal)
    return retVal

#----------------------------------------------------------------------------------------
def trimNonDigits( str_arg ):
    """
    Trim off any leading or trailing non-digits.

    >>> trimNonDigits("ABC123E")
    '123'

    """
    retVal = trimLeadingNonDigits(str_arg)
    retVal = trimTrailingNonDigits(retVal)
    return retVal

# -------------------------------------------------------------------------------------------------------
def isRoman(roman_str):
    # Searching the input string in expression and
    # returning the boolean True if roman
    # if negative, assumes coded for roman
    ret_val = False
    if roman_str:
        if isinstance(roman_str, str):
            ret_val = bool(re.search(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", roman_str.upper()))
        elif isinstance(roman_str, int):
            ret_val = roman_str < 0 #  true if negative

    return ret_val

# -------------------------------------------------------------------------------------------------------
def is_roman_str(roman_str):
    # Searching the input string in expression and
    # returning the boolean True if roman
    ret_val = False
    if roman_str:
        if isinstance(roman_str, str):
            ret_val = bool(re.search(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", roman_str.upper()))

    return ret_val
# -------------------------------------------------------------------------------------------------------
def romanToInt(S: str) -> int:
    roman = {'I':1,'V':5,'X':10,'L':50,'C':100,'D':500,'M':1000}
    if isRoman(S):
        summ= 0
        for i in range(len(S)-1,-1,-1):
            num = roman[S[i]]
            if 3*num < summ: 
                summ = summ-num
            else: 
                summ = summ+num
    else:
        try:
            summ = int(S)
        except Exception as e:
            logger.warning(e)
            summ = 0       

    return summ

#----------------------------------------------------------------------------------------
def convertStringToArabic(numStr, stripChars=0):
    """
    Convert a string to an arabic number;

    Always returns numeric!
    12-09-2004: Changed default stripChars to 0, because otherwise a roman I was
    			stripped before processing!  Need to watch for programs that need
    			to now explicitly set stripChars to 1


    >>> convertStringToArabic("IV")
    4
    >>> convertStringToArabic("123")
    123
    >>> convertStringToArabic("MC")
    1100

    """
    num = 0

    if type(numStr) == type(1):
        num = numStr			# already numeric, arabic
    elif isinstance(numStr, str):
        numStr = trimPunctAndSpaces(numStr)
        if stripChars:
            numStr = trimNonDigits(numStr)

        if numStr != "":
            if isRoman(numStr.upper()):
                num = convRomanToArabic(numStr.upper())
            else:
                try:
                    num = int(numStr)
                except Exception as e:
                    ValueError("Invalid Roman number, and it's not integer. Cannot convert: %s" % numStr)

        else:
            # try not causing an exception on this.  If there's no numeric, then return None.
            logger.debug("Empty String.  convertStringToArabic Conversion error")
    else:
        try:
            num = int(numStr)
        except Exception as e:
            ValueError(e)

    if num is None:
        num = 0
        ValueError("Cannot convert: %s" % numStr)

    return num

#----------------------------------------------------------------------------------------
def convArabicToOrdLetter(arabicNum, lowerCase=0):
    """
    Convert the number to the corresponding letter, indexing the alphabet where A is 1
    If lowerCase == 1 then the base letter corresponding to 1 is "a" (lower case alpha)
    """
    if arabicNum > 26:
        raise ValueError("Overflow")
    if lowerCase ==1:
        baseNum = ord("a")-1
    else:
        baseNum = ord("A")-1
    return chr(arabicNum + baseNum)

#----------------------------------------------------------------------------------------
def convArabicToRoman(arabicNum, lCase=0):
    """
    Convet an arabic number to roman number format.

    >>> print (convArabicToRoman(9))
    IX
    >>> print (convArabicToRoman(400))
    CD
    >>> print (convArabicToRoman(1400))
    MCD
    >>> print (convArabicToRoman(3400))
    MMMCD
    >>> print (convArabicToRoman(1999))
    MCMXCIX
    >>> print (convArabicToRoman("1999"))
    MCMXCIX

    """
    try:
        arabicNum = int(arabicNum)
    except:
        try:
            arabicNum = convertStringToArabic(arabicNum)
        except TypeError as e:
            raise TypeError(e)
        except Exception as e:
            raise

    if arabicNum > 4999:   #was 4999, maybe wrong now?
        # use routine from the web--XXX Later, perhaps adapt this as THE routine?
        #return roman.toRoman(arabicNum) (only supports 0..4999 anyway)
        #print "Overflow: %s" % arabicNum
        raise ValueError("roman numbers must be 0..4999") # : #return `arabicNum`
        #raise "Overflow"

    arabicStr = repr(arabicNum)
    deg = len(arabicStr)
    arabicStrList = list(arabicStr)
    allStr = ""
    for a in arabicStrList:
        deg = deg - 1
        digiVal = int(a)

        if deg == 0:
            incr = "I"
            mid = "V"
            endp = "X"
        elif deg == 1:
            incr = "X"
            mid = "L"
            endp = "C"
        elif deg == 2:
            incr = "C"
            mid = "D"
            endp = "M"
        elif deg == 3:
            incr = "M"
            mid = "D"
            endp = "M"

        if digiVal < 4:
            digiStr = digiVal*incr
        elif digiVal == 4:
            digiStr = incr + mid
        elif digiVal == 5:
            digiStr = mid
        elif digiVal > 5 and digiVal < 9:
            digiStr = mid + (digiVal-5)*incr
        elif digiVal == 9:
            digiStr = incr + endp

        allStr += digiStr

    if lCase == 1:
        allStr = allStr.lower()

    return allStr

#----------------------------------------------------------------------------------------
def convRomanToArabic(romnumStr):
    """
    convert arg to arabic number

    >>> print (convRomanToArabic("ix"))
    9
    >>> convRomanToArabic("xcvii")
    97
    >>> convRomanToArabic("X")
    10

    """

    if isNumeric(romnumStr):
        return int(romnumStr)

    if not isRoman(romnumStr):
        raise ValueError(f"Not Roman: {romnumStr}")

    romnumStr = str(romnumStr).strip().upper()
    revromnumStr = list(romnumStr)
    revromnumStr.reverse()

    lastVal = None
    cumList = [0]
    val = 0
    for a in list(revromnumStr):
        if a == "I":
            val= 1
        elif a == "V":
            val= 5
        elif a == "X":
            val= 10
        elif a == "L":
            val= 50
        elif a == "C":
            val= 100
        elif a == "D":
            val= 500
        elif a == "M":
            val= 1000
        else:
            raise ValueError("Bad Roman Number: %s" % romnumStr)

        if cumList[-1] > val:
            cumList[-1] = cumList[-1] - val
        else:
            cumList.append(val)
    aval = 0
    for num in cumList:
        aval = aval + num
    return aval

#--------------------------------------------------------------------------------
def similarityText(string1, string2, accuracyLevel = 2):
    """
    A new similarity algorithm for comparing two strings

        AccuracyLevel = 0 Least Accurate
                        1 Middle
                        2 Most Accurate (and slowest)

        NOTE: As of 2008-01-25, now case insensitive and gets rid of noise words.

    NOTE: Returns 0.9999999 if identical...we don't want it to = 1, because that's reserved.

    >>> import opasDocuments
    >>> tgt = "Freud, S., Ferenczi, S., Abraham, K., Simmel, E., &amp; Jones, E. (1921). Psychoanalysis and War Neurosis. London: Int. Psychoanal. Press."
    >>> tgt2 = "Freud, S., Ferenczi, S., Abraham, K., Simmel, E. (1921). Psychoanalysis and War Neurosis. London: Int. Psychoanal. Press."
    >>> tgt3 = "Freud, S., Ferenczi, S., Abraham, K., Simmel, E., &amp; Jones, E. (1921b). Psychoanalysis and War Neurosis. London: Psychoanal. Press."
    >>> tgt4 = "Freud S. Abraham, K. &amp; Jones, E. (1921). Psychoanalysis. London: Int. Pergammon Press."
    >>> tgt5 = "Freud S. Abraham, K. and Jones, E. (1921a). Psychoanalysis. London: Int. Basic Books"
    >>> tgt6 = "Freud A. Abraham, K. &amp; Jones, E. (1921). Psychoanalysis. London: Int. Basic Books Inc."
    >>> tgt7 = "DEVEREUX, G. 'The Function of Alcohol in Mohave Society' Quarterly Journal of Studies on Alcohol 9 207-251 1948"
    >>> tgt8 = "DEVEREUX, G. 'The Mohave Male Puberty Rite' Samiksa, Journal of the Indian Psycho-Analytical Society 3 11-25 1949"
    >>> tgt9 = "Devereux, G. 'The Mohave Male Puberty Rite' Samiksa, Journal of the Indian Psycho-Analytical Society 3 11-25 1949"
    >>> tgt10 = "Freud, S., Ferenczi, S., Abraham, K., Simmel, E., &amp; Jones, E."
    >>> tgt11 = "Freud, S., Ferenczi, S., Abraham, K."
    >>> tgt12 = "Freud, S., Ferenczi, S., Abraham, K., Simmel, E."
    >>> tgt13 = "Freud, S., Ferenczi, S., Abracham, K., Simmel, E."
    >>> tgt14 = "Freud S. Ferenczi S. Abraham K. Simmel E."
    >>> tgt15 = "Freud S. Ferenczi S. Simmel E. Abraham K. "
    >>> tgt16 = "Freud S. Abraham, K. &amp; Jones, E."
    >>> tgt17 = "Freud S. Abraham K. and Jones E."
    >>> tgt18 = "Freud S. Abraham K. Jones E."

    #a = mangleText(tgt)
    #print a

    >>> print (round(similarityText(tgt, tgt2), 8))
    0.96078431
    >>> print (round(similarityText(tgt, tgt3), 8))
    0.97607656
    >>> print (round(similarityText(tgt2, tgt3), 8))
    0.93532338
    >>> print (round(similarityText(tgt3, tgt4), 8))
    0.70857143
    >>> print (round(similarityText(tgt4, tgt5), 8))
    0.85106383
    >>> print (round(similarityText(tgt5, tgt6), 8))
    0.95035461
    >>> print (round(similarityText(tgt6, tgt7), 8))
    0.24852071
    >>> print (round(similarityText(tgt7, tgt8), 7))
    0.3402062
    >>> print (similarityText(tgt8, tgt9))
    0.9999999
    >>> print (round(similarityText(tgt10, tgt11), 8))
    0.76712329
    >>> print (round(similarityText(tgt11, tgt12), 8))
    0.86153846
    >>> print (round(similarityText(tgt12, tgt13), 8))
    0.98666667
    >>> print (similarityText(tgt12, tgt14))
    0.9999999
    >>> print (round(similarityText(tgt12, tgt15), 7))
    0.7733333
    >>> print (similarityText(tgt16, tgt17))
    0.9999999
    >>> print (similarityText(tgt16, tgt18))
    0.9999999
    >>> print (similarityText(12, 12))
    0.9999999
    >>> print (similarityText("12", "12"))
    0.9999999
    >>> print (similarityText(0, 0))
    0.9999999
    >>> print (similarityText(0, None))
    0.0
    >>> print (similarityText(0, 2))
    0.0
    >>> print (similarityText(opasDocuments.VolumeNumber("3"), opasDocuments.VolumeNumber("5")))
    0.0
    >>> print (similarityText(opasDocuments.VolumeNumber("30"), opasDocuments.VolumeNumber("30")))
    0.9999999

    """
    # XXX if this doesn't keep "breaking" 90% for same items, we could remove connector words like and of the etc.
    def eliminateNoiseWords(noisy_str: str):
        noisy_str = removeAllPunct(noisy_str, punct_set=[',', '.', ':', ';', '(', ')', '\t', '"', "'"])
        noisy_str = noisy_str.lower()
        # eliminate noise words
        noisy_str = noisy_str.replace(" and ", " ")
        noisy_str = noisy_str.replace(" or ", " ")
        noisy_str = noisy_str.replace(" the ", " ")
        noisy_str = noisy_str.replace(" of ", " ")
        noisy_str = noisy_str.replace(" &amp ", " ")	# don't need ";" since punct is removed first.
        return noisy_str

    retVal = 0
    if isinstance(string1, int):
        string1 = str(string1)
        
    if isinstance(string2, int):
        string2 = str(string2)
        
    string1 = eliminateNoiseWords(string1)
    string2 = eliminateNoiseWords(string2)
    #print "String1/String2: ", string1, string2

    junkChars = lambda x: x in " ,.:()\t\"\'"
    s = difflib.SequenceMatcher(junkChars, string1, string2)
    #for tag, i1, i2, j1, j2 in s.get_opcodes():
    #	print ("%7s a[%d:%d] (%s) b[%d:%d] (%s)" % (tag, i1, i2, str1[i1:i2], j1, j2, str2[j1:j2]))
    if accuracyLevel == 2:
        retVal = s.ratio()
    elif accuracyLevel == 1:
        retVal = s.quick_ratio()
    else:
        retVal = s.real_quick_ratio()

    #print "Ratio: ", retVal
    if retVal == 1:
        retVal = opasConfig.MAXSRATIO # can't allow 1, that means unchangeable (manually entered)

    return retVal


# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    print ("Running in Python %s" % sys.version_info[0])

    import doctest
    doctest.testmod()    
    print ("opasGenSupportLib Tests Completed")
