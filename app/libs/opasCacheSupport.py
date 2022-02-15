#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

from opasPySolrSearch import search_text_qs, search_stats_for_download

import opasConfig
# import localsecrets

import opasQueryHelper
import datetime as dtime

#-----------------------------------------------------------------------------
def document_get_most_viewed( publication_period: int=5,
                              author: str=None,
                              title: str=None,
                              source_name: str=None,  
                              source_code: str=None,
                              source_type: str="journal",
                              abstract_requested: bool=False, 
                              view_period: int=4,               # 4=last12months default. 0:lastcalendaryear 1:lastweek 2:lastmonth, 3:last6months, 4:last12months
                              view_count: str="1",              # up this later
                              req_url: str=None,
                              stat:bool=False, 
                              limit: int=5,                     # Get top 10 from the period
                              offset=0,
                              mlt_count:int=None,
                              sort:str=None,
                              download=False, 
                              session_info=None,
                              request=None
                            ):
    """
    Return the most viewed journal articles (often referred to as most downloaded) duing the prior period years.

    This is used for the statistical summary function and accesses only the relational database, not full-text Solr.

    Args:
        publication_period (int, optional): Look only at articles this many years back to current.  Defaults to 5.
        author (str, optional): Filter, include matching author names per string .  Defaults to None (no filter).
        title (str, optional): Filter, include only titles that match.  Defaults to None (no filter).
        source_name (str, optional): Filter, include only journals matching this name.  Defaults to None (no filter).
        source_type (str, optional): journals, books, or videostreams.
        view_period (int, optional): defaults to last12months

            view_period = { 0: "lastcalyear",
                            1: "lastweek",
                            2: "last1mos",
                            3: "last6mos",
                            4: "last12mos",
                           }

        limit (int, optional): Paging mechanism, return is limited to this number of items.
        offset (int, optional): Paging mechanism, start with this item in limited return set, 0 is first item.

    Returns:
        models.DocumentList: Pydantic structure (dict) for DocumentList.  See models.py

    Docstring Tests:

    >>> result, status = document_get_most_viewed()
    >>> result.documentList.responseSet[0].documentID if result.documentList.responseInfo.count >0 else "No views yet."
    '...'

    """
    ret_val = None
    caller_name = "document_get_most_viewed"
    ret_status = (200, "OK") # default is like HTTP_200_OK
    period = opasConfig.VALS_VIEWPERIODDICT_SOLRFIELDS.get(view_period, "last12mos")
    
    if sort is None:
        sort = f"{period} desc"

    start_year = dtime.date.today().year
    if publication_period is None:
        start_year = None
    else:
        start_year -= publication_period
        start_year = f">{start_year}"

    if stat:
        field_set = "STAT"
    else:
        field_set = None
        
    solr_query_spec = \
        opasQueryHelper.parse_search_query_parameters( viewperiod=view_period,      # 0:lastcalendaryear 1:lastweek 2:lastmonth, 3:last6months, 4:last12months
                                                       viewcount=view_count, 
                                                       source_name=source_name,
                                                       source_code=source_code,
                                                       source_type=source_type,
                                                       author=author,
                                                       title=title,
                                                       startyear=start_year,
                                                       highlightlimit=0, 
                                                       abstract_requested=abstract_requested,
                                                       return_field_set=field_set, 
                                                       sort = sort,
                                                       req_url = req_url
                                                       )
    if download: # much more limited document list if download==True
        ret_val, ret_status = search_stats_for_download(solr_query_spec, 
                                                        session_info=session_info, 
                                                        request = request
                                                        )
    else:
        try:
            ret_val, ret_status = search_text_qs(solr_query_spec, 
                                                 limit=limit,
                                                 offset=offset,
                                                 req_url = req_url, 
                                                 session_info=session_info, 
                                                 request = request,
                                                 caller_name=caller_name
                                                )
        except Exception as e:
            logger.error(f"Search error {e}")

    return ret_val, ret_status   

