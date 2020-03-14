# -*- coding: UTF-8 -*-

"""
A collection of routines for manipulating numbers.

Includes a Roman number class (new, 2009-07-17) which allows roman numbers and arabic numbers to be treated equally.

"""

import string, sys, re
# import arabicToRoman
import opasStringSupport
import logging
logger = logging.getLogger(__name__)

reverseStr = lambda s: ''.join([s[i] for i in range(len(s)-1, -1, -1)])	# from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/119029

roman = "(?P<romannum>m*(cm|dc{0,3}|cd|c{0,3})(xc|lx{0,3}|xl|x{0,3})(ix|vi{0,3}|iv|i{0,3}))"
binder = "(?P<binder>(?P<binderprefix>0)(?P<binderletters>[a-z]+))"
romanc = re.compile(roman, re.IGNORECASE)
binderc = re.compile(binder)
romanPgRg = "(%s(\-%s)?)" % (roman, roman)
decPgRg = "(%s(\-%s)?)" % ("\d+", "\d+")
decOrRomanPgRg = "(%s|%s)" % (decPgRg, romanPgRg)

gDbg1 = 0	# details

def roman_to_decimal(the_str: str) -> int:
    """
    Roman to Decimal from GeeksforGeeks
    
    >>> roman_to_decimal("MCMIV")
    1904
    
    >>> roman_to_decimal("vii")
    7

    >>> roman_to_decimal("42")
    42

    """
    def roman_letter_value(r):
        r = r.upper()
        
        if (r == 'I'): 
            return 1
        if (r == 'V'): 
            return 5
        if (r == 'X'): 
            return 10
        if (r == 'L'): 
            return 50
        if (r == 'C'): 
            return 100
        if (r == 'D'): 
            return 500
        if (r == 'M'): 
            return 1000
        return -1

    ret_val = 0
    i = 0
    try:
        ret_val = int(the_str)
    except ValueError as e:
        # must be roman, continue
        convert = True
    else:
        convert = False
         
    if convert:
        while (i < len(the_str)): 
      
            # Getting value of symbol s[i] 
            s1 = roman_letter_value(the_str[i]) 
      
            if (i+1 < len(the_str)): 
      
                # Getting value of symbol s[i+1] 
                s2 = roman_letter_value(the_str[i+1]) 
      
                # Comparing both values 
                if (s1 >= s2): 
      
                    # Value of current symbol is greater 
                    # or equal to the next symbol 
                    ret_val = ret_val + s1 
                    i = i + 1
                else: 
      
                    # Value of current symbol is greater 
                    # or equal to the next symbol 
                    ret_val = ret_val + s2 - s1 
                    i = i + 2
            else: 
                ret_val = ret_val + s1 
                i = i + 1
  
    return ret_val
    
def decimal_to_roman(the_int: int):
    """
    Convert arabic numbers to roman
    
    Translated from a public domain C routine by Jim Walsh in the
    Snippets collection.
    
    >>> print(decimal_to_roman(5000))
    MMMMM
    >>> print(decimal_to_roman(6000))
    MMMMMM
    >>> print(decimal_to_roman(9000))
    MMMMMMMMM
    >>> print(decimal_to_roman(6999))    
    MMMMMMCMXCIX
    """
    roman = ""
    n, the_int = divmod(the_int, 1000)
    roman = "M"*n
    if the_int >= 900:
        roman = roman + "CM"
        the_int = the_int - 900
    while the_int >= 500:
        roman = roman + "D"
        the_int = the_int - 500
    if the_int >= 400:
        roman = roman + "CD"
        the_int = the_int - 400
    while the_int >= 100:
        roman = roman + "C"
        the_int = the_int - 100
    if the_int >= 90:
        roman = roman + "XC"
        the_int = the_int - 90
    while the_int >= 50:
        roman = roman + "L"
        the_int = the_int - 50
    if the_int >= 40:
        roman = roman + "XL"
        the_int = the_int - 40
    while the_int >= 10:
        roman = roman + "X"
        the_int = the_int - 10
    if the_int >= 9:
        roman = roman + "IX"
        the_int = the_int - 9
    while the_int >= 5:
        roman = roman + "V"
        the_int = the_int - 5
    if the_int >= 4:
        roman = roman + "IV"
        the_int = the_int - 4
    while the_int > 0:
        roman = roman + "I"
        the_int = the_int - 1
    return roman

#----------------------------------------------------------------------------------------
def stdDev(listNums):
    """
    Calculate the standard deviation from a list of numbers.

    >>> stdDev((1, 2, 3))
    {'sumsquares': 14, 'squaredsums': 12.0, 'ssdiff': 2.0, 'variance': 1.0, 'stddev': 1.0}

    """
    sdev=None
    retVal = {}

    ss = 0
    total = 0
    n = len(listNums)
    for num in listNums:
        ss += num**2
        total += num

    if n>0:
        retVal["sumsquares"] = ss
        sqsums = (total**2)/n
        retVal["squaredsums"] = sqsums
        ssdiff = float(ss - sqsums)
        retVal["ssdiff"] = ssdiff
        var = float(ssdiff/(n-1))
        retVal["variance"] = var
        sdev = var**.5
        retVal["stddev"] = sdev

    return retVal

#----------------------------------------------------------------------------------------
def atoi(strVal):
    """
    Convert ascii to integer.

    Return integer value also decoding potential base indicators
    Whereas string.atoi requires that you supply the base, this one
    knows how to decode ASCII strings with hex or roman numbers!

    >>> print (atoi("0x22"))
    34
    >>> print (atoi("034"))
    34
    >>> print (atoi("x22"))
    34
    >>> print (atoi("VII"))
    7

    """

    retVal = 0
    if len(strVal) > 0:
        try:
            strVal = strVal.strip()
            if isRoman(strVal):
                retVal = convert_string_to_arabic(strVal)
            elif strVal[0] == "x":
                retVal = int(strVal[1:], base=16)
            elif strVal[:2] == "0x":
                retVal = int(strVal[2:], base=16)
            else:
                if isInt(strVal):
                    retVal = int(strVal)
        except Exception as e:
            raise ValueError("Error %s in numeric entity: %s" % (e, strVal))

    return retVal

#----------------------------------------------------------------------------------------
def isInt( str ):
    """
    Is the given string an integer?

    >>> isInt("22")
    True
    >>> isInt("ABD")
    False
    >>> isInt("IV")
    False

    """

    retVal = True
    try:
        num = int(str)
    except ValueError:
        retVal = False
    return retVal

#----------------------------------------------------------------------------------------
def isAllDigits( arg_str ):
    """ Is the given string composed entirely of digits?  (convenience function for python isdigit)"""
    return arg_str.isdigit()

#----------------------------------------------------------------------------------------
def isNumeric(arg_str: str):
    """ Is the string all numeric? (convenience function for python isdigit)"""
    return arg_str.isdigit()

#----------------------------------------------------------------------------------------
def trimNonDigits( arg_str: str):
    """
    Trim off any leading or trailing non-digits.

    >>> trimNonDigits("ABC123E")
    '123'
    """
    return arg_str.strip(string.ascii_letters)

#----------------------------------------------------------------------------------------
def trimLeadingNonDigits( arg_str ):
    """
    Remove leading characters that aren't digits

    >>> trimLeadingNonDigits("ABC123EFG")
    '123EFG'

    """
    return arg_str.lstrip(string.ascii_letters)

#----------------------------------------------------------------------------------------
def trimTrailingNonDigits( arg_str ):
    """
    Remove Trailing characters that aren't digits

    >>> trimTrailingNonDigits("ABC123EFG")
    'ABC123'

    """
    return arg_str.rstrip(string.ascii_letters)

#----------------------------------------------------------------------------------------
def isNumericList( str ):
    """
    Is the given string or list composed entirely of digits?

    >>> isNumericList("1,2,3,4,5")
    True
    >>> isNumericList("1, 2,  3, 4, 5")
    True
    >>> isNumericList("1")
    True
    >>> isNumericList("A")
    False

    """
    match = string.digits
    retVal = True
    list = re.split("\s*,\s*|\s*;\s*", str)
    #print list
    for nStr in list:
        if not isAllDigits(nStr):
            retVal = False
            break

    return retVal

#----------------------------------------------------------------------------------------
def isAlpha( str ):
    """
    Is the given string composed entirely of letters?

    >>> isAlpha("ABC")
    True
    >>> isAlpha("AB1C")
    False
    >>> isAlpha("123")
    False

    """
    match = string.ascii_letters
    retVal = True
    for letter in str:
        if letter not in match:
            retVal = False
            break
    return retVal

#----------------------------------------------------------------------------------------
def isBinder(numStr):
    """
    Perhaps this is defunct....
    """
    retVal = False
    if type(numStr) == type("str"):
        m = binderc.match(numStr)
        if m is not None:
            retVal = True

    return retVal

#----------------------------------------------------------------------------------------
def isRoman(numStr):
    """
    Return True if the string is a roman number

    >>> print (isRoman("VII"))
    True
    >>> print (isRoman("XIV"))
    True
    >>> print (isRoman("IVIX"))
    True
    >>> print (isRoman("MASSERMAN"))
    False
    >>> print (isRoman(u"iv"))
    True


    """
    #if isinstance(numStr, unicode):  # supports string and unicode Was if type(numStr) == type(u"test"):
        #numStr = sciUnicode.convertUnicodeStrToASCII(numStr)

    if isinstance(numStr, str):  # supports string and unicode Was if type(numStr) == type(""):
        testNum = numStr.strip()
        try:
            conv_roman_to_arabic(testNum)
            retVal = True
        except:
            retVal = False
    else:
        retVal = False

    return retVal

#----------------------------------------------------------------------------------------
def convert_string_to_arabic(numStr, stripChars=0):
    """
    Convert a string to an arabic number;

    Always returns numeric!
    12-09-2004: Changed default stripChars to 0, because otherwise a roman I was
    			stripped before processing!  Need to watch for programs that need
    			to now explicitly set stripChars to 1


    >>> convertStringToArabic("IV")
    4
    >>> convertStringToArabic("123")
    123
    >>> convertStringToArabic("MC")
    1100
    >>> convertStringToArabic("123IV567")
    0

    """
    num = 0

    if type(numStr) == type(1):
        num = numStr			# already numeric, arabic
    elif isinstance(numStr, str):
        numStr = opasStringSupport.trim_punct_and_spaces(numStr)
        if stripChars:
            numStr = trimNonDigits(numStr)

        if numStr != "":
            if isRoman(numStr):
                num = conv_roman_to_arabic(numStr)
            else:
                try:
                    num = int(numStr)
                except:
                    # get rid of leading and trailing 0s
                    romanWithArabicScrap = "(0*" + roman + "0*)"
                    m = re.match(romanWithArabicScrap, numStr)
                    if m is not None:
                        romannum = m.group("romannum")
                        if romannum is not None:
                            num = conv_roman_to_arabic(romannum)
                        else:
                            raise ValueError("convertStringToArabic Conversion error")

        else:
            # try not causing an exception on this.  If there's no numeric, then return None.
            if gDbg1: print ("Empty String.  convertStringToArabic Conversion error")
    else:
        try:
            num = int(numStr)
        except Exception as e:
            raise ValueError(e)

    if num is None:
        num = 0
        raise ValueError("Cannot convert: %s" % numStr)

    return num

#----------------------------------------------------------------------------------------
def convArabicToOrdLetter(arabicNum, lowerCase=0):
    """
    Convert the number to the corresponding letter, indexing the alphabet where A is 1
    If lowerCase == 1 then the base letter corresponding to 1 is "a" (lower case alpha)
    """
    if arabicNum > 26:
        raise ValueError("Overflow")
    if lowerCase ==1:
        baseNum = ord("a")-1
    else:
        baseNum = ord("A")-1
    return chr(arabicNum + baseNum)


#----------------------------------------------------------------------------------------
def arabic_to_roman(arabicNum, lCase=0):
    """
    Convet an arabic number to roman number format.

    >>> print (arabic_to_roman(9))
    IX
    >>> print (arabic_to_roman(400))
    CD
    >>> print (arabic_to_roman(1400))
    MCD
    >>> print (arabic_to_roman(3400))
    MMMCD
    >>> print (arabic_to_roman(9400))
    MMMMMMMMMCD
    >>> print (arabic_to_roman(19400))
    MMMMMMMMMMMMMMMMMMMCD
    >>> print (arabic_to_roman(1999))
    MCMXCIX
    >>> print (arabic_to_roman("1999"))
    MCMXCIX

    """
    try:
        arabicNum = int(arabicNum)
    except:
        try:
            arabicNum = convert_string_to_arabic(arabicNum)
        except TypeError as e:
            raise TypeError(e)
        except Exception as e:
            raise

    if arabicNum > 4999:   #was 4999, maybe wrong now?
        # use routine from the web--XXX Later, perhaps adapt this as THE routine?
        return decimal_to_roman(arabicNum)
        #print "Overflow: %s" % arabicNum
        #return `arabicNum`
        #raise "Overflow"

    arabicStr = repr(arabicNum)
    deg = len(arabicStr)
    arabicStrList = list(arabicStr)
    allStr = ""
    for a in arabicStrList:
        deg = deg - 1
        digiVal = int(a)

        if deg == 0:
            incr = "I"
            mid = "V"
            endp = "X"
        elif deg == 1:
            incr = "X"
            mid = "L"
            endp = "C"
        elif deg == 2:
            incr = "C"
            mid = "D"
            endp = "M"
        elif deg == 3:
            incr = "M"
            mid = "D"
            endp = "M"

        if digiVal < 4:
            digiStr = digiVal*incr
        elif digiVal == 4:
            digiStr = incr + mid
        elif digiVal == 5:
            digiStr = mid
        elif digiVal > 5 and digiVal < 9:
            digiStr = mid + (digiVal-5)*incr
        elif digiVal == 9:
            digiStr = incr + endp

        allStr += digiStr

    if lCase == 1:
        allStr = allStr.lower()

    return allStr

#----------------------------------------------------------------------------------------
def conv_roman_to_arabic(romnumStr):
    r"""
    convert arg to arabic number

    >>> print (convRomanToArabic("IVIX"))
    3
    >>> print (convRomanToArabic("ivix"))
    3
    >>> print (convRomanToArabic("ix"))
    9
    >>> convRomanToArabic("xcvii")
    97
    >>> convRomanToArabic("25")	#doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
      File "C:\Users\nrsha\AppData\Local\Programs\Python\Python37\lib\doctest.py", line 1329, in __run
        compileflags, 1), test.globs)
      File "<doctest __main__.convRomanToArabic[4]>", line 1, in <module>
        convRomanToArabic("25") #doctest: +IGNORE_EXCEPTION_DETAIL
      File "e:\usr3\GitHub\openpubarchive\app\libs\opasMath.py", line 564, in convRomanToArabic
        raise ValueError("Bad Roman Number: %s" % romnumStr)
    ValueError: Bad Roman Number: 25
    
    """

    #if isNumeric(romnumStr):
    #	return int(romnumStr)

    romnumStr = romnumStr.strip().upper()
    revromnumStr = list(romnumStr)
    revromnumStr.reverse()

    lastVal = None
    cumList = [0]
    val = 0
    for a in list(revromnumStr):
        if a == "I":
            val= 1
        elif a == "V":
            val= 5
        elif a == "X":
            val= 10
        elif a == "L":
            val= 50
        elif a == "C":
            val= 100
        elif a == "D":
            val= 500
        elif a == "M":
            val= 1000
        else:
            raise ValueError("Bad Roman Number: %s" % romnumStr)

        if cumList[-1] > val:
            cumList[-1] = cumList[-1] - val
        else:
            cumList.append(val)
    aval = 0
    for num in cumList:
        aval = aval + num
    return aval


#==================================================================================================
# Number Class, handles romans too.
#==================================================================================================

class Number:
    """
    A class to implement Roman and Arabic numbers transparently

    You can then treat them like any other number.
    The Roman and arabic versions are kept throughout all operations.
    Number = self.data
    Arabic = self.dataArabic

    >>> x = Number(1999)
    >>> y = Number(2000)
    >>> x.roman()
    'MCMXCIX'
    >>> x > y
    False
    >>> y > x
    True
    >>> z = Number("IV")
    >>> z
    IV
    >>> int(z)
    4
    >>> z.dump()
    Roman: IV
    Arabic: 4
    >>> x = Number(5)
    >>> y = Number(4)
    >>> z = Number(2)
    >>> x+y
    9
    >>> print (x-y)
    1
    >>> print (x*y)
    20
    >>> print (y/z)
    2.0

    """
    #--------------------------------------------------------------------------------
    def __init__(self, val):
        self.dataArabic = None
        self.dataRoman = None
        self.isRoman = False

        if isinstance(val, Number):
            self.dataRoman = val.dataRoman
            self.dataArabic = val.dataArabic
            self.isRoman = val.isRoman
        elif isRoman(val):
            self.dataRoman = val
            self.dataArabic = conv_roman_to_arabic(val)
            self.isRoman = True
        elif isInt(val):
            self.dataRoman = arabic_to_roman(val)
            self.dataArabic = val
            self.isRoman = False
        else:
            raise ValueError()

    #--------------------------------------------------------------------------------
    def __repr__(self):
        retVal = self.__str__()
        return retVal

    #--------------------------------------------------------------------------------
    def __str__(self):
        if self.isRoman:
            retVal = self.dataRoman
        else:
            retVal = repr(self.dataArabic)
        return retVal

    #--------------------------------------------------------------------------------
    def roman(self):
        retVal = self.dataRoman
        return retVal

    #--------------------------------------------------------------------------------
    def arabic(self):
        retVal = self.dataArabic
        return retVal

    #--------------------------------------------------------------------------------
    def dump(self):
        print(f"Roman: {self.dataRoman}") 
        print(f"Arabic: {self.dataArabic}")

    #--------------------------------------------------------------------------------
    def __add__(self, val2):
        """
        Add val2 to current number
        """
        val2r = Number(val2)
        return self.dataArabic + val2r.dataArabic

    #--------------------------------------------------------------------------------
    def __sub__(self, val2):
        """
        Add val2 to current number
        """
        val2r = Number(val2)
        return self.dataArabic - val2r.dataArabic

    #--------------------------------------------------------------------------------
    def __mul__(self, val2):
        """
        Multiply val2 and current number
        """
        val2r = Number(val2)
        return self.dataArabic * val2r.dataArabic

    #--------------------------------------------------------------------------------
    def __truediv__(self, val2):
        """
        Multiply val2 and current number
        """
        val2r = Number(val2)
        return self.dataArabic / val2r.dataArabic

    #--------------------------------------------------------------------------------
    def __eq__(self, other):
        """
        Assess equality of two objects.
        """

        if not isinstance(other, Number):
            other = Number(other)

        retVal = (0 == other)

        return retVal

    #--------------------------------------------------------------------------------
    def __int__(self):
        return self.dataArabic

    #--------------------------------------------------------------------------------
    def __len__(self):
        return len(self.__str__())

    ##--------------------------------------------------------------------------------
    #def __long__(self):
        #return long(self.dataArabic)

    #--------------------------------------------------------------------------------
    def __eq__(self, other):
        if not isinstance(other, Number):
            v2 = Number(other)
            v2 = v2.arabic()
        else:
            v2 = other.arabic()
    
        if not isinstance(self, Number):
            v1 = Number(self)
            v1 = v1.arabic()
        else:
            v1 = self.arabic()

        return v1 == v2

    def __ne__(self, other):
        if not isinstance(other, Number):
            v2 = Number(other)
            v2 = v2.arabic()
        else:
            v2 = other.arabic()
    
        if not isinstance(self, Number):
            v1 = Number(self)
            v1 = v1.arabic()
        else:
            v1 = self.arabic()

        return v1 != v2

    def __lt__(self, other):
        if not isinstance(other, Number):
            v2 = Number(other)
            v2 = v2.arabic()
        else:
            v2 = other.arabic()
    
        if not isinstance(self, Number):
            v1 = Number(self)
            v1 = v1.arabic()
        else:
            v1 = self.arabic()

        return v1 < v2

    def __le__(self, other):
        if not isinstance(other, Number):
            v2 = Number(other)
            v2 = v2.arabic()
        else:
            v2 = other.arabic()
    
        if not isinstance(self, Number):
            v1 = Number(self)
            v1 = v1.arabic()
        else:
            v1 = self.arabic()

        return v1 <= v2

    def __gt__(self, other):
        if not isinstance(other, Number):
            v2 = Number(other)
            v2 = v2.arabic()
        else:
            v2 = other.arabic()
    
        if not isinstance(self, Number):
            v1 = Number(self)
            v1 = v1.arabic()
        else:
            v1 = self.arabic()

        return v1 > v2

    def __ge__(self, other):
        if not isinstance(other, Number):
            v2 = Number(other)
            v2 = v2.arabic()
        else:
            v2 = other.arabic()
    
        if not isinstance(self, Number):
            v1 = Number(self)
            v1 = v1.arabic()
        else:
            v1 = self.arabic()

        return (self >= other)

#==================================================================================================
# Main Routines
#==================================================================================================

if __name__ == "__main__":

    import sys

    import doctest
    doctest.testmod()
    print ("Done with tests")
    sys.exit()


