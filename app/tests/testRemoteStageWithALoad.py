#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant
#2022.1026 # Reset queries and amounts for smaller test/distrib database, still trying to cover as much as possibly query wise.  PEP Test version still broader.

import unittest
import time
import requests
from unitTestConfig import base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, test_login
APIDOMAIN = "pep-web.org"
DATA_UPDATE_LOG_DIR = "./dataUpdateLogs"
DATA_SOURCE = f"OPAS.AWSStage"
COOKIE_DOMAIN = f".{APIDOMAIN}"
BASEURL = "pep-web.org"
APIURL = "https://stage-api.pep-web.org"
#SOLRURL = STAGE_SOLR_URL
#SOLRUSER = REMOTE_SOLRUSER
#SOLRPW = DEF_SOLRPW

import logging
logger = logging.getLogger(__name__)

from localsecrets import PADS_TEST_ID2, PADS_TEST_PW2
base = APIURL

# Login!
sessID, headers, session_info = test_login(username=PADS_TEST_ID2, password=PADS_TEST_PW2)

# List of URLs to test
urls = [
    "https://stage.pep-web.org",
    "https://stage.pep-web.org/search?facets=&q=hazy%20feelings%20AND%20sadness",
    "https://stage.pep-web.org/browse/document/IJP.096.1213A?page=P1219",
    "https://stage.pep-web.org/browse/document/IJP.096.0319A?page=P0325",
    "https://stage.pep-web.org/search?citedCount=&facets=%5B%5D&matchSynonyms=false&openNotificationModal=false&q=psychoanalysis&viewedCount=&viewedPeriod=1", 
    "https://stage.pep-web.org/search/document/PPSY.034.0221A?q=psychoanalysis", 
    "https://stage.pep-web.org/search/document/SPR.037.0113A?q=psychoanalysis", 
    "https://stage.pep-web.org/search?citedCount=&facets=%5B%5D&matchSynonyms=false&openNotificationModal=false&q=Peer%20Gynt&viewedCount=&viewedPeriod=1", 
    "https://stage.pep-web.org/search/document/SPR.010.0117A?page=P0117&q=Peer%20Gynt", 
    'https://stage.pep-web.org/search/document/BJP.019.0151A?index=40&page=P0117&searchTerms=%5B%7B"term"%3A"Jean%20Arundale"%2C"type"%3A"author"%2C"value"%3A"Jean%20Arundale"%7D%5D', 
    'https://stage.pep-web.org/search?citedCount=&facets=%5B%5D&matchSynonyms=false&openNotificationModal=false&q=&searchTerms=%5B%7B"term"%3A"Jean%20Arundale"%2C"type"%3A"author"%2C"value"%3A"Jean%20Arundale"%7D%5D&viewedCount=&viewedPeriod=1', 
    'https://stage.pep-web.org/search/document/BJP.011.0388A?searchTerms=%5B%7B"term"%3A"Jean%20Arundale"%2C"type"%3A"author"%2C"value"%3A"Jean%20Arundale"%7D%5D', 
    'https://stage.pep-web.org/browse/BJP/volumes?openNotificationModal=false', 
    'https://stage.pep-web.org/browse/BJP/volumes/18', 
    'https://stage.pep-web.org/browse/document/BJP.018.0134A?index=40&page=P0134', 
    'https://stage.pep-web.org/browse/document/BJP.018.0367A?index=40&page=P0367',
    'https://stage.pep-web.org/browse/document/BJP.018.0563A?index=40&page=P0563',
    'https://stage.pep-web.org/search?citedCount=&facets=%5B%5D&matchSynonyms=false&openNotificationModal=false&q=&searchTerms=%5B%7B"term"%3A"Elizabeth%20Reddish"%2C"type"%3A"author"%2C"value"%3A"Elizabeth%20Reddish"%7D%5D&viewedCount=&viewedPeriod=1',
    'https://stage.pep-web.org/search/document/BJP.018.0563A?searchTerms=%5B%7B"term"%3A"Elizabeth%20Reddish"%2C"type"%3A"author"%2C"value"%3A"Elizabeth%20Reddish"%7D%5D',
    'https://stage.pep-web.org/browse/BJP/volumes/18?openNotificationModal=false',
    'https://stage.pep-web.org/browse/IFP/volumes', 
    'https://stage.pep-web.org/browse/CFP/volumes', 
    'https://stage.pep-web.org/browse/BAFC/volumes', 
    'https://stage.pep-web.org/browse/BAFC/volumes/15', 
    'https://stage.pep-web.org/browse/OEDA/volumes', 
    'https://stage.pep-web.org/browse/PAQ/volumes', 
    'https://stage.pep-web.org/browse/ZPSAP/volumes', 
    'https://stage.pep-web.org/browse/document/IJP.041.0585A?page=P0585', 
    'https://stage.pep-web.org/browse/document/IJP.034.0089A', 
    'https://stage.pep-web.org/search?citedCount=&facets=%5B%5D&matchSynonyms=false&openNotificationModal=false&q=&searchTerms=%5B%7B"term"%3A"D.%20Winnicott"%2C"type"%3A"author"%2C"value"%3A"D.%20Winnicott"%7D%5D&viewedCount=&viewedPeriod=1', 
    'https://stage.pep-web.org/browse', 
    'https://stage.pep-web.org/browse/book/se', 
    'https://stage.pep-web.org/browse/document/SE.002.0000A?page=PR0004', 
    'https://stage.pep-web.org/browse/AIM/volumes/79', 
    'https://stage.pep-web.org/browse/document/AIM.079.0137A',    
]

# Loop through each URL and send a GET request
for url in urls:
    response = requests.get(url, headers=headers, cookies={"session_id": sessID})
    time.sleep(0.75)
    
    # Print the response status code and content
    print(f"URL: {url} - Status Code: {response.status_code}")
    print(response.content)