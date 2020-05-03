#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Main entry module for PEP version of OPAS API

This API server is based on the existing PEP-Web API 1.0.  The data returned 
may have additional fields but should be otherwise compatible with PEP API clients
such as PEP-Easy.

It's an initial version of the Opas Solr Server (API); it's not yet "generic", it's
schema and functionality dependent on PEP's needs (who is funding development).  But
it would be a start, that could be genericized for a general purpose OPAS.

To Install (at least in windows)
  rem python 3.7 required
  python -m venv .\venv
  .\venv\Scripts\activate.bat
  pip install --trusted-host pypi.python.org -r /app/requirements.txt
  rem if it complains pip is not up to date
  python -m pip install --upgrade pip

Run with:
    uvicorn server:app --reload

    or for debug:

    uvicorn main:app --debug --log-level=debug

(Debug set up in this file as well: app = FastAPI(debug=True))

Endpoint and model documentation automatically available when server is running at:

  http://subdomain.domain:port/docs
  (components above as needed)
  
  e.g.,
  http://api.development.org/docs
  http://localhost:8000/docs
  etc.

(base URL + "/docs")


"""
#----------------------------------------------------------------------------------------------
# Coding Standards
#----------------------------------------------------------------------------------------------
#Original code came from camelCase, my previously main code standard.  However, to make
#it at least a bit more acceptible to modern Pythonistas, I've converted variables and
#functions to snake_case.  There is still a mix, which does serve a purpose of separating
#names by use.

#Naming standards: 
  #- converted variables (still may be some camelCase) in snake_case
  #- class names in camelCase per python standards
  #- model attributes - camelCase
  #- database fields/attributes - snake_case
  #- solr attributes - snake_case
  #- api path parameters - camelCase
  #- api query parameters - lowercase
#----------------------------------------------------------------------------------------------
#Revisions (early history not recorded...and will roll off some history as needed)
#2019.0617.1 - First version with 6 endpoints, 5 set up for Pydantic and one not yet
                #converted - nrs
#2019.0617.4 - Changed functions under decorators to snake case since the auto doc uses those 
              #as sentences!

#2019.0816.1 - Figured out that I need to return the same model in case of error. 
              #Responseinfo has errors which is a struct with error messages.
              #Setting resp.status_code returns the error code.

              #EXAMPLE in get_the_author_index_entries_for_matching_author_names
                      #Returns the error correctly when Solr is not running.
                      #USE THAT AS A TEMPLATE.

              ##TODO: This now needs to be done to each end point.

#2019.0904.1 - Started conversion to snake_case...

#2019.1019.1 - This and the other modules have now been (mostly) converted from camelCase to snake_case
              #for the sake of other Python programmers using the source.  This does lead
              #to some consistency issues, because you do end up with a mix of camelCase given
              #the API and some libraries using it.  I'm not a big fan of snake_case but
              #trying to do it in the most consistent way possible :)

#2019-11-30 - Updated FastAPI/Starlette/Pydantic.  Removed EmailStr import which was just there to prevent warnings on older versions.
           #- Added additional fields, some admin only, to get_server_status (now shows versions)
           
#2019-11-28 - Added SSH support to allow communicating with AWS mySQL offsite.

#2019.1202.1 - Fixed password encoding for create user. Parameterized some settings.
              #Tuned mostcited to retrieve fewer records which is what was making it slow.
              #Continued working on term search fixes...not done! #TODO

#2019.1202.2 - Fixed text_server_ver return
#2019.1203.1 - authentication parameter default (None) error slipped in!  But important, it blocked abstracts showing.
#2019.1204.1 - modified cors origin list to try *. instead of just . origins [didn't work]
#2019.1204.3 - modified cors to use regex opion. Define regex in localsecrets CORS_REGEX
#2019.1205.1 - Added opasQueryHelper with QueryTextToSolr to parse form text query fields and translate to Solr syntax
#2019.1207.1 - Search analysis reenabled and being tested...may be problems from pepeasy
#2019.1213.1 - Added S3 access via s3fs library - working well for images.  Downloads still needs work because
              #while it downloads, it doesn't trigger browser to download to user's choice of locations.
#2019.1214.1 - Added experimental "prefix switches" to opasQueryHelper to allow proximity selection via "p>" (or now just "p "
              #at the beginning of string.
#2019.1220.1 - pepwebdocs Schema added nested documents, supporting schema changes.
#2019.1221.1 - pepwebdocs Schema optimization pass 2.  Needs a pass 3!
#2019.1222.1 - Added v2 endpoints:
                 #termcount endpoint
                 #advancedsearch
                 #search (replaced v1 search with more minimal one matching pepEasy requirements)
                 #update v2 search as a more general (and yet more optimized search)
#2019.1227.1 - Image config S3 work for the production system.
#2019.1229.1 - Tested and corrected termcounts endpoint.
              #Updated status to give more server info for the admin.
#2019.1231.1 - Fixed journal logo case of logo suffix to Logo to match files in xslt file.  Also, there was a .logo where sent back to the client which is wrong.
            #- added db url for admins in status
            #- fixes to query analysis and terms
            #- fixes to solrXMLPEPWebLoad programs to allow tunneling for remote SQL server (or Bitnami SQL install)
#2020.0103.1 - fixed session_id cookie for non-logged in users
            #- Added experimental body parameter to allow field level specification of query.  Not sure
              #that will work out because the url parameter search is needed to communicate the last query to doc retrieval with
              #hits marked (the server repeats the search)
#2020.0107.1 - Reorganized the schema and models for clarity. Still thinking about renaming all the art_ prefixed schema elements to doc_.
              #Fixed interaction with PEP-Easy by properly filling out the accesslimited model attributes
              #Added p_ to all parent_tag names because the marking engine was picking up those names from the query
                 #and marking them when found in text.  So for example Doc is not a good name anymore.  Prefixed all
                 #with p_ and that shouldn't match anywhere
              #Although the original goal was to implement the v1 API, that tied my hands and made the code less
                 #manageable in the long run.  So I decided to remmove any V1 API feature (endpoint or parameter) that wasn't used by PEPEasy,
                 #I have kept some unused endpoints though because I think they have vakue in v2.
              #To make it clear to the vendors bidding on the Client project what the "best/future" API is, I created
                 #a v2 for every v1 endpoint, and other than leaving v1 endpoints in a v1 category, all the other endpoint
                 #groups now refer to v2.
              #Added preliminary functions to allow friendly names for parent tags.  The API converts them to the p_ equivalent
                 #and converts the p_ equiv. back to friendly names for query analysis display.  This also allows
                 #multiple names to be substituted for a friendly name.  For example:
                 #doc is now translated to a group of three tags (the doc is everything but the references.
                 #Here's the current list:
                     #"doc" : "(p_body OR p_summaries OR p_appxs)",
                     #"headings": "(p_heading)",
                     #"quotes": "(p_quote)",
                     #"dreams": "(p_dream)",
                     #"poems": "(p_poem)",
                     #"notes": "(p_note)",
                     #"dialogs": "(p_dialog)",
                     #"panels": "(p_panel)",
                     #"captions": "(p_captions)",
                     #"biblios": "(p_bib)",
                     #"appendixes": "(p_appxs)",
                     #"summaries": "(p_summaries)",
                 #It's not certain yet, whether we can keep this feature.
#2020.0108.1 - Fixed accesslimited return values, and optimized columns in search_text
              #by adding a param for requesting full-text or abstracts.  When abstracts
              #aren't needed, neither is full-text.  Saves a lot of time when returning 25
              #or more search results!
              
              #TODO: What to do about the new multiple "routes" and complex query generation for marking hits in a document?
                    #Option 1: Allow those routes in the Doc routine so it's just up to the client to send whatever
                              #back.  That's essentially what's currently done via the Search URL param.  The client
                              #has the record of what was sent.
                              
#2020.0111.1 Endpoint parameter documentation changed to 'constant' names from opasConfig
#2020.0112.1 Added Glossary search convenience function
            #Finished endpoint constant names
            #Changed query parameters journal to sourcecode for v2 endpoints
            #Added sourcetype to endpoints.  An easier way to specify all books, videos, or journals.  Was already in database.
            
#2020.0113.1 Changed timestamp to file_last_modified in get_what's new so it's not just when the file is uploaded, but rather when it's edited (processed)
               #updated endpoint documentation

            #Added code to search_text so (abstract_xml, summaries_xml, and text_xml) are only returned when abstract_requested is set, and only text_xml from
               #that set is returned when just full_text_requested is set in the call to search_text.
            #Added parameters to most downloaded to meet PEP-Web like functionality for filtering.  Note that you can't do most downloaded with Solr data, only
            #  with the mySQL recording of downloads.
            
#2020.0114.1 Fixed problem with Documents/Documents on a secondary request, added check there with embargo and authentication info.

#2020.0215.1 Partial fix for nested pb in files, like Bion, W. R. (1962).  Those were showing complete data when an excerpt (it has no abstract) was being generated.
             # solved by an excerpting XSLT file which gets rid of the <p>'s and all other tags other than the pb, then translates to html.
             # But this translation needs a lot more work due to lack of formatting (and perhaps more.)
             #TODO MORE
#2020.0222.1 Fix for PDF downloads, document declaration was causing errors and .
             # utf char conversions which caused errors.
             # also added running head and copyright notice.
             # Still needs css formatting applied and banner if
             # we want it (path issue right now)
             
#2020.0311.1 Setup html conversion to substutute current server domain + api call
             # for image src.  Changed xslt file as well.
             
#Alpha       Released as Alpha3

#2020.0313   Updated schemaMap.py to include p_bib for biblios
#2020.0314   Removed journal paran min length of 2, since sometimes it's empty!
#2020.0318   Add new endpoints which may be temporary convenience functions because
#            we will be moving authentication and authorization to another separate
#            API server (e.g., PaDS).  But these will allow me to more easily manage 
#            subscriptions in the meanwhile.
#            Added:
#                /v2/Admin/ChangeUserPassword/
#                /v2/Admin/SubscribeUser/
#            Tested database with RDS/MySQL and it's working as configured.

#2020.0325   Removed deprecated response_model_skip_defaults and replaced with 
#            response_model_exclude_unset per FastAPI change to be consistent with
#            pydantic
#

#2020.0330   Updates to endpoint documentation headers for live documentation
#            /v2/Database/TermCounts

#2020.0401  In opasAPISupportLib.py lib: 
#              Set it so user-agent is optional in session settings, in case client doesn't supply 
#              it (as PaDS didn't)

#2020.0408  Changes to fix bug and complete implementation (it wasn't fully implemented).
#           Added endpoint for openAPI (will add key next)
#           All tests pass (though need more tests!)

#2020.0417  Added API_KEY code, only applied to documentation functions now, and mainly as an
#           example, since docs is not marked as protected right now.

#           BasicLogin is now working.  Extracted common setup after login code
#           to login_setup_user_session, so next it can be moved to other login endpoints.

#2020.0418  More fixes to parse_search_query_parameters() regarding sort
#           and a solr query param which was offset=0 rather than start=offset
#           in database_get_whats_new()

#2020.0419  Fixed endpoint function names to match endpoints (easier to find when programming) 
#           Added endpoint summary to replace what the descriptive function names were doing
#           A few bug fixes.
#           Added facet return in responseInfo if facefields specified in endpoint params 
#             or SolrQuery input.

#2020.0423 Changed excerpting in SolrXMLPEPWebLoad to remove words in the trailing sentence 
#          of the excerpt to the preceding punctuation mark. Excluding ", which does mean 
#          sometimes there's an unclosed quote at the end of a sentence ending in .", but
#          the alternative was worse, since it left fragments where the quote wasn't at the
#          end of the sentence.
#          The limits which determine excerpt size can be configured in OpasConfig.
#             MIN_EXCERPT_CHARS = 480
#             MAX_EXCERPT_CHARS = 2000
#             MAX_EXCERPT_PARAS = 10
#          Min means it will even go past a pb if there are less chars than 480.
#
#2020.0430 Added a sort clause to the database query behind the metadata/volume return so
           # the data comes back better organized.
           # Fixed it so metadata/sourcetype/sourcecode gets everything if you use * for each
#2020.0502 Added endpoint WordWheel and supporting function in opasAPISupportLib to collect
           # a termlist from specified field.  Uses solr.SearchHandler(solr_docs, "/terms")
#2020.0503 Found error when issuing meta call for sources when pepcode was missing for a book
           # in the api_productbase table.  Fixed it (and missing data for IPL) and created a test
           # test_8b2_meta_all_sources to check all the source codes.
           # Also: documentID wasn't being filled in due to error in the dict lookup.  Fixed.
#----------------------------------------------------------------------------------------------

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2020, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2020.0503.1.Alpha3.3.1"
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
import wget
import shlex

# import json
from urllib import parse
# from http import cookies

# from enum import Enum
import uvicorn
from fastapi import FastAPI, Query, Path, Cookie, Header, Security, Depends, HTTPException, File, Form, UploadFile
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, RedirectResponse, FileResponse
from starlette.middleware.cors import CORSMiddleware
#from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_200_OK, \
                             HTTP_400_BAD_REQUEST, \
                             HTTP_401_UNAUTHORIZED, \
                             HTTP_403_FORBIDDEN, \
                             HTTP_404_NOT_FOUND, \
                             HTTP_500_INTERNAL_SERVER_ERROR, \
                             HTTP_503_SERVICE_UNAVAILABLE

import requests
from requests.auth import HTTPBasicAuth
import aiofiles
# from typing import List

TIME_FORMAT_STR = '%Y-%m-%dT%H:%M:%SZ'

# to protect documentation, use: app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app = FastAPI()

# from pydantic import BaseModel
# from pydantic.types import EmailStr
from pydantic import ValidationError
import solrpy as solr
# import json
import libs.opasConfig as opasConfig
from opasConfig import OPASSESSIONID, OPASACCESSTOKEN, OPASEXPIRES
import logging
logger = logging.getLogger(__name__)

# from config.localsecrets import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
import jwt
# import localsecrets as localsecrets
import localsecrets
import libs.opasAPISupportLib as opasAPISupportLib
# import libs.opasBasicLoginLib as opasBasicLoginLib
#from libs.opasBasicLoginLib import get_current_user

from errorMessages import *
import models
# import modelsOpasCentralPydantic
import opasCentralDBLib
import opasFileSupport
import opasQueryHelper

# from sourceInfoDB import SourceInfoDB

# Check text server version
# doesn't work for some reason.  Works for localhost, but not cross-domain.
# on the bitnami server, I get unauthorized (401).  I get an error on the
# codesypher server.
text_server_ver = None
text_server_url = localsecrets.SOLRURL
PARAMS = {'wt':'json'}
url = f"{localsecrets.SOLRURL}admin/info/system"
if localsecrets.SOLRUSER is not None:
    # need username and password
    r = requests.get(url = url, params = PARAMS, auth=HTTPBasicAuth(localsecrets.SOLRUSER, localsecrets.SOLRPW))
else:
    r = requests.get(url = url, params = PARAMS)
    
if r.status_code == 200:
    ver_json = r.json()
    try:
        text_server_ver = ver_json["lucene"]["lucene-spec-version"]
    except KeyError:
        text_server_ver = ver_json["lucene"]["solr-spec-version"]

CURRENT_DEVELOPMENT_STATUS = "Developing"

app = FastAPI(
    debug=True,
    title="Open Publications Archive (OPAS) API for PEP-Web",
        description = "Open Publications Archive Software API for PEP-Web by Psychoanalytic Electronic Publishing (PEP)",
        version = f"{__version__}",
        static_directory=r"./docs",
        swagger_static={
            "favicon": "pepfavicon"
            },
)

#app.add_middleware(SessionMiddleware,
                    #secret_key = secrets.token_urlsafe(16),
                    #session_cookie = secrets.token_urlsafe(16)
    #)

origins = [
    "http://*.development.org",
    "http://*.development.org:9999",
    "http://*.pep-web.rocks",
    "http://*.pep-web.info",
    "http://*.localhost",
    "http://localhost"
]

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=localsecrets.CORS_REGEX, 
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

opas_fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET)

logger.info('Started at %s', datetime.today().strftime('%Y-%m-%d %H:%M:%S"'))

#class DateTimeEncoder(json.JSONEncoder):
    #def default(self, o):
        #if isinstance(o, datetime):
            #return o.isoformat()

        #return json.JSONEncoder.default(self, o)

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

#-----------------------------------------------------------------------------
# API Documentation section
#-------------------------
#An option that lets you check header and return company from database
#see https://github.com/tiangolo/fastapi/issues/142
#X_API_KEY = APIKeyHeader(name='X-API-Key')
#class APIUser(BaseModel):  # snake_case names to match DB
    #id: int = None
    #key: str = ""
    #companies: list = []
    #sites: list = []

#def check_authentication_header(x_api_key: str = Depends(X_API_KEY)):
    #""" takes the X-API-Key header and converts it into the matching user object from the database """

    ## this is where the SQL query for converting the API key into a user_id will go
    #api_user = sql_query(x_api_key)
    #if api_user:
        ## if passes validation check, return user data for API Key
        #return api_user
    ## else raise 401
    #raise HTTPException(
        #status_code=status.HTTP_401_UNAUTHORIZED,
        #detail="Invalid API Key",
    #)

#-----------------------------------------------------------------------------
api_key_query = APIKeyQuery(name=localsecrets.API_KEY_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=localsecrets.API_KEY_NAME, auto_error=False)
api_key_cookie = APIKeyCookie(name=localsecrets.API_KEY_NAME, auto_error=False)


async def get_api_key(api_key_query: str = Security(api_key_query),
                      api_key_header: str = Security(api_key_header),
                      api_key_cookie: str = Security(api_key_cookie),
                      ):
    
    if api_key_query == localsecrets.API_KEY:
        return api_key_query
    elif api_key_header == localsecrets.API_KEY:
        return api_key_header
    elif api_key_cookie == localsecrets.API_KEY:
        return api_key_cookie
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )

@app.get("/v2/Api/OpenapiSpec", tags=["API documentation"], summary=opasConfig.ENDPOINT_SUMMARY_OPEN_API)
async def api_openapi_spec(api_key: APIKey = Depends(get_api_key)):
    """
    This returns openapi documentation in json that can be loaded to Swagger
    
    Requires API key.
    
    """
    #Also a good demo of the simplicity to add APIKey to any endpoint. The APIKey
    #can be added to the header (see postman example), in the interactive documentation
    #it's just a matter of pressing the lock icon and filling out the form.  It can also
    #be supplied as a query parameter in the endpoint call.
    
    response = JSONResponse(get_openapi(title="FastAPI", version=1, routes=app.routes))
    return response


@app.get("/v2/Api/LiveDoc", tags=["API documentation"], summary=opasConfig.ENDPOINT_SUMMARY_DOCUMENTATION)
async def api_live_doc(api_key: APIKey = Depends(get_api_key)):
    """
    This returns an HTML page of interactive api documentation.
    
    Requires API key.

    """
    #It's really only useful if/when we turn off the free documentation
    #changing the app call to:

       #app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    response = get_swagger_ui_html(openapi_url="/v2/Api/OpenapiSpec", title="docs")
    
    #TODO: should we set this wherever the key is required?
    response.set_cookie(
        localsecrets.API_KEY_NAME,
        value=api_key,
        domain=localsecrets.COOKIE_DOMAIN,
        httponly=True,
        max_age=1800,
        expires=1800,
    )
    return response
#-----------------------------------------------------------------------------
@app.post("/v2/Admin/CreateUser/", response_model=models.User, response_model_exclude_unset=True, tags=["Admin"], summary=opasConfig.ENDPOINT_SUMMARY_CREATE_USER)
async def admin_create_user(response: Response, 
                            request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                            username: str = Form(..., description="Username"),
                            password: str = Form(..., description="Password"),
                            company: str = Form(default=None, description="Optional, company name"),
                            fullname: str = Form(default=None, description="Optional, full name"),
                            email: str = Form(default=None, description="The user's email address"),
                            tracking: bool = Form(default=1, description="Tracking information recorded for reports"),
                            cookies: bool = Form(default=1, description="User agrees to site cookies"),
                            reports: bool = Form(default=0, description="View Parent Reports"),
                            optin: bool = Form(default=1, description="User agrees to email communications"),
                            hide: bool = Form(default=1, description="User agrees to site cookies"),
                            ):
    """
    ## Function
       <b>Add a new user</b>
       
       Temporary admin for development

       This is only a stopgap for development
       All authentication processing is to be done in PaDS as planned
       (though it may be this stays conditionally for future iteration of local development TBD)
       

    ## Return Type
       models.UserInfo

    ## Status
       Status: In Development

    ## Sample Call
         /v2/Admin/CreateUser/

    ## Notes
         NA

    ## Potential Errors
       NA

    """
    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    # ensure user is admin
    if ocd.verify_admin(session_info):
        ret_val = ocd.create_user(session_info=session_info,
                                  username=username,
                                  password=password,
                                  full_name=fullname, 
                                  company=company,
                                  email=email,
                                  user_agrees_tracking=tracking,
                                  user_agrees_cookies=cookies,
                                  view_parent_user_reports=reports, 
                                  email_optin=optin,
                                  hide_activity=hide
                                  )
    else:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, 
            detail="Not authorized"
        )        
    return ret_val

##-----------------------------------------------------------------------------
#@app.post("/v2/Admin/SubmitFile/", response_model_exclude_unset=True, tags=["Admin"])
#async def submit_file(response: Response, 
                      #request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),
                      #submit_token: bytes= File(...), 
                      #xml_data: bytes = File(..., description="Article data (complete) or just metadata and abstract in xml"),
                      #pdf_data: bytes = File(..., description="Article data (complete) in original PDF file"),
                    #):
    #"""
    ### Function
       #<b>Submit a XML file and PDF for inclusion</b>
       
       #Requires an authenticated submit_token, and temporarily is only available to admins

    ### Return Type
       #models.FileItem

    ### Status
       #Status: In Development

    ### Sample Call
         #/v2/Admin/SubmitFile/

    ### Notes
         #NA

    ### Potential Errors
       #NA

    #"""
    #ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    ## ensure user is admin
    #if ocd.verify_admin(session_info):
        #ret_val = opasAPISupportLib.submit_file(submit_token,
                                                #xml_data,
                                                #pdf_data
        #)
    #else:
        #raise HTTPException(
            #status_code=HTTP_401_UNAUTHORIZED, 
            #detail="Not authorized"
        #)        
    #return ret_val

#-----------------------------------------------------------------------------
@app.post("/v2/Admin/ChangeUserPassword/", response_model=models.User, response_model_exclude_unset=True, tags=["Admin"], summary=opasConfig.ENDPOINT_SUMMARY_CHANGE_PASSWORD)
async def admin_change_user_password(response: Response, 
                                     request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                                     username: str = Form(..., description="Username"),
                                     oldpassword: str = Form(..., description="Previous Password"),
                                     newpassword: str = Form(..., description="New Password"),
                                     ):
    """
    ## Function
       <b>Change a user's Password</b>
       
       Temporary admin for development

       This is only a stopgap for development
       All authentication processing is to be done in PaDS as planned
       (though it may be this stays conditionally for future iteration of local development TBD)
       
    ## Return Type
       models.UserInfo

    ## Status
       Status: Development Only Function

    ## Sample Call
         /v2/Admin/ChangeUserPassword/

    ## Notes

    ## Potential Errors
       NA

    """
    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    # ensure user is admin
    if ocd.verify_admin(session_info):
        ret_val = ocd.admin_change_user_password(session_info=session_info,
                                                 username=username,
                                                 old_password=oldpassword,
                                                 new_password=newpassword,
                                  )
    else:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, 
            detail="Not authorized"
        )        
    return ret_val
#-----------------------------------------------------------------------------
@app.post("/v2/Admin/SubscribeUser/", response_model=models.User, response_model_exclude_unset=True, tags=["Admin"], summary=opasConfig.ENDPOINT_SUMMARY_SUBSCRIBE_USER)
async def admin_subscribe_user(response: Response, 
                               request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                               username: str = Form(..., description="Username"),
                               startdate: str = Form(..., description="Subscription Starts"),
                               enddate: str = Form(..., description="Subscription ends"),
                               productcode: str = Form(..., description="Product code, e.g., PEPArchive, IJPOpen, ..."),
                               productparentcode: str = Form(..., description="Product parent code, e.g., PEPArchive, IJPOpen, ..."),
                               ):
    """
    ## Function
       <b>Add a subscription to one or more products for a user</b>
       
       Admin user endpoint only
       
       Temporary admin for development

       This is only a stop gap for development
       All authentication processing is to be done in PaDS as planned
       (though it may be this stays conditionally for future iteration of local development TBD)

    ## Return Type
       models.UserInfo

    ## Status
       Status: Development Only Function

    ## Sample Call
         /v2/Admin/SubscribeUser/

    ## Notes
       This is only a temp feature to help with testing.
       All subscriptions and authorization processing will be done in PaDS as planned

    ## Potential Errors
       NA

    """
    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    # ensure user is admin
    if ocd.verify_admin(session_info):
        ret_val = ocd.admin_subscribe_user(session_info=session_info,
                                           username=username,
                                           start_date=startdate,
                                           end_date=enddate,
                                           product_code=productcode, 
                                           product_parent_code=productparentcode
                                          )
    else:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, 
            detail="Not authorized"
        )        
    return ret_val

#-----------------------------------------------------------------------------
@app.get("/v2/Session/WhoAmI/", response_model=models.SessionInfo, response_model_exclude_unset=True, tags=["Session"], summary=opasConfig.ENDPOINT_SUMMARY_WHO_AM_I)
async def session_whoami(response: Response,
                         request: Request):
    """
    ## Function
       <b>Temporary endpoint for debugging purposes</b>

       This is only a stopgap for development
       All authentication processing is to be done in PaDS as planned
       (though it may be this stays conditionally for future iteration of local development TBD)
       

    ## Return Type
       models.SessionInfo

    ## Status
       This endpoint is working.

    ## Sample Call
         /v2/Session/WhoAmI/

    ## Notes
       NA

    ## Potential Errors
       NA

    """

    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    return(session_info)


#-----------------------------------------------------------------------------
@app.get("/v2/Session/Status/", response_model=models.ServerStatusItem, response_model_exclude_unset=True, tags=["Session"], summary=opasConfig.ENDPOINT_SUMMARY_SERVER_STATUS)
async def session_status(response: Response, 
                         request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST)
                        ):
    """
    ## Function
       <b>Return the status of the database and text server.  Some field returns depend on the user's security level.</b>

    ## Return Type
       models.ServerStatusItem

    ## Status
       Status: Working

    ## Sample Call
         /v2/Session/Status/

    ## Notes
       NA

    ## Potential Errors
       NA

    """
    global text_server_ver
    
    ocd, session_info = opasAPISupportLib.get_session_info(request, response)   

    db_ok = ocd.open_connection()
    solr_ok = opasAPISupportLib.check_solr_docs_connection()
    config_name = None
    mysql_ver = None
    config_name = None
    mysql_ver = ocd.get_mysql_version()
    if ocd.verify_admin(session_info):
        # Check text server version
        #PARAMS = {'wt':'json'}
        #url = f"{localsecrets.SOLRURL}/admin/info/system"
        #r = requests.get(url = "http://localhost:8983/solr/admin/info/system", params = PARAMS)
        #if r.status_code == 200:
            #ver_json = r.json()
            #text_server_ver = ver_json["lucene"]["lucene-spec-version"]

        config_name = localsecrets.CONFIG
        try:
            server_status_item = models.ServerStatusItem(text_server_ok = solr_ok,
                                                         db_server_ok = db_ok,
                                                         api_server_version = __version__, 
                                                         user_ip = request.client.host,
                                                         timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ'), 
                                                         # admin only fields
                                                         text_server_url = localsecrets.SOLRURL,
                                                         text_server_version = text_server_ver, 
                                                         db_server_url = localsecrets.DBHOST,
                                                         db_server_version = mysql_ver,
                                                         config_name = config_name,
                                                         user_count = 0
                                                         )
        except ValidationError as e:
            logger.warning("ValidationError", e.json())
    else:
        try:
            server_status_item = models.ServerStatusItem(text_server_ok = solr_ok,
                                                         db_server_ok = db_ok,
                                                         api_server_version = __version__, 
                                                         user_ip = request.client.host,
                                                         timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ'), 
                                                         )
        except ValidationError as e:
            logger.warning("ValidationError", e.json())


    ocd.close_connection()
    return server_status_item

##-----------------------------------------------------------------------------
#@app.get("/v2/Database/Alerts/", response_model=models.AlertList, response_model_exclude_unset=True, tags=["Database", "Planned"])
#def get_database_alerts(response: Response,
                        #request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                        #):
    #"""
    ### Function
       #<b>Get database alert settings</b>

    ### Return Type
       #models.AlertList

    ### Status
        #Currently just a stub.

    ### Sample Call
         #/v2/Admin/Alerts/

    ### Notes
       #NA

    ### Potential Errors
       #NA

    #"""

    #ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    #ret_val = None
    #try:
        #response_info = models.ResponseInfoLoginStatus(username = session_info.username,
                                                       #request = request.url._url,
                                                       #timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')
                                                       #)

        #alert_struct = models.AlertListStruct(responseInfo = response_info, 
                                              #responseSet = [] #TODO: add info
                                              #)

        #ret_val = models.AlertList(alertList = alert_struct)

    #except ValidationError as e:
        #logger.error(e.json())             

    #return(ret_val )

##-----------------------------------------------------------------------------
#@app.post("/v2/Database/Alerts/", response_model=models.AlertList, response_model_exclude_unset=True, tags=["Database", "Planned"])
#def subscribe_to_database_alerts(*,
                                 #response: Response,
                                 #request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                                 #email: str = Form(default=None, description="The email address where to send alerts"),
                                 #product: str = Form(default=None, description="Alert on a specific product"),
                                 #journals: bool = Form(default=None, description="Alerts on all Journal updates"),
                                 #books: bool = Form(default=None, description="Alerts on all Book updates"),
                                 #videos: bool = Form(default=None, description="Alerts on all Video updates")
                                 #):
    #"""
    ### Function
       #<b>Subscribe to database alerts/b>

    ### Return Type
       #models.AlertList

    ### Status
       #in development planning - currently unimplemented

    ### Sample Call
         #/v2/Database/Alerts/

    ### Notes
       #NA

    ### Potential Errors
       #NA

    #"""

    #ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    #ret_val = None
    #try:
        #response_info = models.ResponseInfoLoginStatus(username = session_info.username,
                                                       #request = request.url._url,
                                                       #timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')
                                                       #)

        #alert_struct = models.AlertListStruct(responseInfo = response_info, 
                                              #responseSet = [] #TODO: add info
                                              #)

        #ret_val = models.AlertList(alertList = alert_struct)

    #except ValidationError as e:
        #logger.error(e.json())             

    #return(ret_val )

##-----------------------------------------------------------------------------
#@app.get("/v2/Database/Reports/", response_model=models.Report, response_model_exclude_unset=True, tags=["Database", "Planned"])
#def get_reports(response: Response,
                #request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                ##report: models.ReportTypeEnum=Query(default="None", title="Report Type", description="Report Type"),
                #journal: str=Query(None, title="Filter by Journal or Source Code", description="PEP Journal Code (e.g., APA, CPS, IJP, PAQ),", min_length=2), 
                ##author: str=Query(None, title="Filter by Author name", description="Author name, use wildcard * for partial entries (e.g., Johan*)"), 
                ##title: str=Query(None, title="Filter by Document Title", description="The title of the document (article, book, video)"),
                #period: models.TimePeriod=Query(None, title="Time period (range)", description="Range of data to return"), 
                ##endyear: str=Query(None, title="Last year to match", description="Last year of documents to match (e.g, 2001)"), 
                #limit: int=Query(5, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                #offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
                #):
    #"""
    ### Function
       #<b>Return the specified report</b>

    ### Return Type
       #models.Report

    ### Status
       #in development planning - currently unimplemented, just a stub

    ### Sample Call
         #/v2/Database/Reports/

    ### Notes
       #NA

    ### Potential Errors
       #NA

    #"""
    #ret_val = None

    #ocd, session_info = opasAPISupportLib.get_session_info(request, response)

    #try:
        #ret_val = models.Report(report=[4, 5, [1, 2, 3]])

    #except ValidationError as e:
        #logger.error(e.json())             

    #return(ret_val )


#-----------------------------------------------------------------------------
@app.get("/v2/Documents/Submission/", response_model_exclude_unset=True, tags=["Planned"], summary=opasConfig.ENDPOINT_SUMMARY_DOCUMENT_SUBMIT)   
async def documents_submission(*,
                               journalcode: str = Form(default=None, description="The 3-8 digit PEP Code for this journal"),
                               title: str = Form(..., description="The title of the article"),
                               keywords: str = Form(default=None, description="A comma separated list of keywords"),
                               region: str = Form(default=None, description="The region it's from"),
                               editor: str = Form(default=None, description="The editor assigned to this article"),
                               country: str = Form(default=None, description="The country of origin"),
                               language: str = Form(default="English", description="The language in which the article is written"),
                               anonymous: bool = Form(default=None, description="If the author is to be anonymous"),
                               authorlist: models.authorList = Form(default=None, description="This must be a structure of the form shown."),
                               abstract: str = Form(...),
                               reviewernotes: str = Form(default=None, description="Notes for the revieweer"),
                               file: UploadFile = File(..., description="PDF or EPUB version of article"),
                               token: str = Form(..., description="Authorization code")                             
                               ):
    """
    ## Function
       <b>An <i>authorized user</i> can submit an article in PDF</b>

       This is currently only aimed at IJPOpen which is nnot supported in OPAS, and may be made into a separate
       system.
       
    ## Return Type
       models.XXX

    ## Status
       In Development

    ## Sample Call
         /v2/Documents/Submission/

    ## Notes

    ## Potential Errors

    """
    ocd, session_info = opasAPISupportLib.get_session_info(request, response)

    if ocd.verify_admin(session_info): #TODO Later add specific permissions
        sample = await file.read()
        
        async with aiofiles.open(fr"{UPLOAD_DIR}{file.filename}", "wb") as f:
            await f.write(sample)
    
        #with open(fr"z:\back\{fileb.filename}", "wb") as f:
            #f.write(sample)
    
        return {
            "file_size": len(file),
            "token": token,
            "fileb_content_type": fileb.content_type,
            "fileb_sample": len(sample)
        }
    else:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authorized to upload",
            headers={"WWW-Authenticate": "Basic"},
        )

#-----------------------------------------------------------------------------
@app.get("/v2/Session/BasicLogin/", response_model_exclude_unset=True, tags=["Session"], summary=opasConfig.ENDPOINT_SUMMARY_LOGIN_BASIC)
def session_login_basic(response: Response, 
                        request: Request,
                        user: str = Depends(get_current_username), 
                        ka=False):
    """
    ## Function
       <b>Basic login Authentication.  Calls up a simple dialog allowing secure login.</b>
       
       Also can get username and password from the header information which is
       secure in https.

    ## Return Type
       models.LoginReturnItem

    ## Status
       This endpoint is working.

    ## Sample Call
         /v2/Session/BasicLogin/

    ## Notes

    ## Potential Errors

    """
    logger.debug("V2 Basic Login Request: ")
    err_code = None
    
    session_id = request.cookies.get(OPASSESSIONID) #  opasAPISupportLib.get_session_id(request)
    access_token = request.cookies.get(OPASACCESSTOKEN)   #  opasAPISupportLib.get_access_token(request)
    expiration_time = datetime.utcfromtimestamp(time.time() + opasAPISupportLib.get_max_age(keep_active=ka))

    # ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    if session_id is not None and access_token is not None and access_token != "":
        logger.debug("...note, already logged in...")
        pass # we are already logged in
    else: # 
        if user:
            session_id, access_token = login_setup_user_session(response,
                                                                request,
                                                                user,
                                                                session_id,
                                                                access_token,
                                                                expiration_time,
                                                                ka)
        else:
            access_token = None # user rejected
            err_code = response.status_code = HTTP_401_UNAUTHORIZED
            err_return = models.ErrorReturn(error = ERR_CREDENTIALS,
                                            error_message = ERR_MSG_LOGIN_CREDENTIALS)


    # this simple return without responseInfo matches the GVPi server return.
    if err_code is not None:
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
@app.get("/v1/Token/", response_model_exclude_unset=True, tags=["PEPEasy1 (Deprecated)"], summary=opasConfig.ENDPOINT_SUMMARY_TOKEN, description="Used by PEP-Easy to login; will be need to be changed in V2 for oauth")  
@app.get("/v2/Token/", response_model_exclude_unset=True, tags=["Session"], summary=opasConfig.ENDPOINT_SUMMARY_TOKEN, description="Used by PEP-Easy to login; will be need to be changed in V2 for oauth")  
def get_token(response: Response, 
              request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
              username=None, 
              password=None, 
              grant_type=None, 
              ka=False):
    """
    ## Function
       <b>Actually, this is just like a login.  Used by PEP-Easy from v1</b>
       Will be deprecated eventually.

    ## Return Type
       models.LoginReturnItem

    ## Status
       This is currently used by PEPEasy (under checkLoginStatus)

       This endpoint is working.

    ## Sample Call
         /v1/Token/

    ## Notes

    ## Potential Errors

    """
    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    if grant_type=="password" and username is not None and password is not None:
        login_return_item = session_login_user(response, request, grant_type, username, password, ka)
        return login_return_item
    else:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, 
            detail=ERR_CREDENTIALS
        )
        #err_code = response.status_code = HTTP_400_BAD_REQUEST
        #err_return = models.ErrorReturn(error = ERR_CREDENTIALS, error_message = ERR_MSG_INSUFFICIENT_INFO)

#-----------------------------------------------------------------------------
@app.get("/v1/License/Status/Login/", response_model_exclude_unset=True, tags=["PEPEasy1 (Deprecated)"], summary=opasConfig.ENDPOINT_SUMMARY_LICENSE_STATUS)
def get_license_status(response: Response, 
                       request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST)):
    """
    ## Function
       <b>Return a LicenseStatusInfo object showing the user's license status info.</b>

    ## Return Type
       models.LoginStatus

    ## Status
       This is currently used by PEPEasy (under checkLoginStatus)
       For V1, and PEP-Easy.  Deprecated for the future.

    ## Sample Call
         /v1/License/Status/Login/

    ## Notes

    ## Potential Errors
    
    """
    # get session info database record if there is one
    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    # session_id = session_info.session_id
    # is the user authenticated? if so, loggedIn is true
    if session_info is not None:
        logged_in = session_info.authenticated
        user_id = session_info.user_id
        username = session_info.username
        #if user_id == 0:
            ##user = ocd.get_user(user_id=user_id)
            #username = "NotLoggedIn"
            #logged_in = False
        #elif user_id is not None:
            #username = session_info.username
    else:
        logged_in = False
        username = "NotLoggedIn"
    
    # hide the password hash
    response_info = models.ResponseInfoLoginStatus(loggedIn = logged_in,
                                                   username = username,
                                                   request = request.url._url,
                                                   #user=user,
                                                   timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')
                                                   )

    license_info_struct = models.LicenseInfoStruct(responseInfo = response_info, 
                                                   responseSet = None
                                                   )

    license_info = models.LicenseStatusInfo(licenseInfo = license_info_struct)
    return license_info
#-----------------------------------------------------------------------------
def login_setup_user_session(response: Response, 
                             request: Request,
                             user, 
                             session_id,
                             access_token,
                             expiration_time,
                             ka):
    # user must be already authenticated before calling here.
    # we need to close any open sessions.
    ocd = opasCentralDBLib.opasCentralDB()    
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
    # let people log in even without a current subscription (just can't access non-free data)
    # user.start_date = user.start_date.timestamp()  # we may just want to null these in the jwt
    # user.end_date = user.end_date.timestamp()
    # user.last_update = user.last_update.timestamp()
    access_token = jwt.encode({'exp': expiration_time.timestamp(),
                               'user': user.user_id, # .dict(),
                               'admin': user.admin,
                               'orig_session_id': session_id,
                               },
                              key=localsecrets.SECRET_KEY,
                              algorithm=localsecrets.ALGORITHM)

    # this seems like a good time to close any expired sessions, 
    # to free up resources in case this is a related user
    # added 2019-11-21
    count = ocd.close_expired_sessions()
    logging.info(f"Setting up new session. Closed {count} expired sessions")

    # start a new session, with this user (could even still be the old user)
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

    return session_id, access_token

#-----------------------------------------------------------------------------
#@app.get("/v1/Login/", response_model_exclude_unset=True, tags=["Deprecated"], summary=opasConfig.ENDPOINT_SUMMARY_LOGIN)
@app.get("/v2/Session/Login/", response_model_exclude_unset=True, tags=["Session"], summary=opasConfig.ENDPOINT_SUMMARY_LOGIN) # I like it under Users so I did them both.
def session_login_user(response: Response, 
                       request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
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
       #TODO: Need to figure out the right way to do timeouts for this "easy" login.

    ## Sample Call
       /v1/Login/             (Needed to support the original version of the PEP API.)
       /v2/Session/Login/    

    ## Notes

    ## Potential Errors

    """
    logger.debug("Login via: /v2/(Users)?/Login/ - %s", username)
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
                session_id, access_token = login_setup_user_session(response,
                                                                    request,
                                                                    user,
                                                                    session_id,
                                                                    access_token,
                                                                    expiration_time,
                                                                    ka)                
                ## user is authenticated
                ## we need to close any open sessions.
                #if session_id is not None and access_token is not None:
                    ## do a logout
                    #session_end_time = datetime.utcfromtimestamp(time.time())
                    #success = ocd.update_session(session_id=session_id, 
                                                 #session_end=session_end_time
                                                 #)    
                    ##opasAPISupportLib.deleteCookies(resp, session_id="", accessToken="")

                ## NOW lets give them a new session
                ## new session and then token
                #session_id = secrets.token_urlsafe(16)
                #max_age = opasAPISupportLib.get_max_age(ka)
                ## let people log in even without a current subscription (just can't access non-free data)
                ## user.start_date = user.start_date.timestamp()  # we may just want to null these in the jwt
                ## user.end_date = user.end_date.timestamp()
                ## user.last_update = user.last_update.timestamp()
                #access_token = jwt.encode({'exp': expiration_time.timestamp(),
                                           #'user': user.user_id, # .dict(),
                                           #'admin': user.admin,
                                           #'orig_session_id': session_id,
                                           #},
                                          #key=localsecrets.SECRET_KEY,
                                          #algorithm=localsecrets.ALGORITHM)

                ## this seems like a good time to close any expired sessions, 
                ## to free up resources in case this is a related user
                ## added 2019-11-21
                #count = ocd.close_expired_sessions()
                #logging.info(f"Setting up new session.  Closed {count} expired sessions")

                ## start a new session, with this user (could even still be the old user)
                #ocd, session_info = opasAPISupportLib.start_new_session(response,
                                                                        #request,
                                                                        #session_id=session_id,
                                                                        #access_token=access_token,
                                                                        #user=user)
                ## new code
                #response.set_cookie(key=OPASSESSIONID,
                                    #value=session_id,
                                    #max_age=max_age, expires=None, 
                                    #path="/",
                                    #secure=False, 
                                    #httponly=False)

                #response.set_cookie(key=OPASACCESSTOKEN,
                                    #value=access_token,
                                    #max_age=max_age, expires=None, 
                                    #path="/",
                                    #secure=False, 
                                    #httponly=False)

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
    if err_code is not None:
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
@app.get("/v1/Logout/", response_model_exclude_unset=True, tags=["PEPEasy1 (Deprecated)"], summary=opasConfig.ENDPOINT_SUMMARY_LOGOUT)  # The original GVPi URL
@app.get("/v2/Session/Logout/", response_model_exclude_unset=True, tags=["Session"], summary=opasConfig.ENDPOINT_SUMMARY_LOGOUT) # I like it under Users so I did them both.
def session_logout_user(response: Response, 
                request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST)):  
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
         /v2/Session/Logout/

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

    if err_code is not None:
        return err_return
    else:
        license_info_struct = models.LicenseInfoStruct( responseInfo = response_info, 
                                                        responseSet = []
                                                        )
        license_info = models.LicenseStatusInfo(licenseInfo = license_info_struct)
        return license_info

#-----------------------------------------------------------------------------
@app.get("/v2/Database/TermCounts/", response_model_exclude_unset=True, tags=["Database"], summary=opasConfig.ENDPOINT_SUMMARY_TERM_COUNTS)  #  removed for now: response_model=models.DocumentList, 
async def database_term_counts(response: Response, 
                               request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                               termlist: str=Query(None, title=opasConfig.TITLE_TERMLIST, description=opasConfig.DESCRIPTION_TERMLIST),
                               termfield: str=Query("text", title=opasConfig.TITLE_TERMFIELD, description=opasConfig.DESCRIPTION_TERMFIELD)
                               ):
    """
    ## Function
    <b>Get a list of term frequency counts (# of times term occurs across documents)</b>
    
    Can specify a field per the schema to limit it. e.g.,
    
       text - all text
       title - within titles
       author -
       author_bio_xml - in author bio
       art_kwds - in keyword lists
       art_lang - can look at frequency of en, fr, ... at article level
       lang - can look at frequency of en, fr, ... at paragraph level
       meta_xml - meta document data, including description of fixes, edits to documents
       
       Note: it appears the field must be listed as stored, not just indexed.
        
    ## Return Type
       models.TermIndex

    ## Status
       Status: Working as described above

    ## Sample Call

    ## Notes

    ## Potential Errors
    
    ### Doctests/Example Calls

      >>> get_term_counts(termlist="'author:tuckett, levinson, mosher', 'text:playfull, joy*'")
      
    """
    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    session_id = session_info.session_id
    term_index_items = []
    if termfield is None:
        termfield = "text"
    
    results = {}  # results = {field1:{term:value, term:value, term:value}, field2:{term:value, term:value, term:value}}
    terms = shlex.split(termlist)
    for n in terms:
        try:
            # If specified as field:term
            nfield, nterms = n.split(":")
            result = opasAPISupportLib.get_term_count_list(nterms, nfield)
        except:
            # just list of terms, use against termfield parameter
            nterms = n.strip("', ")
            try:
                result = opasAPISupportLib.get_term_count_list(nterms, term_field = termfield)
                for key, value in result.items():
                    try:
                        results[termfield][key] = value
                    except:
                        results[termfield] = {}
                        results[termfield][key] = value
            except Exception as e:
                # Solr Error
                raise HTTPException(
                    status_code=result.httpcode, 
                    detail=f"{result.error}. {result.error_description}"
                )
        else:
            try:
                a = results[nfield]
                # exists, if we get here, so add it to the existing dict
                for key, value in result.items():
                    results[nfield][key] = value
            except: #  new dict entry
                results[nfield] = result
    
    response_info = models.ResponseInfo( listType="termindex", # this is a mistake in the GVPi API, should be termIndex
                                         scopeQuery=[f"Terms: {termlist}"],
                                         timestamp=datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)
                                       )

    response_info.count = 0
    if results != {}:
        for field, termdict in results.items():
            for term, value in termdict.items():
                if value > 0:
                    item = models.TermIndexItem(field = field, 
                                                term = term, 
                                                termCount = value,
                                                ) 
                    term_index_items.append(item)
                    logger.debug("termIndexGetInfo: %s", item)
           
    response_info.count = len(term_index_items)

    response_info.fullCountComplete = True
    term_index_struct = models.TermIndexStruct( responseInfo = response_info, 
                                                responseSet = term_index_items
                                              )
    
    term_index = models.TermIndex(termIndex = term_index_struct)
    
    if response_info.count > 0:
        matches = response_info.count
        term_index.termIndex.responseInfo.request = request.url._url
    else:
        matches = 0

    statusMsg = f"{matches} hits"
    logger.debug(statusMsg)

    # client_host = request.client.host
    ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_DATABASE_TERMCOUNTS,
                                session_info=session_info, 
                                params=request.url._url,
                                status_message=statusMsg
                                )

    return term_index

#-----------------------------------------------------------------------------
@app.get("/v2/Database/AdvancedSearch/", response_model_exclude_unset=True, tags=["Database"], summary=opasConfig.ENDPOINT_SUMMARY_SEARCH_ADVANCED)  #  removed for now: response_model=models.DocumentList, 
async def database_advanced_search(response: Response, 
                                   request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                                   advanced_query: str=Query(None, title="Advanced Query (Solr Syntax)", description="Advanced Query in Solr syntax (see schema names)"),
                                   filter_query: str=Query(None, title="Advanced Query (Solr Syntax)", description="Advanced Query in Solr syntax (see schema names)"),
                                   highlight_fields: str=Query("text_xml", title="Fields to return for highlighted matches", description="Comma separated list of field names"),
                                   def_type: str=Query("lucene", title="edisMax, disMax, lucene (standard) or None (lucene)", description="Query analyzer"),
                                   facet_fields: str=Query(None, title=opasConfig.TITLE_FACETFIELDS, description=opasConfig.DESCRIPTION_FACETFIELDS), 
                                   sort: str=Query("score desc", title="Field names to sort by", description="Comma separated list of field names, optionally each with direction (desc or asc)"),
                                   limit: int=Query(15, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                                   offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
                                   ):
    """
    ## Function
    <b>Advanced search in Solr query syntax.</b>
    
    IMPORTANT NOTE: This endpoint is intended for client (user interface) developers to take advantage of the
    full Solr query functionality, while still returning the usual OPAS DocumentList return model, including conversion
    from XML to HTML.  If the developer wishes to specify the fields for return data, endpoint /v2/ExtendedSearch should be used.  
    
    This endpoint is not used, for example, in PEP-Easy because it isn't needed for basic query and retrieval operations which are built in
    to other endpoints.  PEP-Easy uses the v1 API exclusively (and not the Solr API or the v2 API).
    
    The documentation below on how to use the advanced query is intimately tied to the schemas (data structure based on the PEP DTDs).
    But it's not possible to provide query examples and sample data returns without tying them to a schema.  
    
    Currently, this endpoint only queries the Docs core (database), which is the main content database. Other cores include the Glossary core, the Authors core,
    and the References core.  Endpoint /v2/ExtendedSearch should be used to query other cores.
    
    ### Nested document search.

    Nested document search is used with the PEP Solr Schemas to search with paragraphs
    (or bibliographic entries--references) being the "atomic" unit of search (the record, in common database terms),
    while also using the context of the parent element and whole document metadata to filter.  So for example, you can find matches
    in paragraphs in "dreams", and the scope of the boolean logic of word searches must fall within
    a single paragraph (or reference).
    
    Per the Solr API, a nested document search must ensure that the matches for the different levels don't overlap or an error will occur.
    To prevent this, and to provide selectivity of the different child types, the art_level and parent_tag fields are included, which
    can be used to select the child (art_level:2), and the parent (art_level:1) and parent_tag (see below).
    
    For example, these PEP DTD elements (tags) are indexed as nested, art_level:2 documents in the pepwebdocs core
    with their parent tags as field <i>parent_tag</i>.
   
        * para in "doc" - this is mapped to the entire doc, minus the reference section (PEP Requirements).
          Advanced query must use "(p_body OR p_summaries OR p_appxs)"
            -- Note "doc" is a mapped (convenience) name for non-advanced query types and expanded to "(p_body OR p_summaries OR p_appxs)".  The entire document would be (p_body OR p_summaries OR "biblios" OR p_appxs)
        * para in "headings" - for advanced query use actual schema name "(p_heading)"
        * para in "quotes" - for advanced query use actual schema name "(p_quote)"
        * para in "dreams" - for advanced query use actual schema name "(p_dream)" 
        * para in "poems" - for advanced query use actual schema name "(p_poem)"
        * para in "notes" - for advanced query use actual schema name "(p_note)"
        * para in "dialogs" - for advanced query use actual schema name "(p_dialog)"
        * para in "panels" - for advanced query use actual schema name "(p_panel)"
        * para in "captions" - for advanced query use actual schema name "(p_caption)"
        * para in "biblios" - for advanced query use actual schema name "(p_biblio)"
            -- (each be/binc under PEP element bib, i.e., the references)
        * para in "appendixes" - for advanced query use actual schema name "(p_appendixes)"
        * para in "summaries" - for advanced query use actual schema name "(p_summaries)"
     
    Note that para is always the field name for convenience, but in some cases, it's logically something else, like a reference
    (which is comprised of an xml element be rather than xml element para), or even just cdata
    in the element
    
    Here's an example of a note "child" record:
    
        "id":"IJAPS.013.0191A.67",
        "parent_tag":"p_note",
        "para":"<p><i>Wikipedia</i>, Enlightenment, p. 1, emphasis added.</p>",
        "_version_":1655037031541112832,
        "art_level":2
        
    Solr keeps the relation to the parent for us, for which we use the special query syntax below.
    
    #### Sample nested queries

    <b>Find documents with paragraphs which contain "successful therapy" and "methods":</b>
        
    `{!parent which='art_level:1'} (art_level:2 AND parent_tag:(p_body OR p_summaries OR p_appxs) AND para:("successful therapy" AND methods))`
        
    <b>Find documents with paragraphs which contain Gabbard but NOT impact (the minus is shorthand for NOT):</b>
        
    `{!parent which='art_level:1'} (art_level:2 AND parent_tag:(p_body OR p_summaries OR p_appxs) AND para:(Gabbard AND -impact))`
        
    <b>Find documents with the words flying and falling in the same paragraph in a dream:</b>

    `{!parent which="art_level:1"} art_level:2 AND parent_tag:p_dream AND para:(flying AND falling)`

    To return the matching "full" paras as records, you can directly search the child documents.  However, you will not
    get the parent document data as part of the return in this case (the fields will be in the return records, but the data will just be 'null').
    The matching paras will be in the field para in the return records, and there will be no marked hits.
    
    ##### Child Only Query Example
       
    `parent_tag:p_dream AND para:(flying AND wings)`
    
    ##### Child Only Return data example (abbreviated) from above example (null fields removed)
     
       ```
       "response":{"numFound":3,"start":0,"maxScore":11.844459,"docs":[
           {
             "parent_tag":"p_dream",
             "para":"<p><i>I'm on an island beach looking out over a large body of water. High above the beach just making its way out over the water is an enormous flying contraption whose wings appear to be made of silk that is beige or golden in color. Roosting on the wings are exotic birds whose plumage is also this color. It's moving slowly out over the water. It's a remarkable sight</i>.</p>",
             "art_level":2,
             "score":11.844459},
           {
             "parent_tag":"p_dream",
             "para":"<p>I was with my brother, going to a meeting. I felt sick, and soiled my pants. It was a mess. Then I showed him where he could get fresh clothes—odd, <impx type=\"TERM2\" rx=\"ZBK.069.0001c.YN0004867612400\" grpname=\"CAUSE\">cause</impx> I was the one that made the mess.—Then we're back at the meeting, where I should be able to find my brother, but I can't. I'm looking all over, moving faster, and then…. I started to fly! A woman applauded and encouraged my flying. And I said “I like to do it this smooth way, don't need to flap wings harder.” Then I was flying over a college campus, a festive scene, but then I realized I'd forgotten my brother and felt guilty.</p>",
             "art_level":2,
             "score":10.832498},
           {
             "parent_tag":"p_dream",
             "para":"<p2>eyes, but at the same time I am full of joy, because it is a beautiful <impx type=\"TERM2\" rx=\"ZBK.069.0001d.YN0013300865870\" grpname=\"DEATH\">death</impx>. At this <impx type=\"TERM2\" rx=\"ZBK.069.0001m.YP0001417964900\" grpname=\"MOMENT\">moment</impx> the sliding stops, and I see someone who is flying. He glides downward several times; then he again wings upwards. I am watching him at these performances, and a young man with a pince nez is also looking up. I am no longer alone. He is singing a very nice Russian song, which I have heard already. As the aviator disappears, the scene changes and I am no longer in the N<su>***</su> Valley in G<su>***</su> but in the S<su>***</su> Park in B<su>***</su>, and I am singing or humming the song too. He asks me whether he may accompany me. I tell him that he may walk with me to the optometrist. A piece of my lorgnette had broken off, and I want to have it repaired. I start to cross the street at the S<su>***</su> Park, but the young man has disappeared. Then I awake.</p2>",
             "art_level":2,
             "score":8.666403
           }
           ]
       ```

    ### Thesaurus matching
    
    Solr thesaurus matching is either on or off for a field, it's not something you can specify as a query parameter to Solr.
    So for thesaurus matches, where desirable, a secondary field is defined with the suffix _syn that has the PEP thesaurus enabled.
    
    This currently includes
        * text -> text_syn
        * title -> title_syn
        * para -> para_syn
        
    ### Final Notes
    
       * Solr advanced queries are case sensitive. The boolean connector AND must be in caps.
       * important to understand the applicable schema to query (unless you only search the default field text)

    ## Return Type
       models.DocumentList

    ## Status
       Status: Still in Development and testing

    """
    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    session_id = session_info.session_id 

    if re.search(r"/Search/", request.url._url):
        logger.debug("Search Request: %s", request.url._url)
        
    facet_fields = opasAPISupportLib.string_to_list(facet_fields)
    if facet_fields == []:
        facet_fields = None # string to list returns [] if no parameter, but to omit return data, send None for facet_fields
        
    #  just to play let's try this direct instead using a nested para approach   
    ret_val, ret_status = opasAPISupportLib.search_text(query=advanced_query, 
                                                        filter_query = None,
                                                        full_text_requested = False,
                                                        abstract_requested = False, 
                                                        query_debug = False, # TEMPORARY
                                                        def_type = def_type, # edisMax, disMax, or None
                                                        highlight_fields=highlight_fields,
                                                        facet_fields = facet_fields,
                                                        sort = sort,
                                                        limit=limit, 
                                                        offset=offset,
                                                        extra_context_len=200
                                                        )

    #  if there's a Solr server error in the call, it returns a non-200 ret_status[0]
    if ret_status[0] != HTTP_200_OK:
        #  throw an exception rather than return an object (which will fail)
        #TODO: should we let this fall through to log the endpoint even though there was an error?
        return ret_val # function returns - models.ErrorReturn
        #raise HTTPException(
            #status_code=ret_status[0], 
            #detail=f"Bad Solr Search Request. {ret_status[1].reason}:{ret_status[1].body}"
        #)
    else:
        if ret_val != {}:
            matches = len(ret_val.documentList.responseSet)
            ret_val.documentList.responseInfo.request = request.url._url
        else:
            matches = 0

        statusMsg = f"{matches} hits"
        logger.debug(statusMsg)

    # client_host = request.client.host
    ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_DATABASE_ADVANCEDSEARCH,
                                session_info=session_info, 
                                params=request.url._url,
                                status_message=statusMsg
                                )

    return ret_val

#---------------------------------------------------------------------------------------------------------
@app.get("/v1/Database/Search/", response_model_exclude_unset=True, tags=["PEPEasy1 (Deprecated)"], summary=opasConfig.ENDPOINT_SUMMARY_SEARCH_V1) #  removed pydantic validation for now: response_model=models.DocumentList, 
async def database_search_v1(response: Response, 
                             request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                             fulltext1: str=Query(None, title=opasConfig.TITLE_FULLTEXT1_V1, description=opasConfig.DESCRIPTION_FULLTEXT1_V1),
                             zone1: str=Query("doc", title=opasConfig.TITLE_PARAZONE1_V1, description=opasConfig.DESCRIPTION_PARAZONE_V1),
                             synonyms: bool=Query(False, title=opasConfig.TITLE_SYNONYMS, description=opasConfig.DESCRIPTION_SYNONYMS),
                             # filters, v1 naming
                             journal: str=Query(None, title=opasConfig.TITLE_SOURCECODE, description=opasConfig.DESCRIPTION_SOURCECODE), 
                             volume: str=Query(None, title=opasConfig.TITLE_VOLUMENUMBER, description=opasConfig.DESCRIPTION_VOLUMENUMBER), 
                             author: str=Query(None, title=opasConfig.TITLE_AUTHOR, description=opasConfig.DESCRIPTION_AUTHOR), 
                             title: str=Query(None, title=opasConfig.TITLE_TITLE, description=opasConfig.DESCRIPTION_TITLE),
                             startyear: str=Query(None, title=opasConfig.TITLE_STARTYEAR, description=opasConfig.DESCRIPTION_STARTYEAR), 
                             endyear: str=Query(None, title=opasConfig.TITLE_ENDYEAR, description=opasConfig.DESCRIPTION_ENDYEAR), 
                             sort: str=Query("score desc", title=opasConfig.TITLE_SORT, description=opasConfig.DESCRIPTION_SORT),
                             limit: int=Query(15, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                             offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
                            ):
    """
    ## Function
       <b>Backwards compatibility function to search the database by a simple list of words within paragraphs for the PEPEasy client.</b>
       
       In v1, at GVPi, search was by para, for field fulltext1.  It also allowed for scopes.
       
       In the v2 function, the names of these parameters will be changed to reflect whether it's para or full document search.

       New functionality and names are not present here.  This just maps the old interface onto the newwer v2 function

    ## Return Type
       models.DocumentList

    ## Status
       Status: In Development

    ## Sample Call

    ## Notes

    ## Potential Errors

    """
    # need to decide if we should parse and cleanup fulltext1.
    # IMPORTANT NOTE: when calling another endpoint directly like this, you must include all parameters, or else what gets defaulted for that 
    #                 schema description which isn't what you want!
    ret_val = await database_search_paragraphs(response,
                                               request,
                                               paratext=fulltext1, #  no advanced search. Only words, phrases, prox ~ op, and booleans allowed
                                               parascope=zone1,
                                               synonyms=synonyms, 
                                               sourcecode=journal,
                                               sourcename=None, # not used in V1
                                               sourcetype=None, # not used in V1
                                               sourcelangcode=None, # not used in v1
                                               volume=volume, 
                                               author=author,
                                               title=title,
                                               articletype=None, # not used in V1
                                               startyear=startyear,
                                               endyear=endyear, 
                                               citecount=None,   # not used in V1 
                                               viewcount=None,   # not used in V1
                                               facetfields=None, 
                                               sort=sort,
                                               limit=limit,
                                               offset=offset
                                               )
    return ret_val
#---------------------------------------------------------------------------------------------------------
@app.get("/v2/Database/SearchParagraphs/", tags=["Database"], summary=opasConfig.ENDPOINT_SUMMARY_SEARCH_PARAGRAPHS)  #  response_model_exclude_unset=True removed for now: response_model=models.DocumentList, 
async def database_search_paragraphs(response: Response, 
                                     request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                                     # path parameters
                                     termlist: models.SolrQueryTermList=None, # experimental, allows full specification in body per models.QuerySpecification
                                     # query parameters
                                     paratext: str=Query(None, title=opasConfig.TITLE_PARATEXT, description=opasConfig.DESCRIPTION_PARATEXT),
                                     parascope: str=Query("doc", title=opasConfig.TITLE_PARASCOPE, description=opasConfig.DESCRIPTION_PARASCOPE),
                                     synonyms: bool=Query(False, title=opasConfig.TITLE_SYNONYMS, description=opasConfig.DESCRIPTION_SYNONYMS),
                                     # query parameters mapped to filters (Solr query filter)
                                     sourcename: str=Query(None, title=opasConfig.TITLE_SOURCENAME, description=opasConfig.DESCRIPTION_SOURCENAME),  
                                     sourcecode: str=Query(None, title=opasConfig.TITLE_SOURCECODE, description=opasConfig.DESCRIPTION_SOURCECODE), 
                                     sourcetype: str=Query(None, title=opasConfig.TITLE_SOURCETYPE, description=opasConfig.DESCRIPTION_PARAM_SOURCETYPE),
                                     sourcelangcode: str=Query(None, title=opasConfig.TITLE_SOURCELANGCODE, description=opasConfig.DESCRIPTION_SOURCELANGCODE),
                                     volume: str=Query(None, title=opasConfig.TITLE_VOLUMENUMBER, description=opasConfig.DESCRIPTION_VOLUMENUMBER), 
                                     author: str=Query(None, title=opasConfig.TITLE_AUTHOR, description=opasConfig.DESCRIPTION_AUTHOR), 
                                     title: str=Query(None, title=opasConfig.TITLE_TITLE, description=opasConfig.DESCRIPTION_TITLE),
                                     articletype: str=Query(None, title=opasConfig.TITLE_ARTICLETYPE, description=opasConfig.DESCRIPTION_ARTICLETYPE),
                                     startyear: str=Query(None, title=opasConfig.TITLE_STARTYEAR, description=opasConfig.DESCRIPTION_STARTYEAR), 
                                     endyear: str=Query(None, title=opasConfig.TITLE_ENDYEAR, description=opasConfig.DESCRIPTION_ENDYEAR), 
                                     citecount: str=Query(None, title=opasConfig.TITLE_CITECOUNT, description=opasConfig.DESCRIPTION_CITECOUNT),   
                                     viewcount: str=Query(None, title=opasConfig.TITLE_VIEWCOUNT, description=opasConfig.DESCRIPTION_VIEWCOUNT),
                                     # return set control
                                     facetfields: str=Query(None, title=opasConfig.TITLE_FACETFIELDS, description=opasConfig.DESCRIPTION_FACETFIELDS), 
                                     sort: str=Query("score desc", title=opasConfig.TITLE_SORT, description=opasConfig.DESCRIPTION_SORT),
                                     limit: int=Query(15, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                                     offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
                                     ):
    """
    ## Function
       <b>Convenience function to search the database by basic criteria (as exemplified in PEP-Easy).</b>
       
       Multiple word search is within markup terminals, namely a paragraph.  The scope is the parent of the paragraph
       and this currently supports:
        - doc
        - dreams
        - dialogs
        - quotes
        - poems
        - references (each reference is the equivalent of paragraph)

    ## Return Type
       models.DocumentList

    ## Status
       Status: In Development

    ## Sample Call

    ## Notes

    ## Potential Errors

    """

    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    # session_id = session_info.session_id 
    logger.debug("Search Request: %s", request.url._url)
        
    # this does intelligent processing of the query parameters and returns a
    # smaller set of solr oriented params (per pydantic model
    # SolrQueryParameters), ready to use
    solr_query_spec = \
        opasQueryHelper.parse_search_query_parameters(para_textsearch=paratext,
                                                      para_scope=parascope, 
                                                      solrQueryTermList=termlist,
                                                      synonyms=synonyms, 
                                                      source_name=sourcename,
                                                      source_code=sourcecode,
                                                      source_lang_code=sourcelangcode,
                                                      vol=volume,
                                                      author=author,
                                                      title=title,
                                                      startyear=startyear,
                                                      endyear=endyear, 
                                                      #references=references,
                                                      articletype=articletype, 
                                                      citecount=citecount,
                                                      viewcount=viewcount,
                                                      facetfields=facetfields, 
                                                      sort = sort
                                                    )
    solr_query_spec.urlRequest = request.url._url
    solr_query_params = solr_query_spec.solrQuery
    solr_query_opts = solr_query_spec.solrQueryOpts

    ret_val, ret_status = opasAPISupportLib.search_text(query=solr_query_params.searchQ, 
                                                        filter_query = solr_query_params.filterQ,
                                                        full_text_requested = False,
                                                        abstract_requested = False, 
                                                        query_debug = False, # TEMPORARY
                                                        def_type = None, # edisMax, disMax, or None
                                                        facet_fields = solr_query_opts.facetFields, 
                                                        sort = solr_query_params.sort,
                                                        limit=limit, 
                                                        offset=offset,
                                                        extra_context_len=200
                                                        )

    #  if there's a Solr server error in the call, it returns a non-200 ret_status[0]
    if ret_status[0] != HTTP_200_OK:
        #  throw an exception rather than return an object (which will fail)
        return models.ErrorReturn(error="Search syntax error", error_description=f"The search engine returned an error ({ret_status[1].reason}:{ret_status[1].body}) from your search input (FQ:{solr_query_params.filterQ} Q:{solr_query_params.searchQ}).")
        #raise HTTPException(
            #status_code=ret_status[0], 
            #detail=f"Bad Solr Search Request. {ret_status[1].reason}:{ret_status[1].body}"
        #)

    if ret_val != {}:
        matches = len(ret_val.documentList.responseSet)
        ret_val.documentList.responseInfo.request = request.url._url
    else:
        matches = 0

    statusMsg = f"{matches} hits"
    logger.debug(statusMsg)

    # client_host = request.client.host
    ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_DATABASE_SEARCH,
                                session_info=session_info, 
                                params=request.url._url,
                                status_message=statusMsg
                                )

    return ret_val

#---------------------------------------------------------------------------------------------------------
@app.get("/v2/Database/Search/", response_model=models.DocumentList, response_model_exclude_unset=True, tags=["Database"], summary=opasConfig.ENDPOINT_SUMMARY_SEARCH_V2)
@app.get("/v2/Database/MoreLikeThese/", response_model=models.DocumentList, response_model_exclude_unset=True, tags=["Database"], summary=opasConfig.ENDPOINT_SUMMARY_SEARCH_MORE_LIKE_THESE)
async def database_search_v2( response: Response, 
                              request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                              termlist: models.SolrQueryTermList=None, # allows full specification
                              fulltext1: str=Query(None, title=opasConfig.TITLE_FULLTEXT1, description=opasConfig.DESCRIPTION_FULLTEXT1),
                              paratext: str=Query(None, title=opasConfig.TITLE_PARATEXT, description=opasConfig.DESCRIPTION_PARATEXT),
                              parascope: str=Query(None, title=opasConfig.TITLE_PARASCOPE, description=opasConfig.DESCRIPTION_PARASCOPE),
                              synonyms: bool=Query(False, title=opasConfig.TITLE_SYNONYMS, description=opasConfig.DESCRIPTION_SYNONYMS),
                              # filters (Solr query filter)
                              sourcename: str=Query(None, title=opasConfig.TITLE_SOURCENAME, description=opasConfig.DESCRIPTION_SOURCENAME, min_length=2),  
                              sourcecode: str=Query(None, title=opasConfig.TITLE_SOURCECODE, description=opasConfig.DESCRIPTION_SOURCECODE, min_length=2), 
                              sourcetype: str=Query(None, title=opasConfig.TITLE_SOURCETYPE, description=opasConfig.DESCRIPTION_PARAM_SOURCETYPE), 
                              sourcelangcode: str=Query("EN", title=opasConfig.TITLE_SOURCELANGCODE, description=opasConfig.DESCRIPTION_SOURCELANGCODE), 
                              volume: str=Query(None, title=opasConfig.TITLE_VOLUMENUMBER, description=opasConfig.DESCRIPTION_VOLUMENUMBER), 
                              issue: str=Query(None, title=opasConfig.TITLE_ISSUE, description=opasConfig.DESCRIPTION_ISSUE),
                              author: str=Query(None, title=opasConfig.TITLE_AUTHOR, description=opasConfig.DESCRIPTION_AUTHOR), 
                              title: str=Query(None, title=opasConfig.TITLE_TITLE, description=opasConfig.DESCRIPTION_TITLE),
                              articletype: str=Query(None, title=opasConfig.TITLE_ARTICLETYPE, description=opasConfig.DESCRIPTION_ARTICLETYPE),
                              startyear: str=Query(None, title=opasConfig.TITLE_STARTYEAR, description=opasConfig.DESCRIPTION_STARTYEAR), 
                              endyear: str=Query(None, title=opasConfig.TITLE_ENDYEAR, description=opasConfig.DESCRIPTION_ENDYEAR), 
                              citecount: str=Query(None, title=opasConfig.TITLE_CITECOUNT, description=opasConfig.DESCRIPTION_CITECOUNT),   
                              viewcount: str=Query(None, title=opasConfig.TITLE_VIEWCOUNT, description=opasConfig.DESCRIPTION_VIEWCOUNT),    
                              viewedwithin: str=Query(None, title=opasConfig.TITLE_VIEWEDWITHIN, description=opasConfig.DESCRIPTION_VIEWEDWITHIN),     
                              # return set control
                              facetfields: str=Query(None, title=opasConfig.TITLE_FACETFIELDS, description=opasConfig.DESCRIPTION_FACETFIELDS), 
                              sort: str=Query("score desc", title=opasConfig.TITLE_SORT, description=opasConfig.DESCRIPTION_SORT),
                              limit: int=Query(15, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                              offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
                            ):
    """
    ## Function
       <b>Search the database per one or more of the fields specified.</b>

       Some of the fields should probably be deprecated, but for now, they support PEP-Easy,
       as configured to use the GVPi based PEP Server
       endyear isn't needed, because startyear can handle the ranges (and better than before).
       journal is also configured to take anything that would have otherwise been entered in sourcename

       Search terms can also be put into "termlist", so synonyms can be turned on term by term, defined as this model

       ```
          termlist =
           {"query" : [
               {   /* SolrQueryTerm 1 */
                   "words":"first term",
                   "field": "text_xml",
                   "synonyms": "false"
               },
               {   /* SolrQueryTerm 2 (optional, ...) */
                   "words":"unconscious",
                   "field": "text_xml",
                   "synonyms": "true"
               }
               /* repeat as needed */
               ],
           "solrQueryOpts" : {
                   "hlFields": "text_xml",
               }
           }
       ```
   
     e.g.,
   
       ```
           {"query" : [
                   {
                       "words":"unconscious",
                       "field": "text_xml",
                       "synonyms": "false",
                   }
               ],
            "solrQueryOpts": 
                  {
                       "hlFields": "text_xml"
                  }
           }
           
           or
           
           
           {"query" : [
                  {
                         "words":"parent abuse",
                         "field": "para",
                         "synonyms": "false",
                   },
                   {
                         "words":"aggression",
                         "field": "para",
                         "synonyms": "true",
                   }
               ]
           }
       ```
    ## Return Type
       models.DocumentList

    ## Status
       Status: In Development

       #TODO:    
          viewcount, viewedWithin not yet implemented...and probably will be streamlined for future use.
          disMax, edisMax also not yet implemented

          
    ## Sample Call
         /v2/Database/MoreLikeThese/
         /v2/Database/Search/"

    ## Notes

    ## Potential Errors

    """

    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    # session_id = session_info.session_id 

    if re.search(r"/Search/", request.url._url):
        logger.debug("Search Request: %s", request.url._url)

    analysis_mode = False

    if re.search(r"/MoreLikeThese/", request.url._url):
        logger.debug("MoreLikeThese Request: %s", request.url._url)
        more_like_these_mode = True
    else:
        more_like_these_mode = False

    # don't set parascope, unless they set paratext and forgot to set parascope
    if paratext is not None and parascope is None:
        parascope = "doc"

    # current_year = datetime.utcfromtimestamp(time.time()).strftime('%Y')
    # this does intelligent processing of the query parameters and returns a smaller set of solr oriented         
    # params (per pydantic model SolrQuery), ready to use
    solr_query_spec = \
        opasQueryHelper.parse_search_query_parameters(solrQueryTermList=termlist,
                                                      source_name=sourcename,
                                                      source_code=sourcecode,
                                                      source_type=sourcetype,
                                                      source_lang_code=sourcelangcode,
                                                      para_textsearch=paratext, # search within paragraphs
                                                      para_scope=parascope, # scope for par_search
                                                      fulltext1=fulltext1,  # more flexible search, including fields, anywhere in the doc, across paras
                                                      synonyms=synonyms, 
                                                      vol=volume,
                                                      issue=issue,
                                                      author=author,
                                                      title=title,
                                                      articletype=articletype, 
                                                      startyear=startyear,
                                                      endyear=endyear,
                                                      citecount=citecount,
                                                      viewcount=viewcount,
                                                      viewedwithin=viewedwithin,
                                                      facetfields=facetfields, 
                                                      sort = sort
                                                      )
    solr_query_spec.urlRequest = request.url._url
    solr_query_params = solr_query_spec.solrQuery
    solr_query_opts = solr_query_spec.solrQueryOpts

    ret_val, ret_status = opasAPISupportLib.search_text(query=solr_query_params.searchQ, 
                                                        filter_query = solr_query_params.filterQ,
                                                        full_text_requested = False,
                                                        abstract_requested = False, 
                                                        query_debug = True, # TEMPORARY
                                                        more_like_these = more_like_these_mode,
                                                        facet_fields = solr_query_opts.facetFields, 
                                                        sort = solr_query_params.sort,
                                                        limit = limit, 
                                                        offset = offset,
                                                        extra_context_len = 200
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

    ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_DATABASE_SEARCH,
                                session_info=session_info, 
                                params=request.url._url,
                                status_message=statusMsg
                                )

    return ret_val

#---------------------------------------------------------------------------------------------------------
@app.get("/v1/Database/SearchAnalysis/", response_model_exclude_unset=True, tags=["PEPEasy1 (Deprecated)"], summary=opasConfig.ENDPOINT_SUMMARY_SEARCH_ANALYSIS)  #  remove validation response_model=models.DocumentList, 
async def database_searchanalysis_v1(response: Response, 
                                     request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                                     fulltext1: str=Query(None, title=opasConfig.TITLE_FULLTEXT1_V1, description=opasConfig.DESCRIPTION_FULLTEXT1_V1),
                                     zone1: str=Query("doc", title=opasConfig.TITLE_PARAZONE1_V1, description=opasConfig.DESCRIPTION_PARAZONE_V1),
                                     synonyms: bool=Query(False, title=opasConfig.TITLE_SYNONYMS, description=opasConfig.DESCRIPTION_SYNONYMS),
                                     # filters (Solr query filter)
                                     journal: str=Query(None, title=opasConfig.TITLE_SOURCECODE, description=opasConfig.DESCRIPTION_SOURCECODE, min_length=2), 
                                     volume: str=Query(None, title=opasConfig.TITLE_VOLUMENUMBER, description=opasConfig.DESCRIPTION_VOLUMENUMBER), 
                                     author: str=Query(None, title=opasConfig.TITLE_AUTHOR, description=opasConfig.DESCRIPTION_AUTHOR), 
                                     title: str=Query(None, title=opasConfig.TITLE_TITLE, description=opasConfig.DESCRIPTION_TITLE),
                                     startyear: str=Query(None, title=opasConfig.TITLE_STARTYEAR, description=opasConfig.DESCRIPTION_STARTYEAR), 
                                     endyear: str=Query(None, title=opasConfig.TITLE_ENDYEAR, description=opasConfig.DESCRIPTION_ENDYEAR), 
                                     # return set control
                                     sort: str=Query("score desc", title=opasConfig.TITLE_SORT, description=opasConfig.DESCRIPTION_SORT),
                                     limit: int=Query(15, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                                     offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
                                    ):
    """
    ## Function
       <b>Backwards compatibility function to analyze the search .</b>

       New functionality and names are not present here.  This just maps the old interface onto the newwer v2 function

    ## Return Type
       models.DocumentList

    ## Status
       Status: In Development
       This endpoint is DEPRECATED

    ## Sample Call

    ## Notes

    ## Potential Errors

    """
    # need to decide if we should parse and cleanup fulltext1.
    
    solr_query_spec = \
        opasQueryHelper.parse_search_query_parameters(para_textsearch=fulltext1,     # v1 fulltext was by para  
                                                      para_scope=zone1,              # from v1 terminology
                                                      source_code=journal,
                                                      synonyms=synonyms, 
                                                      vol=volume,
                                                      author=author,
                                                      title=title,
                                                      startyear=startyear,
                                                      sort = sort
                                                      )

    solr_query_spec.urlRequest = request.url._url
    solr_query_params = solr_query_spec.solrQuery

    # We don't always need full-text, but if we need to request the doc later we'll need to repeat the search parameters plus the docID
    ret_val = opasAPISupportLib.search_analysis(query_list=solr_query_params.searchAnalysisTermList, 
                                                filter_query = solr_query_params.filterQ,
                                                def_type = "lucene",
                                                full_text_requested=False,
                                                limit=limit, 
                                                api_version="v1"
                                                )

    logger.debug("Done with search analysis.")
    # print (f"Search analysis called: {solr_query_params}")

    return ret_val

#---------------------------------------------------------------------------------------------------------
@app.get("/v2/Database/SearchAnalysis/", response_model_exclude_unset=True, tags=["Database"], summary=opasConfig.ENDPOINT_SUMMARY_SEARCH_ANALYSIS)  #  remove validation response_model=models.DocumentList, 
def database_searchanalysis(response: Response, 
                            request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                            termlist: models.SolrQueryTermList=None, # allows full specification
                            fulltext1: str=Query(None, title=opasConfig.TITLE_FULLTEXT1, description=opasConfig.DESCRIPTION_FULLTEXT1),
                            paratext: str=Query(None, title=opasConfig.TITLE_PARATEXT, description=opasConfig.DESCRIPTION_PARATEXT),
                            parascope: str=Query(None, title=opasConfig.TITLE_PARASCOPE, description=opasConfig.DESCRIPTION_PARASCOPE),
                            synonyms: bool=Query(False, title=opasConfig.TITLE_SYNONYMS, description=opasConfig.DESCRIPTION_SYNONYMS),
                            # filters (Solr query filter)
                            sourcename: str=Query(None, title=opasConfig.TITLE_SOURCENAME, description=opasConfig.DESCRIPTION_SOURCENAME, min_length=2),  
                            sourcecode: str=Query(None, title=opasConfig.TITLE_SOURCECODE, description=opasConfig.DESCRIPTION_SOURCECODE, min_length=2),
                            sourcelangcode: str=Query(None, title=opasConfig.TITLE_SOURCELANGCODE, description=opasConfig.DESCRIPTION_SOURCELANGCODE), 
                            volume: str=Query(None, title=opasConfig.TITLE_VOLUMENUMBER, description=opasConfig.DESCRIPTION_VOLUMENUMBER), 
                            issue: str=Query(None, title=opasConfig.TITLE_ISSUE, description=opasConfig.DESCRIPTION_ISSUE),
                            author: str=Query(None, title=opasConfig.TITLE_AUTHOR, description=opasConfig.DESCRIPTION_AUTHOR), 
                            title: str=Query(None, title=opasConfig.TITLE_TITLE, description=opasConfig.DESCRIPTION_TITLE),
                            articletype: str=Query(None, title=opasConfig.TITLE_ARTICLETYPE, description=opasConfig.DESCRIPTION_ARTICLETYPE),
                            startyear: str=Query(None, title=opasConfig.TITLE_STARTYEAR, description=opasConfig.DESCRIPTION_STARTYEAR), 
                            endyear: str=Query(None, title=opasConfig.TITLE_ENDYEAR, description=opasConfig.DESCRIPTION_ENDYEAR), 
                            citecount: str=Query(None, title=opasConfig.TITLE_CITECOUNT, description=opasConfig.DESCRIPTION_CITECOUNT),   
                            viewcount: str=Query(None, title=opasConfig.TITLE_VIEWCOUNT, description=opasConfig.DESCRIPTION_VIEWCOUNT),    
                            viewedwithin: str=Query(None, title=opasConfig.TITLE_VIEWEDWITHIN, description=opasConfig.DESCRIPTION_VIEWEDWITHIN),     
                            # return set control
                            facetfields: str=Query(None, title=opasConfig.TITLE_FACETFIELDS, description=opasConfig.DESCRIPTION_FACETFIELDS), 
                            sort: str=Query("score desc", title=opasConfig.TITLE_SORT, description=opasConfig.DESCRIPTION_SORT),
                            limit: int=Query(15, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                            offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
                         ):

    # don't set parascope, unless they set paratext and forgot to set parascope
    if paratext is not None and parascope is None:
        parascope = "doc"

    # this does intelligent processing of the query parameters and returns a smaller set of solr oriented         
    # params (per pydantic model SolrQuery), ready to use
    solr_query_spec = \
        opasQueryHelper.parse_search_query_parameters(solrQueryTermList=termlist,
                                                      source_name=sourcename,
                                                      source_code=sourcecode,
                                                      source_lang_code=sourcelangcode, 
                                                      para_textsearch=paratext, # search within paragraphs
                                                      para_scope=parascope, # scope for par_search
                                                      fulltext1=fulltext1,  # more flexible search, including fields, anywhere in the doc, across paras
                                                      synonyms=synonyms, 
                                                      vol=volume,
                                                      issue=issue,
                                                      author=author,
                                                      title=title,
                                                      articletype=articletype, 
                                                      startyear=startyear,
                                                      endyear=endyear,
                                                      citecount=citecount,
                                                      viewcount=viewcount,
                                                      viewedwithin=viewedwithin,
                                                      facetfields=facetfields, 
                                                      sort = sort
                                                      )

    solr_query_spec.urlRequest = request.url._url
    solr_query_params = solr_query_spec.solrQuery

    # We don't always need full-text, but if we need to request the doc later we'll need to repeat the search parameters plus the docID
    ret_val = opasAPISupportLib.search_analysis(query_list=solr_query_params.searchAnalysisTermList, 
                                                filter_query = solr_query_params.filterQ,
                                                def_type = "lucene",
                                                #query_analysis=analysis_mode,
                                                #more_like_these = None,
                                                full_text_requested=False,
                                                limit=limit, 
                                                api_version="v2"
                                                )

    logger.debug("Done with search analysis.")
    # print (f"Search analysis called: {solr_query_params}")

    return ret_val
#---------------------------------------------------------------------------------------------------------
@app.get("/v2/Database/ExtendedSearch/", response_model=models.SolrReturnList, tags=["Database"], summary=opasConfig.ENDPOINT_SUMMARY_EXTENDED_SEARCH)  #  response_model_exclude_unset=True removed for now: response_model=models.DocumentList, 
async def database_extendedsearch(response: Response,
                                  request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                                  solrQuerySpec: models.SolrQuerySpec=None, # allows full specification of parameters in the body
                                  api_key: APIKey = Depends(get_api_key)
                                 ):
    """
    ## Function
    <b>Search_extended Solr style</b>
    
    Perform a solr query using solr parameter definitions with any server core.
    
    API_KEY required.
    
    #TODO: For security, the endpoint is configured not to allow the return of PEP text_xml. Now there's an API_KEY requirement,
           consider removing constraint
    
    IMPORTANT NOTE: This endpoint is intended for client (user interface) developers to take advantage of the
    full Solr query functionality beyond what the current endpoints allow, without directly connecting to Solr.
    It provides a flexible Solr return set, but offers a bit of a hand by integrating highlighted (match) data with
    return data, which are returned in separate lists in the normal Solr return structure.  For flexibility and expandability,
    this endpoint requires parameters in the REST call body, according to the models.SolrQuerySpec structure
    rather than as URL arguments.  To test, call with an REST API test tool like Postman. Postman
    also provides a nice 'pretty printed' data return.
    
    The API user must be logged in to a valid account currently to use this for full-text return (return size is limited).
    
    The documentation on how to use the advanced query is intimately tied to the schemas (data structure based on the PEP DTDs).
    But it's not possible to provide query examples and sample data returns without tying them to a schema.

    This endpoint is not used in PEP-Easy because it isn't needed to provide any of the PEP-Easy functionality, all of which are built in
    to other endpoints.  PEP-Easy functionality only requires what was present in the v1 API (and not the expanded v2 API).

    ## Return Type
       SolrReturnList - flexible field solr results in the responseSet of an otherwise OPAS standard structure 
       
    #### Sample queries
        
    ##### <b>Find documents with paragraphs which contain Othogenic school, returning art_id, title, and art_citeas_xml:</b>
    
    ###### Request Body
    ```
    { 
        "core" : "pepwebdocs",
        "solrQuery" : {
                        "searchQ" : "Orthogenic\u0020school",
                        "fullReturn": false
        },
        "solrQueryOpts" : {
            "returnFields": "art_id, title, art_citeas_xml",
            "hlFields": "text_xml",
            "hlFragsize": 100,
            "hlSnippets" : 10,
            "hlUsePhraseHighlighter" : "true"
        }
    }
    ```
        
       
    ## Status
       Status: New, created 2020-01-03 and now in development and testing 

    ## Notes
    See also /v2/Database/AdvancedSearch/ for an alternative endpoint which returns data
    in OPAS DocumentList format.

    ## Potential Errors

    """

    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    # session_id = session_info.session_id 
    logger.debug("Solr Search Request: %s", request.url._url)
    solr_ret_list = None
    
    if solrQuerySpec is not None:
        solrQuery = solrQuerySpec.solrQuery
        if solrQuery is not None:
            solrQueryOpts = solrQuerySpec.solrQueryOpts
            if solrQuery.returnFields is None:
                solrQuery.returnFields = "id, file_classification" #  need to always return id
            else:
                solrQuery.returnFields += ", id, file_classification"

            # don't let them bring back full-text content in at least PEP schema fields in docs or glossary
            solrQuery.returnFields = re.sub("(,\s*?)?[^A-z0-9](text_xml|para|term_def_rest_xml)[^A-z0-9]", "", solrQuery.returnFields)
            # limited return, no full-text, EVER (because it could be used to bypass the embargo.)
            fragSize = opasConfig.DEFAULT_KWIC_CONTENT_LENGTH 

            #TODO allow core parameter here 
            solr_docs = solr.SolrConnection(localsecrets.SOLRURL + solrQuerySpec.core, http_user=localsecrets.SOLRUSER, http_pass=localsecrets.SOLRPW)
            # see if highlight fields are selected
            hl = solrQueryOpts.hlFields is not None
                
            try:
                if hl:
                    results = solr_docs.query(q = solrQuery.searchQ,  
                                              fq = solrQuery.filterQ,
                                              q_op = solrQueryOpts.qOper.upper(), 
                                              fields = solrQuery.returnFields, 
                                              # highlighting parameters
                                              hl = "true",
                                              hl_method = solrQueryOpts.hlMethod.lower(),
                                              hl_bs_type="SENTENCE", 
                                              hl_fl = solrQueryOpts.hlFields,
                                              hl_fragsize = fragSize,  # from above
                                              hl_maxAnalyzedChars=solrQueryOpts.hlMaxAnalyzedChars if solrQueryOpts.hlMaxAnalyzedChars>0 else opasConfig.SOLR_HIGHLIGHT_RETURN_FRAGMENT_SIZE, 
                                              hl_multiterm = solrQueryOpts.hlMultiterm, # def "true", # only if highlighting is on
                                              hl_multitermQuery="true",
                                              hl_highlightMultiTerm="true",
                                              hl_weightMatches="true", 
                                              hl_tag_post = solrQueryOpts.hlTagPost,
                                              hl_tag_pre = solrQueryOpts.hlTagPre,
                                              hl_snippets = solrQueryOpts.hlSnippets,
                                              #hl_encoder = "html", # (doesn't work for standard, doesn't do anything we want in unified)
                                              hl_usePhraseHighlighter = solrQueryOpts.hlUsePhraseHighlighter, # only if highlighting is on
                                              #hl_q = solrQueryOpts.hlQ, # doesn't help with phrases; searches for None if it's none!
                                              # morelikethis parameters
                                              mlt = solrQueryOpts.moreLikeThis, # if true turns on morelike this
                                              mlt_fl = solrQueryOpts.moreLikeThisFields, 
                                              mlt_count = solrQueryOpts.moreLikeThisCount,
                                              # paging parameters
                                              rows = solrQuerySpec.limit,
                                              start = solrQuerySpec.offset
                                              )
                    solr_ret_list_items = []
                    for n in results.results:
                        rid = n["id"]
                        n["highlighting"] = results.highlighting[rid]  
                        item = models.SolrReturnItem(solrRet=n)
                        solr_ret_list_items.append(item)
                else:
                    results = solr_docs.query(q = solrQuery.searchQ,  
                                              fq = solrQuery.filterQ,
                                              q_op = "AND", 
                                              fields = solrQueryOpts.returnFields,
                                              # morelikethis parameters
                                              mlt = solrQueryOpts.moreLikeThis, # if true turns on morelike this
                                              mlt_fl = solrQueryOpts.moreLikeThisFields, 
                                              mlt_count = solrQueryOpts.moreLikeThisCount,
                                              # paging parameters
                                              rows = solrQuerySpec.limit,
                                              start = solrQuerySpec.offset
                                              )
                    solr_ret_list_items = []
                    for n in results.results:
                        item = models.SolrReturnItem(solrRet=n)
                        solr_ret_list_items.append(item)
        
            except solr.SolrException as e:
                #if e.httpcode == 400:
                    #ret_val = models.ErrorReturn(httpcode=e.httpcode, error="Search syntax error", error_description=f"There's an error in your input {e.reason}")
                #else:
                    #ret_val = models.ErrorReturn(httpcode=e.httpcode, error="Solr engine returned an unknown error", error_description=f"Solr engine returned error {e.httpcode} - {e.reason}")
                # statusMsg = f"Solr Runtime Search Error: {e.reason}"
                ret_status = (e.httpcode, e)
                raise HTTPException(
                    status_code=ret_status[0], 
                    detail=f"Bad Solr Search Request. {ret_status[1].reason}:{ret_status[1].body}"
                )
                
            statusMsg = f"RAW Q:{solrQuery.searchQ} / F:{solrQuery.filterQ} N: {results._numFound}"
            logger.debug(statusMsg)
        
            response_info = models.ResponseInfo( count = len(solr_ret_list_items),
                                                 fullCount = results._numFound,
                                                 limit = solrQuerySpec.limit,
                                                 offset = solrQuerySpec.offset,
                                                 listType="advancedsearchlist",
                                                 fullCountComplete = solrQuerySpec.limit >= results._numFound,  
                                                 timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                               )
            solr_list_struct = models.SolrReturnStruct( responseInfo = response_info, 
                                                        responseSet = solr_ret_list_items
                                                       )
        
            solr_ret_list = models.SolrReturnList(solrRetList = solr_list_struct)
                
        
            # client_host = request.client.host
            ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_DATABASE_SEARCH,
                                        session_info=session_info, 
                                        params=request.url._url,
                                        status_message=statusMsg
                                        )
    
    return solr_ret_list

#---------------------------------------------------------------------------------------------------------
#@app.get("/v1/Database/MostDownloaded/", response_model=models.DocumentList, response_model_exclude_unset=True, tags=["Deprecated"], summary=opasConfig.ENDPOINT_SUMMARY_MOST_VIEWED)
@app.get("/v2/Database/MostViewed/", response_model=models.DocumentList, response_model_exclude_unset=True, tags=["Database"], summary=opasConfig.ENDPOINT_SUMMARY_MOST_VIEWED)
async def database_mostviewed(response: Response,
                              request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),
                              # period is str because it can be "all"
                              pubperiod: int=Query(None, title=opasConfig.TITLE_PUBLICATION_PERIOD, description=opasConfig.DESCRIPTION_PUBLICATION_PERIOD),
                              # viewperiod=4 Prior cal year, per PEP-Web design
                              viewperiod: int=Query(4, title=opasConfig.TITLE_MOST_VIEWED_PERIOD, description=opasConfig.DESCRIPTION_MOST_VIEWED_PERIOD), # 4=Prior year, per PEP-Web design
                              author: str=Query(None, title=opasConfig.TITLE_AUTHOR, description=opasConfig.DESCRIPTION_AUTHOR), 
                              title: str=Query(None, title=opasConfig.TITLE_TITLE, description=opasConfig.DESCRIPTION_TITLE),
                              sourcename: str=Query(None, title=opasConfig.TITLE_SOURCENAME, description=opasConfig.DESCRIPTION_SOURCENAME),  
                              sourcecode: str=Query(None, title=opasConfig.TITLE_SOURCECODE, description=opasConfig.DESCRIPTION_SOURCECODE), 
                              sourcetype: str=Query(None, title=opasConfig.TITLE_SOURCETYPE, description=opasConfig.DESCRIPTION_PARAM_SOURCETYPE), 
                              limit: int=Query(5, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT), # by PEP-Web standards, we want 10, but 5 is better for PEP-Easy
                              offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
                              ):
    """
    ## Function
       <b>Return a list of documents which are the most downloaded (viewed)</b>

            viewperiod = 0: lastcalendaryear
                         1: lastweek
                         2: lastmonth
                         3: last6months
                         4: last12months                                

                         
    ## Return Type
       models.DocumentList

    ## Status
       This endpoint is working.
       For whatever reason, async works here, without a wait on the long running database call.  And
         adding the await makes it never return

    ## Sample Call
         /v1/Database/MostDownloaded/

    ## Notes

    ## Potential Errors

    """

    # ocd, session_info = opasAPISupportLib.get_session_info(request, resp)
    if viewperiod < 0 or viewperiod > 4:
        viewperiod = 4

    try:
        # we want the last year (default, per PEP-Web) of views, for all articles (journal articles)
        ret_val = opasAPISupportLib.database_get_most_viewed( sort_by_view_period=viewperiod, # limiting to 5, you'd get the 5 biggest values for this view period
                                                              publication_period=pubperiod,
                                                              author=author,
                                                              title=title,
                                                              source_name=sourcename, 
                                                              source_code=sourcecode,
                                                              source_type=sourcetype, 
                                                              limit=limit, 
                                                              offset=offset
                                                            )
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

#---------------------------------------------------------------------------------------------------------
#@app.get("/v1/Database/MostCited/", response_model=models.DocumentList, response_model_exclude_unset=True, tags=["Deprecated"], summary=opasConfig.ENDPOINT_SUMMARY_MOST_CITED)
@app.get("/v2/Database/MostCited/", response_model=models.DocumentList, response_model_exclude_unset=True, tags=["Database"], summary=opasConfig.ENDPOINT_SUMMARY_MOST_CITED)
def database_mostcited(response: Response,
                       request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                       morethan: int=Query(15, title=opasConfig.TITLE_CITED_MORETHAN, description=opasConfig.DESCRIPTION_CITED_MORETHAN),
                       period: str=Query('5', title="Period (5, 10, 20, or all)", description=opasConfig.DESCRIPTION_MOST_CITED_PERIOD),
                       pubperiod: int=Query(None, title=opasConfig.TITLE_PUBLICATION_PERIOD, description=opasConfig.DESCRIPTION_PUBLICATION_PERIOD),
                       author: str=Query(None, title=opasConfig.TITLE_AUTHOR, description=opasConfig.DESCRIPTION_AUTHOR), 
                       title: str=Query(None, title=opasConfig.TITLE_TITLE, description=opasConfig.DESCRIPTION_TITLE),
                       sourcename: str=Query(None, title=opasConfig.TITLE_SOURCENAME, description=opasConfig.DESCRIPTION_SOURCENAME),  
                       sourcecode: str=Query(None, title=opasConfig.TITLE_SOURCECODE, description=opasConfig.DESCRIPTION_SOURCECODE), 
                       sourcetype: str=Query(None, title=opasConfig.TITLE_SOURCETYPE, description=opasConfig.DESCRIPTION_PARAM_SOURCETYPE), 
                       limit: int=Query(10, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                       offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
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
    # session_id = session_info.session_id 

    #print ("in most cited")
    try:
        # return documentList
        ret_val = opasAPISupportLib.database_get_most_cited( period=period,
                                                             more_than=morethan,
                                                             publication_period=pubperiod,
                                                             author=author,
                                                             title=title,
                                                             source_name=sourcename, 
                                                             source_code=sourcecode,
                                                             source_type=sourcetype, 
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

#---------------------------------------------------------------------------------------------------------
@app.get("/v1/Database/WhatsNew/", response_model=models.WhatsNewList, response_model_exclude_unset=True, tags=["PEPEasy1 (Deprecated)"], summary=opasConfig.ENDPOINT_SUMMARY_WHATS_NEW)
@app.get("/v2/Database/WhatsNew/", response_model=models.WhatsNewList, response_model_exclude_unset=True, tags=["Database"], summary=opasConfig.ENDPOINT_SUMMARY_WHATS_NEW)
def database_whatsnew(response: Response,
                      request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                      days_back: int=Query(14, title=opasConfig.TITLE_DAYSBACK, description=opasConfig.DESCRIPTION_DAYSBACK),
                      limit: int=Query(5, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                      offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
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

#-----------------------------------------------------------------------------
#@app.get("/v1/Metadata/Contents/{SourceCode}/", response_model=models.DocumentList, response_model_exclude_unset=True, tags=["Deprecated"], summary=opasConfig.ENDPOINT_SUMMARY_CONTENTS_SOURCE)
@app.get("/v2/Metadata/Contents/{SourceCode}/", response_model=models.DocumentList, response_model_exclude_unset=True, tags=["Metadata"], summary=opasConfig.ENDPOINT_SUMMARY_CONTENTS_SOURCE)
def metadata_contents_sourcecode(response: Response,
                                 request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                                 SourceCode: str=Path(..., title=opasConfig.TITLE_SOURCECODE, description=opasConfig.DESCRIPTION_SOURCECODE), 
                                 year: str=Query("*", title=opasConfig.TITLE_YEAR, description=opasConfig.DESCRIPTION_YEAR),
                                 limit: int=Query(15, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                                 offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
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
#@app.get("/v1/Metadata/Contents/{SourceCode}/{SourceVolume}/", response_model=models.DocumentList, response_model_exclude_unset=True, tags=["Deprecated"], summary=opasConfig.ENDPOINT_SUMMARY_CONTENTS_SOURCE_VOLUME)
@app.get("/v2/Metadata/Contents/{SourceCode}/{SourceVolume}/", response_model=models.DocumentList, response_model_exclude_unset=True, tags=["Metadata"], summary=opasConfig.ENDPOINT_SUMMARY_CONTENTS_SOURCE_VOLUME)
def metadata_contents(SourceCode: str, 
                      SourceVolume: str, 
                      response: Response,
                      request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                      year: str=Query("*", title=opasConfig.TITLE_YEAR, description=opasConfig.DESCRIPTION_YEAR),
                      limit: int=Query(15, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                      offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
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
@app.get("/v1/Metadata/Videos/", response_model=models.VideoInfoList, response_model_exclude_unset=True, tags=["PEPEasy1 (Deprecated)"], summary=opasConfig.ENDPOINT_SUMMARY_VIDEOS)
@app.get("/v2/Metadata/Videos/", response_model=models.VideoInfoList, response_model_exclude_unset=True, tags=["Metadata"], summary=opasConfig.ENDPOINT_SUMMARY_VIDEOS)
def metadata_videos(response: Response,
                    request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),
                    sourcecode: str=Query("*", title=opasConfig.TITLE_SOURCECODE, description=opasConfig.DESCRIPTION_SOURCECODE), 
                    limit: int=Query(200, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                    offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
                    ):
    """
    ## Function
    <b>Get a complete list of video names</b>

    sourcecode is the short abbreviation used as part of the DocumentIDs. e.g., for PEP in 2019, this includes:
      IPSAVS, PEPVS, PEPTOPAUTHVS, BPSIVS, IJPVS, PCVS, SFCPVS, UCLVS, PEPGRANTVS, AFCVS, NYPSIVS, SPIVS

    ## Return Type
       models.VideoInfoList

    ## Status
       This endpoint is working.

    ## Sample Call
         /v1/Metadata/Videos/

    ## Notes

    ## Potential Errors

    """
    ret_val = metadata_by_sourcetype_sourcecode(response, request, SourceType="Video", SourceCode=sourcecode, limit=limit, offset=offset)
    return ret_val

#-----------------------------------------------------------------------------
@app.get("/v1/Metadata/Journals/", response_model=models.JournalInfoList, response_model_exclude_unset=True, tags=["PEPEasy1 (Deprecated)"], summary=opasConfig.ENDPOINT_SUMMARY_JOURNALS)
def metadata_journals_v1(response: Response,
                         request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                         journal: str=Query("*", title=opasConfig.TITLE_SOURCECODE, description=opasConfig.DESCRIPTION_SOURCECODE), 
                         limit: int=Query(200, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                         offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
                         ):
    """
    ## Function
    <b>Get a complete list of journal names</b>

    ## Return Type
       models.JournalInfoList

    ## Status
       This endpoint is working.

    ## Sample Call
       /v1/Metadata/Journals/

    ## Notes

    ## Potential Errors

    """
    ret_val = metadata_by_sourcetype_sourcecode(response, request, SourceType="Journal", SourceCode=journal, limit=limit, offset=offset)
    return ret_val

#-----------------------------------------------------------------------------
@app.get("/v2/Metadata/Journals/", response_model=models.JournalInfoList, response_model_exclude_unset=True, tags=["Metadata"], summary=opasConfig.ENDPOINT_SUMMARY_JOURNALS)
def metadata_journals(response: Response,
                                request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                                #this param changed to sourcecode in v2 from journal in v1 (sourcecode is more accurately descriptive since this includes book series and video series)
                                sourcecode: str=Query("*", title=opasConfig.TITLE_SOURCECODE, description=opasConfig.DESCRIPTION_SOURCECODE), 
                                limit: int=Query(200, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                                offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
                                ):
    """
    ## Function
    <b>Get a complete list of journal names</b>

    ## Return Type
       models.JournalInfoList

    ## Status
       This endpoint is working.

    ## Sample Call
       /v2/Metadata/Journals/

    ## Notes

    ## Potential Errors

    """
    ret_val = metadata_by_sourcetype_sourcecode(response, request, SourceType="Journal", SourceCode=sourcecode, limit=limit, offset=offset)
    return ret_val

#-----------------------------------------------------------------------------
@app.get("/v1/Metadata/Volumes/{SourceCode}", response_model=models.VolumeList, response_model_exclude_unset=True, tags=["PEPEasy1 (Deprecated)"], summary=opasConfig.ENDPOINT_SUMMARY_VOLUMES)
def metadata_volumes_sourcecode(response: Response,
                                        request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                                        limit: int=Query(200, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                                        sourcetype: str=Query(None, title=opasConfig.TITLE_SOURCETYPE, description=opasConfig.DESCRIPTION_PARAM_SOURCETYPE),
                                        offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET),
                                        # v1 arg
                                        SourceCode: str=Path(..., title=opasConfig.TITLE_SOURCECODE, description=opasConfig.DESCRIPTION_SOURCECODE), 
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
    ret_val = metadata_volumes(response=response, request=request, sourcetype=sourcetype, sourcecode=SourceCode, limit=limit, offset=offset)
    return ret_val # returns volumeList
    
@app.get("/v2/Metadata/Volumes/", response_model=models.VolumeList, response_model_exclude_unset=True, tags=["Metadata"], summary=opasConfig.ENDPOINT_SUMMARY_VOLUMES)
def metadata_volumes(response: Response,
                     request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                     sourcetype: str=Query(None, title=opasConfig.TITLE_SOURCETYPE, description=opasConfig.DESCRIPTION_PARAM_SOURCETYPE),
                     sourcecode: str=Query(None, title=opasConfig.TITLE_SOURCECODE, description=opasConfig.DESCRIPTION_SOURCECODE), 
                     limit: int=Query(200, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                     offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET),
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
    # Solr is case sensitive, make sure arg is upper
    try:
        source_code = sourcecode.upper()
    except:
        source_code = None

    src_exists = ocd.get_sources(source_code=source_code)
    if not src_exists[0] and source_code != "*" and source_code != "ZBK" and source_code is not None: # ZBK not in productbase table without booknum
        response.status_code = HTTP_400_BAD_REQUEST
        status_message = f"Failure: Bad SourceCode {source_code}"
        ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_METADATA_VOLUME_INDEX,
                                    session_info=session_info, 
                                    params=request.url._url,
                                    item_of_interest=f"{source_code}", 
                                    return_status_code=response.status_code,
                                    status_message=status_message
                                    )
        raise HTTPException(
            status_code=response.status_code,
            detail=status_message
        )
    else:
        try:
            ret_val = opasAPISupportLib.metadata_get_volumes(source_code, source_type=sourcetype, limit=limit, offset=offset)
        except Exception as e:
            response.status_code = HTTP_400_BAD_REQUEST,
            status_message = "Error: {}".format(e)
            ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_METADATA_VOLUME_INDEX,
                                        session_info=session_info, 
                                        params=request.url._url,
                                        item_of_interest=f"{source_code}", 
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
                                        item_of_interest=f"{source_code}", 
                                        return_status_code=response.status_code,
                                        status_message=status_message
                                        )

    return ret_val # returns volumeList

#-----------------------------------------------------------------------------
@app.get("/v1/Metadata/Books/", response_model=models.SourceInfoList, response_model_exclude_unset=True, tags=["PEPEasy1 (Deprecated)"], summary=opasConfig.ENDPOINT_SUMMARY_BOOK_NAMES)
@app.get("/v2/Metadata/Books/", response_model=models.SourceInfoList, response_model_exclude_unset=True, tags=["Metadata"], summary=opasConfig.ENDPOINT_SUMMARY_BOOK_NAMES)
def metadata_books(response: Response,
                             request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                             SourceCode: str=Query("*", title=opasConfig.TITLE_SOURCECODE, description=opasConfig.DESCRIPTION_SOURCECODE), 
                             limit: int=Query(200, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                             offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
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

    ret_val = metadata_by_sourcetype_sourcecode(response, request, SourceType="Book", SourceCode=SourceCode, limit=limit, offset=offset)
    return ret_val

#-----------------------------------------------------------------------------
#@app.get("/v1/Metadata/{SourceType}/{SourceCode}/", response_model=models.SourceInfoList, response_model_exclude_unset=True, tags=["Deprecated"], summary=opasConfig.ENDPOINT_SUMMARY_SOURCE_NAMES)
@app.get("/v2/Metadata/{SourceType}/{SourceCode}/", response_model=models.SourceInfoList, response_model_exclude_unset=True, tags=["Metadata"], summary=opasConfig.ENDPOINT_SUMMARY_SOURCE_NAMES)
def metadata_by_sourcetype_sourcecode(response: Response,
                               request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                               SourceType: str=Path(..., title=opasConfig.TITLE_SOURCETYPE, description=opasConfig.DESCRIPTION_PATH_SOURCETYPE), 
                               SourceCode: str=Path(..., title=opasConfig.TITLE_SOURCECODE, description=opasConfig.DESCRIPTION_SOURCECODE), 
                               limit: int=Query(200, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                               offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
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
       Depends on:
          vw_api_productbase for videos

    ## Potential Errors


    """

    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    source_code = SourceCode.upper()
    try:    
        if source_code == "*" or SourceType != "Journal":
            ret_val = source_info_list = opasAPISupportLib.metadata_get_source_by_type(src_type=SourceType, src_code=source_code, limit=limit, offset=offset)
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
@app.get("/v1/Authors/Index/{authorNamePartial}/", response_model=models.AuthorIndex, response_model_exclude_unset=True, tags=["PEPEasy1 (Deprecated)"], summary=opasConfig.ENDPOINT_SUMMARY_AUTHOR_INDEX)
@app.get("/v2/Authors/Index/{authorNamePartial}/", response_model=models.AuthorIndex, response_model_exclude_unset=True, tags=["Authors"], summary=opasConfig.ENDPOINT_SUMMARY_AUTHOR_INDEX)
def authors_index(response: Response,
                  request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                  authorNamePartial: str=Path(..., title=opasConfig.TITLE_AUTHORNAMEORPARTIAL, description=opasConfig.DESCRIPTION_AUTHORNAMEORPARTIAL), 
                  limit: int=Query(15, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                  offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
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
        status_message = f"The server is not running or is currently not accepting connections: {e}"
        logger.error(status_message)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=status_message
        )

    except Exception as e:
        status_message = f"Error: {e}"
        logger.error(status_message)
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
#@app.get("/v1/Authors/Publications/{authorNamePartial}/", response_model=models.AuthorPubList, response_model_exclude_unset=True, tags=["Deprecated"], summary=opasConfig.ENDPOINT_SUMMARY_AUTHOR_PUBLICATIONS)
@app.get("/v2/Authors/Publications/{authorNamePartial}/", response_model=models.AuthorPubList, response_model_exclude_unset=True, tags=["Authors"], summary=opasConfig.ENDPOINT_SUMMARY_AUTHOR_PUBLICATIONS)
def authors_publications(response: Response,
                         request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                         authorNamePartial: str=Path(..., title=opasConfig.TITLE_AUTHORNAMEORPARTIAL, description=opasConfig.DESCRIPTION_AUTHORNAMEORPARTIAL), 
                         limit: int=Query(15, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                         offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
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

#-----------------------------------------------------------------------------
#@app.get("/v1/Documents/Abstracts/{documentID}/", response_model=models.Documents, response_model_exclude_unset=True, tags=["Deprecated"], summary=opasConfig.ENDPOINT_SUMMARY_ABSTRACT_VIEW)
@app.get("/v2/Documents/Abstracts/{documentID}/", response_model=models.Documents, response_model_exclude_unset=True, tags=["Documents"], summary=opasConfig.ENDPOINT_SUMMARY_ABSTRACT_VIEW)
def documents_abstracts(response: Response,
                        request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                        documentID: str=Path(..., title=opasConfig.TITLE_DOCUMENT_ID, description=opasConfig.DESCRIPTION_DOCIDORPARTIAL), 
                        return_format: str=Query("HTML", title=opasConfig.TITLE_RETURNFORMATS, description=opasConfig.DESCRIPTION_RETURNFORMATS),
                        limit: int=Query(5, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                        offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
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
        PEP Easy 1.03Beta expects HTML abstract return (it doesn't specify a format)

    ## Potential Errors

    """

    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    try:
        authenticated = opasAPISupportLib.is_session_authenticated(request, response)
        ret_val = documents = opasAPISupportLib.documents_get_abstracts(documentID,
                                                                        ret_format=return_format,
                                                                        authenticated=authenticated, 
                                                                        limit=limit,
                                                                        offset=offset)
    except Exception as e:
        response.status_code=HTTP_400_BAD_REQUEST
        status_message = f"Error: {e}"
        logger.error(status_message)
        ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_DOCUMENTS_ABSTRACTS,
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
    else:
        status_message = "Success"
        #client_host = request.client.host
        # title = ret_val.documents.responseSet[0].title  # blank!
        ret_val.documents.responseInfo.request = request.url._url
        if ret_val.documents.responseInfo.count > 0:
            response.status_code = HTTP_200_OK
            #  record document view if found
            ocd.record_document_view(document_id=documentID,
                                     session_info=session_info,
                                     view_type="Abstract")
        else:
            # make sure we specify an error in the session log
            #  not sure this is the best return code, but for now...
            response.status_code = HTTP_404_NOT_FOUND

        ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_DOCUMENTS_ABSTRACTS,
                                    session_info=session_info, 
                                    params=request.url._url,
                                    item_of_interest=f"{documentID}", 
                                    return_status_code = response.status_code,
                                    status_message=status_message
                                    )
    return ret_val
#-----------------------------------------------------------------------------
@app.get("/v2/Database/Glossary/Search/", response_model=models.DocumentList, response_model_exclude_unset=True, tags=["Database"], summary=opasConfig.ENDPOINT_SUMMARY_GLOSSARY_SEARCH)
async def database_glossary_search(response: Response, 
                                   request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                                   termlist: models.SolrQueryTermList=None, # allows full specification
                                   fulltext1: str=Query(None, title=opasConfig.TITLE_FULLTEXT1, description=opasConfig.DESCRIPTION_FULLTEXT1),
                                   sourcelangcode: str=Query("EN", title=opasConfig.TITLE_SOURCELANGCODE, description=opasConfig.DESCRIPTION_SOURCELANGCODE), 
                                   paratext: str=Query(None, title=opasConfig.TITLE_PARATEXT, description=opasConfig.DESCRIPTION_PARATEXT),
                                   parascope: str=Query("doc", title=opasConfig.TITLE_PARASCOPE, description=opasConfig.DESCRIPTION_PARASCOPE),
                                   synonyms: bool=Query(False, title=opasConfig.TITLE_SYNONYMS, description=opasConfig.DESCRIPTION_SYNONYMS),
                                   sort: str=Query("score desc", title=opasConfig.TITLE_SORT, description=opasConfig.DESCRIPTION_SORT),
                                   limit: int=Query(15, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                                   offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
                                   ):
    """
    ## Function
       <b>Search the glossary records in the doc core (not the glossary core -- it doesn't support sub paras important for full-text search).</b>
       
       This is just a convenience function to search a specific book, the glossary (ZBK.069), in the doc core (pepwebdoc).

    ## Return Type
       models.Documents

    ## Status
       This endpoint is working.

    ## Sample Call
         /v2/Documents/Glossary/Search/

    ## Notes

    ## Potential Errors
       USER NEEDS TO BE AUTHENTICATED for glossary access at the term level.  Otherwise, returns error.

       Client apps should disable the glossary links when not authenticated.
    """
    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    # session_id = session_info.session_id

    ret_val = await database_search_v2(response,
                                        request,
                                        termlist=termlist,
                                        fulltext1=fulltext1, 
                                        paratext=paratext, #  no advanced search. Only words, phrases, prox ~ op, and booleans allowed
                                        parascope=parascope,
                                        synonyms=synonyms,
                                        sourcename=None, 
                                        sourcecode="ZBK",
                                        volume="69",
                                        sourcetype=None, 
                                        sourcelangcode=sourcelangcode,
                                        articletype=None, 
                                        issue=None, 
                                        author=None, 
                                        title="glossary",
                                        startyear=None,
                                        endyear=None,
                                        citecount=None,
                                        viewcount=None,
                                        viewedwithin=None, 
                                        sort=sort,
                                        limit=limit,
                                        offset=offset
                                       )
    if ret_val != {}:
        matches = len(ret_val.documentList.responseSet)
    else:
        matches = 0

    statusMsg = f"{matches} hits"
    logger.debug(statusMsg)

    ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_DATABASE_SEARCH,
                                session_info=session_info, 
                                params=request.url._url,
                                status_message=statusMsg
                                )

    return ret_val


#-----------------------------------------------------------------------------
@app.get("/v2/Documents/Glossary/{term_id}/", response_model=models.Documents, tags=["Documents"], summary=opasConfig.ENDPOINT_SUMMARY_GLOSSARY_VIEW, response_model_exclude_unset=True)  # the current PEP API
def documents_glossary_term(response: Response,
                            request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                            term_id: str=Path(..., title="Glossary Term ID or Partial ID", description=opasConfig.DESCRIPTION_GLOSSARYID),
                            #search: str=Query(None, title="Document request from search results", description="This is a document request, including search parameters, to show hits"),
                            return_format: str=Query("HTML", title=opasConfig.TITLE_RETURNFORMATS, description=opasConfig.DESCRIPTION_RETURNFORMATS)
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

    ## Notes
         In V1 (and PEP-Easy 1.0), glossary entries are fetched via the /v1/Documents endpoint rather than here.

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
        #if search is not None:
            #arg_dict = dict(parse.parse_qsl(parse.urlsplit(search).query))
            #if term_id is not None:
                ## make sure this is part of the last search set.
                #j = arg_dict.get("journal")
                #if j is not None:
                    #if j not in term_id:
                        #arg_dict["journal"] = None
        #else:
            #arg_dict = {}
        
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

#-----------------------------------------------------------------------------
@app.get("/v1/Documents/{documentID}/", response_model=models.Documents, tags=["PEPEasy1 (Deprecated)"], summary=opasConfig.ENDPOINT_SUMMARY_DOCUMENT_VIEW, response_model_exclude_unset=True)  # the current PEP API
@app.get("/v2/Documents/Document/{documentID}/", response_model=models.Documents, tags=["Documents"], summary=opasConfig.ENDPOINT_SUMMARY_DOCUMENT_VIEW, response_model_exclude_unset=True) # more consistent with the model grouping
def documents_document_fetch(response: Response,
                            request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                            documentID: str=Path(..., title=opasConfig.TITLE_DOCUMENT_ID, description=opasConfig.DESCRIPTION_DOCIDORPARTIAL),
                            # return controls
                            page: int=Query(None, title=opasConfig.TITLE_PAGEREQUEST, description=opasConfig.DESCRIPTION_PAGEREQUEST),
                            return_format: str=Query("HTML", title=opasConfig.TITLE_RETURNFORMATS, description=opasConfig.DESCRIPTION_RETURNFORMATS),
                            search: str=Query(None, title=opasConfig.TITLE_SEARCHPARAM, description=opasConfig.DESCRIPTION_SEARCHPARAM), 
                            limit: int=Query(None, title=opasConfig.TITLE_PAGELIMIT, description=opasConfig.DESCRIPTION_PAGELIMIT),
                            offset: int=Query(None, title=opasConfig.TITLE_PAGEOFFSET, description=opasConfig.DESCRIPTION_PAGEOFFSET)
                            ):
    """
    ## Function
       <b>Returns the Document information and summary and full-text - but conditionally.</b>
       Returns the Document information the document itself (authenticated) for the requested documentID (e.g., IJP.077.0001A)
          Returns only the summary (abstract) if non-authenticated unless the document has field
          file_classification in the Solr database set to the same as the value of opasConfig.DOCUMENT_ACCESS_FREE.

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
        #ret_val = view_a_glossary_entry(response, request, term_id=term_id, search=search, return_format=return_format)
        ret_val = documents_glossary_term(response, request, term_id=term_id, return_format=return_format)
    else:
        m = re.match("(?P<docid>[A-Z]{2,12}\.[0-9]{3,3}[A-F]?\.(?P<pagestart>[0-9]{4,4})[A-Z]?)(\.P(?P<pagenbr>[0-9]{4,4}))?", documentID)
        if m is not None:
            documentID = m.group("docid")
            page_number = m.group("pagenbr")
            if page_number is not None:
                try:
                    page_start_int = int(m.group("pagestart"))
                    page_number_int = int(page_number)
                    offset = page_number_int - page_start_int
                except Exception as e:
                    logging.error(f"Page offset calc issue.  {e}")
                    offset = 0
                    
        doc_info = opasAPISupportLib.document_get_info(documentID, fields="art_id, art_sourcetype, art_year, file_classification, art_sourcecode")
        file_classification = doc_info.get("file_classification", opasConfig.DOCUMENT_ACCESS_UNDEFINED)
        try:
            # is the user authenticated? if so, loggedIn is true
            if session_info.authenticated or file_classification == opasConfig.DOCUMENT_ACCESS_FREE:
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

                #if not file_classification == opasConfig.DOCUMENT_ACCESS_FREE:
                    ## see if the user has access to this document
                    #basecode = opasAPISupportLib.get_basecode(documentID)
                    #year = 
                    #ocd.authenticate_user_product_request(session_info.user_id, basecode, year)

                solr_query_params = opasQueryHelper.parse_search_query_parameters(**argdict)
                logger.debug("Document View Request: %s/%s/%s", solr_query_params, documentID, return_format)

                ret_val = opasAPISupportLib.documents_get_document( documentID, 
                                                                    solr_query_params,
                                                                    ret_format=return_format, 
                                                                    authenticated = session_info.authenticated,
                                                                    file_classification=file_classification, 
                                                                    page_offset=offset, # starting page
                                                                    page_limit=limit, # number of pages
                                                                    page=page # specific page number request (rather than offset)
                                                                    )
            else:
                logger.debug("user is not authenticated.  Returning abstract only)")

                ret_val = opasAPISupportLib.documents_get_abstracts( documentID,
                                                                     ret_format=return_format,
                                                                     authenticated=session_info.authenticated,
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
            if ret_val != {}:
                response.status_code = HTTP_200_OK
                status_message = "Success"
            else:
                # make sure we specify an error in the session log
                # not sure this is the best return code, but for now...
                status_message = "Not Found"
                response.status_code = HTTP_404_NOT_FOUND
                # record session endpoint in any case   

            ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_DOCUMENTS,
                                        session_info=session_info, 
                                        params=request.url._url,
                                        item_of_interest="{}".format(documentID), 
                                        return_status_code = response.status_code,
                                        status_message=status_message
                                        )

            if ret_val == {}:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=status_message
                )           
            else:
                ret_val.documents.responseInfo.request = request.url._url
                if ret_val.documents.responseInfo.count > 0:
                    #  record document view if found
                    ocd.record_document_view(document_id=documentID,
                                             session_info=session_info,
                                             view_type="Document")

    return ret_val

#-----------------------------------------------------------------------------
@app.get("/v1/Documents/Downloads/Images/{imageID}/", response_model_exclude_unset=True, tags=["PEPEasy1 (Deprecated)"], summary=opasConfig.ENDPOINT_SUMMARY_IMAGE_DOWNLOAD)
@app.get("/v2/Documents/Image/{imageID}/", response_model_exclude_unset=True, tags=["Documents"], summary=opasConfig.ENDPOINT_SUMMARY_IMAGE_DOWNLOAD)
async def documents_image_fetch(response: Response,
                               request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                               imageID: str=Path(..., title=opasConfig.TITLE_IMAGEID, description=opasConfig.DESCRIPTION_DOCIDORPARTIAL),
                               download: int=Query(0, title="Return or download", description="0 to return the image to the browser, 1 to download")
                               ):
    """
    ## Function
       <b>Returns a binary image per the GVPi server</b>
       if download == 1 then the file is returned as a downloadable file to the client/browser.
       Otherwise, it's returned as binary data, and displays in the browser.  This is in fact
          how it works to display images in articles.

    ## Return Type
       Binary data

    ## Status
       This endpoint is working.


    ## Sample Call
         http://localhost:9100/v1/Documents/Images/AIM.036.0275A.FIG001/
         http://development.org:9100/v1/Documents/Downloads/Images/AIM.036.0275A.FIG001

    ## Notes

    ## Potential Errors
       USER NEEDS TO BE AUTHENTICATED to request a download.  Otherwise, returns error.
    """
    ret_val = None
    if imageID is not None:
        imageID = imageID.replace("+", " ")
        
    endpoint = opasCentralDBLib.API_DOCUMENTS_IMAGE
    ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    # allow viewing, but not downloading if not logged in
    if not session_info.authenticated and download != 0:
        response.status_code = HTTP_400_BAD_REQUEST 
        status_message = "Must be logged in and authorized to download an image."
        # no need to record endpoint failure
        #ocd.record_session_endpoint(api_endpoint_id=endpoint,
                                    #session_info=session_info, 
                                    #params=request.url._url,
                                    #item_of_interest=f"{imageID}", 
                                    #return_status_code = response.status_code,
                                    #status_message=status_message
                                    #)
        raise HTTPException(
            status_code=response.status_code,
            detail=status_message
        )    

    filename = opas_fs.get_image_filename(filespec=imageID, path=localsecrets.IMAGE_SOURCE_PATH)    
    media_type='image/jpeg'
    if download == 0:
        if filename is None:
            response.status_code = HTTP_400_BAD_REQUEST 
            status_message = "Error: no filename specified"
            logger.error(status_message)
            # no need to record endpoint failure
            #ocd.record_session_endpoint(api_endpoint_id=endpoint,
                                        #session_info=session_info, 
                                        #params=request.url._url,
                                        #item_of_interest=f"{imageID}", 
                                        #return_status_code = response.status_code,
                                        #status_message=status_message
                                        #)
            raise HTTPException(status_code=response.status_code,
                                detail=status_message)
        else:
            file_content = opas_fs.get_image_binary(filename)
            try:
                ret_val = response = Response(file_content, media_type=media_type)

            except Exception as e:
                response.status_code = HTTP_400_BAD_REQUEST 
                status_message = f" The requested document {filename} could not be returned {e}"
                raise HTTPException(status_code=response.status_code,
                                    detail=status_message)

            else:
                status_message = "Success"
                logger.info(status_message)
                ocd.record_document_view(document_id=imageID,
                                         session_info=session_info,
                                         view_type=media_type)
                # no need to record image return (happens many times per article)
                #ocd.record_session_endpoint(api_endpoint_id=endpoint,
                #session_info=session_info, 
                                            #params=request.url._url,
                                            #item_of_interest=f"{imageID}", 
                                            #return_status_code = response.status_code,
                                            #status_message=status_message
                                            #)
    else: # download == 1
        try:
            response.status_code = HTTP_200_OK
            filename = opas_fs.get_image_filename(filename)
            if opas_fs.key is not None:
                fileurl = opas_fs.fs.url(filename)
                fname = wget.download(fileurl)
                ret_val = FileResponse(path=fname,
                                       status_code=response.status_code,
                                       filename=os.path.split(fname)[1], 
                                       media_type=media_type)
            else:
                fileurl = filename
                ret_val = FileResponse(path=fileurl,
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
            ocd.record_document_view(document_id=imageID,
                                     session_info=session_info,
                                     view_type="file_format")
            ocd.record_session_endpoint(api_endpoint_id=endpoint,
                                        session_info=session_info, 
                                        params=request.url._url,
                                        item_of_interest=f"{imageID}", 
                                        return_status_code = response.status_code,
                                        status_message=status_message
                                        )

    return ret_val

#-----------------------------------------------------------------------------
@app.get("/v1/Documents/Downloads/{retFormat}/{documentID}/", response_model_exclude_unset=True, tags=["PEPEasy1 (Deprecated)"], summary=opasConfig.ENDPOINT_SUMMARY_DOCUMENT_DOWNLOAD)
@app.get("/v2/Documents/Downloads/{retFormat}/{documentID}/", response_model_exclude_unset=True, tags=["Documents"], summary=opasConfig.ENDPOINT_SUMMARY_DOCUMENT_DOWNLOAD)
def documents_downloads(response: Response,
                        request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),  
                        documentID: str=Path(..., title=opasConfig.TITLE_DOCUMENT_ID, description=opasConfig.DESCRIPTION_DOCIDORPARTIAL), 
                        retFormat=Path(..., title=opasConfig.TITLE_RETURNFORMATS, description=opasConfig.DESCRIPTION_DOCDOWNLOADFORMAT),
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
        # no need to record endpoint failure
        #ocd.record_session_endpoint(api_endpoint_id=opasCentralDBLib.API_DOCUMENTS_DOWNLOADS,
                                    #session_info=session_info, 
                                    #params=request.url._url,
                                    #item_of_interest=f"{documentID}", 
                                    #return_status_code = response.status_code,
                                    #status_message=status_message
                                    #)
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
    if filename is None:
        response.status_code = HTTP_400_BAD_REQUEST 
        status_message = "Error: no filename specified"
        logger.error(status_message)
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
            ocd.record_document_view(document_id=documentID,
                                     session_info=session_info,
                                     view_type=file_format)
            ocd.record_session_endpoint(api_endpoint_id=endpoint,
                                        session_info=session_info, 
                                        params=request.url._url,
                                        item_of_interest=f"{documentID}", 
                                        return_status_code = response.status_code,
                                        status_message=status_message
                                        )

    return ret_val

@app.get("/v2/Database/WordWheel/", response_model=models.TermIndex, response_model_exclude_unset=True, tags=["Database"], summary=opasConfig.ENDPOINT_SUMMARY_WORD_WHEEL)
def database_word_wheel(response: Response,
                        request: Request=Query(None, title=opasConfig.TITLE_REQUEST, description=opasConfig.DESCRIPTION_REQUEST),
                        word: str=Query(None, title=opasConfig.TITLE_WORD, description=opasConfig.DESCRIPTION_WORD),
                        field: str=Query("text", title=opasConfig.TITLE_WORDFIELD, description=opasConfig.DESCRIPTION_WORDFIELD),
                        limit: int=Query(15, title=opasConfig.TITLE_LIMIT, description=opasConfig.DESCRIPTION_LIMIT),
                        offset: int=Query(0, title=opasConfig.TITLE_OFFSET, description=opasConfig.DESCRIPTION_OFFSET)
                        ):
    """
    ## Function
       <b>Return a list (index) of words for the field matching the prefix.  </b>

    ## Return Type
       models.termIndex

    ## Status
       This endpoint is working.

    ## Sample Call
       http://localhost:9100/v2/WordWheel?phleb

    ## Notes

    ## Potential Errors

    """
    ret_val = None 

    # ocd, session_info = opasAPISupportLib.get_session_info(request, response)
    try:
        # returns models.TermIndex
        term_to_check = word.lower()  # work with lower case only, since Solr is case sensitive.
        ret_val = opasAPISupportLib.get_term_index(term_to_check, term_field=field, limit=limit, offset=offset)
    except ConnectionRefusedError as e:
        status_message = f"The server is not running or is currently not accepting connections: {e}"
        logger.error(status_message)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=status_message
        )

    except Exception as e:
        status_message = f"Error: {e}"
        logger.error(status_message)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=status_message
        )
    else:
        status_message = "Success"
        response.status_code = HTTP_200_OK
        # fill in additional return structure status info
        ret_val.termIndex.responseInfo.request = request.url._url

    # for maximum speed since this is used for word_wheels, don't log the endpoint occurrences
    #ocd.recordSessionEndpoint(apiEndpointID=opasCentralDBLib.API_AUTHORS_INDEX,
                                        #params=request.url._url,
                                        #returnStatusCode = resp.status_code = ,
                                        #statusMessage=statusMessage
                                        #)

    return ret_val  # Return author information or error


if __name__ == "__main__":
    print(f"Server Running ({localsecrets.BASEURL}:{localsecrets.API_PORT_MAIN})")
    print (f"Running in Python {sys.version_info[0]}.{sys.version_info[1]}")
    uvicorn.run(app, host="development.org", port=localsecrets.API_PORT_MAIN, debug=True)
        # uvicorn.run(app, host=localsecrets.BASEURL, port=9100, debug=True)
    print ("Now we're exiting...")