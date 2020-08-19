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

import logging
logger = logging.getLogger(__name__)

import schemaMap
import opasConfig 
import opasGenSupportLib as opasgenlib
import smartsearch

sourceDB = opasCentralDBLib.SourceInfoDB()
ocd = opasCentralDBLib.opasCentralDB()
pat_prefix_amps = re.compile("^\s*&& ")

def cleanup_solr_query(solrquery):
    """
    Clean up whitespace and extra symbols that happen when building up query or solr query filter

    """
    ret_val = solrquery.strip()
    ret_val = ' '.join(ret_val.split()) #solrquery = re.sub("\s+", " ", solrquery)
    ret_val = re.sub("\(\s+", "(", ret_val)
    ret_val = re.sub("\s+\)", ")", ret_val)
    
    if ret_val is not None:
        # no need to start with '*:* && '.  Remove it.
        ret_val = ret_val.replace("*:* && ", "")
        ret_val = ret_val.replace("*:* {", "{")  # if it's before a solr join for level 2 queries
        ret_val = pat_prefix_amps.sub("", ret_val)

    ret_val = re.sub("\s+(AND)\s+", " && ", ret_val, flags=re.IGNORECASE)
    ret_val = re.sub("\s+(OR)\s+", " || ", ret_val, flags=re.IGNORECASE)
 
    return ret_val

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
        self.token_or = re.compile("\s+OR\s+", re.IGNORECASE)
        self.token_and = re.compile("\s+AND\s+", re.IGNORECASE)
        self.token_not = re.compile("\s+not\s+")
        
        self.token_word = re.compile(regex_token_word, re.IGNORECASE)
        self.token_implied_and = re.compile("(^&&)+\s", re.IGNORECASE) 

    def boolConnectorsToSymbols(self, str_input):
        ret_val = str_input
        if ret_val is not None and ret_val != "":
            ret_val = self.token_or.sub(" || ", ret_val)
            ret_val = self.token_and.sub(" && ", ret_val)
            ret_val = self.token_not.sub(" NOT ", ret_val) # upper case a must
        
        return ret_val
        
    def markup(self, str_input, field_label, field_thesaurus=None, quoted=False):

        if quoted == False:
            ret_val = self.boolConnectorsToSymbols(f"{field_label}:({str_input})")
        else:
            ret_val = self.boolConnectorsToSymbols(f'{field_label}:("{str_input}")')
        
        ret_val = re.sub("([A-Z]\.)([A-Z])", "\g<1> \g<2>", ret_val)
        return ret_val    

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
    '&& art_year_int:=1955 '
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
                   
    
def get_term_list_spec(termlist):
    """
    Process termlists with recursion capabilities
    
    """
    ret_val = ""
    for q_term in termlist:
        try:
            boolean_connector = q_term.connector
        except:
            boolean_connector = ""

        q_term_sublist = []
        try:
            q_term_sublist = q_term.subClause
        except:
            q_term_sublist = []
            
        if q_term_sublist != []:
            ret_val += f"{boolean_connector} ({get_term_list_spec(q_term_sublist)})"
        else:
            if q_term.field is None:
                use_field = "text"
            else:
                use_field = q_term.field
    
            if q_term.synonyms:
                use_field = use_field + q_term.synonyms_suffix
            
            if use_field is not None and q_term.words is not None:
                sub_clause = f"{use_field}:({q_term.words})"
            else:
                if q_term.words is not None:
                    sub_clause = f"({q_term.words})"
                else:
                    sub_clause = ""
            if ret_val == "":
                ret_val += f"{sub_clause} "
            else:
                ret_val += f" {boolean_connector} {sub_clause}"

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
                                  like_this_id=None,       # for morelikethis
                                  similar_count:int=0, # Turn on morelikethis for the set
                                  fulltext1=None,          # term, phrases, and boolean connectors with optional fields for full-text search
                                  smarttext=None,          # experimental detection of search parameters
                                  #solrSearchQ=None,       # the standard solr (advanced) query, overrides other query specs
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
                                  facetmincount=1,
                                  facetlimit=None,
                                  facetoffset=0,
                                  facetspec: dict={}, 
                                  abstract_requested: bool=False,
                                  format_requested:str="HTML", 
                                  sort=None,
                                  extra_context_len=None,
                                  limit=None,
                                  offset=None, 
                                  # v1 parameters
                                  journal = None,
                                  req_url = None
                                  ):
    """
    This function parses various parameters in the api parameter and body to convert them
      to a Solr Query into model SolrQuerySpec.
      
    The optional parameter, solrQueryTermList holds a complete term by term query request,
    so field and synonym can vary.

        Sample:
            {   "artLevel": 2, 
                "query" :
                [
                    {
                        "field" : "para",
                        "words": "love",
                        "synonyms": "true",
                        "synonyms_suffix": "_syn"
                    },
                    {
                        "connector": "AND",
                        "field" : "para",
                        "words": "joy"
                    }
                ],
                "qfilter" : 
                [
                    {
                        "comment":"This example should produce the filter 'art_source_code:AOP && (art_year:1977 || art_year:2000)'",
                        "field" : "art_sourcecode",
                        "words": "AOP"
                    },
                    {
                        "field" : "art_year",
                        "words": "1977"
                    }
                ]
            }        

    >>> search = parse_search_query_parameters(journal="IJP", vol=57, author="Tuckett")
    >>> search.solrQuery.analyzeThis
    'art_authors_text:(Tuckett)'
    
    """
    artLevel = 1 # Doc query, sets to 2 if clauses indicate child query
    search_q_prefix = ""
    
    if isinstance(synonyms, str):
        logger.warning("Synonyms parameter should be bool, not str")
        if synonyms.lower() == "true":
            synonyms = True
        else:
            synonyms = False

    # always return SolrQueryOpts with SolrQuery
    if solrQueryTermList is not None:
        try:
            if solrQueryTermList.solrQueryOpts is not None:
                solrQueryOpts = solrQueryTermList.solrQueryOpts
            else: # initialize a new model
                solrQueryOpts = models.SolrQueryOpts()
        except Exception as e:
            solrQueryTermList = None
            solrQueryOpts = models.SolrQueryOpts()
            if isinstance(solrQueryTermList, str):
                logger.warning(f"solrQueryTermList must be a model {e}")
            else:
                logger.warning(f"solrQueryTermList error {e}")

        if solrQueryTermList.abstractReturn is not None and abstract_requested is None:
            abstract_requested = solrQueryTermList.abstractReturn

        if solrQueryTermList.facetFields is not None and facetfields is None:
            facetfields = solrQueryTermList.facetFields

        if solrQueryTermList.facetMinCount is not None and facetmincount is None:
            facetmincount = solrQueryTermList.facetMinCount

        if solrQueryTermList.facetSpec != {} and facetspec == {}:
            facetspec = solrQueryTermList.facetSpec

        if solrQueryTermList.returnFormat is not None and format_requested is None:
            format_requested = solrQueryTermList.returnFormat
    
        if solrQueryTermList.similarCount != 0 and similar_count == 0:
            similar_count = solrQueryTermList.similarCount
                
    else: # initialize a new model (qtermlist didn't supply and no other upper structure passed)
        solrQueryOpts = models.SolrQueryOpts()

    # Set up return structure
    solr_query_spec = \
        models.SolrQuerySpec(
                             core="pepwebdocs", # for now, this is tied to this core #TODO maybe change later
                             solrQuery = models.SolrQuery(),
                             solrQueryOpts=solrQueryOpts,
                             req_url=req_url
        )

    if limit is not None:
        solr_query_spec.limit = limit

    if offset is not None:
        solr_query_spec.offset = offset
        
    if extra_context_len is not None:
        solr_query_spec.solrQueryOpts.hlFragsize = extra_context_len
           
    # v1 translation:
    if journal is not None and journal != "":
        source_code = journal

    if similar_count > 0:
        solr_query_spec.solrQueryOpts.moreLikeThisCount = similar_count
        # solr_query_spec.solrQueryOpts.moreLikeThis = True

    if like_this_id is not None:
        solr_query_spec.solrQuery.likeThisID = like_this_id
    
    # parent_tag is any parent of a child doc as stored in the schema child field parent_tag.  

    # initialize accumulated variables
    search_q = "*:* "  # solr main query q
    filter_q = "*:* "  # for solr filter fq
    analyze_this = ""  # search analysis
    search_analysis_term_list = [] # component terms for search analysis
    query_term_list = [] #  the terms themselves

    # Hold these for special view counts
    #vc_source_code = source_code # for view count query (if it can work this way)
    #vc_source_name = source_name # for view count query (if it can work this way)
    #vc_title = title # for view count query (if it can work this way)
    #vc_author = author # for view count query (if it can work this way)

    # used to remove prefix && added to queries.  
    # Could make it global to save a couple of CPU cycles, but I suspect it doesn't matter
    # and the function is cleaner this way.
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
                porder = opasConfig.DEFAULT_SOLR_SORT_DIRECTION
            else:
                psort = None 
                porder = opasConfig.DEFAULT_SOLR_SORT_DIRECTION

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
            sort = f"title {porder}" 
        elif psort in ["citecount5", "art_cited_5", "citecount"]:
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

    if smarttext is not None:
        search_dict = smartsearch.smart_search(smarttext)
        # set up parameters as a solrQueryTermList to share that processing
        # solr_query_spec.solrQueryOpts.qOper = "OR"
        schema_field = search_dict.get("schema_field")
        limit = 0
        if schema_field is not None:
            schema_value = search_dict.get("schema_value")
            if "'" in schema_value or '"' in schema_value:
                search_q += f"&& {schema_field}:{schema_value} "
            else:
                search_q += f"&& {schema_field}:({schema_value}) "
            limit = 1
        else:
            syntax = search_dict.get("syntax")
            if syntax is not None:
                if syntax == "solr" and search_q == "*:*":
                    query = search_dict.get("query")
                    search_q = f"{query}"
                    limit = 1
            else:
                doi = search_dict.get("doi")
                if doi is not None:
                    filter_q += f"&& art_doi:({doi}) "
                    limit = 1
                    
        if limit == 0: # not found special token
            art_id = search_dict.get("art_id")
            if art_id is not None:
                limit = 1
                filter_q += f"&& art_id:({art_id}) "
            else:
                art_vol = search_dict.get("vol")
                if art_vol is not None:
                    if vol is None:
                        vol = art_vol.lstrip("0")
        
                art_pgrg = search_dict.get("pgrg")
                if art_pgrg is not None:
                    # art_pgrg1 = art_pgrg.split("-")
                    if "-" in art_pgrg:
                        filter_q += f"&& art_pgrg:({art_pgrg}) "
                    else:
                        filter_q += f"&& art_pgrg:({art_pgrg}-*) "
        
                art_yr = search_dict.get("yr")
                if art_yr is not None:
                    if startyear is None and endyear is None:
                        startyear = art_yr
        
                art_authors = search_dict.get("author_list")
                if art_authors is not None:
                    if author is None:
                        author = art_authors
                
                art_author = search_dict.get("author")
                if art_author is not None:
                    if author is None:
                        author = f'"{art_author}"'
    
                title_search = search_dict.get("title")
                if title_search is not None:
                    if title is None:
                        title = title_search
                        
                word_search = search_dict.get("wordsearch")
                if word_search is not None:
                    if para_textsearch is None:
                        para_textsearch = word_search
            

    if para_textsearch is not None:
        # set up parameters as a solrQueryTermList to share that processing
        query_term_from_params = [
                                    models.SolrQueryTerm (
                                                          connector="AND", 
                                                          parent = para_scope,
                                                          field = "para",
                                                          words = para_textsearch,
                                                          synonyms = synonyms,
                                                          synonyms_suffix = opasConfig.SYNONYM_SUFFIX
                                                        )
                                 ]

        #  if a term list is supplied, add it to the list, otherwise, create list
        if solrQueryTermList is None:
            solrQueryTermList = models.SolrQueryTermList(qt=query_term_from_params)
            solrQueryTermList.artLevel = 2;
        else:
            solrQueryTermList.qt.extend(query_term_from_params)
            solrQueryTermList.artLevel = 2;           

    if solrQueryTermList is not None:
        # used for a queryTermList structure which is typically sent via the API endpoint body.
        # It allows each term to set some individual patterns, like turning on synonyms and the field add-on for synonyns
        # Right now, handles two levels...not sure yet how to do 3 if it ever comes to pass.
        # NOTE: default is now 1 for artLevel. Always specify it otherwise
        if solrQueryTermList.artLevel is None:
            artLevel = 1
        else:
            artLevel = solrQueryTermList.artLevel
            
        query_sub_clause = ""
        if artLevel == 2:
            # Set up child search prefix
            search_q_prefix = "{!parent which='art_level:1'} art_level:2 "
        else:
            search_q_prefix = ""
        
        # look for query clauses in body queryTermList       
        last_parent = None
        query = models.SolrQueryTerm()
        for query in solrQueryTermList.qt:
            boolean_connector = query.connector
            if artLevel == 2:
                if query.parent is None:
                    solr_parent = schemaMap.user2solr("doc") # default
                else:
                    solr_parent = schemaMap.user2solr(query.parent)

                if last_parent is None:
                    last_parent = solr_parent

                if last_parent != solr_parent:
                    boolean_connector = " || " # otherwise it will always rsult in empty sete

            if query.field is None:
                if artLevel == 2:
                    use_field = "para"
                else:
                    use_field = "text"
            else:
                use_field = query.field
    
            if query.synonyms:
                use_field = use_field + query.synonyms_suffix
            
            if use_field is not None and query.words is not None:
                sub_clause = f"{use_field}:({query.words})"
            else:
                if query.words is not None:
                    sub_clause = f"({query.words})"
                else:
                    sub_clause = ""

            query_term_list.append(sub_clause)
            
            if query_sub_clause != "":
                query_sub_clause += boolean_connector
                
            if artLevel == 2 and solr_parent is not None:
                query_sub_clause += f" (parent_tag:{solr_parent} AND {sub_clause}) "
            else:
                query_sub_clause += f" {sub_clause}"
        
        if query_sub_clause != "":
            analyze_this = f"{search_q_prefix} && ({query_sub_clause})"
            #if search_q_prefix == "":
            #else:
                #analyze_this = f"&& {search_q_prefix} {query_sub_clause}"

            search_q += analyze_this
            search_analysis_term_list.append(analyze_this)

        # now look for filter clauses in body queryTermList       
        filter_sub_clause = ""
        qfilterTerm = ""
        filter_sub_clause = get_term_list_spec(solrQueryTermList.qf)
        #for qfilter in solrQueryTermList.qf:
            #boolean_connector = qfilter.connector
            #qfilterTerm += f"({boolean_connector} {get_term_list_spec(qfilter)})"

            #if qfilter.subField != []:
                #for qfilterSub in qfilter.subField:
                
            #if qfilter.field is None:
                #use_field = "text"
            #else:
                #use_field = qfilter.field
    
            #if qfilter.synonyms:
                #use_field = use_field + qfilter.synonyms_suffix
            
            #if use_field is not None and qfilter.words is not None:
                #sub_clause = f"{use_field}:({qfilter.words})"
            #else:
                #if query.words is not None:
                    #sub_clause = f"({qfilter.words})"
                #else:
                    #sub_clause = ""
            #if qfilterTerm == "":
                #qfilterTerm += f"{sub_clause}"
            #else:
                #qfilterTerm += f" {boolean_connector} {sub_clause}"
    
        if filter_sub_clause != "":
            analyze_this = f"&& ({filter_sub_clause})"
            filter_q += analyze_this
            search_analysis_term_list.append(analyze_this)

    if facetfields is not None:
        solr_query_spec.facetFields = opasgenlib.string_to_list(facetfields)
        solr_query_spec.facetMinCount=facetmincount
        solr_query_spec.facetSpec = facetspec
        if facetlimit is not None:
            solr_query_spec.facetSpec["facet_limit"] = facetlimit
        if facetoffset is not None:
            solr_query_spec.facetSpec["facet_offset"] = facetoffset
            
        #solr_query_spec.facetLimit=facetmincount,
        #solr_query_spec.facetOffset=facetoffset,                                                        

    # note these are specific to pepwebdocs core.  #TODO Perhaps conditional on core later, or change to a class and do it better.
    #if para_textsearch is not None:
        #artLevel = 2 # definitely child level
        #search_q_prefix = "{!parent which='art_level:1'} art_level:2 &&"

        #use_field = "para"
        #if synonyms:
            #use_field = use_field + "_syn"
    
        #solrParent = schemaMap.user2solr(para_scope) # e.g., doc -> (body OR summaries OR appxs)
            
        ## clean up query / connetors
        #qs = QueryTextToSolr()
        #para_textsearch = qs.boolConnectorsToSymbols(para_textsearch)
        ## note: cannot use F strings here due to quoting requirements for 'which'
        #if para_scope is not None:
            #query = " (parent_tag:%s AND (%s:(%s)))" % (solrParent, use_field, para_textsearch)
        #else:
            #query = " (%s:(%s))" % (use_field, para_textsearch)

        #analyze_this = f"{search_q_prefix}{query} "
        #search_q += analyze_this
        #search_analysis_term_list.append(analyze_this)
        #query_term_list.append(f"{use_field}:{para_textsearch}")
    
    if fulltext1 is not None:
        #  if there are no field specs in the fulltext spec
        if ":" not in fulltext1:
            fulltext1 = qparse.markup(fulltext1, "text")

        if synonyms:
            fulltext1 = fulltext1.replace("text:", "text_syn:")
            fulltext1 = fulltext1.replace("para:", "para_syn:")
            fulltext1 = fulltext1.replace("title:", "title_syn:")
            fulltext1 = fulltext1.replace("text_xml_offsite:", "text_xml_offsite_syn:")
            
        analyze_this = f"&& {fulltext1} "
        if artLevel == 1:
            search_q += analyze_this
            filter_q += "&& art_level:1 "
        else: # we are looking at a child query, so put top level queries in the filter.
            filter_q += analyze_this
            
        search_analysis_term_list.append(analyze_this)
        query_term_list.append(fulltext1)
    
    if title is not None:
        title = title.strip()
        if title != '':
            title = qparse.markup(title, "title")
            if synonyms:
                title = title.replace("title:", "title_syn:")
            analyze_this = f"&& {title} "

            if artLevel == 1:
                search_q += analyze_this
            else: # we are looking at a child query, so put top level queries in the filter.
                filter_q += analyze_this

            search_analysis_term_list.append(analyze_this)  
            query_term_list.append(title)

    if source_name is not None and source_name != "":
        # accepts a journal, book or video series name and optional wildcard.  No booleans.
        analyze_this = f"&& art_sourcetitlefull:({source_name}) "
        filter_q += analyze_this
        search_analysis_term_list.append(analyze_this)
        query_term_list.append(f"art_sourcetitlefull:({source_name})")       

    if source_type is not None:  # source_type = book, journal, video ... (maybe more later)
        # accepts a source type or boolean combination of source types.
        source_type = qparse.markup(source_type, "art_sourcetype") # convert AND/OR/NOT, set up field
        analyze_this = f"&& {source_type} "
        filter_q += analyze_this
        search_analysis_term_list.append(analyze_this)  
        query_term_list.append(source_type)       

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
        # art_authors_citation:("tuckett, D.") OR art_authors_text:("tuckett, David")
        author_text = qparse.markup(author, "art_authors_text", quoted=False) # convert AND/OR/NOT, set up field query
        author_cited = qparse.markup(author, "art_authors_citation", quoted=False)
        analyze_this = f' && ({author_text} || {author_cited}) ' # search analysis
        filter_q += analyze_this        # query filter qf
        search_analysis_term_list.append(analyze_this)  
        query_term_list.append(author)       

    if articletype is not None:
        # articletype = " ".join([x.upper() if x in ("or", "and", "not") else x for x in re.split("\s+(and|or|not)\s+", articletype)])
        articletype = qparse.markup(articletype, "art_type") # convert AND/OR/NOT, set up field query
        analyze_this = f"&& {articletype} "   # search analysis
        filter_q += analyze_this                         # query filter qf 
        search_analysis_term_list.append(analyze_this)
        query_term_list.append(articletype)       
        
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
        
        analyze_this = f"&& {view_count_field}:[{viewcount_int} TO *] "
        filter_q += analyze_this
        search_analysis_term_list.append(analyze_this)

    # now clean up the final components.
    search_q = cleanup_solr_query(search_q)
    filter_q = cleanup_solr_query(filter_q)
    analyze_this = cleanup_solr_query(analyze_this)
    # get rid of extra spaces first, for consistency of matching.

    #if analyze_this is not None:
        ## no need to start with '&& '.  Remove it.
        #analyze_this = pat_prefix_amps.sub("", analyze_this)
    
    if search_analysis_term_list is not []:
        search_analysis_term_list = [cleanup_solr_query(x) for x in search_analysis_term_list]  

    if search_q == "*:*" and filter_q == "*:*":
        filter_q = "art_level:1"

    solr_query_spec.abstractReturn = abstract_requested
    solr_query_spec.returnFormat = format_requested # HTML, TEXT_ONLY, XML
    solr_query_spec.solrQuery.searchQ = search_q
    solr_query_spec.solrQuery.searchQPrefix = search_q_prefix
    solr_query_spec.solrQuery.filterQ = filter_q
    solr_query_spec.solrQuery.analyzeThis = analyze_this
    solr_query_spec.solrQuery.searchAnalysisTermList = search_analysis_term_list
    solr_query_spec.solrQuery.queryTermList = query_term_list
    solr_query_spec.solrQuery.sort = sort
    
    return solr_query_spec

#================================================================================================================
def parse_to_query_spec(solr_query_spec: models.SolrQuerySpec = None,
                        core = None, 
                        req_url = None, 
                        query = None, 
                        filter_query = None,
                        query_debug = None,
                        similar_count = None,
                        full_text_requested = None,
                        abstract_requested = None, 
                        file_classification = None, 
                        format_requested = None,
                        def_type = None,
                        summary_fields=opasConfig.DOCUMENT_ITEM_SUMMARY_FIELDS, 
                        highlight_fields = None,
                        facet_fields = None,
                        facet_mincount = None, 
                        extra_context_len = None,
                        maxKWICReturns = None,
                        sort= None,
                        limit = None, 
                        offset = None,
                        page_offset = None,
                        page_limit = None,
                        page = None
                        ):
    """
    This function creates or updates a SolrQuerySpec, with the caller specifying the Solr query and filter query fields
    and other options directly.

    The caller sends the Query using the models.SolrQuerySpec, with the option of including other parameters to override
    the values in models.SolrQuerySpec.
    
    """
    if solr_query_spec is None:
        #  create it
        
        solr_query_spec = models.SolrQuerySpec(
                                               solrQuery=models.SolrQuery(), 
                                               solrQueryOpts=models.SolrQueryOpts()
        )
        
    if solr_query_spec.solrQuery is None:
        solr_query_spec.solrQuery = models.SolrQuery() 
    
    if solr_query_spec.solrQueryOpts is None:
        solr_query_spec.solrQueryOpts = models.SolrQueryOpts() 
    
    solr_query_spec.returnFields = summary_fields 

    # parameters specified override QuerySpec
    
    if file_classification is not None:
        solr_query_spec.fileClassification = file_classification 

    if query_debug is not None:
        solr_query_spec.solrQueryOpts.queryDebug = query_debug 

    if solr_query_spec.solrQueryOpts.queryDebug != "on":
        solr_query_spec.solrQueryOpts.queryDebug = "off"

    if req_url is not None:
        solr_query_spec.urlRequest = req_url

    if full_text_requested is not None:
        solr_query_spec.fullReturn = full_text_requested

    if abstract_requested is not None:
        solr_query_spec.abstractReturn = abstract_requested 

    if format_requested is not None:
        solr_query_spec.returnFormat = format_requested

    if limit is not None:
        solr_query_spec.limit = limit

    if offset is not None:
        solr_query_spec.offset = offset

    if page_offset is not None:
        solr_query_spec.page_offset = page_offset

    if page_limit is not None:
        solr_query_spec.page_limit = page_limit

    if page is not None:
        solr_query_spec.page = page

    # part of the query model

    if query is not None:
        solr_query_spec.solrQuery.searchQ = query
        
    if solr_query_spec.solrQuery.searchQ is None:
        solr_query_spec.solrQuery.searchQ = "*:*"       

    if filter_query is not None:
        solr_query_spec.solrQuery.filterQ = filter_query

    if solr_query_spec.solrQuery.filterQ is not None:
        # for logging/debug
        solr_query_spec.solrQuery.filterQ = solr_query_spec.solrQuery.filterQ.replace("*:* && ", "")
        logger.debug("Solr FilterQ: %s", filter_query)
    else:
        solr_query_spec.solrQuery.filterQ = "*:*"
        
    #  clean up spaces and cr's from in code readable formatting
    if solr_query_spec.returnFields is not None:
        solr_query_spec.returnFields = ", ".join(e.lstrip() for e in solr_query_spec.returnFields.split(","))

    if sort is not None:
        solr_query_spec.solrQuery.sort = sort

    #  part of the options model

    if similar_count is not None:
        solr_query_spec.solrQueryOpts.moreLikeThisCount = similar_count
        
    if def_type is not None:
        solr_query_spec.solrQueryOpts.defType = def_type 

    if highlight_fields is not None:
        solr_query_spec.solrQueryOpts.hlFields = highlight_fields 

    if facet_fields is not None:
        facet_fields = opasgenlib.string_to_list(facet_fields)
        solr_query_spec.facetFields = facet_fields 
    else:
        facet_fields = opasgenlib.string_to_list(solr_query_spec.facetFields)
        solr_query_spec.facetFields = facet_fields 
        
    if facet_mincount is not None:
        solr_query_spec.facetMinCount = facet_mincount
        
    if extra_context_len is not None:
        solr_query_spec.solrQueryOpts.hlFragsize = max(extra_context_len, opasConfig.DEFAULT_KWIC_CONTENT_LENGTH)
    else:
        solr_query_spec.solrQueryOpts.hlFragsize = opasConfig.DEFAULT_KWIC_CONTENT_LENGTH

    if maxKWICReturns is not None:
        solr_query_spec.solrQueryOpts.hlSnippets = maxKWICReturns 
       
    ret_val = solr_query_spec
    
    return ret_val


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
    
