# Configuration file for solrXMLWebLoad

# Global variables (for data and instances)
logger = None
bibTotalReferenceCount = 0
options = None

# constants
COMMITLIMIT = 2500  # commit the load to Solr every X articles
#SOURCEINFODBFILENAME = 'PEPSourceInfo.json'
DEFAULTDATAROOT = r"C:\solr-8.0.0\server\solr\pepwebproto\sampledata\_PEPA1"
DEFAULTSOLRHOME = "http://localhost:8983/solr/"

AUTHORCORENAME = "pepwebauthors"
DOCSCORENAME = "pepwebdocs"
REFSCORENAME = "pepwebrefs"
GLOSSARYCORENAME = "pepwebglossary"

DBPORT = 3306
DBHOST = "localhost"
DBUSER = "root"
DBPW = ""
DBNAME = "opascentral"
