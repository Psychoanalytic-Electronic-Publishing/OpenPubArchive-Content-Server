#!/usr/bin/env python
# -*- coding: utf-8 -*-
# To run:
#     python3 updateSolrviewData
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2023, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2023.0509/v1.1.15"
__status__      = "Beta"

programNameShort = "opasDataUpdateStat"

print(
    f"""
    {programNameShort} - Program to update the view and citation stat fields in the pepwebdocs Solr database.
      
      By default, it only updates records which have views data.
        Views data needs to be updated when the database is moved to Production, since those are the REAL views for the DB.
        The citation data does not need to be reupdated, so you don't need --all (and not including it will save a lot
        of time)
      
      Use -h or --help for complete options.  Below are key ones.

      Use command line option --everything to add all citation and views data to pepwebdocs.
      (This takes significantly longer.)
        
         - The first stat run after a load should be with option --everything or --all (these are the same; "everything"
            might be clearer though, since it's two types of data rather than just the number of records)

         - Then, omit --all to update views daily
            - only records with views will update Solr
            - views data needs to be updated again when moved to Production, since those are the REAL views for the DB.
              The citation data does not need to be reupdated, so you don't need --all

         - Citations (include --all) only need be updated after non PEPCurrent data updates
         
      To limit the records to an art_id pattern, use --key pattern, e.g., --key PSYCHE\..*
      
      To limit the views records to after a date, use --since date, e.g., --since 2023-03-01
         
         For complete details, see:
          https://github.com/Psychoanalytic-Electronic-Publishing/OpenPubArchive-Content-Server/wiki/Loading-Data-into-OpenPubArchive

      The records added are controlled by the database views:
         vw_stat_docviews_crosstab
         vw_stat_cited_crosstab2
         
         Bad article ids, e.g., ref_rx in these tables will cause "article not found" warnings (in Solr)

    """
)

import sys
sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')

DATA_WITH_SUB_RECORDS = "GW.*|SE.*"
UPDATE_AFTER = 500
REMAINING_COUNT_INTERVAL = 1000

import logging
import re
import time
import pymysql
import pysolr
import localsecrets
from optparse import OptionParser

from pydantic import BaseModel
from datetime import datetime
from loggingDebugStream import log_everywhere_if
import opasSolrLoadSupport
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
        print ("Getting most viewed data...this may take a few minutes...")
        and_subset = ""
        if options.file_key:
            and_subset = f"WHERE document_id RLIKE '{options.file_key}'"

        if not options.all_records:
            if options.since_date:
                if options.file_key:
                    connector = "AND"
                else:
                    connector = "WHERE"
    
                and_subset = f" {connector} last_viewed >= '{options.since_date}'"
                
        if self.db is not None:
            try:
                cursor = self.db.cursor(pymysql.cursors.DictCursor)
                sql = f"""SELECT DISTINCTROW * FROM vw_stat_docviews_crosstab {and_subset}"""
                row_count = cursor.execute(sql)
                msg = f"{row_count} view records retrieved"
                log_everywhere_if(True, "info", msg)
                ret_val = cursor.fetchall() # returns empty list if no rows
                cursor.close()
            except Exception as e:
                log_everywhere_if(options.verbose, "error", f"RDS Database error: {e}")
        else:
            logger.fatal("Connection not available to database.")
        
        self.close_connection(caller_name="get_most_viewed_crosstab") # make sure connection is closed
        return row_count, ret_val

    def get_citation_counts(self) -> dict:
        """
         Using the opascentral vw_stat_cited_crosstab2 view, based on the api_biblioxml2 which
         is used to detect citations
         
         Return the cited counts for each art_id
         
        """
        citation_table = []
        print ("Collecting citation counts from cross-tab in biblio database...this may take a few minutes...")
        and_subset = ""
        if options.file_key:
            and_subset = f"AND cited_document_id RLIKE '{options.file_key}'"
        
        try:
            self.open_connection("get_citation_counts")
            # Get citation lookup table
            try:
                cursor = self.db.cursor(pymysql.cursors.DictCursor)
                # 2023-02-12 Watch out for Null and empty doc ids
                sql = f"""
                      SELECT cited_document_id, count5, count10, count20, countAll
                      from vw_stat_cited_crosstab2
                      where cited_document_id is not Null
                      AND cited_document_id != ''
                      {and_subset};
                      """
                success = cursor.execute(sql)
                if success:
                    citation_table = cursor.fetchall()
                    cursor.close()
                else:
                    logger.error("opasDataUpdateStatDBError: Cursor execution failed.  Can't fetch.")
                    
            except MemoryError as e:
                msg = "Memory error loading table: {}".format(e)
                log_everywhere_if(True, "error", msg)
                
            except Exception as e:
                msg = "Table Query Error: {}".format(e)
                log_everywhere_if(True, "error", msg)
            
            self.close_connection("get_citation_counts")
            
        except Exception as e:
            msg = "Database Connect Error: {}".format(e)
            log_everywhere_if(True, "error", msg)
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
    skipped_as_not_updated = 0
    skipped_as_special_case = 0
    item_count = len(unified_article_stat.items())
    remaining_count = item_count
    msg = f"Merging up to {item_count} stat records into Solr Docs core records."
    log_everywhere_if(True, "info", msg)

    articleHasBeenUpdated = {}
    
    for key, art_stat in unified_article_stat.items():
        remaining_count -= 1
        if not key or "?" in key:
            msg = f"Key Error (skipping): '{key}': {art_stat}"
            log_everywhere_if(True, "warning", msg)
            continue
            
        if not all_records: # not --all
            # if not doing all records, for optimum speed, we don't bother to update items with citation info only.  
            # Unless --all was specified, we just update those with view data, and skip if there are no views.           
            # When doing a full update, or a full rebuild, the stat run should include --all (or --everywhere), which will fill in 
            # the citation data..
            
            if not art_stat.art_views_update:
                #print (f"Skipping {key} (No update)")
                continue
            elif art_stat.art_views_lastcalyear == \
                 art_stat.art_views_last12mos == \
                 art_stat.art_views_last6mos == \
                 art_stat.art_views_last1mos == \
                 art_stat.art_views_lastweek == 0:
                    skipped_as_not_updated += 1
                    #print (f"Skipping {key} (all 0 views)")
                    continue

        if remaining_count % REMAINING_COUNT_INTERVAL == 0:
            msg = f"...{remaining_count} records to go (update count: {update_count})"
            log_everywhere_if(True, "info", msg)
            
        # set only includes those with the desired update value > 0 
        parsed_id = ArticleID(art_id=key)
        doc_id = parsed_id.art_id
        found = False
        try:
            results = solrcon.search(q = f"art_id:{doc_id}")
            if results.raw_response["response"]["numFound"] > 0:
                found = True
            else: # TryAlternateID:
                # try this 
                found_results, found_id = opasSolrLoadSupport.find_article_id(solrcon, parsed_id, verbose=options.display_verbose)
                if found_id:
                    results = found_results
                    doc_id = found_id
                    found = True
                else:
                    skipped_as_missing += 1
        except Exception as e:
            log_everywhere_if(options.display_verbose, "error", f"Issue when finding Document ID {doc_id} in Solr...Exception: {e}")
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
                    solr_art_views_lastcalyear = result.get("art_views_lastcalyear", 0)
                    solr_art_views_last12mos = result.get("art_views_last12mos", 0)
                    solr_art_views_last6mos = result.get("art_views_last6mos", 0)
                    solr_art_views_last1mos = result.get("art_views_last1mos", 0)
                    solr_art_views_lastweek = result.get("art_views_lastweek", 0)
                    if solr_art_cited_5 != art_stat.art_cited_5 or \
                       solr_art_cited_10 != art_stat.art_cited_10 or \
                       solr_art_cited_20 != art_stat.art_cited_20 or \
                       solr_art_cited_all != art_stat.art_cited_all or \
                       solr_art_views_lastcalyear != art_stat.art_views_lastcalyear or \
                       solr_art_views_last12mos != art_stat.art_views_last12mos or \
                       solr_art_views_last6mos != art_stat.art_views_last6mos or \
                       solr_art_views_last1mos != art_stat.art_views_last1mos or \
                       solr_art_views_lastweek != art_stat.art_views_lastweek:
                        update_rec = True
                    else:
                        update_rec = False
                except Exception as e:
                    logger.error(f"Update stat for {doc_id} in Solr...Error: {e}.")
                    skipped_as_update_error += 1
                    continue
                        
                if doc_id is not None and update_rec:
                    if re.match(DATA_WITH_SUB_RECORDS, doc_id):
                        # can't update GW/SE this way because they have subrecords
                        # if we want to track these in Solr, we need to do that during
                        # loading, or reload the whole record here.
                        skipped_as_special_case += 1
                        if skipped_as_special_case == 1 or skipped_as_special_case % 100 == 0:
                            msg = f"Skipped {DATA_WITH_SUB_RECORDS} documents with subrecords (e.g., {doc_id})"
                            log_everywhere_if(options.display_verbose, "warning", msg)
                    else:
                        if options.display_verbose:
                            if all_records == False:
                                print(f"Upd. solr stat {doc_id} {remaining_count} more to go. Vws 12m:{art_stat.art_views_last12mos} 6m:{art_stat.art_views_last6mos} 1m:{art_stat.art_views_last1mos} 1w:{art_stat.art_views_lastweek}")
                            else:
                                print(f"...{remaining_count} more to go (views/citations). Updated:{doc_id} Cited: {solr_art_cited_all} Vws 12m:{art_stat.art_views_last12mos}")

                        alreadyUpdated = doc_id in articleHasBeenUpdated

                        upd_rec = {
                                    "id":doc_id,
                                    "art_id": doc_id,
                                    "art_cited_5": art_stat.art_cited_5 if not alreadyUpdated else art_stat.art_cited_5 + solr_art_cited_5, 
                                    "art_cited_10": art_stat.art_cited_10 if not alreadyUpdated else art_stat.art_cited_10 + solr_art_cited_10,
                                    "art_cited_20": art_stat.art_cited_20 if not alreadyUpdated else art_stat.art_cited_20 + solr_art_cited_20,
                                    "art_cited_all": art_stat.art_cited_all if not alreadyUpdated else art_stat.art_cited_all + solr_art_cited_all,
                                    "art_views_lastcalyear": art_stat.art_views_lastcalyear if not alreadyUpdated else art_stat.art_views_lastcalyear + solr_art_views_lastcalyear,
                                    "art_views_last12mos": art_stat.art_views_last12mos if not alreadyUpdated else art_stat.art_views_last12mos + solr_art_views_last12mos,
                                    "art_views_last6mos": art_stat.art_views_last6mos if not alreadyUpdated else art_stat.art_views_last6mos + solr_art_views_last6mos,
                                    "art_views_last1mos": art_stat.art_views_last1mos if not alreadyUpdated else art_stat.art_views_last1mos + solr_art_views_last1mos,
                                    "art_views_lastweek": art_stat.art_views_lastweek if not alreadyUpdated else art_stat.art_views_lastweek + solr_art_views_lastweek
                        }             

                        if not alreadyUpdated:
                            articleHasBeenUpdated[doc_id] = True       
                
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
                                #if options.display_verbose:
                                    #print (f"{doc_id} - Views Yr:{art_stat.art_views_lastcalyear} 12mos:{art_stat.art_views_last12mos} 6mos:{art_stat.art_views_last6mos} 1mo:{art_stat.art_views_last1mos} 1wk:{art_stat.art_views_lastweek}")
                                
                            if update_count > 0 and update_count % UPDATE_AFTER == 0:
                                solr_docs2.commit()
                                infoStr = f"...Updated {update_count} records with citation data"
                                log_everywhere_if(options.display_verbose, "info", infoStr)
                            
                        except Exception as err:
                            errStr = f"Solr call exception for update on {doc_id}: {err}"
                            skipped_as_update_error += 1
                            log_everywhere_if(True, "error", errStr)
                        else:
                            update_count += 1
            else:
                msg = (f"Document {doc_id} not in Solr...skipping")
                log_everywhere_if(options.display_verbose, "warning", msg)
                if ".jpg" in msg or ".JPG" in msg:
                    msg = f"TODO: eliminate these jpgs from the table driving the stat {doc_id}"
                    log_everywhere_if(options.display_verbose, "warning", msg)

    #  final commit
    try:
        solr_docs2.commit()
    except Exception as e:
        msg = f"Exception in final commit {e}"
        print(msg)
        logger.error(msg)        

    print (f"Finished updating Solr stat. Article records updated: {update_count} skipped: {skipped_as_not_updated} errors: {skipped_as_update_error }.")
    return update_count

if __name__ == "__main__":
    import pymysql
    global options  # so the information can be used in support functions
    options = None
    
    description = """Collect citation and view counts from the RDS database and copy them to Solr"""
    parser = OptionParser(usage="%prog [options]", version=f"%prog ver. {__version__}", description=description)

    #parser = argparse.ArgumentParser() 
    parser.add_option("--loglevel", "-l", dest="logLevel", default='ERROR',
                        help="Level at which events should be logged (DEBUG, INFO, WARNING, ERROR")
    parser.add_option("-a", "--all", "--everything", dest="all_records", default=False, action="store_true",
                        help="Include citation data update with the standard views update (can take significantly longer)")
    parser.add_option("--verbose", action="store_true", dest="display_verbose", default=False,
                        help="Display status and operational timing info as load progresses.")
    parser.add_option("--key", dest="file_key", default=None,
                        help="Key for a single file to load, e.g., AIM.076.0269A.")
    parser.add_option("--since", dest="since_date", default=None,
                        help="If only doing view records, you can use this to update only records updated after this date")
    
    (options, args) = parser.parse_args()

    if options.file_key:
        print (f"Limit selected to file_key: {options.file_key}")

    logger.setLevel(options.logLevel)

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
    updates = update_solr_stat_data(solr_docs2, options.all_records)
    total_time = time.time() - start_time
    final_stat = f"{time.ctime()} Updated {updates} Solr records in {total_time:0,.2f} secs ({total_time/60:0,.2f} minutes))."
    print (final_stat)
        

