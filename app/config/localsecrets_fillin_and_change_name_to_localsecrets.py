
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

TESTUSER = "gvpi"
TESTPW = "fish88"

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

elif CONFIG == "AWSProdAccount": # Codesypher setup, but running from my PC
    API_PORT_MAIN = 9100
    COOKIE_DOMAIN = ".pep-web.rocks" # OR pep-web.rocks when running all from AWS
    BASEURL = "pep-web.rocks"
    SOLRURL = "http://fill-me-in//solr/" # AWS Bitnami server "http://3.17.164.178/solr/" # AWS Codesypher server
    SOLRUSER = "fill-me-in"
    SOLRPW = "fill-me-in"
    DBPORT = 3306
    DBHOST = "localhost"
    DBUSER = "root"
    DBPW = ""
    DBNAME = "opascentral"
    SSH_HOST = None
    API_BINARY_IMAGE_SOURCE_PATH = "/var/pep2021/images"
    API_PDF_ORIGINALS_PATH = "/var/pep2021/downloads/pdfs"

elif CONFIG == "AWSCodesyper": # Codesypher setup, but running from my PC
    API_PORT_MAIN = 9100
    COOKIE_DOMAIN = ".development.org" # OR pep-web.rocks when running all from AWS
    BASEURL = "development.org"
    SOLRURL = "http://3.135.134.136:8983/solr/" # AWS Bitnami server "http://3.17.164.178/solr/" # AWS Codesypher server
    SOLRUSER = "" # bitnami
    SOLRPW = ""
    DBPORT = 3306
    DBHOST = "localhost"
    DBUSER = "root"
    DBPW = ""
    #DBPORT = 3308
    #DBHOST = "3.17.164.178"
    #DBUSER = "fill-me-in"
    #DBPW = "fill-me-in"
    DBNAME = "opascentral"
    SSH_HOST = None
    
elif CONFIG == "AWSTestAccountTunnel":
    import paramiko
    from paramiko import SSHClient
    import sshtunnel
    API_PORT_MAIN = 9100
    # domain running server (.development.org is Neils PC; )
    COOKIE_DOMAIN = ".development.org"
    BASEURL = "development.org"
    SOLRURL = "http://3.91.175.102/solr/" # AWS Bitnami server on my AWS test account (not dev), 
    SOLRUSER = "fill-me-in"                     # need user and password for codesypher server
    SOLRPW = "fill-me-in"
    DBPORT = 3306
    DBHOST = "localhost"
    DBUSER = "fill-me-in"
    DBPW = "fill-me-in"
    DBNAME = "opascentral"
    SSH_HOST = 'ec2-54-161-xxxxxxx.com'
    SSH_USER = 'bitnami'
    SSH_PORT = 22
    PKEYFILE = r"fill-me-in"
    SSH_MYPKEY = paramiko.RSAKey.from_private_key_file(PKEYFILE)
    
elif CONFIG == "Docker":
    API_PORT_MAIN = 9100
    COOKIE_DOMAIN = ".localtest.me"
    BASEURL = "localest.me"
    SOLRURL = "http://localhost:8983/solr/"
    SOLRUSER = None
    SOLRPW = None
    DBHOST = "localhost"
    DBPORT = "3308"
    DBUSER = "pepnrs"
    DBPW = "pep_NRS_opas1_DEV"
    DBNAME = "opascentral"
    SSH_HOST = None
    
elif CONFIG == "LocalDebugRemoteSOLR":
    API_PORT_MAIN = 9100
    COOKIE_DOMAIN = ".development.org"
    BASEURL = "development.org"
    SOLRURL = "http://fill-me-in/solr/" # AWS Bitnami server
    SOLRUSER = "user"
    SOLRPW = "fill-me-in"
    DBHOST = "localhost"
    DBUSER = "root"
    DBPW = ""
    DBNAME = "opascentral"
    SSH_HOST = None
    


# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    import sys
    print ("Running in Python %s" % sys.version_info[0])
   
    import doctest
    doctest.testmod()    
    print ("Tests Completed")