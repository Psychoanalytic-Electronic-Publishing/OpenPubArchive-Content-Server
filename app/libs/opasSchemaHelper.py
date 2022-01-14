#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326

"""
opasSchemaHelper

2020.0821.1 - First version

"""
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2020.0821.1"
__status__      = "Development"

# import re
import requests
from requests.auth import HTTPBasicAuth 
from localsecrets import SOLRUSER, SOLRPW, SOLRURL

import models
# import opasCentralDBLib

import logging
logger = logging.getLogger(__name__)

# import schemaMap
# import opasConfig
from configLib.opasCoreConfig import EXTENDED_CORES

def direct_endpoint_call(endpoint, base_api=None):
    if base_api == None:
        base_api = SOLRURL
        
    ret_val = base_api + endpoint
    return ret_val


# -------------------------------------------------------------------------------------------------------
def solr_field_check(core, field_name):
    """
    Check the existence of a field_name using the Solr schema API
    
    >>> solr_field_check("pepwebdocs", "art_id")
    (True, {'name': 'art_id', 'type': 'string', 'indexed': True, 'stored': True, 'docValues': True, 'termVectors': False, 'termPositions': False, 'termOffsets': False, 'termPayloads': False, 'omitNorms': True, 'omitTermFreqAndPositions': True, 'omitPositions': False, 'storeOffsetsWithPositions': False, 'multiValued': False, 'large': False, 'uninvertible': True, 'sortMissingLast': True, 'required': False, 'tokenized': False, 'useDocValuesAsStored': True})

    >>> solr_field_check("pepwebdocs", "art_ixxx")
    (False, None)
    """
    ret_val = False, None
    try:
        endpoint = f"{core}/schema/fields/{field_name}/?showDefaults=true"
        
        apicall = direct_endpoint_call(endpoint, SOLRURL)
        if SOLRUSER is not None:
            response = requests.get(apicall, auth=HTTPBasicAuth(SOLRUSER, SOLRPW))
        else:
            response = requests.get(apicall)

        if response.status_code == 200:
            r = response.json()
            try:
                if r["field"]["name"] == field_name:
                    isvalid = True
                    info = r["field"]
                else:
                    isvalid = False
            except KeyError:
                isvalid = False
                info = None
        else:
            isvalid = False
            info = f"Error checking schema {response.status_code}"
            logger.error(info)
            
    except Exception as e:
        isvalid = False
        info = f"Error checking schema {e}"
        logger.error(info)
        
    ret_val = isvalid, info

    return ret_val

# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    import sys
    print ("Running in Python %s" % sys.version_info[0])
    SOLR_DOCS = "pepwebdocs"

    #import pysolr
    #solr_docs_schema = pysolr.Solr(SOLRURL + SOLR_DOCS + "/schema/fields/", auth=(SOLRUSER, SOLRPW))
    #solr_docs_schema.search_handler.

    
    import doctest
    doctest.testmod()
    print ("Fini. OpasSchemaHelper Tests complete.")
    sys.exit()
    
