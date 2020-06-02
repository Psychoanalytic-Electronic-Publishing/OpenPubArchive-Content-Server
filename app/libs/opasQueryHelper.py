#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326

"""
opasQueryHelper

This library is meant to hold parsing and other functions which support query translation to Solr

2019.1205.1 - First version
2020.0416.1 - Sort fixes, new viewcount options
2020.0530.1 - Doc Test updates

"""
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2020.0530.1"
__status__      = "Development"

import re
import models
import opasCentralDBLib
import shlex

import logging
logger = logging.getLogger(__name__)

import schemaMap
import opasConfig 
import opasAPISupportLib

sourceDB = opasCentralDBLib.SourceInfoDB()
ocd = opasCentralDBLib.opasCentralDB()


def strip_outer_matching_chars(s, outer_char):
    """
    If a string has the same characters wrapped around it, remove them.
    Make sure the pair match.
    """
    s = s.strip()
    if (s[0] == s[-1]) and s.startswith(outer_char):
        return s[1:-1]
    return s
#-----------------------------------------------------------------------------
def search_qualifiers(searchstr, field_label, field_thesaurus=None, paragraph_len=25):
    """
    See if the searchstr has a special prefix qualifying the search
    
    [5]P> = within 5 paragraphs, P> (default one paragraph, paragraph_len)
    [5]W> = within 5 words
    T>    = Use Thesaurus 
    
    """
    ret_val = False # if there's no qualifier
    search_specs = None
    search_qual = "^\s*(?P<arg>[0-9]{0,3})(?P<op>[PWT])\s(?P<spec>.*)"
    m = re.match(search_qual, searchstr, re.IGNORECASE)
    if m:
        ret_val = True
        op = m.group("op").upper()
        spec = m.group("spec")
        arg = m.group("arg")
        if arg == "":
            arg = 1
        else:
            arg = int(arg)

        if op == "P":
            #  paragraph proximity
            distance = arg * paragraph_len
            search_specs = f'{field_label}:"{spec}"~{distance}'
        elif op == "W":
            distance = arg
            search_specs = f'{field_label}:"{spec}"~{distance}'
        elif op == "T":
            distance = arg
            # Thesaurus
            if field_thesaurus is not None:
                search_specs = f'{field_thesaurus}:"{spec}"~{distance}'
        else:
            raise Exception("Programming Error - RE Specification")
            
    return ret_val, search_specs

#-----------------------------------------------------------------------------
def comma_sep_list_to_simple_bool(termlist_str, boolpred="||"):
    """
    Take a comma separated term list or boolean list and change to a
    bool type query list using the single boolpred as connecting term (e.g., for solr)
    
    Really meant for comma separated lists, but in case use input has
    boolean connectors, it can remove those.
    
    **IMPORTANT: if your user is going to be entering boolean phrases, with various
      logical connectors, you should not be calling this for processing the list
    
    >>> a = "EN, IT,  FR"
    >>> comma_sep_list_to_simple_bool(a)
    'EN || IT || FR'
    
    >>> a = "EN AND IT OR  FR NOT EX"
    >>> comma_sep_list_to_simple_bool(a)
    'EN || IT || FR || EX'

    """
    # split it
    term_list = re.split("\W+", termlist_str)
    term_list = [val for val in term_list if val not in ("NOT", "OR", "AND")] # list(filter(("OR").__ne__, term_list))
    ret_val = f" {boolpred} ".join(term_list)
    return ret_val
#-----------------------------------------------------------------------------
def termlist_to_doubleamp_query(termlist_str, field=None):
    """
    Take a comma separated term list and change to a
    (double ampersand) type query term (e.g., for solr)
    
    >>> a = "tuckett, dav"
    >>> termlist_to_doubleamp_query(a)
    'tuckett && dav'
    >>> termlist_to_doubleamp_query(a, field="art_authors_ngrm")
    'art_authors_ngrm:tuckett && art_authors_ngrm:dav'

    """
    # in case it's in quotes in the string
    termlist_str = termlist_str.replace('"', '')
    # split it
    name_list = re.split("\W+", termlist_str)
    # if a field or function is supplied, use it
    if field is not None:
        name_list = [f"art_authors_ngrm:{x}"
                     for x in name_list if len(x) > 0]
    else:
        name_list = [f"{x}" for x in name_list]
        
    ret_val = " && ".join(name_list)
    return ret_val
#-----------------------------------------------------------------------------
class QueryTextToSolr(): 
    """
    This is a simple regex based word and phrase entry parser, intended to handle
      words and quoted phrases separated by ' and ' or ' or '.
      
    Syntax allowed:
      space separated list of words or phrases
      space separated list of words or phrases connected by AND or OR (with spaces as separation)
      negated words or phrases in quotes in above, where word or phrase prefixed by ^
      phrase in quotes followed by ~ and a number (for word proximity)
      parentheses for grouping the above
    
    >>> qs = QueryTextToSolr()
    >>> qs.boolConnectorsToSymbols("a and band")
    'a && band'
    
    """
    def __init__(self):
        regex_token_quoted =  "[\^]?[\'\"][^\'\"]+[\'\"]"
        regex_token_word = "(?P<word>[^\|\^\&\(\"\'\s)]+)"

        self.counter = 0
        self.token_quoted = re.compile(regex_token_quoted, re.IGNORECASE)
        self.token_or = re.compile("\sOR\s", re.IGNORECASE)
        self.token_and = re.compile("\sAND\s", re.IGNORECASE)
        self.token_not = re.compile("\snot\s")
        
        self.token_word = re.compile(regex_token_word, re.IGNORECASE)
        self.token_implied_and = re.compile("(^&&)+\s", re.IGNORECASE) 

    def boolConnectorsToSymbols(self, str_input):
        ret_val = str_input
        if ret_val is not None and ret_val != "":
            ret_val = self.token_or.sub(" || ", ret_val)
            ret_val = self.token_and.sub(" && ", ret_val)
            ret_val = self.token_not.sub(" NOT ", ret_val) # upper case a must
        
        return ret_val
        
    def markup(self, str_input, field_label, field_thesaurus=None):

        return self.boolConnectorsToSymbols(f"{field_label}:({str_input})")
    

#-----------------------------------------------------------------------------
def year_arg_parser(year_arg):
    """
    Look for fulll start/end year ranges submitted in a single field.
    Returns with Solr field name and proper syntax
    
    For example:
        >1977
        <1990
        1980-1990
        1970

    >>> year_arg_parser("=1955")
    '&& art_year_int:1970 '
    >>> year_arg_parser("1970")
    '&& art_year_int:1970 '
    >>> year_arg_parser("-1990")
    '&& art_year_int:[* TO 1990] '
    >>> year_arg_parser("1980-")
    '&& art_year_int:[1980 TO *] '
    >>> year_arg_parser("1980-1980")
    '&& art_year_int:[1980 TO 1980] '
    >>> year_arg_parser(">1977")
    '&& art_year_int:[1977 TO *] '
    >>> year_arg_parser("<1990")
    '&& art_year_int:[* TO 1990] '
    >>> year_arg_parser("1980-1990")
    '&& art_year_int:[1980 TO 1990] '
    """
    ret_val = None
    year_query = re.match("[ ]*(?P<option>[\>\^\<\=])?[ ]*(?P<start>[12][0-9]{3,3})?[ ]*(?P<separator>([-]|TO))*[ ]*(?P<end>[12][0-9]{3,3})?[ ]*", year_arg, re.IGNORECASE)            
    if year_query is None:
        logger.warning("Search - StartYear bad argument {}".format(year_arg))
    else:
        option = year_query.group("option")
        start = year_query.group("start")
        end = year_query.group("end")
        separator = year_query.group("separator")
        if start is None and end is None:
            logger.warning("Search - StartYear bad argument {}".format(year_arg))
        else:
            if option is None and separator is None:
                search_clause = f"&& art_year_int:{year_arg} "
            elif option == "=" and separator is None:
                search_clause = f"&& art_year_int:{year_arg} "
            elif separator == "-":
                # between
                # find endyear by parsing
                if start is None:
                    start = "*"
                if end is None:
                    end = "*"
                search_clause = f"&& art_year_int:[{start} TO {end}] "
            elif option == ">":
                # greater
                if start is None and end is not None:
                    start = end # they put > in start rather than end.
                search_clause = f"&& art_year_int:[{start} TO *] "
            elif option == "<":
                # less than
                if end is None and start is not None:
                    end = start  
                search_clause = f"&& art_year_int:[* TO {end}] "

            ret_val = search_clause

    return ret_val
                   
    
#---------------------------------------------------------------------------------------------------------
# this function lets various endpoints like search, searchanalysis, and document, share this large parameter set.
def parse_search_query_parameters(search=None,             # url based parameters, e.g., from previous search to be parsed
                                  # model based query specification, allows full specification 
                                  # of words/thes in request body, component at a time, per model
                                  solrQueryTermList=None,
                                  # parameter based options
                                  para_textsearch=None,    # search paragraphs as child of scope
                                  para_scope="doc",        # parent_tag of the para, i.e., scope of the para ()
                                  fulltext1=None,          # term, phrases, and boolean connectors with optional fields for full-text search
                                  #solrSearchQ=None,        # the standard solr (advanced) query, overrides other query specs
                                  synonyms=False,          # global field synonyn flag (for all applicable fields)
                                  # these are all going to the filter query
                                  source_name=None,        # full name of journal or wildcarded
                                  source_code=None,        # series/source (e.g., journal code) or list of codes
                                  source_type=None,        # series source type, e.g., video, journal, book
                                  source_lang_code=None,   # source language code
                                  vol=None,                # match only this volume (integer)
                                  issue=None,              # match only this issue (integer)
                                  author=None,             # author last name, optional first, middle.  Wildcards permitted
                                  title=None,
                                  articletype=None,        # types of articles: article, abstract, announcement, commentary, errata, profile, report, or review
                                  datetype=None,           # not implemented
                                  startyear=None,          # can contain complete range syntax
                                  endyear=None,            # year only.
                                  citecount=None, 
                                  viewcount=None,          # minimum view count
                                  viewperiod=None,         # period to evaluate view count 0-4
                                  facetfields=None,        # facetfields to return
                                  # sort field and direction
                                  sort=None, 
                                  # v1 parameters
                                  journal=None
                                  ):
    """
    This function parses various parameters in the api parameter and body to convert them
      to a Solr Query into model SolrQuerySpec.
      
    The optional parameter, solrQueryTermList holds a complete term by term query request,
    so it doesn't have to be parsed out and field and synonym can vary.

        Sample:
         {"query" : [
                            {
                                "words":"child abuse",
                                "parent": "doc",
                                "field": "para",
                                "synonyms": "true",
                        }
                    ]
         }        
        
    >>> search = parse_search_query_parameters(journal="IJP", vol=57, author="Tuckett")
    >>> search.solrQuery.analyzeThis
    'art_authors_text:(Tuckett) '
    
    """
    # always return SolrQueryOpts with SolrQuery
    if solrQueryTermList is not None:
        if solrQueryTermList.solrQueryOpts is not None:
            solrQueryOpts = solrQueryTermList.solrQueryOpts
        else: # initialize a new model
            solrQueryOpts = models.SolrQueryOpts()
    else: # initialize a new model
        solrQueryOpts = models.SolrQueryOpts()

    # Set up return structure
    solr_query_spec = \
        models.SolrQuerySpec(
                             core="pepwebdocs", # for now, this is tied to this core #TODO maybe change later
                             solrQuery = models.SolrQuery(),
                             solrQueryOpts=solrQueryOpts
        )
           
    # v1 translation:
    if journal is not None and journal != "":
        source_code = journal
    
    # parent_tag is any parent of a child doc as stored in the schema child field parent_tag.  

    # initialize accumulated variables
    search_q = "*:* "  # solr main query q
    filter_q = "*:* "  # for solr filter fq
    analyze_this = ""  # search analysis
    search_analysis_term_list = [] # component terms for search analysis

    # Hold these for special view counts
    vc_source_code = source_code # for view count query (if it can work this way)
    vc_source_name = source_name # for view count query (if it can work this way)
    vc_title = title # for view count query (if it can work this way)
    vc_author = author # for view count query (if it can work this way)

    # used to remove prefix && added to queries.  
    # Could make it global to save a couple of CPU cycles, but I suspect it doesn't matter
    # and the function is cleaner this way.
    pat_prefix_amps = re.compile("^\s*&& ")
    # this class can converts boolean operators AND/OR/NOT (case insensitive) to symbols ||, &&, ^
    # can do more but mainly using markup function for now.
    qparse = QueryTextToSolr()
    
    if sort is not None:  # not sure why this seems to have a slash, but remove it
        sort = re.sub("\/", "", sort)
        sort = re.split("\s|,", sort)
        try:
            psort, porder = sort
            plength = 2
        except:
            porder = None # set to default below
            plength = len(sort)
            if plength == 1:
                psort = sort[0]
            else:
                psort = None # falls to default below

        if psort is not None:
            psort = psort.lower()
        if porder is not None:
            porder = porder.lower()
            
        if porder == "a" or porder == "asc":
            porder = " asc"
        elif porder == "d" or porder == "desc":
            porder = " desc"
        else:
            if psort != "rank":
                porder = opasConfig.DEFAULT_SOLR_SORT_DIRECTION
            else:
                porder = " desc" # asc gives a memory error in solr

        if psort == "author":
            sort = f"art_authors_citation {porder}" #  new field 20200410 for sorting (author names citation format)!
        elif psort == "rank":
            sort = f"score {porder}"
        elif psort == "year":
            sort = f"art_year {porder}"
        elif psort == "source":
            sort = f"art_sourcetitleabbr {porder}"
        elif psort == "title":
            sort = f"art_title_xml {porder}" 
        elif psort in ["citecount5", "art_cited_5"]:
            if plength == 1: # default to desc, it makes the most sense
                sort = f"art_cited_5 desc"
            else: # sort was explicit, obey
                sort = f"art_cited_5 {porder}" # need the space here
        elif psort in ["citecount10", "art_cited_10"]:
            if plength == 1: # default to desc, it makes the most sense
                sort = f"art_cited_10 desc"
            else: # sort was explicit, obey
                sort = f"art_cited_10 {porder}" # need the space here
        elif psort in ["citecount20", "art_cited_20"]:
            if plength == 1: # default to desc, it makes the most sense
                sort = f"art_cited_20 desc"
            else: # sort was explicit, obey
                sort = f"art_cited_20 {porder}" # need the space here
        elif psort in ["citecountall", "art_cited_all"]:
            if plength == 1: # default to desc, it makes the most sense
                sort = f"art_cited_all desc"
            else: # sort was explicit, obey
                sort = f"art_cited_all {porder}" # need the space here
        else:
            sort = f"{opasConfig.DEFAULT_SOLR_SORT_FIELD} {opasConfig.DEFAULT_SOLR_SORT_DIRECTION}"
            
    if solrQueryTermList is not None:
        # used for a queryTermList structure which is typically sent via the API endpoint body.
        # It allows each term to set some individual patterns, like turning on synonyms and the field add-on for synonyns 
        q = ""
        for query in solrQueryTermList.query:
            if query.field is None:
                use_field = "para"
            else:
                use_field = query.field
    
            if q != "":
                q += " && "
                
            if query.synonyms:
                use_field = use_field + query.synonyms_suffix
            
            if query.parent is not None:
                solr_parent = schemaMap.user2solr(query.parent)
                
                q += "{!parent which='art_level:1'} art_level:2 AND parent_tag:%s AND %s:(%s) " % (solr_parent, use_field, query.words)
            else:
                if query.field is not None:
                    q += f"{use_field}:({query.words}) "
                else:
                    q += f"{query.words} "
    
        analyze_this = f"&& {q} "
        search_q += analyze_this
        search_analysis_term_list.append(analyze_this)

    if facetfields is not None:
        solr_query_spec.facetFields = opasAPISupportLib.string_to_list(facetfields)

    # note these are specific to pepwebdocs core.  #TODO Perhaps conditional on core later, or change to a class and do it better.
    if para_textsearch is not None:
        use_field = "para"
        if synonyms:
            use_field = use_field + "_syn"
    
        solrParent = schemaMap.user2solr(para_scope) # e.g., doc -> (body OR summaries OR appxs)
            
        # clean up query / connetors
        qs = QueryTextToSolr()
        para_textsearch = qs.boolConnectorsToSymbols(para_textsearch)
        # note: cannot use F strings here due to quoting requirements for 'which'
        if para_scope is not None:
            query = "{!parent which='art_level:1'} art_level:2 AND parent_tag:%s AND %s:(%s)" % (solrParent, use_field, para_textsearch)
        else:
            query = "{!parent which='art_level:1'} art_level:2 AND %s:(%s)" % (use_field, para_textsearch)

        analyze_this = f"&& {query} "
        search_q += analyze_this
        search_analysis_term_list.append(analyze_this)
    
    if fulltext1 is not None:
        # fulltext1 = qparse.markup(fulltext1, "text_xml")
        if synonyms:
            fulltext1 = fulltext1.replace("text:", "text_syn:")
            fulltext1 = fulltext1.replace("para:", "para_syn:")
            fulltext1 = fulltext1.replace("title:", "title_syn:")
            fulltext1 = fulltext1.replace("text_xml_offsite:", "text_xml_offsite_syn:")
            
        analyze_this = f"&& {fulltext1} "
        search_q += analyze_this
        search_analysis_term_list.append(analyze_this)
    
    if title is not None:
        title = title.strip()
        if title != '':
            title = qparse.markup(title, "art_title_xml")
            if synonyms:
                title = title.replace("art_title_xml:", "title_syn:")
            analyze_this = f"&& {title} "
            filter_q += analyze_this
            search_analysis_term_list.append(analyze_this)  

    if source_name is not None and source_name != "":
        # accepts a journal, book or video series name and optional wildcard.  No booleans.
        analyze_this = f"&& art_sourcetitlefull:({source_name}) "
        filter_q += analyze_this
        search_analysis_term_list.append(analyze_this)  

    if source_type is not None:  # source_type = book, journal, video ... (maybe more later)
        # accepts a source type or boolean combination of source types.
        source_type = qparse.markup(source_type, "art_sourcetype") # convert AND/OR/NOT, set up field
        analyze_this = f"&& {source_type} "
        filter_q += analyze_this
        search_analysis_term_list.append(analyze_this)  

    if source_lang_code is not None:  # source_language code, e.g., "EN" (added 2020-03, was omitted)
        # accepts a source language code list (e.g., EN, DE, ...).  If a list of codes with boolean connectors, changes to simple OR list
        if "," in source_lang_code:
            source_lang_code = comma_sep_list_to_simple_bool(source_lang_code) #  in case it's comma separated list, in any case, convert to ||

        source_lang_code = qparse.markup(source_lang_code, "art_lang") # convert AND/OR/NOT, set up field
        analyze_this = f"&& {source_lang_code} "
        filter_q += analyze_this
        search_analysis_term_list.append(analyze_this)  

    if source_code is not None and source_code != "":
        # accepts a journal or book code (no wildcards) or a list of journal or book codes (no wildcards)
        # ALSO can accept a single source name or partial name with an optional wildcard.  But
        #   that's really what argument source_name is for, so this is just extra and may be later removed.
        code_for_query = ""
        analyze_this = ""
        # journal_code_list_pattern = "((?P<namelist>[A-z0-9]*[ ]*\+or\+[ ]*)+|(?P<namelist>[A-z0-9]))"
        journal_wildcard_pattern = r".*\*[ ]*"  # see if it ends in a * (wildcard)
        if re.match(journal_wildcard_pattern, source_code):
            # it's a wildcard pattern, it's a full source name
            code_for_query = source_code
            analyze_this = f"&& art_sourcetitlefull:({code_for_query}) "
            filter_q += analyze_this
        else:
            journal_code_list = source_code.upper().split(" OR ")
            if len(journal_code_list) > 1:
                journal_code_list = " OR ".join(journal_code_list)
                # convert to upper case
                code_for_query = f"art_sourcecode:({journal_code_list})"
                # it was a list.
                analyze_this = f"&& {code_for_query} "
                filter_q += analyze_this
            else:
                sourceInfo = sourceDB.lookupSourceCode(source_code.upper())
                if sourceInfo is not None or source_code.upper().strip('0123456789') == opasConfig.BOOKSOURCECODE:
                    # it's a single source code
                    code_for_query = source_code.upper()
                    analyze_this = f"&& art_sourcecode:({code_for_query}) "
                    filter_q += analyze_this
                else: # not a pattern, or a code, or a list of codes.
                    # must be a name
                    code_for_query = source_code
                    analyze_this = f"&& art_sourcetitlefull:({code_for_query}) "
                    filter_q += analyze_this

        search_analysis_term_list.append(analyze_this)
        # or it could be an abbreviation #TODO
        # or it counld be a complete name #TODO

    if vol is not None:
        vol = qparse.markup(vol, "art_vol") # convert AND/OR/NOT, set up field query
        analyze_this = f"&& {vol} "
        filter_q += analyze_this
        search_analysis_term_list.append(analyze_this)  # Not collecting this!

    if issue is not None:
        issue = qparse.markup(issue, "art_iss") # convert AND/OR/NOT, set up field query
        analyze_this = f"&& {issue} "
        filter_q += analyze_this
        search_analysis_term_list.append(analyze_this)  # Not collecting this!

    if author is not None:
        author = author
        # if there's or and or not in lowercase, need to uppercase them
        # author = " ".join([x.upper() if x in ("or", "and", "not") else x for x in re.split("\s+(and|or|not)\s+", author)])
        author = qparse.markup(author, "art_authors_text") # convert AND/OR/NOT, set up field query
        analyze_this = f" && {author} " # search analysis
        filter_q += analyze_this        # query filter qf
        search_analysis_term_list.append(analyze_this)  

    if articletype is not None:
        # articletype = " ".join([x.upper() if x in ("or", "and", "not") else x for x in re.split("\s+(and|or|not)\s+", articletype)])
        articletype = qparse.markup(articletype, "art_type") # convert AND/OR/NOT, set up field query
        analyze_this = f"&& {articletype} "   # search analysis
        filter_q += analyze_this                         # query filter qf 
        search_analysis_term_list.append(analyze_this)
        
    if datetype is not None:
        #TODO for now, lets see if we need this. (We might not)
        pass

    if startyear is not None and endyear is None:
        # Only startyear specified, can use =. >, <, or - for range
        # parse startYear
        parsed_year_search = year_arg_parser(startyear)
        if parsed_year_search is not None:
            filter_q += parsed_year_search
            search_analysis_term_list.append(parsed_year_search)  
        else:
            logger.info(f"Search - StartYear bad argument {startyear}")

    if startyear is not None and endyear is not None:
        # put this in the filter query
        # should check to see if they are each dates
        if re.match("[12][0-9]{3,3}|\*", startyear) is None or re.match("[12][0-9]{3,3}|\*", endyear) is None:
            logger.info("Search - StartYear {} /Endyear {} bad arguments".format(startyear, endyear))
        else:
            analyze_this = f"&& art_year_int:[{startyear} TO {endyear}] "
            filter_q += analyze_this
            search_analysis_term_list.append(analyze_this)

    if startyear is None and endyear is not None:
        if re.match("[12][0-9]{3,3}", endyear) is None:
            logger.info(f"Search - Endyear {endyear} bad argument")
        else:
            analyze_this = f"&& art_year_int:[* TO {endyear}] "
            filter_q += analyze_this
            search_analysis_term_list.append(analyze_this)

    if citecount is not None:
        # This is the only citation query handled by GVPi and the current API.  But
        # the Solr database is set up so this could be easily extended to
        # the 10, 20, and "all" periods.  Here we add syntax to the 
        # citecount field, to allow the user to say:
        #  25 in 10 
        # which means 25 citations in 10 years
        # or 
        #  400 in ALL
        # which means 400 in all years. 
        # 'in' is required along with a space in front of it and after it
        # when specifying the period.
        # the default period is 5 years.
        # citecount = citecount.strip()
        val = None
        match_ptn = "\s*(?P<nbr>[0-9]+)(\s+TO\s+(?P<endnbr>[0-9]+))?(\s+IN\s+(?P<period>(5|10|20|All)))?\s*"
        m = re.match(match_ptn, citecount, re.IGNORECASE)
        if m is not None:
            val = m.group("nbr")
            val_end = m.group("endnbr")
            if val_end is None:
                val_end = "*"
            period = m.group("period")

        if val is None:
            val = 1
        if period is None:
            period = '5'

        analyze_this = f"&& art_cited_{period.lower()}:[{val} TO {val_end}] "
        filter_q += analyze_this
        search_analysis_term_list.append(analyze_this)
        
    # if viewcount == 0, then it's not a criteria needed (same as None)
    # if user inputs text instead, also no criteria.
    try:
        viewcount_int = int(viewcount)
    except:
        viewcount_int = 0
    
    if viewcount_int != 0:
        # bring back top documents viewed viewcount times

        view_periods = {
            0: "art_views_lastcalyear",
            1: "art_views_lastweek",
            2: "art_views_last1mos",
            3: "art_views_last6mos",
            4: "art_views_last12mos",
        }
         
        try:
            viewedwithin = int(viewedwithin) # note default is 4
        except:
            viewedwithin = 4 # default last 12 months
        else:
            # check range, set default if out of bounds
            if viewedwithin < 0 or viewedwithin > 4:
                viewedwithin = 4

        view_count_field = view_periods[viewedwithin]
        
        # Get the viewcounts from the database
        analyze_this = f"&& {view_count_field}:[{viewcount_int} TO *] "
        filter_q += analyze_this
        search_analysis_term_list.append(analyze_this)

    # now clean up the final components.
    if search_q is not None:
        # no need to start with '*:* && '.  Remove it.
        search_q = search_q.replace("*:* && ", "")

    if filter_q is not None:
        # no need to start with '*:* && '.  Remove it.
        filter_q = filter_q.replace("*:* && ", "")
       
    if analyze_this is not None:
        # no need to start with '&& '.  Remove it.
        analyze_this = pat_prefix_amps.sub("", analyze_this)
    
    if search_analysis_term_list is not []:
        search_analysis_term_list = [pat_prefix_amps.sub("", x) for x in search_analysis_term_list]  

    search_q = search_q.strip()
    filter_q = filter_q.strip()
    if search_q == "*:*" and filter_q == "*:*":
        filter_q = "art_level:1"

    solr_query_spec.solrQuery.searchQ = search_q
    solr_query_spec.solrQuery.filterQ = filter_q
    solr_query_spec.solrQuery.analyzeThis = analyze_this
    solr_query_spec.solrQuery.searchAnalysisTermList = search_analysis_term_list
    solr_query_spec.solrQuery.sort = sort
    
    return solr_query_spec

# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    import sys
    print ("Running in Python %s" % sys.version_info[0])

    import doctest
    doctest.testmod()
    print ("Fini. OpasQueryHelper Tests complete.")
    sys.exit()
    
    # this was a test for QueryTextToSolr class, the parser part, but not using that now.
    #tests = ["see dick run 'run dick run' ",
             #"road car truck semi or 'driving too fast'",
             #"or and not", 
             #"dog or 'fred flints*' and 'barney rubble'",
             #"dog and cat and ^provided", 
             #"dog and (cat or flea)",
             #"dog and ^(cat or flea)",
             #"dog or 'fred flintstone' and ^'barney rubble'",
             #"fr* and flintstone or ^barney",
             #"dog and (cat and flea)",
             #"dog or cat",
             #"fleet footed", 
             #"dog and ^cat or ^mouse and pig or hawk", 
             #"dog AND cat or 'mouse pig'", 
             #"dog AND cat or ^'mouse pig bird'",
             #"'freudian slip' or 'exposure therapy'"
             #]
    
    #label_word = "text_xml"
    #for n in tests:
        #mu = QueryTextToSolr()
        #print (n, ":", mu.markup(n, label_word))
    
