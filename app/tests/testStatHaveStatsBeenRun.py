#!/usr/bin/env python
# -*- coding: utf-8 -*-

from localsecrets import PADS_TEST_ID, PADS_TEST_PW

import unittest
import requests
import opasConfig
import sys
from datetime import datetime

from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, test_login

# Login!
sessID, headers, session_info = test_login()


class testPEPStatHaveStatsBeenRun(unittest.TestCase):
    # have stats been run?
    print (f"Running: {sys._getframe(  ).f_code.co_name} at {datetime.now()}")
    full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/')
    response = requests.get(full_URL, headers=headers)
    # Confirm that the request-response cycle completed successfully.
    assert(response.ok == True)
    r = response.json()
    print ("Checking if stats have been run")
    # print (r)
    print (f"Count: {r['documentList']['responseInfo']['count']}")
    print (f"Limit: {r['documentList']['responseInfo']['limit']}")
    assert r['documentList']['responseSet'][0]['stat']['art_cited_5'] >= 15, 0       
    print ("OK")
