#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
# Disable many annoying pylint messages, warning me about variable naming for example.

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2021.0218.1" 
__status__      = "Development"

programNameShort = "opasBuildControl"
print(
    f""" 
    {programNameShort} - Open Publications-Archive Server (OPAS) - Remote Execution Protocol
    
        Manage the complete run process by loading txt files to the XML folder.
        
        Watch the XML folder for one of the text files.
        Rename it to suffix it with -running.txt
        When it finishes running, delete the .txt file

    """)
    
import localsecrets
import opasFileSupport
import time
CONTROL_FILE_PATH = localsecrets.XML_ORIGINALS_PATH

FILE_RUN_FULL_UPDATE = "run-full-update.txt"
FILE_RUN_CURRENT_UPDATE = "run-current-update.txt"
FILE_RUN_FULL_REBUILD = "run-full-rebuild.txt"
FILE_GO_LIVE = "run-send-to-production.txt"
FILE_STOP = "run-stop-monitoring.txt"
INTERVAL = 9
ACTION = 2

flex_fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY,
                         secret=localsecrets.S3_SECRET,
                         root=CONTROL_FILE_PATH) 

def file_exists(document_id, path=CONTROL_FILE_PATH):
    ret_val = flex_fs.exists(filespec=document_id, path=path)
    return ret_val

if file_exists(FILE_RUN_CURRENT_UPDATE, path=CONTROL_FILE_PATH):
    # check current and free folder subtree for new or updated data, process all the way to stage
    print ("Run Update (current) and free subtrees")
    flex_fs.rename(FILE_RUN_CURRENT_UPDATE, FILE_RUN_CURRENT_UPDATE+"-running.txt")
    
    time.sleep(ACTION)  # Placeholder for action call
    
    flex_fs.delete(FILE_RUN_CURRENT_UPDATE+"-running.txt")
    
   
elif file_exists(FILE_RUN_FULL_UPDATE, path=CONTROL_FILE_PATH):
    # check current and archive folders for new data, run update but keep the database/solr data intact, process all the way to stage
    print ("Run Update, archive, free and current subtrees")
    flex_fs.rename(FILE_RUN_FULL_UPDATE, FILE_RUN_FULL_UPDATE+"-running.txt")
    
    time.sleep(ACTION)  # Placeholder for action call
    
    flex_fs.delete(FILE_RUN_FULL_UPDATE+"-running.txt")
    
elif file_exists(FILE_RUN_FULL_REBUILD, path=CONTROL_FILE_PATH):
    
    print ("Run Full Build, all subtrees, fresh database and schema")
    flex_fs.rename(FILE_RUN_FULL_REBUILD, FILE_RUN_FULL_REBUILD+"-running.txt")
    
    time.sleep(ACTION)  # Placeholder for action call
    
    flex_fs.delete(FILE_RUN_FULL_REBUILD+"-running.txt")

elif file_exists(FILE_GO_LIVE, path=CONTROL_FILE_PATH):
    print ("Push Stage to Production")
    flex_fs.rename(FILE_GO_LIVE, FILE_GO_LIVE+"-running.txt")
    
    time.sleep(ACTION)  # Placeholder for action call
    
    flex_fs.delete(FILE_GO_LIVE+"-running.txt")
        
    
