#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initial version of the Opas Solr Server (API) 

This API server is based on the existing PEP-Web API 1.0.  The data returned 
may have additional fields but should be otherwise compatible with PEP API clients
such as PEP-Easy.

2019.0617.1 - First version with 6 endpoints, 5 set up for Pydantic and one not yet
                converted - nrs

Run with:
    uvicorn main:app --reload
    
    or for debug:
    
    uvicorn main:app --debug --log-level=debug
 
(Debug set up in this file as well: app = FastAPI(debug=True))
                
Supports:
   /v1/Metadata/MostCited
   /v1/Metadata/Contents/{PEPCode}
   /v1/Metadata/Volumes/{PEPCode}
   /v1/Authors/Index/{authorNamePartial}
   /v1/Authors/Publications/{authorNamePartial}
   
   and this preliminary, not yet ported to Pydantic

   ​/Documents​/Abstracts​/{documentID}​/Getabstract
   
Endpoint and structure documentation automatically available when server is running at:

  http://127.0.0.1:8000/docs

(base URL + "/docs")

"""

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2019.0617.1"
__status__      = "Development"

import sys

sys.path.append('../libs')

from enum import Enum
import uvicorn
from fastapi import FastAPI, Query, Path, Cookie, Header
from starlette.requests import Request
from pydantic import BaseModel
from pydantic.types import EmailStr

import pysolr
import json
import logging
#import imp
import opasAPISupportLib

#opasxmllib = imp.load_source('opasxmllib', '../libs/opasXMLHelper.py')
#SourceInfoDB = imp.load_source('sourceInfoDB', '../libs/sourceInfoDB.py')

solr = pysolr.Solr('http://localhost:8983/solr/pepwebproto', timeout=10)
import models

app = FastAPI(debug=True)

@app.get("/v1/Metadata/MostCited/", response_model=models.DocumentList)
def getMostCited(request: Request, limit: int = 10, offset: int = 0):
    """
    Return a list of documents for a PEPCode source (and optional year specified in query params).  
    
    Note: The GVPi implementation does not appear to support the limit and offset parameter
    
    Status: this endpoint is working.     
    
    """
    
    retVal = documentList = opasAPISupportLib.databaseGetMostCited(limit=limit, offset=offset)
    # fill in additional return structure status info
    client_host = request.client.host
    retVal.documentList.responseInfo.request = request.url._url

    return retVal


@app.get("/v1/Metadata/Contents/{PEPCode}/", response_model=models.DocumentList)
def getContents(PEPCode: str, request: Request, year: str = "*", limit: int = 15, offset: int = 0):
    """
    Return a list of documents for a PEPCode source (and optional year specified in query params).  
    
    Note: The GVPi implementation does not appear to support the limit and offset parameter
    
    Status: this endpoint is working.  
    
    """
    
    retVal = documentList = opasAPISupportLib.metadataGetContents(PEPCode, year, limit=limit, offset=offset)
    # fill in additional return structure status info
    client_host = request.client.host
    retVal.documentList.responseInfo.request = request.url._url

    return retVal

@app.get("/v1/Metadata/Volumes/{PEPCode}/", response_model=models.VolumeList)
def getVolumeIndex(PEPCode: str, request: Request, limit: int = 15, offset: int = 0):
    """
    Return a list of volumes for a PEPCode (e.g., IJP) per the limit and offset parameters 
    
    Status: this endpoint is working.
    
    Sample Call:
       http://localhost:8000/v1/Metadata/Volumes/CPS/
       
    """
    
    #print ("caller limit = %s, offset = %s" % (limit, offset))

    retVal = volumeList = opasAPISupportLib.metadataGetVolumes(PEPCode, limit=limit, offset=offset)
    
    # fill in additional return structure status info
    client_host = request.client.host
    retVal.volumeList.responseInfo.request = request.url._url

    return retVal
#-----------------------------------------------------------------------------
@app.get("/v1/Authors/Index/{authorNamePartial}/", response_model=models.AuthorIndex)
def getAuthorsIndex(authorNamePartial: str, request: Request, limit: int = 15, offset: int = 0):
    """
    ## /v1/Authors/Index/{authorNamePartial}/
    ## Function
    Return a list (index) of authors.  The list shows the author IDs, which are a normalized form of an authors name.
    
    ## Return Type
    authorindex

    ## Status
    This endpoint is working.

    ## Sample Call
       http://localhost:8000/v1/Authors/Index/Tuck/


    """

    retVal = opasAPISupportLib.authorsGetAuthorInfo(authorNamePartial, limit=limit, offset=offset)

    # fill in additional return structure status info
    client_host = request.client.host
    retVal.authorIndex.responseInfo.request = request.url._url

    return retVal

#-----------------------------------------------------------------------------
@app.get("/v1/Authors/Publications/{authorNamePartial}/", response_model=models.AuthorPubList)
def getAuthorsPublications(authorNamePartial: str, request: Request, limit: int = 15, offset: int = 0):
    """
    ## /v1/Authors/Publications/{authorNamePartial}/
    ## Function
    Return a list of the author's publications.  
    
        ## Return Type
    authorPubList

    ## Status
    This endpoint is working.
    
    ## Sample Call
       http://localhost:8000/v1/Authors/Publications/Tuck/

    """

    retVal = opasAPISupportLib.authorsGetAuthorPublications(authorNamePartial, limit=limit, offset=offset)

    # fill in additional return structure status info
    client_host = request.client.host
    retVal.authorPubList.responseInfo.request = request.url._url
    
    return retVal

@app.get("/Documents/Abstracts/{documentID}/")
def getAbstract(documentID):
    retVal = opasAPISupportLib.getDocumentAbstracts(documentID)

    return retVal

    
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)