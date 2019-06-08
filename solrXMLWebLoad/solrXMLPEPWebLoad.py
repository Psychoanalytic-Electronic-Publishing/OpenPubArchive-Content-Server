#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
from __future__ import print_function
print(
    """ 
    OPAS - Open Publications-Archive Software - Document, Authors, and References Core Loader
    
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
__version__     = "0.1.24"
__status__      = "Development"

#Revision Notes:
    #2019-05-16: Addded command line options to specify a different path for PEPSourceInfo.json
                 #Added error logging using python's built-in logging library default INFO level

    #2019-06-05: added int fields for year as they are needeed to do faceting ranges (though that's
                 #beginning to be unclear)


# Disable many annoying pylint messages, warning me about variable naming for example.
# yes, in my Solr code I'm caught between two worlds of snake_case and camelCase.

import re
import sys
import os
import os.path
import time
import logging
import urllib

from datetime import datetime
from optparse import OptionParser
#from base64 import b64encode

from lxml import etree
import solr     # supports a number of types of authentication, including basic.  This is "solrpy"

import config
from OPASFileTracker import FileTracker, FileTrackingInfo

import imp
SourceInfoDB = imp.load_source('sourceInfoDB', '../libs/sourceInfoDB.py')
opasxmllib = imp.load_source('opasxmllib', '../libs/opasXMLHelper.py')

# Module Globals
#authorTracker = AuthorTracker()

class ExitOnExceptionHandler(logging.StreamHandler):
    """
    Allows us to exit on serious error.
    """
    def emit(self, record):
        super().emit(record)
        if record.levelno in (logging.ERROR, logging.CRITICAL):
            raise SystemExit(-1)

class ArticleInfo(object):
    """
    Grab all the article metadata, and save as instance variables.
    """
    def __init__(self, sourceInfoDBData, pepxml, artID, logger):
        #global options
        # let's just double check artid!
        self.artID = artID
        # Just init these.  Creator will set based on filename
        self.fileClassification = None
        self.fileSize = 0  
        self.fileTimeStamp = ""
        self.fileName = ""

        # now, the rest of the variables we can set from the data
        processedDateTime = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')
        self.processedDateTime = processedDateTime  # use same time for all files this run

        try:
            self.artIDFromFile = pepxml.xpath('//artinfo/@id')[0]
            self.artIDFromFile = self.artIDFromFile.upper()

            if self.artIDFromFile != self.artID:
                logger.warn("File name ID tagged and artID disagree.  %s vs %s", self.artID, self.artIDFromFile)
        except Exception, err:
            logger.warn("Issue reading file's article id. (%s)", err)

        # Containing Article data
        #<!-- Common fields -->
        #<!-- Article front matter fields -->
        #---------------------------------------------
        self.artPepSrcCode = pepxml.xpath("//artinfo/@j")[0]
        try:
            self.artPepSourceTitleAbbr = sourceInfoDBData[self.artPepSrcCode].get("sourcetitleabbr", None)
            self.artPepSourceTitleFull = sourceInfoDBData[self.artPepSrcCode].get("sourcetitlefull", None)
            self.artPepSourceType = sourceInfoDBData[self.artPepSrcCode].get("pep_class", None)  # journal, book, video...
            self.artPepSrcEmbargo = sourceInfoDBData[self.artPepSrcCode].get("wall", None)

        except KeyError, err:
            self.artPepSourceTitleAbbr = None
            self.artPepSourceTitleFull = None
            self.artPepSourceType = None
            self.artPepSrcEmbargo = None
            logger.warn("Error: PEP Source %s not found in source info db.  Use the 'PEPSourceInfo export' after fixing the issn table in MySQL DB", self.artPepSrcCode)

        except Exception, err:
            logger.error("Error: Problem with this files source info. File skipped. (%s)", err)
            #processingErrorCount += 1
            return
        self.artVol = opasxmllib.xmlGetTextSingleton(pepxml, '//artinfo/artvol/node()', defaultReturn=None)
        self.artIssue = opasxmllib.xmlGetTextSingleton(pepxml, '//artinfo/artiss/node()', defaultReturn=None)
        self.artIssueTitle = opasxmllib.xmlGetTextSingleton(pepxml, '//artinfo/isstitle/node()', defaultReturn=None)
        self.artYear = opasxmllib.xmlGetTextSingleton(pepxml, '//artinfo/artyear/node()')
        try:
            artYearForInt = re.sub("[^0-9]", "", self.artYear)
            self.artYearInt = int(artYearForInt)
        except ValueError, err:
            logging.warn("Error converting artYear to int: %s", self.artYear)
            self.artYearInt = 0

        artInfoNode = pepxml.xpath('//artinfo')[0]
        self.artType = opasxmllib.xmlGetElementAttr(artInfoNode, "arttype") 
        self.artDOI = opasxmllib.xmlGetElementAttr(artInfoNode, "doi") 
        self.artISSN = opasxmllib.xmlGetElementAttr(artInfoNode, "ISSN") 
        self.artOrigRX = opasxmllib.xmlGetElementAttr(artInfoNode, "origrx", defaultReturn=None) 
        self.newSecNm = opasxmllib.xmlGetElementAttr(artInfoNode, "newsecnm", defaultReturn=None) 
        self.artPgrg = opasxmllib.xmlFindSubElementText(artInfoNode, "artpgrg")  # note: getSingleSubnodeText(pepxml, "artpgrg"),

        self.artTitle = opasxmllib.xmlFindSubElementXML(artInfoNode, "arttitle")
        if self.artTitle != None and self.artTitle != "":
            # remove tags:
            self.artTitle = ''.join(etree.fromstring(self.artTitle).itertext())
        self.artSubtitle = opasxmllib.xmlFindSubElementXML(artInfoNode, 'artsub')
        if self.artSubtitle == "":
            pass
        elif self.artSubtitle is None:
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
        self.authorList = self.artAuthors = pepxml.xpath('//artinfo/artauth/aut[@listed="true"]/@authindexid')
        self.authorXMLList = pepxml.xpath('//artinfo/artauth/aut')
        self.artAuthors = ", ".join(self.artAuthors)
        self.artKwds = opasxmllib.xmlGetTextSingleton(pepxml, "//artinfo/artkwds/node()")

        # Usually we put the abbreviated title here, but that won't always work here.
        self.artCiteAsXML = """<p class="citeas"><span class="authors">%s</span> (<span class="year">%s</span>) <span class="title">%s</span>. <span class="sourcetitle">%s</span> <span class="pgrg">%s</span>:<span class="pgrg">%s</span></p>""" \
            %                   (self.artAuthors,
                                 self.artYear,
                                 self.artTitle,
                                 self.artPepSourceTitleFull,
                                 self.artVol,
                                 self.artPgrg)

        artQualNode = pepxml.xpath("//artinfo/artqual")
        self.artQual = opasxmllib.xmlGetElementAttr(artQualNode, "rx") 
        bibReferences = pepxml.xpath("/pepkbd3//be")
        self.artBibReferenceCount = len(bibReferences)

def processArticleForDocCore(pepxml, artInfo, solrcon, fileXMLContents):
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
    #------------------------------------------------------------------------------------------------------
    if options.displayVerbose:
        print("   ...Processing main file content for the %s core." % options.fullTextCoreName)

    artLang = pepxml.xpath('//@lang')
    if artLang == []:
        artLang = ['EN']

    # this build of the schema now has all XML data fields indicated in the field name
    # the solr schema names are in snake_case; variables in the code here are camelCase
    # by my own coding habits.

    headings = opasxmllib.xmlElementsToStrings(pepxml, "//h1")
    headings += opasxmllib.xmlElementsToStrings(pepxml, "//h2")
    headings += opasxmllib.xmlElementsToStrings(pepxml, "//h3")
    headings += opasxmllib.xmlElementsToStrings(pepxml, "//h4")
    headings += opasxmllib.xmlElementsToStrings(pepxml, "//h5")
    headings += opasxmllib.xmlElementsToStrings(pepxml, "//h6")
  
    # see if this is an offsite article
    if artInfo.fileClassification == "pepoffsite":
        # certain fields should not be stored in returnable areas.  So full-text searchable special field for that.
        offsiteContents = fileXMLContents
        
        fileXMLContents = """<html>
                             <p>This article or book is available online on a non-PEP website. 
                                Click <a href="//www.doi.org/%s" target="_blank">here</a> to open that website 
                                in another window or tab.
                             </p>
                             </html>
                          """ % urllib.quote(artInfo.artDOI)
        # should we trust clients, or remove this data?  For now, remove.  Need to probably do this in biblio core too
        dialogsXml = dreamsXml = notesXml = panelsXml = poemsXml = quotesXml = None    
        referencesXml = abstractsXml = summariesXml = None
    else: # other PEP classified files, peparchive, pepcurrent, pepfree can have the full-text
        offsiteContents = ""
        #TODO: Later, it may be that we don't need Solr to store these, just index them.  If so, the schema can be changed.
        dialogsXml = opasxmllib.xmlElementsToStrings(pepxml, "//dialog"),
        dreamsXml = opasxmllib.xmlElementsToStrings(pepxml, "//dream"),
        notesXml = opasxmllib.xmlElementsToStrings(pepxml, "//note"),
        panelsXml = opasxmllib.xmlElementsToStrings(pepxml, "//panel"),
        poemsXml = opasxmllib.xmlElementsToStrings(pepxml, "//poem"),
        quotesXml = opasxmllib.xmlElementsToStrings(pepxml, "//quote"),
        referencesXml = opasxmllib.xmlElementsToStrings(pepxml, "/pepkbd3//be"),
        summariesXml = opasxmllib.xmlElementsToStrings(pepxml, "//summaries"),
        abstractsXml = opasxmllib.xmlElementsToStrings(pepxml, "//abs")
        if abstractsXml == "":
            if summariesXml == "":
                abstractsXml = opasxmllib.xmlElementsToStrings(pepxml, "//p")[0:20]
            else:
                abstractsXml = summariesXml
        
    #save main article info    
    try:
        response_update = solrcon.add(id = artInfo.artID,                   # important =  note this is unique id for every reference
                                      art_id = artInfo.artID,
                                      file_last_modified = artInfo.fileTimeStamp,
                                      file_classification = artInfo.fileClassification,
                                      file_size = artInfo.fileSize,
                                      file_name = artInfo.fileName,
                                      timestamp = artInfo.processedDateTime,  # When batch was entered into core
                                      art_title_xml = opasxmllib.xmlElementsToStrings(pepxml, "//arttitle"),
                                      art_subtitle_xml = opasxmllib.xmlElementsToStrings(pepxml, "//artsubtitle"),
                                      title = artInfo.artTitle,
                                      art_pepsrccode = artInfo.artPepSrcCode,
                                      art_pepsourcetitleabbr = artInfo.artPepSourceTitleAbbr,
                                      art_pepsourcetitlefull = artInfo.artPepSourceTitleFull,
                                      art_pepsourcetype = artInfo.artPepSourceType,
                                      art_authors = artInfo.artAuthors,
                                      art_authors_unlisted = pepxml.xpath('//artinfo/artauth/aut[@listed="false"]/@authindexid'),
                                      art_authors_xml = opasxmllib.xmlElementsToStrings(pepxml, "//aut"),
                                      art_year = artInfo.artYear,
                                      art_year_int = artInfo.artYearInt,
                                      art_vol = artInfo.artVol,
                                      art_pgrg = artInfo.artPgrg,
                                      art_iss = artInfo.artIssue,
                                      art_iss_title = artInfo.artIssueTitle,
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
                                      author_bio_xml = opasxmllib.xmlElementsToStrings(pepxml, "//nbio"),
                                      author_aff_xml = opasxmllib.xmlElementsToStrings(pepxml, "//autaff"),
                                      bk_title_xml = opasxmllib.xmlElementsToStrings(pepxml, "//artbkinfo/bktitle"),
                                      bk_alsoknownas_xml = opasxmllib.xmlElementsToStrings(pepxml, "//artbkinfo/bkalsoknownas"),
                                      bk_editors_xml = opasxmllib.xmlElementsToStrings(pepxml, "//bkeditors"),
                                      bk_seriestitle_xml = opasxmllib.xmlElementsToStrings(pepxml, "//bkeditors"),
                                      bk_pubyear = pepxml.xpath("//bkpubyear/node()"),
                                      caption_text_xml = opasxmllib.xmlElementsToStrings(pepxml, "//caption"),
                                      caption_title_xml = opasxmllib.xmlElementsToStrings(pepxml, "//ctitle"),
                                      headings_xml = headings,
                                      abstracts_xml = abstractsXml,
                                      summaries_xml = summariesXml,
                                      terms_xml = opasxmllib.xmlElementsToStrings(pepxml, "//impx[@type='TERM2']"),
                                      terms_highlighted_xml = opasxmllib.xmlElementsToStrings(pepxml, "//b") + opasxmllib.xmlElementsToStrings(pepxml, "//i"),
                                      dialogs_spkr = pepxml.xpath("//dialog/spkr/node()"),
                                      dialogs_xml = dialogsXml,
                                      dreams_xml = dreamsXml,
                                      notes_xml = notesXml,
                                      panels_spkr = opasxmllib.xmlElementsToStrings(pepxml, "//panel/spkr"),
                                      panels_xml = panelsXml,
                                      poems_src = pepxml.xpath("//poem/src/node()"),
                                      poems_xml = poemsXml,
                                      quotes_spkr = pepxml.xpath("//quote/spkr/node()"),
                                      quotes_xml = quotesXml,
                                      reference_count = artInfo.artBibReferenceCount,
                                      references_xml = referencesXml,
                                      meta_xml = opasxmllib.xmlElementsToStrings(pepxml, "//meta"),
                                      text_xml = unicode(fileXMLContents, "utf8"),
                                      text_offsite = unicode(offsiteContents, "utf8")
                                     )
        if not re.search('"status">0</int>', response_update):
            print (response_update)
    except Exception, err:
        #processingErrorCount += 1
        print ("Error for :", artInfo.artID, err)
        config.logger.error("Solr call exception for save doc %s", err)

    return

#------------------------------------------------------------------------------------------------------
def processInfoForAuthorCore(pepxml, artInfo, solrAuthor):
    """
    Get author data and write a record for each author in each document.  Hence an author
       of multiple articles will be listed multiple times, once for each article.  But
       this core will let us research by individual author, including facets.
       
    """
    #------------------------------------------------------------------------------------------------------
    # update author data
    #<!-- ID = PEP articleID + authorID -->
    try:
        # Save author info in database
        authorPos = 0
        for author in artInfo.authorXMLList:
            authorID = author.attrib['authindexid']
            authorListed = author.attrib['listed']
            if authorListed.lower() == "true":
                authorPos += 1
            authorRole = author.attrib['role']
            authorXML = etree.tostring(author)
            authorDocid = artInfo.artID + "." + ''.join(e for e in authorID if e.isalnum())
            authorBio = opasxmllib.xmlElementsToStrings(author, "nbio")
            try:
                authorAffID = author.attrib['affid']
            except KeyError, e:
                authorAffil = None  # see if the add still takes!
            else:
                authorAffil = pepxml.xpath('//artinfo/artauth/autaff[@affid="%s"]' % authorAffID)
                authorAffil = etree.tostring(authorAffil[0])
               
            try:  
                response_update = solrAuthor.add(id = authorDocid,         # important =  note this is unique id for every author + artid
                                              art_id = artInfo.artID,
                                              title = artInfo.artTitle,
                                              authors = artInfo.artAuthors,
                                              art_author_id = authorID,
                                              art_author_listed = authorListed,
                                              art_author_pos_int = authorPos,
                                              art_author_role = authorRole,
                                              art_author_bio = authorBio,
                                              art_author_affil = authorAffil,
                                              art_year_int = artInfo.artYearInt,
                                              art_pepsourcetype = artInfo.artPepSourceType,
                                              art_pepsourcetitlefull = artInfo.artPepSourceTitleFull,
                                              art_citeas_xml = artInfo.artCiteAsXML,
                                              art_author_xml = authorXML,
                                              file_last_modified = artInfo.fileTimeStamp,
                                              file_classification = artInfo.fileClassification,
                                              file_name = artInfo.fileName,
                                              timestamp = artInfo.processedDateTime  # When batch was entered into core
                                             )
                if not re.search('"status">0</int>', response_update):
                    print (response_update)
            except Exception, err:
                #processingErrorCount += 1
                print ("Error for :", artInfo.artID, err)
                config.logger.error("Solr call exception for save author %s", err)
               

    except Exception, err:
        #processingErrorCount += 1
        print ("Error for :", artInfo.artID, err)
          

#------------------------------------------------------------------------------------------------------
def processBibForReferencesCore(pepxml, artInfo, solrcon):
    """
    Adds data to the core per the pepwebrefs schema

    TODO: This is the slowest of the two data adds.  It does multiple transactions
          per document (one per reference).  This could be redone as an AddMany transaction,
          assuming AddMany can handle as many references as we might find in a document.
          It's not unbearably slow locally, but via the API remotely, it adds up.
          Remotely to Bitnami AWS with a 1GB memory: 0.0476 seconds per reference

    """
    #------------------------------------------------------------------------------------------------------
    #<!-- biblio section fields -->
    #Note: currently, this does not include footnotes or biblio include tagged data in document (binc)
    bibReferences = pepxml.xpath("/pepkbd3//be")  # this is the second time we do this (also in artinfo, but not sure or which is better per space vs time considerations)
    retVal = artInfo.artBibReferenceCount
    if options.displayVerbose:
        print("   ...Processing %s references for the references database." % (artInfo.artBibReferenceCount))
    #processedFilesCount += 1

    allRefs = []
    for ref in bibReferences:
        config.bibTotalReferenceCount += 1
        bibRefEntry = etree.tostring(ref, with_tail=False)
        bibRefID = opasxmllib.xmlGetElementAttr(ref, "id")
        refID = artInfo.artID + "." + bibRefID
        bibSourceTitle = opasxmllib.xmlFindSubElementText(ref, "j")
        bibPublishers = opasxmllib.xmlFindSubElementText(ref, "bp")
        if bibPublishers != "":
            bibSourceType = "book"
        else:
            bibSourceType = "journal"
        if bibSourceType == "book":
            bibYearofPublication = opasxmllib.xmlFindSubElementText(ref, "bpd")
            if bibYearofPublication == "":
                bibYearofPublication = opasxmllib.xmlFindSubElementText(ref, "y")
            if bibSourceTitle is None or bibSourceTitle == "":
                # sometimes has markup
                bibSourceTitle = opasxmllib.xmlGetSingleDirectSubnodeText(ref, "bst")  # book title
        else:
            bibYearofPublication = opasxmllib.xmlFindSubElementText(ref, "y")
           
        if bibYearofPublication == "":
            # try to match
            try:
                bibYearofPublication = re.search(r"\(([A-z]*\s*,?\s*)?([12][0-9]{3,3}[abc]?)\)", bibRefEntry).group(2)
            except Exception, e:
                logging.warn("no match %s/%s/%s" % (bibYearofPublication, ref, e))
            
        try:
            bibYearofPublication = re.sub("[^0-9]", "", bibYearofPublication)
            bibYearofPublicationInt = int(bibYearofPublication[0:4])
        except ValueError, e:
            logging.warn("Error converting bibYearofPublication to int: %s / %s.  (%s)" % (bibYearofPublication, bibRefEntry, e))
            bibYearofPublicationInt = 0
        except Exception, e:
            logging.warn("Error trying to find untagged bib year in %s (%s)" % (bibRefEntry, e))
            bibYearofPublicationInt = 0
            

        bibAuthorNameList = [etree.tostring(x, with_tail=False) for x in ref.findall("a") if x is not None]
        bibAuthorsXml = '; '.join(bibAuthorNameList)
        #Note: Changed to is not None since if x gets warning - FutureWarning: The behavior of this method will change in future versions. Use specific 'len(elem)' or 'elem is not None' test instead
        authorList = [opasxmllib.xmlGetTextOnly(x) for x in ref.findall("a") if opasxmllib.xmlGetTextOnly(x) is not None]  # final if x gets rid of any None entries which can rarely occur.
        authorList = '; '.join(authorList)
        bibRefRxCf = opasxmllib.xmlGetElementAttr(ref, "rxcf", defaultReturn=None)
        bibRefRx = opasxmllib.xmlGetElementAttr(ref, "rx", defaultReturn=None)
        if bibRefRx != None:
            bibRefRxSourceCode = re.search("(.*?)\.", bibRefRx, re.IGNORECASE).group(1)
        else:
            bibRefRxSourceCode = None
            
        # see if this is an offsite article
        if artInfo.fileClassification == "pepoffsite":
            # certain fields should not be stored in returnable areas.  So full-text searchable special field for that.
            bibRefOffsiteEntry = bibRefEntry
          
            #bibEntryXMLContents = """<html>
                                 #<p>This reference is in an article or book where text is not is available on PEP. 
                                    #Click <a href="//www.doi.org/%s" target="_blank">here</a> to show the article on another website 
                                    #in another window or tab.
                                 #</p>
                                 #</html>
                              #""" % urllib.quote(artInfo.artDOI)
            # should we trust clients, or remove this data?  For now, remove.  Need to probably do this in biblio core too
            bibRefEntry = None
        else:
            bibRefOffsiteEntry = None
    
        thisRef = {
                    "id" : refID,
                    "art_id" : artInfo.artID,
                    "file_last_modified" : artInfo.fileTimeStamp,
                    "file_classification" : artInfo.fileClassification,
                    "file_size" : artInfo.fileSize,
                    "file_name" : artInfo.fileName,
                    "timestamp" : artInfo.processedDateTime,  # When batch was entered into core
                    "art_title" : artInfo.artTitle,
                    "art_pepsrccode" : artInfo.artPepSrcCode,
                    "art_pepsourcetitleabbr" : artInfo.artPepSourceTitleAbbr,
                    "art_pepsourcetitlefull" : artInfo.artPepSourceTitleFull,
                    "art_pepsourcetype" : artInfo.artPepSourceType,
                    "art_authors" : artInfo.artAuthors,
                    "reference_count" :artInfo.artBibReferenceCount,  # would be the same for each reference in article, but could still be useful
                    "art_year" : artInfo.artYear,
                    "art_year_int" : artInfo.artYearInt,
                    "art_vol" : artInfo.artVol,
                    "art_pgrg" : artInfo.artPgrg,
                    "art_lang" : artInfo.artLang,
                    "art_citeas_xml" : artInfo.artCiteAsXML,
                    "text_ref" : bibRefEntry,                        
                    "text_offsite_ref": bibRefOffsiteEntry,
                    "authors" : authorList,
                    "title" : opasxmllib.xmlFindSubElementText(ref, "t"),
                    "bib_authors_xml" : bibAuthorsXml,
                    "bib_ref_id" : bibRefID,
                    "bib_ref_rx" : bibRefRx,
                    "bib_ref_rxcf" : bibRefRxCf, # the not 
                    "bib_ref_rx_sourcecode" : bibRefRxSourceCode,
                    "bib_articletitle" : opasxmllib.xmlFindSubElementText(ref, "t"),
                    "bib_sourcetype" : bibSourceType,
                    "bib_sourcetitle" : bibSourceTitle,
                    "bib_pgrg" : opasxmllib.xmlFindSubElementText(ref, "pp"),
                    "bib_year" : bibYearofPublication,
                    "bib_year_int" : bibYearofPublicationInt,
                    "bib_volume" : opasxmllib.xmlFindSubElementText(ref, "v"),
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

#------------------------------------------------------------------------------------------------------
def main():
    
    global options  # so the information can be used in support functions
    global bibTotalReferenceCount

    programNameShort = "OPASWebLoaderPEP"  # used for log file
    scriptSourcePath = os.path.dirname(os.path.realpath(__file__))
    logFilename = programNameShort + "_" + datetime.today().strftime('%Y-%m-%d') + ".log"

    parser = OptionParser(usage="%prog [options] - PEP Solr Reference Text Data Loader", version="%prog ver. 0.1.13")
    parser.add_option("-a", "--allfiles", action="store_true", dest="forceRebuildAllFiles", default=False,
                      help="Option to force all files to be updated on the specified cores.  This does not reset the file tracker but updates it as files are processed.")
    parser.add_option("-b", "--bibliocorename", dest="biblioCoreName", default=None,
                      help="the Solr corename (holding the collection) to connect to, i.e., where to send data.  Example: 'pepwebrefs'")
    parser.add_option("-d", "--dataroot", dest="rootFolder", default=config.DEFAULTDATAROOT,
                      help="Root folder path where input data is located")
    parser.add_option("-f", "--fulltextcorename", dest="fullTextCoreName", default=None,
                      help="the Solr corename (holding the collection) to connect to, i.e., where to send data.  Example: 'pepwebdocs'")
    parser.add_option("-l", "--loglevel", dest="logLevel", default=logging.INFO,
                      help="Level at which events should be logged")
    parser.add_option("--logfile", dest="logfile", default=logFilename,
                      help="Logfile name with full path where events should be logged")
    parser.add_option("--resetcore",
                      action="store_true", dest="resetCoreData", default=False,
                      help="reset the data in the selected cores. (authorscore is reset with the fulltext core)")
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

    #processingErrorCount = 0
    #processingWarningCount = 0
    processedFilesCount = 0
    logging.basicConfig(handlers=[ExitOnExceptionHandler()], filename=logFilename, level=options.logLevel)
    logger = config.logger = logging.getLogger(programNameShort)

    logger.info('Started at %s', datetime.today().strftime('%Y-%m-%d %H:%M:%S"'))

    solrAPIURL = None
    solrAPIURLRefs = None

    if options.fullTextCoreName is not None:
        solrAPIURL = options.solrURL + options.fullTextCoreName  # e.g., http://localhost:8983/solr/    + pepwebdocs'
    if options.biblioCoreName is not None:
        solrAPIURLRefs = options.solrURL + options.biblioCoreName  # e.g., http://localhost:8983/solr/  + pepwebrefs'

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
    sourceDB = SourceInfoDB.SourceInfoDB()

    #TODO: Try without the None test, the library should not try to use None as user name or password, so only the first case may be needed
    # The connection call is to solrpy (import was just solr)
    if options.httpUserID is not None and options.httpPassword is not None:
        if options.fullTextCoreName is not None:
            solrDocs = solr.SolrConnection(solrAPIURL, http_user=options.httpUserID, http_pass=options.httpPassword)
            solrAuthor = solr.SolrConnection(options.solrURL + config.AUTHORCORENAME, http_user=options.httpUserID, http_pass=options.httpPassword)
        if options.biblioCoreName is not None:
            solrBib = solr.SolrConnection(solrAPIURLRefs, http_user=options.httpUserID, http_pass=options.httpPassword)
    else:
        if options.fullTextCoreName is not None:
            solrDocs = solr.SolrConnection(solrAPIURL)
            solrAuthor = solr.SolrConnection(options.solrURL + config.AUTHORCORENAME)
        if options.biblioCoreName is not None:
            solrBib = solr.SolrConnection(solrAPIURLRefs)

    # Reset core's data if requested (mainly for early development)
    if options.resetCoreData:
        if options.fullTextCoreName is not None:
            print ("*** Deleting all data from the full text core ***")
            solrDocs.delete_query("*:*")
            solrDocs.commit()
        if options.biblioCoreName is not None:
            print ("*** Deleting all data from the References core ***")
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
                currFileInfo.loadForFile(filename, options.solrURL)  # mod 2019-06-05 Just the base URL, not the core
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
    print ("%s Files to process" % (newFiles ))
    print (80*"-")
    bibTotalReferenceCount = 0
    preCommitFileCount = 0
    processedFilesCount = 0
    

    for n in filenames:
        fileTimeStart = time.time()
        processedFilesCount += 1
        f = open(n)
        fileXMLContents = f.read()
        
        # get file basename without build (which is in paren)
        base = os.path.basename(n)
        artID = os.path.splitext(base)[0]
        m = re.match(r"(.*)\(.*\)", artID)

        # Update this file in the database as "processed"
        currFileInfo.loadForFile(n, options.solrURL)
        fileTracker.setFileDatabaseRecord(currFileInfo)
        fileTimeStamp = datetime.utcfromtimestamp(currFileInfo.fileModDate).strftime('%Y-%m-%dT%H:%M:%SZ')
        print ("Processing file #%s of %s: %s (%s bytes)." % (processedFilesCount, newFiles, base, currFileInfo.fileSize))

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
        artInfo = ArticleInfo(sourceDB.sourceData, pepxml, artID, logger)
        artInfo.fileTimeStamp = fileTimeStamp
        artInfo.fileName = base
        artInfo.fileSize = currFileInfo.fileSize
        try:
            artInfo.fileClassification = re.search("(pepcurrent|peparchive|pepfuture|pepfree|pepoffsite)", n, re.IGNORECASE).group(1)
            # set it to lowercase for ease of matching later
            artInfo.fileClassification = artInfo.fileClassification.lower()
        except Exception, e:
            logging.warn("Could not determine file classification for %s (%s)" % (n, e))
        

        # walk through bib section and add to refs core database

        if preCommitFileCount > config.COMMITLIMIT:
            print ("Committing info for %s documents/articles" % config.COMMITLIMIT)
            
        # input to the full-text code
        if solrAPIURL is not None:
            # this option will also load the biblio and authors cores.
            processArticleForDocCore(pepxml, artInfo, solrDocs, fileXMLContents)
            processInfoForAuthorCore(pepxml, artInfo, solrAuthor)
            if preCommitFileCount > config.COMMITLIMIT:
                preCommitFileCount = 0
                solrDocs.commit()
                solrAuthor.commit()
                fileTracker.commit()

        # input to the references core
        if solrAPIURLRefs is not None:
            bibTotalReferenceCount += processBibForReferencesCore(pepxml, artInfo, solrBib)
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
            solrDocs.commit()
            solrAuthor.commit()
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
    #if processingWarningCount + processingErrorCount > 0:
        #print ("  Issues found.  Warnings: %s, Errors: %s.  See log file %s" % (processingWarningCount, processingErrorCount, logFilename))

# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    main()
