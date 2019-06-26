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
__version__     = "2019.0617.4"
__status__      = "Development"

import sys
import time
import datetime
from datetime import datetime
import re

sys.path.append('../libs')

from enum import Enum
import uvicorn
from fastapi import FastAPI, Query, Path, Cookie, Header, Depends
from starlette.requests import Request
from starlette.middleware.cors import CORSMiddleware

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

#opasxmllib = imp.load_source('opasxmllib', '../libs/opasXMLHelper.py')
#SourceInfoDB = imp.load_source('sourceInfoDB', '../libs/sourceInfoDB.py')

solr = pysolr.Solr('http://localhost:8983/solr/pepwebproto', timeout=10)
import models
import opasCentralModels
import opasCentralDBLib
from sourceInfoDB import SourceInfoDB

sourceInfoDB = SourceInfoDB()
gOCDatabase = opasCentralDBLib.opasCentralDB()
gCurrentDevelopmentStatus = "TestingOnly"

def getSession():
    if currentSession == None:
        currentSession = opasCentralModels.Session()

#app = FastAPI(debug=True)
app = FastAPI(
        debug=True,
        static_directory=r"E:\usr3\GitHub\openpubarchive\OPASServer\docs",
        swagger_static={
            "favicon": "pepfavicon.gif"
        },
    )


origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http:localhost",
    "http:localhost:8080",
    "http://webfaction",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def checkIfUserLoggedIn():
    resp = login_user()
    return resp.licenseInfo.responseInfo.loggedIn
    
#@app.get("/v1/Users/Login/")
@app.get("/v1/Token/")  # used by PEP-Easy for login, for some reason.
@app.get("/v1/Login/")
def login_user(request: Request, 
                       grant_type=None, 
                       username=None, 
                       password=None, 
                       ka=None, 
                       sessionInfo: str = Depends(get_current_user)):
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
    
    print ("Login via: /v1/(Users)?/Login/")
    
    # if username and password are not supplied, uses browser basic auth via the Depends(get_current_user)
    if username is not None and password is not None:
        sessionInfo = gOCDatabase.authenticateUser(username, password)    

    if sessionInfo.authenticated== False:
        responseInfo = models.ResponseInfoLoginStatus(loggedIn = False)
        #userName = username
    else:
        responseInfo = models.ResponseInfoLoginStatus(loggedIn = True)

    try:
        loginReturnItem = models.LoginReturnItem(token_type = "bearer", 
                                                 access_token = sessionInfo.session_token,
                                                 authenticated = sessionInfo.authenticated,
                                                 session_expires_time = sessionInfo.session_expires_time,
                                                 scope = None
                                          )
    except ValidationError as e:
        print(e.json())             
    
    #licenseInfoStruct = models.LicenseInfoStruct( responseInfo = responseInfo, 
                                                  #responseSet = loginReturnItem
                                                  #)
    
    #licenseInfo = models.LicenseStatusInfo(licenseInfo = licenseInfoStruct)
    
    return loginReturnItem

#@app.get("/v1/Users/Logout/") # I like it under Users so I did them both.
@app.get("/v1/Logout/")  # The original GVPi URL
def logout_user(username: str = Depends(get_current_user)):
    """
    Close the user's session, and log them out.
    
    /v1/Logout/ is used by the GVPi/PEPEasy current config.
                It can be removed when we move off the GVPi server.
                              
    /v1/Users/Logout/ is the newer path, parallels logout /v1/Users/Login/ for clarity.
    

    """

    if gOCDatabase.sessionID == None:
        logging.warn("Session logout, but no session open.")
    else:
        gOCDatabase.endSession(sessionToken=gOCDatabase.sessionToken)
    
    responseInfo = models.ResponseInfoLoginStatus()
    if username == False:
        responseInfo.loggedIn = False
        userName = username
    else:
        responseInfo.loggedIn = True
        user = username
    
    licenseInfoStruct = models.LicenseInfoStruct( responseInfo = responseInfo, 
                                                  responseSet = []
                                                  )
    
    licenseInfo = models.LicenseStatusInfo(licenseInfo = licenseInfoStruct)
    return licenseInfo

@app.get("/v1/Login/BasicExample/")
def login_user(sessionInfo: str = Depends(get_current_user)):
    """
    This login uses the browser's basic authentication model 
      which is nicely supported by FastAPI.
      
    It should be upgraded to a more secure and cleaner method,
      per the excellent instructions on the FastAPI site.
      
    /v1/License/Status/Login/ is used by the GVPi/PEPEasy original config.
                              It can be removed when we move off the GVPi server.
                              
    /v1/Users/Login/ is the newer path, parallels logout /v1/Users/Logout/ for clarity.
    
    The two paths work equivalently for now.
      
    """
    print ("Login via: /v1/User/Login/BasicExample")
    if sessionInfo != None:
        try:
            loginReturnItem = models.LoginReturnItem(token_type = "bearer", 
                                                 access_token = sessionInfo.session_token,
                                                 authenticated = sessionInfo.authenticated,
                                                 session_expires_time = sessionInfo.session_expires_time,
                                                 scope = None
                                          )
        except ValidationError as e:
            print(e.json())             

    return loginReturnItem

@app.get("/v1/License/Status/Login/")
def get_login_status():
    """
    Get current session information and login status.
    
    """
    print ("Login Status via: /v1/License/Status/Login/")
    sessionInfo = gOCDatabase.currentSession
    if sessionInfo != None:
        try:
            responseInfo = models.ResponseInfoLoginStatus(loggedIn = sessionInfo.authenticated)
            
            loginReturnItem = models.LoginReturnItem(token_type = "bearer", 
                                                 access_token = sessionInfo.session_token,
                                                 authenticated = sessionInfo.authenticated,
                                                 session_expires_time = sessionInfo.session_expires_time,
                                                 scope = None
                                          )
        except ValidationError as e:
            print(e.json())             
    else:
        try:
            responseInfo = models.ResponseInfoLoginStatus(loggedIn = False)
            loginReturnItem = models.LoginReturnItem(token_type = "bearer", 
                                                 access_token = None,
                                                 authenticated = False,
                                                 session_expires_time = None,
                                                 scope = None
                                          )
        except ValidationError as e:
            print(e.json())             
        
    licenseInfoStruct = models.LicenseInfoStruct( responseInfo = responseInfo, 
                                                  responseSet = loginReturnItem
                                                  )
    
    licenseInfo = models.LicenseStatusInfo(licenseInfo = licenseInfoStruct)
    

    return licenseInfo

@app.get("/v1/Database/MoreLikeThese/", response_model=models.DocumentList)
@app.get("/v1/Database/SearchAnalyses/", response_model=models.DocumentList)
@app.get("/v1/Database/Search/", response_model=models.DocumentList)
def search_the_document_database(request: Request, 
                                 journalName: str=Query(None, title="Match PEP Journal or Source Name", description="PEP Journal, Book, or Video source code (e.g., APA, CPS, IJP, PAQ),", min_length=2),  
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
                                 citecount: str=Query(None, title="Find Documents cited this many times", description="Not yet implemented"),   
                                 viewcount: str=Query(None, title="Find Documents viewed this many times", description="Not yet implemented"),    
                                 viewedWithin: str=Query(None, title="Find Documents viewed this many times", description="Not yet implemented"),     
                                 solrQ: str=Query(None, title="Advanced Query (Solr Syntax)", description="Advanced Query in Solr Q syntax (see schema names)"),
                                 disMax: str=Query(None, title="Advanced Query (Solr disMax Syntax)", description="Advanced Query in Solr disMax syntax (see schema names)"),
                                 edisMax: str=Query(None, title="Advanced Query (Solr edisMax Syntax) ", description="Advanced Query in Solr edisMax syntax (see schema names)"), 
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
       citecount, viewcount, viewedWithin not yet implemented...and probably will be streamlined for future use.
       disMax, edisMax also not yet implemented
    
    
    
    Status: In Development
    
    
    """

    if gOCDatabase.sessionID == None:  # make sure there's an open session for stat.
        gOCDatabase.startSession()
       
    gOCDatabase.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_DATABASE_SEARCH,
                                      params=request.url._url,
                                      statusMessage=gCurrentDevelopmentStatus
                                      )
    
    print ("Request: ", request.url._url)
    searchQ = "*:* "
    filterQ = "*:* "
    
    if re.search(r"/SearchAnalyses/", request.url._url):
        analysisMode = True
    else:
        analysisMode = False

    if re.search(r"/MoreLikeThese/", request.url._url):
        moreLikeTheseMode = True
    else:
        moreLikeTheseMode = False

    currentYear = datetime.utcfromtimestamp(time.time()).strftime('%Y')
    if citecount is not None:
        searchQ += "&& art_authors_xml:{} ".format("shapiro") # TODO: Dummy for now
        
    if title is not None:
        searchQ += "&& art_title_xml:{} ".format(title)

    if journalName is not None:
        searchQ += "&& art_pepsourcetitlefull:{} ".format(journalName)
        
    if journal is not None:
        codeForQuery = ""
        journalCodeListPattern = "((?P<namelist>[A-z0-9]*[ ]*\+or\+[ ]*)+|(?P<namelist>[A-z0-9]))"
        journalWildcardPattern = r".*\*[ ]*"  # see if it ends in a * (wildcard)
        if re.match(journalWildcardPattern, journal):
            # it's a wildcard pattern
            codeForQuery = journal
            filterQ += "&& art_pepsourcetitlefull:{} ".format(codeForQuery)
        else:
            journalCodeList = journal.split("+or+")
            if len(journalCodeList) > 1:
                # it was a list.
                codeForQuery = " OR ".join(journalCodeList)
                filterQ += "&& art_pepsourcetitlefull:{} ".format(codeForQuery)
            else:
                sourceInfo = sourceInfoDB.lookupSourceCode(journal)
                if sourceInfo is not None:
                    # it's a single source code
                    codeForQuery = journal
                    filterQ += "&& art_pepsrccode:{} ".format(codeForQuery)
                else: # not a pattern, or a code, or a list of codes.
                    # must be a name
                    codeForQuery = journal
                    filterQ += "&& art_pepsourcetitlefull:{} ".format(codeForQuery)
        
        # or it could be an abbreviation #TODO
        # or it counld be a complete name #TODO
            
    if vol is not None:
        filterQ += "&& art_vol:{} ".format(vol)
        
    if issue is not None:
        filterQ += "&& art_vol:{} ".format(issue)
            
    if author is not None:
        searchQ += "&& art_authors_xml:{} ".format(author)

    if startyear is not None and endyear is None:
        # put this in the filter query
        # parse startYear
        parsedYearSearch = opasAPISupportLib.yearArgParser(startyear)
        if parsedYearSearch is not None:
            filterQ += parsedYearSearch
        else:
            logging("Search - StartYear bad argument {}".format(startyear))
        
    if startyear is not None and endyear is not None:
        # put this in the filter query
        # should check to see if they are each dates
        if re.match("[12][0-9]{3,3}", startyear) is None or re.match("[12][0-9]{3,3}", endyear) is None:
            logging("Search - StartYear {} /Endyear {} bad arguments".format(startyear, endyear))
        else:
            filterQ += "&& art_year_int:[{} TO {}] ".format(startyear, endyear)

    if startyear is None and endyear is not None:
        parsedYearSearch = opasAPISupportLib.yearArgParser(endyear)
        if parsedYearSearch is not None:
            filterQ += parsedYearSearch
        else:
            logging("Search - EndYear bad argument {}".format(endyear))

    if fulltext1 is not None:
        searchQ += "&& text:{} ".format(fulltext1)

    if fulltext2 is not None:
        searchQ += "&& text:{} ".format(fulltext2)
    
    if dreams is not None:
        searchQ += "&& dreams_xml:{} ".format(dreams)

    if quotes is not None:
        searchQ += "&& quotes_xml:{} ".format(quotes)

    if abstracts is not None:
        searchQ += "&& abstracts_xml:{} ".format(abstracts)
    
    if dialogs is not None:
        searchQ += "&& dialogs_xml:{} ".format(dialogs)

    if references is not None:
        searchQ += "&& references_xml:{} ".format(references)

    if solrQ is not None:
        searchQ = solrQ # (overrides fields) # search = solrQ
    
    # for debug:
    
    # We don't always need full-text, but if we need to request the doc later we'll need to repeat the search parameters plus the docID
    retVal = documentList = opasAPISupportLib.searchText(query=searchQ, 
                                                         filterQuery = filterQ,
                                                         queryAnalysis=analysisMode,
                                                         moreLikeThese = moreLikeTheseMode,
                                                         limit=limit, offset=offset,
                                                         fullTextRequested=False,
                                                         )

    print ("searchQ = {}".format(searchQ))
    print ("filterQ = {}".format(filterQ))
    print ("matches = {}".format(len(documentList.documentList.responseSet)))
    # fill in additional return structure status info
    client_host = request.client.host
    retVal.documentList.responseInfo.request = request.url._url
    print ("Done with search.")

    return retVal
    
@app.get("/v1/Database/MostCited/", response_model=models.DocumentList)
def get_the_most_cited_articles(request: Request, 
                                limit: int=Query(5, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                                offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                                ):
    """
    Return a list of documents for a PEPCode source (and optional year specified in query params).  
    
    Note: The GVPi implementation does not appear to support the limit and offset parameter
    
    Status: this endpoint is working.         
    """
    
    if gOCDatabase.sessionID == None:  # make sure there's an open session for stat.
        gOCDatabase.startSession()
       
    gOCDatabase.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_DATABASE_MOSTCITED,
                                      params=request.url._url,
                                      statusMessage=gCurrentDevelopmentStatus
                                      )

    retVal = documentList = opasAPISupportLib.databaseGetMostCited(limit=limit, offset=offset)
    # fill in additional return structure status info
    client_host = request.client.host
    retVal.documentList.responseInfo.request = request.url._url

    return retVal
@app.get("/v1/Database/WhatsNew/", response_model=models.WhatsNewList)
def get_the_newest_documents(request: Request, 
                             limit: int=Query(5, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                             offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                            ):
    """
    Return a list of issues for journals modified in the last week).  
    
    Status: this endpoint is working.          
    """
    
    if gOCDatabase.sessionID == None:  # make sure there's an open session for stat.
        gOCDatabase.startSession()
       
    gOCDatabase.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_DATABASE_WHATSNEW,
                                      params=request.url._url,
                                      statusMessage=gCurrentDevelopmentStatus
                                      )

    retVal = whatsNewList = opasAPISupportLib.databaseWhatsNew(limit=limit, offset=offset)
    # fill in additional return structure status info
    client_host = request.client.host
    retVal.whatsNew.responseInfo.request = request.url._url

    return retVal

@app.get("/v1/Metadata/Contents/{PEPCode}/", response_model=models.DocumentList)
def get_journal_content_lists(PEPCode: str=Path(..., title="PEP Code for Source", description=opasConfig.DESCRIPTION_PEPCODE), 
                              request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                              year: str=Query("*", title="Contents Year", description="Year of source contents to return"),
                              limit: int=Query(15, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                              offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                              ):
    """
    Return a list of documents for a PEPCode source (and optional year specified in query params).  
    
    Note: The GVPi implementation does not appear to support the limit and offset parameter
    
    Status: this endpoint is working.     
    
    """
    
    if gOCDatabase.sessionID == None:  # make sure there's an open session for stat.
        gOCDatabase.startSession()
       
    gOCDatabase.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_METADATA_CONTENTS,
                                      params=request.url._url,
                                      statusMessage=gCurrentDevelopmentStatus
                                      )

    retVal = documentList = opasAPISupportLib.metadataGetContents(PEPCode, year, limit=limit, offset=offset)
    # fill in additional return structure status info
    client_host = request.client.host
    retVal.documentList.responseInfo.request = request.url._url

    return retVal

@app.get("/v1/Metadata/Contents/{PEPCode}/{srcVol}/", response_model=models.DocumentList)
def get_journal_content_lists_for_volume(PEPCode: str, 
                                         srcVol: str, 
                                         request: Request, 
                                         year: str = "*", 
                                         limit: int=Query(15, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                                         offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                                         ):
    """
    Return a list of documents for a PEPCode source (and optional year specified in query params).  
    
    Note: The GVPi implementation does not appear to support the limit and offset parameter
    
    Status: this endpoint is working.     
    
    """
    if gOCDatabase.sessionID == None:  # make sure there's an open session for stat.
        gOCDatabase.startSession()
       
    gOCDatabase.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_METADATA_CONTENTS_FOR_VOL,
                                      documentID="{}.{}".format(PEPCode, srcVol), 
                                      params=request.url._url,
                                      statusMessage=gCurrentDevelopmentStatus
                                      )
    retVal = documentList = opasAPISupportLib.metadataGetContents(PEPCode, year, vol=srcVol, limit=limit, offset=offset)
    # fill in additional return structure status info
    client_host = request.client.host
    retVal.documentList.responseInfo.request = request.url._url
    
    return retVal

@app.get("/v1/Metadata/{SourceType}/", response_model=models.SourceInfoList)
def get_a_list_of_source_names(SourceType: str=Path(..., title="PEP Code for Source", description=opasConfig.DESCRIPTION_SOURCETYPE), 
                               request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                               limit: int=Query(15, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                               offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                               ):
    """
    Return a list of information about a source type, e.g., journal names 
    
    """
    try:
        if gOCDatabase.sessionID == None:  # make sure there's an open session for stat.
            gOCDatabase.startSession()
    except Exception as e:
        print ("Error: get_a_list_of_source_names: {}".format(e))
               
        
    gOCDatabase.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_METADATA_SOURCEINFO,
                                      params=request.url._url,
                                      statusMessage=gCurrentDevelopmentStatus
                                      )

    retVal = sourceInfoList = opasAPISupportLib.metadataGetSourceByType(SourceType)
    
    # fill in additional return structure status info
    client_host = request.client.host
    retVal.sourceInfo.responseInfo.request = request.url._url
    return retVal

@app.get("/v1/Metadata/Volumes/{PEPCode}/", response_model=models.VolumeList)
def get_a_list_of_volumes_for_a_journal(PEPCode: str=Path(..., title="PEP Code for Source", description=opasConfig.DESCRIPTION_PEPCODE), 
                                        request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                                        limit: int=Query(100, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                                        offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                                        ):
    """
    Return a list of volumes for a PEPCode (e.g., IJP) per the limit and offset parameters 
    
    Status: this endpoint is working.
    
    Sample Call:
       http://localhost:8000/v1/Metadata/Volumes/CPS/
       
    """
    
    if gOCDatabase.sessionID == None:  # make sure there's an open session for stat.
        gOCDatabase.startSession()
       
    gOCDatabase.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_METADATA_VOLUME_INDEX,
                                      params=request.url._url,
                                      statusMessage=gCurrentDevelopmentStatus
                                      )

    retVal = volumeList = opasAPISupportLib.metadataGetVolumes(PEPCode, limit=limit, offset=offset)
    
    # fill in additional return structure status info
    client_host = request.client.host
    retVal.volumeList.responseInfo.request = request.url._url

    return retVal
#-----------------------------------------------------------------------------
@app.get("/v1/Authors/Index/{authorNamePartial}/", response_model=models.AuthorIndex)
def getAuthorsIndex(authorNamePartial: str=Path(..., title="Author name or Partial Name", description=opasConfig.DESCRIPTION_AUTHORNAMEORPARTIAL), 
                    request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
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

    if gOCDatabase.sessionID == None:  # make sure there's an open session for stat.
        gOCDatabase.startSession()
       
    gOCDatabase.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_AUTHORS_INDEX,
                                      params=request.url._url,
                                      statusMessage=gCurrentDevelopmentStatus
                                      )

    retVal = opasAPISupportLib.authorsGetAuthorInfo(authorNamePartial, limit=limit, offset=offset)

    # fill in additional return structure status info
    client_host = request.client.host
    retVal.authorIndex.responseInfo.request = request.url._url

    return retVal

#-----------------------------------------------------------------------------
@app.get("/v1/Authors/Publications/{authorNamePartial}/", response_model=models.AuthorPubList)
def getAuthorsPublications(authorNamePartial: str=Path(..., title="Author name or Partial Name", description=opasConfig.DESCRIPTION_AUTHORNAMEORPARTIAL), 
                           request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
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

    if gOCDatabase.sessionID == None:  # make sure there's an open session for stat.
        gOCDatabase.startSession()
      
    gOCDatabase.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_AUTHORS_PUBLICATIONS,
                                      params=request.url._url,
                                      statusMessage=gCurrentDevelopmentStatus
                                      )

    retVal = opasAPISupportLib.authorsGetAuthorPublications(authorNamePartial, limit=limit, offset=offset)

    # fill in additional return structure status info
    client_host = request.client.host
    retVal.authorPubList.responseInfo.request = request.url._url
    
    return retVal

@app.get("/v1/Documents/Abstracts/{documentID}/", response_model=models.Documents)
def view_an_abstract(documentID: str=Path(..., title="Document ID or Partial ID", description=opasConfig.DESCRIPTION_DOCIDORPARTIAL), 
                     request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                     retFormat: str=Query("HTML", title="Document return format", description=opasConfig.DESCRIPTION_RETURNFORMATS),
                     limit: int=Query(5, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                     offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                     ):
    """
    Return an abstract for the requested documentID (e.g., IJP.077.0001A, or multiple abstracts for a partial ID (e.g., IJP.077)
    """

    if gOCDatabase.sessionID == None:  # make sure there's an open session for stat.
        gOCDatabase.startSession()
      
    gOCDatabase.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_DOCUMENTS_ABSTRACTS,
                                      params=request.url._url,
                                      statusMessage=gCurrentDevelopmentStatus
                                      )

    retVal = documents = opasAPISupportLib.documentsGetAbstracts(documentID, retFormat=retFormat, limit=limit, offset=offset)

    # fill in additional return structure status info
    if retVal is not None:
        client_host = request.client.host
        retVal.documents.responseInfo.request = request.url._url

    return retVal

@app.get("/v1/Documents/{documentID}/", response_model=models.Documents)  # the current PEP API
@app.get("/v1/Documents/Document/{documentID}/", response_model=models.Documents)
def view_a_document(documentID: str=Path(..., title="Document ID or Partial ID", description=opasConfig.DESCRIPTION_DOCIDORPARTIAL), 
                    request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                    retFormat: str=Query("HTML", title="Document return format", description=opasConfig.DESCRIPTION_RETURNFORMATS),
                    limit: int=Query(15, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                    offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                    ):
    """
    Return a document for the requested documentID (e.g., IJP.077.0001A, or multiple documents for a partial ID (e.g., IJP.077)
    """
    retVal = None
    if gOCDatabase.currentSession.authenticated == True:
        gOCDatabase.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_DOCUMENTS_PDF,
                                          params=request.url._url,
                                          statusMessage=gCurrentDevelopmentStatus
                                          )
    
        retVal = documents = opasAPISupportLib.documentsGetDocument(documentID, retFormat=retFormat, authenticated = True)
    
        # fill in additional return structure status info
        client_host = request.client.host
        retVal.documents.responseInfo.request = request.url._url

    return retVal

@app.get("/v1/Documents/Downloads/{retFormat}/{documentID}/")
def download_a_document(documentID: str=Path(..., title="Document ID or Partial ID", description=opasConfig.DESCRIPTION_DOCIDORPARTIAL), 
                        request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST),
                        retFormat=Path(..., title="Download Format", description=opasConfig.DESCRIPTION_DOCDOWNLOADFORMAT),
                        ):

    if gOCDatabase.sessionID == None:  # make sure there's an open session for stat.
        gOCDatabase.startSession()
      
    gOCDatabase.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_DOCUMENTS_EPUB,
                                      params=request.url._url,
                                      statusMessage=gCurrentDevelopmentStatus
                                      )

    isAuthenticated = checkIfUserLoggedIn()  

    opasAPISupportLib.prepDocumentDownload(documentID, retFormat=retFormat, authenticated=True, baseFilename="opasDoc")    

    return True

    
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, debug=True)