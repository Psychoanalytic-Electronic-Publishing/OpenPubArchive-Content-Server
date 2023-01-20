#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests of the OPAS functions which depend on the Solr API.  (Direct, rather than Endpoint calls)

"""
import unittest
import unitTestConfig
from unitTestConfig import base_plus_endpoint_encoded, headers
import requests
import opasAPISupportLib
from opasCentralDBLib import opasCentralDB

class TestSolrAPIPrevNextFunctions(unittest.TestCase):
    """
    Tests of functions getting the metadata from solr rather than the database
    
    """
    def test_1A_meta_contents_for_source(self):
        """
        Test with moreinfo == 1 should produce
            ['documentList']['responseInfo']['supplementalInfo'][infosource] = 'volumes_min_max'
              max = 11
              min = 1
              src_code = 'IJPSP'
        """
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Contents/IJPSP/4/?moreinfo=1')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        print(r['documentList']['responseInfo']['fullCount'])
        #print(r['documentList']['responseInfo']['supplementalInfo']["infosource"])
        assert r['documentList']['responseInfo']['supplementalInfo']["infosource"] == "volumes_min_max", r['documentList']['responseInfo']['supplementalInfo']["infosource"] 
        assert r['documentList']['responseInfo']['supplementalInfo']["min"] == 1,  r['documentList']['responseInfo']['supplementalInfo']["min"]
        assert r['documentList']['responseInfo']['supplementalInfo']["max"] == 11,  r['documentList']['responseInfo']['supplementalInfo']["max"]
        assert r['documentList']['responseInfo']['supplementalInfo']["src_code"] == 'IJPSP',  r['documentList']['responseInfo']['supplementalInfo']["src_code"]
        
    def test_1B_meta_contents_for_source(self):
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Contents/IJPSP/4/?moreinfo=2')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        print(r['documentList']['responseInfo']['fullCount'])
        #print(r['documentList']['responseInfo']['supplementalInfo'])
        assert r['documentList']['responseInfo']['supplementalInfo']["infosource"] == "volumes_adjacent",  r['documentList']['responseInfo']['supplementalInfo']["infosource"]
        assert r['documentList']['responseInfo']['supplementalInfo']["prev_vol"] == {'value': '3', 'count': 44},  r['documentList']['responseInfo']['supplementalInfo']["prev_vol"]
        assert r['documentList']['responseInfo']['supplementalInfo']["next_vol"] == {'value': '5', 'count': 48},  r['documentList']['responseInfo']['supplementalInfo']["next_vol"] == {'value': '5', 'count': 48}
        assert r['documentList']['responseInfo']['supplementalInfo']["matched_vol"] == {'value': '4', 'count': 61},  r['documentList']['responseInfo']['supplementalInfo']["matched_vol"] == {'value': '4', 'count': 61}

    def test_1C_meta_contents_for_source(self):
        """
        {'infosource': 'volumes_adjacent',
        'prev_vol': None,
        'matched_vol': {'value': '1', 'count': 34, 'year': '2006'},
        'next_vol': {'value': '2', 'count': 39, 'year': 'IJPSP'}}
        """
        full_URL = base_plus_endpoint_encoded('/v2/Metadata/Contents/IJPSP/1/?moreinfo=2')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        print(r['documentList']['responseInfo']['fullCount'])
        print(r['documentList']['responseInfo']['supplementalInfo'])
        print(r['documentList']['responseInfo']['supplementalInfo']["next_vol"])
        assert (r['documentList']['responseInfo']['supplementalInfo']["infosource"] == "volumes_adjacent")
        assert (r['documentList']['responseInfo']['supplementalInfo']["prev_vol"] == None)
        assert (r['documentList']['responseInfo']['supplementalInfo']["next_vol"] == {'value': '2', 'count': 39})
        assert (r['documentList']['responseInfo']['supplementalInfo']["matched_vol"] == {'value': '1', 'count': 34})
    
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")