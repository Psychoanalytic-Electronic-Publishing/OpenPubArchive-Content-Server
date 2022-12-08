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
from localsecrets import CONFIG
import subprocess
TESTLOCATION = r"../tests/testdatasource/_PEPSpecial/IJPOpen"

class TestOpasLoaderProgram(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
          
        opasDataLoader.py --nocheck --nohelp  --smartload --rebuild --verbose --only "X:\IJPOpenTest\IJPOPEN.008.0100A(bKBD3).xml"
    
    """

    def test_recompile_docs(self):
        filespec = fr"{TESTLOCATION}/IJPOPEN.008.0100A(bKBD3).xml"
        result = subprocess.run([sys.executable, '../opasDataLoader/opasDataLoader.py', fr'--only={filespec}', f'--dataroot=""', '--nocheck', '--nohelp', '--smartload', '--rebuild', '--verbose'], capture_output=True)
        out = result.stdout.decode("UTF-8")
        err = result.stderr.decode("UTF-8")
        print ("Stdout:")
        print (out[-2240:])
        print ("Stderr:")
        print (err[-1400:])
        #self.assertIn(b'Load process complete', result.stdout)

    def test_recompile_docs_B(self):
        filespec = fr"{TESTLOCATION}/IJPOPEN.008.0100B(bKBD3).xml"
        result = subprocess.run([sys.executable, '../opasDataLoader/opasDataLoader.py', fr'--only={filespec}', f'--dataroot=""', '--nocheck', '--nohelp', '--smartload', '--rebuild', '--verbose'], capture_output=True)
        out = result.stdout.decode("UTF-8")
        err = result.stderr.decode("UTF-8")
        print ("Stdout:")
        print (out[-2240:])
        print ("Stderr:")
        print (err[-1400:])

    def test_recompile_docs_C(self):
        filespec = fr"{TESTLOCATION}/IJPOPEN.008.0100C(bKBD3).xml"
        result = subprocess.run([sys.executable, '../opasDataLoader/opasDataLoader.py', fr'--only={filespec}', f'--dataroot=""', '--nocheck', '--nohelp', '--smartload', '--rebuild', '--verbose'], capture_output=True)
        out = result.stdout.decode("UTF-8")
        err = result.stderr.decode("UTF-8")
        print ("Stdout:")
        print (out[-2240:])
        print ("Stderr:")
        print (err[-1400:])

if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")