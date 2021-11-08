#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestDatabaseSearchMoreLikeThis(unittest.TestCase):
    def test_metadata_articleID_1a(self):
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/ArticleID/?articleID=IJP.078.0335A')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        assert (r["standardized"] == 'IJP.078.0335A')
        assert (r["volumeInt"] == 78)

if __name__ == '__main__':
    unittest.main()
