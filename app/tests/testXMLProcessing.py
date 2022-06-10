#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers
import opasAPISupportLib
import opasConfig
import opasQueryHelper
import opasCentralDBLib
import opasGenSupportLib
import models
import opasPySolrLib
from opasPySolrLib import search_text

ocd = opasCentralDBLib.opasCentralDB()

class TestXMLProcessing(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """

    def test_1_get_reference_from_api_biblio_table(self):
        """
        """
        DocumentID = [
                      ('LU-AM.005I.0025A', 'B0001'),
                      ('CPS.039.0107A', 'B0008'), 
                      ('CPS.039.0107A', 'B0003'),
                      ('IJP.068.0213A', 'B.*')
                      ]
        for n in DocumentID:
            document_id = n[0]
            local_id = n[1]
            result = ocd.get_references_from_biblioxml_table(document_id, local_id)
            assert result[0].art_id == document_id
            print(result[0])
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")