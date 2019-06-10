#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,R0914
from __future__ import print_function
print(
    """ 
    OPAS - Open Publications-Archive Software - Glossary Core Loader

    This module imports references from PEP's processed XML form (bEXP_ARCH1)
       into a Solr database.
       
    Adds data to the core per the pepwebglossary schema
    
    This loader is separate from the other core loaders because it is run infrequently
      and involves only 26 documents from the set.
    
    Example Invocation:
    
            $ python solrXMLGlossaryLoad.py
    
            Use -h for help on arguments.
    
    Initial Release: Neil R. Shapiro 2019-06-06 (python 2.7)
    
    Revisions:
    
    
    """
)

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "0.1.00"
__status__      = "Development"

import re
import os
import time
import sys
import logging
from datetime import datetime
from optparse import OptionParser

import json
import lxml
from lxml import etree
import solr     # Solrpy - supports a number of types of authentication, including basic.  This is "solrpy"

import imp
SourceInfoDB = imp.load_source('sourceInfoDB', '../libs/sourceInfoDB.py')
opasxmllib = imp.load_source('opasxmllib', '../libs/opasXMLHelper.py')


class ExitOnExceptionHandler(logging.StreamHandler):
    """
    Allows us to exit on serious error.
    """
    def emit(self, record):
        super().emit(record)
        if record.levelno in (logging.ERROR, logging.CRITICAL):
            raise SystemExit(-1)

def main():

    #scriptSourcePath = os.path.dirname(os.path.realpath(__file__))
    programNameShort = "OPASGlossaryLoad"

    parser = OptionParser(usage="%prog [options] - PEP Solr Glossary Entry Data Loader", version="%prog ver. 0.1.01")
    parser.add_option("-c", "--corename", dest="coreName", default="pepwebglossary",
                      help="the Solr corename (holding the collection) to connect to, i.e., where to send data, e.g., 'pepwebrefsproto'")
    parser.add_option("-d", "--dataroot", dest="rootFolder", default=r"X:\PEP Dropbox\PEPWeb\_PEPA1\_PEPa1v\_PEPArchive\ZBK\069.PEP",
                      help="Root folder path where input data is located")
    parser.add_option("-l", "--loglevel", dest="logLevel", default=logging.INFO,
                      help="Level at which events should be logged")
    parser.add_option("--resetcore",
                      action="store_true", dest="resetCoreData", default=False,
                      help="reset the data in the glossary core")
    parser.add_option("-u", "--url",
                      dest="solrURL", default="http://localhost:8983/solr/",
                      help="Base URL of Solr api (without core), e.g., http://localhost:8983/solr/", metavar="URL")
    parser.add_option("-v", "--verbose", action="store_true", dest="displayVerbose", default=False,
                      help="Display status and operational timing info as load progresses.")
    parser.add_option("--pw", dest="httpPassword", default=None,
                      help="Password for the server")
    parser.add_option("--userid", dest="httpUserID", default=None,
                      help="UserID for the server")

    (options, args) = parser.parse_args()

    logFilename = programNameShort + "_" + datetime.today().strftime('%Y-%m-%d') + ".log"
    processedDateTime = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')
    processingErrorCount = 0
    processingWarningCount = 0
    processedFilesCount = 0
    logging.basicConfig(handlers=[ExitOnExceptionHandler()], filename=logFilename, level=options.logLevel)
    logger = logging.getLogger(programNameShort)
    logger.info('Started at %s', datetime.today().strftime('%Y-%m-%d %H:%M:%S"'))

    solrAPIURL = options.solrURL + options.coreName  # e.g., http://localhost:8983/solr/pepwebproto'

    print ("Input data Root: ", options.rootFolder)
    print ("Solr Glossary Core: ", options.coreName)
    print ("Reset Core Data: ", options.resetCoreData)
    print ("Logfile: ", logFilename)
    print ("Solr solrAPIURL: ", solrAPIURL)

    solrGlossary = solr.SolrConnection(solrAPIURL)
    time_start = time.time()

    # Reset core's data if requested (mainly for early development)
    if options.resetCoreData:
        solrGlossary.delete_query("*:*")
        solrGlossary.commit()

    # find the Glossaary (bEXP_ARCH1) files (processed with links already) in path
    pat = r"ZBK.069(.*)\(bEXP_ARCH1\)\.(xml|XML)$"
    filePatternMatch = re.compile(pat)
    filenames = []
    countFiles = 0
    for root, d_names, f_names in os.walk(options.rootFolder):
        for f in f_names:
            if filePatternMatch.match(f):
                countFiles += 1
                filenames.append(os.path.join(root, f))

    print ("Ready to import glossary records from %s files at path: %s" % (countFiles, options.rootFolder))
    bibTotalReferenceCount = 0
    for n in filenames:
        f = open(n)
        fileXMLContents = f.read()

        # get file basename without build (which is in paren)
        base = os.path.basename(n)
        artID = os.path.splitext(base)[0]
        m = re.match(r"(.*)\(.*\)", artID)
        artID = m.group(1)
        # all IDs to upper case.
        artID = artID.upper()
        fileTimeStamp = datetime.utcfromtimestamp(os.path.getmtime(n)).strftime('%Y-%m-%dT%H:%M:%SZ')

        # import into lxml
        root = etree.fromstring(fileXMLContents)
        pepxml = root[0]

        # Containing Article data
        #<!-- Common fields -->
        #<!-- Article front matter fields -->
        #---------------------------------------------
        # Usually we put the abbreviated title here, but that won't always work here.

        #<!-- biblio section fields -->
        #Note: currently, this does not include footnotes or biblio include tagged data in document (binc)
        glossaryGroups = pepxml.xpath("/pepkbd3//dictentrygrp")  
        groupCount = len(glossaryGroups)
        print("File %s has %s groups." % (base, groupCount))
        processedFilesCount += 1

        allDictEntries = []
        for glossaryGroup in glossaryGroups:
            glossaryGroupXML = etree.tostring(glossaryGroup, with_tail=False)
            glossaryGroupID = opasxmllib.xmlGetElementAttr(glossaryGroup, "id")
            glossaryGroupTerm = opasxmllib.xmlFindSubElementText(glossaryGroup, "term")
            glossaryGroupAlso = opasxmllib.xmlFindSubElementXML(glossaryGroup, "dictalso")
            if glossaryGroupAlso == "":
                glossaryGroupAlso = None
            print ("Processing Term: %s" % glossaryGroupTerm)
            dictEntries = glossaryGroup.xpath("dictentry")  
            groupTermCount = len(dictEntries)
            counter = 0
            for dictEntry in dictEntries:
                counter += 1
                thisDictEntry = {}
                dictEntryID = glossaryGroupID + ".{:03d}".format(counter)
                dictEntryTerm = opasxmllib.xmlFindSubElementText(dictEntry, "term")
                if dictEntryTerm == "":
                    dictEntryTerm = glossaryGroupTerm
                dictEntryTermType = dictEntry.xpath("term/@type")  
                if dictEntryTermType != []:
                    dictEntryTermType = dictEntryTermType[0]
                else:
                    dictEntryTermType = "term"
                
                dictEntrySrc = opasxmllib.xmlFindSubElementText(dictEntry, "src")
                dictEntryAlso = opasxmllib.xmlFindSubElementXML(dictEntry, "dictalso")
                if dictEntryAlso == "":
                    dictEntryAlso = None
                dictEntryDef = opasxmllib.xmlFindSubElementXML(dictEntry, "def")
                dictEntryDefRest = opasxmllib.xmlFindSubElementXML(dictEntry, "defrest")
                thisDictEntry = {
                    "term_id"             : dictEntryID,
                    "group_id"            : glossaryGroupID,
                    "art_id"              : artID,
                    "term"                : dictEntryTerm,
                    "term_type"           : dictEntryTermType,
                    "term_source"         : dictEntrySrc,
                    "term_also"           : dictEntryAlso,
                    "term_def_xml"        : dictEntryDef,
                    "term_def_rest_xml"   : dictEntryDefRest,
                    "group_name"          : glossaryGroupTerm,
                    "group_also"          : glossaryGroupAlso,
                    "group_term_count"    : groupTermCount,
                    "text"                : glossaryGroupXML,
                    "file_name"           : base,
                    "timestamp"           : processedDateTime,
                    "file_last_modified"  : fileTimeStamp
                }
                allDictEntries.append(thisDictEntry)

        # We collected all the dictentries for the group.  Now lets save the whole shebang
        try:
            response_update = solrGlossary.add_many(allDictEntries)  # lets hold off on the , _commit=True)
    
            if not re.search('"status">0</int>', response_update):
                print (response_update)
        except Exception, err:
            logger.error("Solr call exception %s", err)
    
        f.close()

    solrGlossary.commit()
    time_end = time.time()

    msg = "Finished! Imported %s documents with %s references. Elapsed time: %s secs" % (len(filenames), bibTotalReferenceCount, time_end-time_start)
    print (msg)
    logger.info(msg)
    if processingWarningCount + processingErrorCount > 0:
        print ("  Issues found.  Warnings: %s, Errors: %s.  See log file %s" % (processingWarningCount, processingErrorCount, logFilename))

# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    main()
