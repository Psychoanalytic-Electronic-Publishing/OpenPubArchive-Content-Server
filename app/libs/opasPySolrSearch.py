#!/usr/bin/env python
# -*- coding: utf-8 -*-

# opasPySolrSearch

import sys
sys.path.append('./solrpy')
sys.path.append("..") # Adds higher directory to python modules path.

import re
import logging
logger = logging.getLogger(__name__)
import time
from errorMessages import *
from datetime import datetime
import localsecrets
from opasConfig import TIME_FORMAT_STR

import starlette.status as httpCodes
from configLib.opasCoreConfig import solr_docs2, solr_authors2, solr_gloss2
import opasConfig 
from configLib.opasCoreConfig import EXTENDED_CORES

from xml.sax import SAXParseException

import models
import opasXMLHelper as opasxmllib
import opasDocPermissions as opasDocPerm
import opasQueryHelper
import pysolr
# still using a function in solpy
import solrpy as solr

LOG = logging.getLogger("pysolr")
LOG.setLevel(logging.WARNING)

#-----------------------------------------------------------------------------
def cleanNullTerms(dictionary):
    # one liner comprehension to clean Nones from dict:
    # from https://medium.com/better-programming/how-to-remove-null-none-values-from-a-dictionary-in-python-1bedf1aab5e4
    return {
        k:v
        for k, v in dictionary.items()
        if v is not None
    }

#-----------------------------------------------------------------------------
def remove_nuisance_word_hits(result_str):
    """
    >>> a = '#@@@the@@@# cat #@@@in@@@# #@@@the@@@# hat #@@@is@@@# #@@@so@@@# smart'
    >>> remove_nuisance_word_hits(a)
    'the cat in the hat is so smart'
    """
    ret_val = rcx_remove_nuisance_words.sub("\g<word>", result_str)
    return ret_val 
    
#-----------------------------------------------------------------------------
def list_all_matches(search_result):
    """
    Not currently used.
    """
    # makes it easier to see matches in a large result
    ret_val = re.findall(f"{opasConfig.HITMARKERSTART}.*{opasConfig.HITMARKEREND}", search_result)
    return ret_val

#-----------------------------------------------------------------------------
def list_all_matches_with_loc(search_result):
    # makes it easier to see matches in a large result
    ret_val = []
    for m in re.compile(f"{opasConfig.HITMARKERSTART}.*{opasConfig.HITMARKEREND}").finditer(search_result):
        start_char = max(m.start()-20, 0)
        end_char = m.end()+30
        ret_val.append(search_result[start_char:end_char])

    return ret_val

#-----------------------------------------------------------------------------
def numbered_anchors(matchobj):
    """
    Called by re.sub on replacing anchor placeholders for HTML output.  This allows them to be numbered as they are replaced.
    """
    global count_anchors
    JUMPTOPREVHIT = f"""<a onclick='scrollToAnchor("hit{count_anchors}");event.preventDefault();'>🡄</a>"""
    JUMPTONEXTHIT = f"""<a onclick='scrollToAnchor("hit{count_anchors+1}");event.preventDefault();'>🡆</a>"""

    if matchobj.group(0) == opasConfig.HITMARKERSTART:
        count_anchors += 1
        if count_anchors > 1:
            #return f"<a name='hit{count_anchors}'><a href='hit{count_anchors-1}'>🡄</a>{opasConfig.HITMARKERSTART_OUTPUTHTML}"
            return f"<a name='hit{count_anchors}'>{JUMPTOPREVHIT}{opasConfig.HITMARKERSTART_OUTPUTHTML}"
        elif count_anchors <= 1:
            return f"<a name='hit{count_anchors}'> "
    if matchobj.group(0) == opasConfig.HITMARKEREND:
        return f"{opasConfig.HITMARKEREND_OUTPUTHTML}{JUMPTONEXTHIT}"

    else:
        return matchobj.group(0)

#-----------------------------------------------------------------------------
def pysolrerror_processing(e):
    error = "pySolr.SolrError"
    error_num = 400
    error_description=f"There's an error in your input (no reason supplied)"
    ret_val = models.ErrorReturn(httpcode=400, error=error, error_description=error_description)

    try:
        if e is None:
            pass # take defaults
        elif e.args is not None:
            # defaults, before trying to decode error
            error = 400
            try:
                err = e.args
                error_set = err[0].split(":", 1)
                error = error_set[0]
                error = error.replace('Solr ', 'Search engine ')
                ret_val.error = error_set[1]
                ret_val.error_description = error_description.strip(" []")
                m = re.search("HTTP (?P<err>[0-9]{3,3})", error)
                if m is not None:
                    http_error = m.group("err")
                    http_error_num = int(http_error)
                    ret_val.httpcode = http_error_num
            except Exception as e:
                logger.error(f"PySolrError: Exception {e} Parsing error {e.args}")
            else:
                ret_val = models.ErrorReturn(httpcode=http_error_num, error=error, error_description=error_description)
    except Exception as e2:
        logger.error(f"PySolrError: {e} Processing exception {e2}")

    return ret_val    

#-----------------------------------------------------------------------------
def get_fulltext_from_search_results(result,
                                     text_xml,
                                     page,
                                     page_offset,
                                     page_limit,
                                     documentListItem: models.DocumentListItem,
                                     format_requested="HTML",
                                     fulltext_children_only=False, 
                                     return_options=None):

    child_xml = None
    offset = 0
    if documentListItem.sourceTitle is None:
        documentListItem = opasQueryHelper.get_base_article_info_from_search_result(result, documentListItem)
        
    #if page_limit is None:
        #page_limit = opasConfig.DEFAULT_PAGE_LIMIT

    documentListItem.docPagingInfo = {}    
    documentListItem.docPagingInfo["page"] = page
    documentListItem.docPagingInfo["page_limit"] = page_limit
    documentListItem.docPagingInfo["page_offset"] = page_offset

    fullText = result.get("text_xml", None)
    text_xml = opasQueryHelper.force_string_return_from_various_return_types(text_xml)
    if text_xml is None:  # no highlights, so get it from the main area
        try:
            text_xml = fullText
        except:
            text_xml = None

    elif fullText is not None:
        if len(fullText) > len(text_xml):
            logger.warning("Warning: text with highlighting is smaller than full-text area.  Returning without hit highlighting.")
            text_xml = fullText

    if text_xml is not None:
        reduce = False
        # see if an excerpt was requested.
        if page is not None and page <= int(documentListItem.pgEnd) and page > int(documentListItem.pgStart):
            # use page to grab the starting page
            # we've already done the search, so set page offset and limit these so they are returned as offset and limit per V1 API
            offset = page - int(documentListItem.pgStart)
            reduce = True
        # Only use supplied offset if page parameter is out of range, or not supplied
        if reduce == False and page_offset is not None and page_offset != 0: 
            offset = page_offset
            reduce = True

        if reduce == True or page_limit is not None:
            # extract the requested pages
            try:
                temp_xml = opasxmllib.xml_get_pages(xmlstr=text_xml,
                                                    offset=offset,
                                                    limit=page_limit,
                                                    pagebrk="pb",
                                                    inside="body",
                                                    env="body")
                temp_xml = temp_xml[0]
                
            except Exception as e:
                logger.error(f"GetFulltextError: Page extraction from document failed. Error: {e}.  Keeping entire document.")
            else: # ok
                text_xml = temp_xml
    
        if return_options is not None:
            if return_options.get("Glossary", None) == False:
                # remove glossary markup
                text_xml = opasxmllib.remove_glossary_impx(text_xml)   
    
    try:
        format_requested_ci = format_requested.lower() # just in case someone passes in a wrong type
    except:
        format_requested_ci = "html"

    if documentListItem.docChild != {} and documentListItem.docChild is not None:
        child_xml = documentListItem.docChild["para"]
    else:
        child_xml = None
    
    if text_xml is None and child_xml is not None:
        text_xml = child_xml
        
    try:
        #ret_val.documents.responseSet[0].hitCriteria = urllib.parse.unquote(search) 
        # remove nuisance stop words from matches
        text_xml = remove_nuisance_word_hits(text_xml)
    except Exception as e:
        logger.error(f"GetFulltextError: Error removing nuisance hits: {e}")

    try:
        documentListItem.hitList = list_all_matches_with_loc(text_xml)
        documentListItem.hitCount = len(documentListItem.hitList)
    except Exception as e:
        logger.error(f"GetFulltextError: Error saving hits and count: {e}")
    
    try:
        matches = re.findall(f"class='searchhit'|{opasConfig.HITMARKERSTART}", text_xml)
    except Exception as e:
        logger.error(f"Exception.  Could not count matches. {e}")
        documentListItem.termCount = 0
    else:
        documentListItem.termCount = len(matches)

    if format_requested_ci == "html":
        # Convert to HTML
        heading = opasxmllib.get_running_head( source_title=documentListItem.sourceTitle,
                                               pub_year=documentListItem.year,
                                               vol=documentListItem.vol,
                                               issue=documentListItem.issue,
                                               pgrg=documentListItem.pgRg,
                                               ret_format="HTML"
                                               )
        try:
            text_xml = opasxmllib.xml_str_to_html(text_xml, transformer_name=opasConfig.TRANSFORMER_XMLTOHTML, document_id=documentListItem.documentID) # transformer_name default used explicitly for code readability
            
        except Exception as e:
            logger.error(f"GetFulltextError: Could not convert to HTML {e}; returning native format")
            text_xml = re.sub(f"{opasConfig.HITMARKERSTART}|{opasConfig.HITMARKEREND}", numbered_anchors, text_xml)
        else:
            try:
                global count_anchors
                count_anchors = 0
                text_xml = re.sub(f"{opasConfig.HITMARKERSTART}|{opasConfig.HITMARKEREND}", numbered_anchors, text_xml)
                text_xml = re.sub("\[\[RunningHead\]\]", f"{heading}", text_xml, count=1)
            except Exception as e:
                logger.error(f"GetFulltextError: Could not do anchor substitution {e}")

        if child_xml is not None:
            child_xml = opasxmllib.xml_str_to_html(child_xml, transformer_name=opasConfig.TRANSFORMER_XMLTOHTML, document_id=documentListItem.documentID) # transformer_name default used explicitly for code readability
            
                
    elif format_requested_ci == "textonly":
        # strip tags
        text_xml = opasxmllib.xml_elem_or_str_to_text(text_xml, default_return=text_xml)
        if child_xml is not None:
            child_xml = opasxmllib.xml_elem_or_str_to_text(child_xml, default_return=text_xml)
    elif format_requested_ci == "xml":
        # don't do this for XML
        pass
        # text_xml = re.sub(f"{opasConfig.HITMARKERSTART}|{opasConfig.HITMARKEREND}", numbered_anchors, text_xml)
        # child_xml = child_xml

    documentListItem.document = text_xml
                
    if child_xml is not None:
        # return child para in requested format
        documentListItem.docChild['para'] = child_xml
        if fulltext_children_only == True:
            documentListItem.document = child_xml
    else:
        if fulltext_children_only == True:
            documentListItem.document = None

    return documentListItem

#-----------------------------------------------------------------------------
def search_stats_for_download(solr_query_spec: models.SolrQuerySpec,
                              limit=None,
                              offset=None,
                              sort=None, 
                              session_info=None,
                              solr_core="pepwebdocs"
                              ):
    """
    SPECIAL - do the search for the purpose of downloading stat...could be many records.
    
    """
    ret_val = {}
    ret_status = (200, "OK") # default is like HTTP_200_OK
    
    if solr_query_spec.solrQueryOpts is None: # initialize a new model
        solr_query_spec.solrQueryOpts = models.SolrQueryOpts()

    if solr_query_spec.solrQuery is None: # initialize a new model
        solr_query_spec.solrQuery = models.SolrQuery()

    solr_query_spec.solrQueryOpts.hlMaxAnalyzedChars = 200
    # let this be None, if no limit is set.
    if offset is not None:
        solr_query_spec.offset = offset

    if limit is not None:
        solr_query_spec.limit = min(limit, opasConfig.MAX_DOCUMENT_RECORDS_RETURNED_AT_ONCE) 
    else:
        solr_query_spec.limit = 99000 # opasConfig.MAX_DOCUMENT_RECORDS_RETURNED_AT_ONCE

    if sort is not None:
        solr_query_spec.solrQuery.sort = sort

    # q must be part of any query; this appears to be the cause of the many solr syntax errors seen. 
    if solr_query_spec.solrQuery.searchQ is None or solr_query_spec.solrQuery.searchQ == "":
        logger.error(f"SearchStatDownloadError: searchQ: {solr_query_spec.solrQuery.searchQ}.  Filter: {solr_query_spec.solrQuery.filterQ} Endpoint: {req_url}")
        solr_query_spec.solrQuery.searchQ = "*.*"

    query = solr_query_spec.solrQuery.searchQ
    try:
        solr_param_dict = { 
                            "fq": solr_query_spec.solrQuery.filterQ,
                            "q.op": solr_query_spec.solrQueryOpts.qOper, 
                            "debugQuery": solr_query_spec.solrQueryOpts.queryDebug or localsecrets.SOLR_DEBUG,
                            "fl" : opasConfig.DOCUMENT_ITEM_STAT_FIELDS, 
                            "rows" : solr_query_spec.limit,
                            "start" : solr_query_spec.offset,
                            "sort" : solr_query_spec.solrQuery.sort
        }

        # PySolr does not like None's, so clean them
        solr_param_dict = cleanNullTerms(solr_param_dict)
        
    except Exception as e:
        logger.error(f"SolrParamAssignmentError: {e}")

    #allow core parameter here
    solr_query_spec.core = "pepwebdocs"
    solr_core = solr_docs2 # by specing this it's always solrpy docs2, no effect of core choice

    # ############################################################################
    # SOLR Download Query
    # ############################################################################
    try:
        start_time = time.time()
        results = solr_core.search(query, **solr_param_dict)
        total_time = time.time() - start_time
        
    except pysolr.SolrError as e:
        ret_status = pysolrerror_processing(e)

    except solr.SolrException as e:
        if e is None:
            ret_val = models.ErrorReturn(httpcode=httpCodes.HTTP_400_BAD_REQUEST, error="Solr engine returned an unknown error", error_description=f"Solr engine returned error without a reason")
            logger.error(f"SolrRuntimeError: {e.reason} Body: {e.body}")
            # logger.error(e.body)
        elif e.reason is not None:
            ret_val = models.ErrorReturn(httpcode=e.httpcode, error="Solr engine returned an unknown error", error_description=f"Solr engine returned error {e.httpcode} - {e.reason}")
            logger.error(f"SolrRuntimeError: {e.reason} Body: {e.body}")
            # logger.error(e.body)
        else:
            ret_val = models.ErrorReturn(httpcode=e.httpcode, error="Search syntax error", error_description=f"There's an error in your input (no reason supplied)")
            logger.error(f"SolrRuntimeError: {e.httpcode} Body: {e.body}")
            # logger.error(e.body)
        
        ret_status = (e.httpcode, e) # e has type <class 'solrpy.core.SolrException'>, with useful elements of httpcode, reason, and body, e.g.,

    else: #  search was ok
        try:
            logger.info("Download Search Performed: %s", solr_query_spec.solrQuery.searchQ)
            logger.info("The Filtering: %s", solr_query_spec.solrQuery.filterQ)
            logger.info("Result  Set Size: %s", results.hits)
            logger.info("Return set limit: %s", solr_query_spec.limit)
            logger.info(f"Download Stats Solr Search Time: {total_time}")
            scopeofquery = [solr_query_spec.solrQuery.searchQ, solr_query_spec.solrQuery.filterQ]
    
            if ret_status[0] == 200: 
                documentItemList = []
                rowCount = 0
                for result in results.docs:
                    documentListItem = models.DocumentListItem()
                    #documentListItem = get_base_article_info_from_search_result(result, documentListItem)
                    citeas = result.get("art_citeas_xml", None)
                    citeas = opasQueryHelper.force_string_return_from_various_return_types(citeas)
                    
                    documentListItem.score = result.get("score", None)               
                    # see if this article is an offsite article
                    result["text_xml"] = None                   
                    stat = {}
                    count_all = result.get("art_cited_all", None)
                    if count_all is not None:
                        stat["art_cited_5"] = result.get("art_cited_5", None)
                        stat["art_cited_10"] = result.get("art_cited_10", None)
                        stat["art_cited_20"] = result.get("art_cited_20", None)
                        stat["art_cited_all"] = count_all
    
                    count0 = result.get("art_views_lastcalyear", 0)
                    count1 = result.get("art_views_lastweek", 0)
                    count2 = result.get("art_views_last1mos", 0)
                    count3 = result.get("art_views_last6mos", 0)
                    count4 = result.get("art_views_last12mos", 0)
    
                    if count0 + count1 + count2 + count3+ count4 > 0:
                        stat["art_views_lastcalyear"] = count0
                        stat["art_views_lastweek"] = count1
                        stat["art_views_last1mos"] = count2
                        stat["art_views_last6mos"] = count3
                        stat["art_views_last12mos"] = count4
    
                    if stat == {}:
                        stat = None
    
                    documentListItem.stat = stat
                    documentListItem.docLevel = result.get("art_level", None)
                    rowCount += 1
                    # add it to the set!
                    documentItemList.append(documentListItem)

            responseInfo = models.ResponseInfo(
                                               count = len(results.docs),
                                               fullCount = results.hits,
                                               totalMatchCount = results.hits,
                                               limit = solr_query_spec.limit,
                                               offset = solr_query_spec.offset,
                                               listType="documentlist",
                                               scopeQuery=[scopeofquery], 
                                               fullCountComplete = solr_query_spec.limit >= results.hits,
                                               solrParams = results.raw_response["responseHeader"]["params"],
                                               request=f"{solr_query_spec.urlRequest}",
                                               core=solr_query_spec.core, 
                                               timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
            )
    
            documentListStruct = models.DocumentListStruct( responseInfo = responseInfo, 
                                                            responseSet = documentItemList
                                                            )
    
            documentList = models.DocumentList(documentList = documentListStruct)
    
            ret_val = documentList
            
        except Exception as e:
            logger.error(f"SolrResultsError: Exception: {e}")
            
    logger.info(f"Download Stats Document Return Time: {time.time() - start_time}")
    return ret_val, ret_status

#================================================================================================================
def search_text_qs(solr_query_spec: models.SolrQuerySpec,
                   extra_context_len=None,
                   req_url: str=None,
                   facet_limit=None,
                   facet_offset=None, 
                   limit=None,
                   offset=None,
                   mlt_count=None, # 0 turns off defaults for mlt, number overrides defaults, setting solr_query_spec is top priority
                   sort=None, 
                   session_info=None,
                   solr_core="pepwebdocs", 
                   get_full_text=False, 
                   get_child_text_only=False, # usage example: just return concordance paragraphs
                   request=None, #pass around request object, needed for ip auth
                   caller_name="search_text_qs"
                   ):
    """
    Full-text search, via the Solr server api.

    Returns a pair of values: ret_val, ret_status.  The double return value is important in case the Solr server isn't running or it returns an HTTP error.  The 
       ret_val = a DocumentList model object
       ret_status = a status tuple, consisting of a HTTP status code and a status mesage. Default (HTTP_200_OK, "OK")

    """
    ret_val = {}
    ret_status = (200, "OK") # default is like HTTP_200_OK
    # default_access_limited_message_not_logged_in = msgdb.get_user_message(msg_code=opasConfig.ACCESS_LIMITD_REASON_NOK_NOT_LOGGED_IN)

    # count_anchors = 0
    try:
        caller_name = caller_name + "/ search_text_qs"
    except:
        caller_name="search_text_qs"
        
    try:
        session_id = session_info.session_id
        #user_logged_in_bool = opasDocPerm.user_logged_in_per_header(request, session_id=session_id, caller_name=caller_name + "/ search_text_qs")
    except Exception as e:
        if req_url != opasConfig.CACHEURL: # no session supplied when loading caching, ok
            logger.warning("No Session info supplied to search_text_qs")
        # mark as not logged in
        #user_logged_in_bool = False

    if 1: # just to allow folding
        if solr_query_spec.solrQueryOpts is None: # initialize a new model
            solr_query_spec.solrQueryOpts = models.SolrQueryOpts()
    
        if solr_query_spec.solrQuery is None: # initialize a new model
            solr_query_spec.solrQuery = models.SolrQuery()
    
        if extra_context_len is not None:
            solr_query_spec.solrQueryOpts.hlFragsize = extra_context_len
        elif solr_query_spec.solrQueryOpts.hlFragsize is None or solr_query_spec.solrQueryOpts.hlFragsize < opasConfig.DEFAULT_KWIC_CONTENT_LENGTH:
            solr_query_spec.solrQueryOpts.hlFragsize = opasConfig.DEFAULT_KWIC_CONTENT_LENGTH
        #else: # for debug only
            #print (f"Fragment Size: {solr_query_spec.solrQueryOpts.hlFragsize}")
    
        if solr_query_spec.solrQueryOpts.moreLikeThisCount > 0: # this (arg based) is the priority value
            mlt = "true"
            mlt_count = solr_query_spec.solrQueryOpts.moreLikeThisCount
            if solr_query_spec.solrQueryOpts.moreLikeThisFields is None:
                mlt_fl = opasConfig.DEFAULT_MORE_LIKE_THIS_FIELDS # Later: solr_query_spec.solrQueryOpts.moreLikeThisFields
            mlt_minwl = 4
        elif mlt_count is not None and mlt_count > 0:
            # mlt_count None means "don't care, use default", mlt_count > 0: override default
            mlt = "true"
            #  use default fields though
            mlt_fl = opasConfig.DEFAULT_MORE_LIKE_THIS_FIELDS # Later: solr_query_spec.solrQueryOpts.moreLikeThisFields
            mlt_minwl = 4
        elif (opasConfig.DEFAULT_MORE_LIKE_THIS_COUNT > 0 and mlt_count is None): # if caller doesn't care (None) and default is on
            # mlt_count None means "don't care, use default", mlt_count > 0: override default
            mlt = "true"
            if mlt_count is None: # otherwise it's more than 0 so overrides the default
                mlt_count = opasConfig.DEFAULT_MORE_LIKE_THIS_COUNT
            #  use default fields though
            mlt_fl = opasConfig.DEFAULT_MORE_LIKE_THIS_FIELDS # Later: solr_query_spec.solrQueryOpts.moreLikeThisFields
            mlt_minwl = 4
        else: # otherwise no MLT, mlt_count may be intentionally set to 0, or default is off and caller didn't say
            mlt_fl = None
            mlt = "false"
            mlt_minwl = None
            mlt_count = 0
    
        if solr_query_spec.facetFields is not None:
            facet = "on"
        else:
            facet = "off"
    
        try:
            if solr_query_spec.solrQueryOpts.hlMaxAnalyzedChars != 0: # let caller configure, but not 0!
                if solr_query_spec.fullReturn:
                    solr_query_spec.solrQueryOpts.hlMaxAnalyzedChars = opasConfig.SOLR_KWIC_MAX_ANALYZED_CHARS 
                else:
                    solr_query_spec.solrQueryOpts.hlMaxAnalyzedChars = opasConfig.SOLR_FULL_TEXT_MAX_ANALYZED_CHARS 
            else: # solr default
                solr_query_spec.solrQueryOpts.hlMaxAnalyzedChars = None # will be removed from args, giving solr default of 51200
        except:
            solr_query_spec.solrQueryOpts.hlMaxAnalyzedChars = opasConfig.SOLR_KWIC_MAX_ANALYZED_CHARS # opasConfig.SOLR_HIGHLIGHT_RETURN_FRAGMENT_SIZE
        #else: OK, leave it be!
    
        try: # must have value
            if solr_query_spec.solrQueryOpts.hlFragsize < opasConfig.DEFAULT_KWIC_CONTENT_LENGTH:
                solr_query_spec.solrQueryOpts.hlFragsize = opasConfig.DEFAULT_KWIC_CONTENT_LENGTH
        except:
            solr_query_spec.solrQueryOpts.hlFragsize = opasConfig.DEFAULT_KWIC_CONTENT_LENGTH
        else:
            pass # else, it's ok
    
        # let this be None, if no limit is set.
        if limit is not None:
            if limit < 0: # unlimited return, to bypass default
                solr_query_spec.limit = opasConfig.MAX_DOCUMENT_RECORDS_RETURNED_AT_ONCE
            else:
                solr_query_spec.limit = limit
    
        if offset is not None:
            solr_query_spec.offset = offset
    
        if sort is not None:
            solr_query_spec.solrQuery.sort = sort
    
        # q must be part of any query; this appears to be the cause of the many solr syntax errors seen. 
        if solr_query_spec.solrQuery.searchQ is None or solr_query_spec.solrQuery.searchQ == "":
            logger.error(f"QuerySpecificationError: searchQ is {solr_query_spec.solrQuery.searchQ}.  Filter: {solr_query_spec.solrQuery.filterQ} Endpoint was: {req_url}")
            solr_query_spec.solrQuery.searchQ = "*.*"
        
        # one last cleaning
        #solr_query_spec.solrQuery.searchQ = solr_query_spec.solrQuery.searchQ.replace(" && *:*", "")
        #solr_query_spec.solrQuery.filterQ = solr_query_spec.solrQuery.filterQ.replace(" && *:*", "")

    try:
        query = solr_query_spec.solrQuery.searchQ
        # set up return fields including abstract and full-text if requested
        return_fields = solr_query_spec.returnFields
        if solr_query_spec.fullReturn: #and session_info.XXXauthenticated:
            # NOTE: we add this here, but in return data, access by document will be checked.
            if "text_xml" not in solr_query_spec.returnFields:
                return_fields = return_fields + ", text_xml, para" #, art_excerpt, art_excerpt_xml
        
        if solr_query_spec.abstractReturn:
            if "abstract_xml" not in solr_query_spec.returnFields:
                return_fields = return_fields + ", abstract_xml"
            if "art_excerpt" not in solr_query_spec.returnFields:
                return_fields = return_fields + ", art_excerpt, art_excerpt_xml"
            if "summaries_xml" not in solr_query_spec.returnFields:
                return_fields = return_fields + ", summaries_xml"

        if type(solr_query_spec.solrQuery.facetQ) == str: # sometimes coming in as Query(None)
            if solr_query_spec.solrQuery.facetQ is not None:
                filterQ = solr_query_spec.solrQuery.filterQ + " && (" + solr_query_spec.solrQuery.facetQ + ")"
            else:
                filterQ = solr_query_spec.solrQuery.filterQ
        else:
            filterQ = solr_query_spec.solrQuery.filterQ
            
        # extend related documents search (art_qual) to unmarked documents that are explicitly referenced in ID
        # TODO: (Possible) Should this also do this in the query param?
        #if "art_qual:" in filterQ:
            #filterQ = re.sub('art_qual:\(\"?(?P<tgtid>[^\"]*?)\"?\)', '(art_qual:(\g<tgtid>) || art_id:(\g<tgtid>))', filterQ)
            
        solr_param_dict = { 
                            # "q": solr_query_spec.solrQuery.searchQ,
                            "fq": filterQ,
                            "q.op": solr_query_spec.solrQueryOpts.qOper, 
                            # "debugQuery": solr_query_spec.solrQueryOpts.queryDebug or localsecrets.SOLR_DEBUG,
                            # "defType" : solr_query_spec.solrQueryOpts.defType,
                            "fl" : return_fields,         
                            "facet" : facet,
                            "facet.field" : solr_query_spec.facetFields, #["art_lang", "art_authors"],
                            "facet.mincount" : solr_query_spec.facetMinCount,
                            "mlt" : mlt,
                            "mlt.fl" : mlt_fl,
                            "mlt.count" : mlt_count,
                            "mlt.minwl" : mlt_minwl,
                            "mlt.interestingTerms" : "list",
                            "rows" : solr_query_spec.limit,
                            "start" : solr_query_spec.offset,
                            "sort" : solr_query_spec.solrQuery.sort,
                            "hl" : solr_query_spec.solrQueryOpts.hl, 
                            "hl.multiterm" : solr_query_spec.solrQueryOpts.hlMultiterm,
                            "hl.fl" : solr_query_spec.solrQueryOpts.hlFields,
                            "hl.usePhraseHighlighter" : solr_query_spec.solrQueryOpts.hlUsePhraseHighlighter, 
                            "hl.snippets" : solr_query_spec.solrQueryOpts.hlMaxKWICReturns,
                            "hl.fragsize" : solr_query_spec.solrQueryOpts.hlFragsize, 
                            "hl.maxAnalyzedChars" : solr_query_spec.solrQueryOpts.hlMaxAnalyzedChars,
                            # for unified method, use hl.tag.pre and hl.tag.post NOTE: This tags illegally in XML
                            # for original method, use hl.simple.pre and hl.simple.post
                            "hl.method": "unified",
                            # "hl_encoder":"HTML",
                            "hl.tag.pre" : opasConfig.HITMARKERSTART,
                            "hl.tag.post" : opasConfig.HITMARKEREND        
        }

    except Exception as e:
        logger.error(f"SolrParamError: {e}")

    #allow core parameter here
    if solr_core is None:
        if solr_query_spec.core is not None:
            try:
                solr_core = EXTENDED_CORES.get(solr_query_spec.core, None)
            except Exception as e:
                detail=f"CoreSpecificationError: Bad Extended Request. {e}"
                logger.error(detail)
                ret_val = models.ErrorReturn(httpcode=400, error="Core specification error", error_description=detail)
            else:
                if solr_core is None:
                    detail=f"Bad Extended Request. Unknown core specified."
                    logger.error(detail)
                    ret_val = models.ErrorReturn(httpcode=400, error="Core specification error", error_description=detail)
        else:
            solr_query_spec.core = "pepwebdocs"
            solr_core = solr_docs2
    else:
        try:
            solr_core = EXTENDED_CORES.get(solr_core, None)
        except Exception as e:
            detail=f"CoreSpecificationError: Bad Extended Request. {e}"
            logger.error(detail)
            ret_val = models.ErrorReturn(httpcode=400, error="Core specification error", error_description=detail)
        else:
            if solr_core is None:
                detail=f"CoreSpecificationError: Bad Extended Request. No core specified."
                logger.error(detail)
                ret_val = models.ErrorReturn(httpcode=400, error="Core specification error", error_description=detail)

    try:
        # PySolr does not like None's, so clean them
        solr_param_dict = cleanNullTerms(solr_param_dict)

        if opasConfig.LOCAL_TRACE:
            print (f"+****Solr Query: q:{query}, fq:{filterQ}")
            #print (f"+****Solr facets:{solr_param_dict.get('facet.field', 'No facets to return')}" )
            print (f"+****Solr Facet Query: q:{solr_query_spec.solrQuery.facetQ}")
                       
        # ####################################################################################
        # THE SEARCH!
        results = solr_docs2.search(query, **solr_param_dict)
        # ####################################################################################
       
    except SAXParseException as e:
        ret_val = models.ErrorReturn(httpcode=httpCodes.HTTP_400_BAD_REQUEST, error="Search syntax error", error_description=f"{e.getMessage()}")
        ret_status = (httpCodes.HTTP_400_BAD_REQUEST, e) 
        logger.error(f"SolrSAXParseExceptionError: Search Error (parse): {ret_val}. Params sent: {solr_param_dict}")

    except AttributeError as e:
        logger.error(f"SolrAttributeExceptionError: Attribute Error: {e}")
           
    except pysolr.SolrError as e:
        error = "pySolr.SolrError"
        error_num = 400
        error_description=f"PySolrError: There's an error in your input ({e})"
        # {ret_status[1].reason}:{ret_status[1].body}
        ret_status = (error_num, {"reason": error, "body": error_description})
        ret_val = models.ErrorReturn(httpcode=400, error=error, error_description=error_description)

        if e is None:
            pass # take defaults
        elif e.args is not None:
            # defaults, before trying to decode error
            error_description = "PySolrError: Search Error"
            error = 400
            http_error_num = 0
            try:
                err = e.args
                error_set = err[0].split(":", 1)
                error = error_set[0]
                error = error.replace('Solr ', 'Search engine ')
                error_description = error_set[1]
                error_description = error_description.strip(" []")
                m = re.search("HTTP (?P<err>[0-9]{3,3})", error)
                if m is not None:
                    http_error = m.group("err")
                    http_error_num = int(http_error)
            except Exception as e:
                logger.error(f"PySolrError: Error parsing Solr error {e.args} Query: {query}")
                ret_status = (error_num, e.args)
            else:
                ret_val = models.ErrorReturn(httpcode=http_error_num, error=error, error_description=error_description)
                ret_status = (error_num, {"reason": error, "body": error_description})

        logger.error(f"PySolrError: Syntax: {ret_status}. Query: {query} Params sent: {solr_param_dict}")
        
    except Exception as e:
        try:
            tb = sys.exc_info()[2]
            raise ValueError(...).with_traceback(tb)
        except Exception as e2:
            error_code = 500
            ret_status = (httpCodes.HTTP_500_INTERNAL_SERVER_ERROR, None)
        else:
            ret_status = (httpCodes.HTTP_400_BAD_REQUEST, e) # e has type <class 'solrpy.core.SolrException'>, with useful elements of httpcode, reason, and body, e.g.,
        finally:
            ret_val = models.ErrorReturn(httpcode=error_code, error="Search syntax error", error_description=f"There's an error in your input (no reason supplied)")
            logger.error(f"PySolrError: Syntax: {ret_status}. Query: {query} Params sent: {solr_param_dict}")
                                
    else: #  search was ok
        try:
            logger.info(f"Ok. Result Size:{results.hits}; Search:{solr_query_spec.solrQuery.searchQ}; Filter:{solr_query_spec.solrQuery.filterQ}")
            scopeofquery = solr_query_spec.solrQuery # [solr_query_spec.solrQuery.searchQ, solr_query_spec.solrQuery.filterQ, solr_query_spec.solrQuery.facetQ]
    
            if ret_status[0] == 200: 
                documentItemList = []
                rowCount = 0
                # rowOffset = 0
                #if solr_query_spec.fullReturn:
                    ## if we're not authenticated, then turn off the full-text request and behave as if we didn't try
                    #if not authenticated: # and file_classification != opasConfig.DOCUMENT_ACCESS_FREE:
                        ## can't bring back full-text
                        #logger.warning("Fulltext requested--by API--but not authenticated.")
                        #solr_query_spec.fullReturn = False
                        
                # try checking PaDS for authenticated; if false, no need to check permits
                try:
                    if session_info is not None:
                        if session_info.authenticated == False:
                            logger.debug("User is not authenticated.  Permit optimization enabled.")
                        else:
                            logger.debug("User is authenticated.  Permit optimization disabled.")
                    else: # no session info provided.  Set it to defaults, non-authenticated
                        logger.debug("No session info object provided.")
                        
                except Exception as e:
                    #  no session info...what to do?
                    logger.debug(f"No session info to perform optimizations {e}")
                    
                record_count = len(results.docs)
                for result in results.docs:
                    # reset anchor counts for full-text markup re.sub
                    # count_anchors = 0
                    # authorIDs = result.get("art_authors", None)
                    documentListItem = models.DocumentListItem()
                    documentListItem = opasQueryHelper.get_base_article_info_from_search_result(result, documentListItem, session_info=session_info)
                    documentID = documentListItem.documentID
                    if documentID is None:
                        # there's a problem with this records
                        logger.error(f"DocumentError: Incomplete record, skipping. Possible corrupt solr database: {result}")
                        continue
                    # sometimes, we don't need to check permissions
                    # Always check if fullReturn is selected
                    # Don't check when it's not and a large number of records are requested (but if fullreturn is requested, must check)
                    # NEW 20211008 - If logged in, check permissions for full-text, or an abstract request with one return
                    documentListItem.accessChecked = False # default anyway, but to make sure it always exists
                    documentListItem.accessLimited = True  # default is True anyway, but to make sure it always exists
                    if get_full_text or (solr_query_spec.abstractReturn and record_count == 1): 
                        access = opasDocPerm.get_access_limitations( doc_id=documentListItem.documentID, 
                                                                     classification=documentListItem.accessClassification, # based on file_classification (where it is)
                                                                     year=documentListItem.year,
                                                                     doi=documentListItem.doi, 
                                                                     session_info=session_info, 
                                                                     documentListItem=documentListItem,
                                                                     fulltext_request=solr_query_spec.fullReturn,
                                                                     request=request
                                                                    ) # will updated accessLimited fields in documentListItem
                        
                        if access is not None: # copy all the access info returned
                            documentListItem.accessChecked = True
                            documentListItem.accessLimited = access.accessLimited   
                            documentListItem.accessLimitedCode = access.accessLimitedCode
                            documentListItem.accessLimitedClassifiedAsCurrentContent = access.accessLimitedClassifiedAsCurrentContent
                            documentListItem.accessLimitedReason = access.accessLimitedReason
                            documentListItem.accessLimitedDebugMsg = access.accessLimitedDebugMsg
                            documentListItem.accessLimitedDescription = access.accessLimitedDescription
                            documentListItem.accessLimitedPubLink = access.accessLimitedPubLink
                        else:
                            logger.error("getaccesslimitations: Why is access none?")
                    #else:
                        #if get_full_text or (solr_query_spec.abstractReturn and record_count == 1:
                                             
                        #if documentListItem.accessClassification in (opasConfig.DOCUMENT_ACCESS_CURRENT): # PEPCurrent
                            #documentListItem.accessLimitedDescription = ocd.get_user_message(msg_code=opasConfig.ACCESS_SUMMARY_DESCRIPTION) + ocd.get_user_message(msg_code=opasConfig.ACCESS_CLASS_DESCRIPTION_CURRENT_CONTENT)
                            #documentListItem.accessLimitedClassifiedAsCurrentContent = True
                        #elif documentListItem.accessClassification in (opasConfig.DOCUMENT_ACCESS_FUTURE): 
                            #documentListItem.accessLimitedDescription = ocd.get_user_message(msg_code=opasConfig.ACCESS_SUMMARY_DESCRIPTION) + ocd.get_user_message(msg_code=opasConfig.ACCESS_CLASS_DESCRIPTION_FUTURE_CONTENT)
                            #documentListItem.accessLimitedClassifiedAsCurrentContent = False
                        #documentListItem.accessChecked = False # not logged in
                        #documentListItem.accessLimited = True   
                        #documentListItem.accessLimitedCode = 200
                        #if not user_logged_in_bool:
                            #documentListItem.accessLimitedReason = default_access_limited_message_not_logged_in # ocd.get_user_message(msg_code=opasConfig.ACCESS_LIMITD_REASON_NOK_NOT_LOGGED_IN)
                        ## documentListItem.accessLimitedDebugMsg = access.accessLimitedDebugMsg

                        
                    documentListItem.score = result.get("score", None)               
                    try:
                        text_xml = results.highlighting[documentID].get("text_xml", None)
                        if text_xml == []:
                            text_xml = None
                    except:
                        text_xml = None
    
                    if text_xml is None: # try getting it from para
                        try:
                            text_xml = results.highlighting[documentID].get("para", None)
                        except:
                            try:
                                text_xml = result["text_xml"]
                            except:
                                text_xml = result.get("para", None)
                    
                    #if text_xml is None: # PySolrLib doesn't put text in highlight unless there was a term search, so get it here.
                        #text_xml = result.get("text_xml", None)
    
                    if text_xml is not None and type(text_xml) != list:
                        text_xml = [text_xml]
                       
                    # do this before we potentially clear text_xml if no full text requested below
                    if solr_query_spec.abstractReturn:
                        # this would print a message about logging in and not display an abstract if omit_abstract were true,
                        # but then Google could not index
                        documentListItem = opasQueryHelper.get_excerpt_from_search_result(result,
                                                                                          documentListItem,
                                                                                          solr_query_spec.returnFormat,
                                                                                          omit_abstract=False)
    
                    documentListItem.kwic = "" # need this, so it doesn't default to None
                    documentListItem.kwicList = []
                    # no kwic list when full-text is requested.
                    kwic_list = []
                    kwic = ""  # this has to be "" for PEP-Easy, or it hits an object error.  
                    if text_xml is not None and not solr_query_spec.fullReturn and solr_query_spec.solrQueryOpts.hl == 'true':
                        #kwicList = getKwicList(textXml, extraContextLen=extraContextLen)  # returning context matches as a list, making it easier for clients to work with
                        kwic_list = []
                        for n in text_xml:
                            # strip all tags
                            try:
                                match = opasxmllib.xml_string_to_text(n)
                                # change the tags the user told Solr to use to the final output tags they want
                                #   this is done to use non-xml-html hit tags, then convert to that after stripping the other xml-html tags
                                # this function changes variable count_anchors with the count of changes
                                match = re.sub(opasConfig.HITMARKERSTART, opasConfig.HITMARKERSTART_OUTPUTHTML, match)
                                match = re.sub(opasConfig.HITMARKEREND, opasConfig.HITMARKEREND_OUTPUTHTML, match)
                                # watch for Doctype which isn't removed if partial or part of a tag (2021-04-05)
                                match = re.sub("(\<?DOCTYPE[^>]+?\>)|(^[^\<]{0,25}?>)", "", match)
                                match = match.lstrip(". ")
                            except Exception as e:
                                logger.warn(f"Error in processing hitlist entry: {e}")
                            else:
                                kwic_list.append(match)
    
                        kwic = " . . . ".join(kwic_list)  # how its done at GVPi, for compatibility (as used by PEPEasy)
                        # we don't need fulltext
                        text_xml = None
    
                    if kwic != "": documentListItem.kwic = kwic
                    if kwic_list != []: documentListItem.kwicList = kwic_list
    
                    # see if this article is an offsite article
                    offsite = result.get("art_offsite", False)
                    # ########################################################################
                    # This is the room where where full-text return HAPPENS
                    # ########################################################################
                    if solr_query_spec.fullReturn and (documentListItem.accessChecked and documentListItem.accessLimited == False) and not offsite:
                        documentListItem.term = f"SearchHits({solr_query_spec.solrQuery.searchQ})"
                        documentListItem = get_fulltext_from_search_results(result=result,
                                                                            text_xml=text_xml,
                                                                            format_requested=solr_query_spec.returnFormat,
                                                                            return_options=solr_query_spec.returnOptions, 
                                                                            page=solr_query_spec.page,
                                                                            page_offset=solr_query_spec.page_offset,
                                                                            page_limit=solr_query_spec.page_limit,
                                                                            documentListItem=documentListItem)

                        # test remove glossary..for my tests, not for stage/production code.
                        # Note: the question mark before the first field in search= matters
                        #  e.g., http://development.org:9100/v2/Documents/Document/JCP.001.0246A/?return_format=XML&search=%27?fulltext1="Evenly%20Suspended%20Attention"~25&limit=10&facetmincount=1&facetlimit=15&sort=score%20desc%27
                        # documentListItem.document = opasxmllib.xml_remove_tags_from_xmlstr(documentListItem.document,['impx'])
                        if documentListItem.document == None:
                            errmsg = f"DocumentError: Fetch failed! ({solr_query_spec.solrQuery.searchQ}"
                            logger.error(errmsg)
                            documentListItem.termCount = 0
                        
                    else: # by virtue of not calling that...
                        # no full-text if accessLimited or offsite article
                        # free up some memory, since it may be large
                        result["text_xml"] = None
                        # But if this is a call for a child paragraph, go get it
                        if get_child_text_only: # caller_name == "documents_get_concordance_paras":
                            documentListItem = get_fulltext_from_search_results(result=result,
                                                                                text_xml=text_xml,
                                                                                format_requested=solr_query_spec.returnFormat,
                                                                                return_options=solr_query_spec.returnOptions, 
                                                                                page=solr_query_spec.page,
                                                                                page_offset=solr_query_spec.page_offset,
                                                                                page_limit=solr_query_spec.page_limit,
                                                                                documentListItem=documentListItem,
                                                                                fulltext_children_only=True)
                    
                    stat = {}
                    count_all = result.get("art_cited_all", None)
                    if count_all is not None:
                        stat["art_cited_5"] = result.get("art_cited_5", None)
                        stat["art_cited_10"] = result.get("art_cited_10", None)
                        stat["art_cited_20"] = result.get("art_cited_20", None)
                        stat["art_cited_all"] = count_all
    
                    count0 = result.get("art_views_lastcalyear", 0)
                    count1 = result.get("art_views_lastweek", 0)
                    count2 = result.get("art_views_last1mos", 0)
                    count3 = result.get("art_views_last6mos", 0)
                    count4 = result.get("art_views_last12mos", 0)
    
                    if count0 + count1 + count2 + count3+ count4 > 0:
                        stat["art_views_lastcalyear"] = count0
                        stat["art_views_lastweek"] = count1
                        stat["art_views_last1mos"] = count2
                        stat["art_views_last6mos"] = count3
                        stat["art_views_last12mos"] = count4
    
                    # count fields (relatively new, 2021)
                    stat["reference_count"] = result.get("art_ref_count", 0)
                    stat["art_fig_count"] = result.get("art_fig_count", 0)
                    stat["art_tbl_count"] = result.get("art_tbl_count", 0)
                    stat["art_kwds_count"] = result.get("art_kwds_count", 0)
                    stat["art_words_count"] = result.get("art_words_count", 0)
                    stat["art_citations_count"] = result.get("art_citations_count", 0)
                    stat["art_ftns_count"] = result.get("art_ftns_count", 0)
                    stat["art_notes_count"] = result.get("art_notes_count", 0)
                    stat["art_dreams_count"] = result.get("art_dreams_count", 0)

                    if stat == {}:
                        stat = None
    
                    documentListItem.stat = stat
    
                    similarityMatch = None
                    if mlt_count > 0:
                        if results.raw_response["moreLikeThis"][documentID] is not None:
                            similarityMatch = {}
                            # remove text
                            similarityMatch["similarDocs"] = {}
                            similarityMatch["similarDocs"][documentID] = []
                            for n in results.raw_response["moreLikeThis"][documentID]["docs"]:
                                likeThisListItem = models.DocumentListItem()
                                #n["text_xml"] = None
                                n = opasQueryHelper.get_base_article_info_from_search_result(n, likeThisListItem)                    
                                similarityMatch["similarDocs"][documentID].append(n)
    
                            similarityMatch["similarMaxScore"] = results.raw_response["moreLikeThis"][documentID]["maxScore"]
                            similarityMatch["similarNumFound"] = results.raw_response["moreLikeThis"][documentID]["numFound"]
                            # documentListItem.moreLikeThis = results.moreLikeThis[documentID]
    
                    if similarityMatch is not None: documentListItem.similarityMatch = similarityMatch
                    
                    #parent_tag = result.get("parent_tag", None)
                    #if parent_tag is not None:
                        #documentListItem.docChild = {}
                        #documentListItem.docChild["id"] = result.get("id", None)
                        #documentListItem.docChild["parent_tag"] = parent_tag
                        #documentListItem.docChild["para"] = result.get("para", None)
                        #documentListItem.docChild["lang"] = result.get("lang", None)
                        #documentListItem.docChild["para_art_id"] = result.get("para_art_id", None)
                    #else:
                        #documentListItem.docChild = None
    
                    sort_field = None
                    if solr_query_spec.solrQuery.sort is not None:
                        try:
                            sortby = re.search("(?P<field>[a-z_]+[1-9][0-9]?)[ ]*?", solr_query_spec.solrQuery.sort)
                        except Exception as e:
                            sort_field = None
                        else:
                            if sortby is not None:
                                sort_field = sortby.group("field")
    
                    documentListItem.score = result.get("score", None)
                    documentListItem.rank = rowCount + 1
                    if sort_field is not None:
                        if sort_field == "art_cited_all":
                            documentListItem.rank = result.get("art_cited_all", None) 
                        elif sort_field == "score":
                            documentListItem.rank = result.get("score", None)
                        else:
                            documentListItem.rank = result.get(sort_field, None)
                            
                            
                    rowCount += 1
                    # add it to the set!
                    documentItemList.append(documentListItem)
                    #TODO - we probably don't need this.
                    if solr_query_spec.limit is not None:
                        if rowCount > solr_query_spec.limit:
                            break
    
                try:
                    facet_counts = {}
                    facets = results.facets["facet_fields"]
                    facet_counts["facet_fields"] = facet_processing(facets)
                    
                except:
                    facet_counts = None
    
            if req_url is None:
                req_url = solr_query_spec.urlRequest
    
            # Moved this down here, so we can fill in the Limit, Page and Offset fields based on whether there
            #  was a full-text request with a page offset and limit
            # Solr search was ok
            responseInfo = models.ResponseInfo(count = len(results.docs),
                                               fullCount = results.hits,
                                               totalMatchCount = results.hits,
                                               description=solr_query_spec.solrQuery.semanticDescription, 
                                               limit = solr_query_spec.limit,
                                               offset = solr_query_spec.offset,
                                               page = solr_query_spec.page, 
                                               listType="documentlist",
                                               scopeQuery=[scopeofquery], 
                                               fullCountComplete = solr_query_spec.limit >= results.hits,
                                               solrParams = None, # results._params,
                                               facetCounts=facet_counts,
                                               #authenticated=authenticated, 
                                               request=f"{req_url}",
                                               core=solr_query_spec.core, 
                                               timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                               )
   
            # responseInfo.count = len(documentItemList)
    
            documentListStruct = models.DocumentListStruct( responseInfo = responseInfo, 
                                                            responseSet = documentItemList
                                                            )
    
            documentList = models.DocumentList(documentList = documentListStruct)
    
            ret_val = documentList
            
        except Exception as e:
            logger.error(f"QueryResultsError: Problem processing results {e}")
            

    return ret_val, ret_status
