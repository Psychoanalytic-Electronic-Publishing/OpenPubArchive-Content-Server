# -*- coding: UTF-8 -*-

"""
Classes to manage the VolumeNumbers, PageNumbers, and PageRanges, as would be found in books and journals.

Contains classes:
	VolumeNumber		 - Class to encapsulate journal and book volume numbers, as their own data type.
	PageNumber 			 - Class to encapsulate pagenumbers for journal and book as their own type, as they have special non-numeric properties!
	PageRange			 - Class to represent a range of pages, e.g., 1-200.

"""
#TODO: At some point these could be separated into their own modules.
#MODIFIED:
#			2009-07-17 - Major cleanup of docstrings and added doctests
#

import string, re # , exceptions
import logging
logger = logging.getLogger(__name__)

import opasMath
import opasStringSupport
#import sciSupport
#import sciErrorLogging
# import sciUnicode

LOCALID = "LocalID"			# need this here because it is the default for a argument
                            # and you can't use the local class definition,

def cmp(a, b):
    """
    Replace Python 2 cmp function
    
    >>> cmp(10,1)
    1
    >>> cmp("10","1")
    1
    >>> cmp(1,10)
    -1
    >>> cmp("1","1")
    0
    >>> cmp("1",None)
    1
    >>> cmp(None, 1)
    -1
    """
    ret_val = -1
    if a is None and b is not None:
        ret_val = -1
    elif b is None and a is not None:
        ret_val = 1
    else:
        ret_val = (a>b)-(a<b)

    return ret_val
    

#----------------------------------------------------------------------------------------
# CLASS DEF: Vol
#----------------------------------------------------------------------------------------

class VolumeNumber:

    """
	Class to encapsulate journal and book volume numbers, as their own data type.

	A volume number can now be 1 to 4 digits!  It can have a letter suffix (repeated), and a special "S" suffix (supplement)

	@TODO: That's little too loose in the suffix area; should be tightened.

	>>> VolumeNumber("IVS")
	4
	>>> VolumeNumber("IV (Suppl)")
	4
	>>> VolumeNumber("022A") == '22A'
	True
	>>> VolumeNumber("022A")
	22A
	>>> VolumeNumber("5,7")
	5
	>>> VolumeNumber("IV")
	4
	>>> VolumeNumber("4S")
	4S
	>>> VolumeNumber("4AS")
	4AS
	>>> VolumeNumber("4ABCS")
	4ABCS
	>>> VolumeNumber("4SABCS")
	4SABCS
	>>> VolumeNumber(22)
	22
	>>> VolumeNumber('22S')
	22S
	>>> str(VolumeNumber('22S'))
	'22S'
	>>> VolumeNumber("22S").volID(noLeadingZeros=True)
	'22S'
	>>> VolumeNumber("22Suppl")
	22S
	>>> VolumeNumber("022S").volID(noSuffix=True)
	'022'
	>>> VolumeNumber("022S").volID(noSuffix=True, noLeadingZeros=True)
	'22'
	>>> a = VolumeNumber("IV")
	>>> VolumeNumber(a, volSuffix="G")
	4G
	>>> c = VolumeNumber("10", volSuffix="S")
	>>> "Val %s" % c	   # when forced to string, it includes the suffix
	'Val 10S'
	>>> "Val %d" % c	   # note when forced to int, it drops the volSuffix!
	'Val 10'
	>>> str(VolumeNumber(c)) # this should show the "S" suffix
	'10S'
	>>> c.volID()
	'010S'


	"""

    rgxSuppl = re.compile("sup(p|pl|ple|plemen(t?))\.?", re.IGNORECASE)

    #--------------------------------------------------------------------------------
    def __init__(self, volNum=0, volSuffix=None):
        """
        Initialize pagenumber object
        If forceRoman = true, the int pgNum is flagged to be interpreted as roman (i.e.,
        	isRoman will return true)

        Note: Setting volSuffix to "" will remove the volume suffix if volNum is already a volumenumber
        """

        if isVolumeNumber(volNum):
            # if argument is already a volume number instance.
            self.volPrefix = volNum.volPrefix
            self.volNumber = volNum.volNumber
            if volSuffix is None:
                self.volSuffix = volNum.volSuffix
            else:
                self.volSuffix = volSuffix

            self.volRomanLower = volNum.volRomanLower
            self.volOriginalType = volNum.volOriginalType
        else:
            self.volNumber = ""
            self.volPrefix = ""
            if volSuffix is None:
                self.volSuffix = volSuffix = ""
            else:
                self.volSuffix = volSuffix
            self.volRomanLower = False			# lowercase roman numerals
            self.volOriginalType = "A"
            if volNum is None or volNum=="":
                #raise "Bad volNum"
                volNum = 0

            if isinstance(volNum, str):  # supports string and unicode Was if type(volNum) == type(""):
                self.volNumStr = volNum
                volNum.lstrip()
                if volNum[0] in "MCLVXI":
                    # probably roman, look for space and split there.
                    volNum = re.split("[,/\-\s&\.ABDEFGHJKNOPQRSTUYZ]", volNum, re.IGNORECASE)
                else: # not roman, use a more careful, non-alpha split
                    volNum = re.split("[,/\-\s&\.]", volNum)
                volNum = volNum[0]
                volNum = opasStringSupport.trim_punct_and_spaces(volNum)

            if opasMath.isRoman(volNum):
                self.volOriginalType = "R"
                self.volNumber = opasMath.conv_roman_to_arabic(volNum)
                if volNum.islower():
                    self.volRomanLower = True
            else:
                prefix, self.volStr, self.volSuffixEmbedded = opasStringSupport.remove_letter_prefix_and_suffix(volNum)
                # if a suffix was supplied, use that as precedent.  Embedded suffix is stored anyway
                if self.volSuffix == "" and self.volSuffixEmbedded is not None:
                    self.volSuffix = self.volSuffixEmbedded

                self.volNumber = opasMath.convert_string_to_arabic(self.volStr)
                #print "Check: ", self.volNumber, type(self.volNumber), "Suffix: %s" % self.volSuffix
                if self.volSuffix in ["-", "&"]:
                    self.volSuffix = ""

                if self.volSuffix is None:
                    self.volSuffix = ""

                # standardize the "Roman" prefix
                if prefix.lower()=="r":
                    self.volOriginalType = prefix
                    raise f"Volume Number Prefix Found: {prefix}"

    #--------------------------------------------------------------------------------
    def __repr__(self):
        # make sure no one set this to None
        retVal = self.__str__()
        return retVal

    #--------------------------------------------------------------------------------
    def isRoman(self):
        retVal = (True == (string.upper(self.volOriginalType) == "R"))
        return retVal

    #--------------------------------------------------------------------------------
    def format(self, formatStr=None):

        if opasStringSupport.isEmpty(formatStr):
            if self.volNumber > 999:
                formatStr="%04d"
            else:
                formatStr="%03d"

        retVal = formatStr % self.volNumber
        return retVal
    #--------------------------------------------------------------------------------
    def standardizeSuffix(self):

        if self.volSuffix!=None:
            if None!=self.rgxSuppl.match(self.volSuffix):
                # match, so it's supplement, change to "S"
                self.volSuffix = "S"
            #print "Standardized suffix."
    #--------------------------------------------------------------------------------
    def __getitem__(self,n):
        val = self.volID()
        return val[n]

    #--------------------------------------------------------------------------------
    def __str__(self):
        self.standardizeSuffix()
        #retVal = "%s%s" % (self.volNumber, self.volSuffix)
        retVal = self.volID(noLeadingZeros=True)
        return retVal

    #--------------------------------------------------------------------------------
    def display(self):
        retVal = "(%s, %s, %s)" % (self.volPrefix, self.volNumber, self.volSuffix)
        return retVal

    #--------------------------------------------------------------------------------
    def volID(self, noSuffix=False, noLeadingZeros=False):
        if self.volSuffix is None:
            if 1: raise "None Suffix ERROR!"
            self.volSuffix = ""

        if self.volNumber > 999:
            formatStr="%04d"
        else:
            formatStr="%03d"

        if noSuffix:
            if noLeadingZeros:
                retVal = "%s" % (self.volNumber)
            else:
                retVal = formatStr % (self.volNumber)
        else:
            if noLeadingZeros:
                retVal = "%s%s" % (self.volNumber, self.volSuffix)
            else:
                retVal = (formatStr + "%s") % (self.volNumber, self.volSuffix)

        #print "VolID: ", retVal, self.volSuffix
        return retVal

    #--------------------------------------------------------------------------------
    def __sub__(self, val2):
        """
        Combine/concatenate number to current pagenumber.
        """

        raise "Error: You cannot subtract two volume numbers!"

    #--------------------------------------------------------------------------------
    def __add__(self, val2):
        """
        Combine/concatenate number to current pagenumber.
        """

        raise "Error: You cannot add two volume numbers!"

    #--------------------------------------------------------------------------------
    def __eq__(self, other):
        """
        Assess equality of two objects.
        """
        retVal = (0 == self.__cmp__(other))

        return retVal

    #--------------------------------------------------------------------------------
    def __int__(self):
        if self.volNumber is None:
            raise "INT Convert Error: %s" % self.volNumber
        else:
            return self.volNumber

    #--------------------------------------------------------------------------------
    def __len__(self):
        return len(self.__str__())

    #--------------------------------------------------------------------------------
    def __long__(self):
        return int(self.volNumber)

    #--------------------------------------------------------------------------------
    def __cmp__(self, other):
        retVal = 0
        if other is None:
            #print "comparing to none"
            retVal = cmp(self.volNumber, other)
        elif not isinstance(other, VolumeNumber):
            other = VolumeNumber(other)
        else:
            raise Exception("Trapped!")
        
        if isinstance(other, VolumeNumber):
            suffixComp = cmp(self.volSuffix, other.volSuffix)
            nbrComp = cmp(self.volNumber, other.volNumber)
            if nbrComp != 0:
                #print "number:", nbrComp
                retVal = nbrComp
            elif suffixComp != 0:
                # numbers are same, return suffix comparison
                #print "volSuffix: %s, %s, %s" % (suffixComp, self.volSuffix, other.volSuffix)
                retVal = suffixComp
            else:
                # numbers are same, suffix is same
                retVal = 0
            #print "Compare %s (%s) to %s (%s) = %s" % (self.volNumber, type(self.volNumber), other, type(other.volNumber),  retVal)
        else:
            raise Exception(f"Wrong type for VolNumber comparison {type(other)}")
            # retVal = cmp(self.volNumber, other)

        return retVal

#----------------------------------------------------------------------------------------
# CLASS DEF: PageNumber
#----------------------------------------------------------------------------------------

class PageNumber:

    """
	Class to encapsulate pagenumbers for journal and book as their own type, as they have special non-numeric properties!

	A volume number can now be 1 to 4 digits!  It can have a letter suffix (repeated), and a special "S" suffix (supplement)

	@TODO: That's little too loose in the suffix area; should be tightened.

	>>> PageNumber("3b") < PageNumber("3a")
	False
	>>> PageNumber("R7") > PageNumber("2")
	False
	>>> PageNumber("2") > PageNumber("R2")
	True
    >>> PageNumber("E1").pgPrefix
    'E'
	>>> PageNumber("022A")
	22A
	>>> PageNumber("IV")
	IV
	>>> PageNumber("IVS")
	0
	>>> PageNumber("IV (Suppl)")
	0
	>>> PageNumber("4S")
	4S
	>>> PageNumber("4AS")
	4AS
	>>> PageNumber("4ABCS")
	4ABCS
	>>> PageNumber("4SABCS")
	4SABCS
	>>> PageNumber("iv").isRoman()
	True
	>>> PageNumber("4").isRoman()
	False
	>>> PageNumber("4a").isRoman()
	False
	>>> PageNumber("iva").isRoman()
	False
	>>> PageNumber(3) > PageNumber(6)
	False
	>>> PageNumber(6) > PageNumber(3)
	True
	>>> PageNumber("3") > PageNumber(6)
	False
	>>> PageNumber("6") > PageNumber(3)
	True
	>>> PageNumber("R7") > PageNumber("R2")
	True
	>>> PageNumber("R2") > PageNumber("R7")
	False
	>>> PageNumber("R1") > PageNumber("R2")
	False
	>>> PageNumber("R7") > PageNumber("2")
	False
	>>> PageNumber("R7") < PageNumber("2")
	True
	>>> PageNumber("R13") < PageNumber("7")
	True
	>>> PageNumber("R3") < PageNumber("R1")
	False
	>>> PageNumber("R3a") < PageNumber("R1a")
	False
	>>> PageNumber("R13a") < PageNumber("7a")
	True
	>>> PageNumber("3") > PageNumber("R7")
	True
	>>> PageNumber("3a") > PageNumber("6b")
	False
	>>> PageNumber("3a") > PageNumber("6a")
	False
	>>> PageNumber("6a") > PageNumber("3a")
	True
	>>> PageNumber("6a") > PageNumber("3b")
	True
	>>> PageNumber("3b") > PageNumber("3a")
	True
	>>> PageNumber("iii") > PageNumber("xxii")
	False
	>>> PageNumber("v") > PageNumber("ii")
	True
	>>> PageNumber("3") == PageNumber("3")
	True
	>>> PageNumber("3") == PageNumber("3f")
	False
	"""

    LOCALID = LOCALID		# format keyword option (defined as a module constant because
                            #  it's used as the default for a argument.

    FORCEINT = "ForceInt"	# Use this to force the page number to an integer, EVEN if it's
                            # roman.  Roman page numbers will be changed to negatives.
                            # This allows the number to be stored in a database where the field
                            # is integer.

    #--------------------------------------------------------------------------------
    def __init__(self, pgNum=0, forceRoman=None):
        """
        Initialize the pagenumber object, optionally setting the value to pgNum.

        If forceRoman = true, the int pgNum is flagged to be interpreted as roman (i.e.,
        	isRoman will return true)
        """
        self.pgSuffix = ""
        self.pgNumberText = repr(pgNum)
        self.pgPrefix = ""
        self.pgRomanLower = False			# lowercase roman numerals
        self.internalNotation = False

        if isinstance(pgNum, PageNumber):
            pgNum = pgNum.forceInt()
            
        if pgNum is None or pgNum=="":
            logger.warning("Bad pgNum (None or empty)", "Warning - Bad PgNum")
            #raise "Bad pgNum"
            pgNum = 0

        if isinstance(pgNum, int):
            if pgNum < 0:
                self.pgPrefix = "R"
                self.pgNumber = -pgNum

        if opasMath.isRoman(pgNum):
            self.pgPrefix = "R"
            self.pgNumber = opasMath.conv_roman_to_arabic(pgNum)
            if self.pgNumberText.islower():
                self.pgRomanLower = True
        else:
            self.pgPrefix, self.pgStr, self.pgSuffix = opasStringSupport.remove_letter_prefix_and_suffix(pgNum)
            self.pgNumber = opasMath.convert_string_to_arabic(self.pgStr)
            # standardize the "Roman" prefix

            if self.pgPrefix=="r" or self.pgPrefix=="-":
                if self.pgNumber!=0:
                    self.pgPrefix = "R"

                if self.pgNumber<0:
                    print("Negative!")
                    logger.warning("Negative pgNumber: %s" % self.pgNumber, "Warning - Negative PgNum")
                    self.pgNumber = -self.pgNumber

            if self.pgPrefix == "P" or self.pgPrefix == "p":
                self.pgPrefix = ""

            if self.pgPrefix == "PR":
                self.pgPrefix = "R"


        if forceRoman:
            self.pgPrefix = "R"

        #print "Initd.  PgPrefix = ", self.pgPrefix

        #print "PageNumberInit: (%s, %s, %s)" % (self.pgPrefix, self.pgNumber, self.pgSuffix)

    #--------------------------------------------------------------------------------
    def __repr__(self):
        retVal = self.__str__()
        return retVal

    #--------------------------------------------------------------------------------
    def isRoman(self):
        """
        Return true if the current value is Roman

        >>> pgNum = PageNumber("iv")
        >>> pgNum.isRoman()
        True

        >>> pgNum = PageNumber("3")
        >>> pgNum.isRoman()
        False
        """

        retVal = (True == (self.pgPrefix == "R"))
        return retVal

    #--------------------------------------------------------------------------------
    def forceInt(self):
        """
        Return an integer page number; if roman, return it as negative

        >>> pgNum = PageNumber("iv")
        >>> pgNum.forceInt()
        -4

        >>> pgNum = PageNumber("2")
        >>> pgNum.forceInt()
        2

        """
        pgNumber = self.pgNumber
        if pgNumber is None:
            retVal = 0
        else:
            if self.pgPrefix == "R":
                # return int
                retVal = -pgNumber
            else:
                retVal = pgNumber

        return retVal

    #--------------------------------------------------------------------------------
    def format(self, keyword=LOCALID, formatStr=None):
        """
        Format the page number as a localID (default) per the formatStr argument.
        Args:
        	keyword = Only working value is LOCALID
        	formatStr = Regular python format string, can be used to change significant digits.

        >>> pgNum = PageNumber("iv")
        >>> pgNum.format(keyword=pgNum.LOCALID)
        'PR0004'

        >>> pgNum.format()
        'PR0004'

        >>> pgNum = PageNumber("2")
        >>> pgNum.format(formatStr="%03d")
        'P002'
        """

        if opasStringSupport.isEmpty(formatStr):
            formatStr="%04d"

        #if self.pgPrefix == "P":
        #	raise "Trap 2"

        if keyword == LOCALID:
            #print "Formatting Page Ref: %s" % self.pgNumber, self.pgPrefix
            retVal = "P" + self.pgPrefix + (formatStr % self.pgNumber)

        else:
            retVal = self.pgPrefix + (formatStr % self.pgNumber)

        #print "Returning: %s (prefix: %s, pgnum: %s)" % (retVal, self.pgPrefix, self.pgNumber)
        return retVal


    #--------------------------------------------------------------------------------
    def strInternal(self):
        self.internalNotation = True
        retVal = self.__str__()
        self.internalNotation = False
        return retVal

    #--------------------------------------------------------------------------------
    def __str__(self):
        prefix = ""
        suffix = ""
        pgNumber = self.pgNumber
        if pgNumber is None:
            retVal = ""
        else:
            if self.pgPrefix == "R":
                if self.internalNotation==False:
                    # show this in roman
                    pgNumber = opasMath.arabic_to_roman(pgNumber, self.pgRomanLower)
                    prefix = ""
                else: # keep arabic representation, prefix with R
                    prefix = self.pgPrefix

            elif self.pgPrefix!=None:
                prefix = self.pgPrefix

            if self.pgSuffix!=None:
                suffix = self.pgSuffix

            retVal = "%s%s%s" % (prefix, pgNumber, suffix)

        return retVal

    #--------------------------------------------------------------------------------
    def display(self):
        retVal = "(%s, %s, %s)" % (self.pgPrefix, self.pgNumber, self.pgSuffix)
        return retVal

    #--------------------------------------------------------------------------------
    def pageID(self):
        retVal = "%s%04d%s" % (self.pgPrefix, self.pgNumber, self.pgSuffix)
        return retVal

    #--------------------------------------------------------------------------------
    def __add__(self, val2):
        """
        Combine/concatenate number to current pagenumber.
        """

        self.pgNumber = self.pgNumber + int(val2)
        return self

    #--------------------------------------------------------------------------------
    def __eq__(self, other):
        """
        Assess equality of two objects.
        """
        retVal = (0 == self.__cmp__(other))

        return retVal

    #--------------------------------------------------------------------------------
    def __int__(self):
        if self.pgNumber is None:
            raise "INT Convert Error: %s" % self.pgNumber
        else:
            retVal = self.pgNumber
            return retVal

    #--------------------------------------------------------------------------------
    def __len__(self):
        return len(self.__str__())

    #--------------------------------------------------------------------------------
    def __long__(self):
        return int(self.pgNumber)

    #--------------------------------------------------------------------------------
    def __sub__(self, val2):
        """
        Combine/concatenate number to current pagenumber.
        """

        self.pgNumber = self.pgNumber - int(val2)
        return self

    #--------------------------------------------------------------------------------
    def __gt__(self, other):
        """
        """
        if isinstance(other, int) or isinstance(other, str):
            other = PageNumber(other)

        if self.__cmp__(other) > 0:
            ret_val = True
        else:
            ret_val = False
            
        #if other.isRoman() and not self.isRoman():
            #ret_val = True
        #elif self.isRoman() and not other.isRoman():
            #ret_val = False
        #else:
            #ret_val = self.pgNumber > other.pgNumber
        
        return ret_val

    #--------------------------------------------------------------------------------
    def __ge__(self, other):
        """
        """
        if isinstance(other, int) or isinstance(other, str):
            other = PageNumber(other)

        if self.__cmp__(other) > 0 or self.__cmp__(other) == 0:
            ret_val = True
        else:
            ret_val = False
            
        #if other.isRoman() and not self.isRoman():
            #ret_val = True
        #elif self.isRoman() and not other.isRoman():
            #ret_val = False
        #else:
            #ret_val = self.pgNumber > other.pgNumber
        
        return ret_val

    #--------------------------------------------------------------------------------
    def __lt__(self, other):
        """
        """
        if isinstance(other, int) or isinstance(other, str):
            other = PageNumber(other)
        if self.__cmp__(other) < 0:
            ret_val = True
        else:
            ret_val = False
        
        #if other.isRoman() and not self.isRoman():
            #ret_val = False
        #elif self.isRoman() and not other.isRoman():
            #ret_val = True
        #else:
            #ret_val = self.pgNumber < other.pgNumber

        return ret_val

    #--------------------------------------------------------------------------------
    def __le__(self, other):
        """
        """
        if isinstance(other, int) or isinstance(other, str):
            other = PageNumber(other)
        if self.__cmp__(other) < 0 or self.__cmp__(other) == 0:
            ret_val = True
        else:
            ret_val = False
        
        #if other.isRoman() and not self.isRoman():
            #ret_val = False
        #elif self.isRoman() and not other.isRoman():
            #ret_val = True
        #else:
            #ret_val = self.pgNumber < other.pgNumber

        return ret_val

    #--------------------------------------------------------------------------------
    def __cmp__(self, other):
        retVal = 0
        if isinstance(other, int) or isinstance(other, str):
            other = PageNumber(other)
            
        if isinstance(other, PageNumber):
            if self.pgPrefix != other.pgPrefix:
                #print "Prefix:", self.pgPrefix, other.pgPrefix, self.pgPrefix > other.pgPrefix
                if self.isRoman():
                    # roman pages first
                    retVal = -1
                elif other.isRoman():
                    # roman pages first
                    retVal = 1
            else:
                # prefixes are the same
                suffixComp = cmp(self.pgSuffix, other.pgSuffix)
                nbrComp = cmp(self.pgNumber, other.pgNumber)
                if nbrComp != 0:
                    retVal = nbrComp
                elif suffixComp != 0:
                    # numbers are same, return suffix comparison
                    retVal = suffixComp
                else:
                    # numbers are same, suffix is same
                    retVal = 0
            # else: retVal = 0
        else:
            # raise "Wrong type for PageNumber comparison '%s'", type(other)
            retVal = cmp(self.pgNumber, other)

        return retVal

#----------------------------------------------------------------------------------------
# CLASS DEF: PageList
#
#  A string, converted to a list with some extra functions
#----------------------------------------------------------------------------------------
class PageList(list):
    """
    >>> test = PageList("5, 6, 7")

    >>> test.contains(5)
    True

    >>> test.contains(3)
    False

    >>> test.contains("5")
    True

    """
    #--------------------------------------------------------------------------------
    def __init__(self, pgListStr=""):
        """
        Pass in a string which is a list, and the function returns a list of page number objects.
        """
        self.pgListStr = pgListStr
        self.isValid = False
        self.pgList = []
        if pgListStr is not None:
            self.pgList = [PageNumber(x) for x in pgListStr.split(",")]

        list.__init__(self, self.pgList)

    #--------------------------------------------------------------------------------
    def contains(self, thePageNumber):
        """
        Does the list contain the number?
        """
        retVal = False
        if thePageNumber in self.pgList:
            retVal = True

        return retVal



#----------------------------------------------------------------------------------------
# CLASS DEF: PageRange
#
#  A range of pagenumbers
#----------------------------------------------------------------------------------------

class PageRange:
    """
		Class to represent a range of pages, e.g., 1-200.
		The start of the range 	is given by pgRg.pgStart, and the end by pgRg.pgEnd.
		These two page numbers 	are instances of the PageNumber object.

	A volume number can now be 1 to 4 digits!  It can have a letter suffix (repeated), and a special "S" suffix (supplement)

	>>> (PageRange("14") == PageRange("12-14"))
	True
	>>> (PageRange("13") == PageRange("12-14"))
	True
	>>> PageRange("635-47")
	635-647
	>>> PageRange("635-7")
	635-637
	>>> PageRange("6350-57")
	6350-6357
	>>> PageRange("6350-7")
	6350-6357
	>>> (PageRange("5") > PageRange("12-14"))
	False
	>>> (PageRange("11") > PageRange("12-14"))
	False
	>>> (PageRange("15") > PageRange("12-14"))
	True
	>>> (PageRange(15) > PageRange("12-14"))
	True
	>>> (PageRange("14") > PageRange("12-14"))
	False
	>>> (PageRange("15") < PageRange("12-14"))
	False
	>>> (PageRange("11") < PageRange("12-14"))
	True
	>>> (PageRange("R14") < PageRange("12-14"))
	True
	>>> (PageRange("12") < PageRange("12-14"))
	False
	>>> (PageRange("14") < PageRange("12-14"))
	False
	>>> (PageRange("12") == PageRange("12-14"))
	True
	>>> PageRange("12-14").exactlyEqual(PageRange("12-14"))
	True
	>>> PageRange("12-13").exactlyEqual(PageRange("12-14"))
	False
	>>> PageRange("11-14").exactlyEqual(PageRange("12-14"))
	False
	>>> PageRange("11-12").exactlyEqual(PageRange("12-14"))
	False
	>>> PageRange("10-11").exactlyEqual(PageRange("12-14"))
	False
	>>> PageRange("12-14").exactlyEqual(PageRange("12-14"))
	True
	>>> PageRange("12-14").exactlyEqual(PageRange(10))
	False
	>>> PageRange("12-14").exactlyEqual(PageRange("10-11"))
	False
	>>> PageRange("12-14").contains(PageRange("13a"))
	True
	>>> PageRange("12-14").contains(PageRange("13"))
	True
	>>> PageRange("12-14").contains(PageRange("12"))
	True
	>>> PageRange("12-14").contains(PageRange("13"))
	True
	>>> PageRange("12-14").contains(PageRange("14"))
	True
	>>> PageRange("12-14").contains(PageRange("13c"))
	True
	>>> PageRange("12-14").contains(PageRange("11"))
	False
	>>> PageRange("12-14").contains(12)
	True
	>>> PageRange("12-14").contains("12")
	True
	>>> PageRange("12-14").contains(PageNumber("12"))
	True
	>>> PageRange("10-20").validate()
	True
	>>> PageRange("10a-20").validate()
	True
	>>> PageRange("10-20b").validate()
	True
	>>> PageRange("iii-iv").validate()
	True
	>>> PageRange("iii-20").validate()
	True
	>>> PageRange("5-2").validate()
	False
	>>> PageRange("5-iii").validate()
	False
	>>> PageRange("iii-20").validate(isRomanStart=False)
	False
	>>> PageRange("iii-20").validate(isRomanStart=True)
	True
	>>> PageRange("iii-20").validate()
	True
	>>> PageRange("iii").validate()
	True

	"""

    #--------------------------------------------------------------------------------
    def __init__(self, pgRg="", sourceLabel=""):
        """
        Initialize the PageRange object, optionally setting the value to the supplied parameter pgrg.

        sourceLabel is optionally to identify object of pgRg for logging information
        """
        if type(pgRg) == type(0):
            pgRgWork = str(pgRg)
        elif isinstance(pgRg, PageNumber):
            pgRgWork = repr(pgRg)
            #print "PGTYPE: ", type(pgRg)
        elif isinstance(pgRg, PageRange):
            pgRgWork = repr(pgRg)
        else:
            pgRgWork = pgRg

        if pgRgWork is not None:
            if "–" in pgRgWork:
                pgrgList = pgRgWork.split("–") # ndash
            else:
                pgrgList = pgRgWork.split("-")
            pgStart = pgrgList[0]
            if len(pgrgList) > 1:
                pgEnd = pgrgList[1].strip()
            else:
                pgEnd = pgrgList[0].strip()

            self.pgStart = PageNumber(pgStart)
            if pgEnd =="" or pgEnd is None:
                self.pgEnd = PageNumber(pgStart)
            else:
                try:
                    err1 = "Bad page range %s (%s)...could not auto repair" % (pgRg, sourceLabel)
                    self.pgEnd = PageNumber(pgEnd)
                    if self.pgEnd < self.pgStart:
                        try:
                            if len(pgEnd) == len(pgStart) - 1:
                                pgEnd2 = pgStart[0] + pgEnd
                                self.pgEnd = PageNumber(pgEnd2)
                                if self.pgEnd < self.pgStart:
                                    if "<be" in sourceLabel:
                                        logger.warning(f"Bad PgRg in Ref {err1}")
                                    else:
                                        logger.error(f"Bad PgRg {err1}")

                            elif len(pgEnd) == len(pgStart) - 2:
                                pgEnd2 = pgStart[0:2] + pgEnd
                                self.pgEnd = PageNumber(pgEnd2)
                                if self.pgEnd < self.pgStart:
                                    logger.error(f"Bad PgRg {err1}")
                            elif len(pgEnd) == len(pgStart) - 3:
                                pgEnd2 = pgStart[0:3] + pgEnd
                                self.pgEnd = PageNumber(pgEnd2)
                                if self.pgEnd < self.pgStart:
                                    logger.error(f"Bad PgRg {err1}")
                            else:
                                logger.error(f"Bad PgRg {err1}")
                        except Exception as e:
                            logger.error("Exception: %s.  %s" % (str(e), err1), errorType="Warning - Bad PgNum")
                            #raise Exception, e

                except Exception as e:
                    logger.error("PgEnd Exception: %s.  %s" % (str(e), err1), errorType="Warning - Bad PgNum")
                    # raise Exception, e
        else:
            raise Exception("PgRg Error")

            #print "Initialize Range: %s (%s) to %s (%s) = %s" % (self.pgStart, type(self.pgStart), self.pgEnd, type(self.pgEnd),  self.pgStart==self.pgEnd)
            #print self.pgStart, self.pgEnd
    #--------------------------------------------------------------------------------
    def __repr__(self):
        """
        Return the page range as a displayable string.
        """
        return self.__str__()

    #--------------------------------------------------------------------------------
    def __add__(self, val2):
        """
        Combine/concatenate number to current pagenumber.
        """

        raise "Add is not supported for PageRanges."

    #--------------------------------------------------------------------------------
    def __eq__(self, other):
        """
        Assess equality of two objects.
        """
        retVal = (0 == self.__cmp__(other))

        return retVal

    #--------------------------------------------------------------------------------
    def __lt__(self, other):
        """
        Compare two page ranges.  If either is contained within the other, returns true
        """
        retVal = False
        if self.pgEnd < other.pgStart:
            retVal = True

        return retVal
    #--------------------------------------------------------------------------------
    def __gt__(self, other):
        """
        Compare two page ranges.  If either is contained within the other, returns true
        """
        retVal = False
        if self.pgStart > other.pgEnd:
            retVal = True

        return retVal
    #--------------------------------------------------------------------------------
    def __str__(self):
        """
        Return the page range as a displayable string.
        """
        if self.pgStart != self.pgEnd:
            start = self.pgStart
            # don't let a range start with 0
            if start==0:
                retVal = "1-%s" % (self.pgEnd)
            else:
                retVal = "%s-%s" % (start, self.pgEnd)
        else:
            retVal = "%s" % (self.pgStart)

        return retVal

    #--------------------------------------------------------------------------------
    def validate(self, isRomanStart=None, isRomanEnd=None):
        """
        Validate the page range.  Return True if valid.
        """
        retVal = False
        if (self.pgStart <= self.pgEnd):
            retVal = True
        if isRomanStart==False and self.pgStart.isRoman():
            retVal = False
        if isRomanEnd==False and self.pgEnd.isRoman():
            retVal = False

        return retVal

    #--------------------------------------------------------------------------------
    def exactlyEqual(self, other):
        """
        Compare two page ranges.  If either is contained within the other, returns true
        """
        retVal = False
        if (self.pgStart == other.pgStart and self.pgEnd == other.pgEnd):
            retVal = True

        return retVal

    #--------------------------------------------------------------------------------
    def eitherContains(self, other):
        """
        Compare two page ranges.  If either is contained within the other, returns true
        """
        retVal = False
        if (self.pgStart >= other.pgStart and self.pgEnd <= other.pgEnd) \
           or (other.pgStart >= self.pgStart and other.pgEnd <= self.pgEnd):
            retVal = True

        return retVal


    #--------------------------------------------------------------------------------
    def contains(self, other):
        """
        Compare two page ranges.  If other is contained in self, returns true
        """
        retVal = False
        if isinstance(other, PageNumber):
            #print "PageNumber!"
            if (self.pgStart <= other.pgNumber and self.pgEnd >= other.pgNumber):
                retVal = True
        elif not isinstance(other, PageRange):
            #print other, type(other)
            try:
                otherNum = PageNumber(other)
            except:
                raise Exception("Can't compare to %s" % type(other))

            if (self.pgStart <= otherNum and self.pgEnd >= otherNum):
                retVal = True
        else:
            if (self.pgStart <= other.pgStart and self.pgEnd >= other.pgEnd):
                retVal = True

        return retVal

    #--------------------------------------------------------------------------------
    def __len__(self):
        return len(self.__str__())

    #--------------------------------------------------------------------------------
    def __cmp__(self, other=None):
        """
        Compare two page ranges.
        IMPORTANT: if one of the ranges contains the other, the return is equal (0)
        """
        retVal = 0
        if other is None or not isinstance(other, PageRange):
            retVal = 1
        else:
            #print "Other: ", other, type(other)
            try:
                if self.eitherContains(other):
                    #retVal = 0
                    #print "Warning: Contains"
                    pass
                else:
                    try:
                        retVal = self.pgStart.__cmp__(other.pgStart)
                    except Exception as e:
                        # other may be different type ot none
                        raise "Error: Wrong Type(s) %s - %s (%s)" % (other, type(other), e)
            except Exception as e:
                print(("PgRg Exception %s" % e))

        #print "Returning: ",  retVal
        return retVal


class PubYear:
    """
    Class to encapsulate year for reference processing.  Helps to clean up any irregularities.

    A year must be 4 digits!  If you have 2, it will assume the defaultCentury and add it.
    Any characters following the year are stripped out.

    @TODO: Perhaps detect range and store the second part of the range.

    >>> PubYear("1922")
    1922
    >>> PubYear("1922-25")
    1922
    >>> PubYear("22-25")
    1922
    >>> PubYear("25")
    1925
    >>> PubYear("2014") + 1
    2015
    """

    rgxSuppl = re.compile("sup(p|pl|ple|plemen(t?))\.?", re.IGNORECASE)
    rgxYear = re.compile("((?P<baseYear>[1-9][0-9]([0-9][0-9])?)(?P<suffix>.*))", re.IGNORECASE)

    #--------------------------------------------------------------------------------
    def __init__(self, pubYear=0, defaultCentury="19"):
        """
        Initialize year object
        """
        self.yearValue = ""
        self.yearSuffix = ""

        if isinstance(pubYear, PubYear):  		# use callers object
            self = pubYear
        else:
            if isinstance(pubYear, int):
                pubYear = str(pubYear)
                self.yearValue = pubYear

            if isinstance(pubYear, str):  	# supports string and unicode Was if type(volNum) == type(""):
                m = self.rgxYear.match(pubYear)
                if m is not None:
                    self.yearValue = m.group("baseYear")
                    self.yearSuffix = m.group("suffix")
        if len(self.yearValue) == 2:
            # they left off the century
            self.yearValue = "%s%s" % (defaultCentury, self.yearValue)

    #--------------------------------------------------------------------------------
    def __repr__(self):
        retVal = self.yearValue
        return retVal

    #--------------------------------------------------------------------------------
    def __getitem__(self,n):
        retVal = self.yearValue
        return retVal[n]

    #--------------------------------------------------------------------------------
    def __str__(self):
        retVal = self.yearValue
        return retVal

    #--------------------------------------------------------------------------------
    def display(self):
        retVal = "(%s, %s)" % (self.yearValue, self.yearSuffix)
        return retVal

    #--------------------------------------------------------------------------------
    def __sub__(self, val2):
        """
        Subtract from year
        """
        val1 = self.yearValue
        try:
            retVal = int(val1) - int(val2)
        except Exception as e:
            print(("Error: ", e))

        return retVal
    #--------------------------------------------------------------------------------
    def __add__(self, val2):
        """
        Add to year
        """
        val1 = self.yearValue
        try:
            retVal = int(val1) + int(val2)
        except Exception as e:
            print(("Error: ", e))

        return retVal

    #--------------------------------------------------------------------------------
    def __eq__(self, other):
        """
        Assess equality of two objects.
        """
        retVal = (0 == self.__cmp__(other))

        return retVal

    #--------------------------------------------------------------------------------
    def __int__(self):
        if self.yearValue is None:
            raise "INT Convert Error: %s" % self.yearValue
        else:
            return int(self.yearValue)

    #--------------------------------------------------------------------------------
    def __len__(self):
        return len(self.__str__())

    #--------------------------------------------------------------------------------
    def __long__(self):
        if self.yearValue is None:
            raise "Long Convert Error: %s" % self.yearValue
        else:
            return int(self.yearValue)

    #--------------------------------------------------------------------------------
    def __cmp__(self, other):
        retVal = 0
        if isinstance(other, type(None)):
            #print "comparing to none"
            retVal = cmp(self.yearValue, other)
        elif isinstance(other, PubYear):
            retVal = cmp(self.yearValue, other)
        elif isinstance(other, str):  # supports string and unicode Was if isinstance(other, type("")):
            #print "comparing to string"
            retVal = cmp(self.yearValue, other)
        elif isinstance(other, type(0)):
            #print "comparing to int"
            retVal = cmp(self.yearValue, other)
        else:
            raise f"Wrong type for pubYear comparison '{type(other)}'"

        return retVal

#--------------------------------------------------------------------------------
def isVolumeNumber(val):
    """
    Return true if this is a volume number instance
    """
    if isinstance(val, VolumeNumber):
        retVal = True
    else:
        retVal = False
    return retVal


#--------------------------------------------------------------------------------
def unforceInt(pgNumber):
    """
    If integer page number is negative, return a roman
    """
    if pgNumber < 0:
        pgNumber = -pgNumber
        retVal = PageNumber(pgNumber, forceRoman=True)
    else:
        retVal = PageNumber(pgNumber)

    return retVal


#==================================================================================================
# Main Routines
#==================================================================================================

if __name__ == "__main__":

    import sys

    import doctest
    doctest.testmod()
    print ("OpasDocument Tests Completed")
    sys.exit()


