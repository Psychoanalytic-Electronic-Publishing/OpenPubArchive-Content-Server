# -*- coding: latin-1 -*-
#Copyright 2012 Neil R. Shapiro

"""
Module for gwpageconcordance Table management.

"""
__version__ = "1.0.1"

programNameShort = "opasXMLPageConcordance"
import sys
import logging
logger = logging.getLogger(programNameShort)

import opasCentralDBLib
import opasGenSupportLib as opasgenlib
import lxml
from lxml import etree
parser = lxml.etree.XMLParser(encoding='utf-8', recover=True, resolve_entities=True, load_dtd=True)

# import opasXMLHelper as opasxmllib
import opasDocuments
import opasLocator
import opasCentralDBLib
import opasXMLSplitBookSupport

import opasGenSupportLib as opasgenlib

ocd =  opasCentralDBLib.opasCentralDB()
split_book_data = opasXMLSplitBookSupport.SplitBookData(database_connection=ocd)

gDbg1 = 0

#============================================================================================
class PageConcordance:
    """
    Create and Get data from database table "gwpageconcordance"
      holding information about pages which are translations of the other.

      >>> pepArtRel = PageConcordance()

    """

    #--------------------------------------------------------------------------------
    def __init__(self):
        """
        Initialize the instance.
        """
        self.ocd = ocd  

    #----------------------------------------------------------------------------------------
    def insert_page_translations(self, parsed_xml, art_id):
        """
        Walk through the page elements of the tree and insert links to translations.

        This really belongs in the converter (though it's used in several, so maybe a convenience function here)

        """
        templateSE = """<ftn label="[PEP]" id="F%04d"><p>This page can be read in German in GESAMMELTE WERKE Vol %s, Page <pgx rx="%s">%s</pgx></p></ftn>"""
        templateGW = """<ftn label="[PEP]" id="F%04d"><p>This page can be read in English in the Standard Edition Vol %s, Page <pgx rx="%s">%s</pgx></p></ftn>"""
        aLoc = opasLocator.Locator(art_id)
        footnoteID = 9000
        insertCount = 0
        page_break_nodes = parsed_xml.xpath("//pb")
        if aLoc.jrnlCode in ["SE", "GW"]:
            for pb in page_break_nodes:
                if gDbg1: print(f"pre:\n{etree.tostring(pb, pretty_print=True).decode('utf8')}")
                pg_numbers = pb.xpath("./n")
                pg_num = pg_numbers[0]
                if pg_num is not None:
                    pgLocator = self.get_page_locator(art_id, pg_num.text)  #look it up in the concordance table
                    if pgLocator != None:
                        pg_num_tgt = pgLocator.splitArticleID(includeLocalID=1)[-1][1:]
                        pg_num_tgt = opasDocuments.PageNumber(pg_num_tgt)
                        if aLoc.jrnlCode == "SE":
                            footnoteID += 1
                            ftn = templateSE % (footnoteID, pgLocator.jrnlVol, pgLocator, pg_num_tgt)
                            insertCount += 1
                        elif aLoc.jrnlCode == "GW":
                            footnoteID += 1
                            ftn = templateGW % (footnoteID, pgLocator.jrnlVol, pgLocator, pg_num_tgt)
                            insertCount += 1
                        else:
                            raise Exception("We shouldn't ever be here!")

                        #print "Footnote: ", ftn
                        # now insert it
                        # back to pb
                        ftr = pb.xpath("./ftr")
                        if ftr:
                            # there's already a footer
                            # put it at the end of the existing footer
                            trans_ftn = etree.fromstring(ftn, parser)
                            ftr[0].insert(0, trans_ftn)
                        else:
                            ftn = "<ftr>%s</ftr>" % ftn
                            trans_ftn = etree.fromstring(ftn, parser)
                            # put it at the beginning of the page break
                            pb.insert(0, trans_ftn)

                        if gDbg1:
                            print(f"\nftn to add:\n{etree.tostring(trans_ftn).decode('utf8')}" )
                            print(f"\npost:\n{etree.tostring(pb).decode('utf8')}" ) 
                    else:
                        logger.warn("Couldn't find page concordance for %s: %s, %s" % (aLoc.jrnlCode, pg_num, pgLocator))

        retVal = insertCount
        return retVal

    #----------------------------------------------------------------------------------------------
    def get_page_locator(self, articleID,  page_number):
        """
        Get the page locator for the translated page from the artrelations table

            >>> pepOrigRX = PageConcordance()
            >>> GWLocator = pepOrigRX.getPageLocator("SE.012.0123", 125)
            >>> print (GWLocator)
            GW.008.0454A.P0456
            >>> pepOrigRX.getPageLocator("GW.017.0027", '028')
            SE.018.0173A.P0177

        """
        retVal = None
        aLoc = opasLocator.Locator(articleID)
        if aLoc.jrnlCode == "SE":
            retVal = self.get_page_locator_for_GW(articleID, page_number)
        elif aLoc.jrnlCode == "GW":
            retVal = self.get_page_locator_for_SE(articleID, page_number)
        else:
            pass

        return retVal

    #----------------------------------------------------------------------------------------------
    def get_page_locator_for_GW(self, SE_locator,  SE_page_number):
        """
        Get the GW pagenumber from the SELocator and SEPageNumber.
        For Roman pages, use Negative numbers for SEPageNumber.

            >>> pepOrigRX = PageConcordance()
            >>> GWLocator = pepOrigRX.getGWPageLocator("SE.012.0123", 125)
            >>> print (GWLocator)
            GW.008.0454A.P0456
            >>> GWLocator = pepOrigRX.getGWPageLocator("SE.002.R0029", -31)
            >>> print (GWLocator)
            GW.001.0079A.P0079
        """

        SE_locator_vol = opasLocator.Locator(SE_locator).jrnlVol
        pg_num = opasDocuments.PageNumber(SE_page_number)
        pg_num_val = pg_num.forceInt()

        # SE Exception; Need to check vol 4 if it's certain pages in 5.
        if SE_locator_vol == 4:
            if pg_num_val > 338 and pg_num_val < 629:
                SE_locator_vol = 5

        if pg_num.isRoman():
            if gDbg1: print(f"Roman Page Lookup in getGWPageLocator, uses negative: {pg_num_val}")

        selqry = """Select GWVol, GWFirstPgNum, GWLastPgNum
                    FROM opasloader_gwpageconcordance
                    WHERE %s = SrcPgNum
                    AND SrcVol =   '%s'
                 """  % (pg_num_val, SE_locator_vol)

        pgLocRow = ocd.get_select_as_list(selqry)
        if not opasgenlib.is_empty(pgLocRow):
            GWVol, GWFirstPgNum, GWLastPgNum = pgLocRow[0]
            if GWFirstPgNum != None:
                GWFirstPgNum = int(GWFirstPgNum)
                GWInstanceID = split_book_data.get_splitbook_page_instance(book_code="GW", vol=GWVol, page_id=GWFirstPgNum)
                if GWInstanceID != None:
                    retVal = opasLocator.Locator("%s.P%04d" % (GWInstanceID, GWFirstPgNum))
                else:
                    retVal = opasLocator.Locator("GW.0%s.%04d.P%04d" % (GWVol, GWFirstPgNum, GWFirstPgNum))
            else:
                retVal = None
        else:
            retVal = None

        return retVal

    #----------------------------------------------------------------------------------------------
    def get_page_locator_for_SE(self, GWLocator, GWPageNumber):
        """
        Return the localID page locator for the corresponding SE Page given the GW page.

        	>> SELocator = pepOrigRX.getSEPageLocator("GW.001.0463", 465)
        	>> print (SELocator)
        	SE.003.0223A.P0229
        	>>> pepOrigRX = PageConcordance()
        	>>> pepOrigRX.getSEPageLocator("GW.001.0079A", 79)
        	SE.002.R0031A
        """

        GWLocatorVol = opasLocator.Locator(GWLocator).jrnlVol
        pg_num = opasDocuments.PageNumber(GWPageNumber)
        pg_num_val = pg_num.forceInt()  # forces it to negative if it's roman.
        if pg_num.isRoman():
            #print "Roman Page Lookup in getSEPageLocator, uses negative: %s" % pgNumVal
            print ("Vol %s/Page %s skipped...so far no roman numbers in GW for concordance!" % (GWLocatorVol, pg_num))
            return None

        selqry = """Select SrcName, SrcVol, SrcPgNum
                    FROM opasloader_gwpageconcordance
                    WHERE %s <= GWLastPgNum
                    AND %s >= GWFirstPgNum
                    AND GWVol =   '%s'
                 """  % (pg_num, pg_num_val, GWLocatorVol)

        pg_loc_row = ocd.get_select_as_list(selqry)
        if not opasgenlib.is_empty(pg_loc_row):
            src_name, src_vol, src_pg_num = pg_loc_row[0]
            if src_vol != None and src_pg_num != None:
                src_pg_num = int(src_pg_num)
                pg_src_pg_num = opasDocuments.PageNumber(src_pg_num)
                SE_instance_id = split_book_data.get_splitbook_page_instance(book_code="SE", vol=src_vol, page_id=src_pg_num)
                if SE_instance_id != None:
                    retVal = opasLocator.Locator("%s.%s" % (SE_instance_id, pg_src_pg_num.format(keyword=pg_num.LOCALID)))
                else:
                    retVal = None
            else:
                retVal = None
        else:
            retVal = None

        return retVal


#==================================================================================================
# Main Standalone (Test) Routines
#==================================================================================================

if __name__ == "__main__":
    """
	Run Tests of module routines
	"""

    import doctest
    doctest.testmod()
    print ("All tests Complete!")
    sys.exit()