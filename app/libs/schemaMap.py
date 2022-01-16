#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326

"""
SchemaMap

Used to map solr fields to more common user names and vice versa

2020.0106.1 - First version

Notes:
  2020-03-13 - Added Body to USER2SOLR_MAP as a standalone item, in case someone issues it like that through advanced.  But normally, you should use doc to include summaries or appxs
  2021.0519 - Also see opasConfig, many schema dependent names there.  Consolidated some the sort related ones here

"""

import re

# specify fields for sort, the variable allows ASC and DESC to be varied during calls.
SORT_BIBLIOGRAPHIC = "art_authors_citation_str {0}, art_year {0}, art_title_str {0}"
SORT_YEAR = "art_year {0}"
SORT_AUTHOR = "art_authors_citation_str {0}"
SORT_TITLE = "art_title_str {0}"
SORT_SOURCE = "art_sourcetitlefull_str {0}"
SORT_CITATIONS = "art_cited_5 {0}"
SORT_VIEWS = "art_views_last6mos {0}"
SORT_TOC = "art_sourcetitlefull_str {0}, art_year {0}, art_iss {0}, art_pgrg {0}"
SORT_SCORE = "score {0}"

# Dict = sort key to use, fields, default direction if one is not specified.
PREDEFINED_SORTS = {
    "bibliographic": (SORT_BIBLIOGRAPHIC, "asc"),
    "year":(SORT_YEAR, "desc"),
    "author":(SORT_AUTHOR, "asc"),
    "title":(SORT_TITLE, "asc"),
    "source":(SORT_SOURCE, "asc"),
    "citations":(SORT_CITATIONS, "desc"),
    "views":(SORT_VIEWS, "desc"),
    "toc":(SORT_TOC, "asc"),
    "score":(SORT_SCORE, "desc"),
    # legacy/historical naming for sorts
    "citecount":(SORT_CITATIONS, "desc"), 
    "rank":(SORT_SCORE, "desc"), 
    }

SORT_FIELD_MAP = {
    "documentid": ('art_id', 'asc'),
    "doctype": ('art_type', 'asc'),
    "documentref": (SORT_BIBLIOGRAPHIC, "asc"),
    "authors": (SORT_BIBLIOGRAPHIC, "asc"),
    "authormast": ('art_authors_mast', 'asc'),
    "pepcode": ('art_id', 'asc'),
    "sourcetitle": ('art_sourcetitlefull', 'asc'),
    "sourcetype": ('sourcetype', 'asc'),
    "vol": ('art_vol', 'asc'),
    "year": ('art_year', 'asc'),
    "issue": ('art_iss', 'asc'),
    "lang": ('language', 'asc'),
    "issn": ('art_issn', 'asc'),
    "isbn": ('art_isbn', 'asc'),
    "doi": ('art_doi', 'asc'),
    "figures": ('art_fig_count', 'desc'),
    "tables": ('art_tbl_count', 'desc'),
    "words": ('art_words_count', 'desc'),
    "referencecount": ('art_reference_count', 'asc'), 
    "viewslastmonth": ('art_views_last1mos', 'desc'),
    "viewslastweek": ('art_views_lastweek', 'desc'),
    "viewslastyear": ('art_views_last12mos', 'desc'),
    "viewslastcalyear": ('art_views_lastcalyear', 'desc'),
    "viewslastsixmonths": ('art_views_last6mos', 'desc'),
    "pgstart": ('art_pgrg', 'asc'),
    "rank": ('score', 'desc'),
    "score": ('score', 'desc') # make sure there's a default sort direction of desc when they say score.
}

SOLRPARENT2USER_MAP = {}

# Map client names to schema parent names for level 2 items
USER2SOLRPARENT_MAP = {
    "doc" : "(p_body || p_summaries || p_appxs)",
    "body" : "(p_body)",
    "abstract" : "(p_abstract)",
    "headings": "(p_heading)",
    "quotes": "(p_quote)",
    "dreams": "(p_dream)",
    "poems": "(p_poem)",
    "notes": "(p_note)",
    "dialogs": "(p_dialog)",
    "panels": "(p_panel)",
    "captions": "(p_captions)",
    "biblios": "(p_bib)",
    "appendixes": "(p_appxs)",
    "summaries": "(p_summaries)",
}

# use this to add "equivalent" field names to help users.
USER2SOLRFIELDNAME_MAP = {
    "author" : "authors",
    "abstract" : "abstract_xml",
    "heading": "headings_xml",
    "quote": "quotes",
    "dream": "dreams",
    "poem": "poems",
    "note": "notes",
    "dialog": "dialogs",
    "panel": "panels",
    "caption": "captions",
    "bibs": "references",
    "biblios": "references",
    "bibliographies": "references",
    "body": "body_xml",
    "appxs": "appxs_xml",
    "appendixes": "appxs_xml",
    "summaries": "summaries_xml",
    "type": "art_type",
    "code": "art_sourcecode",
    "src": "art_sourcecode",
    "src_code": "art_sourcecode",
    "journal_code": "art_sourcecode",
    "src_title": "art_sourcetitlefull",
    "source_title": "art_sourcetitlefull",
    "journal": "art_sourcetitlefull",
    "bibliography": "references",
    "page_count" : "art_pgcount",
    "table_count" : "art_tblcount" ,
    "figure_count" : "art_figcount" ,
    "abstract_count" : "art_abs_count" ,
    "keyword_count" : "art_kwds_count" , 
    "footnote_count" : "art_ftns_count" , 
    "term_count" : "art_terms_count", 
    "quote_count" : "art_quotes_count", 
    "dream_count" : "art_dreams_count" , 
    "dialog_count" : "art_dialogs_count", 
    "note_count" : "art_notes_count", 
    "poem_count" : "art_poems_count", 
    "citaton_count" : "art_citations_count", 
    "heading_count" : "art_headings_count", 
    "paragraph_count" : "art_paras_count", 
    "character_count" : "art_chars_count", 
    "nonspace_count" : "art_chars_no_spaces_count", 
    "word_count" : "art_words_count", 
    "author_count" : "art_authors_count", 
    "reference_count" : "art_reference_count",
    "newsecnm" : "art_newsecnm",
    "section_name" : "art_newsecnm",
    "section_title": "art_newsecnm",
    "issn" : "art_issn",
    "isbn" : "art_isbn",
    "volume" : "art_vol",
    "vol" : "art_vol",
    "doi" : "art_doi",
    "lang": "language",
    "graphic":"art_graphic_list",
}

FIELD2USER_MAP = {
    "art_author" : "author",
    "art_authors_text" : "author",
    "art_year" : "year",
    "art_pepsource" : "source",
    "art_sourcecode" : "source",
    "art_newsecnm": "section_name",
    "art_vol": "volume",
    "art_doi": "doi",
    "language": "lang",
    "text_xml" : "text",
    "art_cited_5" : "cited, cited in the last 5 years",
    "art_cited_10" : "cited, cited in the last 10 years",
    "art_cited_20" : "cited, cited in the last 20 years",
}

def boolean_ops_to_symbols(query_string):
    ret_val = query_string
    ret_val = re.sub("\sOR\s", " || ", ret_val)
    ret_val = re.sub("\sAND\s", " && ", ret_val)
    return ret_val

# reverse it for the SOLR2USER conversion
for key, val in USER2SOLRPARENT_MAP.items():
    # Map schema names back to client names
    SOLRPARENT2USER_MAP[val] = key
    
def solrparent2user(solr_key_name):
    """
    Convert a solr to a user schema name
    
    >>> solrparent2user("(p_body OR p_summaries OR p_appxs)")
    'doc'
    """
    solr_key_name = boolean_ops_to_symbols(solr_key_name)
    ret_val = SOLRPARENT2USER_MAP.get(solr_key_name, solr_key_name)
    return ret_val
    
def user2solrparent(user_key_name):
    """
    Convert a user to a Solr schema name
    
    >>> user2solrparent("doc")
    '(p_body || p_summaries || p_appxs)'
    
    """
    ret_val = USER2SOLRPARENT_MAP.get(user_key_name, user_key_name)
    return ret_val

def user2solrfieldname(user_key_name):
    """
    Convert a user variation of a standard field name to a standard Solr schema name
    
    >>> user2solrfieldname("author")
    'authors'
    
    """
    ret_val = USER2SOLRFIELDNAME_MAP.get(user_key_name, user_key_name)
    return ret_val

def user2solrReplace(query):
    """
    ### NOT USED CURRENTLY
    
    Find the parent and convert it; problem is this will only work for a single parent query
    
    >>> query = "{!parent which='art_level:1'} (art_level:2 AND parent_tag:doc AND para:('successful therapy' AND methods))"
    >>> user2solrReplace(query)
    "{!parent which='art_level:1'} (art_level:2 AND parent_tag:(p_body || p_summaries || p_appxs) AND para:('successful therapy' AND methods))"
    
    """
    ret_val = query
    parent_rgx = re.compile(r"parent\_tag\:(?P<ptag>[^ ]+)[ ]", re.IGNORECASE)
    pm = parent_rgx.search(query)
    if pm is not None:
        parent = pm.group("ptag")
        ret_val = query.replace(parent, user2solrparent(parent))
    return ret_val
    
    
if __name__ == "__main__":
    import doctest
    doctest.testmod()    

    print ("...tests all done...")