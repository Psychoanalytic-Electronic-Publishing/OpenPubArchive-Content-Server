#!/usr/bin/env python
# -*- coding: utf-8 -*-
# To run:
#     python3 updateSolrviewData
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2023, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2023.0304/v1.1.12"
__status__      = "Beta"

programNameShort = "opasDataUpdateStat"

print(
    f"""
    {programNameShort} - Program to update the view and citation stat fields in the pepwebdocs
      database.
      
      By default, it only updates records which have views data.

      If you use command line option --all, it will add all citation and views data to the
        pepwebdocs data.  (This takes significantly longer.)
        
         - The first update after a load should be with option --all
         - Then, omit --all to update views daily
            - only records with views will update Solr
            - views data needs to be updated again when moved to Production, since those are the REAL views for the DB.
              The citation data does not need to be reupdated, so you don't need all
         - Citations (include --all) only need be updated after data updates
         
         For complete details, see:
          https://github.com/Psychoanalytic-Electronic-Publishing/OpenPubArchive-Content-Server/wiki/Loading-Data-into-OpenPubArchive

      The records added are controlled by the database views:
         vw_stat_docviews_crosstab
         vw_stat_cited_crosstab2
         
      2020-11-21 Added library numbers display to main startup to monitor what it's running under.
      
      2020-10-29 Important update - Since it is used at database build/rebuild time, it now updates all records
         where views are non-zero, not just the last week.
    """
)

import sys
sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')

UPDATE_AFTER = 100

import logging
import time
import pymysql
import pysolr
import localsecrets
from pydantic import BaseModel
from datetime import datetime

from opasArticleIDSupport import ArticleID

# logFilename = programNameShort + "_" + datetime.today().strftime('%Y-%m-%d') + ".log"
FORMAT = '%(asctime)s %(name)s %(funcName)s %(lineno)d - %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.ERROR, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(programNameShort)
start_notice = f"{programNameShort} version {__version__} started at {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}."
print (start_notice)

unified_article_stat = {}

class ArticleStat(BaseModel):
    document_id: str = None
    art_views_update: bool = False
    art_views_lastcalyear: int = 0
    art_views_last12mos: int = 0
    art_views_last6mos: int = 0
    art_views_last1mos: int = 0
    art_views_lastweek: int = 0
    art_cited_5: int = 0
    art_cited_10: int = 0
    art_cited_20: int = 0
    art_cited_all: int = 0

class MostCitedArticles(BaseModel):
    """
    __Table vw_stat_cited_crosstab2__

    A view with rxCode counts derived from the fullbiblioxml table and the articles table
      for citing sources in one of the date ranges.
      
    """
    document_id: str = None
    countAll: int = 0
    count5: int = 0
    count10: int = 0
    count20: int = 0

class opasCentralDBMini(object):
    """
    This object should be used and then discarded on an endpoint by endpoint basis in any
      multiuser mode.
      
    Therefore, keeping session info in the object is ok,
    """
    def __init__(self, session_id=None, access_token=None, token_expires_time=None, username="NotLoggedIn", user=None):
        self.db = None
        self.connected = False
        #self.authenticated = False
        #self.session_id = session_id
        #self.access_token = access_token
        #self.user = None
        #self.sessionInfo = None
        
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
        except:
            # not open reopen it.
            status = False
        
        if status == False:
            #  not tunneled
            try:
                self.db = pymysql.connect(host=localsecrets.DBHOST, port=localsecrets.DBPORT, user=localsecrets.DBUSER, password=localsecrets.DBPW, database=localsecrets.DBNAME)
                logger.debug(f"Database opened by ({caller_name}) Specs: {localsecrets.DBNAME} for host {localsecrets.DBHOST},  user {localsecrets.DBUSER} port {localsecrets.DBPORT}")
                self.connected = True
            except Exception as e:
                err_str = f"opasDataUpdateStatDBError: Cannot connect to database {localsecrets.DBNAME} for host {localsecrets.DBHOST},  user {localsecrets.DBUSER} port {localsecrets.DBPORT} ({e})"
                print(err_str)
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
                else:
                    logger.debug(f"Database close request, but not open ({caller_name})")
                    
            except Exception as e:
                logger.error(f"opasDataUpdateStatDBError: caller: {caller_name} the db is not open ({e})")

        # make sure to mark the connection false in any case
        self.connected = False           

    def get_most_viewed_crosstab(self):
        """
         Using the opascentral api_docviews table data, as dynamically statistically aggregated into
           the view vw_stat_most_viewed return the most downloaded (viewed) documents
           
         Returns 0,[] if no rows are returned
         
         Supports the updates to Solr via solrXMLPEPWebload, used for view count queries.
           
        """
        ret_val = []
        row_count = 0
        # always make sure we have the right input value
        self.open_connection(caller_name="get_most_viewed_crosstab") # make sure connection is open
        
        if self.db is not None:
            cursor = self.db.cursor(pymysql.cursors.DictCursor)
            sql = """SELECT DISTINCTROW * FROM vw_stat_docviews_crosstab"""
            row_count = cursor.execute(sql)
            ret_val = cursor.fetchall() # returns empty list if no rows
            cursor.close()
        else:
            logger.fatal("Connection not available to database.")
        
        self.close_connection(caller_name="get_most_viewed_crosstab") # make sure connection is closed
        return row_count, ret_val

    def get_citation_counts(self) -> dict:
        """
         Using the opascentral vw_stat_cited_crosstab2 view, based on the api_biblioxml2 which is used to detect citations,
           return the cited counts for each art_id
           
           Primary view definition copied here for safe keeping.
           ----------------------
           vw_stat_cited_crosstab2
           ----------------------
           
           SELECT
           `r0`.`cited_document_id` AS `cited_document_id`,
           any_value (
           COALESCE ( `r1`.`count5`, 0 )) AS `count5`,
           any_value (
           COALESCE ( `r2`.`count10`, 0 )) AS `count10`,
           any_value (
           COALESCE ( `r3`.`count20`, 0 )) AS `count20`,
           any_value (
           COALESCE ( `r4`.`countAll`, 0 )) AS `countAll` 
           FROM
               (((((
                               SELECT DISTINCT
                                   `api_biblioxml2`.`art_id` AS `articleID`,
                                   `api_biblioxml2`.`bib_local_id` AS `internalID`,
                                   `api_biblioxml2`.`full_ref_xml` AS `fullReference`,
                                   `api_biblioxml2`.`bib_rx` AS `cited_document_id` 
                               FROM
                                   `api_biblioxml2` 
                                   ) `r0`
                               LEFT JOIN `vw_stat_cited_in_last_5_years2` `r1` ON ((
                                       `r1`.`cited_document_id` = `r0`.`cited_document_id` 
                                   )))
                           LEFT JOIN `vw_stat_cited_in_last_10_years2` `r2` ON ((
                                   `r2`.`cited_document_id` = `r0`.`cited_document_id` 
                               )))
                       LEFT JOIN `vw_stat_cited_in_last_20_years2` `r3` ON ((
                               `r3`.`cited_document_id` = `r0`.`cited_document_id` 
                           )))
                   LEFT JOIN `vw_stat_cited_in_all_years2` `r4` ON ((
                           `r4`.`cited_document_id` = `r0`.`cited_document_id` 
                       ))) 
           WHERE
               ((
                       `r0`.`cited_document_id` IS NOT NULL 
                       ) 
                   AND ( `r0`.`cited_document_id` <> 'None' ) 
                   AND (
                   substr( `r0`.`cited_document_id`, 1, 3 ) NOT IN ( 'ZBK', 'IPL', 'SE.', 'GW.' ))) 
           GROUP BY
               `r0`.`cited_document_id` 
           ORDER BY
               `countAll` DESC
           
        """
        citation_table = []
        print ("Collecting citation counts from cross-tab in biblio database...this will take a minute or two...")
        try:
            self.open_connection("get_citation_counts")
            # Get citation lookup table
            try:
                cursor = self.db.cursor(pymysql.cursors.DictCursor)
                # 2023-02-12 Watch out for Null and empty doc ids
                sql = """
                      SELECT cited_document_id, count5, count10, count20, countAll from vw_stat_cited_crosstab2 where cited_document_id is not Null and cited_document_id != ''; 
                      """
                success = cursor.execute(sql)
                if success:
                    citation_table = cursor.fetchall()
                    cursor.close()
                else:
                    logger.error("opasDataUpdateStatDBError: Cursor execution failed.  Can't fetch.")
                    
            except MemoryError as e:
                print(("Memory error loading table: {}".format(e)))
            except Exception as e:
                print(("Table Query Error: {}".format(e)))
            
            self.close_connection("get_citation_counts")
            
        except Exception as e:
            print(("Database Connect Error: {}".format(e)))
            citation_table["dummy"] = MostCitedArticles()
        
        return citation_table


#----------------------------------------------------------------------------------------
#  End OpasCentralDBMini
#----------------------------------------------------------------------------------------
def load_unified_article_stat():
    ocd =  opasCentralDBMini()
    # load most viewed data
    count, most_viewed = ocd.get_most_viewed_crosstab()
    # load citation data
    citation_table = ocd.get_citation_counts()

    # integrate data into article_stat
    for n in citation_table:
        try:
            doc_id = n.get("cited_document_id", None)
        except Exception as e:
            logger.error("opasDataUpdateStatLoadError: no document id")
        else:
            if doc_id:
                unified_article_stat[doc_id] = ArticleStat(
                    art_cited_5 = n.get("count5", 0), 
                    art_cited_10 = n.get("count10", 0), 
                    art_cited_20 = n.get("count20", 0), 
                    art_cited_all = n.get("countAll", 0)
                )
            else:
                logger.error(f"Doc ID Error: '{doc_id}'")
            
    for n in most_viewed:
        doc_id = n.get("document_id", None)
        if doc_id:
            try:
                unified_article_stat[doc_id].art_views_update = True
                unified_article_stat[doc_id].art_views_lastcalyear = n.get("lastcalyear", None)
                unified_article_stat[doc_id].art_views_last12mos = n.get("last12months", None) 
                unified_article_stat[doc_id].art_views_last6mos = n.get("last6months", None) 
                unified_article_stat[doc_id].art_views_last1mos = n.get("lastmonth", None)
                unified_article_stat[doc_id].art_views_lastweek = n.get("lastweek", None)
            except KeyError:
                unified_article_stat[doc_id] = ArticleStat()
                unified_article_stat[doc_id].art_views_update = True
                unified_article_stat[doc_id].art_views_lastcalyear = n.get("lastcalyear", None)
                unified_article_stat[doc_id].art_views_last12mos = n.get("last12months", None) 
                unified_article_stat[doc_id].art_views_last6mos = n.get("last6months", None) 
                unified_article_stat[doc_id].art_views_last1mos = n.get("lastmonth", None)
                unified_article_stat[doc_id].art_views_lastweek = n.get("lastweek", None)
        else:
            logger.error(f"Doc ID Error: '{doc_id}'")
                
def update_solr_stat_data(solrcon, all_records:bool=False):
    """
    Use in-place updates to update the views data
    """
    update_count = 0
    skipped_as_update_error = 0
    skipped_as_missing = 0
    item_count = len(unified_article_stat.items())
    remaining_count = item_count
    print (f"Merging up to {item_count} stat records into Solr Docs core records.")
    
    for key, art_stat in unified_article_stat.items():
        remaining_count -= 1
        if not key or "?" in key:
            print (f"Key Error (skipping): '{key}': {art_stat}")
            continue
            
        if all_records==False:
            if not art_stat.art_views_update:
                #print (f"Skipping {key} (No update)")
                continue
            elif art_stat.art_views_lastcalyear == \
                 art_stat.art_views_last12mos == \
                 art_stat.art_views_last6mos == \
                 art_stat.art_views_last1mos == \
                 art_stat.art_views_lastweek == 0:
                    #print (f"Skipping {key} (all 0 views)")
                    continue

        if remaining_count % 1000 == 0:
            print (f"...{remaining_count} records to go")
            
        # set only includes those with the desired update value > 0 
        parsed_id = ArticleID(art_id=key)
        doc_id = parsed_id.art_id
        found = False
        try:
            results = solrcon.search(q = f"art_id:{doc_id}")
            if results.raw_response["response"]["numFound"] > 0:
                found = True
            else: # TryAlternateID:
                results = solrcon.search(q = f"art_id:{parsed_id.alt_standard}")
                if results.raw_response["response"]["numFound"] == 1:  # only accept alternative if there's only one match (otherwise, not known which)
                    # odds are good this is what was cited.
                    found = True
                    logger.debug(f"Document ID {doc_id} not in Solr.  The correct ID seems to be {parsed_id.alt_standard}. Using that instead!")
                    doc_id = parsed_id.alt_standard
                else:
                    logger.debug(f"Document ID {doc_id} not in Solr.  No alternative ID found.")
                
        except Exception as e:
            logger.error(f"Issue finding Document ID {doc_id} in Solr...Exception: {e}")
            skipped_as_missing += 1
        else:
            if found:
                update_rec = False
                try:
                    result = results.raw_response["response"]["docs"][0]
                    solr_art_cited_5 = result.get("art_cited_5", 0)
                    solr_art_cited_10 = result.get("art_cited_10", 0)
                    solr_art_cited_20 = result.get("art_cited_20", 0)
                    solr_art_cited_all = result.get("art_cited_all", 0)
                    solr_art_cited_lastcalyear = result.get("art_cited_lastcalyear", 0)
                    solr_art_cited_last12mos = result.get("art_cited_last12mos", 0)
                    solr_art_cited_last6mos = result.get("art_cited_last6mos", 0)
                    solr_art_cited_last1mos = result.get("art_cited_last1mos", 0)
                    solr_art_cited_lastweek = result.get("art_cited_lastweek", 0)
                    if solr_art_cited_5 != art_stat.art_cited_5 or \
                       solr_art_cited_10 != art_stat.art_cited_10 or \
                       solr_art_cited_20 != art_stat.art_cited_20 or \
                       solr_art_cited_all != art_stat.art_cited_all or \
                       solr_art_cited_lastcalyear != art_stat.art_views_lastcalyear or \
                       solr_art_cited_last12mos != art_stat.art_views_last12mos or \
                       solr_art_cited_last6mos != art_stat.art_views_last6mos or \
                       solr_art_cited_last1mos != art_stat.art_views_last1mos or \
                       solr_art_cited_lastweek != art_stat.art_views_lastweek:
                        update_rec = True
                    else:
                        update_rec = False
                except Exception as e:
                    logger.error(f"...Updating stat for {doc_id} in Solr...Error: {e}.")
                    continue
                        
                if doc_id is not None and update_rec:
                    if all_records == False:
                        logger.info(f"...Updating stat for {doc_id} in Solr...{remaining_count} more to check. Views 12m:{art_stat.art_views_last12mos} 6m:{art_stat.art_views_last6mos} 1m:{art_stat.art_views_last1mos} 1w:{art_stat.art_views_lastweek}")
                    elif args.display_verbose:
                        logger.info(f"...Updating all stat for {doc_id} in Solr...{remaining_count} more to check. Views Yr:{art_stat.art_views_lastcalyear}")

                    upd_rec = {
                                "id":doc_id,
                                "art_id": doc_id,
                                "art_cited_5": art_stat.art_cited_5, 
                                "art_cited_10": art_stat.art_cited_10, 
                                "art_cited_20": art_stat.art_cited_20, 
                                "art_cited_all": art_stat.art_cited_all, 
                                "art_views_lastcalyear": art_stat.art_views_lastcalyear, 
                                "art_views_last12mos": art_stat.art_views_last12mos, 
                                "art_views_last6mos": art_stat.art_views_last6mos, 
                                "art_views_last1mos": art_stat.art_views_last1mos, 
                                "art_views_lastweek": art_stat.art_views_lastweek
                    }                    
        
                    try:
                        solrcon.add([upd_rec], fieldUpdates={
                                                             "art_cited_5": 'set',
                                                             "art_cited_10": 'set',
                                                             "art_cited_20": 'set',
                                                             "art_cited_all": 'set',
                                                             "art_views_lastcalyear": 'set',
                                                             "art_views_last12mos": 'set',
                                                             "art_views_last6mos": 'set',
                                                             "art_views_last1mos": 'set',
                                                             "art_views_lastweek": 'set'
                                                             })
        
                        #if all_records == False:
                            #if args.display_verbose:
                                #print (f"{doc_id} - Views Yr:{art_stat.art_views_lastcalyear} 12mos:{art_stat.art_views_last12mos} 6mos:{art_stat.art_views_last6mos} 1mo:{art_stat.art_views_last1mos} 1wk:{art_stat.art_views_lastweek}")
                            
                        if update_count > 0 and update_count % UPDATE_AFTER == 0:
                            solr_docs2.commit()
                            errStr = f"Updated {update_count} records with citation data"
                            print (errStr)
                            logger.info(errStr)
                        
                    except Exception as err:
                        errStr = f"opasDataUpdateStatUpdateError: Solr call exception for update on {doc_id}: {err}"
                        print (errStr)
                        skipped_as_update_error += 1
                        logger.error(errStr)
                    else:
                        update_count += 1
            else:
                errStr = (f"Document {doc_id} not in Solr...skipping")
                #print (errStr)
                logger.debug(errStr)
                if ".jpg" in errStr:
                    print (f"Todo: eliminate these jpgs from the table driving the stat {doc_id}")

    #  final commit
    try:
        solr_docs2.commit()
    except Exception as e:
        msg = f"opasDataUpdateStatUpdateError: Final commit error {e}"
        print(msg)
        logger.error(msg)

    print (f"Finished updating Solr stat with {update_count} article records updated; records skipped: {skipped_as_update_error }.")
    return update_count

if __name__ == "__main__":
    import argparse
    import pymysql
    global args
    
    parser = argparse.ArgumentParser() 
    parser.add_argument('--version', action='version',
                        version='%(prog)s {version}'.format(version=__version__))    
    parser.add_argument("--loglevel", "-l", dest="logLevel", default='ERROR',
                        help="Level at which events should be logged (DEBUG, INFO, WARNING, ERROR")
    parser.add_argument("-a", "--all", dest="all_records", default=False, action="store_true",
                        help="Update records with views and any citation data (takes significantly longer)")
    parser.add_argument("--verbose", action="store_true", dest="display_verbose", default=True,
                        help="Display status and operational timing info as load progresses.")
    
    args = parser.parse_args()
    logger.setLevel(args.logLevel)

    updates = 0
    SOLR_DOCS = "pepwebdocs"
    solrurl_docs = localsecrets.SOLRURL + SOLR_DOCS  
    if localsecrets.SOLRUSER is not None and localsecrets.SOLRPW is not None:
        solr_docs2 = pysolr.Solr(solrurl_docs, auth=(localsecrets.SOLRUSER, localsecrets.SOLRPW))
    else: #  no user and password needed
        solr_docs2 = pysolr.Solr(solrurl_docs)
    start_time = time.time()
    print (f"Solr URL used: {solrurl_docs}")
    try:
        print (f"Configuration used: {localsecrets.CONFIG}")
    except: # in case it's not set on AWS
        pass
        
    library_versions = {"pymysql": pymysql.__version__,
                        "pysolr": pysolr.__version__,
                       }
    print (f"Key Library Versions: {library_versions}")
    load_unified_article_stat()
    updates = update_solr_stat_data(solr_docs2, args.all_records)
    total_time = time.time() - start_time
    final_stat = f"{time.ctime()} Updated {updates} Solr records in {total_time} secs ({total_time/60} minutes))."
    print (final_stat)
        

