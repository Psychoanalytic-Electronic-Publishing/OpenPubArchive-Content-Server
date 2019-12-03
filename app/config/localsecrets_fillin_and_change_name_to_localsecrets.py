
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = "cc0ef5c4a8304cf790314247d9ced266f54818e0e7cf55f4d9c3937e6ae75317"
ALGORITHM = "HS256"
url_pads="http://www.psychoanalystdatabase.com/PEPProductLive/PEPProduct.asmx"
soapTest = """<?xml version="1.0" encoding="utf-8"?>
              <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
                <soap12:Body>
                  <AuthenticateUserAndReturnExtraInfo xmlns="http://localhost/PEPProduct/PEPProduct">
                      <UserName>neilshapironet</UserName>
                      <Password>pepEasy</Password>
                  </AuthenticateUserAndReturnExtraInfo>                
                </soap12:Body>
            </soap12:Envelope>
"""
import hashlib, binascii, os

CONFIG = "AWSProdAccount"
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
    DBUSER = "root"
    DBPW = ""
    DBNAME = "opascentral"
    API_BINARY_IMAGE_SOURCE_PATH = r"X:\_PEPA1\g"
    API_PDF_ORIGINALS_PATH = r"X:\_Inventory\PEPDownloads\PDF"

elif CONFIG == "AWSProdAccount": # Codesypher setup, but running from my PC
    API_PORT_MAIN = 9100
    COOKIE_DOMAIN = ".pep-web.rocks" # OR pep-web.rocks when running all from AWS
    BASEURL = "pep-web.rocks"
    SOLRURL = "http://3.133.142.119//solr/" # AWS Bitnami server "http://3.17.164.178/solr/" # AWS Codesypher server
    SOLRUSER = "user"
    SOLRPW = "njoWJTX0Rz1h"
    DBPORT = 3306
    DBHOST = "localhost"
    DBUSER = "root"
    DBPW = ""
    DBNAME = "opascentral"
    SSH_HOST = None
    API_BINARY_IMAGE_SOURCE_PATH = "/var/pep2021/images"
    API_PDF_ORIGINALS_PATH = "/var/pep2021/downloads/pdfs"

elif CONFIG == "AWSDevAccount": # Codesypher setup, but running from my PC
    API_PORT_MAIN = 9100
    COOKIE_DOMAIN = ".development.org" # OR pep-web.rocks when running all from AWS
    BASEURL = "development.org"
    SOLRURL = "http://3.91.175.102/solr/" # AWS Bitnami server "http://3.17.164.178/solr/" # AWS Codesypher server
    #SOLRUSER = "pep_user"
    #SOLRPW = "kP6G9NrRD1NC"
    SOLRUSER = "user" # bitnami
    SOLRPW = "kP6G9NrRD1NC"
    DBPORT = 3308
    DBHOST = "3.17.164.178"
    DBUSER = "pep_user"
    DBPW = "peppass2"
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
    SOLRUSER = "user"                     # need user and password for codesypher server
    SOLRPW = "kP6G9NrRD1NC"
    DBPORT = 3306
    DBHOST = "localhost"
    DBUSER = "root"
    DBPW = "aNPO1W8FbKNf"
    DBNAME = "opascentral"
    SSH_HOST = 'ec2-54-161-129-5.compute-1.amazonaws.com'
    SSH_USER = 'bitnami'
    SSH_PORT = 22
    PKEYFILE = r"E:\usr1\Priv\keys\bitnami-aws-561476741418.pem"
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
    SOLRURL = "http://3.84.131.58/solr/" # AWS Bitnami server
    SOLRUSER = "user"
    SOLRPW = "2z0SZPQZUKNG"
    DBHOST = "localhost"
    DBUSER = "root"
    DBPW = ""
    DBNAME = "opascentral"
    SSH_HOST = None
    
elif CONFIG == "LocalDebugRemoteMySQL":
    API_PORT_MAIN = 9100
    COOKIE_DOMAIN = ".development.org"
    BASEURL = "development.org"
    SOLRURL = "http://localhost:8983/solr/"
    SOLRUSER = None
    SOLRPW = None
    DBHOST = "web624.webfaction.com"
    DBUSER = "nrshapiro_pep"
    DBPW = "free2009"
    DBNAME = "opascentral"
    SSH_HOST = None
    
elif CONFIG == "Webfaction":
    API_PORT_MAIN = 9100
    COOKIE_DOMAIN = ".pep-web.info"
    BASEURL = "pep-web.info"
    SOLRURL = "http://3.84.131.58/solr/" # AWS Bitnami server
    SOLRUSER = "user"
    SOLRPW = "2z0SZPQZUKNG"
    DBHOST = "web624.webfaction.com"
    DBUSER = "nrshapiro_pep"
    DBPW = "free2009"
    DBNAME = "opascentral"
    SSH_HOST = None
    
elif CONFIG == "WebfactionLocal":
    API_PORT_MAIN = 9100
    COOKIE_DOMAIN = ".development.org"
    BASEURL = "development.org"
    SOLRURL = "http://3.84.131.58/solr/" # AWS Bitnami server
    SOLRUSER = "user"
    SOLRPW = "2z0SZPQZUKNG"
    DBHOST = "localhost"
    DBUSER = "nrshapiro_pep"
    DBPW = "free2009"
    DBNAME = "opascentral"
    SSH_HOST = None
    
elif CONFIG == "RemoteSolr":
    API_PORT_MAIN = 9100
    COOKIE_DOMAIN = ".development.org"
    BASEURL = "development.org"
    SOLRURL = "http://3.84.131.58/solr/" # AWS Bitnami server
    SOLRUSER = "user"
    SOLRPW = "2z0SZPQZUKNG"
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