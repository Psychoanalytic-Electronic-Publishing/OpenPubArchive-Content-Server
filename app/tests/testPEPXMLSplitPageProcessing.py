#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import unittest
import opasCentralDBLib
import opasXMLSplitBookSupport

ocd = opasCentralDBLib.opasCentralDB()

class TestXMLProcessing(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """

    def test_1_add_to_splitbook_table(self):
        """
        """
        splitbook_data = opasXMLSplitBookSupport.SplitBookData(ocd)
        ret_val = splitbook_data.add_splitbook_page_record("ZBK.999.0000", "0022")
        assert ret_val == True
        inst = splitbook_data.get_splitbook_page_instance(book_code="ZBK",vol="999", page_id="0022")
        print (inst)
        assert inst is not None
        ret_val = splitbook_data.delete_splitbook_page_records("ZBK.999.0000")
        assert ret_val == True

    def test_2_delete_select_splitbook_table_records(self):
        """
        """
        splitbook_data = opasXMLSplitBookSupport.SplitBookData(ocd)
        ret_val = splitbook_data.add_splitbook_page_record("ZBK.999.0100", "R0021")
        assert ret_val == True
        ret_val = splitbook_data.delete_splitbook_page_records("ZBK.999.0100A")
        assert ret_val == True

    def test_3_garbage_collect_splitbook_table(self):
        """
        """
        splitbook_data = opasXMLSplitBookSupport.SplitBookData(ocd)
        test_id = "ZBK.999.0111"
        test_id_pattern = "ZBK.999.%"
        ret_val = splitbook_data.add_splitbook_page_record(test_id, "R0121")
        assert ret_val == True
        ret_val = splitbook_data.garbage_collect(art_id_pattern=test_id_pattern)
        assert ret_val == True

if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")