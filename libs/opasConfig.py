import sys
import logging
import datetime

CONSOLE_DEBUG_MESSAGES_ON = True
CONSOLE_DB_DEBUG_MESSAGES_ON = True

BASELOGFILENAME = "opasAPI"
LOGLEVEL = "DEBUG"
logFilename = BASELOGFILENAME + "_" + datetime.date.today().strftime('%Y-%m-%d') + ".log"
FORMAT = "%(asctime)-15s %(message)s"
logging.basicConfig(filename=logFilename, format=FORMAT,level=logging.INFO,datefmt='%Y-%m-%d %H:%M:%S')

#logger = logging.getLogger(programNameShort)

IMAGES = "images"
HITMARKERSTART = "{{"  # using non html/xml default markers, so we can strip all tags but leave the hitmarkers!
HITMARKEREND = "}}"
HITMARKERSTART_OUTPUTHTML = '<span class="searchhit">'  # to convert the non-markup HIT markers to HTML, supply values here.  These match the current PEPEasy stylesheet.
HITMARKEREND_OUTPUTHTML = "</span>"
    
USER_NOT_LOGGED_IN_ID = 0
    
COOKIE_MIN_KEEP_TIME = 3600  # 1 hour in seconds
COOKIE_MAX_KEEP_TIME = 86400 # 24 hours in seconds

DEFAULT_KWIC_CONTENT_LENGTH = 20  # On each side of match (so use 1/2 of the total you want)
DEFAULT_MAX_KWIC_RETURNS = 5
DEFAULT_LIMIT_FOR_SOLR_RETURNS = 10
DEFAULT_LIMIT_FOR_DOCUMENT_RETURNS = 1
DEFAULT_LIMIT_FOR_WHATS_NEW = 5
DEFAULT_LIMIT_FOR_VOLUME_LISTS = 100
DEFAULT_LIMIT_FOR_CONTENTS_LISTS = 100
DEFAULT_LIMIT_FOR_METADATA_LISTS = 100

SOLR_HIGHLIGHT_RETURN_FRAGMENT_SIZE = 1520000 # to get a complete document from SOLR, with highlights, needs to be large.

# parameter descriptions for documentation
DESCRIPTION_LIMIT = "Number of items to return"
DESCRIPTION_DAYSBACK = "Number of days to look back to assess what's new"
DESCRIPTION_OFFSET = "Start return with this item, referencing the sequence number in the return set (for paging results)"
DESCRIPTION_SOURCECODE = "The 2-8 character assigned PEP Code for source (e.g., APA, CPS, IJP, ANIJP-FR)"
DESCRIPTION_YEAR = "The year for which to return data"
DESCRIPTION_REQUEST = "The request object, passed in automatically by FastAPI"
DESCRIPTION_AUTHORNAMEORPARTIAL = "The author name or a partial name (regex type wildcards [.*] permitted EXCEPT at the end of the string--the system will try that automatically)"
DESCRIPTION_AUTHORNAMEORPARTIALNOWILD = "The author name or a author partial name (prefix, NO WILDCARDS)"
DESCRIPTION_DOCIDORPARTIAL = "The document ID (e.g., IJP.077.0217A) or a partial ID (e.g., IJP.077,  no wildcard) for which to return data"
DESCRIPTION_RETURNFORMATS = "The format of the returned document data.  One of: 'HTML', 'XML', 'TEXTONLY'"
DESCRIPTION_DOCDOWNLOADFORMAT = "The format of the downloaded document data.  One of: 'HTML', 'PDF', 'EPUB'"
DESCRIPTION_SOURCETYPE = "The class of source type for the metadata.  One of: 'Journals', 'Books', 'Videos'"
DESCRIPTION_MOST_CITED_PERIOD = "Look for citations during this Period (5, 10, 20, or all)"
DESCRIPTION_PAGEREQUEST = "The page or page range (from the document's numbering) to return (e.g., 215, or 215-217)"
DESCRIPTION_PAGEOFFSET = "The relative page number (1 is the first) to return"

