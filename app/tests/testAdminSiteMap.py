#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger()

import unittest
import requests
import localsecrets
import tempfile
from localsecrets import API_KEY_NAME, API_KEY, PADS_TEST_ID, PADS_TEST_PW, PDF_ORIGINALS_PATH, PADS_TEST_ID2, PADS_TEST_PW2
from unitTestConfig import base_plus_endpoint_encoded, headers, test_login

# Login!
sessID, headers, session_info = test_login(username=localsecrets.PADS_TEST_ID2, password=localsecrets.PADS_TEST_PW2)

class TestAdminSiteMap(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.

    Note the endpoint returns a sitemap index
          <sitemap>
              <loc>https://pep-web-google.s3.amazonaws.com/X:\\AWS_S3\\AWSProd PEP-Web-Google/sitemap1.xml</loc>
              <lastmod>2021-05-18T09:07:17</lastmod>
           </sitemap>

           <sitemap>
              <loc>https://pep-web-google.s3.amazonaws.com/X:\\AWS_S3\\AWSProd PEP-Web-Google/sitemap2.xml</loc>
              <lastmod>2021-05-18T09:07:17</lastmod>
           </sitemap>
           
           ...
    """   

    def test00_admin_sitemap(self):
        """
        Windows Local path does not require admin permissions
        """
        full_URL = base_plus_endpoint_encoded('/v2/Admin/Sitemap/?path=c:\\windows\\temp&max_records=500&size=100')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        
    def test01_sitemapreport(self):
        # Login!
        sessID, headers, session_info = test_login(username=localsecrets.PADS_TEST_ID2, password=localsecrets.PADS_TEST_PW2)
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
    