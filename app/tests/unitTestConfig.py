#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file has the data counts needed for the server tests.

Version: 2020-08-24

"""
import os.path
import sys
import urllib
import requests
import opasDocPermissions

folder = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
if folder == "tests": # testing from within WingIDE, default folder is tests
    sys.path.append('../libs')
    sys.path.append('../config')
    sys.path.append('../../app')
else: # python running from should be within folder app
    sys.path.append('./libs')
    sys.path.append('./config')

# use the configured server.
import localsecrets
from localsecrets import use_server, PADS_TEST_ID, PADS_TEST_PW, APIURL

base_api = APIURL
ALL_SOURCES_COUNT = 189 # OFFSITE doesn't count
# this must be set to the number of unique journals for testing to pass.
JOURNALCOUNT = 77
# this must be set to the exact number of unique books for testing to pass.
BOOKCOUNT = 100 # 100 book in 2020 on PEP-Web including 96 various ZBK, NLP, IPL books, + 4 special books: L&P, SE, GW, Glossary
VIDEOSOURCECOUNT = 12 # Number of video sources (video journal codes)
VIDEOCOUNT = 117 # count as of 2022-03-21
ARTICLE_COUNT = 135632
ARTICLE_COUNT_BJP = 2735 # Right.  2738 in everything with query "BJP (bEXP_ARCH1).xml", but 3 dups.
ARTICLE_COUNT_VOL1_BJP = 49
VOL_COUNT_ALL_JOURNALS = 2482
VOL_COUNT_ALL_BOOKS = 113
VOL_COUNT_ZBK = 72 #  72 including 2 offline books (by Kohut)
VOL_COUNT_AOP = 34
VOL_COUNT_GW = 18
VOL_COUNT_SE = 24
VOL_COUNT_IPL = 22
VOL_COUNT_NLP = 6
VOL_COUNT_IJPSP = 34
VOL_COUNT_PCT = 26
VOL_COUNT_IMAGO = 23
VOL_COUNT_ALL_VOLUMES = 2580 #  journals and videos
VOL_COUNT_VIDEOS = VIDEOSOURCECOUNT # no actual volumes for videos, just the sources
VOL_COUNT_VIDEOS_PEPVS = 4
VOL_COUNT_IJPSP = 11 #  source code ended, 11 should always be correct

ip = requests.get('https://api.ipify.org').content.decode('utf8')
myTestSystemIP = ip

def get_session_info_for_test():
    session_info = opasDocPermissions.get_authserver_session_info(session_id=None, client_id=UNIT_TEST_CLIENT_ID)
    return session_info

def base_plus_endpoint_encoded(endpoint, base=base_api):
    ret_val = base + endpoint
    return ret_val

UNIT_TEST_CLIENT_ID = "4"

# Get session, but not logged in.
def get_headers_not_logged_in(): 
    session_info = opasDocPermissions.get_authserver_session_info(session_id=None,
                                                                  client_id=UNIT_TEST_CLIENT_ID)
    session_id = session_info.session_id
    headers = {f"client-session":f"{session_id}",
               "client-id": UNIT_TEST_CLIENT_ID, 
               "Content-Type":"application/json" 
               }
    return headers

def test_login(username=localsecrets.PADS_TEST_ID, password=localsecrets.PADS_TEST_PW, client_id=UNIT_TEST_CLIENT_ID):
    pads_session_info = opasDocPermissions.authserver_login(username=username, password=password)
    session_info = opasDocPermissions.get_authserver_session_info(pads_session_info.SessionId, client_id=UNIT_TEST_CLIENT_ID, pads_session_info=pads_session_info)
    # Confirm that the request-response cycle completed successfully.
    sessID = session_info.session_id
    headers = {f"client-session":f"{sessID}",
               "client-id": client_id, 
               "Content-Type":"application/json", 
               "x-forwarded-for-PEP": myTestSystemIP,
               localsecrets.API_KEY_NAME: localsecrets.API_KEY}
    if session_info.is_valid_login == True:
        headers[localsecrets.AUTH_KEY_NAME] = "true"
    
    return sessID, headers, session_info

def test_logout(session_id):
    ret_val = opasDocPermissions.authserver_logout(session_id)
    return ret_val

if 0:
    # session_info, pads_session_info = pads_get_session(client_id=UNIT_TEST_CLIENT_ID)
    session_info = opasDocPermissions.get_authserver_session_info(session_id=None, client_id=UNIT_TEST_CLIENT_ID)
    session_id = session_info.session_id
    headers = {"client-session":session_id,
               "client-id": UNIT_TEST_CLIENT_ID,
               "Content-Type":"application/json",
               localsecrets.API_KEY_NAME: localsecrets.API_KEY}


    print (f"unitTestConfig harness fetched session-id {session_id} (not logging in)")
else:
    session_id = None
    if myTestSystemIP is not None:
        headers = {f"client-session":None,
                   "client-id": UNIT_TEST_CLIENT_ID, 
                   "Content-Type":"application/json", 
                   "x-forwarded-for-PEP": myTestSystemIP,
                   localsecrets.API_KEY_NAME: localsecrets.API_KEY}
    else:
        headers = {"client-session":None,
                   "client-id": UNIT_TEST_CLIENT_ID,
                   "Content-Type":"application/json",
                   localsecrets.API_KEY_NAME: localsecrets.API_KEY}
    
def end_test_session(header):
    from opasCentralDBLib import opasCentralDB
    ocd = opasCentralDB()
    ocd.end_session(session_id=headers["client-session"])
    print ("Session End")
