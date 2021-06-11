#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326

import os
import urllib.request
from datetime import datetime

# *******************************************************************
# OpasDataLoader Definitions
# *******************************************************************
HIGHLIGHT_STOP_WORDS_FILE = r"../config/highlight_stop_words.txt"
DATA_UPDATE_LOG_DIR = "./dataUpdateLogs"

# Time formats
TIME_FORMAT_STR = '%Y-%m-%dT%H:%M:%SZ'

# *******************************************************************
# OPAS Definitions Re-used in various places below
# *******************************************************************
# URLS that change when we rebuild
STAGE_SOLR_URL = "http://..."
PRODUCTION_SOLR_URL = "http://..."
DEVELOPMENT_SOLR_URL = "http://..."

# added 2021-03-21 to allow copying settings from stage to production
STAGE_DB_HOST = ""
PRODUCTION_DB_HOST = ""
STAGE2PROD_PW = ("stagepw", "prodpw")
STAGE2PROD_USER = ("stageuser", "produser")

SERVER_START_DATE = datetime.today().strftime('%Y-%m-%d')

# *******************************************************************
# SET CONFIGURATION TO USE HERE!
# Three configs now of importance.  
# Set use_server for the one to use for current server run:
# *******************************************************************
use_server = 0
if use_server == 0:   # http://development.org
    CONFIG = "Local"
elif use_server == 1: # http://23.21.145.16/solr
    CONFIG = "Development"
elif use_server == 2:  
    CONFIG = "Stage" 
elif use_server == 3:  
    CONFIG = "Production" 

PADS_TEST_ID = "padstestid"
PADS_TEST_PW = "padstestpw"
PADS_TEST_ID2 = "padstestid2"
PADS_TEST_PW2 = "padstestidpw2"
PADS_BASED_CLIENT_IDS = [1, 2, ]

API_KEY = "apikey"
API_KEY_NAME = "apikeyname"

# Allows different APIs depending on location of server
CLIENT_DB = {
    "0": {"api-client0-name": "descriptive", "api-client-key" : None},
    "1": {"api-client1-name": "descriptive", "api-client-key": API_KEY},
    "2": {"api-client2-name": "descriptive", "api-client-key": API_KEY},
    "3": {"api-client3-name": "descriptive", "api-client-key" : API_KEY},
    "666": {"api-client-name" : "unknown", "api-client-key" : None},
}


# *******************************************************************
# *******************************************************************
# defaults
DEBUG_DOCUMENTS = 1
DEBUG_TRACE = 1
SOLR_DEBUG = "on"
DBPORT = 3306 # default
API_PORT_MAIN = 9100
SSH_HOST = None # if set, ssh tunnel is active for database
CORS_ORIGINS = [ "http://...", "http://localhost:8200" ]
CORS_REGEX = "^((.*\.)?((.*namesuffx)|name2|name3)(\..*)?)$"
IMAGE_SOURCE_PATH = None
PDF_ORIGINALS_PATH = None
PDF_ORIGINALS_EXTENSION = ".pdf" #  PDF originals extension
XML_ORIGINALS_PATH = None

# Allows different APIs depending on location of server
CLIENT_DB = {
    "0": {"api-client-name": "OpenAPI Interactive Docs Interface", "api-client-key" : None},
    "1": {"api-client-name": "pep-easy", "api-client-key": API_KEY},
    "2": {"api-client-name": "pep-web", "api-client-key": API_KEY},
    "3": {"api-client-name": "pads", "api-client-key" : API_KEY},
    "4": {"api-client-name": "unittests", "api-client-key" : None},
    "666": {"api-client-name" : "unknown", "api-client-key" : None},
}

# *******************************************************************
# *******************************************************************
# defaults
DEBUG_DOCUMENTS = 1
DEBUG_TRACE = 1
SOLR_DEBUG = "on"
DBPORT = 3306 # default
API_PORT_MAIN = 9100
SSH_HOST = None # if set, ssh tunnel is active for database
CORS_ORIGINS = [ "", "" ]
CORS_REGEX = "^((.*\.)?((orig1|orig2)(\..*)?)$"
IMAGE_SOURCE_PATH = None
PDF_ORIGINALS_PATH = None
PDF_ORIGINALS_EXTENSION = ".pdf" #  PDF originals extension
XML_ORIGINALS_PATH = None

S3_KEY = None
S3_SECRET = None

# OTHER IPs used in multiple places
S3_PDF_ORIGINALS_PATH = "path/pdforiginals"
S3_IMAGE_SOURCE_PATH = "path/doc/g"
S3_IMAGE_EXPERT_PICKS_PATH = "path"

# added 2021-03-22 for sitemap feature
# Needs to point to a folder anyone (e.g., Google) can read and the API can write to
SITEMAP_PATH = "xyz-google" # where the app will write the files (e.g., this is an S3 bucket)
SITEMAP_URL = "https://.../" # sitemap URL address (minus filename) for index

# *******************************************************************
# CONSTANT DEFINITIONS THAT VARY DEPENDING ON CONFIGURATION BELOW
# *******************************************************************
if CONFIG == "Local":
    # config specific constants
    SITEMAP_PATH = r"localpath"
    IMAGE_EXPERT_PICKS_PATH = r"path"
    DATA_SOURCE = f"label for data source"
    API_PORT_MAIN = "apiport# (int)"
    COOKIE_DOMAIN = ".blah.org"
    BASEURL = "blah.org:9100"
    APIURL = "http://blah.org:9100"
    SOLRURL = "http://localhost:8983/solr/"
    SOLRUSER = None
    SOLRPW = None
    DBHOST = ""
    DBUSER = ""
    DBPW = ""
    DBVER = 5 # 8.04 and later use different REXP libs (8 implies 8.04 or newer)
    DBNAME = "opascentral"
    PADS_BASE_URL = "https://..."
    IMAGE_SOURCE_PATH = r"localpath"
    PDF_ORIGINALS_PATH = r"localpath"
    XML_ORIGINALS_PATH = r"localpath"
    PATH_SEPARATOR = "\\"
    XML_CATALOG_NAME = r"localpath"
    
elif CONFIG == "Production":
    # as local above, but site specific defs
    DATA_SOURCE = f"OPAS.AWSStage.{SERVER_START_DATE}"
    API_PORT_MAIN = "apiport# (int)"
    COOKIE_DOMAIN = ".blah.org"
    BASEURL = "blah.org:9100"
    APIURL = "https://stage-api.pep-web.rocks"
    SOLRURL = STAGE_SOLR_URL
    SOLRUSER = "solr username or Python None if there is no security enabled"
    SOLRPW = "fill-in solr password or Python None if there is no security enabled"
    HIGHLIGHT_STOP_WORDS_FILE = r"../config/highlight_stop_words.txt"
    IMAGE_SOURCE_PATH = r"fill-me-in path of image/graphic files"
    PDF_ORIGINALS_PATH = r"fill-me-in path where original pdfs are stored"
    CORS_REGEX = "fill-in" # Example (.*\.)?(localhost|development)\..*"
    DATA_SOURCE = "fill in something to identify the data and version" # e.g., f"OPAS.AWSBuild.{SERVER_START_DATE}"
    S3_KEY = "if applicable"
    S3_SECRET = "if applicable"    
    PADS_BASE_URL = "https://..." # security/auth server
    DBHOST = "localhost" # DB server address, example: "staging.cxxxxxxxx.us-east-1.rds.amazonaws.com"
    DBUSER = "fill-in database username or Python None if there is no security enabled"
    DBPORT = 3306
    DBPW = "database password or Python None if there is no security enabled"
    DBNAME = "database name"
    DBVER = 8 # 8.04 and later use different REXP libs (8 implies 8.04 or newer)
    XML_CATALOG_NAME =  r"path" 
    os.environ['XML_CATALOG_FILES'] = r"file:" + urllib.request.pathname2url(xml_catalog_name)
    PATH_SEPARATOR = "/"
       

