#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests
from unitTestConfig import base_plus_endpoint_encoded, headers
import unitTestConfig

# Login!
sessID, headers, session_info = unitTestConfig.test_login()

class TestConcurrency(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    """
    
    def test_contents_streams_reported_issue(self):
        """
        https://stage-api.pep-web.rocks/v2/Metadata/Videos/?sourcecode=%2A&streams=false&limit=200&offset=0
        """
        count = 0
        while count <= 10:
            full_URL = base_plus_endpoint_encoded('/v2/Metadata/Videos/?sourcecode=%2A&streams=false&limit=200&offset=0')
            response1 = requests.get(full_URL, headers=headers)
            assert(response1.ok == True)
            count += 1

    def test_all_three_together(self):
        """
        Get Author Index For Matching Author Names
        /v1/Authors/Index/{authorNamePartial}/
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostViewed/?formatrequested=XML&limit=10&viewperiod=2')
        response1 = requests.get(full_URL, headers=headers)
        full_URL = base_plus_endpoint_encoded('/v2/Database/WhatsNew/?days_back=30&limit=10')
        response2 = requests.get(full_URL, headers=headers)
        full_URL = base_plus_endpoint_encoded('/v2/Database/MostCited/?formatrequested=XML&limit=10&period=all')
        response3 = requests.get(full_URL, headers=headers)
        #assert(response1.ok == True)
        #assert(response2.ok == True)
        #assert(response3.ok == True)
        r2 = response2.json()
        print (f"{r2['whatsNew']['responseInfo']['limit']}")
        r1 = response1.json()
        print (f"MostViewed Count: {r1['documentList']['responseInfo']['count']}")
        print (f"MostViewed Limit: {r1['documentList']['responseInfo']['limit']}")
        r3 = response3.json()
        print (f"Count: {r3['documentList']['responseInfo']['count']}")
        print (f"Limit: {r3['documentList']['responseInfo']['limit']}")
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")