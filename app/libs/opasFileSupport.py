#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2020.09.13"
__status__      = "Development"

# #TODO
    # Ensure full PC Local/S3 file system interchangeability/transparency.

# Revision Notes:
    # 20200913 Reworked for better S3 functionality and speed
    # 20200530 Added front matter.  Fixed doctest reference (should have been doc rather than docs)

import sys
import localsecrets
import s3fs # https://s3fs.readthedocs.io/en/latest/api.html#s3fs.core.S3FileSystem
import os, os.path
import re
import boto3
import logging
import datetime
import time
import pathlib

logger = logging.getLogger(__name__)

def file_exists(document_id, year, ext, path=localsecrets.PDF_ORIGINALS_PATH):
    flex_fs = FlexFileSystem(key=localsecrets.S3_KEY,
                             secret=localsecrets.S3_SECRET,
                             root=path) 
    filename = flex_fs.get_download_filename(filespec=document_id, path=path, year=year, ext=ext)
    if filename is None:
        ret_val = False
    else:
        ret_val = True

    return ret_val

class FileInfo(object):
    def __init__(self): 
        self.build_date = time.time()
        self.filespec:str = None
        self.basename:str = None
        self.filesize:int = None
        self.filetype = None
        self.etag:str = None
        self.timestamp_str:str = None
        self.timestamp:datetime.datetime = None # datetime.datetime.strptime(self.timestamp_str, localsecrets.TIME_FORMAT_STR)
        self.date_modified:datetime.datetime = None # self.timestamp.date()
        # self.date_modified_str:str = None # str(self.date)
        self.fileinfo:dict = {}       
        
    def mapS3(self, fileinfo: dict):
        self.fileinfo = fileinfo
        self.filespec = fileinfo["Key"]
        self.basename = os.path.basename(self.filespec)
        self.filesize = fileinfo["Size"]
        self.filetype = fileinfo["type"]
        self.build_date = time.time() # current time
        # modified date
        self.timestamp_str = datetime.datetime.strftime(fileinfo["LastModified"], localsecrets.TIME_FORMAT_STR)
        self.timestamp = datetime.datetime.strptime(self.timestamp_str, localsecrets.TIME_FORMAT_STR)
        self.date_modified = self.timestamp.date()
        # self.date_modified_str = str(self.date_modified)
        self.etag = fileinfo.get("Etag", None)
    
    def mapLocalFS(self, filespec):
        self.fileinfo = {}
        self.filespec = filespec
        self.basename = self.fileinfo["base_filename"] = os.path.basename(self.filespec)
        self.filesize = self.fileinfo["Size"] = os.path.getsize(filespec)
        self.filetype = self.fileinfo["type"] = "xml" # fileinfo["type"]
        self.build_date = self.fileinfo["build_date"] = time.time() # current time
        # modified date
        mod_date = self.fileinfo["fileSize"] = os.path.getmtime(filespec)
        self.timestamp_str = self.fileinfo["LastModified"] = datetime.datetime.utcfromtimestamp(mod_date).strftime(localsecrets.TIME_FORMAT_STR)
        self.timestamp = self.fileinfo["timestamp"] = datetime.datetime.strptime(self.timestamp_str, localsecrets.TIME_FORMAT_STR)
        self.date_modified = self.fileinfo["date"] = self.timestamp.date()
        # self.date_modified_str = str(self.date_modified)
        self.etag = self.fileinfo["Etag"] = None
        

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
        
        # We have potentially many roots (buckets, so don't set by default!)
        if root is None:
            self.root = None # localsecrets.XML_ORIGINALS_PATH
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
        """
        Search for file; return None if not found, filename/path if found.
        """
        if path_root is None:
            path_root = self.root
           
        if localsecrets.S3_KEY is None:
            for root, dirs, files in os.walk(path_root):
                if name in files:
                    ret_val = os.path.join(root, name)
                    break
        else:
            found_info = find_s3_file(bucket=path_root, filename=name)
            try:
                ret_val = found_info[0].get("Key", None)
            except:
                ret_val = None

        return ret_val
       
    def fullfilespec(self, filespec, path=None):
        """
         Get the full file spec
         
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
         
        """
        fileinfo_dict = {}
        ret_obj = FileInfo()
        try:
            if self.key is not None:
                filespec = self.fullfilespec(filespec=filespec, path=path) # "pep-graphics/embedded-graphics"
                ret_obj.filespec = fileinfo_dict["filename"] = filespec
                try:
                    fileinfo_dict = self.fs.info(filespec)
                    ret_obj.mapS3(fileinfo_dict)
                    #ret_obj.basename = fileinfo_dict["base_filename"] = os.path.basename(filespec)
                    #ret_obj.filesize = fileinfo_dict["fileSize"] = fileinfo["Size"]
                    #ret_obj.filetype = fileinfo_dict["type"] = fileinfo["type"]
                    ## get rid of times, we only want dates
                    #ret_obj.timestamp_str = fileinfo_dict["timestamp_str"] = datetime.datetime.strftime(fileinfo["LastModified"], localsecrets.TIME_FORMAT_STR)
                    #ret_obj.timestamp = fileinfo_dict["timestamp"] = datetime.datetime.strptime(fileinfo_dict["timestamp_str"], localsecrets.TIME_FORMAT_STR)
                    #ret_obj.date = fileinfo_dict["date_obj"] = fileinfo_dict["timestamp"].date()
                    #ret_obj.date_str = fileinfo_dict["date_str"] = str(fileinfo_dict["date"])
                    #ret_obj.etag = fileinfo_dict["etag"] = fileinfo.get("Etag", None)
                    #ret_obj.build_date = fileinfo_dict["buildDate"] = time.time()
                    #ret_val = self.fs.info(filespec)
                except Exception as e:
                    logger.error(f"File access error: {e}")
            else: # local FS
                filespec = self.fullfilespec(filespec=filespec, path=path) # "pep-graphics/embedded-graphics"
                #stat = os.stat(filespec)
                ret_obj.basename = fileinfo_dict["base_filename"] = os.path.basename(filespec)
                ret_obj.filesize = fileinfo_dict["fileSize"]  = os.path.getsize(filespec)
                ret_obj.timestamp_str = fileinfo_dict["timestamp_str"] = datetime.datetime.utcfromtimestamp(os.path.getmtime(filespec)).strftime(localsecrets.TIME_FORMAT_STR)
                ret_obj.timestamp = fileinfo_dict["timestamp"] = datetime.datetime.strptime(fileinfo_dict["timestamp_str"], localsecrets.TIME_FORMAT_STR)
                ret_obj.date = fileinfo_dict["date"] = fileinfo_dict["timestamp"].date()
                ret_obj.date_str = fileinfo_dict["date_str"] = str(fileinfo_dict["date"])
                #ret_val["type"] = fileinfo["type"]
                ret_obj.build_date = fileinfo_dict["buildDate"] = time.time()
                
            ret_obj.fileinfo = fileinfo_dict

        except Exception as e:
            logger.error(f"File access error: ({e})")
        
        return ret_obj
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
    def create_text_file(self, filespec, path=None, data=" "):
        """
         >>> fs = FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root=localsecrets.XML_ORIGINALS_PATH)
         >>> res = fs.delete(filespec="test-delete.txt", path=localsecrets.XML_ORIGINALS_PATH)
         >>> fs.create_text_file('test-delete.txt')
         True
        """
        #  see if the file exists
        ret_val = False
        filespec = self.fullfilespec(path=path, filespec=filespec) 
        if self.exists(filespec, path):
            logger.error(f"File {filespec} already exists...exiting.")
            ret_val = False
        else:
            try:
                if self.key is not None:
                    with self.fs.open(filespec, 'a') as out:
                        out.write(data)
                else:
                    with open(filespec, 'a') as out:
                        out.write(data)

            except Exception as e:
                logger.error(f"File write/access error: ({e})")
            else:
                ret_val = True
        
        return ret_val        

    #-----------------------------------------------------------------------------
    def delete(self, filespec, path=None):
        """
        Find if the filespec exists, otherwise return None
        if the instance variable key was set at init, checks s3 otherwise, local file system
        
         >>> fs = FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root=localsecrets.XML_ORIGINALS_PATH)
         >>> fs.delete(filespec="test-delete.txt", path=localsecrets.XML_ORIGINALS_PATH)
         True
        """
        #  see if the file exists
        ret_val = False
        filespec = self.fullfilespec(path=path, filespec=filespec) 
        try:
            if self.key is not None:
                ret_val = self.fs.exists(filespec)
            else:
                ret_val = os.path.exists(filespec)
        except Exception as e:
            logger.error(f"File access error: ({e})")
        
        if ret_val:
            try:
                if self.key is not None:
                    self.fs.rm(filespec)
                else:
                    os.remove(filespec)
            except Exception as e:
                logger.error(f"Can't remove file: ({e})")
                ret_val = False
            else:
                ret_val = True
                
        return ret_val
    
    #-----------------------------------------------------------------------------
    def rename(self, filespec1, filespec2, path=None):
        """

         >>> fs = FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root=localsecrets.XML_ORIGINALS_PATH)
         >>> fs.rename(filespec1="test.txt", filespec2="test-running.txt", path=localsecrets.XML_ORIGINALS_PATH)
         True
         >>> fs.rename(filespec1="test-running.txt", filespec2="test.txt", path=localsecrets.XML_ORIGINALS_PATH)
         True
        """
        #  see if the file exists
        ret_val = False
        filespec1full = self.fullfilespec(path=path, filespec=filespec1) 
        filespec2full = self.fullfilespec(path=path, filespec=filespec2) 
        try:
            if self.key is not None:
                self.fs.rename(filespec1full, filespec2full)
            else:
                os.rename(filespec1full, filespec2full)
        except Exception as e:
            logger.error(f"Can't rename file, File access error: ({e})")
        else:
            ret_val = True
        
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
            ret_val = None
            
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
                logger.warning(f"File {ret_val} not found")
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
                    f = open(filespec, "r", encoding="utf-8")
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
    
    def deprecated_get_matching_filelist_info(self, bucket=None, filespec_regex=None, revised_after_date=None, max_items=None, look_past_match_count=0):
        """
        Return a list of matching files, as s3 fileinfo dicts.
        
        fs convenience function for get_s3_matching_files

        Args:
         - filespec_regex - regexp pattern with folder name and file name pattern, not including the root.
         - Examples:
            get_matching_filelist_info(match_path="_PEPArchive/BAP/.*\.xml", after_revised_date="2020-09-01")
            get_matching_filelist_info(match_path="_PEPCurrent/.*\.xml")

      - is_folder - set to true to find folders

      - revised_after_date - files will only match if their revise date is after this

      - max_items - maximum number of matched files

      - look_past_match_count - a number used to stop searching when we "guess" it should be past the last hit.
           This can limit how many items past a match are searched, e.g., if all the matches are in on folder, then
           if this number is greater than the possible number of items in the folder, it will stop at some point in the next folder or so.
           At least this should be useful for testing...in practice, on AWS, it shouldn't be needed, since hopefully, file search is much
           faster.
    """
        if bucket is None:
            bucket = self.root
            
        ret_val = get_s3_matching_files(bucket=bucket,
                                        subpath_tomatch=filespec_regex,
                                        after_revised_date=revised_after_date,
                                        max_items=max_items,
                                        look_past_match_count=look_past_match_count)
        
        return ret_val

    def get_matching_filelist(self, path=None, filespec_regex=None, revised_after_date=None, max_items=None):
        """
        Return a list of matching files, as FileInfo objects

        Args:
         - path - full path to search
         - filespec_regex - regexp pattern with folder name and file name pattern, not including the root.
         - Examples:
            get_matching_filelist_info(match_path="_PEPArchive/BAP/.*\.xml", after_revised_date="2020-09-01")
            get_matching_filelist_info(match_path="_PEPCurrent/.*\.xml")
        
        """
        ret_val = []
        count = 0
        rc_match = re.compile(filespec_regex, flags=re.IGNORECASE)
        
        if path is None:
            data_folder = pathlib.Path(localsecrets.XML_ORIGINALS_PATH) # "pep-web-xml"
        else:
            if path == pathlib.Path(localsecrets.XML_ORIGINALS_PATH):
                data_folder = pathlib.Path(localsecrets.XML_ORIGINALS_PATH)
            elif self.key is not None:
                # s3 running from local
                data_folder = pathlib.Path(path)
            else:
                data_folder = path
            
        if self.key is not None:
            data_folder = data_folder.as_posix()
            
        kwargs = {"detail": True,}
        if revised_after_date is not None:
            revised_after_date = datetime.datetime.date(datetime.datetime.strptime(revised_after_date, '%Y-%m-%d'))
            
        if self.key is not None:
            for folder, subfolder, files in self.fs.walk(path=data_folder, **kwargs):
                if len(files) > 1:
                    # yes, we have files.
                    for key, val_dict in files.items():
                        # print (key)
                        if rc_match.match(key):
                            fileinfo = FileInfo()
                            fileinfo.mapS3(val_dict)
                            if revised_after_date is not None:
                                if fileinfo.date_modified > revised_after_date:
                                    ret_val.append(fileinfo)
                                    count += 1
                                else:
                                    continue
                            else:
                                ret_val.append(fileinfo)
                                count += 1
                            
                            if max_items is not None:
                                if count >= max_items:
                                    break
    
                if max_items is not None:
                    if count >= max_items:
                        break
        else:
            for folder, subfolder, files in os.walk(data_folder):
                for file in files:
                    # print (key)
                    if rc_match.match(file):
                        fileinfo = FileInfo()
                        filespec = pathlib.Path(folder) / file
                        fileinfo.mapLocalFS(filespec)
                        if revised_after_date is not None:
                            if fileinfo.date_modified > revised_after_date:
                                ret_val.append(fileinfo)
                                count += 1
                            else:
                                continue
                        else:
                            ret_val.append(fileinfo)
                            count += 1
                        
                        if max_items is not None:
                            if count >= max_items:
                                break
    
                if max_items is not None:
                    if count >= max_items:
                        break
            
        return ret_val            
    
    
def get_s3_matching_files(bucket=None,
                          subpath_tomatch=".*",
                          is_folder=False,
                          after_revised_date=None,
                          max_items=None,
                          look_past_match_count: int=0):
    """
    Find matching files where:
      - subpath_tomatch - regexp pattern with folder name and file name pattern, not including the root.
         - Examples:
            get_s3_matching_files(match_path="_PEPArchive/BAP/.*\.xml", after_revised_date="2020-09-01")
            get_s3_matching_files(match_path="_PEPCurrent/.*\.xml")

      - is_folder - set to true to find folders

      - after_revised_date - files will only match if their revise date is after this

      - max_items - maximum number of matched files

      - look_past_match_count - a number used to stop searching when we "guess" it should be past the last hit.
           This can limit how many items past a match are searched, e.g., if all the matches are in on folder, then
           if this number is greater than the possible number of items in the folder, it will stop at some point in the next folder or so.
           At least this should be useful for testing...in practice, on AWS, it shouldn't be needed, since hopefully, file search is much
           faster.
    """
    
    ret_val = []
    if bucket == None:
        bucket = localsecrets.XML_ORIGINALS_PATH
        
    count = 0
    tried = 0
    rc_match = re.compile(subpath_tomatch, flags=re.IGNORECASE)
    after_match_count = 0
    for item in iterate_bucket_items(bucket=bucket):
        tried += 1
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
            print (f"Matched: {item['Key']}")
            # reset after match count
            after_match_count = 0
                
            ret_val.append(item)
            if max_items is not None:
                if count >= max_items:
                    break
        else:
            # no match
            if count > 0: # won't increment unless there's been at least one match
                after_match_count += 1
                if look_past_match_count > 0:
                    if after_match_count > look_past_match_count:
                        break # guess we're past all the hits

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

