#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import datetime
import time
import opasConfig
import models
import logging
import localsecrets
# import urllib.parse
# import json
import sys
# from opasAPISupportLib import save_opas_session_cookie
sys.path.append("..") # Adds higher directory to python modules path.
from config.opasConfig import OPASSESSIONID

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
from localsecrets import PADS_BASE_URL, PADS_TEST_ID, PADS_TEST_PW, PADS_BASED_CLIENT_IDS
base = PADS_BASE_URL
# base = "http://development.org:9300"
import opasCentralDBLib

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
                           response: Response,
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
        #msg = f"client-session from header: {ret_val} "
        #logger.debug(msg)
    else:
        #Won't work unless they expose cookie to client, so don't waste time 
        #pepweb_session_cookie = request.cookies.get("pepweb_session", None)
        opas_session_cookie = request.cookies.get(opasConfig.OPASSESSIONID, None)
        client_session_qparam = request.query_params.get(opasConfig.CLIENTSESSIONID, None)
        client_session_cookie = request.cookies.get(opasConfig.CLIENTSESSIONID, None)
        if client_session_qparam is not None:
            ret_val = client_session_qparam
            msg = f"client-session from param: {ret_val}. URL: {request.url}"
            logger.warning(msg) # temp, should be info
        elif client_session_cookie is not None:
            ret_val = client_session_cookie
            msg = f"client-session from client-session cookie: {ret_val}. URL: {request.url}"
            logger.warning(msg) # temp, should be info
        elif opas_session_cookie is not None and opas_session_cookie != 'None':
            msg = f"client-session from stored OPASSESSION cookie {opas_session_cookie}. URL: {request.url} "
            logger.warning(msg) # temp, should be info
            ret_val = opas_session_cookie
        else:
            msg = f"No dependency client-session ID found. Returning None. URL: {request.url}"
            logger.warning(msg) # temp, should be info
            ret_val = None

        if ret_val is not None and opas_session_cookie is not None and opas_session_cookie != ret_val:
            #  overwrite any saved cookie, if there is one
            logger.warning("Saved OpasSessionID Cookie") # temp, should be debug
            response.set_cookie(
                OPASSESSIONID,
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
                        logger.error(f"client_id is str, but not convertible to int.  Default to NO_CLIENT_ID.  Caller: {caller_name}")
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
                                request=None):
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
    caller_name = "GetAuthserverSessionInfo"
    
    #make sure it's ok, this is causing problems on production
    #see if it's an int?
    client_id = validate_client_id(client_id, caller_name=caller_name)
        
    if pads_session_info is None or session_id is None:
        # not supplied, so fetch
        try:
            pads_session_info = get_pads_session_info(session_id=session_id,
                                                      client_id=client_id,
                                                      retry=False, 
                                                      request=request)
            try:
                session_info = models.SessionInfo(session_id=pads_session_info.SessionId, api_client_id=client_id)
            except Exception as e:
                msg = f"{caller_name}: Error {e}.  SessID: {session_id} client_id: {client_id} req: {request}"
                if opasConfig.LOCAL_TRACE:
                    print (msg)
                logger.error(msg)
                session_info = models.SessionInfo(session_id="unknown", api_client_id=client_id)
            else:    
                session_id = session_info.session_id
        except Exception as e:
            logger.error(f"{caller_name}: Error getting pads_session_info {e}")
            client_id_type = type(client_id)
            if client_id_type == int:
                session_info = models.SessionInfo(session_id="unknown", api_client_id=client_id)
            else:
                session_info = models.SessionInfo(session_id="unknown", api_client_id=opasConfig.NO_CLIENT_ID)
                
    #else:
        #session_info = models.SessionInfo(session_id=session_id, api_client_id=client_id)
        
    # This section is causing errors--I believe it's because PaDS is calling the API without real user info
    if pads_session_info is not None:
        if pads_session_info.SessionId is not None:
            session_info = models.SessionInfo(session_id=pads_session_info.SessionId, api_client_id=client_id)
        else:
            session_info = models.SessionInfo(session_id=session_id, api_client_id=client_id)
            
        start_time = pads_session_info.session_start_time if pads_session_info.session_start_time is not None else datetime.datetime.now()
        try:
            session_info.has_subscription = pads_session_info.HasSubscription
        except Exception as e:
            logger.error(f"{caller_name}: HasSubscription not supplied by PaDS")
            session_info.has_subscription = False

        try:
            session_info.is_valid_login = pads_session_info.IsValidLogon
            session_info.authenticated = pads_session_info.IsValidLogon
        except Exception as e:
            logger.error(f"{caller_name}: IsValidLogon not supplied by PaDS")
            session_info.is_valid_login = False

        try:
            session_info.is_valid_username = pads_session_info.IsValidUserName
        except Exception as e:
            logger.error(f"{caller_name}: IsValidUsername not supplied by PaDS")
            session_info.is_valid_username = False
        
        # session_info.confirmed_unauthenticated = False
        session_info.session_start = start_time
        session_info.session_expires_time = start_time + datetime.timedelta(seconds=pads_session_info.SessionExpires)
        session_info.pads_session_info = pads_session_info
        
    # either continue an existing session, or start a new one
    pads_user_info, status_code = get_authserver_session_userinfo(session_id, client_id)
    session_info.pads_user_info = pads_user_info
    if status_code == 401: # could be just no session_id, but also could have be returned by PaDS if it doesn't recognize it
        if session_info.pads_session_info.pads_status_response > 500:
            msg = f"{caller_name}: PaDS error or PaDS unavailable - user cannot be logged in and no session_id assigned"
            logger.error(msg)
        # session is not logged in
        # session_info.confirmed_unauthenticated = True
        # these are defaults so commented out
        # session_info.authenticated = False
        # session_info.user_id = 0
        # session_info.username = opasConfig.USER_NOT_LOGGED_IN_NAME
        # session_info.user_type = "Unknown"
        # session_info.admin = False
        # session_info.authorized_peparchive = False
        # session_info.authorized_pepcurrent = False
    else:
        start_time = pads_session_info.session_start_time if pads_session_info.session_start_time is not None else datetime.datetime.now()
        if pads_user_info is not None:
            session_info.user_id = userID=pads_user_info.UserId
            session_info.username = pads_user_info.UserName
            session_info.user_type = pads_user_info.UserType
            session_info.admin = pads_user_info.UserType=="Admin"
            session_info.authorized_peparchive = pads_user_info.HasArchiveAccess
            session_info.authorized_pepcurrent = pads_user_info.HasCurrentAccess
            logger.debug("PaDS returned user info.  Saving to DB")
            unused_val = save_session_info_to_db(session_info)
    
    if session_info.user_type is None:
        session_info.user_type = "Unknown"
    if session_info.username is None:
        session_info.username = opasConfig.USER_NOT_LOGGED_IN_NAME
            
    # print (f"SessInfo: {session_info}")
    
    logger.info(f"***authent: {session_info.authenticated} - get_full_session_info total time: {time.time() - ts}***")
    return session_info

def get_authserver_session_userinfo(session_id, client_id):
    """
    Send PaDS the session ID and see if that's associated with a user yet.
    """
    ret_val = None
    caller_name = "AuthServerUserinfoError"
    
    status_code = 401
    msg = f"for session {session_id} from client {client_id}"
    #logger.debug(msg)
    if session_id is not None:
        full_URL = base + f"/v1/Users" + f"?SessionID={session_id}"
        try:
            response = requests.get(full_URL, headers={"Content-Type":"application/json"})
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
    session_id = session_info.session_id
    ocd = opasCentralDBLib.opasCentralDB()
    db_session_info = ocd.get_session_from_db(session_id)
    if db_session_info is None:
        ret_val, saved_session_info = ocd.save_session(session_id, session_info)
        logger.warning(f"Saving session info {session_id}") # temp, should be debug
    else:
        logger.debug(f"Session {session_id} already found in db. Updating...")
        if session_info.username != db_session_info.username and db_session_info.username != opasConfig.USER_NOT_LOGGED_IN_NAME:
            msg = f"AuthServerSessionInfoError: MISMATCH! Two Usernames with same session_id. OLD(DB): {db_session_info}; NEW(SESSION): {session_info}"
            print (msg)
            logger.error(msg)
        
        logger.warning(f"Updating session info {session_id}") # temp, should be debug
        ret_val = ocd.update_session(session_id,
                                     userID=session_info.user_id,
                                     username=session_info.username, 
                                     authenticated=1 if session_info.authenticated == True else 0,
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
    caller_name = "AuthServerLogin"
    
    logger.info(f"Logging in user {username} with session_id {session_id}")
    if session_id is not None:
        full_URL = base + f"/v1/Authenticate/?SessionId={session_id}"
    else:
        full_URL = base + f"/v1/Authenticate/"

    try:
        pads_response = requests.post(full_URL, headers={"Content-Type":"application/json"}, json={"UserName":f"{username}", "Password":f"{password}"})
    except Exception as e:
        msg = f"{caller_name}: Authorization server not available. {e}"
        logger.error(msg)
        if opasConfig.LOCAL_TRACE: print (f"****WATCH_THIS****: {msg}")
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
    caller_name = "AuthServerLogout"
    
    if session_id is not None:
        if response is not None:
            response.delete_cookie(key=opasConfig.OPASSESSIONID,path="/",
                                   domain=localsecrets.COOKIE_DOMAIN)
        
        full_URL = base + f"/v1/Users/Logout/?SessionId={session_id}"
        response = requests.post(full_URL, headers={"Content-Type":"application/json"})
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
    caller_name = "AuthServerPermision"
    
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
        response = requests.get(full_URL, headers=headers)
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
                ret_resp = models.PadsPermitInfo(**ret_resp)
                # returns 401 for a non-authenticated session
                ret_resp.StatusCode = response.status_code
                ret_val = ret_resp.Permit
                if ret_resp.StatusCode != 200:
                    msg = f"PaDS returned a non-200 permit req status: {ret_resp.StatusCode}"
                    logger.info(msg)
                    
        except Exception as e:
            msg = f"{caller_name}: Permits response error {e}. Composing no access response."
            logger.error(msg)
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
    caller_name = "AuthServerPermision"
    
    try:
        open_access = False
        ret_val = models.AccessLimitations()
        ret_val.doi = doi
        ret_val.accessLimitedPubLink = None
        ret_val.accessLimitedCode = 200 # default (for now)

        # USE THESE DEFAULTS, only set below if different
        # default, turned on if classification below is opasConfig.DOCUMENT_ACCESS_EMBARGOED
        ret_val.accessLimited = True # no access by default, may be changed below.
        ret_val.accessLimitedClassifiedAsCurrentContent = False
        
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
                publisherAccess = opasConfig.ACCESS_SUMMARY_PUBLISHER_INFO + opasConfig.ACCESS_SUMMARY_PUBLISHER_INFO_DOI_LINK % ret_val.doi
                # TODO: get the link we use to send users to publishers site when we don't have it, and no doi, and implement here.
                #       for now, just doi
                ret_val.accessLimitedPubLink = opasConfig.ACCESS_SUMMARY_PUBLISHER_INFO_DOI_LINK % ret_val.doi
            else:
                publisherAccess = "."
            
            if classification in (opasConfig.DOCUMENT_ACCESS_FREE):
                # free can be for anyone!!!! Change accessLimited
                open_access = True
                ret_val.accessLimited = False
                ret_val.accessLimitedDescription = opasConfig.ACCESSLIMITED_DESCRIPTION_FREE
                #"This content is currently free to all users."
                ret_val.accessLimitedReason = opasConfig.ACCESSLIMITED_DESCRIPTION_FREE
                
            elif classification in (opasConfig.DOCUMENT_ACCESS_OFFSITE):
                # we only allow reading abstracts for offsite, accessLimited is True
                ret_val.accessLimitedDescription = opasConfig.ACCESS_SUMMARY_DESCRIPTION
                #"This content is currently free to all users."
                ret_val.accessLimitedReason = opasConfig.ACCESSLIMITED_DESCRIPTION_OFFSITE + publisherAccess # limited...get it elsewhere
        
            elif classification in (opasConfig.DOCUMENT_ACCESS_EMBARGOED): # PEPCurrent
                ret_val.accessLimitedDescription = opasConfig.ACCESS_SUMMARY_DESCRIPTION
                ret_val.accessLimitedClassifiedAsCurrentContent = True
                ret_val.accessLimitedReason = opasConfig.ACCESS_SUMMARY_DESCRIPTION + opasConfig.ACCESS_SUMMARY_EMBARGOED + publisherAccess # limited...get it elsewhere
                if session_info is not None:
                    try:
                        # #########################################################################################
                        # optimization...if authorized for PEPCurrent, don't check again this query, unless it's a full-text request
                        # #########################################################################################
                        if session_info.authorized_pepcurrent:
                            ret_val.accessLimited = False # you can access it!!!
                            # "This current content is available for you to access"
                            ret_val.accessLimitedReason = opasConfig.ACCESSLIMITED_DESCRIPTION_CURRENT_CONTENT_AVAILABLE 
                            logger.debug("Optimization - session info used to authorize PEPCurrent document")
                    except Exception as e:
                        logger.error(f"{caller_name}: PEPCurrent document permission: {e}")

            elif classification in (opasConfig.DOCUMENT_ACCESS_ARCHIVE):
                ret_val.accessLimitedDescription = opasConfig.ACCESS_SUMMARY_DESCRIPTION 
                # ret_val.accessLimited = True # default is true
                ret_val.accessLimitedReason = opasConfig.ACCESS_SUMMARY_FORSUBSCRIBERS 
                # #########################################################################################
                # optimization...if authorized, don't check again, unless it's a full-text request
                # #########################################################################################
                if session_info is not None:
                    try:
                        if session_info.authorized_peparchive:
                            ret_val.accessLimited = False # you can access it!!!
                            # "This content is available for you to access"
                            ret_val.accessLimitedReason = opasConfig.ACCESSLIMITED_DESCRIPTION_AVAILABLE
                            logger.debug("Optimization - session info used to authorize PEPArchive document")
                    except Exception as e:
                        logger.error(f"{caller_name}: PEPArchive document permission: {e}")

            elif classification in (opasConfig.DOCUMENT_ACCESS_TOC):
                open_access = True
                ret_val.accessLimited = False # you can access it!!! (All TOCs are open)
                # just like free for now
                ret_val.accessLimitedDescription = opasConfig.ACCESSLIMITED_DESCRIPTION_FREE
                #"This content is currently free to all users."
                ret_val.accessLimitedReason = opasConfig.ACCESSLIMITED_DESCRIPTION_FREE
            else:
                logger.error(f"{caller_name}: Unknown classification: {classification}")

            # **************************************
            # Now check for access, or cached access
            #   - always check for a full-text request so PaDS can track them.
            #     since we don't really always know about authentication, we need to check all requests that are otherwise rejected.
            # **************************************
            try:                   
                if not open_access:
                    if (session_info.authenticated == True # Must be authenticated for this check
                        and (ret_val.accessLimited == True # if it's marked limited, then may need to check, it might be first one
                             or fulltext_request == True)): # or whenever full-text is requested.
                        # and session_info.api_client_session and session_info.api_client_id in PADS_BASED_CLIENT_IDS:
                        if fulltext_request:
                            reason_for_check = opasConfig.AUTH_DOCUMENT_VIEW_REQUEST
                        else:
                            reason_for_check = opasConfig.AUTH_ABSTRACT_VIEW_REQUEST
                        try:
                            pads_authorized, resp = authserver_permission_check(session_id=session_info.session_id,
                                                                                doc_id=doc_id,
                                                                                doc_year=year,
                                                                                reason_for_check=reason_for_check,
                                                                                request=request)
                        except Exception as e:
                            # PaDS could be down, local development
                            logger.error(f"{caller_name}: Access Exception: {e}")
                            if localsecrets.BASEURL == "development.org:9100":
                                resp = models.PadsPermitInfo(Permit=True, HasArchiveAccess=True, HasCurrentAccess=True)
                                # so it doesn't have to check this later
                                session_info.authorized_peparchive = True
                                session_info.authorized_pepcurrent = True
                            else:
                                session_info.authorized_peparchive = False
                                session_info.authorized_pepcurrent = False
                                resp = models.PadsPermitInfo(Permit=False, HasArchiveAccess=False, HasCurrentAccess=False)
                                
        
                        finally:
                            # save PaDS code
                            ret_val.accessLimitedCode = resp.StatusCode
    
                            if resp.StatusCode == httpCodes.HTTP_401_UNAUTHORIZED: # or resp.ReasonStr == 'Session has not been authenticated':
                                # if this is True, then we can stop asking this time
                                # You would get the same return if 
                                #    the session was not recognised on pads, 
                                #    the session had been deleted from the database (should never happen…), or 
                                #    the session simply never existed.
                                ret_val.accessLimited = True
                                session_info.authenticated = False
                                msg = f"Full text of {doc_id} unavailable. " + opasConfig.ACCESSLIMITED_401_UNAUTHORIZED
                                ret_val.accessLimitedReason = msg
                            else:
                                # set default again based on update from PaDS query
                                ret_val.accessLimited = True
    
                                if ret_val.accessLimitedClassifiedAsCurrentContent == True:
                                    if resp.HasCurrentAccess == True:
                                        session_info.authorized_pepcurrent = True
                                        ret_val.accessLimited = False
                                    else:
                                        ret_val.accessLimited = True
                                else: # not current content
                                    if resp.HasArchiveAccess == True:
                                        session_info.authorized_peparchive = True
                                        ret_val.accessLimited = False
    
                                if fulltext_request and pads_authorized:
                                    # let's make sure we know about this user.
                                    if session_info.user_id == opasConfig.USER_NOT_LOGGED_IN_NAME:
                                        # We got this far, We need to find out who this is
                                        pads_user_info, status_code = get_authserver_session_userinfo(session_info.session_id, session_info.api_client_id)
                                        if pads_user_info is not None:
                                            session_info.user_id = pads_user_info.UserId
                                            session_info.username = pads_user_info.UserName
                                            session_info.user_type = pads_user_info.UserType # TODO - Add this to session table
                                            # session_info.session_expires_time = ?
                                            ocd = opasCentralDBLib.opasCentralDB()
                                            ocd.update_session(session_info.session_id,
                                                               userID=session_info.user_id,
                                                               username=session_info.username, 
                                                               authenticated=1,
                                                               authorized_peparchive=1 if session_info.authorized_peparchive == True else 0,
                                                               authorized_pepcurrent=1 if session_info.authorized_pepcurrent == True else 0,
                                                               session_end=session_info.session_expires_time,
                                                               api_client_id=session_info.api_client_id
                                                               )
                                            
                                if pads_authorized:
                                    # "This content is available for you to access"
                                    ret_val.accessLimited = False
                                    ret_val.accessLimitedDescription = opasConfig.ACCESSLIMITED_DESCRIPTION_AVAILABLE 
                                    ret_val.accessLimitedReason = opasConfig.ACCESSLIMITED_DESCRIPTION_AVAILABLE 
                                    msg = f"Document {doc_id} available.  Pads Reason: {resp.ReasonStr}. Opas Reason: {ret_val.accessLimitedDescription} - {ret_val.accessLimitedReason}"
                                    logger.debug(msg)
                                    ret_val.accessLimitedDebugMsg = msg
                                else:
                                    # changed from warning to info 2021-06-02 to reduce normal logging
                                    msg = f"Document {doc_id} unavailable.  Pads Reason: {resp.ReasonStr} Opas: {ret_val.accessLimitedDescription} - {ret_val.accessLimitedReason}"
                                    logger.info(msg) # limited...get it elsewhere
                                    ret_val.accessLimitedDebugMsg = msg
                                    ret_val.accessLimited = True
                                    if ret_val.accessLimitedClassifiedAsCurrentContent:
                                        # embargoed
                                        ret_val.accessLimitedReason = opasConfig.ACCESS_SUMMARY_EMBARGOED
                                    else:
                                        # non embargoed, but no access.
                                        ret_val.accessLimitedReason = f"{ret_val.accessLimitedDescription} {ret_val.accessLimitedReason}"
                                        
                    else:
                        # not full-text OR (not authenticated or accessLimited==False)
                        msg = f"No PaDS check needed: Document {doc_id} accessLimited: {ret_val.accessLimited}. Authent: {session_info.authenticated}"
                        logger.debug(msg)
                        ret_val.accessLimitedDebugMsg = msg

                else: # It's open access!
                    msg = f"No PaDS check needed: Document {doc_id} is open access"
                    logger.debug(msg)
                    ret_val.accessLimitedDebugMsg = msg
        
            except Exception as e:
                msg = f"{caller_name}: Issue checking document permission. Possibly not logged in {e}"
                logger.error(msg)
                ret_val.accessLimitedDebugMsg = msg
                pass # can't be checked, will be unauthorized.

    except Exception as e:
        msg = f"{caller_name}: General exception {e} trying ascertain access limitations."
        logger.error(msg)
        ret_val.accessLimitedDebugMsg = msg

    if fulltext_request and ret_val.accessLimited:
        # happens anytime someone views an abstract in Document mode because they don't have an account. Perfectly legal. Changed to info (from error)
        msg = f"Full-text access for {doc_id} denied ({ret_val.accessLimitedCode}). Sess:{session_id}: Access:{ret_val.accessLimitedReason}"
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
    caller_name = "GetPaDSSessionInfo"
    
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
    
    # user_ip is used to get the X_FORWARDED_FOR address to send to server for IP based users
    user_ip = get_user_ip(request)
    try:
        if user_ip is not None and user_ip is not '':
            headers = { opasConfig.X_FORWARDED_FOR:user_ip }
            pads_session_info = requests.get(full_URL, headers)
            logger.warning(f"{caller_name}: Session ID:{session_id}. X_FORWARDED_FOR from authenticateIP: {user_ip}. URL: {req_url} PaDS Session Info: {pads_session_info}") # temp, should be info
        else:
            pads_session_info = requests.get(full_URL)
            
    except Exception as e:
        logger.error(f"{caller_name}: Authorization server not available. {e}")
        pads_session_info = models.PadsSessionInfo()
    else:
        status_code = pads_session_info.status_code # save it for a bit (we replace pads_session_info below)
        if status_code > 403: # e.g., (httpCodes.HTTP_500_INTERNAL_SERVER_ERROR, httpCodes.HTTP_503_SERVICE_UNAVAILABLE):
            error_text = f"{caller_name}: PaDS session_info status_code is {status_code}"
            logger.error(error_text)
            # try once without the session ID
            if retry == True:
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
                logger.warning(f"PaDS Status Ok, Final IP Session Info: {pads_session_info} URL: {req_url}.") # temp, should be info or removed
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