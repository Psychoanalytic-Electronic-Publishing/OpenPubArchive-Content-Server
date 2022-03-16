import sys
from contextlib import closing
import logging
logger = logging.getLogger(__name__)
import opasCentralDBLib

def nested_dict(n, type):
    from collections import defaultdict
    if n == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: nested_dict(n-1, type))

def load_message_table():
    ret_val = None
    fname = "get_user_message"
    ocd = opasCentralDBLib.opasCentralDB()
    ocd.open_connection(caller_name=fname) # make sure connection is open
    sql = f"SELECT * from vw_api_messages;"
    if ocd.db is not None:
        with closing(ocd.db.cursor(buffered=True, dictionary=True)) as curs:
            try:
                curs.execute(sql)
                warnings = curs.fetchwarnings()
                if warnings:
                    for warning in warnings:
                        logger.warning(warning)

                if curs.rowcount >= 1:
                    try:
                        ret_val = curs.fetchall()
                    except Exception as e:
                        print (f"Error: {e}")
                        ret_val = None
            except Exception as e:
                print (f"Error: {e}")
                ret_val = None
    else:
        logger.error("Can't load message table.  ocd.db is None.")
        
    ocd.close_connection (caller_name=fname)

    return ret_val

class messageDB(object):
    def __init__(self):
        # load message database
        message_table = load_message_table()
        self.message_dict = nested_dict(2, dict)
        if message_table is not None:
            for n in message_table:
                msg_code = n["msg_num_code"]
                msg_lang = n["msg_language"]
                self.message_dict[msg_code][msg_lang] = n

    def __del__(self):
        pass
    
    def get_user_message(self, msg_code, lang="EN"):
        ret_val = ""
        try:
            if type(msg_code) == str:
                msg_code = int(msg_code)
        except Exception as e:
            logger.error(f"msg_code should be int or numeric string")
            ret_val = ""

        try:
            ret_val = self.message_dict[msg_code][lang]["msg_text"]
        except Exception as e:
            logger.error(f"get_user_message could not find message for {msg_code}")
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
    
    wdb = messageDB()
    print (wdb.get_user_message(401))

    # import doctest
    # doctest.testmod(optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
    #doctest.testmod()    
    print ("Fini. Tests complete.")
    
    
