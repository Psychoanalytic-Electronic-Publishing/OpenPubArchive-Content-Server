#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestDatabaseWhatsNew(unittest.TestCase):
    """
    Tests of the Whats New endpoint
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """   

    def test_0_whats_new(self):
        """
        (Moved from TestMosts.py)
        """
        # request login to the API server
        full_URL = base_plus_endpoint_encoded('/v2/Database/WhatsNew/?days_back=30')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        response_info = r["whatsNew"]["responseInfo"]
        response_set = r["whatsNew"]["responseSet"] 
        assert(r['whatsNew']['responseInfo']['listType'] == 'newlist')
        #assert(r["db_server_ok"] == True)
        print (f"{r['whatsNew']['responseInfo']['count']}")
        print (r)
        if response_info["count"] == 0:
            logger.warning("There are no new articles.  Could be ok.")
        else:
            assert(response_info["count"] >= 1)

if __name__ == '__main__':
    unittest.main()
    client.close()
    