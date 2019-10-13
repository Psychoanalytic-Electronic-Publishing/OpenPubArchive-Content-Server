#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326

"""
opasAPISupportLib

This library is meant to hold the heart of the API based Solr queries and other support 
functions.  

2019.0614.1 - Python 3.7 compatible.  Work in progress.

"""
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2019.0714.1"
__status__      = "Development"

import sys
    
import solrpy

import http.cookies
import re
import os
import os.path
import secrets
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.responses import Response
import time
import datetime
from datetime import datetime, timedelta
from typing import Union, Optional, Tuple, List
from enum import Enum
import pymysql

import opasConfig as opasConfig
import stdMessageLib as stdMessageLib
import localsecrets as localsecrets
from localsecrets import BASEURL, SOLRURL, SOLRUSER, SOLRPW, DEBUG_DOCUMENTS, CONFIG, COOKIE_DOMAIN
from stdMessageLib import copyrightPageHTML  # copyright page text to be inserted in ePubs and PDFs

pyVer = 2
if (sys.version_info > (3, 0)):
    # Python 3 code in this block
    from io import StringIO
    pyVer = 3
else:
    # Python 2 code in this block
    import StringIO
    
#import pysolr
import solrpy as solr
# import solr
import lxml
import logging
logger = logging.getLogger(__name__)

from lxml import etree
from pydantic import BaseModel
from pydantic import ValidationError

from ebooklib import epub

#import imp

# note: documents and documentList share the same internals, except the first level json label (documents vs documentlist)
import models

import opasXMLHelper as opasxmllib
import opasGenSupportLib as opasgenlib
import opasCentralDBLib
import sourceInfoDB as SourceInfoDB
    
sourceDB = SourceInfoDB.SourceInfoDB()

#from solrq import Q
import json

# Setup a Solr instance. The timeout is optional.
#solr = pysolr.Solr('http://localhost:8983/solr/pepwebproto', timeout=10)
#This is the old way -- should switch to class Solr per https://pythonhosted.org/solrpy/reference.html
if SOLRUSER is not None:
    solr_docs = solr.SolrConnection(SOLRURL + 'pepwebdocs', http_user=SOLRUSER, http_pass=SOLRPW)
    solr_refs = solr.SolrConnection(SOLRURL + 'pepwebrefs', http_user=SOLRUSER, http_pass=SOLRPW)
    solr_gloss = solr.SolrConnection(SOLRURL + 'pepwebglossary', http_user=SOLRUSER, http_pass=SOLRPW)
    solr_authors = solr.SolrConnection(SOLRURL + 'pepwebauthors', http_user=SOLRUSER, http_pass=SOLRPW)
    solr_author_term_search = solr.SearchHandler(solr_authors, "/terms")

else:
    solr_docs = solr.SolrConnection(SOLRURL + 'pepwebdocs')
    solr_refs = solr.SolrConnection(SOLRURL + 'pepwebrefs')
    solr_gloss = solr.SolrConnection(SOLRURL + 'pepwebglossary')
    solr_authors = solr.SolrConnection(SOLRURL + 'pepwebauthors')
    solr_author_term_search = solr.SearchHandler(solr_authors, "/terms")

#API endpoints
documentURL = "/v1/Documents/"
TIME_FORMAT_STR = '%Y-%m-%dT%H:%M:%SZ'

#-----------------------------------------------------------------------------
def get_max_age(keep_active=False):
    if keep_active:    
        ret_val = opasConfig.COOKIE_MAX_KEEP_TIME    
    else:
        ret_val = opasConfig.COOKIE_MIN_KEEP_TIME     
    return ret_val  # maxAge

#-----------------------------------------------------------------------------
def get_session_info(request: Request,
                     resp: Response, 
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
    print ("Get Session Info, Session ID via GetSessionID: ", session_id)
    
    if session_id is None or session_id=='' or force_new_session:  # we need to set it
        # get new sessionID...even if they already had one, this call forces a new one
        print ("session_id is none (or forcedNewSession).  We need to start a new session.")
        ocd, session_info = start_new_session(resp, request, access_token, keep_active=keep_active, user=user)  
        
    else: # we already have a session_id, no need to recreate it.
        # see if an access_token is already in cookies
        access_token = get_access_token(request)
        expiration_time = get_expiration_time(request)
        print (f"session_id {session_id} is already set.")
        try:
            ocd = opasCentralDBLib.opasCentralDB(session_id, access_token, expiration_time)
            session_info = ocd.get_session_from_db(session_id)
            if session_info is None:
                # this is an error, and means there's no recorded session info.  Should we create a s
                #  session record, return an error, or ignore? #TODO
                # try creating a record
                username="NotLoggedIn"
                ret_val, session_info = ocd.save_session(session_id, 
                                                         userID=0,
                                                         userIP=request.client.host, 
                                                         connectedVia=request.headers["user-agent"],
                                                         username=username
                                                        )  # returns save status and a session object (matching what was sent to the db)

        except ValidationError as e:
            print("Validation Error: ", e.json())             
    
    print ("getSessionInfo: ", session_info)
    return ocd, session_info
    
def is_session_authenticated(request, resp):
    """
    Look to see if the session has been marked authenticated in the database
    """
    ocd, sessionInfo = get_session_info(request, resp)
    # sessionID = sessionInfo.session_id
    # is the user authenticated? if so, loggedIn is true
    ret_val = sessionInfo.authenticated
    return ret_val
    
def extract_html_fragment(html_str, xpath_to_extract="//div[@id='abs']"):
    # parse HTML
    htree = etree.HTML(html_str)
    ret_val = htree.xpath(xpath_to_extract)
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
    print ("************** Starting a new SESSION!!!! *************")
    # session_start=datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    max_age = get_max_age(keep_active)
    token_expiration_time=datetime.utcfromtimestamp(time.time() + max_age) # .strftime('%Y-%m-%d %H:%M:%S')
    if session_id == None:
        session_id = secrets.token_urlsafe(16)
        logger.info("startNewSession assigning New Session ID: {}".format(session_id))

    set_cookies(resp, session_id, access_token, token_expires_time=token_expiration_time)
    # get the database Object
    ocd = opasCentralDBLib.opasCentralDB()
    # save the session info
    if user:
        username=user.username
        ret_val, sessionInfo = ocd.save_session(session_id=session_id, 
                                                username=user.username,
                                                userID=user.user_id,
                                                expiresTime=token_expiration_time,
                                                userIP=request.client.host, 
                                                connectedVia=request.headers["user-agent"],
                                                accessToken = access_token
                                                )
    else:
        username="NotLoggedIn"
        ret_val, sessionInfo = ocd.save_session(session_id, 
                                                userID=0,
                                                expiresTime=token_expiration_time,
                                                userIP=request.client.host, 
                                                connectedVia=request.headers["user-agent"],
                                                username=username)  # returns save status and a session object (matching what was sent to the db)

    # return the object so the caller can get the details of the session
    return ocd, sessionInfo

#-----------------------------------------------------------------------------
def delete_cookies(resp: Response, session_id=None, access_token=None):
    """
    Delete the session and or accessToken cookies in the response header 
   
    """

    print ("Setting specified cookies to empty to delete them")
    expires = datetime.utcnow()
    if session_id is not None:
        set_cookie(resp, "opasSessionID", value='', domain=COOKIE_DOMAIN, path="/", expires=expires, max_age=0)

    if access_token is not None:
        set_cookie(resp, "opasAccessToken", value='', domain=COOKIE_DOMAIN, path="/", expires=expires, max_age=0)
    return resp
    
#-----------------------------------------------------------------------------
def set_cookies(resp: Response, session_id, access_token=None, max_age=None, token_expires_time=None):
    """
    Set the session and or accessToken cookies in the response header 
    
    if accessToken isn't supplied, it is not set.
    
    """
    
    print ("Setting cookies for {}".format(COOKIE_DOMAIN))
    if session_id is not None:
        print ("Session Cookie being Written from SetCookies")
        set_cookie(resp, "opasSessionID", session_id, domain=COOKIE_DOMAIN, expires=token_expires_time, httponly=False)

    if access_token is not None:
        access_token = access_token.decode("utf-8")
        set_cookie(resp, "opasAccessToken", access_token, domain=COOKIE_DOMAIN, httponly=False, expires=token_expires_time, max_age=max_age) #, expires=tokenExpiresTime)

    return resp
    
#-----------------------------------------------------------------------------
def parse_cookies_from_header(request):
    ret_val = {}
    client_supplied_cookies = request.headers.get("cookie", None)
    if client_supplied_cookies is not None:
        cookie_statements = client_supplied_cookies.split(";")
        for n in cookie_statements:
            cookie, value = n.split("=")
            ret_val[cookie] = value

    return ret_val

#-----------------------------------------------------------------------------
def get_session_id(request):
    session_cookie_name = "opasSessionID"
    ret_val = request.cookies.get(session_cookie_name, None)
    
    if ret_val is None:
        cookie_dict = parse_cookies_from_header(request)
        ret_val = cookie_dict.get(session_cookie_name, None)
        if ret_val is not None:
            print ("getSessionID: Session cookie had to be retrieved from header: {}".format(ret_val))
    else:
        print ("getSessionID: Session cookie from client: {}".format(ret_val))
    return ret_val

#-----------------------------------------------------------------------------
def get_access_token(request):
    ret_val = request.cookies.get("opasAccessToken", None)
    return ret_val

#-----------------------------------------------------------------------------
def get_expiration_time(request):
    ret_val = request.cookies.get("opasSessionExpirestime", None)
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
def force_string_return_from_various_return_types(text_str, min_length=5):
    """
    Sometimes the return isn't a string (it seems to often be "bytes") 
      and depending on the schema, from Solr it can be a list.  And when it
      involves lxml, it could even be an Element node or tree.
      
    This checks the type and returns a string, converting as necessary.
    
    >>> force_string_return_from_various_return_types(["this is really a list",], minLength=5)
    'this is really a list'

    """
    ret_val = None
    if text_str is not None:
        if isinstance(text_str, str):
            if len(text_str) > min_length:
                # we have an abstract
                ret_val = text_str
        elif isinstance(text_str, list):
            ret_val = text_str[0]
            if ret_val == [] or ret_val == '[]':
                ret_val = None
        else:
            logger.error("Type mismatch on Solr Data")
            print ("forceStringReturn ERROR: %s" % type(ret_val))

        try:
            if isinstance(ret_val, lxml.etree._Element):
                ret_val = etree.tostring(ret_val)
            
            if isinstance(ret_val, bytes) or isinstance(ret_val, bytearray):
                logger.error("Byte Data")
                ret_val = ret_val.decode("utf8")
        except Exception as e:
            err = "forceStringReturn Error forcing conversion to string: %s / %s" % (type(ret_val), e)
            logger.error(err)
            print (err)
            
    return ret_val        

#-----------------------------------------------------------------------------
def get_article_data_raw(article_id, fields=None):  # DEPRECATED??????? (at least, not used)
    """
    Fetch an article "Doc" from the Solr solrDocs core.  If fields is none, it fetches all fields.

    This returns a dictionary--the one returned by Solr 
      (hence why the function is Raw rather than Pydantic like getArticleData)
      
    >>> result = get_article_data_rawleDataRaw("APA.009.0331A")
    >>> result["art_id"]
    APA.009.0331A
    
    """
    ret_val = None
    if article_id != "":
        try:
            results = solr_docs.query(q = "art_id:{}".format(article_id),  fields = fields)
        except Exception as e:
            logger.error("Solr Error: {}".format(e))
            ret_val = None
        else:
            if results._numFound == 0:
                ret_val = None
            else:
                ret_val = results.results[0]

    return ret_val
                
#-----------------------------------------------------------------------------
def get_article_data(article_id, fields=None):  # DEPRECATED???????  (at least, not used)
    """
    Fetch an article "Doc" from the Solr solrDocs core.  If fields is none, it fetches all fields.

    Returns the pydantic model object for a document in a regular documentListStruct

    >>> result = get_article_data("APA.009.0331A")
    >>> result.documentList.responseSet[0].documentID
    APA.009.0331A
    
    """
    ret_val = None
    if article_id != "":
        try:
            results = solr_docs.query(q = "art_id:{}".format(article_id),  fields = fields)
        except Exception as e:
            logger.error("Solr Error: {}".format(e))
            ret_val = None
        else:
            if results._numFound == 0:
                ret_val = None
            else:
                ret_val = results.results[0]
    limit = 5 # for now, we may make this 1
    offset = 0
    response_info = models.ResponseInfo (count = len(results.results),
                                         fullCount = results._numFound,
                                         totalMatchCount = results._numFound,
                                         limit = limit,
                                         offset = offset,
                                         listType="documentlist",
                                         scopeQuery=None,
                                         fullCountComplete = limit >= results._numFound,
                                         solrParams = results._params,
                                         timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                       )

    document_item_list = []
    row_count = 0
    # row_offset = 0
    for result in results.results:
        author_ids = result.get("art_authors", None)
        if author_ids is None:
            authorMast = None
        else:
            authorMast = opasgenlib.deriveAuthorMast(author_ids)

        pgrg = result.get("art_pgrg", None)
        if pgrg is not None:
            pg_start, pg_end = opasgenlib.pgrg_splitter(pgrg)
         
        # TODO: Highlighting return is incomplete.  Return from non-highlighted results, and figure out workaround later.
        
        document_id = result.get("art_id", None)        
        #titleXml = results.highlighting[documentID].get("art_title_xml", None)
        title_xml = result.get("art_title_xml", None)
        title_xml = force_string_return_from_various_return_types(title_xml)
        #abstractsXml = results.highlighting[documentID].get("abstracts_xml", None)
        abstracts_xml = result.get("abstracts_xml", None)
        abstracts_xml  = force_string_return_from_various_return_types(abstracts_xml )
        #summariesXml = results.highlighting[documentID].get("abstracts_xml", None)
        summaries_xml = result.get("abstracts_xml", None)
        summaries_xml  = force_string_return_from_various_return_types(summaries_xml)
        #textXml = results.highlighting[documentID].get("text_xml", None)
        text_xml = result.get("text_xml", None)
        text_xml  = force_string_return_from_various_return_types(text_xml)
        kwic_list = []
        kwic = ""  # this has to be "" for PEP-Easy, or it hits an object error.  
    
        if DEBUG_DOCUMENTS != 1:
            if not user_logged_in or not full_text_requested:
                text_xml = get_excerpt_from_abs_sum_or_doc(xml_abstract=abstracts_xml,
                                                           xml_summary=summaries_xml,
                                                           xml_document=text_xml
                                                          )

        citeas = result.get("art_citeas_xml", None)
        citeas = force_string_return_from_various_return_types(citeas)
        
        try:
            item = models.DocumentListItem(PEPCode = result.get("art_pepsrccode", None), 
                                           year = result.get("art_year", None),
                                           vol = result.get("art_vol", None),
                                           pgRg = pgrg,
                                           pgStart = pg_start,
                                           pgEnd = pg_end,
                                           authorMast = authorMast,
                                           documentID = document_id,
                                           documentRefHTML = citeas,
                                           documentRef = opasxmllib.xml_elem_or_str_to_text(citeas, default_return=""),
                                           title = title_xml,
                                           abstract = abstracts_xml,
                                           documentText = None, #textXml,
                                           score = result.get("score", None), 
                                           )
        except ValidationError as e:
            logger.error(e.json())  
            #print (e.json())
        else:
            row_count += 1
            print ("{}:{}".format(row_count, citeas))
            document_item_list.append(item)
            if row_count > limit:
                break

    response_info.count = len(document_item_list)
    
    document_list_struct = models.DocumentListStruct( responseInfo = response_info, 
                                                      responseSet = document_item_list
                                                    )
    
    document_list = models.DocumentList(documentList = document_list_struct)
    
    ret_val = document_list
    
    return ret_val

#-----------------------------------------------------------------------------
def get_list_of_most_downloaded(period: str="all",
                                document_type: str="journals",
                                author: str=None,
                                title: str=None,
                                journal_name: str=None,
                                limit: int=5,
                                offset=0):
    """
    Return the most downloaded (viewed) journal articles duing the prior period years.
    
    Args:
        period (int or str, optional): Look only at articles this many years back to current.  Defaults to 5.
        documentType (str, optional): The type of document, enumerated set: journals, books, videos, or all.  Defaults to "journals"
        author (str, optional): Filter, include matching author names per string .  Defaults to None (no filter).
        title (str, optional): Filter, include only titles that match.  Defaults to None (no filter).
        journalName (str, optional): Filter, include only journals matching this name.  Defaults to None (no filter).
        limit (int, optional): Paging mechanism, return is limited to this number of items.
        offset (int, optional): Paging mechanism, start with this item in limited return set, 0 is first item.

    Returns:
        models.DocumentList: Pydantic structure (dict) for DocumentList.  See models.py

    Docstring Tests:
    
    >>> result = get_list_of_most_downloaded()

    >>> result.documentList.responseSet[0].documentID


    """
    if period.lower() not in ['5', '10', '20', 'all']:
        period = '5'

    ocd = opasCentralDBLib.opasCentralDB()
    count, most_downloaded = ocd.get_most_downloaded( view_period=period, 
                                                      document_type=document_type, 
                                                      author=author, 
                                                      title=title, 
                                                      journal_name=journal_name, 
                                                      limit=limit, offset=offset
                                                    )  # (most viewed)
    
    response_info = models.ResponseInfo( count = count,
                                         fullCount = None,
                                         limit = limit,
                                         offset = offset,
                                         listType="mostviewed",
                                         fullCountComplete = False,
                                         timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                       )

    
    document_list_items = []
    row_count = 0

    for download in most_downloaded:
        hdg_author = download.get("hdgauthor", None)
        hdg_title = download.get("hdgtitle", None)
        src_title = download.get("srctitleseries", None)
        volume = download.get("vol", None)
        issue = download.get("issue", "")
        year = download.get("pubyear", None)
        pgrg = download.get("pgrg", None)
        pg_start, pg_end = opasgenlib.pgrg_splitter(pgrg)
        xmlref = download.get("xmlref", None)
        citeas = opasxmllib.get_html_citeas( authors_bib_style=hdg_author, 
                                              art_year=year,
                                              art_title=hdg_title, 
                                              art_pep_sourcetitle_full=src_title, 
                                              art_vol=volume, 
                                              art_pgrg=pgrg
                                            )

        item = models.DocumentListItem( documentID = download.get("documentid", None),
                                        instanceCount = download.get("last12months", None),
                                        title = download.get("srctitleseries", None),
                                        PEPCode = download.get("jrnlcode", None), 
                                        authorMast = download.get("authorMast", None),
                                        year = download.get("pubyear", None),
                                        vol = download.get("vol", None),
                                        pgRg = download.get("pgrg", None),
                                        issue = issue,
                                        pgStart = pg_start,
                                        pgEnd = pg_end,
                                        count1 = download.get("lastweek", None),
                                        count2 = download.get("lastmonth", None),
                                        count3 = download.get("last6months", None),
                                        count4 = download.get("last12months", None),
                                        count5 = download.get("lastcalyear", None),
                                        documentRefHTML = citeas,
                                        documentRef = opasxmllib.xml_elem_or_str_to_text(xmlref, default_return=None),
                                     ) 
        row_count += 1
        print (item)
        document_list_items.append(item)
        if row_count > limit:
            break

    # Not sure why it doesn't come back sorted...so we sort it here.
    #ret_val2 = sorted(ret_val, key=lambda x: x[1], reverse=True)
    
    response_info.count = len(document_list_items)
    
    document_list_struct = models.DocumentListStruct( responseInfo = response_info, 
                                                      responseSet = document_list_items
                                                    )
    
    document_list = models.DocumentList(documentList = document_list_struct)
    
    ret_val = document_list
    
    return ret_val   


#-----------------------------------------------------------------------------
def database_get_most_cited(period: models.TimePeriod='5',
                            limit: int=10,
                            offset: int=0):
    """
    Return the most cited journal articles duing the prior period years.
    
    period must be either '5', 10, '20', or 'all'
    
    >>> result = database_get_most_cited()
    Number found: 114589
    >>> result.documentList.responseSet[0].documentID
    'IJP.027.0099A'

    """
    if str(period).lower() not in models.TimePeriod._value2member_map_:
        period = '5'
    
    results = solr_docs.query( q = "*:*",  
                               fl = f"art_id, title, art_vol, art_iss, art_year,  art_pepsrccode, \
                                     art_cited_{period}, art_cited_all, timestamp, art_pepsrccode, \
                                     art_pepsourcetype, art_pepsourcetitleabbr, art_pgrg, \
                                     art_citeas_xml, art_authors_mast, abstract_xml, text_xml",
                               fq = "art_pepsourcetype: journal",
                               sort = f"art_cited_{period} desc",
                               limit = limit
                              )

    print ("databaseGetMostCited Number found: %s" % results._numFound)
    
    response_info = models.ResponseInfo( count = len(results.results),
                                         fullCount = results._numFound,
                                         limit = limit,
                                         offset = offset,
                                         listType="mostcited",
                                         fullCountComplete = limit >= results._numFound,
                                         timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR) 
                                       )

    
    document_list_items = []
    row_count = 0
    # row_offset = 0

    for result in results:
        PEPCode = result.get("art_pepsrccode", None)
        # volume = result.get("art_vol", None)
        # issue = result.get("art_iss", "")
        # year = result.get("art_year", None)
        # abbrev = result.get("art_pepsourcetitleabbr", "")
        # updated = result.get("timestamp", None)
        # updated = updated.strftime('%Y-%m-%d')
        pgrg = result.get("art_pgrg", None)
        pg_start, pg_end = opasgenlib.pgrg_splitter(pgrg)
        
        #displayTitle = abbrev + " v%s.%s (%s) (Added: %s)" % (volume, issue, year, updated)
        #volumeURL = "/v1/Metadata/Contents/%s/%s" % (PEPCode, issue)
        
        citeas = result.get("art_citeas_xml", None)
        art_abstract = result.get("art_abstract", None)
        
        item = models.DocumentListItem( documentID = result.get("art_id", None),
                                        instanceCount = result.get(f"art_cited_{period}", None),
                                        title = result.get("art_pepsourcetitlefull", ""),
                                        PEPCode = PEPCode, 
                                        authorMast = result.get("art_authors_mast", None),
                                        year = result.get("art_year", None),
                                        vol = result.get("art_vol", None),
                                        issue = result.get("art_iss", ""),
                                        pgRg = pgrg,
                                        pgStart = pg_start,
                                        pgEnd = pg_end,
                                        documentRefHTML = citeas,
                                        documentRef = opasxmllib.xml_elem_or_str_to_text(citeas, default_return=None),
                                        abstract = art_abstract
                                      ) 
        row_count += 1
        document_list_items.append(item)
        if row_count > limit:
            break

    # Not sure why it doesn't come back sorted...so we sort it here.
    #ret_val2 = sorted(ret_val, key=lambda x: x[1], reverse=True)
    
    response_info.count = len(document_list_items)
    
    document_list_struct = models.DocumentListStruct( responseInfo = response_info, 
                                                      responseSet = document_list_items
                                                    )
    
    document_list = models.DocumentList(documentList = document_list_struct)
    
    ret_val = document_list
    
    return ret_val   

#-----------------------------------------------------------------------------
def database_whats_new(days_back=7, limit=opasConfig.DEFAULT_LIMIT_FOR_WHATS_NEW, offset=0):
    """
    Return a what's been updated in the last week
    
    >>> result = database_whats_new()
    Number found: 91
    """    
    
    try:
        results = solr_docs.query(q = f"timestamp:[NOW-{daysBack}DAYS TO NOW]",  
                                 fl = "art_id, title, art_vol, art_iss, art_pepsrccode, timestamp, art_pepsourcetype",
                                 fq = "{!collapse field=art_pepsrccode max=art_year_int}",
                                 sort="timestamp", sort_order="desc",
                                 rows=25, offset=0,
                                 )
    
        print ("databaseWhatsNew Number found: %s" % results._numFound)
    except Exception as e:
        print (f"Solr Search Exception: {e}")
    
    if results._numFound == 0:
        try:
            results = solr_docs.query( q = "art_pepsourcetype:journal",  
                                       fl = "art_id, title, art_vol, art_iss, art_pepsrccode, timestamp, art_pepsourcetype",
                                       fq = "{!collapse field=art_pepsrccode max=art_year_int}",
                                       sort="timestamp", sort_order="desc",
                                       rows=25, offset=0,
                                     )
    
            print ("databaseWhatsNew Expanded search to most recent...Number found: %s" % results._numFound)

        except Exception as e:
            print (f"Solr Search Exception: {e}")
    
    response_info = models.ResponseInfo( count = len(results.results),
                                         fullCount = results._numFound,
                                         limit = limit,
                                         offset = offset,
                                         listType="newlist",
                                         fullCountComplete = limit >= results._numFound,
                                         timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                       )

    
    whats_new_list_items = []
    row_count = 0
    already_seen = []
    for result in results:
        PEPCode = result.get("art_pepsrccode", None)
        #if PEPCode is None or PEPCode in ["SE", "GW", "ZBK", "IPL"]:  # no books
            #continue
        pep_source_type = result.get("art_pepsourcetype", None)
        if pep_source_type != "journal":
            continue
            
        volume = result.get("art_vol", None)
        issue = result.get("art_iss", "")
        year = result.get("art_year", None)
        abbrev = sourceDB.sourceData[PEPCode].get("sourcetitleabbr", "")
        updated = result.get("timestamp", None)
        updated = updated.strftime('%Y-%m-%d')
        display_title = abbrev + " v%s.%s (%s) " % (volume, issue, year)
        if display_title in already_seen:
            continue
        else:
            already_seen.append(display_title)
        volume_url = "/v1/Metadata/Contents/%s/%s" % (PEPCode, issue)
        src_title = sourceDB.sourceData[PEPCode].get("sourcetitlefull", "")
            
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

#-----------------------------------------------------------------------------
def search_like_the_pep_api():
    pass  # later

#-----------------------------------------------------------------------------
def metadata_get_volumes(pep_code, year="*", limit=opasConfig.DEFAULT_LIMIT_FOR_VOLUME_LISTS, offset=0):
    """
    Get a list of volumes for this pep_code.
    
    #TODO: Not currently used in OPAS server though.  Deprecate?
    
    """
    ret_val = []
           
    results = solr_docs.query( q = "art_pepsrccode:%s && art_year:%s" % (pep_code, year),  
                               fields = "art_vol, art_year",
                               sort="art_year", sort_order="asc",
                               fq="{!collapse field=art_vol}",
                               rows=limit, start=offset
                             )

    print ("metadataGetVolumes Number found: %s" % results._numFound)
    response_info = models.ResponseInfo( count = len(results.results),
                                         fullCount = results._numFound,
                                         limit = limit,
                                         offset = offset,
                                         listType="volumelist",
                                         fullCountComplete = limit >= results._numFound,
                                         timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                       )

    volume_item_list = []
    for result in results.results:
        item = models.VolumeListItem( PEPCode = pep_code, 
                                      year = result.get("art_year", None),
                                      vol = result.get("art_vol", None),
                                      score = result.get("score", None)
                                    )
    
        #print (item)
        volume_item_list.append(item)
       
    response_info.count = len(volume_item_list)
    
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
                          limit=opasConfig.DEFAULT_LIMIT_FOR_CONTENTS_LISTS, offset=0):
    """
    Return a jounals contents
    
    >>> metadata_get_contents("IJP", "1993", limit=5, offset=0)
    <DocumentList documentList=<DocumentListStruct responseInfo=<models.ResponseInfo count=5 limit=5 offset=0 page=No…>
    >>> metadata_get_contents("IJP", "1993", limit=5, offset=5)
    <DocumentList documentList=<DocumentListStruct responseInfo=<models.ResponseInfo count=5 limit=5 offset=5 page=No…>
    """
    ret_val = []
    if year == "*" and vol != "*":
        # specified only volume
        field="art_vol"
        search_val = vol
    else:  #Just do year
        field="art_year"
        search_val = "*"
        
    results = solr_docs.query(q = "art_pepsrccode:{} && {}:{}".format(pep_code, field, search_val),  
                             fields = "art_id, art_vol, art_year, art_iss, art_iss_title, art_newsecnm, art_pgrg, art_title, art_author_id, art_citeas_xml",
                             sort="art_year, art_pgrg", sort_order="asc",
                             rows=limit, start=offset
                             )

    response_info = models.ResponseInfo( count = len(results.results),
                                         fullCount = results._numFound,
                                         limit = limit,
                                         offset = offset,
                                         listType="documentlist",
                                         fullCountComplete = limit >= results._numFound,
                                         timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                       )

    document_item_list = []
    for result in results.results:
        # transform authorID list to authorMast
        authorIDs = result.get("art_author_id", None)
        if authorIDs is None:
            authorMast = None
        else:
            authorMast = opasgenlib.deriveAuthorMast(authorIDs)
        
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
                                score = result.get("score", None)
                                )
        #print (item)
        document_item_list.append(item)

    response_info.count = len(document_item_list)
    
    document_list_struct = models.DocumentListStruct( responseInfo = response_info, 
                                                      responseSet=document_item_list
                                                    )
    
    document_list = models.DocumentList(documentList = document_list_struct)
    
    ret_val = document_list
    
    return ret_val

#-----------------------------------------------------------------------------
def metadata_get_videos(source_type=None, pep_code=None, limit=opasConfig.DEFAULT_LIMIT_FOR_METADATA_LISTS, offset=0):
    """
    Fill out a sourceInfoDBList which can be used for a getSources return, but return individual 
      videos, as is done for books.  This provides more information than the 
      original API which returned video "journals" names.  
      
    """
    
    if pep_code != None:
        query = "art_pepsourcetype:video* AND art_pepsrccode:{}".format(pep_code)
    else:
        query = "art_pepsourcetype:video*"
    try:
        srcList = solr_docs.query(q = query,  
                                  fields = "art_id, art_issn, art_pepsrccode, art_authors, title, \
                                            art_pepsourcetitlefull, art_pepsourcetitleabbr, art_vol, \
                                            art_year, art_citeas_xml, art_lang, art_pgrg",
                                  sort = "art_citeas_xml",
                                  sort_order = "asc",
                                  rows=limit, start=offset
                                 )
    except Exception as e:
        print ("metadataGetVideos Error: {}".format(e))

    source_info_dblist = []
    count = len(srcList.results)
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
            
        source_info_record["src_code"] = result.get("art_pepsrccode")
        source_info_record["ISSN"] = result.get("art_issn")
        source_info_record["documentID"] = result.get("art_id")
        try:
            source_info_record["title"] = result.get("title")[0]
        except:
            source_info_record["title"] = ""
            
        source_info_record["art_citeas"] = result.get("art_citeas_xml")
        source_info_record["pub_year"] = result.get("art_year")
        source_info_record["bib_abbrev"] = result.get("art_year")
        try:
            source_info_record["language"] = result.get("art_lang")[0]
        except:
            source_info_record["language"] = "EN"

        print ("metadataGetVideos: ", source_info_record)
        source_info_dblist.append(source_info_record)

    return total_count, source_info_dblist

#-----------------------------------------------------------------------------
def metadata_get_source_by_type(source_type=None, pep_code=None, limit=opasConfig.DEFAULT_LIMIT_FOR_METADATA_LISTS, offset=0):
    """
    Rather than get this from Solr, where there's no 1:1 records about this, we will get this from the sourceInfoDB instance.
    
    No attempt here to map to the correct structure, just checking what field/data items we have in sourceInfoDB.
    
    >>> returnData = metadata_get_source_by_type("journal")
    Number found: 75

    >>> returnData = metadata_get_source_by_type("book")
    Number found: 6

    >>> metadata_get_source_by_type("journals", limit=5, offset=0)
    Number found: 75
    
    >>> metadata_get_source_by_type("journals", limit=5, offset=6)
    Number found: 75
    
    """
    ret_val = []
    source_info_dblist = []
    ocd = opasCentralDBLib.opasCentralDB()
    # standardize Source type, allow plural, different cases, but code below this part accepts only those three.
    source_type = source_type.lower()
    if source_type not in ["journal", "book"]:
        if re.match("videos.*", source_type, re.IGNORECASE):
            source_type = "videos"
        elif re.match("video", source_type, re.IGNORECASE):
            source_type = "videostream"
        elif re.match("boo.*", source_type, re.IGNORECASE):
            source_type = "book"
        else: # default
            source_type = "journal"
   
    # This is not part of the original API, it brings back individual videos rather than the videostreams
    # but here in case we need it.  In that case, your source must be videos.*, like videostream, in order
    # to load individual videos rather than the video journals
    if source_type == "videos":        
        total_count, source_info_dblist = metadata_get_videos(source_type, pep_code, limit, offset)
        count = len(source_info_dblist)
    else: # get from mySQL
        try:
            if pep_code != "*":
                total_count, sourceData = ocd.get_sources(source_type = source_type, source=pep_code, limit=limit, offset=offset)
            else:
                total_count, sourceData = ocd.get_sources(source_type = source_type, limit=limit, offset=offset)
                
            for sourceInfoDict in sourceData:
                if sourceInfoDict["src_type"] == source_type:
                    # match
                    source_info_dblist.append(sourceInfoDict)
            if limit < total_count:
                count = limit
            else:
                count = total_count
            print ("MetadataGetSourceByType: Number found: %s" % count)
        except Exception as e:
            errMsg = "MetadataGetSourceByType: Error getting source information.  {}".format(e)
            count = 0
            print (errMsg)

    response_info = models.ResponseInfo( count = count,
                                         fullCount = total_count,
                                         fullCountComplete = count == total_count,
                                         limit = limit,
                                         offset = offset,
                                         listLabel = "{} List".format(source_type),
                                         listType = "sourceinfolist",
                                         scopeQuery = "*",
                                         timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                       )

    source_info_listitems = []
    counter = 0
    for source in source_info_dblist:
        counter += 1
        if counter < offset:
            continue
        if counter > limit:
            break
        try:
            title = source.get("title")
            authors = source.get("author")
            pub_year = source.get("pub_year")
            publisher = source.get("publisher")
            bookCode = None
            if source_type == "book":
                bookCode = source.get("base_code")
                m = re.match("(?P<code>[a-z]+)(?P<num>[0-9]+)", bookCode, re.IGNORECASE)
                if m is not None:
                    code = m.group("code")
                    num = m.group("num")
                    bookCode = code + "." + num
                
                art_citeas = u"""<p class="citeas"><span class="authors">%s</span> (<span class="year">%s</span>) <span class="title">%s</span>. <span class="publisher">%s</span>.""" \
                    %                   (authors,
                                         source.get("pub_year"),
                                         title,
                                         publisher
                                        )
            elif source_type == "video":
                art_citeas = source.get("art_citeas")
            else:
                art_citeas = title # journals just should show display title


            try:
                item = models.SourceInfoListItem( sourceType = source_type,
                                                  PEPCode = source.get("src_code"),
                                                  authors = authors,
                                                  pub_year = pub_year,
                                                  documentID = source.get("art_id"),
                                                  displayTitle = art_citeas,
                                                  title = title,
                                                  srcTitle = title,  # v1 Deprecated for future
                                                  bookCode = bookCode,
                                                  abbrev = source.get("bib_abbrev"),
                                                  bannerURL = f"http://{BASEURL}/{opasConfig.IMAGES}/banner{source.get('src_code')}.logo.gif",
                                                  language = source.get("language"),
                                                  ISSN = source.get("ISSN"),
                                                  yearFirst = source.get("start_year"),
                                                  yearLast = source.get("end_year"),
                                                  embargoYears = source.get("embargo_yrs")
                                                ) 
                print ("metadataGetSourceByType SourceInfoListItem: ", item)
            except ValidationError as e:
                print ("metadataGetSourceByType SourceInfoListItem Validation Error:")
                print(e.json())        

        except Exception as e:
                print("metadataGetSourceByType: ", e)        
            

        source_info_listitems.append(item)
        
    try:
        source_info_struct = models.SourceInfoStruct( responseInfo = response_info, 
                                                      responseSet = source_info_listitems
                                                     )
    except ValidationError as e:
        print ("models.SourceInfoStruct Validation Error:")
        print(e.json())        
    
    try:
        source_info_list = models.SourceInfoList(sourceInfo = source_info_struct)
    except ValidationError as e:
        print ("SourceInfoList Validation Error:")
        print(e.json())        
    
    ret_val = source_info_list

    return ret_val

#-----------------------------------------------------------------------------
def metadata_get_source_by_code(pep_code=None, limit=opasConfig.DEFAULT_LIMIT_FOR_SOLR_RETURNS, offset=0):
    """
    Rather than get this from Solr, where there's no 1:1 records about this, we will get this from the sourceInfoDB instance.
    
    No attempt here to map to the correct structure, just checking what field/data items we have in sourceInfoDB.
    
    The sourceType is listed as part of the endpoint path, but I wonder if we should really do this 
    since it isn't needed, the pepCodes are unique.
    
    curl -X GET "http://stage.pep.gvpi.net/api/v1/Metadata/Journals/AJP/" -H "accept: application/json"
    
    >>> metadata_get_source_by_code("APA")["wall"]
    3
    >>> metadata_get_source_by_code()
    
    """
    ret_val = []
    ocd = opasCentralDBLib.opasCentralDB()
    
    # would need to add URL for the banner
    if pep_code is not None:
        total_count, source_info_dblist = ocd.get_sources(pep_code)    #sourceDB.sourceData[pepCode]
        #sourceType = sourceInfoDBList.get("src_type", None)
    else:
        total_count, source_info_dblist = ocd.get_sources(pep_code)    #sourceDB.sourceData
        #sourceType = "All"
            
    count = len(source_info_dblist)
    print ("metadataGetSourceByCode: Number found: %s" % count)

    response_info = models.ResponseInfo( count = count,
                                         fullCount = total_count,
                                         limit = limit,
                                         offset = offset,
                                         #listLabel = "{} List".format(sourceType),
                                         listType = "sourceinfolist",
                                         scopeQuery = "*",
                                         fullCountComplete = True,
                                         timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                       )

    source_info_list_items = []
    counter = 0
    for source in source_info_dblist:
        counter += 1
        if counter < offset:
            continue
        if counter > limit:
            break
        try:
            item = models.SourceInfoListItem( ISSN = source.get("ISSN"),
                                              PEPCode = source.get("src_code"),
                                              abbrev = source.get("bib_abbrev"),
                                              bannerURL = f"http://{BASEURL}/{opasConfig.IMAGES}/banner{source.get('src_code')}.logo.gif",
                                              displayTitle = source.get("title"),
                                              language = source.get("language"),
                                              yearFirst = source.get("start_year"),
                                              yearLast = source.get("end_year"),
                                              sourceType = source.get("src_type"),
                                              title = source.get("title")
                                            ) 
        except ValidationError as e:
            print (80*"-")
            print ("metadataGetSourceByCode: SourceInfoListItem Validation Error:")
            print(e.json())        
            print (80*"-")

        source_info_list_items.append(item)
        
    try:
        source_info_struct = models.SourceInfoStruct( responseInfo = response_info, 
                                                      responseSet = source_info_list_items
                                                    )
    except ValidationError as e:
        print (80*"-")
        print ("metadataGetSourceByCode: SourceInfoStruct Validation Error:")
        print(e.json())        
        print (80*"-")
    
    try:
        source_info_list = models.SourceInfoList(sourceInfo = source_info_struct)
    
    except ValidationError as e:
        print (80*"-")
        print ("metadataGetSourceByCode: SourceInfoList Validation Error:")
        print(e.json())        
        print (80*"-")
    
    ret_val = source_info_list
    return ret_val

#-----------------------------------------------------------------------------
def authors_get_author_info(author_name_partial, limit=opasConfig.DEFAULT_LIMIT_FOR_SOLR_RETURNS, offset=0, author_order="index"):
    """
    Returns a list of matching names (per authors last name), and the number of articles in PEP found by that author.
    
    Args:
        authorNamePartial (str): String prefix of author names to return.
        limit (int, optional): Paging mechanism, return is limited to this number of items.
        offset (int, optional): Paging mechanism, start with this item in limited return set, 0 is first item.
        authorOrder (str, optional): Return the list in this order, per Solr documentation.  Defaults to "index", which is the Solr determined indexing order.

    Returns:
        models.DocumentList: Pydantic structure (dict) for DocumentList.  See models.py

    Docstring Tests:    
        >>> resp = authors_get_author_info("Tuck")
        Number found: 72
        >>> resp = authors_get_author_info("Fonag")
        Number found: 134
        >>> resp = authors_get_author_info("Levinson, Nadine A.")
        Number found: 8   
    """
    ret_val = {}
    method = 2
    
    if method == 1:
        query = "art_author_id:/%s.*/" % (author_name_partial)
        results = solr_authors.query( q=query,
                                      fields="authors, art_author_id",
                                      facet_field="art_author_id",
                                      facet="on",
                                      facet_sort="index",
                                      facet_prefix="%s" % author_name_partial,
                                      facet_limit=limit,
                                      facet_offset=offset,
                                      rows=0
                                    )       

    if method == 2:
        # should be faster way, but about the same measuring tuck (method1) vs tuck.* (method2) both about 2 query time.  However, allowing regex here.
        if "*" in author_name_partial or "?" in author_name_partial or "." in author_name_partial:
            results = solr_author_term_search( terms_fl="art_author_id",
                                               terms_limit=limit,  # this causes many regex expressions to fail
                                               terms_regex=author_name_partial + ".*",
                                               terms_sort=author_order  # index or count
                                              )           
        else:
            results = solr_author_term_search( terms_fl="art_author_id",
                                               terms_prefix=author_name_partial,
                                               terms_sort=author_order,  # index or count
                                               terms_limit=limit
                                             )

    
    response_info = models.ResponseInfo( limit=limit,
                                         offset=offset,
                                         listType="authorindex",
                                         scopeQuery="Terms: %s" % author_name_partial,
                                         solrParams=results._params,
                                         timeStamp=datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)
                                       )
    
    author_index_items = []
    if method == 1:
        for key, value in results.facet_counts["facet_fields"]["art_author_id"].items():
            if value > 0:
                #ret_val[key] = value
    
                item = models.AuthorIndexItem(authorID = key, 
                                              publicationsURL = "/v1/Authors/Publications/{}/".format(key),
                                              publicationsCount = value,
                                             ) 
                author_index_items.append(item)
                #debug status
                print ("authorsGetAuthorInfo", item)

    if method == 2:  # faster way
        for key, value in results.terms["art_author_id"].items():
            if value > 0:
                item = models.AuthorIndexItem(authorID = key, 
                                              publicationsURL = "/v1/Authors/Publications/{}/".format(key),
                                              publicationsCount = value,
                                             ) 
                author_index_items.append(item)
                #debug status
                print ("authorsGetAuthorInfo", item)
       
    response_info.count = len(author_index_items)
    response_info.fullCountComplete = limit >= response_info.count
        
    author_index_struct = models.AuthorIndexStruct( responseInfo = response_info, 
                                                    responseSet = author_index_items
                                                  )
    
    author_index = models.AuthorIndex(authorIndex = author_index_struct)
    
    ret_val = author_index
    return ret_val

#-----------------------------------------------------------------------------
def authors_get_author_publications(authorNamePartial, limit=opasConfig.DEFAULT_LIMIT_FOR_SOLR_RETURNS, offset=0):
    """
    Returns a list of publications (per authors partial name), and the number of articles by that author.
    
    
    
    >>> resp = authors_get_author_publications("Tuck")
    Number found: 0
    Query didn't work - art_author_id:/Tuck/
    trying again - art_author_id:/Tuck[ ]?.*/
    Number found: 72
    >>> resp = authors_get_author_publications("Fonag")
    Number found: 0
    Query didn't work - art_author_id:/Fonag/
    trying again - art_author_id:/Fonag[ ]?.*/
    Number found: 134    
    >>> resp = authors_get_author_publications("Levinson, Nadine A.")
    Number found: 8
    """
    ret_val = {}
    query = "art_author_id:/{}/".format(authorNamePartial)
    # wildcard in case nothing found for #1
    results = solr_authors.query( q = "{}".format(query),   
                                  fields = "art_author_id, art_year_int, art_id, art_citeas_xml",
                                  sort="art_author_id, art_year_int", sort_order="asc",
                                  rows=limit, start=offset
                                )

    print ("authorsGetAuthorPublications: Number found: %s" % results._numFound)
    
    if results._numFound == 0:
        print ("authorsGetAuthorPublications Query didn't work - {}".format(query))
        query = "art_author_id:/{}[ ]?.*/".format(authorNamePartial)
        print ("authorsGetAuthorPublications trying again - {}".format(query))
        results = solr_authors.query( q = "{}".format(query),  
                                      fields = "art_author_id, art_year_int, art_id, art_citeas_xml",
                                      sort="art_author_id, art_year_int", sort_order="asc",
                                      rows=limit, start=offset
                                    )

        print ("authorsGetAuthorPublications Number found: %s" % results._numFound)
        if results._numFound == 0:
            query = "art_author_id:/(.*[ ])?{}[ ]?.*/".format(authorNamePartial)
            print ("trying again - {}".format(query))
            results = solr_authors.query( q = "{}".format(query),  
                                          fields = "art_author_id, art_year_int, art_id, art_citeas_xml",
                                          sort="art_author_id, art_year_int", sort_order="asc",
                                          rows=limit, start=offset
                                        )
    
    response_info = models.ResponseInfo( count = len(results.results),
                                         fullCount = results._numFound,
                                         limit = limit,
                                         offset = offset,
                                         listType="authorpublist",
                                         scopeQuery=query,
                                         solrParams = results._params,
                                         fullCountComplete = limit >= results._numFound,
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
                                         documentURL = documentURL + result.get("art_id", None),
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
def get_excerpt_from_abs_sum_or_doc(xml_abstract, xml_summary, xml_document):
   
    ret_val = None
    # see if there's an abstract
    ret_val = force_string_return_from_various_return_types(xml_abstract)
    if ret_val is None:
        # try the summary
        ret_val = force_string_return_from_various_return_types(xml_summary)
        if ret_val is None:
            # get excerpt from the document
            if xml_document is None:
                # we fail.  Return None
                logger.warning("No excerpt can be found or generated.")
            else:
                # extract the first 10 paras
                ret_val = force_string_return_from_various_return_types(xml_document)
                ret_val = opasxmllib.remove_encoding_string(ret_val)
                # deal with potentially broken XML excerpts
                parser = lxml.etree.XMLParser(encoding='utf-8', recover=True)                
                #root = etree.parse(StringIO(ret_val), parser)
                root = etree.fromstring(ret_val, parser)
                body = root.xpath("//*[self::h1 or self::p or self::p2 or self::pb]")
                ret_val = ""
                count = 0
                for elem in body:
                    if elem.tag == "pb" or count > 10:
                        # we're done.
                        ret_val = "%s%s%s" % ("<abs><unit type='excerpt'>", ret_val, "</unit></abs>")
                        break
                    else:
                        ret_val  += etree.tostring(elem, encoding='utf8').decode('utf8')

    return ret_val
    
#-----------------------------------------------------------------------------
def documents_get_abstracts(document_id, ret_format="TEXTONLY", authenticated=None, limit=opasConfig.DEFAULT_LIMIT_FOR_SOLR_RETURNS, offset=0):
    """
    Returns an abstract or summary for the specified document
    If part of a documentID is supplied, multiple abstracts will be returned.
    
    The endpoint reminds me that we should be using documentID instead of "art" for article perhaps.
      Not thrilled about the prospect of changing it, but probably the right thing to do.
      
    >>> abstracts = documents_get_abstracts("IJP.075")
    10 document matches for getAbstracts
    >>> abstracts = documents_get_abstracts("AIM.038.0279A")  # no abstract on this one
    1 document matches for getAbstracts
    >>> abstracts = documents_get_abstracts("AIM.040.0311A")
    2 document matches for getAbstracts
      
    """
    ret_val = None
    results = solr_docs.query(q = "art_id:%s*" % (document_id),  
                                fields = "art_id, art_pepsourcetitlefull, art_vol, art_year, art_citeas_xml, art_pgrg, art_title_xml, art_authors, abstracts_xml, summaries_xml, text_xml",
                                sort="art_year, art_pgrg", sort_order="asc",
                                rows=limit, start=offset
                             )
    
    matches = len(results.results)
    cwd = os.getcwd()    
    print ("GetAbstract: Current Directory {}".format(cwd))
    print ("%s document matches for getAbstracts" % matches)
    
    response_info = models.ResponseInfo( count = len(results.results),
                                         fullCount = results._numFound,
                                         limit = limit,
                                         offset = offset,
                                         listType="documentlist",
                                         fullCountComplete = limit >= results._numFound,
                                         timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                       )
    
    document_item_list = []
    for result in results:
        if matches > 0:
            try:
                xml_abstract = result["abstracts_xml"]
            except KeyError as e:
                xml_abstract = None
                logger.info("No abstract for document ID: %s" % document_id)
        
            try:
                xml_summary = result["summaries_xml"]
            except KeyError as e:
                xml_summary = None
                logger.info("No summary for document ID: %s" % document_id)
        
            try:
                xml_document = result["text_xml"]
            except KeyError as e:
                xml_document = None
                logger.error("No content matched document ID for: %s" % document_id)

            author_ids = result.get("art_authors", None)
            if author_ids is None:
                author_mast = None
            else:
                author_mast = opasgenlib.deriveAuthorMast(author_ids)

            pgrg = result.get("art_pgrg", None)
            pg_start, pg_end = opasgenlib.pgrg_splitter(pgrg)
            
            source_title = result.get("art_pepsourcetitlefull", None)
            title = result.get("art_title_xml", "")  # name is misleading, it's not xml.
            art_year = result.get("art_year", None)
            art_vol = result.get("art_vol", None)

            citeas = result.get("art_citeas_xml", None)
            citeas = force_string_return_from_various_return_types(citeas)

            abstract = get_excerpt_from_abs_sum_or_doc(xml_abstract, xml_summary, xml_document)
            if abstract == "[]":
                abstract = None
            elif ret_format == "TEXTONLY":
                abstract = opasxmllib.xml_elem_or_str_to_text(abstract)
            elif ret_format == "HTML":
                abstractHTML = opasxmllib.xml_str_to_html(abstract)
                abstract = extract_html_fragment(abstractHTML, "//div[@id='abs']")

            abstract = opasxmllib.add_headings_to_abstract_html(abstract=abstract, 
                                                            source_title=source_title,
                                                            pub_year=art_year,
                                                            vol=art_vol, 
                                                            pgrg=pgrg, 
                                                            citeas=citeas, 
                                                            title=title,
                                                            author_mast=author_mast )

            item = models.DocumentListItem(year = art_year,
                                    vol = art_vol,
                                    sourceTitle = source_title,
                                    pgRg = pgrg,
                                    pgStart = pg_start,
                                    pgEnd = pg_end,
                                    authorMast = author_mast,
                                    documentID = result.get("art_id", None),
                                    documentRefHTML = citeas,
                                    documentRef = opasxmllib.xml_elem_or_str_to_text(citeas, default_return=""),
                                    accessLimited = authenticated,
                                    abstract = abstract,
                                    score = result.get("score", None)
                                    )
        
            #print (item)
            document_item_list.append(item)

    response_info.count = len(document_item_list)
    
    document_list_struct = models.DocumentListStruct( responseInfo = response_info, 
                                                      responseSet=document_item_list
                                                      )
    
    documents = models.Documents(documents = document_list_struct)
        
    ret_val = documents
            
                
    return ret_val


#-----------------------------------------------------------------------------
def documents_get_document(document_id, solr_query_params=None, ret_format="XML", authenticated=True, limit=opasConfig.DEFAULT_LIMIT_FOR_DOCUMENT_RETURNS, offset=0):
    """
   For non-authenticated users, this endpoint returns only Document summary information (summary/abstract)
   For authenticated users, it returns with the document itself
   
    >> resp = documentsGetDocument("AIM.038.0279A", retFormat="html") 
    
    >> resp = documentsGetDocument("AIM.038.0279A") 
    
    >> resp = documentsGetDocument("AIM.040.0311A")
    

    """
    ret_val = {}
    
    if not authenticated:
        #if user is not authenticated, effectively do endpoint for getDocumentAbstracts
        print ("documentsGetDocument: User not authenticated...fetching abstracts instead")
        ret_val = document_list_struct = documents_get_abstracts(document_id, authenticated=authenticated, limit=1)
        return ret_val

    if solr_query_params is not None:
        # repeat the query that the user had done when retrieving the document
        query = "art_id:{} && {}".format(document_id, solr_query_params.searchQ)
        document_list = search_text(query, 
                                    filter_query = solr_query_params.filterQ,
                                    full_text_requested=True,
                                    full_text_format_requested = ret_format,
                                    authenticated=authenticated,
                                    query_debug = False,
                                    dis_max = solr_query_params.solrMax,
                                    limit=limit, 
                                    offset=offset
                                  )
    
    if document_list == None or document_list.documentList.responseInfo.count == 0:
        #sometimes the query is still sent back, even though the document was an independent selection.  So treat it as a simple doc fetch
        
        query = "art_id:{}".format(document_id)
        #summaryFields = "art_id, art_vol, art_year, art_citeas_xml, art_pgrg, art_title, art_author_id, abstracts_xml, summaries_xml, text_xml"
       
        document_list = search_text(query, 
                                    full_text_requested=True,
                                    full_text_format_requested = ret_format,
                                    authenticated=authenticated,
                                    query_debug = False,
                                    limit=limit, 
                                    offset=offset
                                    )

    try:
        matches = document_list.documentList.responseInfo.count
        full_count = document_list.documentList.responseInfo.fullCount
        full_count_complete = document_list.documentList.responseInfo.fullCountComplete
        document_list_item = document_list.documentList.responseSet[0]
        print ("documentsGetDocument %s document matches" % matches)
    except Exception as e:
        print ("No matches or error: {}").format(e)
    else:
        response_info = models.ResponseInfo( count = matches,
                                             fullCount = full_count,
                                             limit = limit,
                                             offset = offset,
                                             listType="documentlist",
                                             fullCountComplete = full_count_complete,
                                             timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)
                                           )
        
        if matches >= 1:       
            document_list_struct = models.DocumentListStruct( responseInfo = response_info, 
                                                              responseSet = [document_list_item]
                                                            )
                
            documents = models.Documents(documents = document_list_struct)
                    
            ret_val = documents
    
    return ret_val

#-----------------------------------------------------------------------------
def documents_get_glossary_entry(term_id,
                                 solrQueryParams=None,
                                 retFormat="XML",
                                 authenticated=True,
                                 limit=opasConfig.DEFAULT_LIMIT_FOR_DOCUMENT_RETURNS, offset=0):
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
                    else:
                        document = document
                    item = models.DocumentListItem(PEPCode = "ZBK", 
                                                   documentID = result.get("art_id", None), 
                                                   title = result.get("term_source", None),
                                                   abstract = None,
                                                   document = document,
                                                   score = result.get("score", None)
                                            )
                except ValidationError as e:
                    logger.error(e.json())  
                    print (e.json())
                else:
                    document_item_list.append(item)
                    count = len(document_item_list)

        except IndexError as e:
            logger.warning("No matching glossary entry for %s.  Error: %s" % (term_id, e))
        except KeyError as e:
            logger.warning("No content or abstract found for %s.  Error: %s" % (term_id, e))
        else:
            response_info = models.ResponseInfo( count = count,
                                                 fullCount = count,
                                                 limit = limit,
                                                 offset = offset,
                                                 listType="documentlist",
                                                 fullCountComplete = True,
                                                 timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                               )
            
            document_list_struct = models.DocumentListStruct( responseInfo = response_info, 
                                                              responseSet = document_item_list
                                                            )
                
            documents = models.Documents(documents = document_list_struct)
                        
            ret_val = documents
        
        return ret_val

#-----------------------------------------------------------------------------
def prep_document_download(document_id, ret_format="HTML", authenticated=True, base_filename="opasDoc"):
    """
   For non-authenticated users, this endpoint returns only Document summary information (summary/abstract)
   For authenticated users, it returns with the document itself
   
    >>> a = prep_document_download("IJP.051.0175A", ret_format="html") 
    
    >> a = prep_document_download("IJP.051.0175A", ret_format="epub") 
    

    """
    def add_epub_elements(str):
        # for now, just return
        return str
        
    ret_val = {}
    
    if not authenticated:
        #if user is not authenticated, effectively do endpoint for getDocumentAbstracts
        documents_get_abstracts(document_id, limit=1)
    else:
        results = solr_docs.query(q = "art_id:%s" % (document_id),  
                                    fields = "art_id, art_citeas_xml, text_xml"
                                 )
        try:
            ret_val = results.results[0]["text_xml"]
        except IndexError as e:
            logger.warning("No matching document for %s.  Error: %s" % (document_id, e))
        except KeyError as e:
            logger.warning("No content or abstract found for %s.  Error: %s" % (document_id, e))
        else:
            try:    
                if isinstance(ret_val, list):
                    ret_val = ret_val[0]
            except Exception as e:
                logger.warning("Empty return: %s" % e)
            else:
                try:    
                    if ret_format.lower() == "html":
                        ret_val = opasxmllib.remove_encoding_string(ret_val)
                        filename = convert_xml_to_html_file(ret_val, output_filename=document_id + ".html")  # returns filename
                        ret_val = filename
                    elif ret_format.lower() == "epub":
                        ret_val = opasxmllib.remove_encoding_string(ret_val)
                        html_string = opasxmllib.xml_str_to_html(ret_val)
                        html_string = add_epub_elements(html_string)
                        filename = opasxmllib.html_to_epub(html_string, document_id, document_id)
                        ret_val = filename
                        
                except Exception as e:
                    logger.warning("Can't convert data: %s" % e)
        
    return ret_val

#-----------------------------------------------------------------------------
def convert_xml_to_html_file(xmltext_str, xslt_file=r"./styles/pepkbd3-html.xslt", output_filename=None):
    if output_filename is None:
        basename = "opasDoc"
        suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        filename_base = "_".join([basename, suffix]) # e.g. 'mylogfile_120508_171442'        
        output_filename = filename_base + ".html"

    htmlString = opasxmllib.xml_str_to_html(xmltext_str, xslt_file=xslt_file)
    fo = open(output_filename, "w")
    fo.write(str(htmlString))
    fo.close()
    
    return output_filename

#-----------------------------------------------------------------------------
def get_image_binary(image_id):
    """
    Return a binary object of the image, e.g.,
   
    >>> get_image_binary("NOTEXISTS.032.0329A.F0003g")

    >> get_image_binary("AIM.036.0275A.FIG001")

    >> get_image_binary("JCPTX.032.0329A.F0003g")
    
    Note: the current server requires the extension, but it should not.  The server should check
    for the file per the following extension hierarchy: .jpg then .gif then .tif
    
    However, if the extension is supplied, that should be accepted.

    The current API implements this:
    
    curl -X GET "http://stage.pep.gvpi.net/api/v1/Documents/Downloads/Images/aim.036.0275a.fig001.jpg" -H "accept: image/jpeg" -H "Authorization: Basic cC5lLnAuYS5OZWlsUlNoYXBpcm86amFDayFsZWdhcmQhNQ=="
    
    and returns a binary object.  
        
    """
    def getImageFilename(image_id):
        image_source_path = "X:\_PEPA1\g"
        ext = os.path.splitext(image_source_path)[-1].lower()
        if ext in (".jpg", ".tif", ".gif"):
            image_filename = os.path.join(image_source_path, image_id)
            exists = os.path.isfile(image_filename)
            if not exists:
                image_filename = None
        else:
            image_filename = os.path.join(image_source_path, image_id + ".jpg")
            exists = os.path.isfile(image_filename)
            if not exists:
                image_filename = os.path.join(image_source_path, image_id + ".gif")
                exists = os.path.isfile(image_filename)
                if not exists:
                    image_filename = os.path.join(image_source_path, image_id + ".tif")
                    exists = os.path.isfile(image_filename)
                    if not exists:
                        image_filename = None

        return image_filename
    
    # these won't be in the Solr database, needs to be brought back by a file
    # the file ID should match a file name
    ret_val = None
    image_filename = getImageFilename(image_id)
    if image_filename is not None:
        try:
            f = open(image_filename, "rb")
            image_bytes = f.read()
            f.close()    
        except OSError as e:
            print ("getImageBinary: File Open Error: %s", e)
        except Exception as e:
            print ("getImageBinary: Error: %s", e)
        else:
            ret_val = image_bytes
    else:
        logger.warning("Image File ID %s not found", image_id)
  
    return ret_val

#-----------------------------------------------------------------------------
def get_kwic_list(marked_up_text, 
                  extra_context_len=opasConfig.DEFAULT_KWIC_CONTENT_LENGTH, 
                  solr_start_hit_tag=opasConfig.HITMARKERSTART, # supply whatever the start marker that solr was told to use
                  solr_end_hit_tag=opasConfig.HITMARKEREND,     # supply whatever the end marker that solr was told to use
                  output_start_hit_tag_marker=opasConfig.HITMARKERSTART_OUTPUTHTML, # the default output marker, in HTML
                  output_end_hit_tag_marker=opasConfig.HITMARKEREND_OUTPUTHTML,
                  limit=opasConfig.DEFAULT_MAX_KWIC_RETURNS):
    """
    Find all nonoverlapping matches, using Solr's return.  Limit the number.
    """
    
    ret_val = []
    emMarks = re.compile("(.{0,%s}%s.*%s.{0,%s})" % (extra_context_len, solr_start_hit_tag, solr_end_hit_tag, extra_context_len))
    markedUp = re.compile(".*(%s.*%s).*" % (solr_start_hit_tag, solr_end_hit_tag))
    marked_up_text = opasxmllib.xml_string_to_text(marked_up_text) # remove markup except match tags which shouldn't be XML

    matchTextPattern = "({{.*?}})"
    patCompiled = re.compile(matchTextPattern)
    wordList = patCompiled.split(marked_up_text) # split all the words
    listOfMatches = []
    index = 0
    count = 0
    #TODO may have problems with adjacent matches!
    skipNext = False
    for n in wordList:
        if patCompiled.match(n) and skipNext == False:
            # we have a match
            try:
                textBefore = wordList[index-1]
                textBeforeWords = textBefore.split(" ")[-extra_context_len:]
                textBeforePhrase = " ".join(textBeforeWords)
            except:
                textBefore = ""
            try:
                textAfter = wordList[index+1]
                textAfterWords = textAfter.split(" ")[:extra_context_len]
                textAfterPhrase = " ".join(textAfterWords)
                if patCompiled.search(textAfterPhrase):
                    skipNext = True
            except:
                textAfter = ""

            # change the tags the user told Solr to use to the final output tags they want
            #   this is done to use non-xml-html hit tags, then convert to that after stripping the other xml-html tags
            match = re.sub(solr_start_hit_tag, output_start_hit_tag_marker, n)
            match = re.sub(solr_end_hit_tag, output_end_hit_tag_marker, match)

            contextPhrase = textBeforePhrase + match + textAfterPhrase

            ret_val.append(contextPhrase)

            try:
                logger.info("getKwicList Match: '...{}...'".format(contextPhrase))
                print ("getKwicListMatch: '...{}...'".format(contextPhrase))
            except Exception as e:
                print ("getKwicList Error printing or logging matches. {}".format(e))
            
            index += 1
            count += 1
            if count >= limit:
                break
        else:
            skipNext = False
            index += 1
        
    matchCount = len(ret_val)
    
    return ret_val    


#-----------------------------------------------------------------------------
def get_kwic_list_old(marked_up_text, extra_context_len=opasConfig.DEFAULT_KWIC_CONTENT_LENGTH, 
                solr_start_hit_tag=opasConfig.HITMARKERSTART, # supply whatever the start marker that solr was told to use
                solr_end_hit_tag=opasConfig.HITMARKEREND,     # supply whatever the end marker that solr was told to use
                output_start_hit_tag_marker=opasConfig.HITMARKERSTART_OUTPUTHTML, # the default output marker, in HTML
                output_end_hit_tag_marker=opasConfig.HITMARKEREND_OUTPUTHTML,
                limit=opasConfig.DEFAULT_MAX_KWIC_RETURNS):
    """
    Find all nonoverlapping matches, using Solr's return.  Limit the number.
    """
    
    ret_val = []
    em_marks = re.compile("(.{0,%s}%s.*%s.{0,%s})" % (extra_context_len, solr_start_hit_tag, solr_end_hit_tag, extra_context_len))
    count = 0
    for n in em_marks.finditer(marked_up_text):
        count += 1
        match = n.group(0)
        try:
            # strip xml
            match = opasxmllib.xml_string_to_text(match)
            # change the tags the user told Solr to use to the final output tags they want
            #   this is done to use non-xml-html hit tags, then convert to that after stripping the other xml-html tags
            match = re.sub(solr_start_hit_tag, output_start_hit_tag_marker, match)
            match = re.sub(solr_end_hit_tag, output_end_hit_tag_marker, match)
        except Exception as e:
            logging.error("Error stripping xml from kwic entry {}".format(e))
               
        ret_val.append(match)
        try:
            logger.info("getKwicList Match: '...{}...'".format(match))
            print ("getKwicListMatch: '...{}...'".format(match))
        except Exception as e:
            print ("getKwicList Error printing or logging matches. {}".format(e))
        if count >= limit:
            break
        
    match_count = len(ret_val)
    
    return ret_val    

#-----------------------------------------------------------------------------
def year_arg_parser(year_arg):
    ret_val = None
    year_query = re.match("[ ]*(?P<option>[\>\^\<\=])?[ ]*(?P<start>[12][0-9]{3,3})?[ ]*(?P<separator>([-]|TO))*[ ]*(?P<end>[12][0-9]{3,3})?[ ]*", year_arg, re.IGNORECASE)            
    if year_query is None:
        logger.warning("Search - StartYear bad argument {}".format(year_arg))
    else:
        option = year_query.group("option")
        start = year_query.group("start")
        end = year_query.group("end")
        separator = year_query.group("separator")
        if start is None and end is None:
            logger.warning("Search - StartYear bad argument {}".format(year_arg))
        else:
            if option == "^":
                # between
                # find endyear by parsing
                if start is None:
                    start = end # they put > in start rather than end.
                elif end is None:
                    end = start # they put < in start rather than end.
                search_clause = "&& art_year_int:[{} TO {}] ".format(start, end)
            elif option == ">":
                # greater
                if start is None:
                    start = end # they put > in start rather than end.
                search_clause = "&& art_year_int:[{} TO {}] ".format(start, "*")
            elif option == "<":
                # less than
                if end is None:
                    end = start # they put < in start rather than end.
                search_clause = "&& art_year_int:[{} TO {}] ".format("*", end)
            else: # on
                if start is not None and end is not None:
                    # they specified a range anyway
                    search_clause = "&& art_year_int:[{} TO {}] ".format(start, end)
                elif start is None and end is not None:
                    # they specified '- endyear' without the start, so less than
                    search_clause = "&& art_year_int:[{} TO {}] ".format("*", end)
                elif start is not None and separator is not None:
                    # they mean greater than
                    search_clause = "&& art_year_int:[{} TO {}] ".format(start, "*")
                else: # they mean on
                    search_clause = "&& art_year_int:{} ".format(year_arg)

            ret_val = search_clause

    return ret_val
                        
#-----------------------------------------------------------------------------
def search_analysis(query_list, 
                    filter_query = None,
                    more_like_these = False,
                    query_analysis = False,
                    dis_max = None,
                    # summaryFields="art_id, art_pepsrccode, art_vol, art_year, art_iss, 
                        # art_iss_title, art_newsecnm, art_pgrg, art_title, art_author_id, art_citeas_xml", 
                    summary_fields="art_id",                    
                    # highlightFields='art_title_xml, abstracts_xml, summaries_xml, art_authors_xml, text_xml', 
                    full_text_requested=False, 
                    user_logged_in=False,
                    limit=opasConfig.DEFAULT_MAX_KWIC_RETURNS
                   ):
    """
    Analyze the search clauses in the query list
	"""
    ret_val = {}
    document_item_list = []
    rowCount = 0
    for n in query_list:
        n = n[3:]
        n = n.strip(" ")
        if n == "" or n is None:
            continue

        results = solr_docs.query(n,
                                 disMax = dis_max,
                                 queryAnalysis = True,
                                 fields = summary_fields,
                                 rows = 1,
                                 start = 0)
    
        termField, termValue = n.split(":")
        if termField == "art_author_xml":
            term = termValue + " ( in author)"
        elif termField == "text_xml":
            term = termValue + " ( in text)"
            
        print ("Analysis: Term %s, matches %s" % (n, results._numFound))
        item = models.DocumentListItem(term = n, 
                                termCount = results._numFound
                                )
        document_item_list.append(item)
        rowCount += 1

    if rowCount > 0:
        numFound = 0
        item = models.DocumentListItem(term = "combined",
                                termCount = numFound
                                )
        document_item_list.append(item)
        rowCount += 1
        print ("Analysis: Term %s, matches %s" % ("combined: ", numFound))

    response_info = models.ResponseInfo(count = rowCount,
                                        fullCount = rowCount,
                                        listType = "srclist",
                                        fullCountComplete = True,
                                        timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)
                                        )
    
    response_info.count = len(document_item_list)
    
    document_list_struct = models.DocumentListStruct( responseInfo = response_info, 
                                                      responseSet = document_item_list
                                                  )
    
    ret_val = models.DocumentList(documentList = document_list_struct)
    
    return ret_val

#================================================================================================================
# SEARCHTEXT
#================================================================================================================
def search_text(query, 
               filter_query = None,
               query_debug = False,
               more_like_these = False,
               full_text_requested = False, 
               full_text_format_requested = "HTML",
               dis_max = None,
               # bring text_xml back in summary fields in case it's missing in highlights! I documented a case where this happens!
               # summary_fields = "art_id, art_pepsrccode, art_vol, art_year, art_iss, art_iss_title, art_newsecnm, art_pgrg, art_title, art_author_id, art_citeas_xml, text_xml", 
               # highlight_fields = 'art_title_xml, abstracts_xml, summaries_xml, art_authors_xml, text_xml', 
               summary_fields = "art_id, art_pepsrccode, art_vol, art_year, art_iss, art_iss_title, art_newsecnm, art_pgrg, abstracts_xml, art_title, art_author_id, art_citeas_xml, text_xml", 
               highlight_fields = 'text_xml', 
               sort_by="score desc",
               authenticated = None, 
               extra_context_len = opasConfig.DEFAULT_KWIC_CONTENT_LENGTH,
               maxKWICReturns = opasConfig.DEFAULT_MAX_KWIC_RETURNS,
               limit=opasConfig.DEFAULT_LIMIT_FOR_SOLR_RETURNS, 
               offset=0):
    """
    Full-text search

    >>> search_text(query="art_title_xml:'ego identity'", limit=10, offset=0, fullTextRequested=False)
    
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
    
    if more_like_these:
        mlt_fl = "text_xml, headings_xml, terms_xml, references_xml"
        mlt = "true"
        mlt_minwl = 8
    else:
        mlt_fl = None
        mlt = "false"
        mlt_minwl = None
    
    if query_debug:
        query_debug = "on"
    else:
        query_debug = "off"
        
    if full_text_requested:
        fragSize = opasConfig.SOLR_HIGHLIGHT_RETURN_FRAGMENT_SIZE 
    else:
        fragSize = extra_context_len

    if filter_query == "*:*":
        # drop it...it seems to produce problems in simple queries that follow a search.
        filter_query = None

    try:
        results = solr_docs.query(query,  
                                 fq = filter_query,
                                 debugQuery = query_debug,
                                 disMax = dis_max,
                                 fields = summary_fields,
                                 hl='true', 
                                 hl_fragsize = fragSize, 
                                 hl_multiterm = 'true',
                                 hl_fl = highlight_fields,
                                 hl_usePhraseHighlighter = 'true',
                                 hl_snippets = maxKWICReturns,
                                 #hl_method="unified",  # these don't work
                                 #hl_encoder="HTML",
                                 mlt = mlt,
                                 mlt_fl = mlt_fl,
                                 mlt_count = 2,
                                 mlt_minwl = mlt_minwl,
                                 rows = limit,
                                 start = offset,
                                 sort=sort_by,
                                 hl_simple_pre = opasConfig.HITMARKERSTART,
                                 hl_simple_post = opasConfig.HITMARKEREND)
    except Exception as e:
        print ("Solr Search Error.  ", e)
        #errCode = resp.status_code = HTTP_400_BAD_REQUEST
        #errReturn = models.ErrorReturn(error = ERR_CREDENTIALS, error_message = ERR_MSG_INSUFFICIENT_INFO)
    else:
        print ("Search Performed: %s" % query)
        print ("Result  Set Size: %s" % results._numFound)
        print ("Return set limit: %s" % limit)
        if results._numFound == 0:
            try:
                # try removing the filter query
                results = solr_docs.query(query,  
                                         debugQuery = query_debug,
                                         disMax = dis_max,
                                         fields = summary_fields,
                                         hl='true', 
                                         hl_fragsize = fragSize, 
                                         hl_multiterm='true',
                                         hl_fl = highlight_fields,
                                         hl_usePhraseHighlighter = 'true',
                                         hl_snippets = maxKWICReturns,
                                         #hl_method="unified",  # these don't work
                                         #hl_encoder="HTML",
                                         mlt = mlt,
                                         mlt_fl = mlt_fl,
                                         mlt_count = 2,
                                         mlt_minwl = mlt_minwl,
                                         rows = limit,
                                         start = offset,
                                         sort=sort_by,
                                         hl_simple_pre = opasConfig.HITMARKERSTART,
                                         hl_simple_post = opasConfig.HITMARKEREND)
            except Exception as e:
                print ("Solr Search Error.  ", e)
                #errCode = resp.status_code = HTTP_400_BAD_REQUEST
                #errReturn = models.ErrorReturn(error = ERR_CREDENTIALS, error_message = ERR_MSG_INSUFFICIENT_INFO)
            else:
                print ("Research Performed: %s" % query)
                print ("New Result Set Size: %s" % results._numFound)
                print ("Return set limit: %s" % limit)
    
        responseInfo = models.ResponseInfo(
                         count = len(results.results),
                         fullCount = results._numFound,
                         totalMatchCount = results._numFound,
                         limit = limit,
                         offset = offset,
                         listType="documentlist",
                         scopeQuery=query,
                         fullCountComplete = limit >= results._numFound,
                         solrParams = results._params,
                         timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                       )
    
    
        documentItemList = []
        rowCount = 0
        rowOffset = 0
        # if we're not authenticated, then turn off the full-text request and behave as if we didn't try
        if not authenticated:
            if full_text_requested:
                logger.warning("Fulltext requested--by API--but not authenticated.")
    
            full_text_requested = False
            
        for result in results.results:
            authorIDs = result.get("art_author_id", None)
            if authorIDs is None:
                authorMast = None
            else:
                authorMast = opasgenlib.deriveAuthorMast(authorIDs)
    
            pgRg = result.get("art_pgrg", None)
            if pgRg is not None:
                pgStart, pgEnd = opasgenlib.pgrg_splitter(pgRg)
                
            documentID = result.get("art_id", None)        
            text_xml = results.highlighting[documentID].get("text_xml", None)
            # no kwic list when full-text is requested.
            if text_xml is not None and not full_text_requested:
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
                text_xml = None
                #print ("Document Length: {}; Matches to show: {}".format(len(textXml), len(kwicList)))
            else: # either fulltext requested, or no document
                kwic_list = []
                kwic = ""  # this has to be "" for PEP-Easy, or it hits an object error.  
            
            if full_text_requested:
                fullText = result.get("text_xml", None)
                text_xml = force_string_return_from_various_return_types(text_xml)
                if text_xml is None:  # no highlights, so get it from the main area
                    try:
                        text_xml = fullText
                    except:
                        text_xml = None
 
                elif len(fullText) > len(text_xml):
                    print ("Warning: text with highlighting is smaller than full-text area.  Returning without hit highlighting.")
                    text_xml = fullText
                    
                if full_text_format_requested == "HTML":
                    if text_xml is not None:
                        text_xml = opasxmllib.xml_str_to_html(text_xml,
                                                                 xslt_file=r"./styles/pepkbd3-html.xslt")
    
            if full_text_requested and not authenticated: # don't do this when textXml is a fragment from kwiclist!
                try:
                    abstracts_xml = results.highlighting[documentID].get("abstracts_xml", None)
                    abstracts_xml  = force_string_return_from_various_return_types(abstracts_xml )
 
                    summaries_xml = results.highlighting[documentID].get("abstracts_xml", None)
                    summaries_xml  = force_string_return_from_various_return_types(summaries_xml)
 
                    text_xml = get_excerpt_from_abs_sum_or_doc(xml_abstract=abstracts_xml,
                                                               xml_summary=summaries_xml,
                                                               xml_document=text_xml)
                except:
                    text_xml = None
    
            citeAs = result.get("art_citeas_xml", None)
            citeAs = force_string_return_from_various_return_types(citeAs)
            
            if more_like_these:
                similarDocs = results.moreLikeThis[documentID]
                similarMaxScore = results.moreLikeThis[documentID].maxScore
                similarNumFound = results.moreLikeThis[documentID].numFound
            else:
                similarDocs = None
                similarMaxScore = None
                similarNumFound = None
            
            try:
                item = models.DocumentListItem(PEPCode = result.get("art_pepsrccode", None), 
                                        year = result.get("art_year", None),
                                        vol = result.get("art_vol", None),
                                        pgRg = pgRg,
                                        pgStart = pgStart,
                                        pgEnd = pgEnd,
                                        authorMast = authorMast,
                                        documentID = documentID,
                                        documentRefHTML = citeAs,
                                        documentRef = opasxmllib.xml_elem_or_str_to_text(citeAs, default_return=""),
                                        kwic = kwic,
                                        kwicList = kwic_list,
                                        title = result.get("art_title", None),
                                        abstract = force_string_return_from_various_return_types(result.get("abstracts_xml", None)), # these were highlight versions, not needed
                                        document = text_xml,
                                        score = result.get("score", None), 
                                        rank = rowCount + 1,
                                        similarDocs = similarDocs,
                                        similarMaxScore = similarMaxScore,
                                        similarNumFound = similarNumFound
                                        )
            except ValidationError as e:
                logger.error(e.json())  
                #print (e.json())
            else:
                rowCount += 1
                # print ("{}:{}".format(rowCount, citeAs))
                #logger.info("{}:{}".format(rowCount, citeAs.decode("utf8")))
                documentItemList.append(item)
                if rowCount > limit:
                    break
    
        responseInfo.count = len(documentItemList)
        
        documentListStruct = models.DocumentListStruct( responseInfo = responseInfo, 
                                                 responseSet = documentItemList
                                                 )
        
        documentList = models.DocumentList(documentList = documentListStruct)
        
        ret_val = documentList
    
    return ret_val

#-----------------------------------------------------------------------------
def set_cookie(response: Response, name: str, value: Union[str, bytes], *, domain: Optional[str] = None,
               path: str = '/', expires: Optional[Union[float, Tuple, datetime]] = None,
               expires_days: Optional[int] = None, max_age: Optional[int] = None, secure=False, httponly=True,
               samesite: Optional[str] = 'Lax') -> None:
    """Sets an outgoing cookie name/value with the given options.

    Newly-set cookies are not immediately visible via `get_cookie`;
    they are not present until the next request.

    expires may be a numeric timestamp as returned by `time.time`,
    a time tuple as returned by `time.gmtime`, or a
    `datetime.datetime` object.
    """
    if not name.isidentifier():
        # Don't let us accidentally inject bad stuff
        raise ValueError(f'Invalid cookie name: {repr(name)}')
    if value is None:
        raise ValueError(f'Invalid cookie value: {repr(value)}')
    #value = unicode(value)
    cookie = http.cookies.SimpleCookie()
    cookie[name] = value
    morsel = cookie[name]
    if domain:
        morsel['domain'] = domain
    if path:
        morsel['path'] = path
    if expires_days is not None and not expires:
        expires = datetime.utcnow() + timedelta(days=expires_days)
    if expires:
        morsel['expires'] = expires
    if max_age is not None:
        morsel['max-age'] = max_age
    parts = [cookie.output(header='').strip()]
    if secure:
        parts.append('Secure')
    if httponly:
        parts.append('HttpOnly')
    if samesite:
        parts.append(f'SameSite={http.cookies._quote(samesite)}')
    cookie_val = '; '.join(parts)
    response.raw_headers.append((b'set-cookie', cookie_val.encode('latin-1')))

#-----------------------------------------------------------------------------
def delete_cookie(response: Response, name: str, *, domain: Optional[str] = None, path: str = '/') -> None:
    """Deletes the cookie with the given name.

    Due to limitations of the cookie protocol, you must pass the same
    path and domain to clear a cookie as were used when that cookie
    was set (but there is no way to find out on the server side
    which values were used for a given cookie).

    Similar to `set_cookie`, the effect of this method will not be
    seen until the following request.
    """
    expires = datetime.utcnow() - timedelta(days=365)
    set_cookie(response, name, value='', domain=domain, path=path, expires=expires, max_age=0)



#================================================================================================================================
def main():

    print (40*"*", "opasAPISupportLib Tests", 40*"*")
    print ("Fini")

# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    print ("Running in Python %s" % sys.version_info[0])
    
    sys.path.append(r'E:/usr3/GitHub/openpubarchive/app')
    sys.path.append(r'E:/usr3/GitHub/openpubarchive/app/config')
    sys.path.append(r'E:/usr3/GitHub/openpubarchive/app/libs')
    for n in sys.path:
        print (n)

    # Spot testing during Development
    #metadataGetContents("IJP", "1993")
    #getAuthorInfo("Tuck")
    #metadataGetVolumes("IJP")
    #authorsGetAuthorInfo("Tuck")
    #authorsGetAuthorPublications("Tuck", limit=40, offset=0)    
    #databaseGetMostCited(limit=10, offset=0)
    #getArticleData("PAQ.073.0005A")
    #databaseWhatsNew()
    # docstring tests
    # get_list_of_most_downloaded()
    # sys.exit(0)
    
    import doctest
    doctest.testmod()    
    main()
