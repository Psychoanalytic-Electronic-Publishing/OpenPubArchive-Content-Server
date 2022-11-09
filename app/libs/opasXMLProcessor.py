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
__version__     = "2022.0926/v.1.0.101"  # recorded in xml processed pepkbd3 procby
__status__      = "Development"

programNameShort = "opasXMLProcessor"
XMLProcessingEnabled = True

gDbg1 = False # display errors on stdout
gDbg2 = False # processing details

import logging
logger = logging.getLogger(programNameShort)

from loggingDebugStream import log_everywhere_if    # log as usual, but if first arg is true, also put to stdout for watching what's happening

import lxml.etree as ET
import sys
import re

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

import opasXMLHelper as opasxmllib

#from opasFileSupport import FileInfo
import opasXMLPEPAuthorID
import models
import opasLocator
from opasLocator import Locator
import opasGenSupportLib as opasgenlib
import opasSolrLoadSupport
import PEPBookInfo
import opasXMLPEPAuthorID 
import PEPGlossaryRecognitionEngine
import opasXMLSplitBookSupport  # Module not done and may not be needed.
import opasLocalID
import opasPySolrLib

import opasConfig
import opasDocuments
import PEPJournalData

glossEngine = PEPGlossaryRecognitionEngine.GlossaryRecognitionEngine(gather=False)
max_display_len_cf_articles = 90

#----------------------------------------------------------------------------------------------------------------
def add_page_number_markup(parsed_xml):
    """
    Walk through page number "n" elements, and record page number sequence.  Add the next page number to
       the nextpgnum attribute of the n element.
    """

    nodes = parsed_xml.xpath("//n")
    ret_val = len(nodes)

    if gDbg2: print("\t...Adding Page Number Attributes")

    lastPage = None
    
    # Walk through page number "n" elements in reverse, and record page number sequencing
    for node in reversed(nodes):
        n = node.text
        pg_number = opasDocuments.PageNumber(n)
        # record the new pagenumber for the next node
        if lastPage is not None:
            node.attrib["nextpgnum"] = lastPage

        lastPage = pg_number.format()

    return ret_val


#----------------------------------------------------------------------------------------------------------------
def normalize_local_ids(parsed_xml, verbose=False):
    
    nodes = parsed_xml.xpath("//be | //binc | //note | //ftn")
    ret_val = len(nodes)

    global gDbg1, gDbg2
    if verbose:
        print ("\t...Normalizing local ids.")
    else:
        gDbg1 = False
        gDbg2 = False
    
    for node in nodes:
        noteid = node.attrib.get("id", None)
        if noteid is not None:
            nodeid_normal = str(opasLocalID.LocalID(noteid))
            if nodeid_normal != noteid and nodeid_normal != "":
                log_everywhere_if(gDbg2, level="info", msg=f"\t\t\t...Normalized id: {noteid} to {nodeid_normal}")
                node.attrib["id"] = nodeid_normal

    # return node count
    return ret_val

#----------------------------------------------------------------------------------------------------------------
def pgnbr_add_next_attrib(parsed_xml):
    """
    Walk through page number "n" elements, and record page number sequence.  Add the next page number to
       the nextpgnum attribute of the n element.
    """

    # Walk through page number "n" elements, and record page number sequence
    n_nodes = parsed_xml.findall("**/n")
    lastPage = None
    count = 0
    # walk through the nodes backwards.
    for node in n_nodes[::-1]: # backwards
        pgNumber = opasDocuments.PageNumber(node.text)
        if lastPage is not None:
            node.set("nextpgnum", lastPage)
            node.set("prefixused", lastPrefix)
            count += 1
        # record the new pagenumber for the next node
        lastPage = pgNumber.format()
        lastPrefix = pgNumber.pgPrefix

    return count

#------------------------------------------------------------------------------------------------------
def find_related_articles(ref, art_or_source_title, query_target="art_title_xml", max_words=opasConfig.MAX_WORDS, min_words=opasConfig.MIN_WORDS, word_len=opasConfig.MIN_WORD_LEN, max_cf_list=opasConfig.MAX_CF_LIST):
    """
    Search for related articles and add to rxcf of reference
    
    """
    # title is either bib_entry.art_title_xml or bib_entry.source_title
    ret_val = rxcf = []
    prev_rxcf = None
    title_words = re.findall(r'\b\w{%s,}\b' % word_len, art_or_source_title)[:max_words]
    if len(title_words) >= min_words:
        safe_title_words = " AND ".join(title_words)
        result = opasPySolrLib.search_text(query=f"{query_target}:({safe_title_words})", limit=10, offset=0, full_text_requested=False)
        if result[1][0] == 200:
            
            if gDbg2:
                title_list = [item.title for item in result[0].documentList.responseSet[0:max_cf_list]]
                if title_list != []:
                    print (f"\t\t\t...Article title first {len(title_words)} words of len {word_len} for search: {safe_title_words} from title:{art_or_source_title}")
                    for n in title_list:
                        print (f"\t\t\t\t...cf Article Title: {n[:max_display_len_cf_articles]}")
                        
            rxcf = [item.documentID for item in result[0].documentList.responseSet[0:max_cf_list]]
            try:
                prev_rxcf = ref.attrib["rxcf"]
            except Exception:
                pass

            if len(rxcf) > 0 and prev_rxcf is None:
                ref.attrib["rxcf"] = ",".join(rxcf)
                compare_to = f"\t\t\t...Journal title compare to: {ref.attrib['rxcf']}"
                log_everywhere_if(gDbg2, level="debug", msg=compare_to)
            elif prev_rxcf is not None:
                ref.attrib["rxcf"] = prev_rxcf + "," + ",".join(rxcf)
                compare_to = f"\t\t\t...Journal title compare to: {ref.attrib['rxcf']}"
                log_everywhere_if(gDbg2, level="debug", msg=compare_to)
                
        else:
            log_everywhere_if(gDbg1, level="debug", msg=result[1][1])
    elif gDbg2:
        print (f"\t\t\t...Skipped cf search (too few words): {title_words}")

    return ret_val
    
#------------------------------------------------------------------------------------------------------
def add_article_to_split_pages_table(ocd, parsed_xml, artInfo, remove_old=False, verbose=None):
    """
    WORK in PROGRESS - Converting from the OLD PEPXML
    
    Update the split pages table with this article instance from a split book
    
    """
    pep_split_book_data = opasXMLSplitBookSupport.SplitBookData(database_connection=ocd)
    art_id = artInfo.art_id
    article_locator = Locator(art_id )

    # Clear previous info about pages so we can refresh during parse/scan
    if remove_old:
        print (f"Removing split book page records from prior run for this instance: {art_id }")
        pep_split_book_data.delete_splitbook_page_records(art_id)

    # see if instance has a biblio
    #nodes = PYXTree.getElements(ALL, E("bib"))
    nodes = parsed_xml.xpath("/pepkbd3//bib")  
    if len(nodes)>0:
        has_biblio = 1
    else:
        has_biblio = 0

    if article_locator.isMainTOC:
        has_toc = 1
    else:
        has_toc = 0

    nodes = parsed_xml.xpath("//n")  
    # now add new ones
    for node in nodes:
        pg_number = node.text
        if pg_number != "":
            pg_number = opasDocuments.PageNumber(pg_number)
            #print "Split Book PageNumber/Instance Recorded: ", pgN, self.fullFilename
            pep_split_book_data.add_splitbook_page_record(artInfo.art_id,
                                                          pg_number.pageID(),
                                                          has_biblio=has_biblio,
                                                          has_toc=has_toc,
                                                          full_filename=artInfo.filename)
        else:
            print ("Warning!  Blank Page Number")

#------------------------------------------------------------------------------------------------------
def pgxPreProcessing(parsed_xml, ocd, artInfo, split_book_data=None, verbose=False):
    """
    WORK in PROGRESS - Converting from the OLD PEPXML
    
    Deal with the pgxs that go to articles.  Many do, and they rely on the bx entry just before the reference
    """
    global gDbg1, gDbg2
    if not verbose:
        gDbg1 = False
        gDbg2 = False
    
    bxRefR = ""
    bxRefRX = ""
    bibRef = None
    pgLink = None
    jrnlCode = artInfo.src_code
    vol = artInfo.art_vol_str
    aLoc = Locator(artInfo.art_id)

    #  PGX ATTRIBUTES OF INTEREST:
    #     r = Internal Biblio ID Only, if required above (Differs from other
    #             cross-refernces for this reason)
    #
    #     re = External Biblio LocalID, the biblio ID of the biblio record
    #             in a split book where the biblio is in an external instance.
    #             (While a bit awkward to have this separate, this allows the
    #              parser to enforce referential integrity for at least the internal ones).
    #
    #     rx = Full locator to page, if supplied, overrides any computed or implied ref

    # Walk through pgx elements, and fix locators
    split_book_data = opasXMLSplitBookSupport.SplitBookData(database_connection=ocd)
    pgx_links = parsed_xml.xpath("/pepkbd3//pgx")
    if verbose:
        print(f"\t...Processing page links. {len(pgx_links)} pgx links found.")
        
    for pgx in pgx_links:
        # where are we
        #in_toc = pgx.xpath("ancestor::grp[@name='TOC']")
        pgxlink_type = "OTHER"
        #parentNameElem = pgx.getparent()
        grp_ancestor_list = pgx.xpath("ancestor::grp")
        if len(grp_ancestor_list) > 0:
            grp_ancestor = grp_ancestor_list[0]
            grp_type = grp_ancestor.attrib.get("name", None)
            if grp_type is not None:
                grp_type = grp_type.upper()
                if grp_type in ["TOC", "INDEX"]:
                    pgxlink_type = "INDEX" # for TOC or an INDEX
                else:
                    pgxlink_type = grp_type
            
        current_rx_link = pgx.attrib.get("rx", None)
            
        if current_rx_link is None: # otherwise, no need to do
            fulltext = opasxmllib.xml_elem_or_str_to_text(pgx) # x.find("pgx")
            fulltext_cleaned = fulltext.split("-")[0]
            fulltext_cleaned = opasgenlib.removeAllPunct(fulltext_cleaned)
            fulltext_cleaned = opasDocuments.PageNumber(fulltext_cleaned)
            fulltext_cleaned = fulltext_cleaned.format(keyword=fulltext_cleaned.LOCALID)
            split_inst_from_fulltext = split_book_data.get_splitbook_page_instance(book_code=jrnlCode, vol=vol, page_id=fulltext_cleaned)
            if split_inst_from_fulltext is None:
                splitLoc = opasLocator.Locator(jrnlCode=jrnlCode, jrnlVol=vol, pgStart="1", art_info=artInfo, ocd=ocd)
                local = splitLoc.localID(fulltext_cleaned).upper()
                pgx.attrib["rx"] = local
                pgx.attrib["type"] = pgxlink_type
                log_everywhere_if(gDbg2, level="info", msg=f"\t\t\t...Reference to non-Split Book. Set link (type={pgxlink_type}) including local to: {local}")
            else:
                splitLoc = opasLocator.Locator(split_inst_from_fulltext, ocd=ocd)
                #print (splitLoc, SEPage)
                local = splitLoc.localID(fulltext_cleaned).upper()
                pgx.attrib["rx"] = local
                pgx.attrib["type"] = pgxlink_type
                log_everywhere_if(gDbg2, level="info", msg=f"\t\t\t...Reference to Split Book. Set link (type={pgxlink_type}) including local to: {local}")
        else:
            log_everywhere_if(gDbg2, level="info", msg=f"\t\t\t...Rx link for pgx already set: {current_rx_link}")
 
    nodes = parsed_xml.xpath("/pepkbd3//bxe")
    for node in nodes:
        if node.tag == "bxe":
            fulltext = opasxmllib.xml_elem_or_str_to_text(node) # x.find("pgx")
            bxRefRX = node.attrib.get("rx", None)
            if bxRefRX is None:
                log_everywhere_if(gDbg2, level="warning", msg=f"\t\t\t...BXE tag {fulltext} found in {artInfo.art_id} without rx info.")
        
    ## update local ids for biblios if applicable
    #nodes = pepxml.xpath("/pepkbd3//bx|bxe")
    #for node in nodes:
        #if node.tag == "bx":
            #bxRefR = node.get("r")
            #bibRef = aLoc.localID(bxRefR, saveLocalID=True)
            #node.set("r", aLoc.getLocalID())
        #elif node.tag == "bxe":
            #bxRefRX = node.attrib.get("rx", None)
            #bibRef = aLoc.localID(bxRefRX, saveLocalID=True)
            #node.set("r", bibRef)
        
    #should not need to do pgx links here at all.      
    #nodes = pepxml.xpath("/pepkbd3//pgx|bx|bxe")
    if 0: # I don't think we need to do any of this anymore.  Delete in late July
        nodes = parsed_xml.xpath("/pepkbd3//bx|bxe")
        for node in nodes:
            if node.tag == "bx":
                bxRefR = node.get("r")
                # add articleID
                bibRef = aLoc.localID(bxRefR)
                bxRefRX = "" # forget the last one
                log_everywhere_if(gDbg2, level="info", msg=f"\t\t\t...bx r: {bxRefR} bibRef={bibRef}")
                continue	# until you find the next pgx
    
            elif node.tag == "bxe":
                bxRefRX = node.attrib.get("rx", None)
                log_everywhere_if(gDbg2, level="info", msg=f"\t\t\t...bx rxe: {bxRefRX}")
                bxRefR = "" # forget the last one
                continue	# until you find the next pgx
    
            else:	#pgx
                #bibRef = None # need this value sometimes, at least when not in an index.
                pgRefR = node.attrib.get("r", None)
                pgRefRX = node.attrib.get("rx", None)
                pgRefRE = node.attrib.get("re", None)
                pgxtype = node.attrib.get("type", None)
                if pgRefRX is not None:
                    continue
                else:        
                    log_everywhere_if(gDbg2, level="info", msg=f"\t\t\t...pgx r: {pgRefR}  rx: {pgRefRX} re: {pgRefRE} type: {pgxtype}")
                
                if pgxtype in ["BIBJUMP"]:
                    # don't link these
                    continue
                #elif pgxtype in ["INTERNAL", "EXTERNAL"]:
                    #linktype = pgxtype
    
                pgTextRaw = node.text
                if opasgenlib.isRoman(pgTextRaw):
                    pgText = pgTextRaw
                else:
                    pgText = opasgenlib.trimLeadingNonDigits(pgTextRaw)
    
                pgStart = opasDocuments.PageRange(pgText).pgStart
    
                pgLink = None
                pgLink1 = None
                pgLink2 = None
    
                # See if there's no marked reference link
                if opasgenlib.is_empty(pgRefRE) and opasgenlib.is_empty(pgRefRX) and opasgenlib.is_empty(pgRefR):
                    # Nothing Specified.  See what the last reference bx or bxe has, from previous loops.
                    log_everywhere_if(gDbg2, level="debug", msg="\t\t\t...No links in attributes.  See what the last reference bx or bxe has, from previous loops.")

                    msg="\t\t\t...As per 2022 process, the references in splits should already be tagged with the bibliography split instance and id"
                    if bibRef != None: # don't look for a reference if we're in the index!
                        # these split references are mostly and should be linked in the KBD3.  So for now, we don't do this anymore!
                        log_everywhere_if(gDbg2, level="warning", msg=msg)
    
                    # now see if it could also be internal... (if both, then we need to resolve ambiguity)
                    if artInfo.pgRange.contains(pgStart):
                        # this could be a reference to the curernt paper.
                        if aLoc.isSplitBook():
                            #localID looks up split book instance as long as biblioID is supplied
                            logger.warning()
                            log_everywhere_if(gDbg2, level="warning", msg=msg)
                        else:
                            # not a split book so page is internal
                            pgLink2 = aLoc.localID(pgStart)
                            msg = f"\t\t\t...PgxLink Calculated: {pgLink2}"
                            log_everywhere_if(gDbg2, level="info", msg=msg)
                    else:
                        if aLoc.isSplitBook():
                            #localID looks up split book instance as long as biblioID is supplied
                            #print ("Lookup splitbook page: ", pgStartStr)
                            # pgLink2 = aLoc.localID(pgStart, checkSplitInThisBiblioDB=PEPProcInst.biblioDB)
                            # for now using localid
                            pgLink2 = aLoc.localID(pgStart)
                            msg = f"\t\t\t...SplitBook. PgxLink cannot be calculated yet (TBD - needs to be computed).  Trying localID {pgLink2} for now."
                            log_everywhere_if(gDbg1, level="error", msg=msg)
                            
                        else:
                            # not a split book so page is internal
                            msg = "\t\t\t...pgStart: %s not in page range: %s-%s" % (pgStart, artInfo.art_pgstart, artInfo.art_pgend)
                            log_everywhere_if(gDbg2, level="warning", msg=msg)
    
                    if pgLink1 != None and pgLink2 != None:
                        # BOTH the prior match and the article are possible.
                        msg = "\t\t\t...WARNING: Both bx/bxe and internal linking (%s/%s) is possible with this page reference." % (pgLink1, pgLink2)
                        log_everywhere_if(gDbg2, level="warning", msg=msg)
                        # if it's not a book though, it's probably the external link that matters.
                        if artInfo.isBook:
                            # pick the internal
                            pgLink = pgLink2
                        else:
                            pgLink = pgLink1
                            # pick the external
                    elif pgLink2 != None:
                        #print ("\t\tLink is pgLink2: %s" % pgLink2)
                        pgLink = pgLink2
                    elif pgLink1 != None:
                        #print ("\t\tLink is pgLink1: %s" % pgLink1)
                        pgLink = pgLink1
                    else:
                        msg = "\t\t\t...No RE/RX/R attr specified, and no link found for pgx: %s within parent (%s)" % (pgTextRaw, node.getparent().tag)
                        log_everywhere_if(gDbg2, level="warning", msg=msg)
    
                    node.attrib["rx"] = pgLink
    
                else:
                    # one of those isn't empty.
                    target = ""
                    if not opasgenlib.is_empty(pgRefR):
                        # get link from this internal reference
                        target = "pgRefR"
                        bibRef = aLoc.localID(pgRefR)
                        msg = "\t\t\t...This may not be needed and thus is still in development.  Skipping link"
                        log_everywhere_if(gDbg2, level="error", msg=msg)
                        pgLink = None
                        # need update to use:
                        #pgLink = PEPSplitBookData.getBibEntryPageLink(bibRef, pageNumber=pgStart)
                    elif not opasgenlib.is_empty(pgRefRX):
                        # use this full reference, or if its already a page link, go with that.
                        target = "pgRefRX"
                        bibRef = pgRefRX
                        if opasLocator.isLocalIDPageRef(pgRefRX):
                            # go directly to it.
                            pgLink = pgRefRX
                        else:
                            # what to do with this
                            msg = f"\t\t\t...Can't resolve RX.  Bad link info in pgx... {pgRefRX}"
                            log_everywhere_if(gDbg2, level="error", msg=msg)
    
                    elif not opasgenlib.is_empty(pgRefRE): # external biblio locator
                        target = "pgRefRE" 
                        msg = "\t\t\t...pgRefRE empty - watch this.  This may not be needed and thus is still in development.  Skipping link"
                        log_everywhere_if(gDbg2, level="error", msg=msg)
                        pgLink = None
                        # need update to use:
                        #pgLink = PEPSplitBookData.getBibEntryPageLink(bibRef, pageNumber=pgStart) # may not be needed or appropritate
    
                    #else: # we shouldn't be here, so not test needed.
    
                    # we have our link
                    if pgLink != None:
                        msg = "\t\t\t...Setting Link to %s based on value that was in %s." % (pgLink, target)
                        log_everywhere_if(gDbg2, level="warning", msg=msg)
                        if not opasgenlib.is_empty(pgLink):
                            node.attrib["rx"] = pgLink
    
    
                # ok, if there was a pageref, it's handled, go to next pgx
                continue

    return

#------------------------------------------------------------------------------------------------------
def xml_update(parsed_xml, artInfo, ocd, pretty_print=False, verbose=False):
    
    ret_val = None
    ret_status = True

    global gDbg1, gDbg2
    if not verbose:
        gDbg1 = False
        gDbg2 = False
    #else:
        #print ("\t...Converting! Keyboarded XML to processed/precompiled XML.")
        
    # write issn and id to artinfo
    
    parsed_xml.attrib["procby"] = f"{programNameShort}.{__version__}"
    xml_artinfo = parsed_xml.find("artinfo")
    source_row = ocd.get_sources(src_code=artInfo.src_prodkey, get_counts=False)
    known_books = PEPBookInfo.PEPBookInfo()

    try:
        source_info = source_row[1][0]
        # gather info needed about source
        if artInfo.src_code is not None:
            if source_info["ISSN"] is not None:
                xml_artinfo.attrib["ISSN"] = source_info["ISSN"]
            else:
                if artInfo.art_issn is not None:
                    xml_artinfo.attrib["ISSN"] = artInfo.art_issn
                else:
                    # logic changed 2022-09-30 to prioritize existing isbn, and then isbn-10 from 
                    # the productbase (like the local process I ran)
                    if artInfo.art_isbn is not None:
                        xml_artinfo.attrib["ISBN"] = artInfo.art_isbn
                    elif source_info["ISBN-10"] is not None:
                        xml_artinfo.attrib["ISBN"] = source_info["ISBN-10"]
                    elif source_info["ISBN-13"] is not None:
                        xml_artinfo.attrib["ISBN"] = source_info["ISBN-13"]
                    else:
                        logger.warning(f"Source Code: {artInfo.src_code} but no ISSN or ISBN")

    except Exception as e:
        print (e)
    
    if artInfo.art_id is not None: xml_artinfo.set("id", artInfo.art_id)
    if artInfo.art_type is not None: xml_artinfo.set("arttype", artInfo.art_type)
    if artInfo.start_sectname is not None: xml_artinfo.set("newsecnm", artInfo.start_sectname)
    if artInfo.start_sectlevel is not None: xml_artinfo.set("newseclevel", artInfo.start_sectlevel)
    if artInfo.art_vol_suffix is not None:
        xml_artvol = parsed_xml.xpath("//artvol")
        if xml_artvol != []:
            artvol = xml_artvol[0]
            actual = str(artInfo.art_vol_int)
            artvol.attrib["actual"] = actual
            artvol.text = actual + artInfo.art_vol_suffix
            if verbose:
                print (f"\t...Volume suffix required: set in XML to {artvol.text} and attrib 'actual' to {actual}")

    artbkinfo = parsed_xml.xpath("//artbkinfo")
    if artbkinfo != []:
        artbkinfo = artbkinfo[0]
        artbkinfo_next = artbkinfo.attrib.get("next", None)
        artbkinfo_prev = artbkinfo.attrib.get("prev", None)
        artbkinfo_extract = artbkinfo.attrib.get("extract", None)
        
        if artbkinfo_next is not None:
            artbkinfo_next = str(opasLocator.Locator(artbkinfo_next))
            artbkinfo.set("next", artbkinfo_next)
        if artbkinfo_prev is not None:
            artbkinfo_prev = str(opasLocator.Locator(artbkinfo_prev))
            artbkinfo.set("prev", artbkinfo_prev)
        if artbkinfo_extract is not None:
            artbkinfo_extract = str(opasLocator.Locator(artbkinfo_extract))
            artbkinfo.set("extract", artbkinfo_extract)
        
    xml_artauth = parsed_xml.findall("artinfo/artauth")
    for art_auth in xml_artauth:
        art_auth.set("hidden", art_auth.get("hidden", "false"))

    xml_artauth_aut = parsed_xml.xpath("//aut")
    for aut in xml_artauth_aut:
        # print(aut)
        if aut.attrib.get("authindexid", None) is None:
            author_id = opasXMLPEPAuthorID.getStandardAuthorID(nfirst=aut.findtext("nfirst"), nmid=aut.findtext("nmid"), nlast=aut.findtext("nlast"))
            aut.set("authindexid", author_id)
            # set default attributes if not seet
            aut.set("listed", aut.get("listed", "true"))
            aut.set("role", aut.get("role", "author"))
        
        ## write authindexid to aut
        #if opasgenlib.is_empty(artInfo.art_author_id_list):
            #for n in artInfo.author_list: #author_id =
            #PEPAuthorID.getStandardAuthorID(n)
                #print (f"\t\tauthor_id: {author_id}")
        #else:
            #print (artInfo.art_author_id_list)
    
    nodes = parsed_xml.xpath("/pepkbd3//artkwds") # PYXTree.getElements(ALL, E("artkwds"), childSpec=E("impx"), notChild=1)
    # PYXTree.keywordListImpx = None
    for node in nodes:
        markedup_list = []
        keywords = node.text.split(",")
        if verbose:
            print (f"\t...Keyword markup added: {node.text}")
        count = len(keywords)
        for keyword in keywords:
            markup = f'<impx type="KEYWORD">{keyword.strip()}</impx>'
            markedup_list.append(markup)

        if count > 0:
            keyword_str = "".join(markedup_list)
            keywords = f"<artkwds>{keyword_str}</artkwds>"
            newnode = ET.XML(keywords)
            try:
                node.getparent().replace(node, newnode)
            except Exception as e:
                logger.warning(f"Can't replace artkwds node {e}")

    # normalize local ids
    # normalize_local_ids(parsed_xml, verbose=verbose)
    
    # add nextpgnum with id to n, possibly filling in prefixused
    pgnbr_add_next_attrib(parsed_xml)
    
    # add links to biblio entries, rx to be
    if artInfo.ref_count > 0:
        bibReferences = parsed_xml.xpath("/pepkbd3//be")  # this is the second time we do this (also in artinfo, but not sure or which is better per space vs time considerations)
        if verbose: print("\t...Examining %s references for links (rx) and related titles (rxcf)." % (artInfo.ref_count))
        #processedFilesCount += 1
        bib_total_reference_count = 0
        #db_ok = ocd.open_connection(caller_name="processBibliographies")
        for ref in bibReferences:
            # bib_entry_text = ''.join(ref.itertext())
            bib_pgstart = None
            bib_pgend = None
            # compare_to = ""
            ref_id = ref.attrib["id"]
            # see if it's already in table
            bib_saved_entry_tuple = ocd.get_references_from_biblioxml_table(article_id=artInfo.art_id, ref_local_id=ref_id)
            if bib_saved_entry_tuple is not None and bib_saved_entry_tuple != []:
                bib_saved_entry = bib_saved_entry_tuple[0]
            else:
                bib_saved_entry = models.Biblioxml()
            
            # merge record info
            bib_total_reference_count += 1
            bib_entry = opasSolrLoadSupport.BiblioEntry(artInfo, ref)
            try:
                if not opasgenlib.is_empty(bib_entry.pgrg):
                    bib_pgstart, bib_pgend = bib_entry.pgrg.split("-")
            except ValueError as e:
                if not opasgenlib.is_empty(bib_entry.pgrg):
                    bib_pgstart = bib_entry.pgrg
                    bib_pgend = bib_entry.pgrg
                else:
                    bib_pgstart = ""
                    bib_pgend = ""
                
            if bib_entry.source_type != "book": # journal or other
                if opasgenlib.is_empty(bib_entry.sourcecode):
                    if bib_entry.ref_title:
                        # find and store rxcf for related articles (side effect of function)
                        if gDbg2 and verbose: print (f"\t...Finding related articles for bibliography based on ref_title")
                        rxcf = find_related_articles(ref,
                                                     art_or_source_title=bib_entry.ref_title,
                                                     query_target="art_title_xml",
                                                     max_words=opasConfig.MAX_WORDS,
                                                     min_words=opasConfig.MIN_WORDS,
                                                     word_len=opasConfig.MIN_WORD_LEN,
                                                     max_cf_list=opasConfig.MAX_CF_LIST)
                    else:
                        locator = None
                        msg = f"\t\t\t...Skipped: {bib_saved_entry}"
                        log_everywhere_if(gDbg2, level="debug", msg=msg)                            
                    
                else: # if not opasgenlib.is_empty(bib_entry.sourcecode):
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
                    if locator.valid == 0:
                        msg = f"\t\t\t...Bib ID {ref_id} does not have enough info to link. {bib_entry.year}.{bib_entry.volume}.{bib_pgstart}"
                        log_everywhere_if(gDbg2, level="info", msg=msg)
                        continue
                        
                    ref.attrib["rx"] = locator.articleID()
                    search_str = f"//be[@id='{ref_id}']"
                    msg = f"\t\t\t...Matched Journal {opasxmllib.xml_xpath_return_xmlstringlist(parsed_xml, search_str)[0]}"
                    log_everywhere_if(gDbg2, level="debug", msg=msg)

                
            else:
                bk_locator_str, match_val, whatever = known_books.getPEPBookCodeStr(bib_entry.ref_entry_text)
                if bk_locator_str is not None:
                    ref.attrib["rx"] = bk_locator_str 
                    search_str = f"//be[@id='{ref_id}']"
                    msg = f"\t\t\t...Matched Book {match_val}. {opasxmllib.xml_xpath_return_xmlstringlist(parsed_xml, search_str)[0]}"
                    log_everywhere_if(gDbg2, level="info", msg=msg)
                    
                else:
                    # see if we have info to link SE/GW etc., these are in a sense like journals
                    pep_ref = False
                    if PEPJournalData.PEPJournalData.rgxSEPat2.match(bib_entry.source_title):
                        pep_ref = True
                        bib_entry.sourcecode = "SE"
                    elif PEPJournalData.PEPJournalData.rgxGWPat2.match(bib_entry.source_title):
                        pep_ref = True
                        bib_entry.sourcecode = "GW"
                    elif bib_entry.source_title:
                        # find_related_articles assigns to ref attrib rxcf (hence no need to use return val)
                        if gDbg2 and verbose: print (f"\t...Finding related articles for bibliography based on source_title")
                        rxcf = find_related_articles(ref,
                                                     art_or_source_title=bib_entry.source_title,
                                                     query_target="art_title_xml",
                                                     max_words=opasConfig.MAX_WORDS,
                                                     min_words=opasConfig.MIN_WORDS,
                                                     word_len=opasConfig.MIN_WORD_LEN,
                                                     max_cf_list=opasConfig.MAX_CF_LIST)
    
                    if pep_ref:
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
                        # check locator
                        base_info = opasPySolrLib.get_base_article_info_by_id(locator)
                        if base_info is not None:
                            ref.attrib["rx"] = locator.articleID()
                            search_str = f"//be[@id='{ref_id}']"
                            msg = f"\t\t\t...Matched Book {match_val}. {opasxmllib.xml_xpath_return_xmlstringlist(parsed_xml, search_str)[0]}"
                            log_everywhere_if(gDbg2, level="debug", msg=msg)
                        
                    else:     
                        locator = None
                        msg = f"\t\t\t...Skipped: {bib_entry.ref_entry_text}"
                        log_everywhere_if(gDbg2, level="debug", msg=msg)

        #try:
            #ocd.db.commit()
        #except mysql.connector.Error as e:
            #print("SQL Database -- Biblio Commit failed!", e)
        #if db_ok:
            #ocd.close_connection(caller_name="processBibliographies")
    
    # fix pgx links--check for split books
    #  - Note: I've copied the split book table that's created and updated by the original PEPXML process.
    #          But I've opted not to convert the code that creates and updates it here, since it's complicated 
    #          and quite embedded in the old XML libraries.  For now at least, it's left as a later exercise,
    #          so for books not included, I'll need to run the old PEPXML and copy the table over,
    #          or else new split TOCS will need to have direct links to the proper instance manually added.
    # if this is a split book, add pg numbers to split book table
    split_book_data = opasXMLSplitBookSupport.SplitBookData(database_connection=ocd)
    if artInfo.is_splitbook:
        pagebreaks = [pbk.text for pbk in parsed_xml.xpath("//n")]
        nodes = parsed_xml.xpath("//bib")
        if len(nodes)>0:
            has_biblio = 1
        else:
            has_biblio = 0

        if artInfo.is_maintoc:
            has_toc = 1
        else:
            has_toc = len(parsed_xml.xpath('//grp[@name="TOC"]'))
        
        for pgnum in pagebreaks:
            page_id = opasDocuments.PageNumber(pgNum=pgnum).pageID()
            split_book_data.add_splitbook_page_record(artInfo.art_id,
                                                      page_id=page_id, 
                                                      has_biblio=has_biblio, 
                                                      has_toc=has_toc, 
                                                      full_filename=artInfo.filename
                                                      )
            

    # Add page number markup
    add_page_number_markup(parsed_xml)

    pgx_links = parsed_xml.xpath("/pepkbd3//pgx") 
    logger.info("\t...Processing page links.")
    for pgx in pgx_links:
        inst = split_book_data.get_splitbook_page_instance(book_code=artInfo.src_code, vol=artInfo.art_vol_str, page_id=pgx.text)
        if gDbg2:
            print (f"Split book info: {pgx.text}, {pgx.attrib}, {inst}")
            
        if inst is not None and pgx.attrib.get("rx", None) is None:
            if gDbg2: print (f"Setting TOC page link: {pgx.text}, {pgx.attrib}, {inst}")
            loc = Locator(inst)
            pgx.attrib["rx"] = str(loc) + ".P" + opasDocuments.PageNumber(pgx.text).pageID()
        
    pgxPreProcessing(parsed_xml, ocd, artInfo=artInfo, split_book_data=split_book_data, verbose=verbose)

    #processedFilesCount += 1
    #bib_total_reference_count = 0
    ##db_ok = ocd.open_connection(caller_name="processBibliographies")
    #for ref in bibReferences:

    # xml_artauth = pepxml.findall("artinfo/artauth/aut")
    # parsed_xml, ret_status = glossEngine.doGlossaryMarkup(parsed_xml, pretty_print=pretty_print)
    glossEngine.doGlossaryMarkup(parsed_xml, pretty_print=pretty_print, diagnostics=False) # set diagnostics=True to see markup during processing.

    web_links = parsed_xml.xpath("/pepkbd3//autaff//url") 
    logger.info("\t...Processing url links.")
    for url in web_links:
        urltext = "mailto:" + url.text
        url.tag = "webx"
        url.attrib["url"] = urltext
    
    # if SE/GW
    # This section adds related IDs for GW and SE.
    if 1: # to turn on or off the feature.
        import opasXMLParaLanguageConcordance
        paraGWSEConcordance = opasXMLParaLanguageConcordance.PEPGWSEParaConcordance(ocd=ocd)
        if artInfo.src_code in ["GW", "SE"]:
            paraGWSEConcordance.addRelatedIDs(parsed_xml=parsed_xml, artInfo=artInfo) # pass in database instance
    
    ret_val = parsed_xml

    return ret_val, ret_status

