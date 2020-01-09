#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
""" 
OPAS - XML Support Function Library
    
"""

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2019.0523.5"
__status__      = "Development"

import sys
import re
import os
import os.path
import stdMessageLib
import logging
logger = logging.getLogger(__name__)

import lxml
from lxml import etree
import lxml.html as lhtml

from ebooklib import epub
import opasConfig

pyVer = 2
if (sys.version_info > (3, 0)):
    # Python 3 code in this block
    from io import StringIO
    pyVer = 3
else:
    # Python 2 code in this block
    import StringIO

ENCODER_MATCHER = re.compile("\<\?xml\s+version=[\'\"]1.0[\'\"]\s+encoding=[\'\"](UTF-?8|ISO-?8859-?1?)[\'\"]\s*\?\>\n")  # TODO - Move to module globals to optimize


# -------------------------------------------------------------------------------------------------------

def author_mast_from_xmlstr(author_xmlstr, listed=True):
    """
    Parses a string which has the PEP "aut" tag underneath a higher level tag, and returns the article mast for authors
    
    Listed can be True (show only listed authors), False (include unlisted authors), or All (show all authors)
    
    >>> author_mast_from_xmlstr('<aut role="author" alias="false" listed="true" asis="false" lang="en"><nfirst>Dana</nfirst><nmid/><nlast>Birksted-Breen</nlast><nti/></aut>')
    ('Dana Birksted-Breen', ['Dana Birksted-Breen'])
    >>> author_mast_from_xmlstr(r'<artauth hidden="false"><aut role="author" alias="false" listed="true" asis="false" authindexid="Kristeva, Julia"><nfirst type="FIRST">Julia</nfirst> <nlast>Kristeva</nlast> <nti>Professor</nti></aut><aut role="author" alias="false" listed="false" asis="false" authindexid="Vieira, Patricia"><nfirst type="FIRST">Patricia</nfirst> <nlast>Vieira</nlast> </aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Marder, Michael"><nfirst type="FIRST">Michael</nfirst> <nlast>Marder</nlast></aut></artauth>')
    ('Julia Kristeva &amp; Michael Marder', ['Julia Kristeva', 'Michael Marder'])
    >>> author_mast_from_xmlstr(r'<artauth hidden="false"><aut role="author" alias="false" listed="true" asis="false" authindexid="Kristeva, Julia"><nfirst type="FIRST">Julia</nfirst> <nlast>Kristeva</nlast> <nti>Professor</nti></aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Vieira, Patricia"><nfirst type="FIRST">Patricia</nfirst> <nlast>Vieira</nlast> <nbio>A Lecturer at the University of Leeds and a Ph.D. candidate in the Department of Romance Languages and Literatures at Harvard University. Her dissertation is on political fiction and art in Latin America and Portugal. Her areas of specialization are Spanish and Lusophone literature, culture, art and film, as well as French and German cultural and literary theory.</nbio></aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Marder, Michael"><nfirst type="FIRST">Michael</nfirst> <nlast>Marder</nlast></aut></artauth>')
    ('Julia Kristeva, Patricia Vieira &amp; Michael Marder', ['Julia Kristeva', 'Patricia Vieira', 'Michael Marder'])
    >>> author_mast_from_xmlstr(r'<artauth hidden="false"><aut role="author" alias="false" listed="true" asis="false" authindexid="Vieira, Patricia"><nfirst type="FIRST">Patricia</nfirst> <nlast>Vieira</nlast> <nbio>A Lecturer at the University of Leeds and a Ph.D. candidate in the Department of Romance Languages and Literatures at Harvard University. Her dissertation is on political fiction and art in Latin America and Portugal. Her areas of specialization are Spanish and Lusophone literature, culture, art and film, as well as French and German cultural and literary theory.</nbio></aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Marder, Michael"><nfirst type="FIRST">Michael</nfirst> <nlast>Marder</nlast></aut></artauth>')
    ('Patricia Vieira &amp; Michael Marder', ['Patricia Vieira', 'Michael Marder'])
    >>> author_mast_from_xmlstr(r'<artauth hidden="false"><aut role="author" alias="false" listed="true" asis="false" authindexid="Boulanger, Ghislaine"><nfirst type="FIRST">Ghislaine</nfirst> <nlast>Boulanger</nlast></aut></artauth>')
    ('Ghislaine Boulanger', ['Ghislaine Boulanger'])
    """
    ret_val = ("", [])
    pepxml = etree.parse(StringIO(author_xmlstr))
    
    if author_xmlstr[0:4] == "<aut":
        rootFlag = "/"
    else:
        rootFlag = ""
    
    if listed == True:
        author_xml_list = pepxml.xpath(rootFlag + 'aut[@listed="true"]')
    elif listed == False:
        author_xml_list = pepxml.xpath(rootFlag + 'aut[@listed="false"]')
    elif listed == "All":
        author_xml_list = pepxml.xpath(rootFlag + 'aut')
    else:
        logger.error("authorDeriveMast: Bad value supplied for listed: %s" % listed)

    author_count = len(author_xml_list)
    authors_mast = ""
    author_list = []
    curr_author_number = 0
    for n in author_xml_list:
        curr_author_number += 1
        author_first_name = xml_xpath_return_textsingleton(n, "nfirst", "").strip()
        author_last_name = xml_xpath_return_textsingleton(n, "nlast", "").strip()
        author_mid_name = xml_xpath_return_textsingleton(n, "nmid", "").strip()
        if author_mid_name != "":
            author_name = " ".join([author_first_name, author_mid_name, author_last_name])
        else:
            author_name = " ".join([author_first_name, author_last_name])
        
        if authors_mast == "":
            authors_mast = author_name
            author_list = [author_name]
        else:   
            author_list.append(author_name)
            if curr_author_number == author_count:
                authors_mast += " &amp; " + author_name
            else:
                authors_mast += ", " + author_name
    
    ret_val = (authors_mast, author_list)

    return ret_val
    
def authors_citation_from_xmlstr(author_xmlstr, listed=True):
    """
    Parses a string which has the PEP "aut" tag underneath a higher level tag, and returns a citation format list of authors
    
    Listed can be True (listed authors), False (unlisted authors), or All (all authors)

    >>> authors_citation_from_xmlstr('<aut role="author" alias="false" listed="true" asis="false" lang="en"><nfirst>Dana</nfirst><nmid/><nlast>Birksted-Breen</nlast><nti/></aut>')
    ('Birksted-Breen, D.', ['Birksted-Breen, Dana'])
    >>> authors_citation_from_xmlstr(r'')
    ('', [])
    >>> authors_citation_from_xmlstr(r'<artauth><aut role="author" alias="false" listed="true"><nfirst type="FIRST">Julia</nfirst> <nlast>Kristeva</nlast></aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Vieira, Patricia"><nfirst type="FIRST">Patricia</nfirst> <nlast>Vieira</nlast></aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Marder, Michael"><nfirst type="FIRST">Michael</nfirst> <nlast>Marder</nlast></aut></artauth>', listed=True)
    ('Kristeva, J., Vieira, P. &amp; Marder, M.', ['Kristeva, Julia', 'Vieira, Patricia', 'Marder, Michael'])
    >>> authors_citation_from_xmlstr(r'<artauth hidden="false"><aut role="author" alias="false" listed="true" asis="false" authindexid="Vieira, Patricia"><nfirst type="FIRST">Patricia</nfirst> <nlast>Vieira</nlast></aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Marder, Michael"><nfirst type="FIRST">Michael</nfirst> <nlast>Marder</nlast></aut></artauth>')
    ('Vieira, P. &amp; Marder, M.', ['Vieira, Patricia', 'Marder, Michael'])
    >>> authors_citation_from_xmlstr(r'<artauth hidden="false"><aut role="author" alias="false" listed="true" asis="false" authindexid="Boulanger, Ghislaine"><nfirst type="FIRST">Ghislaine</nfirst> <nlast>Boulanger</nlast></aut></artauth>')
    ('Boulanger, G.', ['Boulanger, Ghislaine'])
    
    """
    ret_val = ("", [])
    if isinstance(author_xmlstr, lxml.etree._Element):
        author_xmlstr = etree.tostring(author_xmlstr, with_tail=False, encoding="unicode") 

    if author_xmlstr != "" and author_xmlstr is not None:
    
        if isinstance(author_xmlstr, list):
            author_xmlstr = author_xmlstr[0]
    
        if isinstance(author_xmlstr, bytes):
            author_xmlstr = author_xmlstr.decode("utf-8")
            
        pepxml = etree.parse(StringIO(author_xmlstr))
        if author_xmlstr[0:4] == "<aut":
            rootFlag = "/"
        else:
            rootFlag = ""

        if listed == True:
            author_xml_list = pepxml.xpath(rootFlag + 'aut[@listed="true"]')
        elif listed == False:
            author_xml_list = pepxml.xpath(rootFlag + 'aut[@listed="false"]')
        elif listed == "All":
            author_xml_list = pepxml.xpath(rootFlag + 'aut')
        else:
            logger.error("authorDeriveMast: Bad value supplied for listed: %s" % listed)


        author_count = len(author_xml_list)
        author_list = []
        authors_bib_style = ""
        curr_author_number = 0
        for n in author_xml_list:
            curr_author_number += 1
            author_first_name = xml_xpath_return_textsingleton(n, "nfirst", "")
            author_first_initial = author_first_name[0] if len(author_first_name) > 0 else ""
            author_last_name = xml_xpath_return_textsingleton(n, "nlast", "")
            author_mid_name = xml_xpath_return_textsingleton(n, "nmid", "")
            author_mid_initial = author_mid_name[0] if len(author_mid_name) > 0 else ""
            author_given_names  = ""
            if author_mid_name != "":
                author_given_names = author_first_name + " " + author_mid_name
                author_given_inits = author_first_initial + ". " + author_mid_initial + "."
            else:
                author_given_names = author_first_name
                author_given_inits = author_first_initial + "."
    
            if author_given_names != "":
                author_name = author_last_name + ", " + author_given_names
                author_name_inits = author_last_name + ", " + author_given_inits
            else:
                author_name = author_last_name
                author_name_inits = ""
    
            author_list.append(author_name)
            if authors_bib_style == "":
                authors_bib_style = author_name_inits
            else:   
                if curr_author_number == author_count:
                    authors_bib_style += " &amp; " + author_name_inits
                else:
                    authors_bib_style += ", " + author_name_inits

            ret_val = (authors_bib_style, author_list)

    return ret_val

def get_html_citeas(authors_bib_style, art_year, art_title, art_pep_sourcetitle_full, art_vol, art_pgrg):
    ret_val = f"""<p class="citeas"><span class="authors">{authors_bib_style}</span> (<span class="year">{art_year}</span>) <span class="title">{art_title}</span>. <span class="sourcetitle">{art_pep_sourcetitle_full}</span> <span class="pgrg">{art_vol}</span>:<span class="pgrg">{art_pgrg}</span></p>"""
    return ret_val

def xml_get_pages(xmlstr, offset=0, limit=1, inside="test", env="body", pagebrk="pb"):
    """
    Return the xml between the given page breaks (default <pb>).
    
    The pages are returned in the first entry of a tuple: an 'envelope', default <body></body> tag, an 'envelope' of sorts.
    The xml element list is returned as the second entry of the tuple
    if there's an error ("", []) is returned.

    If offset is not specified, it's 1 by default (first page)
    If limit is not specified, it's 1 by default
    So if neither is specified, it should return everything in 'inside' up to the first 'pagebrk'
    
    >>> ret_tuple = xml_get_pages(test_xml2, 0, 1, env="body")
    >>> ret_tuple[0]
    '<body>\\n<author role="writer">this is just authoring test stuff</author>\\n                \\n<p id="1">A random paragraph</p>\\n                \\n</body>\\n'
    
    >>> ret_tuple = xml_get_pages(test_xml2, 2, 1, env="grp")
    >>> ret_tuple[0]
    '<grp>\\n<p id="4">Another random paragraph</p>\\n                \\n<p id="5">Another <b>random</b> paragraph with multiple <b>subelements</b></p>\\n                \\n<pb/>\\n                \\n</grp>\\n'

    >>> ret_tuple = xml_get_pages(test_xml2, 1, 1, env="grp")
    >>> ret_tuple[0]
    '<grp>\\n<p id="2" type="speech">Another random paragraph</p>\\n                \\n<p id="3">Another <b>random</b> paragraph</p>\\n                \\n<grp>\\n                   <p>inside group</p>\\n                </grp>\\n                \\n<pb/>\\n                \\n</grp>\\n'

    """
    ret_val = ("", [])
    offset1 = offset
    offset2 = offset + limit

    try:
        xmlstr = xmlstr.replace("encoding=\'UTF-8\'", "")
        root = etree.parse(StringIO(xmlstr))
    except Exception as e:
        logging.error(f"Error parsing xmlstr: {e}")
    else:
        if offset1 == 0: # get all tags before offset2
            elem_list = root.xpath(f'/{inside}/{pagebrk}[{offset2}]/preceding-sibling::*')
        else: # get all content between offset1 and offset2
            elem_list = xml_get_elements_between_element(root, between_element=pagebrk, offset1=offset1, offset2=offset2)

        new_xml = f"<{env}>\n"
        for n in elem_list:
            try:
                new_xml += etree.tostring(n).decode("utf8") + "\n"
            except Exception as e:
                logging.warning(f"Error converting node: {e}")
        # close the new xml string
        new_xml += f"</{env}>\n"
        
        ret_val = (new_xml, elem_list)

    return ret_val

def xml_get_elements_between_element(element_node, between_element="pb", offset1=1, offset2=None):
    """
    Return the elements between the offset1 instance and offset2 instance of 'between_element'
    
    >>> root = etree.fromstring(test_xml2)
    >>> elist = xml_get_elements_between_element(root, between_element="pb", offset1=2, offset2=3)
    >>> etree.tostring(elist[0]).decode("utf8")
    '<p id="4">Another random paragraph</p>\\n                '
    
    >>> elist = xml_get_elements_between_element(root, between_element="pb", offset1=3, offset2=4)
    >>> etree.tostring(elist[0]).decode("utf8")
    '<p id="6">Another random paragraph</p>\\n                '
    
    >>> elist = xml_get_elements_between_element(root, between_element="pb", offset1=1, offset2=3)
    >>> etree.tostring(elist[-1]).decode("utf8")
    '<pb/>\\n                '
    
    """
    ret_val = []
    if offset1 is None:
        offset1 == 1

    if offset2 is None:
        offset2 = offset1 + 1

    path = f"//*/*[preceding-sibling::{between_element}[{offset1}] and not (preceding-sibling::{between_element}[{offset2}])]" 
    try:
        ret_val = element_node.xpath(path)
    except Exception as e:
        logging.error(f"Problem extracting xpath nodes: {xpath}")
    
    return ret_val
    
def xml_get_subelement_textsingleton(element_node, subelement_name, default_return=""):
    """
    Text for elements with only CDATA underneath
    
    >>> root = etree.fromstring(test_xml)
    >>> xml_get_subelement_textsingleton(root, "author")
    'this is just authoring test stuff'
    >>> root = etree.fromstring('<p>Another <b>random</b> paragraph with multiple <b>subelements</b></p>')
    >>> xml_get_subelement_textsingleton(root, "b")
    'random'
    >>> xml_get_subelement_textsingleton(root, "bxxx", None)
    """
    ret_val = default_return
    try:
        ret_val = element_node.find(subelement_name).text
        ret_val = ret_val.strip()
    except Exception as err:
        logger.warning(err)
        ret_val = default_return

    return ret_val

def xml_get_subelement_xmlsingleton(element_node, subelement_name, default_return=""):
    """
    Returns the marked up XML text for elements (including subelements)
    If it doesn't exist or is empty, return the default_return
    
    subelement_name cannot be an xpath
    
    >>> root = etree.fromstring(test_xml)
    >>> xml_get_subelement_xmlsingleton(root, "author", None)
    '<author role="writer">this is just authoring test stuff</author>'
    >>> root = etree.fromstring('<p>Another <b>random</b> paragraph with multiple <b>subelements</b></p>')
    >>> xml_get_subelement_xmlsingleton(root, "b")
    '<b>random</b>'
    >>> xml_get_subelement_xmlsingleton(root, "bxxxx", None)
    """
    ret_val = default_return
    try:
        ret_val = etree.tostring(element_node.find(subelement_name), with_tail=False, encoding="unicode")
        if ret_val == "":
            ret_val = default_return
    except Exception as err:
        logger.warning(err)
        ret_val = default_return

    return ret_val

def xml_fragment_text_only(xmlstr, default_return=""):
    """
    Return inner text of XML string element with sub tags stripped out
    
    >>> xml_fragment_text_only("<myxml>this <b>is <i>really</i></b> xml.</myxml>", None)
    'this is really xml.'

    """
    ret_val = default_return
    root = etree.fromstring(xmlstr)
    etree.strip_tags(root, '*')
    inner_text = root.text
    if inner_text:
        ret_val = inner_text.strip()
    else:
        ret_val = default_return
    
    return ret_val

def xml_get_element_attr(element_node, attr_name, default_return=""):
    """
    Get an attribute from the lxml element_node.  
    If it doesn't exist or is empty, return the default_return

    >>> root = etree.fromstring(test_xml)
    >>> curr_element = xml_get_elements(root, "p[@id=2]", None)
    >>> xml_get_element_attr(curr_element[0], "type")
    'speech'
    >>> xml_get_element_attr(curr_element[0], "typeaaa", None)
    """
    ret_val = default_return
    try:
        ret_val = element_node.attrib[attr_name]
        if ret_val == "":
            ret_val = default_return
    except Exception as err:
        logger.warning(err)
        ret_val = default_return

    return ret_val


def xml_get_elements(element_node, xpath_def, default_return=list()):
    """
    Return a list of XML ELEMENTS from the specified xPath

    Example:
    strList = xml_get_elements(treeRoot, "//p")
    
    >>> root = etree.fromstring(test_xml3)
    >>> xml_get_elements(root, "/*/p[count(preceding-sibling::pb)=1]", None)

    >>> root = etree.fromstring(test_xml)
    >>> len(xml_get_elements(root, "p[@id=2]", None))
    1
    >>> xml_get_elements(root, "//pxxxx", None)    # test default return
    
    """
    ret_val = default_return
    try:
        ret_val = element_node.xpath(xpath_def)
        if ret_val == []:
            ret_val = default_return
        
    except Exception as err:
        logger.error(err)

    return ret_val

def xml_get_direct_subnode_textsingleton(element_node, subelement_name, default_return=""):
    """
    Return the text for a direct subnode of the lxml elementTree element_node.
    Returns ONLY the first node found (Singleton).
    
    Important Note: Looks only at direct subnodes, not all decendents (for max speed)
    
    >>> root = etree.fromstring(test_xml)
    >>> xml_get_direct_subnode_textsingleton(root, "p", None)
    'A random paragraph'
    """
    ret_val = default_return

    try:
        ret_val = element_node.xpath('%s/node()' % subelement_name)
        ret_val = ret_val[0]
    except ValueError as err: # try without node
        ret_val = element_node.xpath('%s' % subelement_name)
        ret_val = ret_val[0]
    except IndexError as err:
        pass
        #ret_val = default_return  # empty
    except Exception as err:
        logger.error("getSingleSubnodeText Error: ", err)

    if ret_val == []:
        ret_val = default_return

    return ret_val

def xml_elem_or_str_to_xmlstring(elem_or_xmlstr, default_return=""):
    """
    Return XML string 

    >>> root = etree.fromstring("<myxml>this <b>is <i>really</i></b> xml.</myxml>", None)  #mixed content element
    >>> xml_elem_or_str_to_xmlstring(root, None)
    '<myxml>this <b>is <i>really</i></b> xml.</myxml>'
    """
    ret_val = default_return
    # just in case the caller sent a string.
    try:
        if isinstance(elem_or_xmlstr, lxml.etree._Element):
            ret_val = etree.tostring(elem_or_xmlstr, encoding="unicode")        
        else:
            ret_val = elem_or_xmlstr
    except Exception as err:
        logger.error(err)
        ret_val = default_return
        
    return ret_val

def xml_string_to_text(xmlstr, default_return=""):
    xmlstr = remove_encoding_string(xmlstr)
    clearText = lhtml.fromstring(xmlstr)
    ret_val = clearText.text_content()
    return ret_val
    
def xml_elem_or_str_to_text(elem_or_xmlstr, default_return=""):
    """
    Return string with all tags stripped out from either etree element or xml marked up string
    
    If string is empty or None, return the default_return

    >>> root = etree.fromstring(test_xml)
    >>> xml_elem_or_str_to_text(test_xml, None)[0:100]
    'this is just authoring test stuff\\n                whatever is in the abstract\\n                \\n     '
    >>> xml_elem_or_str_to_text(root, None)[0:100]
    'this is just authoring test stuff\\n                whatever is in the abstract\\n                \\n     '
    >>> root = etree.fromstring("<myxml>this <b>is <i>really</i><empty/></b> xml.</myxml>", None)  #mixed content element
    >>> xml_elem_or_str_to_text(root, None)
    'this is really xml.'
    >>> isinstance(xml_elem_or_str_to_text(root, None), str)  # make sure it's string
    True
    >>> xml_elem_or_str_to_text(xml_xpath_return_textsingleton(root, "pxxx", ""), None)
    """
    ret_val = default_return
    if elem_or_xmlstr is None or elem_or_xmlstr == "":
        ret_val = default_return
    elif isinstance(elem_or_xmlstr, lxml.etree._ElementUnicodeResult):
        ret_val = "%s" % elem_or_xmlstr # convert to string
    # just in case the caller sent a string.
    else:
        try:
            if isinstance(elem_or_xmlstr, str):
                parser = lxml.etree.XMLParser(encoding='utf-8', recover=True)                
                elem = etree.fromstring(elem_or_xmlstr, parser)
            else:
                elem = elem_or_xmlstr
        except Exception as err:
            logger.error(err)
            ret_val = default_return
            
        try:
            etree.strip_tags(elem, '*')
            inner_text = elem.text
            if inner_text:
                ret_val = inner_text.strip()
            else:
                ret_val = default_return
        except Exception as err:
            logger.error("xmlElemOrStrToText: ", err)
            ret_val = default_return

    if ret_val == "":
        ret_val = default_return
        
    return ret_val

def xml_xpath_return_textlist(element_node, xpath, default_return=list()):
    """
    Return text of element specified by xpath (with Node() as final part of path)
    
    >>> root = etree.fromstring(test_xml)
    >>> xml_xpath_return_textlist(root, "//p", None)
    ['A random paragraph', 'Another random paragraph', 'Another random paragraph', 'Another random paragraph', 'Another random paragraph with multiple subelements', 'Another random paragraph', 'Another random paragraph', 'Another random paragraph with multiple subelements']
    >>> xml_xpath_return_textlist(root, "p", None)
    ['A random paragraph', 'Another random paragraph', 'Another random paragraph', 'Another random paragraph', 'Another random paragraph with multiple subelements', 'Another random paragraph', 'Another random paragraph', 'Another random paragraph with multiple subelements']
    >>> xml_xpath_return_textlist(root, "pxxx", None) # check default return
    """
    ret_val = default_return
    try:
        ret_val = element_node.xpath(xpath)
        ret_val = [xml_elem_or_str_to_text(n) for n in ret_val]
        if ret_val == []:
            ret_val = default_return
    except IndexError:
        ret_val = default_return
    
    return ret_val    

def xml_xpath_return_textsingleton(element_node, xpath, default_return=""):
    """
    Return text of element specified by xpath)
    
    >>> root = etree.fromstring(test_xml)
    >>> xml_xpath_return_textsingleton(root, "p[@id=2]/node()", None)
    'Another random paragraph'
    >>> xml_xpath_return_textsingleton(root, "p[@id=2]", None)
    'Another random paragraph'
    >>> xml_xpath_return_textsingleton(root, "p", None)
    'A random paragraph'
    >>> xml_xpath_return_textsingleton(root, "pxxxx", None) # check default return
    """
    ret_val = default_return
    try:
        ret_val = element_node.xpath(xpath)[0]
    except IndexError:
        ret_val = default_return
    
    if type(ret_val) == type(element_node):  # if it comes back an element
        ret_val = xml_elem_or_str_to_text(ret_val)    
        
    return ret_val    

def xml_xpath_return_xmlsingleton(element_node, xpath, default_return=""):
    """
    Return a singleton XML ELEMENT from the specified xPath

    Example:
    strList = xml_xpath_return_xmlsingleton(treeRoot, "//artauth")
    
    >>> root = etree.fromstring(test_xml)
    >>> xml_xpath_return_xmlsingleton(root, "p[@id=2]", None)
    '<p id="2" type="speech">Another random paragraph</p>'
    """
    ret_val = default_return
    try:
        ret_val = element_node.xpath(xpath)
        if isinstance(ret_val, list) and len(ret_val) > 0:
            ret_val = ret_val[0]
        ret_val = etree.tostring(ret_val, with_tail=False, encoding="unicode") 
                
    except Exception as err:
        logger.error(err)

    return ret_val

def xml_xpath_return_xmlstringlist(element_node, xpath, default_return=list()):
    """
    Return a list of XML tagged strings from the nodes in the specified xPath

    Example:
    strList = elementsToStrings(treeRoot, "//aut[@listed='true']")

    >>> root = etree.fromstring(test_xml)
    >>> stringList = xml_xpath_return_xmlstringlist(root, "p")
    >>> len(stringList)
    8
    >>> stringList[0]
    '<p id="1">A random paragraph</p>'
    >>> xml_xpath_return_xmlstringlist(root, "pxxxx", None)  # check default return
    """
    ret_val = default_return
    try:
        ret_val = [etree.tostring(n, with_tail=False, encoding="unicode") for n in element_node.xpath(xpath)]
        if len(ret_val) == 0:
            ret_val = default_return
    except:
        ret_val = default_return
        
    return ret_val

def get_running_head(source_title=None, pub_year=None, vol=None, issue=None, pgrg=None, ret_format="HTML"):
    """
    Return the short running head at the top of articles and Abstracts
    """
    if issue is not None:
        issue = "({})".format(issue)
    else:
        issue = ""
        
    ret_val = f"({pub_year}). {source_title}, {vol}{issue}:{pgrg}"
    return ret_val
    

def add_headings_to_abstract_html(abstract, source_title=None, pub_year=None, vol=None, issue=None, pgrg=None, title=None, author_mast=None, citeas=None, ret_format="HTML"):
    """
    Format the top portion of the Abstracts presented by the client per the original GVPi model
    """

    heading = get_running_head(source_title=source_title, pub_year=pub_year, vol=vol, issue=issue, pgrg=pgrg, ret_format="HTML")
        
    if ret_format != "TEXTONLY":
        # BOTH HTML and XML.  May later want to handle XML separately
        ret_val = f"""
                <p class="heading">{heading}</p>
                <p class="title">{title}</p>
                <p class="title_author">{author_mast}</p>
                <div class="abstract">{abstract}</p>
                """
    else:
        ret_val = f"""
                {heading}\n{title}\n{author_mast}\n\n
                {abstract}
                """
        
        
    return ret_val

def xml_file_to_xmlstr(xml_file, remove_encoding=False, resolve_entities=True):
    """
    Read XML file and convert it to an XML string, expanding all entities
    
    Optionally remove the lead-in encoding string (since some functions trip on that!)
    
    """
    parser = etree.XMLParser(load_dtd=True, resolve_entities=resolve_entities)
    try:
        doc_DOM = etree.parse(xml_file, parser=parser)
    except Exception as e:
        logger.error(f"Error reading XML file {xml_file}", e)
        ret_val = ""
    else:
        ret_val = etree.tostring(doc_DOM)
        ret_val = ret_val.decode("utf8")
        ret_val += "\n"
        
    if remove_encoding:
        ret_val = remove_encoding(ret_val)
    
    return ret_val

def xml_str_to_html(xml_text, xslt_file=opasConfig.XSLT_XMLTOHTML):
    """
    Convert XML to HTML per XSLT file parameter configured in opasConfig.
    
    >>> len(xml_str_to_html(xml_text=test_xml3))
    314
    """
    ret_val = None
    try:
        if not os.path.exists(xslt_file):
            # see if we're too low in the tree (e.g., we're already in libs)
            alt = opasConfig.XSLT_XMLTOHTML_ALT  # e.g., r"../styles/pepkbd3-html.xslt"
            if os.path.exists(alt):
                xslt_file = alt
            else:
                raise FileNotFoundError("XSLT file missing") 
    except Exception as e:
        # return this error, so it will be displayed (for now) instead of the document
        ret_val = f"<p align='center'>Sorry, due to a configuration error (xslt missing), we cannot display this document right now.</p><p align='center'>Please report this to PEP.</p>  <p align='center'>Exception finding style sheet: {e}</p>"
        logger.error(ret_val)

    try:
        if isinstance(xml_text, list) and xml_text != "[]":
            xml_text = xml_text[0]
    except Exception as e:
        logger.error("Problem extracting full-text: ", e)
        
    if xml_text is not None and xml_text != "[]":
        try:
            xml_text = remove_encoding_string(xml_text)
            sourceFile = etree.fromstring(xml_text)
        except Exception as e:
            # return this error, so it will be displayed (for now) instead of the document
            ret_val = f"<p align='center'>Sorry, due to an XML error, we cannot display this document right now.</p><p align='center'>Please report this to PEP.</p>  <p align='center'>XSLT Transform Error: {e}</p>"
            logger.error(ret_val)
        else:
            if xml_text is not None and xml_text != "[]":
                try:
                    xslt_file = etree.parse(xslt_file)
                    xslt_transformer = etree.XSLT(xslt_file)
                    transformed_data = xslt_transformer(sourceFile)
                except Exception as e:
                    # return this error, so it will be displayed (for now) instead of the document
                    ret_val = f"<p align='center'>Sorry, due to a transformation error, we cannot display this document right now.</p><p align='center'>Please report this to PEP.</p>  <p align='center'>XSLT Transform Error: {e}</p>"
                    logger.error(ret_val)
                    ret_val = xml_text
                else:
                    ret_val = str(transformed_data)
    return ret_val

def html_to_epub(htmlstr, output_filename_base, art_id, lang="en", html_title=None, stylesheet=opasConfig.CSS_STYLESHEET): #  e.g., "./libs/styles/pep-html-preview.css"
    """
    uses ebooklib
    
    >>> htmlstr = xml_str_to_html(test_xml3)
    >>> document_id = "epubconversiontest"
    >>> filename = html_to_epub(htmlstr, output_filename_base=document_id, art_id=document_id)
    
    """
    if html_title is None:
        html_title = art_id
        
    root = etree.HTML(htmlstr)
    try:
        title = root.xpath("//title/text()")
        title = title[0]
    except:
        title = art_id
        
    headings = root.xpath("//*[self::h1|h2|h3]")

        
    basename = os.path.basename(output_filename_base)
    
    book = epub.EpubBook()
    book.set_identifier(basename)
    book.set_title(html_title)
    book.set_language('en')
    
    book.add_author('PEP')    
    book.add_metadata('DC', 'description', 'This is description for my book')

    # main chapter
    c1 = epub.EpubHtml(title=title,
                       file_name= art_id + '.xhtml',
                       lang=lang)

    c1.set_content(htmlstr)
    
    # copyright page / chapter
    c2 = epub.EpubHtml(title='Copyright',
                       file_name='copyright.xhtml')
    c2.set_content(stdMessageLib.COPYRIGHT_PAGE_HTML)   
    
    book.add_item(c1)
    book.add_item(c2)    
    
    style = 'body { font-family: Times, Times New Roman, serif; }'
    try:
        styleFile = open(stylesheet, "r")
        style = styleFile.read()
        styleFile.close()
        
    except OSError as e:
        logger.warning("Cannot open stylesheet %s" % e)
    
    
    nav_css = epub.EpubItem(uid="style_nav",
                            file_name="style/pepkbd3-html.css",
                            media_type="text/css",
                            content=style)
    book.add_item(nav_css)    
    
    book.toc = (epub.Link(title, 'Introduction', 'intro'),
                (
                    epub.Section(title),
                    (c1, c2)
                )
                )    

    book.spine = ['nav', c1, c2]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())    
    filename = os.path.join(opasConfig.TEMPDIRECTORY, basename + '.epub')
    epub.write_epub(filename, book)
    return filename

def remove_encoding_string(xmlstr):
    # Get rid of the encoding for lxml
    ret_val = ENCODER_MATCHER.sub("", xmlstr)                
    return ret_val

#def remove_encoding_string(xmlstr):
    #"""
    #Remove the encoding string, as required by lxml in some functions
    
    #>>> remove_encoding_string('<?xml version="1.0" encoding="ISO-8859-1" ?>\n<!DOCTYPE pepkbd3></>')
    
    #"""
    #p=re.compile("\<\?xml\s+version=[\'\"]1.0[\'\"]\s+encoding=[\'\"](UTF-?8|ISO-?8859-?1?)[\'\"]\s*\?\>\n")  # TODO - Move to module globals to optimize
    #ret_val = xmlstr
    #ret_val = p.sub("", ret_val)                
    
    #return ret_val



# -------------------------------------------------------------------------------------------------------
# run it! (for testing)
# 
# nrs note - Trying main at the top, for function refactors (wing moves to the bottom of the file.

if __name__ == "__main__":
    print ("Running in Python %s" % sys.version_info[0])
    import doctest

    test_xml = """
              <test>
                <author role="writer">this is just authoring test stuff</author>
                <abstract>whatever is in the abstract</abstract>
                <pb></pb>
                <p id="1">A random paragraph</p>
                <p id="2" type="speech">Another random paragraph</p>
                <pb></pb>
                <p id="3">Another <b>random</b> paragraph</p>
                <p id="4">Another random paragraph</p>
                <p id="5">Another <b>random</b> paragraph with multiple <b>subelements</b></p>
                <pb></pb>
                <p id="3">Another <b>random</b> paragraph</p>
                <p id="4">Another random paragraph</p>
                <p id="5">Another <b>random</b> paragraph with multiple <b>subelements</b></p>
                <pb></pb>
              </test>
              """

    test_xml2 = """
              <test>
                <author role="writer">this is just authoring test stuff</author>
                <p id="1">A random paragraph</p>
                <pb></pb>
                <p id="2" type="speech">Another random paragraph</p>
                <p id="3">Another <b>random</b> paragraph</p>
                <grp>
                   <p>inside group</p>
                </grp>
                <pb></pb>
                <p id="4">Another random paragraph</p>
                <p id="5">Another <b>random</b> paragraph with multiple <b>subelements</b></p>
                <pb></pb>
                <p id="6">Another random paragraph</p>
                <pb></pb>
                <quote>blah blah</quote>
                <p id="7">Another <b>random</b> paragraph with multiple <b>subelements</b></p>
                <pb></pb>
                <p id="8">Another random paragraph</p>
                <quote>blah blah</quote>
                <p id="9">Another <b>random</b> paragraph with multiple <b>subelements</b></p>
                <p id="10">Another <b>random</b> paragraph with multiple <b>subelements</b></p>
              </test>
              """

    test_xml3 = xml_file_to_xmlstr("./tstfiles/IJP.051.0175A(bEXP_ARCH1).XML")
    
    doctest.testmod()
    print ("All Tests Completed")


