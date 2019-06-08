#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
""" 
OPAS - XML Support Function Library
    
"""

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "0.1.23"
__status__      = "Development"

import lxml
from lxml import etree

def xmlElementsToStrings(elementNode, xPathDef):
    """
    Return a list of XML tagged strings from the nodes in the specified xPath

    Example:
    strList = elementsToStrings(treeRoot, "//aut[@listed='true']")

    >>> root = etree.fromstring(testXML)
    >>> len(xmlElementsToStrings(root, "p"))
    4

    """
    retVal = [etree.tostring(n, with_tail=False) for n in elementNode.xpath(xPathDef)]
    return retVal

def xmlFindSubElementText(elementNode, subElementName, defaultReturn=""):
    """
    Text for elements with only CDATA underneath
    
    >>> root = etree.fromstring(testXML)
    >>> xmlFindSubElementText(root, "author")
    'this is just authoring test stuff'
    """
    retVal = defaultReturn
    try:
        retVal = elementNode.find(subElementName).text
        retVal = retVal.strip()
    except Exception, err:
        retVal = defaultReturn

    return retVal

def xmlFindSubElementXML(elementNode, subElementName, defaultReturn=""):
    """
    Returns the marked up XML text for elements (including subelements)
    
    subElementName cannot be an xpath
    
    >>> root = etree.fromstring(testXML)
    >>> xmlFindSubElementXML(root, "author", None)
    '<author role="writer">this is just authoring test stuff</author>'
    
    """
    retVal = defaultReturn
    try:
        retVal = etree.tostring(elementNode.find(subElementName), with_tail=False)
    except Exception, err:
        retVal = defaultReturn

    return retVal

def xmlFragmentReturnTextOnly(xmlString, defaultReturn=""):
    """
    Return inner text of XML string element with sub tags stripped out
    
    >>> xmlFragmentReturnTextOnly("<myxml>this <b>is <i>really</i></b> xml.</myxml>", None)
    'this is really xml.'

    """
    retVal = defaultReturn
    root = etree.fromstring(xmlString)
    etree.strip_tags(root, '*')
    inner_text = root.text
    if inner_text:
        retVal = inner_text.strip()
    else:
        retVal = defaultReturn
    
    return retVal

def xmlGetElementAttr(elementNode, attrName, defaultReturn=""):
    """
    Get an attribute from the lxml elementNode

    >>> root = etree.fromstring(testXML)
    >>> currElement = xmlGetElements(root, "p[@id=2]", None)
    >>> xmlGetElementAttr(currElement[0], "type")
    'speech'
    
    """
    retVal = defaultReturn
    try:
        retVal = elementNode.attrib[attrName]
        if retVal == "":
            retVal = defaultReturn
    except Exception, err:
        retVal = defaultReturn

    return retVal

def xmlGetElements(elementNode, xPathDef, defaultReturn=[]):
    """
    Return a list of XML ELEMENTS from the specified xPath

    Example:
    strList = xmlGetElements(treeRoot, "//p")
    
    >>> root = etree.fromstring(testXML)
    >>> len(xmlGetElements(root, "p[@id=2]", None))
    1
    """
    retVal = defaultReturn
    try:
        retVal = elementNode.xpath(xPathDef)
    except Exception, err:
        print (err)

    return retVal

def xmlGetSingleDirectSubnodeText(elementNode, subelementName, defaultReturn=""):
    """
    Return the text for a direct subnode of the lxml elementTree elementNode.
    Returns ONLY the first node found.
    
    Important Note: Looks only at direct subnodes, not all decendents (for max speed)
    
    >>> root = etree.fromstring(testXML)
    >>> xmlGetSingleDirectSubnodeText(root, "p", None)
    'A random paragraph'
    """
    retVal = defaultReturn

    try:
        retVal = elementNode.xpath('%s/node()' % subelementName)
        retVal = retVal[0]
    except ValueError, err: # try without node
        retVal = elementNode.xpath('%s' % subelementName)
        retVal = retVal[0]
    except IndexError, err:
        retVal = elementNode.xpath('%s' % subelementName)
    except Exception, err:
        print ("getSingleSubnodeText Error: ", err)

    if retVal == []:
        retVal = defaultReturn
    if isinstance(retVal, lxml.etree._Element):
        retVal = xmlGetTextOnly(retVal)        

    return retVal

def xmlGetTextSingleton(elementNode, xpath, defaultReturn=""):
    """
    Return text of element specified by xpath (with Node() as final part of path)
    
    >>> root = etree.fromstring(testXML)
    >>> xmlGetTextSingleton(root, "p[@id=2]/node()", None)
    'Another random paragraph'
    """
    retVal = defaultReturn
    try:
        retVal = elementNode.xpath(xpath)[0]
    except IndexError:
        retVal = defaultReturn
    
    if type(retVal) == type(elementNode):  # if it comes back an element
        retVal = xmlGetTextOnly(retVal)    
        
    return retVal    

def xmlGetTextOnly(elem, defaultReturn=""):
    """
    Return inner text of mixed content element with sub tags stripped out

    >>> root = etree.fromstring(testXML)
    >>> xmlGetTextOnly("<myxml>this <b>is <i>really</i></b> xml.</myxml>", None)
    'this is really xml.'
    >>> root = etree.fromstring("<myxml>this <b>is <i>really</i></b> xml.</myxml>", None)
    >>> xmlGetTextOnly(root, None)
    'this is really xml.'
    
    """
    retVal = defaultReturn
    # just in case the caller sent a string.
    try:
        if type(elem) == type(""):
            elem = etree.fromstring(elem)
    except Exception, err:
        print (err)
        retVal = defaultReturn
        
    try:
        etree.strip_tags(elem, '*')
        inner_text = elem.text
        if inner_text:
            retVal = inner_text.strip()
        else:
            retVal = defaultReturn
    except Exception, err:
        print (err)
        retVal = defaultReturn

    return retVal


# -------------------------------------------------------------------------------------------------------
# run it! (for testing)

if __name__ == "__main__":
    import doctest
    testXML = """
              <test>
                <author role="writer">this is just authoring test stuff</author>
                <p id="1">A random paragraph</p>
                <p id="2" type="speech">Another random paragraph</p>
                <p id="3">Another <b>random</b> paragraph</p>
                <p id="4">Another random paragraph</p>
              </test>
              """
    
    doctest.testmod()