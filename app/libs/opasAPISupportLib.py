#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
# doctest_ellipsis.py

"""
opasAPISupportLib

This library is meant to hold the 'meat' of the API based Solr queries and other support 
functions to keep the FastAPI definitions smaller, easier to read, and more manageable.

Also, some of these functions are reused in different API calls.

"""
    #2020.0505.1 Removed redundant param document_type from database_get_most_viewed (source_type already there)

    #2020.0530.1 Updated getmostviewed routine and all support for it to use the new in place updated art_view count fields in Solr
                # rather than using the values from the database, as before.  Moving the data to Solr allows these values to be
                # integrated with a solr query.
    #2021.0109.1 Removed commented out code
                 # used new documentID class from opasGenSupportLib rather than local checks and handling of document_od

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2021.0109.1"
__status__      = "Development"

import os
import os.path
import sys
# import shlex
import copy
import string

sys.path.append('./solrpy')
sys.path.append('./libs/configLib')

import http.cookies
import re
# import secrets
# import socket, struct
from collections import OrderedDict
from urllib.parse import unquote
from urllib.error import HTTPError
# import json
# from xml.sax import SAXParseException

from starlette.responses import Response
from starlette.requests import Request
from starlette.responses import Response
# import starlette.status as httpCodes
from starlette.exceptions import HTTPException

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

import opasFileSupport
# opas_fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET)

# from localsecrets import BASEURL, SOLRURL, SOLRUSER, SOLRPW, DEBUG_DOCUMENTS, SOLR_DEBUG, CONFIG, COOKIE_DOMAIN
from localsecrets import TIME_FORMAT_STR

# from opasConfig import OPASSESSIONID
# import configLib.opasCoreConfig as opasCoreConfig
from configLib.opasCoreConfig import solr_docs2, solr_authors2, solr_gloss2

from configLib.opasCoreConfig import EXTENDED_CORES

# from fastapi import HTTPException

# Removed support for Py2, only Py3 supported now
pyVer = 3
import logging
logger = logging.getLogger(__name__)

from lxml import etree
# from pydantic import BaseModel
from pydantic import ValidationError

# note: documents and documentList share the same internals, except the first level json label (documents vs documentlist)
import models

import opasXMLHelper as opasxmllib
import opasQueryHelper
import opasGenSupportLib as opasgenlib
import opasCentralDBLib
import opasDocPermissions as opasDocPerm
import opasPySolrLib
from opasPySolrLib import search_text, search_text_qs

# count_anchors = 0

def has_data(str):
    ret_val = True
    if str is None or str == "":
        ret_val = False

    return ret_val

def get_query_item_of_interest(solrQuery):
    """
    Give a solrQuery, use that to derive a string to be logged in the endpoint_session
      record column item_of_interest
    """
    ret_val = None
    try:
        try:
            fq = re.sub("art_level:1(\s\&\&\s)?", "", solrQuery.filterQ, re.I)
            if fq != '':
                ret_val = f"f:'{fq}'"
                spacer = " "
            else:
                ret_val = ""
                spacer = ""
        except:
            fq = ""
            ret_val = ""
            spacer = ""
    
        try:
            q = re.sub("\*:\*|{!parent\swhich=\'art_level:1\'}\sart_level:2\s&&\s", "", solrQuery.searchQ, re.I)
            if q != '':
                col_width_remaining = opasConfig.DB_ITEM_OF_INTEREST_WIDTH - len(fq) # don't exceed column width for logging 
                ret_val += f"{spacer}q:'{q[:col_width_remaining]}'"
        except Exception as e:
            pass
    except:
        ret_val = None

    return ret_val

def remove_leading_zeros(numeric_string):
    """
        >>> remove_leading_zeros("0033")
        '33'
        
    """
    ret_val = ""
    for n in numeric_string:
        if n != "0":
            ret_val += n
    
    return ret_val
            
def split_article_id(article_id):
    """
    >>> split_article_id("gap.005.0199a")
    ('GAP', None, '5', '199A', None)

    >>> split_article_id("rfp.075.0017a")
    ('RFP', None, '75', '17A', None)

    >>> split_article_id(None)
    (None, None, None, None, None)

    """
    journal = year = vol = page = page_id = None
    if article_id is not None:
        article_id = article_id.upper()
        
        try:
            journal, vol, page = article_id.split(".")
        except Exception as e:
            try:
                a,b,c,d = article_id.split(".")
                if d[0] == "P":
                    journal, vol, page, page_id = a, b, c, d
                elif b[:2] in [19, 20]:
                    journal, year, vol, page = a, b, c, d
            except Exception as e:
                logger.error(f"SplitArticleIDError: can not split ID {article_id} ({e})")
        else:
            vol = remove_leading_zeros(vol)
            page = remove_leading_zeros(page)
        
            if journal is not None:
                journal = journal.upper()
        
            if year is not None:
                year = page.upper()
                
            if page is not None:
                page = page.upper()
                
            if page_id is not None:
                page_id = page_id.upper()
       
    return journal, year, vol, page, page_id
    
#-----------------------------------------------------------------------------
def get_max_age(keep_active=False):
    if keep_active:    
        ret_val = opasConfig.COOKIE_MAX_KEEP_TIME    
    else:
        ret_val = opasConfig.COOKIE_MIN_KEEP_TIME     
    return ret_val  # maxAge


#-----------------------------------------------------------------------------
def get_session_info(request: Request,
                     response: Response,
                     session_id:str=None, 
                     client_id=None,
                     expires_time=None, 
                     force_new_session=False,
                     user=None,
                     caller_name="get_session_info"):
    """
    Return a sessionInfo object with all of that info, and a database handle
    Note that non-logged in sessions are not stored in the database

    Get session info accesses the DB per the session_id to see if the session exists.

     1) If no session_id is supplied (None), it returns a default SessionInfo object, user not logged in,
        with a session id constant defined in opasConfig.NO_SESSION_ID.  These should
        not be written to the DB api_session table (watch elsewhere).

     2) If there is a session_id, it gets the session_info from the api_sessions table in the DB.
        a) If it's not there (None):
           i) It does a permission check on the user via the session_id
           ii) It saves the session
        b) If it's there already: (Repeatable, quickest path)
           i) Done, returns it.  No update.  

    New 2021-10-07 - Header will indicate (from client) if the user is logged in, saving queries to PaDS
                     (Note The server still checks all permissions on full-text returns)

    """
    ocd = opasCentralDBLib.opasCentralDB()
    if session_id is not None and session_id != opasConfig.NO_SESSION_ID:
        user_logged_in_bool = opasDocPerm.user_logged_in_per_header(request, session_id=session_id, caller_name=caller_name)
        ts = time.time()
        session_info = ocd.get_session_from_db(session_id)
        if session_info is None:
            in_db = False
            # logger.warning(f"Session info for {session_id} not found in db.  Getting from authserver (will save on server)")
            # session info is saved in get_authserver_session_info if logged in  
            session_info = opasDocPerm.get_authserver_session_info(session_id=session_id,
                                                                   client_id=client_id,
                                                                   request=request)
            logger.debug(f"{caller_name}: Session {session_id} in DB:{in_db}. Authenticated:{session_info.authenticated}. URL: {request.url} PaDS SessionInfo: {session_info.pads_session_info}") # 09/13 removed  Server Session Info: {session_info} for brevity
            # session info is saved in get_authserver_session_info   
            # success, session_info = ocd.save_session(session_id, session_info)
        else:
            in_db = True
            # if they weren't authenticated, but headers say they are, check again
            if session_info.authenticated == False and user_logged_in_bool: # or session_info.session_expires_time < datetime.today(): # not logged in
                # better check if now they are logged in
                # session info is saved in get_authserver_session_info if logged in  
                session_info = opasDocPerm.get_authserver_session_info(session_id=session_id,
                                                                       client_id=client_id, 
                                                                       request=request)
                # session info is saved in get_authserver_session_info   
                # success, session_info = ocd.save_session(session_id, session_info)
                logger.debug(f"{caller_name}: Session {session_id} in DB:{in_db}. Authenticated:{session_info.authenticated}. URL: {request.url} PaDS SessionInfo: {session_info.pads_session_info}") # 09/14 removed  Server Session Info: {session_info} for brevity
            else:
                if session_info.authenticated == True and user_logged_in_bool == True:
                    # note that user_logged_in_bool can be None
                    ## important - because they "were" logged in, we will return a session timed out error
                    ## so don't refresh it...server likes to know they were logged in
                    remaining_time = session_info.session_expires_time - datetime.today()
                    remaining_time_hrs = remaining_time.seconds // 3600
                    logger.info(f"User was authenticated per server database record.  Session {session_id}. Expires: {remaining_time_hrs} hrs ({session_info.session_expires_time}). DB SessionInfo: {session_info}")
                else:
                    logger.debug(f"User is logged in (session {session_id}), but the client did not supply header info.")

        if opasConfig.LOG_CALL_TIMING:
            logger.debug(f"Get/Save session info response time: {time.time() - ts}")       
        
    else:
        logger.warning("No SessionID; Default session info returned (Not Logged In)")
        session_info = models.SessionInfo() # default session model

    return ocd, session_info

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
    ret_val = opasQueryHelper.force_string_return_from_various_return_types(ret_val)

    return ret_val

# REMOVED COMMENTED CODE 20210109
#-----------------------------------------------------------------------------
#def get_session_id(request):
    ## this will be a sesson ID from the client--must be in every call!
    #ret_val = request.cookies.get(opasConfig.OPASSESSIONID, None)
    #if ret_val is None:
        #ret_val = request.headers.get(opasConfig.CLIENTSESSIONID, None)

    #return ret_val
#-----------------------------------------------------------------------------
#def get_access_token(request):
    #ret_val = request.cookies.get(opasConfig.OPASACCESSTOKEN, None)
    #return ret_val

#-----------------------------------------------------------------------------
def get_expiration_time(request):
    ret_val = request.cookies.get(opasConfig.OPASEXPIRES, None)
    return ret_val
#-----------------------------------------------------------------------------
def database_get_most_viewed( publication_period: int=5,
                              author: str=None,
                              title: str=None,
                              source_name: str=None,  
                              source_code: str=None,
                              source_type: str="journal",
                              abstract_requested: bool=False, 
                              view_period: int=4,               # 4=last12months default. 0:lastcalendaryear 1:lastweek 2:lastmonth, 3:last6months, 4:last12months
                              view_count: str="1",              # up this later
                              req_url: str=None,
                              stat:bool=False, 
                              limit: int=5,                     # Get top 10 from the period
                              offset=0,
                              mlt_count:int=None,
                              sort:str=None,
                              download=False, 
                              session_info=None,
                              request=None
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

    >>> result, status = database_get_most_viewed()
    >>> result.documentList.responseSet[0].documentID if result.documentList.responseInfo.count >0 else "No views yet."
    '...'

    """
    ret_val = None
    caller_name = "database_get_most_viewed"
    ret_status = (200, "OK") # default is like HTTP_200_OK
    period = opasConfig.VALS_VIEWPERIODDICT_SOLRFIELDS.get(view_period, "last12mos")
    
    if sort is None:
        sort = f"{period} desc"

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
        opasQueryHelper.parse_search_query_parameters( viewperiod=view_period,      # 0:lastcalendaryear 1:lastweek 2:lastmonth, 3:last6months, 4:last12months
                                                       viewcount=view_count, 
                                                       source_name=source_name,
                                                       source_code=source_code,
                                                       source_type=source_type,
                                                       author=author,
                                                       title=title,
                                                       startyear=start_year,
                                                       highlightlimit=0, 
                                                       abstract_requested=abstract_requested,
                                                       return_field_set=field_set, 
                                                       sort = sort,
                                                       req_url = req_url
                                                       )
    if download: # much more limited document list if download==True
        ret_val, ret_status = opasPySolrLib.search_stats_for_download(solr_query_spec, 
                                                                      session_info=session_info, 
                                                                      request = request
                                                                      )
    else:
        try:
            ret_val, ret_status = opasPySolrLib.search_text_qs(solr_query_spec, 
                                                               limit=limit,
                                                               offset=offset,
                                                               req_url = req_url, 
                                                               session_info=session_info, 
                                                               request = request,
                                                               caller_name=caller_name
                                                              )
        except Exception as e:
            logger.error(f"Search error {e}")

    return ret_val, ret_status   

#-----------------------------------------------------------------------------
def database_get_most_cited( publication_period: int=None,   # Limit the considered pubs to only those published in these years
                             cited_in_period: str='5',  # 
                             cite_count: int=0,              # Has to be cited more than this number of times, a large nbr speeds the query
                             author: str=None,
                             title: str=None,
                             source_name: str=None,  
                             source_code: str=None,
                             source_type: str=None,
                             abstract_requested: bool=True, 
                             req_url: str=None, 
                             stat:bool=False, 
                             limit: int=None,
                             offset: int=0,
                             mlt_count:int=None, 
                             sort:str=None,
                             download:bool=None, 
                             session_info=None,
                             request=None
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
    ret_val = {}
    ret_status = (200, "OK") # default is like HTTP_200_OK
    caller_name = "database_get_most_cited"
    
    cited_in_period = opasConfig.normalize_val(cited_in_period, opasConfig.VALS_YEAROPTIONS, default='5')
    #if str(period).lower() not in models.TimePeriod._value2member_map_:
        #period = '5'

    if sort is None:
        sort = f"art_cited_{cited_in_period} desc"

    start_year = dtime.date.today().year
    if publication_period is None:
        start_year = None
    else:
        start_year -= publication_period
        start_year = f">{start_year}"

    cite_count_predicate = f"{cite_count} in {cited_in_period}"
    if stat:
        field_set = "STAT"
    else:
        field_set = None
    
    solr_query_spec = \
        opasQueryHelper.parse_search_query_parameters(citecount=cite_count_predicate, 
                                                      source_name=source_name,
                                                      source_code=source_code,
                                                      source_type=source_type, 
                                                      author=author,
                                                      title=title,
                                                      startyear=start_year,
                                                      highlightlimit=0, 
                                                      return_field_set=field_set, 
                                                      abstract_requested=abstract_requested,
                                                      similar_count=mlt_count, 
                                                      sort = sort,
                                                      req_url = req_url
                                                    )

    if download: # much more limited document list if download==True
        ret_val, ret_status = opasPySolrLib.search_stats_for_download(solr_query_spec, 
                                                                      session_info=session_info
                                                                     )
    else:
        try:
            ret_val, ret_status = opasPySolrLib.search_text_qs(solr_query_spec, 
                                                               limit=limit,
                                                               offset=offset,
                                                               #mlt_count=mlt_count, 
                                                               session_info=session_info, 
                                                               req_url = req_url,
                                                               request = request,
                                                               caller_name=caller_name
                                                              )
        except Exception as e:
            logger.error(f"Search error {e}")
        
    return ret_val, ret_status   

#-----------------------------------------------------------------------------
def database_who_cited( publication_period: int=None,   # Limit the considered pubs to only those published in these years
                        cited_in_period: str='5',  # 
                        cited_art_id: str=None, # search rx for this
                        author: str=None,
                        title: str=None,
                        source_name: str=None,  
                        source_code: str=None,
                        source_type: str=None,
                        abstract_requested: bool=True, 
                        req_url: str=None, 
                        stat:bool=False, 
                        limit: int=None,
                        offset: int=0,
                        mlt_count:int=None, 
                        sort:str=None,
                        download:bool=None, 
                        session_info=None,
                        request=None
                        ):
    """
    Return the list of documents that cited this journal article.

    period must be either '5', 10, '20', or 'all'

    args:
      limit: the number of records you want to return

    >>> result, status = database_who_cited()
    >>> len(result.documentList.responseSet)>=10
    True

    """
    
    cited_in_period = opasConfig.normalize_val(cited_in_period, opasConfig.VALS_YEAROPTIONS, default='5')
    caller_name = "database_who_cited"

    if sort is None:
        sort = f"art_cited_{cited_in_period} desc"

    start_year = dtime.date.today().year
    if publication_period is None:
        start_year = None
    else:
        start_year -= publication_period
        start_year = f">{start_year}"

    try:
        solr_query_spec = \
            opasQueryHelper.parse_search_query_parameters(cited_art_id=cited_art_id, 
                                                          source_name=source_name,
                                                          source_code=source_code,
                                                          source_type=source_type, 
                                                          author=author,
                                                          title=title,
                                                          startyear=start_year,
                                                          highlightlimit=0, 
                                                          abstract_requested=abstract_requested,
                                                          similar_count=mlt_count, 
                                                          sort = sort,
                                                          req_url = req_url
                                                        )

        ret_val, ret_status = opasPySolrLib.search_text_qs(solr_query_spec, 
                                             limit=limit,
                                             offset=offset,
                                             #mlt_count=mlt_count, 
                                             session_info=session_info, 
                                             req_url = req_url, 
                                             request = request,
                                             caller_name=caller_name
                                            )
    except Exception as e:
        ret_status_msg = f"Who Cited Search error {e}"
        ret_val = {}
        ret_status = (200, ret_status_msg) 
        logger.error(ret_status_msg)
        
    return ret_val, ret_status   

#-----------------------------------------------------------------------------
def metadata_get_database_statistics(session_info=None):
    """
    Return counts for the annual summary (or load checks)

    >>> results = metadata_get_database_statistics()
    >>> results.article_count > 135000
    True
    """
    content = models.ServerStatusContent()
    
    # data = metadata_get_volumes(source_code="IJPSP")
    documentList, ret_status = search_text(query=f"art_id:*", 
                                               limit=1,
                                               facet_fields="art_year,art_pgcount,art_figcount,art_sourcetitleabbr,art_sourcecode", 
                                               abstract_requested=False,
                                               full_text_requested=False,
                                               session_info=session_info
                                               )
    
    bookList, ret_status = search_text(query=f"art_sourcecode:(ZBK || IPL || NLP)", 
                                               limit=1,
                                               facet_fields="art_product_key", 
                                               abstract_requested=False,
                                               full_text_requested=False, 
                                               session_info=session_info
                                               )
    
    videoList, ret_status = search_text(query=f"art_sourcecode:*VS", 
                                               limit=1,
                                               facet_fields=None, 
                                               abstract_requested=False,
                                               full_text_requested=False, 
                                               session_info=session_info
                                               )

    content.article_count = documentList.documentList.responseInfo.fullCount
    facet_counts = documentList.documentList.responseInfo.facetCounts
    facet_fields = facet_counts["facet_fields"]
    src_counts = facet_fields["art_sourcetitleabbr"]
    src_code_counts = facet_fields["art_sourcecode"]
    fig_counts = facet_fields["art_figcount"]
    # figure count is how many figures shown in all articles (possible some are in more than one, not likely.  But one article could present a graphic multiple times.)
    #  so not the same as the number of graphics in the g folder. (And a figure could be a chart or table)
    content.figure_count = sum([int(y) * int(x) for x,y in fig_counts.items() if x != '0'])
    journals_plus_videos = [x for x,y in src_counts.items() if x not in ("ZBK", "IPL", "NLP", "SE", "GW")]
    journals = [x for x in src_code_counts if re.match(".*VS|OFFSITE|SE|GW|IPL|NLP|ZBK", x) is None]
    content.journal_count = len(journals)
    content.video_count = videoList.documentList.responseInfo.fullCount
    book_facet_counts = bookList.documentList.responseInfo.facetCounts
    book_facet_fields = book_facet_counts["facet_fields"]
    book_facet_product_keys = book_facet_fields["art_product_key"]
    content.book_count = len(book_facet_product_keys)
    content.source_count = dict(OrderedDict(sorted(src_counts.items(), key=lambda t: t[0])))
    vols = opasPySolrLib.metadata_get_volumes(source_type="journal")    
    content.vol_count = vols.volumeList.responseInfo.fullCount
    year_counts = facet_fields["art_year"]
    years = [int(x) for x,y in year_counts.items()]
    content.year_first = min(years)
    content.year_last = max(years)
    content.year_count = content.year_last - content.year_first
    page_counts = facet_fields["art_pgcount"]
    pages = [int(x) *int(y) for x,y in page_counts.items()]
    content.page_count = sum(pages)
    content.page_height_feet = int(((content.page_count * .1) / 25.4) / 12) # page thickness in mm, 25.4 mm per inch, 12 inches per foot
    content.page_weight_tons = int(content.page_count * 4.5 * 0.000001)
    source_count_html = "<ul>"
    for code, cnt in content.source_count.items():
        source_count_html += f"<li>{code} - {cnt}</li>"
    source_count_html += "</ul>"
   
    content.description_html = f"""
<p>This release of PEP-Web contains the complete text and illustrations of
{content.journal_count} premier journals in psychoanalysis,
{content.book_count} classic psychoanalytic books, and the full text and Editorial notes of the
24 volumes of the Standard Edition of the Complete Psychological Works of Sigmund Freud as well as the
19 volume German Freud Standard Edition Gesammelte Werke.  It spans over
{content.year_count} publication years and contains the full text of articles whose source ranges from
{content.year_first} through {content.year_last}.</p>
<p>
There are over
{content.article_count} articles and almost
{content.figure_count} figures and illustrations that originally resided on
{content.vol_count} volumes with over
{content.page_count/1000000:.2f} million printed pages. In hard copy, the PEP Archive represents a stack of paper more than
{content.page_height_feet} feet high and weighing over
{content.page_weight_tons} tons!
</p>
"""
    
    content.source_count_html = f"""
<p>
\nCount of Articles by Source:
\n{source_count_html}
</p>
"""
        
    ret_val = content
    return ret_val

#-----------------------------------------------------------------------------
def metadata_get_source_info(src_type=None, # opasConfig.VALS_PRODUCT_TYPES
                             src_code=None,
                             src_name=None, 
                             req_url: str=None, 
                             limit=opasConfig.DEFAULT_LIMIT_FOR_METADATA_LISTS,
                             offset=0):
    """
    Return a list of source metadata, by type (e.g., journal, book, video, stream.)

    NOTE: Stream is equiv to journal for videos. Video is more like books, individual videos).

    No attempt here to map to the correct structure, just checking what field/data items we have in sourceInfoDB.

    >>> results = metadata_get_source_info(src_code="APA")
    >>> results.sourceInfo.responseInfo.count == 1
    True
    >>> results = metadata_get_source_info(src_type="journal", limit=3)
    >>> results.sourceInfo.responseInfo.count >= 3
    True
    >>> results = metadata_get_source_info(src_type="book", limit=10)
    >>> results.sourceInfo.responseInfo.count >= 10
    True
    >>> results = metadata_get_source_info(src_type="journals", limit=10, offset=0)
    >>> results.sourceInfo.responseInfo.count >= 10
    True
    >>> results = metadata_get_source_info(src_type="journals", limit=10, offset=6)
    >>> results.sourceInfo.responseInfo.count >= 10
    True

    >>> results = metadata_get_source_info()
    >>> results.sourceInfo.responseInfo.fullCount
    191
    
    """
    ret_val = []
    source_info_dblist = []
    err = None
    ocd = opasCentralDBLib.opasCentralDB()
    # standardize Source type, allow plural, different cases, but code below this part accepts only those three.
    if src_type is not None and src_type != "*":
        src_type_in = src_type # save it for logging
        src_type = opasConfig.normalize_val(src_type, opasConfig.VALS_PRODUCT_TYPES)
        if src_type == None:
            err = f"SourceTypeError: {src_type_in}"
            logger.error(err)
            raise Exception(err)

    if src_type == "videos":
        # sort by title like other media types
        # IMPORTANT NOTE: Sort must be a string field to work!
        total_count, source_info_dblist, ret_val, return_status = opasPySolrLib.metadata_get_videos(src_type=src_type, pep_code=src_code, limit=limit, offset=offset, sort_field="title_str")
        count = len(source_info_dblist)
        if return_status != (200, "OK"):
            raise Exception(return_status(1))
    else: # get from mySQL
        try:
            # note...this sorts by title as only current option
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
                publisher = source.get("bib_abbrev")
                book_code = None
                # src_type = source.get("product_type")
                start_year = source.get("yearFirst")
                end_year = source.get("yearLast")
                base_code = source.get("basecode")
                instance_count = source.get("instances", 1)
                documentID = source.get("documentID", source.get("articleID"))
                if start_year is None:
                    start_year = pub_year
                if end_year is None:
                    end_year = pub_year
    
                if src_type == "book":
                    book_code = source.get("pepcode")
                    if book_code is None:
                        logger.warning(f"Book code information missing for requested basecode {base_code} in productbase")
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
                elif src_type == "videos":
                    art_citeas = source.get("art_citeas")
                else:
                    art_citeas = title # journals just should show display title
    
                try:
                    item = models.SourceInfoListItem( sourceType = src_type,
                                                      PEPCode = base_code,
                                                      authors = authors,
                                                      pub_year = pub_year,
                                                      documentID = documentID,
                                                      displayTitle = art_citeas,
                                                      title = title,
                                                      srcTitle = title,  # v1 Deprecated for future
                                                      bookCode = book_code,
                                                      abbrev = source.get("bibabbrev"),
                                                      bannerURL = f"{localsecrets.APIURL}/{opasConfig.IMAGES}/banner{source.get('basecode')}Logo.gif",
                                                      language = source.get("language"),
                                                      ISSN = source.get("ISSN"),
                                                      ISBN10 = source.get("ISBN-10"),
                                                      ISBN13 = source.get("ISBN-13"),
                                                      yearFirst = start_year,
                                                      yearLast = end_year,
                                                      instanceCount = instance_count, 
                                                      embargoYears = source.get("embargo")
                                                      ) 
                except ValidationError as e:
                    logger.error(f"ValidationError: metadataGetSourceByType SourceInfoListItem: {e.json()}")
                    #logger.error(e.json())
                    err = 1
    
            except Exception as e:
                logger.error(f"MetadataGetSourceInfoError: {e}")
                err = 1
    
            if err == 0:
                source_info_listitems.append(item)
    else:
        # book series workaround...any code not enabled in the database, i.e., SE/GW should not ever be getting do
        if src_code in opasConfig.BOOK_CODES_ALL:  # ("ZBK", "IPL", "NLP", "SE", "GW"):
            #print (f"Book Source code workaround--not enabled in DB: {src_code}")
            try:
                item = models.SourceInfoListItem( sourceType = "book series",
                                                  PEPCode = src_code,
                                                  #srcTitle = title,  # v1 Deprecated for future
                                                  #bookCode = book_code,
                                                  #abbrev = source.get("bibabbrev"),
                                                  bannerURL = f"{localsecrets.APIURL}/{opasConfig.IMAGES}/banner{src_code}Logo.gif",
                                                  #language = source.get("language"),
                                                  #ISSN = source.get("ISSN"),
                                                  #ISBN10 = source.get("ISBN-10"),
                                                  #ISBN13 = source.get("ISBN-13"),
                                                  #yearFirst = start_year,
                                                  #yearLast = end_year,
                                                  #instanceCount = instance_count, 
                                                  #embargoYears = source.get("embargo")
                                                  ) 
    
                source_info_listitems.append(item)
                response_info.count = 1
    
            except ValidationError as e:
                logger.error(f"MetadataGetSourceValidationError: {e.json()}")
                #logger.error(e.json())
                err = 1
        
        elif src_code in opasConfig.VIDEOSTREAM_CODES_ALL:  # workaround for getting codes 
            try:
                item = models.SourceInfoListItem( sourceType = "videostream series",
                                                  PEPCode = src_code,
                                                  #srcTitle = title,  # v1 Deprecated for future
                                                  #bookCode = book_code,
                                                  #abbrev = source.get("bibabbrev"),
                                                  bannerURL = f"{localsecrets.APIURL}/{opasConfig.IMAGES}/banner{src_code}Logo.gif",
                                                  #language = source.get("language"),
                                                  #ISSN = source.get("ISSN"),
                                                  #ISBN10 = source.get("ISBN-10"),
                                                  #ISBN13 = source.get("ISBN-13"),
                                                  #yearFirst = start_year,
                                                  #yearLast = end_year,
                                                  #instanceCount = instance_count, 
                                                  #embargoYears = source.get("embargo")
                                                  ) 
    
                source_info_listitems.append(item)
                response_info.count = 1
    
            except ValidationError as e:
                logger.error(f"MetadataGetSourceValidationError: Video Validation Error {e.json()}")
                #logger.error(e.json())
                err = 1

    try:
        source_info_struct = models.SourceInfoStruct( responseInfo = response_info, 
                                                      responseSet = source_info_listitems
                                                      )
    except ValidationError as e:
        logger.error(f"MetadataGetSourceValidationError: models.SourceInfoStruct {e.json()}")
        #logger.error(e.json())        

    try:
        source_info_list = models.SourceInfoList(sourceInfo = source_info_struct)
    except ValidationError as e:
        logger.error("MetadataGetSourceValidationError:")
        logger.error(e.json())        

    ret_val = source_info_list

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
                            session_info=None,
                            request=None
                            ):
    """
    Returns an abstract or summary for the specified document
    If part of a documentID is supplied, multiple abstracts will be returned.

    The endpoint reminds me that we should be using documentID instead of "art" for article perhaps.
      Not thrilled about the prospect of changing it, but probably the right thing to do.

    >>> results = documents_get_abstracts("IJP.075")
    >>> results.documents.responseInfo.count == 15
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
        # new document ID object provides precision and case normalization
        document_id_obj = opasgenlib.DocumentID(document_id)
        document_id = document_id_obj.document_id
        if document_id is None:
            document_id = document_id_obj.jrnlvol_id
            if document_id is None:
                document_id = document_id_obj.journal_code          

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
                                                 session_info=session_info,
                                                 request=request
                                                 )

        try:
            if opasFileSupport.file_exists(document_id=document_id, 
                                           year=document_list.documentList.responseSet[0].year,
                                           ext=localsecrets.PDF_ORIGINALS_EXTENSION, 
                                           path=localsecrets.PDF_ORIGINALS_PATH):
                document_list.documentList.responseSet[0].pdfOriginalAvailable = True
            else:
                document_list.documentList.responseSet[0].pdfOriginalAvailable = False
        except Exception as e:
            logger.debug(f"pdfOriginalAvailable check error: {e}")
            #default is false
            #document_list.documentList.responseSet[0].pdfOriginalAvailable = False          
        
        if not isinstance(document_list, models.ErrorReturn):
            documents = models.Documents(documents = document_list.documentList)
        else:
            err = document_list
            logger.error(f"DocumentGetAbstractError: {err.error_description}")
            raise HTTPException(
                status_code=err.error,
                detail=err.error_description
            )                
        
        ret_val = documents

    return ret_val

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
                           session_info=None, 
                           option_flags=0,
                           request=None
                           ):
    """
    For non-authenticated users, this endpoint returns only Document summary information (summary/abstract)
    For authenticated users, it returns with the document itself

    >> resp = documents_get_document("AIM.038.0279A", ret_format="html") 

    >> resp = documents_get_document("AIM.038.0279A") 

    >> resp = documents_get_document("AIM.040.0311A")


    """
    caller_name = "documents_get_document"
    ret_val = None
    document_list = None
    ext = localsecrets.PDF_ORIGINALS_EXTENSION #  PDF originals extension
    # search_text_qs handles the authentication verification

    # new document ID object provides precision and case normalization
    document_id_obj = opasgenlib.DocumentID(document_id)
    document_id = document_id_obj.document_id

    #m = re.match("(?P<docid>(?P<scode>[A-Z]+)\.(?P<svol>[0-9]{3,3})\.(?P<spage>[0-9]{4,4}[A-Z]))(\.P0{0,3}(?P<pagejump>[0-9]{1,4}))?", document_id)
    #if m is not None:
        #if m.group("pagejump") is not None:
            #document_id = m.group("docid")
            ## only if they haven't directly specified page
            #if page == None:
                #page = m.group("pagejump")
    # just to be sure
    query = "*:*"
    if solr_query_spec is not None:
        solr_query_params = solr_query_spec.solrQuery
        # repeat the query that the user had done when retrieving the document
        query = f"{solr_query_params.searchQ}"
        if query == "":
            query = "*:*"
            search_context = None
        else:
            search_context = query
        filterQ = f"art_id:{document_id} && {solr_query_params.filterQ}"
        # solrParams = solr_query_params.dict() 
    else:
        query = f"art_id:{document_id}"
        filterQ = None
        #solrMax = None
        # solrParams = None

    solr_query_spec = \
            opasQueryHelper.parse_to_query_spec(query = query,
                                                filter_query = filterQ,
                                                similar_count=similar_count, 
                                                full_text_requested=True,
                                                abstract_requested=True,
                                                format_requested=ret_format,
                                                #return_field_set=return_field_set, 
                                                #summary_fields = summary_fields,  # deprecate?
                                                highlight_fields = "text_xml, art_title",
                                                facet_fields=opasConfig.DOCUMENT_VIEW_FACET_LIST,
                                                facet_mincount=1,
                                                extra_context_len=opasConfig.SOLR_HIGHLIGHT_RETURN_FRAGMENT_SIZE, 
                                                limit = 1,
                                                page_offset = page_offset,
                                                page_limit = page_limit,
                                                page = page,
                                                req_url = req_url, 
                                                option_flags=option_flags # dictionary of return options
                                                )

    document_list, ret_status = opasPySolrLib.search_text_qs(solr_query_spec,
                                                             session_info=session_info,
                                                             get_full_text=True, 
                                                             request=request,
                                                             caller_name=caller_name
                                                             )

    try:
        matches = document_list.documentList.responseInfo.count
        if matches > 0:
            # get the first document item only
            document_list_item = document_list.documentList.responseSet[0]
            # is user authorized?
            if document_list_item.accessChecked == False or document_list_item.accessLimited == True or document_list_item.accessLimited is None:
                document_list_item.document = document_list_item.abstract
            else:
                if opasFileSupport.file_exists(document_id=document_list_item.documentID, 
                                               year=document_list_item.year,
                                               ext=ext, 
                                               path=localsecrets.PDF_ORIGINALS_PATH):
                    document_list_item.pdfOriginalAvailable = True
                else:
                    document_list_item.pdfOriginalAvailable = False

        elif search_context is not None:
            # failed to retrieve, get it without the search qualifier from last time.
            solr_query_spec.solrQuery.searchQ = "*:*"
            document_list, ret_status = opasPySolrLib.search_text_qs(solr_query_spec,
                                                                     session_info=session_info,
                                                                     request=request,
                                                                     caller_name=caller_name
                                                                     )
            matches = document_list.documentList.responseInfo.count
            if matches > 0:
                # get the first document item only
                document_list_item = document_list.documentList.responseSet[0]
                # is user authorized?
                if document_list_item.accessChecked == False or document_list_item.accessLimited == True or document_list_item.accessLimited is None:
                    document_list_item.document = document_list_item.abstract
                else:
                    if opasFileSupport.file_exists(document_id=document_list_item.documentID, 
                                                   year=document_list_item.year,
                                                   ext=ext, 
                                                   path=localsecrets.PDF_ORIGINALS_PATH):
                        document_list_item.pdfOriginalAvailable = True
                    else:
                        document_list_item.pdfOriginalAvailable = False
                        
                document_list.documentList.responseSet[0].term = f'SearchHits({search_context})'
                document_list.documentList.responseSet[0].termCount = 0

    except Exception as e:
        logger.error("get_document: No matches or another error: %s", e)
        # return None
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
            # experimental options: uses option_flags to turn on
            if option_flags is not None:
                if option_flags & opasConfig.OPTION_2_RETURN_TRANSLATION_SET:
                    # get document translations of the first document (note this also includes the original)
                    if document_list_item.origrx is not None:
                        translationSet, count = opasPySolrLib.quick_docmeta_docsearch(q_str=f"art_origrx:{document_list_item.origrx}", req_url=req_url)
                        if translationSet is not None:
                            # set translationSet to a list, just like 
                            document_list_item.translationSet = translationSet
            
            # is user authorized?
            if document_list.documentList.responseSet[0].accessLimited or document_list.documentList.responseSet[0].accessChecked == False or document_list.documentList.responseSet[0].accessLimited is None:
                document_list.documentList.responseSet[0].document = document_list.documentList.responseSet[0].abstract
                
            document_list_struct = models.DocumentListStruct( responseInfo = response_info, 
                                                              responseSet = [document_list_item]
                                                              )

            documents = models.Documents(documents = document_list_struct)

            ret_val = documents

    return ret_val

#-----------------------------------------------------------------------------
def documents_get_concordance_paras(para_lang_id,
                                    para_lang_rx=None, 
                                    solr_query_spec=None,
                                    ret_format="XML",
                                    req_url:str=None, 
                                    session_info=None,
                                    request=None
                                    ):
    """
    For non-authenticated users, this endpoint returns only Document summary information (summary/abstract)
    For authenticated users, it returns with the document itself

    >> resp = documents_get_concordance_paras("SEXixa5", ret_format="html") 

    >> resp = documents_get_concordance_paras("SEXixa5") 


    """
    caller_name = "documents_get_concordance_paras"
    ret_val = {}
    document_list = None
    if para_lang_rx is not None:
        paraLangFilterQ = f'({re.sub(",", " || ", para_lang_rx)})'
    else:
        paraLangFilterQ = f"{para_lang_id}"
        
    query = "*:*"
    filterQ = f"para_lgrid:{paraLangFilterQ}"
    try:
        solr_query_spec = \
                opasQueryHelper.parse_to_query_spec(solr_query_spec=solr_query_spec, 
                                                    query=query,
                                                    filter_query=filterQ,
                                                    full_text_requested=True,
                                                    format_requested=ret_format,
                                                    return_field_set="CONCORDANCE", 
                                                    highlight_fields="para",
                                                    extra_context_len=opasConfig.SOLR_HIGHLIGHT_RETURN_FRAGMENT_SIZE, 
                                                    #limit=10,
                                                    req_url=req_url
                                                    )

        document_list, ret_status = search_text_qs(solr_query_spec,
                                                   session_info=session_info,
                                                   request=request,
                                                   caller_name=caller_name
                                                   )

        #matches = document_list.documentList.responseInfo.count
        #if matches >= 1:
            #for count in range(0, matches-1):
                #document_list_item = document_list.documentList.responseSet[count]
                ## is user authorized?
                #if document_list.documentList.responseSet[count].accessLimited and 0:
                    ## Should we require it's authorized?
                    #document_list.documentList.responseSet[count].document = document_list.documentList.responseSet[count].abstract
                ##else:
                    ### All set
        #else:
            #logger.info(f"get_para_trans: No matches: {filterQ}")
    except Exception as e:
        logger.error(f"get_para_trans: No matches or error: {e}")
    else:
        document_list_struct = models.DocumentListStruct( responseInfo = document_list.documentList.responseInfo, 
                                                          responseSet = document_list.documentList.responseSet
                                                          )

        documents = models.Documents(documents = document_list_struct)

        ret_val = documents

    return ret_val

#-----------------------------------------------------------------------------
def documents_get_glossary_entry(term_id,
                                 term_id_type=None,
                                 record_per_term=False, # new 20210127, if false, collapse groups to one return record.
                                 retFormat="XML",
                                 req_url: str=None,
                                 session_info=None,
                                 limit=opasConfig.DEFAULT_LIMIT_FOR_DOCUMENT_RETURNS,
                                 offset=0,
                                 request=None):
    """
    For non-authenticated users, this endpoint should return an error (#TODO)

    For authenticated users, it returns with the glossary itself

    IMPORTANT NOTE: At least the way the database is currently populated, for a group, the textual part (text) is the complete group, 
      and thus the same for all entries.  This is best for PEP-Easy now, otherwise, it would need to concatenate all the result entries.
      
    As of 2020-11, Group and Name use text fields, so partial matches are included rather than string fields which require exact
     matches

    >> resp = documents_get_glossary_entry("ZBK.069.0001o.YN0019667860580", retFormat="html") 

    >> resp = documents_get_glossary_entry("ZBK.069.0001o.YN0004676559070") 

    >> resp = documents_get_glossary_entry("ZBK.069.0001e.YN0005656557260")


    """
    caller_name = "documents_get_glossary_entry"
    ret_val = {}

    # Name and Group are strings, and case sensitive, so search, as submitted, and uppercase as well
    if term_id_type == "Name":
        # 2020-11-11 use text field instead
        qstr = f'term_terms:("{term_id}")'
        # qstr = f'term:("{term_id}" || "{term_id.upper()}" || "{term_id.lower()}")'
    elif term_id_type == "Group":
        # 2020-11-11 use text field instead
        # qstr = f'group_name_terms:("{term_id}")'
        # trying hybrid 2021-01-27
        #qstr = f'group_name:("{term_id}" || "{term_id.upper()}" || "{term_id.lower()}")'
        # hybrid search both if needed! 2021-01-27
        qstr = f'group_name:("{term_id}" || "{term_id.upper()}" || "{term_id.lower()}")'
        count = opasPySolrLib.get_match_count(solr_gloss2, query=qstr)
        if count == 0:
            # no match, look in the group terms for a match
            qstr = f'group_name_terms:("{term_id}")'
            count = opasPySolrLib.get_match_count(solr_gloss2, query=qstr)
        
    else: # default is term ID
        term_id = term_id.upper()
        qstr = f"term_id:{term_id} || group_id:{term_id}"

    solr_query_spec = \
            opasQueryHelper.parse_to_query_spec(query = f"art_id:{opasConfig.GLOSSARY_TOC_INSTANCE}",
                                                full_text_requested=False,
                                                abstract_requested=False,
                                                format_requested="XML",
                                                limit = 1,
                                                req_url = req_url
                                                )


    gloss_info, ret_status = search_text_qs(solr_query_spec, 
                                            extra_context_len=opasConfig.DEFAULT_KWIC_CONTENT_LENGTH,
                                            limit=1,
                                            session_info=session_info,
                                            request = request,
                                            caller_name=caller_name
                                            )
        
    gloss_template = gloss_info.documentList.responseSet[0]
    
    args = {
        "fl": opasConfig.GLOSSARY_ITEM_DEFAULT_FIELDS, 
        "facet.field": opasConfig.DOCUMENT_VIEW_FACET_LIST,
        "facet.mincount": 1
    }
    
    try:
        results = solr_gloss2.search(qstr, **args)
    except Exception as e:
        err = f"Solr query failed {e}"
        logger.error(err)
        raise Exception(err)
           
    document_item_list = []
    count = 0
    last_group = None
    try:
        for result in results.docs:
            document = result.get("text", None)
            documentListItem = copy.deepcopy(gloss_template)
            if not documentListItem.accessChecked == True and documentListItem.accessLimited == False:
                try:
                    if retFormat == "HTML":
                        document = opasxmllib.xml_str_to_html(document)
                    elif retFormat == "TEXTONLY":
                        document = opasxmllib.xml_elem_or_str_to_text(document)
                    else: # XML
                        document = document
                except Exception as e:
                    logger.error(f"Error converting glossary content: {term_id} ({e})")
            else: # summary only
                try:
                    if retFormat == "HTML":
                        document = opasxmllib.xml_str_to_html(document, transformer_name=opasConfig.XSLT_XMLTOHTML_GLOSSARY_EXCERPT)
                    elif retFormat == "TEXTONLY":
                        document = opasxmllib.xml_elem_or_str_to_text(document) # TODO need summary here?  Or are we allowing full access?      
                    else: # XML
                        document = document # TODO need summary here? Or are we allowing full access?                 
                except ValidationError as e:
                    logger.error(e.json())  
                except Exception as e:
                    warning = f"Error getting contents of Glossary entry {term_id}"
                    logger.error(warning)
                    document = warning
                
            documentListItem.groupID = result.get("group_id", None)
            # if using document, getting the individual items in a group is redundant.
            #  so in that case, don't add them.  Only return unique groups.
            if last_group != documentListItem.groupID or record_per_term:
                last_group = documentListItem.groupID
                documentListItem.term = result.get("term", None)
                documentListItem.termID = result.get("term_id")
                # documentListItem.document = document 
                documentListItem.document = result.get("text")
                documentListItem.groupName = result.get("group_name", None)
                documentListItem.groupTermCount = result.get("group_term_count", None)
                documentListItem.termSource = result.get("term_source", None)
                documentListItem.termType = result.get("term_type", None)
                documentListItem.termDefPartXML = result.get("term_def_xml")
                documentListItem.termDefRestXML = result.get("term_def_rest_xml")
                # note, the rest of the document info is from the TOC instance, but we're changing the name here
                documentListItem.documentID = result.get("art_id", None)
                documentListItem.score = result.get("score", None)
                document_item_list.append(documentListItem)

        count = len(document_item_list)
        if count == 0:
            documentListItem = copy.deepcopy(gloss_template)
            documentListItem.document = documentListItem.term = "No matching glossary entry."
            # raise Exception(KeyError("No matching glossary entry"))
    except IndexError as e:
        logger.error("No matching glossary entry for %s.  Error: %s", (term_id, e))
    except KeyError as e:
        logger.error("No content or abstract found for %s.  Error: %s", (term_id, e))
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

#================================================================================================================
def save_opas_session_cookie(request: Request, response: Response, session_id):
    ret_val = False
    already_set = False
    if session_id is not None and session_id is not 'None':
        already_set = False
        try:
            opasSession = [x for x in response.raw_headers[0] if b"opasSessionID" in x]
            already_set = b"opasSessionID" in opasSession[0][0:13]
        except Exception as e:
            logger.info(f"Exception, but Ok, opasSessionID cookie not in response {e}")

    if already_set == False and session_id is not None:
        try:
            logger.debug("Saved OpasSessionID Cookie")
            response.set_cookie(
                opasConfig.OPASSESSIONID,
                value=f"{session_id}",
                domain=localsecrets.COOKIE_DOMAIN
            )
            ret_val = True
        except Exception as e:
            logger.error(f"Can't save opas session-id cookie: {e}")
            ret_val = False
            
    return ret_val
    
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
