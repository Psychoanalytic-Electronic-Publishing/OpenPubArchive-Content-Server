programNameShort = "opasDatabaseArchival"

__copyright__   = "Copyright 2023, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2023.0825.1" 

import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

border = 80 * "*"
print (f"""\n
        {border}
            {programNameShort} - Open Publications-Archive Server (OPAS) Database Archival
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
         --verbose          Display progress information
         
        Note:
          S3 is set up with root=localsecrets.FILESYSTEM_ROOT (default).  The root must be the bucket name.
    """
)

import sys
sys.path.append('../config')
sys.path.append('../libs')

import time
import re
import os
import subprocess
from datetime import datetime
from loggingDebugStream import log_everywhere_if
import logging
from optparse import OptionParser
import localsecrets

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

    logger = logging.getLogger(programNameShort)
    logger.setLevel(options.logLevel)
    logger.info('Started at %s', datetime.today().strftime('%Y-%m-%d %H:%M:%S"'))

    timeStart = time.time()
    
    print((80*"-"))
    log_everywhere_if(True, "info", f"Processing started at ({time.ctime()}).")

    print("Exporting table data")

    exportFilename = f"{options.table_name}-2023-08-27-{time.time() * 1000}.sql"

    result = subprocess.run(
        f"mysqldump -h {localsecrets.DBHOST} -u {localsecrets.DBUSER} -p{localsecrets.DBPW} --port=3306 --set-gtid-purged=OFF --opt --compress opascentral {options.table_name} --where=\"last_update <= \"2023-08-27\"\" > {exportFilename}",
        shell=True,
    )

    print("Finished exporting table data")

    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    for f in files:
        print(f)


    # Upload to bucket

    print("Cleaning table data")

    
    # ---------------------------------------------------------
    # Closing time
    # ---------------------------------------------------------
    timeEnd = time.time()
    log_everywhere_if(True, "info", 'Processing finished. %s' % datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
    elapsed_seconds = timeEnd-timeStart # actual processing time going through files
    elapsed_minutes = elapsed_seconds / 60
    msg = f"Elapsed min: {elapsed_minutes:.2f}"
    log_everywhere_if(True, "info", msg)
    log_everywhere_if(True, "info", 80 * "-")

# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    global options  # so the information can be used in support functions
    options = None
    parser = OptionParser(usage="%prog [options] - PEP DataCleaner", version=f"%prog ver. {__version__}")
    parser.add_option("-l", "--loglevel", dest="logLevel", default=logging.ERROR,
                      help="Level at which events should be logged (DEBUG, INFO, WARNING, ERROR")
    parser.add_option("--verbose", action="store_true", dest="display_verbose", default=False,
                      help="Display status and operational timing info as load progresses.")
    parser.add_option("--nohelp", action="store_true", dest="no_help", default=False,
                      help="Turn off front-matter help")
    parser.add_option("--table", dest="table_name", default=None,
                      help="Name of table to export")

    (options, args) = parser.parse_args()

    if not options.table_name:
        parser.error("Table name is required")
    
    if not options.no_help:
        log_everywhere_if(options.display_verbose, "info", help_text)
    
    main()