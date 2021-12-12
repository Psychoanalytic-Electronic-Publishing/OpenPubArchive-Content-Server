# -*- coding: UTF-8 -*-

import os, sys
# import re, string

sys.path.append("e:\\usr3\py")
sys.path.append("e:\\usr3\py\sciHL")

__author__ = 'Neil R. Shapiro'  # must be single quotes for my addin code to setup.py to find it.
__version__ = '2021.10.31'
__copyright__   = "Copyright 2012-2021, Neil R. Shapiro and Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"

gPEPdbName = "pepa1db"
gPEPShortBldNbr = "21"          # new form of version
gPEPBuild = "A1v21"             # important to keep this matched to the current build
gReleaseYear = 2021             # Released in January of the indicated year

gLineLength = 110          # for drawing borders on error output (though hlLog can override)

# log details for the matching special error types
reMatchKey = "(warning|severe|fatal)"
gLogProgrammingWarnings = 0        # this is used to hide warnings that are intended to flag data showing possible coding issues.
import PEPJournalData

gXMLEditor = r"C:\Program Files\Oxygen XML Editor 21\oxygenAuthor21.1.exe"
gTextEditor = r"C:\Program Files\Notepad++\notepad++.exe"

gProgramLabel = os.path.basename(sys.argv[0]) + " Version " + __version__
gDisplayWidth = 80
#gLastYearBeforeWall = 2010 # this goes into the message abuot PEPCurrent
#gUnicodeProcessing = True
gSeriousErrorsOnly = True  # make the validation count warnings as info, so they aren't shown as errors, callnig more attn to the REAL errors
gDynamicDBGEdits = False   # Turn this on and PEPXML will open files with page number errors in XMetal as it finds them.

gMainSwitch = 0        # turn on or off debugging features, including the Edit Button
gDbg1 = 0*gMainSwitch  # Lotsa Debigging
gDbg2 = 1*gMainSwitch  # big picture
gDbg3 = 0*gMainSwitch  # Extra markup for QA
gDbg4 = 0*gMainSwitch  # Trace on screen
gDbg5 = 0*gMainSwitch  # timing related trace for optimize
gDbg6 = 0*gMainSwitch  # use this to switch to short output format
gDbg1True = True        # so we can put in a temp debug and find it later to turn it off.

#switch back to local DTD - 20171213
#gDefaultDTD = "http://peparchive.org/pepa1dtd/pepkbd3.dtd"
gDefaultDTD = r"X:\_PEPA1\_PEPa1v\pepkbd3.dtd"
gStopOnXMLError = False
gDefaultRoot = "pepbkd3"
gPreface1 = "<?xml version='1.0' ?>" # No need, it's the default and causes problems in LXML encoding='UTF-8' ?>"
gPreface2Template = "<!DOCTYPE $root SYSTEM '$dtd'>"
gDefaultPreface = r"<?xml version='1.0' encoding='UTF-8'?><!DOCTYPE pepkbd3 SYSTEM '%s'>" % gDefaultDTD

gDependentLocatorQueue = [] # queued locators to process after this set

# Parser options
gTrimSpaces = False

gIPHostAddress = "localhost"  # used mainly for programs that don't use settings files.

gConnect = {
    "host" : "localhost",
    "user" : "neil",
    "dbname" : "pepa1db",
    #"password" : 'fr',
    "port" : 3306,
}

gPEPBiblioDB = None
ALLVERSIONS = ["A1v5", "A1v6", "A1v7", "A1v8", "A1v9", "A1v10", "A1v11", "A1v12", "A1v13", "A1v14", "A1v15", "A1v16", "A1v17", "A1v18", "A1v19", "A1v20"]

# common attribute strings
NAME   = "name"
STYLE  = "style"
TYPE   = "type"
STATUS  = "status"
CLASS  = "class"

borderDash = 70*"-"+"\n"
borderEq = 70*"="+"\n"
borderStar = 70*"*"+"\n"

# These are generally useful patterns for regular expressions
ROMANPG = "m*(cm|dc{0,3}|cd|c{0,3})(xc|lx{0,3}|xl|x{0,3})(ix|vi{0,3}|iv|i{0,3})"
ROMANPGRG = "(%s(\-%s)?)" % (ROMANPG, ROMANPG)
DECPG = "(\d+)"
DECPGRG = "(%s(\-%s)?)" % ("\d+", "\d+")
DECORROMANPGRG = "(%s|%s)" % (DECPGRG, ROMANPGRG)
DECORROMANPG = "(%s|%s)" % (DECPG, ROMANPG)

DEFAULTENTITYFILEDB = r"c:\_pepA1\entityDictDB.dat"
#DEFAULTENTITYFILEDBALT = r"x:\_pepA1\entityDictDB.dat"

gDgrAbbr = {
    "PHD" : "Ph.D.",
    "MD"  : "M.D.",
    "SJ"  : "S.J.",         # Jesuit priest, I think
    "DSC" : "D.Sc.",
    "RN"  : "R.N." ,
    "DMH" : "DMH",
    "DDS" : "D.D.S.",
    "BS"  : "B.S." ,
    "BA"  : "B.A." ,
    "MS"  : "M.S." ,
    "MA"  : "M.A." ,
    "MB"  : "M.B." ,
    "EDD" : "ED.D.",
    "MPSY": "M.PSY.",
    "MSW" : "M.S.W."
}

global gJrnlData

try:
    gJrnlData = PEPJournalData.PEPJournalData()
except:
    pass # for standalone testing.

# threshold for declaring a PEP-Web exact match to reference
gDefaultRefMatchThresh = 0.70  # if a match limit isn't specified, this is the default for identify.
gOldRefMatchLowerLimit = 0.52  # default value for guess matching  algorithm
glowestRXLimitOrRemove = 0.35  # if this number or below, remove RX!
gNewRefMatchLowerLimit = gDefaultRefMatchThresh  # default value for identify matching algorithm

# threshold for writing CFRX to instance (related reference match)
gRelatedRXWriteToInstanceThreshold = 0.5
# threshold for saving CFRX to database
gRelatedRXWriteToDBThreshold = 0.5

# REFTYPES
REFBOOK                 =  "RefBook"
REFBOOKSERIES           =  "RefBookSeries"
REFJOURNALARTICLE       =  "RefJrnlArticle"        # (in journal)
REFBOOKARTICLE          =  "RefBookArticle"        # (article in book)
REFBOOKSERIESARTICLE    =  "RefBookSeriesArticle"  # (article in series book)
REFABSTRACT             =  "RefAbstract"
REFSECTION              =  "RefSection"            # Format of "section citation"

class REFCONSTANTS:
    # Article Info Constants - Field Names for article info and biblioentry dictionary
    CONFIDENCELEVEL     = "ConfidenceLevel"             # if this was a heuristic search from the DB, how good of a match was it?
    CONFIDENCETHRESH    = "ConfidenceThresh"            # if this was a heuristic search from the DB, how good of a match was it?
    CONFIDENCEBOOL      = "ConfidenceBoolean"           # If 1, sure enough to replace, if 0, not sure!
    EXACTMATCH          = "ExactMatch"                  # if an exact match, this is 1
    PEPREFVALID         = "Validated"                   # PEP Reference has been validated as existing in PEP
    DBUPDATESRATIO      = "DBUpdateSRatio"              # If data is taken from another reference, how similar is it?
    FULLTEXT            = "ReferenceText"               # Full text of reference
    XMLREF              = "XMLRef"                      # Full XML of the reference
                                                        # This field may not always be populated
    TITLE               = "Title"                       # Title of article, article in book, or book if not edited
    SUBTITLE            = "SubTitle"                    # SubTitle of article, article in book, or book if not edited A1v6
    SOURCETITLESERIES   = "SourceTitleSeries"           # Title of source: Journal name or series book title, such as International Psychoanalytic Library;
    SOURCETITLEFULL     = "SourceTitleFull"             # Full title of journal/series, not abbreviated
    SOURCETITLEABBR     = "SourceTitleAbbr"             # Official abbreviation for SOURCETITLESERIES (journal name or Book) in bibliographies
    SOURCETITLECITED    = "SourceTitleCited"            # Title of Source as originally cited in a reference
    BKALSOKNOWNAS       = "BookAlsoKnownAs"             # List of alternate names for the book
                                                            #
                                                            # Regular Book or Non Series Entire Book Name:
                                                            #   Title:              Book Name
                                                            #   SourceTitleCited:   None
                                                            #   SourceTitleSeries:  None
                                                            #
                                                            # Series Book:
                                                            #   Title:              Book Name
                                                            #   SourceTitleCited:   None
                                                            #   SourceTitleSeries:  Series Name (Abbr)
                                                            #   SourceTitleAbbr:    Series Name Abbreviation
                                                            #
                                                            # Article in Edited Book:
                                                            #   Title:              Article
                                                            #   SourceTitleCited:   Book Name
                                                            #   SourceTitleSeries:  None
                                                            #
                                                            # Article in Edited Book Part of Series:
                                                            #   Title:              Article
                                                            #   SourceTitleCited:   Book Name
                                                            #   SourceTitleSeries:  Series Name Abbr
                                                            #   SourceTitleAbbr:    Series Name Abbreviation

    SOURCEPEPCODE       = "JournalCode"                 # PEP Journal Abbreviation or "OTH" for other nonPEP journals or books
    ARTTYPE             = "ArticleType"                 # Decoded type of reference
    ARTDOI              = "ArticleDOI"                  # DOI for the reference or the article.
    ARTLANG             = "ArticleLanguage"             # New A1v8r2
    ARTQUAL             = "artqual"                     # Link to "common" article this one comments on
    ARTKWDS             = "artkwds"                     # Store article Keywords
    REFTYPE             = "RefType"                     # Decoded type of reference
                                                            #   1 = REFBOOK
                                                            #   2 = REFBOOKSERIES
                                                            #   3 = REFJOURNALARTICLE
                                                            #   4 = REFBOOKARTICLE
    REFINPEP            = "RefInPEP"                    # Set to 1 if source is PEP, 0 or None otherwise
    AUTHORS             = "Authors"                     #
    AUTHLIST            = "AuthList"                    #
    BAUTHORS            = "BookAuthors"                 # Added 20071206 to accomodate the book authors/editors in an edited book
    BAUTHLIST           = "BookAuthList"                # Added 20071206 to accomodate the book authors/editors in an edited book
    TYPEREASON          = "TypeReason"                  # Reason it was classified this way
    REASON              = "Reason"                      #
    PROBABLESOURCE      = "ProbableSource"              # Callers declaration of journal name or book title
    PUBLISHER           = "publisher"                   # Publisher, mainly used for books.  Note this must match the "publisher" column name in articles and issn
    PUBLISHERNAME       = "publisherName"               # Publisher, mainly used for books.  Note this must match the "publisher" column name in articles and issn
    PUBLISHERLOC        = "publisherLocation"           # Publisher, mainly used for books.  Note this must match the "publisher" column name in articles and issn
    YEAR                = "Year"                        # Official Publication year
    BOOKYEAR            = "BookYear"                    # Book Publication year
    VOL                 = "Vol"                         # Volume of journal or book series
    PEPVOL              = "PEPVol"                      # Used for templates, to allow a volume for articleID when it's made up and we blank "Vol"
    VOLSUFFIX           = "VolSuffix"                   # Volume suffix (for supplements)
    VOLNUMBER           = "volNumber"                   # Volume, numeric only
    VOLLIST             = "VolList"                     # Used to hold the list of volumes when more than one matches the year.  New for A1v6
    ISSUE               = "Issue"                       # Issue of journal
    ORIGRX              = "Origrx"                      # The ID of the original aritcle/book
    PGRG                = "PgRg"                        # Hyphenated Page range, e.g., 1-14
    PGSTART             = "PgStart"                     # Starting page number, arabic numbers
    PGVAR               = "PgVar"                       # Page Variant, assigned when more than one article per page
    PGEND               = "PgEnd"                       # Ending page number, arabic numbers
    PAGECOUNT           = "Pagecount"                   # Page count used on output of books
    NEWSECNAME          = "NewSecName"                  # Article begins a new section with this name
    NEWSECLEVEL         = "NewSecLevel"                 # Add on (2019) to indent articles and section names
    KEY                 = "Key"                         # PEP Locator or non-pep derived key
    LOCALID             = "LocalID"                     # Used to specify a local ID to be added to the key for a given location reference
    REFINTID            = "RefIntID"                    # XML Internal ID, unique only within the instance
    #ARTICLEID          = "ArticleID"                   # used to store a locator when passing around the reference
    # defined but not currently (A1v4) used
    JOURNALISS          = "JournalIssue"
    JOURNALVOLSUFFIX    = "jrnlVolSuffix"
    # added for A1v5
    PARTNEXT            = "partNext"                    # Next article in broken up book
    PARTPREV            = "partPrev"                    # prev article in broken up book
    PARTEXTRACT         = "partExtract"                 # this is an extract; titles should have book title appended
    # author dict names (match XML KBD3)
    AUTHORNAMEPREFIX    = "nprefx"
    AUTHORNAMEFIRST     = "nfirst"
    AUTHORNAMEFIRSTMID  = "nfirstmid"                   #First name, middle name
    AUTHORNAMEMID       = "nmid"
    AUTHORNAMELAST      = "nlast"
    AUTHORNAMESUFX      = "nsufx"
    AUTHORNAMENDEG      = "ndeg"
    AUTHORNAMENBIO      = "nbio"
    AUTHORNAMENTI       = "nti"
    AUTHORNAMEROLE      = "role"
    AUTHORNAMELISTED    = "listed"                     # if false, this author not part of biblio listing...still shown in title area
    AUTHORNAMEPOS       = "authorpos"                  # 1 for first author, 2 for second, etc.
    AUTHORNAMEPTITLE    = "ptitle"
    ISSN                = "ISSN"
    ISBN                = "ISBN-10"                    # Note: the DB column is ISBN-10 (or 13), but the attrib is ISBN
    ISBN13              = "ISBN-13"                    # Note: the DB column is ISBN-13
    ISUN                = "ISUN"
    MAINTOCID           = "MAINTOCID"
    DOWNLOAD            = "download"                   # Added 2021-10-05 to allow general prohibition of downloads
    SIMILARITYRATIOS    = "SimilarityRatios"           # a dictionary after a similarity compare

gConst = REFCONSTANTS()
# used to determine the reference style type, and booktype REFBOOKARTICLE
gBookCodes = ["CBK", "ZBK", "IPL", "NLP", "WMK", "SE", "GW"]
# Recorded results in gConst.REFTYPE, REFBOOK or REFBOOKSERIES

gAnnualsThatAreTranslations = ["ANIJP-FR", "ANIJP-IT", "ANIJP-EL", "ANIJP-TR", "ANIJP-DE", "ANRP"]

# Series Classic books with their own code, to add CBK as well.
gBookClassicSeries = ["IPL", "NLP", "SE", "ZBK"]                       # 3-13-2008, added missing ZBK here.
gJrnlNoIssueInfo = ["AOP", "PSC", "PY", "ANIJP-IT", "ANIJP-FR", "ANIJP-TR", "ANIJP-EL"]              # 2008-09-07, added to make sure a no-issues volume isn't given an issue number on the one issue each year.

gSplitCodesForGetProximateArticle = ["CBK", "ZBK", "IPL", "NLP", "WMK", "SE", "GW"]

# put CRs after these elements
breakAfterList = [
    "abs",
    "addr",
    "artauth",
    "artinfo",
    "artiss",
    "artpgrg",
    "arttitle",
    "artvol",
    "artyear",
    "aut",
    "autaff",
    "be",
    "bib",
    "colspec",
    "entry",
    "figure",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "li",
    "list",
    "ln",
    "p",
    "p2",
    "pb",
    "rd",
    "row",
    "table",
    "tbl",
    "tbody",
    "tgroup",
    "thead",
]

# List of split books using basecode notation.
# If the data is 0, then the book has a mainTOC instance;
# if the data is 1, it starts with the 0001 instance
gSplitBooks = {
    "IPL002" : 0,
    "IPL052" : 0,
    "IPL059" : 0,
    "IPL084" : 0,
    "IPL089" : 0,
    "IPL105" : 1,
    "NLP014" : 0,
    "GW001"  : 0,
    "GW002"  : 0,
    "GW003"  : 0,
    "GW004"  : 0,
    "GW005"  : 0,
    "GW006"  : 0,
    "GW007"  : 0,
    "GW008"  : 0,
    "GW009"  : 0,
    "GW010"  : 0,
    "GW011"  : 0,
    "GW012"  : 0,
    "GW013"  : 0,
    "GW014"  : 0,
    "GW015"  : 0,
    "GW016"  : 0,
    "GW017"  : 0,
    "GW018"  : 0,
    "GW018S" : 0,
    "SE001"  : 0,
    "SE002"  : 0,
    "SE003"  : 0,
    "SE004"  : 0,
    "SE005"  : 0,
    "SE006"  : 0,
    "SE007"  : 0,
    "SE008"  : 0,
    "SE009"  : 0,
    "SE010"  : 0,
    "SE011"  : 0,
    "SE012"  : 0,
    "SE013"  : 0,
    "SE014"  : 0,
    "SE015"  : 0,
    "SE016"  : 0,
    "SE017"  : 0,
    "SE018"  : 0,
    "SE019"  : 0,
    "SE020"  : 0,
    "SE021"  : 0,
    "SE022"  : 0,
    "SE023"  : 0,
    "SE024"  : 0,
    "ZBK025" : 0,
    "ZBK026" : 0,
    "ZBK027" : 0,
    "ZBK028" : 0,
    "ZBK029" : 0,
    "ZBK038" : 0,
    "ZBK041" : 0,
    "ZBK042" : 0,
    "ZBK050" : 0,
    "ZBK051" : 0,
    "ZBK052" : 0,
    "ZBK054" : 0,
    "ZBK069" : 0,
    "ZBK073" : 0,
    "ZBK074" : 0,
    "ZBK075" : 0,
    "ZBK078" : 0,
    "ZBK079" : 0,
    "ZBK080" : 0,
    "ZBK081" : 0,
    "ZBK133" : 0,
    "ZBK141" : 0,
    "ZBK145" : 0

}

# Used to generate the index of classic books (excluding SE and GW,, done separately)
gClassicBookTOCList = {
    "IPL.002.0000"  :  "IPL.002.0000",  # A1v7 Ferenczi
    "IPL.022.0001"  :  "IPL.022.0001",  # A1v4 Start
    "IPL.045.0001"  :  "IPL.045.0001",  # A1v4 Jones
    "IPL.052.0000"  :  "IPL.052.0000",
    "IPL.055.0001"  :  "IPL.055.0001",
    "IPL.059.0000"  :  "IPL.059.0000",  #A1v7 Meng
    "IPL.064.0001"  :  "IPL.064.0001",  #A1v6 Winnicott
    "IPL.073.0001"  :  "IPL.073.0001",  #A1v7 Racker
    "IPL.076.0001"  :  "IPL.076.0001",  #A1v7 Milner
    "IPL.079.0001"  :  "IPL.079.0001",  #A1v7 Bowlby
    "IPL.084.0000"  :  "IPL.084.0000",  #A1v7 EFreud
    "IPL.087.0001"  :  "IPL.087.0001",
    "IPL.089.0000"  :  "IPL.089.0000",  # A1v7
    "IPL.094.0001"  :  "IPL.094.0001",
    "IPL.095.0001"  :  "IPL.095.0001",
    "IPL.100.0001"  :  "IPL.100.0001",
    "IPL.104.0001"  :  "IPL.104.0001",
    "IPL.105.0001"  :  "IPL.105.0001",
    "IPL.107.0001"  :  "IPL.107.0001",
    "IPL.109.0001"  :  "IPL.109.0001",  #A1v7 Bowlby
    "IPL.115.0001"  :  "IPL.115.0001",
    "IPL.118.0001"  :  "IPL.118.0001",
    "NLP.001.0001"  :  "NLP.001.0001",
    "NLP.003.0001"  :  "NLP.003.0001",
    "NLP.005.0001"  :  "NLP.005.0001",
    "NLP.009.0001"  :  "NLP.009.0001",  # A1v7
    "NLP.011.0001"  :  "NLP.011.0001",
    "NLP.014.0000"  :  "NLP.014.0000",  # A1v7
    "ZBK.002.0001"  :  "ZBK.002.0001",
    "ZBK.003.0001"  :  "ZBK.003.0001",
    "ZBK.004.0001"  :  "ZBK.004.0001",
    "ZBK.005.0001"  :  "ZBK.005.0001",
    "ZBK.006.0001"  :  "ZBK.006.0001",
    "ZBK.007.0001"  :  "ZBK.007.0001",
    "ZBK.015.0001"  :  "ZBK.015.0001",
    "ZBK.016.0001"  :  "ZBK.016.0001",
    "ZBK.017.0001"  :  "ZBK.017.0001",
    "ZBK.020.0001"  :  "ZBK.020.0001",  # A1v4 End
    "ZBK.025.0000"  :  "ZBK.025.0000",
    "ZBK.026.0000"  :  "ZBK.026.0000",
    "ZBK.027.0000"  :  "ZBK.027.0000",
    "ZBK.028.0000"  :  "ZBK.028.0000",
    "ZBK.029.0000"  :  "ZBK.029.0000",  # A1v7
    "ZBK.033.0001"  :  "ZBK.033.0001",  # A1v7
    # "ZBK.034.0001"    :  "ZBK.034.0001",  # A1v8
    "ZBK.038.0000"  :  "ZBK.038.0000",  # A1v7
    "ZBK.041.0000"  :  "ZBK.041.0000",
    "ZBK.042.0000"  :  "ZBK.042.0000",
    "ZBK.045.0001"  :  "ZBK.045.0001",  # A1v7
    "ZBK.046.0001"  :  "ZBK.046.0001",  # A1v7
    "ZBK.047.0001"  :  "ZBK.047.0001",  # A1v7
    "ZBK.048.0001"  :  "ZBK.048.0001",  # A1v12 Money-Kyrle
    # "ZBK.049.0001"    :  "ZBK.049.0001",  # A1v8
    "ZBK.050.0000"  :  "ZBK.050.0000",  # A1v7
    "ZBK.051.0000"  :  "ZBK.051.0000",  # A1v7
    "ZBK.052.0000"  :  "ZBK.052.0000",
    "ZBK.054.0000"  :  "ZBK.054.0000",
    "ZBK.055.0001"  :  "ZBK.055.0001",
    "ZBK.056.0001"  :  "ZBK.056.0001",
    "ZBK.061.0001"  :  "ZBK.061.0001",
    "ZBK.062.0001"  :  "ZBK.062.0001",

    "ZBK.070.0001"  :  "ZBK.070.0001", # A1v11
    "ZBK.071.0001"  :  "ZBK.071.0001",
    "ZBK.072.0001"  :  "ZBK.072.0001",
    "ZBK.073.0000"  :  "ZBK.073.0000",
    "ZBK.074.0000"  :  "ZBK.074.0000",
    "ZBK.075.0000"  :  "ZBK.075.0000",
    "ZBK.076.0001"  :  "ZBK.076.0001",
    "ZBK.077.0001"  :  "ZBK.077.0001",
    "ZBK.078.0000"  :  "ZBK.078.0000",
    "ZBK.079.0000"  :  "ZBK.079.0000",
    "ZBK.080.0000"  :  "ZBK.080.0000",
    "ZBK.081.0000"  :  "ZBK.081.0000",
    "ZBK.131.0001"  :  "ZBK.131.0001",
    "ZBK.132.0001"  :  "ZBK.132.0001",
    "ZBK.133.0000"  :  "ZBK.133.0000",
    "ZBK.134.0001"  :  "ZBK.134.0001",
    "ZBK.135.0001"  :  "ZBK.135.0001",
    "ZBK.136.0001"  :  "ZBK.136.0001",
    "ZBK.137.0001"  :  "ZBK.137.0001",
    "ZBK.138.0001"  :  "ZBK.138.0001",
    "ZBK.139.0001"  :  "ZBK.139.0001",
    "ZBK.140.0001"  :  "ZBK.140.0001",
    "ZBK.141.0000"  :  "ZBK.141.0000",
    "ZBK.142.0001"  :  "ZBK.142.0001",
    "ZBK.143.0001"  :  "ZBK.143.0001",
    "ZBK.144.0001"  :  "ZBK.144.0001",
    "ZBK.145.0000"  :  "ZBK.145.0000",
    "ZBK.146.0001"  :  "ZBK.146.0001",
    "ZBK.147.0001"  :  "ZBK.147.0001",
    "ZBK.148.0001"  :  "ZBK.148.0001",
    "ZBK.149.0001"  :  "ZBK.149.0001",
    "ZBK.150.0001"  :  "ZBK.150.0001",
    "ZBK.151.0001"  :  "ZBK.151.0001",
    "ZBK.152.0001"  :  "ZBK.152.0001",
    "ZBK.153.0001"  :  "ZBK.153.0001",
    #    "ZBK.154.0001"  :  "ZBK.154.0001",  # Missing book
    "ZBK.155.0001"  :  "ZBK.155.0001",
    "ZBK.156.0001"  :  "ZBK.156.0001",
    "ZBK.160.0001"  :  "ZBK.160.0001",
}

gSEIndex =         {
    "SE.001.0000"   :  "SE.001.0000",
    "SE.002.0000"   :  "SE.002.0000",
    "SE.003.0000"   :  "SE.003.0000",
    "SE.004.0000"   :  "SE.004.0000",
    "SE.005.0000"   :  "SE.005.0000",
    "SE.006.0000"   :  "SE.006.0000",
    "SE.007.0000"   :  "SE.007.0000",
    "SE.008.0000"   :  "SE.008.0000",
    "SE.009.0000"   :  "SE.009.0000",
    "SE.010.0000"   :  "SE.010.0000",
    "SE.011.0000"   :  "SE.011.0000",
    "SE.012.0000"   :  "SE.012.0000",
    "SE.013.0000"   :  "SE.013.0000",
    "SE.014.0000"   :  "SE.014.0000",
    "SE.015.0000"   :  "SE.015.0000",
    "SE.016.0000"   :  "SE.016.0000",
    "SE.017.0000"   :  "SE.017.0000",
    "SE.018.0000"   :  "SE.018.0000",
    "SE.019.0000"   :  "SE.019.0000",
    "SE.020.0000"   :  "SE.020.0000",
    "SE.021.0000"   :  "SE.021.0000",
    "SE.022.0000"   :  "SE.022.0000",
    "SE.023.0000"   :  "SE.023.0000",
    "SE.024.0000"   :  "SE.024.0000"
}

gGWIndex =         {
    "GW.001.0000"   :  "GW.001.0000",
    "GW.002.0000"   :  "GW.002.0000", # this is a combined vol 2/3
    "GW.004.0000"   :  "GW.004.0000",
    "GW.005.0000"   :  "GW.005.0000",
    "GW.006.0000"   :  "GW.006.0000",
    "GW.007.0000"   :  "GW.007.0000",
    "GW.008.0000"   :  "GW.008.0000",
    "GW.009.0000"   :  "GW.009.0000",
    "GW.010.0000"   :  "GW.010.0000",
    "GW.011.0000"   :  "GW.011.0000",
    "GW.012.0000"   :  "GW.012.0000",
    "GW.013.0000"   :  "GW.013.0000",
    "GW.014.0000"   :  "GW.014.0000",
    "GW.015.0000"   :  "GW.015.0000",
    "GW.016.0000"   :  "GW.016.0000",
    "GW.017.0000"   :  "GW.017.0000",
    "GW.018.0000"   :  "GW.018.0000",
    "GW.018S.0000"   :  "GW.018S.0000",
}

# I don't think this is used...removed for A1v9
# Use this to find the default instance for SE Volumes
#gSEDefaults =         {
#                          "SE001" :  "SE.001.0000",
#                          "SE002" :  "SE.002.0000",
#                          "SE003" :  "SE.003.0000",
#                          "SE004" :  "SE.004.0000",
#                          "SE005" :  "SE.005.0000",
#                          "SE006" :  "SE.006.0000",
#                          "SE007" :  "SE.007.0000",
#                          "SE008" :  "SE.008.0000",
#                          "SE009" :  "SE.009.0000",
#                          "SE010" :  "SE.010.0000",
#                          "SE011" :  "SE.011.0000",
#                          "SE012" :  "SE.012.0000",
#                          "SE013" :  "SE.013.0000",
#                          "SE014" :  "SE.014.0000",
#                          "SE015" :  "SE.015.0000",
#                          "SE016" :  "SE.016.0000",
#                          "SE017" :  "SE.017.0000",
#                          "SE018" :  "SE.018.0000",
#                          "SE019" :  "SE.019.0000",
#                          "SE020" :  "SE.020.0000",
#                          "SE021" :  "SE.021.0000",
#                          "SE022" :  "SE.022.0000",
#                          "SE023" :  "SE.023.0000",
#                          "SE024" :  "SE.024.0000",
#                      }

# If it's NOT part of PEP, the value is 0.  When it goes in PEP, indicate the version
# number it went in.  This will help (though not done now) if we had to rebuild a previous
# version (but again, coding would need to be added there.)

gBooksNotYetInPEP = {
    "IPL002" : "A1v7",
    "IPL022" : "A1v5",
    "IPL045" : "A1v7",
    "IPL052" : "A1v7",
    "IPL055" : "A1v5",
    "IPL059" : "A1v7",
    "IPL064" : "A1v5",
    "IPL073" : "A1v7",
    "IPL076" : "A1v7",
    "IPL079" : "A1v7",
    "IPL084" : "A1v7",
    "IPL087" : "A1v5",
    "IPL089" : "A1v7",
    "IPL094" : "A1v5",
    "IPL095" : "A1v7",
    "IPL100" : "A1v5",
    "IPL104" : "A1v5",
    "IPL105" : "A1v7",
    "IPL107" : "A1v5",
    "IPL109" : "A1v7",
    "IPL115" : "A1v5",
    "IPL118" : "A1v5",
    "NLP001" : "A1v5",
    "NLP002" : 0,
    "NLP003" : "A1v7",
    "NLP004" : 0,
    "NLP005" : "A1v5",
    "NLP006" : 0,
    "NLP007" : 0,
    "NLP008" : 0,
    "NLP009" : "A1v7",
    "NLP010" : 0,
    "NLP011" : "A1v5",
    "NLP014" : "A1v7",
    "NLP021" : 0,
    "NLP038" : 0,
    "NLP040" : 0,
    "ZBK002" : "A1v5",
    "ZBK003" : "A1v5",
    "ZBK004" : "A1v5",
    "ZBK005" : "A1v5",
    "ZBK006" : "A1v5",
    "ZBK007" : "A1v5",
    "ZBK015" : "A1v5",
    "ZBK016" : "A1v5",
    "ZBK017" : "A1v5",
    "ZBK020" : "A1v5",
    "ZBK025" : "A1v5",
    "ZBK026" : "A1v5",
    "ZBK027" : "A1v5",
    "ZBK028" : "A1v5",
    "ZBK029" : "A1v7",
    "ZBK030" : 0,
    "ZBK031" : 0,
    "ZBK032" : 0,
    "ZBK033" : "A1v7",
    "ZBK034" : 0,
    "ZBK035" : 0,
    "ZBK036" : 0,
    "ZBK037" : 0,
    "ZBK038" : "A1v7",
    "ZBK039" : 0,
    "ZBK040" : 0,
    "ZBK041" : "A1v5",
    "ZBK042" : "A1v5",
    "ZBK043" : 0,
    "ZBK044" : 0,
    "ZBK045" : "A1v7",
    "ZBK046" : "A1v7",
    "ZBK047" : "A1v7",
    "ZBK048" : "A1v12",
    "ZBK049" : 0,
    "ZBK050" : "A1v7",
    "ZBK051" : "A1v7",
    "ZBK052" : "A1v5",
    "ZBK053" : 0,
    "ZBK054" : "A1v7",
    "ZBK055" : "A1v7",
    "ZBK056" : "A1v7",
    "ZBK061" : "A1v9",
    "ZBK062" : "A1v9",
    "ZBK069" : "A1v9",
    "ZBK070" : "A1v11",
    "ZBK071" : "A1v11",
    "ZBK072" : "A1v11",
    "ZBK073" : "A1v11",
    "ZBK074" : "A1v11",
    "ZBK075" : "A1v11",
    "ZBK076" : "A1v11",
    "ZBK077" : "A1v11",
    "ZBK078" : "A1v11",
    "ZBK079" : "A1v11",
    "ZBK080" : "A1v11",
    "ZBK081" : "A1v11",
    "ZBK130" : "A1v12",
    "ZBK131" : "A1v12",
    "ZBK132" : "A1v12",
    "ZBK133" : "A1v12",
    "ZBK134" : "A1v12",
    "ZBK135" : "A1v12",
    "ZBK136" : "A1v12",
    "ZBK137" : "A1v12",
    "ZBK138" : "A1v12",
    "ZBK139" : "A1v12",
    "ZBK140" : "A1v12",
    "ZBK141" : "A1v12",
    "ZBK142" : "A1v12",
    "ZBK143" : "A1v12",
    "ZBK144" : "A1v12",
    "ZBK145" : "A1v12",
    "ZBK146" : "A1v12",
    "ZBK147" : "A1v12",
    "ZBK148" : "A1v12",
    "ZBK149" : "A1v12",
    "ZBK150" : "A1v12",
    "ZBK151" : "A1v12",
    "ZBK152" : "A1v12",
    "ZBK153" : "A1v12",
    "ZBK154" : "A1v12",
    "ZBK155" : "A1v12",
    "ZBK156" : "A1v12",
    "ZBK160" : "A1v12",

    "SE001" :  "A1v6",
    "SE002" :  "A1v6",
    "SE003" :  "A1v6",
    "SE004" :  "A1v6",
    "SE005" :  "A1v6",
    "SE006" :  "A1v6",
    "SE007" :  "A1v6",
    "SE008" :  "A1v6",
    "SE009" :  "A1v6",
    "SE010" :  "A1v6",
    "SE011" :  "A1v6",
    "SE012" :  "A1v6",
    "SE013" :  "A1v6",
    "SE014" :  "A1v6",
    "SE015" :  "A1v6",
    "SE016" :  "A1v6",
    "SE017" :  "A1v6",
    "SE018" :  "A1v6",
    "SE019" :  "A1v6",
    "SE020" :  "A1v6",
    "SE021" :  "A1v6",
    "SE022" :  "A1v6",
    "SE023" :  "A1v6",
    "SE024" :  "A1v6",
    "GW001" :  "A1v9",
    "GW002" :  "a1v9",
    "GW003" :  "a1v9",
    "GW004" :  "a1v9",
    "GW005" :  "a1v9",
    "GW006" :  "a1v9",
    "GW007" :  "a1v9",
    "GW008" :  "a1v9",
    "GW009" :  "a1v9",
    "GW010" :  "a1v9",
    "GW011" :  "a1v9",
    "GW012" :  "a1v9",
    "GW013" :  "a1v9",
    "GW014" :  "a1v9",
    "GW015" :  "a1v9",
    "GW016" :  "a1v9",
    "GW017" :  "a1v9",
    "GW018" :  "a1v9",
    "GW018S" :  "a1v11",
}


# constants for older log_error statements (new code should use HLErrorLog class.
HLINFO = 1
HLWARNING =    2
HLSEVERE = 3
HLFATAL    = 4

#==================================================================================================
# Main Standalone (Test) Routines
#==================================================================================================
if __name__ == "__main__":

    pass
    # can't test this directly because of pepjournal calls pepglobals
    #print gJrnlData.getVol("IRP", "1974")
    #print gJrnlData.getVol("IJP", "1978")
    #print gJrnlData.getVol("JAA", "1973")

    #print gConst.AUTHORS
