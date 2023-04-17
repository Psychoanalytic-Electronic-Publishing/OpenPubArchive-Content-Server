#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
# Disable many annoying pylint messages, warning me about variable naming for example.
# yes, in my code I'm caught between two worlds of snake_case and camelCase (transitioning to snake_case).

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2022, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2023.0417/v1.0.005"   # semver versioning after date.
__status__      = "Development"

programNameShort = "opasDataCleaner"

import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

border = 80 * "*"
print (f"""\n
        {border}
            {programNameShort} - Open Publications-Archive Server (OPAS) Data Cleaner
                            Version {__version__}
        {border}
        """)

help_text = (
    fr""" 
        - Look for files in the api_articles database that don't exist anymore in the filesystem and remove them
            from the SQL DB and Solr. This is only necessary if incremental updates have been done but
            corrections have been made to datafiles that affect their article ID. When that happens,
            the same data exists in two articles of the database, one with the old, and one with the
            corrected ID.
        
        Example Invocation:
                $ python opasDataCleaner.py
                
        Important option choices:
         -h, --help         List all help options
         --nocheck          Don't prompt whether to proceed after showing setting/option choices
         --nohelp           Turn off front-matter help (that displays when you run)
         
        Note:
          S3 is set up with root=localsecrets.FILESYSTEM_ROOT (default).  The root must be the bucket name.
    """
)

import sys
sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')

import time
import pysolr
import localsecrets
import opasConfig
import re
import os
import os.path
import pathlib
# from opasFileSupport import FileInfo

from datetime import datetime
import logging
logger = logging.getLogger(programNameShort)

from optparse import OptionParser

import configLib
import configLib.opasCoreConfig
import opasCentralDBLib
import opasFileSupport
import opasPySolrLib

#detect data is on *nix or windows system
if "AWS" in localsecrets.CONFIG or re.search("/", localsecrets.IMAGE_SOURCE_PATH) is not None:
    path_separator = "/"
else:
    path_separator = r"\\"

# Module Globals
fs_flex = None

#------------------------------------------------------------------------------------------------------
def main():
    
    global options  # so the information can be used in support functions

    # scriptSourcePath = os.path.dirname(os.path.realpath(__file__))

    ocd =  opasCentralDBLib.opasCentralDB()
    fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root=localsecrets.FILESYSTEM_ROOT)

    # set toplevel logger to specified loglevel
    logger = logging.getLogger()
    logger.setLevel(options.logLevel)
    # get local logger
    logger = logging.getLogger(programNameShort)
    logger.info('Started at %s', datetime.today().strftime('%Y-%m-%d %H:%M:%S"'))

    solrurl_docs = None
    solrurl_authors = None
    if options.rootFolder == localsecrets.XML_ORIGINALS_PATH or options.rootFolder == None:
        start_folder = pathlib.Path(localsecrets.XML_ORIGINALS_PATH)
    else:
        start_folder = pathlib.Path(options.rootFolder)   
    
    if 1: # (options.biblio_update or options.fulltext_core_update or options.glossary_core_update) == True:
        try:
            solrurl_docs = localsecrets.SOLRURL + configLib.opasCoreConfig.SOLR_DOCS  # e.g., http://localhost:8983/solr/    + pepwebdocs'
            solrurl_authors = localsecrets.SOLRURL + configLib.opasCoreConfig.SOLR_AUTHORS
            # print("Logfile: ", logFilename)
            print("Messaging verbose: ", options.display_verbose)
            print("Input data Root: ", start_folder)
            print("Article ID Prefix: ", options.artid_prefix)

            print(80*"*")
            print(f"Database tables api_articles and api_biblioxml2 will be updated. Location: {localsecrets.DBHOST}")
            print("Solr Full-Text Core will be updated: ", solrurl_docs)
            print("Solr Authors Core will be updated: ", solrurl_authors)
            
            print(80*"*")
            if not options.no_check:
                cont = ""
                while cont == "":
                    cont = input ("The above databases will have data from missing files removed.  Do you want to continue (y/n)?")
                    if len(cont) >= 1:
                        if cont[0].lower() == "n":
                            print ("User requested exit.  No data changed.")
                            sys.exit(0)
                
        except Exception as e:
            msg = f"cores specification error ({e})."
            print((len(msg)*"-"))
            print (msg)
            print((len(msg)*"-"))
            sys.exit(0)

    solr_docs2 = None
    # The connection call is to solrpy (import was just solr)
    if localsecrets.SOLRUSER is not None and localsecrets.SOLRPW is not None:
        if 1: # options.fulltext_core_update:
            solr_docs2 = pysolr.Solr(solrurl_docs, auth=(localsecrets.SOLRUSER, localsecrets.SOLRPW))
            solr_authors = pysolr.Solr(solrurl_authors, auth=(localsecrets.SOLRUSER, localsecrets.SOLRPW))
    else: #  no user and password needed
        solr_docs2 = pysolr.Solr(solrurl_docs)
        solr_authors = pysolr.Solr(solrurl_authors)

    # record time in case options.nofiles is true
    timeStart = time.time()
    filenames = []
    name_str = ""

    if options.remove_rogues:
        query = "-art_id:* AND -id:GW* AND -id:SE*"
        r1, status = opasPySolrLib.search_text(query=query)
        r1_count = r1.documentList.responseInfo.fullCount
        if r1_count > 0:
            print (f"There are {r1_count} rogue records without an art_id in Solr.")
            if not options.testmode:
                solr_docs2.delete(q="-art_id:* AND -id:GW* AND -id:SE*")
                solr_docs2.commit()

    if options.no_cleaning == False: # default
        print((80*"-"))
        timeStart = time.time()
        print (f"Processing started at ({time.ctime()}).")
    
        print ("Fetching filenames...")
        if filenames == []:
            filenames = fs.get_matching_filelist(filespec_regex=f"{options.artid_prefix}.*\(bEXP_ARCH1\).*$", path=start_folder)
            for n in filenames:
                nm = n.basename
                nroot = nm[:nm.find('(')]
                nroot = nroot.upper()
                name_str += f"#{nroot}#"
                
        print((80*"-"))
        # Get list of articles from the tracker table.  TBD: Later add filename with path to the table so you don't need to read all
        #  the files at once above.
        time_milestone1 = time.time()
        print (f"Filename collection ({len(filenames)}) from storage took {(time_milestone1-timeStart)/60} minutes")
        print (f"Fetching article info from database...")
        if options.artid_prefix != "":
            search_clause = f" WHERE art_id LIKE '{options.artid_prefix}%'"
        else:
            search_clause = ""
            
        articles_to_check = f"""
                              select art_id, filename from api_articles{search_clause};
                             """
        article_list = ocd.get_select_as_list_of_dicts(articles_to_check)
        time_milestone2 = time.time()
        
        print (f"DB Article Load ({len(article_list)}) took {time_milestone2-time_milestone1} secs")
        print ("Checking for missing articles...")
        # look to see if they exist
        for article in article_list:
            art_id = article["art_id"]
            filename = article["filename"].upper()
            rootname = filename[:filename.find('(')]
            rootname_demarcated = f"#{rootname}#"
            if rootname_demarcated in name_str:
                continue
            print (f"article file for {rootname} no longer exists.")
            # if they don't delete them from the database table and solr
            if not options.testmode:
                try:
                    result = solr_docs2.delete(q=f"art_id:{art_id}")
                    result = solr_authors.delete(q=f"art_id:{art_id}")
                    ocd.delete_specific_article_data(art_id=art_id)
                    
                except Exception as e:
                    print (f"Error deleting {art_id} {e}")
                else:
                    print (f"Deleted {art_id} from solr")
            else:
                print (f"Test mode active...if not {art_id} would have been removed from the database.")
        
        time_milestone3 = time.time()
        print (f"Checking for missing articles and deleting them from the databases (if present) took {time_milestone3-time_milestone2}")
        if not options.testmode:
            solr_docs2.commit()
            solr_authors.commit()
    
    # ---------------------------------------------------------
    # Closing time
    # ---------------------------------------------------------
    timeEnd = time.time()
    print ("Processing finished.")
    elapsed_seconds = timeEnd-timeStart # actual processing time going through files
    elapsed_minutes = elapsed_seconds / 60
    msg = f"Elapsed min: {elapsed_minutes:.4f}"
    logger.info(msg)
    print (msg)
    print (80 * "-")

# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    global options  # so the information can be used in support functions
    options = None
    parser = OptionParser(usage="%prog [options] - PEP DataCleaner", version=f"%prog ver. {__version__}")
    parser.add_option("-d", "--dataroot", dest="rootFolder", default=localsecrets.XML_ORIGINALS_PATH,
                      help="Bucket (Required S3) or Root folder path where data is located")
    parser.add_option("--prefix", "--artidprefix", dest="artid_prefix", default="",
                      help="Article ID/Filename prefix to limit processing")
    parser.add_option("-l", "--loglevel", dest="logLevel", default=logging.ERROR,
                      help="Level at which events should be logged (DEBUG, INFO, WARNING, ERROR")
    parser.add_option("--nocheck", action="store_true", dest="no_check", default=False,
                      help="Don't prompt whether to proceed.")
    parser.add_option("--test", dest="testmode", action="store_true", default=False,
                      help="Don't commit the delete in solr")
    parser.add_option("--verbose", action="store_true", dest="display_verbose", default=False,
                      help="Display status and operational timing info as load progresses.")
    # New OpasLoader2 Options
    parser.add_option("--outputbuild", dest="output_build", default=opasConfig.DEFAULT_OUTPUT_BUILD,
                      help=f"Specific output build specification, default='{opasConfig.DEFAULT_OUTPUT_BUILD}'. e.g., (bEXP_ARCH1) or just bEXP_ARCH1.")
    parser.add_option("--nohelp", action="store_true", dest="no_help", default=False,
                      help="Turn off front-matter help")
    parser.add_option("--rogues", dest="remove_rogues", action="store_true", default=False,
                      help="Delete roque records (without art_id) in Solr")
    parser.add_option("--noclean", dest="no_cleaning", action="store_true", default=False,
                      help="Don't clean the DB for missing files (use with rogues to just remove rogues).")

    (options, args) = parser.parse_args()
    
    if not options.no_help:
        print (help_text)

    if len(options.output_build) < 2:
        logger.error("Bad output buildname. Using default.")
        options.output_build = opasConfig.DEFAULT_OUTPUT_BUILD
        
    if options.output_build is not None and (options.output_build[0] != "(" or options.output_build[-1] != ")"):
        print ("Warning: output build should have parenthesized format like (bEXP_ARCH1). Adding () as needed.")
        if options.output_build[0] != "(":
            options.output_build = f"({options.output_build}"
        if options.output_build[-1] != ")":
            options.output_build = f"{options.output_build})"
    
    main()
