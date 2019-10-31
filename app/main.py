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

2019.0816.1 - Figured out that I need to return the same model in case of error. 
              Responseinfo has errors which is a struct with error messages.
              Setting resp.status_code returns the error code.

              EXAMPLE in get_the_author_index_entries_for_matching_author_names
                      Returns the error correctly when Solr is not running.
                      USE THAT AS A TEMPLATE.

              #TODO: This now needs to be done to each end point.
              
2019.0904.1 - Started conversion to snake_case...

2019.1019/1 - This and the other modules have now been (mostly) converted from camelCase to snake_case
              for the sake of other Python programmers using the source.  This does lead
              to some consistency issues, because you do end up with a mix of camelCase given
              the API and some libraries using it.  I'm not a big fan of snake_case but
              trying to do it in the most consistent way possible :)


Run with:
    uvicorn server:app --reload

    or for debug:

    uvicorn main:app --debug --log-level=debug

(Debug set up in this file as well: app = FastAPI(debug=True))

Supports:
   /v1/Metadata/MostCited
   /v1/Metadata/Contents/{SourceCode}
   /v1/Metadata/Volumes/{SourceCode}
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
__version__     = "2019.0906.1"
__status__      = "Development"

import sys
sys.path.append('./config')
sys.path.append('./libs')
sys.path.append('./libs/solrpy')

import os.path
import time
import datetime
from datetime import datetime
import re
import secrets
# import json
from urllib import parse
# from http import cookies

from enum import Enum
import uvicorn
from fastapi import FastAPI, Query, Path, Cookie, Header, Depends, HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, RedirectResponse, FileResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_200_OK, \
                             HTTP_400_BAD_REQUEST, \
                             HTTP_401_UNAUTHORIZED, \
                             HTTP_403_FORBIDDEN, \
                             HTTP_500_INTERNAL_SERVER_ERROR, \
                             HTTP_503_SERVICE_UNAVAILABLE

from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI()


from pydantic import BaseModel
from pydantic.types import EmailStr
from pydantic import ValidationError
import solrpy as solr
import json
import libs.opasConfig as opasConfig
from opasConfig import OPASSESSIONID, OPASACCESSTOKEN, OPASEXPIRES 
import logging
logger = logging.getLogger(__name__)

from config.localsecrets import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
import jwt
import localsecrets as localsecrets
import localsecrets
import libs.opasAPISupportLib as opasAPISupportLib
import libs.opasBasicLoginLib as opasBasicLoginLib
#from libs.opasBasicLoginLib import get_current_user

from errorMessages import *
import models
import modelsOpasCentralPydantic
import opasCentralDBLib
from sourceInfoDB import SourceInfoDB

sourceInfoDB = SourceInfoDB()
# gActiveSessions = {}

#gOCDatabase = None # opasCentralDBLib.opasCentralDB()
CURRENT_DEVELOPMENT_STATUS = "Developing"

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

#origins = [
    #"http://pepeasy.pep-web.info",
    #"http://api.pep-web.info",
    #"http://pep-web.info",
    #"http://*.pep-web.info",
    #"http://localhost",
    #"http://development",
    #"http://localhost:8080",
    #"http://webfaction",
    #"http://127.0.0.1",
    #"http://127.0.0.1:8000",
    #"http://api.mypep.info",
    #"http://www.pep-web.info"
#]

origins = [
    "http://development",
    "http://development.org",
    "http://.development.org",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info('Started at %s', datetime.today().strftime('%Y-%m-%d %H:%M:%S"'))

def check_if_user_logged_in(request:Request, 
                            response:Response):
    """

    """
    #TBD: Should just check token cookie here.
    ret_val = login_user(response, request)
    return ret_val.authenticated  #  this may not be right.

#-----------------------------------------------------------------------------
@app.get("/v2/Admin/SessionCleanup/", response_model=models.ServerStatusItem, tags=["Admin"])
def cleanup_sessions(response: Response, 
                     request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST) 
                          ):
    """
    ## Function
       <b>Clean up old, open sessions (may only be needed during development</b>

    ## Return Type
       ServerStatusItem

    ## Status
       Status: In Development

    ## Sample Call
         /v2/Admin/SessionCleanup/
    
    ## Notes
         NA
    
    ## Potential Errors
       NA
       
    """
    ocd, session_info = opasAPISupportLib.get_session_info(request, response)   
    #TODO: Check if user is admin
    count = ocd.close_expired_sessions()
    ocd.close_inactive_sessions(inactive_time=opasConfig.SESSION_INACTIVE_LIMIT)
    solr_ok = opasAPISupportLib.check_solr_docs_connection()
    db_ok = ocd.open_connection()
    ocd.close_connection()

    try:
        server_status_item = None
    except ValidationError as e:
        logger.warning("ValidationError", e.json())
    else:
        server_status_item = models.ServerStatusItem(text_server_ok = solr_ok, 
                                                     db_server_ok = db_ok,
                                                     user_ip = request.client.host,
                                                     solr_url = localsecrets.SOLRURL,
                                                     config_name = localsecrets.CONFIG,
                                                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')  
                                                     )


    return server_status_item



#-----------------------------------------------------------------------------
@app.get("/v2/Admin/Status/", response_model=models.ServerStatusItem, tags=["Session"])
def get_the_server_status(response: Response, 
                          request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST) 
                          ):
    """
    ## Function
       <b>Return the status of the database and text server</b>

    ## Return Type
       models.ServerStatusItem

    ## Status
       Status: In Development

    ## Sample Call
         /v2/Admin/Status/
    
    ## Notes
       NA
    
    ## Potential Errors
       NA
        
    """
    ocd, session_info = opasAPISupportLib.get_session_info(request, response)   

    solr_ok = opasAPISupportLib.check_solr_docs_connection()
    db_ok = ocd.open_connection()
    ocd.close_connection()

    try:
        server_status_item = models.ServerStatusItem(text_server_ok = solr_ok, 
                                                     db_server_ok = db_ok,
                                                     user_ip = request.client.host,
                                                     solr_url = localsecrets.SOLRURL,
                                                     config_name = localsecrets.CONFIG,
                                                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')  
                                                     )
    except ValidationError as e:
        logger.warning("ValidationError", e.json())

    #response.set_cookie(key="testtoken", value="testtokenvalue", expires="300")

    return server_status_item

#-----------------------------------------------------------------------------
@app.get("/v2/Admin/WhoAmI/", response_model=models.SessionInfo, tags=["Admin"])
# @app.get("/v2/Admin/WhoAmI/", tags=["Admin"])
def who_am_i(response: Response,
             request: Request):
    """
    ## Function
       <b>Temporary endpoint for debugging purposes</b>

    ## Return Type
       models.SessionInfo

    ## Status
       This endpoint is working.

    ## Sample Call
         /v2/Admin/WhoAmI/
    
    ## Notes
       NA
    
    ## Potential Errors
       NA

    """

    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    return(session_info)

##-----------------------------------------------------------------------------
#@app.get("/v2/Admin/WhoAmIGit/", tags=["Admin"])
#def who_am_i2(response: Response,
              #request: Request):
    #"""
    #Temporary endpoint for debugging purposes
    #"""
    #return {"client_host": request.client.host, 
            #"referrer": request.headers.get('referrer', None), 
            #OPASSESSIONID: request.cookies.get(f"{OPASSESSIONID}", None), 
            #OPASACCESSTOKEN: request.cookies.get(f"{OPASACCESSTOKEN}", None),
            #OPASEXPIRES: request.cookies.get(f"{OPASEXPIRES}", None), 
            #}


#-----------------------------------------------------------------------------
security = HTTPBasic()
def get_current_username(response: Response, 
                         request: Request,
                         credentials: HTTPBasicCredentials = Depends(security)):

    ocd, session_info = opasAPISupportLib.get_session_info(request, response)   
    status, user = ocd.authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

@app.get("/v2/Users/BasicLogin/", tags=["Session"], description="Used for Basic Authentication")
def read_current_user(response: Response, 
                      request: Request,
                      user: str = Depends(get_current_username), 
                      ka=False):
    """
    ## Function
       <b>Basic login Authentication.  Calls up a simple dialog allowing secure login.</b>
       
    ## Return Type
       models.LoginReturnItem

    ## Status
       This endpoint is working.

    ## Sample Call
         /v2/Users/BasicLogin/
    
    ## Notes
    
    ## Potential Errors
        
    """
    session_id = request.cookies.get(OPASSESSIONID) #  opasAPISupportLib.get_session_id(request)
    access_token = request.cookies.get(OPASACCESSTOKEN)   #  opasAPISupportLib.get_access_token(request)
    expiration_time = datetime.utcfromtimestamp(time.time() + opasAPISupportLib.get_max_age(keep_active=ka))
    logger.debug("V2 Login Request: ")
    
    if session_id is not None and access_token is not None:
        logger.debug("...note, already logged in...")
        pass # we are already logged in
    else: # 
        if user:
            # user is authenticated
            # we need to close any open sessions.
            if session_id is not None and access_token is not None:
                # do a logout
                session_end_time = datetime.utcfromtimestamp(time.time())
                success = ocd.update_session(session_id=session_id, 
                                             session_end=session_end_time
                                             )    

            # NOW lets give them a new session
            # new session and then token
            session_id = secrets.token_urlsafe(16)
            max_age = opasAPISupportLib.get_max_age(ka)
            user.start_date = user.start_date.timestamp()  # we may just want to null these in the jwt
            user.end_date = user.end_date.timestamp()
            user.last_update = user.last_update.timestamp()
            access_token = jwt.encode({'exp': expiration_time.timestamp(),
                                       'user': user.dict()
                                      },
                                      key=localsecrets.SECRET_KEY,
                                      algorithm=localsecrets.ALGORITHM)
            # start a new session, with this user (could even still be the old user
            ocd, session_info = opasAPISupportLib.start_new_session(response,
                                                                    request,
                                                                    session_id=session_id,
                                                                    access_token=access_token,
                                                                    user=user)
            # set accessToken (jwt) Cookie!
            response.set_cookie(key=OPASSESSIONID,
                                value=session_id,
                                max_age=max_age, expires=None, 
                                path="/",
                                secure=False, 
                                httponly=False)

            response.set_cookie(key=OPASACCESSTOKEN,
                                value=access_token,
                                max_age=max_age, expires=None, 
                                path="/",
                                secure=False, 
                                httponly=False)
        else: # Can't log in!
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED, 
                detail="Bad credentials"
            )

    try:
        login_return_item = models.LoginReturnItem(token_type = "bearer", 
                                                   session_id = session_id,
                                                   access_token = access_token,
                                                   authenticated = access_token is not None,
                                                   session_expires_time = expiration_time,
                                                   keep_active = ka,
                                                   error_message = None,
                                                   scope = None
                                                   )
    except ValidationError as e:
        logger.error(e.json())             

    return login_return_item

#-----------------------------------------------------------------------------
@app.get("/v1/Token/", tags=["Session"], description="Used by PEP-Easy to login; will be deprecated in V2")  
def get_token(response: Response, 
              request: Request,
              grant_type=None, 
              username=None, 
              password=None, 
              ka=False):
    """
    ## Function
       <b>Get the current sessionID, or generate one.  Uses by PEP-Easy from v1</b>

    ## Return Type
       documents

    ## Status
       This endpoint is working.

    ## Sample Call
         /v1/Token/
    
    ## Notes
    
    ## Potential Errors
        
    """
    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    if grant_type=="password" and username is not None and password is not None:
        login_return_item = login_user(response, request, grant_type, username, password, ka)
        return login_return_item
    else:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, 
            detail=ERR_CREDENTIALS
        )
        #err_code = response.status_code = HTTP_400_BAD_REQUEST
        #err_return = models.ErrorReturn(error = ERR_CREDENTIALS, error_message = ERR_MSG_INSUFFICIENT_INFO)

#-----------------------------------------------------------------------------
@app.get("/v1/License/Status/Login/", tags=["Session"])
def get_license_status(response: Response, 
                       request: Request=Query( None,
                                               title="HTTP Request",
                                               description=opasConfig.DESCRIPTION_REQUEST)):
    """
    ## Function
       <b>Return a LicenseStatusInfo object showing the user's license status info.</b>

    ## Return Type
       models.ResponseInfoLoginStatus

    ## Status
       This is currently used by PEPEasy (under checkLoginStatus)

    ## Sample Call
         /v1/License/Status/Login/
    
    ## Notes
         In V1, glossary entries are fetched via the /v1/Documents endpoint
    
    ## Potential Errors
    """
    # get session info database record if there is one
    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    # session_id = session_info.session_id
    # is the user authenticated? if so, loggedIn is true
    logged_in = session_info.authenticated
    user_id = session_info.user_id
    username = None
    user = None
    if user_id == 0:
        user = ocd.get_user(user_id=user_id)
        username = "NotLoggedIn"
        logged_in = False
    elif user_id is not None:
        user = ocd.get_user(user_id=user_id)
        user.password = "Hidden"
        username = user.username

    # hide the password hash
    response_info = models.ResponseInfoLoginStatus(loggedIn = logged_in,
                                                   username = username,
                                                   request = request.url._url,
                                                   user=user,
                                                   timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')
                                                   )

    license_info_struct = models.LicenseInfoStruct(responseInfo = response_info, 
                                                   responseSet = None
                                                   )

    license_info = models.LicenseStatusInfo(licenseInfo = license_info_struct)
    return license_info

#-----------------------------------------------------------------------------
@app.get("/v2/Users/Login/", tags=["Session"]) # I like it under Users so I did them both.
@app.get("/v1/Login/", tags=["Session"])
def login_user(response: Response, 
               request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST),
               grant_type=None, 
               username=None, 
               password=None, 
               ka=False, 
               #user: bool = Depends(get_current_user)
               ):
    """
    ## Function
       <b>Login the user, via the URL per the GVPi API/PEPEasy interaction.</b>

       This may not be a good secure way to login.  May be deprecated 
          after the move from the GVPi server.  Newer clients
          should use the newer methods, when they are implemented
          in this new sever.


    ## Return Type
       models.LoginReturnItem

    ## Status
       This endpoint is working.
       
       Returns models.ErrorReturn on one error, otherwise throws exception.
       #TODO: Look into whether this is appropriate.

       TODO: Need to figure out the right way to do timeouts for this "easy" login.

    ## Sample Call
       /v1/Login/             (Needed to support the original version of the PEP API.)
       /v2/Users/Login/    

    ## Notes
    
    ## Potential Errors

    """
    logger.debug("Login via: /v1/(Users)?/Login/ - %s", username)
    err_code = None

    session_id = request.cookies.get(OPASSESSIONID) #  opasAPISupportLib.get_session_id(request)
    access_token = request.cookies.get(OPASACCESSTOKEN)   #  opasAPISupportLib.get_access_token(request)
    expiration_time = datetime.utcfromtimestamp(time.time() + opasAPISupportLib.get_max_age(keep_active=ka))
    # logger.debug(f"V1 Login Request: Expiration Time: {expiration_time}")
    if session_id not in ('', None) and access_token not in (None, ''):
        logger.debug("...note, already logged in...")
        pass # we are already logged in
    else: #
        logger.debug("Not logged in...Logging in")
        if username is not None and password is not None:
            ocd = opasCentralDBLib.opasCentralDB()    
            # now try to login (authenticate)
            status, user = ocd.authenticate_user(username, password)
            if user:
                # user is authenticated
                # we need to close any open sessions.
                if session_id is not None and access_token is not None:
                    # do a logout
                    session_end_time = datetime.utcfromtimestamp(time.time())
                    success = ocd.update_session(session_id=session_id, 
                                                 session_end=session_end_time
                                                 )    
                    #opasAPISupportLib.deleteCookies(resp, session_id="", accessToken="")
    
                # NOW lets give them a new session
                # new session and then token
                session_id = secrets.token_urlsafe(16)
                max_age = opasAPISupportLib.get_max_age(ka)
                user.start_date = user.start_date.timestamp()  # we may just want to null these in the jwt
                user.end_date = user.end_date.timestamp()
                user.last_update = user.last_update.timestamp()
                access_token = jwt.encode({'exp': expiration_time.timestamp(),
                                           'user': user.dict(), 
                                           'orig_session_id': session_id,
                                           },
                                          key=localsecrets.SECRET_KEY,
                                          algorithm=localsecrets.ALGORITHM)

                # start a new session, with this user (could even still be the old user
                ocd, session_info = opasAPISupportLib.start_new_session(response,
                                                                        request,
                                                                        session_id=session_id,
                                                                        access_token=access_token,
                                                                        user=user)
                # new code
                response.set_cookie(key=OPASSESSIONID,
                                    value=session_id,
                                    max_age=max_age, expires=None, 
                                    path="/",
                                    secure=False, 
                                    httponly=False)
    
                response.set_cookie(key=OPASACCESSTOKEN,
                                    value=access_token,
                                    max_age=max_age, expires=None, 
                                    path="/",
                                    secure=False, 
                                    httponly=False)
    
            else:
                access_token = None # user rejected
                err_code = response.status_code = HTTP_401_UNAUTHORIZED
                err_return = models.ErrorReturn(error = ERR_CREDENTIALS,
                                                error_message = ERR_MSG_LOGIN_CREDENTIALS)
    
        else: # Can't log in!
            raise HTTPException(
                status_code = HTTP_400_BAD_REQUEST, 
                detail = "Bad or incomplete login credentials"
            )

    # this simple return without responseInfo matches the GVPi server return.
    if err_code != None:
        return err_return
    else:
        try:
            login_return_item = models.LoginReturnItem(token_type = "bearer", 
                                                       session_id = session_id,
                                                       access_token = access_token,
                                                       authenticated = access_token is not None,
                                                       session_expires_time = expiration_time,
                                                       keep_active = ka,
                                                       error_message = None,
                                                       scope = None
                                                       )
        except ValidationError as e:
            logger.error(e.json())             

        return login_return_item

#-----------------------------------------------------------------------------
@app.get("/v2/Users/Logout/", tags=["Session"]) # I like it under Users so I did them both.
@app.get("/v1/Logout/", tags=["Session"])  # The original GVPi URL
def logout_user(response: Response, 
                request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST)):
    """
    ## Function
       <b>Close the user's session, and log them out.</b>

       /v1/Logout/ is used by the GVPi/PEPEasy current config.
                   It can be removed when we move off the GVPi server.
   
       /v2/Users/Logout/ is the newer path, parallels logout /v2/Users/Login/ for clarity.


    ## Return Type
       models.LicenseInfoStruct

    ## Status
       This endpoint is working.

    ## Sample Call
         /v1/Logout/
         /v2/Users/Logout/
    
    ## Notes
    
    ## Potential Errors

    """

    session_id = opasAPISupportLib.get_session_id(request)
    ocd = opasCentralDBLib.opasCentralDB()
    err_code = None
    if session_id is not None:
        session_info = ocd.get_session_from_db(session_id)
        session_end_time = datetime.utcfromtimestamp(time.time())
        success = ocd.update_session(session_id=session_id, 
                                     session_end=session_end_time
                                     )    
        if not success:
            #responseInfo = models.ResponseInfoLoginStatus(session_id = session_id)
            err_return = models.ErrorReturn(error = ERR_CONDITIONS, error_message = ERR_MSG_RECOVERABLE_CONDITION + " (SSave)")
            response_info = models.ResponseInfoLoginStatus(session_id = session_id, errors = err_return)
        else:    # all is well.
            response_info = models.ResponseInfoLoginStatus(sessionID = session_id)
            response_info.loggedIn = False
            # opasAPISupportLib.delete_cookies(response, session_id="", access_token="")
            response.set_cookie(key=OPASSESSIONID,
                                value='',
                                expires=None, 
                                path="/",
                                secure=False, 
                                httponly=False)

            response.set_cookie(key=OPASACCESSTOKEN,
                                value='',
                                expires=None, 
                                path="/",
                                secure=False, 
                                httponly=False)
            
    else:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=ERR_MSG_LOGOUT_UNSUPPORTED
        )

    if err_code != None:
        return err_return
    else:
        license_info_struct = models.LicenseInfoStruct( responseInfo = response_info, 
                                                        responseSet = []
                                                        )
        license_info = models.LicenseStatusInfo(licenseInfo = license_info_struct)
        return license_info

#---------------------------------------------------------------------------------------------------------
# this function lets various endpoints like search, searchanalysis, and document, share this large parameter set.
def parse_search_query_parameters(search=None,
                                  journal_name=None,
                                  journal=None,
                                  fulltext1=None,
                                  fulltext2=None,
                                  vol=None,
                                  issue=None,
                                  author=None,
                                  title=None,
                                  datetype=None,
                                  startyear=None,
                                  endyear=None,
                                  dreams=None,
                                  quotes=None,
                                  abstracts=None,
                                  dialogs=None,
                                  references=None,
                                  citecount=None, 
                                  viewcount=None, 
                                  viewed_within=None, 
                                  solrQ=None, 
                                  disMax=None, 
                                  edisMax=None, 
                                  quick_search=None, 
                                  sort=None, 
                                  ):

    # initialize accumulated variables
    search_q = "*:* "
    filter_q = "*:* "
    analyze_this = ""
    solr_max = None
    search_analysis_term_list = []

    if sort is not None:  # not sure why this seems to have a slash, but remove it
        sort = re.sub("\/", "", sort)

    if title is not None:
        analyze_this = "&& art_title_xml:{} ".format(title)
        filter_q += analyze_this
        search_analysis_term_list.append(analyze_this)  

    if journal_name is not None:
        analyze_this = "&& art_pepsourcetitle_fulltext:{} ".format(journal_name)
        filter_q += analyze_this
        search_analysis_term_list.append(analyze_this)  

    if journal is not None:
        code_for_query = ""
        analyze_this = ""
        # journal_code_list_pattern = "((?P<namelist>[A-z0-9]*[ ]*\+or\+[ ]*)+|(?P<namelist>[A-z0-9]))"
        journal_wildcard_pattern = r".*\*[ ]*"  # see if it ends in a * (wildcard)
        if re.match(journal_wildcard_pattern, journal):
            # it's a wildcard pattern
            code_for_query = journal
            analyze_this = "&& art_pepsourcetitlefull:{} ".format(code_for_query)
            filter_q += analyze_this
        else:
            journal_code_list = journal.split(" or ")
            if len(journal_code_list) > 1:
                # it was a list.
                code_for_query = " OR ".join(journal_code_list)
                analyze_this = "&& (art_pepsrccode:{}) ".format(code_for_query)
                filter_q += analyze_this
            else:
                sourceInfo = sourceInfoDB.lookupSourceCode(journal.upper())
                if sourceInfo is not None:
                    # it's a single source code
                    code_for_query = journal.upper()
                    analyze_this = "&& art_pepsrccode:{} ".format(code_for_query)
                    filter_q += analyze_this
                else: # not a pattern, or a code, or a list of codes.
                    # must be a name
                    code_for_query = journal
                    analyze_this = "&& art_pepsourcetitlefull:{} ".format(code_for_query)
                    filter_q += analyze_this

        search_analysis_term_list.append(analyze_this)
        # or it could be an abbreviation #TODO
        # or it counld be a complete name #TODO

    if vol is not None:
        analyze_this = "&& art_vol:{} ".format(vol)
        filter_q += analyze_this
        #searchAnalysisTermList.append(analyzeThis)  # Not collecting this!

    if issue is not None:
        analyze_this = "&& art_iss:{} ".format(issue)
        filter_q += analyze_this
        #searchAnalysisTermList.append(analyzeThis)  # Not collecting this!

    if author is not None:
        author = author.replace('"', '')
        analyze_this = "&& art_authors_xml:{} ".format(author)
        filter_q += analyze_this
        search_analysis_term_list.append(analyze_this)  

    if datetype is not None:
        #TODO for now, lets see if we need this. (We might)
        pass

    if startyear is not None and endyear is None:
        # put this in the filter query
        # parse startYear
        parsed_year_search = opasAPISupportLib.year_arg_parser(startyear)
        if parsed_year_search is not None:
            filter_q += parsed_year_search
            search_analysis_term_list.append(parsed_year_search)  
        else:
            logger.info("Search - StartYear bad argument {}".format(startyear))

    if startyear is not None and endyear is not None:
        # put this in the filter query
        # should check to see if they are each dates
        if re.match("[12][0-9]{3,3}", startyear) is None or re.match("[12][0-9]{3,3}", endyear) is None:
            logger.info("Search - StartYear {} /Endyear {} bad arguments".format(startyear, endyear))
        else:
            analyze_this = "&& art_year_int:[{} TO {}] ".format(startyear, endyear)
            filter_q += analyze_this
            search_analysis_term_list.append(analyze_this)

    if startyear is None and endyear is not None:
        if re.match("[12][0-9]{3,3}", endyear) is None:
            logger.info("Search - Endyear {} bad argument".format(endyear))
        else:
            analyze_this = "&& art_year_int:[{} TO {}] ".format("*", endyear)
            filter_q += analyze_this
            search_analysis_term_list.append(analyze_this)

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
        match_ptn = "(?P<nbr>[0-9]+)(\s+IN\s+(?P<period>(5|10|20|All)))?"
        m = re.match(match_ptn, citecount, re.IGNORECASE)
        if m is not None:
            val = m.group("nbr")
            period = m.group("period")

        if val is None:
            val = 1
        if period is None:
            period = '5'

        analyze_this = "&& art_cited_{}:[{} TO *] ".format(period.lower(), val)
        filter_q += analyze_this
        search_analysis_term_list.append(analyze_this)

    if fulltext1 is not None:
        analyze_this = "&& text:{} ".format(fulltext1)
        search_q += analyze_this
        search_analysis_term_list.append(analyze_this)

    if fulltext2 is not None:
        analyze_this = "&& text:{} ".format(fulltext2)
        search_q += analyze_this
        search_analysis_term_list.append(analyze_this)

    if dreams is not None:
        analyze_this = "&& dreams_xml:{} ".format(dreams)
        search_q += analyze_this
        search_analysis_term_list.append(analyze_this)

    if quotes is not None:
        analyze_this = "&& quotes_xml:{} ".format(quotes)
        search_q += analyze_this
        search_analysis_term_list.append(analyze_this)

    if abstracts is not None:
        analyze_this = "&& abstracts_xml:{} ".format(abstracts)
        search_q += analyze_this
        search_analysis_term_list.append(analyze_this)

    if dialogs is not None:
        analyze_this = "&& dialogs_xml:{} ".format(dialogs)
        search_q += analyze_this
        search_analysis_term_list.append(analyze_this)

    if references is not None:
        analyze_this = "&& references_xml:{} ".format(references)
        search_q += analyze_this
        search_analysis_term_list.append(analyze_this)

    if solrQ is not None:
        search_q = solrQ # (overrides fields) # search = solrQ
        search_analysis_term_list = [solrQ]

    if disMax is not None:
        search_q = disMax # (overrides fields) # search = solrQ
        solr_max = "disMax"

    if edisMax is not None:
        search_q = edisMax # (overrides fields) # search = solrQ
        solr_max = "edisMax"

    if quick_search is not None: #TODO - might want to change this to match PEP-Web best
        search_q = quick_search # (overrides fields) # search = solrQ
        solr_max = "edisMax"

    ret_val = models.QueryParameters(analyzeThis = analyze_this,
                                     searchQ = search_q,
                                     filterQ = filter_q,
                                     solrMax = solr_max,
                                     searchAnalysisTermList = search_analysis_term_list,
                                     solrSortBy = sort
    )

    return ret_val

#---------------------------------------------------------------------------------------------------------
@app.get("/v2/Database/MoreLikeThese/", response_model=models.DocumentList, response_model_skip_defaults=True, tags=["Database"])
@app.get("/v1/Database/SearchAnalysis/", response_model=models.DocumentList, response_model_skip_defaults=True, tags=["Database"])
@app.get("/v1/Database/Search/", response_model=models.DocumentList, response_model_skip_defaults=True, tags=["Database"])
async def search_the_document_database(response: Response, 
                                       request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST),  
                                       search: str=Query(None, title="Document request, with a search", description="This is a document request, with a search"),  
                                       journalName: str=Query(None, title="Match PEP Journal or Source Name", description="PEP part of a Journal, Book, or Video name (e.g., 'international'),", min_length=2),  
                                       journal: str=Query(None, title="Match PEP Journal or Source Code", description="PEP Journal Code (e.g., APA, CPS, IJP, PAQ),", min_length=2), 
                                       fulltext1: str=Query(None, title="Search for Words or phrases", description="Words or phrases (in quotes) anywhere in the document"),
                                       fulltext2: str=Query(None, title="Search for Words or phrases", description="Words or phrases (in quotes) anywhere in the document"),
                                       volume: str=Query(None, title="Match Volume Number", description="The volume number if the source has one"), 
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
                                       sortBy: str=Query("score desc", title="Field names to sort by", description="Comma separated list of field names to sort by"),
                                       limit: int=Query(15, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                                       offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                                       ):
    """
    ## Function
       <b>Search the database per one or more of the fields specified.</b>

       This code is front end for three endpoints in order to only have to code parameter handling once 
       (since they all would use the same parameters), easily distinguished here by the calling path.
   
       Some of the fields should be deprecated, but for now, they support PEP-Easy, as configured to use the GVPi based PEP Server
   
       MoreLikeThis and SearchAnalysis are brand new (20190625), and there right now for experimentation
   
       Trying to reduce these by making them "smarter". For example, 
           endyear isn't needed, because startyear can handle the ranges (and better than before).
           journal is also configured to take anything that would have otherwise been entered in journalName
   
    ## Return Type
       models.DocumentList

    ## Status
       Status: In Development

       #TODO:    
          viewcount, viewedWithin not yet implemented...and probably will be streamlined for future use.
          disMax, edisMax also not yet implemented


    ## Sample Call
         /v2/Database/MoreLikeThese/
         /v1/Database/SearchAnalysis/
         /v1/Database/Search/"
    
    ## Notes
    
    ## Potential Errors
    
    """

    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    session_id = session_info.session_id 

    if re.search(r"/Search/", request.url._url):
        logger.debug("Search Request: %s", request.url._url)

    if re.search(r"/SearchAnalysis/", request.url._url):
        logger.debug("Analysis Request: %s", request.url._url)
        analysis_mode = True
    else:
        analysis_mode = False

    if re.search(r"/MoreLikeThese/", request.url._url):
        logger.debug("MoreLikeThese Request: %s", request.url._url)
        more_like_these_mode = True
    else:
        more_like_these_mode = False

    current_year = datetime.utcfromtimestamp(time.time()).strftime('%Y')
    # this does intelligent processing of the query parameters and returns a smaller set of solr oriented         
    # params (per pydantic model QueryParameters), ready to use
    solr_query_params = parse_search_query_parameters(search=search,
                                                      journal_name=journalName,
                                                      journal=journal,
                                                      fulltext1=fulltext1,
                                                      fulltext2=fulltext2,
                                                      vol=volume,
                                                      issue=issue,
                                                      author=author,
                                                      title=title,
                                                      startyear=startyear,
                                                      endyear=endyear,
                                                      dreams=dreams,
                                                      quotes=quotes,
                                                      abstracts=abstracts,
                                                      dialogs=dialogs,
                                                      references=references,
                                                      citecount=citecount,
                                                      viewcount=viewcount,
                                                      viewed_within=viewedWithin,
                                                      solrQ=solrQ,
                                                      disMax=disMax,
                                                      edisMax=edisMax,
                                                      quick_search=quickSearch,
                                                      sort = sortBy
                                                      )

    solr_query_params.urlRequest = request.url._url

    # We don't always need full-text, but if we need to request the doc later we'll need to repeat the search parameters plus the docID
    if analysis_mode:
        ret_val = opasAPISupportLib.search_analysis(query_list=solr_query_params.searchAnalysisTermList, 
                                                    filter_query = None,
                                                    dis_max = solr_query_params.solrMax,
                                                    query_analysis=analysis_mode,
                                                    more_like_these = None,
                                                    full_text_requested=False,
                                                    limit=limit
                                                    )

        statusMsg = "{} terms/clauses; queryAnalysis: {}".format(len(solr_query_params.searchAnalysisTermList), 
                                                                 more_like_these_mode, 
                                                                 analysis_mode)
        logger.debug("Done with search analysis.")
    else:  # we are going to do a regular search
        logger.debug("....searchQ = %s", solr_query_params.searchQ)
        logger.debug("....filterQ = %s", solr_query_params.filterQ)

        # note: this now returns a tuple...t
        ret_val, ret_status = opasAPISupportLib.search_text(query=solr_query_params.searchQ, 
                                                            filter_query = solr_query_params.filterQ,
                                                            full_text_requested=False,
                                                            query_debug = False,
                                                            more_like_these = more_like_these_mode,
                                                            dis_max = solr_query_params.solrMax,
                                                            sort_by = sortBy,
                                                            limit=limit, 
                                                            offset=offset,
                                                            extra_context_len=200
                                                            )

        #  if there's a Solr server error in the call, it returns a non-200 ret_status[0]
        if ret_status[0] != HTTP_200_OK:
            #  throw an exception rather than return an object (which will fail)
            raise HTTPException(
                status_code=ret_status[0], 
                detail=f"Bad Solr Search Request. {ret_status[1].reason}:{ret_status[1].body}"
            )
        
        if ret_val != {}:
            matches = len(ret_val.documentList.responseSet)
            ret_val.documentList.responseInfo.request = request.url._url
        else:
            matches = 0
            
        logger.debug(f"....matches = {matches}")
        # fill in additional return structure status info
        statusMsg = f"{matches} hits; moreLikeThese:{more_like_these_mode}; queryAnalysis: {analysis_mode}"
        logger.debug("Done with search.")

    # client_host = request.client.host

    if not analysis_mode: # too slow to do this for that.
        ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_DATABASE_SEARCH,
                                    session_info=session_info, 
                                    params=request.url._url,
                                    status_message=statusMsg
                                    )

    return ret_val

@app.get("/v1/Database/MostDownloaded/", response_model=models.DocumentList, response_model_skip_defaults=True, tags=["Database"])
def get_the_most_viewed_articles(response: Response,
                                 request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                                 period: str=Query('5', title="Period (5, 10, 20, or all)", description=opasConfig.DESCRIPTION_MOST_CITED_PERIOD),
                                 limit: int=Query(5, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                                 offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                                 ):
    """
    ## Function
       <b>Return a list of documents which are the most downloaded (viewed)</b>


    ## Return Type
       models.DocumentList

    ## Status
       This endpoint is working.

    ## Sample Call
         /v1/Database/MostDownloaded/
    
    ## Notes
    
    ## Potential Errors

    """

    # ocd, session_info = opasAPISupportLib.get_session_info(request, resp)

    logger.debug("in most viewed")
    try:
        ret_val = opasAPISupportLib.database_get_most_downloaded(period=period,
                                                                limit=limit,
                                                                offset=offset)
        # fill in additional return structure status info
        # client_host = request.client.host
        ret_val.documentList.responseInfo.request = request.url._url
    except Exception as e:
        status_message = "Error: {}".format(e)
        ret_val = None
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, 
            detail=status_message
        )        
    else:
        status_message = "Success"
        status_code = 200

    # Don't record endpoint use (not a user request, just a default)
    #ocd, session_info = opasAPISupportLib.get_session_info(request, resp)
    #ocd.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_DATABASE_MOSTCITED,
                                #session_info=session_info,
                                #params=request.url._url,
                                #returnStatusCode = statusCode,
                                #statusMessage=statusMessage
                                #)

    logger.debug("out most viewed")
    return ret_val  # document_list

@app.get("/v1/Database/MostCited/", response_model=models.DocumentList, response_model_skip_defaults=True, tags=["Database"])
def get_the_most_cited_articles(response: Response,
                                request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                                period: str=Query('5', title="Period (5, 10, 20, or all)", description=opasConfig.DESCRIPTION_MOST_CITED_PERIOD),
                                limit: int=Query(10, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                                offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                                ):
    """
    ## Function
       <b>Return a list of documents for a SourceCode source (and optional year specified in query params).</b>  

       Note: The GVPi implementation does not appear to support the limit and offset parameter


    ## Return Type
       models.DocumentList

    ## Status
       This endpoint is working.

    ## Sample Call
         /v1/Database/MostCited/
    
    ## Notes
    
    ## Potential Errors

    """

    time.sleep(.25)
    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    session_id = session_info.session_id 

    #print ("in most cited")
    try:
        # return documentList
        ret_val = opasAPISupportLib.database_get_most_cited(period=period, limit=limit, offset=offset)
        # fill in additional return structure status info
        # client_host = request.client.host
        ret_val.documentList.responseInfo.request = request.url._url
    except Exception as e:
        status_message = "Error: {}".format(e)
        ret_val = None
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=status_message
        )
    else:
        status_message = "Success"
        status_code = 200

    # Don't record in final build - (ok for now during testing)
    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_DATABASE_MOSTCITED,
                                session_info=session_info, 
                                params=request.url._url,
                                return_status_code = status_code,
                                status_message=status_message
                                )

    #print ("out mostcited")
    return ret_val

@app.get("/v1/Database/WhatsNew/", response_model=models.WhatsNewList, response_model_skip_defaults=True, tags=["Database"])
def get_the_newest_uploaded_issues(response: Response,
                                   request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                                   days_back: int=Query(14, title="Number of days to look back", description=opasConfig.DESCRIPTION_DAYSBACK),
                                   limit: int=Query(5, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                                   offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                                   ):  
    """
    ## Function
       <b>Return a list of issues for journals modified in the last week).</b>  


    ## Return Type
       models.WhatsNewList

    ## Status
       This endpoint is working.

    ## Sample Call
         /v1/Database/WhatsNew/
    
    ## Notes
    
    ## Potential Errors

    """
    # (Don't log calls to this endpoint)
    
    time.sleep(1.25)  # let it wait
    try:
        # return whatsNewList
        ret_val = opasAPISupportLib.database_get_whats_new(limit=limit, 
                                                       offset=offset,
                                                       days_back=days_back)

    except Exception as e:
        e = str(e)
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                            detail="Error: {}".format(e.replace("'", "\\'"))
        )
    else:
        # response.status_message = "Success"
        response.status_code = HTTP_200_OK
        ret_val.whatsNew.responseInfo.request = request.url._url

    return ret_val

##-----------------------------------------------------------------------------
#@app.get("/v1/Metadata/Banners/", response_model_skip_defaults=True, tags=["Metadata"])
#def get_banners(response: Response, 
                #request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST),
                #):
    #"""
    #Return information on the location of a source's banner.
    #This v1 endpoint has not yet been used by a client.  
    #DEPRECATED.
    #Use /v1/Metadata/{SourceType}/ instead

    #"""
    #errCode = response.status_code = HTTP_400_BAD_REQUEST
    #errorMessage = "Error: {}".format("This endpoint is was unused and is now deprecated. Use /v1/Metadata/{SourceType}/ instead")
    #errReturn = models.ErrorReturn(error = ERR_MSG_DEPRECATED, error_message = errorMessage)

    #return errReturn
##-----------------------------------------------------------------------------
#@app.get("/v1/Metadata/Banners/{SourceCode}", response_model_skip_defaults=True, tags=["Metadata"])
#def get_banners(response Response, 
                #request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST),
                #SourceCode: str=Path(..., title="PEP Code for Source", description=opasConfig.DESCRIPTION_SOURCECODE), 
                #):
    #"""
    #Return information on the location of a source's banner.
    #This v1 endpoint has not yet been used by a client.  
    #DEPRECATED.
    #Use /v1/Metadata/{SourceType}/ instead

    #"""
    #errCode = resp.status_code = HTTP_400_BAD_REQUEST
    #errorMessage = "Error: {}".format("This endpoint is was unused and is now deprecated. Use /v1/Metadata/{SourceType}/ instead")
    #errReturn = models.ErrorReturn(error = ERR_MSG_DEPRECATED, error_message = errorMessage)

    #return errReturn  
#-----------------------------------------------------------------------------
@app.get("/v1/Metadata/Contents/{SourceCode}/", response_model=models.DocumentList, response_model_skip_defaults=True, tags=["Metadata"])
def get_journal_content_lists(response: Response,
                              request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                              SourceCode: str=Path(..., title="PEP Code for Source", description=opasConfig.DESCRIPTION_SOURCECODE), 
                              year: str=Query("*", title="Contents Year", description="Year of source contents to return"),
                              limit: int=Query(15, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                              offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                              ):
    """
    ## Function
       <b>Return a list of documents for a SourceCode (and optional year specified in query params).</b>  

       Note: The GVPi implementation does not appear to support the limit and offset parameter

    ## Return Type
       models.DocumentList

    ## Status
       This endpoint is working.

    ## Sample Call
         /v1/Metadata/Contents/IJP/
    
    ## Notes
    
    ## Potential Errors

    """

    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    try:       
        ret_val = opasAPISupportLib.metadata_get_contents(SourceCode, year, limit=limit, offset=offset)
        # fill in additional return structure status info
        # client_host = request.client.host
    except Exception as e:
        status_message = "Error: {}".format(e)
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=status_message
        )
    else:
        status_message = "Success"
        status_code = HTTP_200_OK
        ret_val.documentList.responseInfo.request = request.url._url

    ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_METADATA_CONTENTS,
                                session_info=session_info, 
                                params=request.url._url,
                                item_of_interest="{}.{}".format(SourceCode, year), 
                                return_status_code = status_code,
                                status_message=status_message
                                )

    return ret_val # document_list

#-----------------------------------------------------------------------------
@app.get("/v1/Metadata/Contents/{SourceCode}/{SourceVolume}/", response_model=models.DocumentList, response_model_skip_defaults=True, tags=["Metadata"])
def get_journal_content_lists_for_volume(SourceCode: str, 
                                         SourceVolume: str, 
                                         response: Response,
                                         request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                                         year: str=Query("*", title="HTTP Request", description=opasConfig.DESCRIPTION_YEAR),
                                         limit: int=Query(15, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                                         offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                                         ):
    """
    ## Function
       <b>Return a list of documents for a SourceCode and Source Volume (required).</b>  

       Year can also be optionally specified in query params.  

    ## Return Type
       models.DocumentList

    ## Status
       This endpoint is working.

    ## Sample Call
         /v1/Metadata/Contents/IJP/77/
         http://development.org:9100/v1/Metadata/Contents/IJP/77/
    
    ## Notes
    
    ## Potential Errors

    """

    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    try:
        ret_val = documentList = opasAPISupportLib.metadata_get_contents(SourceCode, year, vol=SourceVolume, limit=limit, offset=offset)
        # fill in additional return structure status info
        # client_host = request.client.host
    except Exception as e:
        status_message = "Error: {}".format(e)
        logger.error(status_message)
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=status_message
        )
    else:
        status_message = "Success"
        status_code = HTTP_200_OK
        ret_val.documentList.responseInfo.request = request.url._url

    ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_METADATA_CONTENTS_FOR_VOL,
                                session_info=session_info, 
                                item_of_interest="{}.{}".format(SourceCode, SourceVolume), 
                                params=request.url._url,
                                return_status_code = status_code,
                                status_message=status_message
                                )
    return ret_val

#-----------------------------------------------------------------------------
@app.get("/v1/Metadata/Videos/", response_model=models.VideoInfoList, response_model_skip_defaults=True, tags=["Metadata"])
def get_a_list_of_video_names(response: Response,
                              request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                              SourceCode: str=Query("*", title="PEP Code for Source", description=opasConfig.DESCRIPTION_SOURCECODE), 
                              limit: int=Query(200, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                              offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                             ):
    """
    ## Function
    <b>Get a complete list of journal names</b>

    ## Return Type
       models.VideoInfoList

    ## Status
       This endpoint is working.

    ## Sample Call
         /v1/Metadata/Videos/
    
    ## Notes
    
    ## Potential Errors

    """
    ret_val = get_a_list_of_source_names(response, request, SourceType="Video", SourceCode=SourceCode, limit=limit, offset=offset)
    return ret_val

#-----------------------------------------------------------------------------
@app.get("/v1/Metadata/Journals/", response_model=models.JournalInfoList, response_model_skip_defaults=True, tags=["Metadata"])
def get_a_list_of_journal_names(response: Response,
                                request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                                SourceCode: str=Query("*", title="PEP Code for Source", description=opasConfig.DESCRIPTION_SOURCECODE), 
                                limit: int=Query(200, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                                offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                                ):
    """
    ## Function
    <b>Get a complete list of journal names</b>

    ## Return Type
       models.JournalInfoList

    ## Status
       This endpoint is working.

    ## Sample Call
         /v2/Documents/Glossary/{term_id}
    
    ## Notes
    
    ## Potential Errors
        
    """
    ret_val = get_a_list_of_source_names(response, request, SourceType="Journal", SourceCode=SourceCode, limit=limit, offset=offset)
    return ret_val

#-----------------------------------------------------------------------------
@app.get("/v1/Metadata/Volumes/{SourceCode}/", response_model=models.VolumeList, response_model_skip_defaults=True, tags=["Metadata"])
def get_a_list_of_volumes_for_a_journal(response: Response,
                                        request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                                        SourceCode: str=Path(..., title="Code for a Source", description=opasConfig.DESCRIPTION_SOURCECODE), 
                                        limit: int=Query(opasConfig.DEFAULT_LIMIT_FOR_VOLUME_LISTS, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                                        offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                                        ):
    """
    ## Function
       <b>Return a list of volumes for a SourceCode (aka, PEPCode (e.g., IJP)) per the limit and offset parameters</b> 

    ## Return Type
       models.JournalInfoList

    ## Status
       This endpoint is working.

    ## Sample Call
         http://localhost:9100/v1/Metadata/Volumes/CPS/
    
    ## Notes
    
    ## Potential Errors
        
    """

    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    src_exists = ocd.get_sources(source=SourceCode)
    if not src_exists[0]:
        response.status_code = HTTP_400_BAD_REQUEST
        status_message = f"Failure: Bad SourceCode {SourceCode}"
        ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_METADATA_VOLUME_INDEX,
                                    session_info=session_info, 
                                    params=request.url._url,
                                    item_of_interest=f"{SourceCode}", 
                                    return_status_code=response.status_code,
                                    status_message=status_message
                                    )
        raise HTTPException(
            status_code=response.status_code,
            detail=status_message
        )
    else:
        try:
            ret_val = opasAPISupportLib.metadata_get_volumes(SourceCode, limit=limit, offset=offset)
        except Exception as e:
            response.status_code = HTTP_400_BAD_REQUEST,
            status_message = "Error: {}".format(e)
            ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_METADATA_VOLUME_INDEX,
                                        session_info=session_info, 
                                        params=request.url._url,
                                        item_of_interest=f"{SourceCode}", 
                                        return_status_code=response.status_code,
                                        status_message=status_message
                                        )
            raise HTTPException(
                status_code=response.status_code, 
                detail=status_message
            )
        else:
            response.status_code = HTTP_200_OK
            status_message = "Success"
            ret_val.volumeList.responseInfo.request = request.url._url
            ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_METADATA_VOLUME_INDEX,
                                        session_info=session_info, 
                                        params=request.url._url,
                                        item_of_interest=f"{SourceCode}", 
                                        return_status_code=response.status_code,
                                        status_message=status_message
                                        )

    return ret_val # returns volumeList
#-----------------------------------------------------------------------------
@app.get("/v1/Metadata/Books/", response_model=models.SourceInfoList, response_model_skip_defaults=True, tags=["Metadata"])
def get_a_list_of_book_names(response: Response,
                             request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                             SourceCode: str=Query("*", title="PEP Code for Source", description=opasConfig.DESCRIPTION_SOURCECODE), 
                             limit: int=Query(200, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                             offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                             ):
    """
    ## Function
       <b>Get a list of Book names equivalent to what is displayed on the original PEP-Web in the books tab.</b>

       The data is pulled from the database ISSN table.  Subvolumes, of SE and GW are not returned, nor is any volume
       marked with multivolumesubbok in the src_type_qualifier column.  This is exactly what's currently in PEP-Web's
       presentation today.

    ## Return Type
       models.SourceInfoList

    ## Status
       This endpoint is working.

    ## Sample Call
         http://localhost:9100/v1/Metadata/Books
    
    ## Notes
    
    ## Potential Errors
        
    """

    ret_val = get_a_list_of_source_names(response, request, SourceType="Book", SourceCode=SourceCode, limit=limit, offset=offset)
    return ret_val

#-----------------------------------------------------------------------------
@app.get("/v1/Metadata/{SourceType}/{SourceCode}/", response_model=models.SourceInfoList, response_model_skip_defaults=True, tags=["Metadata"])
def get_a_list_of_source_names(response: Response,
                               request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                               SourceType: str=Path(..., title="Source Type", description=opasConfig.DESCRIPTION_SOURCETYPE), 
                               SourceCode: str=Path(..., title="PEP Code for Source", description=opasConfig.DESCRIPTION_SOURCECODE), 
                               limit: int=Query(200, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                               offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                               ):
    """

    ## Function
       <b>Return a list of information about a source type, e.g., journal names</b>

       The data is pulled from the database ISSN table.  Subvolumes, of SE and GW are not returned, nor is any volume
       marked with multivolumesubbok in the src_type_qualifier column.  This is exactly what's currently in PEP-Web's
       presentation today.

    ## Return Type
       models.SourceInfoList

    ## Status
       This endpoint is working.

    ## Sample Call
         http://localhost:9100/v1/Metadata/Books/IPL
    
    ## Notes
    
    ## Potential Errors
        

    """

    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    try:    
        if SourceCode == "*" or SourceType != "Journal":
            ret_val = source_info_list = opasAPISupportLib.metadata_get_source_by_type(src_type=SourceType, src_code=SourceCode, limit=limit, offset=offset)
        else:
            ret_val = source_info_list = opasAPISupportLib.metadata_get_source_by_code(src_code=SourceCode, limit=limit, offset=offset)            

    except Exception as e:
        status_message = "Error: {}".format(e)
        logger.error(status_message)
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=status_message
        )
    else:
        status_message = "Success"
        response.status_code = HTTP_200_OK
        # fill in additional return structure status info
        ret_val.sourceInfo.responseInfo.request = request.url._url

    ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_METADATA_SOURCEINFO,
                                session_info=session_info, 
                                params=request.url._url,
                                item_of_interest="{}".format(SourceType), 
                                return_status_code = response.status_code,
                                status_message=status_message
                                )

    return ret_val
#-----------------------------------------------------------------------------
@app.get("/v1/Authors/Index/{authorNamePartial}/", response_model=models.AuthorIndex, response_model_skip_defaults=True, tags=["Authors"])
def get_author_index_for_matching_author_names(response: Response,
                                               request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                                               authorNamePartial: str=Path(..., title="Author name or Partial Name", description=opasConfig.DESCRIPTION_AUTHORNAMEORPARTIAL), 
                                               limit: int=Query(15, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                                               offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                                               ):
    """
    ## Function
       <b>Return a list (index) of authors.  The list shows the author IDs, which are a normalized form of an authors name.</b>

    ## Return Type
       models.AuthorIndex

    ## Status
       This endpoint is working.

    ## Sample Call
       http://localhost:9100/v1/Authors/Index/Tuck/

    ## Notes
    
    ## Potential Errors
        
    """
    ret_val = None 

    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    try:
        # returns models.AuthorIndex
        author_name_to_check = authorNamePartial.lower()  # work with lower case only, since Solr is case sensitive.
        ret_val = opasAPISupportLib.authors_get_author_info(author_name_to_check, limit=limit, offset=offset)
    except ConnectionRefusedError as e:
        logger.error(f"The server is not running or is currently not accepting connections: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=status_message
        )

    except Exception as e:
        logger.error("Error: {}".format(e))
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=status_message
        )
    else:
        status_message = "Success"
        response.status_code = HTTP_200_OK
        # fill in additional return structure status info
        ret_val.authorIndex.responseInfo.request = request.url._url

    # for speed since this is used for author pick lists, don't log the endpoint occurrences
    #ocd.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_AUTHORS_INDEX,
                                        #params=request.url._url,
                                        #returnStatusCode = resp.status_code = ,
                                        #statusMessage=statusMessage
                                        #)

    return ret_val  # Return author information or error

#-----------------------------------------------------------------------------
@app.get("/v1/Authors/Publications/{authorNamePartial}/", response_model=models.AuthorPubList, response_model_skip_defaults=True, tags=["Authors"])
def get_author_pubs_for_matching_author_names(response: Response,
                                              request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                                              authorNamePartial: str=Path(..., title="Author name or Partial Name", description=opasConfig.DESCRIPTION_AUTHORNAMEORPARTIAL), 
                                              limit: int=Query(15, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                                              offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                                              ):
    """
    ## Function
       <b>Return a list of the author's publications.</b>  
       regex style wildcards are permitted.

    ## Return Type
       models.AuthorPubList

    ## Status
       This endpoint is working.

    ## Sample Call
       http://localhost:8000/v1/Authors/Publications/Tuck/
       http://localhost:8000/v1/Authors/Publications/maslow, a.*/

    ## Notes
    
    ## Potential Errors
        
    """
    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    try:
        author_name_to_check = authorNamePartial.lower()  # work with lower case only, since Solr is case sensitive.
        ret_val = opasAPISupportLib.authors_get_author_publications(author_name_to_check, limit=limit, offset=offset)
    except Exception as e:
        response.status_code=HTTP_500_INTERNAL_SERVER_ERROR
        status_message = f"Error: {e}"
        logger.error(status_message)
        raise HTTPException(
            status_code=response.status_code,
            detail=status_message
        )
    else:
        status_message = "Success"
        ret_val.authorPubList.responseInfo.request = request.url._url
        response.status_code = HTTP_200_OK
        ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_AUTHORS_PUBLICATIONS,
                                    session_info=session_info, 
                                    params=request.url._url,
                                    item_of_interest=f"{authorNamePartial}", 
                                    return_status_code = response.status_code,
                                    status_message=status_message
                                    )

    return ret_val

@app.get("/v1/Documents/Abstracts/{documentID}/", response_model=models.Documents, response_model_skip_defaults=True, tags=["Documents"])
def view_an_abstract(response: Response,
                     request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                     documentID: str=Path(..., title="Document ID or Partial ID", description=opasConfig.DESCRIPTION_DOCIDORPARTIAL), 
                     return_format: str=Query("TEXTONLY", title="Document return format", description=opasConfig.DESCRIPTION_RETURNFORMATS),
                     limit: int=Query(5, title="Document return limit", description=opasConfig.DESCRIPTION_LIMIT),
                     offset: int=Query(0, title="Document return offset", description=opasConfig.DESCRIPTION_OFFSET)
                     ):
    """
    ## Function
       <b>Return an abstract for the requested documentID (e.g., IJP.077.0001A, or multiple abstracts
          for a partial ID (e.g., IJP.077)</b>

    ## Return Type
       models.Documents

    ## Status
       This endpoint is working.

    ## Sample Call
         /v1/Documents/Abstracts/IJP.001.0203A/
         http://localhost:9100/v1/Documents/Abstracts/IJP.001.0203A/
    
    ## Notes
    
    ## Potential Errors

    """

    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    try:
        ret_val = documents = opasAPISupportLib.documents_get_abstracts(documentID, ret_format=return_format, limit=limit, offset=offset)
    except Exception as e:
        response.status_code=HTTP_400_BAD_REQUEST
        status_message = f"Error: {e}"
        logger.error(status_message)
        ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_DOCUMENTS_ABSTRACTS,
                                    session_info=session_info, 
                                    params=request.url._url,
                                    item_of_interest=f"{documentID}", 
                                    return_status_code = status_code,
                                    status_message=status_message
                                    )
        raise HTTPException(
            status_code=status_code,
            detail=status_message
        )
    else:
        status_message = "Success"
        response.status_code = HTTP_200_OK
        #client_host = request.client.host
        ret_val.documents.responseInfo.request = request.url._url
        ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_DOCUMENTS_ABSTRACTS,
                                    session_info=session_info, 
                                    params=request.url._url,
                                    item_of_interest=f"{documentID}", 
                                    return_status_code = response.status_code,
                                    status_message=status_message
                                    )
    return ret_val

@app.get("/v2/Documents/Glossary/{term_id}/", response_model=models.Documents, tags=["Documents"], response_model_skip_defaults=True)  # the current PEP API
def view_a_glossary_entry(response: Response,
                          request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                          term_id: str=Path(..., title="Document ID or Partial ID", description=opasConfig.DESCRIPTION_DOCIDORPARTIAL),
                          search: str=Query(None, title="Document request from search results", description="This is a document request, including search parameters, to show hits"),
                          return_format: str=Query("HTML", title="Glossary return format", description=opasConfig.DESCRIPTION_RETURNFORMATS)
                          ): # Note this is called by the Document endpoint if it detects a term_id in the DocumentID
    """
    ## Function
       <b>Return a glossary entry for the specified {termID} if authenticated.  If not, returns error.</b>

    ## Return Type
       models.Documents

    ## Status
       This endpoint is working.

    ## Sample Call
         /v2/Documents/Glossary/{term_id}

         http://localhost:9100/v2/Documents/Document/YP0004173238470/
    
    ## Notes
         In V1, glossary entries are fetched via the /v1/Documents endpoint
    
    ## Potential Errors
       USER NEEDS TO BE AUTHENTICATED for glossary access at the term level.  Otherwise, returns error.
        
       Client apps should disable the glossary links when not authenticated.
    """
    ret_val = None
    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    # is the user authenticated? 
    # is this document embargoed?
    # the App should not call here if not authenticated.
    if not session_info.authenticated:
        response.status_code = HTTP_400_BAD_REQUEST
        status_message = f"Must be logged in to view a glossary entry."
        ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_DOCUMENTS,
                                    session_info=session_info, 
                                    params=request.url._url,
                                    item_of_interest=term_id, 
                                    return_status_code = response.status_code,
                                    status_message=status_message
                                    )
        raise HTTPException(
            status_code = response.status_code,
            detail = status_message
        )

    try:
        if search is not None:
            arg_dict = dict(parse.parse_qsl(parse.urlsplit(search).query))
            if term_id is not None:
                # make sure this is part of the last search set.
                j = arg_dict.get("journal")
                if j is not None:
                    if j not in term_id:
                        arg_dict["journal"] = None
        else:
            arg_dict = {}

        try:
            term_parts = term_id.split(".")
            if len(term_parts) == 4:
                term_id = term_parts[-2]
            elif len(term_parts) == 3:
                term_id = term_parts[-1]
            else:
                pass
            logger.debug("Glossary View Request (term_id/return_format): %s/%s", term_id, return_format)

        except Exception as e:
            logger.debug("Error splitting term: %s", e)
            #raise HTTPException(
                #status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                #detail=status_message
            #)
            #Keep it as is
            #termID = termID


        ret_val = opasAPISupportLib.documents_get_glossary_entry(term_id, 
                                                                 retFormat=return_format, 
                                                                 authenticated = session_info.authenticated)
        ret_val.documents.responseInfo.request = request.url._url

    except Exception as e:
        response.status_code = HTTP_400_BAD_REQUEST
        status_message = f"View Glossary Error: {e}"
        logger.error(status_message)
        ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_DOCUMENTS,
                                    session_info=session_info, 
                                    params=request.url._url,
                                    item_of_interest=term_id, 
                                    return_status_code = response.status_code,
                                    status_message=status_message
                                    )
        raise HTTPException(
            status_code=status_code,
            detail=status_message
        )
    else:
        status_message = "Success"
        response.status_code = HTTP_200_OK
        ret_val.documents.responseInfo.request = request.url._url
        ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_DOCUMENTS,
                                    session_info=session_info, 
                                    params=request.url._url,
                                    item_of_interest=term_id, 
                                    return_status_code = response.status_code,
                                    status_message=status_message
                                    )
    return ret_val


@app.get("/v2/Documents/Document/{documentID}/", response_model=models.Documents, tags=["Documents"], response_model_skip_defaults=True) # more consistent with the model grouping
@app.get("/v1/Documents/{documentID}/", response_model=models.Documents, tags=["Documents"], response_model_skip_defaults=True)  # the current PEP API
def view_a_document(response: Response,
                    request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                    documentID: str=Path(..., title="Document ID or Partial ID", description=opasConfig.DESCRIPTION_DOCIDORPARTIAL), 
                    offset: int=Query(0, title="Document Page offset", description=opasConfig.DESCRIPTION_PAGEOFFSET),
                    page: int=Query(None, title="Document Page Request (from document pagination)", description=opasConfig.DESCRIPTION_PAGEREQUEST),
                    return_format: str=Query("HTML", title="Document return format", description=opasConfig.DESCRIPTION_RETURNFORMATS),
                    search: str=Query(None, title="Document request from search results", description="This is a document request, including search parameters, to show hits"),
                    ):
    """
    ## Function
       <b>Return Document information (summary, non-authenticated) or the document itself (authenticated) for the requested documentID (e.g., IJP.077.0001A,
        or multiple documents for a partial ID (e.g., IJP.077)</b>

    ## Return Type
       models.Documents

    ## Status
       This endpoint is working.

    ## Sample Call
         http://localhost:9100/v1/Documents/IJP.077.0217A/
    
    ## Notes
    
    ## Potential Errors
       USER NEEDS TO BE AUTHENTICATED to return a document.
       
       If not authenticated:
          - The PEP developed server/API for V1 and V2 will return an abstract or summary if non-authenticated.
       
          - The GVPI V1 API returns an error if not 
        
    """
    # NOTE: Calls the code for the Glossary endpoint via function view_a_glossary_entry)

    ret_val = None
    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    #session_id = session_info.session_id
    # is this document embargoed?
    # check if this is a Glossary request, this is per API.v1.
    m = re.match("(ZBK\.069\..*?)?(?P<termid>(Y.0.*))", documentID)
    if m is not None:    
        # this is a glossary request, submit only the termID
        term_id = m.group("termid")
        ret_val = view_a_glossary_entry(response, request, term_id=term_id, search=search, return_format=return_format)
    else:
        try:
            logger.debug("TODO: CHECK IF USER IS AUTHENTICATED for document download")
            # is the user authenticated? if so, loggedIn is true
            if session_info.authenticated:
                if search is not None:
                    argdict = dict(parse.parse_qsl(parse.urlsplit(search).query))
                    if documentID is not None:
                        # make sure this is part of the last search set.
                        j = argdict.get("journal")
                        if j is not None:
                            if j not in documentID:
                                argdict["journal"] = None
                else:
                    argdict = {}

                solr_query_params = parse_search_query_parameters(**argdict)
                logger.debug("Document View Request: %s/%s/%s", solr_query_params, documentID, return_format)

                ret_val = opasAPISupportLib.documents_get_document( documentID, 
                                                                    solr_query_params,
                                                                    ret_format=return_format, 
                                                                    authenticated = session_info.authenticated
                                                                    )
            else:
                logger.debug("user is not authenticated.  Returning abstract only)")

                ret_val = opasAPISupportLib.documents_get_abstracts( documentID,
                                                                     ret_format="TEXTONLY",
                                                                     authenticated=None,
                                                                     limit=opasConfig.DEFAULT_LIMIT_FOR_SOLR_RETURNS,
                                                                     offset=0
                                                                     )

        except Exception as e:
            response.status_code=HTTP_400_BAD_REQUEST
            status_message = "View Document Error: {}".format(e)
            logger.error(status_message)
            ret_val = None
            ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_DOCUMENTS,
                                        session_info=session_info, 
                                        params=request.url._url,
                                        item_of_interest="{}".format(documentID), 
                                        return_status_code = response.status_code,
                                        status_message=status_message
                                        )
            raise HTTPException(
                status_code=response.status_code,
                detail=status_message
            )
        else:
            response.status_code = HTTP_200_OK
            status_message = "Success"
            ret_val.documents.responseInfo.request = request.url._url
            ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_DOCUMENTS,
                                        session_info=session_info, 
                                        params=request.url._url,
                                        item_of_interest="{}".format(documentID), 
                                        return_status_code = response.status_code,
                                        status_message=status_message
                                        )
    return ret_val

@app.get("/v1/Documents/Downloads/{retFormat}/{documentID}/", response_model_skip_defaults=True, tags=["Documents"])
def download_a_document(response: Response,
                        request: Request=Query(None, title="HTTP Request", description=opasConfig.DESCRIPTION_REQUEST), 
                        documentID: str=Path(..., title="Document ID or Partial ID", description=opasConfig.DESCRIPTION_DOCIDORPARTIAL), 
                        retFormat=Path(..., title="Download Format", description=opasConfig.DESCRIPTION_DOCDOWNLOADFORMAT),
                        ):
    """
    ## Function
       <b>Initiates download of the document in EPUB or PDF format (if authenticated)</b>

    ## Return Type
       initiates a download of the requested document type

    ## Status
       This endpoint is working.
       There may be more work needed on the conversions:
          ePub conversion (links go nowhere in the tests I did' need to compare to GVPi version)
          PDF conversion (formatting is not great)

    ## Sample Call
         http://localhost:9100/v1/Documents/Downloads/EPUB/IJP.077.0217A/
         http://localhost:9100/v1/Documents/Downloads/PDF/IJP.077.0217A/
         http://localhost:9100/v1/Documents/Downloads/PDFORIG/IJP.077.0217A/
    
    ## Notes
    
    ## Potential Errors
       USER NEEDS TO BE AUTHENTICATED to request a download.  Otherwise, returns error.
    """

    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    if not session_info.authenticated:
        response.status_code = HTTP_400_BAD_REQUEST 
        status_message = "Must be logged in and authorized to download a document."
        ocd.record_session_endpoint(api_endpoint_id=endpoint,
                                    session_info=session_info, 
                                    params=request.url._url,
                                    item_of_interest=f"{documentID}", 
                                    return_status_code = response.status_code,
                                    status_message=status_message
                                    )
        raise HTTPException(
            status_code=response.status_code,
            detail=status_message
        )    

    if retFormat.upper() == "EPUB":
        file_format = 'EPUB'
        media_type='application/epub+zip'
        endpoint = opasCentralDBLib.API_DOCUMENTS_EPUB
    elif retFormat.upper() == "PDF":
        file_format = 'PDF'
        media_type='application/pdf'
        endpoint = opasCentralDBLib.API_DOCUMENTS_PDF
    elif retFormat.upper() == "PDFORIG":  # not yet implemented.
        file_format = 'PDFORIG'
        media_type='application/pdf'
        endpoint = opasCentralDBLib.API_DOCUMENTS_PDFORIG
    else:
        file_format = 'HTML'
        media_type='application/xhtml+xml'
        endpoint = opasCentralDBLib.API_DOCUMENTS_HTML

    filename = opasAPISupportLib.prep_document_download(documentID, ret_format=file_format, authenticated=session_info.authenticated, base_filename="opasDoc")    
    if filename == None:
        response.status_code = HTTP_400_BAD_REQUEST 
        status_message = "Error: no filename specified"
        logger.error(status_message)
        ocd.record_session_endpoint(api_endpoint_id=endpoint,
                                    session_info=session_info, 
                                    params=request.url._url,
                                    item_of_interest=f"{documentID}", 
                                    return_status_code = response.status_code,
                                    status_message=status_message
                                    )
        raise HTTPException(status_code=response.status_code,
                            detail=status_message)
    else:
        #with open(filename, mode='rb') as file: # b is important -> binary
            #file_content = file.read()    
        #response = Response(file_content, media_type='application/epub+zip')
        try:
            response.status_code = HTTP_200_OK
            ret_val = FileResponse(path=filename,
                                   status_code=response.status_code,
                                   filename=os.path.split(filename)[1], 
                                   media_type=media_type)
            
        except Exception as e:
            response.status_code = HTTP_400_BAD_REQUEST 
            status_message = f" The requested document {filename} could not be returned {e}"
            raise HTTPException(status_code=response.status_code,
                                detail=status_message)

        else:
            status_message = "Success"
            logger.info(status_message)
            ocd.record_session_endpoint(api_endpoint_id=endpoint,
                                        session_info=session_info, 
                                        params=request.url._url,
                                        item_of_interest=f"{documentID}", 
                                        return_status_code = response.status_code,
                                        status_message=status_message
                                        )
    
    return ret_val

if __name__ == "__main__":
    print(f"Server Running ({localsecrets.BASEURL}:{localsecrets.API_PORT_MAIN})")
    uvicorn.run(app, host="development.org", port=localsecrets.API_PORT_MAIN, debug=True)
        # uvicorn.run(app, host=localsecrets.BASEURL, port=9100, debug=True)
    print ("Now we're exiting...")