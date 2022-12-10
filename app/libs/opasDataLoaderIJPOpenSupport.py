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

import localsecrets
import opasFileSupport
import opasConfig

import lxml
from lxml import etree
import lxml.etree as ET
parser = ET.XMLParser(encoding='utf-8', recover=True, resolve_entities=False)
import opasXMLHelper as opasxmllib


#import opasArticleIDSupport
#import opasSolrLoadSupport
#import opasGenSupportLib as opasgenlib
#import opasXMLHelper as opasxmllib
import logging
logger = logging.getLogger(__name__)

# new for processing code
import opasCentralDBLib
import opasArticleIDSupport
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

    
    def get_metadata_dict(fullfilename):
        fileXMLContents, input_fileinfo = fs.get_file_contents(fullfilename)
        parsed_xml = etree.fromstring(opasxmllib.remove_encoding_string(fileXMLContents), parser)
        root = parsed_xml.getroottree()
        ret_val = {}
        adldata_list = root.findall('meta/adldata')
        for adldata in adldata_list:
            fieldname = adldata[0].text
            fieldvalue = adldata[1].text
            ret_val[fieldname] = fieldvalue 

        return ret_val # metadata dict
        
    ret_val = {
        "is_newest": False, 
        "newest_version": "A",
        "version_section": None, 
        "errors": False,
    }
    
    caller_name = "update_latest_version_info"
    this_article_id = artInfo.art_id
    this_version = artInfo.art_id[-1]
    this_article_id_no_suffix = this_article_id[:-1]
    filespec_regex = f"{this_article_id_no_suffix}.*\(bKBD3\).*"
    path = Path(full_filename_with_path)
    file_path = path.parent
    filenames = fs.get_matching_filelist(filespec_regex=filespec_regex, path=file_path)
    
    # if there's only one file, there's no older versions.  So we can skip this.
    if len(filenames) <= 1:
        ret_val["is_newest"] = True
    else:
        print (f"\t...Checking for old versions from {start_folder}...")
        filenames_reversed = copy.copy(filenames)
        filenames_reversed.sort(key=criteria, reverse=True) # ascending order
        newest_filename = filenames_reversed[0]
        newest_version_info = get_root_ver(newest_filename.basename.upper())
        newest_version_info["fullfilename"] = newest_filename.filespec
        ret_val["newest_version"] = newest_version_info["version"]
        if newest_version_info.get("version") != this_version:
            # get newest manuscript date to put in this version
            metadata_dict = get_metadata_dict(newest_filename.filespec)
            #publisher_ms_id = metadata_dict.get("manuscript-id", "")
            newest_manuscript_date_str = metadata_dict.get("submission-date", "")
            # newest_version_info = retrieve_specific_version_info(ocd, newest_art_id, table="api_articles")

        if 1:
            if this_version == newest_version_info["version"]:
                ret_val["is_newest"] = True
                # this is the newest version       
                if verbose:
                    print (f"\t...Newest Version. Updating IJPOpen old version references for {newest_filename.basename}")
    
            # go through all versions
            for removed_ver in filenames: # not reverse order
                nm = get_root_ver(removed_ver.basename.upper())
                current_file_ver = nm.get("version")
                base = nm.get("root")
                art_id = nm.get("art_id")
                
                if current_file_ver == newest_version_info["version"]:
                    continue
    
                prior_version_art_id = art_id
                
                # if still in api_articles, move to api_articles_removed, and delete from solr
                if retrieve_specific_version_info(ocd, art_id, table="api_articles") != []:
                    # in artinfo table, so copy and remove
                    success = copy_to_articles_removed(ocd, prior_version_art_id)
                    #success = add_removed_article_filename_with_path(ocd, prior_version_art_id, full_filename_with_path, verbose=None)
                else:
                    # not in api_articles. Add it manually to removed
                    if retrieve_specific_version_info(ocd, art_id, table="api_articles_removed") == []:
                        # not in removed table, add the basic info we need
                        removed_ver.artInfo = get_article_info(art_id, removed_ver.basename, removed_ver.filespec)
                        success = add_to_articles_removed_table_fullinfo(ocd, artInfo)
                        # metadata_dict = get_metadata_dict(removed_ver.filespec)
                        #publisher_ms_id = metadata_dict.get("manuscript-id", "")
                        # newest_manuscript_date_str = metadata_dict.get("submission-date", "")
                    else:    
                        if verbose: print (f"\t...{art_id} has already been removed.")
                    
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
    
        #  ##############################################################################################
        #  build version history for end of file, include all versions
        #  ##############################################################################################
        parsed_version_section = build_version_history_section(ocd, this_article_id_no_suffix, verbose)
        ret_val["version_section"] = parsed_version_section

    # Return None, or the new ET_Val unit to be appended
    return ret_val

def add_removed_article_xml(ocd, artInfo, verbose=False):
    """
    Adds the XML data from the file to the articles_removed table
    """
    ret_val = False
    caller_name = "addRemovedArticleXML"
    msg = f"\t...Adding api_articles record to api_articles_removed."
    logger.info(msg)
    if verbose:
        print (msg)
    
    ocd.open_connection(caller_name=caller_name)
    insert_if_not_exists = r"""REPLACE
                               INTO api_articles (
                                    art_id,
                                    fullfilename,
                                    manuscript_date_str,
                                    filename,
                                    filedatetime
                                    )
                                values (
                                        %(art_id)s,
                                        %(fullfilename)s,
                                        %(manuscript_date_str)s,
                                        %(filename)s,
                                        %(filedatetime)s
                                        );
                            """

    query_params = {
        "art_id": artInfo.art_id,
        "fullfilename" : artInfo.fullfilename,
        "filename":  artInfo.filename,
        "manuscript_date_str" : artInfo.manuscript_date_str,
        "filedatetime": artInfo.filedatetime
    }

    # string entries above must match an attr of the art_info instance.
    #query_param_dict = art_info.__dict__.copy()
    # the element objects in the author_xml_list cause an error in the action query 
    # even though that dict entry is not used.  So removed in a copy.
    #query_param_dict["author_xml_list"] = None
        
    try:
        res = ocd.do_action_query(querytxt=insert_if_not_exists, queryparams=query_params)
    except Exception as e:
        errStr = f"AddToArticlesDBError: insert error {e}"
        logger.error(errStr)
        if opasConfig.LOCAL_TRACE: print (errStr)
    else:
        ret_val = True
        
    try:
        ocd.db.commit()
        ocd.close_connection(caller_name="processArticles")
    except mysql.connector.Error as e:
        errStr = f"SQLDatabaseError: Commit failed! {e}"
        logger.error(errStr)
        if opasConfig.LOCAL_TRACE: print (errStr)
        ret_val = False
    
    return ret_val  # return True for success

def add_to_articles_removed_table_fullinfo(ocd, artInfo, verbose=None):
    """
    Adds the article data from a single document to the api_articles table in mysql database opascentral.
    
    This database table is used as the basis for
     
    Note: This data is in addition to the Solr pepwebdocs core which is added elsewhere.  The SQL table is
          currently primarily used for the crosstabs rather than API queries, since the Solr core is more
          easily joined with other Solr cores in queries.  (TODO: Could later experiment with bridging Solr/SQL.)
      
    """
    ret_val = False
    msg = f"\t...Loading metadata to Articles Removed."
    logger.info(msg)
    if verbose:
        print (msg)
    
    ocd.open_connection(caller_name="add_to_articles_removed_table")
    
    # reduce object
  
    insert_if_not_exists = r"""REPLACE
                               INTO api_articles_removed (
                                    art_id,
                                    art_doi,
                                    art_type,
                                    art_lang,
                                    art_kwds,
                                    art_auth_mast,
                                    art_auth_citation,
                                    art_title,
                                    src_title_abbr,
                                    src_code,
                                    art_year,
                                    art_vol,
                                    art_vol_str,
                                    art_vol_suffix,
                                    art_issue,
                                    art_pgrg,
                                    art_pgstart,
                                    art_pgend,
                                    main_toc_id,
                                    start_sectname,
                                    bk_info_xml,
                                    bk_title,
                                    bk_publisher,
                                    art_citeas_xml,
                                    art_citeas_text,
                                    ref_count,
                                    fullfilename,
                                    manuscript_date_str,
                                    filename,
                                    filedatetime
                                    )
                                values (
                                        %(art_id)s,
                                        %(art_doi)s,
                                        %(art_type)s,
                                        %(art_lang)s,
                                        %(art_kwds)s,
                                        %(art_auth_mast)s,
                                        %(art_auth_citation)s,
                                        %(art_title)s,
                                        %(src_title_abbr)s,
                                        %(src_code)s,
                                        %(art_year)s,
                                        %(art_vol_int)s,
                                        %(art_vol_str)s,
                                        %(art_vol_suffix)s,
                                        %(art_issue)s,
                                        %(art_pgrg)s,
                                        %(art_pgstart)s,
                                        %(art_pgend)s,
                                        %(main_toc_id)s,
                                        %(start_sectname)s,
                                        %(bk_info_xml)s,
                                        %(bk_title)s,
                                        %(bk_publisher)s,
                                        %(art_citeas_xml)s,
                                        %(art_citeas_text)s,
                                        %(ref_count)s,
                                        %(fullfilename)s,
                                        %(manuscript_date_str)s,
                                        %(filename)s,
                                        %(filedatetime)s
                                        );
                            """

    query_params = {
        "art_id": artInfo.art_id,
        "art_doi": artInfo.art_doi,
        "art_type": artInfo.art_type,
        "art_lang":  artInfo.art_lang,
        "art_kwds":  artInfo.art_kwds,
        "art_auth_mast":  artInfo.art_auth_mast,
        "art_auth_citation": artInfo.art_auth_citation, 
        "art_title":  artInfo.art_title,
        "src_title_abbr":  artInfo.src_title_abbr,  
        "src_code":  artInfo.src_code,  
        "art_year":  artInfo.art_year,
        "art_vol_int":  artInfo.art_vol_int,
        "art_vol_str":  artInfo.art_vol_str,
        "art_vol_suffix":  artInfo.art_vol_suffix,
        "art_issue":  artInfo.art_issue,
        "art_pgrg":  artInfo.art_pgrg,
        "art_pgstart":  artInfo.art_pgstart,
        "art_pgend":  artInfo.art_pgend,
        "main_toc_id":  artInfo.main_toc_id,
        "start_sectname":  artInfo.start_sectname,
        "bk_info_xml":  artInfo.bk_info_xml,
        "bk_title":  artInfo.bk_title,
        "bk_publisher":  artInfo.bk_publisher,
        "art_citeas_xml":  artInfo.art_citeas_xml,
        "art_citeas_text":  artInfo.art_citeas_text,
        "ref_count":  artInfo.ref_count,
        "fullfilename" : artInfo.fullfilename,
        "filename":  artInfo.filename,
        "manuscript_date_str" : artInfo.manuscript_date_str,
        "filedatetime": artInfo.filedatetime
    }

    # string entries above must match an attr of the art_info instance.
    #query_param_dict = art_info.__dict__.copy()
    # the element objects in the author_xml_list cause an error in the action query 
    # even though that dict entry is not used.  So removed in a copy.
    #query_param_dict["author_xml_list"] = None
        
    try:
        res = ocd.do_action_query(querytxt=insert_if_not_exists, queryparams=query_params)
    except Exception as e:
        errStr = f"AddToArticlesDBError: insert error {e}"
        logger.error(errStr)
        if opasConfig.LOCAL_TRACE: print (errStr)
    else:
        ret_val = True
        
    try:
        ocd.db.commit()
        ocd.close_connection(caller_name="processArticles")
    except mysql.connector.Error as e:
        errStr = f"SQLDatabaseError: Commit failed! {e}"
        logger.error(errStr)
        if opasConfig.LOCAL_TRACE: print (errStr)
        ret_val = False
    
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

def build_version_history_section(ocd, common_name, verbose=False):
    """
    build version history for end of file
    """
    ret_val = None

    # get the addon version history unit to return
    list_of_items = ""

    # get all the known removed versions
    known_version_info = retrieve_all_versions_info(ocd, common_name, verbose=verbose)
    
    for known_ver in known_version_info:
        list_of_items += f"""\t<li><p><impx type='RVDOC' rx='{known_ver["art_id"]}'>{known_ver["manuscript_date_str"]}</impx></p></li>\n"""

    if list_of_items != "": 
        addon_section = f"""
           <unit type="previousversions">
                <h1>{DOCUMENT_UNIT_NAME}</h1>
                <list type="BUL1">
                {list_of_items}
                </list>
            </unit>
        """

    ret_val = ET.fromstring(addon_section, parser)
    return ret_val

def get_article_info(art_id, filename_base, fullfilename):
    fileXMLContents, input_fileinfo = fs.get_file_contents(fullfilename)
    parsed_xml = etree.fromstring(opasxmllib.remove_encoding_string(fileXMLContents), parser)
    #root = parsed_xml.getroottree()
    ret_val = opasArticleIDSupport.ArticleInfo(parsed_xml=parsed_xml, art_id=art_id, filename_base=filename_base, fullfilename=fullfilename, logger=logger)
    
    #adldata_list = root.findall('meta/adldata')
    #for adldata in adldata_list:
        #fieldname = adldata[0].text
        #fieldvalue = adldata[1].text
        #ret_val[fieldname] = fieldvalue 

    return ret_val # artInfo

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

def retrieve_all_versions_info(ocd, art_id_no_suffix, verbose=False):
    """
    Return a list of removed records and current records
    """
    ret_val = []
    select_all = f"""SELECT * from api_articles_removed
                    WHERE art_id RLIKE '{art_id_no_suffix}.'
                    UNION
                    SELECT * from api_articles
                    WHERE art_id RLIKE '{art_id_no_suffix}.'
                  """

    ret_val = ocd.get_select_as_list_of_dicts(sqlSelect=select_all)
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