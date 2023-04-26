import sys
import logging
logger = logging.getLogger(__name__)
import datetime
import time
from datetime import datetime, timedelta
# import opasPySolrLib
# from fastapi import HTTPException
# import starlette.status as httpCodes

import opasConfig
from opasConfig import TIME_FORMAT_STR

# import localsecrets
import models
from configLib.opasCoreConfig import solr_docs2 # solr_authors2, solr_gloss2
import opasCentralDBLib

ocd = opasCentralDBLib.opasCentralDB()

def error_or_empty_return(e="No Error", limit=opasConfig.DEFAULT_LIMIT_FOR_WHATS_NEW, offset=0, query="N/A", req_url="N/A"):
    logger.error(f"WhatsNewError: {e} for query: {query}")
    response_info = models.ResponseInfo( count = 0,
                                         fullCount = 0,
                                         limit = limit,
                                         offset = offset,
                                         listType="newlist",
                                         fullCountComplete = False,
                                         request=f"{req_url}",
                                         timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                         )
    response_info.count = 0
    whats_new_list_items = []
    
    whats_new_list_struct = models.WhatsNewListStruct( responseInfo = response_info, 
                                                       responseSet = whats_new_list_items
                                                       )
    ret_val = models.WhatsNewList(whatsNew = whats_new_list_struct)
    
    return ret_val

def database_uncached_get_whats_new(days_back=14,
                                    limit=opasConfig.DEFAULT_LIMIT_FOR_WHATS_NEW,
                                    req_url:str=None,
                                    source_type="journal",
                                    offset=0,
                                    session_info=None):
    """
    Return what JOURNALS have been updated in the last week

    >>> result = database_uncached_get_whats_new()

    """    
    field_list = "art_id, title, art_vol, art_iss, art_year, art_sourcecode, art_sourcetitlefull, art_sourcetitleabbr, file_last_modified, timestamp, art_sourcetype"
    sort_by = "art_year desc, art_vol desc, file_last_modified desc"
    ret_val = None
    query = "" # initialized for error, added to logging in exception
    try:
        new_articles = ocd.get_articles_newer_than(days_back)
    except Exception as e:
        # log error and return empty set 
        ret_val = error_or_empty_return(e, limit, offset, query=query, req_url=req_url)
    else:
        # two ways to get date, slightly different meaning: timestamp:[NOW-{days_back}DAYS TO NOW] AND file_last_modified:[NOW-{days_back}DAYS TO NOW]
        try:
            query = f"file_last_modified:[NOW-{days_back}DAYS TO NOW] AND art_sourcetype:{source_type}"
            logger.info(f"Solr Query: q={query}")
    
            args = {
                "fl": field_list,
                # "fq": "{!collapse field=art_sourcecode max=art_year_int}",
                "sort": sort_by,
                "rows": opasConfig.MAX_WHATSNEW_ARTICLES_TO_CONSIDER,
                "start": offset
            }
    
            results = solr_docs2.search(query, **args)
    
        except Exception as e:
            # log error and return empty set 
            ret_val = error_or_empty_return(e, limit, offset, query=query, req_url=req_url)
        else:
            num_found = results.raw_response['response']['numFound']
            whats_new_list_items = []
            row_count = 0
            eligible_entry_full_count = 0
            already_seen = []
            for result in results.docs:
                document_id = result.get("art_id", None)
                updated = result.get("file_last_modified", None)
                updated = datetime.strptime(updated,'%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
                if document_id not in new_articles:
                    #print(f"File {document_id} not new {updated}")
                    continue
                
                PEPCode = result.get("art_sourcecode", None)
                #if PEPCode is None or PEPCode in ["SE", "GW", "ZBK", "IPL"]:  # no books
                    #continue
                src_type = result.get("art_sourcetype", None)
                if src_type != "journal":
                    continue
                
                # see if this is already been in the article tracker
                    
                volume = result.get("art_vol", None)
                issue = result.get("art_iss", "")
                year = result.get("art_year", None)
                abbrev = result.get("art_sourcetitleabbr", None)
                src_title = result.get("art_sourcetitlefull", None)
                
                if abbrev is None:
                    abbrev = src_title
                display_title = abbrev + " v%s.%s (%s) " % (volume, issue, year)
                if display_title in already_seen:
                    #print (f"Already seen: {display_title}")
                    continue
                else:
                    already_seen.append(display_title)
    
                eligible_entry_full_count += 1
                volume_url = "/v2/Metadata/Contents/%s/%s/" % (PEPCode, volume)
        
                item = models.WhatsNewListItem( documentID = result.get("art_id", None),
                                                displayTitle = display_title,
                                                abbrev = abbrev,
                                                volume = volume,
                                                issue = issue,
                                                year = year,
                                                PEPCode = PEPCode, 
                                                srcTitle = src_title,
                                                volumeURL = volume_url,
                                                updated = updated
                                                )
    
                whats_new_list_items.append(item)
                row_count += 1 # number of rows added
                if row_count >= limit:
                    break
        
            whats_new_list_items = sorted(whats_new_list_items, key=lambda x: x.displayTitle, reverse = False)    
    
            if limit is not None:
                if offset is None:
                    offset = 0
                limited_whats_new_list = whats_new_list_items[offset:offset+limit]
            else:
                limited_whats_new_list = whats_new_list_items
            
            response_info = models.ResponseInfo( count = len(whats_new_list_items),
                                                 fullCount = eligible_entry_full_count,
                                                 limit = limit,
                                                 offset = offset,
                                                 listType="newlist",
                                                 fullCountComplete = limit >= eligible_entry_full_count,
                                                 request=f"{req_url}",
                                                 timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                                 )
    
            response_info.count = len(whats_new_list_items)
        
            whats_new_list_struct = models.WhatsNewListStruct( responseInfo = response_info, 
                                                               responseSet = limited_whats_new_list
                                                               )
        
            ret_val = models.WhatsNewList(whatsNew = whats_new_list_struct)

    return ret_val   # WhatsNewList

def database_get_whats_new_old(days_back=14,
                           limit=opasConfig.DEFAULT_LIMIT_FOR_WHATS_NEW,
                           req_url:str=None,
                           source_type="journal",
                           offset=0,
                           session_info=None):
    """
    Return what JOURNALS have been updated in the last week

    >>> result = database_get_whats_new()

    """    
    field_list = "art_id, title, art_vol, art_iss, art_year, art_sourcecode, art_sourcetitlefull, art_sourcetitleabbr, file_last_modified, timestamp, art_sourcetype"
    sort_by = "file_last_modified desc"
    ret_val = None
    query = "" # initialized for error, added to logging in exception
    new_articles = ocd.get_articles_newer_than(days_back)

    # two ways to get date, slightly different meaning: timestamp:[NOW-{days_back}DAYS TO NOW] AND file_last_modified:[NOW-{days_back}DAYS TO NOW]
    try:
        query = f"file_last_modified:[NOW-{days_back}DAYS TO NOW] AND art_sourcetype:{source_type}"
        logger.info(f"Solr Query: q={query}")

        args = {
            "fl": field_list,
            "fq": "{!collapse field=art_sourcecode max=art_year_int}",
            "sort": sort_by,
            "rows": opasConfig.MAX_WHATSNEW_ARTICLES_TO_CONSIDER,
            "start": offset
        }

        results = solr_docs2.search(query, **args)

    except Exception as e:
        logger.error(f"WhatsNewError: {e} for query: {query}")
        response_info = models.ResponseInfo( count = 0,
                                             fullCount = 0,
                                             limit = limit,
                                             offset = offset,
                                             listType="newlist",
                                             fullCountComplete = False,
                                             request=f"{req_url}",
                                             timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                             )
        response_info.count = 0
        whats_new_list_items = []
        
        whats_new_list_struct = models.WhatsNewListStruct( responseInfo = response_info, 
                                                           responseSet = whats_new_list_items
                                                           )
        ret_val = models.WhatsNewList(whatsNew = whats_new_list_struct)
    else:
        num_found = results.raw_response['response']['numFound']
        whats_new_list_items = []
        row_count = 0
        eligible_entry_full_count = 0
        already_seen = []
        for result in results.docs:
            document_id = result.get("art_id", None)
            updated = result.get("file_last_modified", None)
            updated = datetime.strptime(updated,'%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
            if document_id not in new_articles:
                print(f"File {document_id} not new {updated}")
                continue
            
            PEPCode = result.get("art_sourcecode", None)
            #if PEPCode is None or PEPCode in ["SE", "GW", "ZBK", "IPL"]:  # no books
                #continue
            src_type = result.get("art_sourcetype", None)
            if src_type != "journal":
                continue
            
            # see if this is already been in the article tracker
                
            volume = result.get("art_vol", None)
            issue = result.get("art_iss", "")
            year = result.get("art_year", None)
            abbrev = result.get("art_sourcetitleabbr", None)
            src_title = result.get("art_sourcetitlefull", None)
            
            if abbrev is None:
                abbrev = src_title
            display_title = abbrev + " v%s.%s (%s) " % (volume, issue, year)
            if display_title in already_seen:
                print (f"Already seen: {display_title}")
                continue
            else:
                already_seen.append(display_title)

            eligible_entry_full_count += 1
            volume_url = "/v2/Metadata/Contents/%s/%s/" % (PEPCode, volume)
    
            item = models.WhatsNewListItem( documentID = result.get("art_id", None),
                                            displayTitle = display_title,
                                            abbrev = abbrev,
                                            volume = volume,
                                            issue = issue,
                                            year = year,
                                            PEPCode = PEPCode, 
                                            srcTitle = src_title,
                                            volumeURL = volume_url,
                                            updated = updated
                                            )

            whats_new_list_items.append(item)
            row_count += 1 # number of rows added
            if row_count >= limit:
                break
    
        whats_new_list_items = sorted(whats_new_list_items, key=lambda x: x.displayTitle, reverse = False)    

        if limit is not None:
            if offset is None:
                offset = 0
            limited_whats_new_list = whats_new_list_items[offset:offset+limit]
        else:
            limited_whats_new_list = whats_new_list_items
        
        response_info = models.ResponseInfo( count = len(whats_new_list_items),
                                             fullCount = eligible_entry_full_count,
                                             limit = limit,
                                             offset = offset,
                                             listType="newlist",
                                             fullCountComplete = limit >= eligible_entry_full_count,
                                             request=f"{req_url}",
                                             timeStamp = datetime.utcfromtimestamp(time.time()).strftime(TIME_FORMAT_STR)                     
                                             )

        response_info.count = len(whats_new_list_items)
    
        whats_new_list_struct = models.WhatsNewListStruct( responseInfo = response_info, 
                                                           responseSet = limited_whats_new_list
                                                           )
    
        ret_val = models.WhatsNewList(whatsNew = whats_new_list_struct)

    return ret_val   # WhatsNewList

def nested_dict(n, type):
    from collections import defaultdict
    if n == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: nested_dict(n-1, type))

def load_whats_new(days_back=opasConfig.DEFAULT_DAYS_BACK_FOR_WHATS_NEW, 
                   limit=opasConfig.DEFAULT_LIMIT_FOR_WHATS_NEW,
                   offset=0, 
                   req_url="Caching"
                   ):
    ret_val = None
    # fname = "load_whats_new"
    try:
        # return whatsNewList
        ret_val = database_uncached_get_whats_new(limit=limit, 
                                         offset=offset,
                                         days_back=days_back, 
                                         req_url=req_url
                                        )

    except Exception as e:
        e = str(e)
        logger.error(f"Error in database_whatsnew: {e}. Raising HTTP_400_BAD_REQUEST.")
    else:
        # response.status_message = "Success"
        ret_val.whatsNew.responseInfo.request = req_url
        ret_val.whatsNew.responseInfo.limit = limit
        ret_val.whatsNew.responseInfo.offset = offset       

    return ret_val

class whatsNewDB(object):
    def __init__(self,
                 days_back=opasConfig.DEFAULT_DAYS_BACK_FOR_WHATS_NEW,
                 limit=opasConfig.DEFAULT_LIMIT_FOR_WHATS_NEW,
                 req_url="Caching"
                ):
        # load message database
        self.limit = limit
        self.offset = 0
        self.days_back = days_back
        self.expires = datetime.now() + timedelta(days=opasConfig.WHATS_NEW_EXPIRES_DAYS,
                                                  hours=opasConfig.WHATS_NEW_EXPIRES_HOURS,
                                                  minutes=opasConfig.WHATS_NEW_EXPIRES_MINUTES)
        self.whats_new = load_whats_new(days_back=days_back, limit=limit, req_url=req_url)
        #print(f"[WhatsNew] Cache initialized. Exp: {self.expires} DaysBack: {days_back} Limit: {limit}")

    def __del__(self):
        pass
    
    def get_whats_new(self,
                      days_back=opasConfig.DEFAULT_DAYS_BACK_FOR_WHATS_NEW, 
                      limit=opasConfig.DEFAULT_LIMIT_FOR_WHATS_NEW,
                      offset=0, 
                      req_url="Caching",
                      forced_update=False
                     ):
        ret_val = {}
        try:
            # reload when needed later
            if self.expires < datetime.now() or forced_update or days_back != self.days_back or offset != self.offset or self.limit != limit:
                self.whats_new = load_whats_new(days_back=days_back, limit=limit, offset=offset, req_url=req_url)            
                self.expires = datetime.now() + timedelta(days=opasConfig.WHATS_NEW_EXPIRES_DAYS,
                                                          hours=opasConfig.WHATS_NEW_EXPIRES_HOURS,
                                                          minutes=opasConfig.WHATS_NEW_EXPIRES_MINUTES)
                self.limit = limit
                self.offset = offset
                self.days_back = days_back

                if opasConfig.DEBUG_TRACE:
                    ts = time.time()
                    logger.info(f"{ts}: [WhatsNew] Cache updated. Exp: {self.expires} DaysBack: {days_back} Limit: {limit} Offset: {offset} Forced:{forced_update}")

            ret_val = self.whats_new
            ret_val.whatsNew.responseInfo.limit = limit
            ret_val.whatsNew.responseInfo.offset = offset

        except Exception as e:
            pass

        return ret_val

if __name__ == "__main__":
    print (40*"*", "DBLib Tests", 40*"*")
    print (f"Running in Python {sys.version_info[0]}.{sys.version_info[1]}")
   
    logger = logging.getLogger(__name__)
    # extra logging for standalong mode 
    # logger.setLevel(logging.DEBUG)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    # ch.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter('%(asctime)s %(name)s %(lineno)d - %(levelname)s %(message)s')    
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)
    
    wdb = whatsNewDB()
    print ("%s: %s" % (wdb.expires, wdb.get_whats_new()))
    cont = input ("Continue (y/n)?")
    print ("%s: %s" % (wdb.expires, wdb.get_whats_new()))
    cont = input ("Continue (y/n)?")
    print ("%s: %s" % (wdb.expires, wdb.get_whats_new(forced_update=True)))
    cont = input ("Continue (y/n)?")
    print ("%s: %s" % (wdb.expires, wdb.get_whats_new()))
    cont = input ("Continue (y/n)?")
    print ("%s: %s" % (wdb.expires, wdb.get_whats_new(forced_update=True)))
    cont = input ("Continue (y/n)?")
    print ("%s: %s" % (wdb.expires, wdb.get_whats_new()))

    print ("Fini. Tests complete.")
    
    
