#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2021.1102/v1.1.1"
__status__      = "Beta"

programNameShort = "opasCentralMini"

import sys
sys.path.append('../config')

UPDATE_AFTER = 2500

import logging
import pymysql
import localsecrets

from datetime import datetime
# logFilename = programNameShort + "_" + datetime.today().strftime('%Y-%m-%d') + ".log"
FORMAT = '%(asctime)s %(name)s %(funcName)s %(lineno)d - %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.WARNING, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(programNameShort)
start_notice = f"{programNameShort} version {__version__} started at {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}."
print (start_notice)


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
