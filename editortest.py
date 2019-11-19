#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

MATCH_STR =  "#!#"
MATCH_STR_START = "##!" 
MATCH_STR_END = "!##" 
count_anchors = 0

def numbered_anchor(matchobj):
    global count_anchors
    if matchobj.group(0) == MATCH_STR:
        count_anchors += 1 
        return f"<a name='hit{count_anchors}'>{matchobj.group(0)}"
    else:
        return matchobj.group(0)

def numbered_anchors(matchobj):
    """
    Called by re.sub on replacing anchor placeholders for HTML output.  This allows them to be numbered as they are replaced.
    """
    global count_anchors
    if matchobj.group(0) == MATCH_STR_START:
        count_anchors += 1
        if count_anchors > 1:
            return f"<a name='hit{count_anchors}'><a href='#hit{count_anchors-1}'>🡄</a> "
        elif count_anchors <= 1:
            return f"<a name='hit{count_anchors}'> "
    if matchobj.group(0) == MATCH_STR_END:
        return f" <a href='#hit{count_anchors+1}'>🡆</a>"
            
    else:
        return matchobj.group(0)



    
if __name__ == "__main__":
    import sys
    print ("Running in Python %s" % sys.version_info[0])

    testStr = """Test 3. By default, the application's ##!words!## is only ##!words!## open ##!words!## to (in other ##!words!## ,"""
    testStr = re.sub(f"{MATCH_STR_START}|{MATCH_STR_END}", numbered_anchors, testStr)
    print (testStr)



    testStr = re.sub(MATCH_STR, numbered_anchor, testStr)
    print (testStr)
    count_anchors = 0
    testStr = """Test 2. By default, the application's #!# is only open to #!# internal #!# traffic (in other words, #!# such """
    testStr = re.sub(MATCH_STR, numbered_anchor, testStr)
    print (testStr)
    
    print ("...done...")
