#!/usr/bin/env python
# -*- coding: utf-8 -*-

from localsecrets import PADS_TEST_ID, PADS_TEST_PW, CONFIG

import unittest
import requests
import re

from unitTestConfig import base_plus_endpoint_encoded, headers

class TestDocumentImageFetch(unittest.TestCase):
    """
    Tests for image fetch
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.   
    """   
    def test_0_ImageCaseInsensitive(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Image/APA44202.JPG/')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Image/apa44202.JPG/')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Image/apa44202.jpg/')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Image/APA44202.jpg/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_0_ImageExtensionmOmitted(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Image/APA44202')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_0_ImageExtensionmOmittedNoDownload(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Image/JOAP.050.0175.FIG001.jpg?download=2')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        #r = response.json()
        #response_info = r["documents"]["responseInfo"]
        #response_set = r["documents"]["responseSet"] 

    def test_0_ImageCaseSensitive(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Image/ApA44202.JPG?insensitive=False')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully if Windows and fails for Unix.
        if CONFIG != "Local" or localsecrets.CONFIG == "Docker":
            assert(response.ok == False)
        else:
            assert(response.ok == True) # no getting around it on windows

    def test_0_Image1(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Image/bannerIJPLogo.gif/')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_0_Image2(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Image/bannerPEPGRANTVSLogo.gif/')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_1_Image(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Image/infoicon.gif/')
        # local, this works...but fails in the response.py code trying to convert self.status to int.
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_2_Image_of_the_day(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Image/*/')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)

    def test_3_Image_of_the_day_article_id(self):
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Image/*/?download=2')
        response = requests.get(full_URL, headers=headers)
        # Confirm that the request-response cycle completed successfully.
        assert(response.ok == True)
        r = response.json()
        doc = r["documentID"]
        print (doc)
        m = re.match("[A-Z\-]{1,12}\.[0-9]{3,3}[A-Z]?\.(R)?[0-9]{4,4}[A-Z]", doc)
        assert (m is not None)
        # print (m.group())

    def test_4_Made_Up_Image_ID(self):
        # someone is sending code like this...this test is used to check the logging of client id and session id for those clowns.
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Image/SE.019.0074.FIG001/?download=0')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == False)
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Image/SE.019.0074.FIG001/?download=1')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == False)
        full_URL = base_plus_endpoint_encoded(f'/v2/Documents/Image/SE.019.0074.FIG001/?download=2')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == False)


if __name__ == '__main__':
    unittest.main()    