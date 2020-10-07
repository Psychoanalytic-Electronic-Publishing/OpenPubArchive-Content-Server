#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import datetime
import opasConfig
import models
import logging
logger = logging.getLogger(__name__)

from starlette.responses import JSONResponse, Response
from starlette.requests import Request

# import localsecrets
from localsecrets import PADS_TEST_ID, PADS_TEST_PW, PADS_BASED_CLIENT_IDS
base = "https://padstest.zedra.net/PEPSecure/api"

import opasCentralDBLib

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
    userinfo = pads_get_userinfo(session_id)
    if userinfo is not None:
        msg = f"Session info and user fetched for sessionid {session_id}"
        logger.debug(msg)
        print(msg)
        userid = userID=userinfo.UserId
        username = userinfo.UserName
        usertype = userinfo.UserType
        admin = userinfo.UserType=="Admin"
    else:
        msg = f"Session info returned no user info...not logged in for sessionid {session_id}"
        logger.debug(msg)
        print(msg)
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
    """
    try:
        # PaDS session info
        pads_session_info = models.PadsSessionInfo(**response)
        session_id = pads_session_info.SessionId # PaDS session ID
        # add user fields
        ret_val = session_info = update_sessioninfo_with_userinfo(pads_session_info, client_id)
        # make sure the session is recorded.
        ocd = opasCentralDBLib.opasCentralDB(session_id=session_id)
        db_session_info = ocd.get_session_from_db(session_id)
        if db_session_info is None:
            ocd.save_session(session_id, session_info) 
    except Exception as e:
        logger.error(f"Can't get or save session info from auth server {e}")
        ret_val = None

    return ret_val
    
def pads_get_session(session_id=None, client_id=opasConfig.NO_CLIENT_ID):
    """
    Get a session ID from the auth server (e.g., PaDS).  This is how PaDS does it.
    """
    if session_id is not None:
        full_URL = base + f"/v1/Authenticate/IP/" + f"?SessionID={session_id}"
    else:
        full_URL = base + f"/v1/Authenticate/IP/"
    
    pads_session_info = requests.get(full_URL)
    pads_session_info = pads_session_info.json()
    pads_session_info = fix_pydantic_invalid_nones(pads_session_info)
    session_info = set_session_info(pads_session_info, client_id)
    return session_info, pads_session_info

def pads_login(username=PADS_TEST_ID, password=PADS_TEST_PW, session_id=None, client_id=opasConfig.NO_CLIENT_ID):
    """
    Login directly via the auth server (e.g., in this case PaDS)
    
    If session_id is included, the idea is that the logged in entity will keep that constant.
      -- #TODO but that's not implemented yet!
      
    """
    if session_id is not None:
        full_URL = base + f"/v1/Authenticate/" + f"?SessionID={session_id}"
    else:
        full_URL = base + f"/v1/Authenticate/"
        
    pads_response = requests.post(full_URL, headers={"Content-Type":"application/json"}, json={"UserName":f"{username}", "Password":f"{password}"})
    pads_response = pads_response.json()
    pads_response = fix_pydantic_invalid_nones(pads_response)
    session_info = set_session_info(pads_response, client_id)
    pads_session_info = models.PadsSessionInfo(**pads_response)
    return session_info, pads_session_info

def pads_logout(session_id):
    ret_val = False
    if session_id is not None:
        full_URL = base + f"/v1/Users/Logout/?SessionId={session_id}"
        response = requests.post(full_URL, headers={"Content-Type":"application/json"})
        if response.ok:
            ret_val = True
        else:
            logger.error(f"Error logging out for sessionId: {session_id} from PaDS: {response.json()}")
    else:
        logger.warning("No SessionId supplied.")

    return ret_val

def pads_get_userinfo(session_id):
    ret_val = None
    print (f"Getting user info for session {session_id}")
    if session_id is not None:
        full_URL = base + f"/v1/Users" + f"?SessionID={session_id}"
        response = requests.get(full_URL, headers={"Content-Type":"application/json"})
        padsinfo = response.json()
        if response.ok:
            ret_val = models.PadsUserInfo(**padsinfo)
        else:
            print(f"User not logged in for sessionId: {session_id} from PaDS: {padsinfo}")
            
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
    if documentListItem is not None:
        ret_val = documentListItem
    else:
        ret_val = models.AccessLimitations()

    ret_val.doi = doi
    ret_val.accessLimitedPubLink = None
    ret_val.accessLimited = True # no access...default, may be changed below.
    
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

    elif session_info is None:
        # not logged in; take the quickest way out.
        ret_val.accessLimitedDescription = opasConfig.ACCESS_SUMMARY_FORSUBSCRIBERS 
        ret_val.accessLimited = True
        ret_val.accessLimitedReason = opasConfig.ACCESS_SUMMARY_DESCRIPTION + opasConfig.ACCESS_SUMMARY_FORSUBSCRIBERS
    
    elif classification in (opasConfig.DOCUMENT_ACCESS_EMBARGOED): # PEPCurrent
        ret_val.accessLimitedDescription = opasConfig.ACCESS_SUMMARY_EMBARGOED
        ret_val.accessLimitedCurrentContent = True
        ret_val.accessLimitedReason = opasConfig.ACCESS_SUMMARY_DESCRIPTION + opasConfig.ACCESS_SUMMARY_EMBARGOED + publisherAccess # limited...get it elsewhere
        try:
            if session_info.authorized_pepcurrent:
                ret_val.accessLimited = False # you can access it
                ret_val.accessLimitedCurrentContent = True # true, this is current content,
                # "This current content is available for you to access"
                ret_val.accessLimitedReason = opasConfig.ACCESSLIMITED_DESCRIPTION_CURRENT_CONTENT_AVAILABLE 
        except:
            pass # could be a direct call without a session; returns unauthorized
            
    elif classification in (opasConfig.DOCUMENT_ACCESS_ARCHIVE):
        ret_val.accessLimitedDescription = opasConfig.ACCESS_SUMMARY_FORSUBSCRIBERS 
        ret_val.accessLimited = True
        ret_val.accessLimitedReason = opasConfig.ACCESS_SUMMARY_DESCRIPTION + opasConfig.ACCESS_SUMMARY_FORSUBSCRIBERS
        try:
            if session_info.authorized_peparchive:
                ret_val.accessLimited = False
                ret_val.accessLimitedCurrentContent = False
                # "This content is available for you to access"
                ret_val.accessLimitedReason = opasConfig.ACCESSLIMITED_DESCRIPTION_AVAILABLE 
        except:
            pass # could be a direct call without a session; returns unauthorized
    
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
                authorized, resp = pads_permission_check(session_id=session_info.session_id,
                                                         doc_id=doc_id,
                                                         doc_year=year,
                                                         reason_for_check=reason_for_check)
    
                # if this is True, then as long as session_info is valid, it won't need to check again
                # if accessLimited is ever True again, e.g., now a different type of document, it will check again.
                # should markedly decrease the number of calls to PaDS to check.
                if resp.HasArchiveAccess == True:
                    session_info.authorized_peparchive = True
                
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
                    ret_val.accessLimitedReason = resp.ReasonStr # limited...get it elsewhere
    
        except Exception as e:
            logger.debug(f"Issue checking document permission. Possibly not logged in {e}")
            pass # can't be checked, will be unauthorized.
    
    return ret_val

