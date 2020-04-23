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
    #2020.0423.1 Tweaked FirstPageCollector to remove words in the trailing sentence of the excerpt
                # to the preceding punctuation mark.
                


__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2020, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2020.0423.1"
__status__      = "Development"


import sys
sys.path.append('../libs')
sys.path.append('../config')

import re
import os
import os.path
import stdMessageLib
import logging
logger = logging.getLogger(__name__)
import copy
import urllib

import lxml
from lxml import etree
import lxml.html as lhtml
from localsecrets import APIURL, IMAGE_API_LINK

from ebooklib import epub
import opasConfig
from io import StringIO

show_dbg_messages = True
stop_on_exceptions = False

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
                    if show_dbg_messages: print (f"   ...Paragraph limit {self.para_limit} for excerpt reached. Para Count: {self.para_count}, Char Count: {self.char_count}")
                    self.close_up = True
    
                if self.char_count > self.char_limit:
                    if show_dbg_messages: print (f"   ...Character limit {self.char_limit} for excerpt reached or exceeded, at end of para. Para Count: {self.para_count}, Char Count: {self.char_count}.")
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
                            #print (self.doc[-80:])
                        else:
                            # not sure why this would be, don't do anything
                            print (google_safe2_list[-1])
                    
            self.doc += f"</{tag}>"
            if len(self.tag_stack) > 0:
                self.tag_stack.pop()
                
        if self.in_body and (tag == "pb" or tag == "p"):
            if not self.fini:
                if self.close_up:
                    self.in_body = False # skip the rest.
                    # print ("Closing Document!", self.tag_stack)
                    while len(self.tag_stack) > 0:
                        tag_to_close = self.tag_stack.pop()
                        self.doc += f"</{tag_to_close}>"
                        # print(f"Closed tag: {tag_to_close}")
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

def xml_get_pages(xmlstr, offset=0, limit=1, inside="body", env="body", pagebrk="pb"):
    """
    Return the xml between the given page breaks (default <pb>).
    
    The pages are returned in the first entry of a tuple: an 'envelope', default <body></body> tag, an 'envelope' of sorts.
    The xml element list is returned as the second entry of the tuple
    if there's an error ("", []) is returned.

    If offset is not specified, it's 1 by default (first page)
    If limit is not specified, it's 1 by default
    So if neither is specified, it should return everything in 'inside' up to the first 'pagebrk'
    
    >>> ret_tuple = xml_get_pages(test_xml2, 0, 1, inside="test", env="body")
    >>> ret_tuple[0]
    '<body>\\n<author role="writer">this is just authoring test stuff</author>\\n                \\n<p id="1">A random paragraph</p>\\n                \\n</body>\\n'
    
    >>> ret_tuple = xml_get_pages(test_xml2, 2, 1, inside="test", env="grp")
    >>> ret_tuple[0]
    '<grp>\\n<p id="4">Another random paragraph</p>\\n                \\n<p id="5">Another <b>random</b> paragraph with multiple <b>subelements</b></p>\\n                \\n<pb/>\\n                \\n</grp>\\n'

    >>> ret_tuple = xml_get_pages(test_xml2, 1, 1, inside="test", env="grp")
    >>> ret_tuple[0]
    '<grp>\\n<p id="2" type="speech">Another random paragraph</p>\\n                \\n<p id="3">Another <b>random</b> paragraph</p>\\n                \\n<grp>\\n                   <p>inside group</p>\\n                </grp>\\n                \\n<pb/>\\n                \\n</grp>\\n'

    """
    ret_val = ("", [])
    offset1 = offset
    offset2 = offset + limit
    
    if isinstance(xmlstr, str):
        try:
            xmlstr = xmlstr.replace("encoding=\'UTF-8\'", "")
            root = etree.parse(StringIO(xmlstr))
        except Exception as e:
            logging.error(f"Error parsing xmlstr: {e}")
    elif etree.iselement(xmlstr):
        root = xmlstr
    else:
        logging.error("Unknown type to xml_get_pages: ", type(xmlstr))
        
    if 1:
        if offset1 == 0: # get all tags before offset2
            elem_list = root.xpath(f'//{inside}/{pagebrk}[{offset2}]/preceding-sibling::*')
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

def xml_get_pages_html(xmlorhtmlstr, offset=0, limit=1, inside="body", env="body", pagebrk="pb"):
    """
    Return html between the given page breaks (default <pb>).
    
    xml doesn't work consistently well for this, because page breaks can occur at many different levels,
    so it's possible the XML retrieved is not well formed.
    
    The pages are returned in the first entry of a tuple: an 'envelope', default <body></body> tag, an 'envelope' of sorts.
    The xml element list is returned as the second entry of the tuple
    if there's an error ("", []) is returned.

    If offset is not specified, it's 1 by default (first page)
    If limit is not specified, it's 1 by default
    So if neither is specified, it should return everything in 'inside' up to the first 'pagebrk'
    
    >>> html = b'<html>\n<head>\n\n<title class="head title">W. Bion: The Psycho-Analytic Study of Thinking</title>\n<link rel="stylesheet" type="text/css" href="pepepub.css">\n</head>\n<body><div class="pepkbd3">\n<div id="idm1504897640-front" class="front">\n<p class="banner"><a class="anchor" name="IJP.043.0306A" id="IJP.043.0306A"></a><a class="toc-link" href="/#/ArticleList/?journal=IJP"><img src="./images/bannerIJPLogo.gif" alt=""></a></p>\n<div class="pubinfotop">[[RunningHead]]</div>\n<div id="idm1504897640-artinfo" class="artinfo" data-arttype="ART" data-journal="IJP">\n<p class="title arttitle"><a href="/#/ArticleList/?journal=IJP&amp;vol=43&amp;page=306">The Psycho-Analytic Study of Thinking</a></p>\n<div class="artauth"><div class="authorwrapper title_author">\n<span><span class="title_author" data-listed="true" data-authindexid="Bion, W. R." data-role="author" data-alias="false" data-asis="false"><a class="author" href="#/Search/?author=Bion,%20W.%20R.">\n<span class="nfirst" data-type="FIRST" data-initials="">W.</span> <span class="nlast">Bion</span></a></span>\r</span> <span class="peppopup newauthortip"><img src="images/infoicon.gif" width="13" height="12" alt="Author Information"><div class="peppopuptext" id="autaffinfo" hidden="True"><p><span class="author">\n<span class="nfirst" data-type="FIRST" data-initials="">W.</span> <span class="nlast">Bion</span></span></p><div class="autaff" data-affid=""><div class="addr autaffaddr">\n<p class="ln">W. R. Bion</p>\n<p class="ln">LONDON</p>\n</div></div></div></span>\n</div></div>\n</div>\n</div>\n<div id="idm1504897640-body" class="body">\n<h1 text-align="">\n<a id="idm1505161704" class="mods"></a>II. A Theory of Thinking<sup><span class="ftnx" data-type="PG" data-r="F00001">1</span></sup>\n</h1>\n<p class="para" id="idm1505156072"></p><p class="first" id="idm1505161320">i.In this paper I am primarily concerned to present a theoretical system.  Its resemblance to a philosophical theory depends on the fact that philosophers have concerned themselves with the same <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001s.YN0015186348230" data-grpname="SUBJECT">subject</span>-matter; it differs from philosophical theory in that it is intended, like all psycho-analytical theories, for use.  It is devised with the intention that practising psycho-analysts should restate the hypotheses of which it is composed in terms of empirically verifiable data.  In this respect it bears the same relationship to similar statements of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0017868339590" data-grpname="PHILOSOPHY">philosophy</span> as the statements of applied <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001m.YP0020560229590" data-grpname="MATHEMATICS">mathematics</span> bear to pure <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001m.YP0020560229590" data-grpname="MATHEMATICS">mathematics</span>.</p><p class="para" id="idm1505028840">The derived hypotheses that are intended to admit of empirical test, and to a lesser extent the theoretical system itself, bear the same relationship to the observed facts in a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0004507089640" data-grpname="Psycho-Analysis; PSYCHOANALYSIS">psycho-analysis</span> as statements of applied <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001m.YP0020560229590" data-grpname="MATHEMATICS">mathematics</span>, say about a mathematical circle, bear to a statement about a circle drawn upon paper.</p><p class="first" id="idm1505023336">ii.This theoretical system is intended to be applicable in a significant number of cases; psycho-analysts should therefore experience realizations that approximate to the theory.</p><p class="para" id="idm1505020520">I attach no diagnostic importance to the theory though I think it may be applicable whenever a disorder of thought is believed to exist.  Its diagnostic significance will depend upon the pattern formed by the constant conjunction of a number of theories of which this theory would be one.</p><p class="para" id="idm1505023080">It may help to explain the theory if I discuss the background of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001e.YN0010741056480" data-grpname="EMOTIONAL EXPERIENCE">emotional experience</span> from which it has been abstracted.  I shall do this in general terms without attempting scientific rigour.</p><p class="first" id="idm1505015656">iii.It is convenient to regard <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0007326625520" data-grpname="Thinking">thinking</span> as dependent on the successful outcome of two main mental developments.  The first is the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0008047204240" data-grpname="DEVELOPMENT">development</span> of thoughts.  They require an apparatus to cope with them.  The second <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0008047204240" data-grpname="DEVELOPMENT">development</span>, therefore, is of this apparatus that I shall provisionally call <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0007326625520" data-grpname="Thinking">thinking</span>.  I repeat&#151;<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0007326625520" data-grpname="Thinking">thinking</span> has to be called into <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001e.YP0017512081750" data-grpname="EXISTENCE">existence</span> to cope with thoughts.</p><p class="para" id="idm1505010920">It will be noted that this differs from any theory of thought as a product of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0007326625520" data-grpname="Thinking">thinking</span>, in that <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0007326625520" data-grpname="Thinking">thinking</span> is a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0008047204240" data-grpname="DEVELOPMENT">development</span> forced on the psyche by the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YP0015141392870" data-grpname="Pressure">pressure</span> of thoughts and not the other way round.  Psychopathological developments may be associated with either <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001s.YP0001821354950" data-grpname="STAGE; PHASE">phase</span> or both, that is, they may be related to a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0018233533600" data-grpname="BREAKDOWN">breakdown</span> in the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0008047204240" data-grpname="DEVELOPMENT">development</span> of thoughts, or a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0018233533600" data-grpname="BREAKDOWN">breakdown</span> in the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0008047204240" data-grpname="DEVELOPMENT">development</span> of the apparatus for \'<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0007326625520" data-grpname="Thinking">thinking</span>\' or dealing with thoughts, or both.</p><p class="first" id="idm1505000040">iv.\'Thoughts\' may be classified, according to the nature of their developmental <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001h.YN0016059068310" data-grpname="HISTORY">history</span>, as pre-conceptions, conceptions or thoughts, and finally concepts; concepts are named and therefore fixed conceptions or thoughts.  The <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span> is initiated by the conjunction of a pre-<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span> with a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YP0016310458970" data-grpname="Realization">realization</span>.  The pre-<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span> may be regarded as the analogue in <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0004507089640" data-grpname="Psycho-Analysis; PSYCHOANALYSIS">psycho-analysis</span> of Kant\'s concept of \'empty thoughts\'.  Psycho-analytically the theory that the infant has an inborn disposition corresponding to an expectation of a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0013849098190" data-grpname="BREAST">breast</span> may be used to supply a model.  When the pre-<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span> is brought into contact with a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YP0016310458970" data-grpname="Realization">realization</span> that approximates to it, the mental outcome is a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span>.  Put in another way, the pre-<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span> (the inborn expectation of a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0013849098190" data-grpname="BREAST">breast</span>, the <i>a priori</i> <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001k.YP0010110936630" data-grpname="KNOWLEDGE">knowledge</span> of a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0013849098190" data-grpname="BREAST">breast</span>, the \'empty thought\') when the infant is brought in contact with the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0013849098190" data-grpname="BREAST">breast</span> itself, mates with awareness of the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YP0016310458970" data-grpname="Realization">realization</span> and is synchronous with the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0008047204240" data-grpname="DEVELOPMENT">development</span> of a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span>.  This model will serve for the theory that every junction of a pre-<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span> with its <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YP0016310458970" data-grpname="Realization">realization</span> produces a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span>.  Conceptions</p><p class="pb pagebreak"><a id="idm1504984168" class="mods"></a>\r</p><div class="footer above-border"><div class="ftn_group"><div class="ftn" id="@id" label="@label"><p class="ftn"><span class="ftnlabel"><sup>1</sup></span>Read at the 22nd International Psycho-Analytical Congress, Edinburgh, July-August, 1961.</p></div></div></div><p class="n pagenumber" data-nextpgnum="P0307">306</p><p class="p2 paracont" id="idm1504986984">therefore will be expected to be constantly conjoined with an emotional <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001e.YN0017014921470" data-grpname="Experience of Satisfaction">experience of satisfaction</span>.</p><p class="first" id="idm1504987880">v.I shall limit the term \'thought\' to the mating of a pre-<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span> with a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001f.YN0004958067340" data-grpname="Frustration">frustration</span>.  The model I propose is that of an infant whose expectation of a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0013849098190" data-grpname="BREAST">breast</span> is mated with a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YP0016310458970" data-grpname="Realization">realization</span> of no <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0013849098190" data-grpname="BREAST">breast</span> available for <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001s.YN0007535286680" data-grpname="SATISFACTION">satisfaction</span>.  This mating is experienced as a no-<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0013849098190" data-grpname="BREAST">breast</span>, or \'absent\' <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0013849098190" data-grpname="BREAST">breast</span> inside.  The next step depends on the infant\'s capacity for <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001f.YN0004958067340" data-grpname="Frustration">frustration</span>:  in particular it depends on whether the decision is to evade <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001f.YN0004958067340" data-grpname="Frustration">frustration</span> or to modify it.</p><p class="first" id="idm1504981096">vi.If the capacity for toleration of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001f.YN0004958067340" data-grpname="Frustration">frustration</span> is sufficient the \'no-<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0013849098190" data-grpname="BREAST">breast</span>\' inside becomes a thought, and an apparatus for \'<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0007326625520" data-grpname="Thinking">thinking</span>\' it develops.  This initiates the state, described by Freud in his \'Two Principles of Mental Functioning\', in which dominance by the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YN0014611118010" data-grpname="Reality Principle">reality principle</span> is synchronous with the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0008047204240" data-grpname="DEVELOPMENT">development</span> of an ability to think and so to bridge the gulf of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001f.YN0004958067340" data-grpname="Frustration">frustration</span> between the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001m.YP0001417964900" data-grpname="MOMENT">moment</span> when a want is felt and the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001m.YP0001417964900" data-grpname="MOMENT">moment</span> when <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001a.YN0005417015680" data-grpname="ACTION">action</span> appropriate to satisfying the want culminates in its <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001s.YN0007535286680" data-grpname="SATISFACTION">satisfaction</span>.  A capacity for tolerating <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001f.YN0004958067340" data-grpname="Frustration">frustration</span> thus enables the psyche to develop thought as a means by which the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001f.YN0004958067340" data-grpname="Frustration">frustration</span> that is tolerated is itself made more tolerable.</p><p class="first" id="idm1504962280">vii.If the capacity for toleration of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001f.YN0004958067340" data-grpname="Frustration">frustration</span> is inadequate, the bad internal \'no-<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0013849098190" data-grpname="BREAST">breast</span>\', that a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0021254895470" data-grpname="PERSONALITY; Personality Disorder">personality</span> capable of maturity ultimately recognizes as a thought, confronts the psyche with the need to decide between evasion of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001f.YN0004958067340" data-grpname="Frustration">frustration</span> and its modification.</p><p class="first" id="idm1504964072">viii.Incapacity for tolerating <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001f.YN0004958067340" data-grpname="Frustration">frustration</span> tips the scale in the direction of evasion of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001f.YN0004958067340" data-grpname="Frustration">frustration</span>.  The result is a significant departure from the events that Freud describes as characteristic of thought in the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001s.YP0001821354950" data-grpname="STAGE; PHASE">phase</span> of dominance of the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YN0014611118010" data-grpname="Reality Principle">reality principle</span>.  What should be a thought, a product of the juxtaposition of pre-<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span> and negative <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YP0016310458970" data-grpname="Realization">realization</span>, becomes a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YN0017605408200" data-grpname="BAD OBJECT">bad object</span>, indistinguishable from a thing-in-itself, fit only for evacuation.  Consequently the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0008047204240" data-grpname="DEVELOPMENT">development</span> of an apparatus for <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0007326625520" data-grpname="Thinking">thinking</span> is disturbed, and instead there takes place a hypertrophic <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0008047204240" data-grpname="DEVELOPMENT">development</span> of the apparatus of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014993008580" data-grpname="Projective Identification">projective identification</span>.  The model I propose for this <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0008047204240" data-grpname="DEVELOPMENT">development</span> is a psyche that operates on the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YP0017496848910" data-grpname="PLEASURE; UNPLEASURE PRINCIPLE">principle</span> that evacuation of a bad <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0013849098190" data-grpname="BREAST">breast</span> is synonymous with obtaining sustenance from a good <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0013849098190" data-grpname="BREAST">breast</span>.  The end result is that all thoughts are treated as if they were indistinguishable from bad internal objects; the appropriate machinery is felt to be, not an apparatus for <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0007326625520" data-grpname="Thinking">thinking</span> the thoughts, but an apparatus for ridding the psyche of accumulations of bad internal objects.  The crux lies in the decision between modification and evasion of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001f.YN0004958067340" data-grpname="Frustration">frustration</span>.</p><p class="first" id="idm1504946792">ix.Mathematical elements, namely straight lines, points, circles, and something corresponding to what later become known by the name of numbers, derive from realizations of two-ness as in <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0013849098190" data-grpname="BREAST">breast</span> and infant, two eyes, two feet, and so on.</p><p class="first" id="idm1504949352">x.If tolerance of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001f.YN0004958067340" data-grpname="Frustration">frustration</span> is not too great, modification becomes the governing aim.  <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0008047204240" data-grpname="DEVELOPMENT">Development</span> of mathematical elements, or mathematical objects as Aristotle calls them, is analogous to the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0008047204240" data-grpname="DEVELOPMENT">development</span> of conceptions.</p><p class="first" id="idm1504945640">xi.If intolerance of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001f.YN0004958067340" data-grpname="Frustration">frustration</span> is <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0008846383800" data-grpname="DOMINANT">dominant</span>, steps are taken to evade <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0010827467910" data-grpname="PERCEPTION">perception</span> of the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YP0016310458970" data-grpname="Realization">realization</span> by destructive attacks.  In so far as pre-<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span> and <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YP0016310458970" data-grpname="Realization">realization</span> are mated, mathematical conceptions are formed, but they are treated as if in-distinguishable from things-inthemselves and are evacuated at high speed as missiles to annihilate space.  In so far as space and time are perceived as identical with a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YN0017605408200" data-grpname="BAD OBJECT">bad object</span> that is destroyed, that is to say a no-<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0013849098190" data-grpname="BREAST">breast</span>, the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YP0016310458970" data-grpname="Realization">realization</span> that should be mated with the pre-<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span> is not available to complete the conditions necessary for the formation of a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span>.  The dominance of protective <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001i.YP0016277282680" data-grpname="Identification">identification</span> confuses the distinction between <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0002234623310" data-grpname="The Self">the self</span> and the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001e.YN0017873467890" data-grpname="EXTERNAL OBJECT">external object</span>.  This contributes to the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001a.YN0004427752900" data-grpname="ABSENCE">absence</span> of any <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0010827467910" data-grpname="PERCEPTION">perception</span> of two-ness, since such an awareness depends on the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YN0015354734460" data-grpname="RECOGNITION">recognition</span> of a distinction between <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001s.YN0015186348230" data-grpname="SUBJECT">subject</span> and <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001o.YN0004676559070" data-grpname="Object">object</span>.</p><p class="first" id="idm1504929128">xii.The relationship with time was graphically brought home to me by a patient who said over and over again that he was wasting time&#151;and continued to waste it.  The patient\'s aim is to destroy time by wasting it.  The consequences are illustrated in the description in <i>Alice in Wonderland</i> of the Mad Hatter\'s tea-party&#151;it is always four o\'clock.</p><p class="first" id="idm1504920168">xiii.Inability to tolerate <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001f.YN0004958067340" data-grpname="Frustration">frustration</span> can obstruct the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0008047204240" data-grpname="DEVELOPMENT">development</span> of thoughts and a capacity to think, though a capacity to think would diminish the sense of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001f.YN0004958067340" data-grpname="Frustration">frustration</span> intrinsic to appreciation of the gap between a wish and its fulfilment.  Conceptions, that is to say the outcome of a mating between a pre-<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span> and its <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YP0016310458970" data-grpname="Realization">realization</span>, repeat in a more <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0011849881830" data-grpname="Complex">complex</span> form the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001h.YN0016059068310" data-grpname="HISTORY">history</span> of pre-<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span>.  A <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span> does not necessarily meet a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YP0016310458970" data-grpname="Realization">realization</span> that approximates sufficiently closely to satisfy.  If <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001f.YN0004958067340" data-grpname="Frustration">frustration</span> can be tolerated, the mating of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span> and realizations whether negative or positive initiates</p><p class="pb pagebreak"><a id="idm1504912232" class="mods"></a></p><p class="n pagenumber" data-nextpgnum="P0308">307</p><p class="p2 paracont" id="idm1504914152">procedures necessary to learning by experience.  If intolerance of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001f.YN0004958067340" data-grpname="Frustration">frustration</span> is not so great as to activate the mechanisms of evasion and yet is too great to bear dominance of the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YN0014611118010" data-grpname="Reality Principle">reality principle</span>, the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0021254895470" data-grpname="PERSONALITY; Personality Disorder">personality</span> develops <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001o.YN0019667860580" data-grpname="Omnipotence">omnipotence</span> as a substitute for the mating of the pre-<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span>, or <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span>, with the negative <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YP0016310458970" data-grpname="Realization">realization</span>.  This involves the assumption of omniscience as a substitute for learning from experience by aid of thoughts and <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0007326625520" data-grpname="Thinking">thinking</span>.  There is therefore no psychic activity to discriminate between true and false.  Omniscience substitutes for the discrimination between true and false a dictatorial affirmation that one thing is morally right and the other wrong.  The assumption of omniscience that denies <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YN0014605906430" data-grpname="REALITY">reality</span> ensures that the morality thus engendered is a function of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YP0013026678540" data-grpname="Psychosis">psychosis</span>.  Discrimination between true and false is a function of the non-psychotic part of the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0021254895470" data-grpname="PERSONALITY; Personality Disorder">personality</span> and its factors.  There is thus potentially a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0004220765300" data-grpname="CONFLICT; INTRAPSYCHIC CONFLICT">conflict</span> between assertion of truth and assertion of moral ascendancy.  The extremism of the one infects the other.</p><p class="first" id="idm1504906856">xiv.Some pre-conceptions relate to expectations of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0002234623310" data-grpname="The Self">the self</span>.  The pre-conceptual apparatus is adequate to realizations that fall in the narrow range of circumstances suitable for the survival of the infant.  One circumstance that <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001a.YP0005740675060" data-grpname="AFFECT; AFFECTS">affects</span> survival is the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0021254895470" data-grpname="PERSONALITY; Personality Disorder">personality</span> of the infant himself.  Ordinarily the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0021254895470" data-grpname="PERSONALITY; Personality Disorder">personality</span> of the infant, like other elements in the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001e.YP0011127177600" data-grpname="ENVIRONMENT">environment</span>, is managed by the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001m.YN0010769193550" data-grpname="MOTHER">mother</span>.  If the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001m.YN0010769193550" data-grpname="MOTHER">mother</span> and <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YP0007842646530" data-grpname="Child">child</span> are adjusted to each other, <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014993008580" data-grpname="Projective Identification">projective identification</span> plays a major role in the management; the infant is able through the operation of a rudimentary <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YN0014605906430" data-grpname="REALITY">reality</span> sense to behave in such a way that <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014993008580" data-grpname="Projective Identification">projective identification</span>, usually an omnipotent <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001f.YN0010700504210" data-grpname="Fantasy; Phantasy">phantasy</span>, is a realistic phenomenon.  This, I am inclined to believe, is its normal condition.  When Klein speaks of \'excessive\' <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014993008580" data-grpname="Projective Identification">projective identification</span> I think the term \'excessive\' should be understood to apply not to the frequency only with which <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014993008580" data-grpname="Projective Identification">projective identification</span> is employed but to excess of belief in <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001o.YN0019667860580" data-grpname="Omnipotence">omnipotence</span>.  As a <i>realistic</i> activity it shows itself as behaviour reasonably calculated to arouse in the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001m.YN0010769193550" data-grpname="MOTHER">mother</span> feelings of which the infant wishes to be rid.  If the infant feels it is dying it can arouse fears that it is dying in the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001m.YN0010769193550" data-grpname="MOTHER">mother</span>.  A well-balanced <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001m.YN0010769193550" data-grpname="MOTHER">mother</span> can accept these and respond therapeutically:  that is to say in a manner that makes the infant feel it is receiving its frightened <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0021254895470" data-grpname="PERSONALITY; Personality Disorder">personality</span> back again, but in a form that it can tolerate&#151;the fears are manageable by the infant <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0021254895470" data-grpname="PERSONALITY; Personality Disorder">personality</span>.  If the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001m.YN0010769193550" data-grpname="MOTHER">mother</span> cannot tolerate these projections the infant is reduced to continue <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014993008580" data-grpname="Projective Identification">projective identification</span> carried out with increasing force and frequency.  The increased force seems to denude the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0000469822530" data-grpname="Projection">projection</span> of its penumbra of meaning.  Reintrojection is affected with similar force and frequency.  Deducing the patient\'s feelings from his behaviour in the consulting room and using the deductions to form a model, the infant of my model does not behave in a way that I ordinarily expect of an adult who is <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0007326625520" data-grpname="Thinking">thinking</span>.  It behaves as if it felt that an <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001i.YN0004868362550" data-grpname="INTERNAL OBJECT">internal object</span> has been built up that has the characteristics of a greedy vagina-like \'<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0013849098190" data-grpname="BREAST">breast</span>\' that strips of its goodness all that the infant receives or gives, leaving only degenerate objects.  This <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001i.YN0004868362550" data-grpname="INTERNAL OBJECT">internal object</span> starves its host of all understanding that is made available.  In analysis such a patient seems unable to <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001g.YP0006494278780" data-grpname="GAIN; PRIMARYGain; Secondary">gain</span> from his <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001e.YP0011127177600" data-grpname="ENVIRONMENT">environment</span> and therefore from his analyst.  The consequences for the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0008047204240" data-grpname="DEVELOPMENT">development</span> of a capacity for <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0007326625520" data-grpname="Thinking">thinking</span> are serious; I shall describe only one, namely, precocious <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0008047204240" data-grpname="DEVELOPMENT">development</span> of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0004696678820" data-grpname="Consciousness">consciousness</span>.</p><p class="first" id="idm1489818472">xv.By <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0004696678820" data-grpname="Consciousness">consciousness</span> I mean in this context what Freud described as a \'sense-organ for the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0010827467910" data-grpname="PERCEPTION">perception</span> of psychic qualities\'.</p><p class="para" id="idm1489821672">I have described previously (at a Scientific Meeting of the British Psycho-Analytical <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001s.YP0018559636030" data-grpname="Society">Society</span>) the use of a concept of \'<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001a.YP0003258700910" data-grpname="Alpha Function; Alpha Elements; Beta Elements">alpha-function</span>\' as a working tool in the analysis of disturbances of thought.  It seemed convenient to suppose an <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001a.YP0003258700910" data-grpname="Alpha Function; Alpha Elements; Beta Elements">alpha-function</span> to convert sense data into alpha-elements and thus provide the psyche with the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001m.YN0018787855710" data-grpname="Material">material</span> for <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0010931565630" data-grpname="DREAMS; DREAMING">dream</span> thoughts, and hence the capacity to wake up or go to sleep, to be <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0005451837790" data-grpname="CONSCIOUS">conscious</span> or <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001u.YP0013420666620" data-grpname="Unconscious">unconscious</span>.  According to this theory <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0004696678820" data-grpname="Consciousness">consciousness</span> depends on <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001a.YP0003258700910" data-grpname="Alpha Function; Alpha Elements; Beta Elements">alpha-function</span>, and it is a logical necessity to suppose that such a function exists if we are to assume that <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0002234623310" data-grpname="The Self">the self</span> is able to be <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0005451837790" data-grpname="CONSCIOUS">conscious</span> of itself in the sense of knowing itself from experience of itself.  Yet the failure to establish, between infant and <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001m.YN0010769193550" data-grpname="MOTHER">mother</span>, a relationship in which normal <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014993008580" data-grpname="Projective Identification">projective identification</span> is possible precludes the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0008047204240" data-grpname="DEVELOPMENT">development</span> of an <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001a.YP0003258700910" data-grpname="Alpha Function; Alpha Elements; Beta Elements">alpha-function</span> and therefore of a differentiation of elements into <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0005451837790" data-grpname="CONSCIOUS">conscious</span> and <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001u.YP0013420666620" data-grpname="Unconscious">unconscious</span>.</p><p class="first" id="idm1490045288">xvi.The difficulty is avoided by restricting the term \'<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0004696678820" data-grpname="Consciousness">consciousness</span>\' to the meaning conferred on it by Freud\'s definition.  Using the term \'<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0004696678820" data-grpname="Consciousness">consciousness</span>\' in this restricted sense it is possible to suppose that this <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0004696678820" data-grpname="Consciousness">consciousness</span> produces \'sense-data\' of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0002234623310" data-grpname="The Self">the self</span>, but that there is no <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001a.YP0003258700910" data-grpname="Alpha Function; Alpha Elements; Beta Elements">alpha-function</span> to convert them into alpha-elements and therefore permit of a capacity for</p><p class="pb pagebreak"><a id="idm1490035432" class="mods"></a></p><p class="n pagenumber" data-nextpgnum="P0309">308</p><p class="p2 paracont" id="idm1490035176"><span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YN0015659043440" data-grpname="BEING">being</span><span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0005451837790" data-grpname="CONSCIOUS">conscious</span> or <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001u.YP0013420666620" data-grpname="Unconscious">unconscious</span> of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0002234623310" data-grpname="The Self">the self</span>.  The infant <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0021254895470" data-grpname="PERSONALITY; Personality Disorder">personality</span> by itself is unable to make use of the sense data, but has to evacuate these elements into the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001m.YN0010769193550" data-grpname="MOTHER">mother</span>, relying on her to do whatever has to be done to convert them into a form suitable for employment as alpha-elements by the infant.</p><p class="first" id="idm1489977448">xvii.The limited <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0004696678820" data-grpname="Consciousness">consciousness</span> defined by Freud, that I am using to define a rudimentary infant <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0004696678820" data-grpname="Consciousness">consciousness</span>, is not associated with an <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001u.YP0013420666620" data-grpname="Unconscious">unconscious</span>.  All impressions of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0002234623310" data-grpname="The Self">the self</span> are of equal value; all are <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0005451837790" data-grpname="CONSCIOUS">conscious</span>.  The <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001m.YN0010769193550" data-grpname="MOTHER">mother</span>\'s capacity for <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YP0005273444210" data-grpname="REVERIE">reverie</span> is the receptor organ for the infant\'s harvest of self-sensation gained by its <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0005451837790" data-grpname="CONSCIOUS">conscious</span>.</p><p class="first" id="idm1489959528">xviii.A rudimentary <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0005451837790" data-grpname="CONSCIOUS">conscious</span> could not perform the tasks that we ordinarily regard as the province of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0004696678820" data-grpname="Consciousness">consciousness</span>, and it would be misleading to attempt to withdraw the term \'<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0005451837790" data-grpname="CONSCIOUS">conscious</span>\' from the sphere of ordinary usage where it is applied to mental functions of great importance in rational <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0007326625520" data-grpname="Thinking">thinking</span>.  For the present I make the distinction only to show what happens if there is a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0018233533600" data-grpname="BREAKDOWN">breakdown</span> of interplay through <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014993008580" data-grpname="Projective Identification">projective identification</span> between the rudimentary <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0004696678820" data-grpname="Consciousness">consciousness</span> and maternal <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YP0005273444210" data-grpname="REVERIE">reverie</span>.</p><p class="para" id="idm1489941608">Normal <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0008047204240" data-grpname="DEVELOPMENT">development</span> follows if the relationship between infant and <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0013849098190" data-grpname="BREAST">breast</span> permits the infant to project a feeling, say, that it is dying, into the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001m.YN0010769193550" data-grpname="MOTHER">mother</span> and to reintroject it after its sojourn in the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0013849098190" data-grpname="BREAST">breast</span> has made it tolerable to the infant psyche.  If the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0000469822530" data-grpname="Projection">projection</span> is not accepted by the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001m.YN0010769193550" data-grpname="MOTHER">mother</span> the infant feels that its feeling that it is dying is stripped of such meaning as it has.  It therefore reintrojects, not a fear of dying made tolerable, but a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001n.YN0016302920320" data-grpname="NAMELESS DREAD">nameless dread</span>.</p><p class="first" id="idm1489937128">xix.The tasks that the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0018233533600" data-grpname="BREAKDOWN">breakdown</span> in the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001m.YN0010769193550" data-grpname="MOTHER">mother</span>\'s capacity for <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YP0005273444210" data-grpname="REVERIE">reverie</span> have left unfinished are imposed on the rudimentary <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0004696678820" data-grpname="Consciousness">consciousness</span>; they are all in different degrees related to the function of correlation.</p><p class="first" id="idm1489923432">xx.The rudimentary <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0004696678820" data-grpname="Consciousness">consciousness</span> cannot carry the burden placed on it.  The establishment internally of a projective-<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001i.YP0016277282680" data-grpname="Identification">identification</span>-rejecting-<span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001o.YN0004676559070" data-grpname="Object">object</span> means that instead of an understanding <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001o.YN0004676559070" data-grpname="Object">object</span> the infant has a wilfully misunderstanding <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001o.YN0004676559070" data-grpname="Object">object</span>&#151;with which it is identified.  Further its psychic qualities are perceived by a precocious and fragile <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0004696678820" data-grpname="Consciousness">consciousness</span>.</p><p class="first" id="idm1489914344">xxi.The apparatus available to the psyche may be regarded as fourfold:</p><p class="first" id="idm1489909480"><span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0007326625520" data-grpname="Thinking">Thinking</span>, associated with modification and evasion.</p><p class="first" id="idm1489908712"><span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014993008580" data-grpname="Projective Identification">Projective identification</span>, associated with evasion by evacuation and not to be confused with normal <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014993008580" data-grpname="Projective Identification">projective identification</span> (par. 14 on \'realistic\' <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014993008580" data-grpname="Projective Identification">projective identification</span>.)</p><p class="first" id="idm1489899880">Omniscience (on the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YP0017496848910" data-grpname="PLEASURE; UNPLEASURE PRINCIPLE">principle</span> of <i>tout savoir tout condamner</i>).</p><p class="first" id="idm1489892328"><span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0000606445570" data-grpname="COMMUNICATION">Communication</span>.</p>\n<p class="first" id="idm1489892200">xxii.Examination of the apparatus I have listed under these four heads shows that it is designed to deal with thoughts, in the broad sense of the term, that is including all objects I have described as conceptions, thoughts, <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0010931565630" data-grpname="DREAMS; DREAMING">dream</span> thoughts, alpha-elements and <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YN0020584909960" data-grpname="BETA ELEMENTS">beta-elements</span>, as if they were objects that had to be dealt with (<i>a</i>) because they in some form <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0007336649800" data-grpname="CONTAINER; CONTAINED; Containing">contained</span> or expressed a problem, and (<i>b</i>) because they were themselves felt to be undesirable excrescences of the psyche and required <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001a.YN0019477127470" data-grpname="ATTENTION">attention</span>, elimination by some means or other, for that reason.</p><p class="first" id="idm1489887848">xxiii.As expressions of a problem it is evident they require an apparatus designed to play the same part in bridging the gap between cognizance and appreciation of lack and <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001a.YN0005417015680" data-grpname="ACTION">action</span> designed to modify the lack, as is played by <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001a.YP0003258700910" data-grpname="Alpha Function; Alpha Elements; Beta Elements">alpha-function</span> in bridging the gap between sense-data and appreciation of sense-data.  (In this context I include the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0010827467910" data-grpname="PERCEPTION">perception</span> of psychic qualities as requiring the same treatment as sense-data.)  In other words just as sense-data have to be modified and worked on by <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001a.YP0003258700910" data-grpname="Alpha Function; Alpha Elements; Beta Elements">alpha-function</span> to make them available for <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0010931565630" data-grpname="DREAMS; DREAMING">dream</span> thoughts, etc., so the thoughts have to be worked on to make them available for translation into <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001a.YN0005417015680" data-grpname="ACTION">action</span>.</p><p class="first" id="idm1489870696">xxiv.Translation into <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001a.YN0005417015680" data-grpname="ACTION">action</span> involves publication, <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0000606445570" data-grpname="COMMUNICATION">communication</span>, and commonsense.  So far I have avoided discussion of these aspects of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0007326625520" data-grpname="Thinking">thinking</span>, although they are implied in the discussion and one at least was openly adumbrated; I refer to correlation.</p><p class="first" id="idm1490915400">xxv.Publication in its origin may be regarded as little more than one function of thoughts, namely making sense-data available to <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0004696678820" data-grpname="Consciousness">consciousness</span>.  I wish to reserve the term for operations that are necessary to make private awareness, that is awareness that is private to the individual, public.  The problems involved may be regarded as technical and emotional.  The emotional problems are associated with the fact that the human individual is a political animal and cannot find fulfilment outside a group, and cannot satisfy any emotional <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0005442939990" data-grpname="DRIVE">drive</span> without expression of its social <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0015997845160" data-grpname="COMPONENT">component</span>.  His impulses, and I mean all impulses and not merely his sexual ones, are at the same time narcissistic.  The problem is the resolution of the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0004220765300" data-grpname="CONFLICT; INTRAPSYCHIC CONFLICT">conflict</span> between <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001n.YP0004638686200" data-grpname="Narcissism">narcissism</span> and social-ism.  The technical</p><p class="pb pagebreak"><a id="idm1491084232" class="mods"></a></p><p class="n pagenumber" data-nextpgnum="P0310">309</p><p class="p2 paracont" id="idm1491082952">problem is that concerned with expression of thought or <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014788201080" data-grpname="PRECONCEPTION; CONCEPTION">conception</span> in <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001l.YP0019468699420" data-grpname="LANGUAGE">language</span>, or its counterpart in signs.</p><p class="first" id="idm1491067464">xxvi.This brings me to <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0000606445570" data-grpname="COMMUNICATION">communication</span>.  In its origin <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0000606445570" data-grpname="COMMUNICATION">communication</span> is effected by realistic <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0014993008580" data-grpname="Projective Identification">projective identification</span>.  The primitive infant procedure undergoes various vicissitudes, including, as we have seen, debasement through hypertrophy of omnipotent <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001f.YN0010700504210" data-grpname="Fantasy; Phantasy">phantasy</span>.  It may develop, if the relationship with the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001b.YP0013849098190" data-grpname="BREAST">breast</span> is good, into a capacity for toleration by <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001t.YP0002234623310" data-grpname="The Self">the self</span> of its own psychic qualities and so pave the way for <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001a.YP0003258700910" data-grpname="Alpha Function; Alpha Elements; Beta Elements">alpha-function</span> and normal thought.  But it does also develop as a part of the social capacity of the individual.  This <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0008047204240" data-grpname="DEVELOPMENT">development</span>, of great importance in group dynamics, has received virtually no <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001a.YN0019477127470" data-grpname="ATTENTION">attention</span>; its <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001a.YN0004427752900" data-grpname="ABSENCE">absence</span> would make even scientific <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0000606445570" data-grpname="COMMUNICATION">communication</span> impossible.  Yet its <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YP0016733341930" data-grpname="PRESENCE">presence</span> may arouse feelings of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0009843100040" data-grpname="Persecution">persecution</span> in the recipients of the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0000606445570" data-grpname="COMMUNICATION">communication</span>.  The need to diminish feelings of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001p.YN0009843100040" data-grpname="Persecution">persecution</span> contributes to the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001d.YP0005442939990" data-grpname="DRIVE">drive</span> to abstraction in the formulation of scientific communications.  The function of the elements of <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0000606445570" data-grpname="COMMUNICATION">communication</span>, words and signs, is to convey either by single substantives, or in verbal groupings, that certain phenomena are constantly conjoined in the pattern of their relatedness.</p><p class="first" id="idm1490956104">xxvii.An important function of communications is to achieve correlation.  While <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0000606445570" data-grpname="COMMUNICATION">communication</span> is still a private function, conceptions, thoughts, and their verbalization are necessary to facilitate the conjunction of one set of sense-data with another.  If the conjoined data harmonize, a sense of truth is experienced, and it is desirable that this sense should be given expression in a statement analogous to a truth-functional statement.  The failure to bring about this conjunction of sense-data, and therefore of a commonplace view, induces a mental state of debility in the patient as if starvation of truth was somehow analogous to alimentary starvation.  The truth of a statement does not imply that there is a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YP0016310458970" data-grpname="Realization">realization</span> approximating to the true statement.</p><p class="first" id="idm1490946120">xxviii.We may now consider further the relationship of rudimentary <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0004696678820" data-grpname="Consciousness">consciousness</span> to psychic quality.  The emotions fulfil for the psyche a function similar to that of the senses in <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YN0013074626040" data-grpname="RELATION">relation</span> to objects in space and time:  that is to say, the counterpart of the commonsense view in private <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001k.YP0010110936630" data-grpname="KNOWLEDGE">knowledge</span> is the common emotional view; a sense of truth is experienced if the view of an <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001o.YN0004676559070" data-grpname="Object">object</span> which is hated can be conjoined to a view of the same <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001o.YN0004676559070" data-grpname="Object">object</span> when it is loved, and the conjunction confirms that the <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001o.YN0004676559070" data-grpname="Object">object</span> experienced by different emotions is the same <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001o.YN0004676559070" data-grpname="Object">object</span>.  A correlation is established.</p><p class="first" id="idm1487530952">xxix.A similar correlation, made possible by bringing <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001c.YN0005451837790" data-grpname="CONSCIOUS">conscious</span> and <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001u.YP0013420666620" data-grpname="Unconscious">unconscious</span> to bear on the phenomena of the consulting room, gives to psycho-analytic objects a <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001r.YN0014605906430" data-grpname="REALITY">reality</span> that is quite unmistakable even though their very <span class="peppopup glosstip impx" data-type="TERM2" data-docid="ZBK.069.0001e.YP0017512081750" data-grpname="EXISTENCE">existence</span> has been disputed.</p>\n\n<p class="pb pagebreak"><a id="idm1487526088" class="mods"></a></p><p class="n pagenumber">310</p>\n</div>\n</div></body>\n<div id="putciteashere"></div>\n</html>' 
    >>> ret_tuple = xml_get_pages_html(html, 0, 1, inside="test", env="html")
    
    >>> ret_tuple[0]
    '<body>\\n<author role="writer">this is just authoring test stuff</author>\\n                \\n<p id="1">A random paragraph</p>\\n                \\n</body>\\n'
    
    >>> ret_tuple = xml_get_pages(test_xml2, 2, 1, inside="test", env="grp")
    >>> ret_tuple[0]
    '<grp>\\n<p id="4">Another random paragraph</p>\\n                \\n<p id="5">Another <b>random</b> paragraph with multiple <b>subelements</b></p>\\n                \\n<pb/>\\n                \\n</grp>\\n'

    >>> ret_tuple = xml_get_pages(test_xml2, 1, 1, inside="test", env="grp")
    >>> ret_tuple[0]
    '<grp>\\n<p id="2" type="speech">Another random paragraph</p>\\n                \\n<p id="3">Another <b>random</b> paragraph</p>\\n                \\n<grp>\\n                   <p>inside group</p>\\n                </grp>\\n                \\n<pb/>\\n                \\n</grp>\\n'

    """
    ret_val = ("", [])
    offset1 = offset
    offset2 = offset + limit

    if re.match("<!DOCTYPE html.*>", xmlorhtmlstr, re.IGNORECASE):
        htmlstr = xmlorhtmlstr
    else:
        htmlstr = xml_str_to_html(xmlorhtmlstr)
    
    try:
        root = lxml.html.fromstring(htmlstr)
    except Exception as e:
        print (f"Error {e}: Could not parse HTML")
        root = None
        raise "Error"
    
    if 1:
        if offset1 == 0: # get all tags before offset2
            elem_list = root.xpath(f'//{inside}/{pagebrk}[{offset2}]/preceding-sibling::*')
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
        logging.error(f"Problem ({e}) extracting xpath nodes: {xpath}")
    
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
        elemcopy = copy.deepcopy(elem)
        for tag_name in skip_tags:
            for node in elemcopy.iter(tag_name):
                tail = node.tail
                node.clear() # (keep_tail) # .remove(node)
                node.tail = tail
                
        # strip the tags
        ret_val = etree.tostring(elemcopy, method="text", with_tail=with_tail, encoding=encoding)
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
    try:
        ret_val = element_node.attrib.get(attr_name, default_return)
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

def xml_string_to_text(xmlstr, default_return=""):
    xmlstr = remove_encoding_string(xmlstr)
    clearText = lhtml.fromstring(xmlstr)
    ret_val = clearText.text_content()
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
def old_get_first_page_excerpt_from_doc_root(root, ret_format="HTML"):
    ret_val = ""
    # extract the first MAX_PARAS_FOR_SUMMARY paras
    #ret_val = force_string_return_from_various_return_types(xml_document)
    #ret_val = remove_encoding_string(ret_val)
    #parser = lxml.etree.XMLParser(encoding='utf-8', recover=True)                
    #root = etree.parse(StringIO(ret_val), parser)
    body = root.xpath("//*[self::h1 or self::p or self::p2 or self::pb]")
    count = 0
    for elem in body:
        if elem.tag == "pb" or count >= opasConfig.MAX_PARAS_FOR_SUMMARY:
            # we're done.
            ret_val  += etree.tostring(elem, encoding='utf8').decode('utf8')
            ret_val = "%s%s%s" % ("<abs><unit type='excerpt'>", ret_val, "</unit></abs>")
            break
        else:
            # count paras
            if elem.tag == "p" or elem.tag == "p2":
                count += 1
            ret_val  += etree.tostring(elem, encoding='utf8').decode('utf8')
    
    
    if ret_val == "" or len(ret_val) > opasConfig.DEFAULT_LIMIT_FOR_EXCERPT_LENGTH:
        # do it another way...convert to mostly text, so we can find pb
        ret_val = xml_elem_or_str_to_excerpt(root)
    else:
        transformer = g_transformer.transformers.get(opasConfig.TRANSFORMER_XMLTOHTML, None)
        if transformer is not None:
            # transform the doc or fragment
            # wrap it.
            root = etree.fromstring(f"<div class='excerpt'>{ret_val}</div>")
            ret_val = transformer(root)
            ret_val = etree.tostring(ret_val)
            ret_val = ret_val.decode("utf8")

    return ret_val
#-----------------------------------------------------------------------------
def xml_iterate_tree(elemtree):
    for n in elemtree.iter():
        pass

#-----------------------------------------------------------------------------
def xml_elem_or_str_to_excerpt(elem_or_xmlstr, transformer_name=opasConfig.TRANSFORMER_XMLTOTEXT_EXCERPT):
    """
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
            xmlstr = remove_encoding_string(xmlstr)
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
                elem = etree.fromstring(elem_or_xmlstr, parser)
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
        logging.warning("xpath error")

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
        
    ret_val = f"({pub_year}). {source_title}{vol}{issue}{pgrg}"
    return ret_val
    
def add_headings_to_abstract_html(abstract, source_title=None, pub_year=None, vol=None, issue=None, pgrg=None, title="", author_mast="", citeas=None, ret_format="HTML"):
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

def xml_str_to_html(elem_or_xmlstr, transformer_name=opasConfig.TRANSFORMER_XMLTOHTML):
    """
    Convert XML to HTML per Doc level XSLT file configured as g_xslt_doc_transformer.
    
    >>> len(xml_str_to_html(elem_or_xmlstr=test_xml))
    1081
    >>> len(xml_str_to_html(elem_or_xmlstr=test_xml2))
    1454
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
                print (xml_text)
                if stop_on_exceptions:
                    raise Exception(ret_val)
            else:
                if xml_text is not None and xml_text != "[]":
                    try:
                        #xslt_doc_transformer_file = etree.parse(xslt_file)
                        #xslt_doc_transformer = etree.XSLT(xslt_doc_transformer_file)
                        transformer = g_transformer.transformers.get(transformer_name, None)
                        # transform the doc or fragment
                        transformed_data = transformer(sourceFile)
                    except Exception as e:
                        # return this error, so it will be displayed (for now) instead of the document
                        ret_val = f"<p align='center'>Sorry, due to a transformation error, we cannot display this document right now.</p><p align='center'>Please report this to PEP.</p>  <p align='center'>XSLT Transform Error: {e}</p>"
                        logger.error(ret_val)
                        ret_val = xml_text
                        print (xml_text)
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
    assert ("309" == page0[0][-22:-19])
    doctest.testmod()
    print ("All Tests Completed")
    sys.exit()


