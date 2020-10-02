#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third-party imports...
#from nose.tools import assert_true

#  This test module is in development...

import sys
import os.path
import logging

logger = logging.getLogger(__name__)

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
#import jwt
from datetime import datetime

import opasQueryHelper
import opasAPISupportLib
import opasCentralDBLib
import opasConfig

from unitTestConfig import base_api, base_plus_endpoint_encoded
from main import app

client = TestClient(app)
ocd = opasCentralDBLib.opasCentralDB()

class TestMostFromDb(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """
    def test_000_generator(self):
        views = ocd.SQLSelectGenerator("select * from vw_stat_most_viewed")
        count = 0
        # print (f"Length of set to be exported: {len(list(views))}")
        for n in views:
            print (n)
            count += 1
            if count > 2:
                break
        assert(len(list(views)) >= 600)
            
    def test_001_download(self):
        import codecs
        import csv
        views = ocd.SQLSelectGenerator("select * from vw_stat_most_viewed order by last12months DESC")
        if 0:
            with codecs.open('views_out.csv', 'w', encoding="utf-8") as csvfile:
                viewswriter = csv.writer(csvfile, delimiter='|', quotechar='^', quoting=csv.QUOTE_MINIMAL)
                header = ["Document", "Last Week", "Last Month", "Last 6 Months", "Last 12 Months", "Last Calendar Year"]
                viewswriter.writerow(header)
                for n in views:
                    print (n)
                    row = (n['textref'], 
                           n["lastweek"], 
                           n["lastmonth"], 
                           n["last6months"], 
                           n["last12months"], 
                           n["lastcalyear"])
                    viewswriter.writerow(row)
       
               
    def test_0_most_viewed_direct_source_type(self):
        rows = ocd.most_viewed_generator( view_in_period=4,
                                          viewcount=0, 
                                          publication_period=5,
                                          author=None,
                                          title=None,
                                          source_name=None, 
                                          source_code=None,
                                          source_type="journals",  # see VALS_SOURCE_TYPE (norm_val applied in opasCenralDBLib)
                                          select_clause=opasConfig.VIEW_MOSTVIEWED_DOWNLOAD_COLUMNS, 
                                          limit=None,
                                          offset=0,
                                          session_info=None
                                          )
        count4in5 = len(list(rows))
        assert (count4in5 > 0)
        
    def test_2_most_cited_direct_author(self):
        """
        Test: Considering papers in the last 5 years for Tuckett, how many citations
              were there across all years, showing only those with more than 0
              
              Then make sure they are filtered out if you increase more_than to 100
        """
        views = ocd.most_cited_generator( cited_in_period="All", 
                                          citecount=0,             # more than applies to cited_in_period
                                          publication_period=5,    # num of years before today for publication
                                          author="Tuckett",
                                          title=None,
                                          source_name=None, 
                                          source_code=None,
                                          source_type="journals",  # see VALS_SOURCE_TYPE (norm_val applied in opasCenralDBLib)
                                          limit=None,
                                          offset=0,
                                          session_info=None
                                        )            
        
        countAll5 = len(list(views))
        assert (countAll5 > 0)
        
        views = ocd.most_cited_generator( cited_in_period="All", 
                                          citecount=100,             # more than applies to cited_in_period
                                          publication_period=5,    # num of years before today for publication
                                          author="Tuckett",
                                          title=None,
                                          source_name=None, 
                                          source_code=None,
                                          source_type="journals",  # see VALS_SOURCE_TYPE (norm_val applied in opasCenralDBLib)
                                          limit=None,
                                          offset=0,
                                          session_info=None
                                        )            
        
        countAll5 = len(list(views))
        assert (countAll5 == 0)

    def test_2_most_cited_direct_source(self):
        views = ocd.most_cited_generator( cited_in_period="All",
                                          citecount=0,
                                          author=None,
                                          publication_period=5,
                                          title=None,
                                          source_name=None, 
                                          source_code="IJP",
                                          source_type="journals",  # see VALS_SOURCE_TYPE (norm_val applied in opasCenralDBLib)
                                          limit=None,
                                          offset=0,
                                          session_info=None
                                          )            
        
        countAll5 = len(list(views))
        assert (countAll5 > 400)
        
    def test_2_most_cited_direct_title(self):
        views = ocd.most_cited_generator( cited_in_period="All",
                                          citecount=0,
                                          author=None,
                                          publication_period=5,
                                          title="guilt",
                                          source_name=None, 
                                          source_code="IJP",
                                          source_type="journals",  # see VALS_SOURCE_TYPE (norm_val applied in opasCenralDBLib)
                                          limit=None,
                                          offset=0,
                                          session_info=None
                                          )            
        
        countAll5 = len(list(views))
        assert (countAll5 > 0)

        
    def test_2_most_cited_direct_period1(self):
        views = ocd.most_cited_generator( cited_in_period="All",
                                          citecount=0,
                                          author=None,
                                          publication_period=5,
                                          title=None,
                                          source_name=None, 
                                          source_code=None,
                                          source_type="journals",  # see VALS_SOURCE_TYPE (norm_val applied in opasCenralDBLib)
                                          limit=None,
                                          offset=0,
                                          session_info=None
                                          )            
        
        countAll5 = len(list(views))
        assert (countAll5 > 1400)

    def test_2_most_cited_direct_period2(self):
        views = ocd.most_cited_generator( cited_in_period="All",
                                          citecount=0,
                                          author=None,
                                          publication_period=4,
                                          title=None,
                                          source_name=None, 
                                          source_code=None,
                                          source_type="journals",  # see VALS_SOURCE_TYPE (norm_val applied in opasCenralDBLib)
                                          limit=None,
                                          offset=0,
                                          session_info=None
                                          )            
        countAll4 = len(list(views))
        assert (countAll4 > 1000)
        
    def test_2_most_cited_direct_period3(self):
        views = ocd.most_cited_generator( cited_in_period="All",
                                          citecount=0,
                                          author=None,
                                          publication_period=3,
                                          title=None,
                                          source_name=None, 
                                          source_code=None,
                                          source_type="journals",  # see VALS_SOURCE_TYPE (norm_val applied in opasCenralDBLib)
                                          limit=None,
                                          offset=0,
                                          session_info=None
                                          )            
        countAll3 = len(list(views))
        assert (countAll3 > 500)
        
    def test_2_most_cited_direct_period4(self):
        views = ocd.most_cited_generator( cited_in_period="All",
                                          citecount=0,
                                          author=None,
                                          publication_period=2,
                                          title=None,
                                          source_name=None, 
                                          source_code=None,
                                          source_type="journals",  # see VALS_SOURCE_TYPE (norm_val applied in opasCenralDBLib)
                                          limit=None,
                                          offset=0,
                                          session_info=None
                                          )            
        countAll2 = len(list(views))
        assert (countAll2 > 175)
        
    def test_2_most_cited_direct_period5(self):
        views = ocd.most_cited_generator( cited_in_period="All",
                                          citecount=0,
                                          author=None,
                                          publication_period=1,
                                          title=None,
                                          source_name=None, 
                                          source_code=None,
                                          source_type="journals",  # see VALS_SOURCE_TYPE (norm_val applied in opasCenralDBLib)
                                          limit=None,
                                          offset=0,
                                          session_info=None
                                          )            
        countAll1 = len(list(views))
        assert (countAll1 > 10)

    def test_1_most_cited_endpoint(self):
        response = client.get(base_api + '/v2/Database/MostCited/?download=True') # limit is trick to get it to return #
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        
if __name__ == '__main__':
    unittest.main()
    client.close()
    