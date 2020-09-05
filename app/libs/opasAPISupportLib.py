#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
# doctest_ellipsis.py

"""
opasAPISupportLib

This library is meant to hold the 'meat' of the API based Solr queries and other support 
functions to keep the FastAPI definitions smaller, easier to read, and more manageable.

Also, some of these functions are reused in different API calls.

#TODO: Should switch back to using pysolr, rather than solrpy.  solrpy is not being maintained
       and pysolr has leapfrogged it (and now works for secured Solr installs).

"""
#Revision Notes:
    #2019.0614.1 - Python 3.7 compatible.  Work in progress.
    #2019.1203.1 - fixed authentication value error in show abstract call
    #2019.1222.1 - Finished term_count_list function for endpoint termcounts
    #2020.0224.1 - Added biblioxml
    #2020.0226.1 - Support TOC instance as exception for abstracting extraction (extract_abstract_from_html)
                # Python 3 only now
    #2020.0401.1 - Set it so user-agent is optional in session settings, in case client doesn't supply it (as PaDS didn't)
    #2020.0423.1 - database_get_most_cited fixes, confusion between publication_period, and period, sorted.
    #2020.0426.1 - Doc level testing of functions and doctest cleanup...
                # setting doctests so they pass even though the data varies in the DB
                # all tests now pass at least with a full database load.
                # Note: ellipses in doctest now working, see configuration in main and in doctests, 
                # e.g., document_get_info (line 417) and database_get_most_viewed (line 525)
    #2020.0505.1 Removed redundant param document_type from database_get_most_viewed (source_type already there)

    #2020.0530.1 Updated getmostviewed routine and all support for it to use the new in place updated art_view count fields in Solr
                # rather than using the values from the database, as before.  Moving the data to Solr allows these values to be
                # integrated with a solr query.

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2020, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2020.0601.1"
__status__      = "Development"

import os
import os.path
import sys
# import shlex

sys.path.append('./solrpy')
sys.path.append('./libs/configLib')

# print(os.getcwd())
import http.cookies
import re
import secrets
import socket, struct
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.responses import Response
#from starlette.status import HTTP_200_OK, \
                                #HTTP_400_BAD_REQUEST, \
                                #HTTP_401_UNAUTHORIZED, \
                                #HTTP_403_FORBIDDEN, \
                                #HTTP_404_NOT_FOUND, \
                                #HTTP_500_INTERNAL_SERVER_ERROR, \
                                #HTTP_503_SERVICE_UNAVAILABLE
import time
# used this name because later we needed to refer to the module, and datetime is also the name
#  of the import from datetime.
import datetime as dtime 
# import datetime
from datetime import datetime
# from typing import Union, Optional, Tuple, List
# from enum import Enum
# import pymysql
# import s3fs # read s3 files just like local files (with keys)

import opasConfig
import localsecrets
from localsecrets import CLIENT_DB

import opasFileSupport
opas_fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET)

from localsecrets import BASEURL, SOLRURL, SOLRUSER, SOLRPW, DEBUG_DOCUMENTS, SOLR_DEBUG, CONFIG, COOKIE_DOMAIN  
# from opasConfig import OPASSESSIONID
# import configLib.opasCoreConfig as opasCoreConfig
from configLib.opasCoreConfig import solr_docs, solr_authors, solr_gloss, solr_docs_term_search, solr_authors_term_search
from stdMessageLib import COPYRIGHT_PAGE_HTML  # copyright page text to be inserted in ePubs and PDFs
from configLib.opasCoreConfig import EXTENDED_CORES

# from fastapi import HTTPException

# Removed support for Py2, only Py3 supported now
pyVer = 3
from io import StringIO
import solrpy as solr
import lxml
import logging
logger = logging.getLogger(__name__)

from lxml import etree
# from pydantic import BaseModel
from pydantic import ValidationError

# from ebooklib import epub              # for HTML 2 EPUB conversion
from xhtml2pdf import pisa             # for HTML 2 PDF conversion

# note: documents and documentList share the same internals, except the first level json label (documents vs documentlist)
import models

import opasXMLHelper as opasxmllib
import opasQueryHelper
import opasGenSupportLib as opasgenlib
import opasCentralDBLib
import schemaMap
import opasDocPermissions as opasDocPerm

count_anchors = 0

TIME_FORMAT_STR = '%Y-%m-%dT%H:%M:%SZ'

def authorized(session_info, art_id):
    if session_info.authenticated == True:
        ret_val = True
    else:
        pads
#-----------------------------------------------------------------------------
def get_basecode(document_id):
    """
    Get basecode from document_id
    """
    ret_val = None
    try:
        parts = document_id.split(".")
        ret_val = parts[0]
    except Exception as e:
        logger.error(f"Bad document_id {document_id} to get_basecode. {e}")

    #TODO: later we might want to check for special book basecodes.

    return ret_val
#-----------------------------------------------------------------------------
def numbered_anchors(matchobj):
    """
    Called by re.sub on replacing anchor placeholders for HTML output.  This allows them to be numbered as they are replaced.
    """
    global count_anchors
    JUMPTOPREVHIT = f"""<a onclick='scrollToAnchor("hit{count_anchors}");event.preventDefault();'>🡄</a>"""
    JUMPTONEXTHIT = f"""<a onclick='scrollToAnchor("hit{count_anchors+1}");event.preventDefault();'>🡆</a>"""

    if matchobj.group(0) == opasConfig.HITMARKERSTART:
        count_anchors += 1
        if count_anchors > 1:
            #return f"<a name='hit{count_anchors}'><a href='hit{count_anchors-1}'>🡄</a>{opasConfig.HITMARKERSTART_OUTPUTHTML}"
            return f"<a name='hit{count_anchors}'>{JUMPTOPREVHIT}{opasConfig.HITMARKERSTART_OUTPUTHTML}"
        elif count_anchors <= 1:
            return f"<a name='hit{count_anchors}'> "
    if matchobj.group(0) == opasConfig.HITMARKEREND:
        return f"{opasConfig.HITMARKEREND_OUTPUTHTML}{JUMPTONEXTHIT}"

    else:
        return matchobj.group(0)

#-----------------------------------------------------------------------------
def get_max_age(keep_active=False):
    if keep_active:    
        ret_val = opasConfig.COOKIE_MAX_KEEP_TIME    
    else:
        ret_val = opasConfig.COOKIE_MIN_KEEP_TIME     
    return ret_val  # maxAge

##-----------------------------------------------------------------------------
#def string_to_list(strlist: str, sep=","):
    #"""
    #Convert a comma separated string to a python list,
    #removing extra white space between items.

    #Returns list, even if strlist is the empty string
    #EXCEPT if you pass None in.

    #>>> string_to_list(strlist="term")
    #['term']

    #>>> string_to_list(strlist="A, B, C, D")
    #['A', 'B', 'C', 'D']

    #>>> string_to_list(strlist="A; B, C; D", sep=";")
    #['A', 'B, C', 'D']

    #>>> string_to_list(strlist="")
    #[]

    #>>> string_to_list(strlist=None)

    #"""
    #if strlist is None:
        #ret_val = None
    #elif strlist == '':
        #ret_val = []
    #else: # always return a list
        #ret_val = []
        #try:
            #if sep in strlist:
                ## change str with cslist to python list
                #ret_val = re.sub(f"\s*{sep}\s*", sep, strlist)
                #ret_val = ret_val.split(sep)
            #else:
                ## cleanup whitespace around str
                #ret_val = [re.sub("\s*(?P<field>\S*)\s*", "\g<field>", strlist)]
        #except Exception as e:
            #logger.error(f"Error in string_to_list - {e}")

    #return ret_val

#-----------------------------------------------------------------------------
def get_session_info(request: Request,
                     response: Response, 
                     access_token=None,
                     expires_time=None, 
                     keep_active=False,
                     force_new_session=False,
                     user=None):
    """
    Get session info from cookies, or create a new session if one doesn't exist.
    Return a sessionInfo object with all of that info, and a database handle

    """
    session_id = get_session_id(request)
    client_session_id = request.headers.get("client-session", None)
    client_id = int(request.headers.get("client-id", '0'))
    try:
        client_dict = CLIENT_DB[client_id]
        client_name = client_dict.get("api-client-name", None)
    except:
        client_dict = {}
        client_name = "Unknown"
    
    logger.debug("Get Session Info, Session ID via GetSessionID: %s", session_id)
    expiration_time = get_expiration_time(request)

    if client_session_id is not None:
        ocd = opasCentralDBLib.opasCentralDB(client_session_id, access_token=None)
        session_info = ocd.get_session_from_db(client_session_id)
        if session_info is None:
            # right now this is going to be PEP-Web and PaDS.  
            ret_val, session_info = ocd.save_session(client_session_id,
                                                     userID=0,
                                                     userIP=request.client.host,
                                                     connected_via=request.headers.get("user-agent", "Not Specified"),
                                                     apiClientID=client_id,
                                                     apiClientSession=True, 
                                                     username=client_name) # returns save status and a session
                                                                            # object (matching what was sent to the db)
            
        
    else:
        if session_id is None or session_id=='' or force_new_session:  # we need to set it
            # get new sessionID...even if they already had one, this call forces a new one
            logger.debug("session_id is none (or forcedNewSession).  We need to start a new session.")
            ocd, session_info = start_new_session(response, request, access_token, keep_active=keep_active, user=user)
    
        else: # we already have a session_id, no need to recreate it.
            # see if an access_token is already in cookies
            access_token = get_access_token(request)
            logger.debug(f"session_id {session_id} is already set.")
            try:
                ocd = opasCentralDBLib.opasCentralDB(session_id, access_token, expiration_time)
                session_info = ocd.get_session_from_db(session_id)
                if session_info is None:
                    # this is an error, and means there's no recorded session info.  Should we create a s
                    #  session record, return an error, or ignore? #TODO
                    # try creating a record
                    ocd, session_info = start_new_session(response, request, access_token=access_token, keep_active=keep_active, user=user) 
                    username="NotLoggedIn"
                    ret_val, session_info = ocd.save_session(session_id,
                                                             userID=0,
                                                             userIP=request.client.host,
                                                             connected_via=request.headers.get("user-agent", "Not Specified"),
                                                             username=username ) # returns save status and a session
                                                                                    # object (matching what was sent to the db)
    
            except ValidationError as e:
                logger.error("Validation Error: %s", e.json())             
    
    logger.debug("getSessionInfo: %s", session_info)
    return ocd, session_info

def is_session_authenticated(request: Request, resp: Response):
    """
    Look to see if the session has been marked authenticated in the database
    """
    ocd, sessionInfo = get_session_info(request, resp)
    # sessionID = sessionInfo.session_id
    # is the user authenticated? if so, loggedIn is true
    ret_val = sessionInfo.authenticated
    return ret_val

def ip2long(ip):
    """
    Convert an IP string to long

    >>> ip2long("127.0.0.1")
    2130706433
    >>> socket.inet_ntoa(struct.pack('!L', 2130706433))
    '127.0.0.1'
    """
    packedIP = socket.inet_aton(ip)
    return struct.unpack("!L", packedIP)[0]    

#-----------------------------------------------------------------------------
def extract_abstract_from_html(html_str, xpath_to_extract=opasConfig.HTML_XPATH_ABSTRACT): # xpath example: "//div[@id='abs']"
    # parse HTML
    htree = etree.HTML(html_str)
    ret_val = htree.xpath(xpath_to_extract)
    # TOC's should be passed through "whole" (well, just the body, since headers will be added.)
    if ret_val == []: # see if it's a TOC
        ret_val = htree.xpath(opasConfig.HTML_XPATH_TOC_INSTANCE) # e.g, "//div[@data-arttype='TOC']"
        if ret_val != []:
            ret_val = htree.xpath(opasConfig.HTML_XPATH_DOC_BODY) # e.g., "//div[@class='body']"
    # make sure it's a string
    ret_val = force_string_return_from_various_return_types(ret_val)

    return ret_val

#-----------------------------------------------------------------------------
def start_new_session(resp: Response, request: Request, session_id=None, access_token=None, keep_active=None, user=None):
    """
    Create a new session record and set cookies with the session

    Returns database object, and the sessionInfo object

    If user is supplied, that means they've been authenticated.

    This should be the only place to generate and start a new session.
    """
    logger.debug("************** Starting a new SESSION!!!! *************")
    # session_start=datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    max_age = get_max_age(keep_active)
    token_expiration_time=datetime.utcfromtimestamp(time.time() + max_age) # .strftime('%Y-%m-%d %H:%M:%S')
    if session_id is None:
        session_id = secrets.token_urlsafe(16)
        logger.info("startNewSession assigning New Session ID: {}".format(session_id))

    # Try 
    # set_cookies(resp, session_id, access_token, token_expires_time=token_expiration_time)
    # get the database Object
    ocd = opasCentralDBLib.opasCentralDB()
    # save the session info
    if user:
        username=user.username
        ret_val, sessionInfo = ocd.save_session(session_id=session_id, 
                                                username=user.username,
                                                userID=user.user_id,
                                                authorized_peparchive=user.authorized_peparchive,
                                                authorized_pepcurrent=user.authorized_pepcurrent,
                                                expiresTime=token_expiration_time,
                                                userIP=request.client.host, 
                                                connected_via=request.headers.get("user-agent", "Not Specified"),
                                                accessToken = access_token
                                                )
    else:
        username="NotLoggedIn"
        ret_val, sessionInfo = ocd.save_session(session_id, 
                                                userID=0,
                                                expiresTime=token_expiration_time,
                                                userIP=request.client.host, 
                                                connected_via=request.headers.get("user-agent", "Not Specified"),
                                                username=username)  # returns save status and a session object 
                                                                    # (matching what was sent to the db)

    resp.set_cookie(key=opasConfig.OPASSESSIONID,
                    value=session_id,
                    max_age=max_age, expires=None, 
                    path="/",
                    secure=False, 
                    httponly=False)

    # return the object so the caller can get the details of the session
    return ocd, sessionInfo

#-----------------------------------------------------------------------------
def get_session_id(request):
    # this will be a sesson ID from the client--must be in every call!
    ret_val = request.cookies.get(opasConfig.OPASSESSIONID, None)
    if ret_val is None:
        ret_val = request.headers.get(opasConfig.CLIENTSESSIONID, None)

    return ret_val
#-----------------------------------------------------------------------------
def get_access_token(request):
    ret_val = request.cookies.get(opasConfig.OPASACCESSTOKEN, None)
    return ret_val

#-----------------------------------------------------------------------------
def get_expiration_time(request):
    ret_val = request.cookies.get(opasConfig.OPASEXPIRES, None)
    return ret_val
#-----------------------------------------------------------------------------
def check_solr_docs_connection():
    """
    Queries the solrDocs core (i.e., pepwebdocs) to see if the server is up and running.
    Solr also supports a ping, at the corename + "/ping", but that doesn't work through pysolr as far as I can tell,
    so it was more straightforward to just query the Core. 

    Note that this only checks one core, since it's only checking if the Solr server is running.

    >>> check_solr_docs_connection()
    True

    """
    if solr_docs is None:
        return False
    else:
        try:
            results = solr_docs.query(q = "art_id:{}".format("APA.009.0331A"),  fields = "art_id, art_vol, art_year")
        except Exception as e:
            logger.error("Solr Connection Error: {}".format(e))
            return False
        else:
            if len(results.results) == 0:
                return False
        return True


#-----------------------------------------------------------------------------
def document_get_info(document_id, fields="art_id, art_sourcetype, art_year, file_classification, art_sourcecode"):
    """
    Gets key information about a single document for the specified fields.

    >>> document_get_info('PEPGRANTVS.001.0003A', fields='file_classification')
    {'file_classification': 'free', 'score': ...}

    """
    ret_val = {}
    if solr_docs is not None:
        try:
            # PEP indexes field in upper case, but just in case caller sends lower case, convert.
            document_id = document_id.upper()
            results = solr_docs.query(q = f"art_id:{document_id}",  fields = fields)
        except Exception as e:
            logger.error(f"Solr Retrieval Error: {e}")
        else:
            if len(results.results) == 0:
                return ret_val
            else:
                try:
                    ret_val = results.results[0]
                except Exception as e:
                    logger.error(f"Solr Result Error: {e}")

    return ret_val

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
            if isinstance(ret_val, lxml.etree._Element):
                ret_val = etree.tostring(ret_val)

            if isinstance(ret_val, bytes) or isinstance(ret_val, bytearray):
                logger.error("Byte Data")
                ret_val = ret_val.decode("utf8")
        except Exception as e:
            err = "forceStringReturn Error forcing conversion to string: %s / %s" % (type(ret_val), e)
            logger.error(err)

    return ret_val        

#-----------------------------------------------------------------------------
def database_get_most_viewed( publication_period: int=5,
                              author: str=None,
                              title: str=None,
                              source_name: str=None,  
                              source_code: str=None,
                              source_type: str="journal",
                              abstract_requested: bool=False, 
                              view_period: int=4,      # 4=last12months default
                              more_than: int=1,        # up this later
                              req_url: str=None,
                              stat:bool=False, 
                              limit: int=5,           # Get top 10 from the period
                              offset=0,
                              download=False, 
                              session_info=None
                            ):
    """
    Return the most viewed journal articles (often referred to as most downloaded) duing the prior period years.

    This is used for the statistical summary function and accesses only the relational database, not full-text Solr.

    Args:
        publication_period (int, optional): Look only at articles this many years back to current.  Defaults to 5.
        author (str, optional): Filter, include matching author names per string .  Defaults to None (no filter).
        title (str, optional): Filter, include only titles that match.  Defaults to None (no filter).
        source_name (str, optional): Filter, include only journals matching this name.  Defaults to None (no filter).
        source_type (str, optional): journals, books, or videostreams.
        view_period (int, optional): defaults to last12months

            view_period = { 0: "lastcalyear",
                            1: "lastweek",
                            2: "last1mos",
                            3: "last6mos",
                            4: "last12mos",
                           }

        limit (int, optional): Paging mechanism, return is limited to this number of items.
        offset (int, optional): Paging mechanism, start with this item in limited return set, 0 is first item.

    Returns:
        models.DocumentList: Pydantic structure (dict) for DocumentList.  See models.py

    Docstring Tests:

    >>> result = database_get_most_viewed()
    >>> result.documentList.responseSet[0].documentID if result.documentList.responseInfo.count >0 else "No views yet."
    '...'

    """
    period_suffix = opasConfig.VALS_VIEWPERIODDICT.get(view_period, "last12mos")
    sort = f"art_views_{period_suffix} desc"

    start_year = dtime.date.today().year
    if publication_period is None:
        start_year = None
    else:
        start_year -= publication_period
        start_year = f">{start_year}"

    if stat:
        field_set = "STAT"
    else:
        field_set = None
        
    solr_query_spec = \
        opasQueryHelper.parse_search_query_parameters(viewcount=more_than, 
                                                      viewperiod=view_period, 
                                                      source_name=source_name,
                                                      source_code=source_code,
                                                      source_type=source_type,
                                                      author=author,
                                                      title=title,
                                                      startyear=start_year,
                                                      abstract_requested=abstract_requested,
                                                      return_field_set=field_set, 
                                                      sort = sort,
                                                      req_url = req_url
        )

    try:
        ret_val, ret_status = search_text_qs(solr_query_spec, 
                                             limit=limit,
                                             offset=offset,
                                             #authenticated=session_info.authenticated
                                             req_url = req_url, 
                                             session_info=session_info
                                            )
    except Exception as e:
        logger.warning(f"Search error {e}")

    return ret_val   

#-----------------------------------------------------------------------------
def database_get_most_cited( publication_period: int=None,   # Limit the considered pubs to only those published in these years
                             period: str='5',  # 
                             more_than: int=25,              # Has to be cited more than this number of times, a large nbr speeds the query
                             author: str=None,
                             title: str=None,
                             source_name: str=None,  
                             source_code: str=None,
                             source_type: str=None,
                             abstract_requested: bool=True, 
                             req_url: str=None, 
                             stat:bool=False, 
                             limit: int=10,
                             offset: int=0, 
                             sort:str=None,
                             session_info=None
                             ):
    """
    Return the most cited journal articles duing the prior period years.

    period must be either '5', 10, '20', or 'all'

    args:
      limit: the number of records you want to return
      more_than: setting more_than to a large number speeds the query because the set to be sorted is smaller.
                 just set it so it's not so high you still get "limit" records back.

    >>> result, status = database_get_most_cited()
    >>> len(result.documentList.responseSet)>=10
    True

    """
    period = opasConfig.normalize_val(period, opasConfig.VALS_YEAROPTIONS, default='5')
    #if str(period).lower() not in models.TimePeriod._value2member_map_:
        #period = '5'

    if sort is None:
        sort = f"art_cited_{period} desc"

    start_year = dtime.date.today().year
    if publication_period is None:
        start_year = None
    else:
        start_year -= publication_period
        start_year = f">{start_year}"

    cite_count = f"{more_than} in {period}"
    if stat:
        field_set = "STAT"
    else:
        field_set = None
    
    solr_query_spec = \
        opasQueryHelper.parse_search_query_parameters(citecount=cite_count, 
                                                      source_name=source_name,
                                                      source_code=source_code,
                                                      source_type=source_type, 
                                                      author=author,
                                                      title=title,
                                                      startyear=start_year,
                                                      return_field_set=field_set, 
                                                      abstract_requested=abstract_requested, 
                                                      sort = sort,
                                                      req_url = req_url
                                                    )

    ret_val, ret_status = search_text_qs(solr_query_spec, 
                                         limit=limit,
                                         offset=offset,
                                         #authenticated=session_info.authenticated
                                         session_info=session_info, 
                                         req_url = req_url
                                        )
        
    return ret_val, ret_status   

#-----------------------------------------------------------------------------
def database_get_whats_new(days_back=7,
                           limit=opasConfig.DEFAULT_LIMIT_FOR_WHATS_NEW,
                           req_url:str=None,
                           source_type="journal",
                           offset=0,
                           session_info=None):
    """
    Return what JOURNALS have been updated in the last week

    >>> result = database_get_whats_new()

    """    
    field_list = "art_id, title, art_vol, art_iss, art_sourcecode, file_last_modified, timestamp, art_sourcetype"
    sort_by = "file_last_modified"

    # two ways to get date, slightly different meaning: timestamp:[NOW-{days_back}DAYS TO NOW] AND file_last_modified:[NOW-{days_back}DAYS TO NOW]
    try:
        results = solr_docs.query( q = f"file_last_modified:[NOW-{days_back}DAYS TO NOW] AND art_sourcetype:{source_type}",  
                                   fl = field_list,
                                   fq = "{!collapse field=art_sourcecode max=art_year_int}",
                                   sort=sort_by, sort_order="desc",
                                   rows=limit, start=offset,
                                   )

        # logger.debug("databaseWhatsNew Number found: %s", results._numFound)
    except Exception as e:
        logger.error(f"Solr Search Exception: {e}")

    response_info = models.ResponseInfo( count = len(results.results),
                                         fullCount = results._numFound,
                                         limit = limit,
                                         offset = offset,
                                         listType="newlist",
                                         fullCountComplete = limit >= results._numFound,
                                         request=f"{req_url}",
                                         timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                         )


    whats_new_list_items = []
    row_count = 0
    already_seen = []
    for result in results:
        PEPCode = result.get("art_sourcecode", None)
        #if PEPCode is None or PEPCode in ["SE", "GW", "ZBK", "IPL"]:  # no books
            #continue
        src_type = result.get("art_sourcetype", None)
        if src_type != "journal":
            continue

        volume = result.get("art_vol", None)
        issue = result.get("art_iss", "")
        year = result.get("art_year", None)
        abbrev = result.get("art_sourcetitleabbr", None)
        src_title = result.get("art_sourcetitlefull", None)
        
        updated = result.get("file_last_modified", None)
        updated = updated.strftime('%Y-%m-%d')
        display_title = abbrev + " v%s.%s (%s) " % (volume, issue, year)
        if display_title in already_seen:
            continue
        else:
            already_seen.append(display_title)
        volume_url = "/v1/Metadata/Contents/%s/%s" % (PEPCode, issue)
        

        item = models.WhatsNewListItem( documentID = result.get("art_id", None),
                                        displayTitle = display_title,
                                        abbrev = abbrev,
                                        volume = volume,
                                        issue = issue,
                                        year = year,
                                        PEPCode = PEPCode, 
                                        srcTitle = src_title,
                                        volumeURL = volume_url,
                                        updated = updated
                                        ) 
        whats_new_list_items.append(item)
        row_count += 1
        if row_count > limit:
            break

    response_info.count = len(whats_new_list_items)

    whats_new_list_struct = models.WhatsNewListStruct( responseInfo = response_info, 
                                                       responseSet = whats_new_list_items
                                                       )

    ret_val = models.WhatsNewList(whatsNew = whats_new_list_struct)

    return ret_val   # WhatsNewList

def metadata_get_volumes(source_code=None,
                         source_type=None,
                         req_url: str=None, 
                         limit=1,
                         offset=0):
    """
    Return a list of volumes
      - for a specific source_code (code),
      - OR for a specific source_type (e.g. journal)
      - OR if source_code and source_type are not specified, bring back them all
      
    This is a new version (08/2020) using Solr pivoting rather than the OCD database.
      
    """
    # returns multiple gw's and se's, 139 unique volumes counting those (at least in 2020)
    # works for journal, videostreams have more than one year per vol.
    # works for books, videostream vol numbers
    #results = solr_docs.query( q = f"art_sourcecode:{pep_code} && art_year:{year}",  
                                #fields = "art_sourcecode, art_vol, art_year",
                                #sort="art_sourcecode, art_year", sort_order="asc",
                                #fq="{!collapse field=art_vol}",
                                #rows=limit, start=offset
                                #)
    
    distinct_return = "art_sourcecode, art_vol, art_year, art_sourcetype"
    limit = 6
    count = 0
    ret_val = None
    
    q_str = "bk_subdoc:false"
    if source_code is not None:
        q_str += f" && art_sourcecode:{source_code}"
    if source_type is not None:
        q_str += f" && art_sourcetype:{source_type}"
    facet_fields = ["art_vol", "art_sourcecode"]
    facet_pivot = "art_sourcecode,art_year,art_vol" # important ...no spaces!
    try:
        result = solr_docs.query( q = q_str,
                                  fq="*:*", 
                                  fields = distinct_return,
                                  sort="art_sourcecode, art_year", sort_order="asc",
                                  #fq="{!collapse field=art_sourcecode, art_vol}",
                                  facet="on", 
                                  facet_fields = facet_fields, 
                                  facet_pivot=facet_pivot,
                                  facet_mincount=1,
                                  facet_sort="art_year asc", 
                                  rows=limit
                                 )
        facet_pivot = result.facet_counts["facet_pivot"][facet_pivot]
        #ret_val = [(piv['value'], [n["value"] for n in piv["pivot"]]) for piv in facet_pivot]

        response_info = models.ResponseInfo( count = count,
                                             fullCount = count,
                                             limit = limit,
                                             offset = offset,
                                             listType="volumelist",
                                             fullCountComplete = (limit == 0 or limit >= count),
                                             request=f"{req_url}",
                                             timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                             )

        
        volume_item_list = []
        volume_dup_check = {}
        for m1 in facet_pivot:
            journal_code = m1["value"] # pepcode
            seclevel = m1["pivot"]
            for m2 in seclevel:
                secfield = m2["field"] # year
                secval = m2["value"]
                thirdlevel = m2["pivot"]
                for m3 in thirdlevel:
                    thirdfield = m3["field"] # vol
                    thirdval = m3["value"]
                    PEPCode = journal_code
                    year = secval
                    vol = thirdval
                    count = m3["count"]
                    pep_code_vol = PEPCode + vol
                    # if it's a journal, Supplements are not a separate vol, they are an issue.
                    if pep_code_vol[-1] == "S" and journal_code not in opasConfig.BOOK_CODES_ALL:
                        pep_code_vol = pep_code_vol[:-1]
                    cur_code = volume_dup_check.get(pep_code_vol)
                    if cur_code is None:
                        volume_dup_check[pep_code_vol] = [year]
                        volume_list_item = models.VolumeListItem(PEPCode=PEPCode,
                                                                 vol=vol,
                                                                 year=year,
                                                                 years=[year],
                                                                 count=count
                        )
                        volume_item_list.append(volume_list_item)
                    else:
                        volume_dup_check[pep_code_vol].append(year)
                        if year not in volume_list_item.years:
                            volume_list_item.years.append(year)
                        volume_list_item.count += count

                
    except Exception as e:
        print (f"Error: {e}")
    else:
        response_info.count = len(volume_item_list)
        response_info.fullCount = len(volume_item_list)
    
        volume_list_struct = models.VolumeListStruct( responseInfo = response_info, 
                                                      responseSet = volume_item_list
                                                      )
    
        volume_list = models.VolumeList(volumeList = volume_list_struct)
    
        ret_val = volume_list
        
    return ret_val

#-----------------------------------------------------------------------------
def metadata_get_contents(pep_code, #  e.g., IJP, PAQ, CPS
                          year="*",
                          vol="*",
                          req_url: str=None, 
                          limit=opasConfig.DEFAULT_LIMIT_FOR_CONTENTS_LISTS, offset=0):
    """
    Return a source's contents

    >>> results = metadata_get_contents("IJP", "1993", limit=5, offset=0)
    >>> results.documentList.responseInfo.count == 5
    True
    >>> results = metadata_get_contents("IJP", "1993", limit=5, offset=5)
    >>> results.documentList.responseInfo.count == 5
    True
    """
    ret_val = []
    if year == "*" and vol != "*":
        # specified only volume
        field="art_vol"
        search_val = vol
    else:  #Just do year
        field="art_year"
        search_val = year  #  was "*", thats an error, fixed 2019-12-19

    try:
        code = pep_code.upper()
    except:
        logger.warning(f"Illegal PEP Code or None supplied to metadata_get_contents: {pep_code}")
    else:
        pep_code = code

    results = solr_docs.query(q = f"art_sourcecode:{pep_code} && {field}:{search_val}",  
                              fields = "art_id, art_vol, art_year, art_iss, art_iss_title, art_newsecnm, art_pgrg, title, art_author_id, art_citeas_xml, art_info_xml",
                              sort="art_year, art_pgrg", sort_order="asc",
                              rows=limit, start=offset
                             )

    response_info = models.ResponseInfo( count = len(results.results),
                                         fullCount = results._numFound,
                                         limit = limit,
                                         offset = offset,
                                         listType="documentlist",
                                         fullCountComplete = limit >= results._numFound,
                                         request=f"{req_url}",
                                         timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                         )

    document_item_list = []
    for result in results.results:
        # transform authorID list to authorMast
        authorIDs = result.get("art_author_id", None)
        if authorIDs is None:
            authorMast = None
        else:
            authorMast = opasgenlib.derive_author_mast(authorIDs)

        pgRg = result.get("art_pgrg", None)
        pgStart, pgEnd = opasgenlib.pgrg_splitter(pgRg)
        citeAs = result.get("art_citeas_xml", None)  
        citeAs = force_string_return_from_various_return_types(citeAs)

        item = models.DocumentListItem(PEPCode = pep_code, 
                                       year = result.get("art_year", None),
                                       vol = result.get("art_vol", None),
                                       pgRg = result.get("art_pgrg", None),
                                       pgStart = pgStart,
                                       pgEnd = pgEnd,
                                       authorMast = authorMast,
                                       documentID = result.get("art_id", None),
                                       documentRef = opasxmllib.xml_elem_or_str_to_text(citeAs, default_return=""),
                                       documentRefHTML = citeAs,
                                       documentInfoXML=result.get("art_info_xml", None), 
                                       score = result.get("score", None)
                                       )
        #logger.debug(item)
        document_item_list.append(item)

    response_info.count = len(document_item_list)

    document_list_struct = models.DocumentListStruct( responseInfo = response_info, 
                                                      responseSet=document_item_list
                                                      )

    document_list = models.DocumentList(documentList = document_list_struct)

    ret_val = document_list

    return ret_val

#-----------------------------------------------------------------------------
def metadata_get_videos(src_type=None, pep_code=None, limit=opasConfig.DEFAULT_LIMIT_FOR_METADATA_LISTS, offset=0):
    """
    Fill out a sourceInfoDBList which can be used for a getSources return, but return individual 
      videos, as is done for books.  This provides more information than the 
      original API which returned video "journals" names.  

    """

    if pep_code is not None:
        query = "art_sourcetype:video* AND art_sourcecode:{}".format(pep_code)
    else:
        query = "art_sourcetype:video*"
    try:
        srcList = solr_docs.query(q = query,  
                                  fields = "art_id, art_issn, art_sourcecode, art_authors, title, \
                                            art_sourcetitlefull, art_sourcetitleabbr, art_vol, \
                                            art_year, art_citeas_xml, art_lang, art_pgrg",
                                  sort = "art_citeas_xml",
                                  sort_order = "asc",
                                  rows=limit, start=offset
                                  )
    except Exception as e:
        logger.error("metadataGetVideos Error: {}".format(e))

    source_info_dblist = []
    # count = len(srcList.results)
    total_count = int(srcList.results.numFound)

    for result in srcList.results:
        source_info_record = {}
        authors = result.get("art_authors")
        if authors is None:
            source_info_record["author"] = None
        elif len(authors) > 1:
            source_info_record["author"] = "; ".join(authors)
        else:    
            source_info_record["author"] = authors[0]

        source_info_record["src_code"] = result.get("art_sourcecode")
        source_info_record["ISSN"] = result.get("art_issn")
        source_info_record["documentID"] = result.get("art_id")
        try:
            source_info_record["title"] = result.get("title")[0]
        except:
            source_info_record["title"] = ""

        source_info_record["art_citeas"] = result.get("art_citeas_xml")
        source_info_record["pub_year"] = result.get("art_year")
        source_info_record["bib_abbrev"] = result.get("art_sourcetitleabbr")  # error in get field, fixed 2019.12.19
        try:
            source_info_record["language"] = result.get("art_lang")[0]
        except:
            source_info_record["language"] = "EN"

        logger.debug("metadataGetVideos: %s", source_info_record)
        source_info_dblist.append(source_info_record)

    return total_count, source_info_dblist

#-----------------------------------------------------------------------------
def metadata_get_source_info(src_type=None,
                             src_code=None,
                             src_name=None, 
                             req_url: str=None, 
                             limit=opasConfig.DEFAULT_LIMIT_FOR_METADATA_LISTS,
                             offset=0):
    """
    Return a list of source metadata, by type (e.g., journal, video, etc.).

    No attempt here to map to the correct structure, just checking what field/data items we have in sourceInfoDB.

    >>> results = metadata_get_source_info(src_type="journal", limit=3)
    >>> results.sourceInfo.responseInfo.count >= 3
    True
    >>> results = metadata_get_source_info(src_type="book", limit=10)
    >>> results.sourceInfo.responseInfo.count >= 5
    True
    >>> results = metadata_get_source_info(src_type="journals", limit=10, offset=0)
    >>> results.sourceInfo.responseInfo.count >= 5
    True
    >>> results = metadata_get_source_info(src_type="journals", limit=10, offset=6)
    >>> results.sourceInfo.responseInfo.count >= 5
    True

    >>> results = metadata_get_source_info(src_code="APA")
    >>> results.sourceInfo.responseInfo.count == 1
    True

    >>> results = metadata_get_source_info()
    >>> results.sourceInfo.responseInfo.fullCount >= 235
    True
    
    """
    ret_val = []
    source_info_dblist = []
    ocd = opasCentralDBLib.opasCentralDB()
    # standardize Source type, allow plural, different cases, but code below this part accepts only those three.
    if src_type is not None:
        src_type = opasConfig.normalize_val(src_type, opasConfig.VALS_PRODUCT_TYPES)

    if src_type == "videos":
        # This is not part of the original API, it brings back individual videos rather than the videostreams
        # but here in case we need it.  In that case, your source must be videos.*, like videostream, in order
        # to load individual videos rather than the video journals
        #  gets count of videos and a list of them (from Solr database)
        total_count, source_info_dblist = metadata_get_videos(src_type, src_code, limit, offset)
        count = len(source_info_dblist)
    else: # get from mySQL
        try:
            total_count, source_info_dblist = ocd.get_sources(src_type = src_type, src_code=src_code, src_name=src_name, limit=limit, offset=offset)
            if source_info_dblist is not None:
                count = len(source_info_dblist)
            else:
                count = 0
            logger.debug("MetadataGetSourceByType: Number found: %s", count)
        except Exception as e:
            errMsg = "MetadataGetSourceByType: Error getting source information.  {}".format(e)
            count = 0
            logger.error(errMsg)

    response_info = models.ResponseInfo( count = count,
                                         fullCount = total_count,
                                         fullCountComplete = count == total_count,
                                         limit = limit,
                                         offset = offset,
                                         listLabel = "{} List".format(src_type),
                                         listType = "sourceinfolist",
                                         scopeQuery = [src_type, src_code],
                                         request=f"{req_url}",
                                         timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                         )

    source_info_listitems = []
    counter = 0
    if count > 0:
        for source in source_info_dblist:
            counter += 1
            err = 0
            if counter < offset:
                continue
            if counter > limit:
                break
            try:
                title = source.get("title")
                authors = source.get("author")
                pub_year = source.get("pub_year")
                publisher = source.get("publisher")
                book_code = None
                src_type = source.get("product_type")
                start_year = source.get("yearFirst")
                end_year = source.get("yearLast")
                base_code = source.get("basecode")
                if start_year is None:
                    start_year = pub_year
                if end_year is None:
                    end_year = pub_year
    
                if src_type == "book":
                    book_code = source.get("pepcode")
                    if book_code is None:
                        logger.error(f"Book code information missing for requested basecode {base_code} in productbase")
                    else:
                        m = re.match("(?P<code>[a-z]+)(?P<num>[0-9]+)", book_code, re.IGNORECASE)
                        if m is not None:
                            code = m.group("code")
                            num = m.group("num")
                            book_code = code + "." + num
    
                        art_citeas = u"""<p class="citeas"><span class="authors">%s</span> (<span class="year">%s</span>) <span class="title">%s</span>. <span class="publisher">%s</span>.""" \
                            %                   (authors,
                                                 pub_year,
                                                 title,
                                                 publisher
                                                 )
                elif src_type == "video":
                    art_citeas = source.get("art_citeas")
                else:
                    art_citeas = title # journals just should show display title
    
    
                try:
                    item = models.SourceInfoListItem( sourceType = src_type,
                                                      PEPCode = base_code,
                                                      authors = authors,
                                                      pub_year = pub_year,
                                                      documentID = source.get("articleID"),
                                                      displayTitle = art_citeas,
                                                      title = title,
                                                      srcTitle = title,  # v1 Deprecated for future
                                                      bookCode = book_code,
                                                      abbrev = source.get("bibabbrev"),
                                                      bannerURL = f"http://{BASEURL}/{opasConfig.IMAGES}/banner{source.get('basecode')}Logo.gif",
                                                      language = source.get("language"),
                                                      ISSN = source.get("ISSN"),
                                                      ISBN10 = source.get("ISBN-10"),
                                                      ISBN13 = source.get("ISBN-13"),
                                                      yearFirst = start_year,
                                                      yearLast = end_year,
                                                      embargoYears = source.get("embargo")
                                                      ) 
                except ValidationError as e:
                    logger.error("metadataGetSourceByType SourceInfoListItem Validation Error:")
                    logger.error(e.json())
                    err = 1
    
            except Exception as e:
                logger.error("metadataGetSourceByType: %s", e)
                err = 1
    
            if err == 0:
                source_info_listitems.append(item)
    
    try:
        source_info_struct = models.SourceInfoStruct( responseInfo = response_info, 
                                                      responseSet = source_info_listitems
                                                      )
    except ValidationError as e:
        logger.error("models.SourceInfoStruct Validation Error:")
        logger.error(e.json())        

    try:
        source_info_list = models.SourceInfoList(sourceInfo = source_info_struct)
    except ValidationError as e:
        logger.error("SourceInfoList Validation Error:")
        logger.error(e.json())        

    ret_val = source_info_list

    return ret_val

#-----------------------------------------------------------------------------
def authors_get_author_info(author_partial,
                            req_url:str=None, 
                            limit=opasConfig.DEFAULT_LIMIT_FOR_SOLR_RETURNS, offset=0, author_order="index"):
    """
    Returns a list of matching names (per authors last name), and the number of articles in PEP found by that author.

    Args:
        author_partial (str): String prefix of author names to return.
        limit (int, optional): Paging mechanism, return is limited to this number of items.
        offset (int, optional): Paging mechanism, start with this item in limited return set, 0 is first item.
        author_order (str, optional): Return the list in this order, per Solr documentation.  Defaults to "index", which is the Solr determined indexing order.

    Returns:
        models.DocumentList: Pydantic structure (dict) for DocumentList.  See models.py

    Docstring Tests:    
        >>> resp = authors_get_author_info("Tuck")
        >>> resp.authorIndex.responseInfo.count >= 7
        True
        >>> resp = authors_get_author_info("Levins.*", limit=5)
        >>> resp.authorIndex.responseInfo.count
        5
    """
    ret_val = {}
    method = 2

    if method == 1:
        query = "art_author_id:/%s.*/" % (author_partial)
        results = solr_authors.query( q=query,
                                      fields="authors, art_author_id",
                                      facet_field="art_author_id",
                                      facet="on",
                                      facet_sort=author_order,  # index or count (updated 20200418)
                                      facet_prefix="%s" % author_partial,
                                      facet_limit=limit,
                                      facet_offset=offset,
                                      rows=0
                                      )       

    if method == 2:
        # should be faster way, but about the same measuring tuck (method1) vs tuck.* (method2) both about 2 query time.  However, allowing regex here.
        if "*" in author_partial or "?" in author_partial or "." in author_partial:
            results = solr_authors_term_search( terms_fl="art_author_id",
                                                terms_limit=limit,  # this causes many regex expressions to fail
                                               terms_regex=author_partial.lower() + ".*",
                                               terms_sort=author_order  # index or count
                                               )           
        else:
            results = solr_authors_term_search( terms_fl="art_author_id",
                                                terms_prefix=author_partial.lower(),
                                               terms_sort=author_order,  # index or count
                                               terms_limit=limit
                                               )

    response_info = models.ResponseInfo( limit=limit,
                                         offset=offset,
                                         listType="authorindex",
                                         scopeQuery=[f"Terms: {author_partial}"],
                                         solrParams=results._params,
                                         request=f"{req_url}",
                                         timeStamp=datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)
                                         )

    author_index_items = []
    if method == 1:
        for key, value in results.facet_counts["facet_fields"]["art_author_id"].items():
            if value > 0:
                item = models.AuthorIndexItem(authorID = key, 
                                              publicationsURL = "/v1/Authors/Publications/{}/".format(key),
                                              publicationsCount = value,
                                              ) 
                author_index_items.append(item)
                logger.debug ("authorsGetAuthorInfo", item)

    if method == 2:  # faster way
        for key, value in results.terms["art_author_id"].items():
            if value > 0:
                item = models.AuthorIndexItem(authorID = key, 
                                              publicationsURL = "/v1/Authors/Publications/{}/".format(key),
                                              publicationsCount = value,
                                              ) 
                author_index_items.append(item)
                logger.debug("authorsGetAuthorInfo: %s", item)

    response_info.count = len(author_index_items)
    response_info.fullCountComplete = limit >= response_info.count

    author_index_struct = models.AuthorIndexStruct( responseInfo = response_info, 
                                                    responseSet = author_index_items
                                                    )

    author_index = models.AuthorIndex(authorIndex = author_index_struct)

    ret_val = author_index
    return ret_val

#-----------------------------------------------------------------------------
def authors_get_author_publications(author_partial,
                                    req_url:str=None, 
                                    limit=opasConfig.DEFAULT_LIMIT_FOR_SOLR_RETURNS,
                                    offset=0):
    """
    Returns a list of publications (per authors partial name), and the number of articles by that author.

    >>> ret_val =authors_get_author_publications(author_partial="Tuck") # doctest: +ELLIPSIS
    >>> type(ret_val)
    <class 'models.AuthorPubList'>
    >>> print (f"{ret_val}"[0:68])
    authorPubList=AuthorPubListStruct(responseInfo=ResponseInfo(count=10
    >>> ret_val=authors_get_author_publications(author_partial="Fonag")
    >>> print (f"{ret_val}"[0:68])
    authorPubList=AuthorPubListStruct(responseInfo=ResponseInfo(count=10
    >>> ret_val=authors_get_author_publications(author_partial="Levinson, Nadine A.")
    >>> print (f"{ret_val}"[0:67])
    authorPubList=AuthorPubListStruct(responseInfo=ResponseInfo(count=8
    """
    ret_val = {}
    query = "art_author_id:/{}/".format(author_partial)
    aut_fields = "art_author_id, art_year_int, art_id, art_auth_pos_int, art_author_role, art_author_bio, art_citeas_xml"
    # wildcard in case nothing found for #1
    results = solr_authors.query( q = "{}".format(query),   
                                  fields = aut_fields,
                                  sort="art_author_id, art_year_int", sort_order="asc",
                                  rows=limit, start=offset
                                  )

    logger.debug("Author Publications: Number found: %s", results._numFound)

    if results._numFound == 0:
        logger.debug("Author Publications: Query didn't work - %s", query)
        query = "art_author_id:/{}[ ]?.*/".format(author_partial)
        logger.debug("Author Publications: trying again - %s", query)
        results = solr_authors.query( q = "{}".format(query),  
                                      fields = aut_fields,
                                      sort="art_author_id, art_year_int", sort_order="asc",
                                      rows=limit, start=offset
                                      )

        logger.debug("Author Publications: Number found: %s", results._numFound)
        if results._numFound == 0:
            query = "art_author_id:/(.*[ ])?{}[ ]?.*/".format(author_partial)
            logger.debug("Author Publications: trying again - %s", query)
            results = solr_authors.query( q = "{}".format(query),  
                                          fields = aut_fields,
                                          sort="art_author_id, art_year_int", sort_order="asc",
                                          rows=limit, start=offset
                                          )

    response_info = models.ResponseInfo( count = len(results.results),
                                         fullCount = results._numFound,
                                         limit = limit,
                                         offset = offset,
                                         listType="authorpublist",
                                         scopeQuery=[query],
                                         solrParams = results._params,
                                         fullCountComplete = limit >= results._numFound,
                                         request=f"{req_url}",
                                         timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                         )

    author_pub_list_items = []
    for result in results.results:
        citeas = result.get("art_citeas_xml", None)
        citeas = force_string_return_from_various_return_types(citeas)

        item = models.AuthorPubListItem( authorID = result.get("art_author_id", None), 
                                         documentID = result.get("art_id", None),
                                         documentRefHTML = citeas,
                                         documentRef = opasxmllib.xml_elem_or_str_to_text(citeas, default_return=""),
                                         documentURL = opasConfig.API_URL_DOCUMENTURL + result.get("art_id", None),
                                         year = result.get("art_year", None),
                                         score = result.get("score", 0)
                                         ) 

        author_pub_list_items.append(item)

    response_info.count = len(author_pub_list_items)

    author_pub_list_struct = models.AuthorPubListStruct( responseInfo = response_info, 
                                                         responseSet = author_pub_list_items
                                           )

    author_pub_list = models.AuthorPubList(authorPubList = author_pub_list_struct)

    ret_val = author_pub_list
    return ret_val

#-----------------------------------------------------------------------------
def documents_get_abstracts(document_id,
                            ret_format="TEXTONLY",
                            authenticated=False,
                            similar_count=0,
                            sort: str=None, 
                            limit=opasConfig.DEFAULT_LIMIT_FOR_SOLR_RETURNS,
                            req_url: str=None, 
                            offset=0,
                            session_info=None
                            ):
    """
    Returns an abstract or summary for the specified document
    If part of a documentID is supplied, multiple abstracts will be returned.

    The endpoint reminds me that we should be using documentID instead of "art" for article perhaps.
      Not thrilled about the prospect of changing it, but probably the right thing to do.

    >>> results = documents_get_abstracts("IJP.075")
    >>> results.documents.responseInfo.count == 10
    True
    >>> results = documents_get_abstracts("AIM.038.0279A")  # no abstract on this one
    >>> results.documents.responseInfo.count == 1
    True
    >>> results = documents_get_abstracts("AIM.040.0311A")
    >>> results.documents.responseInfo.count == 1
    True

    """
    ret_val = None

    if document_id is not None:
        try:
            document_id = document_id.upper()
        except Exception as e:
            logger.warning("Bad argument {document_id} to get_abstract(Error:{e})")
            return ret_val

        if sort is None:
            sort="art_citeas_xml asc"

        document_list, ret_status = search_text( query="art_id:%s*" % (document_id),
                                                 full_text_requested=False,
                                                 abstract_requested=True, 
                                                 format_requested = ret_format,
                                                 #authenticated=authenticated,
                                                 similar_count=similar_count,
                                                 facet_fields=opasConfig.DOCUMENT_VIEW_FACET_LIST,
                                                 facet_mincount=1,
                                                 sort=sort, 
                                                 limit=limit,   
                                                 offset=offset, 
                                                 req_url=req_url,
                                                 session_info=session_info
                                                 )

        documents = models.Documents(documents = document_list.documentList)

        ret_val = documents

    return ret_val

def get_base_article_info_from_search_result(result, documentListItem: models.DocumentListItem):
    
    if result is not None:
        documentListItem.documentID = result.get("art_id", None)
        documentListItem.PEPCode = result.get("art_sourcecode", None)

        # don't set the value, if it's None, so it's not included at all in the pydantic return
        if result.get("meta_xml", None): documentListItem.documentMetaXML = result.get("meta_xml", None)
        if result.get("art_info_xml", None): documentListItem.documentInfoXML = result.get("art_info_xml", None)
        if result.get("art_pgrg", None): documentListItem.pgRg = result.get("art_pgrg", None)
        # temp workaround for art_lang change
        art_lang = result.get("art_lang", None)
        if isinstance(art_lang, list):
            art_lang = art_lang[0]
        documentListItem.lang=art_lang
        if result.get("art_origrx", None): documentListItem.origrx = result.get("art_origrx", None)
        if result.get("art_qual", None): documentListItem.relatedrx= result.get("art_qual", None)
        documentListItem.sourceTitle = result.get("art_sourcetitlefull", None)
        documentListItem.sourceType = result.get("art_sourcetype", None)
        documentListItem.year = result.get("art_year", None)
        documentListItem.vol = result.get("art_vol", None)
        documentListItem.docType = result.get("art_type", None)
        if result.get("art_doi", None): documentListItem.doi = result.get("art_doi", None)
        documentListItem.issue = result.get("art_iss", None)
        documentListItem.issn = result.get("art_issn", None)
        # documentListItem.isbn = result.get("art_isbn", None) # no isbn in solr stored data, only in products table

        documentListItem.title = result.get("art_title_xml", "")  
        if documentListItem.pgRg is not None:
            pg_start, pg_end = opasgenlib.pgrg_splitter(documentListItem.pgRg)
            documentListItem.pgStart = pg_start
            documentListItem.pgEnd = pg_end
        author_ids = result.get("art_authors", None)
        if author_ids is None:
            # try this, instead of abberrant behavior in alpha of display None!
            documentListItem.authorMast = result.get("art_authors_mast", "")
        else:
            documentListItem.authorMast = opasgenlib.derive_author_mast(author_ids)
        if result.get("art_newsecnm", None): documentListItem.newSectionName=result.get("art_newsecnm", None)            
        citeas = result.get("art_citeas_xml", None)
        citeas = force_string_return_from_various_return_types(citeas)
        documentListItem.documentRef = opasxmllib.xml_elem_or_str_to_text(citeas, default_return="")
        documentListItem.documentRefHTML = citeas
        documentListItem.updated=result.get("file_last_modified", None)
        documentListItem.accessClassification = result.get("file_classification", opasConfig.DOCUMENT_ACCESS_ARCHIVE)

    return documentListItem # return a partially filled document list item

def get_excerpt_from_search_result(result, documentListItem: models.DocumentListItem, ret_format="HTML"):
    """
    pass in the result from a solr query and this retrieves the abstract/excerpt from the excerpt field
     which is stored based on the abstract or summary or the first page of the document.

     Substituted for dynamic generation of excerpt 2020-02-26
    """
    # make sure basic info has been retrieved
    if documentListItem.sourceTitle is None:
        documentListItem = get_base_article_info_from_search_result(result, documentListItem)

    try:
        art_excerpt = result["art_excerpt"]
    except KeyError as e:
        art_excerpt  = "No abstract found for this title, or no abstract requested in search options."
        logger.info("No excerpt for document ID: %s", documentListItem.documentID)

    if art_excerpt == "[]" or art_excerpt is None:
        abstract = None
    else:
        heading = opasxmllib.get_running_head(source_title=documentListItem.sourceTitle,
                                              pub_year=documentListItem.year,
                                              vol=documentListItem.vol,
                                              issue=documentListItem.issue,
                                              pgrg=documentListItem.pgRg,
                                              ret_format=ret_format)
        try:
            ret_format = ret_format.upper()
        except Exception as e:
            logger.warning(f"Invalid return format: {ret_format}.  Using default. Error {e}.")
            ret_format = "HTML"

        if ret_format == "TEXTONLY":
            art_excerpt = opasxmllib.xml_elem_or_str_to_text(art_excerpt)
            abstract = f"""
                        {heading}\n{documentListItem.title}\n{documentListItem.authorMast}\n\n
                        {art_excerpt}
                        """
        elif ret_format == "XML":
            # for now, this is only an xml fragment so it's not quite as DTD specific.
            abstract = result.get("art_excerpt_xml", art_excerpt)
            # to make a complete pepkbd3 document, this is the structure...
            #abstract = f"""
                        #<pepkbd3>
                        #{documentListItem.documentInfoXML}
                        #{abstract}
                        #<body></body>
                        #</pepkbd3>
                        #"""
        
        else: # ret_format == "HTML":
            abstract = f"""
                    <p class="heading">{heading}</p>
                    <p class="title">{documentListItem.title}</p>
                    <p class="title_author">{documentListItem.authorMast}</p>
                    <div class="abstract">{art_excerpt}</div>
                    """
            
        
    # elif ret_format == "HTML": #(Excerpt is in HTML already)

    #abstract = opasxmllib.add_headings_to_abstract_html( abstract=art_excerpt, 
                                                         #source_title=documentListItem.sourceTitle,
                                                         #pub_year=documentListItem.year,
                                                         #vol=documentListItem.vol, 
                                                         #pgrg=documentListItem.pgRg, 
                                                         #citeas=documentListItem.documentRefHTML, 
                                                         #title=documentListItem.title,
                                                         #author_mast=documentListItem.authorMast,
                                                         #ret_format=ret_format
                                                         #)

    # return it in the abstract field for display
    documentListItem.abstract = abstract

    return documentListItem

def get_fulltext_from_search_results(result,
                                     text_xml,
                                     page,
                                     page_offset,
                                     page_limit,
                                     documentListItem: models.DocumentListItem, format_requested="HTML"):

    if documentListItem.sourceTitle is None:
        documentListItem = get_base_article_info_from_search_result(result, documentListItem)
        
    #if page_limit is None:
        #page_limit = opasConfig.DEFAULT_PAGE_LIMIT

    documentListItem.docPagingInfo = {}    
    documentListItem.docPagingInfo["page"] = page
    documentListItem.docPagingInfo["page_limit"] = page_limit
    documentListItem.docPagingInfo["page_offset"] = page_offset

    fullText = result.get("text_xml", None)
    text_xml = force_string_return_from_various_return_types(text_xml)
    if text_xml is None:  # no highlights, so get it from the main area
        try:
            text_xml = fullText
        except:
            text_xml = None

    elif len(fullText) > len(text_xml):
        logger.warning("Warning: text with highlighting is smaller than full-text area.  Returning without hit highlighting.")
        text_xml = fullText

    if text_xml is not None:
        reduce = False
        # see if an excerpt was requested.
        if page is not None and page <= int(documentListItem.pgEnd) and page > int(documentListItem.pgStart):
            # use page to grab the starting page
            # we've already done the search, so set page offset and limit these so they are returned as offset and limit per V1 API
            offset = page - int(documentListItem.pgStart)
            reduce = True
        # Only use supplied offset if page parameter is out of range, or not supplied
        if reduce == False and page_offset is not None: 
            offset = page_offset
            reduce = True

        #if page_limit is not None:
            #limit = page_limit

        if reduce == True or page_limit is not None:
            # extract the requested pages
            try:
                temp_xml = opasxmllib.xml_get_pages(xmlstr=text_xml,
                                                    offset=offset,
                                                    limit=page_limit,
                                                    pagebrk="pb",
                                                    inside="body",
                                                    env="body")
                temp_xml = temp_xml[0]
            except Exception as e:
                logger.error(f"Page extraction from document failed. Error: {e}.  Keeping entire document.")
            else: # ok
                text_xml = temp_xml

    try:
        format_requested_ci = format_requested.lower() # just in case someone passes in a wrong type
    except:
        format_requested_ci = "html"

    if format_requested_ci == "html":
        # Convert to HTML
        heading = opasxmllib.get_running_head( source_title=documentListItem.sourceTitle,
                                               pub_year=documentListItem.year,
                                               vol=documentListItem.vol,
                                               issue=documentListItem.issue,
                                               pgrg=documentListItem.pgRg,
                                               ret_format="HTML"
                                               )
        text_xml = opasxmllib.xml_str_to_html(text_xml)  #  e.g, r"./libs/styles/pepkbd3-html.xslt"
        text_xml = re.sub(f"{opasConfig.HITMARKERSTART}|{opasConfig.HITMARKEREND}", numbered_anchors, text_xml)
        text_xml = re.sub("\[\[RunningHead\]\]", f"{heading}", text_xml, count=1)
    elif format_requested_ci == "textonly":
        # strip tags
        text_xml = opasxmllib.xml_elem_or_str_to_text(text_xml, default_return=text_xml)
    elif format_requested_ci == "xml":
        text_xml = re.sub(f"{opasConfig.HITMARKERSTART}|{opasConfig.HITMARKEREND}", numbered_anchors, text_xml)

    documentListItem.document = text_xml
    return documentListItem


#-----------------------------------------------------------------------------
def documents_get_document(document_id,
                           solr_query_spec=None,
                           ret_format="XML",
                           similar_count=0,
                           #file_classification=None,
                           req_url:str=None, 
                           page_offset=None,
                           page_limit=None,
                           page=None, 
                           authenticated=True,
                           session_info=None
                           ):
    """
    For non-authenticated users, this endpoint returns only Document summary information (summary/abstract)
    For authenticated users, it returns with the document itself

    >> resp = documents_get_document("AIM.038.0279A", ret_format="html") 

    >> resp = documents_get_document("AIM.038.0279A") 

    >> resp = documents_get_document("AIM.040.0311A")


    """
    ret_val = {}
    document_list = None
    # let search text handle the authentication verification
    #if not authenticated and file_classification != opasConfig.DOCUMENT_ACCESS_FREE:
        ##if user is not authenticated, effectively do endpoint for getDocumentAbstracts
        #logger.info("documentsGetDocument: User not authenticated...fetching abstracts instead")
        #ret_val = document_list_struct = documents_get_abstracts(document_id, authenticated=authenticated, ret_format=ret_format, limit=1)
        #return ret_val

    try: # Solr match against art_id is case sensitive
        document_id = document_id.upper()
    except Exception as e:
        logger.warning("Bad argument {document_id} to documents_get_document(Error:{e})")
        return ret_val
    else:
        m = re.match("(?P<docid>(?P<scode>[A-Z]+)\.(?P<svol>[0-9]{3,3})\.(?P<spage>[0-9]{4,4}[A-Z]))(\.P0{0,3}(?P<pagejump>[0-9]{1,4}))?", document_id)
        if m is not None:
            if m.group("pagejump") is not None:
                document_id = m.group("docid")
                # only if they haven't directly specified page
                if page == None:
                    page = m.group("pagejump")

        if solr_query_spec is not None:
            solr_query_params = solr_query_spec.solrQuery
            # repeat the query that the user had done when retrieving the document
            query = f"{solr_query_params.searchQ}"
            if query == "":
                query = "*:*"
            filterQ = f"art_id:{document_id} && {solr_query_params.filterQ}"
            solrParams = solr_query_params.dict() 
        else:
            query = f"art_id:{document_id}"
            filterQ = None
            #solrMax = None
            solrParams = None

        solr_query_spec = \
                opasQueryHelper.parse_to_query_spec(
                                                    query = query,
                                                    filter_query = filterQ,
                                                    similar_count=similar_count, 
                                                    full_text_requested=True,
                                                    abstract_requested=True,
                                                    format_requested="HTML",
                                                    #return_field_set=return_field_set, 
                                                    #summary_fields = summary_fields,  # deprecate?
                                                    highlight_fields = "text_xml",
                                                    extra_context_len=opasConfig.SOLR_HIGHLIGHT_RETURN_FRAGMENT_SIZE, 
                                                    limit = 1,
                                                    page_offset = page_offset,
                                                    page_limit = page_limit,
                                                    page = page,
                                                    req_url = req_url
                                                    )

        document_list, ret_status = search_text_qs(solr_query_spec,
                                                   #limit=limit,
                                                   #offset=offset, 
                                                   session_info=session_info
                                                   )

        try:
            matches = document_list.documentList.responseInfo.count
            # get the first document item only
            document_list_item = document_list.documentList.responseSet[0]
            # is user authorized?
            if document_list.documentList.responseSet[0].accessLimited:
                document_list.documentList.responseSet[0].document = document_list.documentList.responseSet[0].abstract
            
        except Exception as e:
            logger.info("get_document: No matches or error: %s", e)
        else:
            if page_limit is None:
                page_limit = 100 # TODO - Check this (was 0 before)
            if page_offset is None:
                page_offset = 0
                
            response_info = document_list.documentList.responseInfo
            response_info.page=page
            response_info.limit = page_limit # use for page_limit, rather than the usual limit
            response_info.offset = page_offset # use for page_offset, rather than the usual limit
            # response_info.solrParams = solrParams
            # response_info.request = req_url
            
            if matches >= 1:       
                document_list_struct = models.DocumentListStruct( responseInfo = response_info, 
                                                                  responseSet = [document_list_item]
                                                                  )

                documents = models.Documents(documents = document_list_struct)

                ret_val = documents

    return ret_val

#-----------------------------------------------------------------------------
def documents_get_glossary_entry(term_id,
                                 retFormat="XML",
                                 authenticated=True,
                                 req_url: str=None,
                                 limit=opasConfig.DEFAULT_LIMIT_FOR_DOCUMENT_RETURNS,
                                 offset=0):
    """
    For non-authenticated users, this endpoint should return an error (#TODO)

    For authenticated users, it returns with the glossary itself

    IMPORTANT NOTE: At least the way the database is currently populated, for a group, the textual part (text) is the complete group, 
      and thus the same for all entries.  This is best for PEP-Easy now, otherwise, it would need to concatenate all the result entries.

    >> resp = documentsGetGlossaryEntry("ZBK.069.0001o.YN0019667860580", retFormat="html") 

    >> resp = documentsGetGlossaryEntry("ZBK.069.0001o.YN0004676559070") 

    >> resp = documentsGetGlossaryEntry("ZBK.069.0001e.YN0005656557260")


    """
    ret_val = {}
    term_id = term_id.upper()

    if not authenticated:
        #if user is not authenticated, effectively do endpoint for getDocumentAbstracts
        documents_get_abstracts(term_id, limit=1)
    else:
        results = solr_gloss.query(q = f"term_id:{term_id} || group_id:{term_id}",  
                                   fields = "term_id, group_id, term_type, term_source, group_term_count, art_id, text"
                                   )
        document_item_list = []
        count = 0
        try:
            for result in results:
                try:
                    document = result.get("text", None)
                    if retFormat == "HTML":
                        document = opasxmllib.xml_str_to_html(document)
                    elif retFormat == "TEXTONLY":
                        document = opasxmllib.xml_elem_or_str_to_text(document)
                    else: # XML
                        document = document
                    item = models.DocumentListItem( PEPCode = "ZBK", 
                                                    documentID = result.get("art_id", None), 
                                                    title = result.get("term_source", None),
                                                    abstract = None,
                                                    document = document,
                                                    score = result.get("score", None)
                                                    )
                except ValidationError as e:
                    logger.error(e.json())  
                else:
                    document_item_list.append(item)
                    count = len(document_item_list)

        except IndexError as e:
            logger.warning("No matching glossary entry for %s.  Error: %s", (term_id, e))
        except KeyError as e:
            logger.warning("No content or abstract found for %s.  Error: %s", (term_id, e))
        else:
            response_info = models.ResponseInfo( count = count,
                                                 fullCount = count,
                                                 limit = limit,
                                                 offset = offset,
                                                 listType = "documentlist",
                                                 fullCountComplete = True,
                                                 request=f"{req_url}",
                                                 timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                                 )

            document_list_struct = models.DocumentListStruct( responseInfo = response_info, 
                                                              responseSet = document_item_list
                                                              )

            documents = models.Documents(documents = document_list_struct)

            ret_val = documents

        return ret_val

#-----------------------------------------------------------------------------
def prep_document_download(document_id,
                           session_info=None, 
                           ret_format="HTML",
                           base_filename="opasDoc"):
    """
    For non-authenticated users, this endpoint returns only Document summary information (summary/abstract)
    For authenticated users, it returns with the document itself

    >>> a = prep_document_download("IJP.051.0175A", ret_format="html") 

    >> a = prep_document_download("IJP.051.0175A", ret_format="epub") 


    """
    def add_epub_elements(str):
        # for now, just return
        return str

    ret_val = None

    results = solr_docs.query( q = "art_id:%s" % (document_id),  
                               fields = """art_id, art_citeas_xml, text_xml, art_excerpt, art_sourcetype, art_year,
                                           art_sourcetitleabbr, art_vol, art_iss, art_pgrg, art_doi,
                                           art_issn, file_classification"""
                               )
    try:
        art_info = results.results[0]
        ret_val = art_info.get("text_xml", art_info.get("art_excerpt", None))
    except IndexError as e:
        logger.warning("No matching document for %s.  Error: %s", document_id, e)
    except KeyError as e:
        logger.warning("No full-text content found for %s.  Error: %s", document_id, e)
    else:
        try:    
            if isinstance(ret_val, list):
                ret_val = ret_val[0]
        except Exception as e:
            logger.warning("Empty return: %s", e)
        else:
            doi = art_info.get("art_doi", None)
            pub_year = art_info.get("art_year", None)
            file_classification = art_info.get("file_classification", None)
            
            access = opasDocPerm.get_access_limitations( doc_id=document_id,
                                                         classification=file_classification,
                                                         session_info=session_info,
                                                         year=pub_year,
                                                         doi=doi)
            if access.accessLimited != True:
                try:
                    heading = opasxmllib.get_running_head( source_title=art_info.get("art_sourcetitleabbr", ""),
                                                           pub_year=pub_year,
                                                           vol=art_info.get("art_vol", ""),
                                                           issue=art_info.get("art_iss", ""),
                                                           pgrg=art_info.get("art_pgrg", ""),
                                                           ret_format="HTML"
                                                           )
    
                    if ret_format.upper() == "HTML":
                        html = opasxmllib.remove_encoding_string(ret_val)
                        filename = convert_xml_to_html_file(html, output_filename=document_id + ".html")  # returns filename
                        ret_val = filename
                    elif ret_format.upper() == "PDFORIG":
                        # setup so can include year in path (folder names) in AWS, helpful.
                        pub_year = art_info.get("art_year", None)
                        filename = opas_fs.get_download_filename(filespec=document_id, path=localsecrets.PDF_ORIGINALS_PATH, year=pub_year, ext=".pdf")    
                        ret_val = filename
                    elif ret_format.upper() == "PDF":
                        pisa.showLogging() # debug only
                        ret_val = opasxmllib.remove_encoding_string(ret_val)
                        html_string = opasxmllib.xml_str_to_html(ret_val)
                        html_string = re.sub("\[\[RunningHead\]\]", f"{heading}", html_string, count=1)
                        html_string = re.sub("</html>", f"{COPYRIGHT_PAGE_HTML}</html>", html_string, count=1)                        
                        # open output file for writing (truncated binary)
                        filename = document_id + ".PDF" 
                        result_file = open(filename, "w+b")
                        # convert HTML to PDF
                        pisaStatus = pisa.CreatePDF(src=html_string,            # the HTML to convert
                                                    dest=result_file)           # file handle to receive result
                        # close output file
                        result_file.close()                 # close output file
                        # return True on success and False on errors
                        ret_val = filename
                    elif ret_format.upper() == "EPUB":
                        ret_val = opasxmllib.remove_encoding_string(ret_val)
                        html_string = opasxmllib.xml_str_to_html(ret_val)
                        html_string = re.sub("\[\[RunningHead\]\]", f"{heading}", html_string, count=1)
                        html_string = add_epub_elements(html_string)
                        filename = opasxmllib.html_to_epub(html_string, document_id, document_id)
                        ret_val = filename
                    else:
                        logger.warning(f"Format {ret_format} not supported")
    
                except Exception as e:
                    logger.warning("Can't convert data: %s", e)

    return ret_val

#-----------------------------------------------------------------------------
#def find(name, path): # Not used? 
    #"""
    #Find the file name in the selected path
    #"""
    #for root, dirs, files in os.walk(path):
        #if name.lower() in [x.lower() for x in files]:
            #return os.path.join(root, name)

#-----------------------------------------------------------------------------
def convert_xml_to_html_file(xmltext_str, output_filename=None):
    if output_filename is None:
        basename = "opasDoc"
        suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        filename_base = "_".join([basename, suffix]) # e.g. 'mylogfile_120508_171442'        
        output_filename = filename_base + ".html"

    htmlString = opasxmllib.xml_str_to_html(xmltext_str)
    fo = open(output_filename, "w", encoding="utf-8")
    fo.write(str(htmlString))
    fo.close()

    return output_filename

#-----------------------------------------------------------------------------
def get_kwic_list( marked_up_text, 
                   extra_context_len=opasConfig.DEFAULT_KWIC_CONTENT_LENGTH, 
                   solr_start_hit_tag=opasConfig.HITMARKERSTART, # supply whatever the start marker that solr was told to use
                   solr_end_hit_tag=opasConfig.HITMARKEREND,     # supply whatever the end marker that solr was told to use
                   output_start_hit_tag_marker=opasConfig.HITMARKERSTART_OUTPUTHTML, # the default output marker, in HTML
                   output_end_hit_tag_marker=opasConfig.HITMARKEREND_OUTPUTHTML,
                   limit=opasConfig.DEFAULT_MAX_KWIC_RETURNS
                   ):
    """
    Find all nonoverlapping matches, using Solr's return.  Limit the number.

    (See git version history for an earlier -- and different version)
    """

    ret_val = []
    em_marks = re.compile("(.{0,%s}%s.*%s.{0,%s})" % (extra_context_len, solr_start_hit_tag, solr_end_hit_tag, extra_context_len))
    marked_up = re.compile(".*(%s.*%s).*" % (solr_start_hit_tag, solr_end_hit_tag))
    marked_up_text = opasxmllib.xml_string_to_text(marked_up_text) # remove markup except match tags which shouldn't be XML

    match_text_pattern = "({{.*?}})"
    pat_compiled = re.compile(match_text_pattern)
    word_list = pat_compiled.split(marked_up_text) # split all the words
    index = 0
    count = 0
    #TODO may have problems with adjacent matches!
    skip_next = False
    for n in word_list:
        if pat_compiled.match(n) and skip_next == False:
            # we have a match
            try:
                text_before = word_list[index-1]
                text_before_words = text_before.split(" ")[-extra_context_len:]
                text_before_phrase = " ".join(text_before_words)
            except:
                text_before = ""
            try:
                text_after = word_list[index+1]
                text_after_words = text_after.split(" ")[:extra_context_len]
                text_after_phrase = " ".join(text_after_words)
                if pat_compiled.search(text_after_phrase):
                    skip_next = True
            except:
                text_after = ""

            # change the tags the user told Solr to use to the final output tags they want
            #   this is done to use non-xml-html hit tags, then convert to that after stripping the other xml-html tags
            match = re.sub(solr_start_hit_tag, output_start_hit_tag_marker, n)
            match = re.sub(solr_end_hit_tag, output_end_hit_tag_marker, match)

            context_phrase = text_before_phrase + match + text_after_phrase

            ret_val.append(context_phrase)

            try:
                logger.info("getKwicList Match: '...{}...'".format(context_phrase))
            except Exception as e:
                logger.error("getKwicList Error printing or logging matches. %s", e)

            index += 1
            count += 1
            if count >= limit:
                break
        else:
            skip_next = False
            index += 1

    # matchCount = len(ret_val)

    return ret_val    
#-----------------------------------------------------------------------------
def search_analysis( query_list, 
                     filter_query = None,
                     #more_like_these = False,
                     #query_analysis = False,
                     def_type = None,
                     # summaryFields="art_id, art_sourcecode, art_vol, art_year, art_iss, 
                     # art_iss_title, art_newsecnm, art_pgrg, art_title, art_author_id, art_citeas_xml", 
                         summary_fields="art_id",                    
                     # highlightFields='art_title_xml, abstract_xml, summaries_xml, art_authors_xml, text_xml', 
                     full_text_requested=False, 
                     user_logged_in=False,
                     req_url:str=None, 
                     limit=opasConfig.DEFAULT_MAX_KWIC_RETURNS,
                     api_version="v2"
                     ):
    """
    Analyze the search clauses in the query list
    """
    ret_val = {}
    return_item_list = []
    rowCount = 0
    term_field = None
    # save classes to neutral names so we can change between documentList and termIndex
    if 0: # api_version == "v1":
        RetItem = models.DocumentListItem
        RetStruct = models.DocumentListStruct
        RetList = models.DocumentList
    else:
        RetItem = models.TermIndexItem
        RetStruct = models.TermIndexStruct
        RetList = models.TermIndex

    for query_item in query_list:
        # get rid of illegal stuff
        # boolean_subs = [termpair.strip() for termpair in re.split("\s+\|\||\&\&|[ ]\s+", query_item)]
        # boolean_subs = [termpair.strip() for termpair in re.split("\s*\|\||\&\&|AND|OR\s*", query_item)]
        # for clause in query_item:
            #clauses = n.split(":")
            #if len(clauses) == 1:
                #term_clause = clauses[0]
            #else:
                #field_clause = clauses[0]
                #term_clause = clauses[1]
            #subfield_clauses = shlex.split(term_clause)

        try:
            results = solr_docs.query(query_item,
                                      defType = def_type,
                                      q_op="AND", 
                                      queryAnalysis = True,
                                      fields = summary_fields,
                                      rows = 1,
                                      start = 0)
        except Exception as e:
            # try to return an error message for now.
            # logger.error(HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=e))
            # raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Bad Search syntax")
            return models.ErrorReturn(error="Search syntax error", error_description=f"There's an error in your input {e}")

        if "!parent" in query_item:
            term = query_item
            try:
                query_item = query_item.replace("parent_tag:(p_body || p_summaries || p_appxs)", "parent_tag:(doc)")
                query_parsed = re.split("(&&|\|\|) \(", query_item)
                del(query_parsed[0])
                for i in range(len(query_parsed)):
                    if query_parsed[i] in ["&&", "||"]:
                        continue
                    if "parent_tag" in query_parsed[i]:
                        m = re.match(".*parent_tag:\((?P<parent_tag>.*)\).*?(?P<field>[A-z_]+)\:\((?P<terms>.*)\)\)?\)?", query_parsed[i])
                        if m is not None:
                            query_parsed[i] = m.groupdict(default="")
                            query_parsed[i]['parent_tag'] = schemaMap.solr2user(query_parsed[i]['parent_tag'])
                            query_parsed[i]['terms'] = query_parsed[i]['terms'].strip("()")

            except Exception as e:
                pass

            by_parent = {}
            connector = ""
            for n in query_parsed:
                if n == '&&':
                    connector = " AND "
                    continue
                elif n == '||':
                    connector = " OR "
                    continue

                try:
                    by_parent[n["parent_tag"]] += f"{connector}{n['terms']}"
                except KeyError as e:
                    by_parent[n["parent_tag"]] = f"{n['terms']}"
                except Exception as e:
                    logger.warning(f"Error saving term clause: {e}")


            for key, value in by_parent.items():
                term = value
                term_field = f"in same paragraph in {key}"

        else:
            term = query_item
            if ":" in query_item:
                try:
                    term_field, term_value = query_item.split(":")
                except:
                    # pat = "((?P<parent>parent_tag\:\([a-z\s\(\)]\))\s+(AND|&&)\s+(?P<term>[A-z]+\:[\(\)A-Z]+))+"
                    # too complex
                    pass
                else:
                    term_value = opasQueryHelper.strip_outer_matching_chars(term_value, ")")
                    term = f"{term_value} (in {schemaMap.FIELD2USER_MAP.get(term_field, term_field)})"
            else:
                term = opasQueryHelper.strip_outer_matching_chars(term, ")")
                term = f"{query_item} (in text)"

        #logger.debug("Analysis: Term %s, matches %s", field_clause, results._numFound)
        item = RetItem(term = term, 
                       termCount = results._numFound, 
                       field=term_field
                       )
        return_item_list.append(item)
        rowCount += 1

    #if rowCount > 0:
        #results = solr_docs.query(query_list,
                                    #defType = def_type,
                                    #q_op="AND", 
                                    #queryAnalysis = True,
                                    #fields = summary_fields,
                                    #rows = 1,
                                    #start = 0)

        #item = models.DocumentListItem(term = "(combined)",
                                        #termCount = results._numFound
                                        #)
        #document_item_list.append(item)
        #rowCount += 1
        #print ("Analysis: Term %s, matches %s" % ("combined: ", results._numFound))

    response_info = models.ResponseInfo( count = rowCount,
                                         fullCount = rowCount,
                                         listType = "srclist",
                                         fullCountComplete = True,
                                         request=f"{req_url}",
                                         timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)
                                         )

    response_info.count = len(return_item_list)

    return_list_struct = RetStruct( responseInfo = response_info, 
                                    responseSet = return_item_list
                                    )
    if 0: # api_version == "v1":
        ret_val = RetList(documentList = return_list_struct)
    else:
        ret_val = RetList(termIndex = return_list_struct)


    return ret_val
#-----------------------------------------------------------------------------
def get_term_count_list(term, term_field="text_xml", limit=opasConfig.DEFAULT_LIMIT_FOR_SOLR_RETURNS, offset=0, term_order="index", wildcard_match_limit=4):
    """
    Returns a list of matching terms, and the number of articles with that term.

    Args:
        term (str): Term or comma separated list of terms to return data on.
        term_field (str): the text field to look in
        limit (int, optional): Paging mechanism, return is limited to this number of items.
        offset (int, optional): Paging mechanism, start with this item in limited return set, 0 is first item.
        term_order (str, optional): Return the list in this order, per Solr documentation.  Defaults to "index", which is the Solr determined indexing order.

    Returns:
        list of dicts with term, count and status var ret_status

        return ret_val, ret_status

    Docstring Tests:    
        >>> resp = get_term_count_list("Jealousy")

    """
    ret_val = {}
    ret_status = (200, "OK", "") # default is like HTTP_200_OK

    #  see if there is a wildcard
    if "," in term: 
        # It's a comma separated list!
        try:
            results = solr_docs_term_search( terms_fl=term_field,
                                             terms_list=term.lower(),
                                             terms_sort=term_order,  # index or count
                                             terms_mincount="1",
                                             #terms_ttf=True, 
                                             terms_limit=limit
                                             )
        except Exception as e:
            # ret_status = (e.httpcode, e.reason, e.body) # default is like HTTP_200_OK
            ret_val = models.ErrorReturn(httpcode=e.httpcode, error="Search syntax error (Solr)", error_description=f"There's an error in your search input.")
        else:
            try:
                ret_val = results.terms.get(term_field, {})
            except Exception as e:
                logger.debug(f"get_term_count_list error: {e}")

    elif isinstance(term, list):
        for term_list_component in term:
            try:
                ret_val.update(get_term_count_list(term_list_component))
            except Exception as e:
                logger.debug(f"get_term_count_list error: {e}")

    elif re.match(".*[\*\?\.].*", term):
        # make sure legit
        # do subs to make wildcard * into zero or more regex character, and ? to zero or one
        term = re.sub("(?P<lead>[^\.])(?P<wildc>[\*\?])", "\g<lead>.\g<wildc>", term)
        try:
            re.compile(term)
            is_valid = True
        except:
            is_valid = False

        # #TODO test is_valid below
        try:
            results = solr_docs_term_search(terms_fl=term_field,
                                            terms_limit=wildcard_match_limit,
                                            terms_regex=term.lower(), # + ".*",
                                            terms_mincount="1",
                                            terms_sort="count"  # wildcard, pick highest
                                            )
        except solr.SolrException as e:
            # ret_status = (e.httpcode, e.reason, e.body) # default is like HTTP_200_OK
            ret_val = models.ErrorReturn(httpcode=e.httpcode, error="Search syntax error (Solr)", error_description=f"There's an error in your search input.")

        try:
            ret_val = results.terms.get(term_field, {})
            term_wild = term.replace(".", "")
            ret_val = {f"{key}({term_wild})": value for (key, value) in ret_val.items()}
            ret_val.update({f"Total({term_wild})>=":sum(x for x in ret_val.values())})

        except Exception as e:
            logger.debug(f"get_term_count_list error: {e}")
    else:
        # Note: we need an exact match here.
        try:
            results = solr_docs_term_search( terms_fl=term_field,
                                             terms_prefix=term.lower(),
                                             terms_sort=term_order,  # index or count
                                             terms_mincount="1",
                                             #terms_ttf=True, 
                                             terms_limit=1 # only one response needed
                                             )
        except solr.SolrException as e:
            # ret_status = (e.httpcode, e.reason, e.body) # default is like HTTP_200_OK
            ret_val = models.ErrorReturn(httpcode=e.httpcode, error="Search syntax error (Solr)", error_description=f"There's an error in your search input.")
        else:
            try:
                ret_val = results.terms.get(term_field, {})
            except Exception as e:
                logger.debug(f"get_term_count_list error: {e}")

    return ret_val

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def get_term_index(term_partial,
                   term_field="text",
                   core="docs",
                   req_url:str=None, 
                   limit=opasConfig.DEFAULT_LIMIT_FOR_SOLR_RETURNS,
                   offset=0,
                   order="index"):
    """
    Returns a list of matching terms from an arbitrary field in the Solr docs database, using the /terms search handler

    Args:
        term_partial (str): String prefix of author names to return.
        term_field (str): Where to look for term
        limit (int, optional): Paging mechanism, return is limited to this number of items.
        offset (int, optional): Paging mechanism, start with this item in limited return set, 0 is first item.
        order (str, optional): Return the list in this order, per Solr documentation.  Defaults to "index", which is the Solr determined indexing order.

    Returns:
        models.termIndex: Pydantic structure (dict) for termIndex.  See models.py

    Docstring Tests:    
        >>> resp = get_term_index("love", term_field="art_kwds_str", limit=5)
        >>> resp.termIndex.responseSet[0].termCount > 0
        True
        >>> resp = get_term_index("bion", term_field="art_kwds", limit=5)
        >>> resp.termIndex.responseSet[0].termCount > 0
        True
        >>> resp = get_term_index("will", term_field="text", limit=5)
        >>> resp.termIndex.responseSet[0].termCount > 0
        True
        >>> resp = get_term_index("david", term_field="art_authors_mast", limit=5)
        >>> resp.termIndex.responseSet[0].termCount > 0
        True
        >>> resp = get_term_index("Inter.*", term_field="art_sourcetitlefull", limit=5)
        >>> resp.termIndex.responseSet[0].termCount > 0
        True
        >>> resp = get_term_index("pand", limit=20)
        >>> resp.termIndex.responseSet[0].termCount > 0
        True
        >>> resp = get_term_index("pand.*", limit=5)
        >>> resp.termIndex.responseSet[0].termCount > 0
        True
    """
    ret_val = {}

    core_term_indexers = {
        "docs": solr_docs_term_search,
        "authors": solr_authors_term_search,
    }

    try:
        term_index = core_term_indexers[core]
    except:
        # error
        logger.error("Specified core does not have a term index configured")
    else:
        if "*" in term_partial or "?" in term_partial or "." in term_partial:
            results = term_index( terms_fl=term_field,
                                  terms_regex=term_partial.lower() + ".*",
                                  terms_limit=limit,  
                                  terms_sort=order  # index or count
                                  )           
        else:
            results = term_index( terms_fl=term_field,
                                  terms_prefix=term_partial.lower(),
                                  terms_sort=order,  # index or count
                                  terms_limit=limit
                                  )

        response_info = models.ResponseInfo( limit=limit,
                                             offset=offset,
                                             listType="termindex",
                                             core=core, 
                                             scopeQuery=[f"Terms: {term_partial}"],
                                             solrParams=results._params,
                                             request=f"{req_url}",
                                             timeStamp=datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)
                                             )

        term_index_items = []
        for key, value in results.terms[term_field].items():
            if value > 0:
                item = models.TermIndexItem(term = key, 
                                            field = term_field,
                                            termCount = value,
                                            ) 
                term_index_items.append(item)
                logger.debug ("TermIndexInfo", item)

        response_info.count = len(term_index_items)
        response_info.fullCountComplete = limit >= response_info.count

        term_index_struct = models.TermIndexStruct( responseInfo = response_info, 
                                                    responseSet = term_index_items
                                                    )

        term_index = models.TermIndex(termIndex = term_index_struct)

        ret_val = term_index

    return ret_val

#================================================================================================================
def search_text(query, 
                filter_query = None,
                query_debug = False,
                similar_count = 0,
                full_text_requested = False,
                abstract_requested = False, 
                format_requested = "HTML",
                def_type = None, # edisMax, disMax, or None
                # bring text_xml back in summary fields in case it's missing in highlights! I documented a case where this happens!
                return_field_set=None, 
                summary_fields=None, 
                highlight_fields = 'text_xml',
                facet_fields = None,
                facet_mincount = 1, 
                extra_context_len = None,
                maxKWICReturns = opasConfig.DEFAULT_MAX_KWIC_RETURNS,
                sort="score desc",
                limit=opasConfig.DEFAULT_LIMIT_FOR_SOLR_RETURNS, 
                offset = 0,
                page_offset = None,
                page_limit = None,
                page = None,
                req_url:str = None, 
                #authenticated = None,
                session_info = None 
                ):
    """
    Full-text search, via the Solr server api.
    
    Mapped now (8/2020) to use search_text_qs which works with the query spec directly,
      so this first calls and builds the querySpec, and then calls
      search_text_qs.

    Returns a pair of values: ret_val, ret_status.  The double return value is important in case the Solr server isn't running or it returns an HTTP error.  The 
        ret_val = a DocumentList model object
        ret_status = a status tuple, consisting of a HTTP status code and a status mesage. Default (HTTP_200_OK, "OK")

    >>> resp, status = search_text(query="art_title_xml:'ego identity'", limit=10, offset=0, full_text_requested=False)
    >>> resp.documentList.responseInfo.count >= 10
    True
    """

    solr_query_spec = \
            opasQueryHelper.parse_to_query_spec(
                                                query = query,
                                                filter_query = filter_query,
                                                similar_count=similar_count, 
                                                full_text_requested=full_text_requested,
                                                abstract_requested=abstract_requested,
                                                format_requested=format_requested,
                                                def_type = def_type, # edisMax, disMax, or None
                                                return_field_set=return_field_set, 
                                                summary_fields = summary_fields,  # deprecate?
                                                highlight_fields = highlight_fields,
                                                facet_fields = facet_fields,
                                                facet_mincount=facet_mincount,
                                                extra_context_len=extra_context_len, 
                                                maxKWICReturns=maxKWICReturns,
                                                sort = sort,
                                                limit = limit,
                                                offset = offset,
                                                page_offset = page_offset,
                                                page_limit = page_limit,
                                                page = page,
                                                req_url = req_url
                                                )

    ret_val, ret_status = search_text_qs(solr_query_spec,
                                         limit=limit,
                                         offset=offset, 
                                         req_url=req_url, 
                                         #authenticated=authenticated,
                                         session_info=session_info
                                         )

    return ret_val, ret_status


#================================================================================================================
def search_text_qs(solr_query_spec: models.SolrQuerySpec,
                   extra_context_len=None,
                   req_url: str=None,
                   facet_limit=None,
                   facet_offset=None, 
                   limit=None,
                   offset=None,
                   sort=None, 
                   #authenticated=False,
                   session_info=None,
                   ):
    """
    Full-text search, via the Solr server api.

    Returns a pair of values: ret_val, ret_status.  The double return value is important in case the Solr server isn't running or it returns an HTTP error.  The 
       ret_val = a DocumentList model object
       ret_status = a status tuple, consisting of a HTTP status code and a status mesage. Default (HTTP_200_OK, "OK")

        Original Parameters in API
        Original API return model example, needs to be supported:

                "authormast": "Ringstrom, P.A.",
                "documentID": "IJPSP.005.0257A",
                "documentRef": "Ringstrom, P.A. (2010). Commentary on Donna Orange's, &#8220;Recognition as: Intersubjective Vulnerability in the Psychoanalytic Dialogue&#8221;. Int. J. Psychoanal. Self Psychol., 5(3):257-273.",
                "issue": "3",
                "PEPCode": "IJPSP",
                "pgStart": "257",
                "pgEnd": "273",
                "title": "Commentary on Donna Orange's, &#8220;Recognition as: Intersubjective Vulnerability in the Psychoanalytic Dialogue&#8221;",
                "vol": "5",
                "year": "2010",
                "rank": "100",
                "citeCount5": "1",
                "citeCount10": "3",
                "citeCount20": "3",
                "citeCountAll": "3",
                "kwic": ". . . \r\n        

    """
    ret_val = {}
    ret_status = (200, "OK") # default is like HTTP_200_OK
    global count_anchors
    
    if solr_query_spec.solrQueryOpts is None: # initialize a new model
        solr_query_spec.solrQueryOpts = models.SolrQueryOpts()

    if solr_query_spec.solrQuery is None: # initialize a new model
        solr_query_spec.solrQuery = models.SolrQuery()

    #if authenticated is None:
        #authenticated = solr_query_spec.a

    if extra_context_len is not None:
        solr_query_spec.solrQueryOpts.hlFragsize = extra_context_len
    elif solr_query_spec.solrQueryOpts.hlFragsize is None or solr_query_spec.solrQueryOpts.hlFragsize < opasConfig.DEFAULT_KWIC_CONTENT_LENGTH:
        solr_query_spec.solrQueryOpts.hlFragsize = opasConfig.DEFAULT_KWIC_CONTENT_LENGTH
    #else: # for debug only
        #print (f"Fragment Size: {solr_query_spec.solrQueryOpts.hlFragsize}")

    if solr_query_spec.solrQueryOpts.moreLikeThisCount > 0:
        mlt_fl = "art_kwds, title, text_xml" # Later: solr_query_spec.solrQueryOpts.moreLikeThisFields
        mlt = "true"
        mlt_minwl = 4
        mlt_count = solr_query_spec.solrQueryOpts.moreLikeThisCount
    else:
        mlt_fl = None
        mlt = "false"
        mlt_minwl = None
        mlt_count = 0

    if solr_query_spec.facetFields is not None:
        facet = "on"
    else:
        facet = "off"

    try:
        if solr_query_spec.solrQueryOpts.hlMaxAnalyzedChars < 200: # let caller configure, but not 0!
            solr_query_spec.solrQueryOpts.hlMaxAnalyzedChars = opasConfig.SOLR_HIGHLIGHT_RETURN_FRAGMENT_SIZE
    except:
        solr_query_spec.solrQueryOpts.hlMaxAnalyzedChars = opasConfig.SOLR_HIGHLIGHT_RETURN_FRAGMENT_SIZE
    #else: OK, leave it be!

    try: # must have value
        if solr_query_spec.solrQueryOpts.hlFragsize < opasConfig.DEFAULT_KWIC_CONTENT_LENGTH:
            solr_query_spec.solrQueryOpts.hlFragsize = opasConfig.DEFAULT_KWIC_CONTENT_LENGTH
    except:
        solr_query_spec.solrQueryOpts.hlFragsize = opasConfig.DEFAULT_KWIC_CONTENT_LENGTH
    else:
        pass # else, it's ok
    
    if limit is not None:
        solr_query_spec.limit = limit

    if offset is not None:
        solr_query_spec.offset = offset

    if sort is not None:
        solr_query_spec.solrQuery.sort = sort

    try:
            
        solr_param_dict = { 
                            "q": solr_query_spec.solrQuery.searchQ,
                            "fq": solr_query_spec.solrQuery.filterQ,
                            "q_op": solr_query_spec.solrQueryOpts.qOper, 
                            "debugQuery": solr_query_spec.solrQueryOpts.queryDebug or localsecrets.SOLR_DEBUG,
                            # "defType" : solr_query_spec.solrQueryOpts.defType,
                            "fl" : solr_query_spec.returnFields,         
                            "hl" : solr_query_spec.solrQueryOpts.hl, 
                            "hl_multiterm" : solr_query_spec.solrQueryOpts.hlMultiterm,
                            "hl_fl" : solr_query_spec.solrQueryOpts.hlFields,
                            "hl_usePhraseHighlighter" : solr_query_spec.solrQueryOpts.hlUsePhraseHighlighter, 
                            "hl_snippets" : solr_query_spec.solrQueryOpts.hlMaxKWICReturns,
                            "hl_fragsize" : solr_query_spec.solrQueryOpts.hlFragsize, 
                            "hl_maxAnalyzedChars" : solr_query_spec.solrQueryOpts.hlMaxAnalyzedChars,
                            "facet" : facet,
                            "facet_field" : solr_query_spec.facetFields, #["art_lang", "art_authors"],
                            "facet_mincount" : solr_query_spec.facetMinCount,
                            #hl_method="unified",  # these don't work
                            #hl_encoder="HTML",
                            "mlt" : mlt,
                            "mlt_fl" : mlt_fl,
                            "mlt_count" : mlt_count,
                            "mlt_minwl" : mlt_minwl,
                            "mlt.interestingTerms" : "list",
                            "rows" : solr_query_spec.limit,
                            "start" : solr_query_spec.offset,
                            "sort" : solr_query_spec.solrQuery.sort,
                            "hl_simple_pre" : opasConfig.HITMARKERSTART,
                            "hl_simple_post" : opasConfig.HITMARKEREND        
        }
    except Exception as e:
        logger.error(f"Solr Param Assignment Error {e}")
        
    # add additional facet parameters from faceSpec
    for key, value in solr_query_spec.facetSpec.items():
        if key[0:1] != "f":
            continue
        else:
            solr_param_dict[key] = value

    #allow core parameter here
    if solr_query_spec.core is not None:
        try:
            solr_core = EXTENDED_CORES.get(solr_query_spec.core, None)
        except Exception as e:
            detail=f"Bad Extended Request. Core Specification Error. {e}"
            logger.error(detail)
            ret_val = models.ErrorReturn(httpcode=400, error="Core specification error", error_description=detail)
        else:
            if solr_core is None:
                detail=f"Bad Extended Request. Unknown core specified."
                logger.warning(detail)
                ret_val = models.ErrorReturn(httpcode=400, error="Core specification error", error_description=detail)
    else:
        solr_query_spec.core = "pepwebdocs"
        solr_core = solr_docs

    try:
        results = solr_core.query(**solr_param_dict)

    except solr.SolrException as e:
        if e.reason is not None:
            ret_val = models.ErrorReturn(httpcode=e.httpcode, error="Solr engine returned an unknown error", error_description=f"Solr engine returned error {e.httpcode} - {e.reason}")
            logger.error(f"Solr Runtime Search Error: {e.reason}")
            logger.error(e.body)
        else:
            ret_val = models.ErrorReturn(httpcode=e.httpcode, error="Search syntax error", error_description=f"There's an error in your input (no reason supplied)")
            logger.error(f"Solr Runtime Search Error: {e.httpcode}")
            logger.error(e.body)
        
        ret_status = (e.httpcode, e) # e has type <class 'solrpy.core.SolrException'>, with useful elements of httpcode, reason, and body, e.g.,
                                #  (I added the 400 first element, because then I have a known quantity to catch)
                                #  httpcode: 400
                                #  reason: 'Bad Request'
                                #  body: b'<?xml version="1.0" encoding="UTF-8"?>\n<response>\n\n<lst name="responseHeader">\n  <int name="status">400</int>\n  <int name="QTime">0</int>\n  <lst name="params">\n    
                                #          <str name="hl">true</str>\n    <str name="fl">art_id, art_sourcecode, art_vol, art_year, art_iss, art_iss_title, art_newsecnm, art_pgrg, abstract_xml, art_title, art_author_id, 
                                #          art_citeas_xml, text_xml,score</str>\n    <str name="hl.fragsize">200</str>\n    <str name="hl.usePhraseHighlighter">true</str>\n    <str name="start">0</str>\n    <str name="fq">*:* 
                                #          </str>\n    <str name="mlt.minwl">None</str>\n    <str name="sort">rank asc</str>\n    <str name="rows">15</str>\n    <str name="hl.multiterm">true</str>\n    <str name="mlt.count">2</str>\n
                                #          <str name="version">2.2</str>\n    <str name="hl.simple.pre">%##</str>\n    <str name="hl.snippets">5</str>\n    <str name="q">*:* &amp;&amp; text:depression &amp;&amp; text:"passive withdrawal" </str>\n
                                #          <str name="mlt">false</str>\n    <str name="hl.simple.post">##%</str>\n    <str name="disMax">None</str>\n    <str name="mlt.fl">None</str>\n    <str name="hl.fl">text_xml</str>\n    <str name="wt">xml</str>\n
                                #          <str name="debugQuery">off</str>\n  </lst>\n</lst>\n<lst name="error">\n  <lst name="metadata">\n    <str name="error-class">org.apache.solr.common.SolrException</str>\n
                                #          <str name="root-error-class">org.apache.solr.common.SolrException</str>\n  </lst>\n  <str name="msg">sort param field can\'t be found: rank</str>\n
                                #          <int name="code">400</int>\n</lst>\n</response>\n'

    else: #  search was ok
        try:
            logger.debug("Search Performed: %s", solr_query_spec.solrQuery.searchQ)
            logger.debug("The Filtering: %s", solr_query_spec.solrQuery.filterQ)
            logger.debug("Result  Set Size: %s", results._numFound)
            logger.debug("Return set limit: %s", solr_query_spec.limit)
            scopeofquery = [solr_query_spec.solrQuery.searchQ, solr_query_spec.solrQuery.filterQ]
    
            if ret_status[0] == 200: 
                documentItemList = []
                rowCount = 0
                # rowOffset = 0
                #if solr_query_spec.fullReturn:
                    ## if we're not authenticated, then turn off the full-text request and behave as if we didn't try
                    #if not authenticated: # and file_classification != opasConfig.DOCUMENT_ACCESS_FREE:
                        ## can't bring back full-text
                        #logger.warning("Fulltext requested--by API--but not authenticated.")
                        #solr_query_spec.fullReturn = False
    
                for result in results.results:
                    # reset anchor counts for full-text markup re.sub
                    count_anchors = 0
                    record_count = len(results.results)
                    # authorIDs = result.get("art_authors", None)
                    documentListItem = models.DocumentListItem()
                    documentListItem = get_base_article_info_from_search_result(result, documentListItem)
                    # sometimes, we don't need to check permissions
                    # Always check if fullReturn is selected
                    # Don't check when it's not and a large number of records are requested.
                    if record_count < opasConfig.MAX_RECORDS_FOR_ACCESS_INFO_RETURN:
                        opasDocPerm.get_access_limitations( doc_id=documentListItem.documentID, 
                                                            classification=documentListItem.accessClassification, 
                                                            year=documentListItem.year,
                                                            doi=documentListItem.doi, 
                                                            session_info=session_info, 
                                                            documentListItem=documentListItem) # will updated accessLimited fields in documentListItem
    
                    documentListItem.score = result.get("score", None)               
                    documentID = documentListItem.documentID
                    try:
                        text_xml = results.highlighting[documentID].get("text_xml", None)
                    except:
                        text_xml = None
    
                    if text_xml is None: # try getting it from para
                        try:
                            text_xml = results.highlighting[documentID].get("para", None)
                        except:
                            try:
                                text_xml = result["text_xml"]
                            except:
                                text_xml = result.get("para", None)
    
                    if text_xml is not None and type(text_xml) != list:
                        text_xml = [text_xml]
    
                    # do this before we potentially clear text_xml if no full text requested below
                    if solr_query_spec.abstractReturn:
                        documentListItem = get_excerpt_from_search_result(result, documentListItem, solr_query_spec.returnFormat)
    
                    documentListItem.kwic = "" # need this, so it doesn't default to Nonw
                    documentListItem.kwicList = []
                    # no kwic list when full-text is requested.
                    if text_xml is not None and not solr_query_spec.fullReturn:
                        #kwicList = getKwicList(textXml, extraContextLen=extraContextLen)  # returning context matches as a list, making it easier for clients to work with
                        kwic_list = []
                        for n in text_xml:
                            # strip all tags
                            match = opasxmllib.xml_string_to_text(n)
                            # change the tags the user told Solr to use to the final output tags they want
                            #   this is done to use non-xml-html hit tags, then convert to that after stripping the other xml-html tags
                            match = re.sub(opasConfig.HITMARKERSTART, opasConfig.HITMARKERSTART_OUTPUTHTML, match)
                            match = re.sub(opasConfig.HITMARKEREND, opasConfig.HITMARKEREND_OUTPUTHTML, match)
                            kwic_list.append(match)
    
                        kwic = " . . . ".join(kwic_list)  # how its done at GVPi, for compatibility (as used by PEPEasy)
                        # we don't need fulltext
                        text_xml = None
                        #print ("Document Length: {}; Matches to show: {}".format(len(textXml), len(kwicList)))
                    else: # either fulltext requested, or no document, we don't need kwic
                        kwic_list = []
                        kwic = ""  # this has to be "" for PEP-Easy, or it hits an object error.  
    
                    if kwic != "": documentListItem.kwic = kwic
                    if kwic_list != []: documentListItem.kwicList = kwic_list
    
                    # see if this article is an offsite article
                    offsite = result.get("art_offsite", False)
                    # ########################################################################
                    # This is the room where where full-text return HAPPENS
                    # ########################################################################
                    if solr_query_spec.fullReturn and not documentListItem.accessLimited and not offsite:
                        documentListItem = get_fulltext_from_search_results(result,
                                                                            text_xml,
                                                                            solr_query_spec.page,
                                                                            solr_query_spec.page_offset,
                                                                            solr_query_spec.page_limit,
                                                                            documentListItem)
                    else: # by virtue of not calling that...
                        # no full-text if accessLimited or offsite article
                        # free up some memory, since it may be large
                        result["text_xml"] = None                   
    
                    stat = {}
                    count_all = result.get("art_cited_all", None)
                    if count_all is not None:
                        stat["art_cited_5"] = result.get("art_cited_5", None)
                        stat["art_cited_10"] = result.get("art_cited_10", None)
                        stat["art_cited_20"] = result.get("art_cited_20", None)
                        stat["art_cited_all"] = count_all
    
                    count0 = result.get("art_views_lastcalyear", 0)
                    count1 = result.get("art_views_lastweek", 0)
                    count2 = result.get("art_views_last1mos", 0)
                    count3 = result.get("art_views_last6mos", 0)
                    count4 = result.get("art_views_last12mos", 0)
    
                    if count0 + count1 + count2 + count3+ count4 > 0:
                        stat["art_views_lastcalyear"] = count0
                        stat["art_views_lastweek"] = count1
                        stat["art_views_last1mos"] = count2
                        stat["art_views_last6mos"] = count3
                        stat["art_views_last12mos"] = count4
    
                    if stat == {}:
                        stat = None
    
                    documentListItem.stat = stat
    
                    similarityMatch = None
                    if mlt_count > 0:
                        if results.moreLikeThis[documentID] is not None:
                            similarityMatch = {}
                            # remove text
                            similarityMatch["similarDocs"] = {}
                            similarityMatch["similarDocs"][documentID] = []
                            for n in results.moreLikeThis[documentID]:
                                likeThisListItem = models.DocumentListItem()
                                #n["text_xml"] = None
                                n = get_base_article_info_from_search_result(n, likeThisListItem)                    
                                similarityMatch["similarDocs"][documentID].append(n)
    
                            similarityMatch["similarMaxScore"] = results.moreLikeThis[documentID].maxScore
                            similarityMatch["similarNumFound"] = results.moreLikeThis[documentID].numFound
                            # documentListItem.moreLikeThis = results.moreLikeThis[documentID]
    
                    if similarityMatch is not None: documentListItem.similarityMatch = similarityMatch
                    documentListItem.docLevel = result.get("art_level", None)
                    parent_tag = result.get("parent_tag", None)
                    if parent_tag is not None:
                        documentListItem.docChild = {}
                        documentListItem.docChild["parent_tag"] = parent_tag
                        documentListItem.docChild["para"] = result.get("para", None)
                    #else:
                        #documentListItem.docChild = None
    
                    sort_field = None
                    if solr_query_spec.solrQuery.sort is not None:
                        try:
                            sortby = re.search("(?P<field>[a-z_]+[1-9][0-9]?)[ ]*?", solr_query_spec.solrQuery.sort)
                        except Exception as e:
                            sort_field = None
                        else:
                            if sortby is not None:
                                sort_field = sortby.group("field")
    
                    documentListItem.score = result.get("score", None)
                    documentListItem.rank = rowCount + 1
                    if sort_field is not None:
                        if sort_field == "art_cited_all":
                            documentListItem.rank = result.get("art_cited_all", None) 
                        elif sort_field == "score":
                            documentListItem.rank = result.get("score", None)
                        else:
                            documentListItem.rank = result.get(sort_field, None)
                            
                    rowCount += 1
                    # add it to the set!
                    documentItemList.append(documentListItem)
                    if rowCount > solr_query_spec.limit:
                        break
    
                try:
                    facet_counts = results.facet_counts
                except:
                    facet_counts = None
    
            if req_url is None:
                req_url = solr_query_spec.urlRequest
    
            # Moved this down here, so we can fill in the Limit, Page and Offset fields based on whether there
            #  was a full-text request with a page offset and limit
            # Solr search was ok
            responseInfo = models.ResponseInfo(
                                               count = len(results.results),
                                               fullCount = results._numFound,
                                               totalMatchCount = results._numFound,
                                               limit = solr_query_spec.limit,
                                               offset = solr_query_spec.offset,
                                               page = solr_query_spec.page, 
                                               listType="documentlist",
                                               scopeQuery=[scopeofquery], 
                                               fullCountComplete = solr_query_spec.limit >= results._numFound,
                                               solrParams = results._params,
                                               facetCounts=facet_counts,
                                               #authenticated=authenticated, 
                                               request=f"{req_url}",
                                               core=solr_query_spec.core, 
                                               timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
            )
    
            # responseInfo.count = len(documentItemList)
    
            documentListStruct = models.DocumentListStruct( responseInfo = responseInfo, 
                                                            responseSet = documentItemList
                                                            )
    
            documentList = models.DocumentList(documentList = documentListStruct)
    
            ret_val = documentList
            
        except Exception as e:
            logger.error(f"problem with query {e}")
            

    return ret_val, ret_status

##================================================================================================================
def submit_file(submit_token: bytes, xml_data: bytes, pdf_data: bytes): 
    pass

# -------------------------------------------------------------------------------------------------------
# run it (tests)!

if __name__ == "__main__":
    sys.path.append('./config') 

    print (40*"*", "opasAPISupportLib Tests", 40*"*")
    print ("Running in Python %s" % sys.version_info[0])
    logger = logging.getLogger(__name__)
    # extra logging for standalong mode 
    logger.setLevel(logging.WARN)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARN)
    # create formatter
    formatter = logging.Formatter('%(asctime)s %(name)s %(lineno)d - %(levelname)s %(message)s')    
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)

    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
    print ("All tests complete!")
    print ("Fini")
