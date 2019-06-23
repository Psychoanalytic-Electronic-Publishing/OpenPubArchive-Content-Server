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
sys.path.append(r'/usr3/keys')  # Private encryption keys
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
from PEPWebKeys import SECRET_KEY, ALGORITHM
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# All opasCentral Database Models here
import opasCentralModels
from opasCentralModels import User, UserInDB

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
    def __init__(self, host="localhost", user="root", userpw="", dbname="opascentral"):
        self.db = None
        self.connected = False
        self.sessionStateReinitialize()
        try:
            self.db = pymysql.connect(host, user, userpw, dbname)
            self.connected = True
        except Exception as e:
            logging.error("Cannot connect to database %s for host %s and user %s" % (dbname, host, user))
        else:
            print ("Connected to database {}.".format(host))
        
    def sessionStateReinitialize(self):
        self.currentSession = None
        self.currentUser = None
        self.sessionID = None # this is also a subfield of currentSession
        self.sessionToken = None
        
    def endSession(self, sessionToken, sessionEnd=datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')):
        """
        >>> ocd = opasCentralDB()
        Connected!
        >>> sessionInfo = ocd.startSession()
        >>> ocd.endSession(sessionInfo.session_token)
        True
        """
        retVal = None

        if self.currentSession == None:
            # no session open!
            logging.warn("endSession: No session is open")
            return retVal
        
        if self.db != None:
            cursor = self.db.cursor()
            sql = """UPDATE api_sessions
                     SET session_end = '%s'
                     WHERE session_token = '%s'
                  """ % (sessionEnd,
                         sessionToken
                        )
            success = cursor.execute(sql)
            self.db.commit()
            cursor.close()
            if success:
                retVal = True
            else:
                logging.warn("Could not record close session per token={} in DB".format(sessionToken))
                retVal = False
                
        self.sessionStateReinitialize()

        return retVal
        
    def getCurrentSession(self):
        return self.currentSession # Session model object
        
    def startSession(self, newUsersID=None, sessionStart=datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), apiClientID=0):
        """
        Start a session and generate a session token.  
        Returns the token or None.
        
        >>> ocd = opasCentralDB()
        Connected!
        >>> sessionInfo = ocd.startSession()
        >>> sessionInfo.authenticated
        False
        """
        retVal = None
        if self.currentSession is not None:
            # session already open.  Close the old one
            self.endSession(sessionToken=self.currentSession.session_token)
            
        sessionToken = secrets.token_urlsafe(16)
        if newUsersID is None:
            usersID = 0 # no one is logged in
        else:
            try:
                usersID = newUsersID.user_id
            except Exception as e:
                print ("Session start error: ", e)
            
        sessionExpires = datetime.now() + timedelta(0, DEFAULTSESSIONLENGTH)
        if self.db != None:
            cursor = self.db.cursor()
            sql = """INSERT INTO api_sessions(user_id, 
                                              session_start, 
                                              session_expires_time,
                                              session_token, 
                                              api_client_id
                                      )
                                      VALUES 
                                        ('%s', '%s', '%s', '%s', '%s') """ % \
                                        (usersID,
                                         sessionStart, 
                                         sessionExpires,
                                         sessionToken, 
                                         apiClientID
                                         )
            
            success = cursor.execute(sql)
            self.db.commit()
            cursor.close()
            if success:
                #retVal = self.sessionToken
                cursor = self.db.cursor(pymysql.cursors.DictCursor)
                sql = """SELECT * FROM api_sessions
                         WHERE session_token = '{}'
                      """.format(sessionToken)
                try:
                    sess = cursor.execute(sql)
                except Exception as e:
                    print ("Can't get to Sessions DB: {}".format(e))
                else:
                    sessionRow = cursor.fetchone()
                    if sessionRow is not None:
                        try:
                            self.currentSession = opasCentralModels.Session(**sessionRow)
                            self.currentSession.session_expires_time = datetime.now() + timedelta(0, DEFAULTSESSIONLENGTH) 
                        except ValidationError as e:
                            print(e.json())        
                            retVal = None
                        else:
                            retVal = self.currentSession
                    else:
                        logging.error("Database fetch error.  Could not find sessionToken which should have been saved.")
                    
                # redundant, but convenient second copy of api_session_id
                self.sessionID = sessionRow["api_session_id"]
                if self.sessionID != self.currentSession.api_session_id:
                    raise ValueError("SessionIDs should have been the same")
                
                cursor.close()

        # return session model object
        return retVal # Session()
    
    def recordSessionEndpoint(self, apiEndpointID=0, params=None, documentID=None, statusMessage=None):
        """
        Track endpoint calls
        >>> ocd = opasCentralDB()
        Connected!
        >>> sessionInfo = ocd.startSession()
        >>> ocd.recordSessionEndpoint(apiEndpointID=API_AUTHORS_INDEX, documentID="IJP.001.0001A", statusMessage="Testing")
        1

        """
        retVal = None

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
                                              return_added_status_message
                                             )
                                             VALUES 
                                             ('%s', '%s', '%s', '%s', '%s')""" % \
                                             (
                                              self.sessionID, 
                                              apiEndpointID, 
                                              params,
                                              documentID,
                                              statusMessage
                                             )
    
            retVal = cursor.execute(sql)
            self.db.commit()
            cursor.close()
        
        return retVal

    def updateDocumentViewCount(self, articleID, account="NotLoggedIn", title=None, viewType="Online"):
        """
        >>> ocd = opasCentralDB()
        Connected!
        >>> ocd.updateDocumentViewCount("IJP.001.0001A")
        1
        """
        retVal = None
        if self.db != None:
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

        return retVal
            
    def getUser(self, username: str):
        """
        >>> ocd = opasCentralDB()
        >>> ocd.getUser("demo")
        
        """
        curs = self.db.cursor(pymysql.cursors.DictCursor)
        
        sql = """SELECT *
                 FROM user
                 WHERE username = '{}'""" .format(username)
        
        res = curs.execute(sql)
        if res == 1:
            user = curs.fetchone()
            return UserInDB(**user)
        else:
            return None
    
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
    
        return retVal
        
    
    def authenticateUser(self, username: str, password: str):
        """
        >>> ocd = opasCentralDB()
        >>> sessionInfo = ocd.authenticateUser("TemporaryDeveloper", "temporaryLover")  # Need to disable this account when system is online!
        >>> sessionInfo.authenticated
        True
        """
        print ("Authenticating user: {}".format(username))
        user = self.getUser(username)  # returns a UserInDB object
        if not user:
            print ("User: {} turned away".format(username))
            return False
        if not verifyPassword(password, user.password):
            print ("User: {} turned away with incorrect password".format(username))
            return False
        # start session for the new user
        self.startSession(newUsersID=user)  # keeps current session as self object attr
        self.currentSession.authenticated = True
        cursor = self.db.cursor(pymysql.cursors.DictCursor)
        sql = """UPDATE api_sessions
                 SET authenticated = {}
                 WHERE session_token = '{}';
              """.format(self.currentSession.authenticated, self.currentSession.session_token)
        sess = cursor.execute(sql)
        self.db.commit()
        
        return self.currentSession  # return the Users session model.  This user is already authenticated. 

    
#================================================================================================================================

if __name__ == "__main__":
    print (40*"*", "opasCentralDBLib Tests", 40*"*")
    print ("Running in Python %s" % sys.version_info[0])
    
    # docstring tests
    import doctest
    doctest.testmod()    
    print ("Tests complete.")