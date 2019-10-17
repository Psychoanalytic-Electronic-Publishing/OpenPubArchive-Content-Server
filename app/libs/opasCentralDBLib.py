#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
opasCentralDBLib

This library is supports the main functionality of the OPAS Central Database

The database has use and usage information.

2019.0708.1 - Python 3.7 compatible.  Work in progress.

"""
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2019.0619.1"
__status__      = "Development"

import sys
sys.path.append('../libs')
sys.path.append('../config')

import opasConfig
import localsecrets
# from localsecrets import DBHOST, DBUSER, DBPW, DBNAME

# import os.path
# import re
import logging
logger = logging.getLogger(__name__)

from datetime import datetime # , timedelta
import time

# import secrets
# from pydantic import BaseModel
from passlib.context import CryptContext
# from pydantic import ValidationError

import pymysql

#import opasAuthBasic
from localsecrets import url_pads
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

import requests
import xml.etree.ElementTree as ET

# All opasCentral Database Models here
import modelsOpasCentralPydantic
from modelsOpasCentralPydantic import User, UserInDB
#from models import SessionInfo

DEFAULTSESSIONLENGTH = 1800 # seconds (timeout)

API_LOGIN = 1	        # /Login/
API_LOGIN_STATUS = 2	#/License/Status/Login/
API_LOGOUT = 3      	# /Logout/
API_ALERTS = 6
API_REPORTS = 7
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
API_DOCUMENTS_EPUB = 33	#/Documents/Downloads/PDF/{documentID}/
API_DOCUMENTS_IMAGE = 34	#/Documents/Downloads/Images/{imageID}/
API_DATABASE_SEARCHANALYSIS_FOR_TERMS = 40	#/Database/SearchAnalysis/{searchTerms}/
API_DATABASE_SEARCH = 41	#/Database/Search/
API_DATABASE_WHATSNEW = 42	#/Database/WhatsNew/
API_DATABASE_MOSTCITED = 43	#/Database/MostCited/
API_DATABASE_MOSTDOWNLOADED = 44	#/Database/MostDownloaded/
API_DATABASE_SEARCHANALYSIS = 45	#/Database/SearchAnalysis/

def verifyAccessToken(session_id, username, access_token):
    return pwd_context.verify(session_id+username, access_token)
    
def verify_password(plain_password, hashed_password):
    """
    >>> verifyPassword("secret", getPasswordHash("secret"))
    
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """
    (Test disabled, since tested via verify_password docstring)
    >> getPasswordHash("test 1 2 3 ")
    
    >>> getPasswordHash("temporaryLover")
    
    """
    return pwd_context.hash(password)

class opasCentralDB(object):
    """
    This object should be used and then discarded on an endpoint by endpoint basis in any
      multiuser mode.
      
    Therefore, keeping session info in the object is ok,
    
    >>> ocd = opasCentralDB()
    >>> randomSessionID = secrets.token_urlsafe(16)
    >>> success, sessionInfo = ocd.saveSession(sessionID=randomSessionID)
    >>> sessionInfo.authenticated
    False
    >>> sessionInfo = ocd.getSession(sessionID=randomSessionID)
    >>> sessionInfo.authenticated
    False
    >>> ocd.recordSessionEndpoint(sessionID=randomSessionID, apiEndpointID=API_AUTHORS_INDEX, documentID="IJP.001.0001A", statusMessage="Testing")
    1
    >>> ocd.updateDocumentViewCount("IJP.001.0001A")
    1
    >>> ocd.endSession(sessionInfo.session_id)
    True
    # don't delete, do it manually
    > ocd.deleteSession(sessionID=randomSessionID)
    True
    """
    def __init__(self, session_id=None, access_token=None, token_expires_time=None, username="NotLoggedIn", user=None):
        self.db = None
        self.connected = False
        self.authenticated = False
        self.session_id = session_id
        self.access_token = access_token
        self.tokenExpiresTime = token_expires_time
        self.user = None
        self.sessionInfo = None
        
    def open_connection(self, caller_name=""):
        """
        Opens a connection if it's not already open.
        
        If already open, no changes.
        
        """
        try:
            status = self.db.open
            self.connected = True
            if opasConfig.CONSOLE_DB_DEBUG_MESSAGES_ON:
                print (f"Database connection was already opened ({caller_name})")
            
        except:
            # not open reopen it.
            status = False
        
        if status == False:
            try:
                self.db = pymysql.connect(host=localsecrets.DBHOST, port=localsecrets.DBPORT, user=localsecrets.DBUSER, password=localsecrets.DBPW, database=localsecrets.DBNAME)
                self.connected = True
                if opasConfig.CONSOLE_DB_DEBUG_MESSAGES_ON:
                    print (f"Database connection was already opened ({caller_name})")
            except:
                err_msg = f"Cannot connect to database {localsecrets.DBNAME} for host {localsecrets.DBHOST},  user {localsecrets.DBUSER} port {localsecrets.DBPORT}"
                logger.error(err_msg)
                if opasConfig.CONSOLE_DB_DEBUG_MESSAGES_ON:
                    print (err_msg)
                self.connected = False
                self.db = None

        return self.connected

    def close_connection(self, caller_name=""):
        try:
            if self.db.open:
                self.db.close()
                if opasConfig.CONSOLE_DB_DEBUG_MESSAGES_ON:
                    print (f"Database connection closed ({caller_name})")
                self.db = None
        except:
            err_msg = f"closeConnection: The db is not open ({caller_name})"
            if opasConfig.CONSOLE_DB_DEBUG_MESSAGES_ON:
                print (err_msg)
            logger.error(err_msg)

        # make sure to mark the connection false in any case
        self.connected = False           

    def end_session(self, session_id, session_end=datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')):
        """
        End the session
        
        Tested in main instance docstring
        """
        ret_val = None
        self.open_connection(caller_name="end_session") # make sure connection is open
        if self.db != None:
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
        
    def get_most_downloaded(self,
                            view_period=5,
                            sort_by_period="last12months",
                            document_type="journals",
                            author=None,
                            title=None,
                            journal_name=None,
                            limit=None,
                            offset=0):
        """
         Using the api_session_endpoints data, return the most downloaded (viewed) Documents
           
         1) Using documents published in the last 5, 10, 20, or all years.
            Viewperiod takes an int and covers these or any other period (now - viewPeriod years).
         2) Filtering videos, journals, books, or all content.  Document type filters this.
            Can be: "journals", "books", "videos", or "all" (default)
         3) Optionally filter for author, title, or specific journal.
            Per whatever the caller specifies in parameters.
         4) show views in last 7 days, last month, last 6 months, last calendar year.
            This function returns them all.
         
        """
        ret_val = None
        self.open_connection(caller_name="get_most_downloaded") # make sure connection is open
        if limit is not None:
            limit_clause = f"LIMIT {offset}, {limit}"
        else:
            limit_clause = ""
            
        if self.db != None:
            cursor = self.db.cursor(pymysql.cursors.DictCursor)

            if document_type == "journals":
                doc_type_clause = " AND jrnlcode NOT IN ('ZBK', 'SE', 'IPL', 'NPL', 'GW') \
                                    AND jrnlcode not like '%VS'"
            elif document_type == "books":
                doc_type_clause = " AND jrnlcode IN ('ZBK', 'SE', 'IPL', 'NPL', 'GW')"
            elif document_type == "videos":
                doc_type_clause = " AND jrnlcode like '%VS'"
            else:
                doc_type_clause = ""  # all

            if author is not None:
                author_clause = f" AND hdgauthor CONTAINS {author}"
            else:
                author_clause = ""
                
            if title is not None:
                title_clause = f" AND hdgtitle CONTAINS {title}"
            else:
                title_clause = ""

            if title is not None:
                journal_clause = f" AND srctitleseries CONTAINS {journalName}"
            else:
                journal_clause = ""
                
            if view_period is not None:
                if view_period == 0 or str(view_period).upper() == "ALL" or str(view_period).upper()=="ALLTIME":
                    view_period = 500 # 500 years should cover all time!
                pub_year_clause = f" AND `pubyear` > YEAR(NOW()) - {view_period}"  # consider only the past viewPeriod years
            else:
                pub_year_clause = ""

            if sort_by_period is not None:
                # 1 through 5 reps the 5 different values
                if sort_by_period == 1 or sort_by_period == "lastweek":
                    sort_by_col_name = "lastweek"
                elif sort_by_period == 2 or sort_by_period == "lastmonth":
                    sort_by_col_name = "lastmonth"
                elif sort_by_period == 3 or sort_by_period == "last6months":
                    sort_by_col_name = "last6months"
                elif sort_by_period == 4 or sort_by_period == "last12months":
                    sort_by_col_name = "last12months"
                elif sort_by_period == 5 or sort_by_period == "lastcalendaryear":
                    sort_by_col_name = "lastcalyear"
                else:
                    sort_by_col_name = "last12months"
            else:
                sort_by_col_name = "last12months"
            
            sort_by_clause = f" ORDER BY {sort_by_col_name} DESC"

            sql = f"""SELECT * 
                      FROM vw_stat_most_viewed
                      WHERE 1 = 1
                      {doc_type_clause}
                      {author_clause}
                      {title_clause}
                      {journal_clause}
                      {pub_year_clause}
                      {sort_by_clause}
                      {limit_clause}
                    """
            row_count = cursor.execute(sql)
            if row_count:
                ret_val = cursor.fetchall()
                
            cursor.close()
        
        self.close_connection(caller_name="get_most_downloaded") # make sure connection is closed
        return row_count, ret_val
        
        
    def get_session_from_db(self, session_id):
        """
        Get the session record info for session sessionID
        
        Tested in main instance docstring
        """
        from models import SessionInfo # do this here to avoid circularity
        self.open_connection(caller_name="get_session_from_db") # make sure connection is open
        ret_val = None
        if self.db != None:
            curs = self.db.cursor(pymysql.cursors.DictCursor)
            # now insert the session
            sql = f"SELECT * FROM api_sessions WHERE session_id = '{session_id}'";
            res = curs.execute(sql)
            if res == 1:
                session = curs.fetchone()
                # sessionRecord
                ret_val = SessionInfo(**session)
                if ret_val.access_token == "None":
                    ret_val.access_token = None
                
            else:
                ret_val = None
            
        self.close_connection(caller_name="get_session_from_db") # make sure connection is closed

        # return session model object
        return ret_val # None or Session Object

    def update_session(self, session_id, userID=None, access_token=None, userIP=None, connectedVia=None, session_end=None):
        """
        Update the extra fields in the session record
        """
        ret_val = None
        self.open_connection(caller_name="update_session") # make sure connection is open
        setClause = "SET "
        added = 0
        if access_token != None:
            setClause += f" access_token = '{accessToken}'"
            added += 1
        if userID != None:
            if added > 0:
                setClause += ", "
            setClause += f" user_id = '{userID}'"
            added += 1
        if userIP != None:
            if added > 0:
                setClause += ", "
            setClause += f" user_ip = '{userIP}'"
            added += 1
        if connectedVia != None:
            if added > 0:
                setClause += ", "
            setClause += f" connected_via = '{connectedVia}'"
            added += 1
        if session_end != None:
            if added > 0:
                setClause += ", "
            setClause += " session_end = '{}'".format(session_end) 
            added += 1

        if added > 0:
            if self.db != None:
                try:
                    cursor = self.db.cursor()
                    sql = """UPDATE api_sessions
                             {}
                             WHERE session_id = %s
                          """.format(setClause)
                    success = cursor.execute(sql, (session_id))
                except pymysql.InternalError as error:
                    code, message = error.args
                    print (">>>>>>>>>>>>> %s %s", code, message)
                    logger.error(code, message)
                else:
                    self.db.commit()
                
                cursor.close()
                if success:
                    ret_val = True
                    print (f"Updated session record for session: {session_id}")
                else:
                    ret_val = False
                    print (f"Session close/update did not work for sessionID: {session_id}")
                    logger.warning(f"Could not record close session per token={session_id} in DB")

        self.close_connection(caller_name="update_session") # make sure connection is closed
        return ret_val

    def delete_session(self, session_id):
        """
        Remove the session record, mostly for testing purposes.
        
        """
        ret_val = False
        #session = None
        if session_id is None:
            err_msg = "No session ID specified"
            logger.error(err_msg)
            if opasConfig.CONSOLE_DB_DEBUG_MESSAGES_ON:
                print (err_msg)
        else:
            if not self.open_connection(caller_name="delete_session"): # make sure connection opens
                err_msg = "Delete session could not open database"
                logger.error(err_msg)
                if opasConfig.CONSOLE_DB_DEBUG_MESSAGES_ON:
                    print (err_msg)
            else: # its open
                if self.db != None:  # don't need this check, but leave it.
                    cursor = self.db.cursor()
       
                    # now delete the session
                    sql = """DELETE FROM api_sessions
                             WHERE session_id = '%s'""" % session_id
                    
                    if cursor.execute(sql):
                        ret_val = self.db.commit()

                    cursor.close()
                    self.sessionInfo = None
                    self.close_connection(caller_name="delete_session") # make sure connection is closed

        return ret_val # return true or false, success or failure
        
    def save_session(self, session_id, 
                         expiresTime=None, 
                         username="NotLoggedIn", 
                         userID=0,  # can save us a lookup ... #TODO
                         userIP=None,
                         connectedVia=None,
                         referrer=None,
                         apiClientID=0, 
                         accessToken=None,
                         keepActive=False
                         ):
        """
        Save the session info to the database
        
        Tested in main instance docstring
        """
        ret_val = False
        session_info = None
        if session_id is None:
            err_msg = "SaveSession: No session ID specified"
            logger.error(err_msg)
            if opasConfig.CONSOLE_DB_DEBUG_MESSAGES_ON:
                print (err_msg)
        else:
            if not self.open_connection(caller_name="save_session"): # make sure connection opens
                err_msg = "Save session could not open database"
                logger.error(err_msg)
                if opasConfig.CONSOLE_DB_DEBUG_MESSAGES_ON:
                    print (err_msg)
            else: # its open
                session_start=datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                if self.db != None:  # don't need this check, but leave it.
                    cursor = self.db.cursor()
                    if username != "NotLoggedIn":
                        user = self.get_user(username=username)
                        if user:
                            userID = user.user_id
                            authenticated = True
                            #if expiresTime == None:
                                #from opasCentralDBLib import getMaxAge
                                #maxAge = getMaxAge(keepActive)
                                #expiresTime = datetime.utcfromtimestamp(time.time() + maxAge).strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            userID = opasConfig.USER_NOT_LOGGED_IN_ID
                            authenticated = False
                    else:
                        userID = opasConfig.USER_NOT_LOGGED_IN_ID
                        authenticated = False
        
                    # now insert the session
                    sql = """INSERT INTO api_sessions(session_id,
                                                      user_id, 
                                                      username,
                                                      user_ip,
                                                      connected_via,
                                                      referrer,
                                                      session_start, 
                                                      session_expires_time,
                                                      access_token, 
                                                      authenticated,
                                                      api_client_id
                                              )
                                              VALUES 
                                                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """
                    
                    success = cursor.execute(sql, 
                                             (session_id, 
                                              userID, 
                                              username,
                                              userIP,
                                              connectedVia,
                                              referrer,
                                              session_start, 
                                              expiresTime,
                                              accessToken,
                                              authenticated,
                                              apiClientID
                                              )
                                             )
                    if success:
                        msg = f"save_session: Session {session_id} Record Saved"
                        print (msg)
                    else:
                        msg = f"save_session {session_id} Record Could not be Saved"
                        print (msg)
                        logger.warning(msg)
                    
                    ret_val = self.db.commit()
                    cursor.close()
                    session_info = self.get_session_from_db(session_id)
                    self.sessionInfo = session_info
                    self.close_connection(caller_name="save_session") # make sure connection is closed
    
        # return session model object
        return ret_val, session_info #True or False, and SessionInfo Object

    def close_expired_sessions(self, expire_time=30):
        """
        Retire any expire sessions
        """
        ret_val = None
        self.open_connection(caller_name="close_expired_sessions") # make sure connection is open

        if self.db != None:
            try:
                cursor = self.db.cursor()
                sql = f""" UPDATE api_sessions
                          SET session_end = NOW()
                          WHERE session_id IN
                          (SELECT
                            vw_latest_session_activity.session_id
                             FROM
                             vw_latest_session_activity
                             WHERE latest_activity < DATE_SUB(NOW(), INTERVAL {expireTime} MINUTE))        
                      """
                success = cursor.execute(sql)
            except pymysql.InternalError as error:
                code, message = error.args
                print (">>>>>>>>>>>>> %s %s", code, message)
                logger.error(code, message)
            else:
                self.db.commit()
            
            cursor.close()
            if success:
                ret_val = True
                print (f"Closed {success} expired sessions")
            else:
                ret_val = False
                print ("Closed expired sessions did not work")
                logger.warning("Could not retire sessions in DB")

        self.close_connection(caller_name="close_expired_sessions") # make sure connection is closed
        return ret_val

    def retire_expired_sessions(self):
        """
        Retire any expired sessions (in the database)
        """
        ret_val = None
        self.open_connection(caller_name="retire_expired_sessions") # make sure connection is open

        if self.db != None:
            try:
                cursor = self.db.cursor()
                sql = """UPDATE api_sessions
                         SET session_end = NOW()
                         WHERE session_expires_time < NOW()
                         AND session_end is NULL
                      """
                success = cursor.execute(sql)
            except pymysql.InternalError as error:
                code, message = error.args
                print (f">>>>>>>>>>>>> {code} {message}")
                logger.error(code, message)
            else:
                self.db.commit()
            
            cursor.close()
            if success:
                ret_val = True
                print (f"Retired {int(success)} expired sessions")
            else:
                ret_val = False
                print ("Retired expired sessions did not work")
                logger.warning("Could not retire sessions in DB")

        self.close_connection(caller_name="retire_expired_sessions") # make sure connection is closed
        return ret_val
    
    def record_session_endpoint(self, session_info=None, api_endpoint_id=0, params=None, document_id=None, return_status_code=0, status_message=None):
        """
        Track endpoint calls
        
        Tested in main instance docstring
        """
        ret_val = None
        if not self.open_connection(caller_name="record_session_endpoint"): # make sure connection is open
            err_msg = "Save session could not open database"
            logger.error(err_msg)
            if opasConfig.CONSOLE_DB_DEBUG_MESSAGES_ON:
                print (err_msg)
        else:
            try:
                session_id = session_info.session_id         
            except:
                if self.session_id == None:
                    # no session open!
                    logger.warning("record_session_endpoint: No session is open")
                    return ret_val
                else:
                    session_id = self.session_id
                
            if self.db != None:  # shouldn't need this test
                cursor = self.db.cursor()
                # TODO: I removed returnStatusCode from here. Remove it from the DB
                sql = """INSERT INTO 
                            api_session_endpoints(session_id, 
                                                  api_endpoint_id,
                                                  params, 
                                                  documentid, 
                                                  return_status_code,
                                                  return_added_status_message
                                                 )
                                                 VALUES 
                                                 (%s, %s, %s, %s, %s, %s)"""
                                                 
        
                ret_val = cursor.execute(sql, (
                                                  session_id, 
                                                  api_endpoint_id, 
                                                  params,
                                                  document_id,
                                                  return_status_code,
                                                  status_message
                                                 ))
                self.db.commit()
                cursor.close()
            
            self.close_connection(caller_name="record_session_endpoint") # make sure connection is closed

        return ret_val

    def get_sources(self, source=None, source_type=None, limit=None, offset=0):
        """
        >>> ocd = opasCentralDB()
        >>> sources = ocd.getSources()

        """
        self.open_connection(caller_name="get_sources") # make sure connection is open
        total_count = 0
        ret_val = None
        limit_clause = ""
        if limit is not None:
            limit_clause = f"LIMIT {limit}"
            if offset != 0:
                limit_clause += f"OFFSET {offset}"

        if self.db != None:
            try:
                curs = self.db.cursor(pymysql.cursors.DictCursor)
                if source is not None:
                    sqlAll = "FROM vw_opas_sources WHERE active = 1 and src_code = '%s'" % source
                elif source_type is not None:
                    sqlAll = "FROM vw_opas_sources WHERE active = 1 and src_type = '%s' and (src_type_qualifier <> 'multivolumesubbook' or src_type_qualifier IS NULL)" % source_type
                else:  # bring them all back
                    sqlAll = "FROM vw_opas_sources WHERE active = 1 and (src_type_qualifier IS NULL or src_type_qualifier <> 'multivolumesubbook')"

                sql = f"SELECT * {sqlAll} ORDER BY title {limit_clause}"
                res = curs.execute(sql)
                    
            except Exception as e:
                msg = f"get_sources Error querying vw_opas_sources: {e}"
                logger.error(msg)
                print (msg)
            else:
                if res:
                    ret_val = curs.fetchall()
                    if limit_clause != None:
                        # do another query to count possil
                        curs2 = self.db.cursor()
                        sqlCount = "SELECT COUNT(*) " + sqlAll
                        count_cur = curs2.execute(sqlCount)
                        try:
                            total_count = curs2.fetchone()[0]
                        except:
                            total_count  = 0
                        curs2.close()
                        curs.close()
                    else:
                        total_count = len(ret_val)
                else:
                    ret_val = None
            
        self.close_connection(caller_name="get_sources") # make sure connection is closed

        # return session model object
        return total_count, ret_val # None or Session Object

    def update_document_view_count(self, articleID, account="NotLoggedIn", title=None, viewType="Online"):
        """
        Add a record to the doc_viewcounts table for specified viewtype

        Tested in main instance docstring
        """
        ret_val = None
        self.open_connection(caller_name="update_document_view_count") # make sure connection is open

        try:
            cursor = self.db.cursor()
            sql = """INSERT INTO 
                        doc_viewcounts(account, 
                                        locator, 
                                        title, 
                                        type, 
                                        datetimechar
                                      )
                                      VALUES 
                                        ('%s', '%s', '%s', '%s', '%s')"""
            
            ret_val = cursor.execute(sql,
                                    (account,
                                     articleID, 
                                     title, 
                                     viewType, 
                                     datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')
                                     )
                                    )
            self.db.commit()
            cursor.close()

        except Exception as e:
            logger.warning(f"recordSessionEndpoint: {e}")
            

        self.close_connection(caller_name="update_document_view_count") # make sure connection is closed

        return ret_val
            
    def get_user(self, username = None, user_id = None):
        """
        If user exists (via username or user_id) and has an active subscription
          Returns userSubscriptions object and saves it to the ocd object properties.
          
        Note: a user cannot login without an active subscription. 

        Specify either username or userID, not both.
        
        >>> ocd = opasCentralDB()
        >>> ocd.getUser("demo")
        
        """
        try:
            db_opened = not self.db.open
        except:
            self.open_connection(caller_name="get_user") # make sure connection is open
            db_opened=True
    
        curs = self.db.cursor(pymysql.cursors.DictCursor)
        if username is not None:
            sql = f"""SELECT *
                     FROM user_active_subscriptions
                     WHERE username = '{username}'"""
        elif user_id is not None:
            sql = f"""SELECT *
                     FROM user_active_subscriptions
                     WHERE user_id = '{user_id}'"""

        if sql is None:
            logger.error("get_user: No user info supplied to search by")
            ret_val = None
        else:
            res = curs.execute(sql)
            if res == 1:
                user = curs.fetchone()
                ret_val = modelsOpasCentralPydantic.UserSubscriptions(**user)
            else:
                ret_val = None

        if db_opened: # if we opened it, close it.
            self.close_connection(caller_name="get_user") # make sure connection is closed

        return ret_val
    
    def verify_admin(self, username, password):
        """
        Find if this is an admin, and return user info for them.
        Returns a user object
        
        >>> ocd = opasCentralDB()
        >>> ocd.verifyAdmin("TemporaryDeveloper", "temporaryLover")
        
        """
        ret_val =  None
        admin = self.get_user(username)
        try:
            if admin.enabled and admin.admin:
                if verify_password(password, admin.password):
                    ret_val = admin
        except:
            err_msg = f"Cannot find admin user {username}"
            logger.error(err_msg)
            if opasConfig.CONSOLE_DB_DEBUG_MESSAGES_ON:
                print (err_msg)
    
        return ret_val   
    
    def create_user(self, username, password, admin_username, admin_password, company=None, email=None):
        """
        Create a new user!
        
        >>> ocd = opasCentralDB()
        >>> ocd.createUser("nobody2", "nothing", "TemporaryDeveloper", "temporaryLover", "USGS", "nobody@usgs.com")
          
        """
        ret_val = None
        self.open_connection(caller_name="create_user") # make sure connection is open
        curs = self.db.cursor(pymysql.cursors.DictCursor)
    
        admin = self.verify_admin(admin_username, admin_password)
        if admin is not None:
            # see if user exists:
            user = self.get_user(username)
            if user is None: # good to go
                user = UserInDB()
                user.username = username
                user.password = get_password_hash(password)
                user.company = company
                user.enabled = True
                user.email_address = email
                user.modified_by_user_id = admin.user_id
                user.enabled = True
                
                sql = """INSERT INTO user 
                         (
                            username,
                            email_address,
                            enabled,
                            company,
                            password,
                            modified_by_user_id,
                            added_date,
                            last_update
                            )
                        VALUES ('%s', '%s', %s, '%s', '%s', '%s', '%s', '%s')
                      """ % \
                          ( pymysql.escape_string(user.username),
                            user.email_address,
                            user.enabled,
                            pymysql.escape_string(user.company),
                            get_password_hash(user.password),
                            admin.user_id,
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                          )
                if curs.execute(sql):
                    msg = f"Created user {user.username}"
                    print (msg)
                    self.db.commit()
                else:
                    err = f"Could not create user {user.username}"
                    logger.error(err)
                    print (err)
    
                curs.close()
                ret_val = User(**user.dict())
            else:
                err = f"Username {user.username} already in database."
                logger.error(err)
                print (err)
    
        self.close_connection(caller_name="create_user") # make sure connection is closed
        return ret_val
        
    
    def authenticate_user(self, username: str, password: str):
        """
        Authenticate a user. 
        If they exist in the database, then return user info as
           (True, user)
        Else returns (False, None)
        
        >>> ocd = opasCentralDB()
        >>> status, userInfo = ocd.authenticateUser("TemporaryDeveloper", "temporaryLover")  # Need to disable this account when system is online!
        >>> status
        True
        """
        print (f"Authenticating user: {username}")
        self.open_connection(caller_name="authenticate_user") # make sure connection is open
        user = self.get_user(username)  # returns a UserInDB object
        if not user:
            msg = f"User: {username} turned away"
            logger.warning(msg)
            print (msg)
            ret_val = (False, None)
        elif not verify_password(password, user.password):
            msg = f"User: {username} turned away with incorrect password"
            logger.warning(msg)
            print (msg)
            ret_val = (False, None)
        else:
            self.user = user
            msg = f"Authenticated (with active subscription) user: {username}, sessionID: {self.session_id}"
            logger.info(msg)
            print (msg)
            
            ret_val = (True, user)

        if ret_val == (False, None):
            # try PaDSlogin
            user = self.auth_via_pads(username, password)
            if user == None:
                # Not a PaDS account
                ret_val = (False, None)
            else:
                ret_val = (True, user)
                
        # start session for the new user

        self.close_connection(caller_name="authenticate_user") # make sure connection is closed
        return ret_val

    def authenticate_referrer(self, referrer: str):
        """
        Authenticate a referrer (e.g., from PaDS). 
        
        >>> ocd = opasCentralDB()
        >>> refToCheck = "http://www.psychoanalystdatabase.com/PEPWeb/PEPWeb{}Gateway.asp".format(13)
        >>> status, userInfo = ocd.authenticateReferrer(refToCheck)  # Need to disable this account when system is online!
        >>> status
        True

        """
        ret_val = (False, None)
        print (f"Authenticating user by referrer: {referrer}")
        try:
            db_opened = not self.db.open
        except:
            self.open_connection(caller_name="authenticate_referrer") # make sure connection is open
            db_opened=True
    
        curs = self.db.cursor(pymysql.cursors.DictCursor)
        if referrer is not None:
            sql = """SELECT *
                     FROM vw_referrer_users
                     WHERE referrer_url = %s
                     AND enabled = 1
                     """ 

            res = curs.execute(sql, referrer)
            if res == 1:
                refUser = curs.fetchone()
                user = modelsOpasCentralPydantic.UserSubscriptions(**refUser)
                self.user = user
                msg = f"Authenticated (with active subscription) referrer: {referrer}"
                logger.info(msg)
                print (msg)
                ret_val = (True, user)
            else:
                ret_val = (False, None)
                msg = f"Referrer: {referrer} turned away"
                logger.warning(msg)
                print (msg)

        if db_opened: # if we opened it, close it.
            self.close_connection(caller_name="authenticate_referrer") # make sure connection is closed

        return ret_val

    def auth_via_pads(self, username, password):
        """
        Check to see if username password is in PaDS
        
        """
        authenticate_more = f"""<?xml version="1.0" encoding="utf-8"?>
                                <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
                                  <soap12:Body>
                                    <AuthenticateUserAndReturnExtraInfo xmlns="http://localhost/PEPProduct/PEPProduct">
                                        <UserName>{username}</UserName>
                                        <Password>{password}</Password>
                                    </AuthenticateUserAndReturnExtraInfo>                
                                  </soap12:Body>
                              </soap12:Envelope>
        """

        ret_val = None
        headers = {'content-type': 'text/xml'}
        ns = {"pepprod": "http://localhost/PEPProduct/PEPProduct"}
        soap_message = authenticate_more
        response = requests.post(url_pads, data=soap_message, headers=headers)
        #print (response.content)
        root = ET.fromstring(response.content)
        # parse XML return
        authenticate_user_and_return_extra_info_result_node = root.find('.//pepprod:AuthenticateUserAndReturnExtraInfoResult', ns)
        product_code_node = root.find('.//pepprod:ProductCode', ns)
        gateway_id_node = root.find('.//pepprod:GatewayId', ns)
        subscriber_name_node = root.find('.//pepprod:SubscriberName', ns)
        subscriber_email_address_node = root.find('.//pepprod:SubscriberEmailAddress', ns)
        # assign data
        authenticate_user_and_return_extra_info_result = authenticate_user_and_return_extra_info_result_node.text
        if authenticate_user_and_return_extra_info_result != "false":
            product_code = product_code_node.text
            gateway_id = gateway_id_node.text
            subscriber_name = subscriber_name_node.text
            subscriber_email_address = subscriber_email_address_node.text
            
            refToCheck = f"http://www.psychoanalystdatabase.com/PEPWeb/PEPWeb{gatewayID}Gateway.asp"
            possible_user = self.authenticate_referrer(refToCheck)
            # would need to add new extended info here
            if possible_user is not None:
                ret_val = possible_user
                ret_val = {
                            "authenticated" : authenticate_user_and_return_extra_info_result,
                            "username" : subscriber_name,
                            "userEmail" : subscriber_email_address,
                            "gatewayID" : gateway_id,
                            "productCode" : product_code
                        }
            else:
                ret_val = None
        
        print (ret_val)
    
        return ret_val

    
#================================================================================================================================

if __name__ == "__main__":
    print (40*"*", "opasCentralDBLib Tests", 40*"*")
    print ("Running in Python %s" % sys.version_info[0])
    
    #sessionID = secrets.token_urlsafe(16)
    #ocd = opasCentralDB(sessionID, 
                        #secrets.token_urlsafe(16), 
                        #datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        #username = "gvpi")

    #session = ocd.startSession(sessionID)
    #ocd.recordSessionEndpoint(apiEndpointID=API_AUTHORS_INDEX, documentID="IJP.001.0001A", statusMessage="Testing")
    #ocd.updateDocumentViewCount("IJP.001.0001A")
    #session = ocd.endSession(sessionID)
    #ocd.closeConnection()
    
    #ocd.connected
    
    ocd = opasCentralDB()
    #refToCheck = "http://www.psychoanalystdatabase.com/PEPWeb/PEPWeb{}Gateway.asp".format(13)
    #ocd.authenticateReferrer(refToCheck)
    results = ocd.get_most_downloaded()
    print (len(results))
    sys.exit()
    
    #docstring tests
    import doctest
    doctest.testmod()    
    print ("Tests complete.")