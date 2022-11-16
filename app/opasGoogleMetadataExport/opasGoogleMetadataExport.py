#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
# Disable many annoying pylint messages, warning me about variable naming for example.
# yes, in my Solr code I'm caught between two worlds of snake_case and camelCase.

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2022.0906/v1.0.0" 
__status__      = "Development"

programNameShort = "opasGoogleMetadataExport"

import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

print(
    f""" 
    {programNameShort} - Open Publications-Archive Server (OPAS) - Google Metadata Exporter
    
        Create Google Metadata from the OPAS Database
        
        TBD: Still need to add book processing!
        
        Example Invocation:
                $ python {programNameShort}.py --recordsperfile=8000 --maxrecords=200000 --bucket pep-web-google
                
        Help for option choices:
         -h, --help  List all help options
    """
)

import os
import re
# import codecs
import time
import logging
from datetime import datetime

from lxml import objectify

sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')
import localsecrets
import opasFileSupport
from opasAPISupportLib import metadata_get_source_info  
import opasPySolrLib
from configGoogleMeta import googleMetadataConfig

# import inspect
# from inspect import cleandoc

logger = logging.getLogger(programNameShort)

from optparse import OptionParser
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

tplBookChapter = """
            <article>
              <front>
                <!-- Information about the book. (REQUIRED) -->
                |&BOOKMAINTOCMETA;|
               |&BOOKCHAPTERMETA;|
              </front>
              <!-- Type of book or chapter. (OPTIONAL. acceptable values:  research-article -->
              <!--  book-chapter, phd-thesis, ms-thesis, bs-thesis, technical-report, unpublished, -->
              <!-- review-article, patent, other -->
              <article-type>book-chapter</article-type>
            </article>
            """

tplBookMainTOCMeta = """
        <book-meta>
          <!-- Book title. (REQUIRED; no more than 128 chars) -->
          <book-title>&TITLE;</book-title>
          <!-- ISBN for the book.  -->
          <!-- (REQUIRED; no more than 128 characters) -->
          <isbn>&ISBN;</isbn>
          <!-- Metadata for the publisher. (REQUIRED) -->
          <publisher>
             <!-- Name of publisher. (REQUIRED; no more than 128 characters) -->
             <publisher-name>&PUBLISHER;</publisher-name>
          </publisher>
          <!-- Author/editor names for the book. (REQUIRED; No more than 1024 entries) -->
          <!-- If chapters have different authors, do not include them here -->
          <!-- Acceptable values:  author, editor -->
             <contrib-group>
               &BOOKAUTHORMARKUP;
             </contrib-group>
          <!-- Date of publication. (REQUIRED; Gregorian calendar) -->
          <pub-date pub-type="pub">
            <!-- Year of publication. Full four digit. (REQUIRED) -->
            <year>&YEAR;</year>
          </pub-date>
        </book-meta>
"""

# this is part of the bookmeta, not for use on it's own
tplChapterMeta = """
                <!-- Information about the chapter. (REQUIRED) -->
                <chapter-meta>
                    <title-group>
                      <!-- Title of the chapter. (REQUIRED; no more than 512 chars) -->
                      <chapter-title>&TITLE;</chapter-title>
                    </title-group>

                    <!-- Information about the chapter contributors. (OPTIONAL) -->
                    <contrib-group>
                      &AUTHORMARKUP;
                    </contrib-group>

                    |<!-- Chapter number. (REQUIRED) -->
                    <chapter-number>&CHAPTERNUMBER;</chapter-number>|

                    <!-- First page. (REQUIRED) -->
                    <fpage>&PGSTART;</fpage>

                    <!-- Last page. (REQUIRED) -->
                    <lpage>&PGEND;</lpage>

                    <!-- URLs for the chapter (REQUIRED; no more than 1024 characters).  -->
                    <!-- It is CRUCIAL that at least one instance of this field be present -->
                    <self-uri xlink:href="https://pep-web.org/browse/document/&KEY;"/>

                  </chapter-meta>
            """

tplAuth = """
                   <!-- Author names. (REQUIRED; No more than 1024 entries) -->
                   <contrib contrib-type="&ROLE;">
                     <name>

                       <!-- Last name of an author. (REQUIRED; No more than 32 characters -->
                       <surname>&NLAST;</surname>

                       <!-- Given names of an author - includes first and middle names if -->
                       <!-- any. (REQUIRED; no more than 48 characters -->
                       <given-names>&NFIRSTMID;</given-names>

                       |<!-- Suffix for the author - Jr/Sr/III etc. (OPTIONAL; no more than 8 chars) -->
                       <suffix>&NSUFX;</suffix>|

                   </name>
                 </contrib>
                  """

tplNoAuth = """
                   <!-- Author name Template used when there are no authors because its REQUIRED -->
                   <contrib contrib-type="">
                     <name>
                       <surname></surname>
                       <given-names></given-names>
                   </name>
                 </contrib>
                  """

def val_or_emptystr(obj, default=""):
    ret_val = ""
    try:
        if obj is not None:
            ret_val = f"{obj}"
    except Exception as e:
        print (f"Exception: {e}")

    return ret_val

def find_or_emptystr(elem, find_target: str, default=""):
    ret_val = ""
    try:
        node = elem.find(find_target)
        if node is not None:
            ret_val = ''.join(node.itertext())
    except Exception as e:
        print (f"Exception: {e}")
    else:
        if ret_val is None:
            ret_val = ""

    return ret_val

#--------------------------------------------------------------------------------
def writePublisherFile(path=None, fs=None, online_link_location="http://peparchive.org/links/pepwebmeta/%s.xml", publisher_file_name = r"publisher-info.xml", doValidate=False, path_is_root_bucket=False):
    pat = ".*\.xml"
    metadata_files_names = fs.get_matching_filelist(filespec_regex=pat, path=path)
    #fileInfo = {}
    publisher_file_cumulated_text = ""
    count = 0
    for filename in metadata_files_names:
       
        count += 1
        #if count == 5: break
        #if fs is None:
            #basename, ext = os.path.splitext(filename)
            #full_filename = os.path.join(path, filename)
            #fstatout = os.stat(full_filename)
            #fileTime = fstatout[stat.ST_MTIME]
        #else:
        basename, ext = os.path.splitext(filename.basename)
        if filename.basename == publisher_file_name:
            continue
        
        #if fs.key is not None:
            #full_filename = filename.fileinfo["name"]
        #else:
            #full_filename = filename.filespec
            
        #fileTime = filename.create_time
            
        year, month, day, hour, minute, second, weekday, day360, dst = time.localtime(filename.timestamp.timestamp())
        #print "File Date/Time: ", fileTime, fileTimeAlt
        #print year, month, day, hour, minute, second, weekday, day, dst
        filenameplusloc = online_link_location + filename.basename
        tplPublisherFile = f"""
                            <!-- Information about one file. -->
                            <file>
                               <!-- Url for a metadata file. (REQUIRED; no more than 1024 chars) -->
                               <url>{filenameplusloc}</url>
        
                               <!-- The date on which this file was last updated. (OPTIONAL; -->
                               <!-- Gregorian calendar) -->
                               <change-date>
                                  <!-- date of change. (REQUIRED) -->
                                  <day>{day}</day>
        
                                  <!-- month of change. (REQUIRED; `1-12) -->
                                  <month>{month}</month>
        
                                  <!-- year of change. (REQUIRED; four digit) -->
                                  <year>{year}</year>
                               </change-date>
                            </file>
                            """
        
        publisher_file_cumulated_text += tplPublisherFile

    tplPublisher = f"""<?xml version="1.0" encoding="UTF-8"?>  <!-- encoding must be UTF-8 -->
{googleMetadataConfig.GOOGLE_METADATA_PUBLISHER_DOCTYPE}
<!-- Information related to content from one publisher for Google Scholar. -->
<!-- This includes preferred name, contact person, and links to metadata files. -->
<publisher>
   <!-- Name of the publisher. (REQUIRED; no more than 128 chars) -->
   <publisher-name>Psychoanalytic Electronic Publishing</publisher-name>

   <!-- Location of the publisher. (OPTIONAL; no more than 32 chars) -->
   <publisher-location>London, UK and California, USA</publisher-location>

   <!-- Preferred name for use in Google Scholar. This name will appear -->
   <!-- in Google Scholar results for urls included in the metadata files. -->
   <!-- Please note that this name only appears if we are able to index the -->
   <!-- url for the given result. (OPTIONAL; no more than 24 chars) -->
   <publisher-result-name>PEP Web</publisher-result-name>

   <!-- Contact email. (REQUIRED; up to five can be specified) -->
   <contact>Orazio Capello &lt;o.cappello@ucl.ac.uk&gt;</contact>
   <contact>Nadine Levinson &lt;nadinelevinson@cs.com&gt;</contact>
   <contact>David Tuckett &lt;d.tuckett@ucl.ac.uk&gt;</contact>

   <!-- Information about metadata files. Upto 10000 files can be specified.  -->
   <!-- (REQUIRED) -->
   <metadata-files>
     {publisher_file_cumulated_text}
   </metadata-files>
</publisher>
"""

    #enf.write(tplPublisher)
    # this is required if running on S3
    msg = f"\t...Exporting! Writing publisher XML file to {publisher_file_name}"
    if fs is not None:
        success = fs.create_text_file(path=path, filespec=publisher_file_name, data=tplPublisher, path_is_root_bucket=True)
        if success:
            if options.display_verbose: # Exporting! Writing publisher XML file
                print (msg)
                print ("\t"+60*"-")
        else:
            print (f"\t...There was a problem writing {publisher_file_name}.")
    else:
        print (f"\t...There was a problem writing {publisher_file_name}. Filesystem not supplied")

    print("%s files found; written to publisher record." % count)

    return

def google_metadata_generator(path=None, source_type="journal", fs=None, size=None, max_records=None, clear_sitemap=None, path_is_root_bucket=False):
    journal_info = metadata_get_source_info(src_type=source_type)
    #journal_codes = [doc.PEPCode for doc in journal_info.sourceInfo.responseSet]
    jinfo = [(doc.PEPCode, doc) for doc in journal_info.sourceInfo.responseSet]
    journal_info_dict = dict(sorted(jinfo, key=lambda PEPCode: PEPCode[0]))
    for journal_code in journal_info_dict.keys():
        print (f"Writing metadata for {journal_code}")
        volume_info = opasPySolrLib.metadata_get_volumes(source_code=journal_code)
        volumes = [(vol.year, vol.vol, vol) for vol in volume_info.volumeList.responseSet]
        vol_metadata_text = ""
        for volume in volumes:
            try:
                print (f"\tWriting metadata for {journal_code}.{volume[0]}")
                header = f"""<?xml version="1.0" encoding="utf-8" ?>\n{googleMetadataConfig.GOOGLE_METADATA_ARTICLE_DOCTYPE}\n<articles>"""
                vol_metadata_text += header
                
                contents = opasPySolrLib.metadata_get_contents(pep_code=journal_code, year=volume[0], vol=volume[1])
                contents = contents.documentList.responseSet
                #  SOURCETITLEFULL, SOURCETITLESERIES, ISSN, PUBLISHER, KEY, TITLE, AUTHORMARKUP, YEAR, VOL, ISSUE, PGSTART, PGEND
                # walk through the articles for the source code.
                for artinfo in contents:
                    try:
                        doclistitem = artinfo
                        # root = etree.fromstring(doclistitem.documentInfoXML)
                        artinfo = objectify.fromstring(doclistitem.documentInfoXML)
                        attrib = artinfo.attrib
                        artTitle = artinfo.arttitle
                        art_title_text = find_or_emptystr(artinfo, "arttitle")
                        if art_title_text == "":
                            print (doclistitem.documentID, " - No title text")
                        else:
                            art_subtitle = find_or_emptystr(artinfo, "artsub")
                            if art_subtitle != "":
                                art_title_text += f": {art_subtitle}"
                        
                        art_vol = artinfo.artvol
                        art_year = artinfo.artyear
                        auts = artinfo.artauth
                        publisher = journal_info_dict[journal_code].publisher
                        issn = journal_info_dict[journal_code].ISSN
                        contribs = ""
                        aut_count = 0
                        try:
                            aut_count += 1
                            for a in auts.aut:
                                given_names = find_or_emptystr(a, "nfirst")
                                given_middle_name = find_or_emptystr(a, "nmid")
                                if given_names != "" and given_middle_name != "":
                                    given_names += f", {given_middle_name}"
                                nsuffix = find_or_emptystr(a, "nsuffix")
                                if nsuffix != "":
                                    suffix_add = """
                                         \t\t\t\t\t<!-- Suffix for the author - Jr/Sr/III etc. (OPTIONAL; no more than 8 chars) -->
                                         \t\t\t\t\t<suffix>{find_or_emptystr(a, "nsuffix")}</suffix>
                                    """
                                else:
                                    suffix_add = ""
                                
                                contribs += f"""
                                    \t\t\t\t\t<!-- Author names. (REQUIRED; No more than 1024 entries) -->
                                    \t\t\t\t\t<contrib contrib-type="{a.attrib.get('role', '')}">
                                        \t\t\t\t<name>
                                        \t\t\t\t\t<!-- Last name of an author. (REQUIRED; No more than 32 characters -->
                                        \t\t\t\t\t<surname>{find_or_emptystr(a, "nlast")}</surname>
                                        \t\t\t\t\t<!-- Given names of an author - includes first and middle names if -->
                                        \t\t\t\t\t<!-- any. (REQUIRED; no more than 48 characters -->
                                        \t\t\t\t\t<given-names>{given_names}</given-names>
                                        \t\t\t\t</name>
                                        {suffix_add}
                                    \t\t\t\t\t</contrib>
                                    """
                                # clean up empty tags
                                # contribs = contribs.replace("<suffix></suffix>", "")
                                
                        except Exception as e:
                            contribs += """
                                    \t\t\t\t\t<!-- Author name Template used when there are no authors because its REQUIRED -->
                                    \t\t\t\t\t<contrib contrib-type="">
                                        \t\t\t\t\t<name>
                                        \t\t\t\t\t\t<surname></surname>
                                        \t\t\t\t\t\t<given-names></given-names>
                                        \t\t\t\t\t</name>
                                    \t\t\t\t\t</contrib>
                                        """
                           
                        #print (doclistitem )
                        #print ("----")
                        #  SOURCETITLEFULL, SOURCETITLESERIES, ISSN, PUBLISHER, KEY, TITLE, AUTHORMARKUP, YEAR, VOL, ISSUE, PGSTART, PGEND
                        article_meta = f"""
                            \t<article> <!-- {doclistitem.documentID} -->
                            \t\t<front>
                            \t\t\t<!-- Information about the journal. (REQUIRED) -->
                            \t\t\t<journal-meta>
                            \t\t\t\t<!-- Journal title. (REQUIRED; no more than 128 chars) -->
                            \t\t\t\t<journal-title>{val_or_emptystr(doclistitem.sourceTitle)}</journal-title>
                            \t\t\t\t<!-- Abbreviated Journal title. This can be repeated. (OPTIONAL; no more than 32 chars) -->
                            \t\t\t\t<abbrev-journal-title>{val_or_emptystr(doclistitem.sourceTitleAbbr)}</abbrev-journal-title>
                            \t\t\t\t<!-- ISSN for the journal. This can be repeated (REQUIRED; no more than 128 characters) -->
                            \t\t\t\t<issn>{val_or_emptystr(issn)}</issn>
                            \t\t\t\t<!-- Metadata for the publisher. (OPTIONAL) -->
                            \t\t\t\t<publisher>
                            \t\t\t\t\t<!-- Name of publisher. (REQUIRED; no more than 128 characters) -->
                            \t\t\t\t\t<publisher-name>{publisher}
                            \t\t\t\t\t</publisher-name>
                            \t\t\t\t</publisher>
                            \t\t\t</journal-meta>
                            \t\t\t<!-- Information about the article. (REQUIRED) -->
                            \t\t\t<article-meta>
                            \t\t\t\t<!-- Various identifiers associated with the article. Currently, we use -->
                            \t\t\t\t<!-- doi, pmid, pmcid, sici, publisher-id. Others are allowed but ignored.  -->
                            \t\t\t\t<!-- (OPTIONAL; at most five entries) -->
                            \t\t\t\t<article-id pub-id-type="publisher-id">{doclistitem.documentID}</article-id>
                            \t\t\t\t<!-- Title of the article. (REQUIRED) -->
                            \t\t\t\t<title-group>
                            \t\t\t\t\t<!-- Title of the article. (REQUIRED; no more than 512 chars) -->
                            \t\t\t\t\t<article-title>{art_title_text}</article-title>
                            \t\t\t\t</title-group>
                            \t\t\t\t<!-- Information about the contributors. (REQUIRED) -->
                            \t\t\t\t\t<contrib-group>
                            \t\t\t\t\t{contribs}
                            \t\t\t\t\t</contrib-group>
                            \t\t\t\t\t<!-- Date of publication. (REQUIRED; Gregorian calendar) -->
                            \t\t\t\t\t<pub-date pub-type="pub">
                            \t\t\t\t\t\t<!-- Year of publication. Full four digit. (REQUIRED) -->
                            \t\t\t\t\t\t<year>{val_or_emptystr(doclistitem.year)}</year>
                            \t\t\t\t\t</pub-date>
                            \t\t\t\t\t<!-- Volume. (REQUIRED) -->
                            \t\t\t\t\t<volume>{val_or_emptystr(doclistitem.vol)}</volume>
                            \t\t\t\t\t<!-- Issue number. (REQUIRED) -->
                            \t\t\t\t\t<issue>{val_or_emptystr(doclistitem.issue)}</issue>
                            \t\t\t\t\t<!-- First page. (REQUIRED) -->
                            \t\t\t\t\t<fpage>{val_or_emptystr(doclistitem.pgStart)}</fpage>
                            \t\t\t\t\t<!-- Last page. (REQUIRED) -->
                            \t\t\t\t\t<lpage>{val_or_emptystr(doclistitem.pgEnd)}</lpage>
                            \t\t\t\t\t<!-- URLs for the article (REQUIRED; no more than 1024 characters).  -->
                            \t\t\t\t\t<!-- Multiple entries are allowed and can refer to multiple formats  -->
                            \t\t\t\t\t<!-- It is CRUCIAL that at least one instance of this field be present -->
                            \t\t\t\t\t<self-uri xlink:href="https://pep-web.org/browse/document/{doclistitem.documentID}"/>
                            \t\t\t</article-meta>
                            \t\t</front>
                         
                            \t\t<!-- Type of article. (OPTIONAL. acceptable values:  research-article -->
                            \t\t<!--  book, phd-thesis, ms-thesis, bs-thesis, technical-report, unpublished, -->
                            \t\t<!-- review-article, patent, other -->
                            \t\t<article-type>research-article</article-type>
                            \t</article>
                            """
            
                    except Exception as e:
                        try:
                            logger.error (f"Error: {e} for {doclistitem.documentID}")
                            vol_metadata_text += article_meta
                        except:
                            pass # ok, skip article
                    else:
                        # print (article_meta)
                        vol_metadata_text += article_meta
                    # article info end
            
                vol_metadata_text += "</articles>"
                    
            except Exception as e:
                logger.error(f"Error: {e}")
                
            # vol is done...write output file for journal vol
            outputFileName = f"{journal_code}.{volume[0]}.xml"
            if fs is not None:
                success = fs.create_text_file(outputFileName, data=vol_metadata_text, path=path, path_is_root_bucket=path_is_root_bucket)
                if success:
                    if options.display_verbose: # vol is done...write output file for journal vol
                        msg = f"\t...Writing volume XML file to {outputFileName}"
                        logger.info(msg)
                        print (msg)
                else:
                    msg =f"\t...There was a problem writing {outputFileName}."
                    logger.error(msg)
                    print (msg)
            else:
                msg = f"\t...There was a problem writing {outputFileName}. Filesystem not supplied"
                logger.error(msg)
                print (msg)
            
# -------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    options = None
    parser = OptionParser(usage="%prog [options] - PEP Google Metadata Generator", version=f"%prog ver. {__version__}")
    parser.add_option("-l", "--loglevel", dest="logLevel", default=logging.ERROR,
                      help="Level at which events should be logged (DEBUG, INFO, WARNING, ERROR")
    parser.add_option("-c", "--clear", dest="clearmetadata", action="store_true", default=False,
                      help="Clear prior metadata files (delete files in path/bucket matching metadata.*)")
    parser.add_option("--verbose", action="store_true", dest="display_verbose", default=False,
                      help="Display status and operational timing info as load progresses.")
    parser.add_option("-t", "--test", dest="testmode", action="store_true", default=False,
                      help="Run Doctests.  Will run a small sample of records and total output")
    parser.add_option("-r", "--recordsperfile", dest="recordsperfile", type="int", default=8000,
                      help="Max Number of records per file")
    parser.add_option("-m", "--maxrecords", dest="maxrecords", type="int", default=200000,
                      help="Max total records to be exported")
    parser.add_option("-b", "--bucket", "--path", dest="bucket", type="string", default=localsecrets.GOOGLE_METADATA_PATH,
                      help="Bucket or Local Path to write sitemap files on local system or S3 (on AWS must be a bucket)")
    parser.add_option("--rb", "--isrootbucket", dest="isrootbucket", action="store_false", 
                      help="True if the pathspecified is the bucketname on AWS")
    parser.add_option("--awsbucket", dest="aws_bucket", type="string", default=localsecrets.GOOGLE_METADATA_PATH, 
                      help="The name of the root (bucket) on AWS")

    (options, args) = parser.parse_args()
    if options.testmode:
        import doctest
        doctest.testmod()
        print ("Fini. Tests complete.")
    else:
        fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root=options.aws_bucket)
        path_is_root_bucket = options.bucket == options.aws_bucket
        writePublisherFile(path=options.bucket,
                           fs=fs,
                           online_link_location="https://pep-web-google-metadata.s3.amazonaws.com/",
                           path_is_root_bucket=path_is_root_bucket
                           )
        ret_val = google_metadata_generator(path=options.bucket, fs=fs, source_type="video", path_is_root_bucket=path_is_root_bucket) # path=options.bucket, size=options.recordsperfile, max_records=options.maxrecords, clear_sitemap=options.clearsitemap)
        ret_val = google_metadata_generator(path=options.bucket, fs=fs, source_type="journal", path_is_root_bucket=path_is_root_bucket) # path=options.bucket, size=options.recordsperfile, max_records=options.maxrecords, clear_sitemap=options.clearsitemap)
        print ("============================================")
        print ("  TBD: Still need to add book processing!")
        print ("============================================")
        print ("Finished!")

    sys.exit()
