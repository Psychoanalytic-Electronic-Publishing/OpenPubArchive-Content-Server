import sys
import logging
logger = logging.getLogger(__name__)
import datetime
from datetime import datetime, timedelta
import opasPySolrLib
from fastapi import HTTPException
import starlette.status as httpCodes
import opasConfig

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
    fname = "load_whats_new"
    try:
        # return whatsNewList
        ret_val = opasPySolrLib.database_get_whats_new(limit=limit, 
                                                       offset=offset,
                                                       days_back=days_back, 
                                                       req_url=req_url
                                                       )

    except Exception as e:
        e = str(e)
        logger.error(f"Error in database_whatsnew: {e}. Raising HTTP_400_BAD_REQUEST.")
        #raise HTTPException(status_code=httpCodes.HTTP_400_BAD_REQUEST,
                            #detail="Error: {}".format(e.replace("'", "\\'"))
                            #)
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
                load_whats_new(days_back=days_back, limit=limit, offset=offset, req_url=req_url)            
                self.expires = datetime.now() + timedelta(days=opasConfig.WHATS_NEW_EXPIRES_DAYS,
                                                          hours=opasConfig.WHATS_NEW_EXPIRES_HOURS,
                                                          minutes=opasConfig.WHATS_NEW_EXPIRES_MINUTES)
                self.limit = limit
                self.offset = offset
                self.days_back = days_back
                print(f"WhatsNew cache updated. Expires: {self.expires} DaysBack: {days_back} Limit: {limit} Offset: {offset} Forced:{forced_update}")
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
    
    
