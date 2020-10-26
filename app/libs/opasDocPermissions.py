#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import datetime
import opasConfig
import models
import logging
import localsecrets
import urllib.parse
import json

logger = logging.getLogger(__name__)

from starlette.responses import JSONResponse, Response
from starlette.requests import Request
import starlette.status as httpCodes

# import localsecrets
from localsecrets import PADS_TEST_ID, PADS_TEST_PW, PADS_BASED_CLIENT_IDS
base = "https://padstest.zedra.net/PEPSecure/api"

import opasCentralDBLib

def verify_header(request, caller_name):
    # Double Check for missing header test--ONLY checks headers, not other avenues used by find
    client_session_from_header = request.headers.get(opasConfig.CLIENTSESSIONID, None)
    client_id_from_header = request.headers.get(opasConfig.CLIENTID, None)
    if client_session_from_header == None:
        logger.error(f"***{caller_name}*** - No client-session supplied. Client-id (from header): {client_id_from_header}.")

def find_client_session_id(request: Request,
                           response: Response,
                           client_session: str=None
                           ):
    """
    ALWAYS returns a session ID.
    
    Dependency for client_session id:
           gets it from header;
           if not there, gets it from query param;
           if not there, gets it from a cookie
           Otherwise, gets a new one from the auth server
    """
    #client_id = int(request.headers.get("client-id", '0'))
    if client_session is None:
        client_session = request.headers.get(opasConfig.CLIENTSESSIONID, None)
    client_session_qparam = request.query_params.get(opasConfig.CLIENTSESSIONID, None)
    client_session_cookie = request.cookies.get(opasConfig.CLIENTSESSIONID, None)
    #Won't work unless they expose cookie to client, so don't waste time 
    #pepweb_session_cookie = request.cookies.get("pepweb_session", None)
    
    opas_session_cookie = request.cookies.get(opasConfig.OPASSESSIONID, None)
    if client_session is not None:
        ret_val = client_session
        msg = f"client-session from header: {ret_val} "
        logger.debug(msg)
    elif client_session_qparam is not None:
        ret_val = client_session_qparam
        msg = f"client-session from param: {ret_val} "
        logger.debug(msg)
    elif client_session_cookie is not None:
        ret_val = client_session_cookie
        msg = f"client-session from client-session cookie: {ret_val} "
        logger.debug(msg)
    #elif pepweb_session_cookie is not None: # this is what Gavant client sets
        #s = urllib.parse.unquote(pepweb_session_cookie)
        #cookie_dict = json.loads(s)
        #ret_val = cookie_dict["authenticated"]["SessionId"]
        #msg = f"client-session from pepweb-session cookie: {ret_val} "
        #logger.info(msg)
    elif opas_session_cookie is not None and opas_session_cookie != 'None':
        msg = f"client-session from stored OPASSESSION cookie {opas_session_cookie}"
        logger.debug(msg)       
        ret_val = opas_session_cookie
    else:
        msg = f"No client-session ID found."
        logger.debug(msg)       
        ret_val = None

    ## save it in cookie in case they call without it.
    #response.set_cookie(opasConfig.OPASSESSIONID,
                        #value=ret_val)

    return ret_val

def find_client_id(request: Request,
                   response: Response,
                  ):
    """
    ALWAYS returns a client ID.
    
    Dependency for client_id:
           gets it from header;
           if not there, gets it from query param;
           if not there, defaults to 0 (server is client)
    """
    #client_id = int(request.headers.get("client-id", '0'))
    ret_val = 0
    client_id = request.headers.get(opasConfig.CLIENTID, None)
    client_id_qparam = request.query_params.get(opasConfig.CLIENTID, None)
    client_id_cookie = request.cookies.get(opasConfig.CLIENTID, None)
    pepweb_session_cookie = request.cookies.get("pepweb_session", None)
    if client_id is not None:
        ret_val = client_id
        msg = f"client-id from header: {ret_val} "
        logger.debug(msg)
    elif client_id_qparam is not None:
        ret_val = client_id_qparam
        msg = f"client-id from param: {ret_val} "
        logger.debug(msg)
    elif client_id_cookie is not None:
        ret_val = client_id_cookie
        msg = f"client-id from cookie: {ret_val} "
        logger.debug(msg)
    elif pepweb_session_cookie is not None:
        ret_val = 2 #  pep-web client
        msg = f"client-id inferred from pepweb-session cookie: {ret_val} "
        logger.debug(msg)
    else:
        ret_val = opasConfig.NO_CLIENT_ID # no client id

    return ret_val

def fix_pydantic_invalid_nones(response_data):
    try:
        if response_data["ReasonStr"] is None:
            response_data["ReasonStr"] = ""
    except Exception as e:
        print (e)

    return response_data

def update_sessioninfo_with_userinfo(pads_session_info, client_id):
    # now get userinfo
    session_id = pads_session_info.SessionId
    userinfo = pads_get_userinfo(session_id, client_id)
    logger.debug(f"update_sessioninfo_with_userinfo: Session ID from PaDS: {session_id}")
    logger.debug(f"update_sessioninfo_with_userinfo: Userinfo from PaDS: {userinfo}")
    if userinfo is not None:
        msg = f"Session info and user fetched for sessionid {session_id} - {userinfo}"
        logger.debug(msg)
        userid = userID=userinfo.UserId
        username = userinfo.UserName
        usertype = userinfo.UserType
        admin = userinfo.UserType=="Admin"
    else:
        msg = f"Authorization server returned no user info for sessionid {session_id}"
        logger.debug(msg)
        userid = 0
        username = opasConfig.USER_NOT_LOGGED_IN_NAME
        usertype = "Unknown"
        admin = False
    
    ret_val = models.SessionInfo(session_id=session_id,
                                 user_id=userid,
                                 username=username,
                                 authenticated=pads_session_info.IsValidLogon,
                                 session_start=datetime.datetime.now(),
                                 user_type=usertype, 
                                 admin=admin,
                                 api_client_id=client_id
    )

    return ret_val # returns a sessionInfo model

def set_session_info(response, client_id):
    """
    Take the return info from the auth server and put it in the Opas SessionInfo model
    
    ** Saves or Updates the Session record in the api_sessions table **
    
    """
    try:
        # PaDS session info
        pads_session_info = models.PadsSessionInfo(**response)
        session_id = pads_session_info.SessionId # PaDS session ID
        logger.debug(f"set_session_info: Session ID from PaDS: {session_id}")
        # add user fields
        ret_val = session_info = update_sessioninfo_with_userinfo(pads_session_info, client_id)
        # make sure the session is recorded.
        ocd = opasCentralDBLib.opasCentralDB(session_id=session_id)
        db_session_info = ocd.get_session_from_db(session_id)
        if db_session_info is None:
            ocd.save_session(session_id, session_info)
        else:
            logger.debug(f"Session {session_id} already found in db. Updating...")
            if session_info.username != db_session_info.username and db_session_info.username != opasConfig.USER_NOT_LOGGED_IN_NAME:
                msg = f"MISMATCH! Two Usernames with same session_id. OLD(DB): {db_session_info}; NEW(SESSION): {session_info}"
                print (msg)
                logger.error(msg)
            
            ocd.update_session(session_id,
                               userID=session_info.user_id,
                               username=session_info.username, 
                               authenticated=1 if session_info.authenticated == True else 0,
                               authorized_peparchive=1 if session_info.authorized_peparchive == True else 0,
                               authorized_pepcurrent=1 if session_info.authorized_pepcurrent == True else 0,
                               session_end=session_info.session_expires_time,
                               api_client_id=session_info.api_client_id
                               )

    except Exception as e:
        logger.error(f"Can't get or save session info from auth server {e}")
        ret_val = None

    return ret_val
    
def pads_get_session(session_id=None, client_id=opasConfig.NO_CLIENT_ID, retry=True):
    """
    Get a session ID from the auth server (e.g., PaDS).  This is how PaDS does it.
    """
    if session_id is not None:
        full_URL = base + f"/v1/Authenticate/IP/" + f"?SessionID={session_id}"
    else:
        full_URL = base + f"/v1/Authenticate/IP/"

    try:
        pads_session_info = requests.get(full_URL)
    except Exception as e:
        logger.error(f"PaDS Authorization server not available. {e}")
        pads_session_info = models.PadsSessionInfo()
        session_info = models.SessionInfo()
    else:
        if pads_session_info.status_code == httpCodes.HTTP_500_INTERNAL_SERVER_ERROR:
            # try once without the session ID
            if retry == True:
                session_info, pads_session_info = pads_get_session(client_id=client_id, retry=False)
            else:
                logger.error(f"PaDS error 500")
        else:
            pads_session_info = pads_session_info.json()
            pads_session_info = fix_pydantic_invalid_nones(pads_session_info)
            # Save or update the data in the database
            session_info = set_session_info(pads_session_info, client_id)
            logger.info(f"Fetched session info {session_info} from PaDS.")

    return session_info, pads_session_info

def pads_login(username=PADS_TEST_ID, password=PADS_TEST_PW, session_id=None, client_id=opasConfig.NO_CLIENT_ID):
    """
    Login directly via the auth server (e.g., in this case PaDS)
    
    If session_id is included, the idea is that the logged in entity will keep that constant.
      -- #TODO but that's not implemented in this server itself, if logged in through there, yet!
      
    """
    logger.info(f"Logging in user {username} with session_id {session_id}")
    if session_id is not None:
        full_URL = base + f"/v1/Authenticate/" + f"?SessionID={session_id}"
    else:
        full_URL = base + f"/v1/Authenticate/"

    try:
        pads_response = requests.post(full_URL, headers={"Content-Type":"application/json"}, json={"UserName":f"{username}", "Password":f"{password}"})
    except Exception as e:
        logger.error(f"PaDS Authorization server not available. {e}")
        pads_session_info = models.PadsSessionInfo()
        session_info = models.SessionInfo()
    else:
        if pads_response.ok:
            pads_response = pads_response.json()
            pads_response = fix_pydantic_invalid_nones(pads_response)
            session_info = set_session_info(pads_response, client_id)
            if isinstance(pads_response, str):
                pads_session_info = models.PadsSessionInfo()
                logger.error(f"Pads returned error string: {pads_response}")
            else:
                try:
                    pads_session_info = models.PadsSessionInfo(**pads_response)
                except Exception as e:
                    logger.error(f"Pads return assignment error: {e}")
                    pads_session_info = models.PadsSessionInfo()
        elif pads_response.status_code == 500: # TODO: may want to limit this to error 500
            # try without session id
            logger.error(f"PaDS login returned {pads_response.status_code}. Trying without session id.")
            session_info, pads_session_info = pads_login(username=username, password=password, client_id=client_id)
        else:
            pads_response = pads_response.json()
            pads_response = fix_pydantic_invalid_nones(pads_response)
            session_info = set_session_info(pads_response, client_id)
            if isinstance(pads_response, str):
                pads_session_info = models.PadsSessionInfo()
                logger.error(f"Pads returned error string: {pads_response}")
            else:
                try:
                    pads_session_info = models.PadsSessionInfo(**pads_response)
                except Exception as e:
                    logger.error(f"Pads return assignment error: {e}")
                    pads_session_info = models.PadsSessionInfo()

    return session_info, pads_session_info

def pads_logout(session_id, request: Request=None, response: Response=None):
    ret_val = False
    if session_id is not None:
        if response is not None:
            response.delete_cookie(key=opasConfig.OPASSESSIONID,path="/",
                                   domain=localsecrets.COOKIE_DOMAIN)
        
        full_URL = base + f"/v1/Users/Logout/?SessionId={session_id}"
        response = requests.post(full_URL, headers={"Content-Type":"application/json"})
        if response.ok:
            ret_val = True
        else:
            logger.error(f"Error logging out for sessionId: {session_id} from PaDS: {response.json()}")
    else:
        logger.warning("No SessionId supplied.")

    return ret_val

def pads_get_userinfo(session_id, client_id):
    ret_val = None
    logger.debug(f"get_user_info for session {session_id} from client {client_id}")
    if session_id is not None:
        full_URL = base + f"/v1/Users" + f"?SessionID={session_id}"
        try:
            response = requests.get(full_URL, headers={"Content-Type":"application/json"})
        except Exception as e:
            msg = f"No user info from authorization server {e}. Non-logged in user for sessionId: {session_id} client-id {client_id}.  Message from PaDS: {padsinfo}. "
            logger.error(msg)
        else:
            padsinfo = response.json()
            if response.ok:
                ret_val = models.PadsUserInfo(**padsinfo)
            else:
                logger.info(f"No userinfo returned for non-logged in user for client-id {client_id} sessionId: {session_id}. Info from PaDS: {padsinfo}")
            
    return ret_val

def pads_permission_check(session_id, doc_id, doc_year, reason_for_check=None):
    ret_val = False
    ret_resp = None
    if reason_for_check is None:
        logger.warning("fulltext_request info not supplied")
        
    full_URL = base + f"/v1/Permits?SessionId={session_id}&DocId={doc_id}&DocYear={doc_year}&ReasonForCheck={reason_for_check}"
    response = requests.get(full_URL)
    # if response.ok == True:  # returns 401 for a non-authenticated session
    try:
        ret_resp = response.json()
        ret_val = ret_resp["Permit"]
        ret_resp = models.PadsPermitInfo(**ret_resp)
        
    except Exception as e:
        msg = f"Permits response error {e}. Composing no access response."
        logger.error(msg)
        ret_val = False
        ret_resp = models.PadsPermitInfo(SessionId=session_id,
                                         DocId=doc_id,
                                         ReasonStr=msg)

    return ret_val, ret_resp      
        
def get_access_limitations(doc_id,
                           classification,
                           session_info,
                           authenticated=None, 
                           year=None,
                           doi=None,
                           documentListItem: models.DocumentListItem=None,
                           fulltext_request:bool=None):
    """
    Based on the classification of the document (archive, current), and the users permissions
      in session_info, determine whether this user has access to the full-text of the document,
      and fill out 
    """
    try:
        
        if documentListItem is not None:
            ret_val = documentListItem
        else:
            ret_val = models.AccessLimitations()
    
        ret_val.doi = doi
        ret_val.accessLimitedPubLink = None
        ret_val.accessLimited = True # no access...default, may be changed below.
        
        if session_info is None:
            logger.info(f"Document permissions for {doc_id} -- no session info")
            ## not logged in; take the quickest way out.
            #ret_val.accessLimitedDescription = opasConfig.ACCESS_SUMMARY_FORSUBSCRIBERS 
            #ret_val.accessLimited = True
            #ret_val.accessLimitedReason = opasConfig.ACCESS_SUMMARY_DESCRIPTION + opasConfig.ACCESS_SUMMARY_FORSUBSCRIBERS
        
        if ret_val.doi is not None:
            publisherAccess = opasConfig.ACCESS_SUMMARY_PUBLISHER_INFO + opasConfig.ACCESS_SUMMARY_PUBLISHER_INFO_DOI_LINK % ret_val.doi
            # TODO: get the link we use to send users to publishers site when we don't have it, and no doi, and implement here.
            #       for now, just doi
            ret_val.accessLimitedPubLink = opasConfig.ACCESS_SUMMARY_PUBLISHER_INFO_DOI_LINK % ret_val.doi
        else:
            publisherAccess = ""
        
        if classification in (opasConfig.DOCUMENT_ACCESS_FREE):
            # free can be for anytone
            ret_val.accessLimitedDescription = opasConfig.ACCESSLIMITED_DESCRIPTION_FREE
            ret_val.accessLimited = False
            ret_val.accessLimitedCurrentContent = False
            #"This content is currently free to all users."
            ret_val.accessLimitedReason = opasConfig.ACCESSLIMITED_DESCRIPTION_FREE
            
        elif classification in (opasConfig.DOCUMENT_ACCESS_OFFSITE):
            ret_val.accessLimitedDescription = opasConfig.ACCESSLIMITED_DESCRIPTION_OFFSITE
            ret_val.accessLimited = True
            ret_val.accessLimitedCurrentContent = False
            #"This content is currently free to all users."
            ret_val.accessLimitedReason = opasConfig.ACCESS_SUMMARY_DESCRIPTION + opasConfig.ACCESS_SUMMARY_EMBARGOED + publisherAccess # limited...get it elsewhere
    
        elif classification in (opasConfig.DOCUMENT_ACCESS_EMBARGOED): # PEPCurrent
            ret_val.accessLimitedDescription = opasConfig.ACCESS_SUMMARY_EMBARGOED
            ret_val.accessLimitedCurrentContent = True
            ret_val.accessLimitedReason = opasConfig.ACCESS_SUMMARY_DESCRIPTION + opasConfig.ACCESS_SUMMARY_EMBARGOED + publisherAccess # limited...get it elsewhere
            if session_info is not None:
                try:
                    if session_info.authorized_pepcurrent:
                        ret_val.accessLimited = False # you can access it
                        ret_val.accessLimitedCurrentContent = True # true, this is current content,
                        # "This current content is available for you to access"
                        ret_val.accessLimitedReason = opasConfig.ACCESSLIMITED_DESCRIPTION_CURRENT_CONTENT_AVAILABLE 
                except Exception as e:
                    logger.error(f"PEPCurrent document error checking permission: {e}")
            else:
                logger.debug("No session info provided to assess current document authorization")
        elif classification in (opasConfig.DOCUMENT_ACCESS_ARCHIVE):
            ret_val.accessLimitedDescription = opasConfig.ACCESS_SUMMARY_FORSUBSCRIBERS 
            ret_val.accessLimited = True
            ret_val.accessLimitedReason = opasConfig.ACCESS_SUMMARY_DESCRIPTION + opasConfig.ACCESS_SUMMARY_FORSUBSCRIBERS
            if session_info is not None:
                try:
                    if session_info.authorized_peparchive:
                        ret_val.accessLimited = False
                        ret_val.accessLimitedCurrentContent = False
                        # "This content is available for you to access"
                        ret_val.accessLimitedReason = opasConfig.ACCESSLIMITED_DESCRIPTION_AVAILABLE 
                except Exception as e:
                    logger.error(f"PEPArchive document error checking permission: {e}")
            else:
                logger.debug("No session info provided to assess archive document authorization")
        else:
            logger.error(f"Unknown classification: {classification}")
        
        # We COULD check the session_id in PADS here with the art_id and year, for EVERY return!
        #  would it be slow?  Certainly for more than a dozen records, might...this is just for one instance though.
        # print (f"SessionID {session_info.session_id}, classificaton: {ret_val.accessLimited} and client_session: {session_info.api_client_session}")
        
        if session_info is not None:
            try:
                # always check for a full-text request so PaDS can track them.  
                # This is an optimization attempt.  
                #     However, if it's not full-text if you're not logged in, save the test.
                # and the user is not logged in, then no need to check special permissions.
                # TODO - Need to double check this...is there ever special permissions for nonlogged in users?
                if ((session_info.authenticated == True and ret_val.accessLimited == True) or fulltext_request == True): # and session_info.api_client_session and session_info.api_client_id in PADS_BASED_CLIENT_IDS:
        
                    if fulltext_request:
                        reason_for_check = opasConfig.AUTH_DOCUMENT_VIEW_REQUEST
                    else:
                        reason_for_check = opasConfig.AUTH_ABSTRACT_VIEW_REQUEST
    
                    logger.debug(f"Sending permit request for {session_info.session_id}")
                    try:
                        authorized, resp = pads_permission_check(session_id=session_info.session_id,
                                                                 doc_id=doc_id,
                                                                 doc_year=year,
                                                                 reason_for_check=reason_for_check)
                    except Exception as e:
                        # PaDS could be down, local development
                        if localsecrets.BASEURL == "development.org":
                            resp = models.PadsPermitInfo(Permit=True, HasArchiveAccess=True, HasCurrentAccess=True)
                            # so it doesn't have to check this later
                            session_info.authorized_peparchive = True
                            session_info.authorized_pepcurrent = True
                            authorized = True
    
                    finally:
                        # if this is True, then as long as session_info is valid, it won't need to check again
                        # if accessLimited is ever True again, e.g., now a different type of document, it will check again.
                        # should markedly decrease the number of calls to PaDS to check.
                        # check for conflicts
                        if session_info.authorized_peparchive == True and resp.HasArchiveAccess == False:
                            logger.error(f"Permission Conflict: session {session_info.session_id} PEPArchive authorized; PaDS says No. PaDS message: {resp.ReasonStr} ")
                            
                        if resp.HasArchiveAccess == True:
                            session_info.authorized_peparchive = True
                            ret_val.accessLimited = False
                        
                        if resp.HasCurrentAccess == True:
                            session_info.authorized_pepcurrent = True
                            ret_val.accessLimitedCurrentContent = False
                    
                        if authorized:
                            # "This content is available for you to access"
                            ret_val.accessLimitedDescription = opasConfig.ACCESSLIMITED_DESCRIPTION_AVAILABLE 
                            ret_val.accessLimited = False
                            #documentListItem.accessLimitedCurrentContent = False
                            # "This content is available for you to access"
                            ret_val.accessLimitedReason = opasConfig.ACCESSLIMITED_DESCRIPTION_AVAILABLE 
                        else:
                            ret_val.accessLimited = True
                            if classification in (opasConfig.DOCUMENT_ACCESS_EMBARGOED):
                                ret_val.accessLimitedReason
                            logger.debug(f"Document unavailable.  Pads Reason: {resp.ReasonStr} Opas Reason: {ret_val.accessLimitedDescription}") # limited...get it elsewhere
        
            except Exception as e:
                logger.error(f"Issue checking document permission. Possibly not logged in {e}")
                pass # can't be checked, will be unauthorized.

    except Exception as e:
        logger.error(f"General exception {e} trying ascertain access limitations.")
        
    return ret_val

