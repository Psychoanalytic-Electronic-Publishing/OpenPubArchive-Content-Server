import re
import sys
from datetime import datetime
from optparse import OptionParser
from configLib.opasCoreConfig import solr_docs, solr_authors, solr_gloss, solr_docs_term_search, solr_authors_term_search
import logging

logger = logging.getLogger(__name__)

from namesparser import HumanNames
rx_space_req = "(\s+|\s*)"
rx_space_opt = "(\s*|\s*)"
rx_space_end_opt = "(\s*|\s*)$"
rx_space_start_opt = "^(\s*|\s*)?"
rx_year = "\(?\s*(?P<yr>(18|19|20)[0-9]{2,2})\s*\)?"
rx_title = ".*?"
rx_space_or_colon = "((\s*\:\s*)|\s+)"
rx_vol = "((?P<vol>([\(]?[12]?[0-9][0-9]?[\)]?))\:)"
# rx_pgrg = f"(pp\.?\s+)|{rx_vol}(?P<pgrg>[1-9][0-9]{0,3}([-][1-9][0-9]{0,3})?)"
rx_pgrg = "(?P<pgrg>[1-9][0-9]{0,3}([-][1-9][0-9]{0,3})?)"
rx_vol_pgrg = "(.*?(\s|,)|^)" + rx_vol + rx_pgrg + ".*"
rx_year_pgrg = rx_space_start_opt + rx_year + rx_space_or_colon + rx_pgrg + rx_space_end_opt
rx_year_vol_pgrg = rx_year + rx_vol_pgrg + rx_space_end_opt
rx_author_name = "(?P<author>[A-Z][a-z]+)(\,\s+(([A-Z]\.?\s?){0,2})\s*)?"
rx_author_connector = "(and|,)"
rx_front_junk = "(\[|\()?[0-9]+(\]|\))?"
# rx_author_and_year = rx_space_start_opt + rx_author_name + rx_space_req + rx_year + rx_space_end_opt
# rx_author_year_pgrg = rx_author_and_year + ".*?" + rx_pgrg
rx_author_name_list = "(?P<author_list>([A-Z][A-z]+\,?\s+?(([A-Z]\.?\s?){0,2})((\,\s+)|(\s*and\s+))?)+)"
# rx_author_name_list_year = rx_author_name_list + rx_space_req + rx_year
rx_author_list_and_year = "(?P<author_list>[A-Z][A-z\s\,\.\-]+?)" + rx_space_req + rx_year
rx_series_of_author_last_names = "(?P<author_list>([A-Z][a-z]+((\,\s+)|(\s*and\s+))?)+)"
rx_doi = "((h.*?://)?(.*?/))?(?P<doi>(10\.[0-9]{4,4}/[A-z0-9\.\-/]+)|(doi.org/[A-z0-9\-\./]+))"
# schema fields must have a _ in them to use.
rx_solr_field = "(?P<schema_field>([a-z]+_[a-z_]{2,13})|text|authors)\:(?P<schema_value>(.*$))"
rx_syntax = "(?P<syntax>^[a-z]{3,9})\:\:(?P<query>.+$)"
rx_pepdoi = "(?P<prefix>PEP\/\.)(?P<locator>[A-Z\-]{2,10}\.[0-9]{3,3}\.[0-9]{4,4}([PN]{1,2}[0-9]{4,4})?"
pat_prefix_amps = re.compile("^\s*&& ")

class SearchEvaluation(object):
    def __init__(self, field=None, found=0, score=0): 
        self.score = score
        self.field = field
        self.found = found
        self.isfound = found == True


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

#-----------------------------------------------------------------------------
def is_value_in_field(value,
                      field="title",
                      core="docs",
                      match_type="exact", # exact, ordered, proximate, or bool
                      limit=10):
    """
    Returns the NumFound if the value is found in the field specified in the docs core.
    
    Args:
        value (str): String prefix of term to check.
        field (str): Where to look for term
        match_type (str): exact, ordered, or bool
        limit (int, optional): Paging mechanism, return is limited to this number of items.

    Returns:
        True if the value is in the specified field

    Docstring Tests:    
        >>> is_value_in_field("Object Relations Theories and the Developmental Tilt", "title") > 0
        True
        
        >>> is_value_in_field("Contemporary Psychoanalysis", "art_sourcetitlefull") > 0
        True

        >>> is_value_in_field("Contemporary Psych", "art_sourcetitlefull") > 0
        False

        >>> is_value_in_field("Contemp. Psychoanal.", "art_sourcetitleabbr") > 0
        True

        >>> is_value_in_field("Tuckett, D", "title") > 0
        False
        
    """
    ret_val = 0

    cores  = {
        "docs": solr_docs,
        "authors": solr_authors,
    }
    
    try:
        solr_core = cores[core]
    except Exception as e:
        logger.debug(f"Core selection: {core}. 'docs' is default {e}")
        solr_core  = solr_docs    

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
        results = []
       
    if len(results) > 0: # it looks like the solr response object to this query always has a len == numFound
        # but just in case
        ret_val = results.numFound

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
        >>> presearch_field("Object Relations Theories and the Developmental Tilt", "title").found
        
        >>> presearch_field("Contemporary Psychoanalysis", "art_sourcetitlefull").found

        >>> presearch_field("Contemporary Psych", "art_sourcetitlefull").found

        >>> presearch_field("Contemp. Psychoanal.", "art_sourcetitleabbr").found

        >>> presearch_field("Tuckett, D", "title").found
        
    """
    ret_val = SearchEvaluation()

    cores  = {
        "docs": solr_docs,
        "authors": solr_authors,
    }
    
    try:
        solr_core = cores[core]
    except Exception as e:
        logger.debug(f"Core selection: {core}. 'docs' is default {e}")
        solr_core  = solr_docs    

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

def name_id_list(names_mess):
    ret_val = []
    names = HumanNames(names_mess)
    try:
        for n in names.human_names:
            if n.last != "":
                name_id = n.last + f", {n.first[0]}."
                ret_val.append(name_id)
            else:
                ret_val.append(n.first)
            
    except Exception as e:
        logger.warning(f"name parse: {names_mess} {e}")
        print (e)

    return ret_val
        

def author_name_to_wildcard(author_list_str: str):
    ret_val = re.sub(" and ", " && ", author_list_str, re.IGNORECASE)
    ret_val = re.sub(",(\s[A-Z]\.){1,2}([\s,]?)", '* ', ret_val, flags=re.IGNORECASE)

    return ret_val

def dict_clean_none_terms(d: dict):
    return {
       k:v.strip()
      for k, v in d.items()
      if v is not None
   }

def smart_search(smart_search_text):
    """
    Function to take an input string and parse out information to do a search against the DOCS core schema.
    
    Some simple syntax is implemented to help identify certain functionality.
    
        schema_field:terms  = Solr field from schema, search terms against it.  (Will be presented
            to solr as field:(terms).  Multiple terms are permitted, but currently, only one field
            specification is permitted.  Field names are converted to lower case automatically.
            
            art_doi:10.1111/j.1745-8315.2012.00606.x
            art_authors_text:[tuckett and fonagy]            
           
        doi = Just enter a DOI
           10.1111/j.1745-8315.2012.00606.x 
        
        AuthorName Year = One or more names (initial capital), followed by a year
            Tuckett and Fonagy 1972
            Tuckett and Fonagy (1972)
            
    >>> smart_search("Kohut, H. & Wolf, E. S. (1978)")
    {'schema_field': 'art_authors_citation', 'schema_value': "'Kohut, H.' && 'Wolf, E.'"}
    
    >>> smart_search("authors:Tuckett, D.")
    {'schema_field': 'authors', 'schema_value': 'Tuckett, D.'}
    
    >>> smart_search("Tuckett 1982")
    {'author_list': 'Tuckett', 'yr': '1982'}
    
    >>> smart_search("solr::art_authors_text:[tuckett and fonagy]")
    {'syntax': 'solr', 'query': 'art_authors_text:[tuckett and fonagy]'}

    >>> smart_search("009:0015")
       
    >>> smart_search("Freud, S. ( 1938), Some elementary lessons in psycho-analysis, Standard Edition. 23:279-286. pp. London: Hogarth Press, 1964.")
    {'author_list': 'Freud, S.', 'yr': '1938', 'vol': '23', 'pgrg': '279-286'}
    >>> smart_search("Tuckett")
    {'author': 'Tuckett'}

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
    
    if re.match("[A-Z\-]{2,9}\.[0-9]{3,3}[A-Z]?\.[0-9]{4,4}[A-Z]?", smart_search_text, flags=re.IGNORECASE):
        loc_corrected = smart_search_text.upper()
        if is_value_in_field(loc_corrected, "art_id"):
            ret_val = {"art_id": loc_corrected}
    
    if ret_val == {}:
        patterns1 = {
                    rx_author_list_and_year : "author_list_and_year",
                    rx_year_pgrg : "rx_year_pgrg",
                    ".*?" + rx_vol_pgrg : "rx_vol_pgrg",
                    rx_doi : "rx_doi",
                    rx_solr_field: "rx_solr_field", 
                    rx_syntax: "rx_syntax",
                    }

        #patterns2 = {
                    #rx_series_of_author_last_names: "author_list", 
                    #rx_author_name_list: "author_list",
                    #rx_author_name: "author_list",
                    #}

        for rx_str, label in patterns1.items():
            m = re.match(rx_str, smart_search_text)
            if m is not None:
                ret_val = {**ret_val, **m.groupdict()}

        #for rx_str, label in patterns2.items():
            #m = re.match(rx_str, smart_search_text)
            #if m is not None:
                #if ret_val.get(label) is None: # Pass 2 - if not already found
                    #ret_val = {**ret_val, **m.groupdict()}

        if ret_val == {}:
            # nothing found yet.
            # see if it's a title
            words = smart_search_text.split(" ")
            word_count = len(words)
            words = [re.sub('\"|\\\:', "", n) for n in words]
            words = " ".join(words)
            words = cleanup_solr_query(words)
            if word_count == 1 and len(words) > 3:
                # could still be an author name
                if is_value_in_field(words, core="authors", field="authors"):
                    ret_val["schema_field"] = "art_authors_citation" 
                    ret_val["schema_value"] = f"{words}"            elif word_count > 4 and is_value_in_field(words, "title", match_type="ordered") == 1: # unique match only
                ret_val["title"] = words
            elif is_value_in_field(words, core="doc", field="art_authors_citation"):
                # see if it's a list of names
                ret_val["schema_field"] = "art_authors_citation" 
                ret_val["schema_value"] = f"{words}"
            elif is_value_in_field(words, core="doc", field="text", match_type="proximate"):
                ret_val["wordsearch"] = re.sub(":", "\:", smart_search_text)
            else:
                # try to build a list of names, and check them individually
                new_q = ""
                names = name_id_list(smart_search_text)
                for name in names:
                    try:
                        if is_value_in_field(name, core="doc", field="authors"):
                            # ok, this is a list of names
                            if new_q != "":
                                new_q += f" && '{name}'"
                            #else:
                                #new_q += f"'{name}'"
                    except Exception as e:
                        logger.warning(f"Value error for {name}. {e}")
                
                if new_q != "":
                    ret_val["schema_field"] = "authors" 
                    ret_val["schema_value"] = f"{new_q}"
                else:
                    #  join the names
                    name_conjunction = " && ".join(names)
                    if is_value_in_field(name_conjunction, core="doc", field="art_authors_citation", match_type="bool"):
                        ret_val["schema_field"] = "art_authors_citation" 
                        ret_val["schema_value"] = f"{name_conjunction}"
    
    #  cleanup 
    if ret_val.get("art_id") is not None:
        ret_val["art_id"] = ret_val["art_id"].upper()
    elif ret_val.get("doi") is not None:
        pass # we're done
    #elif ret_val.get("schema_field") is not None:
        #schema_field = ret_val.get("schema_field")
        #if schema_field is not None:
            #if schema_field == "authors":
                #ret_val["author_list"] = ret_val.get("schema_value")
                #del ret_val["schema_field"]
                #del ret_val["schema_value"]
            #else:
                #ret_val["schema_field"] = ret_val["schema_field"].lower()
        
    # print (ret_dict)
    if ret_val == {}:
        ret_val["wordsearch"] = re.sub(":", "\:", smart_search_text)

    ret_val = dict_clean_none_terms(ret_val)
    return ret_val

def smart_search_v2(smart_search_text):
    """
    Function to take an input string and parse out information to do a search against the DOCS core schema.
    
    Some simple syntax is implemented to help identify certain functionality.
    
        schema_field:terms  = Solr field from schema, search terms against it.  (Will be presented
            to solr as field:(terms).  Multiple terms are permitted, but currently, only one field
            specification is permitted.  Field names are converted to lower case automatically.
            
            art_doi:10.1111/j.1745-8315.2012.00606.x
            art_authors_text:[tuckett and fonagy]            
           
        doi = Just enter a DOI
           10.1111/j.1745-8315.2012.00606.x 
        
        AuthorName Year = One or more names (initial capital), followed by a year
            Tuckett and Fonagy 1972
            Tuckett and Fonagy (1972)
            
    >>> smart_search("Kohut, H. & Wolf, E. S. (1978)")
    {'schema_field': 'art_authors_citation', 'schema_value': "'Kohut, H.' && 'Wolf, E.'"}
    
    >>> smart_search("authors:Tuckett, D.")
    {'schema_field': 'authors', 'schema_value': 'Tuckett, D.'}
    
    >>> smart_search("Tuckett 1982")
    {'author_list': 'Tuckett', 'yr': '1982'}
    
    >>> smart_search("solr::art_authors_text:[tuckett and fonagy]")
    {'syntax': 'solr', 'query': 'art_authors_text:[tuckett and fonagy]'}

    >>> smart_search("009:0015")
       
    >>> smart_search("Freud, S. ( 1938), Some elementary lessons in psycho-analysis, Standard Edition. 23:279-286. pp. London: Hogarth Press, 1964.")
    {'author_list': 'Freud, S.', 'yr': '1938', 'vol': '23', 'pgrg': '279-286'}
    >>> smart_search("Tuckett")
    {'author': 'Tuckett'}

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
    
    if re.match("[A-Z\-]{2,9}\.[0-9]{3,3}[A-Z]?\.[0-9]{4,4}[A-Z]?", smart_search_text, flags=re.IGNORECASE):
        # PEP Locator
        loc_corrected = smart_search_text.upper()
        if is_value_in_field(loc_corrected, "art_id"):
            ret_val = {"art_id": loc_corrected}
    
    if ret_val == {}:
        # Smartpatterns: 
        patterns1 = {
                    rx_author_list_and_year : "author_list_and_year",
                    rx_year_pgrg : "rx_year_pgrg",
                    ".*?" + rx_vol_pgrg : "rx_vol_pgrg",
                    rx_doi : "rx_doi",
                    rx_solr_field: "rx_solr_field", 
                    rx_syntax: "rx_syntax",
                    }

        for rx_str, label in patterns1.items():
            m = re.match(rx_str, smart_search_text)
            if m is not None:
                ret_val = {**ret_val, **m.groupdict()}

        if ret_val == {}:
            # nothing found yet.
            # see if it's a title
            words = smart_search_text.split(" ")
            word_count = len(words)
            words = [re.sub('\"|\\\:', "", n) for n in words]
            words = " ".join(words)
            words = cleanup_solr_query(words)
            title_search = presearch_field(words, "title", match_type="ordered")
            text_search = presearch_field(words, core="doc", field="text", match_type="proximate")
            authors_search = presearch_field(words, core="authors", field="authors")
            authors_citation_search = presearch_field(words, core="doc", field="art_authors_citation")

            if word_count == 1 and len(words) > 3:
                # could still be an author name
                if authors_search.found:
                    ret_val["schema_field"] = "art_authors_citation" 
                    ret_val["schema_value"] = f"{words}"
            elif word_count > 2 and title_search.found and text_search.found:
                if title_search.score > text_search.score:
                    ret_val["title"] = words
                else:
                    ret_val["wordsearch"] = re.sub(":", "\:", smart_search_text)
            elif authors_citation_search.found:
                # see if it's a list of names
                ret_val["schema_field"] = "art_authors_citation" 
                ret_val["schema_value"] = f"{words}"
            elif text_search.found:
                ret_val["wordsearch"] = re.sub(":", "\:", smart_search_text)
            else:
                # try to build a list of names, and check them individually
                new_q = ""
                names = name_id_list(smart_search_text)
                for name in names:
                    try:
                        if is_value_in_field(name, core="doc", field="authors"):
                            # ok, this is a list of names
                            if new_q != "":
                                new_q += f" && '{name}'"
                            #else:
                                #new_q += f"'{name}'"
                    except Exception as e:
                        logger.warning(f"Value error for {name}. {e}")
                
                if new_q != "":
                    ret_val["schema_field"] = "authors" 
                    ret_val["schema_value"] = f"{new_q}"
                else:
                    #  join the names
                    name_conjunction = " && ".join(names)
                    if is_value_in_field(name_conjunction, core="doc", field="art_authors_citation", match_type="bool"):
                        ret_val["schema_field"] = "art_authors_citation" 
                        ret_val["schema_value"] = f"{name_conjunction}"
    
    #  cleanup 
    if ret_val.get("art_id") is not None:
        ret_val["art_id"] = ret_val["art_id"].upper()
    elif ret_val.get("doi") is not None:
        pass # we're done
    #elif ret_val.get("schema_field") is not None:
        #schema_field = ret_val.get("schema_field")
        #if schema_field is not None:
            #if schema_field == "authors":
                #ret_val["author_list"] = ret_val.get("schema_value")
                #del ret_val["schema_field"]
                #del ret_val["schema_value"]
            #else:
                #ret_val["schema_field"] = ret_val["schema_field"].lower()
        
    # print (ret_dict)
    if ret_val == {}:
        ret_val["wordsearch"] = re.sub(":", "\:", smart_search_text)

    ret_val = dict_clean_none_terms(ret_val)
    return ret_val

if __name__ == "__main__":
    global options  # so the information can be used in support functions
    options = None
    programNameShort = "TestSmartSearch"  
    logFilename = programNameShort + "_" + datetime.today().strftime('%Y-%m-%d') + ".log"

    parser = OptionParser(usage="%prog [options] - PEP Solr Reference Text Data Loader", version="%prog ver. 0.1.14")
    parser.add_option("--test", dest="testmode", action="store_true", default=False,
                      help="Run Doctests")

    (options, args) = parser.parse_args()

    if options.testmode:
        import doctest
        doctest.testmod()
        print ("Fini. Tests complete.")
        sys.exit()

    while "a" is not None:
        ssrch = input ("Enter search:")
        result = smart_search(ssrch)



