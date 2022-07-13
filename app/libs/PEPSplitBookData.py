# -*- coding: Latin-1 -*-


import string, os, sys

programNameShort = "opasLocator (PEPSplitBookData)" # Library to build and decompile locators (articleIDs/document ids)

import logging
logger = logging.getLogger(programNameShort)

import opasGenSupportLib as opasgenlib
import opasXMLHelper as opasxmllib
import opasLocator
import opasDocuments


gDbg1 = False

#----------------------------------------------------------------------------------------
def getBibEntryPageLink(articleLocator, bibID=None, pageNumber=None, ocd=None):
    """
    Return a page locator (e.g., RBP.001.0071A.P0057) if the page number is in
        the specified reference, and the reference is in PEP.

    Otherwise, return None

    >>> fullBiblioDB = PEPFullBiblioDB(connectDict=gConnect)
    >>> print "getBibEntryPageLink: ", fullBiblioDB.getBibEntryPageLink("RBP.001.0071A.B002", pageNumber="21")
    getBibEntryPageLink:  None
    >>> print "getBibEntryPageLink: ", fullBiblioDB.getBibEntryPageLink("RBP.001.0071A.B002", pageNumber="57")
    getBibEntryPageLink:  IJP.059.0055A.P0057

    """
    retVal = None

    #if bibID == None:
        #refDBEntry = self.getBibEntryMetadata(articleLocator)
    #else:
        #refDBEntry = self.getBibEntryMetadata(articleLocator, bibID)

    #print refDBEntry

    #print "GetBibEntryPageLink: ", `refDBEntry`
    targetArticleID = refDBEntry[gConst.KEY]
    targetArticleLoc = opasLocator.Locator(targetArticleID)
    pageNumber = opasDocuments.PageNumber(pageNumber)
    pageNumberID = pageNumber.format()
    if targetArticleLoc.isSplitBook():
        splitTargetArticleLocalID = opasLocator.Locator(targetArticleID).localID(pageNumberID, checkSplitInThisBiblioDB=True)
        splitTargetArticleLoc = opasLocator.Locator(splitTargetArticleLocalID).articleID()
        msg = "Split book artID: %s / %s" % (splitTargetArticleLoc, splitTargetArticleLocalID)
        # get the new page range
        pepRef = PEPArticleListDB.PEPArticleListDB()
        refDBEntry = pepRef.fetchArticleReferenceMetadataFromArticleID(splitTargetArticleLoc)
        self.getBibEntryMetadata(splitTargetArticleLoc)
        targetArticleID = splitTargetArticleLoc

    if refDBEntry != None:
        if refDBEntry[gConst.PGRG] != None:
            pgRange = opasDocuments.PageRange(refDBEntry[gConst.PGRG])
            if pgRange.contains(pageNumber):
                retVal = Locator(targetArticleID).localID(pageNumberID)
            else:
                gErrorLog.logInfo("getBibEntryPageLink - Page number %s out of range for PgRange: %s.  No link returned." % (pageNumber, pgRange))
        else:
            if pageNumber != None:
                refDBEntry[gConst.PGRG] = opasDocuments.PageRange(pageNumber)
            else:
                if 1: print ("No page range or page number found for: ", str(refDBEntry))

        #print "Page Link: ", retVal

    return retVal


#----------------------------------------------------------------------------------------
# CLASS DEF: PEPSplitBookData
#----------------------------------------------------------------------------------------
class SplitBookData:
    """
    Manages the table splitbookpages, which is used to store the complete list of
    	instances for each page in a split book, in order to know the instance containing
        that page for link generation.
    """

    splitbookinsqry = r'replace into splitbookpages values ("%s"' + (5*', "%s"') + ")"
    db = None
    mySQLConnection = None

    #----------------------------------------------------------------------------------------------
    def __init__(self, ocd):
        """
        Initiate instance
        """
        self.ocd = ocd
        # use class level variable to keep connection, so you don't have to keep connecting!

    #--------------------------------------------------------------------------------
    def __del__(self):
        """
        Cleanup and destroy the instance
        """
        self.dbName = None

    #--------------------------------------------------------------------------------
    def getSplitBookInstance(self, jrnlCode, vol, pageID, hasBiblio=0, hasTOC=0):
        """
        Return the instance locator containing the pageID for the journalCode and volume.

        >>> pSplitDB = PEPSplitBookData()
        >>> pSplitDB.getSplitBookInstance("ZBK", "27", "0169")
        'ZBK.027.0168A'
        """
        retVal = None
        volObj = opasDocuments.VolumeNumber(vol)
        volInt = volObj.volNumber
        volSuffix = volObj.volSuffix
        if isinstance(pageID, opasDocuments.PageNumber):
            pageIDStr = pageID.pageID()
            pageNumber = pageID
        else:
            pageNumber = opasDocuments.PageNumber(pageID)
            pageIDStr = pageNumber.pageID()

        # SE Exception; Need to check vol 4 if it's certain pages in 5.
        if jrnlCode == "SE":
            if volInt == 5:
                if pageNumber > 0 and pageNumber < 629:
                    volInt = 4

        try:
            artBase = "%s%03d%s" % (jrnlCode, volInt, volSuffix)
        except Exception as e:
            raise (Exception, "Error: %s" % e)

        #print ("GetSplitBookInstance: %s, page %s" % (artBase, pageID))
        if hasBiblio:
            biblioQuery = " and bibliopage = 1"
        else:
            biblioQuery = ""

        if hasTOC:
            tocQuery =  " and tocpage = 1"
        else:
            tocQuery =  ""

        if gDbg1: print ("GetSplitBookInstance: ", artBase, pageIDStr)

        selPageInstance = r"""select articleID,
                               bibliopage,
                               tocpage
                               from opasloader_splitbookpages_static
                               where articleIDbase='%s'
                               and pagenumber='%s'
                               %s
                               %s
                               order by 1 ASC
                           """ % (artBase, pageIDStr, biblioQuery, tocQuery)
        pageSet = self.ocd.get_select_as_list(selPageInstance)
        gLen = len(pageSet)
        if gLen == 0:
            pass
        elif gLen > 1:
            retVal = pageSet[0][0]
            for pg in pageSet:
                articleID = pg[0]
                articleLoc = opasLocator.Locator(articleID)
                pageNumber = articleLoc.pgStart
                #print ("ArticleID: ", articleID, "Starting Pg: ", pageNumber, pageIDStr, retVal)
                if opasDocuments.PageNumber(pageIDStr) == pageNumber:
                    retVal = pg[0]
                    break	# added 20071102 - fixes the fact that it always chose the last article
            #print 50*"*"
            logger.warning("Page %s appears in %s splits. Used: %s" % (pageIDStr, gLen, retVal))
        else :
            retVal = pageSet[0][0]

        return retVal

    #----------------------------------------------------------------------------------------
    #def garbageCollectSplitPageTable(self):
        #"""
        #Go through the splitbook table and eliminate files which no longer exist per the file
                #column
        #"""
        #print ("Deleting old records in splitbookpages table where the file (in XML) no longer exists.")
        #selqry = r"""select distinct articleID, filename from splitbookpages"""
        #dbc = self.db.cursor()
        #dbc.execute(selqry)
        #resultSet = dbc.fetchall()
        #count = 0
        #for cursorRecord in resultSet:
            #(articleID, filename) = cursorRecord
            #if not opasgenlib.is_empty(filename):
                ##print ("Checking %s" % filename)
                #if not os.path.exists(filename):
                    ## delete this article record, the file was consolidated or removed
                    #count = count + 1
                    #doqry = "delete from splitbookpages where articleID = '%s'" % articleID
                    #self.ocd.do_action_query(doqry, "(splitbookpages %s)" % articleID)
        #dbc.close()
        #print ("--finished cleaning records.  %s records deleted." % count)

    #--------------------------------------------------------------------------------
    def delSplitBookPages(self, artLocator):
        """
        Remove all records for a given locator from the split book table splitbookpages

        >>> pSplitDB = PEPSplitBookData()
        >>> pSplitDB.addSplitBookPage("ZBK.999.0100", "R0021")
        >>> pSplitDB.delSplitBookPages("ZBK.999.0100")

        """
        prequery = """delete from splitbookpages where articleID = '%s'""" % (artLocator)
        self.ocd.do_action_query(prequery, "(SplitBookPages Removed for %s)" % (artLocator))

    #--------------------------------------------------------------------------------
    def addSplitBookPage(self, artLocator, pageID, hasBiblio=0, hasTOC=0, fullFilename=None):
        """
        Add a record to the split book table splitbookpages to record the page Id and article locator

        >>> pSplitDB = PEPSplitBookData()
        >>> pSplitDB.addSplitBookPage("ZBK.999.0000", "0021")
        >>> pSplitDB.delSplitBookPages("ZBK.999.0000")

        """

        if isinstance(artLocator, str):  
            artID = opasLocator.Locator(artLocator, noStartingPageException=True)
            artIDBase = artID.baseCode()
        else:
            artID = artLocator
            artIDBase = artLocator.baseCode()

        safeFilename = opasgenlib.do_escapes(fullFilename)

        # set up authorName insert
        querytxt = self.splitbookinsqry % (
            artIDBase,
            artID,
            pageID,
            hasBiblio,
            hasTOC,
            safeFilename
        )
        # now add the row
        self.ocd.do_action_query(querytxt, "(SPLITBOOKS %s/%s)" % (artIDBase, pageID))

#==================================================================================================
# Main Standalone (Test) Routines
#==================================================================================================

if __name__ == "__main__":
    """
	Run Tests of module routines
	"""

    import doctest
    doctest.testmod()
    sys.exit()

    #pSplitDB = PEPSplitBookData(host="192.168.1.158", port=3306, user="neil")
    pSplitDB = PEPSplitBookData()

    if 1:
        pSplitDB.garbageCollectSplitPageTable()

