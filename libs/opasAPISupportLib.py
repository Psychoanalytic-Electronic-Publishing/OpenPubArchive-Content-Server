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
__version__     = "2019.0709.1"
__status__      = "Development"

import sys
sys.path.append('../libs')
sys.path.append('../config')
from typing import Union, Optional, Tuple
import http.cookies

import opasConfig
from opasConfig import *
from localsecrets import SOLRURL, SOLRUSER, SOLRPW, DEBUG_DOCUMENTS, CONFIG
from starlette.requests import Request
from starlette.responses import Response

import re
import os.path
import secrets
from starlette.responses import JSONResponse, Response

import time
import datetime
from datetime import datetime, timedelta
from typing import List
from enum import Enum
import pymysql

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

from stdMessageLib import copyrightPageHTML  # copyright page text to be inserted in ePubs and PDFs

# note: documents and documentList share the same internals, except the first level json label (documents vs documentlist)
import models
from models import ListTypeEnum, \
                   ResponseInfo, \
                   DocumentList, \
                   Documents, \
                   DocumentListStruct, \
                   DocumentListItem, \
                   ImageURLList, \
                   ImageURLListStruct, \
                   ImageURLListItem, \
                   SourceInfoList, \
                   SourceInfoStruct, \
                   SourceInfoListItem, \
                   VolumeList, \
                   VolumeListStruct, \
                   VolumeListItem, \
                   WhatsNewList, \
                   WhatsNewListStruct, \
                   WhatsNewListItem, \
                   AuthorPubListStruct, \
                   AuthorPubListItem, \
                   AuthorPubList, \
                   AuthorIndex, \
                   AuthorIndexStruct, \
                   AuthorIndexItem, \
                   LoginReturnItem, \
                   SearchFormFields

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

else:
    solrDocs = solr.SolrConnection(SOLRURL + 'pepwebdocs')
    solrRefs = solr.SolrConnection(SOLRURL + 'pepwebrefs')
    solrGloss = solr.SolrConnection(SOLRURL + 'pepwebglossary')
    solrAuthors = solr.SolrConnection(SOLRURL + 'pepwebauthors')

#API endpoints
documentURL = "/v1/Documents/"

def getMaxAge(keepActive=False):
    if keepActive:    
        retVal = opasConfig.COOKIE_MAX_KEEP_TIME    
    else:
        retVal = opasConfig.COOKIE_MIN_KEEP_TIME     
    return retVal  # maxAge

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
        #sessionInfo = models.SessionInfo(session_id = sessionID, 
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
    
    print (sessionInfo)
    return ocd, sessionInfo
    
def extractHTMLFragment(strHTML, xpathToExtract="//div[@id='abs']"):
    # parse HTML
    htree = etree.HTML(strHTML)
    retVal = htree.xpath(xpathToExtract)
    # make sure it's a string
    retVal = forceStringReturnFromVariousReturnTypes(retVal)
    
    return retVal

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
                                              userIP=request.client.host, 
                                              connectedVia=request.headers["user-agent"],
                                              accessToken = accessToken
                                              )
    else:
        username="NotLoggedIn"
        retVal, sessionInfo = ocd.saveSession(sessionID, 
                                              userID=0,
                                              userIP=request.client.host, 
                                              connectedVia=request.headers["user-agent"],
                                              username=username)  # returns save status and a session object (matching what was sent to the db)

    # return the object so the caller can get the details of the session
    return ocd, sessionInfo

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
    
def parseCookiesFromHeader(request):
    retVal = {}
    clientSuppliedCookies = request.headers.get("cookie", None)
    if clientSuppliedCookies is not None:
        cookieStatements = clientSuppliedCookies.split(";")
        for n in cookieStatements:
            cookie, value = n.split("=")
            retVal[cookie] = value

    return retVal

def getSessionID(request):
    sessionCookieName = "opasSessionID"
    retVal = request.cookies.get(sessionCookieName, None)
    
    if retVal is None:
        cookieDict = parseCookiesFromHeader(request)
        retVal = cookieDict.get(sessionCookieName, None)
        if retVal is not None:
            print ("Session cookie had to be retrieved from header: {}".format(retVal))
    else:
        print ("Session cookie from client: {}".format(retVal))
    return retVal

def getAccessToken(request):
    retVal = request.cookies.get("opasAccessToken", None)
    return retVal

def getExpirationTime(request):
    retVal = request.cookies.get("opasSessionExpirestime", None)
    return retVal

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
            print ("ERROR: %s" % type(retVal))

        try:
            if isinstance(retVal, lxml.etree._Element):
                retVal = etree.tostring(retVal)
            
            if isinstance(retVal, bytes) or isinstance(retVal, bytearray):
                logger.error("Byte Data")
                retVal = retVal.decode("utf8")
        except Exception as e:
            err = "Error forcing conversion to string: %s / %s" % (type(retVal), e)
            logger.error(err)
            print (err)
            
    return retVal        
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
    responseInfo = ResponseInfo(
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
            item = DocumentListItem(PEPCode = result.get("art_pepsrccode", None), 
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
    
    documentListStruct = DocumentListStruct( responseInfo = responseInfo, 
                                             responseSet = documentItemList
                                             )
    
    documentList = DocumentList(documentList = documentListStruct)
    
    retVal = documentList
    
    return retVal

def databaseGetMostCited(period='5', limit=50, offset=0):
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
                             fl = "art_id, title, art_vol, art_iss, art_year,  art_pepsrccode, \
                                   art_cited_{}, art_cited_all, timestamp, art_pepsrccode, \
                                   art_pepsourcetype, art_pepsourcetitleabbr, art_pgrg, art_citeas_xml, art_authors_mast, \
                                   abstract_xml, text_xml".format(period),
                             fq = "art_pepsourcetype: journal",
                             sort = "art_cited_{} desc".format(period),
                             limit = limit
                             )

    print ("Number found: %s" % results._numFound)
    
    responseInfo = ResponseInfo(
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
        
        item = DocumentListItem( documentID = result.get("art_id", None),
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
    
    documentListStruct = DocumentListStruct( responseInfo = responseInfo, 
                                             responseSet = documentListItems
                                             )
    
    documentList = DocumentList(documentList = documentListStruct)
    
    retVal = documentList
    
    return retVal   

def databaseWhatsNew(limit=DEFAULT_LIMIT_FOR_WHATS_NEW, offset=0):
    """
    Return a what's been updated in the last week
    
    >>> result = databaseWhatsNew()
    Number found: 91
    """    
    results = solrDocs.query(q = "timestamp:[NOW-7DAYS TO NOW]",  
                             fl = "art_id, title, art_vol, art_iss, art_pepsrccode, timestamp, art_pepsourcetype",
                             fq = "{!collapse field=art_pepsrccode max=art_year_int}",
                             sort="timestamp", sort_order="desc",
                             rows=150, offset=0,
                             )
    
    print ("Number found: %s" % results._numFound)
    
    responseInfo = ResponseInfo(
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
        displayTitle = abbrev + " v%s.%s (%s) (Added: %s)" % (volume, issue, year, updated)
        if displayTitle in alreadySeen:
            continue
        else:
            alreadySeen.append(displayTitle)
        volumeURL = "/v1/Metadata/Contents/%s/%s" % (PEPCode, issue)
        srcTitle = sourceDB.sourceData[PEPCode].get("sourcetitlefull", "")
            
        item = WhatsNewListItem( documentID = result.get("art_id", None),
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
    
    whatsNewListStruct = WhatsNewListStruct( responseInfo = responseInfo, 
                                             responseSet = whatsNewListItems
                                             )
    
    whatsNewList = WhatsNewList(whatsNew = whatsNewListStruct)
    
    retVal = whatsNewList
    
    return retVal   

def searchLikeThePEPAPI():
    pass  # later

def metadataGetVolumes(pepCode, year="*", limit=DEFAULT_LIMIT_FOR_VOLUME_LISTS, offset=0):
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

    print ("Number found: %s" % results._numFound)
    responseInfo = ResponseInfo(
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
        item = VolumeListItem(PEPCode = pepCode, 
                              year = result.get("art_year", None),
                              vol = result.get("art_vol", None),
                              score = result.get("score", None)
                             )
    
        #print (item)
        volumeItemList.append(item)
       
    responseInfo.count = len(volumeItemList)
    
    volumeListStruct = VolumeListStruct( responseInfo = responseInfo, 
                                         responseSet = volumeItemList
                                         )
    
    volumeList = VolumeList(volumeList = volumeListStruct)
    
    retVal = volumeList
    return retVal

def metadataGetContents(pepCode, year="*", vol="*", limit=DEFAULT_LIMIT_FOR_CONTENTS_LISTS, offset=0):
    """
    Return a jounals contents
    
    >>> metadataGetContents("IJP", "1993", limit=5, offset=0)
    <DocumentList documentList=<DocumentListStruct responseInfo=<ResponseInfo count=5 limit=5 offset=0 page=No…>
    >>> metadataGetContents("IJP", "1993", limit=5, offset=5)
    <DocumentList documentList=<DocumentListStruct responseInfo=<ResponseInfo count=5 limit=5 offset=5 page=No…>
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

    responseInfo = ResponseInfo(
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
        
        item = DocumentListItem(PEPCode = pepCode, 
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
    
    documentListStruct = DocumentListStruct( responseInfo = responseInfo, 
                                             responseSet=documentItemList
                                             )
    
    documentList = DocumentList(documentList = documentListStruct)
    
    retVal = documentList
    
    return retVal

def metadataGetSourceByType(sourceType=None, limit=DEFAULT_LIMIT_FOR_SOLR_RETURNS, offset=0):
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
    # standardize Source type, allow plural, different cases, but code below this part accepts only those three.
    sourceType = sourceType.lower()
    if sourceType not in ["journal", "book", "video"]:
        if re.match("vid.*", sourceType, re.IGNORECASE):
            sourceType = "video"
        elif re.match("boo.*", sourceType, re.IGNORECASE):
            sourceType = "book"
        else: # default
            sourceType = "journal"
            
    for sourceInfoDict in sourceDB.sourceData.values():
        if sourceInfoDict["pep_class"] == sourceType:
            # match
            sourceInfoDBList.append(sourceInfoDict)
    
    count = len(sourceInfoDBList)
    print ("Number found: %s" % count)

    responseInfo = ResponseInfo(
                     count = count,
                     fullCount = count,
                     limit = limit,
                     offset = offset,
                     listLabel = "{} List".format(sourceType),
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
            item = SourceInfoListItem( ISSN = source.get("ISSN"),
                                       PEPCode = source.get("pepsrccode"),
                                       abbrev = source.get("sourcetitleabbr"),
                                       bannerURL = "http://{}/{}/banner{}.logo.gif".format(opasConfig.BASEURL, opasConfig.IMAGES, source.get("pepsrccode")),
                                       displayTitle = source.get("sourcetitlefull"),
                                       language = source.get("language"),
                                       yearFirst = source.get("start_year"),
                                       yearLast = source.get("end_year"),
                                       sourceType = sourceType,
                                       title = source.get("pepsrccode")
                                       ) 
        except ValidationError as e:
            print ("SourceInfoListItem Validation Error:")
            print(e.json())        

        sourceInfoListItems.append(item)
        
    try:
        sourceInfoStruct = SourceInfoStruct( responseInfo = responseInfo, 
                                             responseSet = sourceInfoListItems
                                            )
    except ValidationError as e:
        print ("SourceInfoStruct Validation Error:")
        print(e.json())        
    
    try:
        sourceInfoList = SourceInfoList(sourceInfo = sourceInfoStruct)
    except ValidationError as e:
        print ("SourceInfoList Validation Error:")
        print(e.json())        
    
    retVal = sourceInfoList
    return retVal

def metadataGetSourceByCode(pepCode=None):
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
    # would need to add URL for the banner
    if pepCode is not None:
        retVal = sourceDB.sourceData[pepCode]
    else:
        retVal = sourceDB.sourceData
    
    return retVal

def authorsGetAuthorInfo(authorNamePartial, limit=DEFAULT_LIMIT_FOR_SOLR_RETURNS, offset=0):
    """
    Returns a list of matching names (per authors last name), and the number of articles
    in PEP found by that author.
    
    >>> resp = authorsGetAuthorInfo("Tuck")
    Number found: 72
    >>> resp = authorsGetAuthorInfo("Fonag")
    Number found: 134
    >>> resp = authorsGetAuthorInfo("Levinson, Nadine A.")
    Number found: 8   
    """
    retVal = {}
    query = "art_author_id:/%s.*/" % (authorNamePartial)
    results = solrAuthors.query(q = query,  
                                fields = "authors, art_author_id",
                                facet_field = "art_author_id",
                                facet = "on",
                                facet_prefix = "%s" % authorNamePartial,
                                rows=100
                             )

    print ("Number found: %s" % results._numFound)
    
    responseInfo = ResponseInfo(
                     count = len(results.results),
                     fullCount = results._numFound,
                     limit = limit,
                     offset = offset,
                     listType="authorindex",
                     fullCountComplete = limit >= results._numFound,
                     scopeQuery=query,
                     solrParams = results._params,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )

    authorIndexItems = []
    for key, value in results.facet_counts["facet_fields"]["art_author_id"].items():
        if value > 0:
            #retVal[key] = value

            item = AuthorIndexItem( authorID = key, 
                                    publicationsURL = "/v1/Authors/Publications/{}/".format(key),
                                    publicationsCount = value,
                                  ) 
            authorIndexItems.append(item)
            #debug status
            print ("authorsGetAuthorInfo", item)
       
    responseInfo.count = len(authorIndexItems)
    
    authorIndexStruct = AuthorIndexStruct( responseInfo = responseInfo, 
                                           responseSet = authorIndexItems
                                           )
    
    authorIndex = AuthorIndex(authorIndex = authorIndexStruct)
    
    retVal = authorIndex
    return retVal

def authorsGetAuthorPublications(authorNamePartial, limit=DEFAULT_LIMIT_FOR_SOLR_RETURNS, offset=0):
    """
    Returns a list of publications (published on PEP-Web (per authors partial name), and the number of articles
    in PEP found by that author.
    
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

    print ("Number found: %s" % results._numFound)
    if results._numFound == 0:
        print ("Query didn't work - {}".format(query))
        query = "art_author_id:/{}[ ]?.*/".format(authorNamePartial)
        print ("trying again - {}".format(query))
        results = solrAuthors.query(q = "{}".format(query),  
                                    fields = "art_author_id, art_year_int, art_id, art_citeas_xml",
                                    sort="art_author_id, art_year_int", sort_order="asc",
                                    rows=limit, start=offset
                                 )
        print ("Number found: %s" % results._numFound)
        if results._numFound == 0:
            query = "art_author_id:/(.*[ ])?{}[ ]?.*/".format(authorNamePartial)
            print ("trying again - {}".format(query))
            results = solrAuthors.query(q = "{}".format(query),  
                                        fields = "art_author_id, art_year_int, art_id, art_citeas_xml",
                                        sort="art_author_id, art_year_int", sort_order="asc",
                                        rows=limit, start=offset
                                     )
    
    responseInfo = ResponseInfo(
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
        
        item = AuthorPubListItem( authorID = result.get("art_author_id", None), 
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
    
    authorPubListStruct = AuthorPubListStruct( responseInfo = responseInfo, 
                                           responseSet = authorPubListItems
                                           )
    
    authorPubList = AuthorPubList(authorPubList = authorPubListStruct)
    
    retVal = authorPubList
    return retVal

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
    
def documentsGetAbstracts(documentID, retFormat="HTML", limit=DEFAULT_LIMIT_FOR_SOLR_RETURNS, offset=0):
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
    print ("%s document matches for getAbstracts" % matches)
    
    responseInfo = ResponseInfo(
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
            elif retFormat == "TEXTONLY":
                abstract = opasxmllib.xmlElemOrStrToText(abstract)
            #else: # xml  # not necessary, let it fall through
                #pass
            
            item = DocumentListItem(year = artYear,
                                    vol = artVol,
                                    sourceTitle = sourceTitle,
                                    pgRg = pgRg,
                                    pgStart = pgStart,
                                    pgEnd = pgEnd,
                                    authorMast = authorMast,
                                    documentID = result.get("art_id", None),
                                    documentRefHTML = citeAs,
                                    documentRef = opasxmllib.xmlElemOrStrToText(citeAs, defaultReturn=""),
                                    accessLimited = False, # Todo
                                    abstract = abstract,
                                    score = result.get("score", None)
                                    )
        
            #print (item)
            documentItemList.append(item)

    responseInfo.count = len(documentItemList)
    
    documentListStruct = DocumentListStruct( responseInfo = responseInfo, 
                                             responseSet=documentItemList
                                             )
    
    documents = Documents(documents = documentListStruct)
        
    retVal = documents
            
                
    return retVal


def documentsGetDocument(documentID, retFormat="XML", authenticated=True, limit=DEFAULT_LIMIT_FOR_DOCUMENT_RETURNS, offset=0):
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
        print ("User not authenticated...fetching abstracts instead")
        return documentsGetAbstracts(documentID, limit=1)

    results = solrDocs.query(q = "art_id:%s" % (documentID),  
                                fields = "art_id, art_vol, art_year, art_citeas_xml, art_pgrg, art_title, art_author_id, abstracts_xml, summaries_xml, text_xml"
                             )
    matches = len(results.results)
    print ("%s document matches for getAbstracts" % matches)
    
    responseInfo = ResponseInfo(
                     count = len(results.results),
                     fullCount = results._numFound,
                     limit = limit,
                     offset = offset,
                     listType="documentlist",
                     fullCountComplete = limit >= results._numFound,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )
    
    documentItemList = []
    if matches >= 1:
        try:
            retVal = results.results[0]["text_xml"]
        except KeyError as e:
            logger.warning("No content or abstract found.  Error: %s" % e)
        else:
            try:    
                retVal = retVal[0]
            except Exception as e:
                logger.warning("Empty return: %s" % e)
        
            try:    
                if retFormat.lower() == "html":
                    retVal = opasxmllib.removeEncodingString(retVal)
                    retVal = opasxmllib.convertXMLStringToHTML(retVal)
                    
            except Exception as e:
                logger.warning("Can't convert data: %s" % e)
    
            responseInfo = ResponseInfo(
                             count = len(results.results),
                             fullCount = results._numFound,
                             limit = 1,
                             offset = 0,
                             listType="documentlist",
                             fullCountComplete = results._numFound <= 1,
                             timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                           )
    
            if results._numFound > 0:
                result = results.results[0]
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
                    xmlDocument = forceStringReturnFromVariousReturnTypes(result["text_xml"])
                except KeyError as e:
                    xmlDocument = None
                    logger.error("No content matched document ID for: %s" % documentID)
    
                authorIDs = result.get("art_author_id", None)
                if authorIDs is None:
                    authorMast = None
                else:
                    authorMast = opasgenlib.deriveAuthorMast(authorIDs)
    
                pgRg = result.get("art_pgrg", None)
                pgStart, pgEnd = opasgenlib.pgRgSplitter(pgRg)
    
                abstract = getExcerptFromAbstractOrSummaryOrDocument(xmlAbstract, xmlSummary, xmlDocument)
                if abstract == "[]":
                    abstract = None
                elif retFormat == "HTML":
                    abstractHTML = opasxmllib.convertXMLStringToHTML(abstract)
                    abstract = opasxmllib.extractHTMLFragment(abstractHTML, "//div[@id='abs']")
                elif retFormat == "TEXTONLY":
                    abstract = opasxmllib.xmlElemOrStrToText(abstract)
                #else: # not needed
                    #abstract = abstract
    
                if xmlDocument == "[]":
                    documentText = xmlDocument = None
                elif retFormat == "HTML":
                    documentText  = opasxmllib.removeEncodingString(xmlDocument)
                    documentText = opasxmllib.convertXMLStringToHTML(documentText)
                elif retFormat == "TEXTONLY":
                    documentText  = opasxmllib.removeEncodingString(xmlDocument)
                    documentText  = opasxmllib.xmlElemOrStrToText(documentText)
                else: # XML
                    documentText = xmlDocument
    
                citeAs = result.get("art_citeas_xml", None)
                citeAs = forceStringReturnFromVariousReturnTypes(citeAs)
                
                item = DocumentListItem(year = result.get("art_year", None),
                                        vol = result.get("art_vol", None),
                                        pgRg = pgRg,
                                        pgStart = pgStart,
                                        pgEnd = pgEnd,
                                        authormast = authorMast,  #TODO fix data model case to authorMast, but GVPi did it like this in their server
                                        documentID = result.get("art_id", None),
                                        documentRefHTML = citeAs,
                                        documentRef = opasxmllib.xmlElemOrStrToText(citeAs, defaultReturn=""),
                                        accessLimited = False, # Todo
                                        abstract = abstract,
                                        document = documentText,
                                        score = result.get("score", None)
                                        )

                documentItemList.append(item)

    responseInfo.count = len(documentItemList)  # will be ONE or ZERO
            
    documentListStruct = DocumentListStruct( responseInfo = responseInfo, 
                                             responseSet=documentItemList
                                             )
    
    documents = Documents(documents = documentListStruct)
        
    retVal = documents
    
    return retVal

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

def convertXMLToHTMLFile(xmlTextStr, xsltFile=r"../styles/pepkbd3-html.xslt", outputFilename=None):
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
            print ("File Open Error: %s", e)
        except Exception as e:
            print ("Error: %s", e)
        else:
            retVal = imageBytes
    else:
        logger.warning("Image File ID %s not found", imageID)
  
    return retVal

def getKwicList(markedUpText, extraContextLen=opasConfig.DEFAULT_KWIC_CONTENT_LENGTH, startHitTag=opasConfig.HITMARKERSTART, endHitTag=opasConfig.HITMARKEREND):
    """
    Find all nonoverlapping 
    """
    
    retVal = []
    emMarks = re.compile("(.{0,%s}%s.*%s.{0,%s})" % (extraContextLen, startHitTag, endHitTag, extraContextLen))
    for n in emMarks.finditer(markedUpText):
        retVal.append(n.group(0))
        #logger.info("Match: '...{}...'".format(n.group(0)))
        print ("Match: '...{}...'".format(n.group(0)))
    matchCount = len(retVal)
    
    return retVal    

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
                        
def searchAnalysis(queryList, 
                   filterQuery = None,
                   moreLikeThese = False,
                   queryAnalysis = False,
                   disMax = None,
                   summaryFields="art_id, art_pepsrccode, art_vol, art_year, art_iss, art_iss_title, art_newsecnm, art_pgrg, art_title, art_author_id, art_citeas_xml", 
                   highlightFields='art_title_xml, abstracts_xml, summaries_xml, art_authors_xml, text_xml', 
                   fullTextRequested=True, userLoggedIn=False, 
                   limit=DEFAULT_LIMIT_FOR_SOLR_RETURNS, offset=0):
    """
    Analyze the search clauses in the query list
	"""
    retVal = {}
    documentItemList = []
    rowCount = 0
    for n in queryList:
        n = n[3:]
        results = solrDocs.query(n,
                                 disMax = disMax,
                                 queryAnalysis = True,
                                 fields = summaryFields,
                                 rows = 1,
                                 start = 0)
    
        print ("Analysis: Term %s, matches %s" % (n, results._numFound))
        item = DocumentListItem(term = n, 
                                termCount = results._numFound
                                )
        documentItemList.append(item)
        rowCount += 1
        
    if rowCount == 0:
        fullCountComplete = True
    else:
        fullCountComplete = limit >= results._numFound
        
    responseInfo = ResponseInfo(count = rowCount,
                                fullCount = rowCount,
                                listType="srclist",
                                fullCountComplete = fullCountComplete,
                                timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                                )
    
    responseInfo.count = len(documentItemList)
    
    documentListStruct = DocumentListStruct( responseInfo = responseInfo, 
                                             responseSet = documentItemList
                                             )
    
    retVal = documentList = DocumentList(documentList = documentListStruct)
    
    return retVal

#================================================================================================================
# SEARCHTEXT
#================================================================================================================
def searchText(query, 
               filterQuery = None,
               moreLikeThese = False,
               queryAnalysis = False,
               disMax = None,
               summaryFields = "art_id, art_pepsrccode, art_vol, art_year, art_iss, art_iss_title, art_newsecnm, art_pgrg, art_title, art_author_id, art_citeas_xml", 
               highlightFields = 'art_title_xml, abstracts_xml, summaries_xml, art_authors_xml, text_xml', 
               fullTextRequested = True, 
               userLoggedIn = False, 
               extraContextLen = opasConfig.DEFAULT_KWIC_CONTENT_LENGTH,
               limit=DEFAULT_LIMIT_FOR_SOLR_RETURNS, 
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
    if moreLikeThese:
        mlt_fl = "text_xml, headings_xml, terms_xml, references_xml"
        mlt = "true"
        mlt_minwl = 8
    else:
        mlt_fl = None
        mlt = "false"
        mlt_minwl = None
    
    if queryAnalysis:
        queryDebug = "on"
    else:
        queryDebug = "off"
        
        
    results = solrDocs.query(query,  
                             fq = filterQuery,
                             debugQuery = queryDebug,
                             disMax = disMax,
                             fields = summaryFields,
                             hl= 'true', 
                             hl_fragsize = opasConfig.SOLR_HIGHLIGHT_RETURN_FRAGMENT_SIZE, 
                             hl_fl = highlightFields,
                             mlt = mlt,
                             mlt_fl = mlt_fl,
                             mlt_count = 2,
                             mlt_minwl = mlt_minwl,
                             rows = limit,
                             start = offset,
                             hl_simple_pre = opasConfig.HITMARKERSTART,
                             hl_simple_post = opasConfig.HITMARKEREND)

    print ("Search Performed: %s" % query)
    print ("Result  Set Size: %s" % results._numFound)
    print ("Return set limit: %s" % limit)
    
    responseInfo = ResponseInfo(
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


    retVal = {}
    documentItemList = []
    rowCount = 0
    rowOffset = 0
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
        titleXml = results.highlighting[documentID].get("art_title_xml", None)
        titleXml = forceStringReturnFromVariousReturnTypes(titleXml)
        abstractsXml = results.highlighting[documentID].get("abstracts_xml", None)
        abstractsXml  = forceStringReturnFromVariousReturnTypes(abstractsXml )
        summariesXml = results.highlighting[documentID].get("abstracts_xml", None)
        summariesXml  = forceStringReturnFromVariousReturnTypes(summariesXml)
        textXml = results.highlighting[documentID].get("text_xml", None)
        textXml  = forceStringReturnFromVariousReturnTypes(textXml)
        if textXml is not None:
            kwicList = getKwicList(textXml, extraContextLen=extraContextLen)  # returning context matches as a list, making it easier for clients to work with
            kwic = " . . . ".join(kwicList)  # how its done at GVPi, for compatibility (as used by PEPEasy)
            #print ("Document Length: {}; Matches to show: {}".format(len(textXml), len(kwicList)))
        else:
            kwicList = []
            kwic = ""  # this has to be "" for PEP-Easy, or it hits an object error.  
            #print ("No matches to show in document {}".format(documentID))            
        
        if not userLoggedIn or not fullTextRequested:
            textXml = getExcerptFromAbstractOrSummaryOrDocument(xmlAbstract=abstractsXml, xmlSummary=summariesXml, xmlDocument=textXml)

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
            item = DocumentListItem(PEPCode = result.get("art_pepsrccode", None), 
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
                                    title = titleXml,
                                    abstract = abstractsXml,
                                    documentText = None, #textXml,
                                    score = result.get("score", None), 
                                    similarDocs = similarDocs,
                                    similarMaxScore = similarMaxScore,
                                    similarNumFound = similarNumFound
                                    )
        except ValidationError as e:
            logger.error(e.json())  
            #print (e.json())
        else:
            rowCount += 1
            print ("{}:{}".format(rowCount, citeAs))
            #logger.info("{}:{}".format(rowCount, citeAs.decode("utf8")))
            documentItemList.append(item)
            if rowCount > limit:
                break

    responseInfo.count = len(documentItemList)
    
    documentListStruct = DocumentListStruct( responseInfo = responseInfo, 
                                             responseSet = documentItemList
                                             )
    
    documentList = DocumentList(documentList = documentListStruct)
    
    retVal = documentList
    
    return retVal

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
    
    import doctest
    doctest.testmod()    
    main()
