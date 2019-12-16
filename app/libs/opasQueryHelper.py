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
        self.token_word = re.compile(regex_token_word, re.IGNORECASE)
        self.token_implied_and = re.compile("(^&&)+\s", re.IGNORECASE) 
        
    def markup(self, str_input, field_label, field_thesaurus=None):
        def quotedrepl(matchobj):
            self.counter += 1
            return f'QS{self.counter}'

        if field_thesaurus is None:
            field_thesaurus = field_label

        qualified, sq = search_qualifiers(str_input, field_label=field_label, field_thesaurus=field_label)
        if qualified:
            ret_val = sq
        else:
            self.counter = 0
            token_list = self.token_quoted.findall(str_input)
            ret_val = self.token_quoted.sub(quotedrepl, str_input)
            ret_val = re.sub("w\s*/\s*[0-9]{1,10}", "", ret_val)
            term_check = ret_val.split()
            i = 0
            while 1:
                if i == len(term_check) - 1:
                    break
                if re.match("&&|\|\||and|or", term_check[i].strip(), re.IGNORECASE) is None:
                    if re.match("&&|\|\||and|or", term_check[i+1].strip(), re.IGNORECASE) is None:
                        #  need to insert one!
                        term_check.insert(i+1, "and")
                i += 1
                
                        
            ret_val = " ".join(term_check)
            
            ret_val = self.token_or.sub(" || ", ret_val)
            ret_val = self.token_and.sub(" && ", ret_val)
            ret_val = self.token_word.sub(f"{field_label}:\g<word>", ret_val)
            counter2 = 1
            # take care of ^ to - before quotes go back
            ret_val = re.sub("\^\s*\(", "-(", ret_val)
            for n in token_list:
                ret_val = re.sub(f"QS{counter2}", n, ret_val)
                counter2 += 1
            
            ptn_token_not = f"{field_label}:(\^)"
            ptn_token_not2 = f"(\^){field_label}:"
            ret_val = re.sub(ptn_token_not, f"-{field_label}:", ret_val)
            ret_val = re.sub(ptn_token_not2, f"-{field_label}:", ret_val)
        
        # debug only    
        # print (str_input, ":", ret_val)
        return ret_val
    
# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    import sys
    print ("Running in Python %s" % sys.version_info[0])
    

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
    
