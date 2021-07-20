#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
# Disable many annoying pylint messages, warning me about variable naming for example.
# yes, in my Solr code I'm caught between two worlds of snake_case and camelCase.

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2021.0719/v1.0.0" 
__status__      = "Development"

programNameShort = "opasSiteMapper"
import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

print(
    f""" 
    {programNameShort} - Open Publications-Archive Server (OPAS) - SiteMapper
    
        Create Google Sitemaps from the opas Database
        
        Example Invocation:
                $ python {programNameShort}.py --recordsperfile=8000 --maxrecords=200000 --bucket pep-web-google
                
        Help for option choices:
         -h, --help  List all help options
    """
)

import sys
sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')

import localsecrets
import re

import logging
logger = logging.getLogger(programNameShort)

from optparse import OptionParser

#detect data is on *nix or windows system
if "AWS" in localsecrets.CONFIG or re.search("/", localsecrets.IMAGE_SOURCE_PATH) is not None:
    path_separator = "/"
else:
    path_separator = r"\\"

#------------------------------------------------------------------------------------------------------
def sitemapper( path: str=localsecrets.SITEMAP_PATH, # local path or bucket for AWS
                size: int=10,                        # records per file
                max_records: int=200                 # max records
               ):
    
    """
    ## Function
       ### Generate a Sitemap for Google.

    ## Return Type
       Dictionary or SiteMapInfo model pointing to sitemapindex and list of files,
       e.g.,
       
            {
               "siteMapIndex": 'pep-web-google/sitemapindex.xml',
               "siteMapList": [
                 "pep-web-google/sitemap1.xml",
                 "pep-web-google/sitemap2.xml",
                 "pep-web-google/sitemap3.xml",
                 "pep-web-google/sitemap4.xml"
               ]
            }

    >>> ret = sitemapper(size=10, max_records=200)
    >>> ret["siteMapIndexFile"]
    'pep-web-google/sitemapindex.xml'
  
    """
    import opasSiteMap
    ret_val = {
        "siteMapIndexFile": "", 
        "siteMapList" : []
    }
    
    try:
        SITEMAP_OUTPUT_FILE = path + localsecrets.PATH_SEPARATOR + "sitemap" # don't include xml extension here, it's added
        SITEMAP_INDEX_FILE = path + localsecrets.PATH_SEPARATOR + "sitemapindex.xml"
    except Exception as e:
        raise Exception(f"Error {e}.")
   
    try:
        # returns a list of the sitemap files (since split)
        sitemap_list = opasSiteMap.metadata_export(SITEMAP_OUTPUT_FILE, total_records=max_records, records_per_file=size)
        opasSiteMap.opas_sitemap_index(output_file=SITEMAP_INDEX_FILE, sitemap_list=sitemap_list)
        ret_val["siteMapIndexFile"] = SITEMAP_INDEX_FILE
        ret_val["siteMapList"] = sitemap_list

    except Exception as e:
        ret_val=f"Sitemap Error: {e}"
        logger.error(ret_val)
        raise Exception(ret_val)
            
    return ret_val
    
# -------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    options = None
    parser = OptionParser(usage="%prog [options] - PEP SiteMap Generator", version=f"%prog ver. {__version__}")
    parser.add_option("-l", "--loglevel", dest="logLevel", default=logging.ERROR,
                      help="Level at which events should be logged (DEBUG, INFO, WARNING, ERROR")
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
        ret_val = sitemapper(path=options.bucket, size=options.recordsperfile, max_records=options.maxrecords)
        print (ret_val["siteMapIndexFile"])
        print (ret_val["siteMapList"])
        print ("Finished!")

    sys.exit()
