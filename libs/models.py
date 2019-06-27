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
from typing import List
from enum import Enum

from pydantic import BaseModel, Schema
from pydantic.types import EmailStr
from modelsOpasCentralPydantic import User

#-------------------------------------------------------
#
# Detail level schema structures
#
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
    
    
class ResponseInfo(BaseModel):
    count: int = Schema(0, title="The number of return items the data list")
    limit: int = Schema(0, title="Limit the results to a subsset of this many items, starting at offset")
    offset: int = Schema(None, title="Used to index into the full set of results for returning subsets")
    fullCount: int = Schema(None, title="The number of items that could be returned without a limit set")
    fullCountComplete: bool = Schema(None, title="Deprecated.  This was for the GVPi server, when not all items could be returned")
    listLabel: str = Schema(None, title="Descriptive title of data return for SourceInfoList, e.g., Book List, Journal List, Video List. Should be used elsewhere too.")
    listType: ListTypeEnum = Schema(None, title="Identifier of return structure from enum list mndel, ListTypeEnum, e.g., ")
    scopeQuery: str = None
    request: str = None
    solrParams: dict = Schema(None, title="The set of parameters passed to the Solr search engine")
    timeStamp: str = None   

class ResponseInfoLoginStatus(BaseModel):
    loggedIn: bool = False
    userName: str = None
    request: str = None
    user: User = None
    timeStamp: str = None

class AlertListItem(BaseModel):
    alertName: str
    alertSubscribeStatus: bool
    alertSubscribeDate: str
    action: str = None

class AuthorIndexItem(BaseModel):
    authorID: str
    publicationsURL: str = None
    publicationsCount: int = None
    
class AuthorPubListItem(BaseModel):
    authorID: str
    documentID: str
    documentRef: str
    documentRefHTML: str = None
    year: str = None
    documentURL: str = None
    score: float = None

class DocumentListItem(BaseModel):
    PEPCode: str = None
    authormast: str = None
    documentID: str = None
    documentRef: str = None
    documentRefHTML: str = None
    kwicList: list = None # a real list, seems better long term
    kwic: str = None # the way GVPi did it
    issue: str = None
    issueTitle: str = None
    newSectionName: str = None
    pgRg: str = None
    pgStart: str = None
    pgEnd: str = None
    title: str = None
    vol: str = None
    year: str = None
    term: str = None
    termCount: str = None
    abstract: str = None
    document: str = None
    updated: datetime = None
    accessLimited: bool = False
    accessLimitedReason: str = None
    accessLimitedDescription: str = None
    accessLimitedCurrentContent: bool = None
    score: float = None
    rank: int = None
    instanceCount: int = None
    similarDocs: list = None
    similarMaxScore: float = None
    similarNumFound: int = None
    
    
class ImageURLListItem(BaseModel):    
    PEPCode: str
    imageURL: str
    sourceType: str
    title: str
    
class LoginReturnItem(BaseModel):    
    token_type: str
    access_token: str = None
    session_expires_time: datetime = None
    authenticated: bool = False
    scope: str = None
    
class ServerStatusItem(BaseModel):
    text_server_ok: bool = None
    db_server_ok: bool = None
    user_ip: str = None
    timeStamp: str = None
    
class SourceInfoListItem(BaseModel):    
    ISSN: str = None
    PEPCode: str = None
    abbrev: str = None
    bannerURL: str = None
    displayTitle: str = None
    language: str = None
    yearFirst: str = None
    yearLast: str = None
    sourceType: str = None
    title: str = None

class VolumeListItem(BaseModel):
    PEPCode: str = None
    vol: str = None
    year: str = None
    
class WhatsNewListItem(BaseModel):
    displayTitle: str = None
    abbrev: str = None
    volume: str = None
    issue: str = None
    year: str = None
    PEPCode: str = None
    srcTitle: str = None
    updated: str = None
    volumeURL: str = None
  
class SearchFormFields(BaseModel):
    quickSearch: str = None
    solrQ: str = None
    disMax: str = None
    edisMax: str = None
    partialDocumentID: str = None
    compoundQuery: bool = None
    wordsOrPhrases: str = None
    sourceWords: str = None
    sourceCodes: str = None
    sourceSet: str = None
    author: str = None
    title: str = None
    year: str = None
    startYear: str = None
    endYear: str = None
    citedTimes: int = None
    citedPeriod: int = None
    viewedTimes: int = None
    viewedPeriod: int = None
    articles: str = None
    paragraphs: str = None
    references: str = None
    referenceAuthors: str = None
    poems: str = None
    quotes: str = None
    dialogs: str = None
    quotes: str = None
    
#-------------------------------------------------------
#
# Top level schema structures
#
#-------------------------------------------------------
class AuthorPubListStruct(BaseModel):
    responseInfo: ResponseInfo 
    responseSet: List[AuthorPubListItem] = []

class AuthorPubList(BaseModel):
    authorPubList: AuthorPubListStruct

class AuthorIndexStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: List[AuthorIndexItem] = []

class AuthorIndex(BaseModel):
    authorIndex: AuthorIndexStruct

class DocumentListStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: List[DocumentListItem] = []

class DocumentList(BaseModel):
    documentList: DocumentListStruct
    
class Documents(BaseModel):        # this shouldnt be needed, should be able to use DocumentList. But for v1 API compat, included.
    documents: DocumentListStruct

class ImageURLListStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: List[ImageURLListItem] = []

class ImageURLList(BaseModel):
    imageURLList: ImageURLListStruct

class LicenseInfoStruct(BaseModel):
    responseInfo: ResponseInfoLoginStatus
    responseSet: LoginReturnItem = None

class LicenseStatusInfo(BaseModel):
    licenseInfo: LicenseInfoStruct 

class SourceInfoStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: List[SourceInfoListItem] = []

class SourceInfoList(BaseModel):
    sourceInfo: SourceInfoStruct

class VolumeListStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: List[VolumeListItem] = []   

class VolumeList(BaseModel):
    volumeList: VolumeListStruct
    
class WhatsNewListStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: List[WhatsNewListItem] = []   

class WhatsNewList(BaseModel):
    whatsNew: WhatsNewListStruct

if __name__ == "__main__":
    pass

