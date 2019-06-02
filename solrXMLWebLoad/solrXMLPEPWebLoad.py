#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
print(
""" 
OPAS - Open Publications-Archive Software 

    Load articles into one Solr core and extract individual references from
    the bibliography into a second Solr core.
    
    This data loader is specific to PEP Data and Bibliography schemas but can 
    serve as a model or framework for other schemas
    
    Example Invocation:
    
            $ python solrXMLPEPWebLoad.py
    
            Use -h for help on arguments.
            
            (Requires Python 2.7)
    
"""
)

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "0.1.22"
__status__      = "Development"

#Revisions:
    #2019-05-16: Addded command line options to specify a different path for PEPSourceInfo.json
                #Added error logging using python's built-in logging library default INFO level

    #2019-06-01: Fixe


# Disable many annoying pylint messages, warning me about variable naming for example.
# yes, in my Solr code I'm caught between two worlds of snake_case and camelCase.

# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004
import re
import sys
import os
import os.path
import time
import logging

from datetime import datetime
from optparse import OptionParser
from base64 import b64encode

import json
import lxml
from lxml import etree
#import pysolr  # does not support basic authentication
import solr     # supports a number of types of authentication, including basic.  This is "solrpy"

import config
from OPASFileTracker import FileTracker, FileTrackingInfo

class ExitOnExceptionHandler(logging.StreamHandler):
    """
    Allows us to exit on serious error.
    """
    def emit(self, record):
        super().emit(record)
        if record.levelno in (logging.ERROR, logging.CRITICAL):
            raise SystemExit(-1)

def xmlElementsToStrings(elementNode, xPathDef):
    """
    Return a list of XML tagged strings from the nodes in the specified xPath

    Example:
    strList = elementsToStrings(treeRoot, "//aut[@listed='true']")

    """
    retVal = [etree.tostring(n, with_tail=False) for n in elementNode.xpath(xPathDef)]
    return retVal

def xmlTextOnly(elem):
    """
    Return inner text of mixed content element with sub tags stripped out
    """
    etree.strip_tags(elem, '*')
    inner_text = elem.text
    if inner_text:
        return inner_text.strip()
    return None

def xmlGetTextSingleton(elementNode, xpath):
    """
    Return text of element specified by xpath (with Node() as final part of path)
    """
    try:
        retVal = elementNode.xpath(xpath)[0]
    except IndexError:
        retVal = ""
        
    return retVal    

def xmlGetSingleDirectSubnodeText(elementNode, subelementName):
    """
    Return the text for a direct subnode of the lxml elementTree elementNode.
    
    Important Note: Looks only at direct subnodes, not all decendents (for max speed)
    """
    retVal = ""

    try:
        retVal = elementNode.xpath('%s/node()' % subelementName)
        retVal = retVal[0]
    except ValueError, err: # try without node
        retVal = elementNode.xpath('%s' % subelementName)
        retVal = retVal[0]
    except IndexError, err:
        retVal = elementNode.xpath('%s' % subelementName)
    except Exception, err:
        print ("getSingleSubnodeText Error: ", err)

    if retVal == []:
        retVal = ""
    if isinstance(retVal, lxml.etree._Element):
        retVal = xmlTextOnly(retVal)        

    return retVal

def xmlGetElementAttr(elementNode, attrName):
    """
    Get an attribute from the lxml elementNode
    """
    retVal = ""
    try:
        retVal = elementNode.attrib[attrName]
    except Exception, err:
        retVal = ""

    return retVal

def xmlFindSubElementText(elementNode, subElementName):
    """
    Text for elements with only CDATA underneath
    """
    retVal = ""
    try:
        retVal = elementNode.find(subElementName).text
    except Exception, err:
        retVal = ""

    return retVal

def xmlFindSubElementXML(elementNode, subElementName):
    """
    Returns the marked up XML text for elements (including subelements)
    """
    retVal = ""
    try:
        retVal = etree.tostring(elementNode.find(subElementName), with_tail=False)
    except Exception, err:
        retVal = ""

    return retVal

def readSourceInfoDB(journalInfoFile):
    """
    The source info DB is a journal basic info "database" in json
    
    Read as is since this JSON file can be simply and quickly exported
         from the PEP issn table in mySQL used in data conversion

    """
    retVal = {}
    with open(journalInfoFile) as f:
        journalInfo = json.load(f)

    # turn it into a in-memory dictionary indexed by jrnlcode;
    # in 2019, note that there are only 111 records
    for n in journalInfo["RECORDS"]:
        retVal[n["pepsrccode"]] = n

    return retVal

class ArticleInfo:
    """
    Grab all the article metadata, and save as instance variables.
    """
    def __init__(self, sourceInfoDB, pepxml, artID, logger):
        #global options
        # let's just double check artid!
        self.artID = artID
        try:
            self.artIDFromFile = pepxml.xpath('//artinfo/@id')[0]
            self.artIDFromFile = self.artIDFromFile.upper()

            if self.artIDFromFile != self.artID:
                logger.warn("File name ID tagged and artID disagree.  %s vs %s", self.artID, self.artIDFromFile)
                #processingWarningCount += 1
        except Exception, err:
            logger.warn("Issue reading file's article id. (%s)", err)
            #processingWarningCount += 1

        # Containing Article data
        #<!-- Common fields -->
        #<!-- Article front matter fields -->
        #---------------------------------------------
        self.artPepSrcCode = pepxml.xpath("//artinfo/@j")[0]
        try:
            self.artPepSourceTitleAbbr = sourceInfoDB[self.artPepSrcCode].get("sourcetitleabbr")
            self.artPepSourceTitleFull = sourceInfoDB[self.artPepSrcCode].get("sourcetitlefull")
            self.artPepSourceType = sourceInfoDB[self.artPepSrcCode].get("pep_class")  # journal, book, video...
            self.artPepSrcEmbargo = sourceInfoDB[self.artPepSrcCode].get("wall")

        except KeyError, err:
            self.artPepSourceTitleAbbr = ""
            self.artPepSourceTitleFull = ""
            self.artPepSourceType = ""
            self.artPepSrcEmbargo = None
            logger.warn("Error: PEP Source %s not found in source info db.  Use the 'PEPSourceInfo export' after fixing the issn table in MySQL DB", self.artPepSrcCode)

        except Exception, err:
            logger.error("Error: Problem with this files source info. File skipped. (%s)", err)
            #processingErrorCount += 1
            return
        self.artVol = xmlGetTextSingleton(pepxml, '//artinfo/artvol/node()')
        self.artYear = xmlGetTextSingleton(pepxml, '//artinfo/artyear/node()')
        self.artIssue = xmlGetTextSingleton(pepxml, '//artinfo/artiss/node()')

        artInfoNode = pepxml.xpath('//artinfo')[0]
        self.artType = xmlGetElementAttr(artInfoNode, "arttype") 
        self.artDOI = xmlGetElementAttr(artInfoNode, "doi") 
        self.artISSN = xmlGetElementAttr(artInfoNode, "ISSN") 
        self.artOrigRX = xmlGetElementAttr(artInfoNode, "origrx") 
        self.newSecNm = xmlGetElementAttr(artInfoNode, "ISSN") 
        self.artPgrg = xmlFindSubElementText(artInfoNode, "artpgrg")  # note: getSingleSubnodeText(pepxml, "artpgrg"),

        self.artTitle = xmlFindSubElementXML(artInfoNode, "arttitle")
        if self.artTitle != None and self.artTitle != "":
            # remove tags:
            self.artTitle = ''.join(etree.fromstring(self.artTitle).itertext())
        self.artSubtitle = xmlFindSubElementXML(artInfoNode, 'artsub')
        if self.artSubtitle == "":
            pass
        elif self.artSubtitle == None:
            self.artSubtitle = ""
        else:
            self.artSubtitle = ''.join(etree.fromstring(self.artSubtitle).itertext())
            self.artSubtitle = ": " + self.artSubtitle

        self.artTitle = self.artTitle + self.artSubtitle
        self.artLang = pepxml.xpath('//pepkbd3/@lang')
        if self.artLang == []:
            self.artLang = ['EN']
        # ToDo: I think I should add an author ID to bib aut too.  But that will have
        #  to wait until I rebuild everything in January.
        self.artAuthors = pepxml.xpath('//artinfo/artauth/aut[@listed="true"]/@authindexid')
        self.artAuthors = ", ".join(self.artAuthors)
        self.artKwds = xmlGetTextSingleton(pepxml, "//artinfo/artkwds/node()")

        # Usually we put the abbreviated title here, but that won't always work here.
        self.artCiteAsXML = """<p class="citeas"><span class="authors">%s</span> (<span class="year">%s</span>) <span class="title">%s</span>. <span class="sourcetitle">%s</span> <span class="pgrg">%s</span>:<span class="pgrg">%s</span></p>""" \
            %                   (self.artAuthors,
                                 self.artYear,
                                 self.artTitle,
                                 self.artPepSourceTitleFull,
                                 self.artVol,
                                 self.artPgrg)

        artQualNode = pepxml.xpath("//artinfo/artqual")
        self.artQual = xmlGetElementAttr(artQualNode, "rx") 
       

def processFileforFullTextCore(pepxml, base, artInfo, solrcon, fileXMLContents):
    """
    Extract and load data for the full-text core.  Whereas in the Refs core each
      Solr document is a reference, here each Solr document is a PEP Article.

      This core contains bib entries too, but not subfields.

      TODO: Originally, this core supported each bibliography record in its own
            json formatted structure, saved in a single field.  However, when
            the code was switched from PySolr to Solrpy this had to be removed,
            since Solrpy prohibits this for some reason.  Need to raise this
            as a case on the issues board for Solrpy.


    """
    if options.displayVerbose:
        print("   ...Processing main file content for the %s core." % options.fullTextCoreName)

    #bib_references = pepxml.xpath("/pepkbd3//be")
    #bib_refentries_struct = {}  # not using this struct because solrpy doesn't like loading structures to solr
                                 # and in retrospect, we probably don't need it.  But leaving as 
                                 # comments if we want to later reintroduce it.

    # walk through the references, save general info into a struct
    #for ref in bib_references:
        # Check special bib fields, where data could come from multiple places
        #bib_articletitle = xmlGetSingleDirectSubnodeText(ref, "t")
        #bib_sourcetitle = xmlGetSingleDirectSubnodeText(ref, "j")
        #bib_publishers = xmlGetSingleDirectSubnodeText(ref, "bp")
        #bib_bookyearofpublication = xmlGetSingleDirectSubnodeText(ref, "bpd")
        #bib_yearofpublication = xmlGetSingleDirectSubnodeText(ref, "y")
        #if bib_publishers != "":
            #bib_sourcetype = "book"
        #else:
            #bib_sourcetype = "journal"
        #if bib_sourcetype == "book":
            #if bib_yearofpublication == "":
                #bib_yearofpublication = bib_bookyearofpublication
            #if bib_bookyearofpublication == "":
                #bib_bookyearofpublication = bib_yearofpublication
            #if bib_sourcetitle == "":
                #bib_sourcetitle = bib_sourcetitle  # book title
                #if bib_articletitle == "":
                    #bib_articletitle = xmlGetSingleDirectSubnodeText(ref, "bst")  # book title
                    #bib_sourcetitle = ""

        #bib_author_name_list = [(etree.tostring(x, with_tail=False)) for x in ref.findall("a")]
        #bib_authors = '; '.join(bib_author_name_list)

        # Now put the reference data into a structure

        # A json structure will be stored in a single field in Solr with the reference field breakdown, as well
        #   as the full-text of the reference tagged.  Otherwise, these data fields would not be stored
        #   together on a reference by reference basis: all the bib_sourcetititles, for example, would be in
        #   one field as a list, the bib_articletitles in another, etc.  This "subrecord" of sorts holds them
        #   together, though as far as I know, they will not be individually addressable by Solr.

        #bib_refentries_struct[xmlGetElementAttr(ref, "id")] = {
            #"bib_ref_rx" : xmlGetElementAttr(ref, "rx"),
            #"bib_sourcetype" : bib_sourcetype,
            #"bib_articletitle" : bib_articletitle,
            #"bib_sourcetitle" : bib_sourcetitle,
            #"bib_yearofpublication" : bib_yearofpublication,
            #"bib_pgrg" : xmlGetSingleDirectSubnodeText(ref, "pp"),
            #"bib_volume" : xmlGetSingleDirectSubnodeText(ref, "v"),
            #"bib_authors" : bib_authors,
            #"bib_bookyearofpublication" : bib_bookyearofpublication,
            #"bib_bookpublisher" : xmlGetSingleDirectSubnodeText(ref, "bp"),
            #"text": etree.tostring(ref, with_tail=False)
        #}

        #if bib_refentries_struct == {}:
            #bib_refentries_struct = ""

    artLang = pepxml.xpath('//@lang')
    if artLang == []:
        artLang = ['EN']

    # Now lets add the article record to Solr
    # this build of the schema now has all XML data fields indicated in the field name
    # the snake_case works better for Solr; as a result, a bit of it thus creeps into this python code, but
    # I still prefer to use camelCase.  Unfortunately, lint is unhappy I use both :)

    headings = xmlElementsToStrings(pepxml, "//h1")
    headings += xmlElementsToStrings(pepxml, "//h2")
    headings += xmlElementsToStrings(pepxml, "//h3")
    headings += xmlElementsToStrings(pepxml, "//h4")
    headings += xmlElementsToStrings(pepxml, "//h5")
    headings += xmlElementsToStrings(pepxml, "//h6")

    try:
        response_update = solrcon.add(id = artInfo.artID,                   # important =  note this is unique id for every reference
                                      art_id = artInfo.artID,
                                      art_title_xml = xmlElementsToStrings(pepxml, "//arttitle"),
                                      art_subtitle_xml = xmlElementsToStrings(pepxml, "//artsubtitle"),
                                      title = artInfo.artTitle,
                                      art_pepsrccode = artInfo.artPepSrcCode,
                                      art_pepsourcetitleabbr = artInfo.artPepSourceTitleAbbr,
                                      art_pepsourcetitlefull = artInfo.artPepSourceTitleFull,
                                      art_pepsourcetype = artInfo.artPepSourceType,
                                      art_authors = artInfo.artAuthors,
                                      art_authors_unlisted = pepxml.xpath('//artinfo/artauth/aut[@listed="false"]/@authindexid'),
                                      art_authors_xml = xmlElementsToStrings(pepxml, "//aut"),
                                      art_year = artInfo.artYear,
                                      art_vol = artInfo.artVol,
                                      art_pgrg = artInfo.artPgrg,
                                      art_iss = artInfo.artIssue,
                                      art_doi = artInfo.artDOI,
                                      art_lang = artInfo.artLang,                      
                                      art_issn = artInfo.artISSN,
                                      art_origrx = artInfo.artOrigRX,
                                      art_qual = artInfo.artQual,
                                      art_kwds = artInfo.artKwds,
                                      art_type = artInfo.artType,
                                      art_newsecnm = artInfo.newSecNm,
                                      art_citeas_xml = artInfo.artCiteAsXML,
                                      # this produces errors because the solrpy library is looking for these and thinks its a mistake.
                                      #bib_entries_json = " " + ','.join(['='.join(i) for i in bib_refentries_struct.items()]), #bib_refentries_struct,  # hmm, I wonder if we should type suffix other fields?
                                      authors =  artInfo.artAuthors,         # for common names convenience
                                      author_bio_xml = xmlElementsToStrings(pepxml, "//nbio"),
                                      author_aff_xml = xmlElementsToStrings(pepxml, "//autaff"),
                                      bk_title_xml = xmlElementsToStrings(pepxml, "//artbkinfo/bktitle"),
                                      bk_alsoknownas_xml = xmlElementsToStrings(pepxml, "//artbkinfo/bkalsoknownas"),
                                      bk_editors_xml = xmlElementsToStrings(pepxml, "//bkeditors"),
                                      bk_seriestitle_xml = xmlElementsToStrings(pepxml, "//bkeditors"),
                                      bk_pubyear = pepxml.xpath("//bkpubyear/node()"),
                                      caption_text_xml = xmlElementsToStrings(pepxml, "//caption"),
                                      caption_title_xml = xmlElementsToStrings(pepxml, "//ctitle"),
                                      headings_xml = headings,
                                      references_xml = xmlElementsToStrings(pepxml, "/pepkbd3//be"),
                                      abstracts_xml = xmlElementsToStrings(pepxml, "///abs"),
                                      summaries_xml = xmlElementsToStrings(pepxml, "///summaries"),
                                      terms_xml = xmlElementsToStrings(pepxml, "//impx[@type='TERM2']"),
                                      terms_highlighted_xml = xmlElementsToStrings(pepxml, "//b") + xmlElementsToStrings(pepxml, "//i"),
                                      dialogs_spkr = pepxml.xpath("//dialog/spkr/node()"),
                                      dialogs_xml = xmlElementsToStrings(pepxml, "//dialog"),
                                      dreams_xml = xmlElementsToStrings(pepxml, "//dream"),
                                      notes_xml = xmlElementsToStrings(pepxml, "//note"),
                                      panels_spkr = xmlElementsToStrings(pepxml, "//panel/spkr"),
                                      panels_xml = xmlElementsToStrings(pepxml, "//panel"),
                                      poems_src = pepxml.xpath("//poem/src/node()"),
                                      poems_xml = xmlElementsToStrings(pepxml, "//poem"),
                                      quotes_spkr = pepxml.xpath("//quote/spkr/node()"),
                                      quotes_xml = xmlElementsToStrings(pepxml, "//quote"),
                                      meta_xml = xmlElementsToStrings(pepxml, "//meta"),
                                      text_xml = unicode(fileXMLContents, "utf8")
                                     )
        if not re.search('"status">0</int>', response_update):
            print (response_update)
    except Exception, err:
        #processingErrorCount += 1
        print ("Error for :", artInfo.artID, err)
        config.logger.error("Solr call exception %s", err)

    return

def processBibSection(pepxml, base, artInfo, solrcon):
    """
    Adds data to the core per the pepwebrefs schema

    TODO: This is the slowest of the two data adds.  It does multiple transactions
          per document (one per reference).  This could be redone as an AddMany transaction,
          assuming AddMany can handle as many references as we might find in a document.
          It's not unbearably slow locally, but via the API remotely, it adds up.
          Remotely to Bitnami AWS with a 1GB memory: 0.0476 seconds per reference

    """
    #<!-- biblio section fields -->
    #Note: currently, this does not include footnotes or biblio include tagged data in document (binc)
    bibReferences = pepxml.xpath("/pepkbd3//be")
    retVal = bibReferenceCount = len(bibReferences)
    if options.displayVerbose:
        print("   ...Processing %s references for the references database." % (bibReferenceCount))
    #processedFilesCount += 1

    allRefs = []
    for ref in bibReferences:
        config.bibTotalReferenceCount += 1
        bibRefEntry = etree.tostring(ref, with_tail=False)
        bibRefID = xmlGetElementAttr(ref, "id")
        refID = artInfo.artID + "." + bibRefID
        bibSourceTitle = xmlFindSubElementText(ref, "j")
        bibPublishers = xmlFindSubElementText(ref, "bp")
        if bibPublishers != "":
            bibSourceType = "book"
        else:
            bibSourceType = "journal"
        if bibSourceType == "book":
            bibYearofPublication = xmlFindSubElementText(ref, "bpd")
            if bibSourceTitle == None or bibSourceTitle == "":
                # sometimes has markup
                bibSourceTitle = xmlGetSingleDirectSubnodeText(ref, "bst")  # book title
        else:
            bibYearofPublication = xmlFindSubElementText(ref, "y")

        bibAuthorNameList = [etree.tostring(x, with_tail=False) for x in ref.findall("a") if x is not None]
        bibAuthorsXml = '; '.join(bibAuthorNameList)
        #Note: Changed to is not None since if x gets warning - FutureWarning: The behavior of this method will change in future versions. Use specific 'len(elem)' or 'elem is not None' test instead
        authorList = [xmlTextOnly(x) for x in ref.findall("a") if xmlTextOnly(x) is not None]  # final if x gets rid of any None entries which can rarely occur.
        authorList = '; '.join(authorList)
        
        thisRef = {
                    "id" : refID,
                    "art_id" : artInfo.artID,
                    "art_title" : artInfo.artTitle,
                    "art_pepsrccode" : artInfo.artPepSrcCode,
                    "art_pepsourcetitleabbr" : artInfo.artPepSourceTitleAbbr,
                    "art_pepsourcetitlefull" : artInfo.artPepSourceTitleFull,
                    "art_pepsourcetype" : artInfo.artPepSourceType,
                    "art_authors" : artInfo.artAuthors,
                    "art_year" : artInfo.artYear,
                    "art_vol" : artInfo.artVol,
                    "art_pgrg" : artInfo.artPgrg,
                    "art_lang" : artInfo.artLang,
                    "art_citeas_xml" : artInfo.artCiteAsXML,
                    "text" : bibRefEntry,                        
                    "authors" : authorList,
                    "title" : xmlFindSubElementText(ref, "t"),
                    "bib_authors_xml" : bibAuthorsXml,
                    "bib_ref_id" : bibRefID,
                    "bib_ref_rx" : xmlGetElementAttr(ref, "rx"),
                    "bib_articletitle" : xmlFindSubElementText(ref, "t"),
                    "bib_sourcetype" : bibSourceType,
                    "bib_sourcetitle" : bibSourceTitle,
                    "bib_pgrg" : xmlFindSubElementText(ref, "pp"),
                    "bib_year" : bibYearofPublication,
                    "bib_volume" : xmlFindSubElementText(ref, "v"),
                    "bib_publisher" : bibPublishers            
                  }
        allRefs.append(thisRef)
        
    # We collected all the references.  Now lets save the whole shebang
    try:
        response_update = solrcon.add_many(allRefs)  # lets hold off on the , _commit=True)

        if not re.search('"status">0</int>', response_update):
            print (response_update)
    except Exception, err:
        #processingErrorCount += 1
        config.logger.error("Solr call exception %s", err)

    return retVal  # return the bibRefCount

def main():
    
    global options  # so the information can be used in support functions
    global bibTotalReferenceCount

    programNameShort = "OPASWebLoaderPEP"  # used for log file
    scriptSourcePath = os.path.dirname(os.path.realpath(__file__))

    parser = OptionParser(usage="%prog [options] - PEP Solr Reference Text Data Loader", version="%prog ver. 0.1.13")
    parser.add_option("-a", "--allfiles", action="store_true", dest="forceRebuildAllFiles", default=False,
                      help="Option to force all files to be updated on the specified cores.  This does not reset the file tracker but updates it as files are processed.")
    parser.add_option("-b", "--bibliocorename", dest="biblioCoreName", default=None,
                      help="the Solr corename (holding the collection) to connect to, i.e., where to send data.  Example: 'pepwebrefs'")
    parser.add_option("-d", "--dataroot", dest="rootFolder", default=config.DEFAULTDATAROOT,
                      help="Root folder path where input data is located")
    parser.add_option("-f", "--fulltextcorename", dest="fullTextCoreName", default=None,
                      help="the Solr corename (holding the collection) to connect to, i.e., where to send data.  Example: 'pepwebproto'")
    parser.add_option("-l", "--loglevel", dest="logLevel", default=logging.INFO,
                      help="Level at which events should be logged")
    parser.add_option("--resetcore",
                      action="store_true", dest="resetCoreData", default=False,
                      help="reset the data in the selected cores")
    parser.add_option("-s", "--sourceinfodbpath", dest="sourceInfoDBPath", default=None,
                      help="Full path (and file name) of JSON file with the source info DB")
    parser.add_option("-t", "--trackerdb", dest="fileTrackerDBPath", default="filetracker.db",
                      help="Full path and database name where the File Tracking Database is located (sqlite3 db)")
    parser.add_option("-u", "--url",
                      dest="solrURL", default=config.DEFAULTSOLRHOME,
                      help="Base URL of Solr api (without core), e.g., http://localhost:8983/solr/", metavar="URL")
    parser.add_option("-v", "--verbose", action="store_true", dest="displayVerbose", default=False,
                      help="Display status and operational timing info as load progresses.")
    parser.add_option("--pw", dest="httpPassword", default=None,
                      help="Password for the server")
    parser.add_option("--userid", dest="httpUserID", default=None,
                      help="UserID for the server")

    (options, args) = parser.parse_args()

    logFilename = programNameShort + "_" + datetime.today().strftime('%Y-%m-%d') + ".log"
    processingErrorCount = 0
    processingWarningCount = 0
    processedFilesCount = 0
    logging.basicConfig(handlers=[ExitOnExceptionHandler()], filename=logFilename, level=options.logLevel)
    logger = config.logger = logging.getLogger(programNameShort)

    logger.info('Started at %s', datetime.today().strftime('%Y-%m-%d %H:%M:%S"'))

    solrAPIURL = None
    solrAPIURLRefs = None

    if options.fullTextCoreName is not None:
        solrAPIURL = options.solrURL + options.fullTextCoreName  # e.g., http://localhost:8983/solr/    + pepwebproto'
    if options.biblioCoreName is not None:
        solrAPIURLRefs = options.solrURL + options.biblioCoreName  # e.g., http://localhost:8983/solr/  + pepwebrefsproto'

    # instantiate the fileTracker.
    fileTracker = FileTracker(options.fileTrackerDBPath)

    print ("Input data Root: ", options.rootFolder)
    print ("Solr Full-Text Core: ", options.fullTextCoreName)
    print ("Solr Biblio Core: ", options.biblioCoreName)
    print ("Reset Core Data: ", options.resetCoreData)
    if options.fullTextCoreName is not None:
        print ("Solr solrAPIURL: ", solrAPIURL)
    if options.biblioCoreName is not None:
        print ("Solr solrAPIURLRefs: ", solrAPIURLRefs)
    print ("Logfile: ", logFilename)

    if options.fullTextCoreName is None and options.biblioCoreName is None:
        msg = "No cores specified so no database to update. Use the -f and -b options to specify the core. Use -h for help."
        print (len(msg)*"-")
        print (msg)
        print (len(msg)*"-")
        sys.exit(0)
        
    timeStart = time.time()

    # import data about the PEP codes for journals and books.
    #  Codes are like APA, PAH, ... and special codes like ZBK000 for a particular book
    sourceInfoDB = {}
    try:
        # Read the source code database - info about the various PEP Codes
        # Default sourceCodeDBName is 'PEPSourceInfo.json' at script path (see config)
        if options.sourceInfoDBPath is None:
            sourceInfoDB = readSourceInfoDB(os.path.join(scriptSourcePath, config.SOURCEINFODBFILENAME))
        else:
            sourceInfoDB = readSourceInfoDB(options.sourceInfoDBPath)
    except IOError:
        logger.fatal("%s not found in %s.", options.sourceCodeDBName, scriptSourcePath)

    #TODO: Try without the None test, the library should not try to use None as user name or password, so only the first case may be needed
    # The connection call is to solrpy (import was just solr)
    if options.httpUserID is not None and options.httpPassword is not None:
        if options.fullTextCoreName is not None:
            solrFT = solr.SolrConnection(solrAPIURL, http_user=options.httpUserID, http_pass=options.httpPassword)
        if options.biblioCoreName is not None:
            solrBib = solr.SolrConnection(solrAPIURLRefs, http_user=options.httpUserID, http_pass=options.httpPassword)
    else:
        if options.fullTextCoreName is not None:
            solrFT = solr.SolrConnection(solrAPIURL)
        if options.biblioCoreName is not None:
            solrBib = solr.SolrConnection(solrAPIURLRefs)

    # Reset core's data if requested (mainly for early development)
    if options.resetCoreData:
        if options.fullTextCoreName is not None:
            print ("Deleting all data from the full text core")
            solrFT.delete_query("*:*")
            solrFT.commit()
        if options.biblioCoreName is not None:
            print ("Deleting all data from the References core")
            solrBib.delete_query("*:*")
            solrBib.commit()
        # also reset the file tracker in both cases
        fileTracker.deleteAll()
        fileTracker.commit()

    if options.forceRebuildAllFiles == False:
        print ("Adding only files with newer modification dates than what's in fileTracker database")
    else:
        print ("Forced Rebuild - All files added, regardless of whether they were marked in the fileTracker as already added.")

    # find all processed XML files where build is (bEXP_ARCH1) in path
    # glob.glob doesn't unfortunately work to do this in Py2.7.x
    pat = r"(.*)\(bEXP_ARCH1\)\.(xml|XML)$"
    filePatternMatch = re.compile(pat)
    filenames = []
    skippedFiles = 0
    newFiles = 0
    totalFiles = 0
    # get a list of all the XML files that are new
    for root, d_names, f_names in os.walk(options.rootFolder):
        for f in f_names:
            if filePatternMatch.match(f):
                totalFiles += 1
                filename = os.path.join(root, f)
                currFileInfo = FileTrackingInfo()
                currFileInfo.loadForFile(filename, solrAPIURL)
                isModified = fileTracker.isFileModified(currFileInfo)
                if options.forceRebuildAllFiles:
                    # fake it, make it look modified!
                    isModified = True
                if not isModified:
                    # file seen before, need to compare.
                    #print "File is the same!  Skipping..."
                    skippedFiles += 1
                    continue
                else:
                    newFiles += 1
                    #print "File is NOT the same!  Scanning the data..."
                    filenames.append(filename)

    print (80*"-")
    print ("Ready to import records from %s files of %s at path: %s." % (newFiles, totalFiles, options.rootFolder))
    print ("%s Skipped files (those not modified since the last run)" % (skippedFiles))
    print (80*"-")
    bibTotalReferenceCount = 0
    preCommitFileCount = 0
    processedFilesCount = 0

    for n in filenames:
        fileTimeStart = time.time()
        processedFilesCount += 1
        nFileSize = os.path.getsize(n)
        f = open(n)
        fileXMLContents = f.read()

        # get file basename without build (which is in paren)
        base = os.path.basename(n)
        artID = os.path.splitext(base)[0]
        m = re.match(r"(.*)\(.*\)", artID)
        print ("Processing file #%s of %s: %s (%s bytes)." % (processedFilesCount, totalFiles, base, nFileSize))

        # Note: We could also get the artID from the XML, but since it's also important
        # the file names are correct, we'll do it here.  Also, it "could" have been left out
        # of the artinfo (attribute), whereas the filename is always there.
        artID = m.group(1)
        # all IDs to upper case.
        artID = artID.upper()

        # import into lxml
        root = etree.fromstring(fileXMLContents)
        pepxml = root

        # save common document (article) field values into artInfo instance for both databases
        artInfo = ArticleInfo(sourceInfoDB, pepxml, artID, logger)

        # walk through bib section and add to refs core database
        # Update this file in the database as "processed"
        currFileInfo.loadForFile(n, solrAPIURL)
        fileTracker.setFileDatabaseRecord(currFileInfo)
        if preCommitFileCount > config.COMMITLIMIT:
            print ("Committing info for %s documents/articles" % config.COMMITLIMIT)
            
        # input to the full-text code
        if solrAPIURL is not None:
            processFileforFullTextCore(pepxml, base, artInfo, solrFT, fileXMLContents)
            if preCommitFileCount > config.COMMITLIMIT:
                preCommitFileCount = 0
                solrFT.commit()
                fileTracker.commit()

        # input to the references core
        if solrAPIURLRefs is not None:
            bibTotalReferenceCount += processBibSection(pepxml, base, artInfo, solrBib)
            if preCommitFileCount > config.COMMITLIMIT:
                preCommitFileCount = 0
                solrBib.commit()
                fileTracker.commit()

        preCommitFileCount += 1
        # close the file, and do the next
        f.close()
        if options.displayVerbose:
            print ("   ...Time: %s seconds." % (time.time() - fileTimeStart))

    # all done with the files.  Do a final commit.
    print ("Performing final commit.")
    try:
        if solrAPIURLRefs is not None:
            solrBib.commit()
            fileTracker.commit()
    except Exception, e:
        print ("Exception: ", e)
    try:
        if solrAPIURL is not None:
            solrFT.commit()
            fileTracker.commit()
    except Exception, e:
        print ("Exception: ", e)

    timeEnd = time.time()

    if bibTotalReferenceCount > 0:
        msg = "Finished! Imported %s documents and %s references. Elapsed time: %s secs" % (len(filenames), bibTotalReferenceCount, timeEnd-timeStart)
    else:
        msg = "Finished! Imported %s documents. Elapsed time: %s secs" % (len(filenames), timeEnd-timeStart)
        
    print (msg)
    config.logger.info(msg)
    if processingWarningCount + processingErrorCount > 0:
        print ("  Issues found.  Warnings: %s, Errors: %s.  See log file %s" % (processingWarningCount, processingErrorCount, logFilename))

# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    main()
