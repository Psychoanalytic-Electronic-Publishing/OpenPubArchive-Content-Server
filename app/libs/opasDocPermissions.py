#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import opasConfig
import models
import logging
logger = logging.getLogger(__name__)

from starlette.responses import JSONResponse, Response
from starlette.requests import Request

DUMMYUSERNAME = opasConfig.USER_NOT_LOGGED_IN_NAME
DUMMYPW = "NoPass"

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

def pads_get_session(session_id=None):
    if session_id is not None:
        full_URL = base + f"/v1/Authenticate/IP/" + f"?SessionID={session_id}"
    else:
        full_URL = base + f"/v1/Authenticate/IP/"

    response = requests.get(full_URL)
    response = response.json()
    response = fix_pydantic_invalid_nones(response)
    ret_val = models.PadsSessionInfo(**response)
    
    # make sure the session is recorded.
    session_id = ret_val.SessionId
    ocd = opasCentralDBLib.opasCentralDB(session_id=session_id)
    session_info = ocd.get_session_from_db(session_id)
    if session_info is None:
        # save the session for referential integrity of logged endpoints
        ocd.save_session(session_id, username=DUMMYUSERNAME, userID=0) 
    return ret_val

def pads_login(username=PADS_TEST_ID, password=PADS_TEST_PW, session_id=None):
    ret_val = None

    if session_id is not None:
        full_URL = base + f"/v1/Authenticate/" + f"?SessionID={session_id}"
    else:
        full_URL = base + f"/v1/Authenticate/"
        
    response = requests.post(full_URL, headers={"Content-Type":"application/json"}, json={"UserName":f"{username}", "Password":f"{password}"})
    jresponse = response.json()
    jresponse = fix_pydantic_invalid_nones(jresponse)
    try:
        ret_val = models.PadsSessionInfo(**jresponse)
    except Exception as e:
        msg = f"Error in response to login. {e}"
        logger.error(msg)
    else:
        # make sure the session is recorded.
        session_id = ret_val.SessionId
        ocd = opasCentralDBLib.opasCentralDB(session_id=session_id)
        userinfo = pads_get_userinfo(session_id)
        try:
            userid = userID=userinfo.UserId
        except Exception as e:
            logger.warning(f"Exception: userinfo is None {e}")
            userid = None
        ocd.save_session(session_id, username=username, userID=userid)

    return ret_val

def pads_logout(session_id):
    ret_val = False
    if session_id is not None:
        full_URL = base + f"/v1/Users/Logout/" + f"?SessionID={session_id}"
        response = requests.post(full_URL, headers={"Content-Type":"application/json"}, json={"UserName":f"{username}", "Password":f"{password}"})
        if response.ok:
            ret_val = True
        else:
            logger.error(f"Error logging out for sessionId: {session_id} from PaDS: {response.json()}")
    else:
        logger.warning("No SessionId supplied.")

    return ret_val

def pads_get_userinfo(session_id):
    ret_val = None
    if session_id is not None:
        full_URL = base + f"/v1/Users" + f"?SessionID={session_id}"
        response = requests.get(full_URL, headers={"Content-Type":"application/json"})
        if response.ok:
            padsinfo = response.json()
            ret_val = models.PadsUserInfo(**padsinfo)
        else:
            logger.error(f"Error getting userinfo for sessionId: {session_id} from PaDS: {response.json()}")
            
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
        ret_val.accessLimitedDescription = opasConfig.ACCESSLIMITED_DESCRIPTION_FREE
        ret_val.accessLimited = False
        ret_val.accessLimitedCurrentContent = False
        #"This content is currently free to all users."
        ret_val.accessLimitedReason = opasConfig.ACCESSLIMITED_DESCRIPTION_FREE
        
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
    
    elif classification in (opasConfig.DOCUMENT_ACCESS_OFFSITE):
        ret_val.accessLimitedDescription = opasConfig.ACCESSLIMITED_DESCRIPTION_OFFSITE
        ret_val.accessLimited = True
        ret_val.accessLimitedCurrentContent = False
        #"This content is currently free to all users."
        ret_val.accessLimitedReason = opasConfig.ACCESS_SUMMARY_DESCRIPTION + opasConfig.ACCESS_SUMMARY_EMBARGOED + publisherAccess # limited...get it elsewhere

    # We COULD check the session_id in PADS here with the art_id and year, for EVERY return!
    #  would it be slow?  Certainly for more than a dozen records, might...this is just for one instance though.
    # print (f"SessionID {session_info.session_id}, classificaton: {ret_val.accessLimited} and client_session: {session_info.api_client_session}")
    try:
        # always check for a full-text request so PaDS can track them.
        if (ret_val.accessLimited == True or fulltext_request == True): # and session_info.api_client_session and session_info.api_client_id in PADS_BASED_CLIENT_IDS:

            if fulltext_request:
                reason_for_check = opasConfig.AUTH_DOCUMENT_VIEW_REQUEST
            else:
                reason_for_check = opasConfig.AUTH_ABSTRACT_VIEW_REQUEST

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
        logger.error(f"Issue checking document permission {e}")
        pass # can't be checked, will be unauthorized.
    
    return ret_val

