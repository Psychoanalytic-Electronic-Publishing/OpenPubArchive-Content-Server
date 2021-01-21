#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
""" 
OPAS - XML Support Function Library

Various support functions having to do with XML conversion (e.g., to HTML, ePub, plain text ...),
  extraction of portions of XML, etc.
    
"""
#Revision Notes:
    #2020.0224.1 XSLT converter optimization (took to long to parse XSLT file) so loads only once.
    
    #2020.0311.1 Setup html conversion to substutute current server domain + api call
                # for image src.  Changed xslt file as well.
                
    #2020.0422.1 Tweaked FirstPageCollector to watch for max characters and paragraphs, not just
                # always to go to the page break
                
    #2020.0423.1 Ajusted FirstPageCollector to remove words in the trailing sentence of the excerpt
                # to the preceding punctuation mark.
                
    #2020.0425.1 - Get rid of commented routines for first_page_excerpting.  FirstPageCollector works
                # well.
                #  added read_file to help testing load
                # All tests except get_pages_html (first page, 0 to 1) pass
                
    #2020.0429.1 - Added new functions and changed several others to work better
    
                # xml_get_pages(xmlstr, offset=1, limit=1, inside="body", env="body", pagebrk="pb", pagenbr="n", remove_tags=[])
                #   This is finally working correctly, per doctests at least.  Note the first and last page offsets are
                #   applied to ONLY the direct children of the "inside" tag specified.  The first tag is 1.
                #   But since pb's are assumed to be at the end of the page, 1 means everything up to the first pagebreak.
                #   Also, added return of first and last page numbers captured, to help the caller especially when the pages
                #   don't exactly match what was expected, due to uneven nesting of pagebreaks in the XML.

                # xml_get_pages_html(xmlorhtmlstr, offset=0, limit=1, inside="div[@id='body']", env="body", pagebrk="div[@class='pagebreak']", pagenbr="p[@class='pagenumber']", remove_tags=[])
                #   This was changed similarly to xml_get_pages, except that it's more likely to return the expected
                #   pages since there's less nesting in the PEP transformed HTML at least.  Like xml_get_pages, it now returns
                #   the page numbers of the first and last page returned.
                
                # xml_get_pages_starting_with(xmlstr, start_with, limit=1, inside="body", env="body", pagebrk="pb", pagenbr="n", remove_tags=[])
                #   Still somewhat experimental, this allows the caller to specify an actual document page number they would like to start
                #   with.  Works well with the test file SE.006.R0007A, but needs more field testing.  Will only work with
                #   pagebreaks that are direct children  to the inside parameter tag.
                
                # xml_get_pagebreak_dict(xmlstr, inside="body", pagebrk="pb", pagenbr="n", remove_tags=[])
                #   Support function for xml_get_pages_starting_with to bring back all "inside" page breaks along with support info.

                # xmlstr_to_etree(xmlstr)
                #   Support function of all the above to safely convert the XML string to a lxml tree.
                
                # All doctests currently pass

    #2020.0812.1 - Cleaned up some error print messages.


__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2020.0812.1"
__status__      = "Development"


import sys
# sys.path.append('../libs')
sys.path.append('../config')

import re
import os
import os.path
import stdMessageLib
import logging
logger = logging.getLogger(__name__)
import copy
import urllib
import urllib.request
os.environ['XML_CATALOG_FILES'] = urllib.request.pathname2url(r"X:\_PEPA1\catalog.xml")
import datetime

import lxml
from lxml import etree
import lxml.html as lhtml
parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=False)

import opasConfig
from localsecrets import APIURL, IMAGE_API_LINK

from ebooklib import epub
from io import StringIO, BytesIO

show_dbg_messages = False
stop_on_exceptions = False

#-----------------------------------------------------------------------------
def convert_xml_to_html_file(xmltext_str, output_filename=None):
    if output_filename is None:
        basename = "opasDoc"
        suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        filename_base = "_".join([basename, suffix]) # e.g. 'mylogfile_120508_171442'        
        output_filename = filename_base + ".html"

    htmlString = xml_str_to_html(xmltext_str)
    fo = open(output_filename, "w", encoding="utf-8")
    fo.write(str(htmlString))
    fo.close()

    return output_filename

#-----------------------------------------------------------------------------
# at least for testing
def read_file(filename):
    """
    NOT CURRENTLY USED in OPAS (2020-09-14)

    >> html = read_file(r"X:\\_PEPA1\\_PEPa1v\\_PEPArchive\\IJP\\043\\IJP.043.0306A(bEXP_ARCH1).XML")
    >> html = read_file(r"X:\\_PEPA1\\_PEPa1v\\_PEPArchive\\SE\\004-005\\SE.004.R0009A(bEXP_ARCH1).XML")
    """
    xml_data = b""
    with open(filename, 'rb') as filehandle:
        for line in filehandle:
            xml_data += line

    return xml_data

def xml_remove_tags_from_xmlstr(xmlstr, remove_tags=[]):
    ret_val = xmlstr
    try:
        root = etree.fromstring(xmlstr.encode()) # encode fixes lxml error 'Unicode strings with encoding declaration are not supported...'
        xml_remove_tags(root, remove_tags=remove_tags)
        ret_val = etree.tostring(root)
        ret_val = ret_val.decode("UTF8")
    except Exception as e:
        logger.error(f"Could not remove tags {remove_tags}. Exception {e}")

    return ret_val

def xml_remove_tags(root, remove_tags=[]):
    ret_val = True
    try:
        for tag_to_remove in remove_tags:
            remove_these = root.xpath(f"//{tag_to_remove}")
            for n in remove_these:
                n.getparent().remove(n)
    except Exception as e:
        logger.error(f"Error removing requested tags: {e}")
        ret_val = False
        
    return ret_val
    
# -------------------------------------------------------------------------------------------------------
class FirstPageCollector:
    def __init__(self, skip_tags=["impx", "tab"], para_limit=opasConfig.MAX_EXCERPT_PARAS, char_limit=opasConfig.MAX_EXCERPT_CHARS, char_min=opasConfig.MIN_EXCERPT_CHARS):
        self.events = []
        self.doc = "<abs>"
        self.in_body = False
        self.tag_stack = []
        self.skip_tags = skip_tags
        self.para_limit = para_limit
        self.para_count = 0
        self.char_limit = char_limit
        self.char_min = char_min
        self.char_count = 0
        self.fini = False # all closed up and ready to stop
        self.close_up = False
        
    def start(self, tag, attrib):
        if tag not in self.skip_tags and self.in_body:
            self.events.append("start %s %r" % (tag, dict(attrib)))
            att_str = ""
            for key, val in attrib.items():
                if key in ["url"]: # only do this in special cases...if it's a title, we don't want it quoted
                    val = urllib.parse.quote_plus(val)
                att_str += f'{key}="{val}" '
            if att_str == "":
                self.doc += f"<{tag}>"
            else:
                att_str = att_str.rstrip()
                self.doc += f"<{tag} {att_str}>"
            self.tag_stack.append(tag)
            
        if tag == "body":
            self.in_body = True
            
    def end(self, tag):
        if tag not in self.skip_tags and tag == "body" and self.in_body:
            # no pb in body.  Stop recording.
            self.in_body = False
            #close outer tag
            self.doc += "</abs>"
            
        if tag not in self.skip_tags and self.in_body:
            self.events.append("end %s" % tag)
          
            if tag == "pb" or tag == "p":
                if tag == "p": # count paras
                    self.para_count += 1

                if self.para_count > self.para_limit:
                    msg = f"   ...Paragraph limit {self.para_limit} for excerpt reached. Para Count: {self.para_count}, Char Count: {self.char_count}"
                    logger.debug(msg)
                    if show_dbg_messages: print (msg)
                    self.close_up = True
    
                if self.char_count > self.char_limit:
                    msg = f"   ...Character limit {self.char_limit} for excerpt reached or exceeded, at end of para. Para Count: {self.para_count}, Char Count: {self.char_count}."
                    logger.debug(msg)
                    if show_dbg_messages: print (msg)
                    self.close_up = True
                
                if tag == "pb" and self.char_count > self.char_min:
                    self.close_up = True
            
                if self.close_up:
                    punct = r'[\.\!\?\)\>]+'
                    if tag == "p": # this could be the last para, and it could be a split para (p then p2)
                        #  back off text to last punctuation.  If you hit a tag (>), stop, can't go further.
                        google_safe = self.doc
                        while re.match(punct, google_safe[-1]) is None:
                            google_safe = google_safe[:-1]
                        self.doc = google_safe
                    
                    if tag == "pb": # this could be a pb between a split para
                        #  back off text to last punctuation.  If you hit a tag (>), stop, can't go further.
                        google_safe_list = self.doc.split(sep="<pb>")
                        pb_tag = google_safe_list[-1]
                        google_safe = "<pb>".join(google_safe_list[0:-1])
                        while re.match(punct, google_safe[-1]) is None:
                            google_safe = google_safe[:-1]
    
                        # see if we need to go behind para tag (for split para)
                        google_safe2_list = google_safe.split(sep="</p>")
                        if google_safe2_list[-1] == "": #  it should be
                            # could make more efficient just using re.split on punct. #TODO
                            while re.match(punct, google_safe2_list[-2][-1]) is None and google_safe2_list[-2] is not "":
                                google_safe2_list[-2] = google_safe2_list[-2][:-1]
                            google_safe2 = '</p>'.join(google_safe2_list)
                            self.doc = google_safe2 + "<pb>" + pb_tag
                        else:
                            # not sure why this would be, don't do anything
                            msg = f"Unaccounted for text when excerpting...first 50 chars of discarded text: {google_safe2_list[-1][:50]}"
                            logger.debug(msg)
                            if show_dbg_messages: print (msg)
                    
            self.doc += f"</{tag}>"
            if len(self.tag_stack) > 0:
                self.tag_stack.pop()
                
        if self.in_body and (tag == "pb" or tag == "p"):
            if not self.fini:
                if self.close_up:
                    self.in_body = False # skip the rest.
                    while len(self.tag_stack) > 0:
                        tag_to_close = self.tag_stack.pop()
                        self.doc += f"</{tag_to_close}>"
                    self.doc += "</abs>"
                    self.fini = True
            
    def data(self, data):
        if self.in_body:
            if data == "&":
                data = "&amp;" # reencode
            elif data == "<":
                data = "&lt;" # reencode
            elif data == ">":
                data = "&gt;" # reencode
            elif data == "'":
                data = "&apos;" # reencode    
            elif data == '"':
                data = "&quot;" # reencode    
            self.events.append("data %r" % data)
            self.char_count += len(data)
            self.doc += f"{data}"
            
    def comment(self, text):
        self.events.append("comment %s" % text)
        
    def close(self):
        self.events.append("close")
        return self.doc

# -------------------------------------------------------------------------------------------------------
class XSLT_Transformer(object):
    # to allow transformers to be saved at class level in dict
    transformers = {}

    def __init__(self):
        pass
    
    def set_transformer(self, transformer_name, xslt_file, style_path=opasConfig.STYLE_PATH):
        self.transformer_name = transformer_name
        self.transformer_tree = None
        self.file_spec = None
        style_paths = style_path.split(";")
        # find path of file
        for relative_path in style_paths:
            self.file_spec = os.path.join(relative_path, xslt_file)
            if os.path.exists(self.file_spec):
                try:
                    self.transformer_tree=etree.parse(self.file_spec)
                except Exception as e:
                    err =  f"Parse error for XSLT file {self.file_spec}.  Error {e}"
                    if stop_on_exceptions:
                        raise Exception(err)
                    else:
                        logger.error(err)
                else:
                    try:
                        # save it to class dict by name
                        self.__class__.transformers[transformer_name] = etree.XSLT(self.transformer_tree)
                    except Exception as e:
                        err = f"Transform definition error for XSLT file {self.file_spec}.  Error {e}"
                        if stop_on_exceptions:
                            raise Exception(err)
                        else:
                            logger.error(err)
                    else:
                        break;
        if not os.path.exists(self.file_spec):
            err = f"XSLT file {self.file_spec} missing for all folders in STYLE path."
            if stop_on_exceptions:
                raise FileNotFoundError(err)
            else:
                logger.error(err)
        

# -------------------------------------------------------------------------------------------------------
# create module level persistent transformers
g_transformer = XSLT_Transformer()
g_transformer.set_transformer(opasConfig.TRANSFORMER_XMLTOHTML, opasConfig.XSLT_XMLTOHTML)
g_transformer.set_transformer(opasConfig.TRANSFORMER_XMLTOTEXT_EXCERPT, opasConfig.XSLT_XMLTOTEXT_EXCERPT)
g_transformer.set_transformer(opasConfig.TRANSFORMER_XMLTOHTML_EXCERPT, opasConfig.XSLT_XMLTOHTML_EXCERPT)
g_transformer.set_transformer(opasConfig.XSLT_XMLTOHTML_GLOSSARY_EXCERPT, opasConfig.XSLT_XMLTOHTML_GLOSSARY_EXCERPT)

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
    pepxml = etree.parse(StringIO(author_xmlstr), parser=parser)
    
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
        author_first_name = xml_xpath_return_textsingleton(n, "nfirst", "")
        author_last_name = xml_xpath_return_textsingleton(n, "nlast", "")
        author_mid_name = xml_xpath_return_textsingleton(n, "nmid", "")
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
        
        pepxml = etree.parse(StringIO(author_xmlstr), parser=parser)
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
    
            if author_last_name != "":
                if author_given_names != "":
                    author_name = author_last_name + ", " + author_given_names
                    author_name_inits = author_last_name + ", " + author_given_inits
                else:
                    author_name = author_last_name
                    author_name_inits = ""
            else:
                if author_given_names != "":
                    author_name = author_given_names
                    author_given_inits = author_first_initial + "."
                    author_name_inits = author_given_inits
                else:
                    author_name = ""
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
    """
    NOT CURRENTLY USED in OPAS (2020-09-14)
    """
    ret_val = f"""<p class="citeas"><span class="authors">{authors_bib_style}</span> (<span class="year">{art_year}</span>) <span class="title">{art_title}</span>. <span class="sourcetitle">{art_pep_sourcetitle_full}</span> <span class="pgrg">{art_vol}</span>:<span class="pgrg">{art_pgrg}</span></p>"""
    return ret_val

def xmlstr_to_etree(xmlstr):
    """
    Convenience function - take an xmlstr, in bytes or string or as etree, and return root of an etree
    """

    if isinstance(xmlstr, bytes):
        try:
            root = etree.parse(BytesIO(xmlstr))
        except Exception as e:
            logger.error(f"Error parsing Bytes xmlstr: {e}")
    elif isinstance(xmlstr, str):
        try:
            xmlstr = xmlstr.replace("encoding=\'UTF-8\'", "")
            root = etree.parse(StringIO(xmlstr))
        except Exception as e:
            logger.error(f"Error parsing xmlstr: {e}")
    elif etree.iselement(xmlstr):
        root = xmlstr
    else:
        logger.error("Unknown type to xmlstr_to_etree: ", type(xmlstr))
        
    return root
    
def xml_get_pagebreak_dict(xmlstr, inside="body", pagebrk="pb", pagenbr="n", remove_tags=[]):
    """
    Return a dictionary of page numbers and page break counts

    >>> ret_tuple = xml_get_pagebreak_dict(test_xml2, inside="test")
    >>> ret_tuple[0]
    {'1': (...)}
    
    """
    ret_val = (None, None)
    pb_dict = {}
    root = xmlstr_to_etree(xmlstr)
    
    pb_list = root.xpath(f'//{inside}/{pagebrk}') # for first page nbr, which is 1 pb after the offset1 since pb is at end of page
    count = 0
    try:
        for pb in pb_list:
            count += 1
            try:
                pn_node = pb.xpath(pagenbr)[0]
            except Exception as e:
                # no page number
                pass
            else:
                pb_dict[pn_node.text] = (count, pb, pn_node)
    except Exception as e:
        logger.error(f"Error compiling pagebreak dict: {e}")
    else:
        ret_val = (pb_dict, root)

    return ret_val
    
def xml_get_pages_starting_with(xmlstr, start_with, limit=1, inside="body", env="body", pagebrk="pb", pagenbr="n", remove_tags=[]):
    """
    NOT CURRENTLY USED in OPAS (2020-09-14)

    Return the xml between the given page breaks (default <pb>).

    >>> xml = xml_file_to_xmlstr(r"tstfiles/DoNotRedistribute/SE.006.R0007A(bKBD3).xml")
    >>> ret_tuple = xml_get_pages_starting_with(xml, start_with="13", remove_tags=["meta"])
    >>> ret_tuple[0][:100]
    '<body>\\n<p lgrid="SEFviia120">The chief importance however of the <i>aliquis</i> example lies ...'
    >>> ret_tuple[2:]
    ('13', '13')
    

    """
    pg_end_nbr = ""
    ret_val = ""
    pg_dict = {}
    # root = xmlstr_to_etree(xmlstr)

    try:
        pg_dict, root = xml_get_pagebreak_dict(xmlstr, inside=inside)
        count = 0
        pg_start_elem = None
        pg_end_elem = None
        for key in pg_dict.keys():
            if key == start_with:
                pg_start_elem = pg_dict[key][1]
            else:
                if pg_start_elem is None:
                    #track the last key
                    last_key = pg_dict[key][1]

            if pg_start_elem is not None:
                count += 1
                if count >= limit:
                    pg_start_elem = last_key # start the pagebreak before
                    pg_end_elem = pg_dict[key][1]
                    pg_end_nbr = key
                    break
        
        elem_list = root.xpath(f"//{inside}")[0].getchildren()
        start_idx = elem_list.index(pg_start_elem) + 1
        end_idx = elem_list.index(pg_end_elem) + 1
        subtree = elem_list[start_idx:end_idx]
        new_xml = f"<{env}>\n"
        for n in subtree:
            try:
                frag = etree.tostring(n).decode("utf8") + "\n" # separate for monitoring the fragment
                new_xml += frag
            except Exception as e:
                logger.warning(f"Error converting node: {e}")
        # close the new xml string
        new_xml += f"</{env}>\n"
    except Exception as e:
        logger.error(f"Error getting pages starting with: {e}")
    else:
        ret_val = new_xml
        
    ret_val = (new_xml, subtree, start_with, pg_end_nbr)

    return ret_val    
    
    
def xml_get_pages(xmlstr, offset=0, limit=1, inside="body", env="body", pagebrk="pb", pagenbr="n", remove_tags=[]):
    """
    Return the xml between the given page breaks (default <pb>).
    
    The pages are returned in the first entry of a tuple: an 'envelope', default <body></body> tag, an 'envelope' of sorts.
    The xml element list is returned as the second entry of the tuple
    if there's an error ("", []) is returned.

    If offset is not specified, it's 1 by default (first page)
    If limit is not specified, it's 1 by default
    So if neither is specified, it should return everything in 'inside' up to the first 'pagebrk'
    
    >>> ret_tuple = xml_get_pages(test_xml2, 2, 1, inside="test", env="body")
    >>> ret_tuple[0]
    '<body>\\n<p id="2" type="speech">Another random paragraph</p>\\n                \\n<p id="3">Another <b>random</b> paragraph</p>\\n                \\n<grp>\\n                   <p>inside group</p>\\n                </grp>\\n                \\n<pb><n>2</n></pb>\\n                \\n</body>\\n'
    >>> ret_tuple[2:]
    ('2', '2')

    >>> ret_tuple = xml_get_pages(test_xml2, 1, 1, inside="test", env="body")
    >>> ret_tuple[0]
    '<body>\\n<author role="writer">this is just authoring test stuff</author>\\n                \\n<p id="1">A random paragraph</p>\\n                \\n<pb><n>1</n></pb>\\n                \\n</body>\\n'
    >>> ret_tuple[2:]
    ('1', '1')

    >>> xml = xml_file_to_xmlstr(r"tstfiles/DoNotRedistribute/SE.006.R0007A(bKBD3).xml")
    >>> ret_tuple = xml_get_pages(xml, 1, 1, inside="body", env="pepkbd3", remove_tags=["meta"])
    >>> ret_tuple[0]
    '<pepkbd3>\\n<artinfo arttype="ART" j="SE" ISBN="0099426579">\\n<artyear>1901</artyear><artbkinfo prev="SE.006.0000A" extract="SE.006.0000A"/>\\n<artvol>6</artvol>\\n<artpgrg style="arabic">vii-296</artpgrg>\\n<arttitle lgrid="SEFviia1">The Psychopathology of Everyday Life</arttitle><artsub lgrid="SEFviia2">Forgetting, Slips of the Tongue, Bungled Actions, Superstitions and Errors (1901)</artsub>\\n<artauth>\\n<aut alias="false" role="author" listed="true"><nfirst>Sigmund</nfirst> <nlast>Freud</nlast></aut></artauth></artinfo>\\n<tagline><poem><verse>\\n<p lgrid="SEFviia3">Nun ist die Luft von solchem Spuk so voll,</p>\\n<p lgrid="SEFviia4">Dass niemand weiss, wie er ihn meiden soil.</p>\\n<p lgrid="SEFviia5" align="right"><i>Faust</i>, Part II, Act V, Scene 5</p></verse><verse>\\n<p lgrid="SEFviia6">Now fills the air so many a haunting shape,</p>\\n<p lgrid="SEFviia7">That no one knows how best he may escape.</p>\\n<p lgrid="SEFviia8" align="right">(Bayard Taylor\\'s translation)</p></verse></poem></tagline>\\n<pb><n>vii</n></pb>\\n</pepkbd3>\\n'
    >>> ret_tuple[2:]
    ('vii', 'vii')

    >>> ret_tuple = xml_get_pages(xml, 3, 1, inside="body", env="body")
    >>> ret_tuple[0][-50:]
    'k to 1901.]</p></ftn></ftr><n>1</n></pb>\\n\\n</body>\\n'
    >>> ret_tuple[2:]
    ('1', '1')
    
    >>> ret_tuple = xml_get_pages(xml, 1, 3, inside="body", env="body")
    >>> ret_tuple[0][-50:]
    'k to 1901.]</p></ftn></ftr><n>1</n></pb>\\n\\n</body>\\n'
    >>> ret_tuple[2:]
    ('vii', '1')
    
    >>> ret_tuple = xml_get_pages(xml, 2, 1, inside="body", env="body")
    >>> ret_tuple[0]
    '<body>\\n<blank type="PEPBLANK"/>\\n\\n<pb><n>viii</n></pb>\\n</body>\\n'
    >>> ret_tuple[2:]
    ('viii', 'viii')
    
    >>> ret_tuple = xml_get_pages(xml, 10, 2, inside="body", env="body")
    >>> ret_tuple[0][-463:]
    '<pb><ftr><ftn type="PG" id="F018" label="1">\\n<p lgrid="SEFviia91">[Virgil, <i>Aeneid</i>, IV, 625. Literally: &#8216;Let someone (<i>aliquis</i>) arise from my bones as an avenger!&#8217;]</p></ftn><ftn type="PG" id="F019" label="2">\\n<p lgrid="SEFviia92">This is the general method of introducing concealed ideational elements to consciousness. Cf. my <i>Interpretation of Dreams, Standard Ed.</i>, <b>4</b>, <pgx>101</pgx>.</p></ftn></ftr><n>9</n></pb>\\n\\n</body>\\n'
    >>> ret_tuple[2:]
    ('8', '9')
    """
    no_page_nbr = "npn"
    ret_val = ("", [], no_page_nbr, no_page_nbr)

    if limit is None: # this should not happen, it should assign the default as specd.  Not sure why it does.
        ret_val = (xmlstr, [], no_page_nbr, no_page_nbr)
    else:
        try:
            if offset == 0:
                #logger.error("Bad page offset requested.  First offset is 0 instead of 1")
                offset = 1 # First page is 1 (even though we're not jumping)
                offset1 = offset - 1 # offset 2 is the second page, so from the first pb to the one before
            else:
                offset1 = offset # offset 2 is the second page, so from the first pb to the one before
            
            offset2 = offset1 + limit
            
        except Exception as e:
            logger.warning(f"Offset/Limit specification error: {e}")
    
        try:
            root = xmlstr_to_etree(xmlstr)
            page_count = len(root.xpath("//pb"))
            if offset2 > page_count:
                offset2 = page_count - 2
            xml_remove_tags(root, remove_tags=remove_tags)
        except Exception as e:
            logger.error(f"xml conversion (extract) error: {e}. Returning full xml instance")
            ret_val = (xmlstr, [], no_page_nbr, no_page_nbr)
        else:
            try: # get first page break
                pb = root.xpath(f'//{inside}/{pagebrk}[{offset1+1}]') # for first page nbr, which is 1 pb after the offset1 since pb is at end of page
                if pb != []:
                    #firstpbfrag  = etree.tostring(pb[0]).decode("utf8") + "\n"
                    # make sure we were given the subelement spec
                    if pagenbr is not None:
                        try:
                            pn_node = pb[0].xpath(pagenbr)[0]
                        except Exception as e:
                            # no page number
                            first_pn = no_page_nbr
                        else:
                            first_pn = pn_node.text
                else:
                    #firstpbfrag = ""
                    first_pn = no_page_nbr
            except Exception as e:
                #firstpbfrag = ""
                logger.warning(f"Could not get first pagebreak: {e}")
                
            try: # get second page break
                pb2 = root.xpath(f'//{inside}/{pagebrk}[{offset2}]')
                if pb2 != []:
                    secondpbfrag = etree.tostring(pb2[0]).decode("utf8") + "\n"
                    if pagenbr is not None:
                        try:
                            pn2_node = pb2[0].xpath(pagenbr)[0]
                        except Exception as e:
                            # no page number
                            last_pn = no_page_nbr
                        else:
                            last_pn = pn2_node.text
                else:
                    secondpbfrag = "" 
                    last_pn = no_page_nbr
                    
            except Exception as e:
                secondpbfrag = ""
                logger.warning(f"Could not get ending pagebreak: {e}")
            
            # Now let's get the text between, or before, if offset1 == 0 (first break)
            if offset1 == 0: # get all tags before the first pb (offset passed in was 1)
                elem_list = root.xpath(f'//{inside}/{pagebrk}[{offset2}]/preceding::*')
                for n in reversed(elem_list):
                    if n.getparent() in elem_list:
                        elem_list.remove(n)
                
            else: # get all content between offset1 and offset2
                # get list of elements between
                elem_list = xml_get_elements_between_element(root, inside=inside, between_element=pagebrk, offset1=offset1, offset2=offset2)
                # no need to add end page
                secondpbfrag = ""
                
            new_xml = f"<{env}>\n"
            for n in elem_list:
                try:
                    frag = etree.tostring(n).decode("utf8") + "\n" # separate for monitoring the fragment
                    new_xml += frag
                except Exception as e:
                    logger.warning(f"Error converting node: {e}")
        
            # add the last pb
            new_xml += secondpbfrag
            # close the new xml string
            new_xml += f"</{env}>\n"
            
            ret_val = (new_xml, elem_list, first_pn, last_pn)

    return ret_val

def xml_get_pages_html(xmlorhtmlstr, offset=0, limit=1, inside="div[@id='body']", env="body", pagebrk="div[@class='pagebreak']", pagenbr="p[@class='pagenumber']", remove_tags=[]):
    """
    NOT CURRENTLY USED in OPAS (2020-09-14)
    
    First converts XML to HTML (if not passed in html) then returns the
    html between the given page break numbers (default <p[@class=pagebreak]>).
    However, the page breaks must be at the same level in the HTML, e.g.,
    not buried under DIVS
    
    xml doesn't work consistently well for this, because page breaks can occur at many different levels,
    so it's possible the XML retrieved is not well formed.
    
    The pages are returned in the first entry of a tuple: an 'envelope', default <body></body> tag, an 'envelope' of sorts.
    The xml element list is returned as the second entry of the tuple
    if there's an error ("", []) is returned.
    
    If offset is not specified, it's 1 by default (first page)
    If limit is not specified, it's 1 by default
    So if neither is specified, it should return everything in 'inside' up to the first 'pagebrk'
    
    >>> ret_tuple = xml_get_pages_html(test_html, 2, 1, env="html")
    >>> ret_tuple[0]
    '<html>\\n<p>text on page 7</p>\\n                  <div class="pagebreak">\\n                    <p class="pagenumber">7</p>\\n                  </div>\\n                  </html>\\n'
    >>> ret_tuple[2:]
    ('7', '7')
    
    # Test real instance, large SE
    >>> realxmlinst = xml_file_to_xmlstr(r"tstfiles/DoNotRedistribute/SE.006.R0007A(bKBD3).xml")
    >>> ret_tuple = xml_get_pages_html(realxmlinst, 1, 1, inside="div[@id='body']", env="html", remove_tags=["div[@id='front']"])
    >>> ret_tuple[0]
    '<html>\\n<head>\\n<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>\\n<title class="head title">Sigmund Freud: The Psychopathology of Everyday Life</title>\\n<link rel="stylesheet" type="text/css" href="pepepub.css"/>\\n</head>\\n</html>\\n'
    >>> ret_tuple[2:]
    ('vii', 'vii')

    >>> ret_tuple = xml_get_pages_html(realxmlinst, 2, 1, inside="div[@id='body']", env="html", remove_tags=["div[@id='front']"])
    >>> ret_tuple[0]
    '<html>\\n<div class="pagebreak" data-class="pb">\\n<a id="..." class="mods"/><p class="pagenumber">viii</p>\\n</div>\\n</html>\\n'
    >>> ret_tuple[2:]
    ('viii', 'viii')
    
    >>> ret_tuple = xml_get_pages_html(realxmlinst, 21, 3, inside="div[@id='body']", env="html", remove_tags=["div[@id='front']"])
    >>> ret_tuple[0][:99]
    '<html>\\n<p class="para" id="...">The chief importance however of the <i>aliquis</i> ...'
    >>> ret_tuple[2:]
    ('13', '15')
    """
    # notes:
    #  front matter div
    #    root.xpath(f"//body//div[@id='front']") #
    #  body div
    #    root.xpath(f"//body//div[@id='body']")
    #  xpath for first page (only material in body, which in the HTML includes the front matter div
    #    root.xpath(f"//body//p[@class='pagebreak'][1]/preceding-sibling::*")
    
    no_page_nbr = "npn"
    ret_val = ("", [], no_page_nbr, no_page_nbr)
    if offset == 0:
        logger.error("Bad page offset requested.  First offset is 0 instead of 1")
        offset = 1 # First offset is 1

    offset1 = offset - 1 # offset 2 is the second page, so from the first pb to the one before
    offset2 = offset1 + limit
    
    if isinstance(xmlorhtmlstr, bytes):
        xmlorhtmlstr = xmlorhtmlstr.decode("utf8")
        
    if re.match("\s*(\<!DOCTYPE html.*\>|\<html\>)", xmlorhtmlstr, re.IGNORECASE):
        htmlstr = xmlorhtmlstr
    else:
        htmlstr = xml_str_to_html(xmlorhtmlstr)
    
    try:
        root = lxml.html.fromstring(htmlstr)
    except Exception as e:
        msg = f"Error {e}: Could not parse HTML"
        logger.warning(msg)
        if show_dbg_messages: print (msg)
        root = None
        raise "Error"
    
    xml_remove_tags(root, remove_tags=remove_tags)
    
    if 1:
        try: # get first page break
            pb = root.xpath(f'//{inside}/{pagebrk}[{offset1+1}]') # for first page nbr, which is 1 pb after the offset1 since pb is at end of page
            if pb != []:
                #firstpbfrag  = etree.tostring(pb[0]).decode("utf8") + "\n"
                # make sure we were given the subelement spec
                if pagenbr is not None:
                    try:
                        pn_node = pb[0].xpath(pagenbr)[0]
                    except Exception as e:
                        # no page number
                        first_pn = no_page_nbr
                    else:
                        first_pn = pn_node.text_content()
            else:
                #firstpbfrag = ""
                first_pn = no_page_nbr
        except:
            #firstpbfrag = ""
            logger.warning(f"Could not get first pagebreak: {e}")
            
        try: # get second page break
            pb2 = root.xpath(f'//{inside}/{pagebrk}[{offset2}]')
            if pb2 != []:
                #secondpbfrag = etree.tostring(pb2[0]).decode("utf8") + "\n"
                if pagenbr is not None:
                    try:
                        pn2_node = pb2[0].xpath(pagenbr)[0]
                    except Exception as e:
                        # no page number
                        last_pn = no_page_nbr
                    else:
                        last_pn = pn2_node.text_content()
            else:
                #secondpbfrag = "" 
                last_pn = no_page_nbr
                
        except Exception as e:
            #secondpbfrag = ""
            logger.warning(f"Could not get ending pagebreak: {e}")
        
        # Now let's get the text between, or before, if offset1 == 0 (first break)
        if offset1 == 0: # get all tags before the first pb (offset passed in was 1)
            elem_list = root.xpath(f'//{inside}/{pagebrk}[{offset2}]/preceding::*')
            for n in reversed(elem_list):
                if n.getparent() in elem_list:
                    elem_list.remove(n)
        else: # get all content between offset1 and offset2
            # get list of elements between
            elem_list = xml_get_elements_between_element(root, inside=inside, between_element=pagebrk, offset1=offset1, offset2=offset2)
        
        new_html = f"<{env}>\n"
        # new_xml = f"<{env}>\n" + firstpbfrag  # we don't need to add this in anymore, we return the numbers
        for n in elem_list:
            try:
                frag = etree.tostring(n).decode("utf8") 
                new_html += frag
            except Exception as e:
                logger.warning(f"Error converting node: {e}")
                
        # add the last pb
        #new_xml += secondpbfrag
        # close the new xml string
        new_html += f"</{env}>\n"
        
        ret_val = (new_html, elem_list, first_pn, last_pn)

    return ret_val

def xml_get_elements_between_element(element_node, inside="*", between_element="pb", offset1=1, offset2=None):
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
    '<pb><n>3</n></pb>\\n                '
    
    """
    ret_val = []
    if offset1 is None:
        offset1 == 1

    if offset2 is None:
        offset2 = offset1 + 1

    path = f"//{inside}/*[preceding-sibling::{between_element}[{offset1}] and not (preceding-sibling::{between_element}[{offset2}])]" 
    try:
        ret_val = element_node.xpath(path)
    except Exception as e:
        logger.error(f"Problem ({e}) extracting xpath nodes: {xpath}")
    
    return ret_val
    
def xml_get_subelement_textsingleton(element_node, subelement_name, skip_tags=[], with_tail=False, encoding="unicode", default_return=""):
    """
    Get text-only underneath the subelement_name

    >>> root = etree.fromstring('<p>Another <b>random</b> paragraph with multiple <b>subelements</b><note>a <b>bold</b> note<ftnx>10</ftnx> about nothing</note></p>')

    >>> xml_get_subelement_textsingleton(root, "note", skip_tags=["ftnx"], default_return=None)
    'a bold note about nothing'

    >>> xml_get_subelement_textsingleton(root, "b", with_tail=False)
    'random'

    >>> root = etree.fromstring(test_xml)

    >>> xml_get_subelement_textsingleton(root, "author")
    'this is just authoring test stuff'
    """
    ret_val = default_return
    
    try:
        # go to subelement
        elem = element_node.find(subelement_name)
        if elem is not None:
            elemcopy = copy.deepcopy(elem)
            for tag_name in skip_tags:
                for node in elemcopy.iter(tag_name):
                    tail = node.tail
                    node.clear() # (keep_tail) # .remove(node)
                    node.tail = tail
                    
            # strip the tags
            ret_val = etree.tostring(elemcopy, method="text", with_tail=with_tail, encoding=encoding)
            # strip leading and trailing spaces
            try:
                ret_val = ret_val.strip()
            except Exception as e:
                logger.warning(f"Whitepsace strip error: {ret_val} {e}")

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
        node = element_node.find(subelement_name)
        if node is not None:
            ret_val = etree.tostring(node, with_tail=False, encoding="unicode")
            if ret_val == "":
                logger.debug(f"Element {subelement_name} was empty")
                ret_val = default_return
        else:
            logger.warning(f"Element {subelement_name} was not found")
            ret_val = default_return

    except Exception as err:
        logger.warning(err)
        ret_val = default_return

    return ret_val

def xml_fragment_text_only(xmlstr, default_return=""):
    """
    NOT CURRENTLY USED in OPAS (2020-09-14)

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
    try:
        ret_val = element_node.attrib.get(attr_name, default_return)
    except Exception as err:
        logger.warning(err)
        ret_val = default_return

    return ret_val

def xml_get_elements(element_node, xpath_def, default_return=list()):
    """
    NOT CURRENTLY USED in OPAS (2020-09-14)

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
    elif isinstance(ret_val, lxml.etree._Element):
        ret_val = etree.tostring(ret_val).decode("utf8")
        
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

def xml_string_to_text(xmlstr, default_return=None):
    if xmlstr is not None:
        xmlstr = remove_encoding_string(xmlstr)
        clearText = lhtml.fromstring(xmlstr)
        ret_val = clearText.text_content()
    else:
        ret_val = default_return
    return ret_val

#-----------------------------------------------------------------------------
def get_first_page_excerpt_from_doc_root(elem_or_xmlstr, ret_format="HTML"):
    """
    Extract an acceptable length excerpt for articles that don't have Abstracts.
    
    Note: for performance reasons, it's best practice to use this in the database
          load process rather than run-time excerpting.  (This is currently whats done.)
    """
    try:
        if isinstance(elem_or_xmlstr, lxml.etree._Element):
            xmlstr = etree.tostring(elem_or_xmlstr, encoding="unicode")        
        else:
            xmlstr = elem_or_xmlstr
    except Exception as err:
        logger.error(err)
        ret_val = None
        
    parser = etree.XMLParser(target = FirstPageCollector(skip_tags=["impx"]), resolve_entities=False)
    ret_val = etree.XML(xmlstr, parser=parser)        # doctest: +ELLIPSIS
    
    return ret_val

#-----------------------------------------------------------------------------
def xml_elem_or_str_to_excerpt(elem_or_xmlstr, transformer_name=opasConfig.TRANSFORMER_XMLTOTEXT_EXCERPT):
    """
    NOT CURRENTLY USED in OPAS (2020-09-14)

    Use xslt to extract a formatted excerpt
    """
    ret_val = None
    try:
        if isinstance(elem_or_xmlstr, list) and elem_or_xmlstr != "[]":
            elem_or_xmlstr = elem_or_xmlstr[0]
    except Exception as e:
        logger.error("Problem extracting full-text: ", e)

    if isinstance(elem_or_xmlstr, str):
        try:
            # make sure it's not HTML already
            if re.match("<!DOCTYPE html .*", elem_or_xmlstr, re.IGNORECASE):
                logger.error("Warning - Data is HTML already:", e)
            xmlstr = remove_encoding_string(elem_or_xmlstr)
            source_data = etree.fromstring(xmlstr)
        except Exception as e:
            # return this error, so it will be displayed (for now) instead of the document
            ret_val = f"<p align='center'>Sorry, due to an XML error, we cannot display this document right now.</p><p align='center'>Please report this to PEP.</p>  <p align='center'>XSLT Transform Error: {e}</p>"
            logger.error(ret_val)
            raise Exception(ret_val)
    else: # it's already etree (#TODO perhaps check?)
        source_data = elem_or_xmlstr

    if source_data is not None and source_data != "[]":
        try:
            #xslt_file = etree.parse(xslt_file)
            #xslt_transformer = etree.XSLT(xslt_file)
            transformer = g_transformer.transformers.get(transformer_name, None)
            # transform the doc or fragment
            transformed_data = transformer(source_data)
            
        except Exception as e:
            # return this error, so it will be displayed (for now) instead of the document
            ret_val = f"<p align='center'>Sorry, due to a transformation error, we cannot display this excerpt right now.</p><p align='center'>Please report this to PEP.</p>  <p align='center'>XSLT Transform Error: {e}</p>"
            logger.error(ret_val)
            ret_val = elem_or_xmlstr
            raise Exception(ret_val)
        else:
            ret_val = str(transformed_data)
            pb = re.match("(?P<excerpt>.*?\<p class=\"pb.*?\</p\>)", ret_val, re.DOTALL)
            if pb is not None:
                ret_val = pb.group("excerpt") + "</html>"
            else:
                logger.error("No page break in data to extract excerpt")
                   
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
                elem = etree.fromstring(elem_or_xmlstr.encode("utf8"), parser)
            else:
                elem = copy.copy(elem_or_xmlstr) # etree will otherwise change calling parm elem_or_xmlstr when stripping
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

def xml_xpath_with_default(element_node, xpath, default_return=None):
    ret_val = default_return
    try:
        ret_val = element_node.xpath(xpath)
        if ret_val is None or ret_val == []:
            ret_val = default_return
    except:
        logger.warning("xpath error")

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
        
    if ret_val is not None:
        ret_val = ret_val.strip()
        
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
        if ret_val == []:
            ret_val = default_return
        else:
            if isinstance(ret_val, list) and len(ret_val) > 0:
                ret_val = ret_val[0]
            ret_val = etree.tostring(ret_val, with_tail=False, encoding="unicode")
            try:
                ret_val = ret_val.strip()
            except Exception as e:
                logger.warning(f"Whitepsace strip error: {ret_val} {e}")
                
    except Exception as err:
        logger.error(err)

    return ret_val

def xml_xpath_return_xmlstringlist_withinheritance(element_node, xpath, default_return=list(), attr_to_find=None):
    """
    Return a list of tuples,
    
       (XML tagged strings, Attr_List)
    
    from the nodes in the specified xPath

    Example:
    strList = elementsToStrings(treeRoot, "//aut[@listed='true']")

    >>> root = etree.fromstring(test_xml)
    >>> stringList = xml_xpath_return_xmlstringlist_withinheritance(root, "//p")
    >>> len(stringList)
    8
    >>> stringList[0]
    '<p id="1">A random paragraph</p>'
    >>> xml_xpath_return_xmlstringlist_withinheritance(root, "pxxxx", None)  # check default return
    
    """
    ret_val = default_return
    working_list = []
    try:
        # lset = [(n, [m.attrib for m in n.iterancestors() if m.attrib != {}]) for n in element_node.xpath(xpath)]
        for node in element_node.xpath(xpath):
            if attr_to_find is not None:
                if node.attrib.get(attr_to_find, None):
                    # already have it
                    pass
                else:
                    for m in node.iterancestors():
                        if m.attrib.get(attr_to_find, None):
                            #  we have one
                            node.attrib[attr_to_find] = m.attrib[attr_to_find]
                            break

            working_list.append(node)

        if len(working_list) == 0:
            ret_val = default_return
        else:
            ret_val = [etree.tostring(n, with_tail=False, encoding="unicode") for n in working_list]
    except:
        ret_val = default_return
        
    return ret_val

def xml_xpath_return_xmlstringlist(element_node, xpath, default_return=list(), min_len=1):
    """
    Return a list of XML tagged strings from the nodes in the specified xPath
    
    Update (2020-04-20): Add min_len to offer rejection of words that are too short.

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
        # changed 20200420 to expand to loop for len test so etree.tostring doesn't have to be done twice
        # ret_val = [etree.tostring(n, with_tail=False, encoding="unicode") for n in element_node.xpath(xpath)]
        ret_val = []
        els = element_node.xpath(xpath)
        for n in els:
            nstr = etree.tostring(n, with_tail=False, encoding="unicode")
            if len(nstr) > min_len:
                ret_val.append(nstr)

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
        issue = f"({issue})"
    else:
        issue = ""
    
    if vol is not None:
        vol = f"({vol})"
    else:
        vol = ""
    
    if pgrg is not None:
        pgrg = f":{pgrg}"
    else:
        pgrg = ""
    
    if source_title is not None:
        source_title = f"{source_title}, "
    else:
        source_title = ""

    ret_format = ret_format.lower()

    try:
        s = opasConfig.running_head_fmts[ret_format]
        ret_val = s.format(pub_year=pub_year, source_title=source_title, vol=vol, issue=issue, pgrg=pgrg)
    except Exception as e:
        print (f"Exception: {e}")
        ret_val = f"({pub_year}). {source_title}{vol}{issue}{pgrg}"
        
    return ret_val
    
def xml_file_to_xmlstr(xml_file, remove_encoding=False, resolve_entities=True, dtd_validations=True):
    """
    Read XML file and convert it to an XML string, expanding all entities
    
    """
    parser = etree.XMLParser(resolve_entities=resolve_entities, dtd_validation=dtd_validations)
    try:
        doc_DOM = etree.parse(xml_file, parser=parser)
    except Exception as e:
        logger.error(f"Error reading XML file {xml_file}", e)
        ret_val = ""
    else:
        ret_val = etree.tostring(doc_DOM, pretty_print=True)
        ret_val = ret_val.decode("utf8")
        ret_val += "\n"
        
    if remove_encoding:
        ret_val = remove_encoding_string(ret_val)
    
    return ret_val

def xml_str_to_html(elem_or_xmlstr, transformer_name=opasConfig.TRANSFORMER_XMLTOHTML):
    """
    Convert XML to HTML per Doc level XSLT file configured as g_xslt_doc_transformer.
    
    >>> len(xml_str_to_html(elem_or_xmlstr=test_xml)) > 1000
    True
    >>> len(xml_str_to_html(elem_or_xmlstr=test_xml2)) > 1400
    True
    """
    ret_val = None
    if isinstance(elem_or_xmlstr, lxml.etree._Element):
        #xml_tree = elem_or_xmlstr
        xml_text = etree.tostring(elem_or_xmlstr).decode("utf8")
    else:
        xml_text = elem_or_xmlstr
        
    elem_or_xmlstr = None # just to free up memory
    
    # make sure it's not HTML already
    if re.match("<!DOCTYPE html.*>", xml_text, re.IGNORECASE):
        ret_val = xml_text
    else:
        try:
            if isinstance(xml_text, list) and xml_text != "[]":
                xml_text = xml_text[0]
        except Exception as e:
            logger.error("Problem extracting full-text: ", e)
            
        if xml_text is not None and xml_text != "[]":
            try:
                xml_text = remove_encoding_string(xml_text)
                parser = etree.XMLParser(resolve_entities=False)
                sourceFile = etree.XML(xml_text, parser=parser)
                #sourceFile = etree.fromstring(xml_text, remove_entities=False)
            except Exception as e:
                # return this error, so it will be displayed (for now) instead of the document
                ret_val = f"<p align='center'>Sorry, due to an XML error, we cannot display this document right now.</p><p align='center'>Please report this to PEP.</p>  <p align='center'>XSLT Transform Error: {e}</p>"
                logger.error(ret_val)
                print (f"Error processing this text: {xml_text}")
                if stop_on_exceptions:
                    raise Exception(ret_val)
            else:
                if xml_text is not None and xml_text != "[]":
                    try:
                        #xslt_doc_transformer_file = etree.parse(xslt_file)
                        #xslt_doc_transformer = etree.XSLT(xslt_doc_transformer_file)
                        transformer = g_transformer.transformers[transformer_name]
                        # transform the doc or fragment
                        transformed_data = transformer(sourceFile)
                    except KeyError as e:
                        if transformer is None:
                            logger.error(f"Selected Transformer: {transformer_name} not found ({e})")
                            if stop_on_exceptions:
                                raise Exception(ret_val)
                    except Exception as e:
                        # return this error, so it will be displayed (for now) instead of the document
                        ret_val = f"<p align='center'>Sorry, due to a transformation error, we cannot display this document right now.</p><p align='center'>Please report this to PEP.</p>  <p align='center'>XSLT Transform Error: {e}</p>"
                        logger.error(ret_val)
                        ret_val = xml_text
                        print (f"Error processing this text: {xml_text}.  Transformer: {transformer_name}")
                        if stop_on_exceptions:
                            raise Exception(ret_val)
                    else:
                        ret_val = str(transformed_data)
                        # do substitutes
                        ret_val = ret_val.replace("%24OPAS_IMAGE_URL;", APIURL + IMAGE_API_LINK)
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

def remove_glossary_impx(xmlstr):
    """
    Since there can be so many glossary impx's in the document, if they are not needed, remove them, reducing the size
    of the return data greatly, and cleaning the xml to the eye.

    >>> teststr = "<myxml>this <b>is <i>really</i></b> xml with term <impx type='TERM2'>big term</impx>.</myxml>"
    >>> remove_glossary_impx(teststr)
    '<myxml>this <b>is <i>really</i></b> xml with term big term.</myxml>\n'
    """
    root = xmlstr_to_etree(xmlstr)
    deltag ="xxyyzzdelme"
    for el in root.iterfind("//impx[@type='TERM2']"):
        el.tag = deltag
    etree.strip_tags(root, deltag)
    return etree.tostring(root, encoding="unicode", pretty_print=True)
    
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
                <p id="2" type="speech">Another random paragraph with impx <impx>contents</impx></p>
                <pb></pb>
                <p id="3">Another <b>random</b> paragraph</p>
                <p id="4">Another random paragraph</p>
                <p id="5">Another <b>random</b> paragraph <i>with</i> multiple <b>subelements</b></p>
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
                <pb><n>1</n></pb>
                <p id="2" type="speech">Another random paragraph</p>
                <p id="3">Another <b>random</b> paragraph</p>
                <grp>
                   <p>inside group</p>
                </grp>
                <pb><n>2</n></pb>
                <p id="4">Another random paragraph</p>
                <p id="5">Another <b>random</b> paragraph with multiple <b>subelements</b></p>
                <pb><n>3</n></pb>
                <p id="6">Another random paragraph</p>
                <pb><n>4</n></pb>
                <quote>blah blah</quote>
                <p id="7">Another <b>random</b> paragraph with multiple <b>subelements</b></p>
                <pb><n>5</n></pb>
                <p id="8">Another random paragraph</p>
                <quote>blah blah</quote>
                <p id="9">Another <b>random</b> paragraph with multiple <b>subelements</b></p>
                <p id="10">Another <b>random</b> paragraph with multiple <b>subelements</b></p>
              </test>
              """

    test_html = """
             <html>
                <div id='body'>
                  <p>text on page 6</p>
                  <div class='pagebreak'>
                    <p class='pagenumber'>6</p>
                  </div>
                  <p>text on page 7</p>
                  <div class='pagebreak'>
                    <p class='pagenumber'>7</p>
                  </div>
                  <p>text page 8</p>
                  <div class='pagebreak'>
                    <p class='pagenumber'>8</p>
                  </div>
                </div>
            </html>
    """
    test_html2 = """
              <html>
                <div>this is just authoring test stuff</div>
                <p id="1">A random paragraph</p>
                <div class='pagebreak><p class='pagenumber'>1</p></div>
                <p id="2" type="speech">Another random paragraph</p>
                <p id="3">Another <b>random</b> paragraph</p>
                <p class='grp'>
                   <p>inside group</p>
                </p>
                <div class='pagebreak><p class='pagenumber'>2</p></div>
                <p id="4">Another random paragraph</p>
                <p id="5">Another <b>random</b> paragraph with multiple <b>subelements</b></p>
                <div class='pagebreak><p class='pagenumber'>3</p></div>
                <p id="6">Another random paragraph</p>
                <div class='pagebreak><p class='pagenumber'>4</p></div>
                <p class='quote'>blah blah</p>
                <p id="7">Another <b>random</b> paragraph with multiple <b>subelements</b></p>
                <div class='pagebreak><p class='pagenumber'>5</p></div>
                <p id="8">Another random paragraph</p>
                <p class='quote'>blah blah</p>
                <p id="9">Another <b>random</b> paragraph with multiple <b>subelements</b></p>
                <p id="10">Another <b>random</b> paragraph with multiple <b>subelements</b></p>
                <div class='pagebreak><p class='pagenumber'>6</p></div>
              </test>
              """

    test_xml3 = xml_file_to_xmlstr("./tstfiles/IJP.051.0175A(bEXP_ARCH1).XML")
    
    if 0:
        page0 = xml_get_pages(test_xml3, 0, 1, inside="body", env="tes1")
        # print (page0[0][-33:])
        txt = page0[0][-33:]
        page0 = xml_get_pages(test_xml3, 1, 2, env="body")
        assert ("177" == page0[0][-22:-19])
        page0 = xml_get_pages(test_xml3, 2, 3, env="body")
        # print (page0[0][-33:])
        assert ("179" == page0[0][-22:-19])
        test_xml3 = xml_file_to_xmlstr("./tstfiles/IJP.043.0306A(bEXP_ARCH1).XML")
        page0 = xml_get_pages(test_xml3, 0, 1, inside="body", env="tes2")
        txt = page0[0][-33:]
        #assert ("306" == page0[0][-22:-19])
        # print (page0[0][-33:])
        
        # it doesn't work for page breaks inside a list, underneath body!!
        page0 = xml_get_pages(test_xml3, 1, 2, env="body")
        txt = page0[0][-33:]
        # print (page0[0][-33:])
        #assert ("308" == page0[0][-22:-19])
        page0 = xml_get_pages(test_xml3, 2, 3, env="body")
        # print (page0[0][-33:])
        #assert ("309" == page0[0][-22:-19])
    
    doctest.testmod(optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
    print ("All Tests Completed")
    sys.exit()


