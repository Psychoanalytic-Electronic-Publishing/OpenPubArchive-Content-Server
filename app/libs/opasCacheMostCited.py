import sys
import logging
logger = logging.getLogger(__name__)
import time
#import opasAPISupportLib
from datetime import datetime, timedelta
#from fastapi import HTTPException
#import starlette.status as httpCodes
from opasConfig import normalize_val, VALS_YEAROPTIONS, CACHEURL, \
                       DEFAULT_LIMIT_FOR_CACHE, DEBUG_TRACE, CACHE_EXPIRES_DAYS, \
                       CACHE_EXPIRES_HOURS, CACHE_EXPIRES_MINUTES
#import models
#import opasPySolrLib
from opasPySolrSearch import search_text_qs
import opasQueryHelper

def nested_dict(n, type):
    from collections import defaultdict
    if n == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: nested_dict(n-1, type))

def load_most_cited(cited_in_period: str='5',
                    cite_count: int=0,
                    publication_period: int=None,
                    limit=DEFAULT_LIMIT_FOR_CACHE, 
                    req_url=CACHEURL
                   ):
    ret_val = None
    fname = "load_whats_cited"
    try:
        ret_status = (200, "OK") # default is like HTTP_200_OK
        cited_in_period = normalize_val(cited_in_period, VALS_YEAROPTIONS, default='5')
        sort = f"art_cited_{cited_in_period} desc"
        currentDateTime = datetime.now()
        date = currentDateTime.date()
        start_year = date.strftime("%Y")
        if publication_period is None:
            start_year = None
        else:
            start_year -= publication_period
            start_year = f">{start_year}"
        
        cite_count_predicate = f"{cite_count} in {cited_in_period}"
        field_set = None
        
        solr_query_spec = \
            opasQueryHelper.parse_search_query_parameters(citecount=cite_count_predicate, 
                                                          startyear=start_year,
                                                          highlightlimit=0, 
                                                          return_field_set=field_set, 
                                                          abstract_requested=False,
                                                          sort = sort,
                                                          req_url = req_url
                                                        )
        
        
        ret_val, ret_status = search_text_qs(solr_query_spec, 
                                             limit=limit,
                                             offset=0,
                                             req_url = req_url,
                                             caller_name=fname
                                            )
    except Exception as e:
        logger.error(f"Error {e}")

    return ret_val

class mostCitedCache(object):
    def __init__(self,
                 cited_in_period: str='5',
                 publication_period: int=None,
                 limit=DEFAULT_LIMIT_FOR_CACHE,
                 offset=0, 
                 cite_count: int=0,
                 session_info=None, 
                 req_url=CACHEURL): 
                 
        # load message database
        self.limit = limit
        self.offset = offset
        self.cited_in_period = cited_in_period
        self.publication_period = publication_period

        self.expires = datetime.now() + timedelta(days=CACHE_EXPIRES_DAYS,
                                                  hours=CACHE_EXPIRES_HOURS,
                                                  minutes=CACHE_EXPIRES_MINUTES)

        self.most_cited = load_most_cited(cited_in_period,
                                           cite_count,
                                           publication_period,
                                           limit=limit, 
                                           req_url=req_url
                                         )
        
        
        # response.status_message = "Success"
        self.most_cited.documentList.responseInfo.request = req_url
        self.most_cited.documentList.responseInfo.limit = limit
        self.most_cited.documentList.responseInfo.offset = offset       

    def __del__(self):
        pass
    
    def get_most_cited(self,
                       cited_in_period: str='5',
                       publication_period: int=None,
                       limit=DEFAULT_LIMIT_FOR_CACHE,
                       offset=0, 
                       cite_count: int=0,
                       session_info=None, 
                       req_url=CACHEURL,
                       forced_update=False                ):
        ret_val = {}
        try:
            # reload when needed later
            if self.expires < datetime.now() or forced_update or self.limit != limit or self.cited_in_period != cited_in_period or self.publication_period != publication_period:
                self.most_cited = load_most_cited(cited_in_period=cited_in_period, publication_period=publication_period, limit=limit, offset=offset, req_url=req_url)            
                self.expires = datetime.now() + timedelta(days=CACHE_EXPIRES_DAYS,
                                                          hours=CACHE_EXPIRES_HOURS,
                                                          minutes=CACHE_EXPIRES_MINUTES)
                self.limit = limit
                self.offset = offset
                self.cited_in_period = cited_in_period
                self.publication_period = publication_period

                if DEBUG_TRACE:
                    ts = time.time()
                    print(f"{ts}: [WhatsNew] Cache updated. Exp: {self.expires} DaysBack: {days_back} Limit: {limit} Offset: {offset} Forced:{forced_update}")

            ret_val = self.most_cited
            ret_val.documentList.responseInfo.limit = limit
            ret_val.documentList.responseInfo.offset = offset

        except Exception as e:
            pass

        return ret_val

if __name__ == "__main__":
    print (40*"*", "DBLib Tests", 40*"*")
    print (f"Running in Python {sys.version_info[0]}.{sys.version_info[1]}")
   
    logger = logging.getLogger(__name__)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(name)s %(lineno)d - %(levelname)s %(message)s')    
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    mvdb = mostCitedCache()
    print ("%s: %s" % (mvdb.expires, mvdb.get_most_cited()))

    print ("Fini. Tests complete.")
    
    
