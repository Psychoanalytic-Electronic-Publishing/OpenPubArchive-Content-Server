# -*- coding: UTF-8 -*-

"""
This is the module with the class for LocalIDs, the 4-6 character string appended to the end of a locator,
 and following rules so they may also be used as local IDRefs in XML.

This module adapted from a much older module used in PEPXML to compile PEP instances since 200x!

  ** Slowly being adopted to opas as needed **

"""
__author__      = "Neil R. Shapiro"
__license__     = "Apache 2.0"
__version__     = "2022.0609" 
__status__      = "Development"

programNameShort = "opasLocalID" # SubLibrary to build and decompile locators (articleIDs/document ids)

import sys
import logging
logger = logging.getLogger(programNameShort)

import re
import opasLocator

import opasXMLPEPAuthorID
from opasDocuments import PageNumber, PageRange

gDbg1 = 0

#----------------------------------------------------------------------------------------
# CLASS DEF: LocalID
#----------------------------------------------------------------------------------------
class LocalID:

    """
	A class for LocalIDs, the 2-6 character string appended to the end of a locator,
	 and following rules so they may also be used as local IDRefs in XML.

	This is a specific sequentially assigned ID used to identify a location in an instance,
      basically, an XML id.  We use various prefixes to qualify the type of local ID:

	    A = Affiliation ID
	            "A" followed by a two digit number from 00 to 99

	    B = Bibliographic Reference ID
	            "B" followed by four digit number from 000 to 999

	    F = Footnote ID
	            "F" followed by four digit number from 000 to 999

	    G = Figure ID
	            "G" followed by three digit number from 000 to 999

	    H = Heading ID (and ArtTitle ID)
	            "H" followed by a five digit number from 00000 to 99990

	    N = Note ID
	            "N" followed by three digit number from 000 to 999

	    T = Table ID
	            "T" followed by three digit number from 000 to 999

	    O = Table Footnote ID
	            "O" followed by three digit number from 000 to 999

		Y = Glossary Item ID
				"Y" followed by a signed long integer (no spaces)

	if the checkSplitInThisBiblioDB parameter is specified, it will return

	"""

    SHORTIDPREFIXLETTERS = "ABFGHNPTOY"

    # shortID = LocalID component of locator
    # 1-7-2005: Note added "R" option in case ID is page reference and pg numb is roman!

    # OLD	ptnShortID =  r"""
    #					(?P<xmlid>
    #						\b
    #						([\"\'])?
    #						(?P<pepshortID>[%s]R?[0-9\-][0-9_]{1,22})
    #						(?P<peplocalIDSuffix>[A-z])?
    #						([\"\'])?
    #						\b
    #					)
    #				 """ % SHORTIDPREFIXLETTERS
    #
    # removed ' -- not sure why we'd want to accept those in an ID!

    # 2017-12-15 Allow FN as a local ID
    ptnShortID = r"""
        (?P<xmlid>
        \b
        (?P<pepshortID>[%s](N|R)?[0-9\-][0-9_]{1,22})
        (?P<peplocalIDSuffix>[A-z])?
        \b
        )
        """ % SHORTIDPREFIXLETTERS
    rgxShortID = re.compile("(" + ptnShortID
                            + ")", re.VERBOSE
                            )

    ptnValidID = r"""
        (?P<xmlid>
        \b
        (?P<pepshortID>
        ([ABFGHNPTO]
        (
        (R[0-9]{2,4})
        |([0-9][0-9_]{1,3})
        )
        )
        |Y([0-9\-][0-9]{1,27})
        )
        (?P<peplocalIDSuffix>[A-z])?
        \b
        )
        """ #% SHORTIDPREFIXLETTERS[:-1]

    rgxValidShortID = re.compile("(" + ptnValidID
                                 + ")", re.VERBOSE
                                 )

    #--------------------------------------------------------------------------------
    def __init__(self, localIDRef=None):
        """
        Init class for a standard local id

        Kwargs:
            localIDRef (str):  Optional localID to use

        Also: Standardizes the local ID component (no spaces are
        		allowed, so they are replaced with "_"


        >>> LocalID("B0005")
        B0005
        >>> LocalID("B005")
        B0005
        >>> LocalID("B3")
        B0003
        >>> LocalID("F001")
        F00001
        >>> LocalID("FN001")
        FN00001

        """

        self.localID = None
        self.localIDList = [] # 2016-06-04 Added to handle IDRefs!
        self.localIDIsList = False # 2016-06-04 Added to handle IDRefs!
        self.localIDType = None
        self.locatorBaseStr = None
        self.localIDStr = None
        self.initStr = None
        self.localIDVal = None
        self.localIDSuffix = None #20071101

        import opasLocator

        if isinstance(localIDRef, opasLocator.Locator):
            localIDRef = repr(localIDRef)
            if gDbg1: print("LocalIDRef: ", localIDRef)

        if isinstance(localIDRef, PageNumber):
            localIDRef = localIDRef.format()
            if gDbg1: print("LocalIDRef: ", localIDRef)

        if localIDRef is not None:

            self.localIDList = localIDRef.split(" ")
            if len(self.localIDList) > 1:
                # may be IDREFS rather than IDREF
                for n in self.localIDList:
                    if isLocalID(n):
                        self.localIDIsList = True
                    else:
                        # if any are not, then it's not a list
                        self.localIDIsList = False
                if self.localIDIsList == True:
                    # set localID to the first one, but will watch for the list later.
                    localIDRef = self.localIDList[0]
                    # for the most part, as long as we don't save the formatted local ID, we don't need to work with
                    # the others in the list.  Or do we?

            # if its a full locator, get the locator part only
            self.initStr = localIDRef
            self.locatorBaseStr, self.localIDStr = splitLocalID(localIDRef)

            if self.localIDStr is None:
                print("Warning: no local ID component")
                return

            if len(self.localIDStr) < 2:
                raise Exception("Local ID too short: %s" % localIDRef)

            self.localIDStr = self.localIDStr.upper()     # 2013-05-28 Make sure first letter is uppercase; there are a lot of tests on this.

            self.localIDStr = self.__updateOld(self.localIDStr)

            # Watch out for local refID component starting with "R"
            if self.localIDStr[0] == "R" and self.localIDStr[1].isdigit():
                if gDbg1: print("Warning: Roman local ID %s without page prefix.  Adjusting." % self.localIDStr)
                self.localIDStr = "P" + self.localIDStr

            # now note the type
            if self.localIDStr[1].isalpha():
                self.localIDType = self.localIDStr[0:2]
                valPart = self.localIDStr[2:]
            else:
                self.localIDType = self.localIDStr[0]
                valPart = self.localIDStr[1:]

            try:
                self.localIDVal = valPart
                if valPart[-1].isalpha():
                    self.localIDSuffix = valPart[-1]
                    self.localIDVal = valPart[:-1]
                    if gDbg1: print("LocalIDVal: %s" % self.localIDVal)
                    if gDbg1: print("localIDSuffix: %s" % self.localIDSuffix)
            except:
                # must only be one char!
                raise Exception("Illegal local id specified (more than 2 letter prefix): %s" % localIDRef)

            self.__standardize()

            # check to make sure it conforms!
            if not isShortIDRef(self.localIDStr):
                # Illegal Local ID!
                # BEEP
                # print chr(7)  # disabled 2/28/2013 - not sure if this is what's beeping!
                # Changed this to warning 2019-03-05
                logger.warning("Nonstandard local id '%s' specified: %s" % (self.localIDStr, localIDRef))


        #else: # create instance, no initial value (None)
        return

    #----------------------------------------------------------------------------------------
    def __cmp__(self, other):
        if other is None:
            retVal = 1
            return retVal
        elif isinstance(other, str):  # supports string and unicode
            cmpTo = str(self)
        elif isinstance(other, LocalID):
            cmpTo = str(self)
            other = str(other)
        else:
            raise Exception("LocalID Compare - Mismatched Objects")


        if cmpTo == other:
            retVal = 0
        elif cmpTo > other:
            retVal = 1
        else:
            retVal = -1

        return retVal

    #--------------------------------------------------------------------------------
    def __repr__(self):
        """
        Create displayable (string) version of LocalID object
        """
        return self.__str__()

    #--------------------------------------------------------------------------------
    def __str__(self):
        """
        Create displayable (string) version of LocalID object
        """
        if self.localIDStr is None:
            return ""
        else:
            return str(self.localIDStr)

    #--------------------------------------------------------------------------------
    def __len__(self):
        """
        Return string length of localID
        """
        return len(self.__str__())

    #--------------------------------------------------------------------------------
    def __getslice__(self, start, end):
        """
        Substring function
        """
        start = max(start, 0)
        end = max(end, 0)
        retVal = self.localIDStr[start:end]
        return retVal

    #--------------------------------------------------------------------------------
    def __getitem__(self, index):
        """
        Dictionary like function
        """
        if not isinstance(index, int):
            mbr = index[0].upper()
            if mbr == "S":	# LocalIDStr
                retVal = self.localIDStr
            elif mbr == "T":
                retVal = self.localIDType
        else:
            tmpLoc = self.localIDStr
            retVal = tmpLoc[index]
        return retVal

    #--------------------------------------------------------------------------------
    def __standardize(self):
        """
        Check all local ID types.  Make sure length is right for localID

        B (biblio IDs changed to 4)
        FN allowed (comes from TNF, usually for footnote, but sometimes in notes.)
        """

        retVal = None

        if self.localIDStr is None:
            retVal = None
        elif self.localIDType in ["A", "B", "F", "G", "H", "N", "T", "O", "FN"]:
            if self.localIDType == "A":		# Author ID
                idLen = 2
            elif self.localIDType in ["G", "T", "O"]:		# Biblio LocalID
                idLen = 3
                if self.localIDVal[0] == "A":
                    # exception from TF JATS, add suffix!
                    self.localIDSuffix = "Z"
                    self.localIDVal = self.localIDVal[1:]
            elif self.localIDType == "B":
                idLen = 3                           # opas uses 3 digit biblio local ids
            elif self.localIDType in ["F", "FN"]:
                idLen = 5                           # 3 doesn't work, because T&F had 4 digit (not 0) IDs.  So make it 5, then it won't clash with graphics.
            elif self.localIDType == "H":
                idLen = 5
            elif self.localIDType == "N":  # change 20071024 from 3 to 5, TB keyed it this way.
                if self.localIDVal[0] == "B":
                    idLen = 4
                else:
                    idLen = 5

            try:
                idVal = int(self.localIDVal)
            except:
                errMsg = "Error in idString in identifier: %s" % self.localIDVal
                raise Exception(errMsg)

            idStd = "%0" + str(idLen) + "d"
            self.localIDVal = idStd % idVal
            if self.localIDSuffix is None:
                localIDSuffix = ""
            else:
                localIDSuffix = self.localIDSuffix

            retVal = self.localIDStr = "%s%s%s" % (self.localIDType, self.localIDVal, localIDSuffix)

        elif self.localIDType == "P":
            pageNum = PageRange(self.localIDVal)
            retVal = self.localIDStr = "%s" % (pageNum.pgStart.format())


        return retVal

    #--------------------------------------------------------------------------------
    def __updateOld(self, idString):
        """
        Private function to Update an old format ID to the current format.
        Return the new format as a string.
        """

        #--------------------------------------------------------------------------------
        def isOldFormatIDRef(idString):
            """
            Check for the old format of IDRef
			"""
            m = re.search("[ _]", idString)
            if m is not None:
                if idString[0] == "B":
                    return False
                else:
                    return True
            else:
                return False
        #--------------------------------------------------------------------------------

        retVal = idString

        if isOldFormatIDRef(idString):
            if gDbg1:
                logger.warning("Old format LocalIDRef: %s" % idString)

            parts = re.split("[ _]+", idString)

            if len(parts) < 2:
                retVal = idString
            else:
                prefix = parts[0]
                if prefix == "TFN": prefix="O"
                if not parts[1][0].isdigits():
                    parts[1] = parts[1][1:]
                    # Create new ID--Add 500 to avoid collisions
                    offsetPre = 500
                else:
                    offsetPre = 0

                try:
                    num = int(parts[1]) + offsetPre
                    retVal = "%s%03d" % (prefix[0], num)
                except Exception as e:
                    # for now, lets see what happens if we allow "a" etc. suffixes through
                    # get last char
                    try:
                        letter = parts[1][-1]
                        letter = letter.lower()
                        if letter > 'q': raise Exception("****Old letter suffix too high: %s" % letter)
                        # otherwise, use it as the 100's digit
                        offset = (ord(letter) - ord('a') + 1)*100
                        valOnly = parts[1][:-1]
                        num = int(valOnly) + offset + offsetPre
                        if num > 999: raise Exception("****Overflow on old suffix number conversion: %d" % num)
                        try:
                            retVal = "%s%03d" % (prefix[0], num)
                        except:
                            retVal = idString
                            logger.warning("****Nonstandard Local ID Adjust failed: %s (%s)" % (num, e))

                        logger.info("Fixing nonstandard IDs (e.g., 10a):  %s" % idString)

                    except Exception as e:
                        #raise log_error("****Nonstandard Local ID failed coercion: %s (%s)" % (parts[1], e))
                        retVal = idString
                        logger.error("****Nonstandard Local ID failed coercion: %s (%s)" % (parts[1], e))

        return retVal

#--------------------------------------------------------------------------------
def splitLocalID(idString):
    """
    Takes a localID or locator string and splits it into componants

    If there's no local id, returns ""
    If it is not a locator, returns the whole string
    assuming it must be just the idref already

    Args:
      idString (string):  The name to use.

    Returns:
      tuple.  ()
      First member is locator, or None
      Second member is localID or None or idString if it's not a Locator

    >>> print (splitLocalID("gobbely gook"))
    (None, 'gobbely gook')

    >>> print (splitLocalID("zbk.052.0001A.P0607"))
    ('zbk.052.0001A', 'P0607')

    test abberant local ID from TNF
    >>> print (splitLocalID("zbk.052.0001A.FN0607"))
    ('zbk.052.0001A', 'FN0607')

    >>> print (splitLocalID("zbk.052.0001A"))
    ('zbk.052.0001A', None)
    """

    locatorRef = None
    # make sure its a string
    if not isinstance(idString, str):  # supports string and unicode
        idString = str(idString)

    m = opasLocator.Locator.rgxLocator.match(idString)
    if m is not None:
        localIDRef = m.group("localID")
        locatorRef = m.group("articleID")
    else:
        localIDRef = idString

    return locatorRef, localIDRef

#--------------------------------------------------------------------------------
def isLocalID(idString):
    """
    Return true if the string is a localId or a locator with a localID component

    Args:
      idString (string):  The name to use.

    Returns:
      Bool.  The return code::
         True -- String is a localID
         False -- String is not a localID

    >>> isLocalID(opasLocator.Locator("zbk.052.0001A").localID("P0607"))
    True
    >>> isLocalID("H0607")
    True
    >>> isLocalID("B001")
    True
    >>> isLocalID("Y-223344210607")
    True
    >>> isLocalID("Y-_223344210607")
    True
    >>> isLocalID("Y-_44444333223344210607")
    True
    >>> isLocalID("Y-_4444433322334421H0607")
    False
    """

    retVal = False  #default return

    if not isinstance(idString, str):  # supports string and unicode Was type(idString)!=type(""):
        idString = str(idString)

    #print "IDString: ", idString
    if not opasXMLPEPAuthorID.isAuthorIDString(idString):
        if isShortIDRef(idString):
            #if 1: print "Short ID!"
            retVal = True
        else:
            m = opasLocator.Locator.rgxLocator.match(idString)
            if m is not None:
                if m.group("localID") is not None:
                    #if 1: print m.group("localID")
                    # that just grabs the last part.  Now check it!	   20071101
                    if isShortIDRef(m.group("localID")):
                        retVal = True

    return retVal

#--------------------------------------------------------------------------------
def isShortIDRef(idString):
    """
    Return true if this matches the "short id pattern" used in PEPA1, e.g.,
    	B001, F001, etc.  (A letter followed by digits, including "_" as desired.)

    >>> isShortIDRef("H0607")
    True
    >>> isShortIDRef("B001")
    True
    """

    retVal = False
    #print "ShortIDRef: ", idString
    if idString is not None:
        m = LocalID.rgxShortID.match(idString)
        if m is not None:
            if m.group("pepshortID") is not None:
                retVal = True

    return retVal

#--------------------------------------------------------------------------------
def isValidShortIDRef(idString):
    """
    Return true if this matches the "short id pattern" used in PEPA1, e.g.,
    	B001, F001, etc.  AND its also valid per the rules for those.

    >>> isValidShortIDRef("T0607")
    True
    >>> isValidShortIDRef("B0000001")
    False
    >>> isValidShortIDRef("Y-0000001")
    True
    >>> isValidShortIDRef("B-0001")
    False
    >>> isValidShortIDRef("P0999")
    True
    >>> isValidShortIDRef("PR099")
    True
    """

    retVal = False
    #print "ShortIDRef: ", idString
    if idString is not None:
        m = LocalID.rgxValidShortID.match(idString)
        if m is not None:
            if m.group("pepshortID") is not None:
                retVal = True

    return retVal

#--------------------------------------------------------------------------------
def isLocalIDBiblioRef(idVal):
    """
    Return true if this is a biblio ref type localID
    """

    retVal = False
    #print "ShortIDRef: ", idString
    if isinstance(idVal, str):  # supports string and unicode Was type(idVal) == type(""):
        pgRefLoc = opasLocator.Locator(idVal)
    elif isinstance(idVal, opasLocator.Locator):
        pgRefLoc = idVal
    else:
        raise Exception("Bad Argument to isLocalIDBiblioRef: ").with_traceback(idVal)

    localIDtype = pgRefLoc.localIDType()

    if localIDtype == "B":
        retVal = True

    return retVal

#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------
if __name__ == "__main__":
    """
	Run Locator test routines
	"""

    import sys

    import doctest
    doctest.testmod()
    sys.exit()

