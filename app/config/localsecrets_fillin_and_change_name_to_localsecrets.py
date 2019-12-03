
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = ""
ALGORITHM = "HS256"
url_pads="http://www.psychoanalystdatabase.com/PEPProductLive/PEPProduct.asmx"

import hashlib, binascii, os

CONFIG = "AWSCodesyper"
# defaults
DEBUG_DOCUMENTS = 1
DBPORT = 3306 # default
API_PORT_MAIN = 9100
SSH_HOST = None

if CONFIG == "Local":
    API_PORT_MAIN = 9100
    COOKIE_DOMAIN = ".development.org"
    BASEURL = "development.org"
    SOLRURL = "http://localhost:8983/solr/"
    SOLRUSER = None
    SOLRPW = None
    DBHOST = "localhost"
    DBUSER = "fill-me-in"
    DBPW = "fill-me-in"
    DBNAME = "opascentral"
    API_BINARY_IMAGE_SOURCE_PATH = r"fill-me-in"
    API_PDF_ORIGINALS_PATH = r"fill-me-in"

elif CONFIG == "AWSCodesyper": # Codesypher setup, but running from my PC
    API_PORT_MAIN = 9100
    COOKIE_DOMAIN = ".pep-web.rocks" # OR pep-web.rocks when running all from AWS
    BASEURL = "pep-web.rocks"
    SOLRURL = "http://3.135.134.136:8983/solr/" 
    SOLRUSER = "pep_user"
    SOLRPW = None
    DBPORT = 3308
    DBHOST = "3.135.134.136"
    DBUSER = "fill-me-in"
    DBPW = "fill-me-in"
    DBNAME = "opascentral"
    SSH_HOST = None
    API_BINARY_IMAGE_SOURCE_PATH = r"fill-me-in"
    API_PDF_ORIGINALS_PATH = r"fill-me-in"

