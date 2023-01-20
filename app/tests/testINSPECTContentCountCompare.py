#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from .utilityCompareTables import compareTables
import difflib
#import compareTables
import opasCentralDBLib
import opasFileSupport

def get_journal_codes(): 
    sql1 = f"""SELECT distinct src_code from api_articles;"""
    count, rec_list = compareTables.get_range_of_data(sql1)

    return rec_list

class TestContentCountCompare(unittest.TestCase):
    """
    Runs the database compare program, which makes sure the configured tables
      are the same across development, test, and production databases
    
    """
    
    ocd =  opasCentralDBLib.opasCentralDB()
    
    def test_1a(self):
        """
        """
        rec_list = get_journal_codes()
        #sql1 = f"""SELECT distinct src_code from api_articles;"""
        #count, rec_list = compareTables.get_range_of_data(sql1)
        
        dblist = []
        for journal in rec_list:
            journal = journal[0]
            dblist_dict = {"test":f"{journal} article Counts", "name": "api_articles", "key": "art_id", "where": f"WHERE src_code='{journal}'"}
            dblist.append(dblist_dict)

        ret_val, difference_tables = compareTables.compare_server_matched_record_counts(dblist)
        if ret_val > 0:
            print (80*"=")
            print (10*"*FINAL*")
            print ("Table api_articles count differences found!")
            for n in difference_tables:
                print (f"In table: {n}")
            
        assert(ret_val == 0)
        
    def test_2(self):
        """
        In 2023, with the --smartload option, it's essential that for every EXP_ARCH1 we used to load, the original KBD3
        file is present.  This test goes through and checks that there's a matching KBD3 for each EXP_ARCH1.
        
        """
        import localsecrets
        fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root="pep-web-live-data")

        rec_list = get_journal_codes()

        
        for data_class in ("_PEPArchive", "_PEPCurrent"):
            print (f"*** Data Group: {data_class} Checking output bEXP_ARCH1 files***")
            for journal in rec_list:
                journal = journal[0]
                filenames = fs.get_matching_filelist(filespec_regex=f"{journal}.*\(bEXP_ARCH1\).*$", subfolder=f"{data_class}/{journal}/")
                error_count = 0
                for compiled_filename in filenames:
                    source_filename = str(compiled_filename.filespec)
                    source_filename = source_filename.replace("bEXP_ARCH1", "bKBD3")
                    if not fs.exists(source_filename):
                        if "ZBK.069" not in source_filename:
                            alt_source_filename = str(compiled_filename.filespec)
                            alt_source_filename = alt_source_filename.replace("bEXP_ARCH1", "bSeriesTOC")
                            # for books like GW that are a series
                            if not fs.exists(alt_source_filename):
                                error_count += 1
                                print (f"{source_filename} is missing!")
                        
                    
                print (f"{error_count} files were missing for {journal}")
            
    def test_3(self):
        """
        This is intended to catch any KBD3 file which didn't get converted to EXP_ARCH1
        """
        import localsecrets
        fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root="pep-web-live-data")

        rec_list = get_journal_codes()

        
        for data_class in ("_PEPArchive", "_PEPCurrent"):
            print (f"*** Data Group: {data_class} - Checking PDFS ***")
            for journal in rec_list:
                journal = journal[0]
                filenames = fs.get_matching_filelist(filespec_regex=f"{journal}.*\(bKBD3\).*$", subfolder=f"{data_class}/{journal}/")
                error_count = 0
                for compiled_filename in filenames:
                    source_filename = str(compiled_filename.filespec)
                    source_filename = source_filename.replace("bKBD3", "bEXP_ARCH1")
                    if not fs.exists(source_filename):
                        if "ZBK.069" not in source_filename:
                            alt_source_filename = str(compiled_filename.filespec)
                            alt_source_filename = alt_source_filename.replace("bSeriesTOC", "bEXP_ARCH1")
                            # for books like GW that are a series
                            if not fs.exists(alt_source_filename):
                                error_count += 1
                                print (f"{source_filename} is missing!")
                print (f"{error_count} files were missing for {journal}")

    def test_4(self):
        """
        This is intended to catch any KBD3 file which doesn't have an accompanying PDF
        """
        import localsecrets
        fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root="pep-web-live-data")

        rec_list = get_journal_codes()

        for data_class in ("_PEPArchive", "_PEPCurrent"):
            print (f"*** Data Group: {data_class} ***")
            for journal in rec_list:
                journal = journal[0]
                filenames = fs.get_matching_filelist(filespec_regex=f"{journal}.*\(bKBD3\).xml$", subfolder=f"{data_class}/{journal}/")
                error_count = 0
                for compiled_filename in filenames:
                    source_filename = str(compiled_filename.filespec)
                    source_filename = source_filename.replace("(bKBD3).xml", ".pdf")
                    if not fs.exists(source_filename):
                        error_count += 1
                        print (f"{source_filename} is missing!")

                print (f"{error_count} files were missing for {journal}")
            

if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")