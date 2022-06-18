# -*- coding: Latin-1 -*-

"""
PEPArticleListDB manages a list of articles retrieved from the Articles Table.  It's used to match references with the articles in the PEP Database
(which consists of articles that are published by PEP)

@TODO: consolidate all the SQL code into one sub, to shorten and make it easier to make table changes.

"""

import sys, copy #, exceptions
# from PEPGlobals import *

#sys.path.append("e:/usr3/py/sciHL")

from PEPGlobals import gConnect, gJrnlData, gConst, gDbg1, gDbg2, gDbg3, gDbg4, gSplitCodesForGetProximateArticle, gLineLength, gDefaultRefMatchThresh, gErrorLog
#import sciSupport
#import sciUnicode
#import sciPEPSupport
#import sciDocuments
#import libPEPBiblioDB
#import PEPLocator
#import PEPLocalID
#from PEPReferenceMetaData import ReferenceMetaData
#from PEPCorrectedReferenceData import PEPCorrectedReferenceData
#from sciDocuments import PageNumber, PageRange

#from XMLArticle import *
#from sciDateTime import *
#import MySQLdb

#============================================================================================
class ArticleListDBBase:
    """
    Reference data base class

    """
    #--------------------------------------------------------------------------------
    def __init__(self, biblioDB=None, hlog=None, minThreshold=gDefaultRefMatchThresh, bibTemplate=r"<bibentry id='%s'><ba>%s</ba> <by>(%s)</by> <bt><jl name='%s'>%s.</jl></bt> <bj>&%s;</bj>. <bv>%s</bv>:<bp>%s</bp></bibentry>"):

        # set up error log object passed in or a new instance
        self.bibTemplate = bibTemplate
        self.refList = []
        self.bestMatch = None
        self.minThreshold=minThreshold
        self.biblioDB=biblioDB

    #--------------------------------------------------------------------------------
    def __initDB__(self):

        # Isolate db init routines so it's not run until the class is used rather than initialized

        if self.biblioDB==None:
            # set up bibliodb object passed in or a new instance
            self.biblioDB = libPEPBiblioDB.BiblioDB()
            self.biblioDB.__initDB__()

    #--------------------------------------------------------------------------------
    def clear(self):
        """
        Clear the instance of the working data
        """
        self.refList = []
        self.bestMatch = None

    #--------------------------------------------------------------------------------
    def setMinThreshold(self, newMin):
        """
        Change the minimum threshold for a match
        """
        self.minThreshold = newMin

    #--------------------------------------------------------------------------------
    def __repr__(self):
        """
        If article info has been fetched, display it as the current value
        """
        retVal = ""
        for n in self.refList:
            retVal += repr(n) + "\n"
            #print "XYZ", n
        return retVal

#============================================================================================
class PEPArticleListDB(ArticleListDBBase):
    """
    A list of Reference data extracted from the PEP Articles database

       >>> pepArticleList = PEPArticleListDB()
       >>> art = pepArticleList.fetchArticleReferenceFromArticleID("IPL.118.0001A")
       >>> print art[0][gConst.KEY]
       IPL.118.0001A
       >>> lockey = PEPLocator.Locator("IPL.052.0000A")
       >>> art = pepArticleList.fetchArticleReferenceFromArticleID(lockey)
       >>> print art[0][gConst.KEY]
       IPL.052.0000A

    """

    #	FULLTEXT			= "ReferenceText"				# Full text of reference
    #	TITLE 		   		= "Title"						# Title of article, article in book, or book if not edited
    #	SOURCETITLESERIES	= "SourceTitleSeries"			# Title of source: Journal name or series book title, such as International Psychoanalytic Library;
    #	SOURCETITLEABBR		= "SourceTitleAbbr"	  			# Official abbreviation for SOURCETITLESERIES (journal name or Book) in bibliographies
    #	SOURCETITLECITED 	= "SourceTitleCited"			# Title of Source as originally cited in a reference
    #	BKALSOKNOWNAS		= "BookAlsoKnownAs"				# List of alternate names for the book
    #														#
    #														# Regular Book or Non Series Entire Book Name:
    #														# 	Title: 				Book Name
    #														# 	SourceTitleCited: 	None
    #														# 	SourceTitleSeries: 	None
    #														#
    #														# Series Book:
    #														# 	Title: 				Book Name
    #														# 	SourceTitleCited: 	None
    #														# 	SourceTitleSeries:	Series Name
    #														# 	SourceTitleAbbr:	Series Name Abbreviation
    #														#
    #														# Article in Edited Book:
    #														# 	Title: 				Article
    #														# 	SourceTitleCited: 	Book Name
    #														# 	SourceTitleSeries: 	None
    #														#
    #														# Article in Edited Book Part of Series:
    #														# 	Title: 				Article
    #														# 	SourceTitleCited: 	Book Name
    #														# 	SourceTitleSeries: 	Series Name
    #														# 	SourceTitleAbbr:	Series Name Abbreviation
    #
    #	SOURCEPEPCODE 	   	= "JournalCode"					# PEP Journal Abbreviation or "OTH" for other nonPEP journals or books
    #	ARTTYPE 		   	= "ArticleType"					# Decoded type of reference
    #	REFTYPE 		   	= "RefType"						# Decoded type of reference
    #	AUTHORS		   		= "Authors"						#
    #	AUTHLIST		   	= "AuthList"					#
    #	TYPEREASON	   		= "TypeReason"					# Reason it was classified this way
    #	REASON				= "Reason"						#
    #	PROBABLESOURCE  	= "ProbableSource"				# Callers declaration of journal name or book title
    #	PUBLISHER	   		= "Publisher"					# Publisher, mainly used for books
    #	YEAR			   	= "Year"						# Official Publication year
    #	VOL			   		= "Vol"							# Volume of journal or book series
    #	VOLSUFFIX	   		= "VolSuffix" 					# Volume suffix (for supplements)
    #	ISSUE		   		= "Issue"						# Issue of journal
    #	PGRG			   	= "PgRg"						# Hyphenated Page range, e.g., 1-14
    #	PGSTART		   		= "PgStart"						# Starting page number, arabic numbers
    #	PGEND		   		= "PgEnd"						# Ending page number, arabic numbers
    #	PAGECOUNT			= "Pagecount" 					# Page count used on output of books
    #	KEY			   		= "Key"							# PEP Locator or non-pep derived key
    #	REFINTID			= "RefIntID"					# XML Internal ID, unique only within the instance
    #	# defined but not currently (A1v4) used
    #	JOURNALISS			= "JournalIssue"
    #	JOURNALVOLSUFFIX    = "jrnlVolSuffix"

    RELATEDSQLCONFTITLE = "RelatedSQLConfTitle"
    RELATEDSQLCONFAUTHOR = "RelatedSQLConfAuthor"
    RELATEDSQLCONFXMLSTRING = "RelatedSQLConfXMLString"

    articleTableMap = [	gConst.KEY,
                               gConst.ARTTYPE,
                               gConst.AUTHORS,
                               gConst.YEAR,
                               gConst.TITLE,
                               gConst.SOURCETITLESERIES,
                               gConst.SOURCEPEPCODE,
                               gConst.PUBLISHER,
                               gConst.VOL,
                               gConst.VOLSUFFIX,
                               gConst.ISSUE,
                               gConst.PGRG,
                               gConst.PGSTART,
                               gConst.PGEND,
                               gConst.MAINTOCID,
                               gConst.NEWSECNAME,
                               gConst.XMLREF
                               ]

    #----------------------------------------------------------------------------------------
    def fetchArticleReferenceFromArticleID(self, articleID, accumulate=0, altTable=None, regExpressionAllowed=False, noLog=1, callerID=""):
        """
        Search the PEP article table for article/book metadata,
         Return a list of matching ReferenceMetaData objects

        Note that the variant code, the last digit of the articleID, is not used in the search.

        >>> pepArticleList = PEPArticleListDB()
        >>> art = pepArticleList.fetchArticleReferenceFromArticleID("IPL.118.0001A")
        >>> print art[0][gConst.KEY]
        IPL.118.0001A

        """
        retVal = []
        localIDStr = None
        funcName = "fetchArticleReferenceFromArticleID"

        self.__initDB__()

        if altTable==None:
            qTable = "articles"
        else:
            qTable = "jourlitarticles"

        aLoc = PEPLocator.Locator(articleID)
        if aLoc.jrnlVol == 0:
            if gDbg1: print("%s Bad Volume in %s!" % (funcName, articleID))
            return retVal

        # verify article; but only can use articleID portion (in case a localID is passed in)
        if gDbg1: print("%s: %s" % (funcName, articleID))
        if regExpressionAllowed == True:
            predicate = "rlike"
            suffix = ""
            queryArticleID = articleID
        else:
            predicate = "like"
            suffix = "%%"
            #print "ArticleID: ", articleID
            if PEPLocalID.isLocalID(articleID):
                localIDStr = PEPLocator.Locator(articleID)
                queryArticleID = localIDStr.articleID()
            else:
                if not PEPLocator.isLocator(articleID): # shouldn't this be NOT?  Changed 2012-08-07
                    queryArticleID = PEPLocator.Locator(articleID)
                else:
                    queryArticleID = articleID

        if not opasgenlib.is_empty(articleID):
            # use entire key instead
            selqry = r"""select articleID,
                arttype,
                hdgauthor,
                year,
                hdgtitle,
                srctitleseries,
                jrnlcode,
                publisher,
                vol,
                volsuffix,
                issue,
                pgrg,
                pgstart,
                pgend,
                maintocID,
                newsecname,
                xmlRef
                from %s
                where articleID %s '%s%s'""" % (qTable, predicate, queryArticleID, suffix)
            if gDbg1: print("%s: %s" % (funcName, selqry))
            dbc = self.biblioDB.db.cursor()
            dbc.execute(selqry)
            resultSet = dbc.fetchall()
            if len(resultSet) == 0:
                # try to search components.  The ID itself doesn't work when the jrnlcode has a suffix, unless its supplied.
                retVal = self.fetchArticleReferenceFromArticleJnlVolPage(jrnlCode=aLoc.jrnlCode, vol=aLoc.jrnlVol, pgStart=aLoc.pgStart)
            else:
                for cursorRecord in resultSet:
                    recData = fetchAndConvertToRefMeta(cursorRecord, self.articleTableMap)
                    # Need to reinstate REFINPEP after loading new data
                    if localIDStr!=None:
                        recData[gConst.LOCALID] = localIDStr

                    if recData[gConst.ISSUE] == "S":
                        recData[gConst.JOURNALVOLSUFFIX] = "S"
                    recData[gConst.REFINPEP] = 1
                    refLoc = PEPLocator.Locator(recData[gConst.KEY])
                    recData[gConst.REFTYPE] = refLoc.sourceType()
                    #print "Recalc'd RefType: ", recData[gConst.REFTYPE]

                    if len(resultSet)==1:
                        recData[gConst.EXACTMATCH] = 1
                        #recData[gConst.CONFIDENCELEVEL] = 100
                        if gDbg1: print("%s: ExactMatch Set" % funcName)
                    else:
                        recData[gConst.EXACTMATCH] = 0

                    # A1v7 (added for a1v6 metadata export)
                    (recData[gConst.ISSN], recData[gConst.ISBN], recData[gConst.ISUN]) = self.biblioDB.getISSNISBN(refLoc)
                    #print "RecData: ", recData
                    retVal.append(recData)

            dbc.close()
        else: # may not want this, but try it.
            raise Exception("%s Empty Article ID.  Cannot fetch article reference info." % funcName)

        if accumulate==0:
            self.refList = retVal
        else:
            self.refList += retVal

        return self.refList

    #----------------------------------------------------------------------------------------
    def fetchArticleReferenceMetadataFromArticleID(self, articleID):
        """
        Return a single refMetaData object from a given articleID, or None if it isn't in the article database.

        >>> pepArticleList = PEPArticleListDB()
        >>> print pepArticleList.fetchArticleReferenceMetadataFromArticleID("IPL.118.0001A")
        {'PgStart': 1, 'Title': u"Freud's Self-Analysis", 'JournalCode': u'IPL', 'Issue': u'', 'SourceTitleSeries': u'Int. Psycho-Anal. Lib. ', 'PgRg': u'1-596', 'ISSN': '', 'ISUN': u'070120446X', 'Key': u'IPL.118.0001A', 'Authors': u'Anzieu, D.', 'VolSuffix': u'', 'NewSecName': None, 'ArticleType': u'ART', 'RefType': 'RefBookSeries', 'publisher': u'London: The Hogarth Press and the Institute of Psycho-Analysis', 'Vol': 118, 'PgEnd': 596, 'ExactMatch': 1, 'MAINTOCID': None, 'Year': u'1986', 'RefInPEP': 1, 'ISBN-10': u'070120446X'}
        >>> print pepArticleList.fetchArticleReferenceMetadataFromArticleID("PSW.008.0015A")[gConst.KEY]
        PSW.008A.0015A

        """
        self.__initDB__()

        retVal = self.fetchArticleReferenceFromArticleID(articleID)
        if retVal != []:
            retVal = retVal[0]
        else:
            retVal = None

        return retVal

    #----------------------------------------------------------------------------------------
    def fetchArticleReferenceFromArticleJnlVolPage(self, jrnlCode, vol, pgStart, noLog=0, accumulate=0):
        """
        Search the PEP article table for article/book metadata, using the components of the ID
         Return a list of matching ReferenceMetaData objects

        Note that the variant code, the last digit of the articleID, is not used in the search.
        >>> pepArticleList = PEPArticleListDB()
        >>> print pepArticleList.fetchArticleReferenceFromArticleJnlVolPage("PSW", 18, "107")[0]
        {'PgStart': 107, 'Title': u'The Changing Role of Fatherhood: The Father as a Provider of Selfobject Functions', 'JournalCode': u'PSW', 'Issue': u'2', 'SourceTitleSeries': u'Psychoanal. Soc. Work', 'PgRg': u'107-125', 'ISSN': u'1522-8878', 'ISUN': u'1522-8878', 'Key': u'PSW.018.0107A', 'Authors': u'Dick, G. L.', 'VolSuffix': u'', 'NewSecName': u'Articles', 'ArticleType': u'ART', 'RefType': 'RefJrnlArticle', 'publisher': u'', 'Vol': 18, 'PgEnd': 125, 'ExactMatch': 1, 'MAINTOCID': None, 'Year': u'2011', 'RefInPEP': 1, 'ISBN-10': ''}
        """
        retVal = []
        localIDStr = None
        funcName = "fetchArticleReferenceFromArticleJnlVolYear"

        self.__initDB__()

        qTable = "articles"
        selqry = r"""select articleID,
            arttype,
            hdgauthor,
            year,
            hdgtitle,
            srctitleseries,
            jrnlcode,
            publisher,
            vol,
            volsuffix,
            issue,
            pgrg,
            pgstart,
            pgend,
            maintocID,
            newsecname,
            xmlref
            from %s
            where jrnlcode = '%s'
            and  vol = '%s'
            and  pgstart = '%s'
            """ % (qTable, jrnlCode, int(vol), pgStart)

        if opasgenlib.is_empty(vol) or opasgenlib.is_empty(jrnlCode) or opasgenlib.is_empty(pgStart):
            raise Exception("%s Empty Article ID.  Cannot fetch article reference info." % funcName)
        else:
            if gDbg1: print("%s: %s" % (funcName, selqry))
            dbc = self.biblioDB.db.cursor()
            dbc.execute(selqry)
            resultSet = dbc.fetchall()
            if len(resultSet) == 0:
                if noLog==0:
                    if gDbg1: self.hLog.logWarning("%s - Article for '%s/%s/%s not found in db of PEP articles!" % (funcName, jrnlCode, vol, pgStart))
            else:
                for cursorRecord in resultSet:
                    recData = fetchAndConvertToRefMeta(cursorRecord, self.articleTableMap)
                    # Need to reinstate REFINPEP after loading new data
                    if localIDStr!=None:
                        recData[gConst.LOCALID] = localIDStr

                    if recData[gConst.ISSUE] == "S":
                        recData[gConst.JOURNALVOLSUFFIX] = "S"
                    recData[gConst.REFINPEP] = 1
                    refLoc = PEPLocator.Locator(recData[gConst.KEY])
                    recData[gConst.REFTYPE] = refLoc.sourceType()
                    #print "Recalc'd RefType: ", recData[gConst.REFTYPE]

                    if len(resultSet)==1:
                        recData[gConst.EXACTMATCH] = 1
                        #recData[gConst.CONFIDENCELEVEL] = 100
                        if gDbg1: print("%s: ExactMatch Set" % funcName)
                    else:
                        recData[gConst.EXACTMATCH] = 0

                    # A1v7 (added for a1v6 metadata export)
                    (recData[gConst.ISSN], recData[gConst.ISBN], recData[gConst.ISUN]) = self.biblioDB.getISSNISBN(refLoc)
                    retVal.append(recData)

            dbc.close()

        if accumulate==0:
            self.refList = retVal
        else:
            self.refList += retVal
        return self.refList

    #----------------------------------------------------------------------------------------
    def fetchArticleReferenceFromArticleIDForceYear(self, origArticleID, jrnlCode, Year, accumulate=0, noLog=1, callerID=""):

        retVal = []
        self.__initDB__()

        if gDbg1: print("Force Year: ", origArticleID, jrnlCode, Year)
        if callerID != "":
            callerIDStr = "(" + callerID + "/" + "forceYear" + ") "
        else:
            callerIDStr = ""

        if jrnlCode != None and Year != None:
            # XXX Need to do something more here if volList is populated!
            if jrnlCode!="SE":
                vol, volList = gJrnlData.getVol(jrnlCode, Year)
                for vol in volList:
                    if gDbg1: print("Vol Lookup: ", vol, type(vol))
                    newArticleID = PEPLocator.Locator(origArticleID).forceArticleID(forceJrnlVol=vol)
                    if newArticleID!=origArticleID:
                        if gDbg1: print("%sForcing Vol based on year.  Force %s to locator %s." % (callerIDStr, origArticleID, newArticleID))
                        retVal = self.fetchArticleReferenceFromArticleID(newArticleID, accumulate=accumulate, noLog=noLog)
                        if gDbg1: print("Candidate Article Count: ", len(retVal))
                    else:
                        if gDbg1: print("No need to force year to %s in %s!" % (Year, origArticleID))
                        #retVal = []
            else:
                print("Warning: Can't force SE lookup volume by Year")
                #vol, volList = gJrnlData.getVol(jrnlCode, Year)

        return retVal

    #----------------------------------------------------------------------------------------
    def fetchArticleReferenceFromArticleIDForceJournal(self, origArticleID, jrnlCode, accumulate=0, noLog=1, callerID=""):

        self.__initDB__()

        if gDbg1: print("Force Journal: ", origArticleID, jrnlCode)
        newArticleID = PEPLocator.Locator(origArticleID).forceArticleID(forceJrnlCode=jrnlCode)
        if newArticleID!=origArticleID:
            if gDbg1: print("Forcing Journal.  Force %s to locator %s." % (origArticleID, newArticleID))
            retVal = self.fetchArticleReferenceFromArticleID(newArticleID, accumulate=accumulate, noLog=noLog, callerID=callerID)
        else:
            if gDbg1: print("No need to force Journal to %s in %s!" % (jrnlCode, origArticleID))
            retVal = []
        return retVal

    #----------------------------------------------------------------------------------------
    def fetchArticleReferenceFromArticleIDForceSuffix(self, origArticleID, forceJrnlVolSuffix="S", accumulate=0, noLog=1, callerID=""):
        """
        >>> pepArticleList = PEPArticleListDB()
        >>> res = pepArticleList.fetchArticleReferenceFromArticleIDForceSuffix("FD.008.0007A", forceJrnlVolSuffix="A")
        >>> print res[0][gConst.KEY]
        FD.008A.0007A

        """
        self.__initDB__()

        if callerID != "":
            callerIDStr = "(" + callerID + "/" + "ForceSuffix" + ") "
        else:
            callerIDStr = ""

        newArticleID = PEPLocator.Locator(origArticleID).forceArticleID(forceJrnlVolSuffix=forceJrnlVolSuffix)
        if gDbg1: print("OriginalID: ", origArticleID, "NewID: ", newArticleID)
        if newArticleID!=origArticleID:
            if gDbg1: print("%sForcing Journal Suffix.  Force %s to locator %s." % (callerIDStr, origArticleID, newArticleID))
            retVal = self.fetchArticleReferenceFromArticleID(newArticleID, accumulate=accumulate, noLog=noLog, callerID=callerID)
        else:
            if gDbg1: print("%sNo need to force Suffix to %s in %s!" % (callerIDStr, forceJrnlVolSuffix, origArticleID))
            retVal = []
        return retVal

    #----------------------------------------------------------------------------------------
    def fetchArticleReferenceFromCitation(self, citedNames, citedYear=None, accumulate=0, noLog=0, callerID=""):
        """
        Search the reference database for an article based on a probabalistic search
            using the citation (names and year already separated).
            Return a list of matching ReferenceMetaData objects, ordred by probability of matching.

            >>> pepArticleList = PEPArticleListDB()
            >>> res = pepArticleList.fetchArticleReferenceFromCitation(citedNames="Tuckett", citedYear="200%")
            >>> print res[0]["Title"]
            Does anything go?: Towards a framework for the more transparent assessment of psychoanalytic competence

        """
        retVal = []
        errMsg = None

        self.__initDB__()

        if callerID != "":
            callerIDStr = "(" + callerID + "/" + "fetchFromCitation" + ") "
        else:
            callerIDStr = ""

        if citedYear!=None:
            yearClause = "  AND year like '%s'" % citedYear
        else:
            yearClause = ""

        selqry = """SELECT 	articleID,
                            arttype,
                            hdgauthor,
                            year,
                            hdgtitle,
                            srctitleseries,
                            jrnlcode,
                            publisher,
                            vol,
                            volsuffix,
                            issue,
                            pgrg,
                            pgstart,
                            pgend,
                            maintocID,
                            newsecname,
                            xmlRef,
                            MATCH hdgauthor AGAINST ('%s') AS authrel
                FROM articles
                  where MATCH hdgauthor AGAINST ('%s') > 1
                  %s
                  order by authrel desc
                """ % (sciSupport.doEscapes(citedNames), sciSupport.doEscapes(citedNames), yearClause)
        #print "QRY (citation): ", selqry
        dbc = self.biblioDB.db.cursor()
        dbc.execute(selqry)
        resultSet = dbc.fetchall()
        if len(resultSet) == 0:
            errMsg = "%sWARNING: No articles matched citedName: '%s'/citedYear: '%s'!" % (callerIDStr, citedNames, citedYear)
        else:
            if gDbg1: print("%s%s matches in PEP Articles for author %s found" % (callerIDStr, len(resultSet), citedNames))
            extendedMap = copy.copy(self.articleTableMap)
            extendedMap.append("MatchRelevance")
            for cursorRecord in resultSet:
                cdata = cursorRecord
                recData = fetchAndConvertToRefMeta(cdata, extendedMap)
                retVal.append(recData)

        dbc.close()
        if noLog==0 and errMsg!=None:
            self.hLog.logWarning(errMsg)

        if accumulate==0:
            self.refList = retVal
        else:
            self.refList += retVal

        return retVal

    #----------------------------------------------------------------------------------------
    def fetchArticleReferenceFromWhereClause(self, whereClause, accumulate=0, callerID="", altTable=None):
        """
        Search the PEP article table for article/book metadata, using supplied where clause.
         Return a list of matching ReferenceMetaData objects

        Note that the variant code, the last digit of the articleID, is not used in the search.
        """
        retVal = []
        localIDStr = None

        self.__initDB__()

        if altTable==None:
            qTable = "articles"
        else:
            qTable = "jourlitarticles"

        if not opasgenlib.is_empty(whereClause):
            # use entire key instead
            selqry = r"""select articleID,
                arttype,
                hdgauthor,
                year,
                hdgtitle,
                srctitleseries,
                jrnlcode,
                publisher,
                vol,
                volsuffix,
                issue,
                pgrg,
                pgstart,
                pgend,
                maintocID,
                newsecname,
                xmlRef
                from %s
                %s
                """ % (qTable, whereClause)

            dbc = self.biblioDB.db.cursor()
            dbc.execute(selqry)
            resultSet = dbc.fetchall()
            if len(resultSet) == 0:
                self.hLog.logWarning("Whereclause '%s' resulted in zero rows!" % whereClause)
            else:
                for cursorRecord in resultSet:
                    recData = fetchAndConvertToRefMeta(cursorRecord, self.articleTableMap)
                    if localIDStr!=None:
                        recData[gConst.LOCALID] = localIDStr
                    if recData[gConst.ISSUE] == "S":
                        recData[gConst.JOURNALVOLSUFFIX] = "S"
                    recData[gConst.REFINPEP] = 1
                    refLoc = PEPLocator.Locator(recData[gConst.KEY])
                    recData[gConst.REFTYPE] = refLoc.sourceType()
                    if len(resultSet)==1:
                        recData[gConst.EXACTMATCH] = 1
                        if gDbg1: print("fetchArticleReferenceFromWhereClause: ExactMatch Set")
                    else:
                        recData[gConst.EXACTMATCH] = 0
                    # A1v7 (added for a1v6 metadata export)
                    (recData[gConst.ISSN], recData[gConst.ISBN], recData[gConst.ISUN]) = self.biblioDB.getISSNISBN(refLoc)
                    #print "RecData: ", recData
                    retVal.append(recData)

            dbc.close()
        else: # may not want this, but try it.
            raise ValueError("Empty Where Clause.  Cannot fetch article reference info.")

        if accumulate==0:
            self.refList = retVal
        else:
            self.refList += retVal
        return self.refList

    #----------------------------------------------------------------------------------------
    def mostSimilar(self, baseRef, weightDict={}, threshold=None, verbose=0):
        """
        Walk through result list, find the one that's most similar.
        Return a RefMetaData object that is closest.
        Set confidencebool in refmetadata to reflect if this was a clear/statistical "winner".
        If no matches, return None.
        """
        retVal = None
        simList = []
        maxRef = None
        oldMaxRef = None
        maxSimVal = -1
        minPrecision = .05
        total = 0
        ss = 0
        sd = 0
        numStdDevsFromMean=1

        if self.refList == []:
            if gDbg1: print("WARNING: There are no matches to compare!")
            return retVal

        if threshold==None:
            threshold=self.minThreshold
        else:
            if threshold > 1:
                raise Exception("Programming Error: Threshold should be >0 and <1")

        sdThreshold = threshold

        if verbose:
            #print 10*"*" + "Start Most similar search." + 50*"*"
            #print "Search for: %s", baseRef[gConst.AUTHLIST], baseRef[gConst.TITLE]
            #print "Search for: %s", sciUnicode.unicode2Console(baseRef.formatRef(baseRef.DISPLAYSTYLEREF))
            print("Search: %s", baseRef.text())

        if weightDict == []:
            weightDict={gConst.AUTHORS: 70,
                        gConst.TITLE: 70,
                        gConst.SOURCETITLESERIES: 70,
                        gConst.SOURCETITLECITED: 50, # bookTitle
                        gConst.VOL: 20,
                        gConst.YEAR: 20,
                        gConst.PGSTART: 10,
                        gConst.PGEND: 0,
                        gConst.REFTYPE: 0,
                        gConst.ARTTYPE: 0,
                        gConst.EXACTMATCH:0}

        n = len(self.refList)
        count = 0
        if verbose:
            print("mostsimilar Looking For: %s / %s" % (baseRef[gConst.TITLE], baseRef[gConst.SOURCETITLECITED]))
            print("---")

        for ref in self.refList:
            count += 1
            #if 1: print "Comparing to: ", sciUnicode.unicode2Console(ref["Title"])
            if verbose: print("Comparing to reference: ", sciUnicode.unicode2Console(ref.formatRef(ref.DISPLAYSTYLEREF)))
            sim, ratios = baseRef.similarity(ref, weightDict=weightDict, verbose=verbose)
            ref[gConst.CONFIDENCELEVEL] = sim
            simList.append(sim)
            total += sim
            ss += sim**2
            if verbose: print("Comparing: %s / %s (simVal %s)" % (ref[gConst.TITLE], ref[gConst.SOURCETITLECITED], sim))
            if sim>maxSimVal:
                oldMaxRef = copy.copy(maxRef)
                maxRef = ref
                maxSimVal = sim	# new max

        simList.sort()
        #print "Highest 2 Entries: ", simList[-2:]
        # if the sample size is big enough, do it statistically

        if n>2: #and maxSimVal>0:
            mean = float(total/n)
        else:
            mean = total

        if n>4 and maxSimVal>0:
            if verbose: print("Using Statistical Threshold: %s" % sdThreshold)
            num = (ss - float((total**2)/n))
            sd = abs(float(num/n-1))**.5
            cdiff = numStdDevsFromMean*sd
            sdThreshold = min((cdiff)+mean, sdThreshold)
            if gDbg1: print("Min Statistical Threshold: %s, Mean: %s, SD: %s" % (sdThreshold, mean, sd))

        if verbose: #and verbose:  # verbose
            print(gLineLength*"-")
            print("Max: %s" % maxSimVal)
            print("MaxRef: %s" % maxRef)
            if n>2:
                print("Max2 (2nd highest): %s" % simList[-2])
                print("Max Item Separation: %f" % (maxSimVal-simList[-2]))
                print("Mean: %s" % mean)
            if n>4:
                print("SD: %s" % sd)

            print("Count: %s" % n)
            print("SD Threshold: %s" % sdThreshold)


        if maxSimVal>sdThreshold:
            if count>2:
                if maxSimVal-simList[-2]<minPrecision:
                    errtxt = "Statistical tie.  Nominal highest.\n\tMax: %s\n\tMax2 2nd: %s\n\tRef: %s" % (maxRef, oldMaxRef, baseRef)
                    if verbose:
                        print(self.hLog.logWarning(errtxt))

            # take it anyway
            self.bestMatch = maxRef
            if verbose:
                print("Searched: %s" % baseRef.text())
                print("Winner: ", maxRef.text())
            maxRef[gConst.CONFIDENCETHRESH] = sdThreshold
            maxRef[gConst.CONFIDENCEBOOL] = 1
        else:
            #self.bestMatch = None
            self.bestMatch = maxRef
            if gDbg1: print("No winner, confidence low (%s), best match: %s" % (maxSimVal, maxRef.text()))
            if maxRef!=None:
                maxRef[gConst.CONFIDENCEBOOL] = 0

        retVal = self.bestMatch
        if verbose:
            print(gLineLength*"*")
            print("Search Completed.  Best Match: " % retVal)
            print(gLineLength*"*")
        return retVal

    #----------------------------------------------------------------------------------------
    def guessArticleFromRefMetaData(self, baseRef, weightDict={}, verbose=0, callerID=""):
        """
        Use similarity matching built into the refMetaData object to find
            the refMetaData object in the list which is most similar.
        """

        #gDbg1 = 1

        articleIDPattern = baseRef.get(gConst.KEY, None)
        jrnlCode = baseRef.get(gConst.SOURCEPEPCODE, None)
        authors = baseRef.get(gConst.AUTHORS, None)
        title = baseRef.get(gConst.TITLE, None)
        jrnlVol = baseRef.get(gConst.VOL, None)
        jrnlYear = baseRef.get(gConst.YEAR, None)
        #pgStart = baseRef.get(gConst.PGSTART, None)
        retVal = None
        matchRef=None
        self.refList = [] # don't use what was in the list; queries below populate it.

        result=[]

        if baseRef.isBook() or not baseRef.isPEPJournal():  # forget about it if it's a book, or not a PEP journal
            if gDbg1: print("Book and not in PEP - No second guess.")
            retVal = None
        else:
            if gDbg1: print("This looks like it's in PEP - Trying Secondary Match.")
            if callerID != "":
                callerIDStr = "(" + callerID + "/" + "guess100" + ") "
            else:
                callerIDStr = ""

            #fetchArticleFromReferenceInfo(self, articleIDPattern=None, jrnlCode=None, authors=None, title=None, jrnlVol=None, jrnlYear=None, noLog=0):
            # we start with only basic restriction; to make sure we have some refs to pick from.
            # But we need to keep it down to a small amount to compare.
            # so we add some restrictions if there is no author list, or title
            if gDbg1:
                print("Guess Reference from Metadata")
                print("Starting with articleID: %s" % articleIDPattern)
            # start with common errors

            if jrnlVol != 0 and not opasgenlib.is_empty(articleIDPattern) and jrnlCode!="SE":
                result = self.fetchArticleReferenceFromArticleIDForceSuffix(articleIDPattern,
                                                                            noLog=1,
                                                                            callerID=callerID)
                matchRef = self.mostSimilar(baseRef, weightDict=weightDict, verbose=0)

                # for debugging what works with references
                if gDbg1:
                    if matchRef != None: print("Successful reference link guess via fetch...force Suffix")

            if matchRef==None:
                # try to force year
                if not opasgenlib.is_empty(articleIDPattern) and jrnlCode!="SE":
                    result = self.fetchArticleReferenceFromArticleIDForceYear(articleIDPattern,
                                                                              jrnlCode,
                                                                              jrnlYear,
                                                                              noLog=1,
                                                                              callerID=callerID)

                    # see if we already have a winner.  Otherwise, keep looking
                    matchRef = self.mostSimilar(baseRef, weightDict=weightDict, verbose=0)

                    # for debugging what works with references
                    if gDbg1:
                        if matchRef != None: print("Successful reference link guess via fetch...force Year")

                if matchRef==None:
                    # try journal "equivalents"
                    if not opasgenlib.is_empty(articleIDPattern) and jrnlCode!="SE":
                        if gDbg1: print("Trying Journal Equivalents")

                        if jrnlCode == "IJP":
                            self.fetchArticleReferenceFromArticleIDForceJournal(articleIDPattern,
                                                                                "IRP",
                                                                                noLog=1,
                                                                                callerID=callerID)
                            self.fetchArticleReferenceFromArticleIDForceJournal(articleIDPattern,
                                                                                "BIP", accumulate=1,
                                                                                noLog=1,
                                                                                callerID=callerID)
                        elif jrnlCode == "BIP":
                            self.fetchArticleReferenceFromArticleIDForceJournal(articleIDPattern,
                                                                                "IRP",
                                                                                noLog=1,
                                                                                callerID=callerID)
                            self.fetchArticleReferenceFromArticleIDForceJournal(articleIDPattern,
                                                                                "IJP", accumulate=1,
                                                                                noLog=1,
                                                                                callerID=callerID)
                        elif jrnlCode == "IRP":
                            self.fetchArticleReferenceFromArticleIDForceJournal(articleIDPattern,
                                                                                "IJP", accumulate=1,
                                                                                noLog=1,
                                                                                callerID=callerID)
                            self.fetchArticleReferenceFromArticleIDForceJournal(articleIDPattern,
                                                                                "BIP", accumulate=1,
                                                                                noLog=1,
                                                                                callerID=callerID)
                        elif jrnlCode == "BAP":
                            self.fetchArticleReferenceFromArticleIDForceJournal(articleIDPattern,
                                                                                "APA",
                                                                                noLog=1,
                                                                                callerID=callerID)
                        elif jrnlCode == "APA":
                            self.fetchArticleReferenceFromArticleIDForceJournal(articleIDPattern,
                                                                                "BAP", accumulate=1,
                                                                                noLog=1,
                                                                                callerID=callerID)

                        # see if we already have a winner.  Otherwise, keep looking
                        matchRef = self.mostSimilar(baseRef, weightDict=weightDict, verbose=0)

                        # for debugging what works with references
                        if gDbg1:
                            if matchRef != None: print("Successful reference link guess via fetch...Journal Equivalents")

                    if matchRef==None:
                        # Second strategy.  General search
                        if gDbg1: print("Trying Second Strategy!!!!***************************************************")

                        if not opasgenlib.is_empty(title) and not opasgenlib.is_empty(jrnlCode) and not opasgenlib.is_empty(authors):
                            if gDbg1: print("Trying author, title and journal search: (%s/%s)" % (sciUnicode.unicode2Console(title), jrnlCode))
                            result = self.fetchArticleFromReferenceInfo(authors=authors,
                                                                        title=title,
                                                                        jrnlCode=jrnlCode,
                                                                        callerID=callerID,
                                                                        noLog=1
                                                                        )

                        elif not opasgenlib.is_empty(title) and not opasgenlib.is_empty(authors):
                            if gDbg1:
                                print("Trying author, title search: (%s/%s)" % (sciUnicode.unicode2Console(authors), sciUnicode.unicode2Console(title)))
                            result = self.fetchArticleFromReferenceInfo(authors=authors,
                                                                        title=title,
                                                                        callerID=callerID,
                                                                        noLog=1
                                                                        )

                        elif not opasgenlib.is_empty(title) and not opasgenlib.is_empty(jrnlCode):
                            if gDbg1: print("Trying title and journal search: (%s/%s)" % (sciUnicode.unicode2Console(title), jrnlCode))
                            result = self.fetchArticleFromReferenceInfo(title=title,
                                                                        jrnlCode=jrnlCode,
                                                                        callerID=callerID,
                                                                        noLog=1
                                                                        )
                        elif not opasgenlib.is_empty(title):
                            if gDbg1: print("Trying title search: (%s)" % sciUnicode.unicode2Console(title))
                            result = self.fetchArticleFromReferenceInfo(authors=authors,
                                                                        title=title,
                                                                        callerID=callerID,
                                                                        noLog=1
                                                                        )
                            if result==[]:	# just try title and year
                                self.fetchArticleFromReferenceInfo(title=title,
                                                                   jrnlYear=jrnlYear,
                                                                   accumulate=0,
                                                                   callerID=callerID,
                                                                   noLog=1
                                                                   )

                        elif not opasgenlib.is_empty(jrnlCode):	# try to limit via journal code too
                            if gDbg1: print("Trying jrnlCode search:")
                            self.fetchArticleFromReferenceInfo(authors=authors,
                                                               title=title,
                                                               jrnlCode=jrnlCode,
                                                               accumulate=0,
                                                               callerID=callerID,
                                                               noLog=1
                                                               )
                        elif not opasgenlib.is_empty(jrnlYear):	# try to limit via year too
                            if gDbg1: print("Trying jrnlYear search:")
                            self.fetchArticleFromReferenceInfo(authors=authors,
                                                               title=title,
                                                               jrnlYear=jrnlYear,
                                                               accumulate=0,
                                                               callerID=callerID,
                                                               noLog=1
                                                               )
                        else:
                            if gDbg1: print("Too few fields available to guess (%s)" % baseRef)		   # was raise

                        # see if we already have a winner.  Otherwise, keep looking
                        matchRef = self.mostSimilar(baseRef, weightDict=weightDict, verbose=0)

                        # for debugging what works with references
                        if gDbg1:
                            if matchRef != None: print("Successful reference link guess via fetch...limited info")

                        if matchRef==None:
                            # we haven't found any matches; decide what to do here!
                            # try third strategy--general search with new journal codes
                            if gDbg1: print("Trying THIRD Strategy!!!!***************************************************")

                            if jrnlCode=="IJP" or jrnlCode=="BIP" or jrnlCode=="IRP":
                                self.fetchArticleFromReferenceInfo(jrnlCode="IRP",
                                                                   jrnlYear=jrnlYear,
                                                                   noLog=1
                                                                   )
                                self.fetchArticleFromReferenceInfo(jrnlCode="IJP",
                                                                   jrnlYear=jrnlYear,
                                                                   noLog=1,
                                                                   accumulate=1
                                                                   )
                                self.fetchArticleFromReferenceInfo(jrnlCode="BIP",
                                                                   jrnlYear=jrnlYear,
                                                                   noLog=1,
                                                                   accumulate=1
                                                                   )
                            elif jrnlCode=="APA" or jrnlCode=="BAP":
                                self.fetchArticleFromReferenceInfo(jrnlCode="APA",
                                                                   jrnlYear=jrnlYear,
                                                                   noLog=1,
                                                                   )
                                self.fetchArticleFromReferenceInfo(jrnlCode="BAP",
                                                                   jrnlYear=jrnlYear,
                                                                   accumulate=1,
                                                                   noLog=1
                                                                   )
                            else:
                                self.fetchArticleFromReferenceInfo(jrnlCode=jrnlCode,
                                                                   jrnlYear=jrnlYear,
                                                                   accumulate=1,
                                                                   noLog=1
                                                                   )

                            matchRef = self.mostSimilar(baseRef, weightDict=weightDict, verbose=0)

                            # for debugging what works with references
                            if gDbg1:
                                if matchRef != None: print("Successful reference link guess via fetch...force Year")

            if matchRef==None:
                errMsg = "+++ No matches at all for (%s)!" % baseRef
                if verbose==1:
                    print(self.hLog.logSevere(errMsg))
                retVal = None
                #raise errMsg
            else:
                retVal = matchRef

        return retVal

    #----------------------------------------------------------------------------------------
    def fetchArticleFromRefereinceInfo2018(self, baseRef, articleIDContainingReference = "%", authorPriority=False, accumulate=0):
        """
        Given an XML formatted reference, use full-text to match against the PEP Articles Database

        Returns: a list of matches or the empty list []
                 If parameter accumulate != 0, adds the references to the data list of the current object
                 If parameter accumulate == 0, replaces the references of the current object with the return list

        >> pepArticleList = PEPArticleListDB()
        >> print pepArticleList.fetchArticleFromRefereinceInfo2018(authorPriority=True, articleIDContainingReference="PPERSP.011.0058A", title="Deconstructing the myth of the neutral analyst: An alternative from intersubjective systems theory", authors="Stolorow , R. D. Atwood , G. E")

        """

        retVal = []
        self.__initDB__()
        title = baseRef.get(gConst.TITLE, None)
        if title == "" or title == None:
            title = baseRef.get(gConst.SOURCETITLECITED, None)
        authors = baseRef.get(gConst.AUTHORS, None)
        jrnlCode = baseRef.get(gConst.SOURCEPEPCODE, None)
        jrnlVol = baseRef.get(gConst.VOL, None)
        jrnlYear = baseRef.get(gConst.YEAR, None)

        if title == None:
            title = ""
        else:
            title = sciSupport.removeSingleQuotes(title)

        if authors == None:
            authors = ""
        else:
            authors = sciSupport.removeSingleQuotes(authors)

        errMsg = None

        if authorPriority:
            preciseAuthorclause = """ AND MATCH hdgauthor AGAInST ('%s') > 0""" % authors
        else:
            preciseAuthorclause = ""

        # first try just the article ID if supplied...that is the most precise.
        if 1:
            selqry = """SELECT articleID,
                              arttype,
                              hdgauthor,
                              year,
                              hdgtitle,
                              srctitleseries,
                              jrnlcode,
                              publisher,
                              vol,
                              volsuffix,
                              issue,
                              pgrg,
                              pgstart,
                              pgend,
                              maintocID,
                              newsecname,
                              MATCH hdgtitle AGAINST ('%s' with query expansion) as relTitle,
                              MATCH hdgauthor AGAInST ('%s') as relAuthor
                      FROM articles
                      WHERE (
                            match hdgtitle against ('%s' with query expansion) > 5
                            %s
                            )
                            OR
                            MATCH hdgauthor AGAInST ('%s') > 0
                            OR
                            articleID in (select SUBSTRING_INDEX(bibliofulllocalrefID,".",3) from biblioLinks where referencedID like '%s')
                            order by reltitle DESC, relAuthor DESC
                            LIMIT 4;
                """ % (title,
                       authors,
                       title,
                       preciseAuthorclause,
                       authors,
                       articleIDContainingReference
                    )

        if gDbg1: print("Query: ", selqry)

        dbc = self.biblioDB.db.cursor()
        dbc.execute(selqry)
        resultSet = dbc.fetchall()
        if len(resultSet) == 0:
            if 1: errMsg = "WARNING: No articles matched! (findArticleFromReferenceInfo)"
        else:
            if gDbg1: print("%s matches found" % (len(resultSet)))
            for cursorRecord in resultSet:
                # hack off match fields
                resultTypeLoc = PEPLocator.Locator(cursorRecord[0])
                recData = fetchAndConvertToRefMeta(cursorRecord[:-2], self.articleTableMap)
                # FMI just to see if this is a better confidence score
                #RELATEDSQLCONFTITLE = "RelatedSQLConfTitle"
                #RELATEDSQLCONFAUTHOR = "RelatedSQLConfAuthor"
                #RELATEDSQLCONFXMLSTRING = "RelatedSQLConfXMLString"
                recData[self.RELATEDSQLCONFTITLE] = cursorRecord[-2]
                recData[self.RELATEDSQLCONFAUTHOR] = cursorRecord[-1]
                retVal.append(recData)

            if gDbg1:
                print("%sResults: " % callerID)
                if len(retVal) == 1:
                    print(retVal)
                else:
                    for n in retVal:
                        print(repr(n))

        dbc.close()
        if errMsg!=None:
            if noLog==0:
                gErrorLog.logWarning(errMsg)

        if accumulate==0:
            self.refList = retVal
        else:
            self.refList += retVal

        return retVal

    #----------------------------------------------------------------------------------------
    def fetchArticleFromRefMetaData(self, baseRef):

        retVal = []
        articleIDPattern = baseRef.get(gConst.KEY, None)
        jrnlCode = baseRef.get(gConst.SOURCEPEPCODE, None)
        bookTitle = baseRef.get(gConst.SOURCETITLECITED, None)
        authors = baseRef.get(gConst.AUTHORS, None)
        title = baseRef.get(gConst.TITLE, None)
        publisher = baseRef.get(gConst.PUBLISHER, None)
        jrnlVol = baseRef.get(gConst.VOL, None)
        jrnlYear = baseRef.get(gConst.YEAR, None)
        if title == "":
            title = baseRef.get(gConst.SOURCETITLECITED, None)

        # first try just the article ID if supplied...that is the most precise.
        if articleIDPattern != None:
            retVal = self.fetchArticleFromReferenceInfo(articleIDPattern=articleIDPattern,
                                                        noLog=0)

        if retVal == [] and bookTitle != None:
            # try for a book first
            if title != None:
                retVal = self.fetchArticleFromReferenceInfo(authors=authors,
                                                            title = title,
                                                            bktitle=bookTitle,
                                                            noLog=0)

            if retVal == []:
                retVal = self.fetchArticleFromReferenceInfo(authors=authors,
                                                            bktitle=bookTitle,
                                                            noLog=0)

            if retVal == []:
                retVal = self.fetchArticleFromReferenceInfo(authors=authors,
                                                            title=bookTitle,
                                                            noLog=0)

        if retVal == [] and publisher != None: # don't search publisher, but use it to suggest this is a book
            # try for a book without a book title but with a publisher
            retVal = self.fetchArticleFromReferenceInfo(authors=authors,
                                                        bktitle=title,
                                                        noLog=0)
        if retVal == []:
            retVal = self.fetchArticleFromReferenceInfo(articleIDPattern=articleIDPattern,
                                                        jrnlCode=jrnlCode,
                                                        authors=authors,
                                                        title=title,
                                                        jrnlVol=jrnlVol,
                                                        jrnlYear=jrnlYear,
                                                        noLog=0)

        if retVal == []:
            # try it with less criteria
            retVal = self.fetchArticleFromReferenceInfo(jrnlCode=jrnlCode,
                                                        authors=authors,
                                                        title=title,
                                                        noLog=0)

        if retVal == []:
            # try it with less criteria
            retVal = self.fetchArticleFromReferenceInfo(authors=authors,
                                                        title=title,
                                                        bktitle=bookTitle,
                                                        noLog=0)

        if retVal == []:
            # try it with less criteria
            retVal = self.fetchArticleFromReferenceInfo(jrnlCode=jrnlCode,
                                                        title=title,
                                                        noLog=0)

        if retVal == []: # try this one again
            # try it with less criteria
            retVal = self.fetchArticleFromReferenceInfo(authors=authors,
                                                        bktitle=title,
                                                        noLog=0)


        return retVal

    #----------------------------------------------------------------------------------------
    def fetchArticleFromXMLRef(self, xmlRef, isProbablyBook=None, noLog=0, accumulate=0, callerID=""):
        """
        Given an XML formatted reference, use full-text to match against the PEP Articles Database
        Returns a list of matching references in XML

        >>> pepArticleList = PEPArticleListDB()

        >>> print pepArticleList.fetchArticleFromXMLRef(xmlRef=u'<be label="1" id="B0001"><a><l>Abraham</l>, K.</a> <t>\\u201cA Constitutional Basis of Locomotor Anxiety,\\u201d</t> <bst>Selected Papers</bst>, <bp>Hogarth</bp>, <bpd>1942</bpd>.</be>'.encode("utf"))
        []

        >>> print pepArticleList.fetchArticleFromXMLRef(xmlRef='<be id="B0015"><a><l>Ornstein</l>, A.</a> (<y>1986</y>). <t>The Holocaust: Reconstruction and the establishment of psychic continuity</t>. In A. Rothstein (Ed.), <bst>The reconstruction of trauma: The significance of clinical work</bst> (pp. <pp>171-191</pp>). New York: <bp>International Universities Press</bp>.</be>', isProbablyBook = True)
        [{'publisher': u'', 'PgStart': 171, 'PgEnd': 191, 'PgRg': u'171-191', 'Title': u'Chapter 11: The Holocaust: Reconstruction and the Establishment of Psychic Continuity', 'Vol': 80, 'JournalCode': u'ZBK', 'Authors': u'Ornstein, A.', 'RelatedSQLConfXMLString': 46.24394607543945, 'MAINTOCID': u'ZBK.080.0000A', 'ArticleType': u'ART', 'Key': u'ZBK.080.0171A', 'Year': u'1986', 'VolSuffix': u'', 'Issue': u'', 'SourceTitleSeries': u'Classic Books', 'NewSecName': None, 'XMLRef': u"<be rx='ZBK.080.0171A' class='refinspeb'><a>Ornstein, A.</a> (<y>1986</y>). <t>Chapter 11: The Holocaust: Reconstruction and the Establishment of Psychic Continuity</t>.In: <j>Classic Books</j> <v>80</v>:<pp>171-191</pp></be>"}, {'publisher': u'', 'PgStart': 0, 'PgEnd': 268, 'PgRg': u'1-268', 'Title': u'The Reconstruction of Trauma: Its Significance in Clinical Work', 'Vol': 80, 'JournalCode': u'ZBK', 'Authors': u'Rothstein, A.', 'RelatedSQLConfXMLString': 38.430389404296875, 'MAINTOCID': None, 'ArticleType': u'TOC', 'Key': u'ZBK.080.0000A', 'Year': u'1986', 'VolSuffix': u'', 'Issue': u'', 'SourceTitleSeries': u'Classic Books', 'NewSecName': None, 'XMLRef': u"<be rx='ZBK.080.0000A' class='refinspb'><a>Rothstein, A.</a> (<y>1986</y>). <t>The Reconstruction of Trauma: Its Significance in Clinical Work</t>.</be>"}]

        >>> print pepArticleList.fetchArticleFromXMLRef(xmlRef='<be id="B0087"><a><l>Rustin</l>, M.</a> (<y>1987</y>). <t>Mattie as an educator.</t> <bst>Collected Papers of Martha Harris and Esther Bick</bst>, ed. <bsa><a>M. H. <l>Williams</l></a></bsa>, pp. <pp>ix-xiii</pp>. Perthshire: <bp>Clunie Press</bp>, <bpd>1987</bpd>. Reprint in press in <binc class="na"><bst>Enabling and Inspiring</bst>, ed. <a>M. H. <l>Williams</l></a> et al.</binc></be>', isProbablyBook = True)
        []

        >>> print pepArticleList.fetchArticleFromXMLRef(xmlRef='<be lang="en" rxp="IJP.013.0298A" id="B0020"><a>Glover, Edward</a> <t>"The Aetiology of Drug Addiction"</t> <j>Int. J. Psychoanal.</j> Vol. XIII</be>')
        [{'publisher': u'', 'PgStart': 298, 'PgEnd': 328, 'PgRg': u'298-328', 'Title': u'On the Aetiology of Drug-Addiction', 'Vol': 13, 'JournalCode': u'IJP', 'Authors': u'Glover, E.', 'RelatedSQLConfXMLString': 31.173330307006836, 'MAINTOCID': None, 'ArticleType': u'ART', 'Key': u'IJP.013.0298A', 'Year': u'1932', 'VolSuffix': u'', 'Issue': u'', 'SourceTitleSeries': u'Int. J. Psychoanal.', 'NewSecName': None, 'XMLRef': u"<be rx='IJP.013.0298A' class='refinspj'><a>Glover, E.</a> (<y>1932</y>). <t>On the Aetiology of Drug-Addiction</t>. <j>International Journal of Psycho-Analysis</j> <v>13</v>:<pp>298-328</pp></be>"}]

        >>> print pepArticleList.fetchArticleFromXMLRef(xmlRef='<be rx="ZBK.133.0133A" class="refinspeb"><a>Bick, E.</a> (<y>2011</y>). <t>Chapter Nine: The Experience of the Skin in Early Object Relations (1968)</t>.In: <j>Classic Books</j> <v>133</v>:<pp>133-138</pp></be>', isProbablyBook = True)
        [{'publisher': u'', 'PgStart': 133, 'PgEnd': 138, 'PgRg': u'133-138', 'Title': u'Chapter Nine: The Experience of the Skin in Early Object Relations (1968)', 'Vol': 133, 'JournalCode': u'ZBK', 'Authors': u'Bick, E.', 'RelatedSQLConfXMLString': 55.25883865356445, 'MAINTOCID': u'ZBK.133.0000A', 'ArticleType': u'ART', 'Key': u'ZBK.133.0133A', 'Year': u'2011', 'VolSuffix': u'', 'Issue': u'', 'SourceTitleSeries': u'Classic Books', 'NewSecName': None, 'XMLRef': u"<be rx='ZBK.133.0133A' class='refinspeb'><a>Bick, E.</a> (<y>2011</y>). <t>Chapter Nine: The Experience of the Skin in Early Object Relations (1968)</t>.In: <j>Classic Books</j> <v>133</v>:<pp>133-138</pp></be>"}]

        >>> print pepArticleList.fetchArticleFromXMLRef(xmlRef='<binc id="B003"><a><l>Freud</l>, Sigmund</a>, <t>&ldquo;The Prehistory of Analytie Technique&rdquo;,</t> <bst>Standard Edition of Complete Psychological Works</bst>. (Lond. <y>1953</y>) <v>IV</v>, p. <pp>103</pp></binc>', isProbablyBook = True)
        [{'publisher': u'', 'PgStart': 0, 'PgEnd': VII, 'PgRg': u'1-vii', 'Title': u'The Standard Edition of the Complete Psychological Works of Sigmund Freud, Volume XII (1911-1913): The Case of Schreber, Papers on Technique and Other Works', 'Vol': 12, 'JournalCode': u'SE', 'Authors': u'Strachey, J., Freud, A., Strachey, A. and Tyson, A.', 'RelatedSQLConfXMLString': 36.19141387939453, 'MAINTOCID': None, 'ArticleType': u'TOC', 'Key': u'SE.012.0000A', 'Year': u'1958', 'VolSuffix': u'', 'Issue': u'', 'SourceTitleSeries': u'Standard Edition', 'NewSecName': None, 'XMLRef': u"<be rx='SE.012.0000A' class='refinsbs'><a>Strachey, J., Freud, A., Strachey, A. and Tyson, A.</a> (<y>1958</y>). <t>The Standard Edition of the Complete Psychological Works of Sigmund Freud, Volume XII (1911-1913): The Case of Schreber, Papers on Technique and Other Works</t>. <j>Standard Edition</j> <v>12</v>:<pp>1-vii</pp></be>"}, {'publisher': u'', 'PgStart': 0, 'PgEnd': VI, 'PgRg': u'1-vi', 'Title': u'The Standard Edition of the Complete Psychological Works of Sigmund Freud, Volume VII (1901-1905): A Case of Hysteria, Three Essays on Sexuality and Other Works', 'Vol': 7, 'JournalCode': u'SE', 'Authors': u'Strachey, J., Freud, A., Strachey, A. and Tyson, A.', 'RelatedSQLConfXMLString': 35.85244369506836, 'MAINTOCID': None, 'ArticleType': u'TOC', 'Key': u'SE.007.0000A', 'Year': u'1953', 'VolSuffix': u'', 'Issue': u'', 'SourceTitleSeries': u'Standard Edition', 'NewSecName': None, 'XMLRef': u"<be rx='SE.007.0000A' class='refinsbs'><a>Strachey, J., Freud, A., Strachey, A. and Tyson, A.</a> (<y>1953</y>). <t>The Standard Edition of the Complete Psychological Works of Sigmund Freud, Volume VII (1901-1905): A Case of Hysteria, Three Essays on Sexuality and Other Works</t>. <j>Standard Edition</j> <v>7</v>:<pp>1-vi</pp></be>"}, {'publisher': u'', 'PgStart': 0, 'PgEnd': XIII, 'PgRg': u'1-xiii', 'Title': u'The Standard Edition of the Complete Psychological Works of Sigmund Freud, Volume IV (1900): The Interpretation of Dreams (First Part)', 'Vol': 4, 'JournalCode': u'SE', 'Authors': u'Strachey, J., Freud, A., Strachey, A. and Tyson, A.', 'RelatedSQLConfXMLString': 33.942222595214844, 'MAINTOCID': None, 'ArticleType': u'TOC', 'Key': u'SE.004.0000A', 'Year': u'1953', 'VolSuffix': u'', 'Issue': u'', 'SourceTitleSeries': u'Standard Edition', 'NewSecName': None, 'XMLRef': u"<be rx='SE.004.0000A' class='refinsbs'><a>Strachey, J., Freud, A., Strachey, A. and Tyson, A.</a> (<y>1953</y>). <t>The Standard Edition of the Complete Psychological Works of Sigmund Freud, Volume IV (1900): The Interpretation of Dreams (First Part)</t>. <j>Standard Edition</j> <v>4</v>:<pp>1-xiii</pp></be>"}, {'publisher': u'', 'PgStart': 0, 'PgEnd': IV, 'PgRg': u'1-iv', 'Title': u'The Standard Edition of the Complete Psychological Works of Sigmund Freud, Volume V (1900-1901): The Interpretation of Dreams (Second Part) and On Dreams', 'Vol': 5, 'JournalCode': u'SE', 'Authors': u'Strachey, J., Freud, A., Strachey, A. and Tyson, A.', 'RelatedSQLConfXMLString': 32.89498519897461, 'MAINTOCID': None, 'ArticleType': u'TOC', 'Key': u'SE.005.0000A', 'Year': u'1953', 'VolSuffix': u'', 'Issue': u'', 'SourceTitleSeries': u'Standard Edition', 'NewSecName': None, 'XMLRef': u"<be rx='SE.005.0000A' class='refinsbs'><a>Strachey, J., Freud, A., Strachey, A. and Tyson, A.</a> (<y>1953</y>). <t>The Standard Edition of the Complete Psychological Works of Sigmund Freud, Volume V (1900-1901): The Interpretation of Dreams (Second Part) and On Dreams</t>. <j>Standard Edition</j> <v>5</v>:<pp>1-iv</pp></be>"}]
        """
        retVal = []
        errMsg = None
        orderByClause = "order by xmlRefMatch DESC LIMIT 5"

        self.__initDB__()
        sqlSafeXMLRef = sciSupport.removeSingleQuotes(xmlRef)
        #escXMLRef = sciSupport.doEscapes(xmlRef)
        xmlRefClause = """ and MATCH xmlref AGAINST ('%s') > 1""" % sqlSafeXMLRef
        xmlRefSelect = """MATCH xmlref AGAINST ('%s') as xmlRefMatch""" % sciSupport.removeSingleQuotes(sqlSafeXMLRef )

        #articleTableMap = [	gConst.KEY,
                                   #gConst.ARTTYPE,
                                   #gConst.AUTHORS,
                                   #gConst.YEAR,
                                   #gConst.TITLE,
                                   #gConst.SOURCETITLESERIES,
                                   #gConst.SOURCEPEPCODE,
                                   #gConst.PUBLISHER,
                                   #gConst.VOL,
                                   #gConst.VOLSUFFIX,
                                   #gConst.ISSUE,
                                   #gConst.PGRG,
                                   #gConst.PGSTART,
                                   #gConst.PGEND,
                                   #gConst.MAINTOCID,
                                   #gConst.NEWSECNAME
                                   #]

        selqry = """SELECT 	articleID,
                          arttype,
                          hdgauthor,
                          year,
                          hdgtitle,
                          srctitleseries,
                          jrnlcode,
                          publisher,
                          vol,
                          volsuffix,
                          issue,
                          pgrg,
                          pgstart,
                          pgend,
                          maintocID,
                          newsecname,
                          xmlref,
                          %s
                  FROM articles
                  WHERE 1=1
                  %s
                  %s
                """ % (
                       xmlRefSelect,
                       xmlRefClause,
                       orderByClause
                       )

        if gDbg1: print("Query: ", selqry)

        dbc = self.biblioDB.db.cursor()
        dbc.execute(selqry)
        resultSet = dbc.fetchall()
        if len(resultSet) == 0:
            if 0: errMsg = "%sWARNING: No articles matched! (findArticleFromReferenceInfo)" % callerID
        else:
            for cursorRecord in resultSet:
                if cursorRecord[-1] < 30: # arbitrary threshold - I think it's not a good match
                    break
                # hack off match fields
                resultTypeLoc = PEPLocator.Locator(cursorRecord[0])
                resultTypeBook = resultTypeLoc.isBook()
                if isProbablyBook != None:
                    if isProbablyBook != resultTypeBook:
                        continue # skip it, they are not the same type
                recData = fetchAndConvertToRefMeta(cursorRecord[:-1], self.articleTableMap)
                #RELATEDSQLCONFXMLSTRING = "RelatedSQLConfXMLString"
                recData[self.RELATEDSQLCONFXMLSTRING] = cursorRecord[-1]
                retVal.append(recData)

            # if 1: print "%s FetchArticleFromXMLRef matches found" % (len(retVal))
            if gDbg1:
                print("%sResults: " % callerID)
                for n in retVal:
                    print(n[gConst.KEY], n[gConst.AUTHORS], n[gConst.YEAR], n[gConst.TITLE], n[gConst.AUTHORS])

        dbc.close()
        if errMsg!=None:
            if noLog==0:
                gErrorLog.logWarning(errMsg)

        if accumulate==0:
            self.refList = retVal
        else:
            self.refList += retVal

        return retVal


    #----------------------------------------------------------------------------------------
    def fetchArticleFromReferenceInfo(self, articleIDPattern=None, jrnlCode=None, authors=None, title=None, jrnlVol=None, jrnlYear=None, pgStart=None, bkauthors=None, bktitle=None, bkpublisher=None, isProbablyBook=None, noLog=0, accumulate=0, callerID=""):
        """
        Search the reference database for an article based on incomplete information (whatever's provided
        Return a list of matching biblio tuples that match, ordred by probability of matching.

        >>> pepArticleList = PEPArticleListDB()

        >>> print pepArticleList.fetchArticleFromReferenceInfo(authors="Abraham, K.", title="Ansätze zur psychoanalytischen Erforschung und Behandlung des manisch-depressiven Irreseins und verwandter Zustände.")

        >>> print pepArticleList.fetchArticleFromReferenceInfo(authors="Ornstein", title="The holocaust: Reconstruction and the establishment of psychic continuity")

        >>> print pepArticleList.fetchArticleFromReferenceInfo(authors="Glover", title="On the Aetiology of Drug-Addiction")

        >>> print pepArticleList.fetchArticleFromReferenceInfo(jrnlCode="APA", authors="Walderhorn", title="The silent patient")

        """
        retVal = []
        errMsg = None

        self.__initDB__()

        bibIDClause = ""
        jrnlCodeClause = ""
        authorsClause = ""
        titleClause = ""
        jrnlVolClause = ""
        jrnlYearClause = ""
        pgRangeClause = ""

        if articleIDPattern!=None: 		bibIDClause = """ and articleID like '%s'""" % articleIDPattern
        if jrnlCode!=None: 				jrnlCodeClause = """ and jrnlCode like '%s'""" % jrnlCode
        if pgStart!=None:
            pgRangeClause = """ and   ((pgstart-2 < %s) AND (pgend > %s))""" % (pgStart, pgStart)

        if not opasgenlib.is_empty(authors):
            escAuthors = sciSupport.doEscapes(authors)
            authorsClause = """ and MATCH hdgauthor AGAINST ('%s') > 1""" % escAuthors
            authorsSelect = """MATCH hdgauthor AGAINST ('%s') as relAuthor""" % escAuthors
        else:
            authorsSelect = """1 as relAuthor"""

        if not opasgenlib.is_empty(bktitle):
            escbktitle = sciSupport.doEscapes(bktitle)
            bktitleClause = """ and MATCH bktitle AGAINST ('%s') > 1""" % escbktitle
            bktitleSelect = """MATCH bktitle AGAINST ('%s') as relBookTitle""" % escbktitle
        else:
            bktitleSelect = """1 as relBookTitle"""

        if not opasgenlib.is_empty(bkauthors):
            escbkauthors = sciSupport.doEscapes(bkauthors)
            bkauthorsClause = """ and MATCH bkauthors AGAINST ('%s') > 1""" % escbkauthors
            bkauthorsSelect = """MATCH bkauthors AGAINST ('%s') as relBookAuthors""" % escbkauthors
        else:
            bkauthorsSelect = """1 as relBookAuthors"""

        if not opasgenlib.is_empty(title):
            escTitle = sciSupport.doEscapes(title)
            titleClause = """ and MATCH hdgtitle AGAINST ('%s') > 10""" % escTitle
            titleSelect = """MATCH hdgtitle AGAINST ('%s') as relTitle""" % escTitle
        else:
            titleSelect = """1 as relTitle"""

        orderByClause = "order by relAuthor, relTitle DESC, pgstart ASC LIMIT 10"
        if jrnlVol!=None and jrnlVol!=0: 				jrnlVolClause = """ and vol = %s""" % jrnlVol
        if jrnlYear!=None:
            jrnlYear = sciDocuments.PubYear(jrnlYear)
            jrnlYearClause = """ and year like '%s'""" % jrnlYear

        selqry = """SELECT 	articleID,
                          arttype,
                          hdgauthor,
                          year,
                          hdgtitle,
                          srctitleseries,
                          jrnlcode,
                          publisher,
                          vol,
                          volsuffix,
                          issue,
                          pgrg,
                          pgstart,
                          pgend,
                          maintocID,
                          newsecname,
                          xmlref,
                          %s,
                          %s
                  FROM articles
                  WHERE 1=1
                  %s
                  %s
                  %s
                  %s
                  %s
                  %s
                  %s
                  %s
                """ % (authorsSelect,
                       titleSelect,
                       bibIDClause,
                       jrnlCodeClause,
                       authorsClause,
                       titleClause,
                       jrnlVolClause,
                       jrnlYearClause,
                       pgRangeClause,
                       orderByClause
                       )

        if gDbg1: print("Query: ", selqry)

        dbc = self.biblioDB.db.cursor()
        dbc.execute(selqry)
        resultSet = dbc.fetchall()
        if len(resultSet) == 0:
            if 0: errMsg = "%sWARNING: No articles matched! (findArticleFromReferenceInfo)" % callerID
        else:
            if gDbg1: print("%s matches found" % (len(resultSet)))
            for cursorRecord in resultSet:
                # hack off match fields
                resultTypeLoc = PEPLocator.Locator(cursorRecord[0])
                resultTypeBook = resultTypeLoc.isBook()
                if isProbablyBook != None:
                    if isProbablyBook != resultTypeBook:
                        continue # skip it, they are not the same type
                recData = fetchAndConvertToRefMeta(cursorRecord[:-2], self.articleTableMap)
                #RELATEDSQLCONFTITLE = "RelatedSQLConfTitle"
                #RELATEDSQLCONFAUTHOR = "RelatedSQLConfAuthor"
                #RELATEDSQLCONFXMLSTRING = "RelatedSQLConfXMLString"
                recData[self.RELATEDSQLCONFAUTHOR] = cursorRecord[-2]
                recData[self.RELATEDSQLCONFTITLE] = cursorRecord[-1]
                retVal.append(recData)

            if gDbg1:
                print("%sResults: " % callerID)
                if len(retVal) == 1:
                    print(retVal)
                else:
                    for n in retVal:
                        print(repr(n))

        dbc.close()
        if errMsg!=None:
            if noLog==0:
                gErrorLog.logWarning(errMsg)

        if accumulate==0:
            self.refList = retVal
        else:
            self.refList += retVal

        return retVal

def fetchAndConvertToRefMeta(cursorRecord, referenceFieldMap):
    """
    Convenience function to take care of housekeeping (eg. converting longs)
    after grabbing a record and converting it to ReferenceMetaData.

    Returns a refMeta object
    """

    retVal = ReferenceMetaData(cursorRecord, referenceFieldMap)
    try: # convert from long
        retVal[gConst.VOL] = int(retVal[gConst.VOL])
        retVal[gConst.PGSTART] = sciDocuments.PageNumber(retVal[gConst.PGSTART])
        retVal[gConst.PGEND] = sciDocuments.PageNumber(retVal[gConst.PGEND])
    except TypeError as e:
        print("Warning: Fetch (PEPArticleListDB) Type Error: ", e)
        #pass

    return retVal


#==================================================================================================
# Main Standalone (Test) Routines
#==================================================================================================

if __name__ == "__main__":
    """
   Run Tests of module routines
   """

    biblioDB = libPEPBiblioDB.BiblioDB()

    biblioDB.connectDB()
    pepArticleList = PEPArticleListDB(biblioDB)

    import doctest
    doctest.testmod()
    print("doctests done.")
    sys.exit()

    print(pepArticleList.fetchArticleReferenceMetadataFromArticleID("IJP.080.01970"))
