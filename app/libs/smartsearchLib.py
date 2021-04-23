
import re
import sys
from datetime import datetime
from optparse import OptionParser
import logging
import opasGenSupportLib as opasgenlib

from configLib.opasCoreConfig import solr_docs2, CORES # solr_authors2, solr_gloss2, solr_docs_term_search, solr_authors_term_search
import opasConfig

logger = logging.getLogger(__name__)

from namesparser import HumanNames
rx_space_req = "(\s+|\s*)"
rx_space_opt = "(\s*|\s*)"
rx_space_end_opt = "(\s*|\s*)$"
rx_space_start_opt = "^(\s*|\s*)?"
rx_year = "\(?\s*(?P<yr>(18|19|20)[0-9]{2,2})\s*\)?"
rx_title = ".*?"
rx_space_or_colon = "((\s*\:\s*)|\s+)"
rx_vol = "((?P<vol>([\(]?[0-9]{1,3}[\)]?))\:)"
# rx_pgrg = f"(pp\.?\s+)|{rx_vol}(?P<pgrg>[1-9][0-9]{0,3}([-][1-9][0-9]{0,3})?)"
rx_pgrg = "(?P<pgrg>[1-9][0-9]{0,3}([-][1-9][0-9]{0,3})?)"
rx_cit_vol_pgrg = "([A-Z].*(\s|,))" + rx_vol + rx_pgrg + ".*"
rx_vol_pgrg = rx_vol + rx_pgrg
rx_yr_vol_pgrg = rx_year + "[\s|,]" + rx_vol_pgrg
rx_vol_wildcard = rx_vol + "\*"
rx_year_pgrg = rx_space_start_opt + rx_year + rx_space_or_colon + rx_pgrg + rx_space_end_opt
rx_year_vol_pgrg = rx_year + rx_vol_pgrg + rx_space_end_opt
rx_author_name = "(?P<author>[A-Z][a-z]+)(\,\s+(([A-Z]\.?\s?){0,2})\s*)?"
rx_fuzzy_search = "[A-z]+~[0-9]"
rx_author_connector = "(and|,)"
rx_front_junk = "(\[|\()?[0-9]+(\]|\))?"
# rx_author_and_year = rx_space_start_opt + rx_author_name + rx_space_req + rx_year + rx_space_end_opt
# rx_author_year_pgrg = rx_author_and_year + ".*?" + rx_pgrg
# rx_author_name_list_year = rx_author_name_list + rx_space_req + rx_year
rx_amp_opt = "(\&\s+)?"

# replaced 2021-02-15 with def that follows it:
#     rx_author_list_and_year = "(?P<author_list>[A-Z][A-z\s\,\.\-]+?)" + rx_space_req + rx_year
rx_author_name_list = "(?P<author_list>([A-Z][A-z]+\,?\s+?(([A-Z]\.?\s?){0,2})((\,\s+)|(\s*(and|\&)\s+))?)+)"
rx_author_list_and_year = rx_author_name_list + rx_year
rx_author_list_year_vol_pgrg = rx_author_list_and_year + ".*?" + rx_vol_pgrg
# rx_one_word_string = "[^\s]"
# rx_has_wildcards = "[*?]"
rx_series_of_author_last_names = "(?P<author_list>([A-Z][a-z]+((\,\s+)|(\s*and\s+))?)+)"
rx_doi = "((h.*?://)?(.*?/))?(?P<doi>(10\.[0-9]{4,4}/[A-z0-9\.\-/]+)|(doi.org/[A-z0-9\-\./]+))"
# rx_pepdoi = "(?P<prefix>PEP\/\.)(?P<locator>[A-Z\-]{2,10}\.[0-9]{3,3}\.[0-9]{4,4}([PN]{1,2}[0-9]{4,4})?"

# schema fields must have a _ in them to use.  A - at the beginning is allowed, for negation
# user search fields (PEP Spec)
# USER_SEARCH_FIELDS = "authors|dialogs|dreams|headings|keywords|notes|panels|poems|quotes|references|source|sourcecode|text|volume|year|art_*"
USER_SEARCH_FIELDS = "[a-z_]*"
rx_solr_field = f"(?P<schema_field>^{USER_SEARCH_FIELDS})\:(?P<schema_value>([^:]*$))" # only one field permitted
# rx_syntax = "(?P<schema_field>^[a-z]{3,9})\:\:(?P<schema_value>.+$)"
advanced_syntax = f"(?P<schema_field>^adv)\:\:(?P<schema_value>.+$)"

pat_prefix_amps = re.compile("^\s*&& ")

rx_quoted_str_has_wildcards = r"(\"|\').*(\*|\?).*\1"
pat_quoted_str_has_wildcards = re.compile(rx_quoted_str_has_wildcards, flags=re.I)
rx_str_has_wildcards = r".*(\*|\?).*"
pat_str_has_wildcards = re.compile(rx_quoted_str_has_wildcards, flags=re.I)
pat_str_has_fuzzy_search = re.compile(rx_fuzzy_search, flags=re.I)
cores = CORES

class SearchEvaluation(object):
    def __init__(self, field=None, found=0, score=0): 
        self.score = score
        self.field = field
        self.found = found
        self.isfound = found > 0

def all_words_start_upper_case(search_str):
    """
    >>> all_words_start_upper_case(r"The Rain in Spain")
    False
    >>> all_words_start_upper_case(r"The Rain In Spain")
    True
    """
    ret_val = True
    for word in search_str.split():
        if not word[0].isupper() and word not in ("and"):
            ret_val = False
            break

    return ret_val

def quoted_str_has_wildcards(search_str):
    """
    Test if string which has a substring in quotes, that has wildcards.
    
    >>> result = quoted_str_has_wildcards(r"'test* 12?'")
    >>> result is not None
    True
    
    >>> result = quoted_str_has_wildcards(r"'test** 12?  '")
    >>> result is not None
    True
    """
    ret_val = False
    if pat_quoted_str_has_wildcards.search(search_str):
        ret_val = True

    return ret_val

def str_has_fuzzy_ops(search_str):
    if pat_str_has_fuzzy_search.search(search_str):
        return True
    else:
        return False
    
def str_has_wildcards(search_str):
    """
    Test if string which has a substring in quotes, that has wildcards.
    
    >>> result = str_has_wildcards(r"test* 12?")
    >>> result is not None
    True
    
    >>> result = str_has_wildcards(r"test** 12?  ")
    >>> result is not None
    True
    """
    ret_val = False
    if pat_str_has_wildcards.search(search_str):
        ret_val = True

    return ret_val

#-----------------------------------------------------------------------------
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
    elif match_type == "adjacent":
        q = f'{field}:"{value}"~2'
    else:
        q = f'{field}:({value})'

    if str_has_wildcards(q): # quoted_str_has_wildcards(q):
        complex_phrase = "{!complexphrase}"
        q = f"{complex_phrase}{q}"

    try:
        results = solr_core.search(q=q,  
                                   fields = f"{field}", 
                                   rows = limit,
                                   )
    except Exception as e:
        logger.warning(f"Solr query: {q} fields {field} {e}")
        results = []
       
    if len(results) > 0: 
        ret_val = len(results) # results.numFound # it looks like the solr response object to this query always has a len == numFound

    return ret_val

#-----------------------------------------------------------------------------
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
        
#-----------------------------------------------------------------------------
def author_name_to_wildcard(author_list_str: str):
    ret_val = re.sub(" and ", " && ", author_list_str, re.IGNORECASE)
    ret_val = re.sub(",(\s[A-Z]\.){1,2}([\s,]?)", '* ', ret_val, flags=re.IGNORECASE)

    return ret_val

#-----------------------------------------------------------------------------
def dict_clean_none_terms(d: dict):
    return {
       k:v.strip()
      for k, v in d.items()
      if v is not None
   }

WORDS_NOT_CAPITALIZED = ["the", "and", "but", "in", "for", "a", "an", "at", "by", "to", "etc"]

#-----------------------------------------------------------------------------
def word_is_noun(word: str, stop_words=WORDS_NOT_CAPITALIZED):
    ret_val = False

    if len(word) > 3:
        if word not in stop_words:
            if word[0].isupper() and not word[1].isupper() and not word[2].isupper():
                ret_val = True
            else:
                ret_val = False

    return ret_val

#-----------------------------------------------------------------------------
def names_only(phrase: str):
    """
    >>> names_only("The Rain in Spain")
    False
    >>> names_only("Edward Scissorhands")
    True
    >>> names_only("Tuckett and Fonagy")
    True
    """
    # try to build a list of names, and check them individually
    ret_val = False
    new_q = ""
    hnames = HumanNames(phrase)
    names = name_id_list(phrase)
    for name in names:
        try:
            if is_value_in_field(name, core="docs", field=opasConfig.SEARCH_FIELD_AUTHOR_CITATION):
                # ok, this is a list of names
                ret_val = True
                if new_q != "":
                    new_q += f" && '{name}'"
        except Exception as e:
            logger.warning(f"Value error for {name}. {e}")
    
    return ret_val
#-----------------------------------------------------------------------------
def proper_nouns_or_names(phrase: str, stop_words=WORDS_NOT_CAPITALIZED):
    """
    See if the words longer than 2 chars and non-numeric start with a capital, but are not all capitals
    
    >>> proper_nouns_or_names("The Rain in Spain")
    True
    >>> proper_nouns_or_names("Edward Scissorhands")
    True
    
    >>> proper_nouns_or_names("Every dog has its Day")
    False
    """
    ret_val = True
    for word in phrase:
        if word not in stop_words:
            if not word_is_noun(word):
                ret_val = False
                break

    return ret_val
                
                
if __name__ == "__main__":
    global options  # so the information can be used in support functions
    options = None

    parser = OptionParser(usage="%prog [options] - PEP Solr Reference Text Data Loader", version="%prog ver. 0.1.14")
    parser.add_option("--test", dest="testmode", action="store_true", default=False,
                      help="Run Doctests")

    (options, args) = parser.parse_args()

    if 1: # options.testmode:
        import doctest
        doctest.testmod()
        print ("Fini. Tests complete.")
        sys.exit()

