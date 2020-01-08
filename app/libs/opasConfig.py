import sys
import logging
import datetime
import tempfile

BASELOGFILENAME = "opasAPI"
logFilename = BASELOGFILENAME + "_" + datetime.date.today().strftime('%Y-%m-%d') + ".log"
FORMAT = '%(asctime)s %(name)s %(lineno)d - %(levelname)s %(message)s'
logging.basicConfig(filename=logFilename, format=FORMAT, level=logging.WARNING, datefmt='%Y-%m-%d %H:%M:%S')

# These are the solr database names used
SOLR_DOCS = "pepwebdocs"
SOLR_DOCPARAS = "pepwebdocparas"  # For testing workaround for paragraph search
SOLR_REFS = "pepwebrefs"
SOLR_AUTHORS = "pepwebauthors"
SOLR_GLOSSARY = "pepwebglossary" 

# folders, configure per install
# uploads
UPLOAD_DIR = r"z:\\back\\"
XSLT_XMLTOHTML = r"./libs/styles/pepkbd3-html.xslt"
XSLT_XMLTOHTML_ALT = r"../styles/pepkbd3-html.xslt"
CSS_STYLESHEET = r"./libs/styles/pep-html-preview.css"

#logger = logging.getLogger(programNameShort)

IMAGES = "images"
HITMARKERSTART = "#@@@"  # using non html/xml default markers, so we can strip all tags but leave the hitmarkers!
HITMARKEREND = "@@@#"
HITMARKERSTART_OUTPUTHTML = "<span class='searchhit'>"  # to convert the non-markup HIT markers to HTML, supply values here.  These match the current PEPEasy stylesheet.
HITMARKEREND_OUTPUTHTML = "</span>"
      
USER_NOT_LOGGED_IN_ID = 0
    
COOKIE_MIN_KEEP_TIME = 3600  # 1 hour in seconds
COOKIE_MAX_KEEP_TIME = 86400 # 24 hours in seconds
SESSION_INACTIVE_LIMIT = 30  # minutes

# cookies
OPASSESSIONID = "opasSessionID"
OPASACCESSTOKEN = "opasSessionInfo"
OPASEXPIRES= "OpasExpiresTime"

# file classifications (from documents in the Solr database)
DOCUMENT_ACCESS_FREE = "free"
DOCUMENT_ACCESS_EMBARGOED = "current"
DOCUMENT_ACCESS_ARCHIVE = "archive"
DOCUMENT_ACCESS_UNDEFINED = "undefined"
DOCUMENT_ACCESS_OFFSITE = "offsite"

# configure for location where to find the PDF originals
PDFORIGDIR = r"X:\PEP Dropbox\PEPWeb\Inventory\PEPDownloads\PDF"

DEFAULT_KWIC_CONTENT_LENGTH = 200  # On each side of match (so use 1/2 of the total you want)
DEFAULT_MAX_KWIC_RETURNS = 5
DEFAULT_LIMIT_FOR_SOLR_RETURNS = 10
DEFAULT_LIMIT_FOR_DOCUMENT_RETURNS = 1
DEFAULT_LIMIT_FOR_WHATS_NEW = 5
DEFAULT_LIMIT_FOR_VOLUME_LISTS = 100
DEFAULT_LIMIT_FOR_CONTENTS_LISTS = 100
DEFAULT_LIMIT_FOR_METADATA_LISTS = 100

SOLR_HIGHLIGHT_RETURN_FRAGMENT_SIZE = 2520000 # to get a complete document from SOLR, with highlights, needs to be large.  SummaryFields do not have highlighting.

# parameter descriptions for documentation
DESCRIPTION_LIMIT = "Number of items to return"
DESCRIPTION_DAYSBACK = "Number of days to look back to assess what's new"
DESCRIPTION_OFFSET = "Start return with this item, referencing the sequence number in the return set (for paging results)"
DESCRIPTION_PAGELIMIT = "Number of pages of a document to return"
DESCRIPTION_PAGEOFFSET = "Starting page to return for this document as an offset from the first page.)"
DESCRIPTION_SOURCECODE = "The 2-8 character PEP Code for source (of various types, e.g., journals: APA, ANIJP-FR, CPS, IJP, IJPSP, PSYCHE; books: GW, SE, ZBK; videos: PEPGRANTVS, PEPTOPAUTHVS)"
DESCRIPTION_YEAR = "The year for which to return data"
DESCRIPTION_REQUEST = "The request object, passed in automatically by FastAPI"
DESCRIPTION_AUTHORNAMEORPARTIAL = "The author name or a partial name (regex type wildcards [.*] permitted EXCEPT at the end of the string--the system will try that automatically)"
DESCRIPTION_AUTHORNAMEORPARTIALNOWILD = "The author name or a author partial name (prefix)"
DESCRIPTION_DOCIDORPARTIAL = "The document ID (e.g., IJP.077.0217A) or a partial ID (e.g., IJP.077,  no wildcard) for which to return data"
DESCRIPTION_RETURNFORMATS = "The format of the returned abstract and document data.  One of: 'HTML', 'XML', 'TEXTONLY'.  The default is HTML."
DESCRIPTION_DOCDOWNLOADFORMAT = "The format of the downloaded document data.  One of: 'HTML', 'PDF', 'PDFORIG', EPUB'"
DESCRIPTION_SOURCETYPE = "The class of source type for the metadata.  One of: 'Journals', 'Books', 'Videos'"
DESCRIPTION_MOST_CITED_PERIOD = "Look for citations during this Period (5, 10, 20, or all)"
DESCRIPTION_PAGEREQUEST = "The page or page range (from the document's numbering) to return (e.g., 215, or 215-217)"
DESCRIPTION_PAGEOFFSET = "The relative page number (1 is the first) to return"

# temp directory used for generated downloads
TEMPDIRECTORY = tempfile.gettempdir()

