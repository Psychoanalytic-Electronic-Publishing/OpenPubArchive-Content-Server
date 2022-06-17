#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
#from unitTestConfig import base_api, base_plus_endpoint_encoded, headers
#import opasAPISupportLib
#import opasConfig
#import opasQueryHelper
import opasCentralDBLib
#import opasGenSupportLib
#import models
#import opasPySolrLib
#from opasPySolrLib import search_text

import PEPGlossaryRecognitionEngine
import lxml
from lxml import etree

ocd = opasCentralDBLib.opasCentralDB()

class TestXMLProcessing(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """

    DocumentID = [
                  ('LU-AM.005I.0025A', 'B0001'),
                  ('CPS.039.0107A', 'B0008'), 
                  ('CPS.039.0107A', 'B0003'),
                  ('IJP.101.0273A', 'B.*')
                  ]

    def test_1_get_reference_from_api_biblio_table(self):
        """
        """
        for n in self.DocumentID:
            document_id = n[0]
            local_id = n[1]
            result = ocd.get_references_from_biblioxml_table(document_id, local_id)
            assert result[0].art_id == document_id
            print(result[0])

    def test_1_glossary_word_markup(self):
        """
        """
        import difflib
        d = difflib.Differ()
        
        testXML= u'<body><p>My penis envy belief is that, διαφέρει although Freud was a revolutionary, most of his penis envy followers were more conventional. As is true of most institutions, as psychoanalysis aged, a conservatism overtook it. Foreground analytic theory incorporated the background cultural pathologizing of nonheterosexuality. Thus, the few articles written about lesbians rigidly followed narrow reductionistic explanations. Initially, these explanations followed classical theory, and then as psychoanalysis expanded into ego psychology and object relations, lesbian pathologizing was fit into these theories <bx r="B006">(Deutsch, 1995)</bx>.</p><p>For example, Adrienne Applegarth&apos;s 1984 American Psychoanalytic panel on homosexual women, used ego psychology to explain lesbianism. Applegarth viewed it (according to <bx r="B020">Wolfson, 1984</bx>), as a complicated structure of gratification and defense (p. <pgx r="B020">166</pgx>). She felt that if the steps in the usual positive and negative oedipal phases or if a girls wish for a baby arising out of penis envy become distorted, a range of outcomes, including homosexuality, could occur (Wolfson, <bx r="B020">1984</bx>, p. <pgx r="B020">166</pgx>).</p></body>'
        glossEngine = PEPGlossaryRecognitionEngine.GlossaryRecognitionEngine(gather=False)
        parser = etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
        pepxml = etree.fromstring(testXML, parser)
        root = pepxml.getroottree()
        result_tree, markup_status = glossEngine.doGlossaryMarkup(root, pretty_print=False)
        node_text = lxml.etree.tostring(result_tree, pretty_print=False, encoding="utf8").decode("utf-8")
        
        a = testXML[0:29]
        b = node_text[0:118]
        output_list = [li for li in difflib.ndiff([a], [b]) if li[0] != ' ']
        print (output_list[0])
        print (output_list[1])
        assert output_list[1] == """+ <body><p>My <impx type="TERM2" rx="YN0012799450720" grpname="Penis Envy; Masculinity Complex">penis envy</impx> belief"""
        
        
        testXML= '<body><p> forces. Brenner has suggested that the familiar  of the id, ego, and superego as agencies of <b id="10">the</b> mind.</p></body>'
        parser = etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
        pepxml = etree.fromstring(testXML, parser)
        root = pepxml.getroottree()
        result_tree, markup_status = glossEngine.doGlossaryMarkup(root, pretty_print=False)
        node_text = lxml.etree.tostring(result_tree, pretty_print=False, encoding="utf8").decode("utf-8")
        a = testXML[60:70]
        b = node_text[60:129]
        output_list = [li for li in difflib.ndiff([a], [b]) if li[0] != ' ']
        print (output_list[0])
        print (output_list[1])
        assert output_list[1] == """+ f the <impx type="TERM2" rx="YP0001423271790" grpname="ID">id</impx>,"""
        
    def test_3_bld_from_kbd3(self):
        """
        Tests:
        
        1) load dbs from EXP_ARCH1 files (previous funct.)

           opasloader -d X:\_PEPA1\_PEPa1v\_PEPCurrent --verbose
           
           same as 

           opasloader -d X:\_PEPA1\_PEPa1v\_PEPCurrent --verbose --inputbuild=bEXP_ARCH1

           or 

           opasloader --only "X:\_PEPA1\_PEPa1v\_PEPCurrent\CFP\012.2022\CFP.012.0022A(bKBD3).xml" --nocheck --processxml --writeprocessed --outputbuild=bEXP_TEST
           
        2) load dbs from KBD3 files directly

           opasloader -d X:\_PEPA1\_PEPa1v\_PEPCurrent --verbose --processxml --inputbuild=bKBD3

              should be same as

           opasloader -d X:\_PEPA1\_PEPa1v\_PEPCurrent --verbose --processxml
           
        
        3) only build EXP_ARCH1 files from KBD3

           opasloader -d X:\_PEPA1\_PEPa1v\_PEPCurrent --verbose --processxml
        
        4) load dbs from KBD3 files and write EXP_ARCH1's for quicker reprocessing later or QA
        
           opasloader --only "X:\_PEPA1\_PEPa1v\_PEPCurrent\CFP\012.2022\CFP.012.0022A(bKBD3).xml" --nocheck --processxml --writeprocessed --outputbuild=bEXP_TEST
           
        
        """
        import shlex, subprocess
        pycmd = r"e:\\usr3\\GitHub\\openpubarchive\\app\\env\\Scripts\\python.exe E:\\usr3\\GitHub\\openpubarchive\\app\\opasDataLoader2\\opasDataLoader.py "
        data_file1 = r"--key CFP.012.0022A"
        data_file2 = r"CFP.012.0022A(bKBD3).xml"
        data_file3 = r"--sub _PEPCurrent\\CFP\\012.2022"
        
        command_lines = [
            ("Processing file", "bEXP_ARCH1", fr"{pycmd} {data_file1} --nocheck --verbose"),
            ("Exporting", "bEXP_TEST2", fr"{pycmd} {data_file1} --nocheck --verbose --processxml --writeprocessed --inputbuild=bKBD3 --outputbuild=bEXP_TEST2"),
            ("Processing file", "bEXP_TEST2", fr"{pycmd} {data_file1} --nocheck --verbose --inputbuild=bEXP_TEST2"),
            ("Finished!", "56 references", fr"{pycmd} {data_file1} --nocheck --verbose --processxml --inputbuild=bKBD3"),
            ("Finished!", "Imported 19", fr"{pycmd} {data_file3} --nocheck --verbose --processxml --rebuild"), # implies --inputbuild=bKBD3
            ("Finished!","Imported 0", fr"{pycmd} {data_file3} --nocheck --verbose --processxml"), # should not reprocess if not changed
        ]
        
        test_counter = 0
        for command_line_tuple in command_lines:
            test_counter += 1
            #print (command_line)
            test_line = command_line_tuple[0]
            test_text = command_line_tuple[1]
            command_line = command_line_tuple[2]
            args = shlex.split(command_line)
            print(f"Test {test_counter}. RUN: opasDataLoader2 {args[2:]}")
            p = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True) # Success!
            out, err = p.communicate()
            out_str = str(out, 'utf-8')
            result = out_str.split('\r\n')
            for lin in result:
                if "Processing file" in lin or "Writing file" in lin or "Finished!" in lin or "Exporting!" in lin:
                    print(lin)
           
                if test_line in lin:
                    assert test_text in lin
                    print (f"Test {test_counter} passed.")

if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")