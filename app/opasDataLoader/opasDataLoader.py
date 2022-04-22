#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
# Disable many annoying pylint messages, warning me about variable naming for example.
# yes, in my Solr code I'm caught between two worlds of snake_case and camelCase.

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2022.0315" 
__status__      = "Production"

programNameShort = "opasDataLoader"
import lxml
import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

print(
    f""" 
        {programNameShort} - Open Publications-Archive Server (OPAS) - Document, Authors, and References Core Loader
    
        Load articles into the Docs, Authors, and Glossary Solr cores and
        load article information and bibliography entries into a MySQL database
        (RDS or MySQL) as configured in localsecrets). This data loader is specific to the
        PEP Data and Bibliography schemas but can serve as a model or framework for other schemas.
        
        See documentation at:
          https://github.com/Psychoanalytic-Electronic-Publishing/OpenPubArchive-Content-Server/wiki/Loading-Data-into-OpenPubArchive
        
        Example Invocation:
                $ python opasDataLoader.py
                
        Important option choices:
         -h, --help      List all help options
         -a              Force update of files (otherwise, only updated when the data is newer)
         --sub           Start with this subfolder of the root (can add sublevels to that)
         --key:          Do just one file with the specified PEP locator (e.g., --key AIM.076.0309A)
         --nocheck       Don't prompt whether to proceed after showing setting/option choices
         --reverse       Process in reverse
         --halfway       Stop after doing half of the files, so it can be run in both directions
         --whatsnewdays  Use the days back value supplied to write a new article log, rather than the specific files loaded.
                         Note that 1==today.
         --whatsnewfile  To specify the file in which to write the what's new list.
         --nofiles       Can be used in conjunction with whatsnewdays to simply produce the new article log rather than loading files.

        Example:
          Update all files from the root (default, pep-web-xml) down.  Starting two runs, one running the file list forward, the other backward.
          As long as you don't specify -a, they will skip the ones the other did when they eventually
          cross

             python opasDataLoader.py 
             python opasDataLoader.py --reverse

          Update all of PEPCurrent

             python opasDataLoader.py -a --sub _PEPCurrent
             
          Generate a new articles log file for 10 days back
             
             python opasDataLoader.py --nofiles --whatsnewdays=10

        Note:
          S3 is set up with root pep-web-xml (default).  The root must be the bucket name.
          
          S3 has subfolders _PEPArchive, _PEPCurrent, _PEPFree, _PEPOffsite
            to allow easy processing of one archive type at a time simply using
            the --sub option (or four concurrently for faster processing).
    """
)

import sys
sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')

import time
import random
import pysolr
import localsecrets
import re
import os
import os.path
import pathlib
from opasFileSupport import FileInfo

import datetime as dtime
from datetime import datetime
import logging
logger = logging.getLogger(programNameShort)

from optparse import OptionParser

from lxml import etree
import mysql.connector

import configLib.opasCoreConfig
from configLib.opasCoreConfig import solr_authors2, solr_gloss2
import loaderConfig
import opasSolrLoadSupport

import opasXMLHelper as opasxmllib
import opasCentralDBLib
import opasProductLib
# import opasGenSupportLib as opasgenlib
import localsecrets
import opasFileSupport
import opasAPISupportLib

#detect data is on *nix or windows system
if "AWS" in localsecrets.CONFIG or re.search("/", localsecrets.IMAGE_SOURCE_PATH) is not None:
    path_separator = "/"
else:
    path_separator = r"\\"

# Module Globals
bib_total_reference_count = 0

def find_all(name_pat, path):
    result = []
    name_patc = re.compile(name_pat, re.IGNORECASE)
    for root, dirs, files in os.walk(path):
        for filename in files:
            if name_patc.match(filename):
                result.append(os.path.join(root, filename))
    return result

#------------------------------------------------------------------------------------------------------
def file_was_created_before(before_date, fileinfo):
    ret_val = False
    try:
        timestamp_str = fileinfo.date_str
        if timestamp_str < before_date:
            ret_val = True
        else:
            ret_val = False
    except Exception as e:
        ret_val = False # not found or error, return False
        
    return ret_val

#------------------------------------------------------------------------------------------------------
def file_was_created_after(after_date, fileinfo):
    ret_val = False
    try:
        timestamp_str = fileinfo.date_str
        if timestamp_str >  after_date:
            ret_val = True
        else:
            ret_val = False
    except Exception as e:
        ret_val = False # not found or error, return False
        
    return ret_val
#------------------------------------------------------------------------------------------------------
def file_was_loaded_before(solrcore, before_date, filename):
    ret_val = False
    try:
        result = opasSolrLoadSupport.get_file_dates_solr(solrcore, filename)
        if result[0]["timestamp"] < before_date:
            ret_val = True
        else:
            ret_val = False
    except Exception as e:
        ret_val = True # not found or error, return true
        
    return ret_val

#------------------------------------------------------------------------------------------------------
def file_was_loaded_after(solrcore, after_date, filename):
    ret_val = False
    try:
        result = opasSolrLoadSupport.get_file_dates_solr(solrcore, filename)
        if result[0]["timestamp"] > after_date:
            ret_val = True
        else:
            ret_val = False
    except Exception as e:
        ret_val = True # not found or error, return true
        
    return ret_val

#------------------------------------------------------------------------------------------------------
def file_is_same_as_in_solr(solrcore, filename, timestamp_str):
    ret_val = False
    try:
        result = opasSolrLoadSupport.get_file_dates_solr(solrcore, filename)
        if result[0]["file_last_modified"] == timestamp_str:
            ret_val = True
        else:
            ret_val = False
    except KeyError as e:
        ret_val = False # not found, return false so it's loaded anyway.
    except Exception as e:
        logger.info(f"File check error: {e}")
        ret_val = False # error, return false so it's loaded anyway.
        
    return ret_val

#------------------------------------------------------------------------------------------------------
def main():
    
    global options  # so the information can be used in support functions
    
    cumulative_file_time_start = time.time()
    randomizer_seed = None 

    # scriptSourcePath = os.path.dirname(os.path.realpath(__file__))

    processed_files_count = 0
    ocd =  opasCentralDBLib.opasCentralDB()
    fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root="pep-web-xml")

    # set toplevel logger to specified loglevel
    logger = logging.getLogger()
    logger.setLevel(options.logLevel)
    # get local logger
    logger = logging.getLogger(programNameShort)

    logger.info('Started at %s', datetime.today().strftime('%Y-%m-%d %H:%M:%S"'))
    # logging.basicConfig(filename=logFilename, level=options.logLevel)

    solrurl_docs = None
    solrurl_authors = None
    solrurl_glossary = None
    if options.rootFolder == localsecrets.XML_ORIGINALS_PATH or options.rootFolder == None:
        start_folder = pathlib.Path(localsecrets.XML_ORIGINALS_PATH)
    else:
        start_folder = pathlib.Path(options.rootFolder)   
    
    if 1: # (options.biblio_update or options.fulltext_core_update or options.glossary_core_update) == True:
        try:
            solrurl_docs = localsecrets.SOLRURL + configLib.opasCoreConfig.SOLR_DOCS  # e.g., http://localhost:8983/solr/    + pepwebdocs'
            solrurl_authors = localsecrets.SOLRURL + configLib.opasCoreConfig.SOLR_AUTHORS
            solrurl_glossary = localsecrets.SOLRURL + configLib.opasCoreConfig.SOLR_GLOSSARY
            # print("Logfile: ", logFilename)
            print("Messaging verbose: ", options.display_verbose)
            print("Input data Root: ", start_folder)
            print("Input data Subfolder: ", options.subFolder)
            print("Reset Core Data: ", options.resetCoreData)
            if options.forceRebuildAllFiles == True:
                msg = "Forced Rebuild - All files added, regardless of whether they are the same as in Solr."
                logger.info(msg)
                print (msg)
                
            print(80*"*")
            print(f"Database will be updated. Location: {localsecrets.DBHOST}")
            if not options.glossary_only: # options.fulltext_core_update:
                print("Solr Full-Text Core will be updated: ", solrurl_docs)
                print("Solr Authors Core will be updated: ", solrurl_authors)
            if 1: # options.glossary_core_update:
                print("Solr Glossary Core will be updated: ", solrurl_glossary)

            print(80*"*")
            if options.include_paras:
                print ("--includeparas option selected. Each paragraph will also be stored individually for *Docs* core. Increases core size markedly!")
            else:
                try:
                    print (f"Paragraphs only stored for sources indicated in loaderConfig. Currently: [{', '.join(loaderConfig.src_codes_to_include_paras)}]")
                except:
                    print ("Paragraphs only stored for sources indicated in loaderConfig.")
    
            if options.halfway:
                print ("--halfway option selected.  Processing approximately one-half of the files that match.")
                
            if options.run_in_reverse:
                print ("--reverse option selected.  Running the files found in reverse order.")

            if options.file_key:
                print (f"--key supplied.  Running for files matching the article id {options.file_key}")

            print(80*"*")
            if not options.no_check:
                cont = input ("The above databases will be updated.  Do you want to continue (y/n)?")
                if cont.lower() == "n":
                    print ("User requested exit.  No data changed.")
                    sys.exit(0)
                
        except Exception as e:
            msg = f"cores specification error ({e})."
            print((len(msg)*"-"))
            print (msg)
            print((len(msg)*"-"))
            sys.exit(0)

    # import data about the PEP codes for journals and books.
    #  Codes are like APA, PAH, ... and special codes like ZBK000 for a particular book
    sourceDB = opasProductLib.SourceInfoDB()
    solr_docs2 = None
    # The connection call is to solrpy (import was just solr)
    if localsecrets.SOLRUSER is not None and localsecrets.SOLRPW is not None:
        if 1: # options.fulltext_core_update:
            solr_docs2 = pysolr.Solr(solrurl_docs, auth=(localsecrets.SOLRUSER, localsecrets.SOLRPW))
    else: #  no user and password needed
        solr_docs2 = pysolr.Solr(solrurl_docs)

    # Reset core's data if requested (mainly for early development)
    if options.resetCoreData:
        if not options.glossary_only: # options.fulltext_core_update:
            if not options.no_check:
                cont = input ("The solr cores and the database article and artstat tables will be cleared.  Do you want to continue (y/n)?")
                if cont.lower() == "n":
                    print ("User requested exit.  No data changed.")
                    sys.exit(0)
            else:
                print ("Options --no-check and --resetcore both specified.  Warning: The solr cores and the database article and artstat tables will be cleared.  Pausing 60 seconds to allow you to cancel (ctrl-c) the run.")
                time.sleep(60)
                print ("Second Warning: Continuing the run (and core and database reset) in 20 seconds...")
                time.sleep(20)               

            msg = "*** Deleting all data from the docs and author cores, the articles, artstat, and biblio database tables ***"
            logger.warning(msg)
            print (msg)
            ocd.delete_all_article_data()
            solr_docs2.delete(q='*:*')
            solr_docs2.commit()
            solr_authors2.delete(q="*:*")
            solr_authors2.commit()

        # reset glossary core when others are reset, or when --resetcore is selected with --glossaryonly   
        if 1: # options.glossary_core_update:
            msg = "*** Deleting all data from the Glossary core ***"
            logger.warning(msg)
            print (msg)
            solr_gloss2.delete(q="*:*")
            solr_gloss2.commit()
    else:
        pass   # XXX Later - check for missing files and delete them from the core, since we didn't empty the core above

    # Go through a set of XML files
    bib_total_reference_count = 0 # zero this here, it's checked at the end whether references are processed or not

    # ########################################################################
    # Get list of files to process    
    # ########################################################################
    new_files = 0
    total_files = 0
    
    if options.subFolder is not None:
        start_folder = start_folder / pathlib.Path(options.subFolder)

    # record time in case options.nofiles is true
    timeStart = time.time()

    if not options.no_files:
        print (f"Locating files for processing at {start_folder} with pattern {loaderConfig.file_match_pattern}. Started at ({time.ctime()}).")
        if options.file_key is not None:  
            # print (f"File Key Specified: {options.file_key}")
            pat = fr"({options.file_key}.*){loaderConfig.file_match_pattern}"
            filenames = fs.get_matching_filelist(filespec_regex=pat, path=start_folder, max_items=1000)
            if len(filenames) is None:
                msg = f"File {pat} not found.  Exiting."
                logger.warning(msg)
                print (msg)
                exit(0)
            else:
                options.forceRebuildAllFiles = True
        elif options.file_only is not None:
            fileinfo = FileInfo()
            filespec = options.file_only
            fileinfo.mapLocalFS(filespec)
            filenames = [fileinfo]
        else:
            pat = fr"(.*?){loaderConfig.file_match_pattern}"
            filenames = []
        
        if filenames != []:
            total_files = len(filenames)
            new_files = len(filenames)
        else:
            # get a list of all the XML files that are new
            if options.forceRebuildAllFiles:
                # get a complete list of filenames for start_folder tree
                filenames = fs.get_matching_filelist(filespec_regex=pat, path=start_folder)
            else:
                filenames = fs.get_matching_filelist(filespec_regex=pat, path=start_folder, revised_after_date=options.created_after)
                
        print((80*"-"))
        files_found = len(filenames)
        if options.forceRebuildAllFiles:
            #maybe do this only during core resets?
            #print ("Clearing database tables...")
            #ocd.delete_all_article_data()
            print(f"Ready to import records from {files_found} files at path {start_folder}")
        else:
            print(f"Ready to import {files_found} files *if modified* at path: {start_folder}")
    
        timeStart = time.time()
        print (f"Processing started at ({time.ctime()}).")
    
        print((80*"-"))
        precommit_file_count = 0
        skipped_files = 0
        stop_after = 0
        cumulative_file_time_start = time.time()
        issue_updates = {}
        if files_found > 0:
            if options.halfway:
                stop_after = round(files_found / 2) + 5 # go a bit further
                
            if options.run_in_reverse:
                filenames.reverse()
            
            # ----------------------------------------------------------------------
            # Now walk through all the filenames selected
            # ----------------------------------------------------------------------
            print (f"Load process started ({time.ctime()}).  Examining files.")
            
            for n in filenames:
                fileTimeStart = time.time()
                file_updated = False
                if not options.forceRebuildAllFiles:                    
                    if not options.display_verbose and processed_files_count % 100 == 0 and processed_files_count != 0:
                        print (f"Processed Files ...loaded {processed_files_count} out of {files_found} possible.")
    
                    if not options.display_verbose and skipped_files % 100 == 0 and skipped_files != 0:
                        print (f"Skipped {skipped_files} so far...loaded {processed_files_count} out of {files_found} possible." )
                    
                    if file_is_same_as_in_solr(solr_docs2, filename=n.basename, timestamp_str=n.timestamp_str):
                        skipped_files += 1
                        if options.display_verbose:
                            print (f"Skipped - No refresh needed for {n.basename}")
                        continue
                    else:
                        file_updated = True
                
                # get mod date/time, filesize, etc. for mysql database insert/update
                processed_files_count += 1
                if stop_after > 0:
                    if processed_files_count > stop_after:
                        print (f"Halfway mark reached on file list ({stop_after})...file processing stopped per halfway option")
                        break
    
                fileXMLContents = fs.get_file_contents(n.filespec)
                
                # get file basename without build (which is in paren)
                base = n.basename
                artID = os.path.splitext(base)[0]
                # watch out for comments in file name, like:
                #   JICAP.018.0307A updated but no page breaks (bEXP_ARCH1).XML
                #   so skip data after a space
                m = re.match(r"([^ ]*).*\(.*\)", artID)
                # Note: We could also get the artID from the XML, but since it's also important
                # the file names are correct, we'll do it here.  Also, it "could" have been left out
                # of the artinfo (attribute), whereas the filename is always there.
                artID = m.group(1)
                # all IDs to upper case.
                artID = artID.upper()
                msg = "Processing file #%s of %s: %s (%s bytes). Art-ID:%s" % (processed_files_count, files_found, base, n.filesize, artID)
                logger.info(msg)
                if options.display_verbose:
                    print (msg)
        
                # import into lxml
                parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
                root = etree.fromstring(opasxmllib.remove_encoding_string(fileXMLContents), parser)
                pepxml = root
        
                # save common document (article) field values into artInfo instance for both databases
                artInfo = opasSolrLoadSupport.ArticleInfo(sourceDB.sourceData, pepxml, artID, logger)
                artInfo.filedatetime = n.timestamp_str
                artInfo.filename = base
                artInfo.file_size = n.filesize
                artInfo.file_updated = file_updated
                artInfo.file_create_time = n.create_time
                # not a new journal, see if it's a new article.
                if opasSolrLoadSupport.add_to_tracker_table(ocd, artInfo.art_id): # if true, added successfully, so new!
                    # don't log to issue updates for journals that are new sources added during the annual update
                    if artInfo.src_code not in loaderConfig.DATA_UPDATE_PREPUBLICATION_CODES_TO_IGNORE:
                        art = f"<article id='{artInfo.art_id}'>{artInfo.art_citeas_xml}</article>"
                        try:
                            issue_updates[artInfo.issue_id_str].append(art)
                        except Exception as e:
                            issue_updates[artInfo.issue_id_str] = [art]
    
                try:
                    artInfo.file_classification = re.search("(?P<class>current|archive|future|free|special|offsite)", str(n.filespec), re.IGNORECASE).group("class")
                    # set it to lowercase for ease of matching later
                    if artInfo.file_classification is not None:
                        artInfo.file_classification = artInfo.file_classification.lower()
                except Exception as e:
                    logger.warning("Could not determine file classification for %s (%s)" % (n.filespec, e))
        
                # walk through bib section and add to refs core database
        
                precommit_file_count += 1
                if precommit_file_count > configLib.opasCoreConfig.COMMITLIMIT:
                    print(f"Committing info for {configLib.opasCoreConfig.COMMITLIMIT} documents/articles")
    
                # input to the glossary
                if 1: # options.glossary_core_update:
                    # load the glossary core if this is a glossary item
                    glossary_file_pattern=r"ZBK.069(.*)\(bEXP_ARCH1\)\.(xml|XML)$"
                    if re.match(glossary_file_pattern, n.basename):
                        opasSolrLoadSupport.process_article_for_glossary_core(pepxml, artInfo, solr_gloss2, fileXMLContents, verbose=options.display_verbose)
                
                # input to the full-text and authors cores
                if not options.glossary_only: # options.fulltext_core_update:
                    # load the database
                    opasSolrLoadSupport.add_article_to_api_articles_table(ocd, artInfo, verbose=options.display_verbose)
                    opasSolrLoadSupport.add_to_artstat_table(ocd, artInfo, verbose=options.display_verbose)

                    # -----
                    # 2022-04-22 New Section Name Workaround - This works but it means at least for new data, you can't run the load backwards as we currently do
                    #  on a full build.  Should be put into the client instead, really, during table gen.
                    # -----
                    # Uses new views: vw_article_firstsectnames which is based on the new view vw_article_sectnames
                    #  if an article id is found in that view, it's the first in the section, otherwise it isn't
                    # check database to see if this is the first in the section
                    if not opasSolrLoadSupport.check_if_start_of_section(ocd, artInfo.art_id):
                        print (f"   ...NewSec Workaround: Clearing newsecnm for {artInfo.art_id}")
                        artInfo.start_sectname = None # clear it so it's not written to solr, this is not the first article
                    # -----

                    # load the docs (pepwebdocs) core
                    opasSolrLoadSupport.process_article_for_doc_core(pepxml, artInfo, solr_docs2, fileXMLContents, include_paras=options.include_paras, verbose=options.display_verbose)
                    # load the authors (pepwebauthors) core.
                    opasSolrLoadSupport.process_info_for_author_core(pepxml, artInfo, solr_authors2, verbose=options.display_verbose)
                    # load the database (Moved to above new section name workaround)
                    #opasSolrLoadSupport.add_article_to_api_articles_table(ocd, artInfo, verbose=options.display_verbose)
                    #opasSolrLoadSupport.add_to_artstat_table(ocd, artInfo, verbose=options.display_verbose)
                    
                    if precommit_file_count > configLib.opasCoreConfig.COMMITLIMIT:
                        precommit_file_count = 0
                        solr_docs2.commit()
                        solr_authors2.commit()
        
                # input to the references core
                if 1: # options.biblio_update:
                    if artInfo.ref_count > 0:
                        bibReferences = pepxml.xpath("/pepkbd3//be")  # this is the second time we do this (also in artinfo, but not sure or which is better per space vs time considerations)
                        if options.display_verbose:
                            print(("   ...Processing %s references for the references database." % (artInfo.ref_count)))
    
                        #processedFilesCount += 1
                        bib_total_reference_count = 0
                        ocd.open_connection(caller_name="processBibliographies")
                        for ref in bibReferences:
                            bib_total_reference_count += 1
                            bib_entry = opasSolrLoadSupport.BiblioEntry(artInfo, ref)
                            opasSolrLoadSupport.add_reference_to_biblioxml_table(ocd, artInfo, bib_entry)
    
                        try:
                            ocd.db.commit()
                        except mysql.connector.Error as e:
                            print("SQL Database -- Biblio Commit failed!", e)
                            
                        ocd.close_connection(caller_name="processBibliographies")
    
                # close the file, and do the next
                if options.display_verbose:
                    print(("   ...Time: %s seconds." % (time.time() - fileTimeStart)))
        
            print (f"Load process complete ({time.ctime()}).")
            if processed_files_count > 0:
                try:
                    print ("Performing final commit.")
                    if not options.glossary_only: # options.fulltext_core_update:
                        solr_docs2.commit()
                        solr_authors2.commit()
                        # fileTracker.commit()
                    if 1: # options.glossary_core_update:
                        solr_gloss2.commit()
                except Exception as e:
                    print(("Exception: ", e))
                else:
                    # Use date time as seed, hoping multiple instances don't get here at the same time
                    # but only if caller did not specify
                    if randomizer_seed is None:
                        randomizer_seed = int(datetime.utcnow().timestamp())
    
    # end of docs, authors, and/or references Adds
    # fix statistics by removing any not in the api_articles table
    opasSolrLoadSupport.garbage_collect_stat(ocd)
    
    if options.daysback is not None: #  get all updated records
        print (f"Listing updates for {options.daysback} days.")
        issue_updates = {}
        try:
            days_back = int(options.daysback)
        except:
            logger.error("Incorrect specification of days back. Must be integer.")
        else:
            article_list = ocd.get_articles_newer_than(days_back=days_back)
            for art_id in article_list:
                # save common document (article) field values into artInfo instance for both databases
                artInfoSolr = opasAPISupportLib.documents_get_abstracts(art_id)
                try:
                    art_citeas_xml = artInfoSolr.documents.responseSet[0].documentRefXML
                    src_code = artInfoSolr.documents.responseSet[0].PEPCode
                    art_year = artInfoSolr.documents.responseSet[0].year
                    art_vol_str = artInfoSolr.documents.responseSet[0].vol
                    art_issue = artInfoSolr.documents.responseSet[0].issue
                    issue_id_str = f"<issue_id><src>{src_code}</src><yr>{art_year}</yr><vol>{art_vol_str}</vol><iss>{art_issue}</iss></issue_id>"
                except:
                    logger.error(f"Error: can't find article info for: {art_id} ")
                else:   
                    if src_code not in loaderConfig.DATA_UPDATE_PREPUBLICATION_CODES_TO_IGNORE:
                        art = f"<article id='{art_id}'>{art_citeas_xml}</article>"
                        try:
                            issue_updates[issue_id_str].append(art)
                        except Exception as e:
                            issue_updates[issue_id_str] = [art]
    
    # write updated file
    if issue_updates != {}:
        # now seed randomizer, hopefull all instances have a different seed (or caller must force)
        random.seed(randomizer_seed)
        try:
            # temp exception block just until localsecrets has been updated with DATA_UPDATE_LOG_DIR
            if options.whatsnewfile is None:
                try:
                    fname = f"{localsecrets.DATA_UPDATE_LOG_DIR}/updated_issues_{dtime.datetime.now().strftime('%Y%m%d_%H%M%S')}({random.randint(1000,9999)}).xml"
                except Exception as e:
                    fname = f"updated_issues_{dtime.datetime.now().strftime('%Y%m%d_%H%M%S')}({random.randint(1000,9999)}).xml"
            else:
                fname = options.whatsnewfile
                
            msg = f"Issue updates.  Writing file {fname}"
            print (msg)
            logging.info(msg)
            with open(fname, 'w', encoding="utf8") as fo:
                fo.write( f'<?xml version="1.0" encoding="UTF-8"?>\n')
                fo.write('<issue_updates>\n')
                count_records = 0
                for k, a in issue_updates.items():
                    fo.write(f"\n\t<issue>\n\t\t{str(k)}\n\t\t<articles>\n")
                    count_records += 1
                    for ref in a:
                        try:
                            #ref = re.sub(ref, "([Q ])&([ A])", r"\1&amp;\2", flags=re.IGNORECASE)
                            fo.write(f"\t\t\t{ref}\n")
                        except Exception as e:
                            logging.error(f"Issue Update Article Write Error: ({e})")
                            
                    fo.write("\t\t</articles>\n\t</issue>")
                fo.write('\n</issue_updates>')

            if count_records > 0:
                print (f"{count_records} issue updates written to whatsnew log file.")

        except Exception as e:
            logging.error(f"Issue Update File Write Error: ({e})")
    
    else: # if issue_updates != {}
        if options.daysback is not None:
            msg = f"Note: There was nothing in the whats new request to output for days back == {options.daysback}."
            logging.warning(msg)
        else:
            msg = f"Note: There was nothing new in the batch output whatsnew."
            logging.warning(msg)
            
 
    # ---------------------------------------------------------
    # Closing time
    # ---------------------------------------------------------
    timeEnd = time.time()
    #currentfile_info.close()

    if not options.no_files:
        # for logging
        if 1: # (options.biblio_update or options.fulltext_core_update) == True:
            elapsed_seconds = timeEnd-cumulative_file_time_start # actual processing time going through files
            elapsed_minutes = elapsed_seconds / 60
            if bib_total_reference_count > 0:
                msg = f"Finished! Imported {processed_files_count} documents and {bib_total_reference_count} references. Total file inspection/load time: {elapsed_seconds:.2f} secs ({elapsed_minutes:.2f} minutes.) "
                logger.info(msg)
                print (msg)
            else:
                msg = f"Finished! Imported {processed_files_count} documents. Total file load time: {elapsed_seconds:.2f} secs ({elapsed_minutes:.2f} minutes.)"
                logger.info(msg) 
                print (msg)
            if processed_files_count > 0:
                msg = f"...Files loaded per Min: {processed_files_count/elapsed_minutes:.4f}"
                logger.info(msg)
                print (msg)
                msg = f"...Files evaluated per Min (includes skipped files): {len(filenames)/elapsed_minutes:.4f}"
                logger.info(msg)
                print (msg)
    
        elapsed_seconds = timeEnd-timeStart # actual processing time going through files
        elapsed_minutes = elapsed_seconds / 60
        msg = f"Note: File load time is not total elapsed time. Total elapsed time is: {elapsed_seconds:.2f} secs ({elapsed_minutes:.2f} minutes.)"
        logger.info(msg)
        print (msg)
        if processed_files_count > 0:
            msg = f"Files per elapsed min: {processed_files_count/elapsed_minutes:.4f}"
            logger.info(msg)
            print (msg)
    else:  # no_files
        print ("Processing finished.")
        elapsed_seconds = timeEnd-timeStart # actual processing time going through files
        elapsed_minutes = elapsed_seconds / 60
        msg = f"Elapsed min: {elapsed_minutes:.4f}"
        logger.info(msg)
        print (msg)

# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    global options  # so the information can be used in support functions
    options = None
    parser = OptionParser(usage="%prog [options] - PEP Solr Data Loader", version=f"%prog ver. {__version__}")
    parser.add_option("-a", "--allfiles", action="store_true", dest="forceRebuildAllFiles", default=False,
                      help="Option to force all files to be loaded to the specified cores.")
    # redundant add option to use so compatible options to the PEPXML code for manual use
    parser.add_option("--rebuild", action="store_true", dest="forceRebuildAllFiles", default=False,
                      help="Option to force one or more included files to be reloaded to the specified cores whether changed or not.")
    parser.add_option("--after", dest="created_after", default=None,
                      help="Load files created or modifed after this datetime (use YYYY-MM-DD format). (May not work on S3)")
    parser.add_option("-d", "--dataroot", dest="rootFolder", default=localsecrets.XML_ORIGINALS_PATH,
                      help="Bucket (Required S3) or Root folder path where input data is located")
    parser.add_option("--key", dest="file_key", default=None,
                      help="Key for a single file to load, e.g., AIM.076.0269A.  Use in conjunction with --sub for faster processing of single files on AWS")
    parser.add_option("-l", "--loglevel", dest="logLevel", default=logging.ERROR,
                      help="Level at which events should be logged (DEBUG, INFO, WARNING, ERROR")
    #parser.add_option("--logfile", dest="logfile", default=logFilename,
                      #help="Logfile name with full path where events should be logged")
    parser.add_option("--nocheck", action="store_true", dest="no_check", default=False,
                      help="Don't prompt whether to proceed.")
    parser.add_option("--only", dest="file_only", default=None,
                      help="File spec for a single file to process.")
    parser.add_option("--includeparas", action="store_true", dest="include_paras", default=False,
                      help="Don't separately store paragraphs except for sources using concordance (GW/SE).")
    parser.add_option("--halfway", action="store_true", dest="halfway", default=False,
                      help="Only process halfway through (e.g., when running forward and reverse.")
    parser.add_option("--glossaryonly", action="store_true", dest="glossary_only", default=False,
                      help="Only process the glossary (quicker).")
    parser.add_option("--pw", dest="httpPassword", default=None,
                      help="Password for the server")
    parser.add_option("-r", "--reverse", dest="run_in_reverse", action="store_true", default=False,
                      help="Whether to run the selected files in reverse order")
    parser.add_option("--resetcore",
                      action="store_true", dest="resetCoreData", default=False,
                      help="clear (delete) any data in the selected cores (author core is reset with the fulltext core).")
    parser.add_option("--seed",
                      dest="randomizer_seed", default=None,
                      help="Seed so data update files don't collide if they start writing at exactly the same time.")
    parser.add_option("--sub", dest="subFolder", default=None,
                      help="Sub folder of root folder specified via -d to process")
    parser.add_option("--test", dest="testmode", action="store_true", default=False,
                      help="Run Doctests")
    parser.add_option("--userid", dest="httpUserID", default=None,
                      help="UserID for the server")
    parser.add_option("--verbose", action="store_true", dest="display_verbose", default=False,
                      help="Display status and operational timing info as load progresses.")
    parser.add_option("--nofiles", action="store_true", dest="no_files", default=False,
                      help="Don't load any files (use with whatsnewdays to only generate a whats new list).")
    parser.add_option("--whatsnewdays", dest="daysback", default=None,
                      help="Generate a log of files added in the last n days (1==today), rather than for files added during this run.")
    parser.add_option("--whatsnewfile", dest="whatsnewfile", default=None,
                      help="File name to force the file and path rather than a generated name for the log of files added in the last n days.")

    (options, args) = parser.parse_args()
    
    if options.glossary_only and options.file_key is None:
        options.file_key = "ZBK.069"

    if options.testmode:
        import doctest
        doctest.testmod()
        print ("Fini. SolrXMLPEPWebLoad Tests complete.")
        sys.exit()

    main()
