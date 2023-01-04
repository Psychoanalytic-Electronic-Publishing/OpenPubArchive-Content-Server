#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
# Disable many annoying pylint messages, warning me about variable naming for example.
# yes, in my Solr code I'm caught between two worlds of snake_case and camelCase.

""" 
OPAS - opasEmbargoContent - Can remove the content of an article and replace with a
                            message based on the Embargo type during XML compilation.
                            
                            This is, for example, required by some RFP files, e.g.,
                            RFP.026.0353A.EMBARGOED(bKBD3).xml

"""
import sys
sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')

import logging
logger = logging.getLogger(__name__)
from loggingDebugStream import log_everywhere_if

import lxml
from lxml import etree
import lxml.etree as ET

def embargo_check(artInfo, parsed_xml, verbose=False):
    # Check if the file is embargoed, and eliminate embargoed sections
    if artInfo.embargotype is not None:
        embargotype = artInfo.embargotype.lower()
        if embargotype == "abstractonly" or embargotype == "restricted" or embargotype == "withdrawn":
            node = parsed_xml.xpath("//body")
            if node:
                parent = node[0].getparent()
                parent.replace(node[0], ET.fromstring("<body></body>"))
            
            node = parsed_xml.xpath("//bib")
            if node:
                parent = node[0].getparent()
                parent.replace(node[0], ET.fromstring("<bib/>"))
            
            node = parsed_xml.xpath("//appxs")
            if node:
                parent = node[0].getparent()
                parent.replace(node[0], ET.fromstring("<appxs/>"))

            ET.strip_elements(parsed_xml, 'ftnx')
    
        if embargotype == "withdrawn" or embargotype == "restricted":
            ET.strip_elements(parsed_xml, 'abs')
            ET.strip_elements(parsed_xml, 'summaries')
    
        # add message to instance
        if embargotype == "abstractonly" or embargotype == "restricted" or embargotype == "withdrawn":
            PUBMESSAGE = "<body><p>This article has been %s by the publisher.<pb><n>%s</n></pb></p></body>"
            if embargotype == "withdrawn":
                # message different
                newNode = etree.fromstring(PUBMESSAGE % ("withdrawn", artInfo.art_pgstart))
            else:
                newNode = etree.fromstring(PUBMESSAGE % ("embargoed", artInfo.art_pgstart))
    
            node = parsed_xml.xpath("//body")
            if node:
                parent = node[0].getparent()
                parent.replace(node[0], newNode)
    
        # log it
        if embargotype == "abstractonly":
            errmsg = "This article is tagged as abstractonly.  All content OTHER THAN the abstract and summaries removed"
            log_everywhere_if(verbose, "info", errmsg)
        elif embargotype == "restricted":
            errmsg = "This article is tagged as EMBARGOED RESTRICTED.  All content removed"
            log_everywhere_if(verbose, "info", errmsg)
        elif embargotype == "withdrawn":
            errmsg = "This article is tagged as EMBARGOED WITHDRAWN.  All content removed"
            log_everywhere_if(verbose, "info", errmsg)
        elif embargotype == "excerpted":
            errmsg = f"ATTENTION: need to move {artInfo.art_id} to PEPCurrent "
            log_everywhere_if(verbose, "warning", errmsg)
            print (errmsg)
            print (errmsg)
            print (errmsg)
            print (errmsg)
            print (errmsg)
            print (errmsg)

