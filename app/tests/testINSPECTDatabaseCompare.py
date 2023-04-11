#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from .utilityCompareTables import compareTables
import difflib
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
        
    def test_2_active_product_comparison(self):
        ret_val = compareTables.compare_critical_columns("api_productbase", "basecode", "active")
        assert(ret_val == 0)

    def test_2a1_Critical_column_lists_common(self):
        col_list = [
            "config_settings", 
        ]
        ret_val = compareTables.compare_critical_column_lists("api_client_configs","config_name", col_list, db1Name="STAGE", db2Name="PRODUCTION", key_where_clause='WHERE config_name="common"')
        print (f"Difference Count ={ret_val}")
        assert(ret_val == 0)

    def test_2a2_Critical_column_lists_language_specific(self):
        col_list = [
            "config_settings", 
        ]
        ret_val = compareTables.compare_critical_column_lists("api_client_configs",
                                                              "config_name",
                                                              col_list,
                                                              db1Name="STAGE",
                                                              db2Name="PRODUCTION",
                                                              key_where_clause='WHERE config_name="en-us"')
        print (f"Difference Count ={ret_val}")
        assert(ret_val == 0)

    def test_2b_Productbase_Compare(self):
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
                      #"duplicate", # unused now
                      "landing_page", 
                      "coverage_notes", 
                      #"landing_page_intro_html", # unused now
                      #"landing_page_end_html", # unused now
                      #"google_books_link", # unused now
              ]
        verbose = False
        ret_val = compareTables.compare_critical_column_lists("api_productbase","basecode", col_list, db1Name="LOCALDEV", db2Name="STAGE", verbose=verbose)
        print (f"Difference Count ={ret_val}")
        assert(ret_val == 0)
        ret_val = compareTables.compare_critical_column_lists("api_productbase","basecode", col_list, db1Name="STAGE", db2Name="PRODUCTION", verbose=verbose)
        print (f"Difference Count ={ret_val}")
        assert(ret_val == 0)


    def test_3a_compare_articles_on_localdev_but_not_stage(self):
        print ("Articles on LOCALDEV not on STAGE")
        col_list = [
                      "art_title"
              ]
        verbose = False
        ret_val = compareTables.compare_critical_column_lists("api_articles","art_id", col_list, db1Name="LOCALDEV", db2Name="STAGE", verbose=verbose)
        print (f"Difference Count ={ret_val}")
        assert(ret_val == 0)

    def test_3b_compare_articles_on_stage_but_not_localdev(self):
        print ("Articles on STAGE not on LOCALDEV")
        col_list = [
                      "art_title"
              ]
        verbose = False
        ret_val = compareTables.compare_critical_column_lists("api_articles","art_id", col_list, db1Name="STAGE", db2Name="LOCALDEV", verbose=verbose)
        print (f"Difference Count ={ret_val}")
        assert(ret_val == 0)

if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")