#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OPASFileTracker.py:    Library for file tracking to skip already processed files 
                       for OPAS

                       Uses pymysql as a database for lightweight operation

"""
# Disable many annoying pylint messages, warning me about variable naming for example.
# yes, in my Solr code I'm caught between two worlds of snake_case and camelCase.

# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0325,C0326

from __future__ import absolute_import
from __future__ import print_function
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2019.12.24"
__status__      = "Development"

import sys
sys.path.append('../config')


import os
import os.path
import time
import ntpath

import pymysql
import config
import localsecrets

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
    def __init__(self, sqlDBPath=None):
        """
        Get the file info for the specified file
        
        sqlDBPath is only used in the sqllite version of this lib, but
           left here for parameter compat.
        
        """
        self.conn = pymysql.connect(host=localsecrets.DBHOST, port=localsecrets.DBPORT, user=localsecrets.DBUSER, password=localsecrets.DBPW, database=localsecrets.DBNAME)
        self.createDB()
        return
    #----------------------------------------------------------------------------------------
    def createDB(self):
        """
        Create the database at the location specified, unless it exists
        """
        retVal = True
        createCmd = """
                        CREATE TABLE IF NOT EXISTS fileTracking(
                                                    filePath VARCHAR(512) NOT NULL,
                                                    fileSize INT,
                                                    fileModDate FLOAT,
                                                    buildDate INT,
                                                    solrServerURL VARCHAR(512),
                                                    PRIMARY KEY(filePath)
                                                ) ENGINE=INNODB;
                    """
        try:
            # print(pymysql.version)
            # Try to connect, see if the database table already exists
            count = self.getFileDatabaseRecordCount()
            # if not, create it.
            if count is None:
                try:
                    self.createTable(createCmd)
                    retVal = True
                    print ("Database has 0 entries")
                except pymysql.Error as e:
                    self.conn = None
                    retVal = False
                    print ("Cannot connect to database")
                    print(e)
            else:
                print(f"Database found - it has {count} entries")

        except pymysql.Error as e:
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
            print(("Delete Requested,  %s records in database" % count))
            c = self.conn.cursor()
            c.execute("DELETE FROM fileTracking;")
            self.commit()
            count = self.getFileDatabaseRecordCount()
            print(("Delete Performed, now there are %s records in database" % count))
            retVal = True
        except pymysql.Error as e:
            print(e)

        c.close()
        return retVal

    #----------------------------------------------------------------------------------------
    def deleteRecord(self, filePath):
        """
        Delete a specific record, e.g., for use if the file at filePath was missing
        """
        retVal = False
        try:
            c = self.conn.cursor()
            c.execute(f"DELETE FROM fileTracking WHERE filePath = '{filePath}';")
            self.commit()
            print("Delete Performed")
            retVal = True
        except pymysql.Error as e:
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
        except pymysql.Error as e:
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
        except pymysql.Error as e:
            print(e)
            retVal = None

        c.close()
        return retVal

    #----------------------------------------------------------------------------------------
    def commit(self):
        """
        Do a commit of the pymysql database with error trapping
        """
        try:
            self.conn.commit()
        except pymysql.Error as e:
            print(("Commit failed!", e))

    #----------------------------------------------------------------------------------------
    def setFileDatabaseRecord(self, currentFileInfo):
        """
        Check pymysql to see if and when the file was last processed

        :param currentFileInfo: a CREATE TABLE statement
        :return: False for fail
        """
        retVal = False
        updateFileInfoSQL = r"""
                                    UPDATE fileTracking
                                    SET filePath = %s,
                                        fileSize = %s,
                                        fileModDate = %s,
                                        buildDate = %s,
                                        solrServerURL = %s
                                    WHERE filePath = %s and solrServerURL = %s;
                                """ 
        insertIntoFileInfoSQL = r"""
                                    INSERT INTO fileTracking (filePath,  fileSize, fileModDate, buildDate, solrServerURL)
                                    VALUES (%s, %s, %s, %s, %s)
                                """
        try:
            c = self.conn.cursor()
            c.execute(updateFileInfoSQL, (currentFileInfo.filePath,
                                       currentFileInfo.fileSize,
                                       currentFileInfo.fileModDate,
                                       currentFileInfo.buildDate,
                                       currentFileInfo.solrAPIURL,
                                       currentFileInfo.filePath, 
                                       currentFileInfo.solrAPIURL
                                      ))
            if c.rowcount == 0:
                # if it isn't updated, then it didn't exist, so insert it
                c.execute(insertIntoFileInfoSQL, (currentFileInfo.filePath,
                                       currentFileInfo.fileSize,
                                       currentFileInfo.fileModDate,
                                       currentFileInfo.buildDate,
                                       currentFileInfo.solrAPIURL
                                      ))
            retVal = True
        except pymysql.Error as e:
            print(("SetDatabaseRecord Error: ", e))
            #retVal = False #default

        c.close()
        # for debug, let it commit; otherwise, let it commit later
        self.commit()  # we commit during the Solr update loop, so if Solr update fails, so does the "files seen" database update.
        return retVal

    #----------------------------------------------------------------------------------------
    def getFileDatabaseRecord(self, filePath, serverURL):
        """ Check pymysql to see if and when the file was last processed
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
                            WHERE filePath = %s and solrServerURL = %s
                        """
        try:
            c = self.conn.cursor()
            c.execute(getFileInfoSQL, (filePath, serverURL))
            rows = c.fetchall()
            if rows == ():
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

        except pymysql.Error as e:
            print(e)
            retVal = None

        c.close()  # close cursor
        return retVal

    #----------------------------------------------------------------------------------------
    def getMissingFileList(self, filePath):
        """ Find files that are missing from the disk
        """
        retVal = []
        getFileInfoSQL = """
                            SELECT
                               filePath,
                               fileSize,
                               fileModDate,
                               buildDate,
                               solrServerURL
                            FROM fileTracking
                            """
        try:
            c = self.conn.cursor()
            c.execute(getFileInfoSQL)
            rows = c.fetchall()
            if rows == []:
                # no database record here
                retVal = None
            else:
                rem_count = 0
                for row in rows:
                    filePath = row[0]
                    if not os.path.isfile(filePath):
                        # we need to remove it from solr
                        # create a list of missing IDs
                        rem_count += 1
                        art_id = ntpath.basename(filePath.upper())
                        art_id = art_id.replace("(BEXP_ARCH1).XML", "")
                        # add to retVal
                        print (f"Adding {art_id} to the Solr remove list")
                        retVal.append(art_id)
                        print (f"Deleting {art_id} record frm the database")
                        self.deleteRecord(filePath)

        except pymysql.Error as e:
            print(e)
        
        print(f"{rem_count} files found to be removed from Solr.  Returning list.")
        c.close()  # close cursor
        return retVal

    def isFileModified(self, currentFileInfo):
        """
        """
        retVal = False
        filesDBRecord = self.getFileDatabaseRecord(currentFileInfo.filePath, serverURL = currentFileInfo.solrAPIURL)
        if filesDBRecord is None:
            retVal = True  # file not in database.
        elif format(filesDBRecord.fileModDate, '.2f') != format(currentFileInfo.fileModDate, '.2f'):
            #print filesDBRecord.fileModDate, currentFileInfo.fileModDate
            print(("File is modified: %s.  %s != %s" % (currentFileInfo.filePath, int(filesDBRecord.fileModDate), int(currentFileInfo.fileModDate))))
            retVal = True
        else: #File not modified
            retVal = False

        return retVal

    
if __name__ == "__main__":
    import sys
    print ("Running in Python %s" % sys.version_info[0])

    myFileTracker = FileTracker()
    myFileTracker.getMissingFileList(r"X:\_PEPA1\_PEPa1v\_PEPCurrent")

    #import doctest
    #doctest.testmod()    

    print ("...done...")