import sys
import localsecrets
import s3fs # https://s3fs.readthedocs.io/en/latest/api.html#s3fs.core.S3FileSystem
import os, os.path
import logging
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
        self.key = key
        self.secret = secret
        self.root = root
        # check if local storage or secure storage is enabled
        # self.source_path = path
        try:
            if key is not None:
                self.fs = s3fs.S3FileSystem(anon=anon, key=key, secret=secret)
            else:
                self.fs = None
        except Exception as e:
            logger.error(f"FlexFileSystem initiation error ({e})")

    #-----------------------------------------------------------------------------
    def fullfilespec(self, filespec, path=None):
        """
         Get the full file spec 

         >>> fs = FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root="pep-graphics")
         >>> fs.fullfilespec(filespec="pep.css", path="embedded-graphics")
         'pep-graphics/embedded-graphics/pep.css'

         >>> fs = FlexFileSystem(root=r"X:\\PEP Dropbox\\PEPWeb\\_PEPA1")
         >>> fs.fullfilespec(filespec="IJAPS.016.0181A.FIG002.jpg", path=r"g\")
         'X:\\\\PEP Dropbox\\\\PEPWeb\\\\_PEPA1\\\\g\\\\IJAPS.016.0181A.FIG002.jpg'
        """
        ret_val = filespec
        if self.key is not None:
            if path is not None:
                ret_val = "/".join((path, ret_val)) 
    
            if self.root is not None:
                ret_val = "/".join((self.root, ret_val)) # "pep-graphics/embedded-graphics"
        else:
            if path is None:
                path = ""
            if self.root is None:
                root = ""
            else:
                root = self.root

            ret_val = os.path.join(root, path, filespec)

        return ret_val     
        
            
    #-----------------------------------------------------------------------------
    def fileinfo(self, filespec, path=None):
        """
         Get the file info if it exists, otherwise return None
         if the instance variable key was set at init, checks s3 otherwise, local file system
         
         >>> fs = FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root="pep-graphics")
         >>> fs.fileinfo(filespec="pep.css", path="embedded-graphics")
         {'Key': 'pep-graphics/embedded-graphics/pep.css', 'LastModified': datetime.datetime(2019, 12, 13, 4, 47, 7, tzinfo=tzutc()), 'ETag': '"1b99cd9ae755b36df6bf3bce9cc82603"', 'Size': 22746, 'StorageClass': 'STANDARD', 'type': 'file', 'size': 22746, 'name': 'pep-graphics/embedded-graphics/pep.css'}
         
        """
        ret_val = None
        filespec = self.fullfilespec(filespec=filespec, path=path) # "pep-graphics/embedded-graphics"

        try:
            if self.key is not None:
                ret_val = self.fs.info(filespec)
            else:
                ret_val = os.stat(filespec)
        except Exception as e:
            logger.error(f"File access error: ({e})")
        
        return ret_val     
    #-----------------------------------------------------------------------------
    def exists(self, filespec, path=None):
        """
        Find if the filespec exists, otherwise return None
        if the instance variable key was set at init, checks s3 otherwise, local file system
        
        >>> fs = FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root="pep-graphics")
        >>> fs.exists("pep.css", path="embedded-graphics")
        True
        
        >>> fs.exists("embedded-graphics/pep.css")
        True
        
        #Try local system
        >>> fs = FlexFileSystem()
        >>> fs.exists(r"X:\PEP Dropbox\PEPWeb\_PEPA1\g\IJAPS.016.0181A.FIG002.jpg")
        True
        >>> fs.exists("IJAPS.016.0181A.FIG002.jpg", path=r"X:\PEP Dropbox\PEPWeb\_PEPA1\g\")
        True
        >>> fs = FlexFileSystem(root=r"X:\PEP Dropbox\PEPWeb\_PEPA1\")
        >>> fs.exists(r"g\IJAPS.016.0181A.FIG002.jpg")
        True
        >>> fs.exists("IJAPS.016.0181A.FIG002.jpg", path=r"g")
        True
         
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
    def get_image_filename(self, filespec, path=None):
        """
        Return the file name given the image id, if it exists
        
        >>> fs = FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET)
        >>> fs.get_image_filename("AIM.036.0275A.FIG001", path=localsecrets.IMAGE_SOURCE_PATH)
        'pep-graphics/embedded-graphics/AIM.036.0275A.FIG001.jpg'
        
        >>> fs = FlexFileSystem()
        >>> fs.get_image_filename(r"X:\PEP Dropbox\PEPWeb\_PEPA1\g\IJAPS.016.0181A.FIG002")
        'X:\\\\PEP Dropbox\\\\PEPWeb\\\\_PEPA1\\\\g\\\\IJAPS.016.0181A.FIG002.jpg'
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
        
        curl -X GET "http://stage.pep.gvpi.net/api/v1/Documents/Downloads/Images/aim.036.0275a.fig001.jpg" -H "accept: image/jpeg" -H "Authorization: Basic cC5lLnAuYS5OZWlsUlNoYXBpcm86amFDayFsZWdhcmQhNQ=="
        
        and returns a binary object.
       
        >>> fs = FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET)
        >>> binimg = fs.get_image_binary(filespec="AIM.036.0275A.FIG001", path=localsecrets.IMAGE_SOURCE_PATH)
        >>> len(binimg)
        26038
        
        >>> fs = FlexFileSystem()
        >>> binimg = fs.get_image_binary(r"X:\PEP Dropbox\PEPWeb\_PEPA1\g\AIM.036.0275A.FIG001")
        >>> len(binimg)
        26038
        
            
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
    
    
# Another way to do it...
#from magic import libmagic
#from cloudstorage.drivers.amazon import S3Driver
#import io

#storage = S3Driver(key='AKIAYFOU7FEVLLJVBOBY', secret='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')
#container = storage.get_container('pep-graphics')

#picture_blob = container.get_blob('embedded-graphics/BAP.02.0005.FIG001.jpg')
#picture_blob.size
## 50301
#picture_blob.checksum
## '2f907a59924ad96b7478074ed96b05f0'
#picture_blob.content_type
## 'image/png'
#picture_blob.content_disposition
## 'attachment; filename=picture-attachment.png
##download_url = picture_blob.download_url(expires=3600)

#file_stream = io.StringIO()
#picture_blob.download(file_stream)
#with open(file_stream, mode='rb') as file: # b is important -> binary
    #file_content = file.read()

# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    print (40*"*", "opasFileSupport Tests", 40*"*")
    print ("Running in Python %s" % sys.version_info[0])

    import doctest
    doctest.testmod()    
    print ("Fini")
    sys.exit()

    # test S3FileSystem
    remfs = s3fs.S3FileSystem(anon=False, key='AKIAYFOU7FEVLLJVBOBY', secret='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')
    #fs.ls("embedded-graphics")
    filename_and_path = "pep-graphics/embedded-graphics/BAP.01.0004.FIG001.jpg"
    filename_and_path = "pep-graphics/embedded-graphics/pep.css"
    
    if remfs.ls(filename_and_path) != []:
        # exists
        with remfs.open(filename_and_path, mode='rb') as f:  # doctest: +SKIP
            image_bytes = f.read()
            f.close()    
    
        print (image_bytes)

