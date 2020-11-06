#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
opasPaDSAuthSimulator

"""
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2020, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2020.0406.1"
__status__      = "Development"

from starlette.status import HTTP_200_OK, \
                             HTTP_400_BAD_REQUEST, \
                             HTTP_401_UNAUTHORIZED, \
                             HTTP_403_FORBIDDEN, \
                             HTTP_404_NOT_FOUND, \
                             HTTP_500_INTERNAL_SERVER_ERROR, \
                             HTTP_503_SERVICE_UNAVAILABLE

from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse, Response, RedirectResponse, FileResponse
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Schema
from pydantic import ValidationError
import secrets
import localsecrets
from localsecrets import PADS_TEST_ID, PADS_TEST_PW, PADS_BASED_CLIENT_IDS
import models

from fastapi import Security, FastAPI, Query, Path, Cookie, Header, Depends, HTTPException
from fastapi.openapi.utils import get_openapi

from fastapi.security import HTTPBasic, HTTPBasicCredentials

import opasCentralDBLib
# import opasAPISupportLib as opasAPISupportLib
security = HTTPBasic()

app = FastAPI(
    debug=True,
    title="OpasPaDSAuthenticateSimulator for PEP-Web Development",
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

COOKIE_MIN_KEEP_TIME = 3600  # 1 hour in seconds
COOKIE_MAX_KEEP_TIME = 86400 # 24 hours in seconds
SESSION_INACTIVE_LIMIT = 30  # minutes
OPASPADSSESSIONID = "opasPaDSSessionID"
USER_DB = { "peptest.april": {"pw":"April2020*", "permits": ["pep-web"]},
            "neil" : {"pw": "Scilab!!", "permits": ["pep-web"], "journals": [], "documents": []},
            "gvpi" : {"pw": "xyz", "permits": ["pep-web"], "journals": [], "documents": []},
            "TemporaryDeveloper": {"pw":"limited*", "permits": ["ijp-open"], "journals": ["IJP", "CPS"], "documents": ["PSP.015.0163A", ]}
          }

#-----------------------------------------------------------------------------
def get_max_age(keep_active=False):
    if keep_active:    
        ret_val = COOKIE_MAX_KEEP_TIME    
    else:
        ret_val = COOKIE_MIN_KEEP_TIME     
    return ret_val  # maxAge

@app.get("/openapi.json")
async def get_open_api_endpoint():
    return JSONResponse(get_openapi(title="FastAPI", version=1, routes=app.routes))

@app.get("/v1/Authenticate/IP", response_model_exclude_unset=True, tags=["Open App Endpoints"])
def get_ip_authenticate(request: Request,
                        response: Response, 
                        session_id=None): 
    """IP Login and SessionId

    If IP is known then will useer will be logged on, if not a known IP address then return of just SessionId # noqa: E501

    :param session_id: Optional SessionId.  If supplied will be linked to a previously allocated PaDS SessionId.  If not supplied will be allocated by PaDS.
    :type session_id: str

    :rtype: List[AuthenticateResponse]
    """
    ret_val = models.PadsSessionInfo(HasSubscription=True, 
                                     IsValidLogon=True, 
                                     IsValidUserName=True, 
                                     ReasonId=0, 
                                     ReasonStr = "", 
                                     SessionExpires=0,
                                     SessionId=session_id
                                     )
    
    return retVal 

@app.get("/v1/Authenticate/", response_model_exclude_unset=True, tags=["Open App Endpoints"])
def get_authenticate(response: Response,
                      request: Request,
                      body=None,
                      session_id=None,                      
                      credentials: HTTPBasicCredentials = Depends(security)):
    """


        Returns:
        
        class PadsSessionInfo(BaseModel):
                              HasSubscription: bool = Schema(False, title="")
                              IsValidLogon: bool = Schema(False, title="")
                              IsValidUserName: bool = Schema(False, title="")
                              ReasonId: int = Schema(0, title="")
                              ReasonStr = Schema("", title="")
                              SessionExpires: int = Schema(0, title="Session expires time")
                              SessionId: str = Schema(None, title="Assigned session ID")
                              # added to model, not normally supplied by PaDS
                              session_start_time: datetime = Schema(datetime.now(), title="The time the session was started, not part of the model returned")
                              pads_status_response: int = Schema(0, title="The status code returned by PaDS, not part of the model returned")
                              pads_disposition: str = Schema(None, title="The disposition of PaDS either from error return or deduction")
    """    
    sess_info = models.PadsSessionInfo(HasSubscription=True, 
                                       IsValidLogon=True, 
                                       IsValidUserName=True, 
                                       ReasonId=0, 
                                       ReasonStr = "", 
                                       SessionExpires=0,
                                       SessionId=session_id
                                       )
    
    retVal = sess_info

    if user is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"}, # opens form again
        )

    session_id = secrets.token_urlsafe(16)
    max_age = get_max_age(keep_active=False)
    # expiration_time = datetime.utcfromtimestamp(time.time() + get_max_age(keep_active=ka))
    response.set_cookie(key=OPASPADSSESSIONID,
                        value=session_id,
                        max_age=max_age,
                        expires=None, 
                        path="/",
                        secure=False, 
                        httponly=False)
    return user  # pydantic model based user.  See modelsOpasCentralPydantic.py

@app.get("/v1/Users", response_model_exclude_unset=True, tags=["Open App Endpoints"])
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


@app.get("/v1/Users/Logout", response_model_exclude_unset=True, tags=["Open App Endpoints"])
async def logout(response: Response,
                 request: Request,
                 ):

    response.delete_cookie(key=OPASPADSSESSIONID, path="/")
    return True

#-----------------------------------------------------------------------------
@app.get("/v1/Permits", response_model_exclude_unset=True, tags=["Open App Endpoints"])
def get_permit(response: Response,
               request: Request,  
               session_id: str=Query(None, title="Session ID", description="User's session ID"), 
               doc_id: str=Query(None, title="Document (article ID)", description="Document ID Requested"),
               doc_year: str=Query(None, title="Document Publication Year (Publication Year)", description="Year of document Requested")
               ):
    ret_val=False
    
    ocd = opasCentralDBLib.opasCentralDB()
    #  look up session id, must be logged in
    session_info = ocd.get_session_from_db(session_id)
    #  then check for permissions
    if session_info is not None:
        user_permissions = USER_DB.get(session_info.username)
        if user_permissions is not None:
            user_permit = user_permissions.get("permits", [])
            user_journals = user_permissions.get("journals", [])
            user_documents = user_permissions.get("documents", [])
        
            jrnlcode, vol, pg = doc_id.split(".")
            if "pep-web" in user_permit:
                detailed_reason = "Access to all of PEP-Web" 
                ret_val = True
            elif jrnlcode in user_journals:
                detailed_reason = "Access to this journal" 
                ret_val = True
            elif doc_id in user_documents:
                detailed_reason = "Access to this document" 
                ret_val = True
    else:
        ret_val = False
        detailed_reason = "No Permission for this item." 

    return {"session_id": session_id,
            "doc_id": doc_id,
            "permit": ret_val, 
            "reason": detailed_reason
            }


if __name__ == "__main__":
    import sys
    import uvicorn
    
    API_PORT_MAIN = 9300
    BASEURL = "development.org"
    print(f"Server Running ({localsecrets.BASEURL}:{API_PORT_MAIN})")
    print (f"Running in Python {sys.version_info[0]}.{sys.version_info[1]}")
    uvicorn.run(app, host=BASEURL, port=API_PORT_MAIN, debug=True, log_level="warning")
    print ("Now we're exiting...")  
