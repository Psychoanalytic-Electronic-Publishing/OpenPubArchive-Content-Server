#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
# Disable many annoying pylint messages, warning me about variable naming for example.
# yes, in my Solr code I'm caught between two worlds of snake_case and camelCase.

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2022.0801/v1.0.0" 
__status__      = "Development"

programNameShort = "opasGoogleMetadataExport"

import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

print(
    f""" 
    {programNameShort} - Open Publications-Archive Server (OPAS) - Google Metadata Exporter
    
        Create Google Metadata from the opas Database
        
        Example Invocation:
                $ python {programNameShort}.py --recordsperfile=8000 --maxrecords=200000 --bucket pep-web-google
                
        Help for option choices:
         -h, --help  List all help options
    """
)

import sys
import os
import re
import logging

sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')

import localsecrets
import opasFileSupport

logger = logging.getLogger(programNameShort)

from optparse import OptionParser



# -------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    options = None
    parser = OptionParser(usage="%prog [options] - PEP Google Metadata Generator", version=f"%prog ver. {__version__}")
    parser.add_option("-l", "--loglevel", dest="logLevel", default=logging.ERROR,
                      help="Level at which events should be logged (DEBUG, INFO, WARNING, ERROR")
    parser.add_option("-c", "--clear", dest="clearmetadata", action="store_true", default=False,
                      help="Clear prior metadata files (delete files in path/bucket matching metadata.*)")
    parser.add_option("-t", "--test", dest="testmode", action="store_true", default=False,
                      help="Run Doctests.  Will run a small sample of records and total output")
    parser.add_option("-r", "--recordsperfile", dest="recordsperfile", type="int", default=8000,
                      help="Max Number of records per file")
    parser.add_option("-m", "--maxrecords", dest="maxrecords", type="int", default=200000,
                      help="Max total records to be exported")
    parser.add_option("-b", "--bucket", dest="bucket", type="string", default=localsecrets.SITEMAP_PATH,
                      help="Bucket or Local Path to write sitemap files on local system or S3 (on AWS must be a bucket)")

    (options, args) = parser.parse_args()
    if options.testmode:
        import doctest
        doctest.testmod()
        print ("Fini. Tests complete.")
    else:
        ret_val = google_metadata_generator(path=options.bucket, size=options.recordsperfile, max_records=options.maxrecords, clear_sitemap=options.clearsitemap)
        print ("Finished!")

    sys.exit()
