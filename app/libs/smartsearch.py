import re
import sys
from datetime import datetime
from optparse import OptionParser
import logging
import opasGenSupportLib as opasgenlib

# from configLib.opasCoreConfig import solr_docs2, CORES # solr_authors2, solr_gloss2, solr_docs_term_search, solr_authors_term_search
import opasConfig
import smartsearchLib

logger = logging.getLogger(__name__)

from opasSchemaInfoLib import SchemaInfo
docschemainfo = SchemaInfo()

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
    # count words
    has_wildcards = len(re.findall(r'\*|(\S?\?+\S)', smart_search_text))
    #if smart_search_includes_simple_wildcards:
        #try:
            #regc = re.compile(smart_search_text)
            #smart_search_is_regex = None # we don't know
        #except:
            #smart_search_is_regex = False # we know it's not
    
    
    if re.match("^[\"\'].*[\"\']$", smart_search_text):
        # literal string
        ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = f"Matched articles for {opasConfig.SEARCH_TYPE_LITERAL}: ({smart_search_text})"
        ret_val[opasConfig.KEY_SEARCH_TYPE] = opasConfig.SEARCH_TYPE_LITERAL
        ret_val[opasConfig.KEY_SEARCH_VALUE] = f"{smart_search_text}"
        
    if re.match("[A-Z\-]{2," + f"{opasConfig.MAX_JOURNALCODE_LEN}" + "}\.[0-9]{3,3}[A-Z]?\.[0-9]{4,4}[A-Z]?", smart_search_text, flags=re.IGNORECASE):
        # locator (articleID)
        loc_corrected = smart_search_text.upper()
        if smartsearchLib.is_value_in_field(loc_corrected, opasConfig.SEARCH_FIELD_LOCATOR):
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
        
    if ret_val == {}: # (opasConfig.SEARCH_TYPE_ADVANCED, "ADVANCED")
        # this is not much different than search_type_fielded, except the Solr query will be cleaner and perhaps more flexible.
        #  but I'll leave fielded in for now, because for a simple field search the syntax is a little better.
        if re.match(smartsearchLib.advanced_syntax, smart_search_text):
            ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = smart_search_text[5:] 
            ret_val[opasConfig.KEY_SEARCH_TYPE] ="ADVANCED"
            ret_val[opasConfig.KEY_SEARCH_FIELD] = "solr"
            ret_val[opasConfig.KEY_SEARCH_VALUE] = f"{ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH]}"
            ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = f"Matched articles for advanced search: {ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH]} "
    
    if ret_val == {}:
        # Smartpatterns:   pattern: descriptive pattern label     
        patterns1 = {
                     smartsearchLib.rx_doi : opasConfig.SEARCH_TYPE_DOI,
                     smartsearchLib.rx_solr_field: opasConfig.SEARCH_TYPE_FIELDED, 
                     #smartsearchLib.rx_syntax: opasConfig.SEARCH_TYPE_ADVANCED,
                     smartsearchLib.rx_author_list_year_vol_pgrg : "authors year vol pgrg",
                     smartsearchLib.rx_author_list_and_year : "authors and year",
                     smartsearchLib.rx_cit_vol_pgrg : "citation vol/pg",
                     smartsearchLib.rx_year_pgrg : "a page range",
                     smartsearchLib.rx_vol_pgrg : "vol and page range",
                     smartsearchLib.rx_vol_wildcard : "vol and page wildcard",
                     smartsearchLib.rx_year_vol_pgrg : "yr vol page range"
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
            words = smartsearchLib.cleanup_solr_query(words)

            pattern_boolean_test = "&&|\|\||\s(AND|OR|NOT)\s"
            has_bool = re.search(pattern_boolean_test, words) # case sensitive
            has_bool_insensitive = re.search(pattern_boolean_test, words, flags=re.I) # case sensitive
            
            if smartsearchLib.is_value_in_field(words, core="docs", field=opasConfig.SEARCH_FIELD_AUTHOR_CITATION, match_type="proximate") and words[0].isupper():
                # see if it's a list of names
                ret_val[opasConfig.KEY_SEARCH_TYPE] = opasConfig.SEARCH_TYPE_AUTHOR_CITATION
                ret_val[opasConfig.KEY_SEARCH_FIELD] = opasConfig.SEARCH_FIELD_AUTHOR_CITATION 
                ret_val[opasConfig.KEY_SEARCH_VALUE] = f"{words}"
                ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = f"Matched articles by authors: ({words})"

            if ret_val == {}:
                if 0 != smartsearchLib.is_value_in_field(words, core="docs", field=opasConfig.SEARCH_FIELD_AUTHOR_CITATION, match_type="boolean"):
                    # boolean name search
                    if words[0].isupper() and has_bool: 
                        # see if it's a list of names
                        ret_val[opasConfig.KEY_SEARCH_TYPE] = opasConfig.SEARCH_TYPE_AUTHOR_CITATION
                        ret_val[opasConfig.KEY_SEARCH_FIELD] = opasConfig.SEARCH_FIELD_AUTHOR_CITATION 
                        ret_val[opasConfig.KEY_SEARCH_VALUE] = f"{words}"
                        ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = f"Matched by authors: (boolean query: {words})"

            if ret_val == {}:
                if 0 != smartsearchLib.is_value_in_field(words, core="docs", field=opasConfig.SEARCH_FIELD_TITLE, match_type="ordered") == 1: # unique match only
                    if word_count > 4:
                        ret_val["title"] = words
                        ret_val[opasConfig.KEY_SEARCH_TYPE] = opasConfig.SEARCH_TYPE_TITLE
                        ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = f"Matched words in titles: {words}"
    
            if ret_val == {}:
                # unique match only
                if 1 == smartsearchLib.is_value_in_field(words, core="docs", field=opasConfig.SEARCH_FIELD_TITLE, match_type="proximate"): 
                    if word_count > 4:
                        ret_val["title"] = words
                        ret_val[opasConfig.KEY_SEARCH_TYPE] = opasConfig.SEARCH_TYPE_TITLE
                        ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = f"Matched words in titles: {words}"

            if ret_val == {}:
                if smartsearchLib.all_words_start_upper_case(smart_search_text):
                    # try to build a list of names, and check them individually
                    new_q = ""
                    names = smartsearchLib.get_list_of_name_ids(smart_search_text)
                    for name in names:
                        try:
                            res = smartsearchLib.is_value_in_field(name, core="docs", field=opasConfig.SEARCH_FIELD_AUTHORS, match_type="adjacent")
                            if res:
                                # ok, this is a list of names
                                if new_q != "":
                                    new_q += f" && '{name}'"
                                else: # first name
                                    new_q = f'{name}'
                            else: # name not found, they all have to be
                                new_q = ""
                                break 
                        except Exception as e:
                            logger.warning(f"Value error for {name}. {e}")
                    
                    if new_q != "":
                        ret_val[opasConfig.KEY_SEARCH_TYPE] = opasConfig.SEARCH_TYPE_AUTHORS
                        ret_val[opasConfig.KEY_SEARCH_FIELD] = opasConfig.SEARCH_FIELD_AUTHORS 
                        ret_val[opasConfig.KEY_SEARCH_VALUE] = f"{new_q}"
                    else:
                        #  join the names
                        name_conjunction = " && ".join(names)
                        if smartsearchLib.is_value_in_field(name_conjunction, core="docs", field=opasConfig.SEARCH_FIELD_AUTHOR_CITATION, match_type="adjacent"):
                            ret_val[opasConfig.KEY_SEARCH_TYPE] = opasConfig.SEARCH_TYPE_AUTHOR_CITATION
                            ret_val[opasConfig.KEY_SEARCH_FIELD] = opasConfig.SEARCH_FIELD_AUTHOR_CITATION
                            ret_val[opasConfig.KEY_SEARCH_VALUE] = f"{name_conjunction}"
                            ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = f"Matched articles for authors: {name_conjunction} "

            if ret_val == {}:
                if 1 != smartsearchLib.is_value_in_field(words, core="docs", field=opasConfig.SEARCH_FIELD_TEXT, match_type="proximate"):
                    orig_smart_search_text = smart_search_text
                    if not opasgenlib.in_quotes(smart_search_text):
                        if not opasgenlib.is_boolean(smart_search_text):
                            if not opasgenlib.in_brackets(smart_search_text) and word_count > 1:
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
                        # literal with extra at the end, could be proximate with distance, maybe other solr searches?
                        ret_val[opasConfig.KEY_SEARCH_SMARTSEARCH] = f"Matched articles for: ({orig_smart_search_text})"
                        ret_val[opasConfig.KEY_SEARCH_TYPE] = opasConfig.SEARCH_TYPE_LITERAL
                        ret_val[opasConfig.KEY_SEARCH_VALUE] = f"{orig_smart_search_text}"
                    
   
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

    ret_val = smartsearchLib.dict_clean_none_terms(ret_val)
    
    # parse author list
    author_list = ret_val.get("author_list")
    if author_list is not None:
        working_author_list = re.sub(" and ", ", ", author_list, re.I)
        try:
            alist = opasgenlib.get_author_list_not_comma_separated(working_author_list)
            ret_val["author_list"] = alist
        except Exception as e:
            logging.warning(f"Can't parse and replace author list {e}")
    
        if alist == []:
            # try and?
            try:
                alist = opasgenlib.get_author_list_and_separated(author_list)
                ret_val["author_list"] = alist
            except Exception as e:
                logging.warning(f"Can't parse and replace author list {e}")
            
        ret_val["author_list"] = smartsearchLib.get_list_of_name_ids(author_list)
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



