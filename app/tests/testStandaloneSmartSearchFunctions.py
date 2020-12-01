#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import smartsearch
from opasConfig import KEY_SEARCH_FIELD, KEY_SEARCH_SMARTSEARCH, KEY_SEARCH_VALUE,  KEY_SEARCH_WORDSEARCH
from unitTestConfig import base_plus_endpoint_encoded, headers

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
        assert (result['doi'] == '10.3280/PU2019-004002')

    def test_0b_DOI(self):
        """
        doi = Just enter a DOI
           10.1111/j.1745-8315.2012.00606.x 
        """
        result =  smartsearch.smart_search("https://dx.doi.org/10.1080/07351690.2011.553161")
        print (result)
        assert (result['doi'] == '10.1080/07351690.2011.553161')

    def test_0c_DOI(self):
        """
        doi = Just enter a DOI
           10.1111/j.1745-8315.2012.00606.x 
        """
        result =  smartsearch.smart_search("http://www.tandfonline.com/doi/abs/10.1080/07351690.2011.553161")
        print (result)
        assert (result['doi'] == '10.1080/07351690.2011.553161')

    def test_0_Locator(self):
        """
        """
        result = smartsearch.smart_search("aop.033.0079a")
        print (result)
        assert (result['art_id'] == 'AOP.033.0079A')
        
        result = smartsearch.smart_search("IJP.100.0052A")
        print (result)
        assert (result['art_id'] == 'IJP.100.0052A')       

    def test_0_year_and_page(self):
        """
        """
        result = smartsearch.smart_search("2014 153")
        print (result)
        assert (result['yr'] == '2014')
        assert (result['pgrg'] == '153')
        
        result = smartsearch.smart_search("2014:153")
        print (result)
        assert (result['yr'] == '2014')
        assert (result['pgrg'] == '153')

    def test_0_vol_and_page(self):
        """
        """
        result = smartsearch.smart_search("40:153")
        print (result)
        assert (result['vol'] == '40')
        assert (result['pgrg'] == '153')
        
        result = smartsearch.smart_search("100:153")
        print (result)
        assert (result['vol'] == '100')
        assert (result['pgrg'] == '153')

        result = smartsearch.smart_search("2014 40:153")
        print (result)
        assert (result['vol'] == '40')
        assert (result['pgrg'] == '153')

    def test_0_schema_fields(self):
        """
        """
        result = smartsearch.smart_search("art_type:ART OR COM")
        print (result)
        assert (result['schema_field'] == 'art_type')
        assert (result['schema_value'] == 'ART OR COM')

        result = smartsearch.smart_search("art_type:sup")
        print (result)
        assert (result['schema_field'] == 'art_type')
        assert (result['schema_value'] == 'sup')
        
        result = smartsearch.smart_search("art_authors_text:[tucket and fonagy]")
        print (result)
        assert (result['schema_field'] == 'art_authors_text')
        assert (result['schema_value'] == '[tucket and fonagy]')
        
        result = smartsearch.smart_search("art_kwds:malaise")
        print (result)
        assert (result['schema_field'] == 'art_kwds')
        assert (result['schema_value'] == 'malaise')

        result = smartsearch.smart_search("art_kwds:dissociation")
        print (result)
        assert (result['schema_field'] == 'art_kwds')
        assert (result['schema_value'] == 'dissociation')

        result = smartsearch.smart_search("art_kwds_str:memory and desire")
        print (result)
        assert (result['schema_field'] == 'art_kwds_str')
        assert (result['schema_value'] == 'memory and desire')

        result = smartsearch.smart_search("art_kwds_str:(memory and desire)")
        print (result)
        assert (result['schema_field'] == 'art_kwds_str')
        assert (result['schema_value'] == '(memory and desire)')
 
 

    def test_1A_single_name(self):
        """
        
        """
        result =  smartsearch.smart_search("Tuckett, D.")
        print (result)
        assert (result['schema_field'] == 'art_authors_citation')
        assert (result['schema_value'] == 'Tuckett, D.')

    def test_1B_multiple_name(self):
        """
        
        """
        result =  smartsearch.smart_search("Rapaport, D. and Gill, M. M.")
        print (result)
        assert (result['schema_field'] == 'art_authors_citation')
        assert (result['schema_value'] == 'Rapaport, D. && Gill, M. M.')
        
        result =  smartsearch.smart_search("Goldberg, E.L., Myers, W.A., and Zeifman, I.")
        print (result)
        assert (result['schema_field'] == 'art_authors_citation')
        assert (result['schema_value'] == 'Goldberg, E. && Myers, W. && Zeifman, I.')
        
    def test_2_names_and_dates(self):
        """
        
        """
        result = smartsearch.smart_search("Tuckett and Fonagy (2012)")
        print (result)
        assert (result['author_list'] == 'Tuckett and Fonagy')
        assert (result['yr'] == '2012')
        
        result = smartsearch.smart_search("Tuckett and Fonagy 2012")
        print (result)
        assert (result['author_list'] == 'Tuckett and Fonagy')
        assert (result['yr'] == '2012')
        
        result = smartsearch.smart_search("Tuckett, D. and Fonagy, P. 2012")
        print (result)
        assert (result['author_list'] == 'Tuckett, D. and Fonagy, P.')
        assert (result['yr'] == '2012')
        
        result = smartsearch.smart_search("Tuckett, D. and Fonagy, P. (2012)")
        print (result)
        assert (result['author_list'] == 'Tuckett, D. and Fonagy, P.')
        assert (result['yr'] == '2012')
        
        result = smartsearch.smart_search("Eugene L. Goldberg, Wayne A. Myers and Israel Zeifman (1974)")
        print (result)
        assert (result['author_list'] == 'Eugene L. Goldberg, Wayne A. Myers and Israel Zeifman')
        assert (result['yr'] == '1974')
        
        result = smartsearch.smart_search("Rapaport, D. and Gill, M. M. (1959)")
        print (result)
        assert (result['author_list'] == 'Rapaport, D. and Gill, M. M.')
        assert (result['yr'] == '1959')

        assert (result[KEY_SEARCH_SMARTSEARCH] == 'Matched articles for authors and years:')
        
    def test_2b_title_search(self):
        """
        """
        result =  smartsearch.smart_search("Psychoanalysis of Developmental Arrests: Theory and Treatment.")
        print (result)
        #Title Search in Smart Search is currently "neutered" per David's request.
        # assert (result == {'title': 'Psychoanalysis of Developmental Arrests\\: Theory and Treatment.'})
        assert (result[KEY_SEARCH_WORDSEARCH] == 'Psychoanalysis of Developmental Arrests\\: Theory and Treatment.')
        
    def test_2c_word_search(self):
        """
        
        """
        result =  smartsearch.smart_search("Psychoanalysis Treatment of headaches.")
        print (result)
        assert (result[KEY_SEARCH_SMARTSEARCH] == 'Matched paragraphs with terms: (Psychoanalysis Treatment of headaches.)')

    def test_3_references(self):
        """
        'SmartSearch recognized a citation vol and pg. Matched articles:', 'vol': '55', 'pgrg': '495-500'}
        """
        result = smartsearch.smart_search("Goldberg, E.L. Myers, W.A. Zeifman, I. (1974). Some Observations on Three Interracial Analyses. Int. J. Psycho-Anal., 55:495-500.")
        print (result)
        assert (result[KEY_SEARCH_SMARTSEARCH] == 'Matched articles for a citation vol and pg:')
        
        result = smartsearch.smart_search("Rapaport, D. and Gill, M. M. ( 1959). The Points of View and Assumptions of Metapsychology. Int. J. Psycho-Anal. 40:153-162")
        print (result)
        assert (result[KEY_SEARCH_SMARTSEARCH] == 'Matched articles for a citation vol and pg:')
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")