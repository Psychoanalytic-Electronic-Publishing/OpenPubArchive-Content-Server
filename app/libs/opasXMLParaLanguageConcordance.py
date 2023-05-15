# -*- coding: latin-1 -*-
#Copyright 2012 Neil R. Shapiro
"""
Module for PEPGWSEParaConcordance Table management.
Also includes a function to add these para IDs to GE and SE (but this only needs to be run "once" to insert them)
"""
__version__ = "1.0.0"

import sys
sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')

#ocd = opasCentralDBLib.opasCentralDB()

import opasXMLHelper as opasxmllib
import opasDocuments

gDbg1 = 1 # details
gDbg2 = 1 # big picture, status


#============================================================================================
class PEPGWSEParaConcordance:
    """
    Create and Get data from database table "PEPGWSEParaConcordance"
      holding information about translations of SE/GW paragraphs
    """

    #----------------------------------------------------------------------------------------------
    def __init__(self, ocd):
        """
        Initiate instance
        """
        self.ocd = ocd

    #----------------------------------------------------------------------------------------
    def addRelatedIDs(self, parsed_xml, artInfo, verbose=False):
        """
        Add the related IDS from GWSEparaconcordance to each paragraph, right now used only for GW and SE.

        """
        aInfo = artInfo
        # This section adds IDs by paragraph to GW and SE.
        if artInfo.src_code in ["GW", "SE"]:
            lang = artInfo.art_lang
            vol = artInfo.art_vol_str
            lgIDCount = 0
            nodes = parsed_xml.xpath("//p2|//p|//arttitle|//n|//artsub|//h1|//h2|//h3|//h4|//h5|//h6|//h7")
            lastPXLink = ""
            lastFtrPXLink = ""
            for node in nodes:
                elementName = node.tag
                lgrLink = node.attrib.get("lgrpid", None)
                if lgrLink is not None:
                    raise ValueError("lgrpid should not be in use.")
                lgrX = node.attrib.get("lgrx", None)
                lgrID = node.attrib.get("lgrid", None)
                lgrLinkType = node.attrib.get("lgrtype", None)
                lgIDCount += 1

                if lgrID is not None:
                    # now look it up
                    if artInfo.src_code == "GW":
                        lgrLinkLookup = self.getSEParaID(lgrID)
                        if lgrLinkLookup  != ():
                            lgrXLink = lgrLinkLookup
                    elif artInfo.src_code == "SE":
                        lgrLinkLookup = self.getGWParaID(lgrID)
                        if lgrLinkLookup  != ():
                            lgrXLink = lgrLinkLookup
                    else:
                        raise Exception("Case Error.")  # should never be here.

                    if elementName == "p": # save this in case next element is p2
                        # see what the ancestor is
                        if opasxmllib.xml_node_has_ancestors(node, "ftr"):
                            lastFtrPXLink = lgrXLink
                        else:
                            lastPXLink = lgrXLink # last para link ID found
                            lastPID = lgrID       # last para ID to copy to p2
                    elif elementName == "p2":
                        if lgrXLink == "" and lastPXLink != "":
                            lgrXLink = lastPXLink
                            # set node to previous para ID so it matches from alternate document
                            node.attrib["lgrid"] = lastPID

                        #else: # keep found value
                    else: # clear it, since there are intervening ids
                        lastPXLink = ""

                    if lgrXLink != "":
                        node.attrib["lgrx"] = lgrXLink
                        node.attrib["lgrtype"] = "GroupIDTrans"
                    else:
                        try:
                            del node.attrib["lgrx"]
                        except KeyError:
                            pass

                        try:
                            del node.attrib["lgrtype"]
                        except KeyError:
                            pass

            if verbose:
                print("\t...%d nodes marked with GW/SE related IDs" % lgIDCount)

    #----------------------------------------------------------------------------------------
    def getSEParaID(self, GWParaID):
        """
        Get the Corresponding ArticleID and SEParaID (as a tuple) for the specified GW paraID

        	>>> paraRelations = PEPGWSEParaConcordance()
        	>>> paraRelations.getSEParaID("GWA3a6")
        	u'SEA115a13'
        """
        retVal = ""
        # find article and para ID for this para.
        selqry = r"""
            select SEID
            from opasloader_gwseparaconcordance
            where GWID = '%s'
            """ % (GWParaID)
        
        resultSet = self.ocd.get_select_as_list(selqry)

        if resultSet != []:
            count = 0
            for n in resultSet:
                count += 1
                if count == 1:
                    retVal = "%s" % n[0]
                else:
                    retVal = "%s, %s" % (retVal, n[0])

        return retVal

    #----------------------------------------------------------------------------------------
    def getGWParaID(self, SEParaID):
        """
        Get the Corresponding ArticleID and GWParaID (as a tuple) for the specified SEParaID

            >>> paraRelations = PEPGWSEParaConcordance()
        	>>> paraRelations.getGWParaID("SEA115a22")
        	u'GWA3a13'
        	>>> paraRelations.getGWParaID("SEG123a551")
        	u'GWE132a28, GWE132a29'
        """
        retVal = ""
        # find article and para ID for this para.
        selqry = r"""
            select GWID
            from opasloader_gwseparaconcordance
            where SEID = '%s'
            """ % (SEParaID)

        resultSet = self.ocd.get_select_as_list(selqry)

        if resultSet != []:
            count = 0
            for n in resultSet:
                count += 1
                if count == 1:
                    retVal = "%s" % n[0]
                else:
                    retVal = "%s, %s" % (retVal, n[0])
        return retVal

#----------------------------------------------------------------------------------------
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

