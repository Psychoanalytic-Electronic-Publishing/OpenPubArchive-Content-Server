# -*- coding: UTF-8 -*-

import sys

programNameShort = "SplitBookSuport" # Library to find correct locator for pages in a split book instance
import logging
logger = logging.getLogger(programNameShort)

import opasGenSupportLib as opasgenlib
import opasLocator
import opasDocuments
import opasFileSupport
import loggingDebugStream

DBGSTDOUT = True

SPLIT_BOOK_TABLE = "vw_opasloader_splitbookpages"

#----------------------------------------------------------------------------------------
# CLASS DEF: SplitBookData
#----------------------------------------------------------------------------------------
class SplitBookData:
    """
    Manages the table splitbookpages, which is used to store the complete list of
    	instances for each page in a split book, in order to know the instance containing
        that page for link generation.
        
    Pass in the database connection object when instantiating.
    
    """

    #----------------------------------------------------------------------------------------------
    def __init__(self, database_connection):
        """
        Initiate instance
        """
        self.ocd = database_connection
        # use class level variable to keep connection, so you don't have to keep connecting!

    #--------------------------------------------------------------------------------
    def __del__(self):
        """
        Cleanup and destroy the instance
        """
        self.dbName = None

    #--------------------------------------------------------------------------------
    def get_splitbook_page_instance(self, book_code, vol, page_id, has_biblio=0, has_toc=0):
        """
        Return the instance locator containing the pageID for the journalCode and volume.

        >>> splitbook = SplitBookData()
        >>> splitbook.get_splitbook_instance("ZBK", "27", "0169")
        'ZBK.027.0168A'
        """
        ret_val = None
        vol_number_obj = opasDocuments.VolumeNumber(vol)
        vol_number_int = vol_number_obj.volNumber
        vol_number_suffix = vol_number_obj.volSuffix
        if isinstance(page_id, opasDocuments.PageNumber):
            page_id_str = page_id.pageID()
            page_number = page_id
        else:
            page_number = opasDocuments.PageNumber(page_id)
            page_id_str = page_number.pageID()

        # SE Exception; Need to check vol 4 if it's certain pages in 5.
        if book_code == "SE":
            if vol_number_int == 5:
                if page_number > 0 and page_number < 629:
                    vol_number_int = 4

        try:
            art_base = "%s%03d%s" % (book_code, vol_number_int, vol_number_suffix)
        except Exception as e:
            raise (Exception, "Error: %s" % e)

        if has_biblio:
            biblio_query = " and bibliopage = 1"
        else:
            biblio_query = ""

        if has_toc:
            toc_query =  " and tocpage = 1"
        else:
            toc_query =  ""

        loggingDebugStream.log_everywhere_if(DBGSTDOUT, level="debug", msg=f"GetSplitBookInstance: {art_base} {page_id_str}")

        page_qry = fr"""select articleID,
                        bibliopage,
                        tocpage
                        from {SPLIT_BOOK_TABLE}
                        where articleIDbase='%s'
                        and pagenumber='%s'
                        %s
                        %s
                        order by 1 ASC
                    """ % (art_base, page_id_str, biblio_query, toc_query)
        pageSet = self.ocd.get_select_as_list(page_qry)
        page_set_len = len(pageSet)
        if page_set_len == 0:
            pass
        elif page_set_len > 1:
            ret_val = pageSet[0][0]
            for pg in pageSet:
                articleID = pg[0]
                articleLoc = opasLocator.Locator(articleID)
                page_number = articleLoc.pgStart
                if opasDocuments.PageNumber(page_id_str) == page_number:
                    ret_val = pg[0]
                    break	# added 20071102 - fixes the fact that it always chose the last article
            logger.warning("Page %s appears in %s splits. Used: %s" % (page_id_str, page_set_len, ret_val))
        else :
            ret_val = pageSet[0][0]

        return ret_val

    #----------------------------------------------------------------------------------------
    def garbage_collect(self, art_id_pattern=None):
        """
        Go through the splitbook table and eliminate files which no longer exist per the file
                column

        >>> splitbook = SplitBookData()
        >>> splitbook.garbage_collect(art_id_pattern="ZBK.999.0000")

        """
        import localsecrets
        fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root=localsecrets.IMAGE_SOURCE_PATH)
        loggingDebugStream.log_everywhere_if(DBGSTDOUT, level="debug", msg=f"Garbage Collect. Deleting records {SPLIT_BOOK_TABLE} where the XML file no longer exists.")
        
        art_id_addon = ""
        if art_id_pattern is not None:
            art_id_addon = f" where articleID like '{art_id_pattern}'"

        try:
            selqry = f"select distinct articleID, filename from {SPLIT_BOOK_TABLE} {art_id_addon}"
            list_of_articles = self.ocd.get_select_as_list(selqry)
            if list_of_articles != []:
                count = 0
                for article in list_of_articles:
                    (articleID, filename) = article
                    if filename != 'None' or opasgenlib.is_empty(filename):
                        file_exists = False
                    else:
                        file_exists = fs.exists(filename)
                        
                    if not file_exists:
                        # delete this article record, the file was consolidated or removed
                        count = count + 1
                        delqry = f"delete from {SPLIT_BOOK_TABLE} where articleID = '{articleID}'"
                        self.ocd.do_action_query(delqry, queryparams=None, contextStr=f"({SPLIT_BOOK_TABLE} %s)" % articleID)
                        loggingDebugStream.log_everywhere_if(DBGSTDOUT, level="debug", msg=f"Deleted from {SPLIT_BOOK_TABLE} ArticleID: {articleID}")
                        
        except Exception as e:
            loggingDebugStream.log_everywhere_if(DBGSTDOUT, level="error", msg=f"Error: {articleID} {e}")
            ret_val = False
        else:
            loggingDebugStream.log_everywhere_if(DBGSTDOUT, level="info", msg=f"Finished cleaning records.  {count} records deleted.")
            ret_val = True
            
        return ret_val

    #--------------------------------------------------------------------------------
    def delete_splitbook_page_records(self, art_locator, page_pattern=None, filename_pattern=None): 
        """
        Remove all records for a given locator from the split book table splitbookpages

        >>> splitbook = SplitBookData()
        >>> splitbook.add_splitbook_page_record("ZBK.999.0100", "R0021")
        >>> splitbook.delete_splitbook_page_records("ZBK.999.0100")

        """
        
        if isinstance(art_locator, str):  
            art_id = opasLocator.Locator(art_locator, noStartingPageException=True)
            # art_id_base = art_id.baseCode()
        else:
            art_id = art_locator
            # art_id_base = art_id.baseCode()
        
        if page_pattern is not None:
            add_page_pattern = f" and pagenumber like {page_pattern}"
        else:
            add_page_pattern = ""
                   
        if filename_pattern is not None:
            add_filename_pattern = f" and filename like {filename_pattern}"
        else:
            add_filename_pattern = ""
            
        prequery = f"delete from {SPLIT_BOOK_TABLE} where articleID = '{art_id}' {add_page_pattern} {add_filename_pattern}"
        loggingDebugStream.log_everywhere_if(DBGSTDOUT, level="debug", msg=prequery)
        
        ret_val = self.ocd.do_action_query(prequery, queryparams=None, contextStr=f"(SplitBookPages Removed for {art_id})")
        return ret_val

    #--------------------------------------------------------------------------------
    def add_splitbook_page_record(self, artLocator, pageID, has_biblio=0, hasTOC=0, full_filename=None):
        """
        Add a record to the split book table splitbookpages to record the page Id and article locator

        >>> splitbook = SplitBookData()
        >>> splitbook.add_splitbook_page_record("ZBK.999.0000", "0021")
        >>> splitbook.add_splitbook_page_record("ZBK.999.0000")

        """

        ret_val = None
        insert_splitbook_qry = fr'replace into {SPLIT_BOOK_TABLE} values ("%s"' + (5*', "%s"') + ")"

        if isinstance(artLocator, str):  
            art_id = opasLocator.Locator(artLocator, noStartingPageException=True)
            art_id_base = art_id.baseCode()
        else:
            art_id = artLocator
            art_id_base = artLocator.baseCode()

        safeFilename = opasgenlib.do_escapes(full_filename)

        # set up authorName insert
        querytxt = insert_splitbook_qry % (art_id_base,
                                           art_id,
                                           pageID,
                                           has_biblio,
                                           hasTOC,
                                           safeFilename
                                           )
        
        # now add the row
        ret_val = self.ocd.do_action_query(querytxt,
                                           queryparams=None,
                                           contextStr="(SPLITBOOKS %s/%s)" % (art_id_base, pageID))
        return ret_val

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
    import opasCentralDBLib

    ocd = opasCentralDBLib.opasCentralDB()
    splitbook = SplitBookData(database_connection=ocd)

    if 1:
        splitbook.garbage_collect()

