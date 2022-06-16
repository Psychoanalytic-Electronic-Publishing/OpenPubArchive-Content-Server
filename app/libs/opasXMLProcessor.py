#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
""" 
OPAS - XML Builder/Update Library

Update function to process a keyed/converted XML file for data needed to load into Solr, for runtime use.

Can optionally
- write to XML output build (e.g., EXP_ARCH1)
- Load directly into Solr/RDS without writing the EXP_ARCH1 processed file.
    
"""
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2022, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2022.0613" 
__status__      = "Development"

programNameShort = "opasXMLProcessor"
XMLProcessingEnabled = True

import logging
logger = logging.getLogger(programNameShort)

import lxml
import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

import opasXMLHelper as opasxmllib

#from opasFileSupport import FileInfo
import PEPAuthorID
import modelsOpasCentralPydantic
from opasLocator import Locator
import opasGenSupportLib as opasgenlib
import PEPBookInfo
import PEPAuthorID 
import PEPGlossaryRecognitionEngine
import opasSolrLoadSupport

glossEngine = PEPGlossaryRecognitionEngine.GlossaryRecognitionEngine(gather=False)

dbgVerbose = False
#----------------------------------------------------------------------------------------------------------------
def pgnbr_add_next_attrib(pepxml):
    """
    Walk through page number "n" elements, and record page number sequence.  Add the next page number to
       the nextpgnum attribute of the n element.
    """

    # Walk through page number "n" elements, and record page number sequence
    n_nodes = pepxml.findall("**/n")
    lastPage = None
    count = 0
    # walk through the nodes backwards.
    for node in n_nodes[::-1]: # backwards
        pgNumber = node.text
        if lastPage is not None:
            node.set("nextpgnum", lastPage)
            count += 1
        # record the new pagenumber for the next node
        lastPage = pgNumber # .format()

    return count

#------------------------------------------------------------------------------------------------------
def xml_update(root, pepxml, artInfo, ocd):
    ret_val = None
    # write issn and id to artinfo
    xml_artinfo = pepxml.find("artinfo")
    source_row = ocd.get_sources(src_code=artInfo.src_code)
    known_books = PEPBookInfo.PEPBookInfo()

    try:
        source_info = source_row[1][0]
        # gather info needed about source
        if artInfo.src_code is not None:
            if artInfo.art_issn is None:
                xml_artinfo.attrib["ISSN"] = source_info["ISSN"]
            else:
                if artInfo.art_issn is not None:
                    xml_artinfo.attrib["ISSN"] = artInfo.art_issn
                else:
                    if artInfo.art_isbn is None:
                        xml_artinfo.attrib["ISBN"] = source_info["ISBN-13"]
                    else:
                        xml_artinfo.attrib["ISBN"] = artInfo.art_isbn

    except Exception as e:
        print (e)
    
    if artInfo.art_id is not None: xml_artinfo.set("id", artInfo.art_id)
    if artInfo.art_type is not None: xml_artinfo.set("arttype", artInfo.art_type)
    if artInfo.start_sectname is not None: xml_artinfo.set("newsecnm", artInfo.start_sectname)
    if artInfo.start_sectlevel is not None: xml_artinfo.set("newseclevel", artInfo.start_sectlevel)                
    xml_artauth = pepxml.findall("artinfo/artauth")
    for art_auth in xml_artauth:
        art_auth.set("hidden", art_auth.get("hidden", "false"))

    xml_artauth_aut = pepxml.findall("artinfo/artauth/aut")
    for aut in xml_artauth_aut:
        # print(aut)
        if aut.attrib.get("authindexid", None) is None:
            author_id = PEPAuthorID.getStandardAuthorID(nfirst=aut.findtext("nfirst"), nmid=aut.findtext("nmid"), nlast=aut.findtext("nlast"))
            aut.set("authindexid", author_id)
            # set default attributes if not seet
            aut.set("listed", aut.get("listed", "true"))
            aut.set("role", aut.get("role", "author"))
        
        ## write authindexid to aut
        #if opasgenlib.is_empty(artInfo.art_author_id_list):
            #for n in artInfo.author_list:
                #author_id = PEPAuthorID.getStandardAuthorID(n)
                #print (f"author_id: {author_id}")
        #else:
            #print (artInfo.art_author_id_list)
    
    # tag glossary words
    
    # add nextpgnum with id to n, possibly filling in prefixused
    pgnbr_add_next_attrib(pepxml)
    
    # add links to biblio entries, rx to be
    if artInfo.ref_count > 0:
        bibReferences = pepxml.xpath("/pepkbd3//be")  # this is the second time we do this (also in artinfo, but not sure or which is better per space vs time considerations)
        logger.info(("   ...Processing %s references for links." % (artInfo.ref_count)))

        #processedFilesCount += 1
        bib_total_reference_count = 0
        #db_ok = ocd.open_connection(caller_name="processBibliographies")
        for ref in bibReferences:
            # bib_entry_text = ''.join(ref.itertext())
            bib_pgstart = None
            bib_pgend = None
            ref_id = ref.attrib["id"]
            # see if it's already in table
            bib_saved_entry_tuple = ocd.get_references_from_biblioxml_table(article_id=artInfo.art_id, ref_local_id=ref_id)
            if bib_saved_entry_tuple is not None:
                bib_saved_entry = bib_saved_entry_tuple[0]
            else:
                bib_saved_entry = modelsOpasCentralPydantic.Biblioxml()
            
            # merge record info
            bib_total_reference_count += 1
            bib_entry = opasSolrLoadSupport.BiblioEntry(artInfo, ref)
            if not opasgenlib.is_empty(bib_entry.pgrg):
                bib_pgstart, bib_pgend = bib_entry.pgrg.split("-")

            bk_locator = None
            if bib_entry.source_type != "book":
                if not opasgenlib.is_empty(bib_entry.sourcecode):
                    locator = Locator(strLocator=None,
                                       jrnlCode=bib_entry.sourcecode, 
                                       jrnlVolSuffix="", 
                                       jrnlVol=bib_entry.volume, 
                                       jrnlIss=None, 
                                       pgVar="A", 
                                       pgStart=bib_pgstart, 
                                       jrnlYear=bib_entry.year, 
                                       localID=ref_id, 
                                       keepContext=1, 
                                       forceRoman=False, 
                                       notFatal=True, 
                                       noStartingPageException=True, 
                                       filename=artInfo.filename)
                    # need to check if it's whole, and if it works, but for now.
                    ref.attrib["rx"] = locator.articleID()
                    search_str = f"//be[@id='{ref_id}']"
                    if dbgVerbose:
                        print(f"Matched Journal {opasxmllib.xml_xpath_return_xmlstringlist(pepxml, search_str)[0]}")
                else:
                    locator = None
                    logger.info("Skipped: ", bib_saved_entry)
                
            else:
                bk_locator_str, match_val, whatever = known_books.getPEPBookCodeStr(bib_entry.ref_entry_text)
                if bk_locator_str is not None:
                    ref.attrib["rx"] = bk_locator_str 
                    search_str = f"//be[@id='{ref_id}']"
                    if dbgVerbose:
                        print(f"Matched Book {match_val}. {opasxmllib.xml_xpath_return_xmlstringlist(pepxml, search_str)[0]}")
                    
                else:
                    locator = None
                    logger.debug("Skipped: ", bib_entry.ref_entry_text)

        #try:
            #ocd.db.commit()
        #except mysql.connector.Error as e:
            #print("SQL Database -- Biblio Commit failed!", e)
        #if db_ok:
            #ocd.close_connection(caller_name="processBibliographies")
    

    # xml_artauth = pepxml.findall("artinfo/artauth/aut")
    root, pepxml, result_text = glossEngine.doGlossaryMarkup(root)
    
    ret_val = root, pepxml, result_text
    return ret_val

