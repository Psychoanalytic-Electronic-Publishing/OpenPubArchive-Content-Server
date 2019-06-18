#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OPASFileTracker.py:    Library for file tracking to skip already processed files 
                       for OPAS

                       Uses SQLLite3 as a database for lightweight operation

"""
# Disable many annoying pylint messages, warning me about variable naming for example.
# yes, in my Solr code I'm caught between two worlds of snake_case and camelCase.

# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0325,C0326

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "1.0.0"
__status__      = "Development"


import sqlite3
import os
import os.path
import time

import config

def getModDate(filePath):
    """
    Get the date that a file was last modified
    """
    retVal = None
    try:
        retVal = os.path.getmtime(filePath)
    except IOError:
        # try where the script is running from instead.
        config.logger.info("%s not found.", filePath)
    except Exception as e:
        config.logger.fatal("%s.", e)

    return retVal

class FileTrackingInfo (object):
    """
    A class to store basic file info equivalent to the database records
    """
    #----------------------------------------------------------------------------------------
    def __init__(self):
        self.filePath = ""
        self.fileModDate = None
        self.fileSize = 0
        self.buildDate = None
        self.solrAPIURL = ""

    def loadForFile(self, filePath, solrAPIURL):
        self.filePath = filePath
        self.fileModDate = getModDate(filePath)
        self.fileSize = os.path.getsize(filePath)
        self.buildDate = time.time()
        self.solrAPIURL = solrAPIURL

    def loadData(self, filePath, fileModDate, fileSize, buildDate, solrAPIURL):
        self.filePath = filePath
        self.fileModDate = fileModDate
        self.fileSize = fileSize
        self.buildDate = buildDate
        self.solrAPIURL = solrAPIURL


class FileTracker (object):
    #----------------------------------------------------------------------------------------
    def __init__(self, sqlDBPath="fileTracker.db"):
        """
        Get the file info for the specified file from an SQLLite instance
        """
        #self.currentFilePath.loadForFile(filePath, solrAPIURL)
        self.sqlDBPath = sqlDBPath
        self.connectDB()
        self.lastDatabaseGet = None
        return
    #----------------------------------------------------------------------------------------
    def connectDB(self):
        """
        Create the database at the location specified, unless it exists
        """
        retVal = True
        createCmd = """
                            CREATE TABLE fileTracking(
                            filePath VARCHAR NOT NULL,
                            fileSize BIGINT,
                            fileModDate FLOAT,
                            buildDate INT,
                            solrServerURL VARCHAR,
                            PRIMARY KEY(filePath)
                            );
                            """
        try:
            self.conn = sqlite3.connect(self.sqlDBPath)
            #print(sqlite3.version)
            count = self.getFileDatabaseRecordCount()
            if count is None:
                try:
                    self.createTable(createCmd)
                    retVal = True
                    print ("Database has 0 entries")
                except sqlite3.Error as e:
                    self.conn = None
                    retVal = False
                    print ("Cannot connect to database")
                    print(e)
            else:
                print ("%s Processed File Database found - it has %s entries" % (self.sqlDBPath, count))

        except sqlite3.Error as e:
            self.conn = None
            retVal = False
            print ("Cannot connect to database")
            print(e)


        return retVal

    #----------------------------------------------------------------------------------------
    def deleteAll(self):
        """
        Delete all records

        """
        retVal = False
        try:
            count = self.getFileDatabaseRecordCount()
            print ("Delete Requested,  %s records in database" % count)
            c = self.conn.cursor()
            c.execute("DELETE FROM fileTracking;")
            self.commit()
            count = self.getFileDatabaseRecordCount()
            print ("Delete Performed, now there are %s records in database" % count)
            retVal = True
        except sqlite3.Error as e:
            print(e)

        c.close()
        return retVal

    #----------------------------------------------------------------------------------------
    def createTable(self, createTableSql):
        """
        Create a table from the create_table_sql statement

        :param createTableSql: a CREATE TABLE statement
        :return: False for fail
        """
        retVal = False
        try:
            c = self.conn.cursor()
            c.execute(createTableSql)
            retVal = True
        except sqlite3.Error as e:
            print(e)

        c.close()
        return retVal

    #----------------------------------------------------------------------------------------
    def getFileDatabaseRecordCount(self):
        """
        Get count of records in database
        """

        try:
            c = self.conn.cursor()
            c.execute("SELECT count(*) FROM fileTracking;")
            rows = c.fetchall()
            retVal = rows[0][0]
        except sqlite3.Error as e:
            print(e)
            retVal = None

        c.close()
        return retVal

    #----------------------------------------------------------------------------------------
    def commit(self):
        """
        Do a commit of the sqlite3 database with error trapping
        """
        try:
            self.conn.commit()
        except sqlite3.Error as e:
            print ("Commit failed!", e)

    #----------------------------------------------------------------------------------------
    def setFileDatabaseRecord(self, currentFileInfo):
        """
        Check sqllite to see if and when the file was last processed

        :param currentFileInfo: a CREATE TABLE statement
        :return: False for fail
        """
        retVal = False
        updateFileInfoSQL = """
                                    UPDATE fileTracking
                                    SET filePath = '%s',
                                        fileSize = %s,
                                        fileModDate = %s,
                                        buildDate = %s,
                                        solrServerURL = '%s'
                                    WHERE filePath = '%s';
                                """ % (currentFileInfo.filePath,
                                       currentFileInfo.fileSize,
                                       currentFileInfo.fileModDate,
                                       currentFileInfo.buildDate,
                                       currentFileInfo.solrAPIURL,
                                       currentFileInfo.filePath
                                      )
        insertIntoFileInfoSQL = """
                                    INSERT INTO fileTracking (filePath,  fileSize, fileModDate, buildDate, solrServerURL)
                                    VALUES ('%s', %s, %s, %s, '%s')
                                """ % (currentFileInfo.filePath,
                                       currentFileInfo.fileSize,
                                       currentFileInfo.fileModDate,
                                       currentFileInfo.buildDate,
                                       currentFileInfo.solrAPIURL
                                      )

        try:
            c = self.conn.cursor()
            c.execute(updateFileInfoSQL)
            if c.rowcount == 0:
                # if it isn't updated, then it didn't exist, so insert it
                c.execute(insertIntoFileInfoSQL)
            retVal = True
        except sqlite3.Error as e:
            print("SetDatabaseRecord Error: ", e)
            #retVal = False #default

        c.close()
        #self.commit()  # we commit during the Solr update loop, so if Solr update fails, so does the "files seen" database update.
        return retVal

    #----------------------------------------------------------------------------------------
    def getFileDatabaseRecord(self, filePath):
        """ Check sqllite to see if and when the file was last processed
        """
        retVal = FileTrackingInfo()
        getFileInfoSQL = """
                            SELECT
                               filePath,
                               fileSize,
                               fileModDate,
                               buildDate,
                               solrServerURL
                            FROM fileTracking
                            WHERE filePath = '%s'
                        """ % filePath
        try:
            c = self.conn.cursor()
            c.execute(getFileInfoSQL)
            rows = c.fetchall()
            if rows == []:
                # no database record here
                retVal = None
            elif len(rows) > 1:
                print ("Error: query returned multiple rows")
                retVal = None
            else:
                for row in rows:
                    retVal.filePath = row[0]
                    retVal.fileSize = row[1]
                    retVal.fileModDate = row[2]
                    retVal.buildDate = row[3]
                    retVal.solrAPIURL = row[4]

        except sqlite3.Error as e:
            print(e)

        c.close()  # close cursor
        return retVal

    def isFileModified(self, currentFileInfo):
        """
        """
        retVal = False
        filesDBRecord = self.getFileDatabaseRecord(currentFileInfo.filePath)
        if filesDBRecord is None:
            retVal = True  # file not in database.
        elif format(filesDBRecord.fileModDate, '.2f') != format(currentFileInfo.fileModDate, '.2f'):
            #print filesDBRecord.fileModDate, currentFileInfo.fileModDate
            print ("File is modified: %s.  %s != %s" % (currentFileInfo.filePath, int(filesDBRecord.fileModDate), int(currentFileInfo.fileModDate)))
            retVal = True
        else: #File not modified
            retVal = False

        return retVal
