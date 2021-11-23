# import sys
import logging
#import datetime
import tempfile
import os
import os.path
from pathlib import Path
import re
import urllib.parse
from urllib.parse import urlparse
import string

from schemaMap import PREDEFINED_SORTS
import localsecrets
import opasFileSupport

TIME_FORMAT_STR = '%Y-%m-%dT%H:%M:%SZ'

# To test idea for limiting access calls
LIMIT_TEST_DO_THIS = True
LIMIT_TEST_DONT_DO_THIS = False

#import urllib.request
# from enum import Enum, EnumMeta, IntEnum

# count_anchors = 0 # define here so it can be used globally across modules

# Share httpCodes definition with all OPAS modules that need it.  Starlette provides the symbolic declarations for us.
import starlette.status as httpCodes # HTTP_ codes, e.g.
                                     # HTTP_200_OK, \
                                     # HTTP_400_BAD_REQUEST, \
                                     # HTTP_401_UNAUTHORIZED, \
                                     # HTTP_403_FORBIDDEN, \
                                     # HTTP_404_NOT_FOUND, \
                                     # HTTP_500_INTERNAL_SERVER_ERROR, \
                                     # HTTP_503_SERVICE_UNAVAILABLE
 
# BASELOGFILENAME = "opasAPI"
# logFilename = BASELOGFILENAME + "_" + datetime.date.today().strftime('%Y-%m-%d') + ".log"
FORMAT = '%(asctime)s %(name)s/%(funcName)s(%(lineno)d): %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.WARNING, datefmt='%Y-%m-%d %H:%M:%S')
LOG_CALL_TIMING = True
LOCAL_TRACE = False                   # turn this on to see the queries easily.
LOCAL_DBOPEN_TRACE = False            # show open/close db in init/del

# General books
BOOKSOURCECODE = "ZBK" #  books are listed under this source code, e.g., to make for an id of ZBK.052.0001
BOOK_CODES_ALL = ("GW", "SE", "ZBK", "NLP", "IPL")
VIDEOSTREAM_CODES_ALL = ("AFCVS", "BPSIVS", "IJPVS", "IPSAVS", "NYPSIVS", "PCVS", "PEPGRANTVS", "PEPTOPAUTHVS", "PEPVS", "SFCPVS", "SPIVS", "UCLVS")
ALL_EXCEPT_JOURNAL_CODES = BOOK_CODES_ALL + VIDEOSTREAM_CODES_ALL

# Note: language symbols to be lower case (will be converted to lowercase if not)
DEFAULT_DATA_LANGUAGE_ENCODING = "en"
CLIENT_CONFIGS = ("common", "en-us", "es-es", "fr-fr", "de-de", "it-it")
EXPERT_PICK_IMAGE_FILENAME_READ_LIMIT = 13000 # lower numbers are faster, but don't read the last n files before making a random selection
# paths vary because they depend on module location; solrXMLWebLoad needs a different path than the server
# should do this better...later.
GAVANTXSLT = False
STYLE_PATH = r"./libs/styles;../libs/styles"
if not GAVANTXSLT:
    XSLT_XMLTOHTML = r"pepkbd3-html.xslt"
else:
    XSLT_XMLTOHTML = r"xmlToHtml2021.xslt"                                      # used for dynamic conversion to HTML; trying to update 2021-06-03 
                                                                                # with Gavant improvements, *** but not working here 2021-06-05 yet ****
                                                                                # but needed the doctype code back in and lots of other fixes including params
    
XSLT_XMLTOTEXT_EXCERPT = r"pepkbd3-abstract-text.xslt"
XSLT_XMLTOHTML_EXCERPT = r"pepkbd3-abstract-html.xslt"                       # used for load only
XSLT_XMLTOHTML_GLOSSARY_EXCERPT = r"pepkbd3-glossary-excerpt-html.xslt" 
TRANSFORMER_XMLTOHTML = "XML_TO_HTML"                                        # used for dynamic conversion to HTML (maps to XSLT_XMLTOHTML)
TRANSFORMER_XMLTOHTML_EXCERPT = "EXCERPT_HTML"                               # used for TOC instances on load (maps to XSLT_XMLTOHTML_EXCERPT)
TRANSFORMER_XMLTOTEXT_EXCERPT = "EXCERPT_TEXT"                               # NOT CURRENTLY USED in OPAS (2020-09-14)
TRANSFORMER_XMLTOHTML_GLOSSARY_EXCERPT = "EXCERPT_GLOSSARY"                  # NOT CURRENTLY USED in OPAS (2020-09-14)

CSS_STYLESHEET = r"./libs/styles/pep-html-preview.css"
MAX_RECORDS_FOR_ACCESS_INFO_RETURN = 100

# Special xpaths and attributes for data handling in solrXMLPEPWebLoad
ARTINFO_ARTTYPE_TOC_INSTANCE = "TOC" # the whole instance is a TOC ()
GLOSSARY_TOC_INSTANCE = "ZBK.069.0000A" # Main TOC entry
# XML_XPATH_SUMMARIES = "//summaries"
# XML_XPATH_ABSTRACT = "//abs"

# XPaths for special data handling
# HTML Paths
# Detect an instance which is a TOC, e.g., GW.001.0000A
HTML_XPATH_TOC_INSTANCE = "//div[@data-arttype='TOC']" 
HTML_XPATH_DOC_BODY = "//div[@class='body']" # used, for example, to extract the body from the html
HTML_XPATH_ABSTRACT = "//div[@id='abs']"  # used, for example, to extract the abstract from the HTML

# API URLs used for linking
API_URL_DOCUMENTURL = "/v2/Documents/"

#logger = logging.getLogger(programNameShort)

MAX_WHATSNEW_ARTICLES_TO_CONSIDER = 1000

IMAGES = "v2/Documents/Image" # from endpoint; was just images, e.g., "http://pep-web.org/images/bannerADPSALogo.gif
HITMARKERSTART = "#@@@"  # using non html/xml default markers, so we can strip all tags but leave the hitmarkers!
HITMARKEREND = "@@@#"
HITMARKERSTART_OUTPUTHTML = "<span class='searchhit'>"  # to convert the non-markup HIT markers to HTML, supply values here.  These match the current PEPEasy stylesheet.
HITMARKEREND_OUTPUTHTML = "</span>"
      
USER_NOT_LOGGED_IN_ID = 0
USER_NOT_LOGGED_IN_NAME = "NotLoggedIn"
NO_CLIENT_ID = 666
NO_SESSION_ID = "NO-SESSION-ID"
    
COOKIE_MIN_KEEP_TIME = 3600  # 1 hour in seconds
COOKIE_MAX_KEEP_TIME = 86400 # 24 hours in seconds
SESSION_INACTIVE_LIMIT = 30  # minutes

# cookies
OPASSESSIONID = "opasSessionID"
OPASACCESSTOKEN = "opasSessionInfo"
OPASEXPIRES= "OpasExpiresTime"
CLIENTID = "client-id" # also header param or qparam
CLIENTSESSIONID = "client-session" # also header param or qparam
X_FORWARDED_FOR = "X-Forwarded-For-PEP"

AUTH_DOCUMENT_VIEW_REQUEST = "DocumentView"
AUTH_ABSTRACT_VIEW_REQUEST = "AbstractView"

# file classifications (from documents in the Solr database)
DOCUMENT_ACCESS_FREE = "free"
DOCUMENT_ACCESS_CURRENT = "current"
DOCUMENT_ACCESS_FUTURE = "future"      # Same as current but different messages
DOCUMENT_ACCESS_ARCHIVE = "archive"
DOCUMENT_ACCESS_UNDEFINED = "undefined"
DOCUMENT_ACCESS_OFFSITE = "offsite"
DOCUMENT_ACCESS_SPECIAL = "special"
DOCUMENT_ACCESS_TOC = "toc"              # special handling tocs (free)
# Let this be the default, e.g., when there's no data, like for paras
DOCUMENT_ACCESS_DEFAULT = DOCUMENT_ACCESS_ARCHIVE

MAX_JOURNALCODE_LEN = 13
MIN_EXCERPT_CHARS = 480
MAX_EXCERPT_CHARS = 2000
MAX_EXCERPT_PARAS = 10
MAX_PARAS_FOR_SUMMARY = 10
MAX_DOCUMENT_RECORDS_RETURNED_AT_ONCE = 500 # needs to be practical too, for time out

DEFAULT_KWIC_CONTENT_LENGTH = 50  # On each side of match (so use 1/2 of the total you want)
DEFAULT_MAX_KWIC_RETURNS = 5
DEFAULT_LIMIT_FOR_SOLR_RETURNS = 15
DEFAULT_LIMIT_FOR_DOCUMENT_RETURNS = 1
DEFAULT_LIMIT_FOR_WHATS_NEW = 5
DEFAULT_LIMIT_FOR_VOLUME_LISTS = 10000 # 2020-04-06 raised from 100, so all volumes can be brought back at once
DEFAULT_LIMIT_FOR_CONTENTS_LISTS = 200
DEFAULT_LIMIT_FOR_METADATA_LISTS = 200
DEFAULT_SOLR_SORT_FIELD = "art_cited_5"
DEFAULT_SOLR_SORT_DIRECTION = "asc" # desc or asc
DEFAULT_LIMIT_FOR_EXCERPT_LENGTH = 4000  # If the excerpt to first page break exceeds this, uses a workaround since usually means nested first page break.
DEFAULT_CITED_MORE_THAN = 0
DEFAULT_PAGE_LIMIT = 999
DEFAULT_PUBLICATION_PERIOD = "ALL"

DB_ITEM_OF_INTEREST_WIDTH = 255 # database col for logging query/item of interest

SOLR_KWIC_MAX_ANALYZED_CHARS = 25200000 # kwic (and highlighting) wont show any hits past this.
SOLR_FULL_TEXT_MAX_ANALYZED_CHARS = 25200000 # full-text markup won't show matches beyond this.
SOLR_HIGHLIGHT_RETURN_FRAGMENT_SIZE = 25200000 # to get a complete document from SOLR, with highlights, needs to be large.  SummaryFields do not have highlighting.
SOLR_HIGHLIGHT_RETURN_MIN_FRAGMENT_SIZE = 2000 # Abstract size

# SmartSearch Return Classes
WORDSEARCH = "WORDSEARCH"
NAMELIST = "NAMELIST"
SOLRFIELD = "SOLRFIELD"
ADVANCED = "ADVANCED"
DOI = "DOI"
REFERENCEFIELDS = "REFERENCEFIELDS"

#Standard Values for parameters
# here anything matching the first 4 characters of type matches.
DICTLEN_KEY = 'length'
def list_values(val_dict):
    ret_val = ""
    vals = [ v for v in val_dict.values() ]
    for n in vals[1:-1]:
        ret_val += n + ", "
    ret_val += "or " + vals[-1]

    return ret_val

def norm_val_list(val_dict):
    return [ v for v in val_dict.values() ]

def norm_val_error(val_dict, val_name=""):
    return f"{val_name} Error. Allowed values {list_values(val_dict)} (only {val_dict[DICTLEN_KEY]} char required)."
        
def normalize_val(val, val_dict, default=None):
    """
    Allow quick lookup and normalization of input values
    """
    ret_val = default
    if isinstance(val, int):
        val = str(val)
    
    if val is not None:
        try:
            val = val.lower()    
            if val != DICTLEN_KEY:
                if val[:val_dict['length']] in val_dict:
                    ret_val = val_dict[val[:val_dict['length']]]
                
        except Exception as e:
            logging.warning(f"Value check returned error {e}")
    
    return ret_val

# Special relatedrx field name from Solr schema
RELATED_RX_FIELDNAME = "art_qual"

# Special Options flag map:
OPTION_1_NO_GLOSSARY_TERM_MARKUP = 1
OPTION_2_RETURN_TRANSLATION_SET = 2
OPTION_4_RESERVED = 4
OPTION_8_RESERVED = 8
OPTION_16_RESERVED = 16

# Standard view categories for View functions, mapping to RDS/MySQL and SOLR
VALS_VIEWPERIODDICT_SQLFIELDS = {1: "lastweek", 2: "lastmonth", 3: "last6months", 4: "last12months", 5: "lastcalyear", 0: "lastcalyear" }  # not fond of zero, make both 5 and 0 lastcalyear
VALS_VIEWPERIODDICT_SOLRFIELDS = {1: "art_views_lastweek", 2: "art_views_last1mos", 3: "art_views_last6mos", 4: "art_views_last12mos", 5: "art_views_lastcalyear", 0: "art_views_lastcalyear" }  # not fond of zero, make both 5 and 0 lastcalyear

# Normalized sets: the first key is the minimum abbreviated length for input
# Example:
#  > cited_in_period = opasConfig.normalize_val("al", opasConfig.VALS_YEAROPTIONS, default='ALL')
#  ALL
#  
# 
VALS_PRODUCT_TYPES = {DICTLEN_KEY: 4, "jour": "journal", "vide": "videos", "stre": "stream", "book": "book"}
VALS_SOURCE_TYPE = {DICTLEN_KEY: 1, 'j': 'journal', 'b': 'book', 'v': 'videostream'} # standard values, can abbrev to 1st char or more
VALS_ARTTYPE = {DICTLEN_KEY: 3, 'article': 'ART', 'abstract': 'ABS', 'announcement': 'ANN', 'commentary': 'COM', 'errata': 'ERR', 'profile': 'PRO', 'report': 'REP', 'review': 'REV'}
VALS_DOWNLOADFORMAT = {DICTLEN_KEY: 4, 'html': 'HTML', 'pdf': 'PDF', 'pdfo': 'PDFORIG', 'epub': 'EPUB'}
# cited_in_period values (used for sort selection, and comparison to minimums for search)
VALS_YEAROPTIONS = {DICTLEN_KEY: 2, '5': '5', '10': '10', '20': '20', 'al': 'all'}


# parameter descriptions for OpenAPI documentation; (Some depend on definitions in help text above)
DESCRIPTION_ADMINCONFIG = "Global settings by an administrator for the specific client app"
DESCRIPTION_ADMINCONFIGNAME = "Name for the global settings (configuration) for the specific client app"
DESCRIPTION_ADVANCEDSEARCH = "Advanced Query in Solr syntax (see schema names)"
DESCRIPTION_API_MODE = "Set the api mode to 'debug' or 'production' (default)"
DESCRIPTION_DEF_TYPE = "Query analyzer"
DESCRIPTION_ADVANCEDSEARCHQUERY = "Advanced Query in Solr syntax (see schema names)"
DESCRIPTION_ADVANCEDSEARCHFILTERQUERY ="Advanced Query in Solr syntax (see schema names)"
DESCRIPTION_HIGHLIGHT_FIELDS = "Comma separated list of field names for highlight return"
DESCRIPTION_RETURN_FIELDS = "Comma separated list of field names for data return"
DESCRIPTION_ARTICLETYPE = "Types of articles: ART(article), ABS(abstract), ANN(announcement), COM(commentary), ERR(errata), PRO(profile), (REP)report, or (REV)review."
DESCRIPTION_AUTHOR = "Author name, use wildcard * for partial entries (e.g., Johan*)"
DESCRIPTION_AUTHORNAMEORPARTIAL = "The author name or a partial name (regex type wildcards [.*] permitted EXCEPT at the end of the string--the system will try that automatically)"
DESCRIPTION_AUTHORNAMEORPARTIALNOWILD = "The author name or a author partial name (prefix)"
DESCRIPTION_CITECOUNT = "Include documents cited this many or more times (or X TO Y times) in past 5 years (or IN {5, 10, 20, or ALL}), e.g., 3 TO 6 IN ALL. Default (implied) period is 5 years."  
DESCRIPTION_CLIENT_ID = "Numeric ID assigned to a client app by Opas Administrator"
DESCRIPTION_CLIENT_SESSION = "Client session GUID"
DESCRIPTION_CORE = "The preset name for the specif core to use (e.g., docs, authors, etc.)"
DESCRIPTION_DOWNLOAD = "Download a CSV with the current return set of the statistical table" 
DESCRIPTION_DAYSBACK = "Number of days to look back to assess what's new"
DESCRIPTION_DOCDOWNLOADFORMAT = f"The format of the downloaded document data.  One of: {list_values(VALS_DOWNLOADFORMAT)}"
DESCRIPTION_DOCIDORPARTIAL = "The document ID (e.g., IJP.077.0217A) or a partial ID (e.g., IJP.077,  no wildcard) for which to return data (only one ID for full-text documents)"
DESCRIPTION_DOCIDSINGLE = "The document ID (e.g., IJP.077.0217A) for which to return data (only one ID for full-text documents)"
DESCRIPTION_CITEDID = "The cited document ID (e.g., IJP.077.0217A) for which to return a list of cited documents (booleans permitted)"
DESCRIPTION_DOCUMENT_CONCORDANCE_ID = "Paragraph language ID to return for a concordance link"
DESCRIPTION_DOCUMENT_CONCORDANCE_RX = "String with single or list of Paragraph language IDs to return for a concordance link"
DESCRIPTION_ENDDATE = "Find records on or before this date (input date as 2020-08-10 or 20200810)"
DESCRIPTION_ENDPOINTID_LIST = "Filter by this comma separated list of Endpoint IDs (e.g., 31,32,41)"
DESCRIPTION_ENDYEAR = "Find documents published on or before this year (e.g, 2001)" 
DESCRIPTION_FACETFIELDS = "List of fields for which to return facet info. Field art_sourcetype, for example, will give results counts by type (journal, book, videostream)."
DESCRIPTION_FACETLIMIT = "Maximum number of facet values to return"
DESCRIPTION_FACETMINCOUNT = "Minimum count to return a facet"
DESCRIPTION_FACETOFFSET = "Offset that can be used for paging through a facet"
DESCRIPTION_FIRST_PAGE = "Document's first page"
DESCRIPTION_LAST_PAGE = "Document's last page"
DESCRIPTION_FACETQUERY = 'Facet field(s) limiter using Solr query syntax and facet names, e.g. art_sourcetitleabbr:("Int. J. Psychoanal." OR "Int. Rev. Psycho-Anal." OR "Brit. J. Psychother.").'
DESCRIPTION_FULLTEXT1 = "Find Words (or phrases in quotes) across the document (Boolean search is not paragraph level.) Field specifications--e.g., art_authors:(authorname)--are allowed."
DESCRIPTION_FULLTEXT1_V1 = "Words or phrases (in quotes) in a paragraph in the document."
DESCRIPTION_GETFULLCOUNT = "Return full set size as well as the filtered set size"
DESCRIPTION_GLOSSARYID = "Specify the Name, Group, or ID of a Glossary item to return the document. Specify which type of identifier using query param termidtype."
DESCRIPTION_IMAGEID = "A unique identifier for an image"
DESCRIPTION_ISSN = "Standardized 8-digit code used to identify newspapers, journals, magazines and periodicals of all kinds and on all media–print and electronic."
DESCRIPTION_EISSN = "Standardized 8-digit code used to identify newspapers, journals, magazines and periodicals as electronic (the same as issn in PEP schema)"
DESCRIPTION_ISBN = "International Standard Book Number. 10 digits up to the end of 2006, now always consist of 13 digits"
DESCRIPTION_ISSUE = "The issue number if the source has one (or S, or Supplement for supplements).  If alpha will convert to equivalent number counting from A."
DESCRIPTION_LIMIT = "Maximum number of items to return."
DESCRIPTION_MAX_KWIC_COUNT = "Maximum number of hits in context areas to return"
DESCRIPTION_MOREINFO = "Return statistics on the Archive holdings (and extended version info for admins)"
DESCRIPTION_MORELIKETHIS = "Find similar documents"
DESCRIPTION_MOST_CITED_PERIOD = f"Period for minimum count parameter 'citecount'; show articles cited at least this many times during this time period [in full years: 5, 10, 20, al(l)]"
DESCRIPTION_MOST_VIEWED_PERIOD = f"Period applying to the minimum count parameter 'viewcount' filtering articles viewed during this period (use integer: 1: lastweek,  2: lastmonth, 3: last6months, 4: last12months,  5: lastcalendaryear)"
DESCRIPTION_OFFSET = "Start return with this item, referencing the sequence number in the return set (for paging results)."
DESCRIPTION_PAGELIMIT = "Number of pages of a document to return"
DESCRIPTION_PAGEOFFSET = "Starting page to return for this document as an offset from the first page.)"
DESCRIPTION_PAGEREQUEST = "The page or page range (from the document's numbering) to return (e.g., 215, or 215-217)"
DESCRIPTION_PARAM_SOURCETYPE = f"Source type (One of: {list_values(VALS_SOURCE_TYPE)})"
DESCRIPTION_PARASCOPE = "scope: doc, dreams, dialogs, biblios, per the schema (all the p_ prefixed scopes are also recognized without the p_ here)"
DESCRIPTION_PARATEXT = "Words or phrases (in quotes) in a paragraph in the document"
#DESCRIPTION_PARAZONE_V1 = "scope: doc, dreams, dialogs, biblios, per the schema (all the p_ prefixed scopes are also recognized without the p_ here)"
DESCRIPTION_PATH_SOURCETYPE = f"Source type.  One of: {list_values(VALS_SOURCE_TYPE)})"
DESCRIPTION_PUBLICATION_PERIOD = "Number of publication years to include (counting back from current year, 0 means current year)"
DESCRIPTION_RELATEDTOTHIS = "Enter a document ID to find all related documents per a common schema value"
DESCRIPTION_REPORT_REQUESTED="One of the predefined report names"
DESCRIPTION_REPORT_MATCHSTR="Report specific match string (params for session-views/user-searches, e.g., /Documents/Document/AIM.023.0227A/, and type for document-activity, e.g., PDF)"
DESCRIPTION_REQUEST = "The request object, passed in automatically by FastAPI"
DESCRIPTION_RETURNFORMATS = "The format of the returned full-text (e.g., abstract or document data).  One of: 'HTML', 'XML', 'TEXTONLY'.  The default is HTML."
DESCRIPTION_RETURN_ABSTRACTS = "Return abstracts in the documentList (Boolean: true or false)"
DESCRIPTION_SEARCHPARAM = "This is a document request, including search parameters, to show hits"
DESCRIPTION_SESSION_ID_FILTER = "Filter by this Session ID"
DESCRIPTION_SITEMAP_PATH = f"Folder or S3 Bucket to put the sitemap"
DESCRIPTION_SITEMAP_RECORDS_PER_FILE = "Number of records per file"
DESCRIPTION_SITEMAP_MAX_RECORDS = "Max records exported to sitemap"
DESCRIPTION_SMARTSEARCH = "Search input parser looks for key information and searches based on that."
DESCRIPTION_SORT =f"Comma separated list of field names to sort by {tuple(PREDEFINED_SORTS.keys())}."
DESCRIPTION_SORTORDER = f"Sort order, either DESC or ASC for descending/ascending."
DESCRIPTION_SOURCECODE = "The 2-12 character PEP Code (e.g., APA, ANIJP-FR, CPS, PEPTOPAUTHVS), or a Boolean list of codes (e.g., APA OR CPS) or a comma separated list (e.g.: APA, IJP, CPS)"
DESCRIPTION_SOURCECODE_METADATA_BOOKS = "The 2-3 character PEP Code for the book series (e.g., SE, GW, IPL, NLP, ZBK), or the PEP Code and specific volume number of a book in the series (e.g., GW001, SE006, NLP014, ZBK047 (classic book, specific book assigned number) or * for all."
DESCRIPTION_SOURCECODE_METADATA_JOURNALS = "The FULL 2-8 character PEP Code of the journal source for matching documents (e.g., APA, ANIJP-FR, CPS, IJP, IJPSP, PSYCHE) or * for all."
DESCRIPTION_SOURCECODE_METADATA_VIDEOS = "The PEP Code of the video series (e.g., BPSIVS, IPSAVS, PEPVS, PEPGRANTVS, PEPTOPAUTHVS) or * for all."
DESCRIPTION_SOURCELANGCODE = "Language code or comma separated list of codes for matching documents (e.g., EN, ES, DE, ...)"
DESCRIPTION_SOURCENAME = "Name or partial name of the source (e.g., 'international' or 'psychoanalytic')"
DESCRIPTION_SPECIALOPTIONS = "Integer mapped to Option flags for special options"
DESCRIPTION_STATONLY = "Return minimal documentListItems for statistics."
DESCRIPTION_STARTDATE = "Find records on or after this date (input date as 2020-08-10 or 20200810)"
DESCRIPTION_STARTYEAR = "Find documents published on or after this year, or in this range of years (e.g, 1999, Between range: 1999-2010. After: >1999 Before: <1999" 
DESCRIPTION_SYNONYMS_BOOLEAN = "Expand search to include specially declared synonyms (True/False)"
DESCRIPTION_SIMILARCOUNT = "Return this many similar documents for each document in the return set (0 = none)" 
DESCRIPTION_TERMCOUNT_METHOD = '1=Alternate method for termcounts, allows full wildcards (requires solrpy installed). Default (=0) only supports wildcard at end of string "*"' 
DESCRIPTION_TERMFIELD = "Enter a single field to examine for all terms where a field is not specified in termlist (e.g., text, authors, keywords)."
DESCRIPTION_TERMLIST = "Comma separated list of terms, you can specify a field before each as field:term or just enter the term and the default field will be checked."
DESCRIPTION_QTERMLIST = "SolrQeryTermList model for term by term field, term, and synonynm specification (Post Only)"
DESCRIPTION_TITLE = "The title of the document (article, book, video)"
DESCRIPTION_TRANSLATIONS = "Return a list of documents which are translations of this document in field translationSet"
# DESCRIPTION_DATETYPE = "Qualifier for date range (from API v1), either 'Before', 'On', or 'Between'."
DESCRIPTION_USERID_FILTER = "Filter by this common (global) system userid"
DESCRIPTION_VIEWCOUNT = "Include documents (not abstracts) viewed this many or more times (or X TO Y times). Optionally specify viewperiod, IN (lastweek|lastmonth|last6months|last12months|lastcalendaryear), or in parameter viewperiod"  
DESCRIPTION_VIEWCOUNT_INT = "Include documents (not abstracts) viewed this many or more times. Must be an integer."  
DESCRIPTION_VIEWPERIOD = "One of a few preset time frames for which to evaluate viewcount; 0=last cal year, 1=last week, 2=last month, 3=last 6 months, 4=last 12 months."
DESCRIPTION_VOLUMENUMBER = "The volume number if the source has one"
DESCRIPTION_WORD = "A word prefix to return a limited word index (word-wheel)."
DESCRIPTION_WORDFIELD = "The field for which to look up the prefix for matching index entries.  It must be a full-text indexed field (text field or derivative)"
DESCRIPTION_YEAR = "The year for which to return data"
DESCRIPTION_TERMIDTYPE = f"Source type (One of: ID, Name, Group)"

# title definitions only show in the alternative interactive API 
TITLE_API_MODE = "API mode"
TITLE_ADMINCONFIG = "Administrative global settings"
TITLE_ADMINCONFIGNAME = "Configuration Name"
TITLE_ADVANCEDSEARCHQUERY = "Advanced Query (Solr Syntax)"
TITLE_ADVANCEDSEARCHFILTERQUERY = "Advanced Filter Query (Solr Syntax)"
TITLE_ARTICLETYPE = "Filter by the type of article" 
TITLE_AUTHOR = "Author name"
TITLE_AUTHORNAMEORPARTIAL = "Author name or partial/regex"
TITLE_CITECOUNT = "Find Documents cited this many times"
TITLE_CITED_ID = "Document ID of the cited document (e.g., IJP.077.0217A)"
TITLE_CLIENT_ID = "Client App Numeric ID"
TITLE_CLIENT_SESSION = "GUID/UUID for client session"
TITLE_CORE = "Core to use"
TITLE_DAYSBACK = "Days Back"
TITLE_DEF_TYPE = "edisMax, disMax, lucene (standard) or None (lucene)"
TITLE_DOWNLOAD = "Download response as CSV"
TITLE_DOCUMENT_CONCORDANCE_ID = "Paragraph language ID"
TITLE_DOCUMENT_CONCORDANCE_RX = "Paragraph language IDs"
TITLE_DOCUMENT_ID = "Document ID (e.g., IJP.077.0217A)"
TITLE_ENDDATE = "End date"
TITLE_ENDYEAR = "End year"
TITLE_FACETFIELDS = "List of field names for faceting"
TITLE_FACETQUERY = "Facet field(s) limiter using Solr query syntax and facet names"
TITLE_FACETLIMIT = "Maximum number of facet values to return"
TITLE_FACETMINCOUNT = "Minimum count to return a facet"
TITLE_FACETOFFSET = "Offset that can be used for paging through a facet"
TITLE_FULLTEXT1 = "Document-wide search"
TITLE_FULLTEXT1_V1 = "Paragraph based search"
TITLE_GETFULLCOUNT = "Return full unfiltered set size"
TITLE_HIGHLIGHT_FIELDS = "Fields to return for highlighted matches"
TITLE_IMAGEID = "Image ID (unique)"
TITLE_ISSUE = "Issue Number"
TITLE_LIMIT = "Document return limit"
TITLE_MAX_KWIC_COUNT = "Maximum number of hits in context areas to return"
TITLE_MOREINFO = "Return extended information"
TITLE_MORELIKETHIS = "Enter an document ID to find similar documents"
TITLE_MOST_CITED_PERIOD = f"Show articles cited at least this many times during this time period"
TITLE_MOST_VIEWED_PERIOD = f"Show articles viewed during this period"
TITLE_OFFSET = "Document return offset"
TITLE_PAGELIMIT = "Number pages to return"
TITLE_PAGEOFFSET = "Relative page number (1 is the first) to return"
TITLE_PAGEREQUEST = "Document's first page or page range"
TITLE_PARASCOPE = "Scope for paragraph search"
TITLE_PARATEXT = "Paragraph based search"
TITLE_RELATEDTOTHIS = "A document ID for which to find related documents"
TITLE_SMARTSEARCH = "Search input parser"
TITLE_SPECIALOPTIONS = "Integer mapped to Option flags for special options"
TITLE_PARAZONE1_V1 = "Zone for paragraph search"
TITLE_PUBLICATION_PERIOD = "Number of Years to include"
TITLE_REPORT_MATCHSTR="Report specific match string"
TITLE_REPORT_REQUESTED="Report Requested"
TITLE_REQUEST = "HTTP Request" 
TITLE_RETURN_ABSTRACTS_BOOLEAN = "Return an abstract with each match (true/false)"
TITLE_RETURN_FIELDS = "Fields for data return"
TITLE_RETURNFORMATS = "Document return format"
TITLE_SEARCHPARAM = "Document request from search results"
TITLE_SESSION_ID_FILTER = "SessionID"
TITLE_SITEMAP_PATH = "Where to put the sitemap"
TITLE_SITEMAP_RECORDS_PER_FILE = "Number of records per file"
TITLE_SITEMAP_MAX_RECORDS = "Max records exported to sitemap"
TITLE_SORT = f"Field names to sort by {tuple(PREDEFINED_SORTS.keys())}."
TITLE_SORTORDER = f"Sort order, either DESC or ASC for descending/ascending."
TITLE_SOURCECODE = "Series code"
TITLE_SOURCELANGCODE = "Source language code"
TITLE_SOURCENAME = "Series name"
TITLE_ISSN = "Standardized code for non-books"
TITLE_ISBN = "Standardized code for books"
TITLE_SOURCETYPE = "Source type"
TITLE_FIRST_PAGE = "Document's first page"
TITLE_STATONLY = "Minimal return items"
TITLE_STARTYEAR = "Start year or range"
TITLE_STARTDATE = "Start date"
TITLE_SYNONYMS_BOOLEAN = "Synonym expansion switch (True/False)"
TITLE_SIMILARCOUNT = "Return this many similar documents for each match"
TITLE_TERMCOUNT_METHOD = '1=Alternate method for termcounts (req. solrpy lib installed)' 
TITLE_TERMFIELD = "Default field for which to get term counts"
TITLE_TERMLIST = "List of terms"
TITLE_TRANSLATIONS = "If true, return a list of documents which are translations"
TITLE_QTERMLIST = "Opas Model SolrQeryTermList (Post Only)"
TITLE_TITLE = "Document Title"
# TITLE_DATETYPE = "Qualifier for date range (from API v1), either 'Before', 'On', or 'Between'."
TITLE_VIEWCOUNT = "Include documents viewed this many times or more within the view period"
TITLE_VIEWPERIOD = "One of the preset timeframes within which to evaluate viewcount"
TITLE_VOLUMENUMBER = "Volume Number"
TITLE_USERID_FILTER = "Global User ID"
TITLE_ENDPOINTID_LIST = "Comma separated list of Endpoint IDs"
TITLE_WORD = "Word prefix"
TITLE_WORDFIELD = "Field to check word in index"
TITLE_YEAR = "Year"

ENDPOINT_SUMMARY_ABSTRACT_VIEW = "Return an abstract"
ENDPOINT_SUMMARY_AUTHOR_INDEX = "Return a list of matching author names"
ENDPOINT_SUMMARY_AUTHOR_PUBLICATIONS = "Return a bibliographic format list of publications matching the specified author pattern"
ENDPOINT_SUMMARY_BOOK_NAMES = "Return a list of available books in bibliographic format (with additional info)"
ENDPOINT_SUMMARY_CHANGE_PASSWORD = "Change the user's password"
ENDPOINT_SUMMARY_CONTENTS_SOURCE = "Return the contents of the specified source in bibliographic format"
ENDPOINT_SUMMARY_CONCORDANCE = "Return the corresponding language translated paragraph for the language-paragraph-ID (para_lgrid) specified."
ENDPOINT_SUMMARY_CONTENTS_SOURCE_VOLUME = "Return the contents of the specified volume in bibliographic format"
ENDPOINT_SUMMARY_CREATE_USER = "Create a new user for the system"
ENDPOINT_SUMMARY_DELETE_CONFIGURATION = "Delete the specified named configuration by the client app"
ENDPOINT_SUMMARY_SAVE_CONFIGURATION = "Save a named configuration by the client app (must not exist)."
ENDPOINT_SUMMARY_SAVEORREPLACE_CONFIGURATION = "Save (or replace) the named configuration by the client app"
ENDPOINT_SUMMARY_GET_CONFIGURATION = "Get the named client app configuration"
ENDPOINT_SUMMARY_DOCUMENTATION = "Return a HTML page with the interactive API documentation. Requires API Key."
ENDPOINT_SUMMARY_DOCUMENT_DOWNLOAD = "Download a document"
ENDPOINT_SUMMARY_DOCUMENT_SUBMIT = "document_submission"
ENDPOINT_SUMMARY_DOCUMENT_VIEW = "Return a full document if open access or the current user is subscribed"
ENDPOINT_SUMMARY_EXTENDED_SEARCH = "Extends search for more Solr like flexibility. Requires API Key."
ENDPOINT_SUMMARY_GLOSSARY_SEARCH = "Search the PEP Glossary"
ENDPOINT_SUMMARY_GLOSSARY_SEARCH_POST = "Search the PEP Glossary, allowing POST of a qtermlist, for more precise specification"
ENDPOINT_SUMMARY_GLOSSARY_VIEW = "Return a glossary entry for the terms"
ENDPOINT_SUMMARY_IMAGE_DOWNLOAD = "Download an image"
ENDPOINT_SUMMARY_JOURNALS = "Return a list of available journals"
ENDPOINT_SUMMARY_LICENSE_STATUS = "get_license_status.  Used in v1 for login (maybe oauth?)"
ENDPOINT_SUMMARY_LOGIN = "Login a user (less secure method)"
ENDPOINT_SUMMARY_LOGLEVEL = "Admin function to change logging level"
ENDPOINT_SUMMARY_LOGIN_BASIC = "Login a user more securely"
ENDPOINT_SUMMARY_LOGOUT = "Logout the user who is logged in"
ENDPOINT_SUMMARY_METADATA_ARTICLEID = "Check if articleID (document ID) is a valid articleID and break down the subinformation from it"
ENDPOINT_SUMMARY_MOST_CITED = "Return the most cited journal articles published in this time period (5, 10, 20, or ALL years)"
ENDPOINT_SUMMARY_WHO_CITED = "Return the documents which cited the document specified during this time period (5, 10, 20, or ALL years)"
ENDPOINT_SUMMARY_MORELIKETHIS = "Finds related documents based on the contents of the document."
ENDPOINT_SUMMARY_MOST_VIEWED = "Return the most viewed journal articles published in this time period  (5, 10, 20, or ALL years)"
ENDPOINT_SUMMARY_OPEN_API = "Return the OpenAPI specification for this API"
ENDPOINT_SUMMARY_RELATEDTOTHIS = "Finds related documents based on a field mapped to relatedrx"
ENDPOINT_SUMMARY_REPORTS = "Administrative predefined reports, e.g., from the server logs, e.g., Session-Log, User-Searches"
ENDPOINT_SUMMARY_SEARCH_SMARTSEARCH = "Convenience function focused on the SmartSearch parameter"
ENDPOINT_SUMMARY_SEARCH_ADVANCED = "Advanced document search directly using OPAS schemas with OPAS return structures"
ENDPOINT_SUMMARY_SEARCH_ANALYSIS = "Analyze search and return term/clause counts"
ENDPOINT_SUMMARY_SEARCH_MORE_LIKE_THESE = "Full Search implementation, but expand the results to include 'More like these'"
ENDPOINT_SUMMARY_SEARCH_PARAGRAPHS = "Search at the paragraph (lowest) level by paragraph scope (doc, dreams, ...)"
ENDPOINT_SUMMARY_SEARCH_V1 = "Search at the paragraph level by document zone (API v1 backwards compatible)"
ENDPOINT_SUMMARY_SEARCH_V2 = "Full search implementation, at the document or paragraph level"
ENDPOINT_SUMMARY_SEARCH_POST = "Full search implementation, at the document or paragraph level with body (termlist)"
ENDPOINT_SUMMARY_SITEMAP = "Admin function to generate sitemap for search engines"
ENDPOINT_SUMMARY_OPENURL = "Search implementation using openURL .1 parameters"
ENDPOINT_SUMMARY_API_STATUS = "Return the API version and status"
ENDPOINT_SUMMARY_SERVER_STATUS = "Return the server status and more"
ENDPOINT_SUMMARY_SOURCE_NAMES = "Return a list of available sources"
ENDPOINT_SUMMARY_SUBSCRIBE_USER = "Add a new publication subscription for a user (Restricted)"
ENDPOINT_SUMMARY_TERM_COUNTS = "Get term frequency counts"
ENDPOINT_SUMMARY_TOKEN = "Endpoint from v1, needs to be implemented correctly for oauth"
ENDPOINT_SUMMARY_VIDEOS = "Return the list of available videostreams (video journals)"
ENDPOINT_SUMMARY_VOLUMES = "Return a list of available volumes (and years) for sources"
ENDPOINT_SUMMARY_WHATS_NEW = "Return the newest uploaded issues"
ENDPOINT_SUMMARY_WHO_AM_I = "Return information about the current user"
ENDPOINT_SUMMARY_WORD_WHEEL = "Return matching terms for the prefix in the specified field"

# control whether abstracts can be viewed by non-logged-in users
ACCESS_ABSTRACT_RESTRICTION = False
ACCESS_ABSTRACT_RESTRICTED_MESSAGE = 1220 #"You must be a registered user to view abstracts (registration is free and easy).  If you are already a registered user, please login."

ACCESS_SUMMARY_DESCRIPTION = 1221 # "This is a summary excerpt from the full document. "
ACCESS_SUMMARY_FORSUBSCRIBERS = 1222 # "The full content of the document is available to subscribers. "
ACCESS_SUMMARY_EMBARGOED = 1223 # "The full-text content of the document is embargoed per an agreement with the publisher. "
ACCESS_SUMMARY_FUTURE = 1224 # "This journal is in the process of being added to PEP-Web.  The full-text content of the document is not yet available. "

# ACCESS_SUMMARY_EMBARGOED_YEARS = "The full-text content of the document is embargoed for %s years per an agreement with the publisher. "
ACCESS_SUMMARY_PUBLISHER_INFO = 1225 # "It may be available on the publisher's website" # Take out space here, put it below.  If no link, a period will be added. 
ACCESS_SUMMARY_NOT_AVAILABLE = 1226 # This content is not currently available. 
ACCESS_SUMMARY_SPECIAL = 1227 # "It may be available, it's a case by case basis 

ACCESS_SUMMARY_PUBLISHER_INFO_DOI_LINK = " <a href=\"http://dx.doi.org/%s\" target=\"_blank\">here</a>." # needs the left space now 2021-05-05
# ACCESS_SUMMARY_PUBLISHER_INFO_LINK_TEXT_ONLY = "%s."

ACCESSLIMITED_DESCRIPTION_OFFSITE = 1200 # "This important document is part of our 'offsite' collection--it's searched by our system, but available only from the publisher or authorized sites. "
# ACCESSLIMITED_DESCRIPTION_LIMITED = "This is a summary excerpt from the full text of the article. The full text of the document may be available on the publisher's website"
ACCESSLIMITED_DESCRIPTION_FREE = 1201 # "This content is currently free to all users."
ACCESSLIMITED_DESCRIPTION_AVAILABLE = 1202 # "This archive content is available for you to access."
ACCESSLIMITED_401_UNAUTHORIZED = 401 # "Your session may have timed out. Please try and login again."
ACCESSLIMITED_DESCRIPTION_CURRENT_CONTENT_AVAILABLE = 1204 # "This current content is available for you to access."
ACCESSLIMITED_DESCRIPTION_FUTURE_CONTENT_NOT_AVAILABLE = 1205 #"This future content is not yet available for you to access."

# the following symbolic codes are embargo types, so the numberic equivalent is not needed.
IJPOPEN_REMOVED = 300 # " This article was removed from IJPOpen."

# temp directory used for generated downloads
TEMPDIRECTORY = tempfile.gettempdir()

VIEW_MOSTVIEWED_DOWNLOAD_COLUMNS = "textref, lastweek, lastmonth, last6months, last12months, lastcalyear"
VIEW_MOSTCITED_DOWNLOAD_COLUMNS = "art_citeas_text, count5, count10, count20, countAll"

#Schema Field Name Suffix for Synonym Searching
SYNONYM_SUFFIX = "_syn"
SYNONYM_FIELDS = ["body_xml", "text", "para", "title", "appxs_xml", "quotes_xml", "dialogs_xml", "notes_xml", "panels_xml", "dreams_xml", "poems_xml", "references_xml"]
# Must not have spaces
DOCUMENT_VIEW_FACET_LIST = "glossary_group_terms,terms_highlighted,art_kwds_str"
# GLOSSARY_VIEW_FACET_LIST = "glossary_group_terms,terms_highlighted,art_kwds_str"
DEFAULT_MORE_LIKE_THIS_FIELDS = "art_kwds, title, text_xml"
DEFAULT_MORE_LIKE_THIS_COUNT = 0

# Standard Document List Summary fields 
# (potential data return in document list)
# Indent moved to left so when in query, only a few spaces sent to Solr

# DOCUMENT_ITEM_SUMMARY_FIELDS ="art_id, art_title, art_title_xml, art_subtitle_xml, art_author_id, art_authors, art_citeas_xml, art_info_xml, art_sourcecode, art_sourcetitleabbr, art_sourcetitlefull, art_sourcetype, art_level, para_art_id,parent_tag, para, art_vol, art_type, art_vol_title, art_year, art_iss, art_iss_title, art_newsecnm, art_pgrg, art_lang, art_doi, art_issn, art_origrx, art_qual, art_kwds, art_cited_all, art_cited_5, art_cited_10, art_cited_20, art_views_lastcalyear, art_views_last1mos, art_views_last6mos, art_views_last12mos, art_views_lastweek, reference_count, file_last_modified, timestamp, score"

# This is the default return, used most of the time.
# Adding count type fields (2021/5/19) which might be useful to a client
DOCUMENT_ITEM_SUMMARY_FIELDS =""" 
 art_id, 
 art_title, 
 art_title_xml, 
 art_subtitle_xml, 
 art_author_id, 
 art_authors, 
 art_citeas_xml, 
 art_info_xml, 
 art_sourcecode, 
 art_sourcetitleabbr, 
 art_sourcetitlefull, 
 art_sourcetype, 
 art_level,
 para_art_id,
 parent_tag, 
 para, 
 art_vol, 
 art_type, 
 art_vol_title, 
 art_year, 
 art_iss, 
 art_iss_title, 
 art_newsecnm, 
 art_pgrg, 
 art_lang, 
 art_doi, 
 art_issn,
 art_isbn,
 art_embargo,
 art_embargotype,
 art_origrx, 
 art_qual, 
 art_kwds, 
 art_cited_all, 
 art_cited_5, 
 art_cited_10, 
 art_cited_20, 
 art_views_lastcalyear, 
 art_views_last1mos, 
 art_views_last6mos, 
 art_views_last12mos, 
 art_views_lastweek, 
 reference_count,
 art_fig_count,
 art_tbl_count,
 art_kwds_count,
 art_words_count,
 art_citations_count,
 art_ftns_count,
 art_notes_count,
 art_dreams_count,
 file_last_modified,
 file_classification,
 timestamp, 
 score
"""

DOCUMENT_ITEM_CONCORDANCE_FIELDS ="""
 art_id, 
 art_title, 
 art_title_xml, 
 art_subtitle_xml, 
 art_author_id, 
 art_authors, 
 art_citeas_xml, 
 art_info_xml, 
 art_sourcecode, 
 art_sourcetitleabbr, 
 art_sourcetitlefull, 
 art_sourcetype, 
 art_level,
 para_art_id,
 parent_tag, 
 para,
 lang,
 art_vol, 
 art_type, 
 art_vol_title, 
 art_year, 
 art_iss, 
 art_iss_title, 
 art_pgrg, 
 art_lang, 
 art_doi, 
 art_issn,
 art_isbn,
 art_origrx, 
 art_qual, 
 art_kwds, 
 file_last_modified, 
 timestamp,
 file_classification,
 score
"""

# try the more squashed approach to listing, see if that shows better in the solr call logs
DOCUMENT_ITEM_VIDEO_FIELDS = """
art_id,art_issn, art_sourcecode,art_authors, title, art_subtitle_xml, art_title_xml,
art_sourcetitlefull,art_sourcetitleabbr,art_info_xml, art_vol,art_vol_title, art_year, art_iss, art_iss_title,
art_year, art_citeas_xml, art_pgrg, art_lang, art_origrx, art_qual, art_kwds, file_classification
"""

DOCUMENT_ITEM_TOC_FIELDS = """
 art_id, 
 art_info_xml, 
 art_title_xml, 
 art_subtitle_xml, 
 art_authors_xml, 
 art_citeas_xml, 
 art_sourcecode, 
 art_sourcetitleabbr, 
 art_sourcetitlefull, 
 art_level, 
 art_vol, 
 art_type, 
 art_vol_title, 
 art_year, 
 art_iss, 
 art_iss_title, 
 art_newsecnm, 
 art_pgrg, 
 art_lang, 
 art_doi, 
 art_issn,
 art_isbn,
 art_origrx, 
 art_qual, 
 art_kwds,
 file_classification, 
 score
"""

DOCUMENT_ITEM_META_FIELDS ="""
 art_id, 
 meta_xml, 
 art_citeas_xml, 
 art_title_xml, 
 art_subtitle_xml, 
 art_authors_xml, 
 art_sourcecode, 
 art_sourcetitleabbr, 
 art_sourcetitlefull,
 art_vol,
 art_year, 
 art_pgrg,
 art_qual,
 file_classification, 
 score
"""

DOCUMENT_ITEM_STAT_FIELDS = """
 art_id, 
 art_citeas_xml, 
 art_title, 
 art_authors, 
 art_sourcecode, 
 art_sourcetitleabbr, 
 art_sourcetitlefull, 
 art_vol, 
 art_year, 
 art_cited_all, 
 art_cited_5, 
 art_cited_10, 
 art_cited_20, 
 art_views_lastcalyear, 
 art_views_last1mos, 
 art_views_last6mos, 
 art_views_last12mos, 
 art_views_lastweek, 
 reference_count, 
 file_classification, 
 score
"""

# for Glossary Core
GLOSSARY_ITEM_DEFAULT_FIELDS = """
 art_id,
 term_id,
 group_id,
 term,
 term_type,
 term_source,
 term_def_xml,
 term_def_rest_xml,
 group_name,
 group_term_count,
 file_classification, 
 text
"""

AUTHOR_ITEM_DEFAULT_FIELDS ="""
 id,
 art_id,
 art_year_int,
 title, 
 art_title_xml, 
 art_author_id, 
 art_author_listed,
 art_author_pos_int,
 art_author_role,
 art_sourcetype,
 art_sourcetitlefull,
 file_last_modified,
 file_classification,
 timestamp, 
 score
"""

running_head_fmts = {
    'xml': "<p><cgrp name='pub_year'>({pub_year})</cgrp>. <cgrp name='source_title'>{source_title}</cgrp><cgrp name='vol'>{vol}</cgrp><cgrp name='issue'>{issue}</cgrp><cgrp name='pgrg'>{pgrg}</cgrp></p>", 
    'html': "<span class='pub_year'>({pub_year})</span>. <span class='source_title'>{source_title}</span><span class='vol'>{vol}</span><span class='issue'>{issue}</span><span class='pgrg'>{pgrg}</span>",
    'textonly': "({pub_year}). {source_title}{vol}{issue}{pgrg}"
}

MAX_SOURCE_LEN = 14
# search description fields to communicate about the search
KEY_SEARCH_TYPE = "search_type"
KEY_SEARCH_FIELD = "schema_field"
KEY_SEARCH_VALUE = "schema_value"
KEY_SEARCH_CLAUSE = "search_clause"
KEY_SEARCH_SMARTSEARCH = "smart_search"
KEY_SEARCH_FIELD_COUNT = "field_count"
# KEY_MATCH_DICT = "match_dict"
# KEY_SEARCH_WORDSEARCH = "word_search"

SEARCH_TYPE_AUTHOR_CITATION = "author citation"
SEARCH_TYPE_AUTHORS = "authors"
# SEARCH_TYPE_AUTHORS_AND_YEARS = "pattern authors year"
SEARCH_TYPE_WORDSEARCH = "wordsearch"
SEARCH_TYPE_BOOLEAN = "boolean"
SEARCH_TYPE_LITERAL = "literal"
SEARCH_TYPE_TITLE = "title"
SEARCH_TYPE_PARAGRAPH = "paragraph search"
SEARCH_TYPE_ID = "locator"
# SEARCH_TYPE_ADVANCED = "solradvanced"
SEARCH_TYPE_FIELDED = "document field"
SEARCH_TYPE_DOI = "doi"

SEARCH_FIELD_LOCATOR = "art_id"
SEARCH_FIELD_AUTHOR_CITATION = "art_authors_citation"
SEARCH_FIELD_AUTHORS = "authors"
SEARCH_FIELD_TITLE = "title"
SEARCH_FIELD_TEXT = "text"
SEARCH_FIELD_DOI = "art_doi"
SEARCH_FIELD_PGRG = "art_pgrg"
SEARCH_FIELD_RELATED = "art_qual"
SEARCH_FIELD_RELATED_EXPANDED = "related"

IMAGE_API_LINK = "/v2/Documents/Image/" # API Call for images

SS_BROADEN_SEARCH_FIELD_RELATED = (SEARCH_FIELD_RELATED, SEARCH_FIELD_LOCATOR) # technique can be used generally to expand search based on field specified

SS_BROADEN_DICT = {SEARCH_FIELD_RELATED: SS_BROADEN_SEARCH_FIELD_RELATED,
                   SEARCH_FIELD_RELATED_EXPANDED: SS_BROADEN_SEARCH_FIELD_RELATED,
                  }

SUPPLEMENT_ISSUE_SEARCH_STR = "Supplement" # this is what will be searched in "art_iss" for supplements

#PEPWEB_ABSTRACT_MSG1 = """
#This is a summary or excerpt from the full text of the article. PEP-Web provides full-text search of the complete articles for
#current and archive content, but only the abstracts are displayed for current content, due to contractual obligations with the
#journal publishers. For details on how to read the full text of 2017 and more current articles see the publishers official website 
#"""

# Note the STSong-Light is a built in font for Pisa
PDF_CHINESE_STYLE = """
<style>
   @page {
          margin-top: 12mm;
          margin-bottom: 12mm;
   }
 
   body, p  {
              font-language-override: "zh";
              font-family: STSong-Light;
              padding-right: 20%;
              margin-left: 5mm;
              margin-right: 8mm;
            }	
</style>
"""

PDF_STYLE_SHEET = "pep-pdf.css"              # "pep-html-preview.css"
SUBPATH = 'fonts'                            # sub to app
STYLEPATH = os.path.join("libs", "styles")

# PDF_EXTENDED_FONT_FILE = f"url('{PATHCHECK1}')"
# PDF_EXTENDED_FONT_ALT = f"url('{PATHCHECK2}')"
# Make sure font is defined:
def get_file_path(filename, subpath):
    ret_val = None
    try:
        pathmod = Path()
        path = pathmod.absolute()
        full_file_path = os.path.join(path, subpath, filename)
        if not Path(full_file_path).is_file():
            parentpath = path.parent.absolute()
            full_file_path = os.path.join(parentpath, subpath, filename)
            if not Path(full_file_path).is_file():
                logging.error(f"{full_font_path} not found. Current Path: {full_file_path} ")

    except Exception as e:
        # try current folder relative
        full_file_path = r"E:/usr3/GitHub/openpubarchive/app/fonts/Roboto-Regular.ttf"
    
    else:
        #ret_val = f"url('{full_font_path}')"
        ret_val = full_file_path
        
    return ret_val
    
def fetch_resources(uri, rel):
    path = None
    if ".ttf" in uri:
        path = get_file_path(uri, SUBPATH)
        # print (f"Returning Font Location: {path}")
    elif ".css" in uri:
        path = get_file_path(uri, STYLEPATH)
        # print (f"Returning style Location: {path}")
    elif "http" in uri:
        if localsecrets.CONFIG == "Local":
            a = urlparse(uri)
            m = re.search("src=.*/Documents/Image/(.*)[\"\']", a.path)
            try:
                if m is not None:
                    #print ("Found <img> and source.")
                    filename = m.group(1)
                    filename = os.path.basename(urllib.parse.unquote(filename))
                else:
                    filename = os.path.basename(urllib.parse.unquote(a.path))
            except Exception as e:
                logging.error(f"Can't get filename from url: {a.path} ({e})")
            else:
                #print (f"PDF Image Filename: {filename}")
                fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root=localsecrets.IMAGE_SOURCE_PATH)
                path = fs.get_image_filename(filename)
        else:
            path = uri
            #print (f"fetch resources trying path: {uri}")
    
    # for now, to watch uri's on web.
    logging.debug(f"Fetch Resources for '{uri}': '{path}'")
    return path

FONT_FILENAME = "Roboto-Regular.ttf"
PDF_OTHER_STYLE = r"""
<link rel="stylesheet" type="text/css" href="%s"/>
<style>
    @page {
        size: letter portrait;
        @frame content_frame {
            left: 50pt;
            width: 512pt;
            top: 50pt;
            height: 692pt;
        }
    }
    @font-face {font-family: Roboto; src: url('%s');}
    @font-face {font-family: Roboto; font-style: italic; src: url('%s');}
    @font-face {font-family: Roboto; font-weight: bold; src: url('%s');}
    @font-face {font-family: Roboto; font-weight: bold; font-style: italic; src: url('%s');}
    body, p {   
                font-family: 'Roboto' }	
</style>
""" % (fetch_resources(PDF_STYLE_SHEET, None),
       fetch_resources('Roboto-Regular.ttf', None),
       fetch_resources('Roboto-Italic.ttf', None),
       fetch_resources('Roboto-Bold.ttf', None),
       fetch_resources('Roboto-BoldItalic.ttf', None),
       )

#print (f"PDF Style: '{PDF_OTHER_STYLE}'")

from pydantic import BaseModel, Field

def parse_volume_code(vol_code: str, source_code: str=None): 
    """
    PEP Volume numbers in IDS can be numbers or suffixed by an issue code--we use them after a volume number when a journal repeats pagination
    from issue to issue or starts the pagination over in a Supplement.
    
    >>> parse_volume_code("34S")
    ('34', 'S')
    >>> parse_volume_code("101C")
    ('101', 'C')
    >>> parse_volume_code("130")
    ('130', None)
    
    
    """
    ret_val = ("*", None)
    if vol_code is not None:
        m = re.match("\(*(?P<vol>[0-9]+)(?P<issuecode>[A-z]+)?\)*", vol_code)
        if m is not None:
            vol = m.group("vol")
            vol = vol.lstrip("0")
            issuecode = m.group("issuecode") 
            ret_val = vol, issuecode

    return ret_val    

def parse_issue_code(issue_code: str, source_code=None, vol=None): 
    """
    Issue codes are PEP unique--we use them after a volume number when a journal repeats pagination
    from issue to issue or starts the pagination over in a Supplement.
    
    Source code and volume can be used to handle sources that are "exceptions" to rules (unfortunately)
    
    """
    ret_val = "*"
    if issue_code is not None and issue_code.isalpha():
        issue_code = issue_code.upper()
        if issue_code[0] != "S" or (source_code == "FA" and vol == 1):
            ret_val = string.ascii_uppercase.index(issue_code[0]) # A==0, B==1
            ret_val += 1 # now A==1
            ret_val = str(ret_val)
        elif issue_code[0] == 'S':
            ret_val = SUPPLEMENT_ISSUE_SEARCH_STR # supplement
        else:
            ret_val = "*" # not recognized, allow any issue
            
    elif issue_code.isdecimal():
        if type(issue_code) == "int":
            ret_val = str(issue_code)
        else:
            ret_val = issue_code
    return ret_val    

class ArticleID(BaseModel):
    """
    Article IDs (document IDs) are at the core of the system.  In PEP's design, article IDs are meaningful, and can be broken apart to learn about the content metadata.
      But when designed as such, the structure of the article IDs may be different in different systems, so it needs to be configurable as possible.
      This routine in opasConfig is a start of allowing that to be defined as part of the customization. 

    >>> a = ArticleID(articleID="AJRPP.004.0007A", allInfo=True)
    >>> print (a.articleInfo)
    {'source_code': 'AJRPP', 'vol_str': '004', 'vol_numeric': '004', 'vol_suffix': '', 'vol_wildcard': '', 'issue_nbr': '', 'page': '0007A', 'roman': '', 'page_numeric': '0007', 'page_suffix': 'A', 'page_wildcard': ''}

    >>> a = ArticleID(articleID="MPSA.043.0117A")
    >>> print (a.altStandard)
    MPSA.043?.0117A
    
    >>> a = ArticleID(articleID="AJRPP.004A.0007A")
    >>> print (a.volumeNbrStr)
    004
    >>> a = ArticleID(articleID="AJRPP.004S.R0007A")
    >>> print (a.issueCode)
    S
    >>> a = ArticleID(articleID="AJRPP.004S(1).R0007A")
    >>> print (a.issueInt)
    1
    >>> a.volumeInt
    4
    >>> a.romanPrefix
    'R'
    >>> a.isRoman
    True
    >>> print (a.articleID)
    AJRPP.004S.R0007A
    >>> a.isRoman
    True
    >>> a.pageInt
    7
    >>> a.standardized
    'AJRPP.004S.R0007A'
    >>> a = ArticleID(articleID="AJRPP.*.*")
    >>> a.standardized
    'AJRPP.*.*'
    >>> a = ArticleID(articleID="IJP.034.*")
    >>> a.standardized
    'IJP.034.*'
    >>> a = ArticleID(articleID="IJP.*.0001A")
    >>> a.standardized
    'IJP.*.*'
    
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        regex_article_id =  "(?P<source_code>[A-Z\-]{2,13})\.(?P<vol_str>(((?P<vol_numeric>[0-9]{3,4})(?P<vol_suffix>[A-Z]?))|(?P<vol_wildcard>\*)))(\((?P<issue_nbr>[0-9]{1,3})\))?\.(?P<page>((?P<roman>R?)(((?P<page_numeric>([0-9]{4,4}))(?P<page_suffix>[A-Z]?))|(?P<page_wildcard>\*))))"
        volumeWildcardOverride = ''
        m = re.match(regex_article_id, self.articleID, flags=re.IGNORECASE)
        if m is not None:
            self.articleInfo = m.groupdict("")
            self.sourceCode = self.articleInfo.get("source_code")
            # self.volumeStr = self.articleInfo.get("vol_str")
            
            # See if it has issue number numerically in ()
            self.issueInt = self.articleInfo.get("issue_nbr") # default for groupdict is ''
            if self.issueInt != '':
                self.issueInt = int(self.issueInt)
            else:
                self.issueInt = 0

            volumeSuffix = self.articleInfo.get("vol_suffix", "")
            altVolSuffix = ""
            if volumeSuffix != "":
                self.issueCode  = volumeSuffix[0]  # sometimes it says supplement!
            else:
                self.issueCode = ""
                if self.issueInt > 0:
                    altVolSuffix = string.ascii_uppercase[self.issueInt-1]
                
            if not self.isSupplement and self.issueInt == 0 and self.issueCode != "":
                # an issue code was specified (but not supplement or "S")
                converted = parse_issue_code(self.issueCode, source_code=self.sourceCode, vol=self.volumeInt)
                if converted.isdecimal():
                    self.issueCodeInt = int(converted)

            self.volumeInt = self.articleInfo.get("vol_numeric") 
            if self.volumeInt != '': # default for groupdict is ''
                self.volumeInt = int(self.volumeInt)
                # make sure str is at least 3 places via zero fill
                self.volumeNbrStr = format(self.volumeInt, '03')
            else:
                self.volumeInt = 0

            volumeWildcardOverride = self.articleInfo.get("vol_wildcard")
            if volumeWildcardOverride != '':
                self.volumeNbrStr = volumeWildcardOverride
                
            self.isSupplement = self.issueCode == "S"
                    
            # page info
            # page = self.articleInfo.get("page")
            self.pageNbrStr = self.articleInfo.get("page_numeric")
            self.pageInt = self.pageNbrStr 
            if self.pageInt != '':
                self.pageInt = int(self.pageInt)
                self.pageNbrStr = format(self.pageInt, '04')
            else:
                self.pageInt = 0
                
            pageWildcard = self.articleInfo.get("page_wildcard")
            if pageWildcard != '':
                self.pageNbrStr = pageWildcard
            
            roman_prefix = self.articleInfo.get("roman", "")  
            self.isRoman = roman_prefix.upper() == "R"
            if self.isRoman:
                self.romanPrefix = roman_prefix 
               
            self.pageSuffix = self.articleInfo.get("page_suffix", "A")
            self.standardized = f"{self.sourceCode}.{self.volumeNbrStr}{self.issueCode}"
            self.altStandard = f"{self.sourceCode}.{self.volumeNbrStr}"
            if self.standardized == self.altStandard:
                # there's no issue code in the standard one. Try adding one:
                if altVolSuffix != "":
                    self.altStandard = f"{self.sourceCode}.{self.volumeNbrStr}{altVolSuffix}"
                else: # use 1 character wildcard
                    self.altStandard = f"{self.sourceCode}.{self.volumeNbrStr}?"
            
            if volumeWildcardOverride == '':
                if pageWildcard == '':
                    self.standardized += f".{self.romanPrefix}{self.pageNbrStr}{self.pageSuffix}"
                    self.altStandard += f".{self.romanPrefix}{self.pageNbrStr}{self.pageSuffix}"
                    #self.standardizedPlusIssueCode += f".{self.romanPrefix}{self.pageNbrStr}{self.pageSuffix}"
                else:
                    self.standardized += f".*"
                    self.altStandard += f".*"
                    #self.standardizedPlusIssueCode += f".*"
            else:
                self.standardized += f".*"
                self.altStandard += f".*"
                #self.standardizedPlusIssueCode += f".*"

            # always should be uppercase
            self.standardized = self.standardized.upper()
            self.isArticleID = True
            self.articleID = self.standardized
            if not self.allInfo:
                self.articleInfo = None
                # These show anyway so don't waste time with clear
                #if self.pageInt == 0:
                    #self.pageNbrStr = None
                #if self.volumeSuffix == '':
                    #self.volumeSuffix = None
                #if self.pageSuffix == '':
                    #self.pageSuffix = None
                #if self.volumeWildcardOverride == '':
                    #self.volumeWildcardOverride = None
                #if self.issueCode == '':
                    #self.issueCode = None
                #if self.page == "*":
                    #self.page = None
                #if self.pageWildcard == '':
                    #self.pageWildcard = None
        else:
            self.isArticleID = False
        
    articleID: str = Field(None, title="As submitted ID, if it's a valid ID")
    standardized: str = Field(None, title="Standard form of article (document) ID")
    altStandard: str = Field(None, title="Standard form of article (document) ID from 2020 (most without volume suffix)")
    isArticleID: bool = Field(False, title="True if initialized value is an article (document) ID")
    sourceCode: str = Field(None, title="Source material assigned code (e.g., journal, book, or video source code)")
    # volumeStr: str = Field(None, title="")
    volumeSuffix: str = Field(None, title="")
    # volumeWildcardOverride: str = Field(None, title="")
    volumeInt: int = Field(0, title="")
    volumeNbrStr: str = Field(None, title="")
    issueCode: str = Field(None, title="")
    isSupplement: bool = Field(False, title="")
    issueInt: int = Field(0, title="")
    issueCodeInt: int = Field(0, title="") 
    # page info
    # page: str = Field(None, title="")
    pageNbrStr: str = Field(None, title="")
    pageInt: int = Field(0, title="")
    # pageWildcard: str = Field(None, title="")
    romanPrefix: str = Field("", title="")
    isRoman: bool = Field(False, title="")
    pageSuffix: str = Field(None, title="")    
    articleInfo: dict = Field(None, title="Regex result scanning input articleID")
    allInfo: bool = Field(False, title="Show all captured information, e.g. for diagnostics")
        
            
# -------------------------------------------------------------------------------------------------------
# test it!

if __name__ == "__main__":
    import sys
    print ("Running in Python %s" % sys.version_info[0])
   
    import doctest
    doctest.testmod()    
    print ("opasConfig Tests Completed")
            