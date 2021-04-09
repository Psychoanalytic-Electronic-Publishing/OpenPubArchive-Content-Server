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
rx_series_of_author_last_names = "(?P<author_list>([A-Z][a-z]+((\,\s+)|(\s*and\s+))?)+)"
rx_doi = "((h.*?://)?(.*?/))?(?P<doi>(10\.[0-9]{4,4}/[A-z0-9\.\-/]+)|(doi.org/[A-z0-9\-\./]+))"
# rx_pepdoi = "(?P<prefix>PEP\/\.)(?P<locator>[A-Z\-]{2,10}\.[0-9]{3,3}\.[0-9]{4,4}([PN]{1,2}[0-9]{4,4})?"

# schema fields must have a _ in them to use.  A - at the beginning is allowed, for negation
rx_solr_field = "(?P<schema_field>(\-?[a-z]+_[a-z_]{2,21})|text|authors)\:(?P<schema_value>(.*$))"
rx_syntax = "(?P<schema_field>^[a-z]{3,9})\:\:(?P<schema_value>.+$)"

pat_prefix_amps = re.compile("^\s*&& ")

cores = CORES

class SearchEvaluation(object):
    def __init__(self, field=None, found=0, score=0): 
        self.score = score
        self.field = field
        self.found = found
        self.isfound = found > 0

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
    else:
        q = f'{field}:({value})'

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
            
    >>> ret_dict = smart_search("Freud, S. ( 1938), Some elementary lessons in psycho-analysis, Standard Edition. 23:279-286. pp. London: Hogarth Press, 1964.")
    >>> del ret_dict['smart_search']
    >>> ret_dict
    {'author_list': 'Freud, S.', 'yr': '1938', 'vol': '23', 'pgrg': '279-286', 'search_type': 'pattern authors year vol pgrg'}

    >>> ret_dict = smart_search("009:1015")
    >>> del ret_dict['smart_search']
    >>> ret_dict
    {'vol': '9', 'pgrg': '1015', 'search_type': 'pattern vol and page range'}
    
    >>> ret_dict = smart_search("Tuckett")
    >>> del ret_dict['smart_search']
    >>> ret_dict
    {'search_type': 'author citation', 'schema_field': 'art_authors_citation', 'schema_value': 'Tuckett'}
       
    >>> ret_dict = smart_search("Kohut, H. & Wolf, E. S. (1978)")
    >>> del ret_dict['smart_search']
    >>> ret_dict
    {'author_list': 'Kohut, H. & Wolf, E. S.', 'yr': '1978', 'search_type': 'pattern authors and year'}
    
    >>> ret_dict = smart_search("authors:Tuckett, D.")
    >>> del ret_dict['smart_search']
    >>> ret_dict
    {'schema_field': 'authors', 'schema_value': 'Tuckett, D.', 'search_type': 'pattern article fields'}
    
    >>> ret_dict = smart_search("Tuckett 1982")
    >>> del ret_dict['smart_search']
    >>> ret_dict
    {'author_list': 'Tuckett', 'yr': '1982', 'search_type': 'pattern authors and year'}
    
    >>> ret_dict = smart_search("solr::art_authors_text:[tuckett and fonagy]")
    >>> del ret_dict['smart_search']
    >>> ret_dict
    {'schema_field': 'solr', 'schema_value': 'art_authors_text:[tuckett and fonagy]', 'search_type': 'pattern advanced query syntax'}
    
    >>> ret_dict = smart_search("the cat in the hat was that")
    >>> del ret_dict['smart_search']
    >>> ret_dict
    {'search_type': 'paragraph search', 'schema_value': '"the cat in the hat was that"~25'}
    
    >>> ret_dict = smart_search("'the cat in the hat was that'")
    >>> del ret_dict['smart_search']
    >>> ret_dict
    {'search_type': 'literal search', 'schema_value': "'the cat in the hat was that'"}
    
    >>> tst = []
    >>> tst.append("Emerson, R. W. (1836), An essay on nature. In: The Selected Writings of Ralph Waldo Emerson, ed. W. H. Gilman. New York: New American Library, 1965, pp. 186-187.")
    >>> tst.append("Rapaport, D. and Gill, M. M. ( 1959). The Points of View and Assumptions of Metapsychology. Int. J. Psycho-Anal.40:153-162")
    >>> tst.append("Freud, S. ( 1938), Some elementary lessons in psycho-analysis, Standard Edition. 23:279-286. pp. London: Hogarth Press, 1964.")
    >>> tst.append("Waelder, R. ( 1962). Psychoanalysis, Scientific Method, and Philosophy. J. Amer. Psychoanal. Assn.10:617-637")

    >>> ret = []
    >>> for n in tst: ret.append(smart_search(n))
    >>> for n in ret: del n['smart_search'];print(n)
    {'author_list': 'Emerson, R. W.', 'yr': '1836', 'search_type': 'pattern authors and year'}
    {'author_list': 'Rapaport, D. and Gill, M. M.', 'yr': '1959', 'vol': '40', 'pgrg': '153-162', 'search_type': 'pattern authors year vol pgrg'}
    {'author_list': 'Freud, S.', 'yr': '1938', 'vol': '23', 'pgrg': '279-286', 'search_type': 'pattern authors year vol pgrg'}
    {'author_list': 'Waelder, R.', 'yr': '1962', 'vol': '10', 'pgrg': '617-637', 'search_type': 'pattern authors year vol pgrg'}
    """
    # recognize Smart Search inputs
    ret_val = {}
    # get rid of leading spaces and zeros
    smart_search_text = smart_search_text.lstrip(" 0")
    # get rid of trailing spaces and zeros
    smart_search_text = smart_search_text.rstrip(" ")
    # get rid of smart quotes
    smart_search_text = re.sub("“|”", "'", smart_search_text)
    
    if re.match("^[\"\'].*[\"\']$", smart_search_text):
        # literal string
        ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = f"Matched articles for {opasConfig.SEARCH_TYPE_LITERAL}: ({smart_search_text})"
        ret_val[opasConfig.KEY_SEARCH_TYPE] = opasConfig.SEARCH_TYPE_LITERAL
        ret_val[opasConfig.KEY_SEARCH_VALUE] = f"{smart_search_text}"
        
    if re.match("[A-Z\-]{2," + f"{opasConfig.MAX_JOURNALCODE_LEN}" + "}\.[0-9]{3,3}[A-Z]?\.[0-9]{4,4}[A-Z]?", smart_search_text, flags=re.IGNORECASE):
        # locator (articleID)
        loc_corrected = smart_search_text.upper()
        if is_value_in_field(loc_corrected, opasConfig.SEARCH_FIELD_LOCATOR):
            ret_val = {opasConfig.SEARCH_FIELD_LOCATOR: loc_corrected}

    # journal and issue and wildcard
    m = re.match("(?P<journal>[A-Z\-]{2," + f"{opasConfig.MAX_JOURNALCODE_LEN}" + "})\.(?P<vol>([0-9]{3,3}[A-Z]?)|(\*))\.(?P<page>\*)", smart_search_text, flags=re.IGNORECASE)
    if m is not None:
        src_code = m.group("journal")
        if src_code is not None:
            vol_code = m.group("vol")
            if vol_code is None:
                vol_code = "*"
        loc = f"{src_code}.{vol_code}.*"
        loc_corrected = loc.upper()

        ret_val = {"art_id": loc_corrected}

    if ret_val == {}:
        # Smartpatterns:        
        patterns1 = {
                     rx_doi : opasConfig.SEARCH_TYPE_DOI,
                     rx_solr_field: opasConfig.SEARCH_TYPE_FIELDED, 
                     rx_syntax: opasConfig.SEARCH_TYPE_ADVANCED,
                     rx_author_list_year_vol_pgrg : "authors year vol pgrg",
                     rx_author_list_and_year : "authors and year",
                     rx_cit_vol_pgrg : "citation vol/pg",
                     rx_year_pgrg : "a page range",
                     rx_vol_pgrg : "vol and page range",
                     rx_vol_wildcard : "vol and page wildcard",
                     rx_year_vol_pgrg : "yr vol page range"
                    }

        for rx_str, label in patterns1.items():
            m = re.match(rx_str, smart_search_text)
            if m is not None:
                ret_val = {**ret_val, **m.groupdict()}
                ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = f"Matched {label}: {smart_search_text}"
                ret_val[opasConfig.KEY_SEARCH_TYPE] = f"{label}"
                break
                
        if ret_val == {}:
            # nothing found yet.
            # is it in quotes (phrase?)
            words = smart_search_text.split(" ")
            word_count = len(words)
            words = [re.sub('\"|\\\:', "", n) for n in words]
            words = " ".join(words)
            words = cleanup_solr_query(words)

            #if word_count == 1 and len(words) > 3 and words[0].isupper():
                ## could still be an author name
                #if is_value_in_field(words, core="authors", field=SEARCH_FIELD_AUTHORS):
                    #ret_val[opasConfig.KEY_SEARCH_TYPE] = opasConfig.SEARCH_TYPE_AUTHORS
                    #ret_val[opasConfig.KEY_SEARCH_FIELD] = opasConfig.SEARCH_FIELD_AUTHORS 
                    #ret_val[opasConfig.KEY_SEARCH_VALUE] = f"{words}"
                    #ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = f"Matched articles for authors cited: {words}"
            if is_value_in_field(words, core="docs", field=opasConfig.SEARCH_FIELD_AUTHOR_CITATION) and words[0].isupper():
                # see if it's a list of names
                ret_val[opasConfig.KEY_SEARCH_TYPE] = opasConfig.SEARCH_TYPE_AUTHOR_CITATION
                ret_val[opasConfig.KEY_SEARCH_FIELD] = opasConfig.SEARCH_FIELD_AUTHOR_CITATION 
                ret_val[opasConfig.KEY_SEARCH_VALUE] = f"{words}"
                ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = f"Matched articles for authors cited: ({words})"

            elif word_count > 4 and is_value_in_field(words, core="docs", field=opasConfig.SEARCH_FIELD_TITLE, match_type="ordered") == 1: # unique match only
                ret_val["title"] = words
                ret_val[opasConfig.KEY_SEARCH_TYPE] = opasConfig.SEARCH_TYPE_TITLE
                ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = f"Matched words in titles: {words}"

            elif is_value_in_field(words, core="docs", field=opasConfig.SEARCH_FIELD_TEXT, match_type="proximate"):
                orig_smart_search_text = smart_search_text
                if not opasgenlib.in_quotes(smart_search_text):
                    if not opasgenlib.is_boolean(smart_search_text):
                        if not opasgenlib.in_brackets(smart_search_text):
                            smart_search_text = f'"{smart_search_text}"~25'
                            ret_val[opasConfig.KEY_SEARCH_TYPE] = opasConfig.SEARCH_TYPE_PARAGRAPH
                            ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = f"Matched paragraphs with terms: ({orig_smart_search_text})"
                            ret_val[opasConfig.KEY_SEARCH_VALUE] = f"{smart_search_text}"
                        else:
                            ret_val["wordsearch"] = re.sub(":", "\:", smart_search_text)
                            ret_val[opasConfig.KEY_SEARCH_TYPE] = opasConfig.SEARCH_TYPE_WORDSEARCH
                            ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = f"Matched articles for words: ({orig_smart_search_text})"
                    else:
                        smart_search_text = re.sub ("\snot\s", " NOT ", smart_search_text)
                        ret_val[opasConfig.KEY_SEARCH_TYPE] = opasConfig.SEARCH_TYPE_BOOLEAN
                        ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = f"Matched articles for boolean string: ({orig_smart_search_text})"
                        ret_val[opasConfig.KEY_SEARCH_VALUE] = f"{orig_smart_search_text}"
                        ret_val[opasConfig.KEY_SEARCH_VALUE] = re.sub("\s+(AND)\s+", " && ", ret_val[opasConfig.KEY_SEARCH_VALUE], flags=re.IGNORECASE)
                        ret_val[opasConfig.KEY_SEARCH_VALUE] = re.sub("\s+(OR)\s+", " || ", ret_val[opasConfig.KEY_SEARCH_VALUE], flags=re.IGNORECASE)
                        ret_val[opasConfig.KEY_SEARCH_VALUE] = re.sub("\s+(NOT)\s+", " NOT ", ret_val[opasConfig.KEY_SEARCH_VALUE], flags=re.IGNORECASE)
                else:
                    # literal
                    ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = f"Matched articles for literal string: ({orig_smart_search_text})"
                    ret_val[opasConfig.KEY_SEARCH_TYPE] = opasConfig.SEARCH_TYPE_LITERAL
                    ret_val[opasConfig.KEY_SEARCH_VALUE] = f"{orig_smart_search_text}"
                    
            elif words[0].isupper():
                # try to build a list of names, and check them individually
                new_q = ""
                names = name_id_list(smart_search_text)
                for name in names:
                    try:
                        if is_value_in_field(name, core="docs", field=opasConfig.SEARCH_FIELD_AUTHORS):
                            # ok, this is a list of names
                            if new_q != "":
                                new_q += f" && '{name}'"
                            #else:
                                #new_q += f"'{name}'"
                    except Exception as e:
                        logger.warning(f"Value error for {name}. {e}")
                
                if new_q != "":
                    ret_val[opasConfig.KEY_SEARCH_TYPE] = opasConfig.SEARCH_TYPE_AUTHORS
                    ret_val[opasConfig.KEY_SEARCH_FIELD] = opasConfig.SEARCH_FIELD_AUTHORS 
                    ret_val[opasConfig.KEY_SEARCH_VALUE] = f"{new_q}"
                else:
                    #  join the names
                    name_conjunction = " && ".join(names)
                    if is_value_in_field(name_conjunction, core="docs", field=opasConfig.SEARCH_FIELD_AUTHOR_CITATION, match_type="bool"):
                        ret_val[opasConfig.KEY_SEARCH_TYPE] = opasConfig.SEARCH_TYPE_AUTHOR_CITATION
                        ret_val[opasConfig.KEY_SEARCH_FIELD] = opasConfig.SEARCH_FIELD_AUTHOR_CITATION
                        ret_val[opasConfig.KEY_SEARCH_VALUE] = f"{name_conjunction}"
                        ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = f"Matched articles for authors: {name_conjunction} "
    
    #  cleanup 
    if ret_val.get("art_id") is not None:
        ret_val["art_id"] = ret_val["art_id"].upper()
        ret_val[opasConfig.KEY_SEARCH_TYPE] = opasConfig.SEARCH_TYPE_ID
        ret_val[opasConfig.KEY_SEARCH_FIELD] = opasConfig.SEARCH_FIELD_LOCATOR
        ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = f"Matched articles for article ID {ret_val['art_id'].upper()}:"
    elif ret_val.get("doi") is not None:
        pass # we're done

    if ret_val == {}:
        ret_val["wordsearch"] = re.sub(":", "\:", smart_search_text)
        ret_val[opasConfig.KEY_SEARCH_TYPE] = opasConfig.SEARCH_TYPE_WORDSEARCH
        ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = f"Matched articles with text: {smart_search_text}"

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



