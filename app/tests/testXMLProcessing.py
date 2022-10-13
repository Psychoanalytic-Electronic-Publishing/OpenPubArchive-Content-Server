#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import os
import unittest
import re
#from unitTestConfig import base_api, base_plus_endpoint_encoded, headers
#import opasAPISupportLib
#import opasConfig
#import opasQueryHelper
import opasCentralDBLib
#import opasGenSupportLib
#import models
#import opasPySolrLib
#from opasPySolrLib import search_text
import opasXMLHelper as opasxmllib

import PEPGlossaryRecognitionEngine
import lxml
from lxml import etree
from pathlib import Path

ocd = opasCentralDBLib.opasCentralDB()
test_data = """
<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE pepkbd3 SYSTEM "http://peparchive.org/pepa1dtd/pepkbd3.dtd">
<pepkbd3 lang="en">
<artinfo arttype="ART" j="PAQ" newsecnm="Original Articles" doi="10.1080/00332828.2019.1556036" ISSN="0033-2828">
    <artyear>2019</artyear>
    <artvol>88</artvol>
    <artiss>1</artiss>
    <artpgrg style="arabic">1-24</artpgrg>
    <arttitle>The Genesis of Interpretation Between Subjectivity and Objectivity: Theoretical-clinical Considerations</arttitle>
    <artauth hidden="false"><none/></artauth>
    <artkwds><impx type="KEYWORD">Interpretation</impx><impx type="KEYWORD">transformation</impx><impx type="KEYWORD">analyst’s subjectivity</impx><impx type="KEYWORD">objectivity</impx><impx type="KEYWORD">clinical fact</impx><impx type="KEYWORD">transference-countertransference</impx></artkwds>
</artinfo>
<abs>
    <p>The patient “employs” and “enlists” the analyst in his various transference forms, not so much by attributing a role to him, but by inducing subtle and deep changes in his person. What the patient makes us experience transforms our potential interpretation into words that arise from the emotional “turbulence” established between the patient and the analyst, prompted by the patient's suffering, made “real” by the analyst’s temporary suffering. Interpretation can become alive, meaningful, usable by the patient, only if the analyst allows that turbolence to temporarily become his own, not just to understand the patient, but to transform him through a partial transformation of the analyst himself. To realize this, we have to maintain an ongoing dialogue between our objectivity and our temperate and floating subjectivity.</p>
</abs>
<pb><n>1</n></pb>
<body>
    <h1>THE ANALYST’S MIND AND CLINICAL FACTS</h1>
    <p>We perceive (and organize) observations through the conscious, preconscious, and unconscious, not to mention the superego and the ego ideal that always lurk nearby and are ready to orient our thoughts and our feelings. That is, we use our psyche-soma, employing our normal splitting, repressing those facts that we believe would hamper our understanding of the patient. We use our own “private theories” about <pb><n>2</n></pb>ourselves and the world that surrounds us. We use our internal objects, the connections between them, our relationship with our body and our fantasies about it. We turn to our psychoanalytic theories.</p>
    <p>The image according to which the observations we collect strongly depend on the type of “net” we cast–with the unstated hope that these nets will also be modified by the nature of the observations collected, as well as by what we discover we are unable to catch—can be a useful image to try to start representing the complex relationship between clinical practice, theory, and technique presiding over the genesis of interpretation. From the collection of observations to the construction of facts, we strive to revise, update, and modify the latter, in a combinatory game of description and imagination (Gardner <bx type="bibr" r="B0029">1994</bx>). However, what assume clinical relevance among our observations? Selected on the basis of the perception of the exchanges between analyst and patient, of the object relations and emotional states that occur between them, some observations—and not others—will be given relevance by the analyst's personal modes of experiencing what happens in the session. This selection takes place according to the analyst’s capacities and limitations in seeing what happens in the session through theory and through his knowledge of the patient. In this context, observation and intuition are the elements that enable the emergence of a clinical fact; elements that have a theoretical background but do not derive directly from theory (Ahumada <bx type="bibr" r="B0001">1994</bx>).</p>
    <bib>
        <be id="B0001" reftype="journal" class="mixed-citation"><a class="western"><l>Ahumada</l>, J</a>. (<y>1994</y>). <t class="article-title">What is a clinical fact? Clinical psychoanalysis as inductive method</t>. <j> Int. J. of Psychoan</j>., <pp> 949 - 962</pp></be>
        <be id="B0015" reftype="book" class="mixed-citation"><a class="western"><l>Botella</l>, C.</a>, &amp; <a class="western"> <l>Botella</l>, S</a>. (<y>2001</y>). Propositions sur une notion de symetrie représentation-perception et ses vicissitudes dans la régression de la cure analytique. Paper given at Colloquio Italo-Francese, Bologna.</be>
        <be id="B0024" reftype="journal" class="mixed-citation"><a class="western"><l>Fliess</l>, R</a>. (<y>1942</y>). <t class="article-title">The metapsychology of the analyst</t>. <j> Psychoanal. Q</j>., pp. <pp> 211 - 227</pp></be>
        <be id="B0046" reftype="book" class="mixed-citation"><a class="western"><l>Heimann</l>, P</a>. (<y>1977</y>). <t class="chapter-title">Further observations on the analyst’s cognitive process</t>. In <bst> About Children and Children-No-Longer</bst>, cit., pp. <pp> 226 - 237</pp></be>
        <be id="B0056" reftype="book" class="mixed-citation"><a class="western"><l>Kohut</l>, H</a>. (<y>1984</y>). <t class="chapter-title">The role of empathy in psychoanalytic cure</t>. In <bst> How Does Analysis Cure</bst>? Chicago: <bp class="publisher-name"> The Univ. of Chicago Press</bp>, pp. <pp>172 - 191</pp></be>
        <be id="B0069" reftype="journal" class="mixed-citation"><a class="western"><l>Nissim Momigliano</l>, L</a>. (<y>1974</y>). <t class="article-title">Come si originano le interpretazioni nello psicoanalista</t>. <j> Riv. di Psicoanalisi</j>, <v> 20</v>: <pp>144 - 165</pp></be>
        <be id="B0071" reftype="journal" class="mixed-citation"><a class="western"><l>O’Shaughnessy</l>, E</a>. (<y>1994</y>). <t class="article-title">What is a clinical fact?</t> <j> Int. J. of Psychoanal</j>., <pp> 939 - 948</pp></be>
        <be id="B0074" reftype="journal" class="mixed-citation"><a class="western"><l>Ornstein</l>, P. H.</a>, &amp; <a class="western"> <l>Ornstein</l>, A</a>. (<y>1994</y>). <t class="article-title">On the conceptualisation of clinical facts in psychoanalysis</t>. <j> Int. J. of Psychoanal</j>., <pp> 977 - 994</pp></be>
        <be id="B0080" reftype="journal" class="mixed-citation"><a class="western"><l>Sandler</l>, J.</a>, &amp; <a class="western"> <l>Sandler</l>, A. M</a>. (<y>1994</y>). <t class="article-title">Comments on the conceptualisation of clinical facts in psychoanalysis</t>. <j> Int. J. of Psychoanal</j>., <pp> 995 - 1010</pp></be>
        
    </bib>
</body> 
</pepkbd3>
"""

class TestXMLProcessing(unittest.TestCase):
    """
    Tests
    
    Note: tests are performed in alphabetical order, hence the function naming
          with forced order in the names.
    
    """

    DocumentID = [
                  ('IJP.101.0273A', 'B.*'), 
                  ('LU-AM.005I.0025A', 'B0001'),
                  ('CPS.039.0107A', 'B0008'), 
                  ('CPS.039.0107A', 'B0003'),
                  ]

    def test_1_get_reference_from_api_biblio_table(self):
        """
        """
        for n in self.DocumentID:
            document_id = n[0]
            local_id = n[1]
            result = ocd.get_references_from_biblioxml_table(document_id, local_id)
            assert result[0].art_id == document_id
            print(result[0].art_id, result[0].bib_sourcetitle)

    def test_2_glossary_word_markup(self):
        """
        """
        # testXML= u'<body><p>My penis envy belief is that, διαφέρει although Freud was a revolutionary, most of his penis envy followers were more conventional. As is true of most institutions, as psychoanalysis aged, a conservatism overtook it. Foreground analytic theory incorporated the background cultural pathologizing of nonheterosexuality. Thus, the few articles written about lesbians rigidly followed narrow reductionistic explanations. Initially, these explanations followed classical theory, and then as psychoanalysis expanded into ego psychology and object relations, lesbian pathologizing was fit into these theories <bx r="B006">(Deutsch, 1995)</bx>.</p><p>For example, Adrienne Applegarth&apos;s 1984 American Psychoanalytic panel on homosexual women, used ego psychology to explain lesbianism. Applegarth viewed it (according to <bx r="B020">Wolfson, 1984</bx>), as a complicated structure of gratification and defense (p. <pgx r="B020">166</pgx>). She felt that if the steps in the usual positive and negative oedipal phases or if a girls wish for a baby arising out of penis envy become distorted, a range of outcomes, including homosexuality, could occur (Wolfson, <bx r="B020">1984</bx>, p. <pgx r="B020">166</pgx>).</p></body>'
        glossEngine = PEPGlossaryRecognitionEngine.GlossaryRecognitionEngine(gather=False)
        parser = etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
        pepxml = etree.fromstring(test_data, parser)
        root = pepxml.getroottree()
        p1a = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[0])
        p2a = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[1])
        result_tree, markup_status = glossEngine.doGlossaryMarkup(pepxml, pretty_print=False, diagnostics=True)
        p1b = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[0])
        p2b = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[1])
        print(p1a)
        print(p1b)
        print(p2a)
        print(p2b)
       
        assert re.search("<impx", p1b) is not None
        assert re.search("<impx", p2b) is not None
        
if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")