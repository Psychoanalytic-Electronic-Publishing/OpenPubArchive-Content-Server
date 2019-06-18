#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326

"""
opasAPISupportLib

This library is meant to hold the heart of the API based Solr queries and other support 
functions.  

2019.0614.1 - Python 3.7 compatible

"""
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2019.0614.1"
__status__      = "Development"

import sys
sys.path.append('../libs')

import re
import os.path

import time
import datetime
from datetime import datetime
from typing import List
from enum import Enum

pyVer = 2
if (sys.version_info > (3, 0)):
    # Python 3 code in this block
    from io import StringIO
    pyVer = 3
else:
    # Python 2 code in this block
    import StringIO
    
#import pysolr
import solr
import lxml
import logging

from lxml import etree
from pydantic import BaseModel

from ebooklib import epub

import imp

from stdMessageLib import copyrightPageHTML  # copyright page text to be inserted in ePubs and PDFs

from models import ListTypeEnum, \
                   ResponseInfo, \
                   DocumentList, \
                   DocumentListStruct, \
                   DocumentListItem, \
                   ImageURLList, \
                   ImageURLListStruct, \
                   ImageURLListItem, \
                   SourceInfoList, \
                   SourceInfoStruct, \
                   SourceInfoListItem, \
                   VolumeList, \
                   VolumeListStruct, \
                   VolumeListItem, \
                   WhatsNewList, \
                   WhatsNewListStruct, \
                   WhatsNewListItem, \
                   AuthorPubListStruct, \
                   AuthorPubListItem, \
                   AuthorPubList, \
                   AuthorIndex, \
                   AuthorIndexStruct, \
                   AuthorIndexItem

try:
    import opasXMLHelper as opasxmllib
    import opasGenSupportlib as opasgenlib
    import sourceInfoDB as SourceInfoDB
except Exception as e:
    opasxmllib = imp.load_source('opasxmllib', '../libs/opasXMLHelper.py')
    opasgenlib = imp.load_source('opasgenlib', '../libs/opasGenSupportLib.py')
    SourceInfoDB = imp.load_source('sourceInfoDB', '../libs/sourceInfoDB.py')
    
sourceDB = SourceInfoDB.SourceInfoDB()
logging.basicConfig(filename='pepsolrtest.log', format="%(asctime)s %(message)s", level=logging.INFO)

#from solrq import Q
import json

# Setup a Solr instance. The timeout is optional.
#solr = pysolr.Solr('http://localhost:8983/solr/pepwebproto', timeout=10)
solrDocs = solr.SolrConnection('http://localhost:8983/solr/pepwebproto')
solrRefs = solr.SolrConnection('http://localhost:8983/solr/pepwebrefsproto')
solrGloss = solr.SolrConnection('http://localhost:8983/solr/pepwebglossary')
solrAuthors = solr.SolrConnection('http://localhost:8983/solr/pepwebauthors')

#API endpoints
documentURL = "/api/v1/Documents/"



def removeEncodingString(xmlString):
    # Get rid of the encoding for lxml
    p=re.compile("\<\?xml version=\'1.0\' encoding=\'UTF-8\'\?\>\n")
    retVal = xmlString
    retVal = p.sub("", retVal)                
    
    return retVal

def getArticleData(articleID):
    retVal = None
    if articleID != "":
        results = solrDocs.query(q = "art_id:%s" % articleID)
        if results._numFound == 0:
            retVal = None
        else:
            retVal = results.results[0]
        
    return retVal

def databaseGetMostCited(limit=50, offset=0):
    results = solrRefs.query(q = "art_year_int:[2014 TO 2019]",  
                             facet_field = "bib_ref_rx",
                             facet_sort = "count",
                             fl = "art_id, id, bib_ref_id, art_pepsrccode, bib_ref_rx_sourcecode",
                             rows = "0",
                             facet = "on"
                             )
    
    print ("Number found: %s" % results._numFound)
    
    responseInfo = ResponseInfo(
                     fullCount = results._numFound,
                     limit = limit,
                     offset = offset,
                     listType="mostcited",
                     fullCountComplete = limit >= results._numFound,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )

    
    documentListItems = []
    rowCount = 0
    rowOffset = 0
    for artID, count in results.facet_counts["facet_fields"]["bib_ref_rx"].items():
        rowOffset += 1
        if rowOffset < offset:  # for paging
            continue
        artInfo = getArticleData(artID)
        if artInfo is None:
            continue
        PEPCode = artInfo.get("art_pepsrccode", None)
        if PEPCode is None or PEPCode in ["SE", "GW", "ZBK", "IPL"]:  # no books
            continue
        pgRg =  artInfo.get("art_pgrg", None)
        if pgRg is not None:
            pgStart, pgEnd = opasgenlib.pgRgSplitter(pgRg)
        else:
            pgStart, pgEnd = None
        citeAs = artInfo.get("art_citeas_xml", None)

        item = DocumentListItem( documentID = artID,
                                 instanceCount = count,
                                 title = opasgenlib.getFirstValueOfDictItemList(artInfo, "title"),
                                 PEPCode = artInfo.get("art_pepsrccode", None), 
                                 authorMast = artInfo.get("art_authors_mast", None),
                                 year = artInfo.get("art_year", None),
                                 vol = artInfo.get("art_vol", None),
                                 pgStart = pgStart,
                                 pgEnd = pgEnd,
                                 documentRef = artInfo.get("art_citeas_xml", None),
                                 abstract = opasgenlib.getFirstValueOfDictItemList(artInfo, "abstracts_xml"),
                              ) 
        rowCount += 1
        print (item)
        documentListItems.append(item)
        if rowCount > limit:
            break

    # Not sure why it doesn't come back sorted...so we sort it here.
    #retVal2 = sorted(retVal, key=lambda x: x[1], reverse=True)
    
    responseInfo.count = len(documentListItems)
    
    documentListStruct = DocumentListStruct( responseInfo = responseInfo, 
                                             responseSet = documentListItems
                                             )
    
    documentList = DocumentList(documentList = documentListStruct)
    
    retVal = documentList
    
    return retVal   

def searchLikeThePEPAPI():
    pass  # later

def metadataGetVolumes(pepCode, year="*", limit=100, offset=0):
    """
    """
    retVal = []
    #print ("limit = %s, offset = %s" % (limit, offset))
           
    results = solrDocs.query(q = "art_pepsrccode:%s && art_year:%s" % (pepCode, year),  
                             fields = "art_vol, art_year",
                             sort="art_year", sort_order="asc",
                             fq="{!collapse field=art_vol}",
                             rows=limit, start=offset
                             )

    print ("Number found: %s" % results._numFound)
    responseInfo = ResponseInfo(
                     fullCount = results._numFound,
                     limit = limit,
                     offset = offset,
                     listType="volumelist",
                     fullCountComplete = limit >= results._numFound,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )

    volumeItemList = []
    for result in results.results:
        item = VolumeListItem(PEPCode = pepCode, 
                              year = result.get("art_year", None),
                              vol = result.get("art_vol", None),
                              score = result.get("score", None)
                             )
    
        print (item)
        volumeItemList.append(item)
       
    responseInfo.count = len(volumeItemList)
    
    volumeListStruct = VolumeListStruct( responseInfo = responseInfo, 
                                         responseSet = volumeItemList
                                         )
    
    volumeList = VolumeList(volumeList = volumeListStruct)
    
    retVal = volumeList
    return retVal

def metadataGetContents(pepCode, year="*", limit=100, offset=0):
    """
    Return a jounals contents
    
    >>> metadataGetContents("IJP", "1993")
    
    """
    retVal = []
    results = solrDocs.query(q = "art_pepsrccode:%s && art_year:%s" % (pepCode, year),  
                             fields = "art_id, art_vol, art_year, art_iss, art_iss_title, art_newsecnm, art_pgrg, art_title, art_author_id, art_citeas_xml",
                             sort="art_year, art_pgrg", sort_order="asc",
                             rows=limit, start=offset
                             )

    responseInfo = ResponseInfo(
                     fullCount = results._numFound,
                     limit = limit,
                     offset = offset,
                     listType="documentlist",
                     fullCountComplete = limit >= results._numFound,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )

    documentItemList = []
    for result in results.results:
        # transform authorID list to authorMast
        authorIDs = result.get("art_author_id", None)
        if authorIDs is None:
            authorMast = None
        else:
            authorMast = opasgenlib.deriveAuthorMast(authorIDs)
        
        pgRg = result.get("art_pgrg", None)
        pgStart, pgEnd = opasgenlib.pgRgSplitter(pgRg)
            
        item = DocumentListItem(PEPCode = pepCode, 
                                year = result.get("art_year", None),
                                vol = result.get("art_vol", None),
                                pgRg = result.get("art_pgrg", None),
                                pgStart = pgStart,
                                pgEnd = pgEnd,
                                authorMast = authorMast,
                                documentID = result.get("art_id", None),
                                documentRef = result.get("art_citeas_xml", None),
                                score = result.get("score", None)
                                )
        print (item)
        documentItemList.append(item)

    responseInfo.count = len(documentItemList)
    
    documentListStruct = DocumentListStruct( responseInfo = responseInfo, 
                                             responseSet=documentItemList
                                             )
    
    documentList = DocumentList(documentList = documentListStruct)
    
    retVal = documentList
    
    return retVal

def metadataGetSourceByType(sourceType=None):
    """
    Rather than get this from Solr, where there's no 1:1 records about this, we will get this from the sourceInfoDB instance.
    
    No attempt here to map to the correct structure, just checking what field/data items we have in sourceInfoDB.
    
    Current API Example Return:
    {
        "sourceInfo": {
          "responseInfo": {
            "count": 1,
            "fullCount": 1,
            "fullCountComplete": true,
            "listLabel": "Journal List",
            "listType": "srclist",
            "scopeQuery": "AJP",
            "request": "/api/v1/Metadata/Journals/AJP/",
            "timeStamp": "2019-06-07T19:30:27-04:00"
          },
          "responseSet": [
            {
              "ISSN": "0002-9548",
              "PEPCode": "AJP",
              "abbrev": "Am. J. Psychoanal.",
              "bannerURL": "http://stage.pep.gvpi.net/images/BannerAJPLogo.gif",
              "displayTitle": "American Journal of Psychoanalysis",
              "language": "en",
              "yearFirst": "1941",
              "yearLast": "2018"
            }
          ]
        }
    }
    
    >>> metadataGetSourceByType("journal")
    3
    >>> metadataGetSourceByType()
    
    """
    retVal = []
    for sourceInfoDict in sourceDB.sourceData.values():
        if sourceInfoDict["pep_class"] == sourceType:
            # match
            retVal += sourceInfoDict

    
    return retVal


def metadataGetSourceByCode(pepCode=None):
    """
    Rather than get this from Solr, where there's no 1:1 records about this, we will get this from the sourceInfoDB instance.
    
    No attempt here to map to the correct structure, just checking what field/data items we have in sourceInfoDB.
    
    The sourceType is listed as part of the endpoint path, but I wonder if we should really do this 
    since it isn't needed, the pepCodes are unique.
    
    Current API Example Return:
    {
        "sourceInfo": {
          "responseInfo": {
            "count": 1,
            "fullCount": 1,
            "fullCountComplete": true,
            "listLabel": "Journal List",
            "listType": "srclist",
            "scopeQuery": "AJP",
            "request": "/api/v1/Metadata/Journals/AJP/",
            "timeStamp": "2019-06-07T19:30:27-04:00"
          },
          "responseSet": [
            {
              "ISSN": "0002-9548",
              "PEPCode": "AJP",
              "abbrev": "Am. J. Psychoanal.",
              "bannerURL": "http://stage.pep.gvpi.net/images/BannerAJPLogo.gif",
              "displayTitle": "American Journal of Psychoanalysis",
              "language": "en",
              "yearFirst": "1941",
              "yearLast": "2018"
            }
          ]
        }
    }
    
    curl -X GET "http://stage.pep.gvpi.net/api/v1/Metadata/Journals/AJP/" -H "accept: application/json"
    
    >>> metadataGetSourceByCode("APA")["wall"]
    3
    >>> metadataGetSourceByCode()
    
    """
    retVal = []
    # would need to add URL for the banner
    if pepCode is not None:
        retVal = sourceDB.sourceData[pepCode]
    else:
        retVal = sourceDB.sourceData
    
    return retVal

def authorsGetAuthorInfo(authorNamePartial, limit=10, offset=0):
    """
    Returns a list of matching names (per authors last name), and the number of articles
    in PEP found by that author.
    
    >>> getAuthorInfo("Tuck")
    
    >>> getAuthorInfo("Fonag")
    
    >>> getAuthorInfo("Levinson, Nadine A.")
    
    
    Current API Example Return:
        {
            "authorindex": {
              "responseInfo": {
                "count": 0,
                "fullCount": 0,
                "fullCountComplete": true,
                "listLabel": "string",
                "listType": "string",
                "scopeQuery": "string",
                "request": "string",
                "timeStamp": "string"
              },
              "responseSet": [
                {
                  "authorID": "string",
                  "publicationsURL": "string"
                }
              ]
            }
         }

    
    """
    retVal = {}
    results = solrAuthors.query(q = "art_author_id:/%s.*/" % (authorNamePartial),  
                                fields = "authors, art_author_id",
                                facet_field = "art_author_id",
                                facet = "on",
                                #facet_query = "art_author_id:%s*" % authorNamePartial,
                                facet_prefix = "%s" % authorNamePartial,
                                rows=100
                             )

    print ("Number found: %s" % results._numFound)
    
    responseInfo = ResponseInfo(
                     fullCount = results._numFound,
                     limit = limit,
                     offset = offset,
                     listType="authorindex",
                     fullCountComplete = limit >= results._numFound,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )

    authorIndexItems = []
    for key, value in results.facet_counts["facet_fields"]["art_author_id"].items():
        if value > 0:
            #retVal[key] = value

            item = AuthorIndexItem( authorID = key, 
                                    publicationsURL = "",
                                    publicationsCount = value,
                                  ) 
            authorIndexItems.append(item)
            #debug status
            print (item)
       
    responseInfo.count = len(authorIndexItems)
    
    authorIndexStruct = AuthorIndexStruct( responseInfo = responseInfo, 
                                           responseSet = authorIndexItems
                                           )
    
    authorIndex = AuthorIndex(authorIndex = authorIndexStruct)
    
    retVal = authorIndex
    return retVal

def authorsGetAuthorPublications(authorNamePartial, limit=10, offset=0):
    """
    Returns a list of publications (published on PEP-Web (per authors partial name), and the number of articles
    in PEP found by that author.
    
    >>> getAuthorPublications("Tuck")
    >>> getAuthorPublications("Fonag")
    >>> getAuthorPublications("Levinson, Nadine A.")
    
    Current API Example Return:
        {
          "authorPubList": {
            "responseInfo": {
              "count": 0,
              "fullCount": 0,
              "fullCountComplete": true,
              "offset": 0,
              "limit": null,
              "request": "/api/v1/Authors/Publications/tuckett/",
              "timeStamp": "2019-06-08T23:31:56-04:00"
            },
            "responseSet": []
          }
        }

        The endpoint doesn't seem to work on stage or prod...but here's what should be in responseSet per the API doc.
        respSetAuthPubListItem:
          type: object
          properties:
            authorID:
              type: string
            documentID:
              type: string
            documentRef:
              type: string
            documentURL:
              type: string
    
    """
    retVal = {}
    results = solrAuthors.query(q = "art_author_id:/%s.*/" % (authorNamePartial),  
                                fields = "art_author_id, art_year_int, art_id, art_citeas_xml",
                                sort="art_author_id, art_year_int", sort_order="asc",
                                rows=limit, start=offset
                             )

    print ("Number found: %s" % results._numFound)
    
    responseInfo = ResponseInfo(
                     fullCount = results._numFound,
                     limit = limit,
                     offset = offset,
                     listType="authorpublist",
                     fullCountComplete = limit >= results._numFound,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )

    authorPubListItems = []
    for result in results.results:
        item = AuthorPubListItem( authorID = result.get("art_author_id", None), 
                                  documentID = result.get("art_id", None),
                                  documentRef = result.get("art_citeas_xml", None),
                                  documentURL = documentURL + result.get("art_id", None),
                                  year = result.get("art_year", None),
                                  score = result.get("score", None)
                              ) 
        authorPubListItems.append(item)
        #debug status
        print (item)
       
    responseInfo.count = len(authorPubListItems)
    
    authorPubListStruct = AuthorPubListStruct( responseInfo = responseInfo, 
                                           responseSet = authorPubListItems
                                           )
    
    authorPubList = AuthorPubList(authorPubList = authorPubListStruct)
    
    retVal = authorPubList
    return retVal

def getDocumentAbstracts(documentID):
    """
    Returns an abstract or summary for the specified document
    If part of a documentID is supplied, multiple abstracts will be returned.
    
    The endpoint reminds me that we should be using documentID instead of "art" for article perhaps.
      Not thrilled about the prospect of changing it, but probably the right thing to do.
      
    >>> getDocumentAbstracts("IJP.075")
    >>> getDocumentAbstracts("AIM.038.0279A")  # no abstract on this one
    >>> getDocumentAbstracts("AIM.040.0311A")
    
    Current API Return Schema:
         [
          {
            "responseInfo": {
              "count": 0,
              "fullCount": 0,
              "fullCountComplete": true,
              "listLabel": "string",
              "listType": "string",
              "scopeQuery": "string",
              "request": "string",
              "timeStamp": "string"
            },
            "responseSet": [
              {
                "ISSN": "string",
                "PEPCode": "string",
                "abbrev": "string",
                "bannerURL": "string",
                "language": "string",
                "yearFirst": "string",
                "yearLast": "string"
              }
            ]
          }
        ]
    
    """
    retVal = {}
    results = solrDocs.query(q = "art_id:%s*" % (documentID),  
                                fields = "art_id, art_citeas_xml, abstracts_xml, summaries_xml, text_xml"
                             )
    
    print (len(results.results))

    try:
        retVal = results.results[0]["abstracts_xml"]
    except KeyError as e:
        try:
            retVal = results.results[0]["summaries_xml"]
        except KeyError as e:
            try:
                # Get rid of the encoding for lxml
                if results.results == []:
                    logging.warning("No content matched document ID for: %s" % documentID)
                else:
                    try:
                        retVal = results.results[0]["text_xml"]
                    except KeyError as e:
                        logging.warning("No content matched document ID for: %s" % documentID)
                    else:
                        retVal  = retVal [0]
                        # extract the first 10 paras
                        retVal = removeEncodingString(retVal)
                        root = etree.fromstring(retVal)
                        body = root.xpath("//*[self::h1 or self::p or self::p2 or self::pb]")
                        retVal = ""
                        for elem in body:
                            if elem.tag == "pb":
                                # we're done.
                                retVal = "%s%s%s" % ("<firstpage>", retVal, "</firstpage>")
                                break
                            else:
                                retVal  += etree.tostring(elem, encoding='utf8').decode('utf8')
                
            except KeyError as e:
                print ("No content or abstract found.  Error: %s" % e)
                
    return retVal


def getDocument(documentID, retFormat="XML", authenticated=True):
    """
   For non-authenticated users, this endpoint returns only Document summary information (summary/abstract)
   For authenticated users, it returns with the document itself
   
    >>> getDocument("AIM.038.0279A", retFormat="html") 
    >>> getDocument("AIM.038.0279A") 
    >>> getDocument("AIM.040.0311A")
    
   Example response, nonauthenticated user:
        {
           "error": "access_denied",
           "error_description": "OAuth2 bearer required to access resource."
        }
      
   
    Current API Return Schema:
        {
          "documents": {
            "responseInfo": {
              "count": 0,
              "fullCount": 0,
              "fullCountComplete": true,
              "listLabel": "string",
              "listType": "string",
              "scopeQuery": "string",
              "request": "string",
              "timeStamp": "string"
            },
            "responseSet": [
              {
                "documentID": "string",
                "documentRef": "string",
                "document": "string",
                "accessLimited": true
              }
            ]
          }
        }

    """
    retVal = {}
    
    if not authenticated:
        #if user is not authenticated, effectively do endpoint for getDocumentAbstracts
        retVal = getDocumentAbstracts(documentID)
    else:
        results = solrDocs.query(q = "art_id:%s" % (documentID),  
                                    fields = "art_id, art_citeas_xml, text_xml"
                                 )
        try:
            retVal = results.results[0]["text_xml"]
        except KeyError as e:
            logging.warning("No content or abstract found.  Error: %s" % e)
        else:
            try:    
                retVal = retVal[0]
            except Exception as e:
                logging.warning("Empty return: %s" % e)
        
            try:    
                if retFormat.lower() == "html":
                    retVal = removeEncodingString(retVal)
                    retVal = convertXMLStringToHTML(retVal)
                    
            except Exception as e:
                logging.warning("Can't convert data: %s" % e)
        
    return retVal

def prepDocumentDownload(documentID, retFormat="HTML", authenticated=True, baseFilename="opasDoc"):
    """
   For non-authenticated users, this endpoint returns only Document summary information (summary/abstract)
   For authenticated users, it returns with the document itself
   
    >>> prepDocumentDownload("IJP.051.0175A", retFormat="html") 
    
    >> prepDocumentDownload("IJP.051.0175A", retFormat="epub") 
    

    """
    def addEPUBElements(str):
        # for now, just return
        return str
        
    retVal = {}
    
    if not authenticated:
        #if user is not authenticated, effectively do endpoint for getDocumentAbstracts
        getDocumentAbstracts(documentID)
    else:
        results = solrDocs.query(q = "art_id:%s" % (documentID),  
                                    fields = "art_id, art_citeas_xml, text_xml"
                                 )
        try:
            retVal = results.results[0]["text_xml"]
        except IndexError as e:
            logging.warning("No matching document for %s.  Error: %s" % (documentID, e))
        except KeyError as e:
            logging.warning("No content or abstract found for %s.  Error: %s" % (documentID, e))
        else:
            try:    
                retVal = retVal[0]
            except Exception as e:
                logging.warning("Empty return: %s" % e)
            else:
                try:    
                    if retFormat.lower() == "html":
                        retVal = removeEncodingString(retVal)
                        filename = convertXMLToHTMLFile(retVal, outputFilename=documentID + ".html")  # returns filename
                        retVal = filename
                    elif retFormat.lower() == "epub":
                        retVal = removeEncodingString(retVal)
                        htmlString = convertXMLStringToHTML(retVal)
                        htmlString = addEPUBElements(htmlString)
                        filename = convertHTMLToEPUB(htmlString, documentID, documentID)
                        retVal = filename
                        
                except Exception as e:
                    logging.warning("Can't convert data: %s" % e)
        
    return retVal

def convertXMLToHTMLFile(xmlTextStr, xsltFile=r"../styles/pepkbd3-html.xslt", outputFilename=None):
    if outputFilename is None:
        basename = "opasDoc"
        suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        filenameBase = "_".join([basename, suffix]) # e.g. 'mylogfile_120508_171442'        
        outputFilename = filenameBase + ".html"

    htmlString = convertXMLStringToHTML(xmlTextStr, xsltFile=xsltFile)
    fo = open(outputFilename, "w")
    fo.write(str(htmlString))
    fo.close()
    
    return outputFilename

def convertHTMLToEPUB(htmlString, outputFilenameBase, artID, lang="en", htmlTitle=None, styleSheet="../styles/pep-html-preview.css"):
    """
    uses ebooklib
    
    """
    if htmlTitle is None:
        htmlTitle = artID
        
    root = etree.HTML(htmlString)
    try:
        title = root.xpath("//title/text()")
        title = title[0]
    except:
        title = artID
        
    headings = root.xpath("//*[self::h1|h2|h3]")

        
    basename = os.path.basename(outputFilenameBase)
    
    book = epub.EpubBook()
    book.set_identifier('basename')
    book.set_title(htmlTitle)
    book.set_language('en')
    
    book.add_author('PEP')    
    book.add_metadata('DC', 'description', 'This is description for my book')

    # main chapter
    c1 = epub.EpubHtml(title=title,
                       file_name= artID + '.xhtml',
                       lang=lang)

    c1.set_content(htmlString)
    
    # copyright page / chapter
    c2 = epub.EpubHtml(title='Copyright',
                       file_name='copyright.xhtml')
    c2.set_content(copyrightPageHTML)   
    
    book.add_item(c1)
    book.add_item(c2)    
    
    style = 'body { font-family: Times, Times New Roman, serif; }'
    try:
        styleFile = open(styleSheet, "r")
        style = styleFile.read()
        styleFile.close()
        
    except OSError as e:
        logging.warning("Cannot open stylesheet %s" % e)
    
    
    nav_css = epub.EpubItem(uid="style_nav",
                            file_name="style/pepkbd3-html.css",
                            media_type="text/css",
                            content=style)
    book.add_item(nav_css)    
    
    book.toc = (epub.Link(title, 'Introduction', 'intro'),
                (
                    epub.Section(title),
                    (c1, c2)
                )
                )    

    book.spine = ['nav', c1, c2]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())    
    filename = basename + '.epub'
    epub.write_epub(filename, book)
    return filename


def convertXMLStringToHTML(xmlTextStr, xsltFile=r"../styles/pepkbd3-html.xslt"):
    xsltFile = etree.parse(xsltFile)
    xsltTransformer = etree.XSLT(xsltFile)
    sourceFile = etree.parse(StringIO.StringIO(xmlTextStr))
    transformedData = xsltTransformer(sourceFile)
    
    return str(transformedData)

def getImageBinary(imageID):
    """
    Return a binary object of the image, e.g.,
   
    >>> getImageBinary("NOTEXISTS.032.0329A.F0003g")

    >>> getImageBinary("AIM.036.0275A.FIG001")

    >>> getImageBinary("JCPTX.032.0329A.F0003g")
    
    Note: the current server requires the extension, but it should not.  The server should check
    for the file per the following extension hierarchy: .jpg then .gif then .tif
    
    However, if the extension is supplied, that should be accepted.

    The current API implements this:
    
    curl -X GET "http://stage.pep.gvpi.net/api/v1/Documents/Downloads/Images/aim.036.0275a.fig001.jpg" -H "accept: image/jpeg" -H "Authorization: Basic cC5lLnAuYS5OZWlsUlNoYXBpcm86amFDayFsZWdhcmQhNQ=="
    
    and returns a binary object.  
        
    """
    def getImageFilename(imageID):
        imageSourcePath = "X:\_PEPA1\g"
        ext = os.path.splitext(imageSourcePath)[-1].lower()
        if ext in (".jpg", ".tif", ".gif"):
            imageFilename = os.path.join(imageSourcePath, imageID)
            exists = os.path.isfile(imageFilename)
            if not exists:
                imageFilename = None
        else:
            imageFilename = os.path.join(imageSourcePath, imageID + ".jpg")
            exists = os.path.isfile(imageFilename)
            if not exists:
                imageFilename = os.path.join(imageSourcePath, imageID + ".gif")
                exists = os.path.isfile(imageFilename)
                if not exists:
                    imageFilename = os.path.join(imageSourcePath, imageID + ".tif")
                    exists = os.path.isfile(imageFilename)
                    if not exists:
                        imageFilename = None

        return imageFilename
    
    # these won't be in the Solr database, needs to be brought back by a file
    # the file ID should match a file name
    retVal = None
    imageFilename = getImageFilename(imageID)
    if imageFilename is not None:
        try:
            f = open(imageFilename, "rb")
            imageBytes = f.read()
            f.close()    
        except OSError as e:
            print ("File Open Error: %s", e)
        except Exception as e:
            print ("Error: %s", e)
        else:
            retVal = imageBytes
    else:
        logging.warning("Image File ID %s not found", imageID)
  
    return retVal
    
def searchText(query, summaryFields='art_id, art_citeas_xml', highlightFields='art_title_xml', returnStartAt=0, returnLimit=10):
    results = solrDocs.query(query,  
                             hl= 'true', 
                             hl_fragsize = 125, 
                             hl_fl = highlightFields,
                             rows = returnLimit,
                             hl_simple_pre = '<em>',
                             hl_simplepost = '</em>')
    print ("\n\n")
    print (80*"*")
    print ("Search Performed: %s" % query)
    print ("Result  Set Size: %s" % results._numFound)
    print ("Return set limit: %s" % returnLimit)
    print ("\n")
    
    #print ("Start return  at: %s" % returnStartAt)
    #print ("Highlight Fields: %s" % highlightFields)

    # Just loop over it to access the results.
    retVal = {}
    for result in results:
        #retVal.append(("\tauthors: ", result["art_authors_xml"][0], "\n\ttitle: ", result["art_title_xml"], "{0}: '{1}'.".format(summaryField, result[summaryField])))
        #print ("\tauthors: ", result["art_authors_xml"][0], "\n\ttitle: ", result["art_title_xml"], "{0}: '{1}'.".format(summaryField, result[summaryField]))
        retVal[result["art_id"]] = {}
        retVal[result["art_id"]]["art_citeas"]  = opasxmllib.xmlElemOrStrToText(result["art_citeas_xml"])
        retVal[result["art_id"]]["art_citeasxml"]  = result["art_citeas_xml"]
        try:
            retVal[result["art_id"]]["abstracts_xml"]  = result["abstracts_xml"][0]
        except KeyError as e:
            retVal[result["art_id"]]["abstracts_xml"] = ""
        except IndexError as e:
            retVal[result["art_id"]]["abstracts_xml"] = ""
                                                                       
        #for key, val in result.items():
            #print key, val

    for key, val in results.highlighting.items():
        #print (key)
        retVal[key]["highlights"] = {}
        for key2, val2 in val.items():
            retVal[key]["highlights"][key2] = val2

    for key in retVal.keys():
        print (80*"-")
        print (key, retVal[key]["art_citeas"])
        for key2, val2 in retVal[key]["highlights"].items():
            print (key2, val2)
        if retVal[key]["abstracts_xml"] != "":
            print ("Abstract")
            print ("   ", retVal[key]["abstracts_xml"])
        print (80*"-", "\n")
        
    return retVal



#================================================================================================================================
def main():

    print (40*"*", "opasAPISupportLib Tests", 40*"*")
    print ("Fini")

# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    print ("Running in Python %s" % sys.version_info[0])
    
    # Spot testing during Development
    #metadataGetContents("IJP", "1993")
    #getAuthorInfo("Tuck")
    #metadataGetVolumes("IJP")
    #authorsGetAuthorInfo("Tuck")
    #authorsGetAuthorPublications("Tuck", limit=40, offset=0)    
    #databaseGetMostCited(limit=10, offset=0)
    #getArticleData("PAQ.073.0005A")
    
    # docstring tests
    import doctest
    doctest.testmod()    
    main()
