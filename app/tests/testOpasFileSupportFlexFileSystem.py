#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests
import opasFileSupport
import localsecrets

from unitTestConfig import base_plus_endpoint_encoded, headers

class TestFSFileSystem(unittest.TestCase):
    def test_01(self):
        filespec = 'pep.css'
        fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root=localsecrets.IMAGE_SOURCE_PATH)
        spec = fs.fullfilespec(filespec=filespec)
        assert spec==localsecrets.IMAGE_SOURCE_PATH + localsecrets.PATH_SEPARATOR + filespec, spec

        filespec = 'IJAPS.016.0181A.FIG002.jpg'
        fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root=localsecrets.IMAGE_SOURCE_PATH)
        spec = fs.fullfilespec(filespec=filespec)
        assert spec==localsecrets.IMAGE_SOURCE_PATH + localsecrets.PATH_SEPARATOR + filespec, spec

    def test_02(self):
        fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY,
                                            secret=localsecrets.S3_SECRET,
                                            root=localsecrets.XML_ORIGINALS_PATH)
        filespec="PEPTOPAUTHVS.001.0021A(bEXP_ARCH1).XML"
        fileinfo = fs.fileinfo(filespec, path="_PEPFree/PEPTOPAUTHVS")
        assert fileinfo.basename == filespec
        assert fileinfo.filesize >= 15000
        #  permission problems when trying to open on stage
        fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY,
                                            secret=localsecrets.S3_SECRET,
                                            root=localsecrets.IMAGE_SOURCE_PATH)
        filespec=r"IJAPS.016.0181A.FIG002.jpg"
        fileinfo = fs.fileinfo(filespec)
        assert fileinfo.basename == filespec, fileinfo.basename 
        assert fileinfo.filesize == 21064, fileinfo.filesize 
       
    def test_03(self):
        filespec = 'test-file.txt'
        filespec2 = 'test-file.txt'
        # create text file
        fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root=localsecrets.XML_ORIGINALS_PATH)
        if fs.exists(filespec):
            # delete in case it exists
            res = fs.delete(filespec=filespec, path=localsecrets.XML_ORIGINALS_PATH)
        # now create it
        fs.create_text_file(filespec=filespec)
        assert fs.exists(filespec) == True
        fs.rename(filespec, filespec2)
        assert fs.exists(filespec2) == True
        fs.delete(filespec=filespec2, path=localsecrets.XML_ORIGINALS_PATH)
        assert fs.exists(filespec2) == False
        
    def test_04(self):
        filespec="PEPTOPAUTHVS.001.0021A(bEXP_ARCH1).xml"
        # create text file
        fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY,
                                            secret=localsecrets.S3_SECRET,
                                            root=localsecrets.XML_ORIGINALS_PATH)
        filefound = fs.find(filespec)
        assert filefound != None
        
    def test_05(self):
        fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY,
                                            secret=localsecrets.S3_SECRET,
                                            root=localsecrets.PDF_ORIGINALS_PATH) # important to use this path, not the XML one!
        document_id = "RPSA.047.0605B"
        filename = fs.get_download_filename(filespec=document_id, path=localsecrets.PDF_ORIGINALS_PATH, year="2001", ext=".PDF")
        if filename is None:
            print (f"file {document_id} doesn't exist")
        else:
            print (f"file {filename} exists")

        assert(filename is None)
        assert(opasFileSupport.file_exists(document_id, year="2001", ext=".PDF") == False)
        
    def test_06(self):
        fs = opasFileSupport.FlexFileSystem(root=localsecrets.IMAGE_SOURCE_PATH) # must be for the image if not the root
        fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY,
                                            secret=localsecrets.S3_SECRET,
                                            root=localsecrets.IMAGE_SOURCE_PATH)
        document_id = "IJAPS.016.0181A.FIG002.jpg"
        filename = fs.get_image_filename(filespec=document_id, path=localsecrets.IMAGE_SOURCE_PATH)
        if filename is None:
            print (f"file {document_id} doesn't exist")
        else:
            print (f"file {filename} exists")

        assert(filename is not None)
        


if __name__ == '__main__':
    unittest.main()
    