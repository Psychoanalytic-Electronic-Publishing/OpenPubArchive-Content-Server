#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2019.0617.1"
__status__      = "Development"

import sys
sys.path.append('../libs')

import re
import os.path

import time
import datetime
from datetime import datetime
from typing import List, Generic, TypeVar, Optional
from enum import Enum

from pydantic import BaseModel, Schema
# from pydantic.types import EmailStr
from modelsOpasCentralPydantic import User
#from opasCentralDBLib import opasCentralDB

#-------------------------------------------------------
#
# Detail level schema structures
#
#-------------------------------------------------------
OpasDB = TypeVar('OpasDB')
   
   
class QueryParameters(BaseModel):
    analyzeThis: str = ""
    searchQ: str = ""
    filterQ: str = ""
    searchAnalysisTermList: List[str] = []
    solrMax: str = None
    solrSortBy: str = None
    urlRequest: str = ""

class SearchFormFields(BaseModel): # not used
    quickSearch: str = Schema(None, title="")
    solrQ: str = Schema(None, title="")
    disMax: str = Schema(None, title="")
    edisMax: str = Schema(None, title="")
    partialDocumentID: str = Schema(None, title="")
    compoundQuery: bool = Schema(None, title="")
    wordsOrPhrases: str = Schema(None, title="")
    sourceWords: str = Schema(None, title="")
    sourceCodes: str = Schema(None, title="")
    sourceSet: str = Schema(None, title="")
    author: str = Schema(None, title="")
    title: str = Schema(None, title="")
    year: str = Schema(None, title="")
    startYear: str = Schema(None, title="")
    endYear: str = Schema(None, title="")
    citedTimes: int = Schema(None, title="")
    citedPeriod: int = Schema(None, title="")
    viewedTimes: int = Schema(None, title="")
    viewedPeriod: int = Schema(None, title="")
    articles: str = Schema(None, title="")
    paragraphs: str = Schema(None, title="")
    references: str = Schema(None, title="")
    referenceAuthors: str = Schema(None, title="")
    poems: str = Schema(None, title="")
    quotes: str = Schema(None, title="")
    dialogs: str = Schema(None, title="")
    quotes: str = Schema(None, title="")
    
#-------------------------------------------------------
# Enums
#-------------------------------------------------------
class ListTypeEnum(Enum):
    volumelist = "volumelist"
    documentList = "documentlist"
    authorPubList = "authorpublist"
    authorIndex = "authorindex"
    imageURLList = "imageurllist"
    licenseInfo = "licenseinfo"
    sourceInfoList = "sourceinfolist"
    whatsNewList = "newlist"
    mostCitedList = "mostcited"
    mostViewedList = "mostviewed"
    searchAnalysisList = "srclist"
    
class ReportTypeEnum(str, Enum):
    mostViewed = "mostViewed"
    mostCited = "mostCited"
    
class SearchModeEnum(Enum):
    searchMode = "Searching"
    documentFetchMode = "DocumentFetch"
    moreLikeTheseMode = "MoreLikeThese"
    queryAnalysisMode = "QueryAnalysis"
   
class TimePeriod(Enum):
    five = '5'
    ten = '10'
    twenty = '20'
    alltime = 'all'

#-------------------------------------------------------
# Error Return classes [may not be used, switched to exceptions]
#-------------------------------------------------------
class ErrorReturn(BaseModel):
    error: str = Schema(None, title="Error class or title")
    error_message: str = Schema(None, title="Error description")

#-------------------------------------------------------
# Key data status return structure, part of most models
#-------------------------------------------------------
class ResponseInfo(BaseModel):
    count: int = Schema(0, title="The number of returned items in the accompanying ResponseSet list.")
    limit: int = Schema(0, title="The limit set by the API client for the ResponseSet list.")
    offset: int = Schema(None, title="The offset the ResponseSet list begins as requested by the client to index into the full set of results, i.e., for paging through the full set.")
    page: int = Schema(None, title="If the request for a document was for a specific page number, the page number is listed here.  Offset will then reflect the relative page number from the start of the document.")
    fullCount: int = Schema(None, title="The number of items that could be returned without a limit set.")
    fullCountComplete: bool = Schema(None, title="How many matches 'theoretically' matched, though they cannot be returned for some reason, such as a search engine limitation on returned data.")
    totalMatchCount: int = Schema(None, title="The number of items in the complete match set that can be retrieved and paged through.")  # used in PEPEasy paging controls
    listLabel: str = Schema(None, title="Descriptive title of data return for SourceInfoList, e.g., Book List, Journal List, Video List. Should be used elsewhere too.")
    listType: ListTypeEnum = Schema(None, title="ListTypeEnum based identifier of the return structure, e.g., 'documentList'.")
    scopeQuery: list = Schema(None, title="The query strings applied: [query_string, filter_string]")
    request: str = Schema(None, title="The URL request (endpoint) that resulted in this response.")
    solrParams: dict = Schema(None, title="A dictionary based set of the parameters passed to the Solr search engine for this request.")
    errors: ErrorReturn = Schema(None, title="Any Error information")
    timeStamp: str = Schema(None, title="Server timestamp of return data.")   

#-------------------------------------------------------
# Data Return classes
#-------------------------------------------------------
class authorInfo(BaseModel):
    first: str = Schema(None, title="First name")
    middle: str = Schema(None, title="Middle name")
    last: str = Schema(None, title="Last name")
    title: str = Schema(None, title="Prename title (Mr. Mrs. Dr.") 
    affil: str = Schema(None, title="Affiliation")
    
class authorList(BaseModel):
    authorList: List[authorInfo] = []   

#-------------------------------------------------------

class AuthorPubListItem(BaseModel):
    authorID: str = Schema(None, title="Author ID as indexed by the system.")
    documentID: str = Schema(None, title="Doc ID for this publication by the author.")
    documentRef: str = Schema(None, title="The bibliographic form presentation of the information about the document, as in the 'citeas' area or reference sections (text-only).")
    documentRefHTML: str = Schema(None, title="Same as documentRef but in HTML.")
    year: str = Schema(None, title="Year of publication of this list item.")
    documentURL: str = Schema(None, title="API Endpoint URL (minus base) to access this document.")
    score: float = None

class AuthorPubListStruct(BaseModel):
    responseInfo: ResponseInfo 
    responseSet: List[AuthorPubListItem] = []

class AuthorPubList(BaseModel):
    authorPubList: AuthorPubListStruct

#-------------------------------------------------------

class AuthorIndexItem(BaseModel):
    authorID: str = Schema(None, title="Author ID as indexed by the system.")
    publicationsURL: str = Schema(None, title="Endpoint URL for this API to retrieve a list of this authors publications.")
    publicationsCount: int = Schema(None, title="The number of publications in this database by this author.")
    
class AuthorIndexStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: List[AuthorIndexItem] = []

class AuthorIndex(BaseModel):
    authorIndex: AuthorIndexStruct
    
#-------------------------------------------------------
class AlertListItem(BaseModel):
    alertName: str
    alertSubscribeStatus: bool
    alertSubscribeDate: str
    action: str = Schema(None, title="")

class AlertListStruct(BaseModel):
    responseInfo: ResponseInfo 
    responseSet: List[AlertListItem] = []

class AlertList(BaseModel):
    alertList: AlertListStruct

#-------------------------------------------------------

class DocumentListItem(BaseModel):
    PEPCode: str = Schema(None, title="The code assigned to a source, e.g., CPS, IJP, ANIJP-EL, ZBK.  (The first part of the document ID.)")
    sourceTitle: str = Schema(None, title="The full name of the source(title)")
    documentID: str = Schema(None, title="The multiple-section document ID, e.g., CPS.007B.0021A.B0012 in a biblio, or CPS.007B.0021A as a document ID.")
    authormast: str = Schema(None, title="The author names as displayed below the title in an article.")
    documentRef: str = Schema(None, title="The bibliographic form presentation of the information about the document, as in the 'citeas' area or reference sections (text-only).")
    documentRefHTML: str = Schema(None, title="Same as documentRef but in HTML.")
    kwicList: list = Schema(None, title="The matched terms in the matched document context, set by server config DEFAULT_KWIC_CONTENT_LENGTH ") # a real list, seems better long term
    kwic: str = Schema(None, title="") # text, concatenated, not a list -- the way GVPi did it
    issue: str = Schema(None, title="The source issue")
    issueTitle: str = Schema(None, title="Issues sometimes have titles")
    newSectionName: str = Schema(None, title="The name of the section, appear for the first article of a section")
    pgRg: str = Schema(None, title="The start and end pages of a document, separated by a dash")
    pgStart: str = Schema(None, title="The start page of a document")
    pgEnd: str = Schema(None, title="The end page of a document")
    title: str = Schema(None, title="The document title")
    vol: str = Schema(None, title="The volume number of the source, can be alphanumeric")
    year: str = Schema(None, title="The four digit year of publication")
    term: str = Schema(None, title="For search analysis, the clause or term being reported")
    termCount: int = Schema(None, title="For search analysis, the count of occurences of the clause or term being reported")
    abstract: str = Schema(None, title="The document abstract, with markup")
    document: str = Schema(None, title="The full-text document, with markup")
    updated: datetime = None
    accessLimited: bool = False
    accessLimitedReason: str = Schema(None, title="")
    accessLimitedDescription: str = Schema(None, title="")
    accessLimitedCurrentContent: bool = Schema(None, title="")
    score: float = None
    rank: int = Schema(None, title="")
    instanceCount: int = Schema(None, title="Reusable field to return counts requested")
    count1: int = Schema(None, title="Number of times cited in the past 5 yrs or downloaded in the last week (depending on endpoint)")
    count2: int = Schema(None, title="Number of times cited in the past 10 yrs or downloaded in the last month (depending on endpoint)")
    count3: int = Schema(None, title="Number of times cited in the past 20 yrs or downloaded in the last 6 months (depending on endpoint)")
    count4: int = Schema(None, title="Number of times cited in the past (reserved) yrs or downloaded in the last 12 months (depending on endpoint)")
    count5: int = Schema(None, title="Number of times cited in the past (reserved) yrs or downloaded in the last calendar year (depending on endpoint)")
    countAll: int = Schema(None, title="Number of times cited in the past or downloaded (depending on endpoint) in all years")
    similarDocs: list = None
    similarMaxScore: float = None
    similarNumFound: int = Schema(None, title="")
        
class DocumentListStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: List[DocumentListItem] = []

class DocumentList(BaseModel):
    documentList: DocumentListStruct

#-------------------------------------------------------

class DocumentStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: DocumentListItem

# modified PEPEasy2020 works with multiple 
class Documents(BaseModel):        # For the GVPi server, it returns a single object not an array of documents. But that's inconsistent with the abstract return.  Need to modify PEP-Easy and unify as a list.
    documents: DocumentListStruct

#-------------------------------------------------------

class ImageURLListItem(BaseModel):    
    PEPCode: str
    imageURL: str
    sourceType: str
    title: str

class ImageURLListStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: List[ImageURLListItem] = []

class ImageURLList(BaseModel):
    imageURLList: ImageURLListStruct

#-------------------------------------------------------
class ResponseInfoLoginStatus(BaseModel):
    loggedIn: bool = Schema(False, title="Whether the user is logged in or not")
    username: str = Schema(None, title="The logged in user's name")
    request: str = Schema(None, title="The URL of the request")
    #user: User = Schema(None, title="A user object for the user")
    error_message: str = Schema(None, title="If an error occurred, description")
    timeStamp: str = Schema(None, title="Server timestamp of return data.")   

class LoginReturnItem(BaseModel):    
    session_id: str = Schema(None, title="")
    token_type: str = Schema(None, title="")
    access_token: str = Schema(None, title="")
    session_expires_time: datetime = Schema(None, title="")
    authenticated: bool = Schema(False, title="")
    keep_active: bool = Schema(False, title="Extend the token retention time")
    error_message: str = Schema(None, title="Error description if login failed")
    scope: str = Schema(None, title="")

class LicenseInfoStruct(BaseModel):
    responseInfo: ResponseInfoLoginStatus
    responseSet: LoginReturnItem = None

class LicenseStatusInfo(BaseModel):
    licenseInfo: LicenseInfoStruct 

#-------------------------------------------------------
    

#-------------------------------------------------------

class SessionInfo(BaseModel):    
    #ocd: Optional[OpasDB]
    session_id: str = Schema(None, title="A generated session Identifier number the client passes in the header to identify the session")
    user_id: int = Schema(None, title="User ID (numeric)")
    username: str = Schema(None, title="Registered user name, for convenience here")
    user_ip: str = None
    connected_via: str = None
    session_start: datetime = None
    session_end: datetime = None
    session_expires_time: datetime = Schema(None, title="The limit on the user's session information without renewing")
    access_token: str = Schema(None, title="A generated session token identifying the client's access privileges")
    token_type: str = Schema(None, title="")
    authenticated: bool = Schema(False, title="")
    keep_active: bool = False
    scope: str = Schema(None, title="")
    api_client_id: int = None            

#-------------------------------------------------------
    
class ServerStatusItem(BaseModel):
    db_server_ok: bool = Schema(None, title="Database server is online")
    db_server_version: str = Schema(None, title="Version of the Database server")
    text_server_ok: bool = Schema(None, title="Text server is online")
    text_server_version: str = Schema(None, title="Version of the text server")
    api_server_version: str = Schema(None, title="Version of the API server software")
    timeStamp: str = Schema(None, title="Current time")
    # admin only
    user_count:  int = Schema(0, title="Number of users online")
    user_ip: str = Schema(None, title="Requestor's ip")
    config_name: str= Schema(None, title="Current Configuration Name")
    text_server_url: str= Schema(None, title="Current SOLR URL")

#-------------------------------------------------------

class JournalInfoListItem(BaseModel):    # Same as SourceInfoListItem minus a few fields
    sourceType: str = Schema(None, title="")
    PEPCode: str = Schema(None, title="")
    bannerURL: str = Schema(None, title="")
    displayTitle: str = Schema(None, title="Reference format for this source")
    srcTitle: str = Schema(None, title="Title of this source (from V1. Deprecated)")
    title: str = Schema(None, title="Title of this source")
    abbrev: str = Schema(None, title="")
    ISSN: str = Schema(None, title="")
    language: str = Schema(None, title="")
    yearFirst: str = Schema(None, title="")
    yearLast: str = Schema(None, title="")
    embargoYears: str = Schema(None, title="")
    
class JournalInfoStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: List[JournalInfoListItem] = []

class JournalInfoList(BaseModel):
    sourceInfo: JournalInfoStruct

#-------------------------------------------------------

class SourceInfoListItem(BaseModel):    
    sourceType: str = Schema(None, title="")
    PEPCode: str = Schema(None, title="")
    bookCode: str = Schema(None, title="Like PEPCode (srcCode) but specialized for books where many books fall under the same src_code")
    documentID: str = Schema(None, title="OPAS ID for this document")
    bannerURL: str = Schema(None, title="Graphical banner/logo for this source (URL)")
    displayTitle: str = Schema(None, title="Reference format for this source")
    srcTitle: str = Schema(None, title="Title of this source (from V1. Deprecated)")
    title: str = Schema(None, title="Title of this source")
    authors: str = Schema(None, title="Authors of this source")
    pub_year: str = Schema(None, title="Year this was first published in the database")
    abbrev: str = Schema(None, title="Short form of the source, e.g., as used in references")
    ISSN: str = Schema(None, title="The ISSN for a journal or source that has an ISSN")
    ISBN10: str = Schema(None, title="The ISBN10 for a book, if available")
    ISBN13: str = Schema(None, title="The ISBN13 for a book, if available")
    language: str = Schema(None, title="Publication language (mainly)")
    yearFirst: str = Schema(None, title="First year available for this source")
    yearLast: str = Schema(None, title="Last year available for this source")
    embargoYears: str = Schema(None, title="")

class SourceInfoStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: List[SourceInfoListItem] = []

class SourceInfoList(BaseModel):
    sourceInfo: SourceInfoStruct

#-------------------------------------------------------
class TermIndexItem(BaseModel):
    term: str = Schema(None, title="The term as indexed by the system.")
    termCount: int = Schema(None, title="The number of documents with this term.")
    
class TermIndexStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: List[TermIndexItem] = []

class TermIndex(BaseModel):
    termIndex: TermIndexStruct

#-------------------------------------------------------
class VideoInfoListItem(BaseModel):    # Same as SourceInfoListItem minus a few fields
    sourceType: str = Schema(None, title="")
    PEPCode: str = Schema(None, title="")
    bannerURL: str = Schema(None, title="")
    displayTitle: str = Schema(None, title="Reference format for this source")
    title: str = Schema(None, title="Title of this source")
    abbrev: str = Schema(None, title="")
    ISSN: str = Schema(None, title="")
    language: str = Schema(None, title="")
    yearFirst: str = Schema(None, title="")
    yearLast: str = Schema(None, title="")
    embargoYears: str = Schema(None, title="")

class VideoInfoStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: List[VideoInfoListItem] = []

class VideoInfoList(BaseModel):
    sourceInfo: VideoInfoStruct

#-------------------------------------------------------
class VolumeListItem(BaseModel):
    PEPCode: str = Schema(None, title="")
    vol: str = Schema(None, title="")
    year: str = Schema(None, title="")
    
#-------------------------------------------------------
   
class ReportRow(BaseModel):
    row: List = []

class ReportListItem(BaseModel):
    title: str = Schema(None, title="The report title")
    filterDescription: str = Schema(None, title="Textuall description of filter applied")
    startDate: datetime =  Schema(None, title="Report data from this start date")
    endDate: datetime =  Schema(None, title="Report data to this end date")
    rowCount: int = Schema(None, title="Reusable field to return counts requested")
    row: List[ReportRow] = []
    
class ReportStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: ReportListItem

class Report(BaseModel):
    report: ReportStruct
    
    #responseInfo: ResponseInfo
    #responseSet: List[VolumeListItem] = []   
    #reportTitle: str = Schema(None, title="")
    #reportData: List[ReportRow] = [] # ReportListStruct

#-------------------------------------------------------

class VolumeListStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: List[VolumeListItem] = []   

class VolumeList(BaseModel):
    volumeList: VolumeListStruct
    
#-------------------------------------------------------
class WhatsNewListItem(BaseModel):
    displayTitle: str = Schema(None, title="")
    abbrev: str = Schema(None, title="")
    volume: str = Schema(None, title="")
    issue: str = Schema(None, title="")
    year: str = Schema(None, title="")
    PEPCode: str = Schema(None, title="")
    srcTitle: str = Schema(None, title="")
    updated: str = Schema(None, title="")
    volumeURL: str = Schema(None, title="")

class WhatsNewListStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: List[WhatsNewListItem] = []   

class WhatsNewList(BaseModel):
    whatsNew: WhatsNewListStruct

if __name__ == "__main__":
    pass

