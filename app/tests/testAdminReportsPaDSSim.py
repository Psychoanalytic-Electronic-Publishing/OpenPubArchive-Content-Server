#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import unittest
import time
from pydantic import BaseModel, Field # removed Field, causing an error on AWS
from datetime import datetime
from datetime import date, timedelta

import localsecrets
from localsecrets import AUTH_KEY_NAME, PADS_TEST_ID, PADS_TEST_PW, PADS_TEST_ID2, PADS_TEST_PW2

base_api = "https://stage-api.pep-web.org"
base_api = "http://development2.org:9100"

base = PADS_BASE_URL = "https://stage-pads.pep-web.org/PEPSecure/api"

def base_plus_endpoint_encoded(endpoint, base=base_api):
    ret_val = base + endpoint
    return ret_val

class PadsSessionInfo(BaseModel):
    HasSubscription: bool = Field(False, title="")
    IsValidLogon: bool = Field(False, title="")
    IsValidUserName: bool = Field(False, title="")
    ReasonId: int = Field(0, title="")
    ReasonStr = Field("", title="")
    SessionExpires: int = Field(0, title="Session expires time")
    SessionId: str = Field(None, title="Assigned session ID")
    # added session_started to model, not supplied
    session_start_time: datetime = Field(datetime.now(), title="The time the session was started, not part of the model returned")
    pads_status_response: int = Field(0, title="The status code returned by PaDS, not part of the model returned")

ip = requests.get('https://api.ipify.org').content.decode('utf8')
myTestSystemIP = ip

session_id_from_old_admin_session = "c84c0f30-56c2-4433-b0b5-a11398d6be57"

def fix_pydantic_invalid_nones(response_data, caller_name="DocPermissionsError"):
    try:
        if response_data["ReasonStr"] is None:
            response_data["ReasonStr"] = ""
    except Exception as e:
        print (f"{caller_name}: Exception: {e}")

    return response_data

def authserver_login_simple(username=PADS_TEST_ID,
                            password=PADS_TEST_PW,
                            session_id=None,
                            client_id="4",
                            retry=True):
    """
    Login directly via the auth server (e.g., in this case PaDS)
    """
    print(f"Logging in user {username} with session_id {session_id}")
    if session_id is not None:
        full_URL = base + f"/v1/Authenticate/?SessionId={session_id}"
    else:
        full_URL = base + f"/v1/Authenticate/"

    try:
        pads_response = requests.post(full_URL, headers={"Content-Type":"application/json"}, json={"UserName":f"{username}", "Password":f"{password}"})
        
    except Exception as e:
        msg = f"{caller_name}: Authorization server not available. {e}"
        print (msg)
    else:
        if pads_response.ok:
            pads_response = pads_response.json()
            pads_response = fix_pydantic_invalid_nones(pads_response, caller_name="AuthserverLogin")
            if isinstance(pads_response, str):
                pads_session_info = PadsSessionInfo()
                print (f"{caller_name}: returned error string: {pads_response}")
            else:
                try:
                    pads_session_info = PadsSessionInfo(**pads_response)
                except Exception as e:
                    print (f"{caller_name}: return assignment error: {e}")
                    pads_session_info = PadsSessionInfo()
                
    return pads_session_info

def test_login_padslike(username, password):
    pads_session_info = authserver_login_simple(username=username, password=password)
    sessID = pads_session_info.SessionId
    headers = {f"client-session":f"{sessID}",
               "client-id": "4", 
               "Content-Type":"application/json", 
               "x-forwarded-for-PEP": myTestSystemIP,
               localsecrets.API_KEY_NAME: localsecrets.API_KEY}
    
    # IMPORTANT: Tell the server that the 'user' is logged in.
    if pads_session_info.IsValidLogon == True:
        headers[AUTH_KEY_NAME] = "true"
    return sessID, headers

# Login!
sessID, headers = test_login_padslike(username=PADS_TEST_ID2, password=PADS_TEST_PW2)

class TestReports(unittest.TestCase):
    """
    Note: Test to simulate pads query to server
    """   

    def test_session_log_report_like_pads(self):
        # note api_key is required, but already in headers
        dt = date.today() - timedelta(14)
        print('Current Date :', date.today())
        print('14 days before Current Date :', dt)
        ts = time.time()
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Reports/Session-Log?startdate={dt}&limit=100000&offset=0&download=false&sortorder=asc')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        assert(response.ok == True)
        print (f"Watched: Admin Report Query Complete. Asc Sort.  Time={time.time() - ts}")
        response_info = r["report"]["responseInfo"]
        # response_set = r["report"]["responseSet"]
        print (f'Count Retrieved: {response_info["count"]}')
        assert(response_info["count"] >= 100)
            

if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")