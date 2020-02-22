#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
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
                
                (Requires Python 3.7)
        
    """
)

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2019.1231.1"
__status__      = "Development"

#Revision Notes:
    #2019-05-16: Addded command line options to specify a different path for PEPSourceInfo.json
                 #Added error logging using python's built-in logging library default INFO level - nrs

    #2019-06-05: added int fields for year as they are needeed to do faceting ranges (though that's
                 #beginning to be unclear) - nrs

    #2019-07-05: added citedCounts processing to load the Solr core from the mySQL database 
                 #table which calculates these. - nrs
    #2019-12-31: Support remote datbase tunnel.  Fix use of SQL when not using SQLite.
    #2020-01-05: Some fields marked xml were being loaded as text...fixed.
    

# Disable many annoying pylint messages, warning me about variable naming for example.
# yes, in my Solr code I'm caught between two worlds of snake_case and camelCase.

import sys
sys.path.append('../libs')
import re
import os
import os.path
import time
import logging
import urllib.request, urllib.parse, urllib.error
import random
import pysolr

import modelsOpasCentralPydantic

pyVer = 2
if (sys.version_info > (3, 0)):
    # Python 3 code in this block
    from io import StringIO
    pyVer = 3
else:
    # Python 2 code in this block
    import StringIO

from datetime import datetime
from optparse import OptionParser

from lxml import etree
import solrpy as solr
import pymysql

import config
import opasConfig

from OPASFileTrackerMySQL import FileTracker, FileTrackingInfo
import opasXMLHelper as opasxmllib
import opasCentralDBLib
import localsecrets

# Module Globals
gCitedTable = dict() # large table of citation counts, too slow to run one at a time.

#authorTracker = AuthorTracker()

class ExitOnExceptionHandler(logging.StreamHandler):
    """
    Allows us to exit on serious error.
    """
    def emit(self, record):
        super().emit(record)
        if record.levelno in (logging.ERROR, logging.CRITICAL):
            raise SystemExit(-1)

class BiblioEntry(object):
    def __init__(self, artInfo, ref):
        self.art_id = artInfo.artID
        self.ref_entry = etree.tostring(ref, with_tail=False)
        self.ref_local_id= opasxmllib.xml_get_element_attr(ref, "id")
        self.title = opasxmllib.xml_get_subelement_textsingleton(ref, "t") 
        self.pgrg = opasxmllib.xml_get_subelement_textsingleton(ref, "pp")
        self.rx = opasxmllib.xml_get_element_attr(ref, "rx", default_return=None)
        self.rxcf = opasxmllib.xml_get_element_attr(ref, "rxcf", default_return=None)
        if self.ref_rx != None:
            self.ref_rx_sourcecode = re.search("(.*?)\.", bibRefRx, re.IGNORECASE).group(1)
        else:
            self.ref_rx_sourcecode = None
        
        self.volume = opasxmllib.xml_get_subelement_textsingleton(ref, "v"), 
        self.source_title = opasxmllib.xml_get_subelement_textsingleton(ref, "j")
        self.publishers = opasxmllib.xml_get_subelement_textsingleton(ref, "bp")
        if self.publishers != "":
            self.source_type = "book"
        else:
            self.source_type = "journal"
        if self.source_type == "book":
            self.yearof_publication = opasxmllib.xml_get_subelement_textsingleton(ref, "bpd")
            if self.yearof_publication == "":
                self.yearof_publication = opasxmllib.xml_get_subelement_textsingleton(ref, "y")
            if self.source_title is None or self.source_title == "":
                # sometimes has markup
                self.source_title = opasxmllib.xml_get_direct_subnode_textsingleton(ref, "bst")  # book title
        else:
            self.yearof_publication = opasxmllib.xml_get_subelement_textsingleton(ref, "y")
           
        if self.yearof_publication == "":
            # try to match
            try:
                self.yearof_publication = re.search(r"\(([A-z]*\s*,?\s*)?([12][0-9]{3,3}[abc]?)\)", self.ref_entry).group(2)
            except Exception as e:
                logging.warning("no match %s/%s/%s" % (self.yearof_publication, ref, e))
            
        try:
            self.yearof_publication = re.sub("[^0-9]", "", self.yearof_publication)
            self.yearof_publication_int = int(self.yearof_publication[0:4])
        except ValueError as e:
            logging.warning("Error converting bibYearofPublication to int: %s / %s.  (%s)" % (self.yearof_publication, self.ref_entry, e))
            self.yearof_publication_int = 0
        except Exception as e:
            logging.warning("Error trying to find untagged bib year in %s (%s)" % (self.ref_entry, e))
            self.yearof_publication_int = 0

        self.year = self.yearof_publication 
        self.year_int = int(self.year)
        self.author_name_list = [etree.tostring(x, with_tail=False).decode("utf8") for x in ref.findall("a") if x is not None]
        self.authors_xml = '; '.join(self.author_name_list)
        self.author_list = [opasxmllib.xml_elem_or_str_to_text(x) for x in ref.findall("a") if opasxmllib.xml_elem_or_str_to_text(x) is not None]  # final if x gets rid of any None entries which can rarely occur.
        self.author_list = '; '.join(self.author_list)
        self.ref_rxcf = opasxmllib.xml_get_element_attr(ref, "rxcf", default_return=None)
        self.ref_rx = opasxmllib.xml_get_element_attr(ref, "rx", default_return=None)
        if self.ref_rx != None:
            self.ref_rx_source_code = re.search("(.*?)\.", self.ref_rx, re.IGNORECASE).group(1)
        else:
            self.ref_rx_source_code = None

        if artInfo.fileClassification == opasConfig.DOCUMENT_ACCESS_OFFSITE: # "pepoffsite":
            # certain fields should not be stored in returnable areas.  So full-text searchable special field for that.
            self.ref_offsite_entry = self.bibRefEntry
            self.bibRefEntry = None
        else:
            self.ref_offsite_entry = None
        

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
                logger.warning("File name ID tagged and artID disagree.  %s vs %s", self.artID, self.artIDFromFile)
        except Exception as err:
            logger.warning("Issue reading file's article id. (%s)", err)

        # Containing Article data
        #<!-- Common fields -->
        #<!-- Article front matter fields -->
        #---------------------------------------------
        self.artPepSrcCode = pepxml.xpath("//artinfo/@j")[0]
        try:
            self.artPepSrcCode = self.artPepSrcCode.upper()  # 20191115 - To make sure this is always uppercase
            self.artPepSourceTitleAbbr = sourceInfoDBData[self.artPepSrcCode].get("sourcetitleabbr", None)
            self.artPepSourceTitleFull = sourceInfoDBData[self.artPepSrcCode].get("sourcetitlefull", None)
            self.artPepSourceType = sourceInfoDBData[self.artPepSrcCode].get("product_type", None)  # journal, book, video...
            self.artPepSrcEmbargo = sourceInfoDBData[self.artPepSrcCode].get("wall", None)
        except KeyError as err:
            self.artPepSourceTitleAbbr = None
            self.artPepSourceTitleFull = None
            self.artPepSourceType = None
            self.artPepSrcEmbargo = None
            logger.warning("Error: PEP Source %s not found in source info db.  Use the 'PEPSourceInfo export' after fixing the issn table in MySQL DB", self.artPepSrcCode)

        except Exception as err:
            logger.error("Error: Problem with this files source info. File skipped. (%s)", err)
            #processingErrorCount += 1
            return
        self.artVol = opasxmllib.xml_xpath_return_textsingleton(pepxml, '//artinfo/artvol/node()', default_return=None)
        self.artIssue = opasxmllib.xml_xpath_return_textsingleton(pepxml, '//artinfo/artiss/node()', default_return=None)
        self.artIssueTitle = opasxmllib.xml_xpath_return_textsingleton(pepxml, '//artinfo/artissinfo/isstitle/node()', default_return=None)
            
        self.artYear = opasxmllib.xml_xpath_return_textsingleton(pepxml, '//artinfo/artyear/node()', default_return=None)
        try:
            artYearForInt = re.sub("[^0-9]", "", self.artYear)
            self.artYearInt = int(artYearForInt)
        except ValueError as err:
            logging.warn("Error converting artYear to int: %s", self.artYear)
            self.artYearInt = 0

        artInfoNode = pepxml.xpath('//artinfo')[0]
        self.artType = opasxmllib.xml_get_element_attr(artInfoNode, "arttype", default_return=None)
        self.art_vol_title = opasxmllib.xml_xpath_return_textsingleton(pepxml, '//artinfo/artvolinfo/voltitle/node()', default_return=None)
        if self.art_vol_title is None:
            # try attribute for value (lower priority than element above)
            self.art_vol_title = opasxmllib.xml_get_element_attr(artInfoNode, "voltitle", default_return=None)

        if self.art_vol_title is not None:
            print (f"volume title: {self.art_vol_title}")
    
        if self.artIssueTitle is not None:
            print (f"issue title: {self.artIssueTitle}")
            
        self.artDOI = opasxmllib.xml_get_element_attr(artInfoNode, "doi", default_return=None) 
        self.artISSN = opasxmllib.xml_get_element_attr(artInfoNode, "ISSN", default_return=None) 
        self.artOrigRX = opasxmllib.xml_get_element_attr(artInfoNode, "origrx", default_return=None) 
        self.newSecNm = opasxmllib.xml_get_element_attr(artInfoNode, "newsecnm", default_return=None)
        if self.newSecNm is None:
            #  look in newer, tagged, data
            self.newSecNm = opasxmllib.xml_xpath_return_textsingleton(pepxml, '//artsectinfo/secttitle/node()', default_return=None)
        
        self.artPgrg = opasxmllib.xml_get_subelement_textsingleton(artInfoNode, "artpgrg", default_return=None)  # note: getSingleSubnodeText(pepxml, "artpgrg"),

        self.artTitle = opasxmllib.xml_get_subelement_textsingleton(artInfoNode, "arttitle")
        if self.artTitle == "-": # weird title in ANIJP-CHI
            self.artTitle = ""

        self.artSubtitle = opasxmllib.xml_get_subelement_textsingleton(artInfoNode, 'artsub')
        if self.artSubtitle == "":
            pass
        elif self.artSubtitle is None:
            self.artSubtitle = ""
        else:
            #self.artSubtitle = ''.join(etree.fromstring(self.artSubtitle).itertext())
            if self.artTitle != "":
                self.artSubtitle = ": " + self.artSubtitle
                self.artTitle = self.artTitle + self.artSubtitle
            else:
                self.artTitle = self.artSubtitle
                self.artSubtitle = ""
                
        self.artLang = pepxml.xpath('//pepkbd3/@lang')
        
        if self.artLang == []:
            self.artLang = ['EN']
        
        self.authorXMLList = pepxml.xpath('//artinfo/artauth/aut')
        self.authorXML = opasxmllib.xml_xpath_return_xmlsingleton(pepxml, '//artinfo/artauth')
        self.authorsBibStyle, self.authorList = opasxmllib.authors_citation_from_xmlstr(self.authorXML, listed=True)
        # ToDo: I think I should add an author ID to bib aut too.  But that will have
        #  to wait until I rebuild everything in January.
        self.artAuthorIDList = opasxmllib.xml_xpath_return_textlist(pepxml, '//artinfo/artauth/aut[@listed="true"]/@authindexid')
        if self.artAuthorIDList == []: # no authindexid
            logging.warning("This document %s does not have an author list; may be missing authindexids" % artID)
            self.artAuthorIDList = self.authorList
        self.authorMast, self.authorMastList = opasxmllib.author_mast_from_xmlstr(self.authorXML, listed=True)
        self.authorMastStringUnlisted, self.authorMastListUnlisted = opasxmllib.author_mast_from_xmlstr(self.authorXML, listed=False)
        self.authorCount = len(self.authorXMLList)
        self.artAllAuthors = self.authorMast + " (" + self.authorMastStringUnlisted + ")"
        self.artKwds = opasxmllib.xml_xpath_return_textsingleton(pepxml, "//artinfo/artkwds/node()", None)

        # Usually we put the abbreviated title here, but that won't always work here.
        self.artCiteAsXML = u"""<p class="citeas"><span class="authors">%s</span> (<span class="year">%s</span>) <span class="title">%s</span>. <span class="sourcetitle">%s</span> <span class="pgrg">%s</span>:<span class="pgrg">%s</span></p>""" \
            %                   (self.authorsBibStyle,
                                 self.artYear,
                                 self.artTitle,
                                 self.artPepSourceTitleFull,
                                 self.artVol,
                                 self.artPgrg)

        artQualNode = pepxml.xpath("//artinfo/artqual")
        self.artQual = opasxmllib.xml_get_element_attr(artQualNode, "rx", default_return=None) 
        bibReferences = pepxml.xpath("/pepkbd3//be")
        self.artBibReferenceCount = len(bibReferences)
        if bibReferences == []:
            bibReferences = None

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
    #globals gCitedTable
    
    if options.displayVerbose:
        print(("   ...Processing main file content for the %s core." % opasConfig.SOLR_DOCS))

    artLang = pepxml.xpath('//@lang')
    if artLang == []:
        artLang = ['EN']

    # this build of the schema now has all XML data fields indicated in the field name
    # the solr schema names are in snake_case; variables in the code here are camelCase
    # by my own coding habits.

    #headings = opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//h1", default_return=[])
    #headings += opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//h2", default_return=[])
    #headings += opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//h3", default_return=[])
    #headings += opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//h4", default_return=[])
    #headings += opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//h5", default_return=[])
    #headings += opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//h6", default_return=[])
  
    # see if this is an offsite article
    if artInfo.fileClassification == opasConfig.DOCUMENT_ACCESS_OFFSITE:
        # certain fields should not be stored in returnable areas.  So full-text searchable special field for that.
        offsiteContents = fileXMLContents
        
        fileXMLContents = """<html>
                             <p>This article or book is available online on a non-PEP website. 
                                Click <a href="//www.doi.org/%s" target="_blank">here</a> to open that website 
                                in another window or tab.
                             </p>
                             </html>
                          """ % urllib.parse.quote(artInfo.artDOI)
        # should we trust clients, or remove this data?  For now, remove.  Need to probably do this in biblio core too
        dialogsXml = dreamsXml = notesXml = panelsXml = poemsXml = quotesXml = None    
        #referencesXml = abstractsXml = summariesXml = None
    else: # other PEP classified files, peparchive, pepcurrent, pepfree can have the full-text
        offsiteContents = ""

        summariesXml = opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//summaries", default_return=None)
        abstractsXml = opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//abs", default_return=None)
        # multiple data fields, not needed, search children instead, which allows search by para
        #TODO: Later, it may be that we don't need Solr to store these, just index them.  If so, the schema can be changed.
        #dialogsXml = opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//dialog", default_return=None)
        #dreamsXml = opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//dream", default_return=None)
        #notesXml = opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//note", default_return=None)
        #panelsXml = opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//panel", default_return=None)
        #poemsXml = opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//poem", default_return=None)
        #quotesXml = opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//quote", default_return=None)
        #bodyXml = opasxmllib.xml_xpath_return_xmlsingleton(pepxml, "//body", default_return=None)  # used to search body only
        #referencesXml = opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//be", default_return=None)
        # this was all of the paras in one field, deprecated
        #parasxml = opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//p|//p2")
        if abstractsXml is None:
            if summariesXml is None:
                abstractsXml = opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//p")[0:20]
                if abstractsXml == []:
                    abstractsXml = None
            else:
                abstractsXml = summariesXml

    #art_authors_unlisted = pepxml.xpath(r'//artinfo/artauth/aut[@listed="false"]/@authindexid') 
    citedCounts = gCitedTable.get(artInfo.artID, modelsOpasCentralPydantic.MostCitedArticles())
    # anywhere in the doc.
    children = DocChildren() # new instance, reset child counter suffix
    children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//body//p|//body//p2"),
                          parent_id=artInfo.artID,
                          parent_tag="p_body")
    children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//h1|//h2|//h3|//h4|//h5|//h6"),
                          parent_id=artInfo.artID,
                          parent_tag="p_heading")
    children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//quote//p|//quote//p2"),
                          parent_id=artInfo.artID,
                          parent_tag="p_quote")
    children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//dream//p|//dream//p2"),
                          parent_id=artInfo.artID,
                          parent_tag="p_dream")
    children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//poem//p|//poem//p2"),
                          parent_id=artInfo.artID,
                          parent_tag="p_poem")
    children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//note//p|//note//p2"),
                          parent_id=artInfo.artID,
                          parent_tag="p_note")
    children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//dialog//p|//dialog//p2"),
                          parent_id=artInfo.artID,
                          parent_tag="p_dialog")
    children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//panel//p|//panel//p2"),
                          parent_id=artInfo.artID,
                          parent_tag="p_panel")
    children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//caption//p"),
                          parent_id=artInfo.artID,
                          parent_tag="p_caption")
    children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//bib//be|//binc"),
                          parent_id=artInfo.artID,
                          parent_tag="p_bib")
    children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//appxs//p|//appxs//p2"),
                          parent_id=artInfo.artID,
                          parent_tag="p_appxs")
    # summaries and abstracts
    children.add_children(stringlist=opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//summaries//p|//summaries//p2|//abs//p|//abs//p2"),
                          parent_id=artInfo.artID,
                          parent_tag="p_summaries")

    print (f"Adding children, tags/counts: {children.tag_counts}")

    new_rec = {
                "id": artInfo.artID,                                         # important =  note this is unique id for every reference
                "art_id" : artInfo.artID,                                    # important                                     
                "title" : artInfo.artTitle,                                  # important                                      
                "art_title_xml" : opasxmllib.xml_xpath_return_xmlsingleton(pepxml, "//arttitle"),
                "art_sourcecode" : artInfo.artPepSrcCode,                 # important
                "art_sourcetitleabbr" : artInfo.artPepSourceTitleAbbr,
                "art_sourcetitlefull" : artInfo.artPepSourceTitleFull,
                "art_sourcetype" : artInfo.artPepSourceType,
                # abstract_xml and summaries_xml should not be searched, but useful for display without extracting
                "abstract_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//abs", default_return = None),
                "summaries_xml" : summariesXml,
                # very important field for displaying the whole document or extracting parts
                "text_xml" : fileXMLContents,                                # important
                "text_xml_offsite" : offsiteContents,
                "author_bio_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//nbio", default_return = None),
                "author_aff_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//autaff", default_return = None),
                "bk_title_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//artbkinfo/bktitle", default_return = None),
                "bk_alsoknownas_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//artbkinfo/bkalsoknownas", default_return = None),
                "bk_editors_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//bkeditors", default_return = None),
                "bk_seriestitle_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//bkeditors", default_return = None),
                "caption_text_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml,"//caption", default_return = None),
                "caption_title_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//ctitle", default_return = None),
                #"headings_xml" : headings,
                "meta_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//meta"),"text_xml" : fileXMLContents,
                "timestamp" : artInfo.processedDateTime,                     # important
                "file_last_modified" : artInfo.fileTimeStamp,
                "file_classification" : artInfo.fileClassification,
                "file_size" : artInfo.fileSize,
                "file_name" : artInfo.fileName,
                "art_subtitle_xml" : opasxmllib.xml_xpath_return_xmlsingleton(pepxml, "//artsubtitle", default_return = None),
                "art_citeas_xml" : artInfo.artCiteAsXML,
                "art_cited_all" : citedCounts.countAll,
                "art_cited_5" : citedCounts.count5,
                "art_cited_10" : citedCounts.count10,
                "art_cited_20" : citedCounts.count20,
                #"art_body_xml" : bodyXml,
                "art_authors" : artInfo.authorList,
                "art_authors_mast" : artInfo.authorMast,
                "art_authors_unlisted" : artInfo.authorMastStringUnlisted,
                "art_authors_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//aut", default_return = None),
                "art_year" : artInfo.artYear,
                "art_year_int" : artInfo.artYearInt,
                "art_vol" : artInfo.artVol,
                "art_vol_title" : artInfo.art_vol_title,
                "art_pgrg" : artInfo.artPgrg,
                "art_iss" : artInfo.artIssue,
                "art_iss_title" : artInfo.artIssueTitle,
                "art_doi" : artInfo.artDOI,
                "art_lang" : artInfo.artLang,
                "art_issn" : artInfo.artISSN,
                "art_origrx" : artInfo.artOrigRX,
                "art_qual" : artInfo.artQual,
                "art_kwds" : artInfo.artKwds,
                "art_type" : artInfo.artType,
                "art_newsecnm" : artInfo.newSecNm,
                "authors" :  artInfo.artAllAuthors,
                "terms_xml" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//impx[@type='TERM2']"),
                "terms_highlighted" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//b") + opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//i"),
                "dialogs_spkr" : pepxml.xpath("//dialog/spkr/node()"),
                "panels_spkr" : opasxmllib.xml_xpath_return_xmlstringlist(pepxml, "//panel/spkr"),
                "poems_src" : pepxml.xpath("//poem/src/node()"),
                #"dialogs_xml" : dialogsXml,"dreams_xml" : dreamsXml,
                #"notes_xml" : notesXml,
                #"dreams_xml" : dreamsXml,
                #"panels_xml" : panelsXml,
                #"poems_xml" : poemsXml,
                # "poems" : pepxml.xpath("//quote/spkr/node()"),
                #"quotes_xml" : quotesXml,
                "reference_count" : artInfo.artBibReferenceCount,
                #"references_xml" : referencesXml,
                "bk_pubyear" : pepxml.xpath("//bkpubyear/node()"),
                "art_level" : 1,
                #"art_para" : parasxml, 
                "_doc" : children.child_list
              }

    #experimental paras save
    # parasxml_update(parasxml, solrcon, artInfo)
    # format for pysolr (rather than solrpy, supports nesting)
    try:
        solrcon.add([new_rec], commit=False)
    except Exception as err:
        #processingErrorCount += 1
        errStr = "Solr call exception for save doc on %s: %s" % (artInfo.artID, err)
        print (errStr)
   
 

    return

class DocChildren(object):
    """
    Create an list of child strings to be used as the Solr nested document.
    The parent_tag allows different groups of subelements to be added and separately searchable.
    
    """
    def __init__(self):
        self.count = 0
        self.child_list = []
        self.tag_counts = {}
        
    def add_children(self, stringlist, parent_id, parent_tag=None, level=2):
        """
        params:
         - stringlist is typically going to be the return of an xpath expression on an xml instance
         - parent_id is the typically going to be the Solr ID of the parent, and this is suffixed
                     to produce a similar but unique id for the child
         - parent_tag for indicating where this was located in the main instance, e.g., references, dreams, etc.
         - level for creating children at different levels (even if in the same object)
        """
        for n in stringlist:
            self.count += 1
            try:
                self.tag_counts[parent_tag] += 1
            except: # initialize
                self.tag_counts[parent_tag] = 1
                
            self.child_list.append({"id": parent_id + f".{self.count}",
                                    "art_level": level,
                                    "parent_tag": parent_tag,
                                    "para": n
                                  })
        return self.count

#def parasxml_update(parasxml, solrcon, artInfo):
    #"""
    #Load a core with each paragraph (or equivalent terminal node if that's desirable)
      #so this core can be used as a filter in queries.  Just use it as a filter
      #in the other core, e.g., from the Docs core, filtering on this core:
      
      #{!join from=art_id to=art_id fromIndex=pepwebdocparas}paras:Kultur && paras:Persönlichkeit 
      
    #with this core loading PEPCurrent took 13.55 minutes.  Significantly slower than before.
       #And there were 348583 separate docs created in the core.
      
    #The issues so far seems to be while it works well:
       #- It's much slower of course to process each document since we have to store each paragraph/terminal
       #- If the search relies on a join to this core, the highlighting of the matches in the other core doesn't seem to work
       
    #"""
    #count = 0
    #for n in parasxml:
        #count += 1
        #try:
            #response_update = solrcon.add(id = artInfo.artID + f".{count}",
                                          #art_id = artInfo.artID,
                                          #paras = n
                                         #)

            #if not re.search('"status">0</int>', response_update):
                #print (response_update)
        #except Exception as err:
            ##processingErrorCount += 1
            #errStr = "Solr call exception for save docparas on %s: %s" % (artInfo.artID, err)
            #print (errStr)
            ##config.logger.error(errStr)
    
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
            authorID = author.attrib.get('authindexid', None)
            if authorID is None:
                authorID = opasxmllib.authors_citation_from_xmlstr(author)
                try:
                    authorID = authorID[0]
                except:
                    authorID = "GenID" + "%05d" % random.randint(1, 5000)
            authorListed = author.attrib.get('listed', "true")
            if authorListed.lower() == "true":
                authorPos += 1
            authorRole = author.attrib.get('role', None)
            authorXML = opasxmllib.xml_elem_or_str_to_xmlstring(author)
            authorDocid = artInfo.artID + "." + ''.join(e for e in authorID if e.isalnum())
            authorBio = opasxmllib.xml_xpath_return_textsingleton(author, "nbio")
            try:
                authorAffID = author.attrib['affid']
            except KeyError as e:
                authorAffil = None  # see if the add still takes!
            else:
                authorAffil = pepxml.xpath('//artinfo/artauth/autaff[@affid="%s"]' % authorAffID)
                authorAffil = etree.tostring(authorAffil[0])
               
            try:  
                response_update = solrAuthor.add(id = authorDocid,         # important =  note this is unique id for every author + artid
                                                 art_id = artInfo.artID,
                                                 title = artInfo.artTitle,
                                                 authors = artInfo.artAllAuthors,
                                                 art_author_id = authorID,
                                                 art_author_listed = authorListed,
                                                 art_author_pos_int = authorPos,
                                                 art_author_role = authorRole,
                                                 art_author_bio = authorBio,
                                                 art_author_affil_xml = authorAffil,
                                                 art_year_int = artInfo.artYearInt,
                                                 art_sourcetype = artInfo.artPepSourceType,
                                                 art_sourcetitlefull = artInfo.artPepSourceTitleFull,
                                                 art_citeas_xml = artInfo.artCiteAsXML,
                                                 art_author_xml = authorXML,
                                                 file_last_modified = artInfo.fileTimeStamp,
                                                 file_classification = artInfo.fileClassification,
                                                 file_name = artInfo.fileName,
                                                 timestamp = artInfo.processedDateTime  # When batch was entered into core
                                                )
                if not re.search('"status">0</int>', response_update):
                    print (response_update)
            except Exception as err:
                #processingErrorCount += 1
                errStr = "Error for %s: %s" % (artInfo.artID, err)
                print (errStr)
                config.logger.error(errStr)
               

    except Exception as err:
        #processingErrorCount += 1
        errStr = "Error for %s: %s" % (artInfo.artID, err)
        print (errStr)
        config.logger.error(errStr)

#------------------------------------------------------------------------------------------------------
def processBibForReferencesCore(pepxml, artInfo, solrbib):
    """
    Adds the bibliography data from a single document to the core per the pepwebrefs solr schema
    
    """
    #------------------------------------------------------------------------------------------------------
    #<!-- biblio section fields -->
    #Note: currently, this does not include footnotes or biblio include tagged data in document (binc)
    bibReferences = pepxml.xpath("/pepkbd3//be")  # this is the second time we do this (also in artinfo, but not sure or which is better per space vs time considerations)
    retVal = artInfo.artBibReferenceCount
    if options.displayVerbose:
        print(("   ...Processing %s references for the references database." % (artInfo.artBibReferenceCount)))
    #processedFilesCount += 1
    bibTotalReferenceCount = 0
    allRefs = []
    for ref in bibReferences:
        bibTotalReferenceCount += 1
        bibRefEntry = etree.tostring(ref, with_tail=False)
        bibRefID = opasxmllib.xml_get_element_attr(ref, "id")
        refID = artInfo.artID + "." + bibRefID
        bibSourceTitle = opasxmllib.xml_get_subelement_textsingleton(ref, "j")
        bibPublishers = opasxmllib.xml_get_subelement_textsingleton(ref, "bp")
        if bibPublishers != "":
            bibSourceType = "book"
        else:
            bibSourceType = "journal"
        if bibSourceType == "book":
            bibYearofPublication = opasxmllib.xml_get_subelement_textsingleton(ref, "bpd")
            if bibYearofPublication == "":
                bibYearofPublication = opasxmllib.xml_get_subelement_textsingleton(ref, "y")
            if bibSourceTitle is None or bibSourceTitle == "":
                # sometimes has markup
                bibSourceTitle = opasxmllib.xml_get_direct_subnode_textsingleton(ref, "bst")  # book title
        else:
            bibYearofPublication = opasxmllib.xml_get_subelement_textsingleton(ref, "y")
           
        if bibYearofPublication == "":
            # try to match
            try:
                bibYearofPublication = re.search(r"\(([A-z]*\s*,?\s*)?([12][0-9]{3,3}[abc]?)\)", bibRefEntry).group(2)
            except Exception as e:
                logging.warning("no match %s/%s/%s" % (bibYearofPublication, ref, e))
            
        try:
            bibYearofPublication = re.sub("[^0-9]", "", bibYearofPublication)
            bibYearofPublicationInt = int(bibYearofPublication[0:4])
        except ValueError as e:
            logging.warning("Error converting bibYearofPublication to int: %s / %s.  (%s)" % (bibYearofPublication, bibRefEntry, e))
            bibYearofPublicationInt = 0
        except Exception as e:
            logging.warning("Error trying to find untagged bib year in %s (%s)" % (bibRefEntry, e))
            bibYearofPublicationInt = 0
            

        bibAuthorNameList = [etree.tostring(x, with_tail=False).decode("utf8") for x in ref.findall("a") if x is not None]
        bibAuthorsXml = '; '.join(bibAuthorNameList)
        #Note: Changed to is not None since if x gets warning - FutureWarning: The behavior of this method will change in future versions. Use specific 'len(elem)' or 'elem is not None' test instead
        authorList = [opasxmllib.xml_elem_or_str_to_text(x) for x in ref.findall("a") if opasxmllib.xml_elem_or_str_to_text(x) is not None]  # final if x gets rid of any None entries which can rarely occur.
        authorList = '; '.join(authorList)
        bibRefRxCf = opasxmllib.xml_get_element_attr(ref, "rxcf", default_return=None)
        bibRefRx = opasxmllib.xml_get_element_attr(ref, "rx", default_return=None)
        if bibRefRx != None:
            bibRefRxSourceCode = re.search("(.*?)\.", bibRefRx, re.IGNORECASE).group(1)
        else:
            bibRefRxSourceCode = None
            
        # see if this is an offsite article
        if artInfo.fileClassification == opasConfig.DOCUMENT_ACCESS_OFFSITE: # "pepoffsite":
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
                    "art_sourcecode" : artInfo.artPepSrcCode,
                    "art_sourcetitleabbr" : artInfo.artPepSourceTitleAbbr,
                    "art_sourcetitlefull" : artInfo.artPepSourceTitleFull,
                    "art_sourcetype" : artInfo.artPepSourceType,
                    "art_authors" : artInfo.artAllAuthors,
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
                    "title" : opasxmllib.xml_get_subelement_textsingleton(ref, "t"),
                    "bib_authors_xml" : bibAuthorsXml,
                    "bib_ref_id" : bibRefID,
                    "bib_ref_rx" : bibRefRx,
                    "bib_ref_rxcf" : bibRefRxCf, # the not 
                    "bib_ref_rx_sourcecode" : bibRefRxSourceCode,
                    "bib_articletitle" : opasxmllib.xml_get_subelement_textsingleton(ref, "t"),
                    "bib_sourcetype" : bibSourceType,
                    "bib_sourcetitle" : bibSourceTitle,
                    "bib_pgrg" : opasxmllib.xml_get_subelement_textsingleton(ref, "pp"),
                    "bib_year" : bibYearofPublication,
                    "bib_year_int" : bibYearofPublicationInt,
                    "bib_volume" : opasxmllib.xml_get_subelement_textsingleton(ref, "v"),
                    "bib_publisher" : bibPublishers
                  }
        allRefs.append(thisRef)
        
    # We collected all the references.  Now lets save the whole shebang
    try:
        response_update = solrbib.add_many(allRefs)  # lets hold off on the , _commit=True)

        if not re.search('"status">0</int>', response_update):
            print (response_update)
    except Exception as err:
        #processingErrorCount += 1
        config.logger.error("Solr call exception %s", err)

    return retVal  # return the bibRefCount

#------------------------------------------------------------------------------------------------------
def add_refs_to_biblioxml_table(pepxml, artInfo, solrbib):
    """
    Adds the bibliography data from a single document to the biblioxml table in mysql
    """
    #------------------------------------------------------------------------------------------------------
    #<!-- biblio section fields -->
    #Note: currently, this does not include footnotes or biblio include tagged data in document (binc)
    bib_references = pepxml.xpath("/pepkbd3//be")  # this is the second time we do this (also in artinfo, but not sure or which is better per space vs time considerations)
    retVal = artInfo.artBibReferenceCount
    if options.displayVerbose:
        print(("   ...Processing %s references for the biblioxml table." % (artInfo.artBibReferenceCount)))
    bib_total_reference_count = 0
    all_refs = []
    for ref in bib_references:
        bib_total_reference_count += 1
        bib_entry = BiblioEntry(artInfo, ref)
        bib_entry.ref_id = artInfo.artID + "." + ref_local_id
        biblio_insert_if_not_exists = r"""INSERT IGNORE
                                          INTO api_biblioxml (
                                                              art_id,
                                                              bib_ref_id,
                                                              bib_ref_rx,
                                                              bib_ref_rx_sourcecode, 
                                                              bib_ref_rxcf, 
                                                              bib_authors_xml, 
                                                              bib_articletitle, 
                                                              bib_sourcetype, 
                                                              bib_sourcetitle, 
                                                              bib_pgrg, 
                                                              bib_year, 
                                                              bib_year_int, 
                                                              bib_volume, 
                                                              bib_publisher 
                                                              full_ref_xml,
                                                              full_ref_text,
                                                              )
                                          values ('%(art_id)s',
                                                  '%(bib_ref_id)s',
                                                  '%(bib_ref_rx)s',
                                                  '%(bib_ref_rx_sourcecode)s',
                                                  '%(bib_ref_rxcf)s',
                                                  '%(bib_authors_xml)s',
                                                  '%(bib_articletitle)s',
                                                  '%(bib_sourcetype)s',
                                                  '%(bib_sourcetitle)s',
                                                  '%(bib_pgrg)s',
                                                  '%(bib_year)s',
                                                  '%(bib_year_int)s',
                                                  '%(bib_volume)s',
                                                  '%(bib_publisher)s'
                                                  '%(timestamp)s',
                                                  '%(text_ref)s',
                                                  )
                                                  """
            
        query_param_dict = {
            "art_id" : artInfo.artID,
            "timestamp" : artInfo.processedDateTime,  # When batch was entered into core
            "text_ref" : bib_entry.ref_entry,                        
            "text_offsite_ref": bib_entry.ref_offsite_entry,
            "authors" : bib_entry.author_list,
            "title" : bib_entry.title,
            "bib_authors_xml" : bib_entry.authors_xml,
            "bib_ref_id" : bib_entry.ref_local_id,
            "bib_ref_rx" : bib_entry.ref_rx,
            "bib_ref_rxcf" : bib_entry.ref_rxcf, # the not 
            "bib_ref_rx_sourcecode" : bib_entry.ref_rx_source_code,
            "bib_articletitle" : bib_entry.title,
            "bib_sourcetype" : bib_entry.source_type,
            "bib_sourcetitle" : bib_entry.source_title,
            "bib_pgrg" : bib_entry.pgrg,
            "bib_year" : bib_entry.yearof_publication,
            "bib_year_int" : bib_entry.yearof_publication_int,
            "bib_volume" : bib_entry.volume,
            "bib_publisher" : bib_entry.publishers
        }

        queryupd = opasCentralDBLib.do_action_query()
        
        biblio_insert_if_not_exists % 	(	artInfo.artID,
                                                        ref_local_id,
                                                        bibXML, 
                                                        bib_authors_xml, 
                                                        ref_local_id, 
                                                        bib_ref_rx,
                                                        bib_ref_rxcf, 
                                                        bib_ref_rx_sourcecode, 
                                                        self.articletitle, 
                                                        bib_sourcetype, 
                                                        bib_sourcetitle, 
                                                        bib_pgrg, 
                                                        bib_year, 
                                                        bib_year_int, 
                                                        bib_volume, 
                                                        bib_publisher 
                                                              )

        qryRows = doActionQuery(queryupd, "(FullBib %s/%s)" % (articleID, bibID))
    
        bib_authors_xml 
        ref_local_id 
        bib_ref_rx 
        bib_ref_rxcf 
        bib_ref_rx_sourcecode 
        self.articletitle 
        bib_sourcetype 
        bib_sourcetitle 
        bib_pgrg 
        bib_year 
        bib_year_int 
        bib_volume 
        bib_publisher
        
    
        this_ref = {
                  }
        all_refs.append(this_ref)
        
    # We collected all the references.  Now lets save the whole shebang
    try:
        response_update = solrbib.add_many(all_refs)  # lets hold off on the , _commit=True)

        if not re.search('"status">0</int>', response_update):
            print (response_update)
    except Exception as err:
        #processingErrorCount += 1
        config.logger.error("Solr call exception %s", err)

    return retVal  # return the bibRefCount
#------------------------------------------------------------------------------------------------------
def process_glossary_core(solr_glossary_core):
    """
    Process the special PEP Glossary documents.  These are linked to terms in the document
       as popups.
       
    Unlike the other cores processing, this has a limited document set so it runs
      through them all as a single pass, in a single call to this function.
       
    Note: Moved code 2019/11/30 from separate solrXMLGlossaryLoad program.  It was separate
          because the glossary isn't updated frequently.  However, it was felt that
          it was not as easy to keep in sync as a completely separate program.
    """
    global logger
    
    countFiles = 0
    countTerms = 0
    ret_val = (countFiles, countTerms) # File count, entry count
    
    # find the Glossaary (bEXP_ARCH1) files (processed with links already) in path
    processedDateTime = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')
    pat = r"ZBK.069(.*)\(bEXP_ARCH1\)\.(xml|XML)$"
    filePatternMatch = re.compile(pat)
    filenames = []
    for root, d_names, f_names in os.walk(options.rootFolder):
        for f in f_names:
            if filePatternMatch.match(f):
                countFiles += 1
                filenames.append(os.path.join(root, f))

    print ("Ready to import glossary records from %s files at path: %s" % (countFiles, options.rootFolder))
    for n in filenames:
        f = open(n, encoding='utf8')
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
        # root = etree.fromstring(fileXMLContents)
        root = etree.fromstring(opasxmllib.remove_encoding_string(fileXMLContents))
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
        # processedFilesCount += 1

        allDictEntries = []
        for glossaryGroup in glossaryGroups:
            glossaryGroupXML = etree.tostring(glossaryGroup, with_tail=False)
            glossaryGroupID = opasxmllib.xml_get_element_attr(glossaryGroup, "id")
            glossaryGroupTerm = opasxmllib.xml_get_subelement_textsingleton(glossaryGroup, "term")
            glossaryGroupAlso = opasxmllib.xml_get_subelement_xmlsingleton(glossaryGroup, "dictalso")
            if glossaryGroupAlso == "":
                glossaryGroupAlso = None
            print ("Processing Term: %s" % glossaryGroupTerm)
            countTerms += 1
            dictEntries = glossaryGroup.xpath("dictentry")  
            groupTermCount = len(dictEntries)
            counter = 0
            for dictEntry in dictEntries:
                counter += 1
                thisDictEntry = {}
                dictEntryID = glossaryGroupID + ".{:03d}".format(counter)
                dictEntryTerm = opasxmllib.xml_get_subelement_textsingleton(dictEntry, "term")
                if dictEntryTerm == "":
                    dictEntryTerm = glossaryGroupTerm
                dictEntryTermType = dictEntry.xpath("term/@type")  
                if dictEntryTermType != []:
                    dictEntryTermType = dictEntryTermType[0]
                else:
                    dictEntryTermType = "term"
                
                dictEntrySrc = opasxmllib.xml_get_subelement_textsingleton(dictEntry, "src")
                dictEntryAlso = opasxmllib.xml_get_subelement_xmlsingleton(dictEntry, "dictalso")
                if dictEntryAlso == "":
                    dictEntryAlso = None
                dictEntryDef = opasxmllib.xml_get_subelement_xmlsingleton(dictEntry, "def")
                dictEntryDefRest = opasxmllib.xml_get_subelement_xmlsingleton(dictEntry, "defrest")
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
                    "text"                : str(glossaryGroupXML, "utf8"),
                    "file_name"           : base,
                    "timestamp"           : processedDateTime,
                    "file_last_modified"  : fileTimeStamp
                }
                allDictEntries.append(thisDictEntry)

        # We collected all the dictentries for the group.  Now lets save the whole shebang
        try:
            response_update = solr_glossary_core.add_many(allDictEntries)  # lets hold off on the , _commit=True)
    
            if not re.search('"status">0</int>', response_update):
                print (response_update)
        except Exception as err:
            logger.error("Solr call exception %s", err)
    
        f.close()

    solr_glossary_core.commit()
    ret_val = (countFiles, countTerms) # File count, entry count
    return ret_val    
#------------------------------------------------------------------------------------------------------
def main():
    
    global options  # so the information can be used in support functions
    global bibTotalReferenceCount
    programNameShort = "OPASWebLoaderPEP"  # used for log file
    # scriptSourcePath = os.path.dirname(os.path.realpath(__file__))
    logFilename = programNameShort + "_" + datetime.today().strftime('%Y-%m-%d') + ".log"

    parser = OptionParser(usage="%prog [options] - PEP Solr Reference Text Data Loader", version="%prog ver. 0.1.14")
    parser.add_option("-a", "--allfiles", action="store_true", dest="forceRebuildAllFiles", default=False,
                      help="Option to force all files to be updated on the specified cores.  This does not reset the file tracker but updates it as files are processed.")
    parser.add_option("-b", "--bibliocoreupdate", dest="reference_core_update", action="store_true", default=False,
                      help="Whether to update the biblio core")
    parser.add_option("-d", "--dataroot", dest="rootFolder", default=config.DEFAULTDATAROOT,
                      help="Root folder path where input data is located")
    parser.add_option("-f", "--fulltextcoreupdate", dest="fulltext_core_update", action="store_true", default=False,
                      help="Whether to update the full-text and authors core")
    parser.add_option("-l", "--loglevel", dest="logLevel", default=logging.INFO,
                      help="Level at which events should be logged")
    parser.add_option("--logfile", dest="logfile", default=logFilename,
                      help="Logfile name with full path where events should be logged")
    parser.add_option("--resetcore",
                      action="store_true", dest="resetCoreData", default=False,
                      help="reset the data in the selected cores. (authorscore is reset with the fulltext core)")
    parser.add_option("-g", "--glossarycoreupdate", dest="glossary_core_update", action="store_true", default=False,
                      help="Whether to update the glossary core")
    parser.add_option("-t", "--trackerdb", dest="fileTrackerDBPath", default=None,
                      help="Full path and database name where the File Tracking Database is located (sqlite3 db)")
    #parser.add_option("-u", "--url",
                      #dest="solrURL", default=config.DEFAULTSOLRHOME,
                      #help="Base URL of Solr api (without core), e.g., http://localhost:8983/solr/", metavar="URL")
    parser.add_option("-v", "--verbose", action="store_true", dest="displayVerbose", default=False,
                      help="Display status and operational timing info as load progresses.")
    parser.add_option("--pw", dest="httpPassword", default=None,
                      help="Password for the server")
    parser.add_option("--userid", dest="httpUserID", default=None,
                      help="UserID for the server")
    parser.add_option("--config", dest="config_info", default="Local",
                      help="UserID for the server")


    (options, args) = parser.parse_args()

    processedFilesCount = 0
    # Python 3 did not like the following...
    #logging.basicConfig(handlers=[ExitOnExceptionHandler()], filename=logFilename, level=options.logLevel)
    logging.basicConfig(filename=logFilename, level=options.logLevel)
    logger = config.logger = logging.getLogger(programNameShort)

    logger.info('Started at %s', datetime.today().strftime('%Y-%m-%d %H:%M:%S"'))

    solrurl_docs = None
    solrurl_refs = None
    solrurl_authors = None
    solrurl_glossary = None
    
    if (options.reference_core_update or options.fulltext_core_update or options.glossary_core_update) == True:
        try:
            solrurl_docs = localsecrets.SOLRURL + opasConfig.SOLR_DOCS  # e.g., http://localhost:8983/solr/    + pepwebdocs'
            solrurl_refs = localsecrets.SOLRURL + opasConfig.SOLR_REFS  # e.g., http://localhost:8983/solr/  + pepwebrefs'
            solrurl_authors = localsecrets.SOLRURL + opasConfig.SOLR_AUTHORS
            solrurl_glossary = localsecrets.SOLRURL + opasConfig.SOLR_GLOSSARY
            print("Logfile: ", logFilename)
            print("Input data Root: ", options.rootFolder)
            print("Reset Core Data: ", options.resetCoreData)
            if options.fulltext_core_update:
                print("Solr Full-Text Core will be updated: ", solrurl_docs)
                print("Solr Authors Core will be updated: ", solrurl_authors)
            if options.reference_core_update:
                print("Solr References Core will be updated: ", solrurl_refs)
            if options.glossary_core_update:
                print("Solr Glossary Core will be updated: ", solrurl_glossary)
        except Exception as e:
            msg = "cores specification error (e)."
            print((len(msg)*"-"))
            print (msg)
            print((len(msg)*"-"))
            sys.exit(0)
    else:
        msg = "No cores requested for update.  Use -f or -b to update the full-text and biblio cores respectively"
        print((len(msg)*"-"))
        print (msg)
        print((len(msg)*"-"))
        sys.exit(0)
        
    # instantiate the fileTracker.
    if options.fileTrackerDBPath is None:
        fileTracker = FileTracker()
    else:
        try:
            fileTracker = FileTracker(options.fileTrackerDBPath)
        except Exception as e:
            msg = f"Filetracker error ({e})."
            print((len(msg)*"-"))
            print (msg)
            print((len(msg)*"-"))
            sys.exit(0)
        
    timeStart = time.time()
    
    # import data about the PEP codes for journals and books.
    #  Codes are like APA, PAH, ... and special codes like ZBK000 for a particular book
    sourceDB = opasCentralDBLib.SourceInfoDB()

    #TODO: Try without the None test, the library should not try to use None as user name or password, so only the first case may be needed
    # The connection call is to solrpy (import was just solr)
    #if options.httpUserID is not None and options.httpPassword is not None:
    if localsecrets.SOLRUSER is not None and localsecrets.SOLRPW is not None:
        if options.fulltext_core_update:
            # fulltext update always includes authors
            #solrcore_docs = solr.SolrConnection(solrurl_docs, http_user=localsecrets.SOLRUSER, http_pass=localsecrets.SOLRPW)
            solrcore_docs2 = pysolr.Solr(solrurl_docs, auth=(localsecrets.SOLRUSER, localsecrets.SOLRPW))
            solrcore_authors = solr.SolrConnection(solrurl_authors, http_user=localsecrets.SOLRUSER, http_pass=localsecrets.SOLRPW)
        if options.reference_core_update:
            # as of 2019/11/30 this core isn't actually being used in the API.  May end up dropping this.
            solrcore_references = solr.SolrConnection(solrurl_refs, http_user=localsecrets.SOLRUSER, http_pass=localsecrets.SOLRPW)
        if options.glossary_core_update:
            solrcore_glossary = solr.SolrConnection(solrurl_glossary, http_user=localsecrets.SOLRUSER, http_pass=localsecrets.SOLRPW)
    else: #  no user and password needed
        if options.fulltext_core_update:
            # fulltext update always includes authors
            #solrcore_docs = solr.SolrConnection(solrurl_docs)
            solrcore_docs2 = pysolr.Solr(solrurl_docs)
            solrcore_authors = solr.SolrConnection(solrurl_authors)
        if options.reference_core_update:
            # as of 2019/11/30 this core isn't actually being used in the API.  May end up dropping this.
            solrcore_references = solr.SolrConnection(solrurl_refs)
        if options.glossary_core_update:
            solrcore_glossary = solr.SolrConnection(solrurl_glossary)

    # Reset core's data if requested (mainly for early development)
    if options.resetCoreData:
        if options.fulltext_core_update:
            print ("*** Deleting all data from the docs and author cores ***")
            #solrcore_docs.delete_query("*:*")
            solrcore_docs2.delete(q='*:*')
            solrcore_docs2.commit()
            #solrcore_docs.commit()
            solrcore_authors.delete_query("*:*")
            solrcore_authors.commit()
        if options.reference_core_update:
            print ("*** Deleting all data from the References core ***")
            solrcore_references.delete_query("*:*")
            solrcore_references.commit()
        if options.glossary_core_update:
            print ("*** Deleting all data from the Glossary core ***")
            solrcore_glossary.delete_query("*:*")
            solrcore_glossary.commit()
        # also reset the file tracker in both cases
        fileTracker.deleteAll()
        fileTracker.commit()
    else:
        # check for missing files and delete them from the core, since we didn't empty the core above
        pass

    # Glossary Processing only
    if options.glossary_core_update:
        # this option will process all files in the glossary core.
        glossary_file_count, glossary_terms = process_glossary_core(solrcore_glossary)
    
    # Docs, Authors and References go through a full set of regular XML files
    bibTotalReferenceCount = 0 # zero this here, it's checked at the end whether references are processed or not
    if (options.reference_core_update or options.fulltext_core_update) == True:
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
        currFileInfo = FileTrackingInfo()
        if re.match(".*\.xml$", options.rootFolder, re.IGNORECASE):
            # single file mode.
            singleFileMode = True
            if os.path.exists(options.rootFolder):
                filenames.append(options.rootFolder)
                totalFiles = 1
                newFiles = 1
            else:
                print(("Error: Single file mode name: {} does not exist.".format(options.rootfolder)))
        else:
            # get a list of all the XML files that are new
            singleFileMode = False
            for root, d_names, f_names in os.walk(options.rootFolder):
                for f in f_names:
                    if filePatternMatch.match(f):
                        totalFiles += 1
                        filename = os.path.join(root, f)
                        #currFileInfo = FileTrackingInfo()
                        currFileInfo.loadForFile(filename, localsecrets.SOLRURL)  # mod 2019-06-05 Just the base URL, not the core
                        if options.forceRebuildAllFiles:
                            # fake it, make it look modified!
                            isModified = True
                        else:
                            isModified = fileTracker.isFileModified(currFileInfo)

                        if not isModified:
                            # file seen before, need to compare.
                            #print "File is the same!  Skipping..."
                            skippedFiles += 1
                            continue
                        else:
                            newFiles += 1
                            #print "File is NOT the same!  Scanning the data..."
                            filenames.append(filename)
        
        print((80*"-"))
        if singleFileMode:
            print(("Single File Mode Selected.  Only file {} will be imported".format(options.rootFolder)))
        else:
            print(("Ready to import records from %s files of %s at path: %s." % (newFiles, totalFiles, options.rootFolder)))
            print(("%s Skipped files (those not modified since the last run)" % (skippedFiles)))
            print(("%s Files to process" % (newFiles )))
    
        print((80*"-"))
        preCommitFileCount = 0
        processedFilesCount = 0
        if newFiles > 0:
            print ("Collecting citation counts from cross-tab in biblio database...this will take a minute or two...")
            try:
                ocd =  opasCentralDBLib.opasCentralDB()
                ocd.open_connection()
                # Get citation lookup table
                try:
                    cursor = ocd.db.cursor(pymysql.cursors.DictCursor)
                    sql = """
                          SELECT cited_document_id, count5, count10, count20, countAll from vw_stat_cited_crosstab; 
                          """
                    success = cursor.execute(sql)
                    if success:
                        for n in cursor.fetchall():
                            row = modelsOpasCentralPydantic.MostCitedArticles(**n)
                            gCitedTable[row.cited_document_id] = row
                        cursor.close()
                    else:
                        retVal = 0
                except MemoryError as e:
                    print(("Memory error loading table: {}".format(e)))
                except Exception as e:
                    print(("Table Query Error: {}".format(e)))
                
                ocd.close_connection()
            except Exception as e:
                print(("Database Connect Error: {}".format(e)))
                gCitedTable["dummy"] = modelsOpasCentralPydantic.MostCitedArticles()
                
        
            for n in filenames:
                fileTimeStart = time.time()
                processedFilesCount += 1
                if pyVer == 3:
                    f = open(n, encoding="utf-8")
                else:
                    f = open(n)
                fileXMLContents = f.read()
                
                # get file basename without build (which is in paren)
                base = os.path.basename(n)
                artID = os.path.splitext(base)[0]
                m = re.match(r"(.*)\(.*\)", artID)
        
                # Update this file in the database as "processed"
                currFileInfo.loadForFile(n, localsecrets.SOLRURL)
                fileTracker.setFileDatabaseRecord(currFileInfo)
                fileTimeStamp = datetime.utcfromtimestamp(currFileInfo.fileModDate).strftime('%Y-%m-%dT%H:%M:%SZ')
                print(("Processing file #%s of %s: %s (%s bytes)." % (processedFilesCount, newFiles, base, currFileInfo.fileSize)))
        
                # Note: We could also get the artID from the XML, but since it's also important
                # the file names are correct, we'll do it here.  Also, it "could" have been left out
                # of the artinfo (attribute), whereas the filename is always there.
                artID = m.group(1)
                # all IDs to upper case.
                artID = artID.upper()
        
                # import into lxml
                root = etree.fromstring(opasxmllib.remove_encoding_string(fileXMLContents))
                pepxml = root
        
                # save common document (article) field values into artInfo instance for both databases
                artInfo = ArticleInfo(sourceDB.sourceData, pepxml, artID, logger)
                artInfo.fileTimeStamp = fileTimeStamp
                artInfo.fileName = base
                artInfo.fileSize = currFileInfo.fileSize
                try:
                    artInfo.fileClassification = re.search("(current|archive|future|free|offsite)", n, re.IGNORECASE).group(1)
                    # set it to lowercase for ease of matching later
                    artInfo.fileClassification = artInfo.fileClassification.lower()
                except Exception as e:
                    logging.warn("Could not determine file classification for %s (%s)" % (n, e))
                
        
                # walk through bib section and add to refs core database
        
                if preCommitFileCount > config.COMMITLIMIT:
                    print(("Committing info for %s documents/articles" % config.COMMITLIMIT))
                    
                # input to the full-text code
                if options.fulltext_core_update:
                    # this option will also load the biblio and authors cores.
                    processArticleForDocCore(pepxml, artInfo, solrcore_docs2, fileXMLContents)
                    processInfoForAuthorCore(pepxml, artInfo, solrcore_authors)
                    if preCommitFileCount > config.COMMITLIMIT:
                        preCommitFileCount = 0
                        solrcore_docs2.commit()
                        solrcore_authors.commit()
                        fileTracker.commit()
        
                # input to the references core
                if options.reference_core_update:
                    bibTotalReferenceCount += processBibForReferencesCore(pepxml, artInfo, solrcore_references)
                    if preCommitFileCount > config.COMMITLIMIT:
                        preCommitFileCount = 0
                        solrcore_references.commit()
                        fileTracker.commit()
        
                preCommitFileCount += 1
                # close the file, and do the next
                f.close()
                if options.displayVerbose:
                    print(("   ...Time: %s seconds." % (time.time() - fileTimeStart)))
        
            # all done with the files.  Do a final commit.
            print ("Performing final commit.")
            try:
                if options.reference_core_update:
                    solrcore_references.commit()
                    fileTracker.commit()
            except Exception as e:
                print(("Exception: ", e))
            
            try:
                if options.fulltext_core_update:
                    solrcore_docs2.commit()
                    solrcore_authors.commit()
                    fileTracker.commit()
            except Exception as e:
                print(("Exception: ", e))

    # end of docs, authors, and/or references Adds

    # ---------------------------------------------------------
    # Closing time
    # ---------------------------------------------------------
    timeEnd = time.time()

    elapsed_seconds = timeEnd-timeStart
    elapsed_minutes = elapsed_seconds / 60

    if (options.reference_core_update or options.fulltext_core_update) == True:
        if bibTotalReferenceCount > 0:
            msg = f"Finished! Imported {len(filenames)} documents and {bibTotalReferenceCount} references. Elapsed time: {elapsed_seconds:.2f} secs ({elapsed_minutes:.2f} minutes. Files per Min: {len(filenames)/elapsed_minutes:.4f})" 
        else:
            msg = f"Finished! Imported {len(filenames)} documents. Elapsed time: {elapsed_seconds:.2f} secs ({elapsed_minutes:.2f} minutes. Files per Min: {len(filenames)/elapsed_minutes:.4f})" 

    if options.glossary_core_update:
        msg = f"Finished! Imported {glossary_file_count} glossary documents and {glossary_terms} terms. Elapsed time: {elapsed_seconds} secs ({elapsed_minutes} minutes, Files per Min: {glossary_file_count/elapsed_minutes:.4f})"

    print (msg)
    config.logger.info(msg)
    #if processingWarningCount + processingErrorCount > 0:
        #print ("  Issues found.  Warnings: %s, Errors: %s.  See log file %s" % (processingWarningCount, processingErrorCount, logFilename))

# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    main()
