#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant
#2023.0519 # Split tests from 1 into 10 separate tests to make it easier to review results and any issues.  
# (Code is repetitive as a result of simply copying the tests)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import unittest
import shlex, subprocess
import sys
import glob
#from unitTestConfig import base_api, base_plus_endpoint_encoded, headers
#import opasAPISupportLib
#import opasConfig
#import opasQueryHelper
import opasCentralDBLib
#import opasGenSupportLib
#import models
#import opasPySolrLib
#from opasPySolrLib import search_text

from pathlib import Path

ocd = opasCentralDBLib.opasCentralDB()

class TestXMLProcessing(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    
    1) load dbs from EXP_ARCH1 files (as per previous funct.)

       opasloader -d X:\_PEPA1\_PEPa1v\_PEPCurrent --sub ANIJP-TR
       
       same as 

       opasloader -d X:\_PEPA1\_PEPa1v\_PEPCurrent --sub ANIJP-TR --inputbuild=bEXP_ARCH1
       
       Messaging verbose:  False
       
       Output (on PC):
          ...
          Input data Root:  X:\_PEPA1\_PEPa1v\_PEPCurrent
          Input data Subfolder:  ANIJP-TR
          Precompiled XML of build (bEXP_ARCH1) will be loaded to the databases without further compiling/processing:
          Reset Core Data:  False
          ********************************************************************************
          Database will be updated. Location: development.org
          Solr Full-Text Core will be updated:  http://development.org:8983/solr/pepwebdocs
          Solr Authors Core will be updated:  http://development.org:8983/solr/pepwebauthors
          Solr Glossary Core will be updated:  http://development.org:8983/solr/pepwebglossary
          ********************************************************************************
          Paragraphs only stored for sources indicated in loaderConfig.
          ********************************************************************************
          Locating files for processing at X:\_PEPA1\_PEPa1v\_PEPCurrent\ANIJP-TR with build pattern (bEXP_ARCH1). Started at (Tue Jul 19 11:15:25 2022).
          --------------------------------------------------------------------------------
          Ready to Load 25 files *if modified* at path: X:\_PEPA1\_PEPa1v\_PEPCurrent\ANIJP-TR
          Processing started at (Tue Jul 19 11:15:25 2022).
          --------------------------------------------------------------------------------
          Load started (Tue Jul 19 11:15:25 2022).  Examining files.
          Load process complete (Tue Jul 19 11:15:26 2022 ). Time: 0.03997325897216797 seconds.
          Cleaned up artstat: removed article statistics for any article ids not in article table.
          Finished! Loaded 0 documents (bEXP_ARCH1). Total file load time: 1.32 secs (0.02 minutes.)
          Note: File load time is not total elapsed time. Total elapsed time is: 1.32 secs (0.02 minutes.)

       
    2) force reload dbs from EXP_ARCH1 files (as per previous funct.)

       opasloader -d X:\_PEPA1\_PEPa1v\_PEPCurrent --sub ANIJP-TR --reload
       
          Output on PC:
          
             Messaging verbose:  False
             Input data Root:  X:\_PEPA1\_PEPa1v\_PEPCurrent
             Input data Subfolder:  ANIJP-TR
             Precompiled XML of build (bEXP_ARCH1) will be loaded to the databases without further compiling/processing:
             Reset Core Data:  False
             Forced Rebuild - All files added, regardless of whether they are the same as in Solr.
             ********************************************************************************
             Database will be updated. Location: development.org
             Solr Full-Text Core will be updated:  http://development.org:8983/solr/pepwebdocs
             Solr Authors Core will be updated:  http://development.org:8983/solr/pepwebauthors
             Solr Glossary Core will be updated:  http://development.org:8983/solr/pepwebglossary
             ********************************************************************************
             Paragraphs only stored for sources indicated in loaderConfig.
             ********************************************************************************
             Locating files for processing at X:\_PEPA1\_PEPa1v\_PEPCurrent\ANIJP-TR with build pattern (bEXP_ARCH1). Started at (Tue Jul 19 11:15:37 2022).
             --------------------------------------------------------------------------------
             Ready to Load records from 25 files at path X:\_PEPA1\_PEPa1v\_PEPCurrent\ANIJP-TR
             Processing started at (Tue Jul 19 11:15:37 2022).
             --------------------------------------------------------------------------------
             Load started (Tue Jul 19 11:15:37 2022).  Examining files.
             Load process complete (Tue Jul 19 11:15:47 2022 ). Time: 0.22304987907409668 seconds.
             Performing final commit.
             Cleaned up artstat: removed article statistics for any article ids not in article table.
             Finished! Loaded 25 documents and 5 references. Total file inspection/load time: 10.99 secs (0.18 minutes.)
             ...Files per Min: 136.4688
             ...Files evaluated per Min (includes skipped files): 136.4688
             Note: File load time is not total elapsed time. Total elapsed time is: 10.99 secs (0.18 minutes.)
             Files per elapsed min: 136.4565
      

    3) load dbs from EXP_ARCH1 files, but process KBD3 to EXP_ARCH1 if KBD3 file has been modified or there's no EXP_ARCH1

       opasloader -d X:\_PEPA1\_PEPa1v\_PEPCurrent --sub ANIJP-TR --smartload

          Output on PC:
             Messaging verbose:  False
             Input data Root:  X:\_PEPA1\_PEPa1v\_PEPCurrent
             Input data Subfolder:  ANIJP-TR
             Input form of XML of build (bKBD3|bSeriesTOC) will be compiled, saved, and loaded to the database unless already compiled version
             Reset Core Data:  False
             ********************************************************************************
             Database will be updated. Location: development.org
             Solr Full-Text Core will be updated:  http://development.org:8983/solr/pepwebdocs
             Solr Authors Core will be updated:  http://development.org:8983/solr/pepwebauthors
             Solr Glossary Core will be updated:  http://development.org:8983/solr/pepwebglossary
             ********************************************************************************
             Paragraphs only stored for sources indicated in loaderConfig.
             ********************************************************************************
             Locating files for processing at X:\_PEPA1\_PEPa1v\_PEPCurrent\ANIJP-TR with build pattern (bKBD3). Started at (Tue Jul 19 11:22:21 2022).
             --------------------------------------------------------------------------------
             Ready to Smart compile, save and load 25 files *if modified* at path: X:\_PEPA1\_PEPa1v\_PEPCurrent\ANIJP-TR
             Processing started at (Tue Jul 19 11:22:21 2022).
             --------------------------------------------------------------------------------
             Smart compile, save and load started (Tue Jul 19 11:22:21 2022).  Examining files.
             Smart compile, save and load process complete (Tue Jul 19 11:22:22 2022 ). Time: 0.032021522521972656 seconds.
             Cleaned up artstat: removed article statistics for any article ids not in article table.
             Finished! Smart compiled, saved and loaded 0 documents (bEXP_ARCH1). Total file load time: 1.08 secs (0.02 minutes.)
             Note: File load time is not total elapsed time. Total elapsed time is: 1.08 secs (0.02 minutes.)
          
       
    
    3) only build EXP_ARCH1 files from KBD3

       opasloader --verbose --sub _PEPCurrent/ANIJP-TR 
    
    4) load dbs from KBD3 files and write EXP_ARCH1's for quicker reprocessing later or QA
    
       opasloader --only "X:\_PEPA1\_PEPa1v\_PEPCurrent\CFP\012.2022\CFP.012.0022A(bKBD3).xml" --nocheck --processxml --writeprocessed --outputbuild=bEXP_TEST
       
    
    """

    DocumentID = [
                  ('IJP.101.0273A', 'B.*'), 
                  ('LU-AM.005I.0025A', 'B0001'),
                  ('CPS.039.0107A', 'B0008'), 
                  ('CPS.039.0107A', 'B0003'),
                  ]

    pycmd = Path(sys.executable)
    curr_folder = Path(os.getcwd())
    load_prog = Path("../opasDataLoader/opasDataLoader.py")
    pycmd = f"{pycmd} {load_prog}"       

    data_file1 = r"--key CFP.012.0022A"
    data_folder = curr_folder / "testxml"
    delete_exp_arch1_files = curr_folder / "testxml/*ARCH1*.xml"
    data_file3 = fr"--dataroot {data_folder}"
    data_file2 = curr_folder / "testxml/PEPGRANTVS.001.0017A(bKBD3).xml"
    data_file2 = f"--only {data_file2}"
    print (f"Data file3 folder: {data_file3}")
           
    def test_1_bld_from_kbd3(self):       
        command_lines = [
            # Force build via REBUILD option (or RELOAD) forces the build
            ("Finished!", "loaded 27 documents", fr"{self.pycmd} {self.data_file3} --nocheck --nohelp --rebuild --inputbuild=bKBD3 --outputbuild=bEXP_ARCH1"),
        ]
        
        test_counter = 1
        for command_line_tuple in command_lines:
            #print (command_line)
            test_line = command_line_tuple[0]
            test_text = command_line_tuple[1]
            command_line = command_line_tuple[2]
            args = shlex.split(command_line, posix=False)
            print(f"Test {test_counter}. RUN: opasDataLoader {args[2:]}")
            p = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True) # Success!
            out, err = p.communicate()
            try:
                out_str = str(out, 'utf-8')
            except Exception as e:
                out_str = str(out)
            
            result = out_str.split('\r\n')
            
            for lin in result:
                if "Processing file" in lin or "Writing file" in lin or "Finished!" in lin or "Exporting!" or "Loaded" in lin:
                    print(lin)
           
                if test_line in lin:
                    assert test_text in lin, (test_text, lin)
                    print (f"Test {test_counter} passed.")
                    if "bEXP_ARCH1" in lin:
                        print (f"Deleting temporary test files: {self.delete_exp_arch1_files}")
                        file_list = glob.glob(str(f"{self.delete_exp_arch1_files}"))
                        count = 0
                        for file_path in file_list:
                            try:
                                os.remove(file_path)
                                count += 1
                            except:
                                print("Error while deleting file : ", file_path)                        
                        print (f"Deleted {count} temporary test files.")

    def test_2_bld_from_kbd3(self):
               
        command_lines = [
            ("Finished!", "loaded 0 documents (bEXP_ARCH1)", fr"{self.pycmd} {self.data_file3} --nocheck --nohelp --verbose --smartload --inputbuild=bKBD3"),
            # The parens () around builds now optional, they will be added if missing
        ]
        
        test_counter = 2
        for command_line_tuple in command_lines:
            #print (command_line)
            test_line = command_line_tuple[0]
            test_text = command_line_tuple[1]
            command_line = command_line_tuple[2]
            args = shlex.split(command_line, posix=False)
            print(f"Test {test_counter}. RUN: opasDataLoader {args[2:]}")
            p = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True) # Success!
            out, err = p.communicate()
            try:
                out_str = str(out, 'utf-8')
            except Exception as e:
                out_str = str(out)
            
            result = out_str.split('\r\n')
            
            for lin in result:
                if "Processing file" in lin or "Writing file" in lin or "Finished!" in lin or "Exporting!" or "Loaded" in lin:
                    print(lin)
           
                if test_line in lin:
                    assert test_text in lin, (test_text, lin)
                    print (f"Test {test_counter} passed.")
                    if "bEXP_ARCH1" in lin:
                        print (f"Deleting temporary test files: {self.delete_exp_arch1_files}")
                        file_list = glob.glob(str(f"{self.delete_exp_arch1_files}"))
                        count = 0
                        for file_path in file_list:
                            try:
                                os.remove(file_path)
                                count += 1
                            except:
                                print("Error while deleting file : ", file_path)                        
                        print (f"Deleted {count} temporary test files.")

    def test_3_bld_from_kbd3(self):
        command_lines = [
            ("Finished!", "loaded 27 documents", fr"{self.pycmd} {self.data_file3} --nocheck --nohelp --verbose --rebuild --inputbuild=(bKBD3) --outputbuild=(bEXP_ARCH1)"),
            # bEXP_ARCH1 files deleted automatically after above command
        ]
        
        test_counter = 3
        for command_line_tuple in command_lines:
            #print (command_line)
            test_line = command_line_tuple[0]
            test_text = command_line_tuple[1]
            command_line = command_line_tuple[2]
            args = shlex.split(command_line, posix=False)
            print(f"Test {test_counter}. RUN: opasDataLoader {args[2:]}")
            p = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True) # Success!
            out, err = p.communicate()
            try:
                out_str = str(out, 'utf-8')
            except Exception as e:
                out_str = str(out)
            
            result = out_str.split('\r\n')
            
            for lin in result:
                if "Processing file" in lin or "Writing file" in lin or "Finished!" in lin or "Exporting!" or "Loaded" in lin:
                    print(lin)
           
                if test_line in lin:
                    assert test_text in lin, (test_text, lin)
                    print (f"Test {test_counter} passed.")
                    if "bEXP_ARCH1" in lin:
                        print (f"Deleting temporary test files: {self.delete_exp_arch1_files}")
                        file_list = glob.glob(str(f"{self.delete_exp_arch1_files}"))
                        count = 0
                        for file_path in file_list:
                            try:
                                os.remove(file_path)
                                count += 1
                            except:
                                print("Error while deleting file : ", file_path)                        
                        print (f"Deleted {count} temporary test files.")

    def test_4_bld_from_kbd3(self):
        command_lines = [
            # bEXP_ARCH1 files still in place
            ("references for links", "56 references", fr"{self.pycmd} {self.data_file1} --nocheck --nohelp --verbose --smartload --outputbuild=(bEXP_ARCH1)"),
        ]
        
        test_counter = 4
        for command_line_tuple in command_lines:
            #print (command_line)
            test_line = command_line_tuple[0]
            test_text = command_line_tuple[1]
            command_line = command_line_tuple[2]
            args = shlex.split(command_line, posix=False)
            print(f"Test {test_counter}. RUN: opasDataLoader {args[2:]}")
            p = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True) # Success!
            out, err = p.communicate()
            try:
                out_str = str(out, 'utf-8')
            except Exception as e:
                out_str = str(out)
            
            result = out_str.split('\r\n')
            
            for lin in result:
                if "Processing file" in lin or "Writing file" in lin or "Finished!" in lin or "Exporting!" or "Loaded" in lin:
                    print(lin)
           
                if test_line in lin:
                    assert test_text in lin, (test_text, lin)
                    print (f"Test {test_counter} passed.")
                    if "bEXP_ARCH1" in lin:
                        print (f"Deleting temporary test files: {self.delete_exp_arch1_files}")
                        file_list = glob.glob(str(f"{self.delete_exp_arch1_files}"))
                        count = 0
                        for file_path in file_list:
                            try:
                                os.remove(file_path)
                                count += 1
                            except:
                                print("Error while deleting file : ", file_path)                        
                        print (f"Deleted {count} temporary test files.")

    def test_5_bld_from_kbd3(self):
        command_lines = [
            #  note it always builds when there's only one file specified.
            ("Exporting!", "Writing precompiled XML file", fr"{self.pycmd} {self.data_file1} --nocheck --nohelp --verbose --smartload --outputbuild=(bEXP_ARCH1)"),
        ]
        
        test_counter = 5
        for command_line_tuple in command_lines:
            #print (command_line)
            test_line = command_line_tuple[0]
            test_text = command_line_tuple[1]
            command_line = command_line_tuple[2]
            args = shlex.split(command_line, posix=False)
            print(f"Test {test_counter}. RUN: opasDataLoader {args[2:]}")
            p = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True) # Success!
            out, err = p.communicate()
            try:
                out_str = str(out, 'utf-8')
            except Exception as e:
                out_str = str(out)
            
            result = out_str.split('\r\n')
            
            for lin in result:
                if "Processing file" in lin or "Writing file" in lin or "Finished!" in lin or "Exporting!" or "Loaded" in lin:
                    print(lin)
           
                if test_line in lin:
                    assert test_text in lin, (test_text, lin)
                    print (f"Test {test_counter} passed.")
                    if "bEXP_ARCH1" in lin:
                        print (f"Deleting temporary test files: {self.delete_exp_arch1_files}")
                        file_list = glob.glob(str(f"{self.delete_exp_arch1_files}"))
                        count = 0
                        for file_path in file_list:
                            try:
                                os.remove(file_path)
                                count += 1
                            except:
                                print("Error while deleting file : ", file_path)                        
                        print (f"Deleted {count} temporary test files.")

    def test_6_bld_from_kbd3(self):
        command_lines = [
            ("Processing file", "bEXP_ARCH1", fr"{self.pycmd} {self.data_file1} --nocheck --nohelp --load --verbose"),
        ]
        
        test_counter = 6
        for command_line_tuple in command_lines:
            #print (command_line)
            test_line = command_line_tuple[0]
            test_text = command_line_tuple[1]
            command_line = command_line_tuple[2]
            args = shlex.split(command_line, posix=False)
            print(f"Test {test_counter}. RUN: opasDataLoader {args[2:]}")
            p = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True) # Success!
            out, err = p.communicate()
            try:
                out_str = str(out, 'utf-8')
            except Exception as e:
                out_str = str(out)
            
            result = out_str.split('\r\n')
            
            for lin in result:
                if "Processing file" in lin or "Writing file" in lin or "Finished!" in lin or "Exporting!" or "Loaded" in lin:
                    print(lin)
           
                if test_line in lin:
                    assert test_text in lin, (test_text, lin)
                    print (f"Test {test_counter} passed.")
                    if "bEXP_ARCH1" in lin:
                        print (f"Deleting temporary test files: {self.delete_exp_arch1_files}")
                        file_list = glob.glob(str(f"{self.delete_exp_arch1_files}"))
                        count = 0
                        for file_path in file_list:
                            try:
                                os.remove(file_path)
                                count += 1
                            except:
                                print("Error while deleting file : ", file_path)                        
                        print (f"Deleted {count} temporary test files.")

    def test_7_bld_from_kbd3(self):
        command_lines = [
            # Already built, should not load any
            ("Finished!", "saved and loaded 0 documents (bEXP_ARCH1)", fr"{self.pycmd} {self.data_file3} --nocheck --nohelp --verbose --smartload"),
        ]
        
        test_counter = 7
        for command_line_tuple in command_lines:
            #print (command_line)
            test_line = command_line_tuple[0]
            test_text = command_line_tuple[1]
            command_line = command_line_tuple[2]
            args = shlex.split(command_line, posix=False)
            print(f"Test {test_counter}. RUN: opasDataLoader {args[2:]}")
            p = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True) # Success!
            out, err = p.communicate()
            try:
                out_str = str(out, 'utf-8')
            except Exception as e:
                out_str = str(out)
            
            result = out_str.split('\r\n')
            
            for lin in result:
                if "Processing file" in lin or "Writing file" in lin or "Finished!" in lin or "Exporting!" or "Loaded" in lin:
                    print(lin)
           
                if test_line in lin:
                    assert test_text in lin, (test_text, lin)
                    print (f"Test {test_counter} passed.")
                    if "bEXP_ARCH1" in lin:
                        print (f"Deleting temporary test files: {self.delete_exp_arch1_files}")
                        file_list = glob.glob(str(f"{self.delete_exp_arch1_files}"))
                        count = 0
                        for file_path in file_list:
                            try:
                                os.remove(file_path)
                                count += 1
                            except:
                                print("Error while deleting file : ", file_path)                        
                        print (f"Deleted {count} temporary test files.")

    def test_8_bld_from_kbd3(self):
        command_lines = [
            # Already built, should not load any
            ("Finished!", "saved and loaded 0 documents (bEXP_ARCH1)", fr"{self.pycmd} {self.data_file3} --nocheck --nohelp --verbose --smartload --inputbuild=(bKBD3) --outputbuild=(bEXP_ARCH1)"),
        ]
        
        test_counter = 8
        for command_line_tuple in command_lines:
            #print (command_line)
            test_line = command_line_tuple[0]
            test_text = command_line_tuple[1]
            command_line = command_line_tuple[2]
            args = shlex.split(command_line, posix=False)
            print(f"Test {test_counter}. RUN: opasDataLoader {args[2:]}")
            p = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True) # Success!
            out, err = p.communicate()
            try:
                out_str = str(out, 'utf-8')
            except Exception as e:
                out_str = str(out)
            
            result = out_str.split('\r\n')
            
            for lin in result:
                if "Processing file" in lin or "Writing file" in lin or "Finished!" in lin or "Exporting!" or "Loaded" in lin:
                    print(lin)
           
                if test_line in lin:
                    assert test_text in lin, (test_text, lin)
                    print (f"Test {test_counter} passed.")
                    if "bEXP_ARCH1" in lin:
                        print (f"Deleting temporary test files: {self.delete_exp_arch1_files}")
                        file_list = glob.glob(str(f"{self.delete_exp_arch1_files}"))
                        count = 0
                        for file_path in file_list:
                            try:
                                os.remove(file_path)
                                count += 1
                            except:
                                print("Error while deleting file : ", file_path)                        
                        print (f"Deleted {count} temporary test files.")

    def test_9_bld_from_kbd3(self):
        command_lines = [
            # Already built, should not load any
            ## bEXP_ARCH1 files still in place
            ("Finished!", "loaded 0 documents (bEXP_ARCH1)", fr"{self.pycmd} {self.data_file3} --nocheck --nohelp --verbose --smartload --outputbuild=(bEXP_ARCH1)"), # should not reprocess if not changed
        ]
        
        test_counter = 9
        for command_line_tuple in command_lines:
            #print (command_line)
            test_line = command_line_tuple[0]
            test_text = command_line_tuple[1]
            command_line = command_line_tuple[2]
            args = shlex.split(command_line, posix=False)
            print(f"Test {test_counter}. RUN: opasDataLoader {args[2:]}")
            p = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True) # Success!
            out, err = p.communicate()
            try:
                out_str = str(out, 'utf-8')
            except Exception as e:
                out_str = str(out)
            
            result = out_str.split('\r\n')
            
            for lin in result:
                if "Processing file" in lin or "Writing file" in lin or "Finished!" in lin or "Exporting!" or "Loaded" in lin:
                    print(lin)
           
                if test_line in lin:
                    assert test_text in lin, (test_text, lin)
                    print (f"Test {test_counter} passed.")
                    if "bEXP_ARCH1" in lin:
                        print (f"Deleting temporary test files: {self.delete_exp_arch1_files}")
                        file_list = glob.glob(str(f"{self.delete_exp_arch1_files}"))
                        count = 0
                        for file_path in file_list:
                            try:
                                os.remove(file_path)
                                count += 1
                            except:
                                print("Error while deleting file : ", file_path)                        
                        print (f"Deleted {count} temporary test files.")

    def test_10_bld_from_kbd3(self):
        command_lines = [
            ("Finished!", "loaded 27 documents", fr"{self.pycmd} {self.data_file3} --nocheck --nohelp --reload --verbose --inputbuild=(bEXP_ARCH1) --outputbuild=(bEXP_ARCH1)"), # force rebuild, implied bKBD3 input
        ]
        
        test_counter = 10
        for command_line_tuple in command_lines:
            #print (command_line)
            test_line = command_line_tuple[0]
            test_text = command_line_tuple[1]
            command_line = command_line_tuple[2]
            args = shlex.split(command_line, posix=False)
            print(f"Test {test_counter}. RUN: opasDataLoader {args[2:]}")
            p = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True) # Success!
            out, err = p.communicate()
            try:
                out_str = str(out, 'utf-8')
            except Exception as e:
                out_str = str(out)
            
            result = out_str.split('\r\n')
            
            for lin in result:
                if "Processing file" in lin or "Writing file" in lin or "Finished!" in lin or "Exporting!" or "Loaded" in lin:
                    print(lin)
           
                if test_line in lin:
                    assert test_text in lin, (test_text, lin)
                    print (f"Test {test_counter} passed.")
                    if "bEXP_ARCH1" in lin:
                        print (f"Deleting temporary test files: {self.delete_exp_arch1_files}")
                        file_list = glob.glob(str(f"{self.delete_exp_arch1_files}"))
                        count = 0
                        for file_path in file_list:
                            try:
                                os.remove(file_path)
                                count += 1
                            except:
                                print("Error while deleting file : ", file_path)                        
                        print (f"Deleted {count} temporary test files.")

if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")