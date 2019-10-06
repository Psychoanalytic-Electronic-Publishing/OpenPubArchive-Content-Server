#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
""" 
OPAS - XML Support Function Library
    
"""

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2019.0523.4"
__status__      = "Development"

import sys
import re
import os
import stdMessageLib
import logging
logger = logging.getLogger(__name__)

import lxml
from lxml import etree
import lxml.html as lhtml

from ebooklib import epub

pyVer = 2
if (sys.version_info > (3, 0)):
    # Python 3 code in this block
    from io import StringIO
    pyVer = 3
else:
    # Python 2 code in this block
    import StringIO

# -------------------------------------------------------------------------------------------------------

def author_derive_mast_from_xmlstr(authorXMLStr, listed=True):
    """
    Parses a string which has the PEP "aut" tag underneath a higher level tag, and returns the article Mast. for authors
    
    Listed can be True (listed authors), False (unlisted authors), or All (all authors)
    
    >>> author_derive_mast_from_xmlstr('<aut role="author" alias="false" listed="true" asis="false" lang="en"><nfirst>Dana</nfirst><nmid/><nlast>Birksted-Breen</nlast><nti/></aut>')
    ('Dana Birksted-Breen', ['Dana Birksted-Breen'])
    >>> author_derive_mast_from_xmlstr(r'<artauth hidden="false"><aut role="author" alias="false" listed="true" asis="false" authindexid="Kristeva, Julia"><nfirst type="FIRST">Julia</nfirst> <nlast>Kristeva</nlast> <nti>Professor</nti></aut><aut role="author" alias="false" listed="false" asis="false" authindexid="Vieira, Patricia"><nfirst type="FIRST">Patricia</nfirst> <nlast>Vieira</nlast> </aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Marder, Michael"><nfirst type="FIRST">Michael</nfirst> <nlast>Marder</nlast></aut></artauth>')
    ('Julia Kristeva &amp; Michael Marder', ['Julia Kristeva', 'Michael Marder'])
    >>> author_derive_mast_from_xmlstr(r'<artauth hidden="false"><aut role="author" alias="false" listed="true" asis="false" authindexid="Kristeva, Julia"><nfirst type="FIRST">Julia</nfirst> <nlast>Kristeva</nlast> <nti>Professor</nti></aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Vieira, Patricia"><nfirst type="FIRST">Patricia</nfirst> <nlast>Vieira</nlast> <nbio>A Lecturer at the University of Leeds and a Ph.D. candidate in the Department of Romance Languages and Literatures at Harvard University. Her dissertation is on political fiction and art in Latin America and Portugal. Her areas of specialization are Spanish and Lusophone literature, culture, art and film, as well as French and German cultural and literary theory.</nbio></aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Marder, Michael"><nfirst type="FIRST">Michael</nfirst> <nlast>Marder</nlast></aut></artauth>')
    ('Julia Kristeva, Patricia Vieira &amp; Michael Marder', ['Julia Kristeva', 'Patricia Vieira', 'Michael Marder'])
    >>> author_derive_mast_from_xmlstr(r'<artauth hidden="false"><aut role="author" alias="false" listed="true" asis="false" authindexid="Vieira, Patricia"><nfirst type="FIRST">Patricia</nfirst> <nlast>Vieira</nlast> <nbio>A Lecturer at the University of Leeds and a Ph.D. candidate in the Department of Romance Languages and Literatures at Harvard University. Her dissertation is on political fiction and art in Latin America and Portugal. Her areas of specialization are Spanish and Lusophone literature, culture, art and film, as well as French and German cultural and literary theory.</nbio></aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Marder, Michael"><nfirst type="FIRST">Michael</nfirst> <nlast>Marder</nlast></aut></artauth>')
    ('Patricia Vieira &amp; Michael Marder', ['Patricia Vieira', 'Michael Marder'])
    >>> author_derive_mast_from_xmlstr(r'<artauth hidden="false"><aut role="author" alias="false" listed="true" asis="false" authindexid="Boulanger, Ghislaine"><nfirst type="FIRST">Ghislaine</nfirst> <nlast>Boulanger</nlast></aut></artauth>')
    ('Ghislaine Boulanger', ['Ghislaine Boulanger'])
    """
    ret_val = ("", [])
    pepxml = etree.parse(StringIO(authorXMLStr))
    
    if authorXMLStr[0:4] == "<aut":
        rootFlag = "/"
    else:
        rootFlag = ""
    
    if listed == True:
        authorXMLList = pepxml.xpath(rootFlag + 'aut[@listed="true"]')
    elif listed == False:
        authorXMLList = pepxml.xpath(rootFlag + 'aut[@listed="false"]')
    elif listed == "All":
        authorXMLList = pepxml.xpath(rootFlag + 'aut')
    else:
        logger.error("authorDeriveMast: Bad value supplied for listed: %s" % listed)

    authorCount = len(authorXMLList)
    authorsMast = ""
    authorList = []
    currAuthorNumber = 0
    for n in authorXMLList:
        currAuthorNumber += 1
        authorFirstName = xml_xpath_return_textsingleton(n, "nfirst", "").strip()
        authorLastName = xml_xpath_return_textsingleton(n, "nlast", "").strip()
        authorMidName = xml_xpath_return_textsingleton(n, "nmid", "").strip()
        if authorMidName != "":
            authorName = " ".join([authorFirstName, authorMidName, authorLastName])
        else:
            authorName = " ".join([authorFirstName, authorLastName])
        
        if authorsMast == "":
            authorsMast = authorName
            authorList = [authorName]
        else:   
            authorList.append(authorName)
            if currAuthorNumber == authorCount:
                authorsMast += " &amp; " + authorName
            else:
                authorsMast += ", " + authorName
    
    ret_val = (authorsMast, authorList)

    return ret_val
    
def authors_citation_format_from_xmlstr(author_xmlstr, listed=True):
    """
    Parses a string which has the PEP "aut" tag underneath a higher level tag, and returns a citation format list of authors
    
    Listed can be True (listed authors), False (unlisted authors), or All (all authors)

    >>> authors_citation_format_from_xmlstr('<aut role="author" alias="false" listed="true" asis="false" lang="en"><nfirst>Dana</nfirst><nmid/><nlast>Birksted-Breen</nlast><nti/></aut>')
    ('Birksted-Breen, D.', ['Birksted-Breen, Dana'])
    >>> authors_citation_format_from_xmlstr(r'')
    ('', [])
    >>> authors_citation_format_from_xmlstr(r'<artauth><aut role="author" alias="false" listed="true"><nfirst type="FIRST">Julia</nfirst> <nlast>Kristeva</nlast></aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Vieira, Patricia"><nfirst type="FIRST">Patricia</nfirst> <nlast>Vieira</nlast></aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Marder, Michael"><nfirst type="FIRST">Michael</nfirst> <nlast>Marder</nlast></aut></artauth>', listed=True)
    ('Kristeva, J., Vieira, P. &amp; Marder, M.', ['Kristeva, Julia', 'Vieira, Patricia', 'Marder, Michael'])
    >>> authors_citation_format_from_xmlstr(r'<artauth hidden="false"><aut role="author" alias="false" listed="true" asis="false" authindexid="Vieira, Patricia"><nfirst type="FIRST">Patricia</nfirst> <nlast>Vieira</nlast></aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Marder, Michael"><nfirst type="FIRST">Michael</nfirst> <nlast>Marder</nlast></aut></artauth>')
    ('Vieira, P. &amp; Marder, M.', ['Vieira, Patricia', 'Marder, Michael'])
    >>> authors_citation_format_from_xmlstr(r'<artauth hidden="false"><aut role="author" alias="false" listed="true" asis="false" authindexid="Boulanger, Ghislaine"><nfirst type="FIRST">Ghislaine</nfirst> <nlast>Boulanger</nlast></aut></artauth>')
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
            authorXMLList = pepxml.xpath(rootFlag + 'aut[@listed="true"]')
        elif listed == False:
            authorXMLList = pepxml.xpath(rootFlag + 'aut[@listed="false"]')
        elif listed == "All":
            authorXMLList = pepxml.xpath(rootFlag + 'aut')
        else:
            logger.error("authorDeriveMast: Bad value supplied for listed: %s" % listed)


        authorCount = len(authorXMLList)
        authorList = []
        authorsBibStyle = ""
        currAuthorNumber = 0
        for n in authorXMLList:
            currAuthorNumber += 1
            authorFirstName = xml_xpath_return_textsingleton(n, "nfirst", "")
            authorFirstInitial = authorFirstName[0] if len(authorFirstName) > 0 else ""
            authorLastName = xml_xpath_return_textsingleton(n, "nlast", "")
            authorMidName = xml_xpath_return_textsingleton(n, "nmid", "")
            authorMidInitial = authorMidName[0] if len(authorMidName) > 0 else ""
            authorGivenNames  = ""
            if authorMidName != "":
                authorGivenNames = authorFirstName + " " + authorMidName
                authorGivenInits = authorFirstInitial + ". " + authorMidInitial + "."
            else:
                authorGivenNames = authorFirstName
                authorGivenInits = authorFirstInitial + "."
    
            if authorGivenNames != "":
                authorName = authorLastName + ", " + authorGivenNames
                authorNameInits = authorLastName + ", " + authorGivenInits
            else:
                authorName = authorLastName
                authorNameInits = ""
    
            authorList.append(authorName)
            if authorsBibStyle == "":
                authorsBibStyle = authorNameInits
            else:   
                if currAuthorNumber == authorCount:
                    authorsBibStyle += " &amp; " + authorNameInits
                else:
                    authorsBibStyle += ", " + authorNameInits

            ret_val = (authorsBibStyle, authorList)

    return ret_val

def get_html_citeas(authorsBibStyle, artYear, artTitle, artPepSourceTitleFull, artVol, artPgrg):
    ret_val = f"""<p class="citeas"><span class="authors">{authorsBibStyle}</span> (<span class="year">{artYear}</span>) <span class="title">{artTitle}</span>. <span class="sourcetitle">{artPepSourceTitleFull}</span> <span class="pgrg">{artVol}</span>:<span class="pgrg">{artPgrg}</span></p>"""
    return ret_val
    
def xml_remove_encoding_string(xmlString):
    # Get rid of the encoding for lxml
    p=re.compile("\<\?xml version=[\'\"]1.0[\'\"] encoding=[\'\"]UTF-8[\'\"]\?\>\n", re.IGNORECASE)
    ret_val = xmlString
    ret_val = p.sub("", ret_val)                
    
    return ret_val

def xml_get_subelement_textsingleton(element_node, subElementName, default_return=""):
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
        ret_val = element_node.find(subElementName).text
        ret_val = ret_val.strip()
    except Exception as err:
        ret_val = default_return

    return ret_val

def xml_get_subelement_xmlsingleton(element_node, subElementName, default_return=""):
    """
    Returns the marked up XML text for elements (including subelements)
    If it doesn't exist or is empty, return the default_return
    
    subElementName cannot be an xpath
    
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
        ret_val = etree.tostring(element_node.find(subElementName), with_tail=False, encoding="unicode")
        if ret_val == "":
            ret_val = default_return
    except Exception as err:
        ret_val = default_return

    return ret_val

#def xmlFragmentReturnTextOnly(xmlString, default_return=""):
    #"""
    #Return inner text of XML string element with sub tags stripped out
    
    #>>> xmlFragmentReturnTextOnly("<myxml>this <b>is <i>really</i></b> xml.</myxml>", None)
    #'this is really xml.'

    #"""
    #ret_val = default_return
    #root = etree.fromstring(xmlString)
    #etree.strip_tags(root, '*')
    #inner_text = root.text
    #if inner_text:
        #ret_val = inner_text.strip()
    #else:
        #ret_val = default_return
    
    #return ret_val

def xml_get_element_attr(element_node, attrName, default_return=""):
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
        ret_val = element_node.attrib[attrName]
        if ret_val == "":
            ret_val = default_return
    except Exception as err:
        ret_val = default_return

    return ret_val


def xml_get_elements(element_node, xpath_def, default_return=list()):
    """
    Return a list of XML ELEMENTS from the specified xPath

    Example:
    strList = xml_get_elements(treeRoot, "//p")
    
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
        print (err)

    return ret_val

def xml_get_direct_subnode_textsingleton(element_node, subelementName, default_return=""):
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
        ret_val = element_node.xpath('%s/node()' % subelementName)
        ret_val = ret_val[0]
    except ValueError as err: # try without node
        ret_val = element_node.xpath('%s' % subelementName)
        ret_val = ret_val[0]
    except IndexError as err:
        pass
        #ret_val = default_return  # empty
    except Exception as err:
        print ("getSingleSubnodeText Error: ", err)

    if ret_val == []:
        ret_val = default_return

    return ret_val

def xml_elem_or_str_to_xmlstring(elemOrXMLStr, default_return=""):
    """
    Return XML string 

    >>> root = etree.fromstring("<myxml>this <b>is <i>really</i></b> xml.</myxml>", None)  #mixed content element
    >>> xml_elem_or_str_to_xmlstring(root, None)
    '<myxml>this <b>is <i>really</i></b> xml.</myxml>'
    """
    ret_val = default_return
    # just in case the caller sent a string.
    try:
        if isinstance(elemOrXMLStr, lxml.etree._Element):
            ret_val = etree.tostring(elemOrXMLStr, encoding="unicode")        
        else:
            ret_val = elemOrXMLStr
    except Exception as err:
        print (err)
        ret_val = default_return
        
    return ret_val

def xml_string_to_text(xml_string, default_return=""):
    xml_string = xml_remove_encoding_string(xml_string)
    clearText = lhtml.fromstring(xml_string)
    ret_val = clearText.text_content()
    return ret_val
    
def xml_elem_or_str_to_text(elem_or_xmlstr, default_return=""):
    """
    Return string with all tags stripped out from either etree element or xml marked up string
    
    If string is empty or None, return the default_return

    >>> root = etree.fromstring(test_xml)
    >>> xml_elem_or_str_to_text(test_xml, None)[0:100]
    'this is just authoring test stuff\\n                A random paragraph\\n                Another random '
    >>> xml_elem_or_str_to_text(root, None)[0:100]
    'this is just authoring test stuff\\n                A random paragraph\\n                Another random '
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
            print (err)
            ret_val = default_return
            
        try:
            etree.strip_tags(elem, '*')
            inner_text = elem.text
            if inner_text:
                ret_val = inner_text.strip()
            else:
                ret_val = default_return
        except Exception as err:
            print ("xmlElemOrStrToText: %s" % err)
            ret_val = default_return

    if ret_val == "":
        ret_val = default_return
        
    return ret_val

def xml_xpath_return_textlist(element_node, xpath, default_return=list()):
    """
    Return text of element specified by xpath (with Node() as final part of path)
    
    >>> root = etree.fromstring(test_xml)
    >>> xml_xpath_return_textlist(root, "//p", None)
    ['A random paragraph', 'Another random paragraph', 'Another random paragraph', 'Another random paragraph', 'Another random paragraph with multiple subelements']
    >>> xml_xpath_return_textlist(root, "p", None)
    ['A random paragraph', 'Another random paragraph', 'Another random paragraph', 'Another random paragraph', 'Another random paragraph with multiple subelements']
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

def xml_xpath_return_xmlsingleton(element_node, xPathDef, default_return=""):
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
        ret_val = element_node.xpath(xPathDef)
        if isinstance(ret_val, list) and len(ret_val) > 0:
            ret_val = ret_val[0]
        ret_val = etree.tostring(ret_val, with_tail=False, encoding="unicode") 
                
    except Exception as err:
        print (err)

    return ret_val

def xml_xpath_return_xmlstringlist(element_node, xPathDef, default_return=list()):
    """
    Return a list of XML tagged strings from the nodes in the specified xPath

    Example:
    strList = elementsToStrings(treeRoot, "//aut[@listed='true']")

    >>> root = etree.fromstring(test_xml)
    >>> stringList = xml_xpath_return_xmlstringlist(root, "p")
    >>> len(stringList)
    5
    >>> stringList[0]
    '<p id="1">A random paragraph</p>'
    >>> xml_xpath_return_xmlstringlist(root, "pxxxx", None)  # check default return
    """
    ret_val = default_return
    try:
        ret_val = [etree.tostring(n, with_tail=False, encoding="unicode") for n in element_node.xpath(xPathDef)]
        if len(ret_val) == 0:
            ret_val = default_return
    except:
        ret_val = default_return
        
    return ret_val   

def add_headings_to_abstract_html(abstract, sourceTitle=None, pubYear=None, vol=None, issue=None, pgRg=None, title=None, authorMast=None, citeas=None):
    """
    Format the top portion of the Abstracts presented by the client per the original GVPi model
    """

    if issue is not None:
        issue = "({})".format(issue)
    else:
        issue = ""
        
    heading = f"({pubYear}). {sourceTitle}, {vol}{issue}:{pgRg}"
    ret_val = f"""
            <p class="heading">{heading}</p>
            <p class="title">{title}</p>
            <p class="title_author">{authorMast}</p>
            <div class="abstract">{abstract}</p>
            """
    return ret_val

def xml_string_to_html(xmlTextStr, xsltFile=r"./styles/pepkbd3-html.xslt"):
    ret_val = None
    try:
        if not os.path.exists(xsltFile):
            alt = "../styles/pepkbd3-html.xslt"
            if os.path.exists("./styles/pepkbd3-html.xslt"):
                xsltFile = alt
    except Exception as e:
        # return this error, so it will be displayed (for now) instead of the document
        ret_val = f"<p align='center'>Sorry, due to a transformation error, we cannot display this document right now.</p><p align='center'>Please report this to PEP.</p>  <p align='center'>Exception finding style sheet: {e}</p>"
        print (ret_val)

    try:
        if isinstance(xmlTextStr, list) and xmlTextStr != "[]":
            xmlTextStr = xmlTextStr[0]
    except Exception as e:
        logger.error("Problem extracting full-text: ", e)
        
    if xmlTextStr is not None and xmlTextStr != "[]":
        try:
            xmlTextStr = remove_encoding_string(xmlTextStr)
            sourceFile = etree.fromstring(xmlTextStr)
        except Exception as e:
            # return this error, so it will be displayed (for now) instead of the document
            ret_val = f"<p align='center'>Sorry, due to an XML error, we cannot display this document right now.</p><p align='center'>Please report this to PEP.</p>  <p align='center'>XSLT Transform Error: {e}</p>"
            logger.error(ret_val)
            print (ret_val)
        else:
            if xmlTextStr is not None and xmlTextStr != "[]":
                try:
                    xsltFile = etree.parse(xsltFile)
                    xsltTransformer = etree.XSLT(xsltFile)
                    transformedData = xsltTransformer(sourceFile)
                except Exception as e:
                    # return this error, so it will be displayed (for now) instead of the document
                    ret_val = f"<p align='center'>Sorry, due to a transformation error, we cannot display this document right now.</p><p align='center'>Please report this to PEP.</p>  <p align='center'>XSLT Transform Error: {e}</p>"
                    logger.error(ret_val)
                    print (ret_val)
                else:
                    ret_val = str(transformedData)
    return ret_val

def html_to_epub(htmlString, outputFilenameBase, artID, lang="en", htmlTitle=None, styleSheet="../styles/pep-html-preview.css"):
    """
    uses ebooklib
    
    """
    if htmlTitle is None:
        htmlTitle = artID
        
    root = etree.HTML(htmlString)
    try:
        title = root.xpath("//title/text()")
        title = title[0]
    except:
        title = artID
        
    headings = root.xpath("//*[self::h1|h2|h3]")

        
    basename = os.path.basename(outputFilenameBase)
    
    book = epub.EpubBook()
    book.set_identifier('basename')
    book.set_title(htmlTitle)
    book.set_language('en')
    
    book.add_author('PEP')    
    book.add_metadata('DC', 'description', 'This is description for my book')

    # main chapter
    c1 = epub.EpubHtml(title=title,
                       file_name= artID + '.xhtml',
                       lang=lang)

    c1.set_content(htmlString)
    
    # copyright page / chapter
    c2 = epub.EpubHtml(title='Copyright',
                       file_name='copyright.xhtml')
    c2.set_content(stdMessageLib.copyrightPageHTML)   
    
    book.add_item(c1)
    book.add_item(c2)    
    
    style = 'body { font-family: Times, Times New Roman, serif; }'
    try:
        styleFile = open(styleSheet, "r")
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
    filename = basename + '.epub'
    epub.write_epub(filename, book)
    return filename

def remove_encoding_string(xml_string):
    # Get rid of the encoding for lxml
    p=re.compile("\<\?xml version=\'1.0\' encoding=\'UTF-8\'\?\>\n")  # TODO - Move to module globals to optimize
    ret_val = xml_string
    ret_val = p.sub("", ret_val)                
    
    return ret_val



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
                <p id="1">A random paragraph</p>
                <p id="2" type="speech">Another random paragraph</p>
                <p id="3">Another <b>random</b> paragraph</p>
                <p id="4">Another random paragraph</p>
                <p id="5">Another <b>random</b> paragraph with multiple <b>subelements</b></p>
              </test>
              """
    doctest.testmod()
    print ("Tests Completed")


