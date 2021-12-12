#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger()

import unittest
import requests
import localsecrets
import tempfile
import opasDocPermissions
import models

from localsecrets import API_KEY_NAME, AUTH_KEY_NAME, API_KEY, PADS_TEST_ID, PADS_TEST_PW, \
                         PDF_ORIGINALS_PATH, PADS_BASED_CLIENT_IDS, use_server, PADS_BASE_URL
from unitTestConfig import base_plus_endpoint_encoded, headers, test_login

base = PADS_BASE_URL

# Login!
sessID, headers, session_info = test_login(username=localsecrets.PADS_TEST_ID2, password=localsecrets.PADS_TEST_PW2)
    
class TestPaDSCalls(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.

    Note the endpoint returns a sitemap index
          <sitemap>
              <loc>https://pep-web-google.s3.amazonaws.com/X:\\AWS_S3\\AWSProd PEP-Web-Google/sitemap1.xml</loc>
              <lastmod>2021-05-18T09:07:17</lastmod>
           </sitemap>

           <sitemap>
              <loc>https://pep-web-google.s3.amazonaws.com/X:\\AWS_S3\\AWSProd PEP-Web-Google/sitemap2.xml</loc>
              <lastmod>2021-05-18T09:07:17</lastmod>
           </sitemap>
           
           ...
    """   

    def test00_test_users(self): # get_authserver_session_userinfo
        if use_server == 0:
            for count in range(1, 5):
                username = f"test{count}"  # userinfo["username"]
                password = PADS_TEST_PW
                
                full_URL = base + f"/v1/Authenticate/"
                pads_response = requests.post(full_URL, headers={"Content-Type":"application/json"}, json={"UserName":f"{username}", "Password":f"{password}"})
                status_code = pads_response.status_code # save it for a bit (we replace pads_session_info below)
                if pads_response.ok:
                    pads_response = pads_response.json()
                    pads_response = opasDocPermissions.fix_pydantic_invalid_nones(pads_response, caller_name="Test")
                    if isinstance(pads_response, str):
                        pads_session_info = models.PadsSessionInfo()
                        logger.error(f"{caller_name}: returned error string: {pads_response}")
                    else:
                        try:
                            pads_session_info = models.PadsSessionInfo(**pads_response)
                        except Exception as e:
                            logger.error(f"{caller_name}: return assignment error: {e}")
                            pads_session_info = models.PadsSessionInfo()
                    session_id = pads_session_info.SessionId
                    full_URL = base + f"/v1/Users" + f"?SessionID={session_id}"
                    pads_user_response = requests.get(full_URL, headers={"Content-Type":"application/json"}) # Call PaDS
                    pads_user_info = pads_user_response.json()

    
                    print (pads_user_info)
                    assert pads_user_info["UserName"].upper() == username.upper()
                
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")
    