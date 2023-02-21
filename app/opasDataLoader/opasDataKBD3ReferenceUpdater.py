#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#Copyright 2012-2018 Neil R. Shapiro

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2023"
__license__     = "Apache 2.0"
__version__     = "2023.0216/v1.0.001"   
__status__      = "Development"

programNameShort = "opasDataKBD3DReferenceUpdater"

border = 80 * "*"
print (f"""\n
        {border}
            {programNameShort} - Open Publications-Archive Server (OPAS) Reference Updater
                            Version {__version__}
        {border}
        """)

help_text = (
    fr""" 
        - Read the refcorrections table and integrate the replacement references into the KBD3 files.
        
        Example Invocation:
                $ python opasDataKBD3DReferenceUpdater.py
                
        Important option choices:
         -h, --help         List all help options
         -a                 Process all records
         --key             Do just records with the specified PEP locator (e.g., --key AIM.076.0309A)
""")
    
import sys
sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')

# import string, sys, copy, re
import logging
logger = logging.getLogger(__name__)
# import re
import time
from optparse import OptionParser
from loggingDebugStream import log_everywhere_if

import opasConfig
# import opasGenSupportLib as opasgenlib
import opasBiblioSupport
import opasCentralDBLib
import PEPBookInfo
known_books = PEPBookInfo.PEPBookInfo()

# import opasPySolrLib
# from opasLocator import Locator
#import opasXMLHelper
# import opasXMLProcessor
#import opasArticleIDSupport
# import models
# import PEPJournalData
# import PEPReferenceParserStr

gDbg1 = 0	# details
gDbg2 = 1	# High level

LOWER_RELEVANCE_LIMIT = 35

ocd = opasCentralDBLib.opasCentralDB()
import lxml.etree as etree
import lxml
import opasFileSupport
import opasArticleIDSupport
# from opasArticleIDSupport import ArticleInfo
import opasXMLHelper as opasxmllib
import localsecrets
CONTROL_FILE_PATH = localsecrets.XML_ORIGINALS_PATH

sqlSelect = ""
flex_fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY,
                         secret=localsecrets.S3_SECRET,
                         root=CONTROL_FILE_PATH) 

def get_article_info(art_id, filename_base, fullfilename):
    fileXMLContents, input_fileinfo = flex_fs.get_file_contents(fullfilename)
    parsed_xml = etree.fromstring(opasxmllib.remove_encoding_string(fileXMLContents), parser)
    ret_val = parsed_xml, opasArticleIDSupport.ArticleInfo(parsed_xml=parsed_xml, art_id=art_id, filename_base=filename_base, fullfilename=fullfilename, logger=logger)
    return ret_val # artInfo

def update_via_correction_set(ocd=ocd,
                              art_id = None, # can use SQL wildcards
                              verbose=True
                             ):
    """
    >> update_set = "SingleTest1", "select * from api_biblioxml2 where art_id='APA.001.0007A' and ref_local_id='B002'"
    >> update_via_correction_set(ocd, sql_set_select=update_set[1])

    """
    fname = "update_via_correction_set"
    ret_val = None
    parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
    cumulative_time_start = time.time()
    corrected_articles = opasBiblioSupport.get_reference_correction_articles(ocd=ocd, article_id=art_id)
    print (f"There are {len(corrected_articles)} corrected articles to process.")
    rebuild_count = 0 
    for article in corrected_articles:
        art_id = article.get("art_id", None)
        if ocd.article_exists(art_id):
            file_error = False
            biblio_entries = opasBiblioSupport.get_reference_correction_list(ocd=ocd, article_id=art_id)
            if len(biblio_entries) > 0:
                art_id_records = ocd.get_article_records(art_id)
                article = art_id_records[0]
                filename = article["fullfilename"]
                filename = filename.replace("bEXP_ARCH1", "bKBD3")
                print (80*"-")
                print (f"{rebuild_count}: Replacing {len(biblio_entries)} references in {filename} from opasloader_refcorrections.")
                fileXMLContents, input_fileinfo = flex_fs.get_file_contents(filename)
                parsed_xml = etree.fromstring(opasxmllib.remove_encoding_string(fileXMLContents), parser)
                counter = 0
                for ref_model in biblio_entries:
                    counter += 1
                    bibref_xml = parsed_xml.xpath(f"//be[@id='{ref_model.ref_local_id}']")
                    if bibref_xml:
                        bibrefs_parent = bibref_xml[0].getparent()
                        existing_ref_xml = bibref_xml[0].text
                        # new_ref_text = ref_model.ref_text
                        new_ref_xml = ref_model.ref_xml
                        # new_node = lxml.etree.XML(new_ref_xml)
                        new_parsed_xml = etree.fromstring(opasxmllib.remove_encoding_string(new_ref_xml), parser)
                        print (f"\t...{counter}:Replacing Record ID:{ref_model.art_id}/{ref_model.ref_local_id}")
                        print (f"\t\t...Old Ref:{existing_ref_xml}")
                        print (f"\t\t...New Ref:{ref_model.ref_xml}")
                        try:
                            bibrefs_parent.replace(bibref_xml[0], new_parsed_xml)
                        except Exception as e:
                            print (80*"!")
                            print (f"{rebuild_count} *** Skipping file {filename} due to Error {e}")
                            print (80*"!")
                            file_error = True
                            break # forget it.  Do next file.
                            
                # now write it
                if not file_error:
                    filename_back = filename.replace(".xml", ".bakxml")
                    flex_fs.rename(filename, filename_back, path=localsecrets.XML_ORIGINALS_PATH)
                    file_text = lxml.etree.tostring(parsed_xml, encoding="utf8").decode("utf-8")
                    output_file = flex_fs.create_text_file(filename, data=file_text, delete_existing=True)
                    if output_file:
                        rebuild_count += 1
                        opasBiblioSupport.update_reference_correction_status(ocd, art_id, verbose=verbose)
                        log_everywhere_if(options.display_verbose , level="info", msg=f"\tUpdated {filename}")
                    else:
                        log_everywhere_if(options.display_verbose, level="error", msg=f"\t...There was a problem writing {filename}.")
        else:
            print (f"Warning: Article {art_id} does not exist.")
            
    print (80 * "-")
    timeEnd = time.time()
    elapsed_seconds = timeEnd-cumulative_time_start # actual processing time going through files
    elapsed_minutes = elapsed_seconds / 60
    if counter > 0:
        msg = f"Files per elapsed min: {rebuild_count/elapsed_minutes:.4f}"
        logger.info(msg)
        print (msg)
    
    msg = f"Finished! {rebuild_count} files updated from {counter} references. Total scan/update time: {elapsed_seconds:.2f} secs ({elapsed_minutes:.2f} minutes.) "
    logger.info(msg)
    print (msg)
    
    # return session model object
    return rebuild_count # 

def test_runs():
    do_walk_set = True
    do_clean = False
    do_doctest = False
    walk_set = [
                  ("Freud", "select * from api_biblioxml2 where ref_rx is NULL and ref_authors like '%Freud%' and ref_rx_confidence=0"),
                  ("FreudTest", "select * from api_biblioxml2 where art_id LIKE 'APA.017.0421A'")
               ]
        
    if do_doctest:
        import doctest
        doctest.testmod(optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
    
    print ("Fini. Tests or Processing complete.")
    
# -------------------------------------------------------------------------------------------------------
# run it!
if __name__ == "__main__":
    global options  # so the information can be used in support functions

    options = None
    parser = OptionParser(usage="%prog [options] - PEP Data Linker", version=f"%prog ver. {__version__}")

    parser.add_option("-a", "--all", action="store_true", dest="process_all", default=False,
                      help="Option to force all records to be checked.")

    parser.add_option("--key", dest="file_key", default=None,
                      help="Key for a single file to load, e.g., AIM.076.0269A.  Use in conjunction with --sub for faster processing of single files on AWS")

    parser.add_option("-l", "--loglevel", dest="logLevel", default=logging.ERROR,
                      help="Level at which events should be logged (DEBUG, INFO, WARNING, ERROR")

    # --load option still the default.  Need to keep for backwards compatibility, at least for now (7/2022)

    parser.add_option("--test", dest="testmode", action="store_true", default=False,
                      help="Run Doctests")

    parser.add_option("--verbose", action="store_true", dest="display_verbose", default=True,
                      help="Display status and operational timing info as load progresses.")

    (options, args) = parser.parse_args()
    # set toplevel logger to specified loglevel
    logger = logging.getLogger()
    logger.setLevel(options.logLevel)
    # get local logger
    logger = logging.getLogger(programNameShort)
    
    if options.display_verbose: print (help_text)

    biblio_refs_matching_artid = f"""select *
                                     from opasdataloader_refcorrections
                                     where art_id RLIKE '%s'
                                  """
    
    if options.file_key:
        article_id = options.file_key
    elif options.process_all:
        article_id = '%.%.%'
    else:
        print ("No records selected")
        exit()

    update_via_correction_set(ocd, art_id=article_id, verbose=True)
    print ("Finished!")
