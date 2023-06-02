3#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326

from datetime import datetime

# Time formats (moved to opasConfig)
TIME_FORMAT_STR = '%Y-%m-%dT%H:%M:%SZ'

import sys
sys.path.append(r'E:\usr1\Priv\keys')

# all private information here so localsecrets can be published.
# when using it for your purposes, you can fill in constants directly.
import pepkeys 

# S3 keys
PADS_PRODUCTION_URL = pepkeys.PADS_PRODUCTION_URL

SERVER_START_DATE = datetime.today().strftime('%Y-%m-%d')

# *******************************************************************
# SET CONFIGURATION TO USE HERE!
# Set use_server for the one to use for current server run:
# *******************************************************************
use_server = 1
if use_server == 0:  
    CONFIG = "TestSetup"
elif use_server == 1:   
    CONFIG = "Local"
elif use_server == 2:                        
    CONFIG = "AWSStage" 
    
# *******************************************************************
# *******************************************************************
# defaults
SOLR_DEBUG = "on"
# SSH_HOST = None # if set, ssh tunnel is active for database
CORS_ORIGINS = []
CORS_REGEX = ""

# *******************************************************************
# CONSTANT DEFINITIONS THAT VARY DEPENDING ON CONFIGURATION BELOW
# *******************************************************************

API_KEY_NAME = pepkeys.API_KEY_NAME
API_KEY = pepkeys.API_KEY
AUTH_KEY_NAME = pepkeys.AUTH_KEY_NAME
PADS_TEST_ID = pepkeys.PADS_TEST_ID
PADS_TEST_PW = pepkeys.PADS_TEST_PW
PADS_BASED_CLIENT_IDS = [2, ]
PDF_ORIGINALS_EXTENSION = ".pdf" #  PDF originals extension


if CONFIG == "TestSetup": # 0
    APIDOMAIN = "development.org"
    API_PORT_MAIN = 9100
    SITEMAP_PATH = pepkeys.LOCALDEV_SITEMAP_PATH # r"X:\AWS_S3\AWSProd PEP-Web-Google"
    GOOGLE_METADATA_PATH = pepkeys.LOCALDEV_GOOGLE_METADATA_PATH
    IMAGE_EXPERT_PICKS_PATH = pepkeys.LOCALDEV_IMAGE_EXPERT_PICKS_PATH
    DATA_SOURCE = f"OPAS.Local"                                # arbitrary name used for information from server
    COOKIE_DOMAIN = f".{APIDOMAIN}"
    BASEURL = APIDOMAIN
    APIURL = f"http://{APIDOMAIN}:{9100}"
    SOLRURL = f"http://{APIDOMAIN}:8983/solr/"
    SOLRUSER = None
    SOLRPW = None
    # Local DB
    DBPORT = 3306 # default
    DBHOST = APIDOMAIN
    DBUSER = pepkeys.LOCALDEV_DBUSER
    DBNAME = "opastest3"
    DBPW = pepkeys.LOCALDEV_DBPW
    DBVER = 5 # 8.04 and later use different REXP libs (8 implies 8.04 or newer)
    PADS_BASE_URL = pepkeys.PADS_STAGE_URL
    # must set to None for local paths for flex file system
    S3_KEY = None
    S3_SECRET = None
    # local paths
    IMAGE_SOURCE_PATH = pepkeys.LOCALDEV_IMAGE_SOURCE_PATH # "X:\\AWS_S3\\AWS PEP-Web-Live-Data\\graphics"
    PDF_ORIGINALS_PATH = pepkeys.LOCALDEV_PDF_ORIGINALS_PATH # "X:\\AWS_S3\\AWS PEP-Web-Live-Data\\PEPDownloads"
    # PDF_EXTENDED_FONT_LOCATION = 'E:\\usr3\\GitHub\\openpubarchive\\examples\\Roboto-Regular.ttf'
    XML_ORIGINALS_PATH = pepkeys.LOCALDEV_XML_ORIGINALS_PATH # r"X:\AWS_S3\AWS PEP-Web-Live-Data"
    DATA_UPDATE_LOG_DIR = pepkeys.LOCALDEV_DATA_UPDATE_LOG_DIR # "./dataUpdateLogs"
    FILESYSTEM_ROOT = XML_ORIGINALS_PATH 
    PATH_SEPARATOR = "\\"
    # XML_CATALOG_NAME = LOCALDEV_XML_CATALOG_NAME # "x:/_PEPA1/catalog.xml"

elif CONFIG == "Local": # 1
    APIDOMAIN = "development.org"
    API_PORT_MAIN = 9100
    SITEMAP_PATH = pepkeys.LOCALDEV_SITEMAP_PATH # r"X:\AWS_S3\AWSProd PEP-Web-Google"
    DATA_SOURCE = f"OPAS.Local"                                # arbitrary name used for information from server
    COOKIE_DOMAIN = f".{APIDOMAIN}"
    BASEURL = APIDOMAIN
    APIURL = f"http://{APIDOMAIN}:{9100}"
    SOLRURL = f"http://{APIDOMAIN}:8983/solr/"
    SOLRUSER = None
    SOLRPW = None
    # Local DB
    DBPORT = 3306 # default
    DBHOST = APIDOMAIN
    DBUSER = pepkeys.LOCALDEV_DBUSER
    DBPW = pepkeys.LOCALDEV_DBPW
    DBVER = 5 # 8.04 and later use different REXP libs (8 implies 8.04 or newer)
    DBNAME = "opascentral"
    PADS_BASE_URL = pepkeys.PADS_STAGE_URL
    # must set to None for local paths for flex file system
    S3_KEY = None
    S3_SECRET = None
    # local paths
    GOOGLE_METADATA_PATH = pepkeys.LOCALDEV_GOOGLE_METADATA_PATH
    IMAGE_EXPERT_PICKS_PATH = pepkeys.LOCALDEV_IMAGE_EXPERT_PICKS_PATH
    IMAGE_SOURCE_PATH = pepkeys.LOCALDEV_IMAGE_SOURCE_PATH # "X:\\AWS_S3\\AWS PEP-Web-Live-Data\\graphics"
    PDF_ORIGINALS_PATH = pepkeys.LOCALDEV_PDF_ORIGINALS_PATH # "X:\\AWS_S3\\AWS PEP-Web-Live-Data\\PEPDownloads"
    XML_ORIGINALS_PATH = pepkeys.LOCALDEV_XML_ORIGINALS_PATH # r"X:\AWS_S3\AWS PEP-Web-Live-Data"
    DATA_UPDATE_LOG_DIR = pepkeys.LOCALDEV_DATA_UPDATE_LOG_DIR # "./dataUpdateLogs"
    FILESYSTEM_ROOT = pepkeys.LOCALDEV_FILESYSTEM_ROOT 
    PATH_SEPARATOR = "\\"
    # XML_CATALOG_NAME = LOCALDEV_XML_CATALOG_NAME # "x:/_PEPA1/catalog.xml"

elif CONFIG == "AWSStage": #2
    APIDOMAIN = "localhost"
    API_PORT_MAIN = ""
    DATA_SOURCE = f"OPAS.AWSStage"
    COOKIE_DOMAIN = f".{APIDOMAIN}"
    BASEURL = "pep-web.org"
    APIURL = pepkeys.STAGE_API
    SOLRURL = pepkeys.STAGE_SOLR_URL
    SOLRUSER = pepkeys.REMOTE_SOLRUSER
    SOLRPW = pepkeys.REMOTE_SOLRPW
    IMAGE_SOURCE_PATH = pepkeys.S3_IMAGE_SOURCE_PATH
    PDF_ORIGINALS_PATH = pepkeys.S3_PDF_ORIGINALS_PATH
    XML_ORIGINALS_PATH = pepkeys.S3_XML_ORIGINALS_PATH 
    DATA_UPDATE_LOG_DIR = pepkeys.S3_DATA_UPDATE_LOG_DIR 
    GOOGLE_METADATA_PATH = pepkeys.S3_GOOGLE_METADATA_PATH
    FILESYSTEM_ROOT = pepkeys.S3_FILESYSTEM_ROOT 
    PATH_SEPARATOR = "/"
    PADS_BASE_URL = pepkeys.PADS_STAGE_URL
    #Stage DB   
    DBPORT = 3306
    DBHOST = pepkeys.STAGE_DB_HOST
    DBUSER = pepkeys.AWSDB_USERS[1]
    DBPW = pepkeys.AWSDB_PWS[1]
    DBVER = 8 # 8.04 and later use different REXP libs (8 implies 8.04 or newer)
    DBNAME = "opascentral"
    # XML_CATALOG_NAME = S3_XML_CATALOG_NAME # "pep-web-files/catalog_for_s3.xml" 

# *******************************************************************
# OpasDataLoader Definitions
# *******************************************************************
HIGHLIGHT_STOP_WORDS_FILE = r"../config/highlight_stop_words.txt"

# *******************************************************************
# PEP Specific authentication server (configure to yours for use
# by the Test suite
# *******************************************************************

PADS_TEST_ID = pepkeys.PADS_TEST_ID7
PADS_TEST_PW = pepkeys.PADS_PWS[7]

PADS_TEST_ID2 = pepkeys.PADS_TEST_ID6                     # ID for special reports on State
PADS_TEST_PW2 = pepkeys.PADS_PWS[6]

PADS_TEST_ID4 = pepkeys.PADS_TEST_ID3
PADS_TEST_PW4 = pepkeys.PADS_PWS[3]

PADS_TEST_ARCHIVEONLY = pepkeys.PADS_TEST_ID7              # was Test7, james changed to padstest7 for some reason, now back 2022-06-05
PADS_TEST_ARCHIVEONLY_PW = pepkeys.PADS_PWS[7]
PADS_TEST_IJPOPENONLY = pepkeys.PADS_TEST_ID3
PADS_TEST_IJPOPENONLY_PW = pepkeys.PADS_PWS[3]
PADS_TEST_ARCHIVEANDCURRENT = pepkeys.PADS_TEST_ID4
PADS_TEST_ARCHIVEANDCURRENT_PW = pepkeys.PADS_PWS[4]
PADS_TEST_REGISTEREDUSER = pepkeys.PADS_TEST_ID8
PADS_TEST_REGISTEREDUSER_PW = pepkeys.PADS_PWS[8]

# DEVELOPMENT_DEBUGGING = 1 # commented out the use of this in code (temporary uses)

 
# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    import sys
    print ("Running in Python %s" % sys.version_info[0])    
   
