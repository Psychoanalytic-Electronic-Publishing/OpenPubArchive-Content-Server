#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2020, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2020.05.30"
__status__      = "Development"

#Revision Notes:
    #20200530 Added front matter.  Fixed doctest reference (should have been doc rather than docs)

import sys
import localsecrets
import s3fs # https://s3fs.readthedocs.io/en/latest/api.html#s3fs.core.S3FileSystem
import os, os.path
import re
import boto3
import logging
import datetime
import time

logger = logging.getLogger(__name__)

class FlexFileSystem(object):
    """
    File access to different types of file systems, 'transparently',
      the only difference being the path and if there's a key, then
      it's accessed via secure S3.
      
    Uses the s3fs library which does the heavy lifting, the only purpose
      of this class is to provide file operations transparently
      wherever the file may be, depending on how the class is initialized

      https://s3fs.readthedocs.io/en/latest/api.html#s3fs.core.S3FileSystem
      
    """

    def __init__(self, key=None, secret=None, anon=False, root=None):
        if key is None:
            self.key = localsecrets.S3_KEY
        else:
            self.key = key

        if secret is None:
            self.secret = localsecrets.S3_SECRET
        else:
            self.secret = secret
        
        if root is None:
            self.root = localsecrets.FILESYSTEM_ROOT
        else:
            self.root = root

        # check if local storage or secure storage is enabled
        # self.source_path = path
        try:
            if self.key is not None:
                self.fs = s3fs.S3FileSystem(anon=anon, key=key, secret=secret)
            else:
                self.fs = None
                
        except Exception as e:
            logger.error(f"FlexFileSystem initiation error ({e})")

    def find(self, name, path_root=None):
        if path_root is None:
            path_root = self.root
           
        if localsecrets.S3_KEY is None:
            for root, dirs, files in os.walk(path_root):
                if name in files:
                    ret_val = os.path.join(root, name)
                    break
        else:
            found_info = find_s3_file(bucket=self.root, filename=name)
            try:
                ret_val = found_info[0].get("Key", None)
            except:
                ret_val = None

        return ret_val
       
    def fullfilespec(self, filespec, path=None):
        """
         Get the full file spec 

         >>> fs = FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root="pep-graphics")
         >>> fs.fullfilespec(filespec="pep.css", path="embedded-graphics")
         'pep-graphics/embedded-graphics/pep.css'

         >>> fs = FlexFileSystem(root=r"X:\\_PEPA1")
         >>> fs.fullfilespec(filespec="IJAPS.016.0181A.FIG002.jpg", path=r"g\")
         'X:\\\\_PEPA1\\\\g\\\\IJAPS.016.0181A.FIG002.jpg'
        """
        ret_val = filespec
        if self.key is not None:
            if path is not None:
                ret_val = localsecrets.PATH_SEPARATOR.join((path, ret_val)) 
    
            if self.root is not None:
                m = re.match(self.root+".*", ret_val, flags=re.IGNORECASE)
                if m is None:
                    ret_val = localsecrets.PATH_SEPARATOR.join((self.root, ret_val)) # "pep-graphics/embedded-graphics"
        else:
            if path is None:
                path = ""
            if self.root is None:
                root = ""
            else:
                root = self.root

            ret_val = os.path.join(root, path, filespec)

        if localsecrets.PATH_SEPARATOR == "/":
            ret_val = ret_val.replace("\\", localsecrets.PATH_SEPARATOR)
        else: # change forward slash to backslash
            ret_val = ret_val.replace("/", localsecrets.PATH_SEPARATOR)

        return ret_val     
    #-----------------------------------------------------------------------------
    def fileinfo(self, filespec, path=None):
        """
         Get the file info if it exists, otherwise return None
         if the instance variable key was set at init, checks s3 otherwise, local file system
         
         >>> fs = FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root="pep-web-xml")
         >>> fs.fileinfo(filespec="PEPTOPAUTHVS.001.0021A(bEXP_ARCH1).XML", path="_PEPFree/PEPTOPAUTHVS")
         {'filename': 'pep-web-xml/_PEPFree/PEPTOPAUTHVS/PEPTOPAUTHVS.001.0021A(bEXP_ARCH1).XML', 'base_filename': 'PEPTOPAUTHVS.001.0021A(bEXP_ARCH1).XML', 'timestamp_str': '2020-09-02T23:15:18Z', 'timestamp_obj': datetime.datetime(2020, 9, 2, 23, 15, 18), 'date_obj': datetime.date(2020, 9, 2), 'date_str': '2020-09-02', 'fileSize': 16719, 'type': 'file', 'etag': None, 'buildDate': ...}
         
         >>> fs = FlexFileSystem()
         >>> fs.fileinfo(filespec=r"x:\_PEPA1\g\IJAPS.016.0181A.FIG002.jpg")
         {'base_filename': 'IJAPS.016.0181A.FIG002.jpg', 'timestamp_str': '2019-12-12T18:59:31Z', 'timestamp_obj': datetime.datetime(2019, 12, 12, 18, 59, 31), 'fileSize': 21064, 'date_obj': datetime.date(2019, 12, 12), 'date_str': '2019-12-12', 'buildDate': ...}
         
        """
        ret_val = {}
        try:
            if self.key is not None:
                filespec = self.fullfilespec(filespec=filespec, path=path) # "pep-graphics/embedded-graphics"
                ret_val["filename"] = filespec
                try:
                    fileinfo = self.fs.info(filespec)
                    ret_val["base_filename"] = os.path.basename(filespec)
                    # get rid of times, we only want dates
                    ret_val["timestamp_str"] = datetime.datetime.strftime(fileinfo["LastModified"], localsecrets.TIME_FORMAT_STR)
                    ret_val["timestamp_obj"] = datetime.datetime.strptime(ret_val["timestamp_str"], localsecrets.TIME_FORMAT_STR)
                    ret_val["date_obj"] = ret_val["timestamp_obj"].date()
                    ret_val["date_str"] = str(ret_val["date_obj"])
                    ret_val["fileSize"] = fileinfo["Size"]
                    ret_val["type"] = fileinfo["type"]
                    ret_val["etag"] = fileinfo.get("Etag", None)
                    ret_val["buildDate"] = time.time()
                    #ret_val = self.fs.info(filespec)
                except Exception as e:
                    logger.error(f"File access error: {e}")
            else: # local FS
                #stat = os.stat(filespec)
                ret_val["base_filename"] = os.path.basename(filespec)
                ret_val["timestamp_str"] = datetime.datetime.utcfromtimestamp(os.path.getmtime(filespec)).strftime(localsecrets.TIME_FORMAT_STR)
                ret_val["timestamp_obj"] = datetime.datetime.strptime(ret_val["timestamp_str"], localsecrets.TIME_FORMAT_STR)
                ret_val["fileSize"]  = os.path.getsize(filespec)
                ret_val["date_obj"] = ret_val["timestamp_obj"].date()
                ret_val["date_str"] = str(ret_val["date_obj"])
                #ret_val["type"] = fileinfo["type"]
                ret_val["buildDate"] = time.time()
                
        except Exception as e:
            logger.error(f"File access error: ({e})")
        
        return ret_val     
    #-----------------------------------------------------------------------------
    def exists(self, filespec, path=None):
        """
        Find if the filespec exists, otherwise return None
        if the instance variable key was set at init, checks s3 otherwise, local file system
        """
        #  see if the file exists
        ret_val = None
        filespec = self.fullfilespec(path=path, filespec=filespec) # "pep-graphics/embedded-graphics"
        try:
            if self.key is not None:
                ret_val = self.fs.exists(filespec)
            else:
                ret_val = os.path.exists(filespec)
        except Exception as e:
            logger.error(f"File access error: ({e})")
        
        return ret_val        
    #-----------------------------------------------------------------------------
    def get_download_filename(self, filespec, path="", year=None, ext=None):
        """
        Return the file name given the filespec, if it exists
      
        """
        # split name to get folder subpath for downloads
        try:
            filespec = filespec.strip()
            fsplit = filespec.split(".")
            jrnlcode, vol, pagenum = fsplit[0:3]
            # remove any suffix for vol, so we don't need to separate the folders
            vol_clean = ''.join(i for i in vol if i.isdigit())
        except Exception as e:
            logger.warning(f"Could not split filespec into path: {filespec}. ({e})")
            subpath = ""
        else:
            subpath = f"/{jrnlcode}/{vol_clean}" #  pad volume to 3 digits with 0

        ret_val = self.fullfilespec(path=path + subpath, filespec=filespec) # "pep-graphics/embedded-graphics"
        if ext is not None:
            ret_val = ret_val + ext  
            
        if not self.exists(ret_val):
            logger.warning(f"Download file does not exist: {ret_val}")
            
        return ret_val   
    #-----------------------------------------------------------------------------
    def get_image_filename(self, filespec, path=None):
        """
        Return the file name given the image id, if it exists
        
        """
        # check if local storage or secure storage is enabled
        ret_val = self.fullfilespec(path=path, filespec=filespec) # "pep-graphics/embedded-graphics"

        # look to see if the file type has been specified via extension
        ext = os.path.splitext(ret_val)[-1].lower()
        if ext in (".jpg", ".tif", ".gif"):
            exists = self.exists(ret_val)
            if not exists:
                ret_val = None
        else:
            if self.exists(ret_val + ".jpg"):
                ret_val = ret_val + ".jpg"
            elif self.exists(ret_val + ".gif"):
                ret_val = ret_val + ".gif"
            elif  self.exists(ret_val + ".tif"):
                ret_val = ret_val + ".tif"
            else:
                ret_val = None
    
        return ret_val   
    #-----------------------------------------------------------------------------
    def get_image_binary(self, filespec, path=None):
        """
        Return a binary object of the image, e.g.,

        Note: the current server requires the extension, but it should not.  The server should check
        for the file per the following extension hierarchy: .jpg then .gif then .tif
        
        However, if the extension is supplied, that should be accepted.
    
        The current API implements this:
        
        curl -X GET "http://stage.pep.gvpi.net/api/v1/Documents/Downloads/Images/aim.036.0275a.fig001.jpg" -H "accept: image/jpeg" 
        
        and returns a binary object.
       
        """
        ret_val = None
        image_filename = self.get_image_filename(filespec, path=path)
        if image_filename is not None:
            try:
                if self.fs is not None:
                    f = self.fs.open(image_filename, "rb")
                else:
                    f = open(image_filename, "rb")
            except Exception as e:
                logger.error("getImageBinary: Open Error: %s", e)
                
            try:
                image_bytes = f.read()
                f.close()    
            except OSError as e:
                logger.error("getImageBinary: Read Error: %s", e)
            except Exception as e:
                logger.error("getImageBinary: Error: %s", e)
            else:
                ret_val = image_bytes
        else:
            logger.error("Image File ID %s not found", filespec)
      
        return ret_val
    #-----------------------------------------------------------------------------
    def get_file_contents(self, filespec, path=None):
        """
        Return the contents of a non-binary file

        The current API implements this:
        
        curl -X GET "http://stage.pep.gvpi.net/api/v1/Documents/Downloads/Images/aim.036.0275a.fig001.jpg" -H "accept: image/jpeg" -H "Authorization: Basic cC5lLnAuYS5OZWlsUlNoYXBpcm86amFDayFsZWdhcmQhNQ=="
        
        and returns a binary object.
       
        """
        ret_val = None
        if not self.exists(filespec, path):
            filespec = self.find(filespec, path_root=path)
            
        filespec = self.fullfilespec(filespec)
        if filespec is not None:
            try:
                if self.fs is not None:
                    f = self.fs.open(filespec, "r", encoding="utf-8")
                else:
                    f = open(filespec, "r")
            except Exception as e:
                logger.error("Open Error: %s", e)
                
            try:
                ret_val = f.read()
                f.close()    
            except OSError as e:
                logger.error("Read Error: %s", e)
            except Exception as e:
                logger.error("Error: %s", e)
        else:
            logger.error("File %s not found", filespec)
      
        return ret_val

def get_s3_matching_files(bucket=None,
                          subpath_tomatch=".*",
                          is_folder=False,
                          after_revised_date=None,
                          max_items=None):
    """
    >> get_s3_matching_files(match_path="_PEPArchive/BAP/.*\.xml", after_revised_date="2020-09-01")

    >> ret =get_s3_matching_files(match_path="_PEPCurrent/.*\.xml")
    >> len(ret)

    >> ret =get_s3_matching_files(match_path="_PEPArchive/.*\.xml")
    >> len(ret)
    
    """
    
    ret_val = []
    if bucket == None:
        bucket = localsecrets.FILESYSTEM_ROOT
        
    count = 0
    rc_match = re.compile(subpath_tomatch, flags=re.IGNORECASE)
    for item in iterate_bucket_items(bucket=bucket):
        m = rc_match.match(item["Key"])
        if m:
            if is_folder == True:
                if item.Size !=  0:
                    continue
            elif after_revised_date is not None:
                after_revised_date_obj = datetime.datetime.date(datetime.datetime.strptime(after_revised_date, '%Y-%m-%d'))
                item_date = datetime.datetime.date(item["LastModified"])
                if item_date <= after_revised_date_obj:
                    continue

            count = count + 1
            ret_val.append(item)
            if max_items is not None:
                if count >= max_items:
                    break

    return ret_val            

def find_s3_file(bucket=r'pep-web-xml',
                 filename=None,
                 is_folder=False,
                 max_items=1):
    """
    Walk through an S3 bucket to find a file
    """
    ret_val = []
    count = 0
    for item in iterate_bucket_items(bucket=bucket):
        if filename in item["Key"]:
            if is_folder == True:
                if item.Size !=  0:
                    continue

            count = count + 1
            ret_val.append(item)
            if max_items is not None:
                if count >= max_items:
                    break

    return ret_val            
        

def iterate_bucket_items(bucket):
    """
    Generator that iterates over all objects in a given s3 bucket

    See http://boto3.readthedocs.io/en/latest/reference/services/s3.html#S3.Client.list_objects_v2 
    for return data format
    :param bucket: name of s3 bucket
    :return: dict of metadata for an object
    
    >> [i for i in iterate_bucket_items(bucket=r'pep-web-xml\\_PEPArchive\\ADPSA\\001.1926')]
    >> print (i[0])
    >> for i in iterate_bucket_items(bucket=r'pep-web-xml') : print(i)
    
    """

    client = boto3.client('s3')
    paginator = client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket)
    for page in page_iterator:
        if page['KeyCount'] > 0:
            for item in page['Contents']:
                yield item

# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    print (40*"*", "opasFileSupport Tests", 40*"*")
    print ("Running in Python %s" % sys.version_info[0])

    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
    print ("Fini. opasFileSupport Tests complete.")
    sys.exit()

    # test S3FileSystem
    remfs = s3fs.S3FileSystem(anon=False, key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET)
    #fs.ls("embedded-graphics")
    filename_and_path = "pep-web-files/doc/g/BAP.01.0004.FIG001.jpg"
    
    try:
        if remfs.ls(filename_and_path) != []:
            # exists
            with remfs.open(filename_and_path, mode='rb') as f:  # doctest: +SKIP
                image_bytes = f.read()
                f.close()    
        
            print (image_bytes)
    except Exception as e:
        print (f"Error: {e}")

