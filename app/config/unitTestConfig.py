#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file has the data counts needed for the server tests.

Version: 2020-08-24

"""

# use the configured server.
from localsecrets import APIURL
# use this to test with whereever the local config points to 
base_api = APIURL
# or override below.
# base_api = "http://stage.pep.gvpi.net/api"
#base_api = "http://127.0.0.1:9100" # local server without naming
#base_api = "http://api.psybrarian.com" # remote AWS server (one of them)
base_api = "http://development.org:9100" #  local server (Scilab)

# this must be set to the number of unique journals for testing to pass.
JOURNALCOUNT = 77
# this must be set to the exact number of unique books for testing to pass.
BOOKCOUNT = 100 # 100 book in 2020 on PEP-Web including 96 various ZBK, NLP, IPL books, + 4 special books: L&P, SE, GW, Glossary
VIDEOSOURCECOUNT = 12 # Number of video sources (video journal codes)
ARTICLE_COUNT_BJP = 2735 # Right.  2738 in everything with query "BJP (bEXP_ARCH1).xml", but 3 dups.
ARTICLE_COUNT_VOL1_BJP = 49
VOL_COUNT_ALL_JOURNALS = 2482
VOL_COUNT_ALL_BOOKS = 113
VOL_COUNT_ZBK = 72 #  72 including 2 offline books (by Kohut)
VOL_COUNT_AOP = 34
VOL_COUNT_GW = 18
VOL_COUNT_SE = 24
VOL_COUNT_IPL = 22
VOL_COUNT_IJPSP = 34
VOL_COUNT_PCT = 26
VOL_COUNT_IMAGO = 23
VOL_COUNT_ALL_VOLUMES = 2580 #  journals and videos
VOL_COUNT_VIDEOS = VIDEOSOURCECOUNT # no actual volumes for videos, just the sources
VOL_COUNT_VIDEOS_PEPVS = 4
VOL_COUNT_IJPSP = 11 #  source code ended, 11 should always be correct

def base_plus_endpoint_encoded(endpoint):
    ret_val = base_api + endpoint
    return ret_val


