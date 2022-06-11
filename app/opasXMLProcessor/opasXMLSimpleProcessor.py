#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
# Disable many annoying pylint messages, warning me about variable naming for example.
# yes, in my Solr code I'm caught between two worlds of snake_case and camelCase.

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2022, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2022.0606" 
__status__      = "Development"

programNameShort = "opasXMLProcessor"
import lxml
import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

print(
    f""" 
        {programNameShort} - Open Publications-Archive Server (OPAS) - XML Processor (early "simple" version)
    
        Read the XML KBD3 files specified and create EXP_ARCH1 files (eventually maybe integrated and directly import to Solr, eliminating the EXP_ARCH1 files).
        
        See documentation at:
          https://github.com/Psychoanalytic-Electronic-Publishing/OpenPubArchive-Content-Server/wiki/TBD  *** TBD ***
        
        Example Invocation:
                $ python opasXMLSimpleProcessor.py
                
        Important option choices:
         -h, --help      List all help options
         -a              Force update of files (otherwise, only updated when the data is newer)
         --sub           Start with this subfolder of the root (can add sublevels to that)
         --key:          Do just one file with the specified PEP locator (e.g., --key AIM.076.0309A)
         --nocheck       Don't prompt whether to proceed after showing setting/option choices
         --reverse       Process in reverse
         --halfway       Stop after doing half of the files, so it can be run in both directions
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
#import random
import pysolr
import localsecrets
import re
import os
import os.path
import pathlib
from opasFileSupport import FileInfo

#import datetime as dtime
from datetime import datetime
import logging
logger = logging.getLogger(programNameShort)

from optparse import OptionParser

from lxml import etree
import mysql.connector

import configLib.opasCoreConfig
from configLib.opasCoreConfig import solr_authors2, solr_gloss2

import localsecrets

import modelsOpasCentralPydantic
import opasSolrLoadSupport
import opasXMLHelper as opasxmllib
import opasCentralDBLib
import opasProductLib
import opasGenSupportLib as opasgenlib
import opasFileSupport
# import opasAPISupportLib
from opasLocator import Locator
import PEPBookInfo

import PEPJournalData # eventually merge with opasProductLib
# import loaderConfig
# Override Configuration file for opasDataLoader
file_match_pattern = "\((bKBD3|bSeriesTOC)\)\.(xml|XML)$"

#detect data is on *nix or windows system
if "AWS" in localsecrets.CONFIG or re.search("/", localsecrets.IMAGE_SOURCE_PATH) is not None:
    path_separator = "/"
else:
    path_separator = r"\\"

# Module Globals
bib_total_reference_count = 0

def xml_update(root, pepxml, artInfo, ocd):
    ret_val = None
    # write issn and id to artinfo
    xml_artinfo = pepxml.find("artinfo")
    source_row = ocd.get_sources(src_code=artInfo.src_code)
    known_books = PEPBookInfo.PEPBookInfo()

    try:
        source_info = source_row[1][0]
        # gather info needed about source
        if artInfo.src_code is not None:
            if artInfo.art_issn is None:
                xml_artinfo.attrib["ISSN"] = source_info["ISSN"]
            else:
                if artInfo.art_issn is not None:
                    xml_artinfo.attrib["ISSN"] = artInfo.art_issn
                else:
                    if artInfo.art_isbn is None:
                        xml_artinfo.attrib["ISBN"] = source_info["ISBN-13"]
                    else:
                        xml_artinfo.attrib["ISBN"] = artInfo.art_isbn

    except Exception as e:
        print (e)
    
    if artInfo.art_id is not None: xml_artinfo.set("id", artInfo.art_id)
    if artInfo.art_type is not None: xml_artinfo.set("arttype", artInfo.art_type)
    if artInfo.start_sectname is not None: xml_artinfo.set("newsecnm", artInfo.start_sectname)
    if artInfo.start_sectlevel is not None: xml_artinfo.set("newseclevel", artInfo.start_sectlevel)                
                
    # write authindexid to aut
    
    # tag glossary words
    
    # add nextpgnum with id to n, possibly filling in prefixused
    pgnbr_add_next_attrib(pepxml)
    
    # add links to biblio entries, rx to be
    if artInfo.ref_count > 0:
        bibReferences = pepxml.xpath("/pepkbd3//be")  # this is the second time we do this (also in artinfo, but not sure or which is better per space vs time considerations)
        if options.display_verbose:
            print(("   ...Processing %s references for links." % (artInfo.ref_count)))

        #processedFilesCount += 1
        bib_total_reference_count = 0
        ocd.open_connection(caller_name="processBibliographies")
        for ref in bibReferences:
            # bib_entry_text = ''.join(ref.itertext())
            bib_pgstart = None
            bib_pgend = None
            ref_id = ref.attrib["id"]
            # see if it's already in table
            bib_saved_entry_tuple = ocd.get_references_from_biblioxml_table(article_id=artInfo.art_id, ref_local_id=ref_id)
            if bib_saved_entry_tuple is not None:
                bib_saved_entry = bib_saved_entry_tuple[0]
            else:
                bib_saved_entry = modelsOpasCentralPydantic.Biblioxml()
            
            # merge record info
            bib_total_reference_count += 1
            bib_entry = opasSolrLoadSupport.BiblioEntry(artInfo, ref)
            # locator = f"{bib_entry.sourcecode}.{bib_entry.volume}.{bib_entry.pgrg}"
            if not opasgenlib.is_empty(bib_entry.pgrg):
                bib_pgstart, bib_pgend = bib_entry.pgrg.split("-")

            # TODO: Populate source code for books as well before calling here.
            bk_locator = None
            if bib_entry.source_type != "book":
                print (bib_saved_entry.bib_rx,
                       bib_entry.author_list_str, 
                       bib_entry.source_title,
                       bib_entry.sourcecode,
                       bib_entry.volume,
                       bib_entry.year,
                       bib_entry.pgrg,
                       )

                if not opasgenlib.is_empty(bib_entry.sourcecode):
                    locator = Locator(strLocator=None,
                                       jrnlCode=bib_entry.sourcecode, 
                                       jrnlVolSuffix="", 
                                       jrnlVol=bib_entry.volume, 
                                       jrnlIss=None, 
                                       pgVar="A", 
                                       pgStart=bib_pgstart, 
                                       jrnlYear=bib_entry.year, 
                                       localID=ref_id, 
                                       keepContext=1, 
                                       forceRoman=False, 
                                       notFatal=True, 
                                       noStartingPageException=True, 
                                       filename=artInfo.filename)
                    # need to check if it's whole, and if it works, but for now.
                    ref.attrib["rx"] = locator.articleID()
                    search_str = f"//be[@id='{ref_id}']"
                    print (opasxmllib.xml_xpath_return_xmlstringlist(pepxml, search_str, default_return=None))
                else:
                    locator = None
                    print ("Skipped: ", bib_saved_entry)
                
                
            else:
                bk_locator_str, match_val, whatever = known_books.getPEPBookCodeStr(bib_entry.ref_entry_text)
                if bk_locator_str is not None:
                    print (f"Added Reference Locator {bk_locator}, {match_val}, {whatever}")
                    ref.attrib["rx"] = bk_locator_str 
                    search_str = f"//be[@id='{ref_id}']"
                    print (opasxmllib.xml_xpath_return_xmlstringlist(pepxml, search_str, default_return=None))
                    
                else:
                    locator = None
                    print ("Skipped: ", bib_entry.ref_entry_text)

            # compute rx
            
            # opasSolrLoadSupport.add_reference_to_biblioxml_table(ocd, artInfo, bib_entry)

        #try:
            #ocd.db.commit()
        #except mysql.connector.Error as e:
            #print("SQL Database -- Biblio Commit failed!", e)
        ocd.close_connection(caller_name="processBibliographies")
    
    ret_val = root
    return ret_val

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

#----------------------------------------------------------------------------------------------------------------
def pgnbr_add_next_attrib(pepxml):
    """
    Walk through page number "n" elements, and record page number sequence.  Add the next page number to
       the nextpgnum attribute of the n element.
    """

    # Walk through page number "n" elements, and record page number sequence
    n_nodes = pepxml.findall("**/n")
    lastPage = None
    count = 0
    # walk through the nodes backwards.
    for node in n_nodes[::-1]: # backwards
        pgNumber = node.text
        if lastPage is not None:
            node.set("nextpgnum", lastPage)
            count += 1
        # record the new pagenumber for the next node
        lastPage = pgNumber # .format()

    return count

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
            if options.forceRebuildAllFiles == True:
                msg = "Forced Rebuild - All files added, regardless of whether they are the same as in Solr."
                logger.info(msg)
                print (msg)
                
            print(80*"*")
            print(f"Database will be updated. Location: {localsecrets.DBHOST}")
            print(80*"*")
    
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
        # print (f"Locating files for processing at {start_folder} with pattern {loaderConfig.file_match_pattern}. Started at ({time.ctime()}).")
        if options.file_key is not None:  
            # print (f"File Key Specified: {options.file_key}")
            # Changed from opasDataLoader (reading in bKBD3 files rather than EXP_ARCH1)
            pat = fr"({options.file_key}.*){file_match_pattern}"
            print (f"Reading {pat} files")
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
            pat = fr"(.*?){file_match_pattern}"
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
            print (f"Processing started ({time.ctime()}).  Examining files.")
            
            for n in filenames:
                fileTimeStart = time.time()
                file_updated = False
                if not options.forceRebuildAllFiles:                    
                    if not options.display_verbose and processed_files_count % 100 == 0 and processed_files_count != 0:
                        print (f"Processed Files ...loaded {processed_files_count} out of {files_found} possible.")
    
                    if not options.display_verbose and skipped_files % 100 == 0 and skipped_files != 0:
                        print (f"Skipped {skipped_files} so far...loaded {processed_files_count} out of {files_found} possible." )
                    
                    if 0: # file_is_already_processed(filename=n.basename, timestamp_str=n.timestamp_str):
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
                # Read file    
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
                pepxml = etree.fromstring(opasxmllib.remove_encoding_string(fileXMLContents), parser)
                root = pepxml.getroottree()
        
                # save common document (article) field values into artInfo instance for both databases
                artInfo = opasSolrLoadSupport.ArticleInfo(sourceDB.sourceData, pepxml, artID, logger)
                artInfo.filedatetime = n.timestamp_str
                artInfo.filename = base
                artInfo.file_size = n.filesize
                artInfo.file_updated = file_updated
                artInfo.file_create_time = n.create_time
                
                
                
                # make changes to the XML
                modified_xml_file_contents = xml_update(root, pepxml, artInfo, ocd)
                # make changes
                
                # fix front matter
                # tag glossary entries
                # link biblio entries
                # write output file
                # fname = n.filespec("bKBD3", "bEXP_TEST")
                fname = f"{artID}(bEXP_TEST).xml"  # *** TBD *** one file for now.
                fname = str(n.filespec.absolute())
                fname = fname.replace("bKBD3", "bEXP_TEST")
                
                msg = f"Writing file {fname}"
                print (msg)
                root.write(fname, encoding="utf8", method="xml", pretty_print=True)
                #with open(fname, 'w', encoding="utf8") as fo:
                    ##fo.write( f'<?xml version="1.0" encoding="UTF-8"?>\n')
                    #fo.write(root.tostring())

                    
                # walk through bib section and add to refs core database
                precommit_file_count += 1
                if 0: # not in XMLSimpleProcessor, but code to keep in sync with XMLDataLoader
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
                            # print (f"   ...NewSec Workaround: Clearing newsecnm for {artInfo.art_id}")
                            artInfo.start_sectname = None # clear it so it's not written to solr, this is not the first article
                        else:
                            if options.display_verbose:
                                print (f"   ...NewSec {artInfo.start_sectname} found in {artInfo.art_id}")
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

                    
                # Add to the references table
                if 0: # options.biblio_update:
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
                            if bib_entry.source_type != "book":
                                print (bib_entry.author_list_str, 
                                       bib_entry.source_title,
                                       bib_entry.sourcecode,
                                       bib_entry.volume,
                                       bib_entry.year,
                                       bib_entry.pgrg)
                                
                            opasSolrLoadSupport.add_reference_to_biblioxml_table(ocd, artInfo, bib_entry)
    
                        try:
                            ocd.db.commit()
                        except mysql.connector.Error as e:
                            print("SQL Database -- Biblio Commit failed!", e)
                            
                        ocd.close_connection(caller_name="processBibliographies")
    
                # close the file, and do the next
                if options.display_verbose:
                    print(("   ...Time: %s seconds." % (time.time() - fileTimeStart)))
        
            print (f"Conversion process complete ({time.ctime()}).")
            if processed_files_count > 0:
                try:
                    print ("Performing final commit.")
                except Exception as e:
                    print(("Exception: ", e))
                else:
                    # Use date time as seed, hoping multiple instances don't get here at the same time
                    # but only if caller did not specify
                    if randomizer_seed is None:
                        randomizer_seed = int(datetime.utcnow().timestamp())
    
        # end of docs

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
            msg = f"Finished! Converted {processed_files_count} documents. Total file processing time: {elapsed_seconds:.2f} secs ({elapsed_minutes:.2f} minutes.)"
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
    parser = OptionParser(usage="%prog [options] - PEP XML Simple Data Processor", version=f"%prog ver. {__version__}")
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
    parser.add_option("--seed",
                      dest="randomizer_seed", default=None,
                      help="Seed so data update files don't collide if they start writing at exactly the same time.")
    parser.add_option("--sub", dest="subFolder", default=None,
                      help="Sub folder of root folder specified via -d to process")
    parser.add_option("--test", dest="testmode", action="store_true", default=False,
                      help="Run Doctests")
    parser.add_option("--userid", dest="httpUserID", default=None,
                      help="UserID for the server")
    parser.add_option("--verbose", action="store_true", dest="display_verbose", default=True,
                      help="Display status and operational timing info as load progresses.")
    parser.add_option("--nofiles", action="store_true", dest="no_files", default=False,
                      help="Don't load any files (use with whatsnewdays to only generate a whats new list).")

    (options, args) = parser.parse_args()
    
    if options.glossary_only and options.file_key is None:
        options.file_key = "ZBK.069"

    if options.testmode:
        import doctest
        doctest.testmod()
        print ("Fini. opasXMLSimpleProcessor Tests complete.")
        sys.exit()

    main()
