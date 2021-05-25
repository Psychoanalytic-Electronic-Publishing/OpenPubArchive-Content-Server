#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers

class TestSmartSearch(unittest.TestCase):
    def test_0_smartsearch_endpoint(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/SmartSearch/?smarttext=aop.033.0079a&abstract=True')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print (f'Smarttext: {response_info["description"]}')
        #response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] == 1)

    def test_0_name_year_smartsearch_endpoint(self): 
        full_URL = base_plus_endpoint_encoded('/v2/Database/SmartSearch/?smarttext=Tuckett 1982&sort=rank&limit=15&offset=0')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True) # rank is accepted, same as score
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        assert(response_info["fullCount"] == 1)
        #print (response_set)
        for n in response_set:
            print (n["documentRef"])
        # Confirm that the request-response cycle completed successfully.
        
    def test_0_DOI_smartsearch_endpoint(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/SmartSearch/?smarttext=10.3280/PU2019-004002')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print (response_info)
        response_set = r["documentList"]["responseSet"]
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["count"])
        assert(response_info["count"] == 1)

    def test_1_smartsearch_regular(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=OPUS&smarttext=physics%20science%20observations&abstract=True')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print (f'Smarttext: {response_info["description"]}')
        #response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] == 1)

    def test__2a_smartsearch_locator1(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=aop.033.0079a&abstract=True')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print (f'Smarttext: {response_info["description"]}')
        #response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] == 1) # should be .  I confirmed all three papers above in test_search_long_para...not sure why this fails.

    def test_2b_smartsearch_locator2(self):
        # Partial locator, gets all articles in this volume.
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=art_id:AOP.033.*&abstract=True')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print (f'Smarttext: {response_info["description"]}')
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] == 19) 
        print (response_set)

    def test_003_smartsearch_name_year(self): 
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Tuckett 1982&sort=rank&limit=15&offset=0')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True) # rank is accepted, same as score
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        assert(response_info["fullCount"] == 1)
        #print (response_set)
        for n in response_set:
            print (n["documentRef"])
        # Confirm that the request-response cycle completed successfully.
        
    def test_3b_smartsearch_two_names_and_year(self): 
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Tuckett and Fonagy (2012)')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True) # rank is accepted, same as score
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print (response_info)
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        assert(response_info["fullCount"] == 1)
        #print (response_set)
        for n in response_set:
            print (n["documentRef"])
        # Confirm that the request-response cycle completed successfully.
        
    def test_4_search_schemafield(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=art_type:REV&sourcecode=AOP')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print (f'Smarttext: {response_info["description"]}')
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] == 3)
        print (response_set[0])

    def test_5_search_author_and_journalcode(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Levin&sourcecode=AOP')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        assert(response.ok == True)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["count"])
        assert(response_info["count"] == 12)
        #print (response_set[0])

    def test_6_search_author_and_journalcode_and_text(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Blum&sourcecode=AOP&fulltext1=transference')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print (response_info)
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["count"])
        assert(response_info["count"] == 2)
        #print (response_set[0])

    def test_10_DOI(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=10.3280/PU2019-004002')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        print (response_info)
        response_set = r["documentList"]["responseSet"]
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["count"])
        assert(response_info["count"] == 1)
        #print (response_set[0])

    def test_10_locator(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=aop.033.0079a')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (response_info["count"])
        assert(response_info["count"] == 1)
        # print (response_set[0])
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=IJP.100.0411A')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["count"])
        assert(response_info["count"] == 1)
        #print (response_set[0])

    def test_10_year_and_page(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=2014 153')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["count"])
        assert(response_info["count"] == 7)  # verified 7 matches 2020-07-26
        # print (response_set[0])

    def test_10_vol_and_page(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=100:272')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["count"])
        assert(response_info["count"] == 1)
        # print (response_set[0])

    def test_10_schema_fields(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=AOP&smarttext=art_type:ART OR COM')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["fullCount"])
        assert(response_info["fullCount"] >= 627)
        # print (response_set[0])

        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=AJP&smarttext=art_type:PRO')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["fullCount"])
        assert(response_info["fullCount"] >= 37)
        print (response_set[0])

    def test_11A_single_name(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Tuckett, D.')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["fullCount"])
        assert(response_info["fullCount"] >= 59)
        print (response_set[0])

    def test_11B_multiple_name(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Goldberg, E.L., Myers, W.A., Zeifman, I.')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["count"])
        assert(response_info["count"] == 1)
        print (response_set[0])

    def test_11B2_anded_names(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Rapaport, D. and Gill, M. M.')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["count"])
        assert(response_info["count"] == 1)
        print (response_set[0])

    def test_12a_names_and_dates(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Tuckett and Fonagy (2012)')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["count"])
        assert(response_info["count"] == 1)
        #print (response_set[0])

    def test_12b_names_and_dates(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Tuckett and Fonagy 2012')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["count"])
        assert(response_info["count"] == 1)
        #print (response_set[0])

    def test_12c_names_and_dates(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Eugene L. Goldberg, Wayne A. Myers and Israel Zeifman (1974)')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["count"])
        assert(response_info["count"] == 1)
        #print (response_set[0])

    def test_12d_names_and_dates(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Tuckett, D., Auchincloss, E.L. and Fonagy, P. (2012)')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["count"])
        assert(response_info["count"] == 1)
        #print (response_set[0])

    def test_12e_names_and_dates(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Tuckett and Fonagy 2012')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["count"])
        assert(response_info["count"] == 1)
        #print (response_set[0])

    def test_12f_names_and_dates(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Rapaport, D. and Gill, M. M. (1959)')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["count"])
        assert(response_info["count"] == 1)
        #print (response_set[0])

    def test_12g_names_and_dates(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Tuckett, D. and Fonagy, P. 2012')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["count"])
        assert(response_info["count"] == 1)
        print (response_set[0])

    def test_12b_phrase_search(self):
        """
        This is a search for a phrase
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext="Manualized Psychodynamic Psychotherapies"')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["count"])
        assert(response_info["count"] >= 3)  
        print (response_set[0]) 

        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Manualized Psychodynamic Psychotherapies')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["count"])
        assert(response_info["count"] >= 3)  
        print (response_set[0]) 

    def test_12c_word_search(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Psychoanalysis Treatment of headaches.')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["fullCount"])
        assert(response_info["count"] >= 1)
        print (response_set[0])

    def test_13_references_a(self):
        """
        Full references
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Goldberg, E.L. Myers, W.A. Zeifman, I. (1974). Some Observations on Three Interracial Analyses. Int. J. Psycho-Anal., 55:495-500.')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["count"])
        assert(response_info["count"] == 1)
        print (response_set[0])

    def test_13_references_b(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Rapaport, D. and Gill, M. M. ( 1959). The Points of View and Assumptions of Metapsychology. Int. J. Psycho-Anal. 40:153-162')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["count"])
        assert(response_info["count"] == 1)
        print (response_set[0])

    def test_13a_dts_example_searches(self):
        """
        Words anded
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Evenly Suspended Attention')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["fullCount"])
        assert(response_info["fullCount"] >= 695 and response_info["fullCount"] <= 810)

    def test_13b_dts_example_searches(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=transference interpretation')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["fullCount"])
        assert(response_info["fullCount"] >= 6900 and response_info["fullCount"] <= 7800)

    def test_13c_dts_example_searches(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Eitingon model')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["fullCount"])
        assert(response_info["fullCount"] >= 133 and response_info["fullCount"] <= 170)

    def test_13d_dts_example_searches(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=unconscious phantasy')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["fullCount"])
        assert(response_info["fullCount"] >= 2300 and response_info["fullCount"] <= 2600)

    def test_14_example_smart_search_classes(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext="Eitingon Model"')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["fullCount"])
        assert(response_info["fullCount"] >= 95 and response_info["fullCount"] <= 115) # range just to give it some upper slack for new data

    def test_14b_example_smart_search_classes(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Eitingon AND Model')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["fullCount"])
        assert(response_info["fullCount"] >= 440 and response_info["fullCount"] <= 525) # range just to give it some upper slack for new data

    def test_14c_example_smart_search_classes(self):
        """
        """
        #full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Eitingon')
        #response = requests.get(full_URL, headers=headers)
        #assert(response.ok == True)
        #r = response.json()
        #response_info = r["documentList"]["responseInfo"]
        #response_set = r["documentList"]["responseSet"] 
        #print (f'Smarttext: {response_info["description"]}')
        #print (response_info["fullCount"])

        #full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Model')
        #response = requests.get(full_URL, headers=headers)
        #assert(response.ok == True)
        #r = response.json()
        #response_info = r["documentList"]["responseInfo"]
        #response_set = r["documentList"]["responseSet"] 
        #print (f'Smarttext: {response_info["description"]}')
        #print (response_info["fullCount"])

        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Eitingon OR Model') # either author
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["fullCount"])
        assert(response_info["fullCount"] >= 50 and response_info["fullCount"] <= 100) # range just to give it some upper slack for new data

    def test_14d_example_smart_search_classes(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext=Eitingon AND NOT Model')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["fullCount"])
        assert(response_info["fullCount"] >= 46 and response_info["fullCount"] <= 50) # range just to give it some upper slack for new data

    def test_14e_example_smart_search_classes(self):
        """
        """
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?smarttext="Eitingon Model"~4')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        print (f'Smarttext: {response_info["description"]}')
        print (response_info["fullCount"])
        assert(response_info["fullCount"] >= 114 and response_info["fullCount"] <= 144)

if __name__ == '__main__':
    unittest.main()
    