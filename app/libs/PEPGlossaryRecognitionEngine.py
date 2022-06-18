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
import lxml
import opasXMLHelper as opasxmllib

default_ancestor_list = "abbr|artinfo|be|h[1-9]|cgrp|figx|frac|impx|ln|pgx|url|a|bx|bxe|webx"
ocd = opasCentralDBLib.opasCentralDB()
# from PEPGlobals import gConst, gDefaultDTD, gPEPdbName, gDefaultPreface

gDbg1 = 0 # general info
gDbg2 = 0 # high level
gDbg4 = 0
gDbg7 = 0 # debug details

__version__=".90"

gDemarc = u"#"

#--------------------------------------------------------------------------------
def unMungeToTermList(mungedTerm, demarcPattern=gDemarc):
    """
    unMunge the term so it can be searched different ways
    Returns a list of terms

    	>>> unMungeToTermList("#dog##eat##dog#")
    	[u'dog', u'eat', u'dog']
    	>>> unMungeToTermList("#dog## eat ##dog#")
    	[u'dog', u'eat', u'dog']
        >>> termL = unMungeToTermList("#DÉJÀ VU##Déjà Raconté#".decode("utf8"))
        >>> print termL[0].encode("utf8")
        DÉJÀ VU
    """

    retVal = filter(None, [x.strip() for x in mungedTerm.split(demarcPattern)])

    return retVal

#--------------------------------------------------------------------------------
def unMungeTerm(mungedTerm, demarcPattern=gDemarc):
    """
    unMunge the term so it can be searched different ways
    Returns a unicode string where terms are separated by ";"

        >>> originalStr = r"#MAHLER, MARGARET S##MARGARET S MAHLER#"
        >>> umT = unMungeTerm(originalStr)
        >>> umT
        u'MAHLER, MARGARET S; MARGARET S MAHLER'
        >>> mungeStr(umT)
        u'#MAHLER, MARGARET S##MARGARET S MAHLER#'
        >>> unMungeTerm("#dog##eat##dog#")
        u'dog; eat; dog'

        >>> unMungeTerm("#dog## eat ##dog#")
        u'dog; eat; dog'

        >>> unMungeTerm("dog eat dog")
        u'dog eat dog'

    """

    #retVal = [x.strip() for x in mungedTerm.split(demarcPattern)]
    retVal = unMungeToTermList(mungedTerm, demarcPattern)
    retVal = u"; ".join(retVal)

    return retVal


#----------------------------------------------------------------------------------------
def	doQuoteEscapes(data, hasEscapes=0):
    retVal = data
    if retVal is not None:
        if re.search(r'"',	retVal)	is not None:
            retVal = re.sub(r'(?P<pre>([^\\]|\A))"', r'\1\\"', retVal)
        if re.search(r"''", retVal) is not None:
            retVal = re.sub(r"''",	r"'\\'", retVal)
        if re.search(r"'", retVal) is not None:
            retVal = re.sub(r"(?P<pre>([^\\]|\A))'", r"\1\\'", retVal)
    return retVal

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
    def __init__(self, gather=True):
        """
        Initialize the instance.  Load the glossary terms.
        If gather is true, search regex's are combined for faster recognition.  However,
        	this means that you cannot track what matches at what does.
        """

        UserDict.__init__(self)
        self.gather = gather
        #if gather != True:
            #print ("Gathering regex patterns is off.")
        self.data = {}
        if self.__class__.matchList == None:
            self.__class__.matchList = self.__loadGlossaryTerms()
        else:
            self.matchList = self.__class__.matchList

        #if self.__class__.impxList == None:
            #self.__class__.impxList = self.loadImpxMatchList()
        #else:
            #self.impxList = self.__class__.impxList

    ##-----------------------------------------------------------------------------
    #def loadImpxMatchList(self):
        #selTerms = r"""SELECT DISTINCT lower(regex), length(regex)
            #FROM
            #opasloader_glossary_details
            #where `regex_ignore` is NULL order by length(regex) DESC
            #"""

        #match_list = ocd.get_select_as_list(sqlSelect=selTerms)
        #retVal = []
        #for n in match_list:
            ## compile the regex:
            #pat = f"\b{n[0]}\b"
            #cRegx = re.compile(pat, re.IGNORECASE)
            #patternRow = [cRegx, pat]
            #retVal.append(patternRow)

        #print ("%d patterns loaded." % len(retVal))
        #return retVal

    #--------------------------------------------------------------------------------
    def __loadGlossaryTerms(self):
        """
        Load the glossary terms into the matchList.  Combine terms so more terms are recognized per row.

        """
        retVal = []
        # changed 2010-09-28: use <> 1 to allow the terms with massive occurrences, but still have a mechanism to disallow others.
        selTerms = r"""select distinct lower(regex), length(regex), glossary_group, groups_group_id from vw_opasloader_glossary_group_terms
                       where `regex_ignore` is NULL
                       order by length(regex) DESC"""
        # use following query to limit glossary list for testing (change glossary group pattern)
        # selTerms = r"""select distinct distinct lower(regex), length(regex) from glossarygroupdetails where `regex_ignore` is NULL and groupMarkedForDeletion = 0 and glossary_group rlike 'child.*' order by length(regex) DESC"""
        match_list = ocd.get_select_as_list(sqlSelect=selTerms)
        gatherPattern = ""
        #count = 0
        if self.gather:
            logger.info("Loading regex patterns.  Gathering regex patterns is ON.")
        else:
            logger.info("Loading regex patterns.  Gathering regex patterns is OFF.")

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
                if self.recognitionMethod == 2: # new way
                    rcpattern = r"\b[^/](?<!\u2a65)(?P<whole>" + n[0] + r")(?!\s*=)(?!\u2a64)\b"
                else: #  old way, seems to work better
                    rcpattern = r"\b(?P<whole>" + n[0] + r"(?!\s*=))\b"

                if gDbg1: logger.debug("Pattern: ", rcpattern)
                # compile the combined terms -- ready for searching
                rc = re.compile(rcpattern, re.IGNORECASE|re.VERBOSE)
                nlist = list(n)
                nlist[2] = unMungeTerm(n[2])
                retVal.append((rc, nlist))

        # load main data
        logger.info ("%d glossary input patterns loaded into %d regex patterns." % (len(match_list), len(retVal)))
        return retVal

    ##--------------------------------------------------------------------------------
    #def fixGlossaryTerms(self):
        #"""
        #Fix bad escapes in the glossary term regex

                #>>> #glossEngine = GlossaryRecognitionEngine(gather=False)
                #>>> #glossEngine.fixGlossaryTerms()

        #"""

        #self.__initDB__()
        #selRegex = r"select regex, term from glossary_tuned_regex"
        #updateRegex = r"update glossary_tuned_regex set regex = '%s' where term='%s'"
        #dbc = self.db.cursor()
        #dbo = self.db.cursor()
        #dbc.execute(selRegex)
        #dbo.execute("set autocommit = 1")
        #count = 0
        #for n in dbc:
            #pattern = n[0]
            #term = n[1]
            #if "\\[" in pattern:
                #pattern = pattern.replace("\[", "[")
                #if "\\]" in pattern:
                    #pattern = pattern.replace("\]", "]")
                #updateSel = updateRegex % (doQuoteEscapes(pattern), doQuoteEscapes(term))
                #print (updateSel) #pattern, term
                #dbo.execute(updateSel)

        #dbc.close()

    ##--------------------------------------------------------------------------------
    #def removeSelfReferencesInGlossaries(self, tree, theGroupName):
        #"""
        #Remove impx from terms in glossary  within the same definition.

        #>>> #glossEngine = GlossaryRecognitionEngine(gather=False)
        #>>> #testXML= '<glossary><dictentrygrp id="YP0003312268840"><term>CANADA</term><dictentry><src>Skelton, R. (Ed.). (2006). The Edinburgh International Encyclopaedia of Psychoanalysis.</src><def><p>Although Ernest *Jones lived and worked in Toronto from 1908 to 1913, interest in psychoanalysis in <impx rx="ZBK.069.0001c.YP0003312268840" grpname="CANADA" type="TERM2">Canada</impx> remained sporadic and individual until after World War II. In 1945 Miguel Prados, a Spanish neuropathologist without formal psychoanalytic <impx rx="ZBK.069.0001t.YN0019043981580" grpname="TRAINING" type="TERM2">training</impx> but with strong psychoanalytic interests, established the Montreal Psychoanalytic Club, leadership of which was assumed in 1948 by Theodore Chentrier, a lay member of the Paris Society who had obtained an appointment to the Department of Psychology of the <i>Universit&eacute; de Montr&eacute;al.</i> In 1950, Eric Wittkower became the first psychoanalyst to be appointed to the faculty of Montreals McGill University.</p></def><defrest><p>As several members of the Montreal group received psychoanalytic <impx rx="ZBK.069.0001t.YN0019043981580" grpname="TRAINING" type="TERM2">training</impx> in the United States, there was an attempt to obtain official Study Group status in the International Psychoanalytic Association through sponsorship by the Detroit affiliate of the American Psychoanalytic Association. In the face of some opposition by the APA, the group decided instead to seek sponsorship from the British Society to which two of its members (Eric Wittkower and Alastair MacLeod) belonged. This led to protests by the Americans who, as they had done in the debate over <impx rx="ZBK.069.0001l.YP0012185582400" grpname="LAY ANALYSIS" type="TERM2">lay analysis</impx>, raised the spectre of their withdrawal from the International, this time over the threat to American hegemony over psychoanalysis in North America that this autonomous application from <impx rx="ZBK.069.0001c.YP0003312268840" grpname="CANADA" type="TERM2">Canada</impx> represented to them.</p></defrest></dictentry></dictentrygrp></glossary>'
        #>>> #myt = hlString2xTree (testXML)
        #>>> #glossEngine.removeSelfReferencesInGlossaries(myt, theGroupName="Canada")

        #"""

        ## Check if this a glossary TBD
        ## get all the dictentry terms
        #tree.Home()
        #theGroupList = re.split("[ ]*;[ ]*", theGroupName)
        #if gDbg4: print ("RemoveSelfReferences looking for terms in list: ", theGroupList)
        #allImpxs = tree.getElements(ALL, elemSpec=E("impx", {"type":"TERM2"}), parentSpec=E("dictalso"), notParent=True)
        #for impx in allImpxs:
            #tree.Seek(impx)
            #term = tree.getCurrElementText()
            #if term.upper() in theGroupList:
                ## matched...so unwrap it
                #if gDbg4: print ("unwrapping...", term, " %s matched" % (term))
                #tree.unwrapNode(impx)
            ##else:
            ##   print "No match: ", term


    ##--------------------------------------------------------------------------------
    #def addImpxIDs(self, tree):
        #"""
        #Markup any glossary entries in paragraphs (only)

        #Uses the preloaded impxList used to mark up terms to get the IDs, so these are
            #based on whatever is in the table (not regenerated as a hash).  This means
            #the hash can be overrided by editing the table in case the group name has changed
            #and we don't want to rebuild all the instances.

        #"""

        #notMatched = []

        ##-----------------------------------------------------------------------------

        #patternList = self.impxList
        #allImpxs = tree.getElements(ALL, elemSpec=E("impx", {"type":"TERM2"}))
        #count = 0
        #skip = 0
        #impList = {}
        #notFoundTerms = {}
        #for impx in allImpxs:
            #tree.Seek(impx)
            #count += 1
            ## get the term
            #term = tree.getCurrElementText()
            #term = term.strip()
            ## default
            #tree.setCurrAttrVal("type", "UNKT")
            #found = False
            #for patternTuple in patternList:
                #if patternTuple[0].match(term):
                    ## found it, now we just save the ID
                    #found = True
                    #groupName = patternTuple[1]
                    #groupID = patternTuple[2]

                    #groupTerm = PEPGlossaryTermList.PEPGlossaryTermList(groupName)
                    #useGroupID = groupTerm[groupTerm.FULLNAMEID]
                    #groupPrettyName = groupTerm[groupTerm.PRETTYPRINTTERMLIST]

                    ##print sciUnicode.unicode2Console(groupPrettyName), useGroupID, groupID

                    ##raise Exception,  "No group matched! '%s'" % selTerms
                    #tree.setCurrAttrVal("type", "TERM2")
                    #tree.setCurrAttrVal("rx", useGroupID )
                    #tree.setCurrAttrVal("grpname", PEPGlossaryTermCommon.unMungeTerm(groupName) )
                    #break  # go to the next impx

            #if not found:
                #try:
                    #notFoundTerms[term] += 1
                #except:
                    #notFoundTerms[term] = 1

        #for term, theCount in notFoundTerms.items():
            #print ("%s instances of '%s' not found." % (theCount, sciUnicode.unicode2Console(term)))

        #print ("Glossary Terms found - Added impx to %s terms" % count)
        #return

    ##--------------------------------------------------------------------------------
    #def checkImpxs(self, tree):
        #"""
        #Find any nested impx's and remove them.

        #"""

        ## unwrap all impx in impx or i
        #count = tree.unwrapElements(ALL, elemSpec=E("impx"), parentSpec=E("impx"))
        #if gDbg1: print ("%d nested impx elements removed." % count)
        ## unwrap all impx in significant elements
        #count2 = tree.unwrapElements(ALL, elemSpec=E("impx", {"type":"TERM2|UNKT"}), parentSpec=E("a|l|abbr|artinfo|be|h[1-9]|bp|bx|bxe|bst|binc|cgrp|num|denom|pgx|spkr|hdex|figx|tblx|webx|i|ln|j|url|t|v"))
        #if 1: print ("%d impx elements in non-allowed locations removed." % count2)
        #retVal = count + count2
        #return retVal

    #--------------------------------------------------------------------------------
    def doGlossaryMarkup(self, parsed_xml, skipIfHasAncestor=default_ancestor_list, preface=None, theGroupName=None, pretty_print=False):
        """
        Markup any glossary entries in paragraphs (only).

        If theGroupName is supplied, it means we are marking up the glossary itself, and any impxs that match
        theGroupName will be removed (as self referential)

        Returns the number of changed terms.

        >>> glossEngine = GlossaryRecognitionEngine(gather=False)
        Gathering regex patterns is off.
        1481 input patterns loaded into 1480 regex patterns.
        >>> testXML= u'<body><p>My belief is that, διαφέρει although Freud was a revolutionary, most of his followers were more conventional. As is true of most institutions, as psychoanalysis aged, a conservatism overtook it. Foreground analytic theory incorporated the background cultural pathologizing of nonheterosexuality. Thus, the few articles written about lesbians rigidly followed narrow reductionistic explanations. Initially, these explanations followed classical theory, and then as psychoanalysis expanded into ego psychology and object relations, lesbian pathologizing was fit into these theories <bx r="B006">(Deutsch, 1995)</bx>.</p><p>For example, Adrienne Applegarth&apos;s 1984 American Psychoanalytic panel on homosexual women, used ego psychology to explain lesbianism. Applegarth viewed it (according to <bx r="B020">Wolfson, 1984</bx>), as a complicated structure of gratification and defense (p. <pgx r="B020">166</pgx>). She felt that if the steps in the usual positive and negative oedipal phases or if a girls wish for a baby arising out of penis envy become distorted, a range of outcomes, including homosexuality, could occur (Wolfson, <bx r="B020">1984</bx>, p. <pgx r="B020">166</pgx>).</p></body>'
        >>> parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
        >>> pepxml = etree.fromstring(testXML, parser)
        >>> root = pepxml.getroottree()

        >>> glossEngine.doGlossaryMarkup(root)
        0 impx elements in non-allowed locations removed.
        15

        >>> testXML= '<body><p> forces. Brenner has suggested that the familiar  of the id, ego, and superego as agencies of <b id="10">the</b> mind.</p></body>'
        >>> parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
        >>> pepxml = etree.fromstring(testXML, parser)
        >>> root = pepxml.getroottree()
        >>> print (glossEngine.doGlossaryMarkup(root))
        0 impx elements in non-allowed locations removed.
        3

        """

        if gDbg2:
            print ("***** Do Glossary Markup *****")
        ret_val = parsed_xml # default - if error, return original parse
        ret_status = False
        
        count = 0
        #preface = """<?xml version='1.0' encoding='UTF-8' ?>""" # TRY THIS TEST CODE 2017-04-02, without named entities, we should not need a DTD loaded (much quicker)

        startTime = time.time()
        # create a string to do replace
        node_text = lxml.etree.tostring(parsed_xml, pretty_print=pretty_print, encoding="utf8").decode("utf-8")
        len_orig_node_text = len(node_text)
        
        # replacement pattern...if we need to add an ID, it probably needs to be done in a second pass (because
        #       we are combining patterns.
        
        changes = False # reset
        sep2 = 'u22E1'
        idx = -1
        for rcrow in self.matchList: # mark terms
            idx += 1
            subStrCxt = f"{self.leftMarker}\g<0>{self.midSeparator}{idx}{self.rightMarker}"
            # Match at the start, at the end, the whole, and in the middle, delineated
            rc = rcrow[0]
            try:
                nodeText2 = node_text # temp
                m = rc.search(node_text)
                if m is not None:
                    #match = m.group(0)
                    #logger.debug(match)
                    nodeText2 = rc.sub(subStrCxt, node_text)
            except Exception as e:
                logger.error(f"Error matching glossary data {e}")

            if 1: # Check for issues before saving node
                if nodeText2 != node_text:
                    # if the markup is within quotes, don't keep it.
                    if re.search(f"\u201C[^\u2019]*?{self.leftMarker}.*?{self.rightMarker}[^201C]*?\u2019", nodeText2, flags=re.IGNORECASE):
                        logger.debug("impx in quoted passage detected. Skipping markup")
                        continue
                    # or double impx
                    elif re.search(f"<[^>]*?{self.leftMarker}.*?{self.rightMarker}[^>]*?>", nodeText2, flags=re.IGNORECASE):
                        logger.debug("impx in tag detected. Skipping markup")
                        continue
                    elif re.search(f"{self.leftMarker}{self.leftMarker}(.*?){self.rightMarker}{self.rightMarker}", nodeText2, flags=re.IGNORECASE):
                        logger.debug("Double impx detected. Skipping markup")
                        continue
                    #  or if nested impx, don't keep it
                    elif re.search(f"{self.leftMarker}[^{self.rightMarker}]*?{self.leftMarker}", nodeText2, flags=re.IGNORECASE):
                        logger.debug("Double nested impx detected. Skipping markup")
                        continue
                    else:
                        # sciSupport.trace("%s%sMarked Abbr %s in %s: " % (60*"-","\n", rc.pattern, nodeText2), outlineLevel=1, debugVar=gDbg7)
                        changes = True
                        count += 1
                        node_text = nodeText2

        # now add new markup, change back markers, and reparse datanode to check if all is well
        if changes:
            glossary_nodes = re.findall(f"{self.leftMarker}[^{self.leftMarker}{self.rightMarker}]+?{self.rightMarker}", node_text)
            if glossary_nodes is not None:
                for term in glossary_nodes:
                    if gDbg7: print (term)
                    #lookup term
                    term_set_item = re.split(f"{self.leftMarker}|{self.midSeparator}|{self.rightMarker}", term)
                    term_index = int(term_set_item[2])
                    term_data = self.__class__.matchList[term_index][1]
                    replacement_text = self.leftTag.replace("$grpnm$", term_data[2])
                    replacement_text = replacement_text.replace("$rx$", term_data[3])
                    if gDbg7: print (replacement_text)
                    node_text = re.sub(term, f"{replacement_text}{term_set_item[1]}</impx>", node_text)
               
            try:
                parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
                reparsed_xml = lxml.etree.fromstring(node_text, parser)
                #root = pepxml.getroottree()
            except Exception as e:
                detail = "Skipped:$%s$ " % node_text.encode("utf-8")
                logger.warning(f"Glossary Replacement makes this section unparseable. {detail}")

        # done, check new_node
        #new_node_text = opasxmllib.xml_xpath_return_xmlstringlist(reparsed_xml, "//*", default_return=None)[0]
        new_node_text = lxml.etree.tostring(reparsed_xml, pretty_print=pretty_print, encoding="utf8").decode("utf-8")
        len_new_node_text = len(new_node_text)
        if len_new_node_text < len_orig_node_text:
            logger.error(f"GlossaryRecognition. OrigLen:{len_orig_node_text} > TaggedLen:{len_new_node_text}.  Tagging Skipped.")

            # ret_val = parsed_xml # return original parsed xml (default)
            # ret_status = False (default)
        else:
            # keep it
            ret_val = reparsed_xml # return reparsed xml with tagging
            ret_status = True
               
        # change impx's of TERM1 to TERM2 -- should be in L&P only
        #count = tree.unwrapElements(ALL, elemSpec=E("impx", {"type":"TERM1"}))
        #count2 = tree.replaceAttrText("type", "TERM1", "TERM2", ALL, E("impx"))
        #if count2 > 0:
            #print ("*********************************************************************")
            #print ("***** Implied Links to L&P redirected to the PEP Glossary")
            #print ("*********************************************************************")
        # return count of changed paragraphs

        endTime = time.time()
        timeDiff = endTime - startTime
        print (f"Time to do glossary markup: {timeDiff}")

        return ret_val, ret_status # return new reparsed_xml if ret_status is true, orig parsed_xml if not.

    ##--------------------------------------------------------------------------------
    #def doGlossaryMarkupOld(self, tree, skipIfHasAncestor=default_ancestor_list, preface=None, theGroupName=None):
        #"""
        #Markup any glossary entries in paragraphs (only).

        #If theGroupName is supplied, it means we are marking up the glossary itself, and any impxs that match
        #theGroupName will be removed (as self referential)

        #Returns the number of changed terms.

        #>>> glossEngine = GlossaryRecognitionEngine(gather=False)
        #Gathering regex patterns is off.
        #1481 input patterns loaded into 1480 regex patterns.
        #>>> testXML= u'<body><p>My belief is that, διαφέρει although Freud was a revolutionary, most of his followers were more conventional. As is true of most institutions, as psychoanalysis aged, a conservatism overtook it. Foreground analytic theory incorporated the background cultural pathologizing of nonheterosexuality. Thus, the few articles written about lesbians rigidly followed narrow reductionistic explanations. Initially, these explanations followed classical theory, and then as psychoanalysis expanded into ego psychology and object relations, lesbian pathologizing was fit into these theories <bx r="B006">(Deutsch, 1995)</bx>.</p><p>For example, Adrienne Applegarth&apos;s 1984 American Psychoanalytic panel on homosexual women, used ego psychology to explain lesbianism. Applegarth viewed it (according to <bx r="B020">Wolfson, 1984</bx>), as a complicated structure of gratification and defense (p. <pgx r="B020">166</pgx>). She felt that if the steps in the usual positive and negative oedipal phases or if a girls wish for a baby arising out of penis envy become distorted, a range of outcomes, including homosexuality, could occur (Wolfson, <bx r="B020">1984</bx>, p. <pgx r="B020">166</pgx>).</p></body>'
        #>>> parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
        #>>> pepxml = etree.fromstring(testXML, parser)
        #>>> root = pepxml.getroottree()

        #>>> glossEngine.doGlossaryMarkup(root)
        #0 impx elements in non-allowed locations removed.
        #15

        #>>> testXML= '<body><p> forces. Brenner has suggested that the familiar  of the id, ego, and superego as agencies of <b id="10">the</b> mind.</p></body>'
        #>>> parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)
        #>>> pepxml = etree.fromstring(testXML, parser)
        #>>> root = pepxml.getroottree()
        #>>> print (glossEngine.doGlossaryMarkup(root))
        #0 impx elements in non-allowed locations removed.
        #3

        #"""

        #print ("***** Do Glossary Markup *****")
        #retVal = 0
        #count = 0
        ##preface="""<?xml version='1.0' encoding='UTF-8' ?><!DOCTYPE %s SYSTEM '%s'>""" % ("p", gDefaultDTD) + "\n"
        #preface = """<?xml version='1.0' encoding='UTF-8' ?>""" # TRY THIS TEST CODE 2017-04-02, without named entities, we should not need a DTD loaded (much quicker)

        #if gDbg2:
            #startTime = time.time()

        ## replacement pattern...if we need to add an ID, it probably needs to be done in a second pass (because
        ##       we are combining patterns.
        #subStrCxt = """<impx type="TERM2">\g<whole></impx>"""
        ## strText = ""

        ## Replace altdata so it doesn't match - Better still, just delete it
        ## BUT NOTE: the altdata attribute in L&P is actually "alternate terms"! (not a display, altdata thing...).  That's why it matches sometimes.
        ##count = tree.replaceAttrText("altdata", "(.*)", "XXX\0", ALL, E("impx", {"type":"TERM1"}))
        ## tree.deleteAttributes(ALL, elemSpec=E("impx", {"type":"TERM1"}), attrNamePtn="altdata")
        #countInDoc = 0
        #countParas = 0
        ## get all paragraphs
        #allParas = tree.xpath(".//p|.//p2")
        #count = 0
        #for para in allParas:
            #nodeText = tree.tostring(para, pretty_print=True, encoding="utf8").decode("utf-8")
            #changes = False # reset
            #for rcrow in self.matchList:
                ## Match at the start, at the end, the whole, and in the middle, delineated
                #rc = rcrow[0]
                #try:
                    #nodeTextHold = nodeText # temp
                    #nodeText2 = rc.sub(subStrCxt, nodeText)
                #except Exception as e:
                    #print (e)

                #if nodeText2 != nodeText:
                    ## if the markup is within quotes, don't keep it.
                    #if re.search("\".*?<impx.*</impx>.*?\"", nodeText2, flags=re.IGNORECASE):
                        #if gDbg1: print ("Error: impx in quoted passage detected. Skipping markup")
                        #continue
                    ##  or if nested impx, don't keep it
                    #elif re.search("<impx type=\"TERM2\"><impx", nodeText2, flags=re.IGNORECASE):
                        #if gDbg1: print ("Error: Double nested impx detected. Skipping markup")
                        #continue
                    #else:
                        ## sciSupport.trace("%s%sMarked Abbr %s in %s: " % (60*"-","\n", rc.pattern, nodeText2), outlineLevel=1, debugVar=gDbg7)
                        #changes = True
                        #count += 1
                        #countInDoc += 1
                        #nodeText = nodeText2

            ## now reparse datanode
            #if changes:
                #try:
                    #if gDbg7:
                        #print ("Old:", nodeTextHold)
                        #print ("New:", nodeText)
                    #newTree = hlString2xTree (nodeText, preface=preface, resolveEntities=False)
                #except Exception as e:
                    #logger.error("WARNING!!!!!  GlossaryRecognition.  Glossary Replacement makes this section unparseable.  Skipped: ")
                    #logger.error("Nodetext:$%s$ " % nodeText.encode("utf-8"))
                #else:
                    #countParas += 1
                    #try:
                        #tree.replaceCurrNode(newTree.RootNode)
                        ##if countParas == 20:
                            ##continue
                        ## print "Paracount: ", countParas
                    #except Exception as e:
                        #print ("Glossary Replace Exception: %s" % e)


        #retVal = count
        #print ("%s glossary terms recognized." % countInDoc)
        ## reset the tree position to the top
        #tree.Home()

        ## change impx's of TERM1 to TERM2 -- should be in L&P only
        ##count = tree.unwrapElements(ALL, elemSpec=E("impx", {"type":"TERM1"}))
        #count2 = tree.replaceAttrText("type", "TERM1", "TERM2", ALL, E("impx"))
        #if count2 > 0:
            #print ("*********************************************************************")
            #print ("***** Implied Links to L&P redirected to the PEP Glossary")
            #print ("*********************************************************************")


        ## ok, now add the IDs
        #self.addImpxIDs(tree)
        ##print "Final XML Text: ", tree.tree2Str()
        #tree.Home()

        ## return count of changed paragraphs
        #if gDbg2:
            #endTime = time.time()
            #timeDiff = endTime - startTime
            #print (80*"-")
            #print ("%d paragraphs marked with glossary terms in %s secs" % (countParas, timeDiff))

        #self.checkImpxs(tree)
        #if theGroupName != None:
            #self.removeSelfReferencesInGlossaries(tree, theGroupName)

        #return retVal

    #--------------------------------------------------------------------------------
    #def doGlossaryMarkupMethod2(self, tree, skipIfHasAncestor=E("abbr|artinfo|be|h[1-9]|cgrp|figx|frac|impx|ln|pgx|url|a|bx|bxe"), folioOutput=False, preface=None, theGroupName=None):
        #"""
        #Markup any glossary entries in paragraphs (only).

        #If theGroupName is supplied, it means we are marking up the glossary itself, and any impxs that match
        #theGroupName will be removed (as self referential)

        #Returns the number of changed terms.

        #>>> glossEngine = GlossaryRecognitionEngine(gather=False)
        #Gathering regex patterns is off.
        #1481 input patterns loaded into 1480 regex patterns.
        #>>> testXML= u'<body><p>My belief is that, διαφέρει although Freud was a revolutionary, most of his followers were more conventional. As is true of most institutions, as psychoanalysis aged, a conservatism overtook it. Foreground analytic theory incorporated the background cultural pathologizing of nonheterosexuality. Thus, the few articles written about lesbians rigidly followed narrow reductionistic explanations. Initially, these explanations followed classical theory, and then as psychoanalysis expanded into ego psychology and object relations, lesbian pathologizing was fit into these theories <bx r="B006">(Deutsch, 1995)</bx>.</p><p>For example, Adrienne Applegarth&apos;s 1984 American Psychoanalytic panel on homosexual women, used ego psychology to explain lesbianism. Applegarth viewed it (according to <bx r="B020">Wolfson, 1984</bx>), as a complicated structure of gratification and defense (p. <pgx r="B020">166</pgx>). She felt that if the steps in the usual positive and negative oedipal phases or if a girls wish for a baby arising out of penis envy become distorted, a range of outcomes, including homosexuality, could occur (Wolfson, <bx r="B020">1984</bx>, p. <pgx r="B020">166</pgx>).</p></body>'
        #>>> myt = hlString2xTree (testXML)
        #>>> glossEngine.doGlossaryMarkup(myt)
        #0 impx elements in non-allowed locations removed.
        #15
        #>>> testXML= '<body><p> forces. Brenner has suggested that the familiar  of the id, ego, and superego as agencies of <b id="10">the</b> mind.</p></body>'
        #>>> myt = hlString2xTree (testXML)
        #>>> print (glossEngine.doGlossaryMarkup(myt))
        #0 impx elements in non-allowed locations removed.
        #3

        #"""

        #global gDbg4  # for some reason, if this isn't three, it thinks gDbg4 is a local variable; but it's fine with gDbg2 (or 1)!
        #retVal = 0
        #count = 0
        ##preface="""<?xml version='1.0' encoding='UTF-8' ?><!DOCTYPE %s SYSTEM '%s'>""" % ("p", gDefaultDTD) + "\n"
        #preface = """<?xml version='1.0' encoding='UTF-8' ?>""" # TRY THIS TEST CODE 2017-04-02, without named entities, we should not need a DTD loaded (much quicker)

        #if gDbg2:
            #startTime = time.time()

        ## replacement pattern...if we need to add an ID, it probably needs to be done in a second pass (because
        ##       we are combining patterns.
        ## subStrCxt = """<impx type="TERM2">\g<whole></impx>"""
        ##leftMarker = u"⩥"
        ##rightMarker = u"⩤"
        #subStrCxt = """ %s\g<whole>%s""" % (self.leftMarker, self.rightMarker)
        ## strText = ""

        ## Replace altdata so it doesn't match - Better still, just delete it
        ## BUT NOTE: the altdata attribute in L&P is actually "alternate terms"! (not a display, altdata thing...).  That's why it matches sometimes.
        ##count = tree.replaceAttrText("altdata", "(.*)", "XXX\0", ALL, E("impx", {"type":"TERM1"}))
        #tree.deleteAttributes(ALL, elemSpec=E("impx", {"type":"TERM1"}), attrNamePtn="altdata")
        #countInDoc = 0
        #countParas = 0
        ## get all paragraphs
        #allParas = tree.getElements(ALL, elemSpec=E("p\Z|p2"), ancestorSpec=skipIfHasAncestor, notAncestor=True)
        #for para in allParas:
            #tree.Seek(para)
            #count = 0
            #if tree.CurPos.getchildren() == []:
                #nodeText = tree.CurPos.text
                #if tree.CurPos.text is not None:
                    #for rcrow in self.matchList:
                        ## Match at the start, at the end, the whole, and in the middle, delineated
                        #rc = rcrow[0]
                        #nodeText2 = rc.sub(subStrCxt, tree.CurPos.text)
                        #if nodeText2 != tree.CurPos.text:
                            ##if 1:
                                ##sciSupport.trace("%s%sMarked Abbr %s in %s: " % (60*"-","\n", rc.pattern, nodeText2), outlineLevel=1, debugVar=gDbg7)
                            #count += 1
                            #countInDoc += 1
                            #tree.CurPos.text = nodeText2
            #else:
                #for node in tree.CurPos.iter():
                    #for rcrow in self.matchList:
                        ## Match at the start, at the end, the whole, and in the middle, delineated
                        #rc = rcrow[0]
                        #if node.text is not None:
                            #nodeText = rc.sub(subStrCxt, node.text)
                            #if nodeText != node.text:
                                ##if 1:
                                    ##sciSupport.trace("%s%sMarked Abbr %s in %s: " % (60*"-","\n", rc.pattern, nodeText), outlineLevel=1, debugVar=gDbg7)
                                #count += 1
                                #countInDoc += 1
                                #node.text = nodeText
                                ## print (nodeText)

                        #if node.tail is not None:
                            #nodeTail = rc.sub(subStrCxt, node.tail)
                            #if nodeTail != node.tail:
                                ##if 1:
                                    ##sciSupport.trace("%s%sMarked Abbr %s in %s: " % (60*"-","\n", rc.pattern, nodeTail), outlineLevel=1, debugVar=gDbg7)
                                #count += 1
                                #countInDoc += 1
                                #node.tail = nodeTail
                                ## print (nodeTail)
            #if count > 0:
                #countParas += 1
                #paraTree = etree.tostring(para)
                #paraTree = re.sub('(&#10853;)+(?P<term>.*?)(&#10852;)+', ' <impx type="TERM2">\g<term></impx>', paraTree)
                #paraTree = re.sub("(&#10853;)|(&#10852;)", "", paraTree)
                ##paraTree = re.sub('(&#10853;)+', ' <impx type="TERM2">', paraTree)
                ##paraTree = re.sub('(&#10852;)+', '</impx>', paraTree)
                #tree.insertXMLStrReplaceNode(paraTree)

        #retVal = count
        #print ("%s glossary terms recognized." % countInDoc)

        ## reset the tree position to the top
        #tree.Home()

        ## change impx's of TERM1 to TERM2 -- should be in L&P only
        ##count = tree.unwrapElements(ALL, elemSpec=E("impx", {"type":"TERM1"}))
        #count2 = tree.replaceAttrText("type", "TERM1", "TERM2", ALL, E("impx"))
        #if count2 > 0:
            #print ("*********************************************************************")
            #print ("***** Implied Links to L&P redirected to the PEP Glossary")
            #print ("*********************************************************************")


        ## ok, now add the IDs
        #self.addImpxIDs(tree)
        ##print "Final XML Text: ", tree.tree2Str()
        #tree.Home()

        ## return count of changed paragraphs
        #if gDbg2:
            #endTime = time.time()
            #timeDiff = endTime - startTime
            #print (80*"-")
            #print ("%d paragraphs marked with glossary terms in %s secs" % (countParas, timeDiff))

        #self.checkImpxs(tree)
        #if theGroupName != None:
            #self.removeSelfReferencesInGlossaries(tree, theGroupName)

        #return retVal



#==================================================================================================
# Main Routines
#==================================================================================================

if __name__ == "__main__":
    """
	Run Test Routines
	"""

    import doctest
    doctest.testmod()
    sys.exit()