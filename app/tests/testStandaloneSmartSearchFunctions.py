#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

#  This test module is in development...

import sys
import os.path

folder = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
if folder == "tests": # testing from within WingIDE, default folder is tests
    sys.path.append('../libs')
    sys.path.append('../config')
    sys.path.append('../../app')
else: # python running from should be within folder app
    sys.path.append('./libs')
    sys.path.append('./config')


from starlette.testclient import TestClient

import unittest
from localsecrets import TESTUSER, TESTPW, SECRET_KEY, ALGORITHM
from datetime import datetime
import opasQueryHelper
import smartsearch
import models

class TestStandaloneSmartSearchFunctions(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    
    def test_0_DOI(self):
        """
        doi = Just enter a DOI
           10.1111/j.1745-8315.2012.00606.x 
        """
        result =  smartsearch.smart_search("10.3280/PU2019-004002")
        print (result)
        assert (result == {'doi': '10.3280/PU2019'})

    def test_0_Locator(self):
        """
        """
        result = smartsearch.smart_search("aop.033.0079a")
        print (result)
        assert (result == {'art_id': 'AOP.033.0079A'})
        
        result = smartsearch.smart_search("IJP.100.0410A")
        print (result)
        assert (result == {'art_id': 'IJP.100.0410A'})       

    def test_0_year_and_page(self):
        """
        """
        result = smartsearch.smart_search("2014 153")
        print (result)
        assert (result == {'yr': '2014', 'pgrg': '153'})
        
        result = smartsearch.smart_search("2014:153")
        print (result)
        assert (result == {'yr': '2014', 'pgrg': '153'})              

    def test_0_vol_and_page(self):
        """
        """
        result = smartsearch.smart_search("40:153")
        print (result)
        assert (result == {'vol': '40', 'pgrg': '153'})
        
        result = smartsearch.smart_search("100:153")
        print (result)
        assert (result == {'vol': '100', 'pgrg': '153'})

        result = smartsearch.smart_search("2014 40:153")
        print (result)
        assert (result == {'vol': '40', 'pgrg': '153'})              

    def test_0_schema_fields(self):
        """
        """
        result = smartsearch.smart_search("art_type:ART OR COM")
        print (result)
        assert (result == {'schema_field': 'art_type', 'schema_value': 'ART OR COM'})

        result = smartsearch.smart_search("art_type:sup")
        print (result)
        assert (result == {'schema_field': 'art_type', 'schema_value': 'sup'})
        
        result = smartsearch.smart_search("art_authors_text:[tucket and fonagy]")
        print (result)
        assert (result == {'schema_field': 'art_authors_text', 'schema_value': '[tucket and fonagy]'})       
       

    def test_1A_single_name(self):
        """
        
        """
        result =  smartsearch.smart_search("Tuckett, D.")
        print (result)
        assert (result == {'author_list': 'Tuckett, D.'})

    def test_1B_multiple_name(self):
        """
        
        """
        result =  smartsearch.smart_search("Rapaport, D. and Gill, M. M.")
        print (result)
        assert (result == {'author_list': 'Rapaport, D. && Gill, M. M.'})
        
        result =  smartsearch.smart_search("Goldberg, E.L. Myers, W.A. Zeifman, I.")
        print (result)
        assert (result == {'author_list': 'Goldberg, E.L. Myers, W.A. Zeifman, I.'})

    def test_2_names_and_dates(self):
        """
        
        """
        result = smartsearch.smart_search("Tuckett and Fonagy (2012)")
        print (result)
        assert (result == {'author_list': 'Tuckett and Fonagy', 'yr': '2012'})
        
        result = smartsearch.smart_search("Tuckett and Fonagy 2012")
        print (result)
        assert (result == {'author_list': 'Tuckett and Fonagy', 'yr': '2012'})
        
        result = smartsearch.smart_search("Tuckett, D. and Fonagy, P. 2012")
        print (result)
        assert (result == {'author_list': 'Tuckett, D. and Fonagy, P.', 'yr': '2012'})
        
        result = smartsearch.smart_search("Eugene L. Goldberg, Wayne A. Myers and Israel Zeifman (1974)")
        print (result)
        assert (result == {'author_list': 'Eugene L. Goldberg, Wayne A. Myers and Israel Zeifman', 'yr': '1974'})
        
        result = smartsearch.smart_search("Tuckett, D. and Fonagy, P. (2012)")
        print (result)
        assert (result == {'author_list': 'Tuckett, D. and Fonagy, P.', 'yr': '2012'})
        
        result = smartsearch.smart_search("Rapaport, D. and Gill, M. M. (1959)")
        print (result)
        assert (result == {'author_list': 'Rapaport, D. and Gill, M. M.', 'yr': '1959'})
        
    def test_2b_title_search(self):
        """
        
        """
        result =  smartsearch.smart_search("Psychoanalysis of Developmental Arrests: Theory and Treatment.")
        print (result)
        assert (result == {'title': 'Psychoanalysis of Developmental Arrests: Theory and Treatment.'})
        
    def test_2c_word_search(self):
        """
        
        """
        result =  smartsearch.smart_search("Psychoanalysis Treatment of headaches.")
        print (result)
        assert (result == {'wordsearch': 'Psychoanalysis Treatment of headaches.'})

    def test_3_references(self):
        """
        
        """
        result = smartsearch.smart_search("Goldberg, E.L. Myers, W.A. Zeifman, I. (1974). Some Observations on Three Interracial Analyses. Int. J. Psycho-Anal., 55:495-500.")
        print (result)
        assert (result == {'author_list': 'Goldberg, E.L. Myers, W.A. Zeifman, I.', 'yr': '1974', 'vol': '55', 'pgrg': '495-500'})
        
        result = smartsearch.smart_search("Rapaport, D. and Gill, M. M. ( 1959). The Points of View and Assumptions of Metapsychology. Int. J. Psycho-Anal. 40:153-162")
        print (result)
        assert (result == {'author_list': 'Rapaport, D. and Gill, M. M.', 'yr': '1959', 'vol': '40', 'pgrg': '153-162'})
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")