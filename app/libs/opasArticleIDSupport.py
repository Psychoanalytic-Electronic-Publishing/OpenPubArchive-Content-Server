#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"

import re
import logging
import string
import opasGenSupportLib as opasgenlib
import time
from typing import List, Generic, TypeVar, Optional
from datetime import datetime
import opasXMLHelper as opasxmllib
import opasLocator
import html
import json
from lxml import etree
import opasConfig
from configLib.opasIJPConfig import IJPOPENISSUES

SUPPLEMENT_ISSUE_SEARCH_STR = "Supplement" # this is what will be searched in "art_iss" for supplements

# The following four functions moved from opasConfig - 2022-06-05
from pydantic import BaseModel, Field

import opasProductLib
sourceDB = opasProductLib.SourceInfoDB()

def parse_glossary_terms_dict(glossary_terms_dict_str, verbose=False):
    #if not glossary_terms_dict_str:
        #glossary_terms_count, glossary_terms_dict = glossEngine.getGlossaryLists(parsed_xml, 
                                                                                 #verbose=verbose)
        ## need to compute it
        #term_json = json.dumps(glossary_terms_dict)
        #pep_addon = f'<unit type="glossary_term_dict"><!-- {term_json} --></unit>'
    #else:
        #print ("\t...Glossary terms list loaded from database")
        #pep_addon = glossary_terms_dict_str
    
    #glossary_terms_dict_str = pep_addon
    
    m = re.search("<!--.*?(?P<dict_str>\{.*\}).*?-->", glossary_terms_dict_str)
    dict_str = m.group("dict_str")
    glossary_terms_dict = json.loads(dict_str)
    
    ret_val = glossary_terms_dict
    
    #new_unit = ET.fromstring(pep_addon, parser)
    #parsed_xml.append(new_unit)
    
    return ret_val
   
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
               
            self.pageSuffix = self.articleInfo.get("page_suffix", "")
            
            if not self.volumeNbrStr[-1].isalpha() and self.issueCode != "":
                self.standardized = f"{self.sourceCode}.{self.volumeNbrStr}{self.issueCode}"
            else:
                self.standardized = f"{self.sourceCode}.{self.volumeNbrStr}"
                
            self.altStandard = f"{self.sourceCode}.{self.volumeNbrStr}"
            if self.standardized == self.altStandard:
                # there's no alpha issue code in the standard one. Try adding one:
                if altVolSuffix != "" and not self.volumeNbrStr[-1].isalpha():
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
    standardized: str = Field(None, title="Standard form of article (document) ID, volume suffix included if volume includes repeat page #s or for supplements")
    altStandard: str = Field(None, title="Alternate form of article (document) ID from 2020 (most without volume suffix)")
    isArticleID: bool = Field(False, title="True if initialized value is an article (document) ID")
    sourceCode: str = Field(None, title="Source material assigned code (e.g., journal, book, or video source code)")
    # volumeStr: str = Field(None, title="")
    volumeSuffix: str = Field(None, title="")
    # volumeWildcardOverride: str = Field(None, title="")
    volumeInt: int = Field(0, title="")
    volumeNbrStr: str = Field(None, title="Volume number padded to 3 digits and issuecode if repeating pages or supplement")
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
            
#------------------------------------------------------------------------------------------------------
class ArticleInfo(BaseModel):
    """
    An entry from a documents metadata.
    
    Used to populate the MySQL table api_articles for relational type querying
       and the Solr core pepwebdocs for full-text searching (and the majority of
       client searches.

    """
    def __init__(self, art_id, parsed_xml, logger=None, filename_base="", fullfilename=None, verbose=None, **kwargs):
        super().__init__(**kwargs)

        # def __init__(self, parsed_xml, art_id, logger, filename_base, fullfilename=None, verbose=None):
        # let's just double check artid!
        self.art_id = None
        self.art_id_from_filename = art_id # file name will always already be uppercase (from caller)
        self.bk_subdoc = None
        self.bk_seriestoc = None
        self.verbose = verbose
        self.src_code_active = 0
        self.src_is_book = False
        
        # Just init these.  Creator will set based on filename
        self.file_classification = None
        self.file_size = 0  
        self.filedatetime = ""
        self.filename = filename_base # filename without path
        self.fullfilename = fullfilename
        # compute various artinfo parts from filename
        self.filename_artinfo = ArticleID(articleID=filename_base) # use base filename for implied artinfo

        # now, the rest of the variables we can set from the data
        self.processed_datetime = datetime.utcfromtimestamp(time.time()).strftime(opasConfig.TIME_FORMAT_STR)
        try:
            art_id = opasxmllib.xml_xpath_return_textsingleton(parsed_xml, "//artinfo/@id", None)
            self.art_id = art_id
            if self.art_id is None:
                self.art_id = self.art_id_from_filename
            else:
                # just to watch for xml keying or naming errors
                if self.art_id_from_filename != self.art_id:
                    logger.warning("File name ID tagged and artID disagree.  %s vs %s", self.art_id, self.art_id_from_filename)
                    self.art_id = self.art_id_from_filename
                    
            # make sure it's uppercase
            self.art_id = self.art_id.upper()
                
        except Exception as err:
            logger.error("Issue reading file's article id. (%s)", err)
            self.art_id = self.filename_artinfo.articleID

        # Containing Article data
        #<!-- Common fields -->
        #<!-- Article front matter fields -->
        #---------------------------------------------
        artinfo_xml = parsed_xml.xpath("//artinfo")[0] # grab full artinfo node, so it can be returned in XML easily.
        self.artinfo_meta_xml = parsed_xml.xpath("//artinfo/meta")
        self.artinfo_xml = etree.tostring(artinfo_xml).decode("utf8")
        self.src_code = parsed_xml.xpath("//artinfo/@j")[0]
        self.src_code = self.src_code.upper()  # 20191115 - To make sure this is always uppercase
        self.embargoed = parsed_xml.xpath("//artinfo/@embargo")
        self.embargotype = opasxmllib.xml_xpath_return_textsingleton(parsed_xml, "//artinfo/@embargotype", default_return=None)
        if self.embargotype is not None:
            self.embargotype = self.embargotype.upper()
            if opasConfig.TEMP_IJPOPEN_VER_COMPAT_FIX:
                if self.embargotype == "IJPOPEN_FULLY_REMOVED":
                    self.embargotype = "IJPOPEN_REMOVED" 

        # Added for IJPOpen but could apply elsewhere        
        self.metadata_dict = {}
        root = parsed_xml.getroottree()
        adldata_list = root.findall('meta/adldata')
        for adldata in adldata_list:
            fieldname = adldata[0].text
            fieldvalue = adldata[1].text
            self.metadata_dict[fieldname] = fieldvalue 
        
        # Currently, 2022/12, these are only used by IJPOpen
        self.publisher_ms_id = self.metadata_dict.get("manuscript-id", "")
        self.manuscript_date_str = self.metadata_dict.get("submission-date", "")
        
        if 1: # vol info (just if'd for folding purposes)
            vol_actual = opasxmllib.xml_xpath_return_textsingleton(parsed_xml, '//artinfo/artvol/@actual', default_return=None)
            self.art_vol_str = opasxmllib.xml_xpath_return_textsingleton(parsed_xml, '//artinfo/artvol/node()', default_return=None)
            if opasgenlib.not_empty(self.filename_artinfo.issueCode):
                # use filename markup
                self.art_vol_int = self.filename_artinfo.volumeInt
                self.art_vol_str = self.filename_artinfo.volumeNbrStr
                self.art_vol_suffix = self.filename_artinfo.issueCode
            else:
                m = re.match("(\d+)([A-Z]*)", self.art_vol_str)
                if m is None:
                    logger.error(f"ArticleInfoError: Bad Vol # in element content: {self.art_vol_str}")
                    m = re.match("(\d+)([A-z\-\s]*)", vol_actual)
                    if m is not None:
                        self.art_vol_int = m.group(1)
                        logger.error(f"ArticleInfoError: Recovered Vol # from actual attr: {self.art_vol_int}")
                    else:
                        raise ValueError("ArticleInfoError: Severe Error in art_vol")
                else:
                    self.art_vol_int = m.group(1)
                    if len(m.groups()) == 2:
                        self.art_vol_suffix = m.group(2)
    
                # now convert to int
                try:
                    self.art_vol_int = int(self.art_vol_int)
                except ValueError:
                    logger.warning(f"Can't convert art_vol to int: {self.art_vol_int} Error: {e}")
                    self.art_vol_suffix = self.art_vol_int[-1]
                    art_vol_ints = re.findall(r'\d+', self.art_vol_str)
                    if len(art_vol_ints) >= 1:
                        self.art_vol_int = art_vol_ints[1]
                        self.art_vol_int = int(self.art_vol_int)
                except Exception as e:
                    logger.warning(f"Can't convert art_vol to int: {self.art_vol_int} Error: {e}")
                     
        try: #  lookup source in db
            if self.src_code in ["ZBK", "IPL", "NLP"]:
                self.src_prodkey = pepsrccode = f"{self.src_code}%03d" % self.art_vol_int
                self.src_type = "book"
                self.src_is_book = True
            else:
                self.src_prodkey = pepsrccode = f"{self.src_code}"
                self.src_is_book = False

            self.src_title_abbr = sourceDB.sourceData[pepsrccode].get("sourcetitleabbr", None)
            self.src_title_full = sourceDB.sourceData[pepsrccode].get("sourcetitlefull", None)
            self.src_code_active = sourceDB.sourceData[pepsrccode].get("active", 0)
                
            # remove '*New*'  prefix if it's there
            if self.src_title_full is not None:
                self.src_title_full = self.src_title_full.replace(opasConfig.JOURNALNEWFLAG, "")
            
            self.src_embargo_in_years = sourceDB.sourceData[pepsrccode].get("wall", None)
            product_type = sourceDB.sourceData[pepsrccode].get("product_type", None)  # journal, book, video...
                
            if self.src_code in ["GW", "SE"]:
                self.src_type = "book"
            else:
                if type(product_type) == set:
                    try:
                        self.src_type = next(iter(product_type))
                    except Exception as e:
                        self.src_type = "exception"
                else:
                    self.src_type = product_type
                
        except KeyError as err:
            self.src_title_abbr = None
            self.src_title_full = None
            self.src_type = "book"
            self.src_embargo_in_years = None
            logger.warning("ArticleInfoError: Source %s not found in source info db.  Assumed to be an offsite book.  Or you can add to the api_productbase table in the RDS/MySQL DB", self.src_code)
        except Exception as err:
            logger.error("ArticleInfoError: Problem with this files source info. File skipped. (%s)", err)
            #processingErrorCount += 1
            return
            
        self.art_issue = opasxmllib.xml_xpath_return_textsingleton(parsed_xml, '//artinfo/artiss/node()', default_return=None)
        self.art_issue_title = opasxmllib.xml_xpath_return_textsingleton(parsed_xml, '//artinfo/artissinfo/isstitle/node()', default_return=None)
        if self.art_issue_title is None:
            try:
                self.art_issue_title = parsed_xml.xpath("//artinfo/@issuetitle")[0]
            except:
                pass
        if self.art_issue is None:
            if self.src_code in ["IJPOPEN"] and self.art_issue_title is not None:
                issue_num = IJPOPENISSUES.get(self.art_issue_title)
                self.art_issue = issue_num
                
        # special sequential numbering for issues used by journals like fa (we code it simply as artnbr in xml)
        self.art_issue_seqnbr = opasxmllib.xml_xpath_return_textsingleton(parsed_xml, '//artinfo/artnbr/node()', default_return=None)
        
        self.art_year_str = opasxmllib.xml_xpath_return_textsingleton(parsed_xml, '//artinfo/artyear/node()', default_return=None)
        m = re.match("(?P<yearint>[0-9]{4,4})(?P<yearsuffix>[a-zA-Z])?(\s*\-\s*)?((?P<year2int>[0-9]{4,4})(?P<year2suffix>[a-zA-Z])?)?", self.art_year_str)
        if m is not None:
            self.art_year_suffix = m.group("yearsuffix")
            self.art_year_str = m.group("yearint")
            self.art_year2_str = m.group("year2int")
            self.art_year2_suffix = m.group("year2suffix")
            self.art_year_int = int(m.group("yearint"))
        else:
            try:
                art_year_for_int = re.sub("[^0-9]", "", self.art_year_str)
                self.art_year_int = int(art_year_for_int)
            except ValueError as err:
                logger.error("Error converting art_year to int: %s", self.art_year_str)
                self.art_year_int = 0


        artInfoNode = parsed_xml.xpath('//artinfo')[0]
        self.art_type = opasxmllib.xml_get_element_attr(artInfoNode, "arttype", default_return=None)
        if self.art_type is not None and self.art_type.upper() == "TOC":
            self.art_is_maintoc = True
        else:
            self.art_is_maintoc = False
            
        self.art_vol_title = opasxmllib.xml_xpath_return_textsingleton(parsed_xml, '//artinfo/artvolinfo/voltitle/node()', default_return=None)
        if self.art_vol_title is None:
            # try attribute for value (lower priority than element above)
            self.art_vol_title = opasxmllib.xml_get_element_attr(artInfoNode, "voltitle", default_return=None)

        # m = re.match("(?P<volint>[0-9]+)(?P<volsuffix>[a-zA-Z])", self.art_vol)
        m = re.match("(?P<volint>[0-9]+)(?P<volsuffix>[a-zA-Z])?(\s*\-\s*)?((?P<vol2int>[0-9]+)(?P<vol2suffix>[a-zA-Z])?)?", str(self.art_vol_str))
        if m is not None:
            self.art_vol_suffix = m.group("volsuffix")
            # self.art_vol = m.group("volint")
        else:
            self.art_vol_suffix = None
            
        if self.verbose and self.art_vol_title is not None:
            print (f"\t...Volume title: {self.art_vol_title}")
    
        if self.verbose and self.art_issue_title is not None:
            print (f"\t...Issue title: {self.art_issue_title}")
            
        art_doi = self.art_doi = opasxmllib.xml_get_element_attr(artInfoNode, "doi", default_return=None) 
        self.art_issn = opasxmllib.xml_get_element_attr(artInfoNode, "ISSN", default_return=None) 
        self.art_isbn = opasxmllib.xml_get_element_attr(artInfoNode, "ISBN", default_return=None) 
        self.art_orig_rx = opasxmllib.xml_get_element_attr(artInfoNode, "origrx", default_return=None) 
        self.start_sectlevel = opasxmllib.xml_get_element_attr(artInfoNode, "newseclevel", default_return=None)
        self.start_sectname = opasxmllib.xml_get_element_attr(artInfoNode, "newsecnm", default_return=None)
        if self.start_sectname is None:
            #  look in newer, tagged, data
            self.start_sectname = opasxmllib.xml_xpath_return_textsingleton(parsed_xml, '//artinfo/artsectinfo/secttitle/node()', default_return=None)
        
        if self.start_sectname is not None:
            self.start_sectname = opasgenlib.trimPunctAndSpaces(self.start_sectname)
        
        self.art_pgrg = opasxmllib.xml_get_subelement_textsingleton(artInfoNode, "artpgrg", default_return=None)  # note: getSingleSubnodeText(pepxml, "artpgrg")
        self.art_pgstart, self.art_pgend = opasgenlib.pgrg_splitter(self.art_pgrg)

        try:
            self.art_pgcount = int(parsed_xml.xpath("count(//pb)")) # 20200506
        except Exception as e:
            self.art_pgcount = 0
            
        self.art_kwds = opasxmllib.xml_xpath_return_textsingleton(parsed_xml, "//artinfo/artkwds/node()", None)
        
        # art_pgrx_count
        try:
            self.art_pgrx_count = int(parsed_xml.xpath("count(//pgx)")) # 20220320
        except Exception as e:
            self.art_pgrx_count = 0


        # ************* new counts! 20210413 *******************************************
        try:
            if self.art_kwds is not None:
                self.art_kwds_count = self.art_kwds.count(",") + 1 # 20210413
            else:
                self.art_kwds_count = 0
        except Exception as e:
            self.art_kwds_count = 0

        # art_abs_count
        try:
            self.art_abs_count = int(parsed_xml.xpath("count(//abs)"))
        except Exception as e:
            self.art_abs_count  = 0

        # art_ftns_count_count 
        try:
            self.art_ftns_count = int(parsed_xml.xpath("count(//ftn)")) # 20210413
        except Exception as e:
            self.art_ftns_count = 0

        # art_paras_count
        try:
            self.art_paras_count = int(parsed_xml.xpath("count(//p)")) # 20210413
        except Exception as e:
            self.art_paras_count = 0

        # art_headings_count
        try:
            self.art_headings_count = int(parsed_xml.xpath("count(//*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6])")) # 20210413
        except Exception as e:
            self.art_headings_count = 0

        # art_terms_count
        try:
            self.art_terms_count = int(parsed_xml.xpath('count(//impx[@type="TERM2"])')) # 20210413
        except Exception as e:
            self.art_terms_count = 0

        # art_dreams_count
        try:
            self.art_dreams_count = int(parsed_xml.xpath("count(//dream)")) # 20210413
        except Exception as e:
            self.art_dreams_count = 0

        # art_dialogs_count
        try:
            self.art_dialogs_count = int(parsed_xml.xpath("count(//dialog)")) # 20210413
        except Exception as e:
            self.art_dialogs_count = 0

        # art_notes_count
        try:
            self.art_notes_count = int(parsed_xml.xpath("count(//note)")) # 20210413
        except Exception as e:
            self.art_notes_count = 0

        # art_poems_count
        try:
            self.art_poems_count = int(parsed_xml.xpath("count(//poem)")) # 20210413
        except Exception as e:
            self.art_poems_count = 0
            
        # art_citations_count
        try:
            self.art_citations_count = int(parsed_xml.xpath("count(//bx)")) # 20210413
        except Exception as e:
            self.art_citations_count = 0
        
        # art_quotes_count
        try:
            self.art_quotes_count = int(parsed_xml.xpath("count(//quote)")) # 20210413
        except Exception as e:
            self.art_quotes_count = 0

        try:
            self.art_tblcount = int(parsed_xml.xpath("count(//tbl)")) # 20200922
        except Exception as e:
            self.art_tblcount = 0

        try:
            self.art_figcount = int(parsed_xml.xpath("count(//figure)")) # 20200922
        except Exception as e:
            self.art_figcount = 0
            
        # art_chars_count
        try:
            self.art_chars_count = int(parsed_xml.xpath("string-length(normalize-space(//node()))"))
            self.art_chars_meta_count = int(parsed_xml.xpath("string-length(normalize-space(//meta))"))
            self.art_chars_count -= self.art_chars_meta_count 
        except Exception as e:
            self.art_chars_count  = 0

        try:
            self.art_chars_no_spaces_count = int(parsed_xml.xpath("string-length(translate(normalize-space(//node()),' ',''))"))
            self.art_chars_no_spaces_meta_count = int(parsed_xml.xpath("string-length(translate(normalize-space(//meta),' ',''))"))
            self.art_chars_no_spaces_count -= self.art_chars_no_spaces_meta_count
        except Exception as e:
            self.art_chars_no_spaces_count  = 0

        try:
            self.art_words_count = self.art_chars_count - self.art_chars_no_spaces_count + 1
        except Exception as e:
            self.art_words_count  = 0

        # ************* end of counts! 20210413 *******************************************

        self.art_graphic_list = parsed_xml.xpath('//graphic//@source')
        #if self.art_graphic_list != []:
            #print (f"Graphics found: {self.art_graphic_list}")
        
        if self.art_pgstart is not None:
            self.art_pgstart_prefix, self.art_pgstart, self.pgstart_suffix = opasgenlib.pgnum_splitter(self.art_pgstart)
        else:
            self.art_pgstart_prefix, self.art_pgstart, self.pgstart_suffix = (None, None, None)
            
        if self.art_pgend is not None:
            self.pgend_prefix, self.art_pgend, self.pgend_suffix = opasgenlib.pgnum_splitter(self.art_pgend)
        else:
            self.pgend_prefix, self.art_pgend, self.pgend_suffix = (None, None, None)

        self.art_title = opasxmllib.xml_get_subelement_textsingleton(artInfoNode, "arttitle", skip_tags=["ftnx"])
        if self.art_title == "-": # weird title in ANIJP-CHI
            self.art_title = ""

        self.art_subtitle = opasxmllib.xml_get_subelement_textsingleton(artInfoNode, 'artsub')
        if self.art_subtitle == "":
            pass
        elif self.art_subtitle is None:
            self.art_subtitle = ""
        else:
            #self.artSubtitle = ''.join(etree.fromstring(self.artSubtitle).itertext())
            if self.art_title != "":
                self.art_subtitle = ": " + self.art_subtitle
                self.art_title = self.art_title + self.art_subtitle
            else:
                self.art_title = self.art_subtitle
                self.art_subtitle = ""
                
        self.art_lang = parsed_xml.xpath('//pepkbd3/@lang')
        
        if self.art_lang == []:
            self.art_lang = [opasConfig.DEFAULT_DATA_LANGUAGE_ENCODING]

        try:
            self.art_lang = self.art_lang[0].lower()
        except:
            logger.warning(f"art_lang value error: {self.art_lang}")
            self.art_lang = opasConfig.DEFAULT_DATA_LANGUAGE_ENCODING
        
        self.author_xml_list = parsed_xml.xpath('//artinfo/artauth/aut')
        self.author_xml = opasxmllib.xml_xpath_return_xmlsingleton(parsed_xml, '//artinfo/artauth')
        self.authors_bibliographic, self.author_list, self.authors_bibliographic_list = opasxmllib.authors_citation_from_xmlstr(self.author_xml, listed="All") #listed=True)
        self.art_auth_citation = self.authors_bibliographic
        self.art_auth_citation_list = self.authors_bibliographic_list
        # ToDo: I think I should add an author ID to bib aut too.  But that will have
        #  to wait until later.
        # TODO: fix PEP2XML--in cases like AJRPP.004.0273A it put Anonymous in the authindexid.
        self.art_author_id_list = opasxmllib.xml_xpath_return_textlist(parsed_xml, '//artinfo/artauth/aut[@listed="true"]/@authindexid')
        self.art_authors_count = len(self.author_list)
        if self.art_author_id_list == []: # no authindexid
            logger.warning("This document %s does not have an author list; may be missing authindexids" % art_id)
            self.art_author_id_list = self.author_list

        self.art_author_ids_str = ", ".join(self.art_author_id_list)
        self.art_auth_mast, self.art_auth_mast_list = opasxmllib.author_mast_from_xmlstr(self.author_xml, listed=True)
        self.art_auth_mast_unlisted_str, self.art_auth_mast_unlisted_list = opasxmllib.author_mast_from_xmlstr(self.author_xml, listed=False)
        # self.art_auth_count = len(self.author_xml_list)
        # self.art_author_lastnames = opasxmllib.xml_xpath_return_textlist(parsed_xml, '//artinfo/artauth/aut[@listed="true"]/nlast')
        
        # self.art_all_authors = self.art_auth_mast + " (" + self.art_auth_mast_unlisted_str + ")"

        self.issue_id_str = f"<issue_id><src>{self.src_code}</src><yr>{self.art_year_str}</yr><vol>{self.art_vol_str}</vol><iss>{self.art_issue}</iss></issue_id>"
        try:
            if self.src_title_full is not None:
                safe_src_title_full = html.escape(self.src_title_full)
            else:
                logger.warning(f"Source title full is None")
                safe_src_title_full = ''

        except Exception as e:
            logger.error(f"ArticleInfoError: Source title escape error: {e}")
            safe_src_title_full = ''
            
        try:
            if self.art_title is not None:
                safe_art_title = html.escape(self.art_title)
            else:
                logger.warning(f"Art title is None")
                safe_art_title = ''

        except Exception as e:
            logger.error(f"ArticleInfoError: Art title escape error: {e}")
            safe_art_title = ''

        try:
            if self.art_pgrg is not None:
                safe_art_pgrg = html.escape(self.art_pgrg)
            else:
                logger.warning(f"Art title is None")
                safe_art_pgrg = ''

        except Exception as e:
            logger.error(f"ArticleInfoError: Art PgRg escape error: {e}")
            safe_art_pgrg = ''
            
        # Usually we put the abbreviated title here, but that won't always work here.
        self.art_citeas_xml = u"""<p class="citeas"><span class="authors">%s</span> (<span class="year">%s</span>) <span class="title">%s</span>. <span class="sourcetitle">%s</span> <span class="vol">%s</span>:<span class="pgrg">%s</span></p>""" \
            %                   (self.authors_bibliographic,
                                 self.art_year_str,
                                 safe_art_title,
                                 safe_src_title_full,
                                 self.art_vol_int,
                                 safe_art_pgrg
                                )
        
        self.art_citeas_text = opasxmllib.xml_elem_or_str_to_text(self.art_citeas_xml)
        art_qual_node = parsed_xml.xpath("//artinfo/artqual")
        if art_qual_node != []:
            self.art_qual = opasxmllib.xml_get_element_attr(art_qual_node[0], "rx", default_return=None)
        else:
            self.art_qual = parsed_xml.xpath("//artbkinfo/@extract")
            if self.art_qual == []:
                self.art_qual = None
            else:
                self.art_qual = str(self.art_qual[0])
                #try:
                    #self.art_qual = str(opasLocator.Locator(self.art_qual))
                #except Exception as e:
                    #print (e)

        #self.artinfo_bkinfo_next = parsed_xml.xpath("//artbkinfo/@next")
        #self.artinfo_bkinfo_prev = parsed_xml.xpath("//artbkinfo/@prev")
        #if self.artinfo_bkinfo_next != []:
            #self.artinfo_bkinfo_next = str(opasLocator.Locator(self.artinfo_bkinfo_next[0]))
        #if self.artinfo_bkinfo_prev != []:
            #self.artinfo_bkinfo_prev = str(opasLocator.Locator(self.artinfo_bkinfo_prev[0]))
            
        # will be None if not a book extract
        # self.art_qual = None
        if self.art_qual is not None:
            if isinstance(self.art_qual, list):
                self.art_qual = str(self.art_qual[0])
                
            if self.art_qual != self.art_id:
                self.bk_subdoc = True
            else:
                self.bk_subdoc = False
        else:
            self.bk_subdoc = False           

        refs = parsed_xml.xpath("/pepkbd3//be")
        self.bib_authors = []
        self.bib_rx = []
        self.bib_title = []
        self.bib_journaltitle = []
        
        for x in refs:
            try:
                if x.attrib["rx"] is not None:
                    self.bib_rx.append(x.attrib["rx"])
            except:
                pass
            journal = x.find("j")
            if journal is not None:
                journal_lc = opasxmllib.xml_elem_or_str_to_text(journal).lower()
                journal_lc = journal_lc.translate(str.maketrans('', '', string.punctuation))
                self.bib_journaltitle.append(journal_lc)

            title = x.find("t")
            # bib article titles for faceting, get rid of punctuation variations
            if title is not None:
                bib_title = opasxmllib.xml_elem_or_str_to_text(title)
                bib_title = bib_title.lower()
                bib_title = bib_title.translate(str.maketrans('', '', string.punctuation))
                self.bib_title.append(opasxmllib.xml_elem_or_str_to_text(title))

            title = x.find("bst")
            # bib source titles for faceting, get rid of punctuation variations
            # cumulate these together with article title
            if title is not None:
                bib_title = opasxmllib.xml_elem_or_str_to_text(title)
                bib_title = bib_title.lower()
                bib_title = bib_title.translate(str.maketrans('', '', string.punctuation))
                self.bib_title.append(bib_title)

            auths = x.findall("a")
            for y in auths:
                if opasxmllib.xml_elem_or_str_to_text(x) is not None:
                    self.bib_authors.append(opasxmllib.xml_elem_or_str_to_text(y))
        
        self.ref_count = len(refs )
        # clear it, we aren't saving it.
        refs  = None
        
        self.bk_info_xml = opasxmllib.xml_xpath_return_xmlsingleton(parsed_xml, "/pepkbd3//artbkinfo") # all book info in instance
        # break it down a bit for the database
        self.main_toc_id = opasxmllib.xml_xpath_return_textsingleton(parsed_xml, "/pepkbd3//artbkinfo/@extract", None)
        if self.main_toc_id is not None:
            self.main_toc_id = str(self.main_toc_id)
            #self.main_toc_id = str(opasLocator.Locator(self.main_toc_id))
            
        self.bk_title = opasxmllib.xml_xpath_return_textsingleton(parsed_xml, "/pepkbd3//bktitle", None)
        self.bk_publisher = opasxmllib.xml_xpath_return_textsingleton(parsed_xml, "/pepkbd3//bkpubandloc", None)
        self.bk_seriestoc = opasxmllib.xml_xpath_return_textsingleton(parsed_xml, "/pepkbd3//artbkinfo/@seriestoc", None)
        self.bk_next_id = opasxmllib.xml_xpath_return_textsingleton(parsed_xml, "//artbkinfo/@next", None)
        #if self.bk_next_id is not None:
            #self.bk_next_id = opasLocator.Locator(self.bk_next_id)
        
        # self.bk_pubyear = opasxmllib.xml_xpath_return_textsingleton(pepxml, "/pepkbd3//artbkinfo/bkpubyear", default_return=self.art_year_str)
        # hard code special cases SE/GW if they are not covered by the instances
        if self.bk_seriestoc is None:
            if self.src_code == "SE":
                self.bk_seriestoc = "SE.000.0000A"
            if self.src_code == "GW":
                self.bk_seriestoc = "GW.000.0000A"               

        # if article xml has glossary_terms, set glossary_terms fields
        glossary_terms_dict_addon = parsed_xml.xpath("//unit[@type='glossary_term_dict']")
        if glossary_terms_dict_addon:
            glossary_terms_dict_addon = glossary_terms_dict_addon[0]
            if glossary_terms_dict_addon is not None:
                self.glossary_terms_dict_str = etree.tostring(glossary_terms_dict_addon).decode("utf8")
                self.glossary_terms_dict = parse_glossary_terms_dict(self.glossary_terms_dict_str)
                # self.glossary_terms_count = len(self.glossary_terms_dict)
        else:
            self.glossary_terms_dict_str = None       
            self.glossary_terms_dict = {}
            # self.glossary_terms_count = 0

        # check art_id's against the standard, old system of locators.
        try:
            art_locator = opasLocator.Locator(self.art_id)                                                  
            if self.art_id != art_locator.articleID():
                logger.warning(f"art_id: {self.art_id} is not the same as the computed locator: {art_locator} ")
                
            # Take advantage of Locator object for conversion data required.
            self.is_splitbook = art_locator.thisIsSplitBook
        except Exception as e:
            logger.error(f"Problem converting {self.art_id} to locator")
            
    #pydantic definitions
    #art_locator: Optional[opasLocator.Locator] = Field(opasLocator.Locator, title="PEP full article ID locator object")
    art_auth_citation: Optional[str]
    art_auth_mast: Optional[str] = Field(None, title="Author mast, for Solr")
    art_auth_mast_list: list = Field([], title="List of author names format for masts, for Solr")
    art_auth_mast_unlisted_str: Optional[str]
    art_auth_mast_unlisted_list: list = Field([], title="List of author names")
    author_xml_list: list = Field([], title="List of authors, for Solr")
    author_xml: Optional[str]
    authors_bibliographic: Optional[str]
    authors_bibliographic_list: list = Field([], title="List of authors")
    art_citeas_text: Optional[str]
    art_citeas_xml: Optional[str]
    art_doi: Optional[str]
    art_graphic_list: list = Field([], title="List of graphic references")
    art_id: str = Field(None)             # Key!!!!
    art_id_from_filename: Optional[str]   # Should match key!!
    art_is_maintoc: Optional[bool]
    art_isbn: Optional[str]
    art_issn: Optional[str]
    art_issue: Optional[str]
    art_issue_title: Optional[str]
    art_issue_title_str: Optional[str]
    art_issue_seqnbr: Optional[str]
    art_kwds: Optional[str]
    art_kwds_str: Optional[str]
    art_lang: Optional[str]
    art_locator_str: Optional[str]
    art_orig_rx: Optional[str]
    art_pgend: Optional[str]
    art_pgrg: Optional[str]
    art_pgstart: Optional[str]
    art_pgstart_prefix: Optional[str]
    pgstart_suffix: Optional[str]
    pgend_prefix: Optional[str]
    art_pgend: Optional[str]
    pgend_suffix: Optional[str]
    art_qual: Optional[str]
    art_subtitle: Optional[str]
    art_title: Optional[str]
    art_type: Optional[str]
    art_vol_int: Optional[int]
    art_vol_str: Optional[str]
    art_vol_suffix: Optional[str]
    art_vol_title: Optional[str]
    art_year_int: Optional[int]
    art_year_str: Optional[str]
    art_year_suffix: Optional[str]
    art_year2_str: Optional[str]
    art_year2_suffix: Optional[str]
    artinfo_meta_xml: Optional[str]
    artinfo_xml: Optional[str]
    author_list: list = Field([], title="List of author names")
    art_authors_mast_list: list = Field([], title="List of author names")
    art_authors_mast_list_strings: list = Field([], title="List of author names")
    art_author_id_list: list = Field([], title="List of author names")  
    art_author_ids_str: Optional[str]
    art_auth_citation: Optional[str]
    art_auth_citation_list: list = Field([], title="List of authors cited")
    bib_authors: Optional[str]
    bib_title: Optional[str]
    bib_rx: Optional[str]
    bk_info_xml: Optional[str]
    bk_next_id: Optional[str]
    bk_publisher: Optional[str]
    bk_seriestoc: Optional[str]
    bk_subdoc: Optional[str]
    bk_title: Optional[str]
    src_embargo_in_years: Optional[str]
    embargoed: Optional[str] = Field("False")
    embargotype: Optional[str]
    file_classification: Optional[str]
    file_create_time: Optional[str]
    file_size: Optional[int]
    file_updated: Optional[bool]
    filedatetime: Optional[str]
    filename: Optional[str]
    filename: Optional[str]
    filename_artinfo: Optional[str]
    fullfilename: Optional[str]
    glossary_terms_dict: Optional[dict]
    glossary_terms_dict_str: Optional[str]
    last_update: Optional[str]
    main_toc_id: Optional[str]
    manuscript_date_str: Optional[str]
    metadata_dict: Optional[dict]
    preserve: Optional[str]
    processed_datetime: Optional[str]
    publisher_ms_id: Optional[str]
    src_code: Optional[str]
    src_code_active: Optional[str]
    src_is_book: Optional[bool]
    src_prodkey: Optional[str]
    src_title_abbr: Optional[str]
    src_title_full: Optional[str]
    src_type: Optional[str]
    start_sectname: Optional[str]
    start_sectlevel: Optional[str]
    verbose: Optional[bool]
    is_splitbook: Optional[bool]
    bib_rx: list = Field([], title="")
    bib_journaltitle: Optional[str]
    issue_id_str: Optional[str]
    # stat fields for artstat
    art_abs_count: int = Field(0, title="")
    art_authors_count: int = Field(0, title="")
    # art_auth_count = int = Field(0, title="") # perhaps not needed
    art_citations_count: Optional[int]
    art_pgrx_count: int = Field(0, title="")
    art_figcount: int = Field(0, title="")
    art_headings_count: int = Field(0, title="")
    art_poems_count: int = Field(0, title="")
    art_notes_count: int = Field(0, title="")
    art_kwds_count: int = Field(0, title="")
    art_tblcount: int = Field(0, title="")
    art_terms_count: int = Field(0, title="")
    art_pgcount: int = Field(0, title="")
    art_ftns_count: int = Field(0, title="")
    art_quotes_count: int = Field(0, title="")
    art_dreams_count: int = Field(0, title="")
    art_dialogs_count: int = Field(0, title="")
    art_paras_count: int = Field(0, title="")
    art_words_count: int = Field(0, title="")
    art_chars_count: int = Field(0, title="")
    art_chars_no_spaces_count: int = Field(0, title="")
    # glossary_terms_count: int = Field(0, title="Number of glossary terms found")
    ref_count: int = Field(0, title="Number of references")
    
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
