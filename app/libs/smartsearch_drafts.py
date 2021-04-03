#-----------------------------------------------------------------------------
def smart_search4(smart_search_text):
    """
    Function to take an input string and parse out information to do a search against the DOCS core schema.
    
    Some simple syntax is implemented to help identify certain functionality.
    
        search_field:terms  = Solr field from schema, search terms against it.  (Will be presented
            to solr as field:(terms).  Multiple terms are permitted, but currently, only one field
            specification is permitted.  Field names are converted to lower case automatically.
            
            art_doi:10.1111/j.1745-8315.2012.00606.x
            art_authors_text:[tuckett and fonagy]            
           
        doi = Just enter a DOI
           10.1111/j.1745-8315.2012.00606.x 
        
        AuthorName Year = One or more names (initial capital), followed by a year
            Tuckett and Fonagy 1972
            Tuckett and Fonagy (1972)
            
    >>> ret_dict = smart_search("'the cat in the hat was that'")
    >>> ret_dict['search_clause'], ret_dict['search_type']
    (" && text:('the cat in the hat was that')", 'literal search')
    
    # pattern 1 tests
    >>> ret_dict = smart_search("solr::art_authors_text:[tuckett and fonagy]")
    >>> ret_dict['search_clause'], ret_dict['search_type']
    (' && art_authors_text:[tuckett and fonagy]', 'solr field')

    >>> ret_dict = smart_search("authors:Tuckett, D.")
    >>> ret_dict['search_clause'], ret_dict['search_type']
    (' && authors:(Tuckett, D.)', 'solr advanced')

    # pattern 2 tests
    >>> ret_dict = smart_search("Freud, S. ( 1938), Some elementary lessons in psycho-analysis, Standard Edition. 23:279-286. pp. London: Hogarth Press, 1964.")
    >>> ret_dict['search_clause'], ret_dict['search_type']
    ('&& author_list:Freud, S.  && yr:1938 && vol:23 && pgrg:279-286 ', 'pattern authors year vol pgrg')    
    
    >>> ret_dict = smart_search("009:1015")
    >>> ret_dict['search_clause'], ret_dict['search_type']
    ('&& vol:9 && pgrg:1015 ', 'pattern vol and page range')
    
    >>> ret_dict = smart_search("Tuckett")
    >>> ret_dict['search_clause'], ret_dict['search_type']
       
    >>> ret_dict = smart_search("Kohut, H. & Wolf, E. S. (1978)")
    >>> ret_dict['search_clause'], ret_dict['search_type']
    
    >>> ret_dict = smart_search("Tuckett 1982")
    >>> ret_dict['search_clause'], ret_dict['search_type']
    ('Tuckett', '1982', 'pattern authors and year')
    
    >>> ret_dict = smart_search("the cat in the hat was that")
    >>> ret_dict['search_clause'], ret_dict['search_type']
    
    >>> tst = []
    >>> tst.append("Emerson, R. W. (1836), An essay on nature. In: The Selected Writings of Ralph Waldo Emerson, ed. W. H. Gilman. New York: New American Library, 1965, pp. 186-187.")
    >>> tst.append("Rapaport, D. and Gill, M. M. ( 1959). The Points of View and Assumptions of Metapsychology. Int. J. Psycho-Anal.40:153-162")
    >>> tst.append("Freud, S. ( 1938), Some elementary lessons in psycho-analysis, Standard Edition. 23:279-286. pp. London: Hogarth Press, 1964.")
    >>> tst.append("Waelder, R. ( 1962). Psychoanalysis, Scientific Method, and Philosophy. J. Amer. Psychoanal. Assn.10:617-637")

    >>> for n in tst: smart_search(n)
    {'author_list': 'Emerson, R. W.', 'yr': '1836'}
    {'author_list': 'Rapaport, D. and Gill, M. M.', 'yr': '1959'}
    {'author_list': 'Freud, S.', 'yr': '1938', 'vol': '23', 'pgrg': '279-286'}
    {'author_list': 'Waelder, R.', 'yr': '1962'}
    """
    # recognize Smart Search inputs
    ret_val = {}
    # get rid of leading spaces and zeros
    smart_search_text = smart_search_text.lstrip(" 0")
    # get rid of smart quotes
    smart_search_text = re.sub("“|”", "'", smart_search_text)
    
    # journal and vol and page
    if re.match(f"[A-Z\-]{2,{MAX_SOURCE_LEN}}\.[0-9]{3,3}[A-Z]?\.[0-9]{4,4}[A-Z]?", smart_search_text, flags=re.IGNORECASE):
        loc_corrected = smart_search_text.upper()
        if is_value_in_field(loc_corrected, SEARCH_FIELD_LOCATOR): # art_id
            ret_val[KEY_SEARCH_TYPE] = SEARCH_TYPE_ID
            ret_val[KEY_SEARCH_FIELD] = SEARCH_FIELD_LOCATOR
            ret_val[KEY_SEARCH_VALUE] = f"{loc_corrected}"
            ret_val[KEY_SEARCH_CLAUSE] = f"{art_id}:{loc_corrected}"
            ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched articles for locator: {loc_corrected}"

    # journal and vol and wildcard
    if ret_val == {}:
        m = re.match(f"(?P<journal>[A-Z\-]{2,{MAX_SOURCE_LEN}})\.(?P<vol>([0-9]{3,3}[A-Z]?)|(\*))\.(?P<page>\*)", smart_search_text, flags=re.IGNORECASE)
        if m is not None:
            src_code = m.group("journal")
            if src_code is not None:
                vol_code = m.group("vol")
                if vol_code is None:
                    vol_code = "*"
            loc = f"{src_code}.{vol_code}.*"
            loc_corrected = loc.upper()
    
            ret_val = {"art_id": loc_corrected}
            ret_val[KEY_SEARCH_TYPE] = SEARCH_TYPE_ID
            ret_val[KEY_SEARCH_CLAUSE] = f"{art_id}:{loc_corrected}"
            ret_val[KEY_SEARCH_FIELD] = SEARCH_FIELD_LOCATOR
            ret_val[KEY_SEARCH_VALUE] = f"{loc_corrected}"
            ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched articles for jrnl-vol-wildcard locator: {loc_corrected}"

    if ret_val == {}:
        # SmartPatterns meta:
        patterns1 = {
                    rx_solr_field: "advanced query syntax", 
                    rx_syntax: SEARCH_TYPE_ARTICLE_FIELDS,
                    #rx_series_of_author_last_names: "author_list", 
                    #rx_author_name_list: "author_list",
                    #rx_author_name: "author_list",
                    }

        for rx_str, label in patterns1.items():
            m = re.match(rx_str, smart_search_text)
            if m is not None:
                match_vals = {**ret_val, **m.groupdict()}
                ret_val = {}
                ret_val[KEY_SEARCH_FIELD_COUNT] = 1
                try:
                    ret_val[KEY_SEARCH_FIELD] = m.group(KEY_SEARCH_FIELD)
                    ret_val[KEY_SEARCH_VALUE] = m.group(KEY_SEARCH_VALUE)
                except Exception as e:
                    logger.error(e)
                else:   
                    # build search clause
                    if ret_val[KEY_SEARCH_FIELD] != "solr": # advance only
                        ret_val[KEY_SEARCH_TYPE] = SEARCH_TYPE_ADVANCED
                        ret_val[KEY_SEARCH_CLAUSE] = f"&& {ret_val[KEY_SEARCH_FIELD]}:({ret_val[KEY_SEARCH_VALUE]}) "
                        ret_val[KEY_SEARCH_SMARTSEARCH] = "Advanced Syntax"
                    else: # field spec'd
                        ret_val[KEY_SEARCH_TYPE] = SEARCH_TYPE_FIELDED
                        ret_val[KEY_SEARCH_CLAUSE] = f"&& {ret_val[KEY_SEARCH_VALUE]} "
                        ret_val[KEY_SEARCH_SMARTSEARCH] = "Fielded Search"
                        
                    ret_val[KEY_MATCH_DICT] = match_vals
                    break
                        
    if ret_val == {}:
        # Smartpatterns general:        
        patterns2 = {
                    rx_author_list_year_vol_pgrg : "authors year vol pgrg",
                    rx_author_list_and_year : "authors and year",
                    rx_cit_vol_pgrg : "citation vol/pg",
                    rx_year_pgrg : "a page range",
                    rx_vol_pgrg : "vol and page range",
                    rx_doi : "an article DOI",
                    rx_solr_field: SEARCH_TYPE_ARTICLE_FIELDS, 
                    rx_syntax: "advanced query syntax",
                    #rx_series_of_author_last_names: "author_list", 
                    #rx_author_name_list: "author_list",
                    #rx_author_name: "author_list",
                    }

        for rx_str, label in patterns2.items():
            m = re.match(rx_str, smart_search_text)
            if m is not None:
                match_vals = {**ret_val, **m.groupdict()}
                ret_val = {}
                ret_val[KEY_SEARCH_FIELD_COUNT] = len(match_vals.items())
                # build search clause
                ret_val[KEY_SEARCH_CLAUSE] = ""
                ret_val[KEY_MATCH_DICT] = match_vals
                for key, val in match_vals.items():
                    ret_val[KEY_SEARCH_CLAUSE] += f" && {key}:({val})"
                    if ret_val[KEY_SEARCH_FIELD_COUNT] == 1:
                        ret_val[KEY_SEARCH_FIELD] = key
                        ret_val[KEY_SEARCH_VALUE] = val
                        
                if ret_val[KEY_SEARCH_FIELD_COUNT] > 1:
                    ret_val[KEY_SEARCH_FIELD] = list(match_vals.keys())
                    ret_val[KEY_SEARCH_VALUE] = list(match_vals.values())
                    
                ret_val[KEY_SEARCH_TYPE] = f"pattern {label}"
                ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched {label}: {smart_search_text}"
                break
                
    if ret_val == {}:
        # nothing found yet.
        # is it in quotes (phrase?)

        words = smart_search_text.split(" ")
        word_count = len(words)
        words = [re.sub('\"|\\\:', "", n) for n in words]
        words = " ".join(words)
        words = cleanup_solr_query(words)

        if word_count == 1 and len(words) > 3 and words[0].isupper():
            # could still be an author name
            if is_value_in_field(words, core="authors", field=SEARCH_FIELD_AUTHORS):
                # authors_search = presearch_field(words, core="authors", field=SEARCH_FIELD_AUTHORS)
                ret_val[KEY_SEARCH_TYPE] = SEARCH_TYPE_AUTHOR_CITATION
                ret_val[KEY_SEARCH_FIELD] = SEARCH_FIELD_AUTHOR_CITATION 
                ret_val[KEY_SEARCH_VALUE] = f"{words}"
                ret_val[KEY_SEARCH_CLAUSE] = f"{words}"
                ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched articles for authors: {words}"

        elif word_count > 4 and is_value_in_field(words, "title", match_type="ordered") == 1: # unique match only
            # might be a faster way to check?
            # title_search = presearch_field(words, "title", match_type="ordered")
            # ret_val["title"] = words
            ret_val[KEY_SEARCH_TYPE] = SEARCH_FIELD_TITLE
            ret_val[KEY_SEARCH_FIELD] = SEARCH_FIELD_TITLE
            ret_val[KEY_SEARCH_VALUE] = f"{words}"
            ret_val[KEY_SEARCH_CLAUSE] = f"{SEARCH_FIELD_TITLE}:({words})"
            ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched words in titles: {words}"

        elif is_value_in_field(words, core="docs", field=SEARCH_FIELD_AUTHOR_CITATION) and words[0].isupper():
            # might be a faster way to check?
            # authors_citation_search = presearch_field(words, core="docs", field="art_authors_citation")
            # see if it's a list of names
            ret_val[KEY_SEARCH_TYPE] = SEARCH_TYPE_AUTHOR_CITATION + "2"
            ret_val[KEY_SEARCH_FIELD] = SEARCH_FIELD_AUTHOR_CITATION
            ret_val[KEY_SEARCH_VALUE] = f"{words}"
            ret_val[KEY_SEARCH_CLAUSE] = f"{SEARCH_FIELD_TITLE}:({words})"
            ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched articles for author citation: ({words})"

        elif is_value_in_field(words, core="docs", field="text", match_type="proximate"):
            orig_smart_search_text = smart_search_text
            if not opasgenlib.in_quotes(smart_search_text):
                if not opasgenlib.is_boolean(smart_search_text):
                    if not opasgenlib.in_brackets(smart_search_text):
                        smart_search_text = f'"{smart_search_text}"~25'
                        ret_val[KEY_SEARCH_TYPE] = "paragraph search"
                        ret_val[KEY_SEARCH_FIELD] = SEARCH_FIELD_TEXT
                        ret_val[KEY_SEARCH_VALUE] = f"{smart_search_text}"
                        ret_val[KEY_SEARCH_CLAUSE] = f"{SEARCH_FIELD_TEXT}:({smart_search_text})"
                        ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched paragraphs with terms: ({orig_smart_search_text})"

                    else:
                        ret_val["wordsearch"] = re.sub(":", "\:", smart_search_text)
                        ret_val[KEY_SEARCH_TYPE] = "term search"
                        ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched articles for terms: ({orig_smart_search_text})"
                else:
                    smart_search_text = re.sub ("\snot\s", " NOT ", smart_search_text)
                    ret_val[KEY_SEARCH_TYPE] = "boolean search"
                    ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched articles for boolean string: ({orig_smart_search_text})"
                    ret_val[KEY_SEARCH_VALUE] = f"{orig_smart_search_text}"
                    ret_val[KEY_SEARCH_VALUE] = re.sub("\s+(AND)\s+", " && ", ret_val[KEY_SEARCH_VALUE], flags=re.IGNORECASE)
                    ret_val[KEY_SEARCH_VALUE] = re.sub("\s+(OR)\s+", " || ", ret_val[KEY_SEARCH_VALUE], flags=re.IGNORECASE)
                    ret_val[KEY_SEARCH_VALUE] = re.sub("\s+(NOT)\s+", " NOT ", ret_val[KEY_SEARCH_VALUE], flags=re.IGNORECASE)
            else:
                # literal
                ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched articles for literal string: ({orig_smart_search_text})"
                ret_val[KEY_SEARCH_TYPE] = "literal search"
                ret_val[KEY_SEARCH_VALUE] = f"{orig_smart_search_text}"
                ret_val[KEY_SEARCH_CLAUSE] = f" && {SEARCH_FIELD_TEXT}:({orig_smart_search_text})"
                
        elif words[0].isupper():
            # try to build a list of names, and check them individually
            new_q = ""
            names = name_id_list(smart_search_text)
            for name in names:
                try:
                    if is_value_in_field(name, core="docs", field="authors"):
                        # ok, this is a list of names
                        if new_q != "":
                            new_q += f" && '{name}'"
                        #else:
                            #new_q += f"'{name}'"
                except Exception as e:
                    logger.warning(f"Value error for {name}. {e}")
            
            if new_q != "":
                ret_val[KEY_SEARCH_TYPE] = "author search"
                ret_val[KEY_SEARCH_FIELD] = "authors" 
                ret_val[KEY_SEARCH_VALUE] = f"{new_q}"
            else:
                #  join the names
                name_conjunction = " && ".join(names)
                if is_value_in_field(name_conjunction, core="docs", field="art_authors_citation", match_type="bool"):
                    ret_val[KEY_SEARCH_TYPE] = "author citation"
                    ret_val[KEY_SEARCH_FIELD] = "art_authors_citation" 
                    ret_val[KEY_SEARCH_VALUE] = f"{name_conjunction}"
                    ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched articles for authors: {name_conjunction} "
    
    #  cleanup 
    if ret_val.get("art_id") is not None:
        ret_val["art_id"] = ret_val["art_id"].upper()
        ret_val[KEY_SEARCH_TYPE] = "article ID search"
        ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched articles for article ID {ret_val['art_id'].upper()}:"
    elif ret_val.get("doi") is not None:
        pass # we're done

    if ret_val == {}:
        ret_val["wordsearch"] = re.sub(":", "\:", smart_search_text)
        ret_val[KEY_SEARCH_TYPE] = "word search"
        ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched articles with text: {smart_search_text}"

    # ret_val = dict_clean_none_terms(ret_val)
    return ret_val

#-----------------------------------------------------------------------------
def smart_search3(smart_search_text):
    """
    Function to take an input string and parse out information to do a search against the DOCS core schema.
    
    Some simple syntax is implemented to help identify certain functionality.
    
        search_field:terms  = Solr field from schema, search terms against it.  (Will be presented
            to solr as field:(terms).  Multiple terms are permitted, but currently, only one field
            specification is permitted.  Field names are converted to lower case automatically.
            
            art_doi:10.1111/j.1745-8315.2012.00606.x
            art_authors_text:[tuckett and fonagy]            
           
        doi = Just enter a DOI
           10.1111/j.1745-8315.2012.00606.x 
        
        AuthorName Year = One or more names (initial capital), followed by a year
            Tuckett and Fonagy 1972
            Tuckett and Fonagy (1972)
            
    >>> ret_dict = smart_search("'the cat in the hat was that'")
    >>> ret_dict['search_clause'], ret_dict['search_type']
    (" && text:('the cat in the hat was that')", 'literal search')
    
    # pattern 1 tests
    >>> ret_dict = smart_search("solr::art_authors_text:[tuckett and fonagy]")
    >>> ret_dict['search_clause'], ret_dict['search_type']
    (' && art_authors_text:[tuckett and fonagy]', 'solr field')

    >>> ret_dict = smart_search("authors:Tuckett, D.")
    >>> ret_dict['search_clause'], ret_dict['search_type']
    (' && authors:(Tuckett, D.)', 'solr advanced')

    # pattern 2 tests
    >>> ret_dict = smart_search("Freud, S. ( 1938), Some elementary lessons in psycho-analysis, Standard Edition. 23:279-286. pp. London: Hogarth Press, 1964.")
    >>> ret_dict['search_clause'], ret_dict['search_type']
    ('&& author_list:Freud, S.  && yr:1938 && vol:23 && pgrg:279-286 ', 'pattern authors year vol pgrg')    
    
    >>> ret_dict = smart_search("009:1015")
    >>> ret_dict['search_clause'], ret_dict['search_type']
    ('&& vol:9 && pgrg:1015 ', 'pattern vol and page range')
    
    >>> ret_dict = smart_search("Tuckett")
    >>> ret_dict['search_clause'], ret_dict['search_type']
       
    >>> ret_dict = smart_search("Kohut, H. & Wolf, E. S. (1978)")
    >>> ret_dict['search_clause'], ret_dict['search_type']
    
    >>> ret_dict = smart_search("Tuckett 1982")
    >>> ret_dict['search_clause'], ret_dict['search_type']
    ('Tuckett', '1982', 'pattern authors and year')
    
    >>> ret_dict = smart_search("the cat in the hat was that")
    >>> ret_dict['search_clause'], ret_dict['search_type']
    
    >>> tst = []
    >>> tst.append("Emerson, R. W. (1836), An essay on nature. In: The Selected Writings of Ralph Waldo Emerson, ed. W. H. Gilman. New York: New American Library, 1965, pp. 186-187.")
    >>> tst.append("Rapaport, D. and Gill, M. M. ( 1959). The Points of View and Assumptions of Metapsychology. Int. J. Psycho-Anal.40:153-162")
    >>> tst.append("Freud, S. ( 1938), Some elementary lessons in psycho-analysis, Standard Edition. 23:279-286. pp. London: Hogarth Press, 1964.")
    >>> tst.append("Waelder, R. ( 1962). Psychoanalysis, Scientific Method, and Philosophy. J. Amer. Psychoanal. Assn.10:617-637")

    >>> for n in tst: smart_search(n)
    {'author_list': 'Emerson, R. W.', 'yr': '1836'}
    {'author_list': 'Rapaport, D. and Gill, M. M.', 'yr': '1959'}
    {'author_list': 'Freud, S.', 'yr': '1938', 'vol': '23', 'pgrg': '279-286'}
    {'author_list': 'Waelder, R.', 'yr': '1962'}
    """
    # recognize Smart Search inputs
    ret_val = {}
    # get rid of leading spaces and zeros
    smart_search_text = smart_search_text.lstrip(" 0")
    # get rid of smart quotes
    smart_search_text = re.sub("“|”", "'", smart_search_text)
    
    # journal and vol and page
    if re.match(f"[A-Z\-]{2,{MAX_SOURCE_LEN}}\.[0-9]{3,3}[A-Z]?\.[0-9]{4,4}[A-Z]?", smart_search_text, flags=re.IGNORECASE):
        loc_corrected = smart_search_text.upper()
        if is_value_in_field(loc_corrected, SEARCH_FIELD_LOCATOR): # art_id
            ret_val[KEY_SEARCH_TYPE] = SEARCH_TYPE_ID
            ret_val[KEY_SEARCH_FIELD] = SEARCH_FIELD_LOCATOR
            ret_val[KEY_SEARCH_VALUE] = f"{loc_corrected}"
            ret_val[KEY_SEARCH_CLAUSE] = f"{art_id}:{loc_corrected}"
            ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched articles for locator: {loc_corrected}"

    # journal and vol and wildcard
    if ret_val == {}:
        m = re.match(f"(?P<journal>[A-Z\-]{2,{MAX_SOURCE_LEN}})\.(?P<vol>([0-9]{3,3}[A-Z]?)|(\*))\.(?P<page>\*)", smart_search_text, flags=re.IGNORECASE)
        if m is not None:
            src_code = m.group("journal")
            if src_code is not None:
                vol_code = m.group("vol")
                if vol_code is None:
                    vol_code = "*"
            loc = f"{src_code}.{vol_code}.*"
            loc_corrected = loc.upper()
    
            ret_val = {"art_id": loc_corrected}
            ret_val[KEY_SEARCH_TYPE] = SEARCH_TYPE_ID
            ret_val[KEY_SEARCH_CLAUSE] = f"{art_id}:{loc_corrected}"
            ret_val[KEY_SEARCH_FIELD] = SEARCH_FIELD_LOCATOR
            ret_val[KEY_SEARCH_VALUE] = f"{loc_corrected}"
            ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched articles for jrnl-vol-wildcard locator: {loc_corrected}"

    if ret_val == {}:
        # SmartPatterns meta:
        patterns1 = {
                    rx_solr_field: "advanced query syntax", 
                    rx_syntax: SEARCH_TYPE_ARTICLE_FIELDS,
                    #rx_series_of_author_last_names: "author_list", 
                    #rx_author_name_list: "author_list",
                    #rx_author_name: "author_list",
                    }

        for rx_str, label in patterns1.items():
            m = re.match(rx_str, smart_search_text)
            if m is not None:
                match_vals = {**ret_val, **m.groupdict()}
                ret_val = {}
                ret_val[KEY_SEARCH_FIELD_COUNT] = 1
                try:
                    ret_val[KEY_SEARCH_FIELD] = m.group(KEY_SEARCH_FIELD)
                    ret_val[KEY_SEARCH_VALUE] = m.group(KEY_SEARCH_VALUE)
                except Exception as e:
                    logger.error(e)
                else:   
                    # build search clause
                    if ret_val[KEY_SEARCH_FIELD] != "solr": # advance only
                        ret_val[KEY_SEARCH_TYPE] = SEARCH_TYPE_ADVANCED
                        ret_val[KEY_SEARCH_CLAUSE] = f"&& {ret_val[KEY_SEARCH_FIELD]}:({ret_val[KEY_SEARCH_VALUE]}) "
                        ret_val[KEY_SEARCH_SMARTSEARCH] = "Advanced Syntax"
                    else: # field spec'd
                        ret_val[KEY_SEARCH_TYPE] = SEARCH_TYPE_FIELDED
                        ret_val[KEY_SEARCH_CLAUSE] = f"&& {ret_val[KEY_SEARCH_VALUE]} "
                        ret_val[KEY_SEARCH_SMARTSEARCH] = "Fielded Search"
                        
                    ret_val[KEY_MATCH_DICT] = match_vals
                    break
                        
    if ret_val == {}:
        # Smartpatterns general:        
        patterns2 = {
                    rx_author_list_year_vol_pgrg : "authors year vol pgrg",
                    rx_author_list_and_year : "authors and year",
                    rx_cit_vol_pgrg : "citation vol/pg",
                    rx_year_pgrg : "a page range",
                    rx_vol_pgrg : "vol and page range",
                    rx_doi : "an article DOI",
                    rx_solr_field: SEARCH_TYPE_ARTICLE_FIELDS, 
                    rx_syntax: "advanced query syntax",
                    #rx_series_of_author_last_names: "author_list", 
                    #rx_author_name_list: "author_list",
                    #rx_author_name: "author_list",
                    }

        for rx_str, label in patterns2.items():
            m = re.match(rx_str, smart_search_text)
            if m is not None:
                match_vals = {**ret_val, **m.groupdict()}
                ret_val = {}
                ret_val[KEY_SEARCH_FIELD_COUNT] = len(match_vals.items())
                # build search clause
                ret_val[KEY_SEARCH_CLAUSE] = ""
                ret_val[KEY_MATCH_DICT] = match_vals
                for key, val in match_vals.items():
                    ret_val[KEY_SEARCH_CLAUSE] += f" && {key}:({val})"
                    if ret_val[KEY_SEARCH_FIELD_COUNT] == 1:
                        ret_val[KEY_SEARCH_FIELD] = key
                        ret_val[KEY_SEARCH_VALUE] = val
                        
                if ret_val[KEY_SEARCH_FIELD_COUNT] > 1:
                    ret_val[KEY_SEARCH_FIELD] = list(match_vals.keys())
                    ret_val[KEY_SEARCH_VALUE] = list(match_vals.values())
                    
                ret_val[KEY_SEARCH_TYPE] = f"pattern {label}"
                ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched {label}: {smart_search_text}"
                break
                
    if ret_val == {}:
        # nothing found yet.
        # is it in quotes (phrase?)

        words = smart_search_text.split(" ")
        word_count = len(words)
        words = [re.sub('\"|\\\:', "", n) for n in words]
        words = " ".join(words)
        words = cleanup_solr_query(words)

        if word_count == 1 and len(words) > 3 and words[0].isupper():
            # could still be an author name
            if is_value_in_field(words, core="authors", field=SEARCH_FIELD_AUTHORS):
                # authors_search = presearch_field(words, core="authors", field=SEARCH_FIELD_AUTHORS)
                ret_val[KEY_SEARCH_TYPE] = SEARCH_TYPE_AUTHOR_CITATION
                ret_val[KEY_SEARCH_FIELD] = SEARCH_FIELD_AUTHOR_CITATION 
                ret_val[KEY_SEARCH_VALUE] = f"{words}"
                ret_val[KEY_SEARCH_CLAUSE] = f"{words}"
                ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched articles for authors: {words}"

        elif word_count > 4 and is_value_in_field(words, "title", match_type="ordered") == 1: # unique match only
            # might be a faster way to check?
            # title_search = presearch_field(words, "title", match_type="ordered")
            # ret_val["title"] = words
            ret_val[KEY_SEARCH_TYPE] = SEARCH_FIELD_TITLE
            ret_val[KEY_SEARCH_FIELD] = SEARCH_FIELD_TITLE
            ret_val[KEY_SEARCH_VALUE] = f"{words}"
            ret_val[KEY_SEARCH_CLAUSE] = f"{SEARCH_FIELD_TITLE}:({words})"
            ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched words in titles: {words}"

        elif is_value_in_field(words, core="docs", field=SEARCH_FIELD_AUTHOR_CITATION) and words[0].isupper():
            # might be a faster way to check?
            # authors_citation_search = presearch_field(words, core="docs", field="art_authors_citation")
            # see if it's a list of names
            ret_val[KEY_SEARCH_TYPE] = SEARCH_TYPE_AUTHOR_CITATION + "2"
            ret_val[KEY_SEARCH_FIELD] = SEARCH_FIELD_AUTHOR_CITATION
            ret_val[KEY_SEARCH_VALUE] = f"{words}"
            ret_val[KEY_SEARCH_CLAUSE] = f"{SEARCH_FIELD_TITLE}:({words})"
            ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched articles for author citation: ({words})"

        elif is_value_in_field(words, core="docs", field="text", match_type="proximate"):
            orig_smart_search_text = smart_search_text
            if not opasgenlib.in_quotes(smart_search_text):
                if not opasgenlib.is_boolean(smart_search_text):
                    if not opasgenlib.in_brackets(smart_search_text):
                        smart_search_text = f'"{smart_search_text}"~25'
                        ret_val[KEY_SEARCH_TYPE] = "paragraph search"
                        ret_val[KEY_SEARCH_FIELD] = SEARCH_FIELD_TEXT
                        ret_val[KEY_SEARCH_VALUE] = f"{smart_search_text}"
                        ret_val[KEY_SEARCH_CLAUSE] = f"{SEARCH_FIELD_TEXT}:({smart_search_text})"
                        ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched paragraphs with terms: ({orig_smart_search_text})"

                    else:
                        ret_val["wordsearch"] = re.sub(":", "\:", smart_search_text)
                        ret_val[KEY_SEARCH_TYPE] = "term search"
                        ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched articles for terms: ({orig_smart_search_text})"
                else:
                    smart_search_text = re.sub ("\snot\s", " NOT ", smart_search_text)
                    ret_val[KEY_SEARCH_TYPE] = "boolean search"
                    ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched articles for boolean string: ({orig_smart_search_text})"
                    ret_val[KEY_SEARCH_VALUE] = f"{orig_smart_search_text}"
                    ret_val[KEY_SEARCH_VALUE] = re.sub("\s+(AND)\s+", " && ", ret_val[KEY_SEARCH_VALUE], flags=re.IGNORECASE)
                    ret_val[KEY_SEARCH_VALUE] = re.sub("\s+(OR)\s+", " || ", ret_val[KEY_SEARCH_VALUE], flags=re.IGNORECASE)
                    ret_val[KEY_SEARCH_VALUE] = re.sub("\s+(NOT)\s+", " NOT ", ret_val[KEY_SEARCH_VALUE], flags=re.IGNORECASE)
            else:
                # literal
                ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched articles for literal string: ({orig_smart_search_text})"
                ret_val[KEY_SEARCH_TYPE] = "literal search"
                ret_val[KEY_SEARCH_VALUE] = f"{orig_smart_search_text}"
                ret_val[KEY_SEARCH_CLAUSE] = f" && {SEARCH_FIELD_TEXT}:({orig_smart_search_text})"
                
        elif words[0].isupper():
            # try to build a list of names, and check them individually
            new_q = ""
            names = name_id_list(smart_search_text)
            for name in names:
                try:
                    if is_value_in_field(name, core="docs", field="authors"):
                        # ok, this is a list of names
                        if new_q != "":
                            new_q += f" && '{name}'"
                        #else:
                            #new_q += f"'{name}'"
                except Exception as e:
                    logger.warning(f"Value error for {name}. {e}")
            
            if new_q != "":
                ret_val[KEY_SEARCH_TYPE] = "author search"
                ret_val[KEY_SEARCH_FIELD] = "authors" 
                ret_val[KEY_SEARCH_VALUE] = f"{new_q}"
            else:
                #  join the names
                name_conjunction = " && ".join(names)
                if is_value_in_field(name_conjunction, core="docs", field="art_authors_citation", match_type="bool"):
                    ret_val[KEY_SEARCH_TYPE] = "author citation"
                    ret_val[KEY_SEARCH_FIELD] = "art_authors_citation" 
                    ret_val[KEY_SEARCH_VALUE] = f"{name_conjunction}"
                    ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched articles for authors: {name_conjunction} "
    
    #  cleanup 
    if ret_val.get("art_id") is not None:
        ret_val["art_id"] = ret_val["art_id"].upper()
        ret_val[KEY_SEARCH_TYPE] = "article ID search"
        ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched articles for article ID {ret_val['art_id'].upper()}:"
    elif ret_val.get("doi") is not None:
        pass # we're done

    if ret_val == {}:
        ret_val["wordsearch"] = re.sub(":", "\:", smart_search_text)
        ret_val[KEY_SEARCH_TYPE] = "word search"
        ret_val[KEY_SEARCH_SMARTSEARCH] = f"Matched articles with text: {smart_search_text}"

    # ret_val = dict_clean_none_terms(ret_val)
    return ret_val

#-----------------------------------------------------------------------------
def presearch_field(value,
                    field="title",
                    core="docs",
                    match_type="exact", # exact, ordered, proximate, or bool
                    limit=10):
    """
    Returns True if the value is found in the field specified in the docs core.
    
    Args:
        value (str): String prefix of term to check.
        field (str): Where to look for term
        match_type (str): exact, ordered, or bool
        limit (int, optional): Paging mechanism, return is limited to this number of items.

    Returns:
        True if the value is in the specified field

    Docstring Tests:    
        >>> presearch_field("Object Relations Theories and the Developmental Tilt", "title").isfound
        True
        >>> presearch_field("Contemporary Psychoanalysis", "art_sourcetitlefull").isfound
        True
        >>> presearch_field("Contemporary Psych", "art_sourcetitlefull").isfound
        False
        >>> presearch_field("Contemp. Psychoanal.", "art_sourcetitleabbr").isfound
        True
        >>> presearch_field("Tuckett, D", "title").isfound
        False
    """
    ret_val = SearchEvaluation()

    cores  = {
        "docs": solr_docs2,
        "authors": solr_authors,
    }
    
    try:
        solr_core = cores[core]
    except Exception as e:
        logger.debug(f"Core selection: {core}. 'docs' is default {e}")
        solr_core  = solr_docs2  

    if match_type == "exact":
        q = f'{field}:"{value}"'
    elif match_type == "ordered":
        q = f'{field}:"{value}"~10'
    elif match_type == "proximate":
        q = f'{field}:"{value}"~25'
    else:
        q = f'{field}:({value})'
        
    try:
        results = solr_core.query(q=q,  
                                  fields = f"{field}", 
                                  rows = limit,
                                  )
    except Exception as e:
        logger.warning(f"Solr query: {q} fields {field} {e}")
        ret_val = SearchEvaluation(field=field, score=0, found=0)
       
    if len(results) > 0:
        ret_val = SearchEvaluation(field=field, score=results.results[0]["score"], found=results.numFound)
    else:
        ret_val = SearchEvaluation(field=field, score=0, found=0)

    return ret_val

#-----------------------------------------------------------------------------
def is_term_in_index(term_partial,
                     term_field="art_authors",
                     core="docs",
                     limit=10, 
                     order="index"):
    """
    Returns True if the term_partial matches the index specified
    
    Args:
        term_partial (str): String prefix of term to check.
        term_field (str): Where to look for term
        limit (int, optional): Paging mechanism, return is limited to this number of items.
        offset (int, optional): Paging mechanism, start with this item in limited return set, 0 is first item.
        order (str, optional): Return the list in this order, per Solr documentation.  Defaults to "index", which is the Solr determined indexing order.

    Returns:
        True if the term is in the specified field

    Docstring Tests:    
        >>> is_term_in_index("Tuckett, David", term_field="art_author_id", core="authors")
        True
        
        >>> is_term_in_index("Tuckett", term_field="art_author_id", core="authors")
        True
        
        >>> is_term_in_index("Tuckett", limit=5)
        True
        
        >>> is_term_in_index("Tucke*")
        True
        
    """
    ret_val = False
    
    core_term_indexers = {
        "docs": solr_docs_term_search,
        "authors": solr_authors_term_search,
    }
    
    try:
        term_index = core_term_indexers[core]
    except:
        # error
        logger.error("Specified core does not have a term index configured")
    else:
        if "*" in term_partial or "?" in term_partial: # or "." in term_partial:
            # Wildcard expected, not RE
            term_partial = term_partial.lower().replace("*", ".*")
            results = term_index( terms_fl=term_field,
                                  terms_regex=term_partial,
                                  terms_limit=limit,  
                                  terms_sort=order  # index or count
                                 )           

            for n in results.terms[term_field].keys():
                m = re.match(term_partial, n)
                if m is not None:
                    ret_val = True
                    break
        else:
            results = term_index( terms_fl=term_field,
                                  terms_prefix=term_partial.lower(),
                                  terms_sort=order,  # index or count
                                  terms_limit=limit
                                 )
        
            for n in results.terms[term_field].keys():
                n_partial = re.split("[\s,]+", n)
                term_adj = term_partial.lower()
                if term_adj == n or term_adj == n_partial[0]:
                    ret_val = True
                    break
            

    return ret_val


