
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = ""
ALGORITHM = "HS256"
url_pads="http://www.psychoanalystdatabase.com/PEPProductLive/PEPProduct.asmx"

import hashlib, binascii, os

# use this to set the active configuration below
CONFIG = "AWSCodesyper"

# Template for local settings, including sensitive info
# These are the defaults, if not overridden below
DEBUG_DOCUMENTS = 1
SOLR_DEBUG = "off"
DBPORT = 3306
API_PORT_MAIN = 9100
SSH_HOST = None # if set, ssh tunnel is active for database
CORS_REGEX = "(.*\.)?(pep\-web|development)\..*"
API_BINARY_IMAGE_SOURCE_PATH = r"./images" # where external images in articles will be found
API_PDF_ORIGINALS_PATH = r"./pdforiginal" # where pdf originals for documents are found for the download feature

# setting config above selects the active configuration
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
    CORS_REGEX = "(.*\.)?(pep\-web|development)\..*"
    
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
    CORS_REGEX = "(.*\.)?(pep\-web|development)\..*"

elif CONFIG == "TunneledRemoteExample":
    import paramiko
    from paramiko import SSHClient
    import sshtunnel # the tunneling is to the db server, not solr
    API_PORT_MAIN = 9100
    # domain running server
    COOKIE_DOMAIN = ".development.org" # . means include any subdomains
    BASEURL = "development.org"
    SOLRURL = "http://3.99.999.999/solr/" # EXAMPLE Solr 
    SOLRUSER = "user"                     # need user and password for codesypher server
    SOLRPW = "fill-me-in"
    DBPORT = 3306
    DBHOST = "localhost" # with tunneling, you are on localhost
    DBUSER = "root"
    DBPW = "fill-me-in"
    DBNAME = "opascentral"
    # if SSH_HOST is not none, then DB will be tunneled to
    SSH_HOST = 'ec2-99-999-999-9.compute-1.amazonaws.com' # made up AWS example
    SSH_USER = "fill-me-in"
    SSH_PORT = 22
    PKEYFILE = "fill-me-in"
    SSH_MYPKEY = paramiko.RSAKey.from_private_key_file(PKEYFILE)
