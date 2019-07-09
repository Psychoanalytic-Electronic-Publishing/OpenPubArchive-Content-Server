#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initial version of the Opas Solr Server (API) 

This API server is based on the existing PEP-Web API 1.0.  The data returned 
may have additional fields but should be otherwise compatible with PEP API clients
such as PEP-Easy.

2019.0617.1 - First version with 6 endpoints, 5 set up for Pydantic and one not yet
                converted - nrs
2019.0617.4 - Changed functions under decorators to snake case since the auto doc uses those 
              as sentences!


Run with:
    uvicorn main:app --reload
    
    or for debug:
    
    uvicorn main:app --debug --log-level=debug
 
(Debug set up in this file as well: app = FastAPI(debug=True))
                
Supports:
   /v1/Metadata/MostCited
   /v1/Metadata/Contents/{PEPCode}
   /v1/Metadata/Volumes/{PEPCode}
   /v1/Authors/Index/{authorNamePartial}
   /v1/Authors/Publications/{authorNamePartial}
   
   and this preliminary, not yet ported to Pydantic

   ​/Documents​/Abstracts​/{documentID}​/Getabstract
   
Endpoint and structure documentation automatically available when server is running at:

  http://127.0.0.1:8000/docs

(base URL + "/docs")

"""

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2019.0709.1"
__status__      = "Development"

import sys
sys.path.append('../libs')
sys.path.append('../config')

import opasConfig
import localsecrets

import time
import datetime
from datetime import datetime
import re
import secrets
import json

from enum import Enum
import uvicorn
from fastapi import FastAPI, Query, Path, Cookie, Header, Depends
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from pydantic import BaseModel
from pydantic.types import EmailStr
from pydantic import ValidationError

import pysolr
import json
import logging

import opasConfig

import opasAPISupportLib
import opasBasicLoginLib
from opasBasicLoginLib import get_current_user

import models
import modelsOpasCentralPydantic
import opasCentralDBLib
from sourceInfoDB import SourceInfoDB

sourceInfoDB = SourceInfoDB()
#gSessions = {}
#gOCDatabase = None # opasCentralDBLib.opasCentralDB()
gCurrentDevelopmentStatus = "Developing"

#def getSession():
    #if currentSession == None:
        #currentSession = modelsOpasCentralPydantic.Session()

app = FastAPI(
        debug=True,
        title="OPAS API for PEP-Web",
        description = "Open Publications Archive Software API",
        version = "1.0.0.Alpha",
        static_directory=r"./docs",
        swagger_static={
            "favicon": "pepfavicon.gif"
        },
    )

#app.add_middleware(SessionMiddleware,
                   #secret_key = secrets.token_urlsafe(16),
                   #session_cookie = secrets.token_urlsafe(16)
    #)

origins = [
    "http://pepeasy.pep-web.info",
    "http://api.pep-web.info",
    "http://pep-web.info",
    "http:localhost",
    "http:localhost:8080",
    "http://webfaction",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "http://api.mypep.info",
    "http://www.pep-web.info"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def checkIfUserLoggedIn():
    """
    
    """
    #TBD: Should just check token cookie here.
    resp = login_user()
    return resp.licenseInfo.responseInfo.loggedIn

@app.get("/v1/Status/", response_model=models.ServerStatusItem, tags=["Session"])
def get_the_server_status(resp: Response, 
                          request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST) 
                          ):
    """
    Return the status of the database and text server
    
    Status: In Development
    """
    ocd, sessionInfo = opasAPISupportLib.getSessionInfo(request, resp)   

    SolrOK = opasAPISupportLib.checkSolrDocsConnection()
    DbOK = ocd.openConnection()
    ocd.closeConnection()

    try:
        serverStatusItem = models.ServerStatusItem(text_server_ok = SolrOK, 
                                                   db_server_ok = DbOK,
                                                   user_ip = request.client.host,
                                                   timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')  
                                          )
    except ValidationError as e:
        print(e.json())             
    
    
    return serverStatusItem

from http import cookies

@app.get("/WhoAmI", tags=["Session"])
def temp_call_for_debugging_to_check_session_information(request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST) ):
    
    return {"client_host": request.client.host, 
            "referrer": request.headers['referer'], 
            "opasSessionID": request.cookies.get("opasSessionID", None), 
            "opasAccessToken": request.cookies.get("opasAccessToken", None),
            "opasSessionExpire": request.cookies.get("opasSessionExpire", None), 
            }


#@app.get("/v1/Session/") # at least start a session (getting a sessionID)
@app.get("/v1/Token/", tags=["Session"])  # used by PEP-Easy for login, for some reason.
def get_token(request: Request,
              resp: Response, 
              ka=None):
    """
    Get the current sessionID, or generate one.  User by PEP-Easy from v1
    """
    ocd, sessionInfo = opasAPISupportLib.getSessionInfo(request, resp)
    return sessionInfo

@app.get("/v1/License/Status/Login/", tags=["Session"])
def get_license_status(resp: Response, 
                       request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST)):
    """
    Return a LicenseStatusInfo object showing the user's license status info.
    {
        "licenseInfo": {
            "responseInfo": {
                "loggedIn": true,
                "userName": "p.e.p.a.NeilRShapiro",
                "request": "\/api\/v1\/License\/Status\/Login",
                "timeStamp": "2019-07-09T09:54:10-04:00"
            },
            "responseSet": null
        }
    }
    """
    ocd, sessionInfo = opasAPISupportLib.getSessionInfo(request, resp)
    # get session info database record if there is one
    # is the user authenticated? if so, loggedIn is true
    
    responseInfo = models.ResponseInfoLoginStatus(
    
    )
    
    responseInfo.loggedIn = False
    
    licenseInfoStruct = models.LicenseInfoStruct( responseInfo = responseInfo, 
                                                  responseSet = []
                                                  )
    
    licenseInfo = models.LicenseStatusInfo(licenseInfo = licenseInfoStruct)
    return licenseInfo

@app.get("/v1/Login/", tags=["Session"])
def login_user(resp: Response, 
               request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST),
               grant_type=None, 
               username=None, 
               password=None, 
               ka=None, 
               #user: bool = Depends(get_current_user)
               ):
    """
    Login the user, via the URL per the GVPi API/PEPEasy interaction.
    
    Needed to support the original version of the PEP API.
    
    This may not be a good secure way to login.  May be deprecated 
       after the move from the GVPi server.  Newer clients
       should use the newer methods, when they are implemented
       in this new sever.
    
    Params: 
    
    
    TODO: Need to figure out the right way to do timeouts for this "easy" login.
          
    """
    
    print ("Login via: /v1/(Users)?/Login/", username, password)
    
    ocd, sessionInfo = opasAPISupportLib.getSessionInfo(request, resp)
    sessionID = sessionInfo.session_id
    accessToken = sessionInfo.access_token
    expirationTime = sessionInfo.session_expires_time

    if accessToken is None:
        # not logged in, try to login
        # if username and password are not supplied, uses browser basic auth via the Depends(get_current_user)
        # get new sessionID, we're logging in
        #sessionID = secrets.token_urlsafe(16)
        #expirationTime = opasAPISupportLib.getExpirationCookieStr(keepActive=ka)
        #ocd = opasCentralDBLib.opasCentralDB(sessionID, accessToken, expirationTime)    
        #if user:
            #accessToken = opasCentralDBLib.getPasswordHash(sessionID)

        user = None
        if username is not None and password is not None:
            user = ocd.authenticateUser(username, password)
            if user:
                accessToken = opasCentralDBLib.getPasswordHash(sessionID)
            else:
                accessToken = None # rejected
          
        # We DONT WANT ALL COOKIES RESET HERE!        
        #opasAPISupportLib.setCookies(resp, sessionID, accessToken, expiresTime=expirationTime)
        #ocd = opasCentralDBLib.opasCentralDB(sessionID, accessToken, expirationTime, user=user)
 
    else: # already logged in with accessToken
        pass
    
    try:
        loginReturnItem = models.LoginReturnItem(token_type = "bearer", 
                                                 session_id = sessionID,
                                                 access_token = accessToken,
                                                 authenticated = accessToken is not None,
                                                 session_expires_time = expirationTime,
                                                 scope = None
                                          )
    except ValidationError as e:
        print(e.json())             

    return loginReturnItem

#@app.get("/v1/Users/Logout/") # I like it under Users so I did them both.
@app.get("/v1/Logout/", tags=["Session"])  # The original GVPi URL
def logout_user(request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST)):
    """
    Close the user's session, and log them out.
    
    /v1/Logout/ is used by the GVPi/PEPEasy current config.
                It can be removed when we move off the GVPi server.
                              
    /v1/Users/Logout/ is the newer path, parallels logout /v1/Users/Login/ for clarity.
    

    """
    #if gOCDatabase.sessionID == None:
        #logging.warn("Session logout, but no session open.")
    #else:
        #gOCDatabase.endSession(sessionToken=gOCDatabase.sessionToken)
    
    responseInfo = models.ResponseInfoLoginStatus()
    responseInfo.loggedIn = False
    
    licenseInfoStruct = models.LicenseInfoStruct( responseInfo = responseInfo, 
                                                  responseSet = []
                                                  )
    
    licenseInfo = models.LicenseStatusInfo(licenseInfo = licenseInfoStruct)
    return licenseInfo

@app.get("/v1/Database/MoreLikeThese/", response_model=models.DocumentList, tags=["Database"])
@app.get("/v1/Database/SearchAnalysis/", response_model=models.DocumentList, tags=["Database"])
@app.get("/v1/Database/Search/", response_model=models.DocumentList, tags=["Database"])
def search_the_document_database(resp: Response, 
                                 request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST),  
                                 journalName: str=Query(None, title="Match PEP Journal or Source Name", description="PEP part of a Journal, Book, or Video name (e.g., 'international'),", min_length=2),  
                                 journal: str=Query(None, title="Match PEP Journal or Source Code", description="PEP Journal Code (e.g., APA, CPS, IJP, PAQ),", min_length=2), 
                                 fulltext1: str=Query(None, title="Search for Words or phrases", description="Words or phrases (in quotes) anywhere in the document"),
                                 fulltext2: str=Query(None, title="Search for Words or phrases", description="Words or phrases (in quotes) anywhere in the document"),
                                 vol: str=Query(None, title="Match Volume Number", description="The volume number if the source has one"), 
                                 issue: str=Query(None, title="Match Issue Number", description="The issue number if the source has one"),
                                 author: str=Query(None, title="Match Author name", description="Author name, use wildcard * for partial entries (e.g., Johan*)"), 
                                 title: str=Query(None, title="Search Document Title", description="The title of the document (article, book, video)"),
                                 startyear: str=Query(None, title="First year to match or a range", description="First year of documents to match (e.g, 1999).  Range query: ^1999-2010 means between 1999-2010.  >1999 is after 1999 <1999 is before 1999"), 
                                 endyear: str=Query(None, title="Last year to match", description="Last year of documents to match (e.g, 2001)"), 
                                 dreams: str=Query(None, title="Search Text within 'Dreams'", description="Words or phrases (in quotes) to match within dreams"),  
                                 quotes: str=Query(None, title="Search Text within 'Quotes'", description="Words or phrases (in quotes) to match within quotes"),  
                                 abstracts: str=Query(None, title="Search Text within 'Abstracts'", description="Words or phrases (in quotes) to match within abstracts"),  
                                 dialogs: str=Query(None, title="Search Text within 'Dialogs'", description="Words or phrases (in quotes) to match within dialogs"),  
                                 references: str=Query(None, title="Search Text within 'References'", description="Words or phrases (in quotes) to match within references"),  
                                 citecount: str=Query(None, title="Find Documents cited this many times", description="Filter for documents cited more than the specified times in the past 5 years"),   
                                 viewcount: str=Query(None, title="Find Documents viewed this many times", description="Not yet implemented"),    
                                 viewedWithin: str=Query(None, title="Find Documents viewed this many times", description="Not yet implemented"),     
                                 solrQ: str=Query(None, title="Advanced Query (Solr Syntax)", description="Advanced Query in Solr Q syntax (see schema names)"),
                                 disMax: str=Query(None, title="Advanced Query (Solr disMax Syntax)", description="Solr disMax syntax - more like Google search"),
                                 edisMax: str=Query(None, title="Advanced Query (Solr edisMax Syntax) ", description="Solr edisMax syntax - more like Google search, better than disMax"), 
                                 quickSearch: str=Query(None, title="Advanced Query (Solr edisMax Syntax)", description="Advanced Query in Solr syntax (see schema names)"),
                                 sortBy: str=Query(None, title="Field names to sort by", description="Comma separated list of field names to sort by"),
                                 limit: int=Query(15, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                                 offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                                 ):
    """
    Search the database per one or more of the fields specified.
    
    This code is front end for three endpoints in order to only have to code parameter handling once 
    (since they all would use the same parameters), easily distinguished here by the calling path.
    
    Some of the fields should be deprecated, but for now, they support PEP-Easy, as configured to use the GVPi based PEP Server
    
    MoreLikeThis and SearchAnalysis are brand new (20190625), and there right now for experimentation
    
    Trying to reduce these by making them "smarter". For example, 
        endyear isn't needed, because startyear can handle the ranges (and better than before).
        journal is also configured to take anything that would have otherwise been entered in journalName
    
    #TODO:    
       viewcount, viewedWithin not yet implemented...and probably will be streamlined for future use.
       disMax, edisMax also not yet implemented
    
    
    Status: In Development
    
    
    """

    ocd, sessionInfo = opasAPISupportLib.getSessionInfo(request, resp)
    
    print ("Request: ", request.url._url)
    searchQ = "*:* "
    filterQ = "*:* "
    searchAnalysisTermList = []
    
    if re.search(r"/SearchAnalyses/", request.url._url):
        analysisMode = True
    else:
        analysisMode = False

    if re.search(r"/MoreLikeThese/", request.url._url):
        moreLikeTheseMode = True
    else:
        moreLikeTheseMode = False

    currentYear = datetime.utcfromtimestamp(time.time()).strftime('%Y')
        
    if title is not None:
        analyzeThis = "&& art_title_xml:{} ".format(title)
        filterQ += analyzeThis
        searchAnalysisTermList.append(analyzeThis)  

    if journalName is not None:
        analyzeThis = "&& art_pepsourcetitle_fulltext:{} ".format(journalName)
        filterQ += analyzeThis
        searchAnalysisTermList.append(analyzeThis)  
        
    if journal is not None:
        codeForQuery = ""
        analyzeThis = ""
        journalCodeListPattern = "((?P<namelist>[A-z0-9]*[ ]*\+or\+[ ]*)+|(?P<namelist>[A-z0-9]))"
        journalWildcardPattern = r".*\*[ ]*"  # see if it ends in a * (wildcard)
        if re.match(journalWildcardPattern, journal):
            # it's a wildcard pattern
            codeForQuery = journal
            analyzeThis = "&& art_pepsourcetitlefull:{} ".format(codeForQuery)
            filterQ += analyzeThis
        else:
            journalCodeList = journal.split("+or+")
            if len(journalCodeList) > 1:
                # it was a list.
                codeForQuery = " OR ".join(journalCodeList)
                analyzeThis = "&& art_pepsourcetitlefull:{} ".format(codeForQuery)
                filterQ += analyzeThis
            else:
                sourceInfo = sourceInfoDB.lookupSourceCode(journal.upper())
                if sourceInfo is not None:
                    # it's a single source code
                    codeForQuery = journal.upper()
                    analyzeThis = "&& art_pepsrccode:{} ".format(codeForQuery)
                    filterQ += analyzeThis
                else: # not a pattern, or a code, or a list of codes.
                    # must be a name
                    codeForQuery = journal
                    analyzeThis = "&& art_pepsourcetitlefull:{} ".format(codeForQuery)
                    filterQ += analyzeThis
        
        searchAnalysisTermList.append(analyzeThis)
        # or it could be an abbreviation #TODO
        # or it counld be a complete name #TODO
            
    if vol is not None:
        analyzeThis = "&& art_vol:{} ".format(vol)
        filterQ += analyzeThis
        #searchAnalysisTermList.append(analyzeThis)  # Not collecting this!
        
    if issue is not None:
        analyzeThis = "&& art_iss:{} ".format(issue)
        filterQ += analyzeThis
        #searchAnalysisTermList.append(analyzeThis)  # Not collecting this!
            
    if author is not None:
        author = author.replace('"', '')
        analyzeThis = "&& art_authors_xml:{} ".format(author)
        filterQ += analyzeThis
        searchAnalysisTermList.append(analyzeThis)  

    if startyear is not None and endyear is None:
        # put this in the filter query
        # parse startYear
        parsedYearSearch = opasAPISupportLib.yearArgParser(startyear)
        if parsedYearSearch is not None:
            filterQ += parsedYearSearch
            searchAnalysisTermList.append(parsedYearSearch)  
        else:
            logging("Search - StartYear bad argument {}".format(startyear))
        
    if startyear is not None and endyear is not None:
        # put this in the filter query
        # should check to see if they are each dates
        if re.match("[12][0-9]{3,3}", startyear) is None or re.match("[12][0-9]{3,3}", endyear) is None:
            logging("Search - StartYear {} /Endyear {} bad arguments".format(startyear, endyear))
        else:
            analyzeThis = "&& art_year_int:[{} TO {}] ".format(startyear, endyear)
            filterQ += analyzeThis
            searchAnalysisTermList.append(analyzeThis)

    if startyear is None and endyear is not None:
        if re.match("[12][0-9]{3,3}", endyear) is None:
            logging("Search - Endyear {} bad argument".format(endyear))
        else:
            analyzeThis = "&& art_year_int:[{} TO {}] ".format("*", endyear)
            filterQ += analyzeThis
            searchAnalysisTermList.append(analyzeThis)

    if citecount is not None:
        # This is the only query handled by GVPi and the current API.  But
        # the Solr database is set up so this could be easily extended to
        # the 10, 20, and "all" periods.  Here we add syntax to the 
        # citecount field, to allow the user to say:
        #  25 in 10 
        # which means 25 citations in 10 years
        # or 
        #  400 in ALL
        # which means 400 in all years. 
        # 'in' is required along with a space in front of it and after it
        # when specifying the period.
        # the default period is 5 years.
        matchPtn = "(?P<nbr>[0-9]+)(\s+IN\s+(?P<period>(5|10|20|All)))?"
        m = re.match(matchPtn, citecount, re.IGNORECASE)
        if m is not None:
            val = m.group("nbr")
            period = m.group("period")

        if val is None:
            val = 1
        if period is None:
            period = '5'
            
        analyzeThis = "&& art_cited_{}:[{} TO *] ".format(period.lower(), val)
        filterQ += analyzeThis
        searchAnalysisTermList.append(analyzeThis)

    if fulltext1 is not None:
        analyzeThis = "&& text:{} ".format(fulltext1)
        searchQ += analyzeThis
        searchAnalysisTermList.append(analyzeThis)

    if fulltext2 is not None:
        analyzeThis = "&& text:{} ".format(fulltext2)
        searchQ += analyzeThis
        searchAnalysisTermList.append(analyzeThis)
    
    if dreams is not None:
        analyzeThis = "&& dreams_xml:{} ".format(dreams)
        searchQ += analyzeThis
        searchAnalysisTermList.append(analyzeThis)

    if quotes is not None:
        analyzeThis = "&& quotes_xml:{} ".format(quotes)
        searchQ += analyzeThis
        searchAnalysisTermList.append(analyzeThis)

    if abstracts is not None:
        analyzeThis = "&& abstracts_xml:{} ".format(abstracts)
        searchQ += analyzeThis
        searchAnalysisTermList.append(analyzeThis)
    
    if dialogs is not None:
        analyzeThis = "&& dialogs_xml:{} ".format(dialogs)
        searchQ += analyzeThis
        searchAnalysisTermList.append(analyzeThis)

    if references is not None:
        analyzeThis = "&& references_xml:{} ".format(references)
        searchQ += analyzeThis
        searchAnalysisTermList.append(analyzeThis)

    if solrQ is not None:
        searchQ = solrQ # (overrides fields) # search = solrQ
        searchAnalysisTermList = [solrQ]

    if disMax is not None:
        searchQ = disMax # (overrides fields) # search = solrQ
        disMax = "disMax"

    if edisMax is not None:
        searchQ = edisMax # (overrides fields) # search = solrQ
        disMax = "edisMax"

    if quickSearch is not None: #TODO - might want to change this to match PEP-Web best
        searchQ = quickSearch # (overrides fields) # search = solrQ
        disMax = "edisMax"

    if sortBy is not None: #TODO - might want to change this to match PEP-Web best
        solrSort = sortBy # (overrides fields) # search = solrQ

    # for debug:
    
    # We don't always need full-text, but if we need to request the doc later we'll need to repeat the search parameters plus the docID
    if analysisMode:
        retVal = documentList = opasAPISupportLib.searchAnalysis(queryList=searchAnalysisTermList, 
                                                                filterQuery = None,
                                                                disMax = disMax,
                                                                queryAnalysis=analysisMode,
                                                                moreLikeThese = None,
                                                                limit=limit, offset=offset,
                                                                fullTextRequested=False,
                                                                )
        statusMsg = "{} terms/clauses; queryAnalysis: {}".format(len(searchAnalysisTermList), moreLikeTheseMode, analysisMode)
        print ("Done with search analysis.")
    else:
        retVal = documentList = opasAPISupportLib.searchText(query=searchQ, 
                                                             filterQuery = filterQ,
                                                             disMax = disMax,
                                                             queryAnalysis=analysisMode,
                                                             moreLikeThese = moreLikeTheseMode,
                                                             limit=limit, offset=offset,
                                                             fullTextRequested=False,
                                                             )

        matches = len(documentList.documentList.responseSet)
        print ("searchQ = {}".format(searchQ))
        print ("filterQ = {}".format(filterQ))
        print ("matches = {}".format(matches))
        # fill in additional return structure status info
        statusMsg = "{} hits; moreLikeThese:{}; queryAnalysis: {}".format(matches, moreLikeTheseMode, analysisMode)
        print ("Done with search.")

    client_host = request.client.host
    retVal.documentList.responseInfo.request = request.url._url

    ocd.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_DATABASE_SEARCH,
                              params=request.url._url,
                              statusMessage=statusMsg
                              )

    return retVal
    
    
@app.get("/v1/Database/MostCited/", response_model=models.DocumentList, tags=["Database"])
def get_the_most_cited_articles(resp: Response,
                                request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                                period: str=Query('5', title="Period (5, 10, 20, or all)", description=opasConfig.DESCRIPTION_MOST_CITED_PERIOD),
                                limit: int=Query(5, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                                offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                                ):
    """
    Return a list of documents for a PEPCode source (and optional year specified in query params).  
    
    Note: The GVPi implementation does not appear to support the limit and offset parameter
    
    Status: this endpoint is working.         
    """
    
    ocd, sessionInfo = opasAPISupportLib.getSessionInfo(request, resp)
    #if gOCDatabase.sessionID == None:  # make sure there's an open session for stat.
        #gOCDatabase.startSession()

    print ("in mostcited")
    try:
        retVal = documentList = opasAPISupportLib.databaseGetMostCited(period=period, limit=limit, offset=offset)
        # fill in additional return structure status info
        client_host = request.client.host
        retVal.documentList.responseInfo.request = request.url._url
    except Exception as e:
        statusMessage = "Error: {}".format(e)
        statusCode = 400
        retVal = None
    else:
        statusMessage = "Success"
        statusCode = 200

    # Don't record
    #ocd, sessionInfo = opasAPISupportLib.getSessionInfo(request, resp)
    #ocd.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_DATABASE_MOSTCITED,
                                      #params=request.url._url,
                                      #returnStatusCode = statusCode,
                                      #statusMessage=statusMessage
                                      #)

    print ("out mostcited")
    return retVal

@app.get("/v1/Database/WhatsNew/", response_model=models.WhatsNewList, tags=["Database"])
def get_the_newest_documents(resp: Response,
                             request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST),  
                             limit: int=Query(5, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                             offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                            ):
    """
    Return a list of issues for journals modified in the last week).  
    
    Status: this endpoint is working.          
    """
    
    print ("In whatsNew")
    ocd, sessionInfo = opasAPISupportLib.getSessionInfo(request, resp)
    try:
        retVal = whatsNewList = opasAPISupportLib.databaseWhatsNew(limit=limit, offset=offset)
        # fill in additional return structure status info
        client_host = request.client.host
    except Exception as e:
        e = str(e)
        statusMessage = "Error: {}".format(e.replace("'", "\\'"))
        statusCode = 400
        retVal = None
    else:
        statusMessage = "Success"
        statusCode = 200
        retVal.whatsNew.responseInfo.request = request.url._url

    # Don't record endpoint what's New
    #ocd.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_DATABASE_WHATSNEW,
                                      #params=request.url._url,
                                      #returnStatusCode = statusCode,
                                      #statusMessage=statusMessage
                                      #)

    print ("Out whatsNew")
    return retVal

@app.get("/v1/Metadata/Contents/{PEPCode}/", response_model=models.DocumentList, tags=["Metadata"])
def get_journal_content_lists(resp: Response,
                              request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                              PEPCode: str=Path(..., title="PEP Code for Source", description=opasConfig.DESCRIPTION_PEPCODE), 
                              year: str=Query("*", title="Contents Year", description="Year of source contents to return"),
                              limit: int=Query(15, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                              offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                              ):
    """
    Return a list of documents for a PEPCode source (and optional year specified in query params).  
    
    Note: The GVPi implementation does not appear to support the limit and offset parameter
    
    Status: this endpoint is working.     
    
    """
    
    ocd, sessionInfo = opasAPISupportLib.getSessionInfo(request, resp)
    try:       
        retVal = documentList = opasAPISupportLib.metadataGetContents(PEPCode, year, limit=limit, offset=offset)
        # fill in additional return structure status info
        client_host = request.client.host
    except Exception as e:
        statusMessage = "Error: {}".format(e)
        statusCode = 400
        retVal = None
    else:
        statusMessage = "Success"
        statusCode = 200
        retVal.documentList.responseInfo.request = request.url._url

    ocd.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_METADATA_CONTENTS,
                                      params=request.url._url,
                                      documentID="{}.{}".format(PEPCode, year), 
                                      returnStatusCode = statusCode,
                                      statusMessage=statusMessage
                                      )

    return retVal

@app.get("/v1/Metadata/Contents/{PEPCode}/{srcVol}/", response_model=models.DocumentList, tags=["Metadata"])
def get_journal_content_lists_for_volume(PEPCode: str, 
                                         srcVol: str, 
                                         resp: Response,
                                         request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                                         year: str=Query("*", title="HTTP Request", description=opasConfig.DESCRIPTION_YEAR),
                                         limit: int=Query(15, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                                         offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                                         ):
    """
    Return a list of documents for a PEPCode source (and optional year specified in query params).  
    
    Note: The GVPi implementation does not appear to support the limit and offset parameter
    
    Status: this endpoint is working.     
    
    """
       
    ocd, sessionInfo = opasAPISupportLib.getSessionInfo(request, resp)
    try:
        retVal = documentList = opasAPISupportLib.metadataGetContents(PEPCode, year, vol=srcVol, limit=limit, offset=offset)
        # fill in additional return structure status info
        client_host = request.client.host
    except Exception as e:
        statusMessage = "Error: {}".format(e)
        print (statusMessage)
        statusCode = 400
        retVal = None
    else:
        statusMessage = "Success"
        statusCode = 200
        retVal.documentList.responseInfo.request = request.url._url
    
    ocd.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_METADATA_CONTENTS_FOR_VOL,
                                      documentID="{}.{}".format(PEPCode, srcVol), 
                                      params=request.url._url,
                                      returnStatusCode = statusCode,
                                      statusMessage=statusMessage
                                      )
    return retVal

@app.get("/v1/Metadata/{SourceType}/", response_model=models.SourceInfoList, tags=["Metadata"])
def get_a_list_of_source_names(resp: Response,
                               request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                               SourceType: str=Path(..., title="Source Type", description=opasConfig.DESCRIPTION_SOURCETYPE), 
                               limit: int=Query(105, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                               offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                               ):
    """
    Return a list of information about a source type, e.g., journal names 
    
    """
               
    ocd, sessionInfo = opasAPISupportLib.getSessionInfo(request, resp)
    try:    
        retVal = sourceInfoList = opasAPISupportLib.metadataGetSourceByType(SourceType, limit=limit, offset=offset)
    except Exception as e:
        statusMessage = "Error: {}".format(e)
        statusCode = 400
        retVal = None
    else:
        statusMessage = "Success"
        statusCode = 200
        # fill in additional return structure status info
        client_host = request.client.host
        retVal.sourceInfo.responseInfo.request = request.url._url


    ocd.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_METADATA_SOURCEINFO,
                                      params=request.url._url,
                                      documentID="{}".format(SourceType), 
                                      returnStatusCode = statusCode,
                                      statusMessage=statusMessage
                                      )

    return retVal

@app.get("/v1/Metadata/Volumes/{PEPCode}/", response_model=models.VolumeList, tags=["Metadata"])
def get_a_list_of_volumes_for_a_journal(resp: Response,
                                        request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                                        PEPCode: str=Path(..., title="PEP Code for Source", description=opasConfig.DESCRIPTION_PEPCODE), 
                                        limit: int=Query(100, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                                        offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                                        ):
    """
    Return a list of volumes for a PEPCode (e.g., IJP) per the limit and offset parameters 
    
    Status: this endpoint is working.
    
    Sample Call:
       http://localhost:8000/v1/Metadata/Volumes/CPS/
       
    """
    
    ocd, sessionInfo = opasAPISupportLib.getSessionInfo(request, resp)
    try:
        retVal = volumeList = opasAPISupportLib.metadataGetVolumes(PEPCode, limit=limit, offset=offset)
        
        # fill in additional return structure status info
        client_host = request.client.host
    except Exception as e:
        statusMessage = "Error: {}".format(e)
        statusCode = 400
        retVal = None
    else:
        statusMessage = "Success"
        statusCode = 200
        retVal.volumeList.responseInfo.request = request.url._url

    ocd.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_METADATA_VOLUME_INDEX,
                                      params=request.url._url,
                                      documentID="{}".format(PEPCode), 
                                      returnStatusCode = statusCode,
                                      statusMessage=statusMessage
                                      )

    return retVal
#-----------------------------------------------------------------------------
@app.get("/v1/Authors/Index/{authorNamePartial}/", response_model=models.AuthorIndex, tags=["Authors"])
def get_the_author_index_entries_for_matching_author_names(resp: Response,
                    request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                    authorNamePartial: str=Path(..., title="Author name or Partial Name", description=opasConfig.DESCRIPTION_AUTHORNAMEORPARTIALNOWILD), 
                    limit: int=Query(15, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                    offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                    ):
    """
    ## /v1/Authors/Index/{authorNamePartial}/
    ## Function
    Return a list (index) of authors.  The list shows the author IDs, which are a normalized form of an authors name.
    
    ## Return Type
    authorindex

    ## Status
    This endpoint is working.

    ## Sample Call
       http://localhost:8000/v1/Authors/Index/Tuck/

    """

    ocd, sessionInfo = opasAPISupportLib.getSessionInfo(request, resp)
    try:
        retVal = opasAPISupportLib.authorsGetAuthorInfo(authorNamePartial, limit=limit, offset=offset)
    except Exception as e:
        try:
            statusMessage = "Error: {}".format(e.body.decode("utf8"))
            statusMessage = re.sub("(\tat( org.apache.*\n)|(org.eclipse.*\n))", "", statusMessage)
            statusMessage = re.sub("\t?at[ ]+", "", statusMessage)
            print ("get_the_author_index_entries_for_matching_author_names", statusMessage)
            statusCode = 400
            retVal = None
        except:
            statusMessage = "Error: {}".format(e)
    else:
        statusMessage = "Success"
        statusCode = 200
        # fill in additional return structure status info
        client_host = request.client.host
        retVal.authorIndex.responseInfo.request = request.url._url

    ocd.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_AUTHORS_INDEX,
                                      params=request.url._url,
                                      returnStatusCode = statusCode,
                                      statusMessage=statusMessage
                                      )

    return retVal

#-----------------------------------------------------------------------------
@app.get("/v1/Authors/Publications/{authorNamePartial}/", response_model=models.AuthorPubList, tags=["Authors"])
def get_a_list_of_author_publications_for_matching_author_names(resp: Response,
                           request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                           authorNamePartial: str=Path(..., title="Author name or Partial Name", description=opasConfig.DESCRIPTION_AUTHORNAMEORPARTIAL), 
                           limit: int=Query(15, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                           offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                           ):
    """
    ## /v1/Authors/Publications/{authorNamePartial}/
    ## Function
    Return a list of the author's publications.  
    
        ## Return Type
    authorPubList

    ## Status
    This endpoint is working.
    
    ## Sample Call
       http://localhost:8000/v1/Authors/Publications/Tuck/

    """
    ocd, sessionInfo = opasAPISupportLib.getSessionInfo(request, resp)
    try:
        retVal = opasAPISupportLib.authorsGetAuthorPublications(authorNamePartial, limit=limit, offset=offset)
    except Exception as e:
        statusMessage = "Error: {}".format(e)
        statusCode = 400
        authorPubListStruct = \
            models.AuthorPubListStruct( 
                responseInfo = models.ResponseInfo(
                                            count = 0,
                                            limit = limit,
                                            offset = offset,
                                            listType ="authorpublist",
                                            listLabel = "Search Error: {}".format(e),
                                            timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')
                                           ),
                responseSet = list()
            )
        
        retVal = authorPubList = models.AuthorPubList(authorPubList = authorPubListStruct)
        
    else:
        statusMessage = "Success"
        retVal.authorPubList.responseInfo.request = request.url._url
        statusCode = 200
    
    # fill in additional return structure status info
    client_host = request.client.host
    
    ocd.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_AUTHORS_PUBLICATIONS,
                                      params=request.url._url,
                                      statusMessage=gCurrentDevelopmentStatus
                                      )

    return retVal

@app.get("/v1/Documents/Abstracts/{documentID}/", response_model=models.Documents, tags=["Documents"])
def view_an_abstract(resp: Response,
                     request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                     documentID: str=Path(..., title="Document ID or Partial ID", description=opasConfig.DESCRIPTION_DOCIDORPARTIAL), 
                     retFormat: str=Query("HTML", title="Document return format", description=opasConfig.DESCRIPTION_RETURNFORMATS),
                     limit: int=Query(5, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                     offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                     ):
    """
    Return an abstract for the requested documentID (e.g., IJP.077.0001A, or multiple abstracts for a partial ID (e.g., IJP.077)
    """

    ocd, sessionInfo = opasAPISupportLib.getSessionInfo(request, resp)
    try:
        retVal = documents = opasAPISupportLib.documentsGetAbstracts(documentID, retFormat=retFormat, limit=limit, offset=offset)
    except Exception as e:
        statusMessage = "Error: {}".format(e)
        logging.error(statusMessage)
        print ("View an Abstract: " + statusMessage)
        statusCode = 400
        retVal = None
    else:
        statusMessage = "Success"
        statusCode = 200
        client_host = request.client.host
        retVal.documents.responseInfo.request = request.url._url

    ocd.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_DOCUMENTS_ABSTRACTS,
                                      params=request.url._url,
                                      returnStatusCode = statusCode,
                                      statusMessage=statusMessage
                                      )
    return retVal

@app.get("/v1/Documents/{documentID}/", response_model=models.Documents, tags=["Documents"])  # the current PEP API
@app.get("/v1/Documents/Document/{documentID}/", response_model=models.Documents, tags=["Documents"]) # more consistent with the model grouping
def view_a_document(resp: Response,
                    request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                    documentID: str=Path(..., title="Document ID or Partial ID", description=opasConfig.DESCRIPTION_DOCIDORPARTIAL), 
                    retFormat: str=Query("HTML", title="Document return format", description=opasConfig.DESCRIPTION_RETURNFORMATS),
                    offset: int=Query(0, title="Document Page offset", description=opasConfig.DESCRIPTION_PAGEOFFSET),
                    page: int=Query(None, title="Document Page Request (from document pagination)", description=opasConfig.DESCRIPTION_PAGEREQUEST),
                    ):
    """
    Return a document for the requested documentID (e.g., IJP.077.0001A, or multiple documents for a partial ID (e.g., IJP.077)
    """
    retVal = None
    sessionID = opasAPISupportLib.getSessionID(request)
    accessToken = opasAPISupportLib.getAccessToken(request)
    expirationTime = opasAPISupportLib.getExpirationTime(request)
    ocd = opasCentralDBLib.opasCentralDB(sessionID, accessToken, expirationTime)    
    try:
        retVal = documents = opasAPISupportLib.documentsGetDocument(documentID, retFormat=retFormat, authenticated = ocd.currentSession.authenticated)
    except Exception as e:
        statusMessage = "Error: {}".format(e)
        statusCode = 400
    else:
        statusMessage = "Success"
        statusCode = 200

        # fill in additional return structure status info
        client_host = request.client.host
        retVal.documents.responseInfo.request = request.url._url

    ocd.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_DOCUMENTS_PDF,
                                      params=request.url._url,
                                      statusMessage=gCurrentDevelopmentStatus
                                      )
    return retVal

@app.get("/v1/Documents/Downloads/{retFormat}/{documentID}/", tags=["Documents"])
def download_a_document(resp: Response,
                        request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                        documentID: str=Path(..., title="Document ID or Partial ID", description=opasConfig.DESCRIPTION_DOCIDORPARTIAL), 
                        retFormat=Path(..., title="Download Format", description=opasConfig.DESCRIPTION_DOCDOWNLOADFORMAT),
                        ):

     
    ocd, sessionInfo = opasAPISupportLib.getSessionInfo(request, resp)
    isAuthenticated = checkIfUserLoggedIn()  

    opasAPISupportLib.prepDocumentDownload(documentID, retFormat=retFormat, authenticated=True, baseFilename="opasDoc")    

    ocd.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_DOCUMENTS_EPUB,
                                      params=request.url._url,
                                      statusMessage=gCurrentDevelopmentStatus
                                      )

    return True

    
if __name__ == "__main__":
    print("Server Running")
    uvicorn.run(app, host="127.0.0.1", port=8000, debug=True)
