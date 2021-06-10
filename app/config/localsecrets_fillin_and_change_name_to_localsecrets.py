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
TIME_FORMAT_STR = '%Y-%m-%dT%H:%M:%SZ'

# set to none if not using S3 (tests check), otherwise set to key
S3_KEY = None
S3_SECRET = None

# Needs to point to a folder anyone (e.g., Google) can read and the API can write to
SITEMAP_PATH = "pep-web-google" # where the app will write the files (e.g., this is an S3 bucket)
SITEMAP_URL = "https://pep-web-google.s3.amazonaws.com/" # sitemap URL address (minus filename) for index

DEBUG_DOCUMENTS = 0
SOLR_DEBUG = "off" 

# setting config above selects the active configuration

API_PORT_MAIN = 9100 # OPAS API Port
COOKIE_DOMAIN = "localhost" # OPAS server domain
BASEURL = "localhost" # OPAS server location
APIURL = "http:/xxx.xxx.com"  # fill in server API, e.g., "https://api.pep-web.rocks"

SOLRURL = "fill-in-solr-url, e.g., http://localhost:8983/solr/"
SOLRUSER = "solr username or Python None if there is no security enabled"
SOLRPW = "fill-in solr password or Python None if there is no security enabled"

DBHOST = "localhost" # DB server address, example: "staging.cxxxxxxxx.us-east-1.rds.amazonaws.com"
DBUSER = "fill-in database username or Python None if there is no security enabled"
DBPORT = 3306
DBPW = "database password or Python None if there is no security enabled"
DBNAME = "opascentral"
# DBVER = 8 # 8.04 and later use different REXP libs (8 implies 8.04 or newer)

IMAGE_SOURCE_PATH = r"fill-me-in path of image/graphic files"
PDF_ORIGINALS_PATH = r"fill-me-in path where original pdfs are stored"
CORS_REGEX = "fill-in" # Example (.*\.)?(localhost|development)\..*"
DATA_SOURCE = "fill in something to identify the data and version" # e.g., f"OPAS.AWSBuild.{SERVER_START_DATE}"

HIGHLIGHT_STOP_WORDS_FILE = r"../config/highlight_stop_words.txt"
IMAGE_SOURCE_PATH = S3_IMAGE_SOURCE_PATH
PDF_ORIGINALS_PATH = S3_PDF_ORIGINALS_PATH
XML_ORIGINALS_PATH = "pep-web-xml"
PATH_SEPARATOR = "/"
PADS_BASE_URL = "fill-in"
DBNAME = "opascentral"
PKEYFILE = r"fill-me-in path of pep file"
xml_catalog_name = "fill-in/catalog_for_s3.xml" 
os.environ['XML_CATALOG_FILES'] = r"file:" + urllib.request.pathname2url(xml_catalog_name)
   
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = "fill-in"
PADS_TEST_ID = "fill-in"
PADS_TEST_PW = "fill-in"
PADS_TEST_ID2 = "fill-in"
PADS_TEST_PW2 = "fill-in"
PADS_BASED_CLIENT_IDS = [2, ]

# added 2021-03-21 to allow copying settings from stage to production
STAGE_DB_HOST = "fill-in.rds.amazonaws.com"
PRODUCTION_DB_HOST = "fill-in.rds.amazonaws.com"
STAGE2PROD_PW = ("fill-in", "fill-in") # (stage pw, prod pw)
STAGE2PROD_USER = ("fill-in", "fill-in")  # (stage user, prod user)

