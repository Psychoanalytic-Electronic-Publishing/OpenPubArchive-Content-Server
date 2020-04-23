# import sys
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

BOOKSOURCECODE = "ZBK" #  books are listed under this source code, e.g., to make for an id of ZBK.052.0001

# folders, configure per install
# uploads
UPLOAD_DIR = r"z:\\back\\"
# paths vary because they depend on module location; solrXMLWebLoad needs a different path than the server
# should do this better...later.
STYLE_PATH = r"./libs/styles;../libs/styles"
XSLT_XMLTOHTML = r"pepkbd3-html.xslt"
XSLT_XMLTOTEXT_EXCERPT = r"pepkbd3-abstract-text.xslt"
TRANSFORMER_XMLTOHTML = "XML_TO_HTML" 
TRANSFORMER_XMLTOTEXT_EXCERPT = "EXCERPT_HTML"

CSS_STYLESHEET = r"./libs/styles/pep-html-preview.css"

# Special xpaths and attributes for data handling in solrXMLPEPWebLoad
ARTINFO_ARTTYPE_TOC_INSTANCE = "TOC" # the whole instance is a TOC ()
XML_XPATH_SUMMARIES = "//summaries"
XML_XPATH_ABSTRACT = "//abs"

# XPaths for special data handling
# HTML Paths
# Detect an instance which is a TOC, e.g., GW.001.0000A
HTML_XPATH_TOC_INSTANCE = "//div[@data-arttype='TOC']" 
HTML_XPATH_DOC_BODY = "//div[@class='body']" # used, for example, to extract the body from the html
HTML_XPATH_ABSTRACT = "//div[@id='abs']"  # used, for example, to extract the abstract from the HTML

# API URLs used for linking
API_URL_DOCUMENTURL = "/v2/Documents/"


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

MIN_EXCERPT_CHARS = 480
MAX_EXCERPT_CHARS = 2000
MAX_EXCERPT_PARAS = 10

DEFAULT_KWIC_CONTENT_LENGTH = 200  # On each side of match (so use 1/2 of the total you want)
DEFAULT_MAX_KWIC_RETURNS = 5
DEFAULT_LIMIT_FOR_SOLR_RETURNS = 10
DEFAULT_LIMIT_FOR_DOCUMENT_RETURNS = 1
DEFAULT_LIMIT_FOR_WHATS_NEW = 5
DEFAULT_LIMIT_FOR_VOLUME_LISTS = 10000 # 2020-04-06 raised from 100, so all volumes can be brought back at once
DEFAULT_LIMIT_FOR_CONTENTS_LISTS = 100
DEFAULT_LIMIT_FOR_METADATA_LISTS = 100
DEFAULT_SOLR_SORT_FIELD = "art_cited_5" 
DEFAULT_SOLR_SORT_DIRECTION = "asc" # desc or asc
DEFAULT_LIMIT_FOR_EXCERPT_LENGTH = 4000  # If the excerpt to first page break exceeds this, uses a workaround since usually means nested first page break.

SOLR_HIGHLIGHT_RETURN_FRAGMENT_SIZE = 2520000 # to get a complete document from SOLR, with highlights, needs to be large.  SummaryFields do not have highlighting.

# parameter descriptions for documentation
DESCRIPTION_REQUEST = "The request object, passed in automatically by FastAPI"
DESCRIPTION_DAYSBACK = "Number of days to look back to assess what's new"
DESCRIPTION_SOURCECODE = "The 2-8 character PEP Code for source (of various types, e.g., journals: APA, ANIJP-FR, CPS, IJP, IJPSP, PSYCHE; books: GW, SE, ZBK; videos: PEPGRANTVS, PEPTOPAUTHVS)"
DESCRIPTION_YEAR = "The year for which to return data"
DESCRIPTION_AUTHORNAMEORPARTIAL = "The author name or a partial name (regex type wildcards [.*] permitted EXCEPT at the end of the string--the system will try that automatically)"
DESCRIPTION_AUTHORNAMEORPARTIALNOWILD = "The author name or a author partial name (prefix)"
DESCRIPTION_DOCIDORPARTIAL = "The document ID (e.g., IJP.077.0217A) or a partial ID (e.g., IJP.077,  no wildcard) for which to return data"
DESCRIPTION_GLOSSARYID = "The glossary ID (e.g., YN0011849316410) or a partial ID and wildcard (e.g., YN*) for which to return data"
DESCRIPTION_RETURNFORMATS = "The format of the returned abstract and document data.  One of: 'HTML', 'XML', 'TEXTONLY'.  The default is HTML."
DESCRIPTION_DOCDOWNLOADFORMAT = "The format of the downloaded document data.  One of: 'HTML', 'PDF', 'PDFORIG', EPUB'"
DESCRIPTION_FULLTEXT1_V1 = "Words or phrases (in quotes) in a paragraph in the document."
DESCRIPTION_FULLTEXT1 = "Words or phrases (in quotes) across the document (booleans search is not paragraph level). Field specifications are allowed."
DESCRIPTION_PARATEXT = "Words or phrases (in quotes) in a paragraph in the document"
DESCRIPTION_PARASCOPE = "scope: doc, dreams, dialogs, biblios, per the schema (all the p_ prefixed scopes are also recognized without the p_ here)"
DESCRIPTION_PARAZONE_V1 = "scope: doc, dreams, dialogs, biblios, per the schema (all the p_ prefixed scopes are also recognized without the p_ here)"
DESCRIPTION_SYNONYMS = "Expand search to include specially declared synonyms (True/False)"
DESCRIPTION_SOURCENAME = "Name of Journal, Book, or Video name (e.g., 'international')"
DESCRIPTION_SOURCECODE = "Assigned short code for Source (e.g., APA, CPS, IJP, PAQ)"
DESCRIPTION_PATH_SOURCETYPE = "Source type.  One of: 'Journals', 'Books', 'Videos'"
DESCRIPTION_PARAM_SOURCETYPE = "Source type (e.g., Journal, Book, Video)"
DESCRIPTION_SOURCELANGCODE = "Source language code or comma separated list of codes (e.g., EN, ES, DE, ...)"
DESCRIPTION_VOLUMENUMBER = "The volume number if the source has one"
DESCRIPTION_ISSUE = "The issue number if the source has one"
DESCRIPTION_AUTHOR = "Author name, use wildcard * for partial entries (e.g., Johan*)"
DESCRIPTION_TITLE = "The title of the document (article, book, video)"
DESCRIPTION_STARTYEAR = "Find documents published on or after this year, or in this range of years (e.g, 1999, Between range: ^1999-2010. After: >1999 Before: <1999" 
DESCRIPTION_ENDYEAR = "Find documents published before this year (e.g, 2001)" 
DESCRIPTION_CITECOUNT = "Find documents cited more than 'X' times (or X TO Y times) in past 5 years (or IN {5, 10, 20, or ALL}), e.g., 3 TO 6 IN ALL"  
DESCRIPTION_VIEWCOUNT = "Not yet implemented"    
DESCRIPTION_VIEWEDWITHIN ="Not yet implemented"
DESCRIPTION_FACETFIELDS = "List of fields for which to return facets"
DESCRIPTION_SORT ="Comma separated list of field names to sort by"
DESCRIPTION_LIMIT = "Number of items to return"
DESCRIPTION_OFFSET = "Start return with this item, referencing the sequence number in the return set (for paging results)"
DESCRIPTION_PAGELIMIT = "Number of pages of a document to return"
DESCRIPTION_PAGEREQUEST = "The page or page range (from the document's numbering) to return (e.g., 215, or 215-217)"
DESCRIPTION_PAGEOFFSET = "Starting page to return for this document as an offset from the first page.)"
DESCRIPTION_PAGEOFFSET = "The relative page number (1 is the first) to return"
DESCRIPTION_SEARCHPARAM = "This is a document request, including search parameters, to show hits"
DESCRIPTION_ARTICLETYPE = "Types of articles: ART(article), ABS(abstract), ANN(announcement), COM(commentary), ERR(errata), PRO(profile), (REP)report, or (REV)review"
DESCRIPTION_TERMFIELD = "Enter a single field to examine for all terms where a field is not specified in termlist (e.g., text, authors, keywords)"
DESCRIPTION_TERMLIST = "Comma separated list of terms, you can specify a field before each as field:term or just enter the term and the default field will be checked."
DESCRIPTION_IMAGEID = "A unique identifier for an image"
DESCRIPTION_MOST_CITED_PERIOD = "Most cited articles from this time period (years: 5, 10, 20, or all)"
DESCRIPTION_PUBLICATION_PERIOD = "Number of publication years to include (counting back from current year)" 
DESCRIPTION_MOST_VIEWED_PERIOD = "Most viewed articles in this period (0=Last Cal year, 1=last month, 2=last month, 3=last 6 months, 4=last 12 months)"
DESCRIPTION_CITED_MORETHAN = "Limit to articles cited more than this many times"

TITLE_DAYSBACK = "Days Back"
TITLE_AUTHORNAMEORPARTIAL = "Author name or partial/regex"
TITLE_ARTICLETYPE = "Filter by the type of article" 
TITLE_SEARCHPARAM = "Document request from search results"
TITLE_REQUEST = "HTTP Request" 
TITLE_FULLTEXT1 = "Document-wide search"
TITLE_FULLTEXT1_V1 = "Paragraph based search"
TITLE_PARATEXT = "Paragraph based search"
TITLE_PARASCOPE = "Scope for paragraph search"
TITLE_PARAZONE1_V1 = "Zone for paragraph search"
TITLE_SYNONYMS = "Synonym expansion switch (True/False)"
TITLE_SOURCENAME = "Series name"
TITLE_SOURCECODE = "Series code"
TITLE_SOURCETYPE = "Source type"
TITLE_SOURCELANGCODE = "Source language code"
TITLE_VOLUMENUMBER = "Volume Number"
TITLE_ISSUE = "Issue Number"
TITLE_AUTHOR = "Author name"
TITLE_TITLE = "Document Title"
TITLE_STARTYEAR = "Start year or range"
TITLE_ENDYEAR = "End year"
TITLE_YEAR = "Year"
TITLE_CITECOUNT = "Find Documents cited this many times"
TITLE_VIEWCOUNT = "Find Documents viewed this many times"
TITLE_VIEWEDWITHIN = "Find Documents viewed this many times within a period"
TITLE_FACETFIELDS = "List of field names for faceting"
TITLE_SORT = "Field names to sort by"
TITLE_LIMIT = "Document return limit"
TITLE_OFFSET = "Document return offset"
TITLE_DOCUMENT_ID = "Document ID or Partial ID"
TITLE_RETURNFORMATS = "Document return format"
TITLE_PAGELIMIT = "Number pages to return"
TITLE_PAGEREQUEST = "Document's Page or page range"
TITLE_PAGEOFFSET = "Relative page number (1 is the first) to return"
TITLE_TERMFIELD = "Default field for which to get term counts"
TITLE_TERMLIST = "Comma separated list of terms for which to get counts"
TITLE_IMAGEID = "Image ID (unique)"
TITLE_MOST_CITED_PERIOD = "Most cited articles"
TITLE_MOST_VIEWED_PERIOD = "Most viewed articles"
TITLE_PUBLICATION_PERIOD = "Number of Years" 
TITLE_CITED_MORETHAN = "Cited more than this many times"

ENDPOINT_SUMMARY_OPEN_API = "Return the OpenAPI specification for this API"
ENDPOINT_SUMMARY_DOCUMENTATION = "Return a HTML page for the interactive API documentation"
ENDPOINT_SUMMARY_CREATE_USER = "Create a new user for the system"
ENDPOINT_SUMMARY_CHANGE_PASSWORD = "Change the user's password"
ENDPOINT_SUMMARY_SUBSCRIBE_USER = "Add a new publication subscription for a user (Restricted)"
ENDPOINT_SUMMARY_WHO_AM_I = "Return information about the current user"
ENDPOINT_SUMMARY_SERVER_STATUS = "Return the server status"
ENDPOINT_SUMMARY_DOCUMENT_SUBMIT = "document_submission"
ENDPOINT_SUMMARY_LOGIN_BASIC = "Login a user more securely"
ENDPOINT_SUMMARY_TOKEN = "Endpoint from v1, needs to be implemented correctly for oauth"
ENDPOINT_SUMMARY_LICENSE_STATUS = "get_license_status.  Used in v1 for login (maybe oauth?)"
ENDPOINT_SUMMARY_LOGIN = "Login a user (less secure method)"
ENDPOINT_SUMMARY_LOGOUT = "Logout the user who is logged in"
ENDPOINT_SUMMARY_TERM_COUNTS = "Get term frequency counts"
ENDPOINT_SUMMARY_SEARCH_ADVANCED = "Advanced document search directly using OPAS schemas with OPAS return structures"
ENDPOINT_SUMMARY_SEARCH_V1 = "Search at the paragraph level by document zone (API v1 backwards compatible)"
ENDPOINT_SUMMARY_SEARCH_PARAGRAPHS = "Search at the paragraph (lowest) level by paragraph scope (doc, dreams, ...)"
ENDPOINT_SUMMARY_SEARCH_V2 = "Full search implementation, search at the full document or paragraph level"
ENDPOINT_SUMMARY_SEARCH_MORE_LIKE_THESE = "Full Search implementation, but expand the results to include 'More like these'"
ENDPOINT_SUMMARY_SEARCH_ANALYSIS = "Analyze search and return term/clause counts"
ENDPOINT_SUMMARY_EXTENDED_SEARCH = "Extends search for more Solr like flexibility. Requires API Token"
ENDPOINT_SUMMARY_MOST_VIEWED = "Return the most viewed journal articles published in this time period  (5, 10, 20, or ALL years)"
ENDPOINT_SUMMARY_MOST_CITED = "Return the most cited journal articles published in this time period (5, 10, 20, or ALL years)"
ENDPOINT_SUMMARY_WHATS_NEW = "Return the newest uploaded issues"
ENDPOINT_SUMMARY_CONTENTS_SOURCE = "Return the contents of the specified source in bibliographic format"
ENDPOINT_SUMMARY_CONTENTS_SOURCE_VOLUME = "Return the contents of the specified volume in bibliographic format"
ENDPOINT_SUMMARY_VIDEOS = "Return the list of available videostreams (video journals)"
ENDPOINT_SUMMARY_JOURNALS = "Return a list of available journals"
ENDPOINT_SUMMARY_VOLUMES = "Return a list of available volumes (and years) for sources"
ENDPOINT_SUMMARY_BOOK_NAMES = "Return a list of available books in bibliographic format (with additional info)"
ENDPOINT_SUMMARY_SOURCE_NAMES = "Return a list of available sources"
ENDPOINT_SUMMARY_AUTHOR_INDEX = "Return a list of matching author names"
ENDPOINT_SUMMARY_AUTHOR_PUBLICATIONS = "Return a bibliographic format list of publications matching the specified author pattern"
ENDPOINT_SUMMARY_ABSTRACT_VIEW = "Return an abstract"
ENDPOINT_SUMMARY_GLOSSARY_SEARCH = "Search the PEP Glossary"
ENDPOINT_SUMMARY_GLOSSARY_VIEW = "Return a glossary entry for the terms"
ENDPOINT_SUMMARY_DOCUMENT_VIEW = "Return a full document if open access or the current user is subscribed"
ENDPOINT_SUMMARY_IMAGE_DOWNLOAD = "Download an image"
ENDPOINT_SUMMARY_DOCUMENT_DOWNLOAD = "Download a document"

# temp directory used for generated downloads
TEMPDIRECTORY = tempfile.gettempdir()

MAX_PARAS_FOR_SUMMARY = 10

VIEW_PERIOD_LASTWEEK = "lastweek"
VIEW_PERIOD_LASTMONTH = "lastmonth"
VIEW_PERIOD_LAST6MONTHS = "last6months"
VIEW_PERIOD_LAST12MONTHS = "last12months"
VIEW_PERIOD_LASTCALYEAR = "lastcalendaryear"

VIEW_DBNAME_LASTWEEK = "vw_stat_docviews_lastweek"
VIEW_DBNAME_LASTMONTH = "vw_stat_docviews_lastmonth"
VIEW_DBNAME_LAST6MONTHS = "vw_stat_docviews_lastsixmonths"
VIEW_DBNAME_LAST12MONTHS = "vw_stat_docviews_last12months"
VIEW_DBNAME_LASTCALYEAR = "vw_stat_docviews_lastcalyear"


