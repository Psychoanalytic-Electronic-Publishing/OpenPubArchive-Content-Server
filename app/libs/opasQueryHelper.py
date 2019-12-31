#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326

"""
opasQueryHelper

This library is meant to hold parsing and other functions which support query translation to Solr

2019.1205.1 - First version

"""
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2019.1205.1"
__status__      = "Development"

import re
import models
import opasCentralDBLib
import shlex

sourceDB = opasCentralDBLib.SourceInfoDB()

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
    a && band
    
    """
    def __init__(self):
        regex_token_quoted =  "[\^]?[\'\"][^\'\"]+[\'\"]"
        regex_token_word = "(?P<word>[^\|\^\&\(\"\'\s)]+)"
        # regex_word_or_quoted = f"{regex_token_quoted}|{regex_token_word}" 
        # token_not = re.compile("\sAND\s", re.IGNORECASE)

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
        #def quotedrepl(matchobj):
            #self.counter += 1
            #return f'QS{self.counter}'

        return self.boolConnectorsToSymbols(f"{field_label}:({str_input})")
    
        #if field_thesaurus is None:
            #field_thesaurus = field_label

        #qualified, sq = search_qualifiers(str_input, field_label=field_label, field_thesaurus=field_label)
        #if qualified:
            #ret_val = sq
        #else:
            #self.counter = 0
            #token_list = self.token_quoted.findall(str_input)
            #ret_val = self.token_quoted.sub(quotedrepl, str_input)
            #ret_val = re.sub("w\s*/\s*[0-9]{1,10}", "", ret_val)
            #term_check = ret_val.split()
            #i = 0
            #while 1:
                #if i == len(term_check) - 1:
                    #break
                #if re.match("&&|\|\||and|or", term_check[i].strip(), re.IGNORECASE) is None:
                    #if re.match("&&|\|\||and|or", term_check[i+1].strip(), re.IGNORECASE) is None:
                        ##  need to insert one!
                        #term_check.insert(i+1, "and")
                #i += 1
                
                        
            #ret_val = " ".join(term_check)
            
            #ret_val = self.token_or.sub(" || ", ret_val)
            #ret_val = self.token_and.sub(" && ", ret_val)
            #ret_val = self.token_word.sub(f"{field_label}:\g<word>", ret_val)
            #counter2 = 1
            ## take care of ^ to - before quotes go back
            #ret_val = re.sub("\^\s*\(", "-(", ret_val)
            #for n in token_list:
                #ret_val = re.sub(f"QS{counter2}", n, ret_val)
                #counter2 += 1
            
            #ptn_token_not = f"{field_label}:(\^)"
            #ptn_token_not2 = f"(\^){field_label}:"
            #ret_val = re.sub(ptn_token_not, f"-{field_label}:", ret_val)
            #ret_val = re.sub(ptn_token_not2, f"-{field_label}:", ret_val)
        
        ## debug only    
        ## print (str_input, ":", ret_val)
        #return ret_val

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

    >>> year_arg_parser("1970")
    '&& art_year_int:1970 '
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
            if option == "^":
                # between
                # find endyear by parsing
                if start is None:
                    start = end # they put > in start rather than end.
                elif end is None:
                    end = start # they put < in start rather than end.
                search_clause = "&& art_year_int:[{} TO {}] ".format(start, end)
            elif option == ">":
                # greater
                if start is None:
                    start = end # they put > in start rather than end.
                search_clause = "&& art_year_int:[{} TO {}] ".format(start, "*")
            elif option == "<":
                # less than
                if end is None:
                    end = start # they put < in start rather than end.
                search_clause = "&& art_year_int:[{} TO {}] ".format("*", end)
            else: # on
                if start is not None and end is not None:
                    # they specified a range anyway
                    search_clause = "&& art_year_int:[{} TO {}] ".format(start, end)
                elif start is None and end is not None:
                    # they specified '- endyear' without the start, so less than
                    search_clause = "&& art_year_int:[{} TO {}] ".format("*", end)
                elif start is not None and separator is not None:
                    # they mean greater than
                    search_clause = "&& art_year_int:[{} TO {}] ".format(start, "*")
                else: # they mean on
                    search_clause = "&& art_year_int:{} ".format(year_arg)

            ret_val = search_clause

    return ret_val
                   
    
#---------------------------------------------------------------------------------------------------------
# this function lets various endpoints like search, searchanalysis, and document, share this large parameter set.
def parse_search_query_parameters(search=None,
                                  def_type="lucene",  # standard query parser
                                  quick_search=None,  # simple google like
                                  search_field=None,  # search here
                                  search_type=None,
                                  thesaurus_expansion=False, 
                                  fulltext1=None,     # term, phrases, and boolean connectors for full-text search
                                  fulltext2=None,     # term, phrases, and boolean connectors for full-text search
                                  solrQ=None,         # advanced search
                                  disMax=None, 
                                  edisMax=None, 
                                  # these are all going to the filter
                                  journal_name=None,  # full name of journal or wildcarded
                                  journal=None,       # journal code or list of codes
                                  vol=None,           # match only this volume (integer)
                                  issue=None,         # match only this issue (integer)
                                  author=None,        # author last name, optional first, middle.  Wildcards permitted
                                  title=None,         
                                  datetype=None,  # not implemented
                                  startyear=None, # can contain complete range syntax
                                  endyear=None,   # year only.
                                  dreams=None,
                                  quotes=None,
                                  abstracts=None,
                                  dialogs=None,
                                  references=None,
                                  citecount=None, 
                                  viewcount=None, 
                                  viewedwithin=None, 
                                  sort=None, 
                                  ):
    """
    >>> search = parse_search_query_parameters(journal="IJP", vol=57, author="Tuckett")
    >>> search.analyzeThis
    'art_authors_ngrm:Tuckett '
    
    <QueryParameters analyzeThis='art_authors_ngrm:Tuckett ' searchQ='*:* ' filterQ='art_pepsourcecode:IJP && art_vol:57  && art_authors_ngrm:Tuckett ' searchAnalysisTermList=['art_pepsourcecode:IJP ', 'art_authors_ngrm:Tuckett '] solrMax=None solrSortBy=None urlRequest=''>    
    """
                
    # initialize accumulated variables
    search_q = "*:* "
    filter_q = "*:* "
    analyze_this = ""
    search_analysis_term_list = []
    # used to remove prefix && added to queries.  
    # Could make it global to save a couple of CPU cycles, but I suspect it doesn't matter
    # and the function is cleaner this way.
    pat_prefix_amps = re.compile("^\s*&& ")
    qparse = QueryTextToSolr()
    
    if sort is not None:  # not sure why this seems to have a slash, but remove it
        sort = re.sub("\/", "", sort)

    if quick_search is not None:
        if search_field is not None:
            analyze_this = f"&& {search_field}:({quick_search})"
        else:
            analyze_this = f"&& {quick_search} "
        search_q += analyze_this
        search_analysis_term_list.append(analyze_this)

    if fulltext1 is not None:
        # fulltext1 = qparse.markup(fulltext1, "text_xml")
        analyze_this = f"&& {fulltext1} "
        search_q += analyze_this
        search_analysis_term_list.append(analyze_this)

    if fulltext2 is not None:
        # we should use this for thesaurus later
        fulltext2 = qparse.markup(fulltext2, "text_xml")
        analyze_this = f"&& {fulltext2} "
        search_q += analyze_this
        search_analysis_term_list.append(analyze_this)

    if title is not None:
        title = qparse.markup(title, "art_title_xml")
        analyze_this = f"&& {title} "
        filter_q += analyze_this
        search_analysis_term_list.append(analyze_this)  

    if journal_name is not None:
        # accepts a journal name and optional wildcard
        analyze_this = f"&& art_pepsourcetitle_fulltext:{journal_name} "
        filter_q += analyze_this
        search_analysis_term_list.append(analyze_this)  

    if journal is not None:
        # accepts a journal code (no wildcards) or a list of journal codes
        # ALSO can accept a single journal name or partial name with an optional wildcard.  But
        #   that's really what argument journal_name is for, so this is just extra and may be later removed.
        code_for_query = ""
        analyze_this = ""
        # journal_code_list_pattern = "((?P<namelist>[A-z0-9]*[ ]*\+or\+[ ]*)+|(?P<namelist>[A-z0-9]))"
        journal_wildcard_pattern = r".*\*[ ]*"  # see if it ends in a * (wildcard)
        if re.match(journal_wildcard_pattern, journal):
            # it's a wildcard pattern
            code_for_query = journal
            analyze_this = f"&& art_pepsourcetitlefull:{code_for_query} "
            filter_q += analyze_this
        else:
            journal_code_list = journal.split(" or ")
            # convert to upper case
            journal_code_list = [f"art_pepsourcecode:{x.upper()}" for x in journal_code_list]
            if len(journal_code_list) > 1:
                # it was a list.
                code_for_query = " OR ".join(journal_code_list)
                analyze_this = f"&& ({code_for_query}) "
                filter_q += analyze_this
            else:
                sourceInfo = sourceDB.lookupSourceCode(journal.upper())
                if sourceInfo is not None:
                    # it's a single source code
                    code_for_query = journal.upper()
                    analyze_this = f"&& art_pepsourcecode:{code_for_query} "
                    filter_q += analyze_this
                else: # not a pattern, or a code, or a list of codes.
                    # must be a name
                    code_for_query = journal
                    analyze_this = f"&& art_pepsourcetitlefull:{code_for_query} "
                    filter_q += analyze_this

        search_analysis_term_list.append(analyze_this)
        # or it could be an abbreviation #TODO
        # or it counld be a complete name #TODO

    if vol is not None:
        analyze_this = f"&& art_vol:{vol} "
        filter_q += analyze_this
        #searchAnalysisTermList.append(analyzeThis)  # Not collecting this!

    if issue is not None:
        analyze_this = f"&& art_iss:{issue} "
        filter_q += analyze_this
        #searchAnalysisTermList.append(analyzeThis)  # Not collecting this!

    if author is not None:
        author = author 
        # add a && to the start to add to existng filter_q 
        analyze_this = f" && art_authors_text:{author} "
        filter_q += analyze_this
        search_analysis_term_list.append(analyze_this)  

    if datetype is not None:
        #TODO for now, lets see if we need this. (We might)
        pass

    if startyear is not None and endyear is None:
        # put this in the filter query
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
        if re.match("[12][0-9]{3,3}", startyear) is None or re.match("[12][0-9]{3,3}", endyear) is None:
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
        # This is the only query handled by GVPi and the current API.  But
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
            if val_end == None:
                val_end = "*"
            period = m.group("period")

        if val is None:
            val = 1
        if period is None:
            period = '5'

        analyze_this = f"&& art_cited_{period.lower()}:[{val} TO {val_end}] "
        filter_q += analyze_this
        search_analysis_term_list.append(analyze_this)

    if dreams is not None:
        # not within para 
        dreams = qparse.markup(dreams, "dreams_xml")
        analyze_this = f"&& {dreams} "
        search_q += analyze_this
        search_analysis_term_list.append(analyze_this)

    if quotes is not None:
        # not within para 
        quotes = qparse.markup(quotes, "quotes_xml")
        analyze_this = f"&& {quotes} "
        search_q += analyze_this
        search_analysis_term_list.append(analyze_this)

    if abstracts is not None:
        # not within para 
        abstracts = qparse.markup(abstracts, "abstracts_xml")
        analyze_this = f"&& {abstracts} "
        search_q += analyze_this
        search_analysis_term_list.append(analyze_this)

    if dialogs is not None:
        # not within para 
        dialogs = qparse.markup(dialogs, "dialogs_xml")
        analyze_this = f"&& {dialogs} "
        search_q += analyze_this
        search_analysis_term_list.append(analyze_this)

    if references is not None:
        # not within para 
        references = qparse.markup(references, "references_xml")
        analyze_this = f"&& {references} "
        search_q += analyze_this
        search_analysis_term_list.append(analyze_this)

    if solrQ is not None:
        search_q = solrQ # (overrides fields) # search = solrQ
        search_analysis_term_list = [solrQ]

    if disMax is not None:
        search_q = disMax # (overrides fields) # search = solrQ
        def_type = "dismax"

    if edisMax is not None:
        search_q = edisMax # (overrides fields) # search = solrQ
        def_type = "edismax"

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

    ret_val = models.QueryParameters(analyzeThis = analyze_this,
                                     searchQ = search_q,
                                     filterQ = filter_q,
                                     defType = def_type, # defType for Solr
                                     searchAnalysisTermList = search_analysis_term_list,
                                     solrSortBy = sort
    )

    return ret_val
                               

# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    import sys
    print ("Running in Python %s" % sys.version_info[0])

    import doctest
    doctest.testmod()    
    sys.exit()
    
    tests = ["see dick run 'run dick run' ",
             "road car truck semi or 'driving too fast'",
             "or and not", 
             "dog or 'fred flints*' and 'barney rubble'",
             "dog and cat and ^provided", 
             "dog and (cat or flea)",
             "dog and ^(cat or flea)",
             "dog or 'fred flintstone' and ^'barney rubble'",
             "fr* and flintstone or ^barney",
             "dog and (cat and flea)",
             "dog or cat",
             "fleet footed", 
             "dog and ^cat or ^mouse and pig or hawk", 
             "dog AND cat or 'mouse pig'", 
             "dog AND cat or ^'mouse pig bird'",
             "'freudian slip' or 'exposure therapy'"
             ]
    
    label_word = "text_xml"
    for n in tests:
        mu = QueryTextToSolr()
        print (n, ":", mu.markup(n, label_word))
    
