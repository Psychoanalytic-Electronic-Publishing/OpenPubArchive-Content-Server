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
#sys.path.append('../libs')
sys.path.append('../config')
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
from localsecrets import BASEURL
#from libs.opasConfig import *

from stdMessageLib import copyrightPageHTML  # copyright page text to be inserted in ePubs and PDFs
from localsecrets import SOLRURL, SOLRUSER, SOLRPW, DEBUG_DOCUMENTS, CONFIG, COOKIE_DOMAIN

pyVer = 2
if (sys.version_info > (3, 0)):
    # Python 3 code in this block
    from io import StringIO
    pyVer = 3
else:
    # Python 2 code in this block
    import StringIO
    
#import pysolr
import solr
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
    solrDocs = solr.SolrConnection(SOLRURL + 'pepwebdocs', http_user=SOLRUSER, http_pass=SOLRPW)
    solrRefs = solr.SolrConnection(SOLRURL + 'pepwebrefs', http_user=SOLRUSER, http_pass=SOLRPW)
    solrGloss = solr.SolrConnection(SOLRURL + 'pepwebglossary', http_user=SOLRUSER, http_pass=SOLRPW)
    solrAuthors = solr.SolrConnection(SOLRURL + 'pepwebauthors', http_user=SOLRUSER, http_pass=SOLRPW)
    solrAuthorTermSearch = solr.SearchHandler(solrAuthors, "/terms")

else:
    solrDocs = solr.SolrConnection(SOLRURL + 'pepwebdocs')
    solrRefs = solr.SolrConnection(SOLRURL + 'pepwebrefs')
    solrGloss = solr.SolrConnection(SOLRURL + 'pepwebglossary')
    solrAuthors = solr.SolrConnection(SOLRURL + 'pepwebauthors')
    solrAuthorTermSearch = solr.SearchHandler(solrAuthors, "/terms")

#API endpoints
documentURL = "/v1/Documents/"

#-----------------------------------------------------------------------------
def getMaxAge(keepActive=False):
    if keepActive:    
        retVal = opasConfig.COOKIE_MAX_KEEP_TIME    
    else:
        retVal = opasConfig.COOKIE_MIN_KEEP_TIME     
    return retVal  # maxAge

#-----------------------------------------------------------------------------
def getSessionInfo(request: Request, resp: Response, 
                   sessionID=None, accessToken=None, expiresTime=None, 
                   keepActive=False, forceNewSession=False, user=None):
    """
    Get session info from cookies, or create a new session if one doesn't exist.
    Return a sessionInfo object with all of that info, and a database handle
    
    """
    sessionID = getSessionID(request)
    print ("Get Session Info, Session ID via GetSessionID: ", sessionID)
    
    if sessionID is None or sessionID=='' or forceNewSession:  # we need to set it
        # get new sessionID...even if they already had one, this call forces a new one
        print ("sessionID is none (or forcedNewSession).  We need to start a new session.")
        ocd, sessionInfo = startNewSession(resp, request, accessToken, keepActive=keepActive, user=user)  
        #sessionInfo = SessionInfo(session_id = sessionID, 
                                         #access_token = ocd.accessToken, 
                                         #authenticated = ocd.accessToken is not None, 
                                         #session_expires_time = ocd.tokenExpiresTime)
        
    else: # we already have a sessionID, no need to recreate it.
        # see if an accessToken is already in cookies
        accessToken = getAccessToken(request)
        expirationTime = getExpirationTime(request)
        print ("sessionID is already set.")
        try:
            ocd = opasCentralDBLib.opasCentralDB(sessionID, accessToken, expirationTime)
            sessionInfo = ocd.getSessionFromDB(sessionID)
            if sessionInfo is None:
                # this is an error, and means there's no recorded session info.  Should we create a s
                #  session record, return an error, or ignore? #TODO
                # try creating a record
                username="NotLoggedIn"
                retVal, sessionInfo = ocd.saveSession(sessionID, 
                                                      userID=0,
                                                      userIP=request.client.host, 
                                                      connectedVia=request.headers["user-agent"],
                                                      username=username)  # returns save status and a session object (matching what was sent to the db)

        except ValidationError as e:
            print("Validation Error: ", e.json())             
    
    print ("getSessionInfo: ", sessionInfo)
    return ocd, sessionInfo
    
def isSessionAuthenticated(request, resp):
    """
    Look to see if the session has been marked authenticated in the database
    """
    ocd, sessionInfo = getSessionInfo(request, resp)
    sessionID = sessionInfo.session_id
    # is the user authenticated? if so, loggedIn is true
    retVal = sessionInfo.authenticated
    return retVal
    
def extractHTMLFragment(strHTML, xpathToExtract="//div[@id='abs']"):
    # parse HTML
    htree = etree.HTML(strHTML)
    retVal = htree.xpath(xpathToExtract)
    # make sure it's a string
    retVal = forceStringReturnFromVariousReturnTypes(retVal)
    
    return retVal

#-----------------------------------------------------------------------------
def startNewSession(resp: Response, request: Request, sessionID=None, accessToken=None, keepActive=None, user=None):
    """
    Create a new session record and set cookies with the session

    Returns database object, and the sessionInfo object
    
    If user is supplied, that means they've been authenticated.
      
    This should be the only place to generate and start a new session.
    """
    print ("************** Starting a new SESSION!!!! *************")
    sessionStart=datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    maxAge = getMaxAge(keepActive)
    tokenExpirationTime=datetime.utcfromtimestamp(time.time() + maxAge).strftime('%Y-%m-%d %H:%M:%S')
    if sessionID == None:
        sessionID = secrets.token_urlsafe(16)
        logger.info("startNewSession assigning New Session ID: {}".format(sessionID))

    setCookies(resp, sessionID, accessToken, tokenExpiresTime=tokenExpirationTime)
    # get the database Object
    ocd = opasCentralDBLib.opasCentralDB()
    # save the session info
    if user:
        username=user.username
        retVal, sessionInfo = ocd.saveSession(sessionID=sessionID, 
                                              username=user.username,
                                              userID=user.user_id,
                                              expiresTime=tokenExpirationTime,
                                              userIP=request.client.host, 
                                              connectedVia=request.headers["user-agent"],
                                              accessToken = accessToken
                                              )
    else:
        username="NotLoggedIn"
        retVal, sessionInfo = ocd.saveSession(sessionID, 
                                              userID=0,
                                              expiresTime=tokenExpirationTime,
                                              userIP=request.client.host, 
                                              connectedVia=request.headers["user-agent"],
                                              username=username)  # returns save status and a session object (matching what was sent to the db)

    # return the object so the caller can get the details of the session
    return ocd, sessionInfo

#-----------------------------------------------------------------------------
def deleteCookies(resp: Response, sessionID=None, accessToken=None, tokenExpiresTime=None):
    """
    Delete the session and or accessToken cookies in the response header 
   
    """

    print ("Setting specified cookies to empty to delete them")
    expires = datetime.utcnow() - timedelta(days=365)
    if sessionID is not None:
        set_cookie(resp, "opasSessionID", value='', domain=COOKIE_DOMAIN, path="/", expires=expires, max_age=0)

    if accessToken is not None:
        set_cookie(resp, "opasAccessToken", value='', domain=COOKIE_DOMAIN, path="/", expires=expires, max_age=0)
        #set_cookie(resp, name, value='', domain=domain, path=path, expires=expires, max_age=0)
    return resp
    
#-----------------------------------------------------------------------------
def setCookies(resp: Response, sessionID, accessToken=None, maxAge=None, tokenExpiresTime=None):
    """
    Set the session and or accessToken cookies in the response header 
    
    if accessToken isn't supplied, it is not set.
    
    """
    
    print ("Setting cookies for {}".format(COOKIE_DOMAIN))
    if sessionID is not None:
        print ("Session Cookie being Written from SetCookies")
        set_cookie(resp, "opasSessionID", sessionID, domain=COOKIE_DOMAIN, httponly=False)

    if accessToken is not None:
        set_cookie(resp, "opasAccessToken", accessToken, domain=COOKIE_DOMAIN, httponly=False, max_age=maxAge) #, expires=tokenExpiresTime)

    return resp
    
#-----------------------------------------------------------------------------
def parseCookiesFromHeader(request):
    retVal = {}
    clientSuppliedCookies = request.headers.get("cookie", None)
    if clientSuppliedCookies is not None:
        cookieStatements = clientSuppliedCookies.split(";")
        for n in cookieStatements:
            cookie, value = n.split("=")
            retVal[cookie] = value

    return retVal

#-----------------------------------------------------------------------------
def getSessionID(request):
    sessionCookieName = "opasSessionID"
    retVal = request.cookies.get(sessionCookieName, None)
    
    if retVal is None:
        cookieDict = parseCookiesFromHeader(request)
        retVal = cookieDict.get(sessionCookieName, None)
        if retVal is not None:
            print ("getSessionID: Session cookie had to be retrieved from header: {}".format(retVal))
    else:
        print ("getSessionID: Session cookie from client: {}".format(retVal))
    return retVal

#-----------------------------------------------------------------------------
def getAccessToken(request):
    retVal = request.cookies.get("opasAccessToken", None)
    return retVal

#-----------------------------------------------------------------------------
def getExpirationTime(request):
    retVal = request.cookies.get("opasSessionExpirestime", None)
    return retVal

#-----------------------------------------------------------------------------
def checkSolrDocsConnection():
    """
    Queries the solrDocs core (i.e., pepwebdocs) to see if the server is up and running.
    Solr also supports a ping, at the corename + "/ping", but that doesn't work through pysolr as far as I can tell,
    so it was more straightforward to just query the Core. 
    
    Note that this only checks one core, since it's only checking if the Solr server is running.
    
    >>> checkSolrDocsConnection()
    True
    
    """
    if solrDocs is None:
        return False
    else:
        try:
            results = solrDocs.query(q = "art_id:{}".format("APA.009.0331A"),  fields = "art_id, art_vol, art_year")
        except Exception as e:
            logger.error("Solr Connection Error: {}".format(e))
            return False
        else:
            if len(results.results) == 0:
                return False
        return True

#-----------------------------------------------------------------------------
def forceStringReturnFromVariousReturnTypes(theText, minLength=5):
    """
    Sometimes the return isn't a string (it seems to often be "bytes") 
      and depending on the schema, from Solr it can be a list.  And when it
      involves lxml, it could even be an Element node or tree.
      
    This checks the type and returns a string, converting as necessary.
    
    >>> forceStringReturnFromVariousReturnTypes(["this is really a list",], minLength=5)
    'this is really a list'

    """
    retVal = None
    if theText is not None:
        if isinstance(theText, str):
            if len(theText) > minLength:
                # we have an abstract
                retVal = theText
        elif isinstance(theText, list):
            retVal = theText[0]
            if retVal == [] or retVal == '[]':
                retVal = None
        else:
            logger.error("Type mismatch on Solr Data")
            print ("forceStringReturn ERROR: %s" % type(retVal))

        try:
            if isinstance(retVal, lxml.etree._Element):
                retVal = etree.tostring(retVal)
            
            if isinstance(retVal, bytes) or isinstance(retVal, bytearray):
                logger.error("Byte Data")
                retVal = retVal.decode("utf8")
        except Exception as e:
            err = "forceStringReturn Error forcing conversion to string: %s / %s" % (type(retVal), e)
            logger.error(err)
            print (err)
            
    return retVal        

#-----------------------------------------------------------------------------
def getArticleDataRaw(articleID, fields=None):
    """
    Fetch an article "Doc" from the Solr solrDocs core.  If fields is none, it fetches all fields.

    This returns a dictionary--the one returned by Solr 
      (hence why the function is Raw rather than Pydantic like getArticleData)
      
    >>> result = getArticleDataRaw("APA.009.0331A")
    >>> result["article_id"]
    APA.009.0331A
    
    """
    retVal = None
    if articleID != "":
        try:
            results = solrDocs.query(q = "art_id:{}".format(articleID),  fields = fields)
        except Exception as e:
            logger.error("Solr Error: {}".format(e))
            retVal = None
        else:
            if results._numFound == 0:
                retVal = None
            else:
                retVal = results.results[0]

    return retVal
                
#-----------------------------------------------------------------------------
def getArticleData(articleID, fields=None):
    """
    Fetch an article "Doc" from the Solr solrDocs core.  If fields is none, it fetches all fields.

    Returns the pydantic model object for a document in a regular documentListStruct

    >>> result = getArticleData("APA.009.0331A")
    >>> result.documentList.responseSet[0].documentID
    APA.009.0331A
    
    """
    retVal = None
    if articleID != "":
        try:
            results = solrDocs.query(q = "art_id:{}".format(articleID),  fields = fields)
        except Exception as e:
            logger.error("Solr Error: {}".format(e))
            retVal = None
        else:
            if results._numFound == 0:
                retVal = None
            else:
                retVal = results.results[0]
    limit = 5 # for now, we may make this 1
    offset = 0
    responseInfo = models.ResponseInfo (
                     count = len(results.results),
                     fullCount = results._numFound,
                     totalMatchCount = results._numFound,
                     limit = limit,
                     offset = offset,
                     listType="documentlist",
                     scopeQuery=None,
                     fullCountComplete = limit >= results._numFound,
                     solrParams = results._params,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )

    documentItemList = []
    rowCount = 0
    rowOffset = 0
    for result in results.results:
        authorIDs = result.get("art_authors", None)
        if authorIDs is None:
            authorMast = None
        else:
            authorMast = opasgenlib.deriveAuthorMast(authorIDs)

        pgRg = result.get("art_pgrg", None)
        if pgRg is not None:
            pgStart, pgEnd = opasgenlib.pgRgSplitter(pgRg)
            
        documentID = result.get("art_id", None)        
        #titleXml = results.highlighting[documentID].get("art_title_xml", None)
        titleXml = result.get("art_title_xml", None)
        titleXml = forceStringReturnFromVariousReturnTypes(titleXml)
        #abstractsXml = results.highlighting[documentID].get("abstracts_xml", None)
        abstractsXml = result.get("abstracts_xml", None)
        abstractsXml  = forceStringReturnFromVariousReturnTypes(abstractsXml )
        #summariesXml = results.highlighting[documentID].get("abstracts_xml", None)
        summariesXml = result.get("abstracts_xml", None)
        summariesXml  = forceStringReturnFromVariousReturnTypes(summariesXml)
        #textXml = results.highlighting[documentID].get("text_xml", None)
        textXml = result.get("text_xml", None)
        textXml  = forceStringReturnFromVariousReturnTypes(textXml)
        kwicList = []
        kwic = ""  # this has to be "" for PEP-Easy, or it hits an object error.  
    
        if DEBUG_DOCUMENTS != 1:
            if not userLoggedIn or not fullTextRequested:
                textXml = getExcerptFromAbstractOrSummaryOrDocument(xmlAbstract=abstractsXml, xmlSummary=summariesXml, xmlDocument=textXml)

        citeAs = result.get("art_citeas_xml", None)
        citeAs = forceStringReturnFromVariousReturnTypes(citeAs)
        
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
                                    documentRef = opasxmllib.xmlElemOrStrToText(citeAs, defaultReturn=""),
                                    title = titleXml,
                                    abstract = abstractsXml,
                                    documentText = None, #textXml,
                                    score = result.get("score", None), 
                                    )
        except ValidationError as e:
            logger.error(e.json())  
            #print (e.json())
        else:
            rowCount += 1
            print ("{}:{}".format(rowCount, citeAs))
            documentItemList.append(item)
            if rowCount > limit:
                break

    responseInfo.count = len(documentItemList)
    
    documentListStruct = models.DocumentListStruct( responseInfo = responseInfo, 
                                             responseSet = documentItemList
                                             )
    
    documentList = models.DocumentList(documentList = documentListStruct)
    
    retVal = documentList
    
    return retVal

#-----------------------------------------------------------------------------
def getListOfMostDownloaded(viewPeriod="all", documentType="journals", author=None, title=None, journalName=None, limit=5, offset=0):
    """
    Return the most downloaded (viewed) journal articles duing the prior period years.
    
    Args:
        viewPeriod (int or str, optional): Look only at articles this many years back to current.  Defaults to 5.
        documentType (str, optional): The type of document, enumerated set: journals, books, videos, or all.  Defaults to "journals"
        author (str, optional): Filter, include matching author names per string .  Defaults to None (no filter).
        title (str, optional): Filter, include only titles that match.  Defaults to None (no filter).
        journalName (str, optional): Filter, include only journals matching this name.  Defaults to None (no filter).
        limit (int, optional): Paging mechanism, return is limited to this number of items.
        offset (int, optional): Paging mechanism, start with this item in limited return set, 0 is first item.

    Returns:
        models.DocumentList: Pydantic structure (dict) for DocumentList.  See models.py

    Docstring Tests:
    
    >>> result = databaseGetMostDownloaded()

    >>> result.documentList.responseSet[0].documentID


    """
    ocd = opasCentralDBLib.opasCentralDB()
    count, mostDownloaded = ocd.getMostDownloaded(viewPeriod=viewPeriod, 
                                                  documentType=documentType, 
                                                  author=author, 
                                                  title=title, 
                                                  journalName=journalName, 
                                                  limit=limit, offset=offset)  # (most viewed)
    
    responseInfo = models.ResponseInfo(
                     count = count,
                     fullCount = None,
                     limit = limit,
                     offset = offset,
                     listType="mostviewed",
                     fullCountComplete = False,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )

    
    documentListItems = []
    rowCount = 0
    rowOffset = 0

    for download in mostDownloaded:
        PEPCode = download.get("jrnlcode", None)
        authorMast = download.get("authorMast", None)
        hdgAuthor = download.get("hdgauthor", None)
        hdgTitle = download.get("hdgtitle", None)
        srcTitle = download.get("srctitleseries", None)
        volume = download.get("vol", None)
        issue = download.get("issue", "")
        year = download.get("pubyear", None)
        abbrev = download.get("srctitleseries", "")
        updated = download.get("updated", None)
        updated = time.strftime('%Y-%m-%d')
        pgRg = download.get("pgrg", None)
        pgStart, pgEnd = opasgenlib.pgRgSplitter(pgRg)
        countLastWeek = download.get("lastweek", None)
        countLastMonth = download.get("lastmonth", None)
        countLast6Months = download.get("last6months", None)
        countLast12Months = download.get("last12months", None)
        countLastCalYear = download.get("lastcalyear", None)
        xmlref = download.get("xmlref", None)
        citeAs = opasxmllib.getHTMLCiteAs(authorsBibStyle=hdgAuthor, 
                                          artYear=year,
                                          artTitle=hdgTitle, 
                                          artPepSourceTitleFull=srcTitle, 
                                          artVol=volume, 
                                          artPgrg=pgRg)
        
        displayTitle = abbrev + f" v{volume}.{issue} ({year}) (Added: {updated})"
        
        volumeURL = f"/v1/Metadata/Contents/{PEPCode}/{volume}"
        
        item = models.DocumentListItem( documentID = download.get("documentid", None),
                                 instanceCount = download.get("last12months", None),
                                 title = srcTitle,
                                 PEPCode = PEPCode, 
                                 authorMast = authorMast,
                                 year = year,
                                 vol = volume,
                                 pgRg = pgRg,
                                 issue = issue,
                                 pgStart = pgStart,
                                 pgEnd = pgEnd,
                                 count1 = countLastWeek,
                                 count2 = countLastMonth,
                                 count3 = countLast6Months,
                                 count4 = countLast12Months,
                                 count5 = countLastCalYear,
                                 documentRefHTML = citeAs,
                                 documentRef = opasxmllib.xmlElemOrStrToText(xmlref, defaultReturn=None),
                              ) 
        rowCount += 1
        print (item)
        documentListItems.append(item)
        if rowCount > limit:
            break

    # Not sure why it doesn't come back sorted...so we sort it here.
    #retVal2 = sorted(retVal, key=lambda x: x[1], reverse=True)
    
    responseInfo.count = len(documentListItems)
    
    documentListStruct = models.DocumentListStruct( responseInfo = responseInfo, 
                                                    responseSet = documentListItems
                                                  )
    
    documentList = models.DocumentList(documentList = documentListStruct)
    
    retVal = documentList
    
    return retVal   


#-----------------------------------------------------------------------------
def databaseGetMostCited(period='5', limit=10, offset=0):
    """
    Return the most cited journal articles duing the prior period years.
    
    period must be either '5', 10, '20', or 'all'
    
    >>> result = databaseGetMostCited()
    Number found: 114589
    >>> result.documentList.responseSet[0].documentID
    'IJP.027.0099A'

    """
    # old way...
    #results = solrRefs.query(q = "art_year_int:[2014 TO 2019]",  
                             #facet_field = "bib_ref_rx",
                             #facet_sort = "count",
                             #fl = "art_id, id, bib_ref_id, art_pepsrccode, bib_ref_rx_sourcecode",
                             #rows = "0",
                             #facet = "on"
                             #)

    if period.lower() not in ['5', '10', '20', 'all']:
        period = '5'
    
    results = solrDocs.query(q = "*:*",  
                             fl = f"art_id, title, art_vol, art_iss, art_year,  art_pepsrccode, \
                                   art_cited_{period}, art_cited_all, timestamp, art_pepsrccode, \
                                   art_pepsourcetype, art_pepsourcetitleabbr, art_pgrg, art_citeas_xml, art_authors_mast, \
                                   abstract_xml, text_xml",
                             fq = "art_pepsourcetype: journal",
                             sort = f"art_cited_{period} desc",
                             limit = limit
                             )

    print ("databaseGetMostCited Number found: %s" % results._numFound)
    
    responseInfo = models.ResponseInfo(
                     count = len(results.results),
                     fullCount = results._numFound,
                     limit = limit,
                     offset = offset,
                     listType="mostcited",
                     fullCountComplete = limit >= results._numFound,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )

    
    documentListItems = []
    rowCount = 0
    rowOffset = 0

    for result in results:
        PEPCode = result.get("art_pepsrccode", None)
        #if PEPCode is None or PEPCode in ["SE", "GW", "ZBK", "IPL"]:  # no books
            #continue

        PEPCode = result.get("art_pepsrccode", None)
        authorMast = result.get("art_authors_mast", None)
        volume = result.get("art_vol", None)
        issue = result.get("art_iss", "")
        year = result.get("art_year", None)
        abbrev = result.get("art_pepsourcetitleabbr", "")
        updated = result.get("timestamp", None)
        updated = updated.strftime('%Y-%m-%d')
        pgRg = result.get("art_pgrg", None)
        pgStart, pgEnd = opasgenlib.pgRgSplitter(pgRg)
        
        displayTitle = abbrev + " v%s.%s (%s) (Added: %s)" % (volume, issue, year, updated)
        volumeURL = "/v1/Metadata/Contents/%s/%s" % (PEPCode, issue)
        srcTitle = result.get("art_pepsourcetitlefull", "")
        citeAs = result.get("art_citeas_xml", None)
        artAbstract = result.get("art_abstract", None)
        
        item = models.DocumentListItem( documentID = result.get("art_id", None),
                                 instanceCount = result.get("art_cited_5", None),
                                 title = srcTitle,
                                 PEPCode = PEPCode, 
                                 authorMast = authorMast,
                                 year = year,
                                 vol = volume,
                                 pgRg = pgRg,
                                 issue = issue,
                                 pgStart = pgStart,
                                 pgEnd = pgEnd,
                                 documentRefHTML = citeAs,
                                 documentRef = opasxmllib.xmlElemOrStrToText(citeAs, defaultReturn=None),
                                 abstract = artAbstract,
                              ) 
        rowCount += 1
        #print (item)
        documentListItems.append(item)
        if rowCount > limit:
            break

    # Not sure why it doesn't come back sorted...so we sort it here.
    #retVal2 = sorted(retVal, key=lambda x: x[1], reverse=True)
    
    responseInfo.count = len(documentListItems)
    
    documentListStruct = models.DocumentListStruct( responseInfo = responseInfo, 
                                             responseSet = documentListItems
                                             )
    
    documentList = models.DocumentList(documentList = documentListStruct)
    
    retVal = documentList
    
    return retVal   

#-----------------------------------------------------------------------------
def databaseWhatsNew(daysBack=7, limit=opasConfig.DEFAULT_LIMIT_FOR_WHATS_NEW, offset=0):
    """
    Return a what's been updated in the last week
    
    >>> result = databaseWhatsNew()
    Number found: 91
    """    
    
    try:
        results = solrDocs.query(q = f"timestamp:[NOW-{daysBack}DAYS TO NOW]",  
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
            results = solrDocs.query(q = "art_pepsourcetype:journal",  
                                     fl = "art_id, title, art_vol, art_iss, art_pepsrccode, timestamp, art_pepsourcetype",
                                     fq = "{!collapse field=art_pepsrccode max=art_year_int}",
                                     sort="timestamp", sort_order="desc",
                                     rows=25, offset=0,
                                     )
    
            print ("databaseWhatsNew Expanded search to most recent...Number found: %s" % results._numFound)

        except Exception as e:
            print (f"Solr Search Exception: {e}")
    
    responseInfo = models.ResponseInfo(
                     count = len(results.results),
                     fullCount = results._numFound,
                     limit = limit,
                     offset = offset,
                     listType="newlist",
                     fullCountComplete = limit >= results._numFound,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )

    
    whatsNewListItems = []
    rowCount = 0
    alreadySeen = []
    for result in results:
        PEPCode = result.get("art_pepsrccode", None)
        #if PEPCode is None or PEPCode in ["SE", "GW", "ZBK", "IPL"]:  # no books
            #continue
        PEPSourceType = result.get("art_pepsourcetype", None)
        if PEPSourceType != "journal":
            continue
            
        volume = result.get("art_vol", None)
        issue = result.get("art_iss", "")
        year = result.get("art_year", None)
        abbrev = sourceDB.sourceData[PEPCode].get("sourcetitleabbr", "")
        updated = result.get("timestamp", None)
        updated = updated.strftime('%Y-%m-%d')
        displayTitle = abbrev + " v%s.%s (%s) " % (volume, issue, year)
        if displayTitle in alreadySeen:
            continue
        else:
            alreadySeen.append(displayTitle)
        volumeURL = "/v1/Metadata/Contents/%s/%s" % (PEPCode, issue)
        srcTitle = sourceDB.sourceData[PEPCode].get("sourcetitlefull", "")
            
        item = models.WhatsNewListItem( documentID = result.get("art_id", None),
                                 displayTitle = displayTitle,
                                 abbrev = abbrev,
                                 volume = volume,
                                 issue = issue,
                                 year = year,
                                 PEPCode = PEPCode, 
                                 srcTitle = srcTitle,
                                 volumeURL = volumeURL,
                                 updated = updated
                              ) 
        #print (item.displayTitle)
        whatsNewListItems.append(item)
        rowCount += 1
        if rowCount > limit:
            break

    responseInfo.count = len(whatsNewListItems)
    
    whatsNewListStruct = models.WhatsNewListStruct( responseInfo = responseInfo, 
                                             responseSet = whatsNewListItems
                                             )
    
    whatsNewList = models.WhatsNewList(whatsNew = whatsNewListStruct)
    
    retVal = whatsNewList
    
    return retVal   

#-----------------------------------------------------------------------------
def searchLikeThePEPAPI():
    pass  # later

#-----------------------------------------------------------------------------
def metadataGetVolumes(pepCode, year="*", limit=opasConfig.DEFAULT_LIMIT_FOR_VOLUME_LISTS, offset=0):
    """
    """
    retVal = []
    #print ("limit = %s, offset = %s" % (limit, offset))
           
    results = solrDocs.query(q = "art_pepsrccode:%s && art_year:%s" % (pepCode, year),  
                             fields = "art_vol, art_year",
                             sort="art_year", sort_order="asc",
                             fq="{!collapse field=art_vol}",
                             rows=limit, start=offset
                             )

    print ("metadataGetVolumes Number found: %s" % results._numFound)
    responseInfo = models.ResponseInfo(
                     count = len(results.results),
                     fullCount = results._numFound,
                     limit = limit,
                     offset = offset,
                     listType="volumelist",
                     fullCountComplete = limit >= results._numFound,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )

    volumeItemList = []
    for result in results.results:
        item = models.VolumeListItem(PEPCode = pepCode, 
                              year = result.get("art_year", None),
                              vol = result.get("art_vol", None),
                              score = result.get("score", None)
                             )
    
        #print (item)
        volumeItemList.append(item)
       
    responseInfo.count = len(volumeItemList)
    
    volumeListStruct = models.VolumeListStruct( responseInfo = responseInfo, 
                                         responseSet = volumeItemList
                                         )
    
    volumeList = models.VolumeList(volumeList = volumeListStruct)
    
    retVal = volumeList
    return retVal

#-----------------------------------------------------------------------------
def metadataGetContents(pepCode, year="*", vol="*", limit=opasConfig.DEFAULT_LIMIT_FOR_CONTENTS_LISTS, offset=0):
    """
    Return a jounals contents
    
    >>> metadataGetContents("IJP", "1993", limit=5, offset=0)
    <DocumentList documentList=<DocumentListStruct responseInfo=<models.ResponseInfo count=5 limit=5 offset=0 page=No…>
    >>> metadataGetContents("IJP", "1993", limit=5, offset=5)
    <DocumentList documentList=<DocumentListStruct responseInfo=<models.ResponseInfo count=5 limit=5 offset=5 page=No…>
    """
    retVal = []
    if year == "*" and vol != "*":
        # specified only volume
        field="art_vol"
        searchVal = vol
    else:  #Just do year
        field="art_year"
        searchVal = "*"
        
    results = solrDocs.query(q = "art_pepsrccode:{} && {}:{}".format(pepCode, field, searchVal),  
                             fields = "art_id, art_vol, art_year, art_iss, art_iss_title, art_newsecnm, art_pgrg, art_title, art_author_id, art_citeas_xml",
                             sort="art_year, art_pgrg", sort_order="asc",
                             rows=limit, start=offset
                             )

    responseInfo = models.ResponseInfo(
                     count = len(results.results),
                     fullCount = results._numFound,
                     limit = limit,
                     offset = offset,
                     listType="documentlist",
                     fullCountComplete = limit >= results._numFound,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )

    documentItemList = []
    for result in results.results:
        # transform authorID list to authorMast
        authorIDs = result.get("art_author_id", None)
        if authorIDs is None:
            authorMast = None
        else:
            authorMast = opasgenlib.deriveAuthorMast(authorIDs)
        
        pgRg = result.get("art_pgrg", None)
        pgStart, pgEnd = opasgenlib.pgRgSplitter(pgRg)
        citeAs = result.get("art_citeas_xml", None)  
        citeAs = forceStringReturnFromVariousReturnTypes(citeAs)
        
        item = models.DocumentListItem(PEPCode = pepCode, 
                                year = result.get("art_year", None),
                                vol = result.get("art_vol", None),
                                pgRg = result.get("art_pgrg", None),
                                pgStart = pgStart,
                                pgEnd = pgEnd,
                                authorMast = authorMast,
                                documentID = result.get("art_id", None),
                                documentRef = opasxmllib.xmlElemOrStrToText(citeAs, defaultReturn=""),
                                documentRefHTML = citeAs,
                                score = result.get("score", None)
                                )
        #print (item)
        documentItemList.append(item)

    responseInfo.count = len(documentItemList)
    
    documentListStruct = models.DocumentListStruct( responseInfo = responseInfo, 
                                             responseSet=documentItemList
                                             )
    
    documentList = models.DocumentList(documentList = documentListStruct)
    
    retVal = documentList
    
    return retVal

#-----------------------------------------------------------------------------
def metadataGetVideos(sourceType=None, PEPCode=None, limit=opasConfig.DEFAULT_LIMIT_FOR_METADATA_LISTS, offset=0):
    """
    Fill out a sourceInfoDBList which can be used for a getSources return, but return individual 
      videos, as is done for books.  This provides more information than the 
      original API which returned video "journals" names.  
      
    """
    
    if PEPCode != None:
        query = "art_pepsourcetype:video* AND art_pepsrccode:{}".format(PEPCode)
    else:
        query = "art_pepsourcetype:video*"
    try:
        srcList = solrDocs.query(q = query,  
                                    fields = "art_id, art_issn, art_pepsrccode, art_authors, title, art_pepsourcetitlefull, art_pepsourcetitleabbr, art_vol, art_year, art_citeas_xml, art_lang, art_pgrg",
                                    sort="art_citeas_xml", sort_order="asc",
                                    rows=limit, start=offset
                                 )
    except Exception as e:
        print ("metadataGetVideos Error: {}".format(e))
    sourceInfoDBList = []
    count = len(srcList.results)
    totalCount = int(srcList.results.numFound)
    
    for result in srcList.results:
        sourceInfoRecord = {}
        authors = result.get("art_authors")
        if authors is None:
            sourceInfoRecord["author"] = None
        elif len(authors) > 1:
            sourceInfoRecord["author"] = "; ".join(authors)
        else:    
            sourceInfoRecord["author"] = authors[0]
            
        sourceInfoRecord["src_code"] = result.get("art_pepsrccode")
        sourceInfoRecord["ISSN"] = result.get("art_issn")
        sourceInfoRecord["documentID"] = result.get("art_id")
        try:
            sourceInfoRecord["title"] = result.get("title")[0]
        except:
            sourceInfoRecord["title"] = ""
            
        sourceInfoRecord["art_citeas"] = result.get("art_citeas_xml")
        sourceInfoRecord["pub_year"] = result.get("art_year")
        sourceInfoRecord["bib_abbrev"] = result.get("art_year")
        try:
            sourceInfoRecord["language"] = result.get("art_lang")[0]
        except:
            sourceInfoRecord["language"] = "EN"

        print ("metadataGetVideos: ", sourceInfoRecord)
        sourceInfoDBList.append(sourceInfoRecord)

    return totalCount, sourceInfoDBList

#-----------------------------------------------------------------------------
def metadataGetSourceByType(sourceType=None, PEPCode=None, limit=opasConfig.DEFAULT_LIMIT_FOR_METADATA_LISTS, offset=0):
    """
    Rather than get this from Solr, where there's no 1:1 records about this, we will get this from the sourceInfoDB instance.
    
    No attempt here to map to the correct structure, just checking what field/data items we have in sourceInfoDB.
    
    >>> returnData = metadataGetSourceByType("journal")
    Number found: 75

    >>> returnData = metadataGetSourceByType("book")
    Number found: 6

    >>> metadataGetSourceByType("journals", limit=5, offset=0)
    Number found: 75
    
    >>> metadataGetSourceByType("journals", limit=5, offset=6)
    Number found: 75
    
    """
    retVal = []
    sourceInfoDBList = []
    ocd = opasCentralDBLib.opasCentralDB()
    # standardize Source type, allow plural, different cases, but code below this part accepts only those three.
    sourceType = sourceType.lower()
    if sourceType not in ["journal", "book"]:
        if re.match("videos.*", sourceType, re.IGNORECASE):
            sourceType = "videos"
        elif re.match("video", sourceType, re.IGNORECASE):
            sourceType = "videostream"
        elif re.match("boo.*", sourceType, re.IGNORECASE):
            sourceType = "book"
        else: # default
            sourceType = "journal"
   
    # This is not part of the original API, it brings back individual videos rather than the videostreams
    # but here in case we need it.  In that case, your source must be videos.*, like videostream, in order
    # to load individual videos rather than the video journals
    if sourceType == "videos":        
        totalCount, sourceInfoDBList = metadataGetVideos(sourceType, PEPCode, limit, offset)
        count = len(sourceInfoDBList)
    else: # get from mySQL
        try:
            if PEPCode != "*":
                totalCount, sourceData = ocd.getSources(sourceType = sourceType, source=PEPCode, limit=limit, offset=offset)
            else:
                totalCount, sourceData = ocd.getSources(sourceType = sourceType, limit=limit, offset=offset)
                
            for sourceInfoDict in sourceData:
                if sourceInfoDict["src_type"] == sourceType:
                    # match
                    sourceInfoDBList.append(sourceInfoDict)
            if limit < totalCount:
                count = limit
            else:
                count = totalCount
            print ("MetadataGetSourceByType: Number found: %s" % count)
        except Exception as e:
            errMsg = "MetadataGetSourceByType: Error getting source information.  {}".format(e)
            count = 0
            print (errMsg)

    responseInfo = models.ResponseInfo(
                     count = count,
                     fullCount = totalCount,
                     fullCountComplete = count == totalCount,
                     limit = limit,
                     offset = offset,
                     listLabel = "{} List".format(sourceType),
                     listType = "sourceinfolist",
                     scopeQuery = "*",
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )

    sourceInfoListItems = []
    counter = 0
    for source in sourceInfoDBList:
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
            if sourceType == "book":
                bookCode = source.get("base_code")
                m = re.match("(?P<code>[a-z]+)(?P<num>[0-9]+)", bookCode, re.IGNORECASE)
                if m is not None:
                    code = m.group("code")
                    num = m.group("num")
                    bookCode = code + "." + num
                
                artCiteAs = u"""<p class="citeas"><span class="authors">%s</span> (<span class="year">%s</span>) <span class="title">%s</span>. <span class="publisher">%s</span>.""" \
                    %                   (authors,
                                         source.get("pub_year"),
                                         title,
                                         publisher
                                        )
            elif sourceType == "video":
                artCiteAs = source.get("art_citeas")
            else:
                artCiteAs = title # journals just should show display title


            try:
                item = models.SourceInfoListItem( sourceType = sourceType,
                                                  PEPCode = source.get("src_code"),
                                                  authors = authors,
                                                  pub_year = pub_year,
                                                  documentID = source.get("art_id"),
                                                  displayTitle = artCiteAs,
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
            

        sourceInfoListItems.append(item)
        
    try:
        sourceInfoStruct = models.SourceInfoStruct( responseInfo = responseInfo, 
                                             responseSet = sourceInfoListItems
                                            )
    except ValidationError as e:
        print ("models.SourceInfoStruct Validation Error:")
        print(e.json())        
    
    try:
        sourceInfoList = models.SourceInfoList(sourceInfo = sourceInfoStruct)
    except ValidationError as e:
        print ("SourceInfoList Validation Error:")
        print(e.json())        
    
    retVal = sourceInfoList

    return retVal

#-----------------------------------------------------------------------------
def metadataGetSourceByCode(PEPCode=None, limit=opasConfig.DEFAULT_LIMIT_FOR_SOLR_RETURNS, offset=0):
    """
    Rather than get this from Solr, where there's no 1:1 records about this, we will get this from the sourceInfoDB instance.
    
    No attempt here to map to the correct structure, just checking what field/data items we have in sourceInfoDB.
    
    The sourceType is listed as part of the endpoint path, but I wonder if we should really do this 
    since it isn't needed, the pepCodes are unique.
    
    curl -X GET "http://stage.pep.gvpi.net/api/v1/Metadata/Journals/AJP/" -H "accept: application/json"
    
    >>> metadataGetSourceByCode("APA")["wall"]
    3
    >>> metadataGetSourceByCode()
    
    """
    retVal = []
    ocd = opasCentralDBLib.opasCentralDB()
    
    # would need to add URL for the banner
    if PEPCode is not None:
        totalCount, sourceInfoDBList = ocd.getSources(PEPCode)    #sourceDB.sourceData[pepCode]
        #sourceType = sourceInfoDBList.get("src_type", None)
    else:
        totalCount, sourceInfoDBList = ocd.getSources(PEPCode)    #sourceDB.sourceData
        sourceType = "All"
            
    count = len(sourceInfoDBList)
    print ("metadataGetSourceByCode: Number found: %s" % count)

    responseInfo = models.ResponseInfo(
                     count = count,
                     fullCount = totalCount,
                     limit = limit,
                     offset = offset,
                     #listLabel = "{} List".format(sourceType),
                     listType = "sourceinfolist",
                     scopeQuery = "*",
                     fullCountComplete = True,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )

    sourceInfoListItems = []
    counter = 0
    for source in sourceInfoDBList:
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

        sourceInfoListItems.append(item)
        
    try:
        sourceInfoStruct = models.SourceInfoStruct( responseInfo = responseInfo, 
                                             responseSet = sourceInfoListItems
                                            )
    except ValidationError as e:
        print (80*"-")
        print ("metadataGetSourceByCode: SourceInfoStruct Validation Error:")
        print(e.json())        
        print (80*"-")
    
    try:
        sourceInfoList = models.SourceInfoList(sourceInfo = sourceInfoStruct)
    except ValidationError as e:
        print (80*"-")
        print ("metadataGetSourceByCode: SourceInfoList Validation Error:")
        print(e.json())        
        print (80*"-")
    
    retVal = sourceInfoList
    return retVal

#-----------------------------------------------------------------------------
def authorsGetAuthorInfo(authorNamePartial, limit=opasConfig.DEFAULT_LIMIT_FOR_SOLR_RETURNS, offset=0, authorOrder="index"):
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
        >>> resp = authorsGetAuthorInfo("Tuck")
        Number found: 72
        >>> resp = authorsGetAuthorInfo("Fonag")
        Number found: 134
        >>> resp = authorsGetAuthorInfo("Levinson, Nadine A.")
        Number found: 8   
    """
    retVal = {}
    method = 2
    
    if method == 1:
        query = "art_author_id:/%s.*/" % (authorNamePartial)
        results = solrAuthors.query(q=query,
                                    fields="authors, art_author_id",
                                    facet_field="art_author_id",
                                    facet="on",
                                    facet_sort="index",
                                    facet_prefix="%s" % authorNamePartial,
                                    facet_limit=limit,
                                    facet_offset=offset,
                                    rows=0
                                    )       

    if method == 2:
        # should be faster way, but about the same measuring tuck (method1) vs tuck.* (method2) both about 2 query time.  However, allowing regex here.
        if "*" in authorNamePartial or "?" in authorNamePartial or "." in authorNamePartial:
            results = solrAuthorTermSearch(terms_fl="art_author_id",
                                           terms_limit=limit,  # this causes many regex expressions to fail
                                           terms_regex=authorNamePartial + ".*",
                                           terms_sort=authorOrder  # index or count
                                           )           
        else:
            results = solrAuthorTermSearch(terms_fl="art_author_id",
                                           terms_prefix=authorNamePartial,
                                           terms_sort=authorOrder,  # index or count
                                           terms_limit=limit
                                           )

    
    responseInfo = models.ResponseInfo(
                                limit=limit,
                                offset=offset,
                                listType="authorindex",
                                scopeQuery="Terms: %s" % authorNamePartial,
                                solrParams=results._params,
                                timeStamp=datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')
    )
    
    authorIndexItems = []
    if method == 1:
        for key, value in results.facet_counts["facet_fields"]["art_author_id"].items():
            if value > 0:
                #retVal[key] = value
    
                item = models.AuthorIndexItem( authorID = key, 
                                        publicationsURL = "/v1/Authors/Publications/{}/".format(key),
                                        publicationsCount = value,
                                      ) 
                authorIndexItems.append(item)
                #debug status
                print ("authorsGetAuthorInfo", item)

    if method == 2:  # faster way
        for key, value in results.terms["art_author_id"].items():
            if value > 0:
                item = models.AuthorIndexItem( authorID = key, 
                                        publicationsURL = "/v1/Authors/Publications/{}/".format(key),
                                        publicationsCount = value,
                                      ) 
                authorIndexItems.append(item)
                #debug status
                print ("authorsGetAuthorInfo", item)
       
    responseInfo.count = len(authorIndexItems)
    responseInfo.fullCountComplete = limit >= responseInfo.count
        
    authorIndexStruct = models.AuthorIndexStruct( responseInfo = responseInfo, 
                                           responseSet = authorIndexItems
                                           )
    
    authorIndex = models.AuthorIndex(authorIndex = authorIndexStruct)
    
    retVal = authorIndex
    return retVal

#-----------------------------------------------------------------------------
def authorsGetAuthorPublications(authorNamePartial, limit=opasConfig.DEFAULT_LIMIT_FOR_SOLR_RETURNS, offset=0):
    """
    Returns a list of publications (per authors partial name), and the number of articles by that author.
    
    
    
    >>> resp = authorsGetAuthorPublications("Tuck")
    Number found: 0
    Query didn't work - art_author_id:/Tuck/
    trying again - art_author_id:/Tuck[ ]?.*/
    Number found: 72
    >>> resp = authorsGetAuthorPublications("Fonag")
    Number found: 0
    Query didn't work - art_author_id:/Fonag/
    trying again - art_author_id:/Fonag[ ]?.*/
    Number found: 134    
    >>> resp = authorsGetAuthorPublications("Levinson, Nadine A.")
    Number found: 8
    """
    retVal = {}
    query = "art_author_id:/{}/".format(authorNamePartial)
    # wildcard in case nothing found for #1
    results = solrAuthors.query(q = "{}".format(query),   
                                fields = "art_author_id, art_year_int, art_id, art_citeas_xml",
                                sort="art_author_id, art_year_int", sort_order="asc",
                                rows=limit, start=offset
                             )

    print ("authorsGetAuthorPublications: Number found: %s" % results._numFound)
    if results._numFound == 0:
        print ("authorsGetAuthorPublications Query didn't work - {}".format(query))
        query = "art_author_id:/{}[ ]?.*/".format(authorNamePartial)
        print ("authorsGetAuthorPublications trying again - {}".format(query))
        results = solrAuthors.query(q = "{}".format(query),  
                                    fields = "art_author_id, art_year_int, art_id, art_citeas_xml",
                                    sort="art_author_id, art_year_int", sort_order="asc",
                                    rows=limit, start=offset
                                 )
        print ("authorsGetAuthorPublications Number found: %s" % results._numFound)
        if results._numFound == 0:
            query = "art_author_id:/(.*[ ])?{}[ ]?.*/".format(authorNamePartial)
            print ("trying again - {}".format(query))
            results = solrAuthors.query(q = "{}".format(query),  
                                        fields = "art_author_id, art_year_int, art_id, art_citeas_xml",
                                        sort="art_author_id, art_year_int", sort_order="asc",
                                        rows=limit, start=offset
                                     )
    
    responseInfo = models.ResponseInfo(
                     count = len(results.results),
                     fullCount = results._numFound,
                     limit = limit,
                     offset = offset,
                     listType="authorpublist",
                     scopeQuery=query,
                     solrParams = results._params,
                     fullCountComplete = limit >= results._numFound,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )

    authorPubListItems = []
    for result in results.results:
        citeAs = result.get("art_citeas_xml", None)
        citeAs = forceStringReturnFromVariousReturnTypes(citeAs)
        
        item = models.AuthorPubListItem( authorID = result.get("art_author_id", None), 
                                  documentID = result.get("art_id", None),
                                  documentRefHTML = citeAs,
                                  documentRef = opasxmllib.xmlElemOrStrToText(citeAs, defaultReturn=""),
                                  documentURL = documentURL + result.get("art_id", None),
                                  year = result.get("art_year", None),
                                  score = result.get("score", 0)
                              ) 
        authorPubListItems.append(item)
        #debug status
        #print (item)
       
    responseInfo.count = len(authorPubListItems)
    
    authorPubListStruct = models.AuthorPubListStruct( responseInfo = responseInfo, 
                                           responseSet = authorPubListItems
                                           )
    
    authorPubList = models.AuthorPubListItem(authorPubList = authorPubListStruct)
    
    retVal = authorPubList
    return retVal

#-----------------------------------------------------------------------------
def getExcerptFromAbstractOrSummaryOrDocument(xmlAbstract, xmlSummary, xmlDocument):
   
    retVal = None
    # see if there's an abstract
    retVal = forceStringReturnFromVariousReturnTypes(xmlAbstract)
    if retVal is None:
        # try the summary
        retVal = forceStringReturnFromVariousReturnTypes(xmlSummary)
        if retVal is None:
            # get excerpt from the document
            if xmlDocument is None:
                # we fail.  Return None
                logger.warning("No excerpt can be found or generated.")
            else:
                # extract the first 10 paras
                retVal = forceStringReturnFromVariousReturnTypes(xmlDocument)
                retVal = opasxmllib.removeEncodingString(retVal)
                # deal with potentially broken XML excerpts
                parser = lxml.etree.XMLParser(encoding='utf-8', recover=True)                
                #root = etree.parse(StringIO(retVal), parser)
                root = etree.fromstring(retVal, parser)
                body = root.xpath("//*[self::h1 or self::p or self::p2 or self::pb]")
                retVal = ""
                count = 0
                for elem in body:
                    if elem.tag == "pb" or count > 10:
                        # we're done.
                        retVal = "%s%s%s" % ("<abs><unit type='excerpt'>", retVal, "</unit></abs>")
                        break
                    else:
                        retVal  += etree.tostring(elem, encoding='utf8').decode('utf8')

    return retVal
    
#-----------------------------------------------------------------------------
def documentsGetAbstracts(documentID, retFormat="TEXTONLY", authenticated=None, limit=opasConfig.DEFAULT_LIMIT_FOR_SOLR_RETURNS, offset=0):
    """
    Returns an abstract or summary for the specified document
    If part of a documentID is supplied, multiple abstracts will be returned.
    
    The endpoint reminds me that we should be using documentID instead of "art" for article perhaps.
      Not thrilled about the prospect of changing it, but probably the right thing to do.
      
    >>> abstracts = documentsGetAbstracts("IJP.075")
    10 document matches for getAbstracts
    >>> abstracts = documentsGetAbstracts("AIM.038.0279A")  # no abstract on this one
    1 document matches for getAbstracts
    >>> abstracts = documentsGetAbstracts("AIM.040.0311A")
    1 document matches for getAbstracts
      
    """
    retVal = None
    results = solrDocs.query(q = "art_id:%s*" % (documentID),  
                                fields = "art_id, art_pepsourcetitlefull, art_vol, art_year, art_citeas_xml, art_pgrg, art_title_xml, art_authors, abstracts_xml, summaries_xml, text_xml",
                                sort="art_year, art_pgrg", sort_order="asc",
                                rows=limit, start=offset
                             )
    
    matches = len(results.results)
    cwd = os.getcwd()    
    print ("GetAbstract: Current Directory {}".format(cwd))
    print ("%s document matches for getAbstracts" % matches)
    
    responseInfo = models.ResponseInfo(
                     count = len(results.results),
                     fullCount = results._numFound,
                     limit = limit,
                     offset = offset,
                     listType="documentlist",
                     fullCountComplete = limit >= results._numFound,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )
    
    documentItemList = []
    for result in results:
        if matches > 0:
            try:
                xmlAbstract = result["abstracts_xml"]
            except KeyError as e:
                xmlAbstract = None
                logger.info("No abstract for document ID: %s" % documentID)
        
            try:
                xmlSummary = result["summaries_xml"]
            except KeyError as e:
                xmlSummary = None
                logger.info("No summary for document ID: %s" % documentID)
        
            try:
                xmlDocument = result["text_xml"]
            except KeyError as e:
                xmlDocument = None
                logger.error("No content matched document ID for: %s" % documentID)

            authorIDs = result.get("art_authors", None)
            if authorIDs is None:
                authorMast = None
            else:
                authorMast = opasgenlib.deriveAuthorMast(authorIDs)

            pgRg = result.get("art_pgrg", None)
            pgStart, pgEnd = opasgenlib.pgRgSplitter(pgRg)
            
            sourceTitle = result.get("art_pepsourcetitlefull", None)
            title = result.get("art_title_xml", "")  # name is misleading, it's not xml.
            artYear = result.get("art_year", None)
            artVol = result.get("art_vol", None)

            citeAs = result.get("art_citeas_xml", None)
            citeAs = forceStringReturnFromVariousReturnTypes(citeAs)

            abstract = getExcerptFromAbstractOrSummaryOrDocument(xmlAbstract, xmlSummary, xmlDocument)
            if abstract == "[]":
                abstract = None
            elif retFormat == "TEXTONLY":
                abstract = opasxmllib.xmlElemOrStrToText(abstract)
            elif retFormat == "HTML":
                abstractHTML = opasxmllib.convertXMLStringToHTML(abstract)
                abstract = extractHTMLFragment(abstractHTML, "//div[@id='abs']")

            abstract = opasxmllib.addHeadingsToAbstractHTML(abstract=abstract, 
                                                                sourceTitle=sourceTitle,
                                                                pubYear=artYear,
                                                                vol=artVol, 
                                                                pgRg=pgRg, 
                                                                citeas=citeAs, 
                                                                title=title,
                                                                authorMast=authorMast )

            item = models.DocumentListItem(year = artYear,
                                    vol = artVol,
                                    sourceTitle = sourceTitle,
                                    pgRg = pgRg,
                                    pgStart = pgStart,
                                    pgEnd = pgEnd,
                                    authorMast = authorMast,
                                    documentID = result.get("art_id", None),
                                    documentRefHTML = citeAs,
                                    documentRef = opasxmllib.xmlElemOrStrToText(citeAs, defaultReturn=""),
                                    accessLimited = authenticated,
                                    abstract = abstract,
                                    score = result.get("score", None)
                                    )
        
            #print (item)
            documentItemList.append(item)

    responseInfo.count = len(documentItemList)
    
    documentListStruct = models.DocumentListStruct( responseInfo = responseInfo, 
                                             responseSet=documentItemList
                                             )
    
    documents = models.Documents(documents = documentListStruct)
        
    retVal = documents
            
                
    return retVal


#-----------------------------------------------------------------------------
def documentsGetDocument(documentID, solrQueryParams=None, retFormat="XML", authenticated=True, limit=opasConfig.DEFAULT_LIMIT_FOR_DOCUMENT_RETURNS, offset=0):
    """
   For non-authenticated users, this endpoint returns only Document summary information (summary/abstract)
   For authenticated users, it returns with the document itself
   
    >> resp = documentsGetDocument("AIM.038.0279A", retFormat="html") 
    
    >> resp = documentsGetDocument("AIM.038.0279A") 
    
    >> resp = documentsGetDocument("AIM.040.0311A")
    

    """
    retVal = {}
    
    if not authenticated:
        #if user is not authenticated, effectively do endpoint for getDocumentAbstracts
        print ("documentsGetDocument: User not authenticated...fetching abstracts instead")
        retVal = documentListStruct = documentsGetAbstracts(documentID, authenticated=authenticated, limit=1)
        return retVal

    if solrQueryParams is not None:
        # repeat the query that the user had done when retrieving the document
        query = "art_id:{} && {}".format(documentID, solrQueryParams.searchQ)
        documentList = searchText(query, 
                                  filterQuery = solrQueryParams.filterQ,
                                  fullTextRequested=True,
                                  fullTextFormatRequested = retFormat,
                                  authenticated=authenticated,
                                  queryDebug = False,
                                  disMax = solrQueryParams.solrMax,
                                  limit=limit, 
                                  offset=offset
                                  )
    
    if documentList == None or documentList.documentList.responseInfo.count == 0:
        #sometimes the query is still sent back, even though the document was an independent selection.  So treat it as a simple doc fetch
        
        query = "art_id:{}".format(documentID)
        #summaryFields = "art_id, art_vol, art_year, art_citeas_xml, art_pgrg, art_title, art_author_id, abstracts_xml, summaries_xml, text_xml"
       
        documentList = searchText(query, 
                                  fullTextRequested=True,
                                  fullTextFormatRequested = retFormat,
                                  authenticated=authenticated,
                                  queryDebug = False,
                                  limit=limit, 
                                  offset=offset
                                  )

    try:
        matches = documentList.documentList.responseInfo.count
        fullCount = documentList.documentList.responseInfo.fullCount
        fullCountComplete = documentList.documentList.responseInfo.fullCountComplete
        documentListItem = documentList.documentList.responseSet[0]
        print ("documentsGetDocument %s document matches" % matches)
    except Exception as e:
        print ("No matches or error: {}").format(e)
    else:
        responseInfo = models.ResponseInfo(
                         count = matches,
                         fullCount = fullCount,
                         limit = limit,
                         offset = offset,
                         listType="documentlist",
                         fullCountComplete = fullCountComplete,
                         timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                       )
        
        if matches >= 1:       
            documentListStruct = models.DocumentListStruct( responseInfo = responseInfo, 
                                                            responseSet = [documentListItem]
                                                            )
                
            documents = models.Documents(documents = documentListStruct)
                    
            retVal = documents
    
    return retVal

#-----------------------------------------------------------------------------
def documentsGetGlossaryEntry(termID, solrQueryParams=None, retFormat="XML", authenticated=True, limit=opasConfig.DEFAULT_LIMIT_FOR_DOCUMENT_RETURNS, offset=0):
    """
   For non-authenticated users, this endpoint should return an error (#TODO)
   
   For authenticated users, it returns with the glossary itself
   
   IMPORTANT NOTE: At least the way the database is currently populated, for a group, the textual part (text) is the complete group, 
      and thus the same for all entries.  This is best for PEP-Easy now, otherwise, it would need to concatenate all the result entries.
   
    >> resp = documentsGetGlossaryEntry("ZBK.069.0001o.YN0019667860580", retFormat="html") 
    
    >> resp = documentsGetGlossaryEntry("ZBK.069.0001o.YN0004676559070") 
    
    >> resp = documentsGetGlossaryEntry("ZBK.069.0001e.YN0005656557260")
    

    """
    retVal = {}
    termID = termID.upper()
    
    if not authenticated:
        #if user is not authenticated, effectively do endpoint for getDocumentAbstracts
        documentsGetAbstracts(termID, limit=1)
    else:
        results = solrGloss.query(q = f"term_id:{termID} || group_id:{termID}",  
                                 fields = "term_id, group_id, term_type, term_source, group_term_count, art_id, text"
                                )
        documentItemList = []
        count = 0
        try:
            for result in results:
                try:
                    document = result.get("text", None)
                    if retFormat == "HTML":
                        document = opasxmllib.convertXMLStringToHTML(document)
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
                    documentItemList.append(item)
                    count = len(documentItemList)

        except IndexError as e:
            logger.warning("No matching glossary entry for %s.  Error: %s" % (termID, e))
        except KeyError as e:
            logger.warning("No content or abstract found for %s.  Error: %s" % (termID, e))
        else:
            responseInfo = models.ResponseInfo(
                             count = count,
                             fullCount = count,
                             limit = limit,
                             offset = offset,
                             listType="documentlist",
                             fullCountComplete = True,
                             timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                           )
            
            documentListStruct = models.DocumentListStruct( responseInfo = responseInfo, 
                                                            responseSet = documentItemList
                                                            )
                
            documents = models.Documents(documents = documentListStruct)
                        
            retVal = documents
        
        return retVal

#-----------------------------------------------------------------------------
def prepDocumentDownload(documentID, retFormat="HTML", authenticated=True, baseFilename="opasDoc"):
    """
   For non-authenticated users, this endpoint returns only Document summary information (summary/abstract)
   For authenticated users, it returns with the document itself
   
    >>> prepDocumentDownload("IJP.051.0175A", retFormat="html") 
    
    >> prepDocumentDownload("IJP.051.0175A", retFormat="epub") 
    

    """
    def addEPUBElements(str):
        # for now, just return
        return str
        
    retVal = {}
    
    if not authenticated:
        #if user is not authenticated, effectively do endpoint for getDocumentAbstracts
        documentsGetAbstracts(documentID, limit=1)
    else:
        results = solrDocs.query(q = "art_id:%s" % (documentID),  
                                    fields = "art_id, art_citeas_xml, text_xml"
                                 )
        try:
            retVal = results.results[0]["text_xml"]
        except IndexError as e:
            logger.warning("No matching document for %s.  Error: %s" % (documentID, e))
        except KeyError as e:
            logger.warning("No content or abstract found for %s.  Error: %s" % (documentID, e))
        else:
            try:    
                if isinstance(retVal, list):
                    retVal = retVal[0]
            except Exception as e:
                logger.warning("Empty return: %s" % e)
            else:
                try:    
                    if retFormat.lower() == "html":
                        retVal = opasxmllib.removeEncodingString(retVal)
                        filename = convertXMLToHTMLFile(retVal, outputFilename=documentID + ".html")  # returns filename
                        retVal = filename
                    elif retFormat.lower() == "epub":
                        retVal = opasxmllib.removeEncodingString(retVal)
                        htmlString = opasxmllib.convertXMLStringToHTML(retVal)
                        htmlString = addEPUBElements(htmlString)
                        filename = opasxmllib.convertHTMLToEPUB(htmlString, documentID, documentID)
                        retVal = filename
                        
                except Exception as e:
                    logger.warning("Can't convert data: %s" % e)
        
    return retVal

#-----------------------------------------------------------------------------
def convertXMLToHTMLFile(xmlTextStr, xsltFile=r"./styles/pepkbd3-html.xslt", outputFilename=None):
    if outputFilename is None:
        basename = "opasDoc"
        suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        filenameBase = "_".join([basename, suffix]) # e.g. 'mylogfile_120508_171442'        
        outputFilename = filenameBase + ".html"

    htmlString = opasxmllib.convertXMLStringToHTML(xmlTextStr, xsltFile=xsltFile)
    fo = open(outputFilename, "w")
    fo.write(str(htmlString))
    fo.close()
    
    return outputFilename

#-----------------------------------------------------------------------------
def getImageBinary(imageID):
    """
    Return a binary object of the image, e.g.,
   
    >>> getImageBinary("NOTEXISTS.032.0329A.F0003g")

    >>> getImageBinary("AIM.036.0275A.FIG001")

    >>> getImageBinary("JCPTX.032.0329A.F0003g")
    
    Note: the current server requires the extension, but it should not.  The server should check
    for the file per the following extension hierarchy: .jpg then .gif then .tif
    
    However, if the extension is supplied, that should be accepted.

    The current API implements this:
    
    curl -X GET "http://stage.pep.gvpi.net/api/v1/Documents/Downloads/Images/aim.036.0275a.fig001.jpg" -H "accept: image/jpeg" -H "Authorization: Basic cC5lLnAuYS5OZWlsUlNoYXBpcm86amFDayFsZWdhcmQhNQ=="
    
    and returns a binary object.  
        
    """
    def getImageFilename(imageID):
        imageSourcePath = "X:\_PEPA1\g"
        ext = os.path.splitext(imageSourcePath)[-1].lower()
        if ext in (".jpg", ".tif", ".gif"):
            imageFilename = os.path.join(imageSourcePath, imageID)
            exists = os.path.isfile(imageFilename)
            if not exists:
                imageFilename = None
        else:
            imageFilename = os.path.join(imageSourcePath, imageID + ".jpg")
            exists = os.path.isfile(imageFilename)
            if not exists:
                imageFilename = os.path.join(imageSourcePath, imageID + ".gif")
                exists = os.path.isfile(imageFilename)
                if not exists:
                    imageFilename = os.path.join(imageSourcePath, imageID + ".tif")
                    exists = os.path.isfile(imageFilename)
                    if not exists:
                        imageFilename = None

        return imageFilename
    
    # these won't be in the Solr database, needs to be brought back by a file
    # the file ID should match a file name
    retVal = None
    imageFilename = getImageFilename(imageID)
    if imageFilename is not None:
        try:
            f = open(imageFilename, "rb")
            imageBytes = f.read()
            f.close()    
        except OSError as e:
            print ("getImageBinary: File Open Error: %s", e)
        except Exception as e:
            print ("getImageBinary: Error: %s", e)
        else:
            retVal = imageBytes
    else:
        logger.warning("Image File ID %s not found", imageID)
  
    return retVal

#-----------------------------------------------------------------------------
def getKwicList(markedUpText, 
                extraContextLen=opasConfig.DEFAULT_KWIC_CONTENT_LENGTH, 
                solrStartHitTag=opasConfig.HITMARKERSTART, # supply whatever the start marker that solr was told to use
                solrEndHitTag=opasConfig.HITMARKEREND,     # supply whatever the end marker that solr was told to use
                outputStartHitTagMarker=opasConfig.HITMARKERSTART_OUTPUTHTML, # the default output marker, in HTML
                outputEndHitTagMarker=opasConfig.HITMARKEREND_OUTPUTHTML,
                limit=opasConfig.DEFAULT_MAX_KWIC_RETURNS):
    """
    Find all nonoverlapping matches, using Solr's return.  Limit the number.
    """
    
    retVal = []
    emMarks = re.compile("(.{0,%s}%s.*%s.{0,%s})" % (extraContextLen, solrStartHitTag, solrEndHitTag, extraContextLen))
    markedUp = re.compile(".*(%s.*%s).*" % (solrStartHitTag, solrEndHitTag))
    markedUpText = opasxmllib.xmlStringToText(markedUpText) # remove markup except match tags which shouldn't be XML

    matchTextPattern = "({{.*?}})"
    patCompiled = re.compile(matchTextPattern)
    wordList = patCompiled.split(markedUpText) # split all the words
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
                textBeforeWords = textBefore.split(" ")[-extraContextLen:]
                textBeforePhrase = " ".join(textBeforeWords)
            except:
                textBefore = ""
            try:
                textAfter = wordList[index+1]
                textAfterWords = textAfter.split(" ")[:extraContextLen]
                textAfterPhrase = " ".join(textAfterWords)
                if patCompiled.search(textAfterPhrase):
                    skipNext = True
            except:
                textAfter = ""

            # change the tags the user told Solr to use to the final output tags they want
            #   this is done to use non-xml-html hit tags, then convert to that after stripping the other xml-html tags
            match = re.sub(solrStartHitTag, outputStartHitTagMarker, n)
            match = re.sub(solrEndHitTag, outputEndHitTagMarker, match)

            contextPhrase = textBeforePhrase + match + textAfterPhrase

            retVal.append(contextPhrase)

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
        
    matchCount = len(retVal)
    
    return retVal    


#-----------------------------------------------------------------------------
def getKwicListOld(markedUpText, extraContextLen=opasConfig.DEFAULT_KWIC_CONTENT_LENGTH, 
                solrStartHitTag=opasConfig.HITMARKERSTART, # supply whatever the start marker that solr was told to use
                solrEndHitTag=opasConfig.HITMARKEREND,     # supply whatever the end marker that solr was told to use
                outputStartHitTagMarker=opasConfig.HITMARKERSTART_OUTPUTHTML, # the default output marker, in HTML
                outputEndHitTagMarker=opasConfig.HITMARKEREND_OUTPUTHTML,
                limit=opasConfig.DEFAULT_MAX_KWIC_RETURNS):
    """
    Find all nonoverlapping matches, using Solr's return.  Limit the number.
    """
    
    retVal = []
    emMarks = re.compile("(.{0,%s}%s.*%s.{0,%s})" % (extraContextLen, solrStartHitTag, solrEndHitTag, extraContextLen))
    count = 0
    for n in emMarks.finditer(markedUpText):
        count += 1
        match = n.group(0)
        try:
            # strip xml
            match = opasxmllib.xmlStringToText(match)
            # change the tags the user told Solr to use to the final output tags they want
            #   this is done to use non-xml-html hit tags, then convert to that after stripping the other xml-html tags
            match = re.sub(solrStartHitTag, outputStartHitTagMarker, match)
            match = re.sub(solrEndHitTag, outputEndHitTagMarker, match)
        except Exception as e:
            logging.error("Error stripping xml from kwic entry {}".format(e))
               
        retVal.append(match)
        try:
            logger.info("getKwicList Match: '...{}...'".format(match))
            print ("getKwicListMatch: '...{}...'".format(match))
        except Exception as e:
            print ("getKwicList Error printing or logging matches. {}".format(e))
        if count >= limit:
            break
        
    matchCount = len(retVal)
    
    return retVal    

#-----------------------------------------------------------------------------
def yearArgParser(yearArg):
    retVal = None
    yearQuery = re.match("[ ]*(?P<option>[\>\^\<\=])?[ ]*(?P<start>[12][0-9]{3,3})?[ ]*(?P<separator>([-]|TO))*[ ]*(?P<end>[12][0-9]{3,3})?[ ]*", yearArg, re.IGNORECASE)            
    if yearQuery is None:
        logger.warning("Search - StartYear bad argument {}".format(yearArg))
    else:
        option = yearQuery.group("option")
        start = yearQuery.group("start")
        end = yearQuery.group("end")
        separator = yearQuery.group("separator")
        if start is None and end is None:
            logger.warning("Search - StartYear bad argument {}".format(yearArg))
        else:
            if option == "^":
                # between
                # find endyear by parsing
                if start is None:
                    start = end # they put > in start rather than end.
                elif end is None:
                    end = start # they put < in start rather than end.
                searchClause = "&& art_year_int:[{} TO {}] ".format(start, end)
            elif option == ">":
                # greater
                if start is None:
                    start = end # they put > in start rather than end.
                searchClause = "&& art_year_int:[{} TO {}] ".format(start, "*")
            elif option == "<":
                # less than
                if end is None:
                    end = start # they put < in start rather than end.
                searchClause = "&& art_year_int:[{} TO {}] ".format("*", end)
            else: # on
                if start is not None and end is not None:
                    # they specified a range anyway
                    searchClause = "&& art_year_int:[{} TO {}] ".format(start, end)
                elif start is None and end is not None:
                    # they specified '- endyear' without the start, so less than
                    searchClause = "&& art_year_int:[{} TO {}] ".format("*", end)
                elif start is not None and separator is not None:
                    # they mean greater than
                    searchClause = "&& art_year_int:[{} TO {}] ".format(start, "*")
                else: # they mean on
                    searchClause = "&& art_year_int:{} ".format(yearArg)

            retVal = searchClause

    return retVal
                        
#-----------------------------------------------------------------------------
def searchAnalysis(queryList, 
                   filterQuery = None,
                   moreLikeThese = False,
                   queryAnalysis = False,
                   disMax = None,
                   #summaryFields="art_id, art_pepsrccode, art_vol, art_year, art_iss, art_iss_title, art_newsecnm, art_pgrg, art_title, art_author_id, art_citeas_xml", 
                   summaryFields="art_id",                    
                   #highlightFields='art_title_xml, abstracts_xml, summaries_xml, art_authors_xml, text_xml', 
                   fullTextRequested=False, 
                   userLoggedIn=False,
                   limit=opasConfig.DEFAULT_MAX_KWIC_RETURNS
                   ):
    """
    Analyze the search clauses in the query list
	"""
    retVal = {}
    documentItemList = []
    rowCount = 0
    for n in queryList:
        n = n[3:]
        n = n.strip(" ")
        if n == "" or n is None:
            continue

        results = solrDocs.query(n,
                                 disMax = disMax,
                                 queryAnalysis = True,
                                 fields = summaryFields,
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
        documentItemList.append(item)
        rowCount += 1

    if rowCount > 0:
        numFound = 0
        item = models.DocumentListItem(term = "combined",
                                termCount = numFound
                                )
        documentItemList.append(item)
        rowCount += 1
        print ("Analysis: Term %s, matches %s" % ("combined: ", numFound))

    responseInfo = models.ResponseInfo(count = rowCount,
                                fullCount = rowCount,
                                listType="srclist",
                                fullCountComplete = True,
                                timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                                )
    
    responseInfo.count = len(documentItemList)
    
    documentListStruct = models.DocumentListStruct( responseInfo = responseInfo, 
                                             responseSet = documentItemList
                                             )
    
    retVal = documentList = models.DocumentList(documentList = documentListStruct)
    
    return retVal

#================================================================================================================
# SEARCHTEXT
#================================================================================================================
def searchText(query, 
               filterQuery = None,
               queryDebug = False,
               moreLikeThese = False,
               fullTextRequested = False, 
               fullTextFormatRequested = "HTML",
               disMax = None,
               # bring text_xml back in summary fields in case it's missing in highlights! I documented a case where this happens!
               #summaryFields = "art_id, art_pepsrccode, art_vol, art_year, art_iss, art_iss_title, art_newsecnm, art_pgrg, art_title, art_author_id, art_citeas_xml, text_xml", 
               #highlightFields = 'art_title_xml, abstracts_xml, summaries_xml, art_authors_xml, text_xml', 
               summaryFields = "art_id, art_pepsrccode, art_vol, art_year, art_iss, art_iss_title, art_newsecnm, art_pgrg, abstracts_xml, art_title, art_author_id, art_citeas_xml, text_xml", 
               highlightFields = 'text_xml', 
               sortBy="score desc",
               authenticated = None, 
               extraContextLen = opasConfig.DEFAULT_KWIC_CONTENT_LENGTH,
               maxKWICReturns = opasConfig.DEFAULT_MAX_KWIC_RETURNS,
               limit=opasConfig.DEFAULT_LIMIT_FOR_SOLR_RETURNS, 
               offset=0):
    """
    Full-text search

    >>> searchText(query="art_title_xml:'ego identity'", limit=10, offset=0, fullTextRequested=False)
    
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
    retVal = {}
    
    if moreLikeThese:
        mlt_fl = "text_xml, headings_xml, terms_xml, references_xml"
        mlt = "true"
        mlt_minwl = 8
    else:
        mlt_fl = None
        mlt = "false"
        mlt_minwl = None
    
    if queryDebug:
        queryDebug = "on"
    else:
        queryDebug = "off"
        
    if fullTextRequested:
        fragSize = opasConfig.SOLR_HIGHLIGHT_RETURN_FRAGMENT_SIZE 
    else:
        fragSize = extraContextLen

    try:
        results = solrDocs.query(query,  
                                 fq = filterQuery,
                                 debugQuery = queryDebug,
                                 disMax = disMax,
                                 fields = summaryFields,
                                 hl='true', 
                                 hl_fragsize = fragSize, 
                                 hl_multiterm='true',
                                 hl_fl = highlightFields,
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
                                 sort=sortBy,
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
                         timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                       )
    
    
        documentItemList = []
        rowCount = 0
        rowOffset = 0
        # if we're not authenticated, then turn off the full-text request and behave as if we didn't try
        if not authenticated:
            if fullTextRequested:
                logger.warning("Fulltext requested--by API--but not authenticated.")
    
            fullTextRequested = False
            
        for result in results.results:
            authorIDs = result.get("art_author_id", None)
            if authorIDs is None:
                authorMast = None
            else:
                authorMast = opasgenlib.deriveAuthorMast(authorIDs)
    
            pgRg = result.get("art_pgrg", None)
            if pgRg is not None:
                pgStart, pgEnd = opasgenlib.pgRgSplitter(pgRg)
                
            documentID = result.get("art_id", None)        
            textXml = results.highlighting[documentID].get("text_xml", None)
            # no kwic list when full-text is requested.
            if textXml is not None and not fullTextRequested:
                #kwicList = getKwicList(textXml, extraContextLen=extraContextLen)  # returning context matches as a list, making it easier for clients to work with
                kwicList = []
                for n in textXml:
                    # strip all tags
                    match = opasxmllib.xmlStringToText(n)
                    # change the tags the user told Solr to use to the final output tags they want
                    #   this is done to use non-xml-html hit tags, then convert to that after stripping the other xml-html tags
                    match = re.sub(opasConfig.HITMARKERSTART, opasConfig.HITMARKERSTART_OUTPUTHTML, match)
                    match = re.sub(opasConfig.HITMARKEREND, opasConfig.HITMARKEREND_OUTPUTHTML, match)
                    kwicList.append(match)
                    
                kwic = " . . . ".join(kwicList)  # how its done at GVPi, for compatibility (as used by PEPEasy)
                textXml = None
                #print ("Document Length: {}; Matches to show: {}".format(len(textXml), len(kwicList)))
            else: # either fulltext requested, or no document
                kwicList = []
                kwic = ""  # this has to be "" for PEP-Easy, or it hits an object error.  
            
            if fullTextRequested:
                fullText = result.get("text_xml", None)
                textXml = forceStringReturnFromVariousReturnTypes(textXml)
                if textXml is None:  # no highlights, so get it from the main area
                    try:
                        textXml = fullText
                    except:
                        textXml = None
                elif len(fullText) > len(textXml):
                    print ("Warning: text with highlighting is smaller than full-text area.  Returning without hit highlighting.")
                    textXml = fullText
                    
                if fullTextFormatRequested == "HTML":
                    if textXml is not None:
                        textXml = opasxmllib.convertXMLStringToHTML(textXml, xsltFile=r"./styles/pepkbd3-html.xslt")
    
            if fullTextRequested and not authenticated: # don't do this when textXml is a fragment from kwiclist!
                try:
                    abstractsXml = results.highlighting[documentID].get("abstracts_xml", None)
                    abstractsXml  = forceStringReturnFromVariousReturnTypes(abstractsXml )
                    summariesXml = results.highlighting[documentID].get("abstracts_xml", None)
                    summariesXml  = forceStringReturnFromVariousReturnTypes(summariesXml)
                    textXml = getExcerptFromAbstractOrSummaryOrDocument(xmlAbstract=abstractsXml, xmlSummary=summariesXml, xmlDocument=textXml)
                except:
                    textXml = None
    
            citeAs = result.get("art_citeas_xml", None)
            citeAs = forceStringReturnFromVariousReturnTypes(citeAs)
            
            if moreLikeThese:
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
                                        documentRef = opasxmllib.xmlElemOrStrToText(citeAs, defaultReturn=""),
                                        kwic = kwic,
                                        kwicList = kwicList,
                                        title = result.get("art_title", None),
                                        abstract = forceStringReturnFromVariousReturnTypes(result.get("abstracts_xml", None)), # these were highlight versions, not needed
                                        document = textXml,
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
        
        retVal = documentList
    
    return retVal

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
        morsel['expires'] = opasgenlib.format_http_timestamp(expires)
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
    getListOfMostDownloaded()
    sys.exit()
    
    import doctest
    doctest.testmod()    
    main()
