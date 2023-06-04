import sys
import logging
logger = logging.getLogger(__name__)
import datetime
import time
#import opasAPISupportLib
from datetime import datetime, timedelta
from fastapi import HTTPException
import starlette.status as httpCodes
from opasConfig import CACHEURL, DEBUG_TRACE, CACHE_EXPIRES_DAYS, CACHE_EXPIRES_HOURS, CACHE_EXPIRES_MINUTES, DEFAULT_LIMIT_FOR_MOST_VIEWED, DEFAULT_LIMIT_FOR_CACHE
import models
from opasCacheSupport import document_get_most_viewed

def nested_dict(n, type):
    from collections import defaultdict
    if n == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: nested_dict(n-1, type))

def load_most_viewed(viewperiod = 2, 
                     limit=DEFAULT_LIMIT_FOR_MOST_VIEWED,
                     offset=0,
                     session_info=None,
                     req_url=CACHEURL):

    ret_val = None
    fname = "load_most_viewed"
    try:
        ret_val, ret_status = document_get_most_viewed( view_period=viewperiod,   # 0:lastcalendaryear 1:lastweek 2:lastmonth, 3:last6months, 4:last12months
                                                        limit=limit, 
                                                        offset=offset,
                                                        session_info=session_info, 
                                                        req_url=req_url
                                                      )

        if ret_val is None:
            status_message = f"MostViewedError: Bad request"
            logger.error(status_message)
            raise HTTPException(
                status_code=httpCodes.HTTP_400_BAD_REQUEST, 
                detail=status_message
            )        
            
    except Exception as e:
        ret_val = None
        status_message = f"MostViewedError: Exception: {e}"
        logger.error(status_message)
        raise HTTPException(
            status_code=httpCodes.HTTP_400_BAD_REQUEST, 
            detail=status_message
        )        
    else:
        if isinstance(ret_val, models.ErrorReturn):
            detail = ret_val.error + " - " + ret_val.error_description                
            logger.error(f"MostViewedError: {detail}")
            raise HTTPException(
                status_code=ret_val.httpcode, 
                detail = detail
            )
        
    return ret_val

class mostViewedCache(object):
    most_viewed = None
    
    def __init__(self,
                 viewperiod = 2, 
                 limit=DEFAULT_LIMIT_FOR_CACHE,
                 offset=0, 
                 session_info=None,
                 req_url=CACHEURL
                ):
        # load message database
        self.limit = limit
        self.offset = offset
        self.viewperiod = viewperiod
        self.expires = datetime.now() + timedelta(days=CACHE_EXPIRES_DAYS,
                                                  hours=CACHE_EXPIRES_HOURS,
                                                  minutes=CACHE_EXPIRES_MINUTES)

        self.most_viewed = load_most_viewed(viewperiod=viewperiod,
                                            limit=limit,
                                            session_info=session_info,
                                            req_url=req_url)

        if self.most_viewed is None:
            status_message = f"MostViewedError: Can't load cache"
            logger.error(status_message)
            raise HTTPException(
                status_code=httpCodes.HTTP_400_BAD_REQUEST, 
                detail=status_message
            )        
            
        # response.status_message = "Success"
        try:
            self.most_viewed.documentList.responseInfo.request = req_url
            self.most_viewed.documentList.responseInfo.limit = limit
            self.most_viewed.documentList.responseInfo.offset = offset
        except Exception as e:
            status_message = f"MostViewedError: Can't load cache {e}"
            logger.error(status_message)
            raise HTTPException(
                status_code=httpCodes.HTTP_400_BAD_REQUEST, 
                detail=status_message
            )        
            
    def __del__(self):
        pass
    
    def get_most_viewed(self,
                        viewperiod = 2, 
                        limit=DEFAULT_LIMIT_FOR_MOST_VIEWED,
                        offset=0, 
                        session_info=None,
                        req_url=CACHEURL,
                        forced_update=False                ):
        ret_val = {}
        try:
            # reload when needed later
            if self.expires < datetime.now() or forced_update or self.limit != limit or self.viewperiod != viewperiod:
                self.most_viewed = load_most_viewed(viewperiod=viewperiod, limit=limit, session_info=session_info, req_url=req_url)
                self.expires = datetime.now() + timedelta(days=CACHE_EXPIRES_DAYS,
                                                          hours=CACHE_EXPIRES_HOURS,
                                                          minutes=CACHE_EXPIRES_MINUTES)
                self.limit = limit
                self.offset = offset
                self.viewperiod = viewperiod
                if DEBUG_TRACE:
                    ts = time.time()
                    print(f"{ts}: [MostViewed] Cache updated. Exp: {self.expires} Limit: {limit} Forced:{forced_update}")

            ret_val = self.most_viewed 
            ret_val.documentList.responseInfo.limit = limit
            ret_val.documentList.responseInfo.offset = offset

        except Exception as e:
            pass

        return ret_val
            
    def __del__(self):
        pass

if __name__ == "__main__":
    print (40*"*", "MostViewedCache Tests", 40*"*")
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
    
    mvdb = mostViewedCache()
    print ("%s: %s" % (mvdb.expires, mvdb.get_most_viewed()))

    print ("Fini. Tests complete.")
    
    
