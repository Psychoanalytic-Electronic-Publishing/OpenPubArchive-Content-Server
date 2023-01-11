from datetime import datetime

CONFIG = "Local"

DEBUG_DOCUMENTS = 1

# OpasDataLoader Definitions
HIGHLIGHT_STOP_WORDS_FILE = r"../config/highlight_stop_words.txt"
DATA_UPDATE_LOG_DIR = "./dataUpdateLogs"

SERVER_START_DATE = datetime.today().strftime('%Y-%m-%d')

# API key configuration
API_KEY = "S!xv>Ev)H$vbzIw"
API_KEY_NAME = "x-api-authorize"
AUTH_KEY_NAME = "x-pep-auth"

# PADS configuration
PADS_BASE_URL = "https://stage-pads.pep-web.org/PEPSecure/api"
PADS_TEST_ID = "padstestid"
PADS_TEST_PW = "padstestpw"
PADS_TEST_ID2 = "padstestid2"
PADS_TEST_PW2 = "padstestidpw2"
PADS_BASED_CLIENT_IDS = [1, 2, ]

# API configuration
BASEURL = "localhost:80"
APIURL = "http://localhost:80"
API_PORT_MAIN = 9100
DATA_SOURCE = f"label for data source"
API_PORT_MAIN = "apiport# (int)"
COOKIE_DOMAIN = ".localhost"

# Solr configuration
SOLR_DEBUG = "on"
SOLRURL = "http://host.docker.internal:8983/solr/"
SOLRUSER = None
SOLRPW = None

# MySQL database configuration
DBHOST = "host.docker.internal"
DBPORT = 3306 # default
DBUSER = "root"
DBPW = "password"
DBVER = 5 # 8.04 and later use different REXP libs (8 implies 8.04 or newer)
DBNAME = "pep_content_server"

# Path configuration
PATH_SEPARATOR = "/"
IMAGE_SOURCE_PATH = r"/app/web-images"
XML_ORIGINALS_PATH = r"/app/xml-originals"
FILESYSTEM_ROOT = XML_ORIGINALS_PATH 
SITEMAP_PATH = r"localpath"
IMAGE_EXPERT_PICKS_PATH = r"/app/expert-picks"
PDF_ORIGINALS_PATH = r"/app/pdf-originals"
XML_CATALOG_NAME = r"localpath"
PDF_ORIGINALS_EXTENSION = ".pdf" #  PDF originals extension

SSH_HOST = None # if set, ssh tunnel is active for database

CORS_ORIGINS = [ "http://localhost:4200", "http://localhost:8200" ]
CORS_REGEX = "^((.*\.)?((.*namesuffx)|name2|name3)(\..*)?)$"

# Allows different API keys depending on location of server
CLIENT_DB = {
    "0": {"api-client-name": "OpenAPI Interactive Docs Interface", "api-client-key" : None},
    "1": {"api-client-name": "pep-easy", "api-client-key": API_KEY},
    "2": {"api-client-name": "pep-web", "api-client-key": API_KEY},
    "3": {"api-client-name": "pads", "api-client-key" : API_KEY},
    "4": {"api-client-name": "unittests", "api-client-key" : None},
    "666": {"api-client-name" : "unknown", "api-client-key" : None},
}