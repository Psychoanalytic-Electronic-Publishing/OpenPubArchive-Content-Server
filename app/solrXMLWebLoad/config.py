# Configuration file for solrXMLWebLoad

# Global variables (for data and instances)
logger = None
bibTotalReferenceCount = 0
options = None

# constants
COMMITLIMIT = 250  # commit the load to Solr every X articles
#SOURCEINFODBFILENAME = 'PEPSourceInfo.json'
DEFAULTDATAROOT = r"X:\\_PEPA1\\_PEPa1v\\"
DEFAULTSOLRHOME = "http://localhost:8983/solr/"

AUTHORCORENAME = "pepwebauthors"
DOCSCORENAME = "pepwebdocs"
REFSCORENAME = "pepwebrefs"
GLOSSARYCORENAME = "pepwebglossary"


