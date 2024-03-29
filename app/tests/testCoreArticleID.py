#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Updates:
#  2020-04-06 - Testing tightened to be exact.
#  2020-04-30 - Added test 8x to test source info retrieval with wildcards
#  2022-10-25 - Genericized

import unittest
import requests
import unitTestConfig
import opasConfig
from opasArticleIDSupport import ArticleID

from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()


class TestArticleID(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
          
    Test the PEP ID system
    
    These tests do not require PEP data to be loaded, but the ID system is PEP Specific
    
    """   
        
    def test_0(self): 
        # ---------------------------------------------------------------------------------------
        # Version 2 style, better, including sourcetype support
        # ---------------------------------------------------------------------------------------
        testIDs = [
            "FA.001A.0005A",
            "FA.018B.0001A",
            "BAFC.012.0071A",
            "BAFC.016.0054A",
            "BAP.013.0720A",
            "BAP.018.0821A",
            "BIP.001.0342A",
            "BIP.003.0117A",
            "BIP.003.0263A",
            "BIP.003.0513A",
            "BIP.012.0258A",
            "CFP.001.0001A",
            "CFP.007.0001A",
            "CPS.001.0001A",
            "CPS.007.0001A",
            "IFP.017.0027A",
            "IFP.017.0158A",
            "ZBK.028.0000A",
            "ZBK.028.0086A",
            "PEPGRANTVS.001.0003A",
            "PEPGRANTVS.001.0004A"
        ]
        for n in testIDs:
            full_URL = base_plus_endpoint_encoded(f'/v2/Metadata/ArticleID/?articleID={n}') 
            response = requests.get(full_URL, headers=headers)
            assert(response.ok == True)
            # test return
            r = response.json()
            a = ArticleID(**r)
            assert(a.standardized == n.upper())
            print (n, " = ", r)
          
    def test_1_issue_nbrs(self): 
        # ---------------------------------------------------------------------------------------
        # Version 2 style, better, including sourcetype support
        # ---------------------------------------------------------------------------------------
        testIDs = [
            ("FA.001S.R0001", 19),
            ("GW.018S.0000A", None), # (ArticleID, Expected issue number)
            ("IJP.034S.0005A", None),
            ("FA.002S.R0001", None),
            ("FA.001A.0005A", 1),
            ("FA.001C.0074", 3), 
            ("FA.001F.R0001", 6),
            ("FA.001W.0062A", 23), 
            ("ajp.034.0155A", None), 
            ("PEPGRANTVS.001.0003A", None),
            ("PEPGRANTVS.001A.0015A", 1), 
            ("JOAP.028B.0184A", 2), 
            ("PAQ.011C.0148B", 3), 
        ]
        for n in testIDs:
            full_URL = base_plus_endpoint_encoded(f'/v2/Metadata/ArticleID/?articleID={n[0]}') 
            response = requests.get(full_URL, headers=headers)
            assert(response.ok == True)
            # test return
            r = response.json()
            a = ArticleID(**r)
            if a.is_supplement and a.src_code != "FA":
                assert(a.art_issue_int is None)
            else:
                assert(a.art_issue_int == n[1]),  print (n, " = ", r)
            
          
    def test_2_articleID_manipulation(self):
        testIDs = [
            "FA.001A.0005A",
            "FA.001C.0074", 
            "FA.001.R0002", 
        ]
        for n in testIDs:
            a = ArticleID(art_id=n)
            print (a.art_id, a.standardized, a.alt_standard)
            assert(a.standardized == n.upper())
        
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")