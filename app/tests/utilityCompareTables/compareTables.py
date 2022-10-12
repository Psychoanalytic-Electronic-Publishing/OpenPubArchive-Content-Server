#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
# Disable many annoying pylint messages, warning me about variable naming for example.
# yes, in my Solr code I'm caught between two worlds of snake_case and camelCase.

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2022.0708.1" 
__status__      = "Development"

programNameShort = "compareTables"
import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")


import sys
sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')

import re
import time
import difflib

from datetime import datetime as datetime1

import logging
logger = logging.getLogger(programNameShort)
logger.setLevel(logging.DEBUG)
import mysql.connector

import localsecrets
# import opasCentralDBLib
# import opasGenSupportLib as opasgenlib

from localsecrets import STAGE_DB_HOST, AWSDB_PWS, AWSDB_USERS, PRODUCTION_DB_HOST, AWSDEV_DB_HOST 
LOCALDEV_DBHOST = "localhost"
LOCALDEV_DBUSER = "root"
LOCALDEV_DBPW = ""

def is_date_time(date_text):
    ret_val = True
    try:
        if isinstance(date_text, datetime1):
            ret_val = True
        else:
            ret_val = datetime1.strptime(date_text, '%Y-%m-%d')
            
    except ValueError:
        ret_val = False

    return ret_val

# ------------------------------------------------------------------------------------------
# diff code from https://towardsdatascience.com/side-by-side-comparison-of-strings-in-python-b9491ac858

def tokenize(s):
    return re.split('\s+', s)

def untokenize(ts):
    return ' '.join(ts)
        
def equalize(s1, s2):
    l1 = tokenize(s1)
    l2 = tokenize(s2)
    res1 = []
    res2 = []
    prev = difflib.Match(0,0,0)
    for match in difflib.SequenceMatcher(a=l1, b=l2).get_matching_blocks():
        if (prev.a + prev.size != match.a):
            for i in range(prev.a + prev.size, match.a):
                res2 += ['_' * len(l1[i])]
            res1 += l1[prev.a + prev.size:match.a]
        if (prev.b + prev.size != match.b):
            for i in range(prev.b + prev.size, match.b):
                res1 += ['_' * len(l2[i])]
            res2 += l2[prev.b + prev.size:match.b]
        res1 += l1[match.a:match.a+match.size]
        res2 += l2[match.b:match.b+match.size]
        prev = match
    return untokenize(res1), untokenize(res2)

def insert_newlines(string, every=64, window=10):
    result = []
    from_string = string
    while len(from_string) > 0:
        cut_off = every
        if len(from_string) > every:
            while (from_string[cut_off-1] != ' ') and (cut_off > (every-window)):
                cut_off -= 1
        else:
            cut_off = len(from_string)
        part = from_string[:cut_off]
        result += [part]
        from_string = from_string[cut_off:]
    return result

def show_comparison(s1, s2, width=40, margin=10, sidebyside=True, compact=False):
    s1, s2 = equalize(s1,s2)

    if sidebyside:
        s1 = insert_newlines(s1, width, margin)
        s2 = insert_newlines(s2, width, margin)
        if compact:
            for i in range(0, len(s1)):
                lft = re.sub(' +', ' ', s1[i].replace('_', '')).ljust(width)
                rgt = re.sub(' +', ' ', s2[i].replace('_', '')).ljust(width)
                if lft != rgt:
                    print(lft + ' | ' + rgt + ' | ')        
        else:
            for i in range(0, len(s1)):
                lft = s1[i].ljust(width)
                rgt = s2[i].ljust(width)
                if lft != rgt:
                    print(lft + ' | ' + rgt + ' | ')
    else:
        print(s1)
        print(s2)

# end diff code
# ------------------------------------------------------------------------------------------

class opasCentralDBMini(object):
    """
    This object should be used and then discarded in any multiuser mode.
    Therefore, keeping session info in the object is ok
    
    """
    connection_count = 0
    
    def __init__(self, session_id=None,
                 host=localsecrets.DBHOST,
                 port=localsecrets.DBPORT,
                 user=localsecrets.DBUSER,
                 password=localsecrets.DBPW,
                 database=localsecrets.DBNAME):

        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connected = False
        self.db = None
        self.session_id = session_id # deprecate?
    
    def open_connection(self, dbname=localsecrets.DBNAME, caller_name=""):
        """
        Opens a connection if it's not already open.
        
        If already open, no changes.
        >>> ocd = opasCentralDB()
        >>> ocd.open_connection("my name")
        True
        >>> ocd.close_connection("my name")
        """
        try:
            status = self.db.open
            self.connected = True
        except:
            # not open reopen it.
            status = False
        
        if status == False:
            try:
                opasCentralDBMini.connection_count += 1
                self.db = mysql.connector.connect(host=self.host, port=self.port, user=self.user, password=self.password, database=self.database)
                self.connected = True
                logger.debug(f"Database opened by ({caller_name}) Specs: {self.database} for host {self.host},  user {self.user} port {self.port} Opened connection #{opasCentralDBMini.connection_count}")
                
            except Exception as e:
                self.connected = False
                logger.error(f"compareTablesDBError: Cannot connect to database {self.database} for host {self.host},  user {self.user} port {self.port} ({e})")
                self.db = None

        return self.connected

    def close_connection(self, caller_name=""):
        try:
            self.db.close()
            self.db = None
            opasCentralDBMini.connection_count -= 1
            logger.debug(f"Database closed by ({caller_name})")
                
        except Exception as e:
            logger.error(f"caller: {caller_name} the db is not open ({e}).")

        self.connected = False
        return self.connected

    def get_table_sql(self, sql):
        """
         Returns 0,[] if no rows are returned
        """
        ret_val = []
        row_count = 0
        caller_name = "get_table_sql"
        # always make sure we have the right input value
        self.open_connection(caller_name=caller_name) # make sure connection is open
        
        if self.db is not None:
            cursor = self.db.cursor(mysql.connector.cursor)
            cursor.execute(sql)
            warnings = cursor.fetchwarnings()
            if warnings:
                for warning in warnings:
                    logger.warning(warning)

            ret_val = cursor.fetchall() # returns empty list if no rows
            row_count = cursor.rowcount

            cursor.close()
        else:
            logger.fatal("Connection not available to database.")
        
        self.close_connection(caller_name=caller_name) # make sure connection is closed
        return row_count, ret_val

#----------------------------------------------------------------------------------------
#  End OpasCentralDBMini
#----------------------------------------------------------------------------------------


def compare_critical_columns(table_name, key_col_name, value_col_name, where_clause=""):
    #  compare local dev and production before pushing
    #  open databases
    try:
        print ("Comparing local DEV table with Production")
        dev_db = opasCentralDBMini(host=LOCALDEV_DBHOST, password=LOCALDEV_DBPW, user=LOCALDEV_DBUSER)
        prod_db = opasCentralDBMini(host=PRODUCTION_DB_HOST, password=AWSDB_PWS[1], user=AWSDB_USERS[1])
    except Exception as e:
        logger.error(f"Cannot open dev or production databases: {e}.  Terminating without changes")
    else:
        pass

    sql1=f"select {key_col_name}, {value_col_name} from {table_name} {where_clause} order by 1 ASC"
    dev_row_count, dev_tbl = dev_db.get_table_sql(sql1)
    prod_row_count, prod_tbl = prod_db.get_table_sql(sql1)
    # dev_dict = {}
    prod_dict = {}

    for n in prod_tbl:
        # unpack and store
        key_col_val, value_col_val = n
        prod_dict[key_col_val] = value_col_val
        
    count = 0
    for n in dev_tbl:
        key_col_val, value_col_val = n
        try:
            if value_col_val != prod_dict[key_col_val]:
                count += 1
                if not isinstance(value_col_val, str):
                    print (f"Difference in {value_col_name}: {(value_col_val, value_col_val, prod_dict[key_col_val])}")
                else:
                    show_comparison(value_col_val, prod_dict[key_col_val], sidebyside=True, width=60, compact=False)

                #else: # enumerate diffs
                    #for i,s in enumerate(difflib.ndiff(value_col_val, prod_dict[key_col_val])):
                        #if s[0]==' ': continue
                        #elif s[0]=='-':
                            #print(u'Delete "{}" from position {}'.format(s[-1],i))
                        #elif s[0]=='+':
                            #print(u'Add "{}" to position {}'.format(s[-1],i))    
                
        except KeyError:
            print (f"Key: {key_col_val} not on production")

    print (f"{count} differences!")
    return count

def compare_critical_column_lists(table_name, key_col_name, value_col_name_list, db1Name="STAGE", db2Name="PRODUCTION", key_where_clause="", verbose=False):
    #  compare local dev and production before pushing
    #  open databases

    try:
        if db1Name == "LOCALDEV":
            dev_db = opasCentralDBMini(host=LOCALDEV_DBHOST, password=LOCALDEV_DBPW, user=LOCALDEV_DBUSER)
        elif db1Name == "STAGE":
            dev_db = opasCentralDBMini(host=STAGE_DB_HOST, password=AWSDB_PWS[1], user=AWSDB_USERS[1])
        elif db1Name == "AWSDEV":
            dev_db = opasCentralDBMini(host=AWSDEV_DB_HOST, password=AWSDB_PWS[1], user=AWSDB_USERS[1])
        elif db1Name  == "PRODUCTION":
            dev_db = opasCentralDBMini(host=PRODUCTION_DB_HOST, password=AWSDB_PWS[1], user=AWSDB_USERS[1])
                
        if db2Name == "LOCALDEV":
            target_db = opasCentralDBMini(host=LOCALDEV_DBHOST, password=LOCALDEV_DBPW, user=LOCALDEV_DBUSER)
        elif db2Name == "STAGE":
            target_db = opasCentralDBMini(host=STAGE_DB_HOST, password=AWSDB_PWS[1], user=AWSDB_USERS[1])
        elif db2Name == "AWSDEV":
            target_db = opasCentralDBMini(host=AWSDEV_DB_HOST, password=AWSDB_PWS[1], user=AWSDB_USERS[1])
        elif db2Name == "PRODUCTION":
            target_db = opasCentralDBMini(host=PRODUCTION_DB_HOST, password=AWSDB_PWS[1], user=AWSDB_USERS[1])

    except Exception as e:
        logger.error(f"Cannot open dev or production databases: {e}.  Terminating without changes")
    else:
        if key_where_clause != "" and key_where_clause is not None:
            additional_info = key_where_clause
        else:
            additional_info = ""
            
        print (f"\nComparing {db1Name} table {table_name} with {db2Name} {additional_info}")


    for value_col_name in value_col_name_list:
        # if verbose: print (f"\tChecking: {value_col_name}")
        sql1=f"select {key_col_name}, {value_col_name} from {table_name} {key_where_clause} order by 1 ASC"
        dev_row_count, dev_tbl = dev_db.get_table_sql(sql1)
        target_row_count, target_tbl = target_db.get_table_sql(sql1)
        #dev_dict = {}
        target_dict = {}

        for n in target_tbl:
            # unpack and store
            key_col_val, value_col_val = n
            target_dict[key_col_val] = value_col_val
            
        count = 0
        for n in dev_tbl:
            key_col_val, value_col_val = n
            try:
                if value_col_val != target_dict[key_col_val]:
                    count += 1
                    if not isinstance(value_col_val, str):
                        print (f"Difference in {value_col_name}: {(value_col_val, target_dict[key_col_val])}")
                    else:
                        print (f"Difference in {value_col_name}:{key_col_val}")
                        show_comparison(value_col_val, target_dict[key_col_val], sidebyside=True, width=60, compact=False)
                    #else: # enumerate diffs
                        #for i,s in enumerate(difflib.ndiff(value_col_val, target_dict[key_col_val])):
                            #if s[0]==' ': continue
                            #elif s[0]=='-':
                                #print(u'Delete "{}" from position {}'.format(s[-1],i))
                            #elif s[0]=='+':
                                #print(u'Add "{}" to position {}'.format(s[-1],i))    
            except KeyError:
                print (f"Key: {key_col_val} on {db1Name} not on target {db2Name}")
                count += 1
    
        if count > 0 or verbose: print (f"\t{value_col_name} has {count} differences!")
    
    return count
    

def compare_tables(db_tables=None):

    def_db_tables = [{"name": "api_productbase", "key": "basecode"},
                     #{"name": "vw_api_productbase_instance_counts", "key": "basecode"},
                     {"name": "api_endpoints", "key": "api_endpoint_id"},
                     {"name": "vw_api_messages", "key": "msg_num_code, msg_language"},
                     {"name": "api_client_apps", "key": "api_client_id"}
    ]
    
    if db_tables is None:
        db_tables = def_db_tables

    #  open databases
    try:
        stage_ocd = opasCentralDBMini(host=STAGE_DB_HOST, password=AWSDB_PWS[0], user=AWSDB_USERS[0])
        prod_ocd = opasCentralDBMini(host=PRODUCTION_DB_HOST, password=AWSDB_PWS[1], user=AWSDB_USERS[1])
        awsdev_ocd = opasCentralDBMini(host=AWSDEV_DB_HOST, password=AWSDB_PWS[2], user=AWSDB_USERS[2])
        # if local
        localdev_ocd = opasCentralDBMini(host=LOCALDEV_DBHOST, password=LOCALDEV_DBPW, user=LOCALDEV_DBUSER)

    except Exception as e:
        logger.error(f"Cannot open stage or production databases: {e}.  Terminating without changes")
    else:
        pass
    
    total_diffs = 0       
    for db_table in db_tables:
        sql1 = f"""SELECT * from {db_table['name']} ORDER BY {db_table['key']} ASC;"""

        try:
            print (80*"=")
            print (f"Evaluating table: {db_table['name']}")
            stage_row_count, stage_tbl = stage_ocd.get_table_sql(sql1)
            dev_row_count, dev_tbl = localdev_ocd.get_table_sql(sql1)
            awsdev_row_count, awsdev_tbl = awsdev_ocd.get_table_sql(sql1)
            prod_row_count, prod_tbl = prod_ocd.get_table_sql(sql1)
            if stage_row_count != dev_row_count != awsdev_row_count != prod_row_count:
                print (f"\t{db_table['name']} differs!")
                continue
            else:
                row_count = stage_row_count
                print (f"\tRow counts (localdev, awsdev, stage, prod): {(dev_row_count, awsdev_row_count, stage_row_count, prod_row_count)}")
            
            stage_col_count = len(stage_tbl[0])
            dev_col_count = len(dev_tbl[0])
            awsdev_col_count = len(awsdev_tbl[0])
            prod_col_count = len(prod_tbl[0])
            
            diffs = 0
            coldiffs = 0
            if stage_col_count != dev_col_count:
                print (f"Stage column count {stage_col_count} different than LocalDev column count {dev_col_count}.")
                coldiffs += 1
            if stage_col_count != awsdev_col_count:
                print (f"Stage column count {stage_col_count} different than AWSDev column count {awsdev_col_count}.")
                coldiffs += 1
            if stage_col_count != prod_col_count:
                print (f"Stage column count {stage_col_count} different than Prod column count {prod_col_count}.")
                coldiffs += 1

            if coldiffs > 0:
                print ("Column count differences.  Stopping compare.")
            else:
                for n in range(row_count):
                    if dev_tbl[n] != stage_tbl[n]:
                        print (f"\tLocalDev vs Stage: {db_table['name']} row {n} differs! Key: {dev_tbl[n][0]}")
                        for item in range(len(stage_tbl[n])):
                            if dev_tbl[n][item] !=  stage_tbl[n][item]:
                                print (f"\t\tCol {item} LocalDev: {dev_tbl[n][item]}")
                                print (f"\t\tCol {item} Stage: {stage_tbl[n][item]}")
                                print (f"\t\t{40*'-'}")
                        #print (f"\t\tDev: {dev_tbl[n]}")
                        #print (f"\t\tStage: {stage_tbl[n]}")
                        diffs += 1
                    if stage_tbl[n] != awsdev_tbl[n]:
                        print (f"\tStage vs AWS Dev: {db_table['name']} row {n} differs! Key:  {dev_tbl[n][0]}")
                        for item in range(len(stage_tbl[n])):
                            if awsdev_tbl[n][item] !=  stage_tbl[n][item]:
                                if awsdev_tbl[n][item] is not None:
                                    if is_date_time(awsdev_tbl[n][item]):
                                        continue
                                print (f"\t\tCol {item} Dev: {awsdev_tbl[n][item]}")
                                print (f"\t\tCol {item} Stage: {stage_tbl[n][item]}")
                                print (f"\t\t{40*'-'}")
                        #print (f"\t\tStage: {stage_tbl[n]}")
                        #print (f"\t\tAWSDev: {awsdev_tbl[n]}")
                        diffs += 1
                    if stage_tbl[n] != prod_tbl[n]:
                        print (f"\tStage vs Prod: {db_table['name']} row {n} differs!")
                        for item in range(len(stage_tbl[n])):
                            if prod_tbl[n][item] != stage_tbl[n][item]:
                                if is_date_time(awsdev_tbl[n][item]):
                                    pass
                                else:
                                    print (f"\t\tCol {item} Dev: {prod_tbl[n][item]}")
                                    print (f"\t\tCol {item} Stage: {stage_tbl[n][item]}")
                                    print (f"\t\t{40*'-'}")
                        #print (f"\t\tStage: {stage_tbl[n]}")
                        #print (f"\t\tProd: {prod_tbl[n]}")
                        diffs += 1
                    if diffs > 10:
                        print (f"{diffs} row differences found; compare was discontinued.")
                        break

            if diffs == 0 and coldiffs == 0:
                print(f"\t{db_table['name']} Tables are the same.")
            else:
                print(f"\t{db_table['name']} Tables Differ.  Row diff Count: {diffs}")
    
            total_diffs += diffs
            
        except IndexError:
            pass # column count difference
        
        except Exception as e:
            print (f"Error: {e}")

    return total_diffs

#------------------------------------------------------------------------------------------------------
def main():

    print(
        f""" 
            {programNameShort} - CompareTables
        
            This program compares the important setup tables in the four MySQL/RDS databases
            used in the PEP-Web data preparation and Production process.
            
            The tables compared need to be in sync for the system to operate properly.
            
            Databases:
              dev - localhost development database
              awsdev - Development database used by production process
              stage - stage server for testing builds
              production - PEP-Web end-user site
            
            Tables:
              The tested tables are listed in a list of dicts.  They currently include:
              db_tables = "api_productbase" - List of journals and books and metadata
                          "api_endpoints"   - List of endpoints and ids
                          "api_messages"    - API return messages (from the server)
                          "api_client_apps" - List of registered client apps
              
            Example Invocation:
                    $ python compareTables.py
                    
            Requires Python 3
            
        """
    )

    # set toplevel logger to specified loglevel
    logger = logging.getLogger()
    logger.setLevel(logging.WARN)
    # get local logger
    logger = logging.getLogger(programNameShort)
    logger.info('Started at %s', datetime1.today().strftime('%Y-%m-%d %H:%M:%S"'))
    logger.setLevel(logging.WARN)

    print (f"Processing started at ({time.ctime()}).")
    print((80*"-"))

# -------------------------------------------------------------------------------------------------------
# run it!

#if __name__ == "__main__":
    #main()
