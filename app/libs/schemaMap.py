#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326

"""
Schemamap

2020.0106.1 - First version

"""
# 2020-03-13 - Added Body to USER2SOLR_MAP as a standalone item, in case someone issues it like that through advanced.  But normally, you should use doc to include summaries or appxs

SOLR2USER_MAP = {}
import re

# Map client names to schema names
USER2SOLR_MAP = {
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

FIELD2USER_MAP = {
    "art_author" : "author",
    "art_authors_text" : "author",
    "art_year" : "year",
    "art_pepsource" : "source",
    "art_sourcecode" : "source",
    "text_xml" : "text",
    "text" : "text",
    "art_cited_5" : "cited, cited in the last 5 years",
    "art_cited_10" : "cited, cited in the last 10 years",
    "art_cited_20" : "cited, cited in the last 20 years",
}


# reverse it for the SOLR2USER conversion
for key, val in USER2SOLR_MAP.items():
    # Map schema names back to client names
    SOLR2USER_MAP[val] = key
    
def solr2user(solr_key_name):
    """
    Convert a solr to a user schema name
    
    >>> solr2user("(p_body OR p_summaries OR p_appxs)")
    'doc'
    """
    ret_val = SOLR2USER_MAP.get(solr_key_name, solr_key_name)
    return ret_val
    
def user2solr(user_key_name):
    """
    Convert a user to a Solr schema name
    
    >>> user2solr("doc")
    '(p_body OR p_summaries OR p_appxs)'
    
    """
    ret_val = USER2SOLR_MAP.get(user_key_name, user_key_name)
    return ret_val

def user2solrReplace(query):
    """
    Find the parent and convert it; problem is this will only work for a single parent query
    
    >>> query = "{!parent which='art_level:1'} (art_level:2 AND parent_tag:doc AND para:('successful therapy' AND methods))"
    >>> user2solrReplace(query)
    
    """
    ret_val = query
    parent_rgx = re.compile(r"parent\_tag\:(?P<ptag>[^ ]+)[ ]", re.IGNORECASE)
    pm = parent_rgx.search(query)
    if pm is not None:
        parent = pm.group("ptag")
        ret_val = query.replace(parent, user2solr(parent))
    return ret_val
    
    
if __name__ == "__main__":
    import doctest
    doctest.testmod()    

    print ("...tests all done...")