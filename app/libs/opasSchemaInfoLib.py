#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326

"""
schemaInfoLib

This library is meant to support query to Solr

"""
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2021.0607.1"
__status__      = "Development"

#import re
#import os
import sys
import logging
logger = logging.getLogger(__name__)
import json

# import localsecrets

# from localsecrets import BASEURL, SOLRURL, SOLRUSER, SOLRPW, DEBUG_DOCUMENTS, SOLR_DEBUG, CONFIG, COOKIE_DOMAIN  
# import starlette.status as httpCodes
from configLib.opasCoreConfig import solr_call, SOLR_DOCS # , SOLR_GLOSSARY, SOLR_AUTHORS

def get_field_names(core=SOLR_DOCS):
    """
    Return a list of field names
    
    >>> names = get_field_names()
    >>> len(names) >= 180
    True
    >>> names = get_field_names(SOLR_GLOSSARY)
    >>> len(names) >= 22
    True
    
    """
    ret_val = []
    logger.debug(f"Core selection: {core}.")
    solr_path = f"/{core}/schema/fields"    
    try:
        results = solr_call._send_request("get", path=solr_path)
    except Exception as e:
        logger.error(f"Field name fetch exception: {e}")
    else:
        try:
            field_results = json.loads(results)
        except Exception as e:
            logger.error(f"JSON convert exception: {e}")
        else:
            fields = field_results["fields"]
            for n in fields:
                if n["name"][0] != "_":
                    ret_val.append(n["name"])
                
    return ret_val

class SchemaInfo:
    """
    Get schema info dynamically and store a copy in class instance.
    
    >>> si = SchemaInfo()
    >>> si.field_in_schema("art_sourcecode")
    True
    """
    doc_fields = []
    
    def __init__(self):
        self.doc_fields = get_field_names()
    
    def __str__(self):
        ret_val = ' '.join([str(elem) for elem in self.doc_fields])
        return ret_val
    
    def field_in_schema(self, field_name, core=SOLR_DOCS):
        """
        """
        ret_val = False
        if core == SOLR_DOCS:
            ret_val = field_name in self.doc_fields
        
        return ret_val


#-----------------------------------------------------------------------------
if __name__ == "__main__":
    sys.path.append('./config') 

    logger = logging.getLogger(__name__)
    # extra logging for standalong mode 
    logger.setLevel(logging.WARN)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARN)
    # create formatter
    formatter = logging.Formatter('%(asctime)s %(name)s %(lineno)d - %(levelname)s %(message)s')    
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)
    docschemainfo = SchemaInfo()
    print (docschemainfo)

    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
    print ("All tests complete!")
    print ("Fini")
