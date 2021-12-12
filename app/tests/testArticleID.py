#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Updates:
#  2020-04-06 - Testing tightened to be exact.
#  2020-04-30 - Added test 8x to test source info retrieval with wildcards

import unittest
import requests
import unitTestConfig
import opasConfig

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()


# import opasCentralDBLib

class TestArticleID(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    """   
        
    def test_0(self): 
        # ---------------------------------------------------------------------------------------
        # Version 2 style, better, including sourcetype support
        # ---------------------------------------------------------------------------------------
        testIDs = [
            "FA.001A.0005A",
            "FA.001C.0074", 
            "FA.001.R0002", 
            "FA.001F.R0001",
            "FA.001W.0062A", 
            "IJP.034.0005A",
            "IJP.034S.0005A",
            "ajp.034.0155A", 
        ]
        for n in testIDs:
            full_URL = base_plus_endpoint_encoded(f'/v2/Metadata/ArticleID/?articleID={n}') 
            response = requests.get(full_URL, headers=headers)
            assert(response.ok == True)
            # test return
            r = response.json()
            a = opasConfig.ArticleID(**r)
            assert(a.standardized == n.upper())
            print (n, " = ", r)
          
    def test_1_issue_nbrs(self): 
        # ---------------------------------------------------------------------------------------
        # Version 2 style, better, including sourcetype support
        # ---------------------------------------------------------------------------------------
        testIDs = [
            ("FA.001A.0005A", 1),
            ("FA.001C.0074", 3), 
            ("FA.001F.R0001", 6),
            ("FA.001W.0062A", 23), 
            ("IJP.034S.0005A", 0),
            ("FA.001S.R0001", 19),
            ("FA.002S.R0001", 0),
            ("ajp.034.0155A", 0), 
        ]
        for n in testIDs:
            full_URL = base_plus_endpoint_encoded(f'/v2/Metadata/ArticleID/?articleID={n[0]}') 
            response = requests.get(full_URL, headers=headers)
            assert(response.ok == True)
            # test return
            r = response.json()
            a = opasConfig.ArticleID(**r)
            if a.isSupplement:
                assert(a.issueCodeInt == 0)
            else:
                assert(a.issueCodeInt == n[1])
            
            print (n, " = ", r)
          
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")