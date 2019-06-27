#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326

"""
opasAPISupportLib

This library is meant to hold the heart of the API based Solr queries and other support 
functions.  

2019.0614.1 - Python 3.7 compatible.  Work in progress.

"""
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2019.0625.1"
__status__      = "Development"

import sys
sys.path.append('../libs')
sys.path.append('../config')

import opasConfig
from localsecrets import SOLRURL, SOLRUSER, SOLRPW

import re
import os.path

import time
import datetime
from datetime import datetime
from typing import List
from enum import Enum
import pymysql

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
from pydantic import ValidationError

from ebooklib import epub

#import imp

from stdMessageLib import copyrightPageHTML  # copyright page text to be inserted in ePubs and PDFs

# note: documents and documentList share the same internals, except the first level json label (documents vs documentlist)
from models import ListTypeEnum, \
                   ResponseInfo, \
                   DocumentList, \
                   Documents, \
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
                   AuthorIndexItem, \
                   SearchFormFields

import opasXMLHelper as opasxmllib
import opasGenSupportLib as opasgenlib
import sourceInfoDB as SourceInfoDB
    
sourceDB = SourceInfoDB.SourceInfoDB()
logging.basicConfig(filename='pepsolrtest.log', format="%(asctime)s %(message)s", level=logging.INFO)

#from solrq import Q
import json

# Setup a Solr instance. The timeout is optional.
#solr = pysolr.Solr('http://localhost:8983/solr/pepwebproto', timeout=10)
#This is the old way -- should switch to class Solr per https://pythonhosted.org/solrpy/reference.html
if SOLRUSER is not None:
    solrDocs = solr.SolrConnection(SOLRURL + 'pepwebproto', http_user=SOLRUSER, http_pass=SOLRPW)
    solrRefs = solr.SolrConnection(SOLRURL + 'pepwebrefsproto', http_user=SOLRUSER, http_pass=SOLRPW)
    solrGloss = solr.SolrConnection(SOLRURL + 'pepwebglossary', http_user=SOLRUSER, http_pass=SOLRPW)
    solrAuthors = solr.SolrConnection(SOLRURL + 'pepwebauthors', http_user=SOLRUSER, http_pass=SOLRPW)

else:
    solrDocs = solr.SolrConnection(SOLRURL + 'pepwebproto')
    solrRefs = solr.SolrConnection(SOLRURL + 'pepwebrefsproto')
    solrGloss = solr.SolrConnection(SOLRURL + 'pepwebglossary')
    solrAuthors = solr.SolrConnection(SOLRURL + 'pepwebauthors')

#API endpoints
documentURL = "/v1/Documents/"

def checkSolrDocsConnection():
    if solrDocs is None:
        return False
    else:
        return True

def forceStringReturnFromVariousReturnTypes(theText, minLength=5):
    retVal = None
    if theText is not None:
        if isinstance(theText, str):
            if len(theText) > minLength:
                # we have an abstract
                retVal = theText
        elif isinstance(theText, list):
            retVal = theText[0]
            if retVal == [] or retVal == '[]':
                retVal = None
        else:
            logging.error("Type mismatch on Solr Data")
            print ("ERROR: %s" % type(retVal))

        try:
            if isinstance(retVal, lxml.etree._Element):
                retVal = etree.tostring(retVal)
            
            if isinstance(retVal, bytes) or isinstance(retVal, bytearray):
                logging.error("Byte Data")
                retVal = retVal.decode("utf8")
        except Exception as e:
            err = "Error forcing conversion to string: %s / %s" % (type(retVal), e)
            logging.error(err)
            print (err)
            
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
                     count = len(results.results),
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
        citeAs = forceStringReturnFromVariousReturnTypes(citeAs)
        
        item = DocumentListItem( documentID = artID,
                                 instanceCount = count,
                                 title = opasgenlib.getFirstValueOfDictItemList(artInfo, "title"),
                                 PEPCode = artInfo.get("art_pepsrccode", None), 
                                 authorMast = artInfo.get("art_authors_mast", None),
                                 year = artInfo.get("art_year", None),
                                 vol = artInfo.get("art_vol", None),
                                 pgRg = pgRg,
                                 issue = artInfo.get("art_iss", None),
                                 pgStart = pgStart,
                                 pgEnd = pgEnd,
                                 documentRefHTML = artInfo.get("art_citeas_xml", None),
                                 documentRef = opasxmllib.xmlElemOrStrToText(citeAs, defaultReturn=None),
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

def databaseWhatsNew(limit=15, offset=0):
    """
    Return a what's been updated in the last week
    
    >>> databaseWhatsNew()
    
    """    
    results = solrDocs.query(q = "timestamp:[NOW-7DAYS TO NOW]",  
                             fl = "art_id, title, art_vol, art_iss, art_pepsrccode, timestamp, art_pepsourcetype",
                             fq = "{!collapse field=art_pepsrccode max=art_year_int}",
                             sort="timestamp", sort_order="desc",
                             rows=150, offset=0,
                             )
    
    print ("Number found: %s" % results._numFound)
    
    responseInfo = ResponseInfo(
                     count = len(results.results),
                     fullCount = results._numFound,
                     limit = limit,
                     offset = offset,
                     listType="newlist",
                     fullCountComplete = limit >= results._numFound,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )

    
    whatsNewListItems = []
    rowCount = 0
    alreadySeen = []
    for result in results:
        PEPCode = result.get("art_pepsrccode", None)
        #if PEPCode is None or PEPCode in ["SE", "GW", "ZBK", "IPL"]:  # no books
            #continue
        PEPSourceType = result.get("art_pepsourcetype", None)
        if PEPSourceType != "journal":
            continue
            
        volume = result.get("art_vol", None)
        issue = result.get("art_iss", "")
        year = result.get("art_year", None)
        abbrev = sourceDB.sourceData[PEPCode].get("sourcetitleabbr", "")
        updated = result.get("timestamp", None)
        updated = updated.strftime('%Y-%m-%d')
        displayTitle = abbrev + " v%s.%s (%s) (Added: %s)" % (volume, issue, year, updated)
        if displayTitle in alreadySeen:
            continue
        else:
            alreadySeen.append(displayTitle)
        volumeURL = "/v1/Metadata/Contents/%s/%s" % (PEPCode, issue)
        srcTitle = sourceDB.sourceData[PEPCode].get("sourcetitlefull", "")
            
        item = WhatsNewListItem( documentID = result.get("art_id", None),
                                 displayTitle = displayTitle,
                                 abbrev = abbrev,
                                 volume = volume,
                                 issue = issue,
                                 year = year,
                                 PEPCode = PEPCode, 
                                 srcTitle = srcTitle,
                                 volumeURL = volumeURL,
                                 updated = updated
                              ) 
        print (item.displayTitle)
        whatsNewListItems.append(item)
        rowCount += 1
        if rowCount > limit:
            break

    responseInfo.count = len(whatsNewListItems)
    
    whatsNewListStruct = WhatsNewListStruct( responseInfo = responseInfo, 
                                             responseSet = whatsNewListItems
                                             )
    
    whatsNewList = WhatsNewList(whatsNew = whatsNewListStruct)
    
    retVal = whatsNewList
    
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
                     count = len(results.results),
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

def metadataGetContents(pepCode, year="*", vol="*", limit=100, offset=0):
    """
    Return a jounals contents
    
    >>> metadataGetContents("IJP", "1993", limit=5, offset=0)
    
    >>> metadataGetContents("IJP", "1993", limit=5, offset=5)
    
    """
    retVal = []
    if year == "*" and vol != "*":
        # specified only volume
        field="art_vol"
        searchVal = vol
    else:  #Just do year
        field="art_year"
        searchVal = "*"
        
    results = solrDocs.query(q = "art_pepsrccode:{} && {}:{}".format(pepCode, field, searchVal),  
                             fields = "art_id, art_vol, art_year, art_iss, art_iss_title, art_newsecnm, art_pgrg, art_title, art_author_id, art_citeas_xml",
                             sort="art_year, art_pgrg", sort_order="asc",
                             rows=limit, start=offset
                             )

    responseInfo = ResponseInfo(
                     count = len(results.results),
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
        citeAs = result.get("art_citeas_xml", None)  
        citeAs = forceStringReturnFromVariousReturnTypes(citeAs)
        
        item = DocumentListItem(PEPCode = pepCode, 
                                year = result.get("art_year", None),
                                vol = result.get("art_vol", None),
                                pgRg = result.get("art_pgrg", None),
                                pgStart = pgStart,
                                pgEnd = pgEnd,
                                authorMast = authorMast,
                                documentID = result.get("art_id", None),
                                documentRef = opasxmllib.xmlElemOrStrToText(citeAs, defaultReturn=""),
                                documentRefHTML = citeAs,
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

def metadataGetSourceByType(sourceType=None, limit=100, offset=0):
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
    
    >>> returnData = metadataGetSourceByType("journal")
    75

    >>> returnData = metadataGetSourceByType("book")
    75

    >>> returnData = metadataGetSourceByType("journals", limit=5, offset=0)
    
    >>> returnData = metadataGetSourceByType("journals", limit=5, offset=6)
    
    """
    retVal = []
    sourceInfoDBList = []
    # standardize Source type, allow plural, different cases, but code below this part accepts only those three.
    if sourceType not in ["journal", "book", "video"]:
        if re.match("vid.*", sourceType, re.IGNORECASE):
            sourceType = "video"
        elif re.match("boo.*", sourceType, re.IGNORECASE):
            sourceType = "book"
        else: # default
            sourceType = "journal"
            
    for sourceInfoDict in sourceDB.sourceData.values():
        if sourceInfoDict["pep_class"] == sourceType:
            # match
            sourceInfoDBList.append(sourceInfoDict)
    
    count = len(sourceInfoDBList)
    print ("Number found: %s" % count)

    responseInfo = ResponseInfo(
                     count = count,
                     fullCount = count,
                     limit = limit,
                     offset = offset,
                     listLabel = "{} List".format(sourceType),
                     listType = "sourceinfolist",
                     scopeQuery = "*",
                     fullCountComplete = True,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )

    sourceInfoListItems = []
    counter = 0
    for source in sourceInfoDBList:
        counter += 1
        if counter < offset:
            continue
        if counter > limit:
            break
        try:
            item = SourceInfoListItem( ISSN = source.get("ISSN"),
                                       PEPCode = source.get("pepsrccode"),
                                       abbrev = source.get("sourcetitleabbr"),
                                       bannerURL = "http://{}/{}/banner{}.logo.gif".format(opasConfig.BASEURL, opasConfig.IMAGES, source.get("pepsrccode")),
                                       displayTitle = source.get("sourcetitlefull"),
                                       language = source.get("language"),
                                       yearFirst = source.get("start_year"),
                                       yearLast = source.get("end_year"),
                                       sourceType = sourceType,
                                       title = source.get("pepsrccode")
                                       ) 
        except ValidationError as e:
            print ("SourceInfoListItem Validation Error:")
            print(e.json())        

        sourceInfoListItems.append(item)
        
    try:
        sourceInfoStruct = SourceInfoStruct( responseInfo = responseInfo, 
                                             responseSet = sourceInfoListItems
                                            )
    except ValidationError as e:
        print ("SourceInfoStruct Validation Error:")
        print(e.json())        
    
    try:
        sourceInfoList = SourceInfoList(sourceInfo = sourceInfoStruct)
    except ValidationError as e:
        print ("SourceInfoList Validation Error:")
        print(e.json())        
    
    retVal = sourceInfoList
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
    
    >>> authorsGetAuthorInfo("Tuck")
    
    >>> authorsGetAuthorInfo("Fonag")
    
    >>> authorsGetAuthorInfo("Levinson, Nadine A.")
    
    
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
                     count = len(results.results),
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
    
    >>> authorsGetAuthorPublications("Tuck")
    >>> authorsGetAuthorPublications("Fonag")
    >>> authorsGetAuthorPublications("Levinson, Nadine A.")
    
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
                     count = len(results.results),
                     fullCount = results._numFound,
                     limit = limit,
                     offset = offset,
                     listType="authorpublist",
                     fullCountComplete = limit >= results._numFound,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )

    authorPubListItems = []
    for result in results.results:
        citeAs = result.get("art_citeas_xml", None)
        citeAs = forceStringReturnFromVariousReturnTypes(citeAs)
        
        item = AuthorPubListItem( authorID = result.get("art_author_id", None), 
                                  documentID = result.get("art_id", None),
                                  documentRefHTML = citeAs,
                                  documentRef = opasxmllib.xmlElemOrStrToText(citeAs, defaultReturn=""),
                                  documentURL = documentURL + result.get("art_id", None),
                                  year = result.get("art_year", None),
                                  score = result.get("score", 0)
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

def getExcerptFromAbstractOrSummaryOrDocument(xmlAbstract, xmlSummary, xmlDocument):
   
    retVal = None
    # see if there's an abstract
    retVal = forceStringReturnFromVariousReturnTypes(xmlAbstract)
    if retVal is None:
        # try the summary
        retVal = forceStringReturnFromVariousReturnTypes(xmlSummary)
        if retVal is None:
            # get excerpt from the document
            if xmlDocument is None:
                # we fail.  Return None
                logging.warn("No excerpt can be found or generated.")
            else:
                # extract the first 10 paras
                retVal = forceStringReturnFromVariousReturnTypes(xmlDocument)
                retVal = opasxmllib.removeEncodingString(retVal)
                # deal with potentially broken XML excerpts
                parser = lxml.etree.XMLParser(encoding='utf-8', recover=True)                
                #root = etree.parse(StringIO(retVal), parser)
                root = etree.fromstring(retVal, parser)
                body = root.xpath("//*[self::h1 or self::p or self::p2 or self::pb]")
                retVal = ""
                count = 0
                for elem in body:
                    if elem.tag == "pb" or count > 10:
                        # we're done.
                        retVal = "%s%s%s" % ("<abs><unit type='excerpt'>", retVal, "</unit></abs>")
                        break
                    else:
                        retVal  += etree.tostring(elem, encoding='utf8').decode('utf8')

    return retVal
    
def documentsGetAbstracts(documentID, retFormat="HTML", limit=100, offset=0):
    """
    Returns an abstract or summary for the specified document
    If part of a documentID is supplied, multiple abstracts will be returned.
    
    The endpoint reminds me that we should be using documentID instead of "art" for article perhaps.
      Not thrilled about the prospect of changing it, but probably the right thing to do.
      
    >>> abstracts = documentsGetAbstracts("IJP.075")
    100 document matches for getAbstracts
    >>> abstracts = documentsGetAbstracts("AIM.038.0279A")  # no abstract on this one
    1 document matches for getAbstracts
    >>> abstracts = documentsGetAbstracts("AIM.040.0311A")
    1 document matches for getAbstracts
      
    """
    retVal = None
    results = solrDocs.query(q = "art_id:%s*" % (documentID),  
                                fields = "art_id, art_vol, art_year, art_citeas_xml, art_pgrg, art_title, art_author_id, abstracts_xml, summaries_xml, text_xml",
                                sort="art_year, art_pgrg", sort_order="asc",
                                rows=limit, start=offset
                             )
    
    matches = len(results.results)
    print ("%s document matches for getAbstracts" % matches)
    
    responseInfo = ResponseInfo(
                     count = len(results.results),
                     fullCount = results._numFound,
                     limit = limit,
                     offset = offset,
                     listType="documentlist",
                     fullCountComplete = limit >= results._numFound,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )
    
    documentItemList = []
    for result in results:
        if matches > 0:
            try:
                xmlAbstract = result["abstracts_xml"]
            except KeyError as e:
                xmlAbstract = None
                logging.info("No abstract for document ID: %s" % documentID)
        
            try:
                xmlSummary = result["summaries_xml"]
            except KeyError as e:
                xmlSummary = None
                logging.info("No summary for document ID: %s" % documentID)
        
            try:
                xmlDocument = result["text_xml"]
            except KeyError as e:
                xmlDocument = None
                logging.error("No content matched document ID for: %s" % documentID)

            authorIDs = result.get("art_author_id", None)
            if authorIDs is None:
                authorMast = None
            else:
                authorMast = opasgenlib.deriveAuthorMast(authorIDs)

            pgRg = result.get("art_pgrg", None)
            pgStart, pgEnd = opasgenlib.pgRgSplitter(pgRg)

            abstract = getExcerptFromAbstractOrSummaryOrDocument(xmlAbstract, xmlSummary, xmlDocument)
            if abstract == "[]":
                abstract = None
            elif retFormat == "HTML":
                abstractHTML = opasxmllib.convertXMLStringToHTML(abstract)
                abstract = opasxmllib.extractHTMLFragment(abstractHTML, "//div[@id='abs']")
            elif retFormat == "TEXTONLY":
                abstract = opasxmllib.xmlElemOrStrToText(abstract)
            #else: # xml  # not necessary, let it fall through
                #pass
            
            citeAs = result.get("art_citeas_xml", None)
            citeAs = forceStringReturnFromVariousReturnTypes(citeAs)
            
            item = DocumentListItem(year = result.get("art_year", None),
                                    vol = result.get("art_vol", None),
                                    pgRg = pgRg,
                                    pgStart = pgStart,
                                    pgEnd = pgEnd,
                                    authorMast = authorMast,
                                    documentID = result.get("art_id", None),
                                    documentRefHTML = citeAs,
                                    documentRef = opasxmllib.xmlElemOrStrToText(citeAs, defaultReturn=""),
                                    accessLimited = False, # Todo
                                    abstract = abstract,
                                    score = result.get("score", None)
                                    )
        
            #print (item)
            documentItemList.append(item)

    responseInfo.count = len(documentItemList)
    
    documentListStruct = DocumentListStruct( responseInfo = responseInfo, 
                                             responseSet=documentItemList
                                             )
    
    documents = Documents(documents = documentListStruct)
        
    retVal = documents
            
                
    return retVal


def documentsGetDocument(documentID, retFormat="XML", authenticated=True, limit=1, offset=0):
    """
   For non-authenticated users, this endpoint returns only Document summary information (summary/abstract)
   For authenticated users, it returns with the document itself
   
    >>> documentsGetDocument("AIM.038.0279A", retFormat="html") 
    >>> documentsGetDocument("AIM.038.0279A") 
    >>> documentsGetDocument("AIM.040.0311A")
    

    """
    retVal = {}
    
    if not authenticated:
        #if user is not authenticated, effectively do endpoint for getDocumentAbstracts
        return documentsGetAbstracts(documentID, limit=1)

    results = solrDocs.query(q = "art_id:%s" % (documentID),  
                                fields = "art_id, art_vol, art_year, art_citeas_xml, art_pgrg, art_title, art_author_id, abstracts_xml, summaries_xml, text_xml"
                             )
    matches = len(results.results)
    print ("%s document matches for getAbstracts" % matches)
    
    responseInfo = ResponseInfo(
                     count = len(results.results),
                     fullCount = results._numFound,
                     limit = limit,
                     offset = offset,
                     listType="documentlist",
                     fullCountComplete = limit >= results._numFound,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )
    
    documentItemList = []
    if matches >= 1:
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
                    retVal = opasxmllib.removeEncodingString(retVal)
                    retVal = opasxmllib.convertXMLStringToHTML(retVal)
                    
            except Exception as e:
                logging.warning("Can't convert data: %s" % e)
    
            responseInfo = ResponseInfo(
                             count = len(results.results),
                             fullCount = results._numFound,
                             limit = 1,
                             offset = 0,
                             listType="documentlist",
                             fullCountComplete = results._numFound <= 1,
                             timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                           )
    
            if results._numFound > 0:
                result = results.results[0]
                try:
                    xmlAbstract = result["abstracts_xml"]
                except KeyError as e:
                    xmlAbstract = None
                    logging.info("No abstract for document ID: %s" % documentID)
            
                try:
                    xmlSummary = result["summaries_xml"]
                except KeyError as e:
                    xmlSummary = None
                    logging.info("No summary for document ID: %s" % documentID)
            
                try:
                    xmlDocument = forceStringReturnFromVariousReturnTypes(result["text_xml"])
                except KeyError as e:
                    xmlDocument = None
                    logging.error("No content matched document ID for: %s" % documentID)
    
                authorIDs = result.get("art_author_id", None)
                if authorIDs is None:
                    authorMast = None
                else:
                    authorMast = opasgenlib.deriveAuthorMast(authorIDs)
    
                pgRg = result.get("art_pgrg", None)
                pgStart, pgEnd = opasgenlib.pgRgSplitter(pgRg)
    
                abstract = getExcerptFromAbstractOrSummaryOrDocument(xmlAbstract, xmlSummary, xmlDocument)
                if abstract == "[]":
                    abstract = None
                elif retFormat == "HTML":
                    abstractHTML = opasxmllib.convertXMLStringToHTML(abstract)
                    abstract = opasxmllib.extractHTMLFragment(abstractHTML, "//div[@id='abs']")
                elif retFormat == "TEXTONLY":
                    abstract = opasxmllib.xmlElemOrStrToText(abstract)
                #else: # not needed
                    #abstract = abstract
    
                if xmlDocument == "[]":
                    documentText = xmlDocument = None
                elif retFormat == "HTML":
                    documentText  = opasxmllib.removeEncodingString(xmlDocument)
                    documentText = opasxmllib.convertXMLStringToHTML(documentText)
                elif retFormat == "TEXTONLY":
                    documentText  = opasxmllib.removeEncodingString(xmlDocument)
                    documentText  = opasxmllib.xmlElemOrStrToText(documentText)
                else: # XML
                    documentText = xmlDocument
    
                citeAs = result.get("art_citeas_xml", None)
                citeAs = forceStringReturnFromVariousReturnTypes(citeAs)
                
                item = DocumentListItem(year = result.get("art_year", None),
                                        vol = result.get("art_vol", None),
                                        pgRg = pgRg,
                                        pgStart = pgStart,
                                        pgEnd = pgEnd,
                                        authormast = authorMast,  #TODO fix data model case to authorMast, but GVPi did it like this in their server
                                        documentID = result.get("art_id", None),
                                        documentRefHTML = citeAs,
                                        documentRef = opasxmllib.xmlElemOrStrToText(citeAs, defaultReturn=""),
                                        accessLimited = False, # Todo
                                        abstract = abstract,
                                        document = documentText,
                                        score = result.get("score", None)
                                        )

                documentItemList.append(item)

    responseInfo.count = len(documentItemList)  # will be ONE or ZERO
            
    documentListStruct = DocumentListStruct( responseInfo = responseInfo, 
                                             responseSet=documentItemList
                                             )
    
    documents = Documents(documents = documentListStruct)
        
    retVal = documents
    
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
        documentsGetAbstracts(documentID, limit=1)
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
                        retVal = opasxmllib.removeEncodingString(retVal)
                        filename = convertXMLToHTMLFile(retVal, outputFilename=documentID + ".html")  # returns filename
                        retVal = filename
                    elif retFormat.lower() == "epub":
                        retVal = opasxmllib.removeEncodingString(retVal)
                        htmlString = opasxmllib.convertXMLStringToHTML(retVal)
                        htmlString = addEPUBElements(htmlString)
                        filename = opasxmllib.convertHTMLToEPUB(htmlString, documentID, documentID)
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

    htmlString = opasxmllib.convertXMLStringToHTML(xmlTextStr, xsltFile=xsltFile)
    fo = open(outputFilename, "w")
    fo.write(str(htmlString))
    fo.close()
    
    return outputFilename

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

def getKwicList(markedUpText, extraContextLen=20, startHitTag=opasConfig.HITMARKERSTART, endHitTag=opasConfig.HITMARKEREND):
    """
    Find all nonoverlapping 
    """
    retVal = []
    emMarks = re.compile("(.{0,20}%s.*%s.{0,20})" % (startHitTag, endHitTag))
    for n in emMarks.finditer(markedUpText):
        retVal.append(n.group(0))
        print ("Match {}".format(n.group(0)))
    matchCount = len(retVal)
    
    return retVal    

def yearArgParser(yearArg):
    retVal = None
    yearQuery = re.match("[ ]*(?P<option>[\>\^\<\=])?[ ]*(?P<start>[12][0-9]{3,3})?[ ]*(?P<separator>([-]|TO))*[ ]*(?P<end>[12][0-9]{3,3})?[ ]*", yearArg, re.IGNORECASE)            
    if yearQuery is None:
        logging("Search - StartYear bad argument {}".format(yearArg))
    else:
        option = yearQuery.group("option")
        start = yearQuery.group("start")
        end = yearQuery.group("end")
        separator = yearQuery.group("separator")
        if start is None and end is None:
            logging("Search - StartYear bad argument {}".format(yearArg))
        else:
            if option == "^":
                # between
                # find endyear by parsing
                if start is None:
                    start = end # they put > in start rather than end.
                elif end is None:
                    end = start # they put < in start rather than end.
                searchClause = "&& art_year_int:[{} TO {}] ".format(start, end)
            elif option == ">":
                # greater
                if start is None:
                    start = end # they put > in start rather than end.
                searchClause = "&& art_year_int:[{} TO {}] ".format(start, "*")
            elif option == "<":
                # less than
                if end is None:
                    end = start # they put < in start rather than end.
                searchClause = "&& art_year_int:[{} TO {}] ".format("*", end)
            else: # on
                if start is not None and end is not None:
                    # they specified a range anyway
                    searchClause = "&& art_year_int:[{} TO {}] ".format(start, end)
                elif start is None and end is not None:
                    # they specified '- endyear' without the start, so less than
                    searchClause = "&& art_year_int:[{} TO {}] ".format("*", end)
                elif start is not None and separator is not None:
                    # they mean greater than
                    searchClause = "&& art_year_int:[{} TO {}] ".format(start, "*")
                else: # they mean on
                    searchClause = "&& art_year_int:{} ".format(yearArg)

            retVal = searchClause

    return retVal
                         
def searchText(query, 
               filterQuery = None,
               moreLikeThese = False,
               queryAnalysis = False,
               summaryFields="art_id, art_pepsrccode, art_vol, art_year, art_iss, art_iss_title, art_newsecnm, art_pgrg, art_title, art_author_id, art_citeas_xml", 
               highlightFields='art_title_xml, abstracts_xml, summaries_xml, art_authors_xml, text_xml', 
               fullTextRequested=True, userLoggedIn=False, limit=0, offset=10):
    """
    Full-text search

    >>> searchText(query="art_title_xml:'ego identity'", limit=10, offset=0, fullTextRequested=False)
    
        Original Parameters in API
        Original API return model example, needs to be supported:
    
                "authormast": "Ringstrom, P.A.",
				"documentID": "IJPSP.005.0257A",
				"documentRef": "Ringstrom, P.A. (2010). Commentary on Donna Orange's, &#8220;Recognition as: Intersubjective Vulnerability in the Psychoanalytic Dialogue&#8221;. Int. J. Psychoanal. Self Psychol., 5(3):257-273.",
				"issue": "3",
				"PEPCode": "IJPSP",
				"pgStart": "257",
				"pgEnd": "273",
				"title": "Commentary on Donna Orange's, &#8220;Recognition as: Intersubjective Vulnerability in the Psychoanalytic Dialogue&#8221;",
				"vol": "5",
				"year": "2010",
				"rank": "100",
				"citeCount5": "1",
				"citeCount10": "3",
				"citeCount20": "3",
				"citeCountAll": "3",
				"kwic": ". . . \r\n        

    
    """
    if moreLikeThese:
        mlt_fl = "text_xml, headings_xml, terms_xml, references_xml"
        mlt = "true"
        mlt_minwl = 8
    else:
        mlt_fl = None
        mlt = "false"
        mlt_minwl = None
    
    if queryAnalysis:
        queryDebug = "on"
    else:
        queryDebug = "off"
        
        
    results = solrDocs.query(query,  
                             fq = filterQuery,
                             debugQuery = queryDebug,
                             fields = summaryFields,
                             hl= 'true', 
                             hl_fragsize = 1520000, 
                             hl_fl = highlightFields,
                             mlt = mlt,
                             mlt_fl = mlt_fl,
                             mlt_count = 2,
                             mlt_minwl = mlt_minwl,
                             rows = limit,
                             start = offset,
                             hl_simple_pre = opasConfig.HITMARKERSTART,
                             hl_simple_post = opasConfig.HITMARKEREND)

    print ("Search Performed: %s" % query)
    print ("Result  Set Size: %s" % results._numFound)
    print ("Return set limit: %s" % limit)
    
    responseInfo = ResponseInfo(
                     count = len(results.results),
                     fullCount = results._numFound,
                     limit = limit,
                     offset = offset,
                     listType="documentlist",
                     scopeQuery=query,
                     fullCountComplete = limit >= results._numFound,
                     solrParams = results._params,
                     timeStamp = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')                     
                   )


    retVal = {}
    documentItemList = []
    rowCount = 0
    rowOffset = 0
    for result in results.results:
        authorIDs = result.get("art_author_id", None)
        if authorIDs is None:
            authorMast = None
        else:
            authorMast = opasgenlib.deriveAuthorMast(authorIDs)

        pgRg = result.get("art_pgrg", None)
        if pgRg is not None:
            pgStart, pgEnd = opasgenlib.pgRgSplitter(pgRg)
            
        documentID = result.get("art_id", None)        
        titleXml = results.highlighting[documentID].get("art_title_xml", None)
        titleXml = forceStringReturnFromVariousReturnTypes(titleXml)
        abstractsXml = results.highlighting[documentID].get("abstracts_xml", None)
        abstractsXml  = forceStringReturnFromVariousReturnTypes(abstractsXml )
        summariesXml = results.highlighting[documentID].get("abstracts_xml", None)
        summariesXml  = forceStringReturnFromVariousReturnTypes(summariesXml)
        textXml = results.highlighting[documentID].get("text_xml", None)
        textXml  = forceStringReturnFromVariousReturnTypes(textXml)
        if textXml is not None:
            kwicList = getKwicList(textXml)  # an alternate way making it easier for clients
            kwic = " . . . ".join(kwicList)  # how its done at GVPi, for compatibility.
            print ("Length of document: {} Number of matches to show: {}".format(len(textXml), len(kwicList)))
        else:
            kwicList = []
            kwic = ""  # this has to be "" for PEP-Easy, or it hits an object error.  
            print ("No matches to show in document {}".format(documentID))            
        
        if not userLoggedIn or not fullTextRequested:
            textXml = getExcerptFromAbstractOrSummaryOrDocument(xmlAbstract=abstractsXml, xmlSummary=summariesXml, xmlDocument=textXml)

        citeAs = result.get("art_citeas_xml", None)
        citeAs = forceStringReturnFromVariousReturnTypes(citeAs)
        
        if moreLikeThese:
            similarDocs = results.moreLikeThis[documentID]
            similarMaxScore = results.moreLikeThis[documentID].maxScore
            similarNumFound = results.moreLikeThis[documentID].numFound
        else:
            similarDocs = None
            similarMaxScore = None
            similarNumFound = None
        
        try:
            item = DocumentListItem(PEPCode = result.get("art_pepsrccode", None), 
                                    year = result.get("art_year", None),
                                    vol = result.get("art_vol", None),
                                    pgRg = pgRg,
                                    pgStart = pgStart,
                                    pgEnd = pgEnd,
                                    authorMast = authorMast,
                                    documentID = documentID,
                                    documentRefHTML = citeAs,
                                    documentRef = opasxmllib.xmlElemOrStrToText(citeAs, defaultReturn=""),
                                    kwic = kwic,
                                    kwicList = kwicList,
                                    title = titleXml,
                                    abstract = abstractsXml,
                                    documentText = None, #textXml,
                                    score = result.get("score", None), 
                                    similarDocs = similarDocs,
                                    similarMaxScore = similarMaxScore,
                                    similarNumFound = similarNumFound
                                    )
        except ValidationError as e:
            print(e.json())        
        else:
            rowCount += 1
            print ("{}:{}".format(rowCount, citeAs))
            documentItemList.append(item)
            if rowCount > limit:
                break

    responseInfo.count = len(documentItemList)
    
    documentListStruct = DocumentListStruct( responseInfo = responseInfo, 
                                             responseSet = documentItemList
                                             )
    
    documentList = DocumentList(documentList = documentListStruct)
    
    retVal = documentList
    
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
    #databaseWhatsNew()
    # docstring tests
    
    import doctest
    doctest.testmod()    
    main()
