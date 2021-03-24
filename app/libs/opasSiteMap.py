#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
# doctest_ellipsis.py

"""
Sitemap.py


"""
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2021.0301.1"
__status__      = "Development"

# from xml.sax import SAXParseException
import sys
import os.path
import datetime
import logging
logger = logging.getLogger(__name__)

from fastapi import HTTPException

import codecs
sys.path.append('./libs/configLib')

import opasPySolrLib

SITEMAP_LOC = r"development.org"
SITEMAP_DATE = "2021-03-01"

def opas_sitemap_index(output_file="../sitemapindex", sitemap_list=[]):
   """
   Create a site index
   Call metadata_export to populate the index files.
   Create the index of the returned file names

   >>> sitemap_list = metadata_export(outputFileName="../sitemap", total_records=1000, records_per_file=200)
   >>> list = opas_sitemap_index(output_file="../sitemapindex", sitemap_list=sitemap_list)
   >>> len(list) > 0
   True
   
   """
   dtformat = '%Y-%m-%dT%H:%M:%S%Z'
   
   try:
      ret_val = ""
      enf = codecs.open(output_file,'w','utf-8')
      sm_index_head = f'''
         <?xml version="1.0" encoding="UTF-8"?>\n
         <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n
         '''
   
      mod_time = datetime.datetime.now().strftime(dtformat)
      enf.write(sm_index_head)
      for sitemap in sitemap_list:
         sitemap_base = os.path.basename(sitemap)
         record = f'''
            <sitemap>
               <loc>{sitemap_base}</loc>
               <lastmod>{mod_time}</lastmod>
            </sitemap>\n
         '''
         enf.write(record)
         ret_val += record
   
      enf.write("</sitemapindex>\n")
      enf.close()
   except Exception as err:
      ret_val = f"Error: {err}"
      logger.error(ret_val)
      
   return ret_val
     
     
#--------------------------------------------------------------------------------
def metadata_export(outputFileName="../sitemap", total_records=140000, records_per_file=10000):
   """
   Populate the build table from the articles table.
   Create the include list by calling class member	writeFFFInclude

   The intermediate tables are built, rather than using a transitional query, in order to
   correctly populate the author information, which is used for sorting.

   >> metadata_export()
   
   """

   retVal = 0
   base_url = "https://stage.pep-web.rocks/read/document"
   header = '<?xml version="1.0" encoding="utf-8" ?>\n<!DOCTYPE articles SYSTEM "googlearticles.dtd">\n'
   sitemap_list = []
   file_count = 0
   rec_count = 0
   try:
      for rec_group in range(0, total_records, records_per_file):
         if rec_count > total_records: # don't write more than total_records
            break
         try:
            results = opasPySolrLib.search("art_level:1", 
                                           summaryField="art_id, file_last_modified", 
                                           returnStartAt=rec_group, 
                                           returnLimit=records_per_file)
         except Exception as err:
            raise HTTPException(404, detail=err)
            
         if len(results.docs) == 0: # if there are no more records, stop creating files
            break
         else: # write the file
            file_count += 1
            filename = f"{outputFileName}{file_count}.xml"
            sitemap_list.append(filename)
            enf = codecs.open(filename,'w','utf-8')
            logger.info(f"Writing {filename}")
            enf.write(header)
            enf.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
   
            for n in results.docs:
               rec_count += 1
               art_id = n.get("art_id", None)
               file_last_modified = n.get("file_last_modified", None)
               
               if art_id is not None:
                  enf.write("\t<url>\n")
                  enf.write(f"\t\t<loc>{base_url}/{art_id}</loc>\n")
                  enf.write(f"\t\t<lastmod>{file_last_modified}</lastmod>\n")
                  enf.write("\t</url>\n")
            
            enf.write("</urlset>\n")
            enf.close()

   except Exception as err:
      raise HTTPException(404, detail=err)
      

   return sitemap_list

if __name__ == "__main__":
   sys.path.append('./config') 
   print (40*"*", "opasAPISupportLib Tests", 40*"*")
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
   
   import doctest
   doctest.testmod(optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
   print ("All tests complete!")
   print ("Fini")
