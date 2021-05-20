#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger()

import unittest
import requests
from unitTestConfig import base_plus_endpoint_encoded, headers
from localsecrets import API_KEY_NAME, API_KEY
import tempfile

class TestSiteMapReports(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
          
          
    """   

    def test01_sitemapreport(self):
        """
        Note the endpoint returns a sitemap index
         "     <sitemap>
                  <loc>https://pep-web-google.s3.amazonaws.com/X:\\AWS_S3\\AWSProd PEP-Web-Google/sitemap1.xml</loc>
                  <lastmod>2021-05-18T09:07:17</lastmod>
               </sitemap>

               <sitemap>
                  <loc>https://pep-web-google.s3.amazonaws.com/X:\\AWS_S3\\AWSProd PEP-Web-Google/sitemap2.xml</loc>
                  <lastmod>2021-05-18T09:07:17</lastmod>
               </sitemap>
               
               ...
            "
            
        """
        # get temp folder, cross platform
        tmpf = tempfile.gettempdir()
        # note api_key is required, but already in headers
        full_URL = base_plus_endpoint_encoded(f'/v2/Admin/Sitemap/?size=100&max_records=500&path={tmpf}')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        site_map_index = r["siteMapIndex"]
        site_map_list = r["siteMapList"]
        assert(len(site_map_list) == 5)

if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")