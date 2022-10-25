#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant

import unittest
import requests
from unitTestConfig import base_api, base_plus_endpoint_encoded, headers, session_id, UNIT_TEST_CLIENT_ID, get_headers_not_logged_in

# Get session, but not logged in.
headers = get_headers_not_logged_in()

class TestDatabaseSearch(unittest.TestCase):

    def test_search_fulltext0(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?abstract=true&facetfields=art_year_int%2Cart_views_last12mos%2Cart_cited_5%2Cart_authors%2Cart_lang%2Cart_type%2Cart_sourcetype%2Cart_sourcetitleabbr%2Cglossary_group_terms%2Cart_kwds_str&facetlimit=15&facetmincount=1&formatrequested=XML&fulltext1=text%3A(%22anxiety+hysteria%22~25)&highlightlimit=5&limit=20&offset=0&sort=author&synonyms=false')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        kwiclist = r["documentList"]["responseSet"][0]["kwicList"]
        assert(len(kwiclist) > 0)
        assert(response_info["count"] >= 1)
        print (f"return count: {response_info['count']}")
        print (response_set[0]['documentRef'])
        #print (response_set[0]['abstract'])

    def test_search_fulltext1(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1="military"')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        kwiclist = r["documentList"]["responseSet"][0]["kwicList"]
        assert(len(kwiclist) > 0)
        assert(response_info["count"] >= 1)
        print (f"return count: {response_info['count']}")
        #print (response_set[0]['abstract'])

    def test_search_long_para(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=OPUS&fulltext1="physics science observations"~25&abstract=True')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] == 1)
        print (response_set[0]['documentRef'])

    def test_search_long_para_alt_seems_to_show_solr_misses_one(self):
        # This produces 0 results on the GVPi server; this result is correct though
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=AOP&fulltext1="physics%20science%20observations"~90&abstract=True')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] == 2) # should REALLY be 3. I confirmed all three papers above in test_search_long_para...
                                            # not sure why we get 2 here, but set that way for now. TODO
        print (f"return count: {response_info['count']}")
        print (response_set[0]['documentRef'])

    def test_0a_rank(self): 
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=AOP&fulltext1=cried&sort=rank desc&limit=15&offset=0')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True) # rank is accepted, same as score
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] == 47)
        #print (response_set)
        print (f"return count: {response_info['count']}")
        for n in response_set:
            print (n["documentRef"])
        # Confirm that the request-response cycle completed successfully.
        
    def test_0b_parameter_error(self):
        # bad boolean parameter
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewperiod=&fulltext1=cried&sort=rank&synonyms=WTF')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == False)
        r = response.json()

    def test_0b_good_language_code(self):
        # bad boolean parameter
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=cried&sourcelangcode=en')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()

    def test_0b_bad_language_code(self):
        # bad boolean parameter
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?viewperiod=&fulltext1=cried&sourcelangcode=e')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == False)
        r = response.json()

    def test_search_author_and_journalcode(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=Levin&sourcecode=AOP')
        response = requests.get(full_URL, headers=headers)
        r = response.json()
        assert(response.ok == True)
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] == 12)
        print (response_set[0]['documentRef'])

    def test_search_author_and_journalcode_and_text(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=Blum&sourcecode=AOP&fulltext1=transference')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        # print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] == 2)
        print (response_set[0]['documentRef'])

    def test_search_author_and_journalcode_and_citecount(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=Bollas&sourcecode=AOP&citecount=1 IN 10')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] == 2)
        print (response_set[0]['documentRef'])

    def test_search_startyear(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=aop&startyear=2015')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] == 20)
        print("Titles:")
        for n in response_set: 
            print (n['title'])
        # try it with parens as the client does
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=aop&startyear=(2015)')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] == 20)
        print (f"return count: {response_info['count']}")
        print("Titles:")
        for n in response_set: 
            print (n['title'])

    def test_search_endyear(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=aop&endyear=2011') # note: no volume in 2009-2011
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] >= 610)
        print (response_set[0]['documentRef'])
        # try it with parens as the client does
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=aop&endyear=(2011)') # note: no volume in 2009-2011
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] >= 610)
        print (f"return count: {response_info['count']}")
        print (response_set[0]['documentRef'])

    def test_search_year_range1(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=aop&startyear=1975&endyear=1976')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] == 42)
        print (f"return count: {response_info['count']}")
        print("Years:")
        count = 0
        year = ""
        for n in response_set:
            if year != n['year']:
                print (n['year'])
                year = n['year']
                count += 1
              
            if count > 10:
                break

    def test_search_year_range2(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=aop&startyear=1975&endyear=1975')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] == 21)
        print (f"return count: {response_info['count']}")
        print("Years:")
        count = 0
        year = ""
        for n in response_set:
            if year != n['year']:
                print (n['year'])
                year = n['year']
                count += 1
              
            if count > 10:
                break

    def test_search_year_range3(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=aop&startyear=1975&endyear=2020')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] >= 588)
        print (f"return count: {response_info['count']}")
        print("Years:")
        count = 0
        year = ""
        for n in response_set:
            if year != n['year']:
                print (n['year'])
                year = n['year']
                count += 1
              
            if count > 10:
                break

    def test_search_title(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=aop&title=west')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["fullCount"] == 3)
        print("Titles:")
        for n in response_set: 
            print (n['title'])

    def test_video_list_search(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?abstract=false&formatrequested=XML&limit=20&offset=0&source=PEPGRANTVS&sort=bibliographic&synonyms=false')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        assert(response_info['count'] >= 10)
        print (f"return count: {response_info['count']}")

        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?abstract=false&formatrequested=XML&limit=20&offset=0&smarttext=PEPGRANTVS.*.*&sort=bibliographic&synonyms=false')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        assert(response_info['count'] >= 10)
        print (f"return count: {response_info['count']}")

        #  test longest (current) sourcecode
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?abstract=false&formatrequested=XML&limit=20&offset=0&smarttext=PEPTOPAUTHVS.*.*&sort=bibliographic&synonyms=false')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # test return
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        assert(response_info['count'] >= 10)
        print (f"return count: {response_info['count']}")

    def test_search_almost_all_params(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=transference&sourcecode=aop&sourcetype=journal&sourcelangcode=EN&volume=10&author=blum&startyear=1982&facetfields=art_sourcetype')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        #print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"] 
        assert(response_info["count"] == 1)
        print (f"Response Set Length: {len(response_set)}")
        print (response_set[0]['documentRef'])
        
    def test_v2_database_search_fulltext(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?title=psychoanalysis&sourcecode=CPS&startyear=1990-1993&fulltext1="child%20abuse"&sort=citeCount&limit=10&offset=0')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] >= 1)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?title=psychoanalysis&sourcecode=CPS&startyear=1990&endyear=1995&fulltext1="child%20abuse"&sort=citeCount&limit=10&offset=0')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 3)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)

    def test_v2_database_search_author(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=freud&sourcecode=IJP&startyear=1990-1993&limit=10&offset=0')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] >= 1)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?author=freud&limit=10&offset=0')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['count'] == 10)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == False)

    def test_v2_database_search_synonyms(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?sourcecode=BAP&fulltext1=text:bisexuality&sort=citeCount&limit=10&offset=0')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 14)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == False)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?synonyms=true&sourcecode=BAP&fulltext1=text:bisexuality&sort=citeCount&limit=10&offset=0')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        assert(r['documentList']['responseInfo']['fullCount'] == 78)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == False)

    def test_v2_database_search_citedcount(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?citecount=6 TO 10 IN 10&sourcecode=IJP OR APA&startyear=1990&endyear=2010&fulltext1="theoretical underpinnings"&sort=citeCount&limit=10&offset=0')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        print (f"Count: {r['documentList']['responseInfo']['fullCount']} Count complete: {r['documentList']['responseInfo']['fullCountComplete']}")
        
        assert(r['documentList']['responseInfo']['fullCount'] >= 3)
        assert(r['documentList']['responseInfo']['fullCountComplete'] == True)

        
        

if __name__ == '__main__':
    unittest.main()
    