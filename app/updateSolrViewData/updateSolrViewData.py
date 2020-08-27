#!/usr/bin/env python
# -*- coding: utf-8 -*-
print(
    """
    UpdateSolrViewData - Program to update the view stat child records in the pepwebdocs
                        Solr instance
    """
)
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2020, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2020.0827.1"
__status__      = "Testing"

import sys
sys.path.append('../config')

import logging
import time
import pymysql
import pysolr
import localsecrets

from datetime import datetime
programNameShort = "updateSolrviewData"  # used for log file
logFilename = programNameShort + "_" + datetime.today().strftime('%Y-%m-%d') + ".log"
logger = logging.getLogger(programNameShort)
logger.info('Started at %s', datetime.today().strftime('%Y-%m-%d %H:%M:%S"'))

class opasCentralDBMini(object):
    """
    This object should be used and then discarded on an endpoint by endpoint basis in any
      multiuser mode.
      
    Therefore, keeping session info in the object is ok,
    """
    def __init__(self, session_id=None, access_token=None, token_expires_time=None, username="NotLoggedIn", user=None):
        self.db = None
        self.connected = False
        self.authenticated = False
        self.session_id = session_id
        self.access_token = access_token
        self.user = None
        self.sessionInfo = None
        
    def open_connection(self, caller_name=""):
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
            # this is normal, why log it?
            # logger.debug(f"Database connection was already opened ({caller_name})")
        except:
            # not open reopen it.
            status = False
        
        if status == False:
            try:
                tunneling = None
                if localsecrets.SSH_HOST is not None:
                    from sshtunnel import SSHTunnelForwarder
                    self.tunnel = SSHTunnelForwarder(
                                                      (localsecrets.SSH_HOST,
                                                       localsecrets.SSH_PORT),
                                                       ssh_username=localsecrets.SSH_USER,
                                                       ssh_pkey=localsecrets.SSH_MYPKEY,
                                                       remote_bind_address=(localsecrets.DBHOST,
                                                                            localsecrets.DBPORT))
                    self.tunnel.start()
                    self.db = pymysql.connect(host='127.0.0.1',
                                           user=localsecrets.DBUSER,
                                           passwd=localsecrets.DBPW,
                                           db=localsecrets.DBNAME,
                                           port=self.tunnel.local_bind_port)
                    tunneling = self.tunnel.local_bind_port
                else:
                    #  not tunneled
                    self.db = pymysql.connect(host=localsecrets.DBHOST, port=localsecrets.DBPORT, user=localsecrets.DBUSER, password=localsecrets.DBPW, database=localsecrets.DBNAME)

                logger.debug(f"Database opened by ({caller_name}) Specs: {localsecrets.DBNAME} for host {localsecrets.DBHOST},  user {localsecrets.DBUSER} port {localsecrets.DBPORT} tunnel {tunneling}")
                self.connected = True
            except Exception as e:
                err_str = f"Cannot connect to database {localsecrets.DBNAME} for host {localsecrets.DBHOST},  user {localsecrets.DBUSER} port {localsecrets.DBPORT} ({e})"
                logger.error(err_str)
                self.connected = False
                self.db = None

        return self.connected

    def close_connection(self, caller_name=""):
        if self.db is not None:
            try:
                if self.db.open:
                    self.db.close()
                    self.db = None
                    logger.debug(f"Database closed by ({caller_name})")
                    if localsecrets.CONFIG == "AWSTestAccountTunnel":
                        self.tunnel.stop()
                        logger.debug(f"Database tunnel stopped.")
                else:
                    logger.debug(f"Database close request, but not open ({caller_name})")
                    
            except Exception as e:
                logger.error(f"caller: {caller_name} the db is not open ({e})")

        # make sure to mark the connection false in any case
        self.connected = False           

    def get_most_viewed_crosstab(self):
        """
         Using the opascentral api_docviews table data, as dynamically statistically aggregated into
           the view vw_stat_most_viewed return the most downloaded (viewed) documents
           
         Supports the updates to Solr via solrXMLPEPWebload, used for view count queries.
            
        """
        ret_val = None
        row_count = 0
        # always make sure we have the right input value
        self.open_connection(caller_name="get_most_viewed_crosstab") # make sure connection is open
        
        if self.db is not None:
            cursor = self.db.cursor(pymysql.cursors.DictCursor)
            sql = """SELECT DISTINCTROW * FROM vw_stat_to_update_solr_docviews"""
            row_count = cursor.execute(sql)
            if row_count:
                ret_val = cursor.fetchall()
            cursor.close()
        else:
            logger.fatal("Connection not available to database.")
        
        self.close_connection(caller_name="get_most_downloaded_crosstab") # make sure connection is closed
        return row_count, ret_val

    #----------------------------------------------------------------------------------------

def update_views_data(solrcon):
    """
    Use in-place updates to update the views data
    """
    ocd =  opasCentralDBMini()
    
    # set only includes those with the desired update value > 0 
    #   (see RDS vw_stat_to_update_solr_docviews to change criteria)
    count, most_viewed = ocd.get_most_viewed_crosstab()
    update_count = 0
    if most_viewed is not None:
        for n in most_viewed:
            doc_id = n.get("document_id", None)
            count_lastcalyear = n.get("lastcalyear", None) 
            count_last12mos = n.get("last12months", None) 
            count_last6mos = n.get("last6months", None) 
            count_last1mos = n.get("lastmonth", None)
            count_lastweek = n.get("lastweek", None)
            if doc_id is not None:
                update_count += 1
                upd_rec = {
                            "id":doc_id,
                            "art_views_lastcalyear": count_lastcalyear, 
                            "art_views_last12mos": count_last12mos, 
                            "art_views_last6mos": count_last6mos, 
                            "art_views_last1mos": count_last1mos, 
                            "art_views_lastweek": count_lastweek
                }                    
                try:
                    solrcon.add([upd_rec], fieldUpdates={"art_views_lastcalyear": 'set',
                                                         "art_views_last12mos": 'set',
                                                         "art_views_last6mos": 'set',
                                                         "art_views_last1mos": 'set',
                                                         "art_views_lastweek": 'set',
                                                         }, commit=True)
                except Exception as err:
                    errStr = "Solr call exception for views update on %s: %s" % (doc_id, err)
                    logger.error(errStr)
                    
    logger.info(f"Finished updating Solr database with {update_count} article records updated.")
    return update_count

if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser(usage="%prog [options] - PEP Solr Views Update Loader", version=f"Ver. {__version__}")
    parser.add_option("-l", "--loglevel", dest="logLevel", default=logging.WARNING,
                      help="Level at which events should be logged")
    (options, args) = parser.parse_args()

    logging.basicConfig(filename=logFilename, level=options.logLevel)

    updates = 0
    SOLR_DOCS = "pepwebdocs"
    solrurl_docs = localsecrets.SOLRURL + SOLR_DOCS  
    if localsecrets.SOLRUSER is not None and localsecrets.SOLRPW is not None:
        solr_docs2 = pysolr.Solr(solrurl_docs, auth=(localsecrets.SOLRUSER, localsecrets.SOLRPW))
    else: #  no user and password needed
        solr_docs2 = pysolr.Solr(solrurl_docs)
    start_time = time.time()
    logger.info(f"Started at {start_time}")
    updates = update_views_data(solr_docs2)
    total_time = time.time() - start_time
    final_stat = f"{time.ctime()} Updated {updates} Solr records in {total_time} secs)."
    logging.getLogger().setLevel(logging.INFO)
    logger.info(final_stat)
    print (final_stat)
        

