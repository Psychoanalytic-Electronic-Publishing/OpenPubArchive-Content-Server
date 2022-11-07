#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"

import re
import logging
import string
import opasGenSupportLib as opasgenlib

SUPPLEMENT_ISSUE_SEARCH_STR = "Supplement" # this is what will be searched in "art_iss" for supplements

# The following four functions moved from opasConfig - 2022-06-05
from pydantic import BaseModel, Field

def parse_volume_code(vol_code: str, source_code: str=None): 
    """
    PEP Volume numbers in IDS can be numbers or suffixed by an issue code--we use them after a volume number when a journal repeats pagination
    from issue to issue or starts the pagination over in a Supplement.
    
    >>> parse_volume_code("34S")
    ('34', 'S')
    >>> parse_volume_code("101C")
    ('101', 'C')
    >>> parse_volume_code("130")
    ('130', None)
    
    
    """
    ret_val = ("*", None)
    if vol_code is not None:
        m = re.match("\(*(?P<vol>[0-9]+)(?P<issuecode>[A-z]+)?\)*", vol_code)
        if m is not None:
            vol = m.group("vol")
            vol = vol.lstrip("0")
            issuecode = m.group("issuecode") 
            ret_val = vol, issuecode

    return ret_val    

def parse_issue_code(issue_code: str, source_code=None, vol=None): 
    """
    Issue codes are PEP unique--we use them after a volume number when a journal repeats pagination
    from issue to issue or starts the pagination over in a Supplement.
    
    Source code and volume can be used to handle sources that are "exceptions" to rules (unfortunately)
    
    """
    ret_val = "*"
    if issue_code is not None and issue_code.isalpha():
        issue_code = issue_code.upper()
        if issue_code[0] != "S" or (source_code == "FA" and vol == 1):
            ret_val = string.ascii_uppercase.index(issue_code[0]) # A==0, B==1
            ret_val += 1 # now A==1
            ret_val = str(ret_val)
        elif issue_code[0] == 'S':
            ret_val = SUPPLEMENT_ISSUE_SEARCH_STR # supplement
        else:
            ret_val = "*" # not recognized, allow any issue
            
    elif issue_code.isdecimal():
        if type(issue_code) == "int":
            ret_val = str(issue_code)
        else:
            ret_val = issue_code
    return ret_val    

class ArticleID(BaseModel):
    """
    This is a pydantic model for Opas Article IDs
    
    Article IDs (document IDs) are at the core of the system.  In PEP's design, article IDs are meaningful, and can be broken apart to learn about the content metadata.
      But when designed as such, the structure of the article IDs may be different in different systems, so it needs to be configurable as possible.
      This routine in opasConfig is a start of allowing that to be defined as part of the customization. 

    >>> a = ArticleID(articleID="AJRPP.004.0007A", allInfo=True)
    >>> print (a.articleInfo)
    {'source_code': 'AJRPP', 'vol_str': '004', 'vol_numeric': '004', 'vol_suffix': '', 'vol_wildcard': '', 'issue_nbr': '', 'page': '0007A', 'roman': '', 'page_numeric': '0007', 'page_suffix': 'A', 'page_wildcard': ''}

    >>> a = ArticleID(articleID="MPSA.043.0117A")
    >>> print (a.altStandard)
    MPSA.043?.0117A
    
    >>> a = ArticleID(articleID="AJRPP.004A.0007A")
    >>> print (a.volumeNbrStr)
    004
    >>> a = ArticleID(articleID="AJRPP.004S.R0007A")
    >>> print (a.issueCode)
    S
    >>> a = ArticleID(articleID="AJRPP.004S(1).R0007A")
    >>> print (a.issueInt)
    1
    >>> a.volumeInt
    4
    >>> a.romanPrefix
    'R'
    >>> a.isRoman
    True
    >>> print (a.articleID)
    AJRPP.004S.R0007A
    >>> a.isRoman
    True
    >>> a.pageInt
    7
    >>> a.standardized
    'AJRPP.004S.R0007A'
    >>> a = ArticleID(articleID="AJRPP.*.*")
    >>> a.standardized
    'AJRPP.*.*'
    >>> a = ArticleID(articleID="IJP.034.*")
    >>> a.standardized
    'IJP.034.*'
    >>> a = ArticleID(articleID="IJP.*.0001A")
    >>> a.standardized
    'IJP.*.*'
    
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        regex_article_id =  "(?P<source_code>[A-Z\-]{2,13})\.(?P<vol_str>(((?P<vol_numeric>[0-9]{3,4})(?P<vol_suffix>[A-Z]?))|(?P<vol_wildcard>\*)))(\((?P<issue_nbr>[0-9]{1,3})\))?\.(?P<page>((?P<roman>R?)(((?P<page_numeric>([0-9]{4,4}))(?P<page_suffix>[A-Z]?))|(?P<page_wildcard>\*))))"
        volumeWildcardOverride = ''
        m = re.match(regex_article_id, self.articleID, flags=re.IGNORECASE)
        if m is not None:
            self.articleInfo = m.groupdict("")
            self.sourceCode = self.articleInfo.get("source_code")
            # self.volumeStr = self.articleInfo.get("vol_str")
            
            # See if it has issue number numerically in ()
            self.issueInt = self.articleInfo.get("issue_nbr") # default for groupdict is ''
            if self.issueInt != '':
                self.issueInt = int(self.issueInt)
            else:
                self.issueInt = 0

            volumeSuffix = self.articleInfo.get("vol_suffix", "")
            altVolSuffix = ""
            if volumeSuffix != "":
                self.issueCode  = volumeSuffix[0]  # sometimes it says supplement!
            else:
                self.issueCode = ""
                if self.issueInt > 0:
                    altVolSuffix = string.ascii_uppercase[self.issueInt-1]
                
            if not self.isSupplement and self.issueInt == 0 and self.issueCode != "":
                # an issue code was specified (but not supplement or "S")
                converted = parse_issue_code(self.issueCode, source_code=self.sourceCode, vol=self.volumeInt)
                if converted.isdecimal():
                    self.issueCodeInt = int(converted)

            self.volumeInt = self.articleInfo.get("vol_numeric") 
            if self.volumeInt != '': # default for groupdict is ''
                self.volumeInt = int(self.volumeInt)
                # make sure str is at least 3 places via zero fill
                self.volumeNbrStr = format(self.volumeInt, '03')
                if self.issueCode != "":
                    self.volumeNbrStr += self.issueCode # covers journals with repeating pages
            else:
                self.volumeInt = 0

            volumeWildcardOverride = self.articleInfo.get("vol_wildcard")
            if volumeWildcardOverride != '':
                self.volumeNbrStr = volumeWildcardOverride
                
            self.isSupplement = self.issueCode == "S"
                    
            # page info
            # page = self.articleInfo.get("page")
            self.pageNbrStr = self.articleInfo.get("page_numeric")
            self.pageInt = self.pageNbrStr 
            if self.pageInt != '':
                self.pageInt = int(self.pageInt)
                self.pageNbrStr = format(self.pageInt, '04')
            else:
                self.pageInt = 0
                
            pageWildcard = self.articleInfo.get("page_wildcard")
            if pageWildcard != '':
                self.pageNbrStr = pageWildcard
            
            roman_prefix = self.articleInfo.get("roman", "")  
            self.isRoman = roman_prefix.upper() == "R"
            if self.isRoman:
                self.romanPrefix = roman_prefix 
               
            self.pageSuffix = self.articleInfo.get("page_suffix", "A")
            self.standardized = f"{self.sourceCode}.{self.volumeNbrStr}{self.issueCode}"
            self.altStandard = f"{self.sourceCode}.{self.volumeNbrStr}"
            if self.standardized == self.altStandard:
                # there's no issue code in the standard one. Try adding one:
                if altVolSuffix != "":
                    self.altStandard = f"{self.sourceCode}.{self.volumeNbrStr}{altVolSuffix}"
                else: # use 1 character wildcard
                    self.altStandard = f"{self.sourceCode}.{self.volumeNbrStr}?"
            
            if volumeWildcardOverride == '':
                if pageWildcard == '':
                    self.standardized += f".{self.romanPrefix}{self.pageNbrStr}{self.pageSuffix}"
                    self.altStandard += f".{self.romanPrefix}{self.pageNbrStr}{self.pageSuffix}"
                    #self.standardizedPlusIssueCode += f".{self.romanPrefix}{self.pageNbrStr}{self.pageSuffix}"
                else:
                    self.standardized += f".*"
                    self.altStandard += f".*"
                    #self.standardizedPlusIssueCode += f".*"
            else:
                self.standardized += f".*"
                self.altStandard += f".*"
                #self.standardizedPlusIssueCode += f".*"

            # always should be uppercase
            self.standardized = self.standardized.upper()
            self.isArticleID = True
            self.articleID = self.standardized
            if not self.allInfo:
                self.articleInfo = None
                # These show anyway so don't waste time with clear
                #if self.pageInt == 0:
                    #self.pageNbrStr = None
                #if self.volumeSuffix == '':
                    #self.volumeSuffix = None
                #if self.pageSuffix == '':
                    #self.pageSuffix = None
                #if self.volumeWildcardOverride == '':
                    #self.volumeWildcardOverride = None
                #if self.issueCode == '':
                    #self.issueCode = None
                #if self.page == "*":
                    #self.page = None
                #if self.pageWildcard == '':
                    #self.pageWildcard = None
        else:
            self.isArticleID = False   
    
    # pydantic field definitions for ArticleID       
    articleID: str = Field(None, title="As submitted ID, if it's a valid ID")
    standardized: str = Field(None, title="Standard form of article (document) ID")
    altStandard: str = Field(None, title="Standard form of article (document) ID from 2020 (most without volume suffix)")
    isArticleID: bool = Field(False, title="True if initialized value is an article (document) ID")
    sourceCode: str = Field(None, title="Source material assigned code (e.g., journal, book, or video source code)")
    # volumeStr: str = Field(None, title="")
    volumeSuffix: str = Field(None, title="")
    # volumeWildcardOverride: str = Field(None, title="")
    volumeInt: int = Field(0, title="")
    volumeNbrStr: str = Field(None, title="")
    issueCode: str = Field(None, title="")
    isSupplement: bool = Field(False, title="")
    issueInt: int = Field(0, title="")
    issueCodeInt: int = Field(0, title="") 
    # page info
    # page: str = Field(None, title="")
    pageNbrStr: str = Field(None, title="")
    pageInt: int = Field(0, title="")
    # pageWildcard: str = Field(None, title="")
    romanPrefix: str = Field("", title="")
    isRoman: bool = Field(False, title="")
    pageSuffix: str = Field(None, title="")    
    articleInfo: dict = Field(None, title="Regex result scanning input articleID")
    allInfo: bool = Field(False, title="Show all captured information, e.g. for diagnostics")
            

class JournalVolIssue(BaseModel):
    """
    #Identify and parse a "loose" spec if a journal code, volume or year, and issue.
    
    #>>> a = JournalVolIssue(journalSpec="AJRPP.004", allInfo=True)
    #>>> print (a.JournalVolIssue)
    
    #>>> a = JournalVolIssue(journalSpec="AJRPP 1972")
    #>>> print (f"\'{a.journalSpec}\'", a.sourceCode, a.yearStr)
    
    #>>> a = JournalVolIssue(journalSpec="ANIJP-DE 42")
    #>>> print (f"\'{a.journalSpec}\'", a.sourceCode, a.volumeNbrStr)

    #>>> a = JournalVolIssue(journalSpec="ANIJP-CHI 2021")
    #>>> print (f"\'{a.journalSpec}\'", a.sourceCode, a.yearStr)

    #>>> a = JournalVolIssue(journalSpec="IJP.*.0001A")
    #>>> print (f"\'{a.journalSpec}\'", a.standardized)
    #'IJP.*.*'
    
    """
  
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        JOURNAL_VOL_RX = "(?P<source_code>%s)(\s+|\.)?(?P<vol_numeric>[0-9]{1,4})?(?P<issue_letter>[A-z]?)(\s+|\.)?(?P<issue_nbr>[0-9]{1-2})?" % JOURNAL_CODES
        loose_journal_rxc = re.compile(JOURNAL_VOL_RX)        
        m = loose_journal_rxc.match(self.journalSpec)
        if m is not None:
            self.JournalVolIssue = m.groupdict("")
            self.sourceCode = self.JournalVolIssue.get("source_code")
            
            # See if it has issue number numerically in ()
            self.issueInt = self.JournalVolIssue.get("issue_nbr") # default for groupdict is ''
            if self.issueInt != '':
                self.issueInt = int(self.issueInt)
            else:
                self.issueInt = 0

            issue_letter = self.JournalVolIssue.get("vol_suffix", "")
            altVolSuffix = ""
            if issue_letter != "":
                self.issueCode  = issue_letter[0]  
            else:
                self.issueCode = ""
                if self.issueInt > 0:
                    altVolSuffix = string.ascii_uppercase[self.issueInt-1]
                
            if not self.isSupplement and self.issueInt == 0 and self.issueCode != "":
                # an issue code was specified (but not supplement or "S")
                converted = parse_issue_code(self.issueCode, source_code=self.sourceCode, vol=self.volumeInt)
                if converted.isdecimal():
                    self.issueCodeInt = int(converted)

            self.volumeInt = self.JournalVolIssue.get("vol_numeric") 
            if self.volumeInt != '': # default for groupdict is ''
                self.volumeInt = int(self.volumeInt)
                # make sure str is at least 3 places via zero fill
                self.volumeNbrStr = format(self.volumeInt, '03')
            else:
                self.volumeInt = 0

            if self.volumeInt > 1000:
                self.yearInt = self.volumeInt
                self.yearStr = format(self.volumeInt, '04')
                self.volumeInt = 0
                self.volumeNbrStr = ""

            self.isSupplement = self.issueCode == "S"
                
            self.standardized = f"{self.sourceCode}.{self.volumeNbrStr}{self.issueCode}"
            self.altStandard = f"{self.sourceCode}.{self.volumeNbrStr}"
            if self.standardized == self.altStandard:
                # there's no issue code in the standard one. Try adding one:
                if altVolSuffix != "":
                    self.altStandard = f"{self.sourceCode}.{self.volumeNbrStr}{altVolSuffix}"
                else: # use 1 character wildcard
                    self.altStandard = f"{self.sourceCode}.{self.volumeNbrStr}?"
            
            # always should be uppercase
            self.standardized = self.standardized.upper()
            self.isJournalSpec = True
            self.journalSpec = self.standardized
            if not self.allInfo:
                self.JournalVolIssue = None
        else:
            self.isArticleID = False

    journalSpec: str = Field(None, title="As submitted")
    JournalVolIssue: dict = Field(None, title="Regex result scanning input JournalSpec")
    solrQuerySpec: dict = Field(None, title="Solr Query spec")
    standardized: str = Field(None, title="Standard form of article (document) ID")
    altStandard: str = Field(None, title="Standard form of article (document) ID from 2020 (most without volume suffix)")
    isArticleID: bool = Field(False, title="True if initialized value is an article (document) ID")
    sourceCode: str = Field(None, title="Source material assigned code (e.g., journal, book, or video source code)")
    # volumeStr: str = Field(None, title="")
    volumeSuffix: str = Field(None, title="")
    # volumeWildcardOverride: str = Field(None, title="")
    volumeInt: int = Field(0, title="")
    volumeNbrStr: str = Field(None, title="")
    yearInt: int = Field(0, title="")
    yearStr: str = Field(None, title="")
    issueCode: str = Field(None, title="")
    isJournalSpec: bool = Field(False, title="True if it correctly specifies a journal")
    isSupplement: bool = Field(False, title="")
    issueInt: int = Field(0, title="")
    issueCodeInt: int = Field(0, title="") 
    allInfo: bool = Field(False, title="Show all captured information, e.g. for diagnostics")
        

if __name__ == "__main__":
    sys.path.append('./config') 

    print (40*"*", "ArticleID module test", 40*"*")
    print ("Running in Python %s" % sys.version_info[0])
    logger = logging.getLogger(__name__)
    # extra logging for standalong mode 
    logger.setLevel(logging.WARN)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARN)
    # create formatter
    formatter = logging.Formatter('%(asctime)s %(name)s %(lineno)d - %(levelname)s %(message)s')    
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)

    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
    print ("All tests complete!")
    print ("Fini")
