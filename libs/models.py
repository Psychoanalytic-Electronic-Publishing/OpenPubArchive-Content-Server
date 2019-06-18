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

from pydantic import BaseModel
from pydantic.types import EmailStr

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
    sourceInfoList = "sourceinfolist"
    whatsNewList = "newlist"
    mostCitedList = "mostcited"
    
    
class ResponseInfo(BaseModel):
    count: int = 0
    limit: int = None
    offset: int = None
    fullCount: int = None
    fullCountComplete: bool = None
    listLabel: str = None
    listType: ListTypeEnum = None
    scopeQuery: str = None
    request: str = None
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
    year: str = None
    documentURL: str = None
    score: float = None
    
class DocumentListItem(BaseModel):
    PEPCode: str
    authorMast: str = None
    documentID: str = None
    documentRef: str = None
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
    score: float = None
    instanceCount: int = None
    
class ImageURLListItem(BaseModel):    
    PEPCode: str
    imageURL: str
    sourceType: str
    title: str
    
class SourceInfoListItem(BaseModel):    
    ISSN: str = None
    PEPCode: str = None
    abbrev: str = None
    bannerURL: str = None
    displayTitle: str = None
    language: str = None
    yearFirst: str = None
    yearLast: str = None
    sourceType: str
    title: str   

class VolumeListItem(BaseModel):
    PEPCode: str
    vol: str
    year: str = None
    
class WhatsNewListItem(BaseModel):
    displayTitle: str
    volume: str = None
    issue: str = None
    year: str = None
    PEPCode: str = None
    srcTitle: str = None
    updated: str = None
    volumeURL: str = None
    timestamp: str = None
  
    

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

class ImageURLListStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: List[ImageURLListItem] = []

class ImageURLList(BaseModel):
    imageURLList: ImageURLListStruct

class SourceInfoStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: List[SourceInfoListItem] = []

class SourceInfoList(BaseModel):
    sourceInfoList: SourceInfoStruct

class VolumeListStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: List[VolumeListItem] = []   

class VolumeList(BaseModel):
    volumeList: VolumeListStruct
    
class WhatsNewListStruct(BaseModel):
    responseInfo: ResponseInfo
    responseSet: List[WhatsNewListItem] = []   

class WhatsNewList(BaseModel):
    whatsNewList: WhatsNewListStruct

if __name__ == "__main__":
    pass

