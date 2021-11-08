#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Updates:
#  2020-04-06 - Testing tightened to be exact.
#  2020-04-30 - Added test 8x to test source info retrieval with wildcards

import unittest
import requests
import unitTestConfig
from unitTestConfig import base_plus_endpoint_encoded, headers, get_headers_not_logged_in
# Get session, but not logged in.
headers = get_headers_not_logged_in()

# import opasCentralDBLib

class TestMetadataV1EndpointsOnly(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    """   

    def test_7_meta_get_sourcenames(self):
        """
        List of names for a specific source -- this is v1 only with name in path!!!!
        /v1/Metadata/{SourceType}/{SourceCode}/
        """
        full_URL = base_plus_endpoint_encoded('/v1/Metadata/Journals/IJPSP/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseInfo']['fullCount'] == 1)
        assert(r['sourceInfo']['responseSet'][0]['displayTitle'] == 'International Journal of Psychoanalytic Self Psychology')
        
    def test_8_meta_all_sources(self):
        """
        List of names for a specific source -- this is v1 only with name in path!!!!
        /v1/Metadata/{SourceType}/{SourceCode}/
        """
        full_URL = base_plus_endpoint_encoded('/v1/Metadata/*/*/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        count = r['sourceInfo']['responseInfo']['count']
        print (f"Count {count}")
        assert(count >= unitTestConfig.ALL_SOURCES_COUNT)

    def test_8b_meta_all_sources(self):
        """
        List of names for a specific source -- this is v1 only with name in path!!!!
        /v1/Metadata/{SourceType}/{SourceCode}/
        """
        full_URL = base_plus_endpoint_encoded('/v1/Metadata/*/IJP/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseInfo']['count'] == 1)
    
    def test_8b2_meta_all_sources(self):
        """
        List of names for a specific source, a book, but not spec'd as book -- this is v1 only with name in path!!!!
        /v1/Metadata/{SourceType}/{SourceCode}/
        """
        # get all the PEP Codes
        full_URL = base_plus_endpoint_encoded('/v1/Metadata/*/*/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        pep_codes = []
        for n in r['sourceInfo']['responseSet']:
            pep_codes.append(n['PEPCode'])
        # Now test to make sure they can be read (if there's missing data in the product table, can cause error)
        for n in pep_codes:
            full_URL = base_plus_endpoint_encoded(f'/v1/Metadata/*/{n}/')
            # Confirm that the request-response cycle completed successfully.
            assert(response.ok == True)
            # test return
            r = response.json()
            print(f"{n} count={r['sourceInfo']['responseInfo']['count']}")
            assert(r['sourceInfo']['responseInfo']['count'] >= 1)

    def test_8b3_meta_sourcename(self):
        """
        List of names for a specific source by name -- this is v1 only with name in path!!!!
        /v1/Metadata/{SourceType}/{SourceCode}/
        """
        full_URL = base_plus_endpoint_encoded('/v1/Metadata/*/*/?sourcename=.*psychoanalytic.*')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseInfo']['count'] == 33)

        full_URL = base_plus_endpoint_encoded('/v1/Metadata/*/*/?sourcename=.*international journal of psychoanalysis.*')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseInfo']['count'] == 4)

    def test_8c_meta_all_sources_nonsense(self):
        """
        List of names for a source that doesn't match the type -- this is v1 only with name in path!!!!
        /v1/Metadata/{SourceType}/{SourceCode}/
        """
        full_URL = base_plus_endpoint_encoded('/v1/Metadata/Books/IJP/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        assert(r['sourceInfo']['responseInfo']['count'] == 0)
    
    def test_8d_meta_all_sourcetype_nonsense(self):
        """
        List of names for a source for an unknown type -- this is v1 only with name in path!!!!
        /v1/Metadata/{SourceType}/{SourceCode}/
        
        Currently: just changes to Journal, maybe should change to "*"
        """
        full_URL = base_plus_endpoint_encoded('/v1/Metadata/Garbage/*/')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == False)
        
        full_URL = base_plus_endpoint_encoded('/v1/Metadata/Garbage/IJP/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == False)
        
        full_URL = base_plus_endpoint_encoded('/v1/Metadata/Garbage/GW/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == False)
        
        # test return

if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")