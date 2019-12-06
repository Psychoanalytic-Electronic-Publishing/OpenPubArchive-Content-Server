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

class QueryTextToSolr():
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
        
    def markup(self, str_input, label_word):
        def quotedrepl(matchobj):
            self.counter += 1
            return f'QS{self.counter}'
        
        self.counter = 0
        token_list = self.token_quoted.findall(str_input)
        ret_val = self.token_quoted.sub(quotedrepl, str_input)
        ret_val = self.token_or.sub(" || ", ret_val)
        ret_val = self.token_and.sub(" && ", ret_val)
        ret_val = self.token_word.sub(f"{label_word}:\g<word>", ret_val)
        counter2 = 1
        # take care of ^ to - before quotes go back
        ret_val = re.sub("\^\s*\(", "-(", ret_val)
        for n in token_list:
            ret_val = re.sub(f"QS{counter2}", n, ret_val)
            counter2 += 1
        
        ptn_token_not = f"{label_word}:(\^)"
        ptn_token_not2 = f"(\^){label_word}:"
        ret_val = re.sub(ptn_token_not, f"-{label_word}:", ret_val)
        ret_val = re.sub(ptn_token_not2, f"-{label_word}:", ret_val)
        
        # debug only    
        # print (str_input, ":", ret_val)
        return ret_val
    
# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    import sys
    print ("Running in Python %s" % sys.version_info[0])
    

    tests = ["dog or 'fred flints*' and 'barney rubble'",
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
    
