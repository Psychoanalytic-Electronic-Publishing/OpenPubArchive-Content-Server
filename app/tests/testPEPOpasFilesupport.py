#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import localsecrets
import pathlib
import datetime as dt
import opasFileSupport

from unitTestConfig import base_plus_endpoint_encoded, headers

class TestOpasFileSupport(unittest.TestCase):
    """
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """

    def test_0_Find(self):
        # This should work whether on local or S3
        if localsecrets.S3_KEY is not None: #  test AWS
            print ("S3 FS tests")

        fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY,
                                            secret=localsecrets.S3_SECRET,
                                            root=localsecrets.XML_ORIGINALS_PATH)
        filename = "ADPSA.001.0007A(bEXP_ARCH1).xml"
        ret_val = fs.find(filename)
        print (ret_val)
        try:
            assert (filename in ret_val)
        except Exception as e:
            print (f"Except: {e}")
            assert (False)
        
    def test_0_exists(self):
        # This should work whether on local or S3
        if localsecrets.S3_KEY is not None: #  test AWS
            print ("S3 FS tests")
        fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY,
                                            secret=localsecrets.S3_SECRET,
                                            root=localsecrets.XML_ORIGINALS_PATH)
        filename = "ADPSA.001.0007A(bEXP_ARCH1).xml"
        ret_val = fs.find(filename)
        print (ret_val)
        try:
            assert (filename in ret_val)
        except Exception as e:
            print (f"Except: {e}")
            assert (False)
        
    def test_1_fetch_file_info(self):
        # get from s3 if localsecrets set to use it
        fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY,
                                            secret=localsecrets.S3_SECRET,
                                            root=localsecrets.XML_ORIGINALS_PATH)

        filename="PEPTOPAUTHVS.001.0021A(bEXP_ARCH1).xml"
        filespec = fs.find(filename)
        ret = fs.fileinfo(filespec=filespec)
        assert (ret.filesize >= 15000)

    def test_0_get_filespec(self):
        # get from s3 if localsecrets set to use it
        if localsecrets.S3_KEY is not None: #  test AWS
            print ("S3 FS tests")
            fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY,
                                                secret=localsecrets.S3_SECRET,
                                                root=localsecrets.IMAGE_SOURCE_PATH)
            ret = fs.fullfilespec(filespec="IJAPS.016.0181A.FIG002.jpg", path=localsecrets.IMAGE_SOURCE_PATH)
            assert(ret ==f'{localsecrets.IMAGE_SOURCE_PATH}/IJAPS.016.0181A.FIG002.jpg')
        else:
            print ("Local FS tests")
            fs = opasFileSupport.FlexFileSystem(root=localsecrets.XML_ORIGINALS_PATH)
            # >>> fs.fullfilespec(filespec="pep.css", path="embedded-graphics")
            'pep-graphics/embedded-graphics/pep.css'
            ret = fs.fullfilespec(filespec="IJAPS.016.0181A.FIG002.jpg", path=localsecrets.IMAGE_SOURCE_PATH)
            assert(ret == 'X:\\AWS_S3\\AWS PEP-Web-Live-Data\\graphics\\IJAPS.016.0181A.FIG002.jpg')
   
    def test_2_exists(self):
        fs = opasFileSupport.FlexFileSystem(root=localsecrets.IMAGE_SOURCE_PATH)
        ret = fs.exists(filespec="IJAPS.016.0181A.FIG002.jpg", path=localsecrets.IMAGE_SOURCE_PATH)
        assert(ret == True)
        ret = fs.exists(filespec="IJAPS.016.0181A.FIG002B.jpg", path=localsecrets.IMAGE_SOURCE_PATH)
        assert(ret == False)
   
    def test_3_get_download_filename(self):
        """
        """
        fs = opasFileSupport.FlexFileSystem(root=localsecrets.PDF_ORIGINALS_PATH)
        filespec = "AIM.026.0021A.pdf"
        ret = fs.get_download_filename(filespec=filespec, path=localsecrets.PDF_ORIGINALS_PATH)
        print (ret)
        assert(filespec in ret)
   
    def test_4_get_image_filename(self):
        """
        """
        fs = opasFileSupport.FlexFileSystem(root=localsecrets.IMAGE_SOURCE_PATH) # must be for the image if not the root
        filespec = "AIM.036.0275A.FIG001"
        ret = fs.get_image_filename(filespec=filespec, path=localsecrets.IMAGE_SOURCE_PATH)
        print (ret)
        assert(filespec in ret)
        ret = fs.get_image_filename(filespec=filespec)
        print (ret)
        assert(filespec in ret)
   
    def test_5_get_image_len(self):
        """
        >>> fs = FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET)
        >>> binimg = fs.get_image_binary(filespec="AIM.036.0275A.FIG001", path=localsecrets.IMAGE_SOURCE_PATH)
        >>> len(binimg)
        26038
        
        """
        fs = opasFileSupport.FlexFileSystem(root=localsecrets.IMAGE_SOURCE_PATH) # must be for the image if not the root
        filespec = "AIM.036.0275A.FIG001"
        img_bin = fs.get_image_binary(filespec=filespec, path=localsecrets.IMAGE_SOURCE_PATH)
        image_len = len(img_bin)
        print (image_len)
        assert(image_len >= 26038)
   
    def test_6_get_file_contents(self):
        """
        # left in for an example
        >> fs = FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET)
        >> file_content = fs.get_file_contents(filespec='pep-web-xml/_PEPArchive/ADPSA/001.1926/ADPSA.001.0007A(bEXP_ARCH1).XML', path=None)
        >> a = len(file_content)
        >> print (a)
        692
        
        """
        fs = opasFileSupport.FlexFileSystem(root=localsecrets.XML_ORIGINALS_PATH) # must be for the image if not the root
        filespec = "ADPSA.001.0007A(bEXP_ARCH1).xml"
        content, fileinfo = fs.get_file_contents(filespec=filespec, path=localsecrets.XML_ORIGINALS_PATH)
        content_len = len(content)
        print (content_len)
        assert(content_len >= 691)
    
    def test_7_get_matching_filenames(self):
        
        pat = r"(.*?)\((bEXP_ARCH1|bSeriesTOC)\)\.(xml|XML)$"
        fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY,
                                            secret=localsecrets.S3_SECRET,
                                            root=localsecrets.XML_ORIGINALS_PATH)

        root = pathlib.Path(localsecrets.XML_ORIGINALS_PATH)
        testsubpath = "_PEPCurrent/IJP/"
        testfullpath = root / testsubpath
        # two weeks to today
        two_weeks_ago = dt.date.today() - dt.timedelta(days=14)
        matchlist = fs.get_matching_filelist(path=testfullpath, filespec_regex=pat, revised_after_date=str(two_weeks_ago))
        print (len(matchlist))
        assert (len(matchlist) >= 1)

        matchlist = fs.get_matching_filelist(path=testfullpath, filespec_regex=pat)
        print (len(matchlist))
        assert (len(matchlist) >= 100)

        matchlist = fs.get_matching_filelist(path=testfullpath, filespec_regex=pat, max_items=20)
        print (len(matchlist))
        assert (len(matchlist) >= 20)

        matchlist = fs.get_matching_filelist(path=testfullpath, filespec_regex=pat, max_items=20)
        print (len(matchlist))
        assert (len(matchlist) >= 20)

        # function removed 2021-05-05
           #res = opasFileSupport.get_s3_matching_files(subpath_tomatch="_PEPArchive/BAP/.*\.xml", after_revised_date="2020-09-01")
           #res = opasFileSupport.get_s3_matching_files(subpath_tomatch="_PEPCurrent/.*\.xml")
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")