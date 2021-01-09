#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
opasCentralDBLib

This library is supports the main functionality of the OPAS Central Database

The database has use and usage information.

OPASCENTRAL TABLES (and Views) CURRENTLY USED:
   vw_stat_most_viewed (depends on vw_stat_docviews_crosstab,
                                   table articles)

   vw_stat_docviews_crosstab (depends on api_docviews,
                                         vw_stat_docviews_lastweek,
                                         vw_stat_docviews_lastmonth,
                                         vw_stat_docviews_lastsixmonths,
                                         vw_stat_docviews_lastcalyear,
                                         vw_stat_docviews_last12months
                                         )

   vw_stat_cited_crosstab (depends on fullbiblioxml - table copied from PEP XML Processing db pepa1db
                           vw_stat_cited_in_last_5_years,
                           vw_stat_cited_in_last_10_years,
                           vw_stat_cited_in_last_20_years,
                           vw_stat_cited_in_all_years
                           )                                        
    
    vw_api_productbase (this is the ISSN table from pepa1vdb used during processing)
    
    vw_latest_session_activity (list of sessions with date from table api_session_endpoints)
    
    Used in generators:
    
      vw_stat_cited_crosstab_with_details (depeds on vw_stat_cited_crosstab + articles)
      vw_stat_most_viewed

"""
#2019.0708.1 - Python 3.7 compatible. 
#2019.1110.1 - Updates for database view/table naming cleanup
#2020.0426.1 - Updates to ensure doc tests working, a couple of parameters changed names
#2020.0530.1 - Fixed doc tests for termindex, they were looking at number of terms rather than term counts

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2020-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2020.0530.1"
__status__      = "Development"

import sys
import re
# import fnmatch

# import os.path
from contextlib import closing

sys.path.append('../libs')
sys.path.append('../config')

from fastapi import Depends

import opasConfig
from opasConfig import normalize_val # use short form everywhere

import localsecrets
# from localsecrets import DBHOST, DBUSER, DBPW, DBNAME

import logging
logger = logging.getLogger(__name__)
import starlette.status as httpCodes

import datetime as dtime
from datetime import datetime # , timedelta
import time

# import secrets
# from pydantic import BaseModel
from passlib.context import CryptContext
# from pydantic import ValidationError

import pymysql
import jwt
import json

#import opasAuthBasic
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

import requests
import xml.etree.ElementTree as ET

import models

# All opasCentral Database Models here
import modelsOpasCentralPydantic
from modelsOpasCentralPydantic import User, UserInDB
#from models import SessionInfo

DEFAULTSESSIONLENGTH = 1800 # seconds (timeout)
API_STATUS_SUCCESS = "Success"
API_ENDPOINT_METHOD_GET = "get"
API_ENDPOINT_METHOD_PUT = "put"
API_ENDPOINT_METHOD_POST = "post"
API_ENDPOINT_METHOD_DELETE = "delete"

# ###############################################################
# API SYMBOLIC ENDPOINTS MUST MATCH API_ENDPOINTS TABLE IN DB!!!!
# ###############################################################
API_LOGIN = 1	        # /Login/
API_LOGIN_STATUS = 2	#/License/Status/Login/
API_LOGOUT = 3      	# /Logout/
API_ALERTS = 6
API_REPORTS = 7
API_OPENAPISPEC = 8     # /Api/Openapispec
API_LIVEDOC = 9         # /Api/Livedoc
API_METADATA_BANNERS = 10	#/Metadata/Banners/
API_METADATA_BANNERS_FOR_PEPCODE = 11	#/Metadata/Banners/{pepcode}/
API_METADATA_SOURCEINFO = 12	#/Metadata/{sourceType}/
API_METADATA_SOURCEINFO_FOR_PEPCODE = 13	#/Metadata/{sourceType}/{pepCode}/
API_METADATA_VOLUME_INDEX = 14	#/Metadata/Volumes/{pepCode}/
API_METADATA_CONTENTS = 15	#/Metadata/Contents/{pepCode}/
API_METADATA_CONTENTS_FOR_VOL = 16	#/Metadata/Contents/{pepCode}/{pepVol}/
API_METADATA_BOOKS = 17	#/Metadata/Contents/Books/{bookBaseDocumentID}/
API_AUTHORS_INDEX = 20	#/Authors/Index/{authNamePartial}/
API_AUTHORS_PUBLICATIONS = 21	#/Authors/Publications/{authNamePartial}/
API_DOCUMENTS_ABSTRACTS = 30	#/Documents/Abstracts/{documentID}/
API_DOCUMENTS = 31	#/Documents/{documentID}/
API_DOCUMENTS_PDF = 32	#/Documents/Downloads/PDF/{documentID}/
API_DOCUMENTS_PDFORIG = 33	#/Documents/Downloads/PDFORIG/{documentID}/
API_DOCUMENTS_EPUB = 35	#/Documents/Downloads/PDF/{documentID}/
API_DOCUMENTS_HTML = 36	#/Documents/Downloads/HTML/{documentID}/
API_DOCUMENTS_IMAGE = 37	#/Documents/Downloads/Images/{imageID}/
API_DOCUMENTS_CONCORDANCE = 38	    #/Documents/Paragraph/Concordance/
API_DATABASE_SEARCHANALYSIS_FOR_TERMS = 40	#/Database/SearchAnalysis/{searchTerms}/
API_DATABASE_SEARCH = 41	#/Database/Search/
API_DATABASE_WHATSNEW = 42	#/Database/WhatsNew/
API_DATABASE_MOSTCITED = 43	#/Database/MostCited/
API_DATABASE_MOSTVIEWED = 44	#/Database/MostViewed/ (Logged only CSV downloads)
API_DATABASE_SEARCHANALYSIS = 45	#/Database/SearchAnalysis/
API_DATABASE_ADVANCEDSEARCH = 46	
API_DATABASE_TERMCOUNTS = 47
API_DATABASE_GLOSSARY_SEARCH = 48	#/Database/Search/
API_DATABASE_EXTENDEDSEARCH = 49
API_DATABASE_SEARCHTERMLIST = 50
API_DATABASE_CLIENT_CONFIGURATION = 51 # /Client/Configuration



#def verifyAccessToken(session_id, username, access_token):
    #return pwd_context.verify(session_id+username, access_token)
    
def verify_password(plain_password, hashed_password):
    """
    >>> verify_password("secret", get_password_hash("secret"))
    True

    >>> verify_password("temporaryLover", '$2b$12$dy27eHxQoeekTMQIlofzvekWPr1rgrGp1fmXbWcQwCQynFkqvDH62')
    True
    
    >>> verify_password("temporaryLover", '$2b$12$0VH2W6CPxJdARmEcVQ7S9.FWk.xC41KdwN1e5XS2wuhbPYNRCFrmy')
    True
    
    >>> verify_password("pakistan", '$2b$12$VRLAkonDGCEuavaSotvbhOf.bVV0GDNysja.cHBFrrYHZw3e2vV7C')
    True

    >>> verify_password("pakistan", '$2b$12$z7F1BD8NhgcuBq090omf1.PfmP6obAaFN0QGyU1n/Gqv2oUvU9CGy')
    False

    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """
    Returns the hashed password that's stored
    >>> get_password_hash("doogie")
    '...'
    """
    return pwd_context.hash(password)

class SourceInfoDB(object):
    def __init__(self):
        self.sourceData = {}
        ocd = opasCentralDB()
        recs = ocd.get_productbase_data()
        for n in recs:
            try:
                self.sourceData[n["pepsrccode"]] = n
            except KeyError as e:
                logger.error("Missing Source Code Value in %s" % n)

    def lookupSourceCode(self, sourceCode):
        """
        Returns the dictionary entry for the source code or None
          if it doesn't exist.
        """
        dbEntry = self.sourceData.get(sourceCode, None)
        retVal = dbEntry
        return retVal

class opasCentralDB(object):
    """
    This object should be used and then discarded on an endpoint by endpoint basis in any
      multiuser mode.
      
    Therefore, keeping session info in the object is ok,
    
    >>> import secrets
    >>> ocd = opasCentralDB()
    >>> random_session_id = secrets.token_urlsafe(16)
    >>> success, session_info = ocd.save_session(session_id=random_session_id)
    >>> session_info.authenticated
    False
    >>> ocd.record_session_endpoint(session_info=session_info, api_endpoint_id=API_AUTHORS_INDEX, item_of_interest="IJP.001.0001A", status_message="Testing")
    1
    >>> ocd.end_session(session_info.session_id)
    True

    # don't delete, do it manually
    > ocd.delete_session(session_id=random_session_id)
    True
    """
    def __init__(self, session_id=None, access_token=None, token_expires_time=None, username=opasConfig.USER_NOT_LOGGED_IN_NAME, user=None):
        self.db = None
        self.connected = False
        # self.authenticated = False
        self.session_id = session_id # deprecate?
        # self.user = None
        # self.sessionInfo = None
        
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
        except:
            # not open reopen it.
            try:
                self.db = pymysql.connect(host=localsecrets.DBHOST, port=localsecrets.DBPORT, user=localsecrets.DBUSER, password=localsecrets.DBPW, database=localsecrets.DBNAME)
                logger.debug(f"Database opened by ({caller_name}) Specs: {localsecrets.DBNAME} for host {localsecrets.DBHOST},  user {localsecrets.DBUSER} port {localsecrets.DBPORT}")
                self.connected = True
            except Exception as e:
                logger.warning(f"Database connection not opened ({caller_name}) ({e})")
                # status = False
        
        return self.connected

    def close_connection(self, caller_name=""):
        if self.db is not None:
            try:
                if self.db.open:
                    self.db.close()
                    self.db = None
                    logger.debug(f"Database closed by ({caller_name})")
                else:
                    logger.warning(f"Database close request, but not open ({caller_name})")
                    
            except Exception as e:
                logger.error(f"caller: {caller_name} the db is not open ({e})")

        # make sure to mark the connection false in any case
        self.connected = False           

    def end_session(self, session_id, session_end=datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')):
        """
        End the session
        
        Tested in main instance docstring
        """
        ret_val = None
        self.open_connection(caller_name="end_session") # make sure connection is open
        if self.db is not None:
            cursor = self.db.cursor()
            sql = """UPDATE api_sessions
                     SET session_end = %s
                     WHERE session_id = %s
                  """
            success = cursor.execute(sql,
                                     (session_end,
                                      session_id
                                      )                                     
                                    )
            self.db.commit()
            cursor.close()
            if success:
                ret_val = True
            else:
                logger.warning(f"Could not record close session per token={sessionToken} in DB")
                ret_val = False

        self.close_connection(caller_name="end_session") # make sure connection is closed
        return ret_val

    def get_productbase_data(self):
        """
        Load the journal book and video product data
        """
        ret_val = {}
        self.open_connection(caller_name="get_productbase_data") # make sure connection is open
        if self.db is not None:
            curs = self.db.cursor(pymysql.cursors.DictCursor)
            sql = "SELECT * from vw_api_sourceinfodb where active=1;"
            row_count = curs.execute(sql)
            if row_count:
                sourceData = curs.fetchall()
                ret_val = sourceData
        else:
            logger.fatal("Connection not available to database.")
        self.close_connection(caller_name="get_productbase_data") # make sure connection is closed
        return ret_val
        
    def get_article_year(self, doc_id):
        """
        Load the article data for a document id
        """
        ret_val = None
        self.open_connection(caller_name="get_productbase_data") # make sure connection is open
        if self.db is not None:
            curs = self.db.cursor(pymysql.cursors.DictCursor)
            sql = f"SELECT art_year from api_articles where art_id='{doc_id}';"
            row_count = curs.execute(sql)
            if row_count:
                sourceData = curs.fetchall()
                ret_val = sourceData[0]["art_year"]
        else:
            logger.fatal("Connection not available to database.")

        self.close_connection(caller_name="get_productbase_data") # make sure connection is closed
        return ret_val
        
    def most_viewed_generator( self,
                               publication_period: int=5,  # Number of publication years to include (counting back from current year, 0 means current year)
                               viewperiod: int=4,          # used here for sort and limiting viewcount results (more_than_clause)
                               viewcount: int=None,        # cutoff at this minimum number of views for viewperiod column
                               author: str=None,
                               title: str=None,
                               source_name: str=None,
                               source_code: str=None, 
                               source_type: str="journals", # 'journal', 'book', 'videostream'} standard vals, can abbrev to 1 char or more
                               select_clause: str=opasConfig.VIEW_MOSTVIEWED_DOWNLOAD_COLUMNS, 
                               limit: int=None,
                               offset=0,
                               sort=None, #  can be None (default sort), False (no sort) or a column name + ASC || DESC
                               session_info=None
                               ):
        """
        Return records which are the most viewed for the viewperiod
           restricted to documents published in the publication_period (prev years)
           
        Reinstated here because equivalent from Solr is too slow when fetching the whole set.

           ---------------------
           view_stat_most_viewed
           ---------------------
            SELECT
                `vw_stat_docviews_crosstab`.`document_id` AS `document_id`,
                `vw_stat_docviews_crosstab`.`last_viewed` AS `last_viewed`,
                COALESCE ( `vw_stat_docviews_crosstab`.`lastweek`, 0 ) AS `lastweek`,
                COALESCE ( `vw_stat_docviews_crosstab`.`lastmonth`, 0 ) AS `lastmonth`,
                COALESCE ( `vw_stat_docviews_crosstab`.`last6months`, 0 ) AS `last6months`,
                COALESCE ( `vw_stat_docviews_crosstab`.`last12months`, 0 ) AS `last12months`,
                COALESCE ( `vw_stat_docviews_crosstab`.`lastcalyear`, 0 ) AS `lastcalyear`,
                `api_articles`.`art_auth_citation` AS `hdgauthor`,
                `api_articles`.`art_title` AS `hdgtitle`,
                `api_articles`.`src_title_abbr` AS `srctitleseries`,
                `api_articles`.`bk_publisher` AS `publisher`,
                `api_articles`.`src_code` AS `jrnlcode`,
                `api_articles`.`art_year` AS `pubyear`,
                `api_articles`.`art_vol` AS `vol`,
                `api_articles`.`art_pgrg` AS `pgrg`,
                `api_productbase`.`pep_class` AS `source_type`,
                `api_articles`.`preserve` AS `preserve`,
                `api_articles`.`filename` AS `filename`,
                `api_articles`.`bk_title` AS `bktitle`,
                `api_articles`.`bk_info_xml` AS `bk_info_xml`,
                `api_articles`.`art_citeas_xml` AS `xmlref`,
                `api_articles`.`art_citeas_text` AS `textref`,
                `api_articles`.`art_auth_mast` AS `authorMast`,
                `api_articles`.`art_issue` AS `issue`,
                `api_articles`.`last_update` AS `last_update` 
            FROM
            (  (
                `vw_stat_docviews_crosstab`
                   JOIN `api_articles` ON ((
                           `api_articles`.`art_id` = `vw_stat_docviews_crosstab`.`document_id` ))
                )
               LEFT JOIN `api_productbase` ON ((
                   `api_articles`.`src_code` = `api_productbase`.`pepcode` 
                ))
            )

            viewperiod = 0: lastcalendaryear
                         1: lastweek
                         2: lastmonth
                         3: last6months
                         4: last12months                                
                         
         
         Using the opascentral api_docviews table data, as dynamically statistically aggregated into
           the view vw_stat_most_viewed return the most downloaded (viewed) Documents
           
         1) Using documents published in the last 5, 10, 20, or all years.
            Viewperiod takes an int and covers these or any other period (now - viewPeriod years).
         2) Filtering videos, journals, books, or all content.  source_type filters this.
            Can be: "journals", "books", "videos", or "all" (default)
         3) Optionally filter for author, title, or specific journal.
            Per whatever the caller specifies in parameters.
         4) show views in last 7 days, last month, last 6 months, last calendar year.
            This function returns them all.
         
        """
        self.open_connection(caller_name="get_most_viewed_table") # make sure connection is open
        # get selected view_col_name used for sort and limiting results (more_than_clause)
        view_col_name = opasConfig.VALS_VIEWPERIODDICT_SQLFIELDS.get(viewperiod, "last12months")

        if limit is not None:
            limit_clause = f"LIMIT {offset}, {limit}"
        else:
            limit_clause = ""
            
        if self.db != None:
            if sort is None or sort == True:
                sort_by_clause = f" ORDER BY {view_col_name} DESC"
            elif sort == False:
                sort_by_clause = ""
            else:
                sort_by_clause = f"ORDER BY {sort}"
            
            if publication_period is not None:
                if str(publication_period).upper() == "ALL" or str(publication_period).upper()=="ALLTIME":
                    publication_period = 1000 # should cover most/all time of published writings!
                pub_year_clause = f" AND `pubyear` >= YEAR(NOW()) - {publication_period}"  
            else:
                pub_year_clause = ""

            if source_code is not None:
                source_code_clause = f" AND source_code = '{source_code}'" 
            else:
                source_code_clause = ""

            if source_name is not None:
                source_name = re.sub("[^\.]\*", ".*", source_name, flags=re.IGNORECASE)
                journal_clause = f" AND srctitleseries rlike '{source_name}'" 
            else:
                journal_clause = ""
            
            if source_type == "journals":
                doc_type_clause = f" AND source_code NOT IN {opasConfig.ALL_EXCEPT_JOURNAL_CODES}" 
            elif source_type == "books":
                doc_type_clause = f" AND source_code IN {opasConfig.BOOK_CODES_ALL}"
            elif source_type == "videos":
                doc_type_clause = f" AND source_code IN {opasConfig.VIDOSTREAM_CODES_ALL}"
            else:
                doc_type_clause = ""  # everything

            if author is not None:
                author = re.sub("[^\.]\*", ".*", author, flags=re.IGNORECASE)
                author_clause = f" AND hdgauthor rlike {author}"
            else:
                author_clause = ""
                
            if title is not None:
                # glob to re pattern
                # title = re.sub("[^\.]\*", ".*", title, flags=re.IGNORECASE)
                title = re.sub("[^\.]\*", ".*", title, flags=re.IGNORECASE)
                title_clause = f" AND hdgtitle rlike '{title}'"
            else:
                title_clause = ""

            if viewcount is not None:
                more_than_clause = f" AND {view_col_name} > {viewcount}"
            else:
                more_than_clause = ""
            
            # select_clause = "textref, lastweek, lastmonth, last6months, last12months, lastcalyear"
            # Note that WHERE 1 = 1 is used since clauses all start with AND
            sql = f"""SELECT {select_clause} 
                      FROM vw_stat_most_viewed
                      WHERE 1 = 1
                      {doc_type_clause}
                      {author_clause}
                      {more_than_clause}
                      {title_clause}
                      {source_code_clause}
                      {journal_clause}
                      {pub_year_clause}
                      {sort_by_clause}
                      {limit_clause}
                    """
            cursor = self.db.cursor(pymysql.cursors.DictCursor)
            row_count = cursor.execute(sql)
            for row in cursor:
                yield row
                
        self.close_connection(caller_name="get_most_viewed_table") # make sure connection is closed

    def SQLSelectGenerator(self, sql):
        #execute a select query and return results as a generator
        #error handling code removed
        self.open_connection(caller_name="SQLSelectGenerator") # make sure connection is open
        cursor = self.db.cursor(pymysql.cursors.DictCursor)
        cursor.execute(sql)
   
        for row in cursor:
            yield row    

        self.close_connection(caller_name="SQLSelectGenerator") # make sure connection is open
    
    def most_cited_generator( self,
                              publication_period = None, # Limit the considered pubs to only those published in these years
                              cited_in_period:str=None,  # Has to be cited more than this number of times, a large nbr speeds the query
                              citecount: int=None,              
                              author: str=None,
                              title: str=None,
                              source_name: str=None,  
                              source_code: str=None,
                              source_type: str=None,
                              select_clause: str=opasConfig.VIEW_MOSTCITED_DOWNLOAD_COLUMNS, 
                              limit: int=None,
                              offset: int=0,
                              sort=None #  can be None (default sort), False (no sort) or a column name + ASC || DESC
                              ):
        """
        Return records which are the most cited for the cited_in_period
           restricted to documents published in the publication_period (prev years)

        Reinstated because downloading from Solr is too slow!
         
        ------------------------------------
         vw_stat_cited_crosstab_with_details
        ------------------------------------
         
         SELECT
            `vw_stat_cited_crosstab`.`cited_document_id` AS `cited_document_id`,
            `vw_stat_cited_crosstab`.`count5` AS `count5`,
            `vw_stat_cited_crosstab`.`count10` AS `count10`,
            `vw_stat_cited_crosstab`.`count20` AS `count20`,
            `vw_stat_cited_crosstab`.`countAll` AS `countAll`,
            `api_articles`.`art_auth_citation` AS `hdgauthor`,
            `api_articles`.`art_title` AS `hdgtitle`,
            `api_articles`.`src_title_abbr` AS `srctitleseries`,
            `api_articles`.`src_code` AS `source_code`,
            `api_articles`.`art_year` AS `year`,
            `api_articles`.`art_vol` AS `vol`,
            `api_articles`.`art_pgrg` AS `pgrg`,
            `api_articles`.`art_id` AS `art_id`,
            `api_articles`.`art_citeas_text` AS `art_citeas_text` 
         FROM
            (
                `vw_stat_cited_crosstab`
                JOIN `api_articles` ON ((
                        `vw_stat_cited_crosstab`.`cited_document_id` = `api_articles`.`art_id` 
                    ))) 
         ORDER BY
            `vw_stat_cited_crosstab`.`countAll` DESC
         
        """
        self.open_connection(caller_name="most_cited_generator") # make sure connection is open
        cited_in_period = opasConfig.normalize_val(cited_in_period, opasConfig.VALS_YEAROPTIONS, default='ALL')
        
        if limit is not None:
            limit_clause = f"LIMIT {offset}, {limit}"
        else:
            limit_clause = ""
            
        if self.db != None:
            if sort is None or sort == True:
                sort_by_clause = f"ORDER BY count{cited_in_period} DESC"
            elif sort == False:
                sort_by_clause = ""
            else:
                sort_by_clause = f"ORDER BY {sort}"
        
            
            start_year = dtime.date.today().year
            if publication_period == "All":
                publication_period = dtime.date.today().year

            if publication_period is None:
                start_year = None
            else:
                start_year -= publication_period
                start_year = f">{start_year}"
                
            #TODO which one, before code, or after code?
            if publication_period is not None:
                pub_year_clause = f" AND `year` >= YEAR(NOW()) - {publication_period}"  # consider only the past viewPeriod years
            else:
                pub_year_clause = ""
            
            if source_name is not None:
                source_name = re.sub("[^\.]\*", ".*", source_name, flags=re.IGNORECASE)
                journal_clause = f" AND srctitleseries rlike '{source_name}'" 
            else:
                journal_clause = ""

            if source_code is not None:
                source_code_clause = f" AND source_code = '{source_code}'" 
            else:
                source_code_clause = ""

            if source_type == "journals":
                doc_type_clause = f" AND source_code NOT IN {opasConfig.ALL_EXCEPT_JOURNAL_CODES}" 
            elif source_type == "books":
                doc_type_clause = f" AND source_code IN {opasConfig.BOOK_CODES_ALL}"
            elif source_type == "videos":
                doc_type_clause = f" AND source_code IN {opasConfig.VIDOSTREAM_CODES_ALL}"
            else:
                doc_type_clause = ""  # everything

            if author is not None:
                # author = fnmatch.translate(author)
                author = re.sub("[^\.]\*", ".*", author, flags=re.IGNORECASE)
                author_clause = f" AND hdgauthor rlike '{author}'"
            else:
                author_clause = ""
                
            if title is not None:
                # glob to re pattern
                title = re.sub("[^\.]\*", ".*", title, flags=re.IGNORECASE)
                # title = fnmatch.translate(title)
                title_clause = f" AND hdgtitle rlike '{title}'"
            else:
                title_clause = ""

            if citecount is not None:
                more_than_clause = f" AND count{cited_in_period} > {citecount}"
            else:
                more_than_clause = ""
                
            # Note that WHERE 1 = 1 is used since clauses all start with AND
            sql = f"""SELECT {select_clause} 
                      FROM vw_stat_cited_crosstab_with_details
                      WHERE 1 = 1
                      {doc_type_clause}
                      {author_clause}
                      {more_than_clause}
                      {title_clause}
                      {journal_clause}
                      {pub_year_clause}
                      {sort_by_clause}
                      {limit_clause}
                    """

            cursor = self.db.cursor(pymysql.cursors.DictCursor)
            row_count = cursor.execute(sql)
            for row in cursor:
                yield row
        
        self.close_connection(caller_name="most_cited_generator") # make sure connection is closed

    def get_citation_counts(self) -> dict:
        """
         Using the opascentral vw_stat_cited_crosstab view, based on the api_biblioxml which is used to detect citations,
           return the cited counts for each art_id
           
           Primary view definition copied here for safe keeping.
           ----------------------
           vw_stat_cited_crosstab
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
                                   `api_biblioxml`.`art_id` AS `articleID`,
                                   `api_biblioxml`.`bib_local_id` AS `internalID`,
                                   `api_biblioxml`.`full_ref_xml` AS `fullReference`,
                                   `api_biblioxml`.`bib_rx` AS `cited_document_id` 
                               FROM
                                   `api_biblioxml` 
                                   ) `r0`
                               LEFT JOIN `vw_stat_cited_in_last_5_years` `r1` ON ((
                                       `r1`.`cited_document_id` = `r0`.`cited_document_id` 
                                   )))
                           LEFT JOIN `vw_stat_cited_in_last_10_years` `r2` ON ((
                                   `r2`.`cited_document_id` = `r0`.`cited_document_id` 
                               )))
                       LEFT JOIN `vw_stat_cited_in_last_20_years` `r3` ON ((
                               `r3`.`cited_document_id` = `r0`.`cited_document_id` 
                           )))
                   LEFT JOIN `vw_stat_cited_in_all_years` `r4` ON ((
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
            self.open_connection("collect_citation_counts")
            # Get citation lookup table
            try:
                cursor = self.db.cursor(pymysql.cursors.DictCursor)
                sql = """
                      SELECT cited_document_id, count5, count10, count20, countAll from vw_stat_cited_crosstab; 
                      """
                success = cursor.execute(sql)
                if success:
                    citation_table = cursor.fetchall()
                    cursor.close()
                else:
                    logger.error("Cursor execution failed.  Can't fetch.")
                    
            except MemoryError as e:
                print(("Memory error loading table: {}".format(e)))
            except Exception as e:
                print(("Table Query Error: {}".format(e)))
            
            self.close_connection("collect_citation_counts")
            
        except Exception as e:
            print(("Database Connect Error: {}".format(e)))
            citation_table["dummy"] = MostCitedArticles()
        
        return citation_table

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
        
        self.close_connection(caller_name="get_most_downloaded_crosstab") # make sure connection is closed
        return row_count, ret_val

    def get_select_count(self, sqlSelect: str):
        """
        Generic retrieval from database, just the count
        
        >>> ocd = opasCentralDB()
        >>> count = ocd.get_select_count(sqlSelect="SELECT * from vw_reports_user_searches WHERE global_uid = 'nrs';")
        >>> count > 1000
        True
        
        """
        self.open_connection(caller_name="get_select_count") # make sure connection is open
        ret_val = None

        sqlSelect = re.sub("SELECT .+? FROM", "SELECT COUNT(*) FROM", sqlSelect, count=1, flags=re.IGNORECASE)
        try:
            if self.db is not None:
                curs = self.db.cursor(pymysql.cursors.Cursor)
                curs.execute(sqlSelect)
                row = curs.fetchall()
                ret_val = row[0][0]
        except Exception as e:
            logger.warning("Can't retrieve count.")
            ret_val = 0
            
        self.close_connection(caller_name="get_select_count") # make sure connection is closed

        # return session model object
        return ret_val # None or Session Object

               
    def get_select_as_list_of_dicts(self, sqlSelect: str):
        """
        Generic retrieval from database, into dict
        
        >>> ocd = opasCentralDB()
        >>> records = ocd.get_select_as_list_of_dicts(sqlSelect="SELECT * from vw_reports_session_activity WHERE global_uid = 'nrs';")
        >>> len(records) > 1
        True

        """
        self.open_connection(caller_name="get_selection_as_list_of_dicts") # make sure connection is open
        ret_val = None
        if self.db is not None:
            curs = self.db.cursor(pymysql.cursors.DictCursor)
            curs.execute(sqlSelect)
            ret_val = [models.ReportListItem(row=row) for row in curs.fetchall()]
            
        self.close_connection(caller_name="get_selection_as_list_of_dicts") # make sure connection is closed

        # return session model object
        return ret_val # None or Session Object

    def get_min_max_volumes(self, source_code):
        sel = f"""
                SELECT `api_articles`.`src_code` AS `src_code`,
                       min( `api_articles`.`art_vol` ) AS `min`,
                       max( `api_articles`.`art_vol` ) AS `max` 
                FROM
                    `api_articles`
                WHERE src_code = '{source_code}'
                GROUP BY
                    `api_articles`.`src_code`
		"""

        self.open_connection(caller_name="get_min_max_volumes") # make sure connection is open
        ret_val = None
        if self.db is not None:
            curs = self.db.cursor(pymysql.cursors.DictCursor)
            curs.execute(sel)
            ret_val = curs.fetchall()

        self.close_connection(caller_name="get_min_max_volumes") # make sure connection is closed

        try:
            ret_val = ret_val[0]
            ret_val["infosource"] = "volumes_min_max"
        except Exception as e:
            ret_val = None
            
        return ret_val
        
    def get_select_as_list(self, sqlSelect: str):
        """
        Generic retrieval from database, into dict
        
        >>> ocd = opasCentralDB()
        >>> records = ocd.get_select_as_list(sqlSelect="SELECT * from vw_reports_session_activity WHERE global_uid = 'nrs';")
        >>> len(records) > 1
        True

        """
        self.open_connection(caller_name="get_selection_as_list") # make sure connection is open
        ret_val = None
        if self.db is not None:
            curs = self.db.cursor(pymysql.cursors.Cursor)
            curs.execute(sqlSelect)
            ret_val = curs.fetchall()
            
        self.close_connection(caller_name="get_selection_as_list") # make sure connection is closed

        # return session model object
        return ret_val # None or Session Object

    def get_session_from_db(self, session_id):
        """
        Get the session record info for session sessionID
        
        Tested in main instance docstring
        """
        from models import SessionInfo # do this here to avoid circularity
        self.open_connection(caller_name="get_session_from_db") # make sure connection is open
        ret_val = None
        if self.db is not None:
            curs = self.db.cursor(pymysql.cursors.DictCursor)
            # now insert the session
            sql = f"SELECT * FROM api_sessions WHERE session_id = '{session_id}'";
            res = curs.execute(sql)
            if res == 1:
                session = curs.fetchone()
                try:
                    if session["username"] is None:
                        session["username"] = opasConfig.USER_NOT_LOGGED_IN_NAME
                except Exception as e:
                    session["username"] = opasConfig.USER_NOT_LOGGED_IN_NAME
                    logger.error(f"Username is None. {e}")

                # sessionRecord
                ret_val = SessionInfo(**session)
            else:
                ret_val = None
                logger.debug(f"get_session_from_db - Session info not found in db {session_id}")
                     
            
        self.close_connection(caller_name="get_session_from_db") # make sure connection is closed

        # return session model object
        return ret_val # None or Session Object

    def get_mysql_version(self):
        """
        Get the mysql version number
        
        >>> ocd = opasCentralDB()
        >>> ocd.get_mysql_version()
        'Vers: ...'
        """
        ret_val = "Unknown"
        self.open_connection(caller_name="update_session") # make sure connection is open
        if self.db is not None:
            curs = self.db.cursor()
            sql = "SELECT VERSION();"
            success = curs.execute(sql)
            if success:
                ret_val = "Vers: " + curs.fetchone()[0]
                curs.close()
            else:
                ret_val = None
        else:
            logger.fatal("Connection not available to database.")

        self.close_connection(caller_name="update_session") # make sure connection is closed
        return ret_val
    
    def update_session(self,
                       session_id,
                       api_client_id, 
                       userID=None,
                       username=None, 
                       authenticated: int=None,
                       authorized_peparchive: int=None,
                       authorized_pepcurrent: int=None,
                       session_end=None, 
                       userIP=None):
        """
        Update the extra fields in the session record
        """
        ret_val = None
        self.open_connection(caller_name="update_session") # make sure connection is open
        setClause = "SET "
        added = 0
        if api_client_id is not None:
            setClause += f" api_client_id = '{api_client_id}'"
            added += 1
        if userID is not None:
            if added > 0:
                setClause += ", "
            setClause += f" user_id = '{userID}'"
            added += 1
        if username is not None:
            if added > 0:
                setClause += ", "
            setClause += f" username = '{username}'"
            added += 1
        if authenticated:
            if added > 0:
                setClause += ", "
            setClause += f" authenticated = '{authenticated}'"
            added += 1
        if authorized_peparchive:
            if added > 0:
                setClause += ", "
            setClause += f" authorized_peparchive = '{authorized_peparchive}'"
            added += 1
        if authorized_pepcurrent:
            if added > 0:
                setClause += ", "
            setClause += f" authorized_pepcurrent = '{authorized_pepcurrent}'"
            added += 1
        if session_end is not None:
            if added > 0:
                setClause += ", "
            setClause += " session_end = '{}'".format(session_end) 
            added += 1

        if added > 0:
            if self.db is not None:
                try:
                    cursor = self.db.cursor()
                    sql = """UPDATE api_sessions
                             {}
                             WHERE session_id = %s
                          """.format(setClause)
                    success = cursor.execute(sql, (session_id))
                except pymysql.InternalError as error:
                    code, message = error.args
                    logger.error(code, message)
                else:
                    self.db.commit()
                
                cursor.close()
                if success:
                    ret_val = True
                    logger.debug(f"Updated session record for session: {session_id}")
                else:
                    ret_val = False
                    logger.warning(f"Could not record close session per sessionID {session_id} in DB")

        self.close_connection(caller_name="update_session") # make sure connection is closed
        return ret_val

    def delete_session(self, session_id):
        """
        Remove the session record, mostly for testing purposes.
        
        """
        ret_val = False
        #session = None
        if session_id is None:
            err_msg = "Parameter error: No session ID specified"
            logger.warning(err_msg)
        else:
            if not self.open_connection(caller_name="delete_session"): # make sure connection opens
                logger.error("Delete session could not open database")
            else: # its open
                if self.db is not None:  # don't need this check, but leave it.
                    cursor = self.db.cursor()
       
                    # now delete the session
                    sql = """DELETE FROM api_sessions
                             WHERE session_id = '%s'""" % session_id
                    
                    if cursor.execute(sql):
                        ret_val = self.db.commit()

                    cursor.close()
                    # self.sessionInfo = None
                    self.close_connection(caller_name="delete_session") # make sure connection is closed
                else:
                    logger.fatal("Connection not available to database.")

        return ret_val # return true or false, success or failure
        
    def save_session(self,
                     session_id,
                     session_info: models.SessionInfo=None
                     ):
        """
        Save the session info to the database
        
        Tested in main instance docstring
        """
        ret_val = False
        if session_id is None:
            logger.warning("SaveSession: No session ID specified")
        elif session_info is None: # for now, required
            logger.warning("SaveSession: No session_info specified")
        else:
            if session_info.session_start is None:
                session_info.session_start = datetime.now()                
            if not self.open_connection(caller_name="save_session"): # make sure connection opens
                logger.error("Save session could not open database")
            else: # its open
                if self.db is not None:  # don't need this check, but leave it.
                    cursor = self.db.cursor()
                    # now insert the session
                    sql = """REPLACE INTO api_sessions(session_id,
                                                       user_id, 
                                                       username,
                                                       session_start, 
                                                       session_expires_time,
                                                       authenticated,
                                                       admin,
                                                       api_client_id,
                                                       authorized_peparchive,
                                                       authorized_pepcurrent
            )
            VALUES 
              (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s ) """
                    try:
                        success = cursor.execute(sql, 
                                                 (session_info.session_id, 
                                                  session_info.user_id, 
                                                  session_info.username,
                                                  session_info.session_start, 
                                                  session_info.session_expires_time,
                                                  session_info.authenticated,
                                                  session_info.admin, 
                                                  session_info.api_client_id,
                                                  session_info.authorized_peparchive,
                                                  session_info.authorized_pepcurrent
                                                  )
                                                 )
                    except pymysql.IntegrityError as e:
                        success = False
                        logger.error(f"save_session: Integrity Error {e}")
                        
                    except Exception as e:
                        success = False
                        logger.error(f"save_session Error: {e}")
                       
                    if success:
                        ret_val = True
                        self.db.commit()
                        logger.debug(f"Saved sessioninfo: {session_info.session_id}")
                    else:
                        msg = f"save_session {session_id} Insert Error. Record Could not be Saved"
                        logger.warning(msg)
                        ret_val = False
                    
                    cursor.close()
                    # session_info = self.get_session_from_db(session_id)
                    # self.sessionInfo = session_info
                    self.close_connection(caller_name="save_session") # make sure connection is closed
    
        # return session model object
        return ret_val, session_info #True or False, and SessionInfo Object

    def close_inactive_sessions(self, inactive_time=opasConfig.SESSION_INACTIVE_LIMIT):
        """
        Close any sessions where they've been inactive for inactive_time minutes
        """
        ret_val = None
        self.open_connection(caller_name="close_expired_sessions") # make sure connection is open

        if self.db is not None:
            try:
                cursor = self.db.cursor()
                sql = f""" UPDATE api_sessions
                          SET session_end = NOW()
                          WHERE session_id IN
                          (SELECT
                            vw_latest_session_activity.session_id
                             FROM
                             vw_latest_session_activity
                             WHERE latest_activity < DATE_SUB(NOW(), INTERVAL {inactive_time} MINUTE))        
                      """
                success = cursor.execute(sql)
            except pymysql.InternalError as error:
                code, message = error.args
                logger.error(code, message)
            else:
                self.db.commit()
            
            cursor.close()
            if success:
                ret_val = True
                logger.debug(f"Closed {success} expired sessions")
            else:
                ret_val = False
                logger.warning("Could not retire sessions in DB")

        self.close_connection(caller_name="close_expired_sessions") # make sure connection is closed
        return ret_val

    def count_open_sessions(self):
        """
        Get a count of any open sessions
        
        >>> ocd = opasCentralDB()
        >>> session_count = ocd.count_open_sessions()

        """
        ret_val = 0
        self.open_connection(caller_name="count_open_sessions") # make sure connection is open

        if self.db is not None:
            try:
                cursor = self.db.cursor()
                sql = """SELECT COUNT(*)
                         FROM api_sessions
                         WHERE session_end is NULL
                      """
                success = cursor.execute(sql)
                    
            except pymysql.InternalError as error:
                code, message = error.args
                logger.error(code, message)
            else:
                if success:
                    result = cursor.fetchone()
                    ret_val = result[0]
                else:
                    ret_val = 0
            
            cursor.close()

        self.close_connection(caller_name="count_open_sessions") # make sure connection is closed
        return ret_val
    
    def close_expired_sessions(self):
        """
        Close any sessions past the set expiration time set in the record
        
        >>> ocd = opasCentralDB()
        >>> session_count = ocd.close_expired_sessions()
        Closed ... expired sessions
        """
        ret_val = 0
        self.open_connection(caller_name="close_expired_sessions") # make sure connection is open

        if self.db is not None:
            try:
                cursor = self.db.cursor()
                sql = """UPDATE api_sessions
                         SET session_end = NOW()
                         WHERE session_expires_time < NOW()
                         AND session_end is NULL
                      """
                success = cursor.execute(sql)
                if success:
                    ret_val = cursor.fetchone()
                    
            except pymysql.InternalError as error:
                code, message = error.args
                logger.error(code, message)
            else:
                self.db.commit()
            
            cursor.close()
            ret_val = int(success)
            logger.info(f"Closed {ret_val} expired sessions")

        self.close_connection(caller_name="close_expired_sessions") # make sure connection is closed
        return ret_val
    
    def record_session_endpoint(self,
                                session_info=None,
                                api_endpoint_id=0,
                                params=None,
                                item_of_interest=None,
                                return_status_code=0,
                                api_endpoint_method="get",
                                status_message=None):
        """
        Track endpoint calls
        2020-08-25: Added api_endpoint_method
        
        Tested in main instance docstring
        """
        ret_val = None
        if not self.open_connection(caller_name="record_session_endpoint"): # make sure connection is open
            logger.error("record_session_endpoint could not open database")
        else:
            try:
                session_id = session_info.session_id
                client_id = session_info.api_client_id
            except:
                if self.session_id is None:
                    # no session open!
                    logger.warning("OCD: No session is open")
                    return ret_val
                else:
                    session_id = self.session_id
                    client_id = opasConfig.NO_CLIENT_ID
                    
            # Workaround for None in session id
            if session_id is None:
                session_id = opasConfig.NO_SESSION_ID # just to record it
                
            if self.db is not None:  # shouldn't need this test
                cursor = self.db.cursor()
                # TODO: I removed returnStatusCode from here. Remove it from the DB
                sql = """INSERT INTO 
                            api_session_endpoints(session_id, 
                                                  api_endpoint_id,
                                                  params, 
                                                  item_of_interest, 
                                                  return_status_code,
                                                  api_method,
                                                  return_added_status_message
                                                 )
                                                 VALUES 
                                                 (%s, %s, %s, %s, %s, %s, %s)"""

                logger.debug(f"Session ID: {session_id} (client {client_id}) accessed Session Endpoint {api_endpoint_id}")
                try:
                    ret_val = cursor.execute(sql, (session_id, 
                                                   api_endpoint_id, 
                                                   params,
                                                   item_of_interest,
                                                   return_status_code,
                                                   api_endpoint_method, 
                                                   status_message
                                                  ))
                    self.db.commit()
                    cursor.close()
                except pymysql.IntegrityError as e:
                    logger.error(f"Integrity Error {e} logging endpoint {api_endpoint_id} for session {session_id}.")
                    #session_info = self.get_session_from_db(session_id)
                    #if session_info is None:
                        #self.save_session(session_id) # recover for next time.
                except Exception as e:
                    logger.error(f"Error logging endpoint {api_endpoint_id} for session {session_id}. Error: {e}")
            
            self.close_connection(caller_name="record_session_endpoint") # make sure connection is closed

        return ret_val

    def get_sources(self, src_code=None, src_type=None, src_name=None, limit=None, offset=0):
        """
        Return a list of sources
          - for a specific source_code
          - OR for a specific source type (e.g. journal, book)
          - OR if source and src_type are not specified, bring back them all
          - OR rlike a src_name (any word(s) within src_name, or can be regex.  Always matches the start and end words")
          
        >>> ocd = opasCentralDB()
        >>> count, resp = ocd.get_sources(src_code='IJP')
        >>> resp[0]["basecode"]
        'IJP'
        >>> count
        1

        >>> ocd = opasCentralDB()
        >>> count, resp = ocd.get_sources(src_type='book')
        >>> count
        140

        # test normalize src_type (req len of input=4, expands to full, standard value)
        >>> ocd = opasCentralDB()
        >>> count, resp = ocd.get_sources(src_type='vide') 
        >>> count
        12

        >>> count, resp = ocd.get_sources(src_name='Psychoanalysis')
        >>> count > 34
        True
        >>> resp[0]["basecode"]
        'AJP'

        >>> count, resp = ocd.get_sources(src_name='Psychoan.*')
        >>> count > 34
        True
        >>> resp[0]["basecode"]
        'ADPSA'

        >>> count, resp = ocd.get_sources(src_code='IJP', src_name='Psychoanalysis', limit=5)
        >>> resp[0]["basecode"]
        'IJP'
        >>> count
        1

        >>> count, resp = ocd.get_sources()
        >>> count
        235
        """
        self.open_connection(caller_name="get_sources") # make sure connection is open
        total_count = 0
        ret_val = None
        limit_clause = ""
        if limit is not None:
            limit_clause = f"LIMIT {limit}"
            if offset != 0:
                limit_clause += f" OFFSET {offset}"

        if self.db is not None:
            src_code_clause = ""
            prod_type_clause = ""
            src_title_clause = ""
            
            try:
                curs = self.db.cursor(pymysql.cursors.DictCursor)
                if src_code is not None and src_code != "*":
                    src_code_clause = f"AND basecode = '{src_code}'"
                if src_type is not None and src_type != "*":
                    # already normalized, don't do it again
                    # src_type = normalize_val(src_type, opasConfig.VALS_PRODUCT_TYPES)
                    if src_type in ("stream", "videos"):
                        src_type = "videostream"
                    prod_type_clause = f"AND product_type = '{src_type}'"
                if src_name is not None:
                    src_title_clause = f"AND title rlike '(.*\s)?{src_name}(\s.*)?'"

                # 2020-11-13 - changed ref from vw_api_productbase to vw_api_productbase_instance_counts to include instance counts
                sqlAll = f"""FROM vw_api_productbase_instance_counts
                             WHERE active = 1
                                AND product_type <> 'bookseriessub'
                                {src_code_clause}
                                {prod_type_clause}
                                {src_title_clause}
                             ORDER BY title {limit_clause}"""
                
                sql = "SELECT * " + sqlAll
                res = curs.execute(sql)
                    
            except Exception as e:
                msg = f"Error querying vw_api_productbase: {e}"
                logger.error(msg)
                # print (msg)
            else:
                if res:
                    ret_val = curs.fetchall()
                    curs.close()

                    if limit_clause is not None:
                        # do another query to count
                        curs2 = self.db.cursor()
                        sqlCount = "SELECT COUNT(*) " + sqlAll
                        curs2.execute(sqlCount)
                        try:
                            total_count = curs2.fetchone()[0]
                        except:
                            total_count  = 0
                        curs2.close()
                    else:
                        total_count = len(ret_val)
                else:
                    ret_val = None
            
        self.close_connection(caller_name="get_sources") # make sure connection is closed

        # return session model object
        return total_count, ret_val # None or Session Object

    def save_client_config(self, client_id:str, client_configuration: models.ClientConfig, session_id, replace=False):
        """
        Save a client configuration.  Data format is up to the client.
        
        Returns True of False

        >>> ocd = opasCentralDB()
        >>> model = models.ClientConfig(configName="test", configSettings={"A":"123", "B":"1234"})
        >>> ocd.save_client_config(client_id="test", client_configuration=model, session_id="test123", replace=True)
        (200, 'OK')
        """
        msg = "OK"
        # convert client id to int
        try:
            client_id_int = int(client_id)
        except Exception as e:
            msg = f"Client ID should be a string containing an int {e}"
            logger.error(msg)
            ret_val = httpCodes.HTTP_400_BAD_REQUEST
        else:
            if client_configuration is None:
                msg = "No client configuration model provided to save."
                logger.error(msg)
                ret_val = httpCodes.HTTP_400_BAD_REQUEST
            else:
                if replace:
                    sql_action = "REPLACE"
                    ret_val = httpCodes.HTTP_200_OK
                else:
                    sql_action = "INSERT"
                    ret_val = httpCodes.HTTP_201_CREATED
                try:
                    session_id = session_id
                except Exception as e:
                    # no session open!
                    msg = "No session is open / Not authorized"
                    logger.error(msg)
                    ret_val = 401 # not authorized
                else:
                    self.open_connection(caller_name="record_client_config") # make sure connection is open
                    try:
                        try:
                            config_json = json.dumps(client_configuration.configSettings)
                        except Exception as e:
                            logger.warning(f"Error converting configuration to json {e}.")
                            return ret_val
            
                        with closing(self.db.cursor(pymysql.cursors.DictCursor)) as curs:
                            sql = f"""{sql_action} INTO 
                                        api_client_configs(client_id,
                                                           config_name, 
                                                           config_settings, 
                                                           session_id
                                                          )
                                                          VALUES 
                                                           (%s, %s, %s, %s)"""
                            
                            succ = curs.execute(sql,
                                                (client_id_int,
                                                 client_configuration.configName,
                                                 config_json, 
                                                 session_id
                                                )
                                               )
                            self.db.commit()
            
                    except Exception as e:
                        if sql_action == "REPLACE":
                            msg = f"Error updating (replacing) client config: {e}"
                            logger.error(msg)
                            ret_val = 400
                        else: # insert
                            msg = f"Error saving client config: {e}"
                            logger.error(msg)
                            ret_val = 409
            
                    self.close_connection(caller_name="record_client_config") # make sure connection is closed
    
        return (ret_val, msg)

    def get_client_config(self, client_id: str, client_config_name: str):
        """
        
        >>> ocd = opasCentralDB()
        >>> ocd.get_client_config(2, "demo")
        
        """
        ret_val = None
        self.open_connection(caller_name="get_client_config") # make sure connection is open
        try:
            client_id_int = int(client_id)
        except Exception as e:
            msg = f"Client ID should be a string containing an int {e}"
            logging.error(msg)
            ret_val = httpCodes.HTTP_400_BAD_REQUEST
        else:
            with closing(self.db.cursor(pymysql.cursors.DictCursor)) as curs:
                sql = f"""SELECT *
                          FROM api_client_configs
                          WHERE client_id = {client_id_int}
                          AND config_name = '{client_config_name}'"""
    
                res = curs.execute(sql)
                if res >= 1:
                    clientConfig = curs.fetchone()
                    ret_val = modelsOpasCentralPydantic.ClientConfigs(**clientConfig)
                else:
                    ret_val = None
    
            self.close_connection(caller_name="get_client_config") # make sure connection is closed
            if ret_val is not None:
                # convert to return model
                ret_val = models.ClientConfig(clientID = ret_val.client_id,
                                              configName = ret_val.config_name,
                                              configSettings=json.loads(ret_val.config_settings))
    
        return ret_val

    def del_client_config(self, client_id: int, client_config_name: str):
        """
        
        >>> ocd = opasCentralDB()
        >>> ocd.del_client_config(2, "demo")
        
        """
        ret_val = None
        saved = self.get_client_config(client_id, client_config_name)
        # open after fetching, since db is closed by call.
        self.open_connection(caller_name="del_client_config") # make sure connection is open
        try:
            client_id_int = int(client_id)
        except Exception as e:
            msg = f"Client ID should be a string containing an int {e}"
            logging.error(msg)
            ret_val = httpCodes.HTTP_400_BAD_REQUEST
        else:
            if saved is not None:
                sql = f"""DELETE FROM api_client_configs
                          WHERE client_id = {client_id_int}
                          AND config_name = '{client_config_name}'"""
        
                with closing(self.db.cursor(pymysql.cursors.DictCursor)) as curs:
                    res = curs.execute(sql)
                    if res >= 1:
                        ret_val = saved
                        self.db.commit()
                    else:
                        ret_val = None
                
            self.close_connection(caller_name="del_client_config") # make sure connection is closed

        return ret_val

    def record_document_view(self, document_id, session_info=None, view_type="Abstract"):
        """
        Add a record to the api_doc_views table for specified view_type (Abstract, Document, PDF, PDFOriginal, or EPub)

        Tested in main instance docstring
        
        """
        ret_val = None
        self.open_connection(caller_name="record_document_view") # make sure connection is open
        try:
            session_id = session_info.session_id
            user_id =  session_info.user_id
        except:
            # no session open!
            logger.debug("No session is open")
            return ret_val
        try:
            if view_type.lower() != "abstract" and view_type.lower() != "image/jpeg":
                try:
                    cursor = self.db.cursor()
                    sql = """INSERT INTO 
                                api_docviews(user_id, 
                                              document_id, 
                                              session_id, 
                                              type, 
                                              datetimechar
                                             )
                                             VALUES 
                                              (%s, %s, %s, %s, %s)"""
                    
                    ret_val = cursor.execute(sql,
                                            (user_id,
                                             document_id,
                                             session_id, 
                                             view_type, 
                                             datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                                             )
                                            )
                    self.db.commit()
                    cursor.close()
        
                except Exception as e:
                    logger.warning(f"Error saving document view: {e}")
                    
        except Exception as e:
            logger.warning(f"Error checking document view type: {e}")

        self.close_connection(caller_name="record_document_view") # make sure connection is closed

        return ret_val

    #def get_user(self, username = None, user_id = None):
        #"""
        #If user exists (via username or user_id) and has an active subscription
          #Returns userSubscriptions object and saves it to the ocd object properties.
          
        #Note: a user cannot login without an active subscription. 

        #Specify either username or userID, not both.
        
        #>>> ocd = opasCentralDB()
        #>>> ocd.get_user("demo")
        
        #"""
        #ret_val = None

        #return ret_val
    
    def verify_admin(self, session_info):
        """
        Find if this is an admin, and return user info for them.
        Returns a user object
        
        >>> ocd = opasCentralDB()
        >>> ocd.verify_admin(ocd.sessionInfo)
        False
        """
        #TODO - Use PaDS to verify admin status!
        ret_val = False
            
        return ret_val   
       
    #----------------------------------------------------------------------------------------
    def do_action_query(self, querytxt, queryparams, contextStr=None):
    
        ret_val = None
        localDisconnectNeeded = False
        if self.connected != True:
            self.open_connection(caller_name="action_query") # make sure connection is open
            localDisconnectNeeded = True
            
        dbc = self.db.cursor(pymysql.cursors.DictCursor)
        try:
            ret_val = dbc.execute(querytxt, queryparams)
        except self.db.DataError as e:
            logger.error(f"Art: {contextStr}. DB Data Error {e} ({querytxt})")
            raise self.db.DataError(e)
        except self.db.OperationalError as e:
            logger.error(f"Art: {contextStr}. DB Operation Error {e} ({querytxt})")
            raise self.db.OperationalError(e)
        except self.db.IntegrityError as e:
            logger.error(f"Art: {contextStr}. DB Integrity Error {e} ({querytxt})")
            raise self.db.IntegrityError(e)
        except self.db.InternalError as e:
            logger.error(f"Art: {contextStr}. DB Internal Error {e} ({querytxt})")
            raise self.db.InternalError(e)
            # raise RuntimeError, gErrorLog.logSevere("Art: %s.  DB Intr. Error (%s)" % (contextStr, querytxt))
        except self.db.ProgrammingError as e:
            logger.error(f"DB Programming Error {e} ({querytxt})")
            raise self.db.ProgrammingError(e)
        except self.db.NotSupportedError as e:
            logger.error(f"DB Feature Not Supported Error {e} ({querytxt})")
            raise self.db.NotSupportedError(e)
        except Exception as e:
            logger.error(f"error: %s" % (e))
            raise Exception(e)
    
        # close cursor
        dbc.close()
        
        if localDisconnectNeeded == True:
            # if so, commit any changesand close.  Otherwise, it's up to caller.
            self.db.commit()
            self.close_connection(caller_name="action_query") # make sure connection is open
        
        return ret_val

#================================================================================================================================

if __name__ == "__main__":
    print (40*"*", "opasCentralDBLib Tests", 40*"*")
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
    
    ocd = opasCentralDB()
    sourceDB = SourceInfoDB()
    code = sourceDB.lookupSourceCode("ANIJP-EL")
    # check this user permissions 
    #ocd.get_dict_of_products()
    #ocd.get_subscription_access("IJP", 421)
    #ocd.get_subscription_access("BIPPI", 421)
    #docstring tests
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
    #doctest.testmod()    
    print ("Fini. Tests complete.")