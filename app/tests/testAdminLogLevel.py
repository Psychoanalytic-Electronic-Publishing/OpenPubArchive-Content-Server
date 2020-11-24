#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger()

import unittest
import requests
from unitTestConfig import base_plus_endpoint_encoded, headers

class TestAdminLogLevel(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
          
    The logger tests won't work because the loglevel in the server doesn't
    seem to affect the test client logging.
    """   

    #TODO: Later these will need to be done while logged in.
    
    def test00_loglevel_warning(self):
        full_URL = base_plus_endpoint_encoded('/v2/Admin/LogLevel/?Level=WARN')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        # these don't get affected by the level.
        r = response.json()
        print (f"Loglevel: {r}")
        assert (r == "WARNING") # WARNING
        # set client log level now!
        logger.setLevel(r)
        logger.debug("This should not be logged/displayed since it's debug")
        logger.info("This should not be logged/displayed since it's info")
        logger.warning("This should be logged/displayed since it's warning")
        logger.error("This should be logged/displayed since it's error")

    def test01_loglevel_error(self):
        full_URL = base_plus_endpoint_encoded('/v2/Admin/LogLevel/?level=ERROR')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)      
        r = response.json()
        assert (r == "ERROR")
        # set client log level now!
        logger.setLevel(r)
        logger.debug("This should not be logged/displayed since it's debug")
        logger.info("This should not be logged/displayed since it's info")
        logger.warning("This should not be logged/displayed since it's warning")
        logger.error("This should be logged/displayed since it's error")

    def test02_loglevel_debug(self):
        full_URL = base_plus_endpoint_encoded('/v2/Admin/LogLevel/?level=DEBUG')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)      
        r = response.json()
        print (f"Loglevel: {r}")
        assert (r == "DEBUG")
        # set client log level now!
        logger.setLevel(r)
        logger.debug("This should be logged/displayed since it's debug")
        logger.info("This should be logged/displayed since it's info")
        logger.warning("This should be logged/displayed since it's warning")
        logger.error("This should be logged/displayed since it's error")

    # last test--leave it on info
    def test03_loglevel_info(self):
        full_URL = base_plus_endpoint_encoded('/v2/Admin/LogLevel/?level=INFO')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)      
        r = response.json()
        print (f"Loglevel: {r}")
        assert (r == "INFO") 
        # set client log level now!
        logger.setLevel(r)
        logger.debug("This should not be logged/displayed since it's debug")
        logger.info("This should be logged/displayed since it's info")
        logger.warning("This should be logged/displayed since it's warning")
        logger.error("This should be logged/displayed since it's error")
        

if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")