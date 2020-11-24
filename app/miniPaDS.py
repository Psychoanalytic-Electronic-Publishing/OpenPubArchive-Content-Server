#!/usr/bin/env python
# -*- coding: utf-8 -*-

#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2020, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2020.1106.0.Stub"
__status__      = "Development"

import sys
sys.path.append('./config')
sys.path.append('./libs')
sys.path.append('./libs/solrpy')

import os.path
import time
import datetime
from datetime import datetime
# import re
from urllib import parse

# import secrets
import localsecrets
from localsecrets import PADS_TEST_ID, PADS_TEST_PW, PADS_BASED_CLIENT_IDS
import models
from pydantic import ValidationError

from config.opasConfig import OPASSESSIONID, OPASACCESSTOKEN, OPASEXPIRES
import config.opasConfig as opasConfig
import logging

# import json


import uvicorn
from fastapi import FastAPI, Query, Body, Path, Header, Security, Depends, HTTPException, File, Form #, UploadFile, Cookie
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, FileResponse, StreamingResponse # RedirectResponse
from starlette.middleware.cors import CORSMiddleware
import starlette.status as httpCodes
#from starlette.middleware.sessions import SessionMiddleware
#from typing import Optional
import pandas as pd

import requests
from requests.auth import HTTPBasicAuth
# import aiofiles
# from typing import List

TIME_FORMAT_STR = '%Y-%m-%dT%H:%M:%SZ'

logger = logging.getLogger(__name__)

base = "https://padstest.zedra.net/PEPSecure/api"

app = FastAPI(
    debug=True,
    title="miniPaDS for PEP-Web Development",
    description = "Mini authorization server for PEP-Web by Psychoanalytic Electronic Publishing (PEP)",
        version = f"{__version__}",
        static_directory=r"./docs",
        swagger_static={
            "favicon": "pepfavicon"
            },
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex = localsecrets.CORS_REGEX, 
    allow_origins = localsecrets.CORS_ORIGINS, 
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

msg = 'Started at %s' % datetime.today().strftime('%Y-%m-%d %H:%M:%S"')

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

@app.get("/v1/Authenticate/IP")
async def get_ip_authenticate(request: Request,
                              response: Response,
                              session_id=None
                              ):
    """IP Login and SessionId

    If IP is known then will useer will be logged on, if not a known IP address then return of just SessionId # noqa: E501

    :param session_id: Optional SessionId.  If supplied will be linked to a previously allocated PaDS SessionId.  If not supplied will be allocated by PaDS.
    :type session_id: str

    :rtype: List[AuthenticateResponse]
    """

    retVal = pads_session_info = models.PadsSessionInfo()
    return retVal 

@app.get("/v1/Authenticate")
def get_authenticate(request: Request,
                     response: Response, 
                     body=None,
                     session_id=None):  # noqa: E501
    """Log in

    Login request  # noqa: E501

    :param body: 
    :type body: dict | bytes
    :param session_id: Optional SessionId.  If supplied will be linked to a previously allocated PaDS SessionId.  If not supplied will be allocated by PaDS.
    :type session_id: str

    :rtype: List[AuthenticateResponse]
    """
    retVal = pads_session_info = models.PadsSessionInfo()
    return retVal 

@app.get("/v1/Permits/")
def get_permit(request: Request,
               response: Response, 
               session_id,
               doc_id=None,
               doc_year=None):  # noqa: E501
    """Ask full-text read permission for a document

    The document server asks the pep permits system for access permission for a specific session (identified by session_id) for a specific document (identified by doc_id) and also provides additional identifying information including document_year  # noqa: E501

    :param session_id: ID of a particular users session
    :type session_id: str
    :param doc_id: Standard PEP document_id (sometimes referred to as article_id) which usually consists of a publication code, volume number, and starting page, e.g., \&quot;IJP.082.0215A\&quot;
    :type doc_id: str
    :param doc_year: The year of the document to help identify it beyond the document_id (which has the publication volume only)
    :type doc_year: str

    :rtype: List[PermitResponse]
    """
    ret_val = models.PadsPermitInfo(SessionId = session_id,
                                    DocID = doc_id,
                                    HasArchiveAccess=True, 
                                    HasCurrentAccess=False,
                                    Permit=True, 
                                    ReasonId=0, 
                                    StatusCode=200,
                                    ReasonStr="miniPads"
    )

    return ret_val

@app.get("/v1/Users")
def get_users(request: Request,
              response: Response, 
              session_id):  # noqa: E501
    """Returns user details

    If passed a known session ID for s logged on user will return the users details # noqa: E501

    :param session_id: If sessionId is unknown then request will be rejected
    :type session_id: str

    :rtype: List[UserResponse]
    """
    ret_val = models.PadsUserInfo(UserId="",  
                                  UserName="",  
                                  UserType="", 
                                  SubscriptionEndDate="",  
                                  Branding=False, 
                                  ClientSettings=None, 
                                  ReasonId= 0, 
                                  ReasonStr="", 
                                  HasArchiveAccess=True, 
                                  HasCurrentAccess=False 
                                  )

    
    return ret_val

if __name__ == "__main__":
    import sys
    API_PORT_MAIN = 9200
    BASEURL = "development.org"
    print(f"Server Running ({localsecrets.BASEURL}:{API_PORT_MAIN})")
    print (f"Running in Python {sys.version_info[0]}.{sys.version_info[1]}")
    uvicorn.run(app, host=BASEURL, port=API_PORT_MAIN, debug=True, log_level="warning")
    print ("Now we're exiting...")