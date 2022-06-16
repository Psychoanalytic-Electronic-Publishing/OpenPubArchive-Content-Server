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
                  ('IJP.068.0213A', 'B.*')
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
        testXML= u'<body><p>My penis envy belief is that, διαφέρει although Freud was a revolutionary, most of his penis envy followers were more conventional. As is true of most institutions, as psychoanalysis aged, a conservatism overtook it. Foreground analytic theory incorporated the background cultural pathologizing of nonheterosexuality. Thus, the few articles written about lesbians rigidly followed narrow reductionistic explanations. Initially, these explanations followed classical theory, and then as psychoanalysis expanded into ego psychology and object relations, lesbian pathologizing was fit into these theories <bx r="B006">(Deutsch, 1995)</bx>.</p><p>For example, Adrienne Applegarth&apos;s 1984 American Psychoanalytic panel on homosexual women, used ego psychology to explain lesbianism. Applegarth viewed it (according to <bx r="B020">Wolfson, 1984</bx>), as a complicated structure of gratification and defense (p. <pgx r="B020">166</pgx>). She felt that if the steps in the usual positive and negative oedipal phases or if a girls wish for a baby arising out of penis envy become distorted, a range of outcomes, including homosexuality, could occur (Wolfson, <bx r="B020">1984</bx>, p. <pgx r="B020">166</pgx>).</p></body>'
        glossEngine = PEPGlossaryRecognitionEngine.GlossaryRecognitionEngine(gather=False)
        parser = etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
        pepxml = etree.fromstring(testXML, parser)
        root = pepxml.getroottree()
        result, result_text = glossEngine.doGlossaryMarkup(root)
        print (result_text)
        
        testXML= '<body><p> forces. Brenner has suggested that the familiar  of the id, ego, and superego as agencies of <b id="10">the</b> mind.</p></body>'
        parser = etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
        pepxml = etree.fromstring(testXML, parser)
        root = pepxml.getroottree()
        result, result_text = glossEngine.doGlossaryMarkup(root)
        print (result_text)
            
    def test_bld_from_kbd3(self):
        """
        """
        import shlex, subprocess
        command_line = ""
        /bin/vikings -input eggs.txt -output "spam spam.txt" -cmd "echo '$MONEY'"
        >>> args = shlex.split(command_line)
        >>> print(args)
        ['/bin/vikings', '-input', 'eggs.txt', '-output', 'spam spam.txt', '-cmd', "echo '$MONEY'"]
        >>> p = subprocess.Popen(args) # Success!

        # Start the unit tests
        result = os.spawnv(os.P_NOWAIT, gTextEditor, ("textEditor", self.logFileName))
        
        
            owlrec, owlmean = get_sightings(filename, 'Owl')
            assert owlrec == 2, 'Number of records for owl is wrong'
            assert owlmean == 17, 'Mean sightings for owl is wrong'
        parser = etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
        pepxml = etree.fromstring(testXML, parser)
        root = pepxml.getroottree()
        result, result_text = glossEngine.doGlossaryMarkup(root)
        print (result_text)
           
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")