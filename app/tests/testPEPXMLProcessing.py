#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant
#2022.1129 # Added tests for turning of glossary tags and returning dictionary (as comment in end "unit")
import unittest
import re
import opasCentralDBLib
import opasXMLHelper as opasxmllib
import PEPGlossaryRecognitionEngine
import opasXMLProcessor
import opasArticleIDSupport
import opasCentralDBLib
import opasConfig
from lxml import etree

import logging
logger = logging.getLogger()

ocd = opasCentralDBLib.opasCentralDB()
test_data = f"""
<?xml version='1.0' encoding='UTF-8'?>
{opasConfig.PEP_KBD_DOCTYPE}
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

test_data2 = f"""
<?xml version='1.0' encoding='UTF-8'?>
{opasConfig.PEP_KBD_DOCTYPE}
<pepkbd3 lang="en">
<artinfo arttype="ART" j="ZBK" doi="10.7208/chicago/9780226450148.001.0001" id="ZBK.049.0001A">
        <artyear>1971</artyear>
        <artbkinfo>
            <bktitle>The analysis of the self</bktitle>
            <bkseriestitle>The Monograph Series of The Psychoanalytic Study of the Child Monograph
                No. 4</bkseriestitle>
            <bkpubandloc>International Universities Press, Inc., New York</bkpubandloc>
        </artbkinfo>
        <artvol>49</artvol>
        <artpgrg>1-343</artpgrg>
        <arttitle>The Analysis of the Self</arttitle>
        <artsub>A Systematic Approach to the Psychoanalytic Treatment of Narcissistic Personality
            Disorders</artsub>
        <artauth hidden="false">
            <aut authindexid="Kohut, Heinz" listed="true" role="author">
                <nfirst>Heinz</nfirst>
                <nlast>Kohut</nlast>
                <ndeg dgr="MD"/>
            </aut>
        </artauth>
    </artinfo>
<pb><n>1</n></pb>
<body>
    <p2>(2) loss-of-the-love-of-the-object, (3) loss-of-the-object experiences in the narcissistic disorders over (a) the guilt, (b) castration-anxiety experiences in the transference neuroses is not just a diagnostic psychological given that cannot be further explained but is a direct consequence of the essential fact that the self-objects which play the central role in the psychopathology of the narcissistic disorders are not equivalent to the objects in the transference neuroses. The objects in the narcissistic personality disturbances are archaic, narcissistically cathected, and prestructural (see <hdix r="H0006">Chapter 2</hdix>). Whether they threaten punishment, therefore, or withdrawal of love, or confront the patient with their temporary absence or permanent disappearance--the result is always a <i>narcissistic</i> imbalance or defect in the patient who had been interwoven with them in a variety of ways and whose maintenance of self cohesiveness and self-esteem, and of a reward-providing relationship to aim-channeling ideals, depended on their presence, their confirming approval,<ftnx r="F007">7</ftnx> or other modes of narcissistic sustenance. In the transference neuroses, however, the analogous psychological events lead to fear of punishment by an object which is cathected with object-instinctual energies (i.e., an object which is experienced as separate and independent), to tensions concerning the fact that one's love is not being responded to, to the possibility of a lonely longing for an absent object, and the like--with only a secondary drop in self-esteem.</p2>    <p>If there is a disturbance of those central functions which should enable the patient to experience the analytic reality, then neither educational measures (explanations) nor persuasion (moral pressure) should be employed, but the defect should be permitted to unfold freely so that its analysis can be undertaken. If, in other words, the patient's (preconscious) self was poorly cathected, then his difficulties with regard to the more or less spontaneous establishment of the analytic situation may themselves become the very center of the analytic work. But this important and central aspect of the patient's psychopathology would be removed from the focus of the analysis if the patient's inability to tolerate the decathexis of current reality and to accept the ambiguity of the analytic situation is seen within a moral framework and is responded to by persuasion and exhortation, or by an affirmation of reality or morality from the side of the analyst.</p><p>I now turn to the delimitation of the concepts of idealizing transference and mirror transference with their specifically appropriate working-through processes from the concepts of projective and introjective identification <bx r="B148">(Klein, 1946)</bx> and their therapeutic confrontation by the "English school" of psychoanalysis. The mirror transference may deal with an area which at least partly overlaps the area called "introjective</p>
    <p2>identification" by the Kleinian school, and similarly the idealizing transference may cover some of the territory of so-called "projective identification." The characteristic theoretical viewpoint which distinguishes the approach taken in the present work from that of the English school--it leads also to a vastly different therapeutic attitude--needs no summarizing presentation at this point. Suffice it to say that, according to the view presented here, the mirror transference and the idealizing transference are the therapeutically activated forms of the two basic positions of the narcissistic libido which establish themselves subsequent to the stage of primary narcissism. Since these positions constitute healthy and necessary maturational steps, even fixations on them or regressions to them must in therapy be first understood as in essence neither ill nor evil. The patient learns first to recognize these forms of narcissism in their therapeutic activation--and he must first be able to accept them as maturationally healthy and necessary!--before he can undertake the task of gradually transforming them and of building them into the higher organization of the adult personality and of harnessing them to his mature goals and purposes. The analysand's ego is thus not set up against his archaic narcissism as if it were an enemy and a stranger, no ideational processes belonging to higher stages of object differentiation (such as specific fantasies regarding a wish to devour a frustrating object or the fear of being devoured by it) are imputed to the therapeutically mobilized areas, and no guilt tensions are created. There exist, of course, tensions which arise spontaneously in the course of the analysis. They are due to the influx of unmodified narcissistic libido into the ego, and they are experienced as hypochondria, self-consciousness, and shame. (They do not arise from a conflict with an idealized superego, a structure which does not exist at the developmental level with which we are dealing in these instances.) If the analyst bases his attitude on the foregoing theoretic considerations, the difficult job of recognizing the flux of regression to and</p2>
</body> 
</pepkbd3>
"""

test_data3 = f"""
<?xml version="1.0" encoding="UTF-8" ?>
{opasConfig.PEP_KBD_DOCTYPE}
<pepkbd3 srcdate="2022-10-11" cvtby="aptara" cvtfrom="TF">
<artinfo arttype="ART" j="CPS" ISSN="0010-7530" doi="10.1080/00107530.2022.2110758">
<artyear>2022</artyear>
<artvol>58</artvol>
<artiss>1</artiss>
<artpgrg>138-139</artpgrg>
<arttitle>Dream Group</arttitle>
<artqual rx="CPS.058.0137A"/>
<artauth>
<aut><nfirst>Richard</nfirst> <nlast>Loewus</nlast> <ndeg dgr="PHD"/> <nbio>Faculty and Supervisor of Psychotherapy, William Alanson White Institute, and Faculty and Analytic Supervisor at the Institute for Contemporary Psychotherapy. He maintains a private practice in New York City.</nbio></aut>
<autaff>
<addr>
<ln type="email">E-mail: <url>rhloewus@gmail.com</url></ln>
</addr>
</autaff>
</artauth>
</artinfo>
<body>
<p>Paul’s enthusiasm for and joy in psychoanalysis was limitless. Nowhere was this more alive than in his engagement with dreams. He was the kid in the candy store, the scholar, the creative artist, the deeply curious guide and explorer. Dreams were a bridge to others’ individuality and to the human condition generally. Paul was humane, truthful, genuine, open, playful, kind. His enthusiasm and wonder were
<pb>
<ftr><p>Address correspondence to Richard Loewus, E-mail: <url>rhloewus@gmail.com</url></p></ftr>
<n>138</n></pb> contagious, and his example encouraged and nurtured these qualities in us. It was a privilege professionally, and a great personal joy to be a member of our group.</p>
<p>Richard Loewus, Ph.D., is Faculty and Supervisor of Psychotherapy, William Alanson White Institute, and Faculty and Analytic Supervisor at the Institute for Contemporary Psychotherapy. He maintains a private practice in New York City.</p>
<pb><n>139</n></pb>
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
                  ('LU-AM.005I.0025A', 'B001'),
                  ('CPS.039.0107A', 'B008'), 
                  ('CPS.039.0107A', 'B003'),
                  ]

    def test_1_get_reference_from_api_biblio_table(self):
        """
        """
        for n in self.DocumentID:
            document_id = n[0]
            local_id = n[1]
            result = ocd.get_references_from_biblioxml_table(document_id, local_id)
            assert result[0].art_id == document_id
            print(result[0].art_id, result[0].ref_sourcetitle)

    def test_2_glossary_word_markup(self):
        """
        """
        # testXML= u'<body><p>My penis envy belief is that, διαφέρει although Freud was a revolutionary, most of his penis envy followers were more conventional. As is true of most institutions, as psychoanalysis aged, a conservatism overtook it. Foreground analytic theory incorporated the background cultural pathologizing of nonheterosexuality. Thus, the few articles written about lesbians rigidly followed narrow reductionistic explanations. Initially, these explanations followed classical theory, and then as psychoanalysis expanded into ego psychology and object relations, lesbian pathologizing was fit into these theories <bx r="B006">(Deutsch, 1995)</bx>.</p><p>For example, Adrienne Applegarth's 1984 American Psychoanalytic panel on homosexual women, used ego psychology to explain lesbianism. Applegarth viewed it (according to <bx r="B020">Wolfson, 1984</bx>), as a complicated structure of gratification and defense (p. <pgx r="B020">166</pgx>). She felt that if the steps in the usual positive and negative oedipal phases or if a girls wish for a baby arising out of penis envy become distorted, a range of outcomes, including homosexuality, could occur (Wolfson, <bx r="B020">1984</bx>, p. <pgx r="B020">166</pgx>).</p></body>'
        glossEngine = PEPGlossaryRecognitionEngine.GlossaryRecognitionEngine(gather=False)
        parser = etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
        pepxml = etree.fromstring(test_data2, parser)
        root = pepxml.getroottree()
        p1a = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[0])
        p2a = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[1])
        total_count, marked_term_dict = glossEngine.doGlossaryMarkup(pepxml, pretty_print=False)
        p1b = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[0])
        p2b = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[1])
        print(p1a)
        print(p1b)
        print(p2a)
        print(p2b)
       
        assert re.search("<impx", p1b) is not None
        assert re.search("<impx", p2b) is not None
        
    def test_3_glossary_word_markup_on(self):
        """
        """
        # testXML= u'<body><p>My penis envy belief is that, διαφέρει although Freud was a revolutionary, most of his penis envy followers were more conventional. As is true of most institutions, as psychoanalysis aged, a conservatism overtook it. Foreground analytic theory incorporated the background cultural pathologizing of nonheterosexuality. Thus, the few articles written about lesbians rigidly followed narrow reductionistic explanations. Initially, these explanations followed classical theory, and then as psychoanalysis expanded into ego psychology and object relations, lesbian pathologizing was fit into these theories <bx r="B006">(Deutsch, 1995)</bx>.</p><p>For example, Adrienne Applegarth's 1984 American Psychoanalytic panel on homosexual women, used ego psychology to explain lesbianism. Applegarth viewed it (according to <bx r="B020">Wolfson, 1984</bx>), as a complicated structure of gratification and defense (p. <pgx r="B020">166</pgx>). She felt that if the steps in the usual positive and negative oedipal phases or if a girls wish for a baby arising out of penis envy become distorted, a range of outcomes, including homosexuality, could occur (Wolfson, <bx r="B020">1984</bx>, p. <pgx r="B020">166</pgx>).</p></body>'
        glossEngine = PEPGlossaryRecognitionEngine.GlossaryRecognitionEngine(gather=False)
        parser = etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
        pepxml = etree.fromstring(test_data, parser)
        root = pepxml.getroottree()
        p1a = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[0])
        p2a = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[1])
        total_count, marked_term_dict = glossEngine.doGlossaryMarkup(pepxml, pretty_print=False, markup_terms=True)
        p1b = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[0])
        p2b = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[1])
        print(p1a)
        print(p1b)
        print(p2a)
        print(p2b)
       
        assert re.search("<impx", p1b) is not None
        assert re.search("<impx", p2b) is not None

    def test_4_glossary_word_markup_off(self):
        """
        """
        # testXML= u'<body><p>My penis envy belief is that, διαφέρει although Freud was a revolutionary, most of his penis envy followers were more conventional. As is true of most institutions, as psychoanalysis aged, a conservatism overtook it. Foreground analytic theory incorporated the background cultural pathologizing of nonheterosexuality. Thus, the few articles written about lesbians rigidly followed narrow reductionistic explanations. Initially, these explanations followed classical theory, and then as psychoanalysis expanded into ego psychology and object relations, lesbian pathologizing was fit into these theories <bx r="B006">(Deutsch, 1995)</bx>.</p><p>For example, Adrienne Applegarth's 1984 American Psychoanalytic panel on homosexual women, used ego psychology to explain lesbianism. Applegarth viewed it (according to <bx r="B020">Wolfson, 1984</bx>), as a complicated structure of gratification and defense (p. <pgx r="B020">166</pgx>). She felt that if the steps in the usual positive and negative oedipal phases or if a girls wish for a baby arising out of penis envy become distorted, a range of outcomes, including homosexuality, could occur (Wolfson, <bx r="B020">1984</bx>, p. <pgx r="B020">166</pgx>).</p></body>'
        glossEngine = PEPGlossaryRecognitionEngine.GlossaryRecognitionEngine(gather=False)
        parser = etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
        pepxml = etree.fromstring(test_data2, parser)
        root = pepxml.getroottree()
        p1a = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[0])
        p2a = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[1])
        total_count, marked_term_dict = glossEngine.doGlossaryMarkup(pepxml, pretty_print=False, markup_terms=False)
        p1b = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[0])
        p2b = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[1])
        print(p1a)
        print(p1b)
        print(p2a)
        print(p2b)
       
        assert re.search("<impx", p1b) is None
        assert re.search("<impx", p2b) is None

    def test_5_glossary_word_markup_add_terms_off(self):
        """
        """
        ocd = opasCentralDBLib.opasCentralDB()
        # testXML= u'<body><p>My penis envy belief is that, διαφέρει although Freud was a revolutionary, most of his penis envy followers were more conventional. As is true of most institutions, as psychoanalysis aged, a conservatism overtook it. Foreground analytic theory incorporated the background cultural pathologizing of nonheterosexuality. Thus, the few articles written about lesbians rigidly followed narrow reductionistic explanations. Initially, these explanations followed classical theory, and then as psychoanalysis expanded into ego psychology and object relations, lesbian pathologizing was fit into these theories <bx r="B006">(Deutsch, 1995)</bx>.</p><p>For example, Adrienne Applegarth's 1984 American Psychoanalytic panel on homosexual women, used ego psychology to explain lesbianism. Applegarth viewed it (according to <bx r="B020">Wolfson, 1984</bx>), as a complicated structure of gratification and defense (p. <pgx r="B020">166</pgx>). She felt that if the steps in the usual positive and negative oedipal phases or if a girls wish for a baby arising out of penis envy become distorted, a range of outcomes, including homosexuality, could occur (Wolfson, <bx r="B020">1984</bx>, p. <pgx r="B020">166</pgx>).</p></body>'
        # glossEngine = PEPGlossaryRecognitionEngine.GlossaryRecognitionEngine(gather=False)
        parser = etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
        pepxml = etree.fromstring(test_data3, parser)
        #sourceDB = opasProductLib.SourceInfoDB()
        artInfo = opasArticleIDSupport.ArticleInfo(parsed_xml=pepxml, art_id="CPS.058.0138A", filename_base="CPS.058.0138A", logger=logger) # , art_id=artID, filename_base=base, 
        #root = pepxml.getroottree()
        p1a = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[0])
        p2a = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[1])
        total_count, term_dict = opasXMLProcessor.xml_update(pepxml,
                                                             artInfo,
                                                             ocd=ocd, 
                                                             add_glossary_list=False,
                                                             pretty_print=False,
                                                             markup_terms=False,
                                                             no_database_update=True)
        p1b = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[0])
        p2b = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[1])
        print(p1a)
        print(p1b)
        print(p2a)
        print(p2b)
       
        assert re.search("<impx", p1b) is None
        assert re.search("<impx", p2b) is None
        pepxmltxt = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml)
        assert pepxmltxt.find('<unit type="glossary_term_dict">') is -1

    def test_6_glossary_word_markup_add_terms_off_list_on(self):
        """
        """
        ocd = opasCentralDBLib.opasCentralDB()
        # testXML= u'<body><p>My penis envy belief is that, διαφέρει although Freud was a revolutionary, most of his penis envy followers were more conventional. As is true of most institutions, as psychoanalysis aged, a conservatism overtook it. Foreground analytic theory incorporated the background cultural pathologizing of nonheterosexuality. Thus, the few articles written about lesbians rigidly followed narrow reductionistic explanations. Initially, these explanations followed classical theory, and then as psychoanalysis expanded into ego psychology and object relations, lesbian pathologizing was fit into these theories <bx r="B006">(Deutsch, 1995)</bx>.</p><p>For example, Adrienne Applegarth's 1984 American Psychoanalytic panel on homosexual women, used ego psychology to explain lesbianism. Applegarth viewed it (according to <bx r="B020">Wolfson, 1984</bx>), as a complicated structure of gratification and defense (p. <pgx r="B020">166</pgx>). She felt that if the steps in the usual positive and negative oedipal phases or if a girls wish for a baby arising out of penis envy become distorted, a range of outcomes, including homosexuality, could occur (Wolfson, <bx r="B020">1984</bx>, p. <pgx r="B020">166</pgx>).</p></body>'
        # glossEngine = PEPGlossaryRecognitionEngine.GlossaryRecognitionEngine(gather=False)
        parser = etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
        pepxml = etree.fromstring(test_data3, parser)
        #sourceDB = opasProductLib.SourceInfoDB()
        artInfo = opasArticleIDSupport.ArticleInfo(parsed_xml=pepxml, art_id="CPS.058.0138A", filename_base="CPS.058.0138A", logger=logger) # , art_id=artID, filename_base=base, 
        #root = pepxml.getroottree()
        p1a = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[0])
        p2a = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[1])
        total_count, term_dict = opasXMLProcessor.xml_update(pepxml,
                                                             artInfo,
                                                             ocd=ocd, 
                                                             add_glossary_list=True,
                                                             pretty_print=False,
                                                             markup_terms=False,
                                                             no_database_update=True)
        p1b = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[0])
        p2b = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml.xpath("//body/p")[1])
        print(p1a)
        print(p1b)
        print(p2a)
        print(p2b)
       
        assert re.search("<impx", p1b) is None
        assert re.search("<impx", p2b) is None
        pepxmltxt = opasxmllib.xml_elem_or_str_to_xmlstring(pepxml)
        assert pepxmltxt.find('<unit type="glossary_term_dict">') is not -1

if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")