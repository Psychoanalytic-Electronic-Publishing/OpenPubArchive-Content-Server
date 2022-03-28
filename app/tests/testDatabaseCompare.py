#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from .utilityCompareTables import compareTables
#import compareTables

class TestDoDatabaseCompare(unittest.TestCase):
    """
    Runs the database compare program, which makes sure the configured tables
      are the same across development, test, and production databases
    
    """

    def test_1a(self):
        """
        """
        ret_val = compareTables.compare_tables()
        if ret_val > 0:
            print (80*"=")
            print (30*"*FINAL*")
            print ("Table differences found!")
        assert(ret_val == 0)
        
    def test_2(self):
        ret_val = compareTables.compare_critical_columns("api_productbase","basecode", "active")
        assert(ret_val == 0)

    def test_2b(self):
        col_list = [
                      "articleID", 
                      "active", 
                      "pep_class", 
                      "pep_class_qualifier", 
                      "accessClassification", 
                      "wall", 
                      "mainTOC", 
                      "first_author", 
                      "author", 
                      "title", 
                      "bibabbrev", 
                      "ISSN", 
                      "'ISBN-10'", 
                      "'ISBN-13'", 
                      "pages", 
                      "Comment", 
                      "pepcode", 
                      "publisher", 
                      "jrnl", 
                      "pub_year", 
                      "start_year", 
                      "end_year", 
                      "pep_url", 
                      "language", 
                      #"updated", 
                      "pepversion", 
                      "duplicate", 
                      "landing_page", 
                      "coverage_notes", 
                      "landing_page_intro_html", 
                      "landing_page_end_html", 
                      "google_books_link", 
              ]
        verbose = False
        ret_val = compareTables.compare_critical_column_lists("api_productbase","basecode", col_list, db1Name="DEV", db2Name="STAGE", verbose=verbose)
        print (f"Difference Count ={ret_val}")
        assert(ret_val == 0)
        ret_val = compareTables.compare_critical_column_lists("api_productbase","basecode", col_list, db1Name="STAGE", db2Name="PRODUCTION", verbose=verbose)
        print (f"Difference Count ={ret_val}")
        assert(ret_val == 0)

if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")