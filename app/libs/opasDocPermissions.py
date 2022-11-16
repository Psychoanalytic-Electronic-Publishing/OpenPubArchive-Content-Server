#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Uses PaDS for authorization.  
# 
# PaDS builds its product database by polling the metadata endpoints.
#  - For journals and books, this data comes from the api_products table. 
#     - column 'active' turns on or off the listing in the journal list of the client
#     - column 'accessClassificaiton' sets a journal as archive or future. (current is not at the journal level)
# 

import sys
sys.path.append("..") # Adds higher directory to python modules path.

import requests
import datetime
from datetime import datetime as dt # to avoid python's confusion with datetime.timedelta
import datetime as dtime 
import time
import opasConfig
import models
import logging
import localsecrets
# import urllib.parse
# import json
from fastapi import HTTPException
from errorMessages import *

logger = logging.getLogger(__name__)
# for this module
# logger.setLevel(logging.DEBUG)

if 0:
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    # create formatter
    formatter = logging.Formatter(opasConfig.FORMAT)
    # add formatter to ch
    ch.setFormatter(formatter)
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)

from starlette.responses import Response
from starlette.requests import Request
import starlette.status as httpCodes

# import localsecrets
from localsecrets import PADS_BASE_URL, PADS_TEST_ID, PADS_TEST_PW # , PADS_BASED_CLIENT_IDS
base = PADS_BASE_URL
# base = "http://development.org:9300"
import opasCentralDBLib
#from config import msgdb
import opasMessageLib
msgdb = opasMessageLib.messageDB()

ocd = opasCentralDBLib.opasCentralDB()

def user_logged_in_per_header(request, session_id=None, caller_name="unknown") -> bool:
    """
    Return logged in per header, or None if no info found, unless there's no request
    
    """
    if request == None:
        logger.warning(f"No request param supplied to check log-in. Returning False ({caller_name} / {session_id})")
        ret_val = False
    else:
        ret_val = request.headers.get(key=localsecrets.AUTH_KEY_NAME, default=None)
        # is logged in?
        if ret_val == "true":
            #logger.warning(f"Loggedin=True ({caller_name} / {session_id})") #TEMP diagnostic
            ret_val = True
        elif ret_val == "false":
            #logger.warning(f"Loggedin=False ({caller_name} / {session_id})") #TEMP diagnostic
            # make sure session is ended in database [Why..not logged in?]
            # success = ocd.end_session(session_id=session_id)
            ret_val = False
        else:
            ret_val = None # no info
            
    return ret_val    

def verify_header(request, caller_name):
    # Double Check for missing header test--ONLY checks headers, not other avenues used by find
    client_session_from_header = request.headers.get(opasConfig.CLIENTSESSIONID, None)
    client_id_from_header = request.headers.get(opasConfig.CLIENTID, None)
    if client_id_from_header == 2 or client_id_from_header == 3:
        if client_session_from_header == None:
            logger.warning(f"***{caller_name}*** - No client-session supplied. Client-id (from header): {client_id_from_header}.")
        else:
            logger.debug(f"***{caller_name}*** - Client-session found. Client-id (from header): {client_id_from_header}.")

    return client_id_from_header, client_session_from_header    

def find_client_session_id(request: Request,
                           response: Response=None,
                           client_session: str=None
                           ):
    """
    ALWAYS returns a session ID or None
    
    Dependency for client_session id:
           gets it from header;
           if not there, gets it from query param;
           if not there, gets it from a cookie
           Otherwise, gets a new one from the auth server
    """
    ret_val = None

    if client_session is None or client_session == 'None':
        client_session = request.headers.get(opasConfig.CLIENTSESSIONID, None)
    
    if client_session is not None:
        ret_val = client_session
        msg = f"client-session from header (find_client_session_id): {ret_val} "
        if opasConfig.LOCAL_TRACE: print (msg)
    else:
        #Won't work unless they expose cookie to client, so don't waste time 
        #pepweb_session_cookie = request.cookies.get("pepweb_session", None)
        opas_session_cookie = request.cookies.get(opasConfig.OPASSESSIONID, None)
        client_session_qparam = request.query_params.get(opasConfig.CLIENTSESSIONID, None)
        client_session_cookie = request.cookies.get(opasConfig.CLIENTSESSIONID, None)
        if client_session_qparam is not None:
            ret_val = client_session_qparam
            msg = f"client-session from param: {ret_val}. URL: {request.url}"
            logger.info(msg) 
        elif client_session_cookie is not None:
            ret_val = client_session_cookie
            msg = f"client-session from client-session cookie: {ret_val}. URL: {request.url}"
            logger.info(msg) 
        elif opas_session_cookie is not None and opas_session_cookie != 'None':
            msg = f"client-session from stored OPASSESSION cookie {opas_session_cookie}. URL: {request.url} "
            logger.info(msg) 
            ret_val = opas_session_cookie
        else:
            msg = f"No dependency client-session ID found. Returning None. URL: {request.url}"
            logger.info(msg) 
            ret_val = None

        if ret_val is not None and opas_session_cookie is not None and opas_session_cookie != ret_val and response is not None:
            #  overwrite any saved cookie, if there is one
            logger.debug(f"Saved OpasSessionID Cookie: {ret_val}") 
            response.set_cookie(
                opasConfig.OPASSESSIONID,
                value=f"{client_session}",
                domain=localsecrets.COOKIE_DOMAIN
            )

    return ret_val

def get_user_ip(request: Request):
    """
    Returns a users IP if passed in the headers.
    """
    ret_val = None
    if request is not None:
        ret_val = request.headers.get(opasConfig.X_FORWARDED_FOR, None)
        if ret_val is not None:
            try:
                req_url = request.url
                msg = f"X-Forwarded-For from header: {ret_val}. URL: {req_url}"
                logger.debug(msg)
            except Exception as e:
                logger.error(f"Error: {e}")               

    return ret_val
    
def fix_userinfo_invalid_nones(response_data, caller_name="DocPermissionsError"):
    try:
        if response_data["UserName"] is None:
            response_data["UserName"] = "NotLoggedIn"
    except Exception as e:
        logger.error(f"{caller_name}: PaDS UserName Data Exception: {e}")

    try:
        if response_data["UserType"] is None:
            response_data["UserType"] = "Unknown"
    except Exception as e:
        logger.error(f"{caller_name}: PaDS UserType Data Exception: {e}")

    return response_data

def fix_pydantic_invalid_nones(response_data, caller_name="DocPermissionsError"):
    try:
        if response_data["ReasonStr"] is None:
            response_data["ReasonStr"] = ""
    except Exception as e:
        logger.error(f"{caller_name}: Exception: {e}")

    return response_data

def validate_client_id(client_id, caller_name="DocPermissionsError"):
    if client_id is None:
        client_id = opasConfig.NO_CLIENT_ID
        logger.error(f"{caller_name}: Error: Client ID is None")
    else: 
        try:
            if not isinstance(client_id, int):
                if isinstance(client_id, str):
                    try:
                        client_id = int(client_id)
                    except:
                        logger.error(f"client_id is str ('{client_id}'), but not convertible to int.  Default to NO_CLIENT_ID.  Caller: {caller_name}")
                        client_id = opasConfig.NO_CLIENT_ID
                else:
                    logger.error(f"client_id is not int or str.  Type is {type(client_id)}. Default to NO_CLIENT_ID. Caller: {caller_name}")
                    client_id = opasConfig.NO_CLIENT_ID
        except Exception as e:
            logger.error(f"client_id instance check failed. {e}")       
            client_id = opasConfig.NO_CLIENT_ID

    return client_id            

def get_authserver_session_info(session_id,
                                client_id=opasConfig.NO_CLIENT_ID,
                                pads_session_info=None,
                                user_logged_in_header=None, 
                                request=None,
                                response=None):
    """
    Return a filled-in SessionInfo object from several PaDS calls
    Saves the session information to the SQL database (or updates it)
    
    >>> session_info = get_authserver_session_info(None, "4")
    >>> session_info.username == "NotLoggedIn"
    True
    
    >>> pads_session_info = pads_login()
    >>> session_id = pads_session_info.SessionId
    >>> session_info = get_authserver_session_info(session_id, "4", pads_session_info=pads_session_info)
    >>> session_info.authorized_peparchive == True
    True

    >>> session_info = get_authserver_session_info("7F481226-9AF1-47BC-8E26-F07DB8C3E78D", "4")
    >>> print (session_info)
    session_id='7F481226-9AF1-47BC-8E26-F07DB8C3E78D' user_id=0 username='NotLoggedIn' ...
    >>> session_info.username == "NotLoggedIn"
    True
    
    
    """
    ts = time.time()
    caller_name = "get_authserver_session_info"
    
    #make sure it's ok, this is causing problems on production
    #see if it's an int?
    client_id = validate_client_id(client_id, caller_name=caller_name)
    if session_id is None and request is not None:  # removed pads_session_info is None or
        session_id = find_client_session_id(request) # not supplied, so fetch

    ocd, session_info = get_session_info(request, response, session_id=session_id, client_id=client_id, pads_session_info=pads_session_info, caller_name=caller_name)
        
    return session_info

def get_base_session_info(request=None, session_id=None, client_id=4, pads_session_info=None, session_info=None):
    """
    If we have a session_id, look in DB for full info
    If we don't have a session_id but there's a request, see if it's there.
    If we still don't have a session_id, get one from PaDS
    
    Now, is the session_id one that is logged in?
    
    If logged in, let's check user info?
        - If we have a database entry for the session_id, get user info from there.
            If the user info is incomplete, get it from PaDS and update the database entry
       
        - If we don't have a database entry, get user info from PaDS
            Update complete info into database
    
    """
    if session_id is None:
        # try to find the session id!
        if pads_session_info is not None:
            session_id = pads_session_info.SessionId
        elif request is not None:
            session_id = find_client_session_id(request)
        
        # if not found, get one!
        if session_id is None: # get a new session id
            pads_session_info = get_pads_session_info(session_id=None,
                                                      client_id=client_id,
                                                      retry=False)
            
            session_id = pads_session_info.SessionId

    if session_info is None:
        #  try to handle pydantic validation errors we're seeing in the production logs - nrs 2022-04-15
        #  to turn off validation for the model, see https://pydantic-docs.helpmanual.io/usage/models/#creating-models-without-validation
        try:
            base_session_info = models.SessionInfo(session_id=session_id,
                                                   api_client_id=client_id
                                                   )
        except Exception as e: 
            logger.error(f"SessionInfo model creation error - {e}. Sessionid: {session_id} clientid: {client_id}")
            # default session info
            base_session_info = models.SessionInfo()
    else:
        base_session_info = session_info
        
    if pads_session_info is not None:
        base_session_info.is_valid_login = pads_session_info.IsValidLogon
        base_session_info.is_valid_username = pads_session_info.IsValidUserName
        base_session_info.authenticated = pads_session_info.IsValidUserName
        base_session_info.has_subscription = pads_session_info.HasSubscription

    return base_session_info

#-----------------------------------------------------------------------------
def get_session_info(request: Request,
                     response: Response,
                     session_id:str=None, 
                     client_id=None,
                     expires_time=None, 
                     force_new_session=False,
                     pads_session_info=None, 
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
    update_db = False
    ts = time.time()

    # check client id for legality
    client_id = validate_client_id(client_id, caller_name="get_session_info")

    if request is not None:
        request_url = request.url
    else:
        request_url = None

    session_info = get_base_session_info(request=request,
                                         session_id=session_id,
                                         client_id=client_id,
                                         pads_session_info=pads_session_info,
                                         session_info=None)
    
    session_id = session_info.session_id

    # is the user logged in? 
    if pads_session_info is not None:
        user_logged_in_bool = pads_session_info.IsValidLogon
        if opasConfig.PADS_INFO_TRACE: print(f"Is the user logged in? IsValidLogon: {pads_session_info.IsValidLogon}") # diagnostic trace
    elif request is not None:
        user_logged_in_bool = user_logged_in_per_header(request, session_id=session_id, caller_name=caller_name)
    else:
        user_logged_in_bool = False
           
    # should now have a session id
    if session_id is not None and session_id != opasConfig.NO_SESSION_ID:
        session_info_from_db = ocd.get_session_from_db(session_id)
        if session_info_from_db is None: # not in DB
            in_db = False
            update_db = True
            # logged in but not that way in the db
            if pads_session_info is None:
                # need to get PaDS session info
                pads_session_info = get_pads_session_info(session_id=session_id,
                                                          client_id=client_id,
                                                          retry=False)

            session_info.is_valid_login = session_info.is_valid_username = pads_session_info.IsValidLogon
            session_info.authenticated = pads_session_info.IsValidUserName
            session_info.has_subscription = pads_session_info.HasSubscription
            session_info.pads_session_info = pads_session_info
            # this may give a way to set logged in in db artificially, but as soon as they try to read a document, db will be updated to agree with PaDS
            logger.debug(f"{caller_name}: Session {session_id} in DB:{in_db}. Authenticated:{session_info.authenticated}. URL: {request_url} PaDS SessionInfo: {session_info.pads_session_info}") # 09/13 removed  Server Session Info: {session_info} for brevity
            
        else: # found in DB
            in_db = True
            if user_logged_in_bool is None:
                # no info on loging.  Use DB info
                if session_info_from_db.is_valid_login == False:
                    user_logged_in_bool = False
                else: # use DB value
                    user_logged_in_bool = session_info_from_db.is_valid_login

            if user_logged_in_bool == False and session_info_from_db.is_valid_login == False:
               #not logged in, db shows that already.
                update_db = False
                session_info = session_info_from_db
            else:
                if session_info_from_db.session_end is not None:
                    # the session has been logged out
                    db_session_ended = True
                else:
                    db_session_ended = False
                    
                if db_session_ended and user_logged_in_bool:
                    # this should not happen in real life.
                    logger.info(f"Warning: DB Session {session_id} marked ended, but active session with same id received.")
                    
                if user_logged_in_bool == True and (session_info_from_db.is_valid_login == False or session_info_from_db.username == opasConfig.USER_NOT_LOGGED_IN_NAME):
                    # logged in but not that way in the db
                    if pads_session_info is not None:
                        session_info = session_info_from_db
                        session_info.is_valid_login = session_info.is_valid_username = pads_session_info.IsValidLogon
                        session_info.authenticated = pads_session_info.IsValidUserName
                        session_info.has_subscription = pads_session_info.HasSubscription
                        session_info.pads_session_info = pads_session_info
                        logger.debug(f"{caller_name}: Session {session_id} in DB:{in_db}. Authenticated:{session_info.authenticated}. URL: {request_url} PaDS SessionInfo: {session_info.pads_session_info}") # 09/14 removed  Server Session Info: {session_info} for brevity
                        update_db = True
                    else:
                        session_info = session_info_from_db
                        session_info.is_valid_login = session_info.is_valid_username = True
                        session_info.authenticated = session_info.is_valid_login
                        # this may give a way to set logged in in db artificially, but as soon as they try to read a document, db will be updated to agree with PaDS
                        logger.debug(f"{caller_name}: Session {session_id} in DB:{in_db}. DB says not logged in, but they are.  Authenticated:{session_info.authenticated}. URL: {request_url}")
                        update_db = True
                elif not user_logged_in_bool and session_info_from_db.is_valid_login == True: # if login status has changed
                    # Not logged in but database says they are, so logout
                    result = authserver_logout(session_id)
                    session_info = session_info_from_db
                    session_info.is_valid_login = False
                    update_db = True
                else: # logged in, no changes
                    # important state is the same. So use db record (should we
                    # compare here?)
                    session_info = session_info_from_db
                    logger.debug(f"{caller_name}: Session {session_id} in DB:{in_db}. DB says logged in, no changes.  Authenticated:{session_info.authenticated}. URL: {request_url}")
                    update_db = False
        
                #if update_db: # get_user_info: # user_logged_in_bool or session_info.is_valid_login:
                    #status_code = 0 # no check, no error
                    #pads_user_info = None
                    #if user_logged_in_bool:
                        #logger.debug(f"{caller_name}: For Tracing.  Getting session userinfo from PaDS.  Request: {request}")
                        #pads_user_info, status_code = get_authserver_session_userinfo(session_id, client_id, addl_log_info=" (complete session_record)")
            
                    #if status_code == 401: # could be just no session_id, but also could have be returned by PaDS if it doesn't recognize it
                        ##if session_info.pads_session_info.pads_status_response > 500:
                            ##msg = f"{caller_name}: PaDS error or PaDS unavailable - user cannot be logged in and no session_id assigned"
                            ##logger.error(msg)
                        #if session_id is not None:
                            #logger.warning(f"{session_id} call to pads produces 401 error. Setting user_logged_in to False")
                            #user_logged_in_bool = False
                    #else:
                        #if pads_user_info is not None:
                            #session_info.pads_user_info = pads_user_info
                        #else:
                            #try:
                                #session_info.pads_user_info = session_info.pads_user_info
                            #except:
                                #session_info.pads_user_info = None
                            
                        #if pads_user_info is not None:
                            #session_info.user_id = userID=pads_user_info.UserId
                            #session_info.username = pads_user_info.UserName
                            #session_info.user_type = pads_user_info.UserType
                            #session_info.admin = pads_user_info.UserType==opasConfig.ADMIN_TYPE
                            #session_info.authorized_peparchive = pads_user_info.HasArchiveAccess
                            #session_info.authorized_pepcurrent = pads_user_info.HasCurrentAccess
                            #logger.debug(f"PaDS returned user info {session_info.user_id}.  Saving to DB")
   
    if update_db: # not user_logged_in_bool:
        status_code = 0 # no check, no error
        pads_user_info = None
        if user_logged_in_bool:
            logger.debug(f"{caller_name}: For Tracing.  Getting session userinfo from PaDS.  Request: {request}")
            pads_user_info, status_code = get_authserver_session_userinfo(session_id, client_id, addl_log_info=" (complete session_record)")

        if status_code == 401: # could be just no session_id, but also could have be returned by PaDS if it doesn't recognize it
            #if session_info.pads_session_info.pads_status_response > 500:
                #msg = f"{caller_name}: PaDS error or PaDS unavailable - user cannot be logged in and no session_id assigned"
                #logger.error(msg)
            if session_id is not None:
                logger.warning(f"{session_id} call to pads produces 401 error. Setting user_logged_in to False")
                user_logged_in_bool = False
        else:
            if pads_user_info is not None:
                session_info.pads_user_info = pads_user_info
            else:
                try:
                    session_info.pads_user_info = session_info.pads_user_info
                except:
                    session_info.pads_user_info = None
                
            if pads_user_info is not None:
                session_info.user_id = userID=pads_user_info.UserId
                session_info.username = pads_user_info.UserName
                session_info.user_type = pads_user_info.UserType
                session_info.admin = pads_user_info.UserType==opasConfig.ADMIN_TYPE
                session_info.authorized_peparchive = pads_user_info.HasArchiveAccess
                session_info.authorized_pepcurrent = pads_user_info.HasCurrentAccess
                logger.debug(f"PaDS returned user info {session_info.user_id}.  Saving to DB")
        
        if session_id is not None:
            # save session
            if not save_session_info_to_db(session_info):  # now session info will contain non-logged in users
                logger.debug(f"***authent: {session_info.authenticated} - Save session info failed.")
            else: 
                logger.debug(f"***authent: {session_info.authenticated} - Save session succeeded.")
        else:
            msg = f"SessionID:[{session_id}] was not resolved. Raising Exception 424."
            raise HTTPException(
                status_code=httpCodes.HTTP_424_FAILED_DEPENDENCY,
                detail=ERR_MSG_PASSWORD + f" {msg}"
                )
    else:
        if session_id is not None:
            logger.debug(f"***session_id : {session_id} - get_full_session_info total time: {time.time() - ts} (no session_info update)***")
        else:
            msg = f"SessionID:[{session_id}] was not resolved. Raising Exception 424."
            raise HTTPException(
                status_code=httpCodes.HTTP_424_FAILED_DEPENDENCY,
                detail=ERR_MSG_PASSWORD + f" {msg}"
                )

    return ocd, session_info

    
def get_authserver_session_userinfo(session_id, client_id, addl_log_info=""):
    """
    Send PaDS the session ID and see if that's associated with a user yet.
    """
    ret_val = None
    caller_name = "get_authserver_session_userinfo"
    
    status_code = httpCodes.HTTP_401_UNAUTHORIZED # 401
    msg = f"for session {session_id} from client {client_id}"
    #logger.debug(msg)
    if session_id is not None:
        full_URL = base + f"/v1/Users" + f"?SessionID={session_id}"
        try:
            response = requests.get(full_URL, headers={"Content-Type":"application/json"}) # Call PaDS
            ocd.log_pads_calls(caller=caller_name, reason=caller_name + addl_log_info, session_id=session_id, pads_call=full_URL, return_status_code=response.status_code) # Log Call PaDS
            
        except Exception as e:
            logger.error(f"{caller_name}: Error from auth server user info call: {e}. Non-logged in user {msg}")
        else:
            status_code = response.status_code
            padsinfo = response.json()
            if response.ok:
                padsinfo = fix_userinfo_invalid_nones(padsinfo)
                ret_val = models.PadsUserInfo(**padsinfo)
            else:
                logger.debug(f"Non-logged in user {msg}. Info from PaDS: {padsinfo}") # 2021.08.08 back to debug...seems consistent.
        
    return ret_val, status_code # padsinfo, status_code
    
def save_session_info_to_db(session_info):
    # make sure the session is recorded.
    ret_val = False # default return
    session_id = session_info.session_id
    ocd = opasCentralDBLib.opasCentralDB()
    db_session_info = ocd.get_session_from_db(session_id)
    if db_session_info is None:
        ret_val, saved_session_info = ocd.save_session(session_id, session_info)
        logger.debug(f"Saving session info {session_id}")
    else:
        logger.debug(f"Session {session_id} already found in db.")
        if session_info.username != db_session_info.username and db_session_info.username != opasConfig.USER_NOT_LOGGED_IN_NAME:
            msg = f"AuthServerSessionInfoError: MISMATCH! Two Usernames with same session_id. OLD(DB): {db_session_info}; NEW(SESSION): {session_info}"
            logger.error(msg)
        if session_info.username != opasConfig.USER_NOT_LOGGED_IN_NAME:
            logger.debug(f"Updating session info {session_id}")
            ret_val = ocd.update_session(session_id,
                                         userID=session_info.user_id,
                                         username=session_info.username,
                                         usertype=session_info.user_type, 
                                         authenticated=1 if session_info.authenticated == True else 0,
                                         hassubscription=1 if session_info.has_subscription == True else 0,
                                         validusername=1 if session_info.is_valid_username == True else 0,
                                         authorized_peparchive=1 if session_info.authorized_peparchive == True else 0,
                                         authorized_pepcurrent=1 if session_info.authorized_pepcurrent == True else 0,
                                         session_end=session_info.session_expires_time,
                                         api_client_id=session_info.api_client_id
                                         )
    
    return ret_val

def authserver_login(username=PADS_TEST_ID,
                     password=PADS_TEST_PW,
                     session_id=None,
                     client_id=opasConfig.NO_CLIENT_ID,
                     retry=True):
    """
    Login directly via the auth server (e.g., in this case PaDS)
    
    If session_id is included, the idea is that the logged in entity will keep that constant.
      -- #TODO but that's not implemented in this server itself, if logged in through there, yet!
      
    """
    msg = ""
    caller_name = "authserver_login"
    
    logger.info(f"Logging in user {username} with session_id {session_id}")
    if session_id is not None:
        full_URL = base + f"/v1/Authenticate/?SessionId={session_id}"
    else:
        full_URL = base + f"/v1/Authenticate/"

    try:
        pads_response = requests.post(full_URL, headers={"Content-Type":"application/json"}, json={"UserName":f"{username}", "Password":f"{password}"})
        ocd.log_pads_calls(caller=caller_name, reason=caller_name, session_id=session_id, pads_call=full_URL, return_status_code=pads_response.status_code, params=username) # Log Call PaDS
        
    except Exception as e:
        msg = f"{caller_name}: Authorization server not available. {e}"
        logger.error(msg)
        # set up response with default model
        pads_session_info = models.PadsSessionInfo()
        if session_id is not None:
            pads_session_info.SessionId = session_id 
        #session_info = models.SessionInfo()
    else:
        status_code = pads_response.status_code # save it for a bit (we replace pads_session_info below)
        if pads_response.ok:
            pads_response = pads_response.json()
            pads_response = fix_pydantic_invalid_nones(pads_response, caller_name="AuthserverLogin")
            if isinstance(pads_response, str):
                pads_session_info = models.PadsSessionInfo()
                logger.error(f"{caller_name}: returned error string: {pads_response}")
            else:
                try:
                    pads_session_info = models.PadsSessionInfo(**pads_response)
                except Exception as e:
                    logger.error(f"{caller_name}: return assignment error: {e}")
                    pads_session_info = models.PadsSessionInfo()
        elif status_code > 403: 
            if retry == True:
                # try once without the session ID
                msg = f"{caller_name}: Login returned {status_code}. Trying without session id."
                logger.error(msg)
                pads_session_info = authserver_login(username=username, password=password, client_id=client_id, retry=False)
            else:
                msg = f"{caller_name}: Auth System Issue. Login returned {status_code}. Retry (failed), or Retry not selected."
                logger.error(msg)
                pads_session_info = models.PadsSessionInfo()
                pads_session_info.pads_status_response = status_code
                pads_session_info.pads_disposition = msg 
        else:
            try:
                pads_response = pads_response.json()
                pads_response = fix_pydantic_invalid_nones(pads_response)
                if isinstance(pads_response, str):
                    pads_session_info = models.PadsSessionInfo()
                    msg = f"{caller_name}: Returned error string: {pads_response}"
                    logger.error(msg)
                else:
                    try:
                        pads_session_info = models.PadsSessionInfo(**pads_response)
                    except Exception as e:
                        msg = f"{caller_name}: Return assignment error: {e}"
                        logger.error(msg)
                        pads_session_info = models.PadsSessionInfo()
            except Exception as e:
                logger.error(f"{caller_name}: Response processing error {e}")
                pads_session_info = models.PadsSessionInfo(**pads_session_info)
                pads_session_info.pads_status_response = status_code
                pads_session_info.pads_disposition = msg 
                
    return pads_session_info

def authserver_logout(session_id, request: Request=None, response: Response=None):
    ret_val = False
    caller_name = "authserver_logout"
    
    if session_id is not None:
        if response is not None:
            response.delete_cookie(key=opasConfig.OPASSESSIONID,path="/",
                                   domain=localsecrets.COOKIE_DOMAIN)
        # call PaDS
        full_URL = base + f"/v1/Users/Logout/?SessionId={session_id}"
        response = requests.post(full_URL, headers={"Content-Type":"application/json"})
        ocd.log_pads_calls(caller=caller_name, reason=caller_name, session_id=session_id, pads_call=full_URL, return_status_code=response.status_code) # Log Call PaDS
        if response.ok:
            ret_val = True
        else:
            logger.error(f"{caller_name}: Error Logging out for sessionId: {session_id} from PaDS: {response.json()}")
    else:
        logger.error(f"{caller_name}: No SessionId supplied.")

    return ret_val

def authserver_permission_check(session_id,
                                doc_id,
                                doc_year,
                                reason_for_check=None,
                                request=None):
    ret_val = False
    caller_name = "authserver_permission_check"
    
    ret_resp = None
    if reason_for_check is None:
        logger.warning(f"{caller_name}: fulltext_request info not supplied")
        
    full_URL = base + f"/v1/Permits?SessionId={session_id}&DocId={doc_id}&DocYear={doc_year}&ReasonForCheck={reason_for_check}"

    user_ip = get_user_ip(request)
    if user_ip is not None:
        headers = { opasConfig.X_FORWARDED_FOR:user_ip }
    else:
        headers = None

    try: # permit request to PaDS
        response = requests.get(full_URL, headers=headers) # Call PaDS
        ocd.log_pads_calls(caller=caller_name, reason=reason_for_check, session_id=session_id, pads_call=full_URL, return_status_code=response.status_code, params=doc_id) # Log Call PaDS
        
    except Exception as e:
        logger.error(f"{caller_name}: Request session {session_id} exception part 1: {full_URL}")
        logger.error(f"{caller_name}: Request session {session_id} exception part 2: {response}")
        logger.error(f"{caller_name}: Request session {session_id} exception part 3: {e}")
        logger.error(f"{caller_name}: Request session {session_id} exception part 4: headers {headers}")
        # just return no access
        ret_resp = models.PadsPermitInfo(SessionId = session_id,
                                         DocID = doc_id,
                                         HasArchiveAccess=True, 
                                         HasCurrentAccess=False,
                                         Permit=True, 
                                         ReasonId=0, 
                                         StatusCode=200,
                                         ReasonStr=f"PaDS error {e}"
        )
    else:
        try:
                
            if response.status_code == 503:
                # PaDS down, fake it for now
                msg = f"{caller_name}: Permits response error {e}. Temporarily return data."
                logger.error(msg)
                ret_resp = models.PadsPermitInfo(SessionId = session_id,
                                                 DocID = doc_id,
                                                 HasArchiveAccess=True, 
                                                 HasCurrentAccess=False,
                                                 Permit=True, 
                                                 ReasonId=0, 
                                                 StatusCode=200,
                                                 ReasonStr="PaDS not responding"
                )
            elif response.status_code == 401:
                msg = response.json()
                ret_val = False
                ret_resp = models.PadsPermitInfo(SessionId = session_id,
                                                 DocID = doc_id,
                                                 HasArchiveAccess=False, 
                                                 HasCurrentAccess=False,
                                                 Permit=False, 
                                                 ReasonId=0, 
                                                 StatusCode=401,
                                                 ReasonStr=msg
                )
            else:
                ret_resp = response.json()
                if type(ret_resp) == str:
                    msg = f"(PaDS responded: {ret_resp})"
                    ret_resp = models.PadsPermitInfo(SessionId=session_id,
                                                     DocId=doc_id,
                                                     ReasonStr=msg)
                else:
                    ret_resp = models.PadsPermitInfo(**ret_resp)
                    # returns 401 for a non-authenticated session
                    ret_resp.StatusCode = response.status_code
                    ret_val = ret_resp.Permit
                    if ret_resp.StatusCode != 200:
                        msg = f"PaDS returned a non-200 permit req status: {ret_resp.StatusCode}"
                        logger.info(msg)
                    
        except Exception as e:
            # added detail from json response for log but not response 2022-01-18 (seeing some of these in the production log)
            msg = f"{caller_name}: PaDS response error {e}. Assumed access rejected."
            msg2 = msg + f" - return response {response.json()}."
            logger.error(msg2)
            
            ret_val = False
            ret_resp = models.PadsPermitInfo(SessionId=session_id,
                                             DocId=doc_id,
                                             ReasonStr=msg)

    return ret_val, ret_resp      
        
def get_access_limitations(doc_id,
                           classification,   # document classification, e.g., free, current, archive, undefined, offsite, toc
                           session_info,     # updated in code below
                           year=None,
                           doi=None,
                           documentListItem: models.DocumentListItem=None,  # deprecated, not used
                           fulltext_request:bool=None,
                           request=None):
    """
    Based on the classification of the document (archive, current [embargoed],
       free, offsite), and the users permissions in session_info, determine whether
       this user has access to the full-text of the document, and fill out permissions
       in accessLimitations (ret_val) structure for document doc_id
       
    20210428 - removed documentListItem and update side effects, caller should copy access
               There are still side effects on session_info
       
    """
    caller_name = "get_access_limitations"
    
    try:
        open_access = False
        bypass_pads_check = False # need to check
        ret_val = models.AccessLimitations()
        ret_val.doi = doi
        ret_val.accessType = classification
        ret_val.accessLimitedPubLink = None
        ret_val.accessLimitedCode = 200 # default (for now)
        ret_val.accessLimitedReason = ""

        # USE THESE DEFAULTS, only set below if different
        # default, turned on if classification below is opasConfig.DOCUMENT_ACCESS_EMBARGOED
        ret_val.accessLimited = True # no access by default, may be changed below.
        ret_val.accessChecked = False # Same as default, for better clarity here
        ret_val.accessLimitedClassifiedAsCurrentContent = False

        # check embargo information from document if available
        if documentListItem is not None:
            embargoed = documentListItem.embargo
            embargo_type = documentListItem.embargotype
        else: # documentListItem can be None
            embargoed = False
            embargo_type = None
        
        if session_info is None:
            # logger.warning(f"Document permissions for {doc_id} -- no session info")
            ret_val.accessLimitedCode = 401 # no session
            session_id = "No Session Info"
            # not logged in
            # use all the defaults above, log error below.
        else:
            # for debugging display at return
            try:
                session_id = session_info.session_id
            except:
                session_id = "No Session ID"

            if ret_val.doi is not None:
                # publisher_access_via_doi = True
                publisher_access = msgdb.get_user_message(msg_code=opasConfig.ACCESS_SUMMARY_PUBLISHER_INFO) + opasConfig.ACCESS_SUMMARY_PUBLISHER_INFO_DOI_LINK % ret_val.doi
                # TODO: get the link we use to send users to publishers site when we don't have it, and no doi, and implement here.
                #       for now, just doi
                ret_val.accessLimitedPubLink = opasConfig.ACCESS_SUMMARY_PUBLISHER_INFO_DOI_LINK % ret_val.doi
            else:
                # publisher_access_via_doi = False
                #TODO Look up and see if there's a URL for the publisher, and then give them the general URL?
                publisher_access = "" # "."
            
            ret_val.accessLimitedClassifiedAsCurrentContent = False # default
            if classification in (opasConfig.DOCUMENT_ACCESS_FREE):
                # free can be for anyone!!!! Change accessLimited
                open_access = True
                ret_val.accessLimited = False
                ret_val.accessChecked = True
                #"This content is currently free to all users."
                ret_val.accessLimitedDescription = msgdb.get_user_message(msg_code=opasConfig.ACCESS_CLASS_DESCRIPTION_FREE)
                ret_val.accessLimitedReason = ret_val.accessLimitedDescription
                
            elif classification in (opasConfig.DOCUMENT_ACCESS_OFFSITE):
                # we only allow reading abstracts for offsite, accessLimited is True
                #"This content is currently completely limited to all users."
                ret_val.accessLimitedDescription = msgdb.get_user_message(msg_code=opasConfig.ACCESS_CLASS_DESCRIPTION_OFFSITE)
                ret_val.accessLimitedReason = ret_val.accessLimitedDescription # + " " + publisherAccess # limited...get it elsewhere
                # turning this off (false) in opasConfig means offsite docs will be checked with PaDS.
                if opasConfig.NO_OFFSITE_DOCUMENT_ACCESS_CHECKS:
                    bypass_pads_check = True
        
            elif classification in (opasConfig.DOCUMENT_ACCESS_CURRENT): # PEPCurrent
                ret_val.accessLimitedDescription = msgdb.get_user_message(msg_code=opasConfig.ACCESS_SUMMARY_DESCRIPTION) + msgdb.get_user_message(msg_code=opasConfig.ACCESS_CLASS_DESCRIPTION_CURRENT_CONTENT)
                ret_val.accessLimitedClassifiedAsCurrentContent = True
                ret_val.accessLimitedReason = msgdb.get_user_message(msg_code=opasConfig.ACCESS_LIMITED_REASON_NOK_CURRENT_CONTENT) + " " + publisher_access # limited...get it elsewhere
                if session_info is not None:
                    try:
                        # #########################################################################################
                        # optimization...if authorized for PEPCurrent, don't check again this query, unless it's a full-text request
                        # #########################################################################################
                        if session_info.authorized_pepcurrent:
                            ret_val.accessLimited = False # you can access it!!!
                            ret_val.accessChecked = True
                            # "This current content is available for you to access"
                            ret_val.accessLimitedReason = msgdb.get_user_message(opasConfig.ACCESS_LIMITED_REASON_OK_CURRENT_CONTENT) 
                            logger.debug("Optimization - session info used to authorize PEPCurrent document")
                            
                    except Exception as e:
                        logger.error(f"{caller_name}: PEPCurrent document permission: {e}")

            elif classification in (opasConfig.DOCUMENT_ACCESS_FUTURE): # PEPFuture
                ret_val.accessLimitedDescription = msgdb.get_user_message(msg_code=opasConfig.ACCESS_CLASS_DESCRIPTION_FUTURE)
                ret_val.accessLimitedReason = msgdb.get_user_message(msg_code=opasConfig.ACCESS_LIMITED_REASON_NOK_FUTURE_CONTENT) + " " + publisher_access # limited...get it elsewhere
                # ret_val.accessLimitedClassifiedAsCurrentContent = False # (Default)
                if session_info is not None:
                    try:
                        # #########################################################################################
                        # not optimization for PEP_Future.  Case by case.
                        # #########################################################################################
                        ret_val.accessLimited = True 
                        ret_val.accessChecked = True
                    except Exception as e:
                        logger.error(f"{caller_name}: PEPCurrent document permission: {e}")

            elif classification in (opasConfig.DOCUMENT_ACCESS_SPECIAL): # PEPSpecial
                if documentListItem.PEPCode.upper() in opasConfig.SPECIAL_SUBSCRIPTION_CODES:
                    ret_val.accessLimitedDescription = msgdb.get_user_message(msg_code=opasConfig.ACCESS_SUMMARY_SPECIAL_SUBSCRIPTION)
                    ret_val.accessLimitedReason = ret_val.accessLimitedDescription + " " + publisher_access # limited...get it elsewhere
                else:
                    ret_val.accessLimitedDescription = msgdb.get_user_message(msg_code=opasConfig.ACCESS_SUMMARY_DESCRIPTION)
                    ret_val.accessLimitedReason = ret_val.accessLimitedDescription + " " + msgdb.get_user_message(msg_code=opasConfig.ACCESS_SUMMARY_SPECIAL) + " " + publisher_access # limited...get it elsewhere
                # ret_val.accessLimitedClassifiedAsCurrentContent = False # (Default)
                if session_info is not None:
                    try:
                        # #########################################################################################
                        # Case by case.
                        # #########################################################################################
                        ret_val.accessLimited = True 
                        ret_val.accessChecked = False
                    except Exception as e:
                        logger.error(f"{caller_name}: PEPCurrent document permission: {e}")

            elif classification in (opasConfig.DOCUMENT_ACCESS_ARCHIVE):
                ret_val.accessLimitedDescription = msgdb.get_user_message(msg_code=opasConfig.ACCESS_CLASS_DESCRIPTION_ARCHIVE)
                # if they end up without access, default reason.
                ret_val.accessLimitedReason = msgdb.get_user_message(msg_code=opasConfig.ACCESS_LIMITED_REASON_NOK_ARCHIVE_CONTENT) #  Maybe we should redirect in this case? + " " + publisher_access # limited...get it elsewhere
                # ret_val.accessLimitedClassifiedAsCurrentContent = False # (Default)
                # ret_val.accessLimited = True # default is true
                # #########################################################################################
                # optimization...if authorized, don't check again, unless it's a full-text request
                # #########################################################################################
                if session_info is not None:
                    try:
                        if session_info.authorized_peparchive:
                            ret_val.accessLimited = False # you can access it!!!
                            ret_val.accessChecked = True
                            # "This content is available for you to access"
                            ret_val.accessLimitedReason = msgdb.get_user_message(msg_code=opasConfig.ACCESS_CLASS_DESCRIPTION_ARCHIVE)
                            logger.debug("Optimization - session info used to authorize PEPArchive document")
                    except Exception as e:
                        logger.error(f"{caller_name}: PEPArchive document permission: {e}")

            elif classification in (opasConfig.DOCUMENT_ACCESS_TOC):
                open_access = True
                ret_val.accessLimited = False # you can access it!!! (All TOCs are open)
                ret_val.accessChecked = True
                # just like free for now
                ret_val.accessLimitedDescription = msgdb.get_user_message(msg_code=opasConfig.ACCESS_CLASS_DESCRIPTION_TOC)
                ret_val.accessLimitedReason = ret_val.accessLimitedDescription
            else:
                msg = f"Unknown classification: {classification}"
                logger.error(f"{caller_name}: {msg}")
                ret_val.accessLimitedReason = msg

            # **************************************
            # Now check for access, or cached access
            #   - always check for a full-text request so PaDS can track them.
            #     since we don't really always know about authentication, we need to check all requests that are otherwise rejected.
            # **************************************
            
            try:                   
                if not open_access and not bypass_pads_check:
                    if (ret_val.accessLimited == True      # if it's marked limited, then may need to check, it might be first one
                             or fulltext_request == True): # or whenever full-text is requested.
                        # and session_info.api_client_session and session_info.api_client_id in PADS_BASED_CLIENT_IDS:
                        if fulltext_request:
                            reason_for_check = opasConfig.AUTH_DOCUMENT_VIEW_REQUEST
                        else:
                            reason_for_check = opasConfig.AUTH_ABSTRACT_VIEW_REQUEST

                        try:
                            if opasConfig.PADS_INFO_TRACE:
                                print(f"{dt.now().time().isoformat()}: [PaDS/PermissChk] {session_info.session_id}: {doc_id} authenticated: {session_info.authenticated}")

                            pads_authorized, resp = authserver_permission_check(session_id=session_info.session_id,
                                                                                doc_id=doc_id,
                                                                                doc_year=year,
                                                                                reason_for_check=reason_for_check,
                                                                                request=request)
                        except Exception as e:
                            # PaDS could be down, local development
                            msg = f"{caller_name}: Subsystem (e.g., PaDS) unavailable. Access Exception: {e}"
                            logger.error(msg)
                            if localsecrets.BASEURL == "development2.org:9100":
                                resp = models.PadsPermitInfo(Permit=True, HasArchiveAccess=True, HasCurrentAccess=True)
                                # so it doesn't have to check this later
                                session_info.authorized_peparchive = True
                                session_info.authorized_pepcurrent = True
                            else:
                                session_info.authorized_peparchive = False
                                session_info.authorized_pepcurrent = False
                                resp = models.PadsPermitInfo(Permit=False, HasArchiveAccess=False, HasCurrentAccess=False)
                                resp.ReasonStr = msg
        
                        finally:
                            # save PaDS code and full response to pass back
                            ret_val.accessLimitedAuthResponse = resp
                            ret_val.accessLimitedCode = resp.StatusCode
    
                            if resp.StatusCode == httpCodes.HTTP_401_UNAUTHORIZED: # or resp.ReasonStr == 'Session has not been authenticated':
                                # if this is True, then we can stop asking this time
                                # You would get the same return if 
                                #    the session was not recognised on pads, 
                                #    the session had been deleted from the database (should never happen…), or 
                                #    the session simply never existed.
                                ret_val.accessLimited = True
                                session_info.authenticated = False
                                msg = msgdb.get_user_message(msg_code=opasConfig.ACCESS_SUMMARY_ONLY_401_UNAUTHORIZED)
                                ret_val.accessLimitedReason = msg
                            elif embargoed == True:
                                ret_val.accessLimited = True
                                if embargo_type is not None:
                                    if embargo_type == 'IJPOPEN_REMOVED':
                                        msg = msgdb.get_user_message(msg_code=opasConfig.EMBARGO_IJPOPEN_REMOVED)
                                    elif embargo_type == 'IJPOPEN_FULLY_REMOVED':
                                        msg = msgdb.get_user_message(msg_code=opasConfig.EMBARGO_IJPOPEN_FULLY_REMOVED)
                                    elif embargo_type == 'RESTRICTED':
                                        msg = msgdb.get_user_message(msg_code=opasConfig.EMBARGO_PUBLISHER_EMBARGOED)
                                    else:
                                        msg = msgdb.get_user_message(msg_code=opasConfig.EMBARGO_TYPE_OTHER)
                                else:
                                    msg = msgdb.get_user_message(msg_code=opasConfig.ACCESS_LIMITED_REASON_NOK_EMBARGOED_CONTENT)
                                ret_val.accessLimitedReason = msg
                            else:
                                # set default again based on update from PaDS query
                                ret_val.accessLimited = True
    
                                if ret_val.accessLimitedClassifiedAsCurrentContent == True:
                                    if resp.HasCurrentAccess == True:
                                        session_info.authorized_pepcurrent = True
                                        ret_val.accessLimited = False
                                        ret_val.accessChecked = True
                                    else:
                                        ret_val.accessLimited = True
                                else: # not current content
                                    if resp.HasArchiveAccess == True:
                                        session_info.authorized_peparchive = True
                                        ret_val.accessLimited = False
                                        ret_val.accessChecked = True
    
                                if fulltext_request and pads_authorized:
                                    # let's make sure we know about this user.
                                    if session_info.user_id == opasConfig.USER_NOT_LOGGED_IN_NAME:
                                        # We got this far, We need to find out who this is
                                        pads_user_info, status_code = get_authserver_session_userinfo(session_info.session_id, session_info.api_client_id, addl_log_info=" (user info not yet collected)")
                                        ret_val.accessChecked = True
                                        if pads_user_info is not None:
                                            session_info.user_id = pads_user_info.UserId
                                            session_info.username = pads_user_info.UserName
                                            session_info.user_type = pads_user_info.UserType # TODO - Add this to session table
                                            # session_info.session_expires_time = ?
                                            # ocd = opasCentralDBLib.opasCentralDB()
                                            ocd.update_session(session_info.session_id,
                                                               userID=session_info.user_id,
                                                               username=session_info.username,
                                                               usertype=session_info.user_type,
                                                               authenticated=1,
                                                               authorized_peparchive=1 if session_info.authorized_peparchive == True else 0,
                                                               authorized_pepcurrent=1 if session_info.authorized_pepcurrent == True else 0,
                                                               session_end=session_info.session_expires_time,
                                                               api_client_id=session_info.api_client_id
                                                               )
                                                
                                            
                                if pads_authorized:
                                    # "This content is available for you to access"
                                    ret_val.accessLimited = False
                                    ret_val.accessChecked = True
                                    ret_val.accessLimitedDescription = msgdb.get_user_message(opasConfig.ACCESS_CLASS_DESCRIPTION_ARCHIVE)
                                    ret_val.accessLimitedReason = " (Authorized)"

                                    msg = f"Doc {doc_id} available. Pads: {resp.ReasonStr}. Server: {ret_val.accessLimitedDescription} - {ret_val.accessLimitedReason}"
                                    logger.debug(msg)
                                    if opasConfig.PADS_INFO_TRACE:
                                        print(f"{dt.now().time().isoformat()}: [PaDS] {session_info.session_id}: Doc {doc_id} available. Pads: {resp.ReasonStr}. Server: {ret_val.accessLimitedDescription} - {ret_val.accessLimitedReason}")
                                    ret_val.accessLimitedDebugMsg = msg
                                else:
                                    # changed from warning to info 2021-06-02 to reduce normal logging
                                    if opasConfig.PADS_INFO_TRACE:
                                        print(f"{dt.now().time().isoformat()}: [PaDS] {session_info.session_id}: Doc {doc_id} unavailable. Pads: {resp.ReasonStr}. Server: {ret_val.accessLimitedDescription} - {ret_val.accessLimitedReason}")

                                    msg = f"Doc {doc_id} unavailable. Pads: {resp.ReasonStr}. Server: {ret_val.accessLimitedDescription} - {ret_val.accessLimitedReason}"
                                    logger.info(msg) # limited...get it elsewhere
                                    ret_val.accessLimitedDebugMsg = msg
                                    ret_val.accessLimited = True
                                    if not ret_val.accessLimitedClassifiedAsCurrentContent:
                                        # not current content, but no access.
                                        if resp.ReasonStr is not None:
                                            ret_val.accessLimitedReason += " (" + resp.ReasonStr + ")"
                                    else:
                                        if ret_val.accessLimitedReason is None:
                                            ret_val.accessLimitedReason = "(" + resp.ReasonStr + ")"
                    else:
                        # not full-text OR not access_limited
                        if opasConfig.PADS_INFO_TRACE:
                            print(f"{dt.now().time().isoformat()}: [get_access_limitations] No PaDS check needed: Document {doc_id} accessLimited: {ret_val.accessLimited}. Authent: {session_info.authenticated}")

                        msg = f"No PaDS check needed: Document {doc_id} accessLimited: {ret_val.accessLimited}. Authent: {session_info.authenticated}"
                        ret_val.accessLimitedDebugMsg = msg

                else: # It's open access!
                    if opasConfig.PADS_INFO_TRACE:
                        print(f"{dt.now().time().isoformat()}: [get_access_limitations] No PaDS check needed: Document {doc_id} is open access")

                    msg = f"No PaDS check needed: Document {doc_id} is open access"
                    ret_val.accessLimitedDebugMsg = msg
        
            except Exception as e:
                msg = f"{caller_name}: Unexpected issue checking document permission. Possibly not logged in. {e}"
                logger.warning(msg)

                if opasConfig.PADS_INFO_TRACE:
                    print(f"{dt.now().time().isoformat()}: [get_access_limitations] {msg}")
                
                ret_val.accessLimitedDebugMsg = msg
                pass # can't be checked, will be unauthorized.

    except Exception as e:
        msg = f"{caller_name}: General exception {e} trying ascertain access limitations."
        logger.error(msg)
        if ret_val is None:
            ret_val = models.AccessLimitations() # make sure there's defaults!
        ret_val.accessLimitedDebugMsg = msg

    if fulltext_request and ret_val.accessLimited:
        # happens anytime someone views an abstract in Document mode because they don't have an account. Perfectly legal. Changed to info (from error)
        msg = f"Full-text access for {doc_id} denied ({ret_val.accessLimitedCode}). Sess:{session_id}. Reason: {ret_val.accessLimitedReason}"
        logger.info(msg)
        ret_val.accessLimitedDebugMsg = msg

    return ret_val

# ##################################################################################################################################################
#
#  LOCAL ROUTUNES
#
# ##################################################################################################################################################
def get_pads_session_info(session_id=None,
                          client_id=opasConfig.NO_CLIENT_ID,
                          retry=True,
                          request=None):
    """
    Get the PaDS session model, and get a new session ID from the auth server if needed 
    """
    msg = ""
    caller_name = "get_pads_session_info"
    msg = f"Checking PaDS authentication for Session ID: {session_id}"
    logger.debug(msg)
    if opasConfig.PADS_INFO_TRACE: print(msg)
    
    if client_id == opasConfig.NO_CLIENT_ID:
        logger.warning(f"{caller_name}: Session info call for Session ID: {session_id} Client ID was NO_CLIENT_ID ({opasConfig.NO_CLIENT_ID}).")
    
    if session_id is not None:
        full_URL = base + f"/v1/Authenticate/IP/" + f"?SessionID={session_id}"
    else:
        full_URL = base + f"/v1/Authenticate/IP/"

    req_url = "No request info."
    if request is not None:
        try: # just in case this generates an error
            req_url = request.url # to log caller url
        except Exception as e:
            pass
    
    user_ip = get_user_ip(request) # returns an IP if X_FORWARDED_FOR address is in header
    try:
        logger.debug(f"{caller_name}: calling PaDS")
        if user_ip is not None and user_ip is not '':
            headers = { opasConfig.X_FORWARDED_FOR:user_ip }
            pads_session_info = requests.get(full_URL, headers) # Call PaDS
            status_code = pads_session_info.status_code # save it for a bit (we replace pads_session_info below); this is only in PaDS return of pads_session_info, not in the model.
            msg = f"{caller_name}: Session ID:{session_id}. X_FORWARDED_FOR from authenticateIP: {user_ip}. URL: {req_url} PaDS Session Info: {pads_session_info}"
            logger.debug(msg)
            if opasConfig.PADS_INFO_TRACE: print (f"PADS Monitor: {msg}")
        else:
            if session_id is not None:
                pads_session_info = requests.get(full_URL) # Call PaDS
                status_code = pads_session_info.status_code # save it for a bit (we replace pads_session_info below)
                if opasConfig.PADS_INFO_TRACE: print (f"PADS Monitor: {full_URL} / {pads_session_info}")
                
            else: # we need a session id, go ahead and ask Pads (separate for tracking)
                pads_session_info = requests.get(full_URL) # Call PaDS
                status_code = pads_session_info.status_code # save it for a bit (we replace pads_session_info below)
                if opasConfig.PADS_INFO_TRACE: print (f"PADS Monitor: {full_URL} / {pads_session_info}")
            
    except Exception as e:
        logger.error(f"{caller_name}: Authorization server not available. {e}")
        pads_session_info = models.PadsSessionInfo()
    else:
        #status_code = pads_session_info.status_code # save it for a bit (we replace pads_session_info below)
        ocd.log_pads_calls(caller=caller_name, reason=caller_name, session_id=session_id, pads_call=full_URL, ip_address=user_ip, return_status_code=status_code) # Log Call PaDS

        if status_code > 403: # e.g., (httpCodes.HTTP_500_INTERNAL_SERVER_ERROR, httpCodes.HTTP_503_SERVICE_UNAVAILABLE):
            error_text = f"{caller_name}: PaDS session_info status_code is {status_code}"
            logger.error(error_text)
            # try once without the session ID
            if retry == True:
                # recursive call
                pads_session_info = get_pads_session_info(client_id=client_id, retry=False, request=request)
                pads_session_info.pads_status_response = status_code
            else:
                logger.error(error_text)
                pads_session_info = models.PadsSessionInfo()
                pads_session_info.pads_status_response = status_code
                pads_session_info.pads_disposition = error_text
        else:
            try:
                pads_session_info = pads_session_info.json()
                pads_session_info = fix_pydantic_invalid_nones(pads_session_info, caller_name=caller_name)
                pads_session_info = models.PadsSessionInfo(**pads_session_info)
                pads_session_info.pads_status_response = status_code
                msg = f"PaDS Status Ok, Final IP Session Info: {pads_session_info} URL: {req_url}."
                logger.debug(msg)
                if opasConfig.PADS_INFO_TRACE: print (f"PADS Monitor: {msg}")
                
            except Exception as e:
                msg = f"{caller_name}: Response processing error {e}"
                logger.error(msg)
                pads_session_info = models.PadsSessionInfo(**pads_session_info)
                pads_session_info.pads_status_response = status_code
                pads_session_info.pads_disposition = msg 

    return pads_session_info

if __name__ == "__main__":
    import doctest
    import sys
    
    print (40*"*", "opasDocPermissionsTests", 40*"*")
    print (f"Running in Python {sys.version_info[0]}.{sys.version_info[1]}")
   
    logger = logging.getLogger(__name__)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(name)s %(lineno)d - %(levelname)s %(message)s')    
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    doctest.testmod(optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
    print ("Fini. Tests complete.")