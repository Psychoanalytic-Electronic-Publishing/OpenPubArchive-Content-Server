#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
opasCentralDBLib

This library is supports the main functionality of the OPAS Central Database

The database has use and usage information.

2019.0614.1 - Python 3.7 compatible.  Work in progress.

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
from localsecrets import DBHOST, DBUSER, DBPW, DBNAME

import os.path
import re
import logging
from datetime import datetime, timedelta
import time

import secrets
from pydantic import BaseModel
from passlib.context import CryptContext
from pydantic import ValidationError

import pymysql

#import opasAuthBasic
from localsecrets import SECRET_KEY, ALGORITHM
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# All opasCentral Database Models here
import modelsOpasCentralPydantic
from modelsOpasCentralPydantic import User, UserInDB

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

def verifyPassword(plain_password, hashed_password):
    """
    >>> verifyPassword("secret", getPasswordHash("secret"))
    
    """
    return pwd_context.verify(plain_password, hashed_password)


def getPasswordHash(password):
    """
    (Test disabled, since tested via verify_password docstring)
    >> getPasswordHash("test 1 2 3 ")
    
    >>> getPasswordHash("temporaryLover")
    
    """
    return pwd_context.hash(password)

class opasCentralDB(object):
    """
    >>> ocd = opasCentralDB()
    >>> 
    """
    def __init__(self, sessionID=None, accessToken=None, expiresTime=None, userName="NotLoggedIn", user=None):
        pass
        # Try getting rid of all this
        
        #self.authenticated = False
        #self.sessionID = sessionID
        #self.accessToken = accessToken
        #self.expiresTime = expiresTime
        #self.user = user
        ## this global object info probably won't work for shared server instance, but leave it for now.
        #if user:
            #self.userName = user.username 
            #self.userID = user.user_id # "NotLoggedIn"
            #self.connected = False
            #self.authenticated = user.enabled
        #else:
            #self.userName = userName 
            #self.userID = opasConfig.USER_NOT_LOGGED_IN_ID # "NotLoggedIn"
            #self.connected = False

        #if self.accessToken is not None:
            #self.authenticated = True
        
    def openConnection(self, callerName=""):
        """
        Opens a connection if it's not already open.
        
        If already open, no changes.
        
        """
        try:
            status = self.db.open
        except:
            # not open reopen it.
            status = False
        
        if status == False:
            try:
                self.db = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPW, database=DBNAME)
                self.connected = True
                if opasConfig.CONSOLE_DEBUG_MESSAGES_ON:
                    print ("Database connection opened {}".format("(" + callerName + ")"))
            except:
                errMsg = "Cannot connect to database {} for host {} and user {}".format(DBNAME, DBHOST, DBUSER)
                logging.error(errMsg)
                if opasConfig.CONSOLE_DEBUG_MESSAGES_ON:
                    print (errMsg)
                self.connected = False

        return self.connected

    def closeConnection(self, callerName=""):
        try:
            if self.db.open:
                self.db.close()
                if opasConfig.CONSOLE_DEBUG_MESSAGES_ON:
                    print ("Database connection closed {}".format("(" + callerName + ")"))
        except:
            errMsg = "closeConnection: The db is not open {}".format("(" + callerName + ")")
            if opasConfig.CONSOLE_DEBUG_MESSAGES_ON:
                print (errMsg)
            logging.error(errMsg)

        # make sure to mark the connection false in any case
        self.connected = False           

    def endSession(self, sessionID, sessionEnd=datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')):
        """
        >>> ocd = opasCentralDB()
        >>> ocd.connected
        True
        >>> sessionInfo = ocd.startSession()
        >>> ocd.endSession(sessionInfo.session_token)
        True
        """
        retVal = None
        self.openConnection() # make sure connection is open
        if self.db != None:
            cursor = self.db.cursor()
            sql = """UPDATE api_sessions
                     SET session_end = '%s'
                     WHERE session_id = '%s'
                  """ % (sessionEnd,
                         sessionID
                        )
            success = cursor.execute(sql)
            self.db.commit()
            cursor.close()
            if success:
                retVal = True
            else:
                logging.warn("Could not record close session per token={} in DB".format(sessionToken))
                retVal = False

        self.closeConnection() # make sure connection is closed
        return retVal
        
    def getUserID(self, userName):
        retVal = 0
        if self.db != None:
            # get the user ID
            cursor = self.db.cursor(pymysql.cursors.DictCursor)
            sql = """
                  SELECT user_id from user WHERE username = '{}';
                  """.format(self.userName)
            
            success = cursor.execute(sql)
            if success:
                userDict = cursor.fetchone()
                retVal = self.userID = userDict.get("user_id", 0)
            else:
                retVal = self.userID = 0

            cursor.close()

        return retVal # userID
        
    def getSession(self, sessionID):
        """
        Get the session record info for session sessionID
        
        >>> sessionInfo = ocd.getSession(sessionID = "_JustATestSessionID")
        >>> sessionInfo.authenticated
        False
        """
        self.openConnection() # make sure connection is open
        retVal = None
        if self.db != None:
            curs = self.db.cursor()
            # now insert the session
            sql = "SELECT * FROM api_sessions";
            res = curs.execute(sql)
            if res == 1:
                session = curs.fetchone()
                # sessionRecord
                retVal = modelsOpasCentralPydantic.Session(**session)
            else:
                retVal = None
            
        self.closeConnection() # make sure connection is closed

        # return session model object
        return retVal # None or Session Object
        
    def startSession(self, sessionID=None, expiresTime=None, userName="NotLoggedIn", apiClientID=0):
        """
        Start a session
        
        >>> ocd = opasCentralDB()
        >>> sessionInfo = ocd.startSession()
        >>> sessionInfo.authenticated
        False
        """
        self.openConnection() # make sure connection is open
        retVal = None
        sessionStart=datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        if sessionID == None:
            # create a session ID
            print ("startSession creating a session ID, none supplied: {}".format(sessionID))
            sessionID = secrets.token_urlsafe(16)

        if self.db != None:
            cursor = self.db.cursor()
            if userName != "NotLoggedIn":
                userID = self.getUserID(userName=userName)
            else:
                userID = opasConfig.USER_NOT_LOGGED_IN_ID

            # now insert the session
            sql = """INSERT INTO api_sessions(session_id,
                                              user_id, 
                                              session_start, 
                                              session_expires_time,
                                              access_token, 
                                              authenticated,
                                              api_client_id
                                      )
                                      VALUES 
                                        ('%s', '%s', '%s', '%s', '%s', '%s', '%s') """ % \
                                        (sessionID, 
                                         userID, 
                                         sessionStart, 
                                         self.expiresTime,
                                         self.accessToken,
                                         (1 if self.authenticated else 0),
                                         apiClientID
                                         )
            
            success = cursor.execute(sql)
            retVal = self.db.commit()
            cursor.close()
            retVal = modelsOpasCentralPydantic.Session(api_session_id = sessionID,
                             user_id = self.userID,
                             session_start = sessionStart,
                             session_expires_time = self.expiresTime,
                             authenticated = self.authenticated,
                             api_client_id = apiClientID
                             )

        self.closeConnection() # make sure connection is closed

        # return session model object
        return retVal # None or Session Object
    
    def recordSessionEndpoint(self, apiEndpointID=0, params=None, documentID=None, returnStatusCode=0, statusMessage=None):
        """
        Track endpoint calls
        >>> ocd = opasCentralDB()
        >>> sessionInfo = ocd.startSession()
        >>> ocd.recordSessionEndpoint(apiEndpointID=API_AUTHORS_INDEX, documentID="IJP.001.0001A", statusMessage="Testing")
        1

        """
        retVal = None

        self.openConnection() # make sure connection is open

        if self.sessionID == None:
            # no session open!
            logging.warn("recordSessionEndpoint: No session is open")
            return retVal

        if self.db != None:
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
                                             ('%s', '%s', '%s', '%s', '%s', '%s')""" % \
                                             (
                                              self.sessionID, 
                                              apiEndpointID, 
                                              params,
                                              documentID,
                                              returnStatusCode,
                                              statusMessage
                                             )
    
            retVal = cursor.execute(sql)
            self.db.commit()
            cursor.close()
        
        self.closeConnection() # make sure connection is closed

        return retVal

    def updateDocumentViewCount(self, articleID, account="NotLoggedIn", title=None, viewType="Online"):
        """
        >>> ocd = opasCentralDB()
        >>> ocd.updateDocumentViewCount("IJP.001.0001A")
        1
        """
        retVal = None
        self.openConnection() # make sure connection is open

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
                                        ('%s', '%s', '%s', '%s', '%s') """ % \
                                        (account,
                                         articleID, 
                                         title, 
                                         viewType, 
                                         datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%SZ')
                                         )
            
            retVal = cursor.execute(sql)
            self.db.commit()
            cursor.close()

        except Exception as e:
            logging.warn("recordSessionEndpoint: {}".format(e))
            

        self.closeConnection() # make sure connection is closed

        return retVal
            
    def getUser(self, username: str):
        """
        >>> ocd = opasCentralDB()
        >>> ocd.getUser("demo")
        
        """
        self.openConnection() # make sure connection is open
        curs = self.db.cursor(pymysql.cursors.DictCursor)
        
        sql = """SELECT *
                 FROM user_active_subscriptions
                 WHERE username = '{}'""" .format(username)
        
        res = curs.execute(sql)
        if res == 1:
            user = curs.fetchone()
            retVal = modelsOpasCentralPydantic.UserSubscriptions(**user)
        else:
            retVal = None

        self.closeConnection() # make sure connection is closed
        return retVal
    
    def verifyAdmin(self, username, password):
        """
        >>> ocd = opasCentralDB()
        >>> ocd.verifyAdmin("TemporaryDeveloper", "temporaryLover")
        
        """
        retVal =  None
        admin = self.getUser(username)
        if admin.enabled and admin.admin:
            if verifyPassword(password, admin.password):
                retVal = admin
    
        return retVal   
    
    def createUser(self, username, password, adminUsername, adminPassword, company=None, email=None):
        """
        Create a new user!
        
        >>> ocd = opasCentralDB()
        >>> ocd.createUser("nobody2", "nothing", "TemporaryDeveloper", "temporaryLover", "USGS", "nobody@usgs.com")
          
        """
        retVal = None
        self.openConnection() # make sure connection is open
        curs = self.db.cursor(pymysql.cursors.DictCursor)
    
        admin = self.verifyAdmin(adminUsername, adminPassword)
        if admin is not None:
            # see if user exists:
            user = self.getUser(username)
            if user is None: # good to go
                user = UserInDB()
                user.username = username
                user.password = getPasswordHash(password)
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
                            getPasswordHash(user.password),
                            admin.user_id,
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                          )
                if curs.execute(sql):
                    msg = "Created user {}".format(user.username)
                    print (msg)
                    self.db.commit()
                else:
                    err = "Could not create user {}".format(user.username)
                    logging.error(err)
                    print (err)
    
                curs.close()
                retVal = User(**user.dict())
            else:
                err = "Username {} already in database.".format(user.username)
                logging.error(err)
                print (err)
    
        self.closeConnection() # make sure connection is closed
        return retVal
        
    
    def authenticateUser(self, username: str, password: str):
        """
        >>> ocd = opasCentralDB()
        >>> sessionInfo = ocd.authenticateUser("TemporaryDeveloper", "temporaryLover")  # Need to disable this account when system is online!
        True
        """
        print ("Authenticating user: {}".format(username))
        self.openConnection() # make sure connection is open
        user = self.getUser(username)  # returns a UserInDB object
        if not user:
            print ("User: {} turned away".format(username))
            retVal = False
        elif not verifyPassword(password, user.password):
            print ("User: {} turned away with incorrect password".format(username))
            retVal = False
        else:
            retVal = True

        # start session for the new user

        self.closeConnection() # make sure connection is closed
        return user  

    
#================================================================================================================================

if __name__ == "__main__":
    print (40*"*", "opasCentralDBLib Tests", 40*"*")
    print ("Running in Python %s" % sys.version_info[0])
    
    #sessionID = secrets.token_urlsafe(16)
    #ocd = opasCentralDB(sessionID, 
                        #secrets.token_urlsafe(16), 
                        #datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        #userName = "gvpi")

    #session = ocd.startSession(sessionID)
    #ocd.recordSessionEndpoint(apiEndpointID=API_AUTHORS_INDEX, documentID="IJP.001.0001A", statusMessage="Testing")
    #ocd.updateDocumentViewCount("IJP.001.0001A")
    #session = ocd.endSession(sessionID)
    #ocd.closeConnection()
    
    #ocd.connected
    
    #docstring tests
    import doctest
    doctest.testmod()    
    print ("Tests complete.")