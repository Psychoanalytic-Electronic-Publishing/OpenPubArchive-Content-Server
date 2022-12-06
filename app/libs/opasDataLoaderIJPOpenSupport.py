#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
# Disable many annoying pylint messages, warning me about variable naming for example.
# yes, in my Solr code I'm caught between two worlds of snake_case and camelCase.

""" 
OPAS - opasSolrLoadSupport  

"""
import sys
sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')

import os
import string
import re
import time
import mysql
import dateutil
# from datetime import datetime
from pathlib import Path

import lxml
from lxml import etree
import lxml.etree as ET
parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=False)

from configLib.opasIJPConfig import IJPOPENISSUES
import opasConfig

import localsecrets
import opasFileSupport
import opasArticleIDSupport
#import opasSolrLoadSupport
import opasGenSupportLib as opasgenlib
import opasXMLHelper as opasxmllib
import logging
logger = logging.getLogger(__name__)

# new for processing code
import opasCentralDBLib
import PEPJournalData
jrnlData = PEPJournalData.PEPJournalData()
ocd =  opasCentralDBLib.opasCentralDB()
fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root=localsecrets.FILESYSTEM_ROOT)
start_folder = localsecrets.XML_ORIGINALS_PATH + "/IJPOPEN"
DOCUMENT_UNIT_NAME = "PEP-Web Manuscript Version History"

def is_removed_version(ocd, art_id, verbose=None):
    """
    If it's in the articles_removed table, it's not.
    """
    ret_val = False
        
    select_old = f"""SELECT * from api_articles_removed
                    WHERE art_id RLIKE '{art_id}.'
                  """
    vals = ocd.get_select_as_list_of_dicts(sqlSelect=select_old)
    if vals != []:
        ret_val = True
        
    return ret_val
    
def version_history_processing(artInfo, solrdocs, solrauth, file_xml_contents, filename, testmode=False, verbose=False):
    """
        - This is designed for IJPOpen
        - The server will perform version process on these, and return an XML unit that can be appended to the compiled (processed) XML file.
        - This IJPOPEN preprocessor will:
           - look for the most recent version of the file that's described in artInfo.  
           - For all the older files, it will: 
               - copy the api_articles table info for each to api_articles_removed.
               - delete the api_articles table info for the removed article
               - In the "newest" article, it will build a version_history_unit (to be returned from this function) in XML, which will consist of:
                   - The unit, "PEP-Web Manuscript Version List" (set this in DOCUMENT_UNIT_NAME will include a list with the article id, date and manuscript number
                   - a list of the older files 
                   - impx around each item in the list to a special API function to retrieve the contents of "removed versions"such that the client could present each if the user clicks.
           - A special API call will be added comparable to the v2/documents/document endpoint to retrieve the XML for these (or the document endpoint will be extended)
           - To get the XML for these, the client will make the new API call.
    
    Database and Solr Change Requirements:
        - A new table with the exact same structure as api_articles is added to track removed articles...api_articles_removed
        - An extra field with the manuscript ID is added to api_articles and api_articles_removed in order to supply that
          in the version history list without reading the older file xml
        - No Solr changes required (though see "future" below)
        - The manuscript ID should be supplied in meta/adldata per this example data (the other adldata fields are not required if they are not available)
          <meta>
           <adldata>
               <adlfield>submission-date</adlfield>
               <adlval>2021-11-12</adlval>
           </adldata>
           <adldata>
               <adlfield>region</adlfield>
               <adlval>Europe</adlval>
           </adldata>
           <adldata>
               <adlfield>assigned-editor</adlfield>
               <adlval>Beatriz de Leon de Bernardi</adlval>
           </adldata>
           <adldata>
               <adlfield>author-country</adlfield>
               <adlval>Portugal</adlval>
           </adldata>
           <adldata>
               <adlfield>submitting-language</adlfield>
               <adlval>Portuguese</adlval>
           </adldata>
            <adldata>
                <adlfield>manuscript-id</adlfield>
                <adlval>IJPOPEN.2022-43111</adlval>
            </adldata>
          </meta>
     
    Via this method:
       - Any newly processed (input XML type) file for IJPOpen will be checked for old versions
       - Since, if there are old versions, only the output XML file is modified, it is automatically included on subsequent "loads"
       - If there are no old versions, nothing is changed in the processing, except manuscript id is added to api_articles and artInfo
       - Over time:
         - Since all versions stay as authored,
            - When the second version is added, it will include the new version unit pointing to the first version.
              The first version will be removed from api_articles and Solr and api_articles so it won't appear in searches
              but not the filesystem.
            - When the third version is added, it will scan the file system and include the new version unit
              pointing to both the first and second versions.  It will remove the second version from Solr
              and api_articles so it won't appear in searches.
    
    For the future:
       - The code now also parses the meta/adldata fields and adds all the fields to the artInfo structure for later use if needed.
    
    """
    ret_val = None
    caller_name = "update_latest_version_info"
    manuscript_id = artInfo.publisher_ms_id
    target_article_id = artInfo.art_id
    if artInfo.art_id[-1] != "A":
        # this is a new version
        
        path = Path(filename)
        file_path = path.parent
        if verbose:
            print(80*"-")
            print ("\t...Updating IJPOpen version references")
            
        target_article = opasArticleIDSupport.ArticleID(articleID=target_article_id)
        art_id_no_suffix = target_article.articleID[:-1]
        
        print (f"\t...Checking for old versions from {start_folder}...")
        filespec_regex = f"{art_id_no_suffix}.*\(bKBD3\).*"
        #article_ids_in_target_folder = ""
        filenames = fs.get_matching_filelist(filespec_regex=filespec_regex, path=file_path)
        for n in filenames:
            nm = n.basename
            nroot = nm[:nm.find('(')]
            prior_version_art_id = nroot.upper()
            # rename article KBD3
            #  TBD LATER - easier for testing this way
            # rename article EXP_ARCH1
            #  TBD LATER - easier for testing this way
            # remove other common articles from articles_id
            if target_article_id == prior_version_art_id:
                # this is the new article...skip it.
                continue
            success = copy_to_articles_removed(ocd, prior_version_art_id)
            if success:
                #this is not needed now, can delete xml field!
                #success = add_removed_article_xml(ocd, prior_version_art_id, file_xml_contents, verbose=None)
                success = remove_from_articles(ocd, prior_version_art_id)
                success = solrdocs.delete(q=f"art_id:{prior_version_art_id}")
                success = solrauth.delete(q=f"art_id:{prior_version_art_id}")
                    
            if success and not testmode: # success:
                try:
                    solrdocs.commit()
                    solrauth.commit()
                    
                except mysql.connector.Error as e:
                    errStr = f"{caller_name}: Commit failed! {e}"
                    logger.error(errStr)
                    if opasConfig.LOCAL_TRACE: print (errStr)
                    ret_val = False

        # TBD - remove prior article version from Solr

        # now get the version history unit to return
        old_version_article_info = retrieve_removed_versions_info(ocd, art_id_no_suffix, verbose=verbose)
        list_of_items = ""
        for n in old_version_article_info:
            tmz = dateutil.parser.isoparse(n["filedatetime"])
            tmz_str = tmz.strftime("%Y/%m/%d")
            ver_art_id = n["art_id"]
            list_item = f'{ver_art_id}: {tmz_str} {manuscript_id}'
            list_of_items += f"""<li><p><impx type='RVDOC' rx='{ver_art_id}'>{list_item}</impx></p></li>"""

        if list_of_items != "": 
            ijpopen_addon = f"""
               <unit type="previousversions">
                    <h1>{DOCUMENT_UNIT_NAME}</h1>
                    <list>
                    {list_of_items}
                    </list>
                </unit>
            """
            ret_val = ET.fromstring(ijpopen_addon, parser)
            if verbose:
                print("\t...Added PEP-Web Manuscript history unit to compiled XML")

        # query solr for all records with this artid base
        # figure out the most recent one
        # update all of the artquals to point to the most recent one, except the most recent one. [maybe]
        # no need to touch the files or other fields
        
        # query Solr, get other document records...or maybe just write them?
        # update other record art_qual with this art_id
        print((80*"-"))
    # Return None, or the new ET_Val unit to be appended
    return ret_val

def add_removed_article_xml(ocd, art_id, xml_filecontents, verbose=None):
    """
    Adds the XML data from the file to the articles_removed table
    
    Not needed or used at the moment
    
    """
    ret_val = False
    caller_name = "addRemovedArticleXML"
    msg = f"\t...Copying api_articles record to api_articles_removed."
    logger.info(msg)
    if verbose:
        print (msg)
    
    ocd.open_connection(caller_name=caller_name)
    sqlcpy = f"""
                UPDATE api_articles_removed
                    SET art_xml = %s
                    WHERE art_id = %s
              """
    
    query_params = (xml_filecontents, art_id )

    try:
        res = ocd.do_action_query(querytxt=sqlcpy, queryparams=query_params)
    except Exception as e:
        errStr = f"{caller_name}: update error {e}"
        logger.error(errStr)
        if opasConfig.LOCAL_TRACE: print (errStr)
    else:
        ret_val = True

    
    return ret_val  # return True for success

def retrieve_removed_versions_info(ocd, art_id_no_suffix, verbose=False):
    """
    Return a list of removed records
    """
    ret_val = []
    caller_name = "fetchOldVersions"
        
    select_old = f"""SELECT * from api_articles_removed
                    WHERE art_id RLIKE '{art_id_no_suffix}.'
                  """

    ret_val = ocd.get_select_as_list_of_dicts(sqlSelect=select_old)
    return ret_val

def copy_to_articles_removed(ocd, art_id, verbose=None):
    """
    Removes the article data for a single document from the api_articles table in mysql database opascentral
      and copies it to the api_articles_removed table
    
    """
    ret_val = False
    caller_name = "removeArticle"
    msg = f"\t...Copying api_articles record to api_articles_removed."
    logger.info(msg)
    if verbose:
        print (msg)
    
    ocd.open_connection(caller_name=caller_name)
    sqlcpy = f"""
                insert into api_articles_removed
                    select * from api_articles where art_id='{art_id}'
              """
    
    try:
        res = ocd.do_action_query(querytxt=sqlcpy, log_integrity_errors=False)
    except Exception as e:
        sql_error_nbr = str(e.msg)[0:4]
        if sql_error_nbr == "1062":
            pass # duplicate, integrity error.  Ok.
            ret_val = True
        else:
            errStr = f"AddToArticlesDBError: insert error {e}"
            logger.error(errStr)
            if opasConfig.LOCAL_TRACE: print (errStr)
    else:
        ret_val = True
   
    return ret_val  # return True for success
    
def remove_from_articles(ocd, art_id, verbose=None):
    """
    Removes the article data for a single document from the api_articles table in mysql database opascentral
      and copies it to the api_articles_removed table
    
    """
    ret_val = False
    caller_name = "removeArticle"
    msg = f"\t...Copying api_articles record to api_articles_removed."
    logger.info(msg)
    if verbose:
        print (msg)
    
    ocd.open_connection(caller_name=caller_name)
    sqldel = f"""
                DELETE from api_articles
                    WHERE art_id='{art_id}'
              """
    try:
        res = ocd.do_action_query(querytxt=sqldel)
    except Exception as e:
        errStr = f"AddToArticlesDBError: delete error {e}"
        logger.error(errStr)
        if opasConfig.LOCAL_TRACE: print (errStr)
    else:
        if verbose:
            print ("\t...Old Version deleted from articles")

    try:
        ocd.db.commit()
        ocd.close_connection(caller_name=caller_name)
    except mysql.connector.Error as e:
        errStr = f"SQLDatabaseError: Commit failed! {e}"
        logger.error(errStr)
        if opasConfig.LOCAL_TRACE: print (errStr)
        ret_val = False
    
    return ret_val  # return True for success
   
#-----------------------------------------------------------------------------
if __name__ == "__main__":
    sys.path.append('./config') 

    print (40*"*", "opasDataLoaderIJPOpenSupport Tests", 40*"*")
    print ("Running in Python %s" % sys.version_info[0])
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
    IJPOPENTEST = "X:\IJPOpenTest"

    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)

    print ("All tests complete!")
    print ("Fini")    