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

# import lxml
# from lxml import etree
import lxml.etree as ET
parser = ET.XMLParser(encoding='utf-8', recover=True, resolve_entities=False)

import opasConfig

import localsecrets
import opasFileSupport
#import opasArticleIDSupport
#import opasSolrLoadSupport
#import opasGenSupportLib as opasgenlib
#import opasXMLHelper as opasxmllib
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
import copy

def is_removed_version(ocd, art_id, verbose=None):
    """
    If it's in the articles_removed table, it's not.
    """
    ret_val = False
        
    select_old = f"""SELECT * from api_articles_removed
                    WHERE art_id RLIKE '{art_id}.?'
                  """
    vals = ocd.get_select_as_list_of_dicts(sqlSelect=select_old)
    if vals != []:
        ret_val = True
        
    return ret_val
    
def version_history_processing(artInfo, solrdocs, solrauth,
                               file_xml_contents,
                               full_filename_with_path,
                               testmode=False,
                               verbose=False):
    """
        This is designed for IJPOpen to store old (replaced) versions of manuscripts.
        The server will perform version process on these, and return an XML unit that can be appended to the compiled (processed) XML file.
        
        Parameters:
        artinfo  - is the artInfo object created by opasDataLoader
        solrdocs - is the opened, authorized pysolr object for the docs core
        solrauth - is the opened, authorized pysolr object for the authors core
        file_xml_contents - is not currently needed
        filename - should be the full name of the file, **including path**
        testmode - does the copying part of the action but does not do the deletions, so the tests may be repeated
        verbose - shows more messages during processing
        
        - The process works like this.  This IJPOPEN preprocessor will:
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
    
    def criteria(fileinfoobj):
        return fileinfoobj.basename
    
    def get_root_ver(name):
        ret_val = {}
        m = re.match("(?P<artid>(?P<root>.*?)(?P<ver>.))[\(].*", name)
        if m is not None:
            ret_val = {
                "root": m.group("root"),
                "version": m.group("ver"),
                "art_id": m.group("artid")
            }
        return ret_val
    
    ret_val = {
        "is_newest": False, 
        "newest_version": "A",
        "version_section": None, 
        "errors": False,
    }
    
    VERSION_STR_DTIME_FMT = "%Y/%m/%d %H:%M:%S"
    caller_name = "update_latest_version_info"
    target_article_id = artInfo.art_id
    art_id_no_suffix = target_article_id[:-1]
    filespec_regex = f"{art_id_no_suffix}.*\(bKBD3\).*"
    path = Path(full_filename_with_path)
    file_path = path.parent
    filenames = fs.get_matching_filelist(filespec_regex=filespec_regex, path=file_path)
    filenames_reversed = copy.copy(filenames)
    # figure out newest suffix
    filenames_reversed.sort(key=criteria, reverse=True) # ascending order
    newest_filename = filenames_reversed[0]
    newest_filename_info = get_root_ver(newest_filename.basename.upper())
    newest_version = newest_filename_info.get("version")
    ret_val["newest_version"] = newest_version
    if artInfo.art_id[-1] == newest_version:
        ret_val["is_newest"] = True
        # this is the newest version       
        if verbose:
            print(80*"-")
            print (f"\t...Updating IJPOpen old version references for {newest_filename.basename}")

    if len(filenames_reversed) > 1:
        print (f"\t...Checking for old versions from {start_folder}...")
        # go through prior versions
        for n in filenames: # not reverse order
            nm = get_root_ver(n.basename.upper())
            ver = nm.get("version")
            base = nm.get("root")
            art_id = nm.get("art_id")
            
            if ver == newest_version:
                continue

            prior_version_art_id = art_id
            # remove other common articles from articles_id
            
            if retrieve_specific_version_info(ocd, art_id, table="api_articles") != []:
                # still in api_articles
                if retrieve_specific_version_info(ocd, art_id, table="api_articles_removed") == []:
                    # not in removed table
                    success = copy_to_articles_removed(ocd, prior_version_art_id)
                    success = add_removed_article_filename_with_path(ocd, prior_version_art_id, full_filename_with_path, verbose=None)
                else:
                    if verbose:
                        print (f"\t...{art_id} has already been removed.")
                
                # in either case, need to remove from articles and the bibliotable
                ocd.delete_specific_article_data(prior_version_art_id)
                
                # now remove from solr
                success = solrdocs.delete(q=f"art_id:{prior_version_art_id}")
                success = solrauth.delete(q=f"art_id:{prior_version_art_id}")
                if not testmode:
                    try:
                        solrdocs.commit()
                        solrauth.commit()
                    
                    except Exception as e:
                        errStr = f"{caller_name}: Commit failed! {e}"
                        logger.error(errStr)
                        if opasConfig.LOCAL_TRACE: print (errStr)
                        ret_val["errors"] = True

    # now get the version history unit to return
    list_of_items = ""
    list_of_items_count = 0
    old_version_article_info = retrieve_removed_versions_info(ocd, art_id_no_suffix, verbose=verbose)
    
    # Perhaps the internal file date stored in the tables would be better.
    for n in old_version_article_info:
        tmz = dateutil.parser.isoparse(n["filedatetime"])
        tmz_str = tmz.strftime(VERSION_STR_DTIME_FMT)
        ver_art_id = n["art_id"]
        if ver_art_id[-1] == artInfo.art_id[-1]:
            add_note = " (This Version)"
        else:
            add_note = ""

        list_item = f'Manuscript Date: {tmz_str}'
        list_of_items_count += 1
        list_of_items += f"""<li><p><impx type='RVDOC' rx='{ver_art_id}'>{list_item}</impx>{add_note}</p></li>"""

    # Option to indicate newest version
    if list_of_items_count > 0:
        newest_art_id = art_id_no_suffix + newest_version
        lastmod = newest_filename.fileinfo["LastModified"]
        tmz_str = lastmod.strftime(VERSION_STR_DTIME_FMT)
        list_item = f'Manuscript Date: {tmz_str}'
        list_of_items_count += 1

        if artInfo.art_id[-1] != newest_version:
            # add note with link to newst version
            add_note = " (Newest Version)"
        else:
            add_note = " (This Version -- Newest Version)"
    
        list_item = f'Manuscript Date: {tmz_str}'
        list_of_items += f"""<li><p><impx type='RVDOC' rx='{newest_art_id}'>{list_item}</impx>{add_note}</p></li>"""
        

    if list_of_items != "": 
        ijpopen_addon = f"""
           <unit type="previousversions">
                <h1>{DOCUMENT_UNIT_NAME}</h1>
                <list type="BUL1">
                {list_of_items}
                </list>
            </unit>
        """
        ret_val["version_section"] = ET.fromstring(ijpopen_addon, parser)

    # Return None, or the new ET_Val unit to be appended
    return ret_val

def add_removed_article_xml(ocd, art_id, xml_filecontents, verbose=False):
    """
    Adds the XML data from the file to the articles_removed table
    
    Not currently used or needed
    
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

def add_removed_article_filename_with_path(ocd, art_id, filename_with_path, verbose=False):
    """
    Adds the XML data from the file to the articles_removed table.  The field which
     normally, in api_articles, has only the filename, is updated to have the complete file path.
     This is needed to facilitate reloading the file upon the archival endpoint call for
     that id.
    
    """
    ret_val = False
    caller_name = "addRemovedArticleFilename"
    msg = f"\t...Updating record to add full file path to api_articles_removed."
    logger.info(msg)
    if verbose:
        print (msg)
    
    ocd.open_connection(caller_name=caller_name)
    sqlcpy = f"""
                UPDATE api_articles_removed
                    SET filename = %s
                    WHERE art_id = %s
              """
    
    query_params = (filename_with_path, art_id )

    try:
        res = ocd.do_action_query(querytxt=sqlcpy, queryparams=query_params)
    except Exception as e:
        errStr = f"{caller_name}: update error {e}"
        logger.error(errStr)
        if opasConfig.LOCAL_TRACE: print (errStr)
    else:
        ret_val = True

    
    return ret_val  # return True for success

def retrieve_specific_version_info(ocd, art_id, table="api_articles_removed", verbose=False):
    """
    Return a list of removed records
    """
    ret_val = []
    select_old = f"""SELECT * from {table}
                    WHERE art_id = '{art_id}'
                  """

    ret_val = ocd.get_select_as_list_of_dicts(sqlSelect=select_old)
    return ret_val

def retrieve_removed_versions_info(ocd, art_id_no_suffix, verbose=False):
    """
    Return a list of removed records
    """
    ret_val = []
    select_old = f"""SELECT * from api_articles_removed
                    WHERE art_id RLIKE '{art_id_no_suffix}.'
                  """

    ret_val = ocd.get_select_as_list_of_dicts(sqlSelect=select_old)
    return ret_val

def copy_to_articles_removed(ocd, art_id, verbose=None):
    """
    Removes the article data for a single document from the api_articles table 
      and copies it to the api_articles_removed table
    
    """
    ret_val = False
    caller_name = "copyArticle"
    msg = f"\t...Copying api_articles record to api_articles_removed."
    logger.info(msg)
    if verbose:
        print (msg)
    
    # ocd.open_connection(caller_name=caller_name)
    sqlcpy = f"""
                insert into api_articles_removed
                    select * from api_articles where art_id='{art_id}'
              """
    
    try:
        res = ocd.do_action_query(querytxt=sqlcpy, log_integrity_errors=False)
    except Exception as e:
        errStr = f"AddToArticlesDBError: insert error {e}"
        logger.error(errStr)
        if opasConfig.LOCAL_TRACE:
            print (errStr)
    else:
        ret_val = True
   
    return ret_val  # return True for success
    
def remove_from_articles(ocd, art_id, verbose=None):
    """
    Removes the article data for a single document from the api_articles table
    
    """
    ret_val = False
    caller_name = "removeArticle"
    msg = f"\t...Removing api_articles record."
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
        errStr = f"DeleteArticlesDBError: delete error {e}"
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