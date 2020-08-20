#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from requests.utils import requote_uri
import urllib
from localsecrets import PADS_TEST_ID, PADS_TEST_PW
base = "https://padstest.zedra.net/PEPSecure/api"

def pads_login(username=PADS_TEST_ID, password=PADS_TEST_PW):
    ret_val = False
    full_URL = base + f"/v1/Authenticate?UserName={username}&Password={password}"
    response = requests.get(full_URL)
    if response.ok == True:
        ret_val = response.json()
    return ret_val
    
def pads_session_check(session_id, doc_id, doc_year):
    ret_val = False
    ret_resp = None
    full_URL = base + f"/v1/Permits?SessionId={session_id}&DocId={doc_id}&DocYear={doc_year}"
    response = requests.get(full_URL)
    if response.ok == True:
        ret_resp = response.json()
        ret_val = ret_resp["Permit"]

    return ret_val, ret_resp      
        

def server_session_check(session_id, doc_id, doc_year):
    ret_val = False
    ret_resp = None
    