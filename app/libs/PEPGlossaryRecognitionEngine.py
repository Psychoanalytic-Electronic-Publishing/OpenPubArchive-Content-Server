# -*- coding: UTF-8 -*-

import sys
import time
import re
sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')

import logging
logger = logging.getLogger(__name__)

#from sciHLPyxie import sciPyxieTree, ALL, SUB, FIRST, E, A, hlString2xTree
# from sciHLElemTreeLXML import ALL, SUB, FIRST, E, A, hlString2xTree
# from lxml import etree

from collections import UserDict
import opasCentralDBLib
import opasGenSupportLib as opasgenlib
import lxml
from lxml import etree
parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
import json

import opasXMLHelper as opasxmllib
import opasConfig

# no glossary link/markup if under these ancestoral tags
default_ancestor_list = r"\b(abbr|abs|artinfo|artkwds|bkpubandloc|be|h[1-9]|cgrp|figx|frac|impx|ln|pgx|url|tbl|table|a|bx|bxe|webx)\b"
ocd = opasCentralDBLib.opasCentralDB()

gDbg1 = 0 # general info
gDbg2 = 0 # high level
gDbg7 = 0 # extreme debug details

__version__=".90"

import PEPMungeLibrary as munger

#--------------------------------------------------------------------------------
def split_glossary_group_terms(glossary_group_terms):
    ret_val = []
    if glossary_group_terms is not None:
        for n in glossary_group_terms:
            ret_val += opasgenlib.string_to_list(n, sep=";")

        ret_val = [item.lower() for item in ret_val]
        ret_val = sorted(ret_val)
    
    return ret_val

#--------------------------------------------------------------------------------
class GlossaryRecognitionEngine(UserDict):
    """
    Glossary Term Recognition Engine

    Uses VIEW GlossaryGroupDetails to load regex patterns for recognition.  (These are derived from the Glossary_Terms table, since it's a view)

    HOWEVER: if column "subset_of_another" is > 0, the pattern is ignored; this is a way to avoid partial matches and way too common terms.

    ALSO, as of 2010-09-06: regex colum comes from table glossary_tuned_regex.  This is extracted from the glossary_terms table but then hand tuned
    						to get rid of anomalies in the automatically generated regexes.

    """

    biblioDB = None
    matchList = None
    impxList = None
    recognitionMethod = 1 # original method, for now works better than "new" mothod
    leftMarker = u"⩥"   # used only in new code version, recognitionMethod=2
    rightMarker = u"⩤"  # used only in new code version, recognitionMethod=2
    midSeparator = u"∞"
    leftTag = '<impx type="TERM2" rx="$rx$" grpname="$grpnm$">'
    rightTag = '</impx>'
    
    #--------------------------------------------------------------------------------
    def __init__(self, gather=True, diagnostics=False, verbose=False):
        """
        Initialize the instance.  Load the glossary terms.
        If gather is true, search regex's are combined for faster recognition.  However,
        	this means that you cannot track what matches at what does.
        """

        UserDict.__init__(self)
        self.gather = gather
        self.verbose = verbose
        self.diagnostics = diagnostics
        if gather != True and verbose:
            print ("Gathering regex patterns is off.")
        self.data = {}
        if self.__class__.matchList == None:
            self.__class__.matchList = self.__loadGlossaryTerms()
        else:
            self.matchList = self.__class__.matchList

        #if self.__class__.impxList == None:
            #self.__class__.impxList = self.loadImpxMatchList()
        #else:
            #self.impxList = self.__class__.impxList

    #--------------------------------------------------------------------------------
    def __loadGlossaryTerms(self):
        """
        Load the glossary terms into the matchList.  Combine terms so more terms are recognized per row.
        
        Glossary group terms are 'munged' to combine forms and terms representing the group
          (see PEPMungeLibrary)

        """
        retVal = []
        # changed 2010-09-28: use != 1 to allow the terms with massive occurrences, but still have a mechanism to disallow others.
        selTerms = r"""select distinct lower(regex), length(regex), glossary_group, groups_group_id from vw_opasloader_glossary_group_terms
                       where `regex_ignore` is NULL
                       order by length(regex) DESC"""
        # use following query to limit glossary list for testing (change glossary group pattern)
        # selTerms = r"""select distinct distinct lower(regex), length(regex) from glossarygroupdetails where `regex_ignore` is NULL and groupMarkedForDeletion = 0 and glossary_group rlike 'child.*' order by length(regex) DESC"""
        match_list = ocd.get_select_as_list(sqlSelect=selTerms)
        gatherPattern = ""
        #count = 0
        msg_str = "Loading regex patterns.  Gathering regex patterns is "
        if self.gather:
            logger.info(msg_str + "ON")
        else:
            logger.info(msg_str + "OFF")

        for n in match_list:
            if gDbg1:
                if n[0] is None or len(n[0]) < 3:
                    logger.error(f"Glossary Pattern Exception: {n}")
                
            if self.gather:  # combine the patterns, to speed things up
                if n[0] == None:
                    if gDbg1: logger.debug("Glossary match patterns contain Null pattern: ", n)
                    continue
                if len(gatherPattern) < 650:
                    if gatherPattern == "":
                        gatherPattern = n[0]
                        continue
                    else:
                        gatherPattern += "|" + n[0]
                else:
                    if gatherPattern == "":
                        raise "Holy Hell"
                    # note that \b requires VERBOSE mode to work correctly!
                    rcpattern = r"\b(?P<whole>" + gatherPattern + r")\b"
                    if gDbg7: print ("Pat: ", gatherPattern[0:132])
                    # compile the combined terms -- ready for searching
                    rc = re.compile(rcpattern, re.IGNORECASE|re.VERBOSE)
                    retVal.append((rc, n))
                    # reset the gather area to start a new combined pattern.
                    gatherPattern = ""
            else: # don't combine them...lets us collect statistics and diagnose the pattern matching
                if n[0] == None:
                    if gDbg1: logger.debug("Warning: Glossary match patterns contain Null pattern: ", n)
                    continue
                if n[1] < opasConfig.MIN_TERM_LENGTH_MATCH:
                    if gDbg1: logger.debug("Warning: Glossary match too short: ", n)
                    continue
                if self.recognitionMethod == 2: # new way
                    rcpattern = r"\b[^/](?<!\u2a65)(?P<whole>" + n[0] + r")(?!\s*=)(?!\u2a64)\b"
                else: #  old way, seems to work better
                    rcpattern = r"\b(?P<whole>" + n[0] + r"(?!\s*=))\b"

                if gDbg1: logger.debug("Pattern: ", rcpattern)
                # compile the combined terms -- ready for searching
                rc = re.compile(rcpattern, re.IGNORECASE|re.VERBOSE)
                nlist = list(n)
                nlist[2] = munger.unMungeTerm(n[2])
                if re.match(f"^({opasConfig.GLOSSARY_TERM_SKIP_REGEX})$", nlist[2], re.IGNORECASE) is None:
                    retVal.append((rc, nlist))

        # load main data
        logger.info ("%d glossary input patterns loaded into %d regex patterns." % (len(match_list), len(retVal)))
        return retVal

    #--------------------------------------------------------------------------------
    def doGlossaryMarkup(self, parsed_xml, skipIfHasAncestorRegx=default_ancestor_list, preface=None,
                         theGroupName=None, pretty_print=False, markup_terms=True, verbose=False):
        """
        Markup any glossary entries in paragraphs (only).

        If theGroupName is supplied, it means we are marking up the glossary itself, and any impxs that match
        theGroupName will be removed (as self referential)

        Returns the number of changed terms, and a dictionary of terms and counts

        >>> glossEngine = GlossaryRecognitionEngine(gather=False, verbose=True)
        Gathering regex patterns is off.
        >>> testXML= '<body><p>My belief is that, διαφέρει although Freud was a revolutionary, most of his followers were more conventional. As is true of most institutions, as psychoanalysis aged, a conservatism overtook it. Foreground analytic theory incorporated the background cultural pathologizing of nonheterosexuality. Thus, the few articles written about lesbians rigidly followed narrow reductionistic explanations. Initially, these explanations followed classical theory, and then as psychoanalysis expanded into ego psychology and object relations, lesbian pathologizing was fit into these theories <bx r="B006">(Deutsch, 1995)</bx>.</p><p>For example, Adrienne Applegarth&apos;s 1984 American Psychoanalytic panel on homosexual women, used ego psychology to explain lesbianism. Applegarth viewed it (according to <bx r="B020">Wolfson, 1984</bx>), as a complicated structure of gratification and defense (p. <pgx r="B020">166</pgx>). She felt that if the steps in the usual positive and negative oedipal phases or if a girls wish for a baby arising out of penis envy become distorted, a range of outcomes, including homosexuality, could occur (Wolfson, <bx r="B020">1984</bx>, p. <pgx r="B020">166</pgx>).</p></body>'
        >>> parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
        >>> pepxml = etree.fromstring(testXML, parser)
        >>> root = pepxml.getroottree()
        >>> count, marked_term_list = glossEngine.doGlossaryMarkup(root)
        >>> print (count)
        25

        >>> testXML= '<body><p> forces. Brenner has suggested that the familiar  of the id, ego, and superego as agencies of <b id="10">the</b> mind.</p></body>'
        >>> parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
        >>> pepxml = etree.fromstring(testXML, parser)
        >>> root = pepxml.getroottree()
        >>> count, marked_term_list = glossEngine.doGlossaryMarkup(root)
        >>> print (count)
        4
        """
        
        ret_status = 0
        if gDbg2: print (f"\t...Starting Glossary Markup")
        #preface="""<?xml version='1.0' encoding='UTF-8' ?><!DOCTYPE %s SYSTEM '%s'>""" % ("p", gDefaultDTD) + "\n"
        preface = """<?xml version='1.0' encoding='UTF-8' ?>""" # TRY THIS TEST CODE 2017-04-02, without named entities, we should not need a DTD loaded (much quicker)
        startTime = time.time()
        count_in_doc = 0
        total_changes = 0
        # get all paragraphs
        allParas = parsed_xml.xpath(".//p|.//p2")
        para_count = 0
        found_term_dict = {}
        for para_working in allParas:
            para_count += 1
            #para_working = para
            # skip if has skipped ancestor:
            # ancestors = opasxmllib.xml_node_list_ancestor_names(para_working)
            ancestor_match = opasxmllib.xml_node_regx_ancestors(para_working, regx=skipIfHasAncestorRegx)
            if ancestor_match:
                if self.diagnostics: print (f"\t\t...Skipped para {para_count} (due to ancestor)")
                continue

            # unicode opt returns string inst of bytes, which is for compat w py2 (http://makble.com/python-why-lxml-etree-tostring-method-returns-bytes)
            node_text = lxml.etree.tostring(para_working, encoding="unicode")
            # len_node_text = len(node_text)
            if self.diagnostics: print (node_text)
            changes = False # reset
            for rcrow in self.matchList:
                # replacement pattern...if we need to add an ID, it probably needs to be done in a second pass (because
                #       we are combining patterns.
                term_data = rcrow[1]
                grpnm = term_data[2]
                rx = term_data[3]
                if theGroupName == grpnm:
                    continue # skip per parameter def [TBD: Needs to be checked for glossary build]
                
                subStrCxt = f'<impx type="TERM2" rx="{rx}" grpname="{grpnm}">\g<whole></impx>'
                # Match at the start, at the end, the whole, and in the middle, delineated
                rc = rcrow[0]
                try:
                    found = rc.findall(node_text)
                    change_count = len(found)
                    total_changes += change_count
                    if change_count:
                        term = found[0][0]
                        term = term.lower().strip()
                        term_count = found_term_dict.get(term, 0)
                        term_count += change_count
                        count_in_doc += change_count
                        found_term_dict[term] = term_count
                        if markup_terms:
                            node_text2 = rc.sub(subStrCxt, node_text)
                except Exception as e:
                    print (e)

                if change_count and markup_terms: 
                    #  or if within one of these tags within a paragraph, don't keep it
                    if re.search("<(j|pb|t)>.*?<impx.*?</(j|pb)>", node_text2, flags=re.IGNORECASE):
                        if gDbg1: print ("\t..Error: Nested in forbidden tag. Skipping markup for para")
                        continue
                    # if the markup is within quotes, don't keep it.
                    elif re.search("\".*?<impx.*</impx>.*?\"", node_text2, flags=re.IGNORECASE):
                        if gDbg1: print ("\t..Error: impx in quoted passage detected. Skipping markup for para")
                        continue
                    #  or if nested impx, don't keep it
                    elif re.search("<impx type=\"TERM2\"><impx", node_text2, flags=re.IGNORECASE):
                        if gDbg1: print ("\t..Error: Double nested impx detected. Skipping markup for para")
                        continue
                    else:
                        if self.diagnostics: print (f"\t\t...Para {para_count}: Marked Glossary Term: {grpnm} ID: {rx}")
                        changes = True
                        node_text = node_text2

            if changes and markup_terms:
                try:
                    new_node = lxml.etree.XML(node_text)
                    parent_node = para_working.getparent()
                    parent_node.replace(para_working, new_node)
                    if self.diagnostics:
                        print (f"\t\t...Para {para_count}: Final markup: {node_text}")
                        print (f"\t\t...Para {para_count}: {count_in_doc} glossary terms recognized.")
                except Exception as e:
                    # skip this change and log
                    logger.error(f"Could not save node change (skipped) {e}.")

        if verbose: 
            endTime = time.time()
            timeDiff = endTime - startTime
            #print (80*"-")
            if markup_terms:
                print (f"\t...{total_changes} glossary term markups for {count_in_doc} paragraphs in {timeDiff} secs")
            else:  
                print (f"\t...{total_changes} glossary terms recognized in {timeDiff} secs")

        # option: should we return count of changed paragraphs?
        ret_status = count_in_doc
        sorted_term_dict = dict(sorted(found_term_dict.items(), key=lambda item: item[1], reverse=True))

        # returns count of changes and list of tuples with (term, count)
        return ret_status, sorted_term_dict

    #--------------------------------------------------------------------------------
    def getGlossaryLists(self,
                         parsed_xml,
                         skipIfHasAncestorRegx=default_ancestor_list,
                         verbose=True):
        """
        Get glossary term lists from document without marking any up.
    
        Returns the number of changed terms, and a dictionary of terms and counts
    
        """
        
        ret_val = {}
        startTime = time.time()
        caller_name = "getGlossaryLists"
        count_in_doc = 0
        total_changes = 0
        if isinstance(parsed_xml, str):
            parsed_xml = etree.fromstring(opasxmllib.remove_encoding_string(parsed_xml), parser)
        
        # see if the precompiled version is present
        glossary_term_dict = parsed_xml.xpath("//unit[@type='glossary_term_dict']")
        if glossary_term_dict == []: # if empty
            allParas = parsed_xml.xpath(".//p|.//p2")  # get all paragraphs
            found_term_dict = {}
            for para_working in allParas:
                ancestor_match = opasxmllib.xml_node_regx_ancestors(para_working, regx=skipIfHasAncestorRegx)
                if ancestor_match:
                    if self.diagnostics: print (f"\t\t...Skipped para {para_count} (due to ancestor)")
                    continue
                node_text = lxml.etree.tostring(para_working, encoding="unicode")
                for rcrow in self.matchList:
                    term_data = rcrow[1]
                    grpnm = term_data[2]
                    # rx = term_data[3]
                    # Match at the start, at the end, the whole, and in the middle, delineated
                    rc = rcrow[0]
                    try:
                        found = rc.findall(node_text)
                        found_count = len(found)
                        total_changes += found_count
                        # use terms, not groups.  Groups are compound, and the
                        # multiple terms do not reflect what was found in the specific document
                        if 1: # terms
                            if found_count:
                                term = found[0][0]
                                term = term.lower().strip()
                                term_count = found_term_dict.get(term, 0)
                                term_count += found_count
                                count_in_doc += found_count
                                found_term_dict[term] = term_count
                                if 0: print (f"\t\t\tTerm: {term} / {grpnm}")
                        else: # groups
                            if found_count:
                                term = found[0][0]
                                term_grp = grpnm.lower().strip()
                                term_count = found_term_dict.get(term_grp, 0)
                                term_count += found_count
                                count_in_doc += found_count
                                found_term_dict[term_grp] = term_count
                                if 1: print (f"\t\t\tTerm: {term} / {grpnm}")
                            
                    except Exception as e:
                        print (e)
            
            ret_val = dict(sorted(found_term_dict.items(), key=lambda item: item[1], reverse=True))
            
        else: # use the precompiled dictionary
            try:
                glossary_term_dict_str = lxml.html.tostring(glossary_term_dict[0][0], method="text").strip()
                glossary_dict = json.loads(glossary_term_dict_str)
                # for historical reasons it's a list sometimes, but now it should always be a dict.  Handle either here.
                # convert to dict if it's a list
                if isinstance(glossary_dict, list):
                    ret_val = {k: v for k, v in glossary_dict}
                elif isinstance(glossary_dict, dict):
                    ret_val = glossary_dict
            except Exception as e:
                logger.error(f"{caller_name}: Error loading precompiled term_dict {e}")
                    
        #ret_status = count_in_doc
        if verbose: 
            endTime = time.time()
            timeDiff = endTime - startTime
            if count_in_doc > 0:
                print (f"\t...{count_in_doc} glossary terms recognized in {timeDiff} secs")
            else:
                print (f"\t...Glossary terms loaded from compiled XML in {timeDiff} secs")
            
        return ret_val


#==================================================================================================
# Main Routines
#==================================================================================================

if __name__ == "__main__":
    """
	Run Test Routines
	"""

    import doctest
    doctest.testmod()
    print ("Fini. Tests complete.")
    sys.exit()