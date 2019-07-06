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

import lxml
from lxml import etree
from ebooklib import epub

pyVer = 2
if (sys.version_info > (3, 0)):
    # Python 3 code in this block
    from io import StringIO
    pyVer = 3
else:
    # Python 2 code in this block
    import StringIO
import opasAPISupportLib

# -------------------------------------------------------------------------------------------------------

def authorDeriveMastFromXMLStr(authorXMLStr, listed=True):
    """
    Parses a string which has the PEP "aut" tag underneath a higher level tag, and returns the article Mast. for authors
    
    Listed can be True (listed authors), False (unlisted authors), or All (all authors)
    
    >>> authorDeriveMastFromXMLStr('<aut role="author" alias="false" listed="true" asis="false" lang="en"><nfirst>Dana</nfirst><nmid/><nlast>Birksted-Breen</nlast><nti/></aut>')
    ('Dana Birksted-Breen', ['Dana Birksted-Breen'])
    >>> authorDeriveMastFromXMLStr(r'<artauth hidden="false"><aut role="author" alias="false" listed="true" asis="false" authindexid="Kristeva, Julia"><nfirst type="FIRST">Julia</nfirst> <nlast>Kristeva</nlast> <nti>Professor</nti></aut><aut role="author" alias="false" listed="false" asis="false" authindexid="Vieira, Patricia"><nfirst type="FIRST">Patricia</nfirst> <nlast>Vieira</nlast> </aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Marder, Michael"><nfirst type="FIRST">Michael</nfirst> <nlast>Marder</nlast></aut></artauth>')
    ('Julia Kristeva &amp; Michael Marder', ['Julia Kristeva', 'Michael Marder'])
    >>> authorDeriveMastFromXMLStr(r'<artauth hidden="false"><aut role="author" alias="false" listed="true" asis="false" authindexid="Kristeva, Julia"><nfirst type="FIRST">Julia</nfirst> <nlast>Kristeva</nlast> <nti>Professor</nti></aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Vieira, Patricia"><nfirst type="FIRST">Patricia</nfirst> <nlast>Vieira</nlast> <nbio>A Lecturer at the University of Leeds and a Ph.D. candidate in the Department of Romance Languages and Literatures at Harvard University. Her dissertation is on political fiction and art in Latin America and Portugal. Her areas of specialization are Spanish and Lusophone literature, culture, art and film, as well as French and German cultural and literary theory.</nbio></aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Marder, Michael"><nfirst type="FIRST">Michael</nfirst> <nlast>Marder</nlast></aut></artauth>')
    ('Julia Kristeva, Patricia Vieira &amp; Michael Marder', ['Julia Kristeva', 'Patricia Vieira', 'Michael Marder'])
    >>> authorDeriveMastFromXMLStr(r'<artauth hidden="false"><aut role="author" alias="false" listed="true" asis="false" authindexid="Vieira, Patricia"><nfirst type="FIRST">Patricia</nfirst> <nlast>Vieira</nlast> <nbio>A Lecturer at the University of Leeds and a Ph.D. candidate in the Department of Romance Languages and Literatures at Harvard University. Her dissertation is on political fiction and art in Latin America and Portugal. Her areas of specialization are Spanish and Lusophone literature, culture, art and film, as well as French and German cultural and literary theory.</nbio></aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Marder, Michael"><nfirst type="FIRST">Michael</nfirst> <nlast>Marder</nlast></aut></artauth>')
    ('Patricia Vieira &amp; Michael Marder', ['Patricia Vieira', 'Michael Marder'])
    >>> authorDeriveMastFromXMLStr(r'<artauth hidden="false"><aut role="author" alias="false" listed="true" asis="false" authindexid="Boulanger, Ghislaine"><nfirst type="FIRST">Ghislaine</nfirst> <nlast>Boulanger</nlast></aut></artauth>')
    ('Ghislaine Boulanger', ['Ghislaine Boulanger'])
    """
    retVal = ("", [])
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
        logging.error("authorDeriveMast: Bad value supplied for listed: %s" % listed)

    authorCount = len(authorXMLList)
    authorsMast = ""
    authorList = []
    currAuthorNumber = 0
    for n in authorXMLList:
        currAuthorNumber += 1
        authorFirstName = xmlXPathReturnTextSingleton(n, "nfirst", "").strip()
        authorLastName = xmlXPathReturnTextSingleton(n, "nlast", "").strip()
        authorMidName = xmlXPathReturnTextSingleton(n, "nmid", "").strip()
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
    
    retVal = (authorsMast, authorList)

    return retVal
    
def authorsInCitationFormatFromXMLStr(authorXMLStr, listed=True):
    """
    Parses a string which has the PEP "aut" tag underneath a higher level tag, and returns a citation format list of authors
    
    Listed can be True (listed authors), False (unlisted authors), or All (all authors)

    >>> authorsInCitationFormatFromXMLStr('<aut role="author" alias="false" listed="true" asis="false" lang="en"><nfirst>Dana</nfirst><nmid/><nlast>Birksted-Breen</nlast><nti/></aut>')
    ('Birksted-Breen, D.', ['Birksted-Breen, Dana'])
    >>> authorsInCitationFormatFromXMLStr(r'')
    ('', [])
    >>> authorsInCitationFormatFromXMLStr(r'<artauth><aut role="author" alias="false" listed="true"><nfirst type="FIRST">Julia</nfirst> <nlast>Kristeva</nlast></aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Vieira, Patricia"><nfirst type="FIRST">Patricia</nfirst> <nlast>Vieira</nlast></aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Marder, Michael"><nfirst type="FIRST">Michael</nfirst> <nlast>Marder</nlast></aut></artauth>', listed=True)
    ('Kristeva, J., Vieira, P. &amp; Marder, M.', ['Kristeva, Julia', 'Vieira, Patricia', 'Marder, Michael'])
    >>> authorsInCitationFormatFromXMLStr(r'<artauth hidden="false"><aut role="author" alias="false" listed="true" asis="false" authindexid="Vieira, Patricia"><nfirst type="FIRST">Patricia</nfirst> <nlast>Vieira</nlast></aut><aut role="author" alias="false" listed="true" asis="false" authindexid="Marder, Michael"><nfirst type="FIRST">Michael</nfirst> <nlast>Marder</nlast></aut></artauth>')
    ('Vieira, P. &amp; Marder, M.', ['Vieira, Patricia', 'Marder, Michael'])
    >>> authorsInCitationFormatFromXMLStr(r'<artauth hidden="false"><aut role="author" alias="false" listed="true" asis="false" authindexid="Boulanger, Ghislaine"><nfirst type="FIRST">Ghislaine</nfirst> <nlast>Boulanger</nlast></aut></artauth>')
    ('Boulanger, G.', ['Boulanger, Ghislaine'])
    
    """
    retVal = ("", [])
    if isinstance(authorXMLStr, lxml.etree._Element):
        authorXMLStr = etree.tostring(authorXMLStr, with_tail=False, encoding="unicode") 

    if authorXMLStr != "" and authorXMLStr is not None:
    
        if isinstance(authorXMLStr, list):
            authorXMLStr = authorXMLStr[0]
    
        if isinstance(authorXMLStr, bytes):
            authorXMLStr = authorXMLStr.decode("utf-8")
            
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
            logging.error("authorDeriveMast: Bad value supplied for listed: %s" % listed)


        authorCount = len(authorXMLList)
        authorList = []
        authorsBibStyle = ""
        currAuthorNumber = 0
        for n in authorXMLList:
            currAuthorNumber += 1
            authorFirstName = xmlXPathReturnTextSingleton(n, "nfirst", "")
            authorFirstInitial = authorFirstName[0] if len(authorFirstName) > 0 else ""
            authorLastName = xmlXPathReturnTextSingleton(n, "nlast", "")
            authorMidName = xmlXPathReturnTextSingleton(n, "nmid", "")
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

            retVal = (authorsBibStyle, authorList)

    return retVal

def xmlRemoveEncodingString(xmlString):
    # Get rid of the encoding for lxml
    p=re.compile("\<\?xml version=[\'\"]1.0[\'\"] encoding=[\'\"]UTF-8[\'\"]\?\>\n", re.IGNORECASE)
    retVal = xmlString
    retVal = p.sub("", retVal)                
    
    return retVal

def xmlGetSubElementTextSingleton(elementNode, subElementName, defaultReturn=""):
    """
    Text for elements with only CDATA underneath
    
    >>> root = etree.fromstring(testXML)
    >>> xmlGetSubElementTextSingleton(root, "author")
    'this is just authoring test stuff'
    >>> root = etree.fromstring('<p>Another <b>random</b> paragraph with multiple <b>subelements</b></p>')
    >>> xmlGetSubElementTextSingleton(root, "b")
    'random'
    >>> xmlGetSubElementTextSingleton(root, "bxxx", None)
    """
    retVal = defaultReturn
    try:
        retVal = elementNode.find(subElementName).text
        retVal = retVal.strip()
    except Exception as err:
        retVal = defaultReturn

    return retVal

def xmlGetSubElementXMLSingleton(elementNode, subElementName, defaultReturn=""):
    """
    Returns the marked up XML text for elements (including subelements)
    If it doesn't exist or is empty, return the defaultReturn
    
    subElementName cannot be an xpath
    
    >>> root = etree.fromstring(testXML)
    >>> xmlGetSubElementXMLSingleton(root, "author", None)
    '<author role="writer">this is just authoring test stuff</author>'
    >>> root = etree.fromstring('<p>Another <b>random</b> paragraph with multiple <b>subelements</b></p>')
    >>> xmlGetSubElementXMLSingleton(root, "b")
    '<b>random</b>'
    >>> xmlGetSubElementXMLSingleton(root, "bxxxx", None)
    """
    retVal = defaultReturn
    try:
        retVal = etree.tostring(elementNode.find(subElementName), with_tail=False, encoding="unicode")
        if retVal == "":
            retVal = defaultReturn
    except Exception as err:
        retVal = defaultReturn

    return retVal

#def xmlFragmentReturnTextOnly(xmlString, defaultReturn=""):
    #"""
    #Return inner text of XML string element with sub tags stripped out
    
    #>>> xmlFragmentReturnTextOnly("<myxml>this <b>is <i>really</i></b> xml.</myxml>", None)
    #'this is really xml.'

    #"""
    #retVal = defaultReturn
    #root = etree.fromstring(xmlString)
    #etree.strip_tags(root, '*')
    #inner_text = root.text
    #if inner_text:
        #retVal = inner_text.strip()
    #else:
        #retVal = defaultReturn
    
    #return retVal

def xmlGetElementAttr(elementNode, attrName, defaultReturn=""):
    """
    Get an attribute from the lxml elementNode.  
    If it doesn't exist or is empty, return the defaultReturn

    >>> root = etree.fromstring(testXML)
    >>> currElement = xmlGetElements(root, "p[@id=2]", None)
    >>> xmlGetElementAttr(currElement[0], "type")
    'speech'
    >>> xmlGetElementAttr(currElement[0], "typeaaa", None)
    """
    retVal = defaultReturn
    try:
        retVal = elementNode.attrib[attrName]
        if retVal == "":
            retVal = defaultReturn
    except Exception as err:
        retVal = defaultReturn

    return retVal


def xmlGetElements(elementNode, xPathDef, defaultReturn=list()):
    """
    Return a list of XML ELEMENTS from the specified xPath

    Example:
    strList = xmlGetElements(treeRoot, "//p")
    
    >>> root = etree.fromstring(testXML)
    >>> len(xmlGetElements(root, "p[@id=2]", None))
    1
    >>> xmlGetElements(root, "//pxxxx", None)    # test default return
    """
    retVal = defaultReturn
    try:
        retVal = elementNode.xpath(xPathDef)
        if retVal == []:
            retVal = defaultReturn
        
    except Exception as err:
        print (err)

    return retVal

def xmlGetDirectSubnodeTextSingleton(elementNode, subelementName, defaultReturn=""):
    """
    Return the text for a direct subnode of the lxml elementTree elementNode.
    Returns ONLY the first node found (Singleton).
    
    Important Note: Looks only at direct subnodes, not all decendents (for max speed)
    
    >>> root = etree.fromstring(testXML)
    >>> xmlGetDirectSubnodeTextSingleton(root, "p", None)
    'A random paragraph'
    """
    retVal = defaultReturn

    try:
        retVal = elementNode.xpath('%s/node()' % subelementName)
        retVal = retVal[0]
    except ValueError as err: # try without node
        retVal = elementNode.xpath('%s' % subelementName)
        retVal = retVal[0]
    except IndexError as err:
        pass
        #retVal = defaultReturn  # empty
    except Exception as err:
        print ("getSingleSubnodeText Error: ", err)

    if retVal == []:
        retVal = defaultReturn

    return retVal

def xmlElemOrStrToXMLString(elemOrXMLStr, defaultReturn=""):
    """
    Return XML string 

    >>> root = etree.fromstring("<myxml>this <b>is <i>really</i></b> xml.</myxml>", None)  #mixed content element
    >>> xmlElemOrStrToXMLString(root, None)
    '<myxml>this <b>is <i>really</i></b> xml.</myxml>'
    """
    retVal = defaultReturn
    # just in case the caller sent a string.
    try:
        if isinstance(elemOrXMLStr, lxml.etree._Element):
            retVal = etree.tostring(elemOrXMLStr, encoding="unicode")        
        else:
            retVal = elemOrXMLStr
    except Exception as err:
        print (err)
        retVal = defaultReturn
        
    return retVal

def xmlElemOrStrToText(elemOrXMLStr, defaultReturn=""):
    """
    Return string with all tags stripped out from either etree element or xml marked up string
    
    If string is empty or None, return the defaultReturn

    >>> root = etree.fromstring(testXML)
    >>> xmlElemOrStrToText(testXML, None)[0:100]
    'this is just authoring test stuff\\n                A random paragraph\\n                Another random '
    >>> xmlElemOrStrToText(root, None)[0:100]
    'this is just authoring test stuff\\n                A random paragraph\\n                Another random '
    >>> root = etree.fromstring("<myxml>this <b>is <i>really</i><empty/></b> xml.</myxml>", None)  #mixed content element
    >>> xmlElemOrStrToText(root, None)
    'this is really xml.'
    >>> isinstance(xmlElemOrStrToText(root, None), str)  # make sure it's string
    True
    >>> xmlElemOrStrToText(xmlXPathReturnTextSingleton(root, "pxxx", ""), None)
    """
    retVal = defaultReturn
    if elemOrXMLStr is None or elemOrXMLStr == "":
        retVal = defaultReturn
    elif isinstance(elemOrXMLStr, lxml.etree._ElementUnicodeResult):
        retVal = "%s" % elemOrXMLStr # convert to string
    # just in case the caller sent a string.
    else:
        try:
            if isinstance(elemOrXMLStr, str):
                parser = lxml.etree.XMLParser(encoding='utf-8', recover=True)                
                elem = etree.fromstring(elemOrXMLStr, parser)
            else:
                elem = elemOrXMLStr
        except Exception as err:
            print (err)
            retVal = defaultReturn
            
        try:
            etree.strip_tags(elem, '*')
            inner_text = elem.text
            if inner_text:
                retVal = inner_text.strip()
            else:
                retVal = defaultReturn
        except Exception as err:
            print ("xmlElemOrStrToText: %s" % err)
            retVal = defaultReturn

    if retVal == "":
        retVal = defaultReturn
        
    return retVal

def xmlXPathReturnTextList(elementNode, xpath, defaultReturn=list()):
    """
    Return text of element specified by xpath (with Node() as final part of path)
    
    >>> root = etree.fromstring(testXML)
    >>> xmlXPathReturnTextList(root, "//p", None)
    ['A random paragraph', 'Another random paragraph', 'Another random paragraph', 'Another random paragraph', 'Another random paragraph with multiple subelements']
    >>> xmlXPathReturnTextList(root, "p", None)
    ['A random paragraph', 'Another random paragraph', 'Another random paragraph', 'Another random paragraph', 'Another random paragraph with multiple subelements']
    >>> xmlXPathReturnTextList(root, "pxxx", None) # check default return
    """
    retVal = defaultReturn
    try:
        retVal = elementNode.xpath(xpath)
        retVal = [xmlElemOrStrToText(n) for n in retVal]
        if retVal == []:
            retVal = defaultReturn
    except IndexError:
        retVal = defaultReturn
    
    return retVal    

def xmlXPathReturnTextSingleton(elementNode, xpath, defaultReturn=""):
    """
    Return text of element specified by xpath)
    
    >>> root = etree.fromstring(testXML)
    >>> xmlXPathReturnTextSingleton(root, "p[@id=2]/node()", None)
    'Another random paragraph'
    >>> xmlXPathReturnTextSingleton(root, "p[@id=2]", None)
    'Another random paragraph'
    >>> xmlXPathReturnTextSingleton(root, "p", None)
    'A random paragraph'
    >>> xmlXPathReturnTextSingleton(root, "pxxxx", None) # check default return
    """
    retVal = defaultReturn
    try:
        retVal = elementNode.xpath(xpath)[0]
    except IndexError:
        retVal = defaultReturn
    
    if type(retVal) == type(elementNode):  # if it comes back an element
        retVal = xmlElemOrStrToText(retVal)    
        
    return retVal    

def xmlXPathReturnXMLSingleton(elementNode, xPathDef, defaultReturn=""):
    """
    Return a list of XML ELEMENTS from the specified xPath

    Example:
    strList = xmlXPathReturnXMLSingleton(treeRoot, "//artauth")
    
    >>> root = etree.fromstring(testXML)
    >>> xmlXPathReturnXMLSingleton(root, "p[@id=2]", None)
    '<p id="2" type="speech">Another random paragraph</p>'
    """
    retVal = defaultReturn
    try:
        retVal = elementNode.xpath(xPathDef)
        if isinstance(retVal, list) and len(retVal) > 0:
            retVal = retVal[0]
        retVal = etree.tostring(retVal, with_tail=False, encoding="unicode") 
                
    except Exception as err:
        print (err)

    return retVal

def xmlXPathReturnXMLStringList(elementNode, xPathDef, defaultReturn=list()):
    """
    Return a list of XML tagged strings from the nodes in the specified xPath

    Example:
    strList = elementsToStrings(treeRoot, "//aut[@listed='true']")

    >>> root = etree.fromstring(testXML)
    >>> stringList = xmlXPathReturnXMLStringList(root, "p")
    >>> len(stringList)
    5
    >>> stringList[0]
    '<p id="1">A random paragraph</p>'
    >>> xmlXPathReturnXMLStringList(root, "pxxxx", None)  # check default return
    """
    retVal = defaultReturn
    try:
        retVal = [etree.tostring(n, with_tail=False, encoding="unicode") for n in elementNode.xpath(xPathDef)]
        if len(retVal) == 0:
            retVal = defaultReturn
    except:
        retVal = defaultReturn
        
    return retVal   

def extractHTMLFragment(strHTML, xpathToExtract="//div[@id='abs']"):
    # parse HTML
    htree = etree.HTML(strHTML)
    retVal = htree.xpath(xpathToExtract)
    # make sure it's a string
    retVal = opasAPISupportLib.forceStringReturnFromVariousReturnTypes(retVal)
    
    return retVal

def convertXMLStringToHTML(xmlTextStr, xsltFile=r"../styles/pepkbd3-html.xslt"):
    retVal = None
    if xmlTextStr is not None and xmlTextStr != "[]":
        xsltFile = etree.parse(xsltFile)
        xsltTransformer = etree.XSLT(xsltFile)
        sourceFile = etree.fromstring(xmlTextStr)
        transformedData = xsltTransformer(sourceFile)
        retVal = str(transformedData)
    
    return retVal
def convertHTMLToEPUB(htmlString, outputFilenameBase, artID, lang="en", htmlTitle=None, styleSheet="../styles/pep-html-preview.css"):
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
        logging.warning("Cannot open stylesheet %s" % e)
    
    
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

def removeEncodingString(xmlString):
    # Get rid of the encoding for lxml
    p=re.compile("\<\?xml version=\'1.0\' encoding=\'UTF-8\'\?\>\n")  # TODO - Move to module globals to optimize
    retVal = xmlString
    retVal = p.sub("", retVal)                
    
    return retVal



# -------------------------------------------------------------------------------------------------------
# run it! (for testing)
# 
# nrs note - Trying main at the top, for function refactors (wing moves to the bottom of the file.

if __name__ == "__main__":
    print ("Running in Python %s" % sys.version_info[0])
    import doctest

    testXML = """
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


