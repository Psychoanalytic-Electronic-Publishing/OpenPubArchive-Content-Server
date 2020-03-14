# -*- coding: UTF-8 -*-


from __future__ import absolute_import
from __future__ import print_function
import string
import os
import sys
import re
import six
from six.moves import range

import logging
logger = logging.getLogger(__name__)

gdbg1 = False
gReuseConnections = 1

#rgxMixedCase = re.compile("([A-Z]+.*?[a-z])|([a-z]+.*?[A-Z])")
rgxNumStrSplit = re.compile("(?P<str1>[A-Z\-]*)(?P<num>[0-9]+)(?P<str2>[A-Z\-]*)", re.IGNORECASE)
rgxTrim = re.compile("^\s+(?P<cleanStr>.*?)\s+$")

# A dictionary of words not capitalized in titles, according to Chicago manual of style
wordsNotCapitalized = {
    "has" 	: 1,
    "was"	: 1,
    "a"		: 1,  # articles
    "an"	: 1,
    "the"	: 1,
    "and"	: 1,  # Coordinating conjunctions
    "but"	: 1,
    "for"	: 1,
    "or"	: 1,
    "to"	: 1,
    "of"	: 1,
    "into"	: 1,
    "thee"	: 1,
    "from"	: 1,
    "by"	: 1,
    "nor"	: 1
}

punctRegx = "[\s,\.;:\)\(\t\"\']+"
punctOrWhite = re.compile(punctRegx)

# Set up check of word exceptions for caller
wordExceptions = {}

class DocumentString(object):
    def __init__(self, doc_str:str=None):
        # A dictionary of words not capitalized in titles, according to Chicago manual of style
        self.doc_str = doc_str
        self.WordsNotCapitalized = {
            "has" 	: 1,
            "was"	: 1,
            "a"		: 1,  # articles
            "an"	: 1,
            "the"	: 1,
            "and"	: 1,  # Coordinating conjunctions
            "but"	: 1,
            "for"	: 1,
            "or"	: 1,
            "to"	: 1,
            "of"	: 1,
            "into"	: 1,
            "thee"	: 1,
            "from"	: 1,
            "by"	: 1,
            "nor"	: 1
        }

        # Set up check of word exceptions for caller
        self.WordExceptions = {}

        # print "Log File Opened:", self.OutputFilename

    def __del__(self):
        return

    # --------------------------------------------------------------------------------
    # Capitalize each word per title case rules
    def title_case(self, dictOfExceptions=None):
        """
        >>> tst = DocumentString("the rain in spain falls mainly on the plain")
        >>> tst.title_case()
        'The Rain In Spain Falls Mainly On the Plain'
        """
        def isRoman(the_str):
            m = re.match("^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", the_str)
            if m is not None:
                return True
            else:
                return False

        if dictOfExceptions is not None:
            if type(dictOfExceptions) == type({}):
                self.WordExceptions = dictOfExceptions

        # sep = ' '
        # return string.join(map(self.capitalizeTitleWord, string.split(s, sep)), sep or ' ')
        extendedWhitespace = string.whitespace + "{}()[]:/&!=\""
        res = ''
        i, n = 0, len(self.doc_str)
        count = 0
        while i < n:

            while i < n and self.doc_str[i] in extendedWhitespace:
                res = res + self.doc_str[i]
                i = i + 1
            if i == n:
                break  # no word, just white space

            j = i
            while j < n and self.doc_str[j] not in extendedWhitespace:
                j = j + 1

            count = count + 1
            sword = self.doc_str[i:j]

            if (len(sword) <= 2 and self.doc_str[j:j] == ".") or re.search(".+\..+", sword):
                # This is likely to be an abbreviation or initial(s)
                res = res + sword
            elif isRoman(sword):
                # This is likely to be an roman numbre
                res = res + sword
            else:
                res = res + self.capitalize_title_word(sword, count)
            i = j

        return res

    # --------------------------------------------------------------------------------
    # Capitalize each word per title case rules

    def capitalize_title_word(self, word_str, position=1):
        """
        >>> tst = DocumentString()
        >>> tst.capitalize_title_word("rest")
        'Rest'
        """
        w = word_str.lower()
        # look for word exceptions, but don't do it if this is the first word
        if position > 1:
            if len(w) < 4:
                # Only check if applicable, which means < 4
                if w in self.WordsNotCapitalized:
                    return w  # return lowercased word

            if w in self.WordExceptions or word_str in self.WordExceptions:
                return word_str		# return original word!

        # is this word a roman numeral?
        # To find out, ask if it "isn't" a roman numerals
        m = re.search("([^IXVLC]+)", word_str)
        if m is None:
            # could be roman numeral, so return orig
            return word_str		# return original word!

        # does this word have special characters?
        # To find out, ask if it "isn't" a roman numerals
        m = re.search("(([+$#0-9_%]+)|(.*\-$))", word_str)
        if m is not None:
            # special characters
            return word_str		# return original word!

        # Else
            # Return a copy of the string s with only its first character
            # capitalized.
        return word_str[:1].upper() + w[1:]

    # --------------------------------------------------------------------------------
    # Capitalize each word per title case rules

    def is_mixed_case(self):
        """
        >>> tst = DocumentString("the rain in spain falls mainly on the Plain")
        >>> tst.is_mixed_case()
        True
        >>> tst = DocumentString("the rain in spain falls mainly on the plain")
        >>> tst.is_mixed_case()
        False
        >>> tst = DocumentString("THE RAIN IN SPAIN FALLS MAINLY ON THE PLAIN")
        >>> tst.is_mixed_case()
        False
        """
        ret_val = False
        hasUpperCase = False
        hasLowerCase = False
        # count = 0
        for n in self.doc_str:
            if n.islower(): hasLowerCase = True
            if n.isupper(): hasUpperCase = True
            ret_val = hasLowerCase and hasUpperCase
            if ret_val:
                break

        return ret_val

    # --------------------------------------------------------------------------------
    # Remove Punctuation
    def remove_punctuation(self, punct="*+':;<=>?@\",.&#/()", butNot=""):
        "Removes punctuation, but not spaces, '-', or '_' which may be part of names"
        for chr in punct:
            if butNot == "" or not self.instr(1, butNot, str(chr)):
                self.doc_str = self.doc_str.replace(chr, "")

        return self.doc_str

# --------------------------------------------------------------------------------
# Remove Quotes
def remove_dbl_quotes(s):
    "Removes quotes (double only)"
    retStr = s.replace("\"", "")
    return retStr

# --------------------------------------------------------------------------------
# Remove Single Quotes
def remove_single_quotes(s):
    "Removes single quotes"
    retStr = s.replace("\'", "")
    return retStr

# --------------------------------------------------------------------------------
# Remove Extra Spaces between Words
def remove_extra_spaces(s):
    """
    removeExtraSpaces(word) 
    
    Removes extra spaces between words and lead and trail space
    """
    s = s.join(s.split(' '))
    return s

# --------------------------------------------------------------------------------
def is_mixed_case(s):
    """
    >>> is_mixed_case("the Rain in Spain")
    True
    >>> is_mixed_case("the rain in spain")
    False
    """
    #print "Here I am in isMixedCase with str: '%s'" % str
    if repr(s) != repr(s.upper()) and repr(s) != repr(s.lower()):
        retVal = True
    else:
        retVal = False

    return retVal

# --------------------------------------------------------------------------------
def title_case(str, dictOfExceptions=None):
    """
    Wrapper for DocumentString function to convert to title case.
    """
    s = DocumentString()
    retVal = s.title_case(str, dictOfExceptions)
    return retVal

# --------------------------------------------------------------------------------
def if_not_none_else(val, def_val):
    """
    If not none, return val, else return def_val
    >>> if_not_none_else("the", "else")
    'the'
    
    >>> if_not_none_else(None, "else")
    'else'
    """

    if val is not None:
        return val
    else:
        return def_val

# --------------------------------------------------------------------------------
def remove_letter_prefix_and_suffix(arg_str: str):
    """
    >>> remove_letter_prefix_and_suffix("23f")
    ('', '23', 'f')
    
    """
    ret_val_prefix = ""
    ret_val_base = arg_str
    ret_val_suffix = ""
    if isinstance(arg_str, six.string_types):
        m = rgxNumStrSplit.match(arg_str)
        if m is not None:
            ret_val_prefix = m.group("str1")
            ret_val_base = m.group("num")
            ret_val_suffix = m.group("str2")
            
    retVal = (ret_val_prefix, ret_val_base, ret_val_suffix)
    return retVal

# --------------------------------------------------------------------------------
def atoiTrueFalse(strArg):
    retVal = 0
    if type(strArg) == type(0):
        retVal = strArg
    else:
        if not isEmpty(strArg):
            if type(strArg) == type(""):
                strChr = strArg[0].lower()
                if strChr == '1' or strChr == 't':
                    retVal = 1

    return retVal

# --------------------------------------------------------------------------------
def atoiYear(strArg):
    if isEmpty(strArg):
        retVal = 0
    else:
        if isinstance(strArg, six.string_types):  # supports string and unicode Was if type(strArg) == type(""):
            str = trim_punct_and_spaces(strArg)
            if len(str) > 4:
                m = re.match("[^0-9]*?(?P<year>[1-2][0-9]{3,3})[^0-9]*?", str)
                if m is not None:
                    retVal = m.group("year")
                else:
                    retVal = 0
            else:
                retVal = str

            try:
                retVal = int(retVal)
            except Exception as e:
                print (f"Error: {e}")
                retVal = 0
        else:
            retVal = strArg

    return retVal

# --------------------------------------------------------------------------------
def atoiNotEmpty(strArg):
    retVal = 0

    if type(strArg) == type(1):
        # already a number
        retVal = strArg
    else:
        try:
            retVal = int(strArg)
        except:
            dummy1, numArg, dummy2 = remove_letter_prefix_and_suffix(strArg)
            try:
                retVal = int(numArg)
            except:
                #log_error("Bad value for atoi '%s'" % strArg, displayAlso=1)
                retVal = 0

    return retVal
# --------------------------------------------------------------------------------
def not_empty(localArg, default=None):
    """
    Return default if empty (none, "", [], ())
    Otherwise return localArg
    """
    if localArg is None or localArg == "" or localArg == [] or localArg == ():
        retVal = default
    else:
        retVal = localArg

    return retVal

# ---------------------------------------------------------------------------------------------
def depluralize(term):
    """
    	Remove any pluralization
    	Simple approach now.
    """
    #print "Ending: ", term[-3:]
    if term[-3:] == "ies":
        retVal = term[:-3] + "y"
    elif term[-1] == "s":
        retVal = term[:-1]
    else:
        retVal = None

    return retVal

def is_empty_or_zero(theVal):
    """
    This function is used to see if a return value is empty nor zero
    If theVal is none, or an empty list, or 0, it returns True.
    """
    if isEmpty(theVal) or theVal == 0:
        return 1
    else:
        return 0

# ----------------------------------------------------------------------------------------


def isPunctOrWhitespace(inputStr, punctSet=[',', '.', ' ', ':', ';', ')', '\t', '"', "'"]):
    """
    This function is used to see if a string consists only of punctuation or whitespace.

    	>>> isPunctOrWhitespace("555")
    	False
    	>>> isPunctOrWhitespace("     ")
    	True
    	>>> isPunctOrWhitespace("    \t   \\n ")
    	True
    	>>> isPunctOrWhitespace("  ,; s \t   \\n ")
    	True
    	>>> isPunctOrWhitespace("A ,; s \t   \\n ")
    	False
    """

    retVal = False
    m = punctOrWhite.match(inputStr)
    if m is not None:
        retVal = True

    return retVal

# --------------------------------------------------------------------------------


def isWhitespace(theVal):
    """
    This function is used to see if a string consists only of whitespace.

    	>>> isWhitespace("555")
    	False
    	>>> isWhitespace("     ")
    	True
    	>>> isWhitespace("    \t   \\n ")
    	True
    	>>> isWhitespace("   s \t   \\n ")
    	False

    """
    retVal = True
    mStr = "[ \n\t]*\Z"
    m = re.match(mStr, theVal)
    if m is not None:
        # all whitespace
        retVal = True
    else:
        retVal = False

    return retVal
# --------------------------------------------------------------------------------
def isEmpty(theVal):
    """
    This function is used to see if a return value, which may be a
    	list or a value, is non-empty (and not none)
    	Check if theVal is a list; if it is, does it
    	have any nonempty (none) members?  If so return False
    If theVal is none, or an empty list, it also returns false.

        >>> a = None
        >>> isEmpty(a)
        True
        >>> isEmpty([])
        True
        >>> isEmpty([None])
        False
        >>> isEmpty(["A", "B"])
        False
        >>> isEmpty(())
        True
        >>> isEmpty(("A", "B"))
        False



    """
    retVal = True
    #print "Type: ", type(theVal), theVal

    if theVal is None:
        retVal = True

    elif not isinstance(theVal, (list, tuple, six.string_types)):  # unicode and general cleanup WAS type(theVal) not in [type([]), type(""), type({})]:
        retVal = False

    elif len(theVal) != 0:  # if the list or tuple is empty, the length is 0, so true.  TBD...should we see if any members are not none?
        retVal = False

    return retVal

# --------------------------------------------------------------------------------
def isEmptyOrNoneStr(theVal):
    """
    Same as isEmpty, but also considers the string "None" empty (case sensitve)
    This covers databases, where None has been stored from the python actions.

    If theVal is None, "None", the list is empty, or all items in the list are empty, it returns True.
    """
    retVal = True
    if type(theVal) == type([]):
        for val in theVal:
            if val is not None and val != [] and val != "None":
                retVal = False
        # note that if the list is empty, it returns true.
    elif not (theVal is None or theVal == "" or theVal == "None"):
        retVal = False

    return retVal

# ----------------------------------------------------------------------------------------


def doEscapes(data, hasEscapes=0):
    retVal = data
    if retVal is not None:
        if hasEscapes == 0:
            if re.search(r'\\', retVal) is not None:
                retVal = re.sub(r'\\', r'\\\\', retVal)
        if re.search(r'"', retVal) is not None:
            retVal = re.sub(r'(?P<pre>([^\\]|\A))"', r'\1\\"', retVal)
        # if doubled, take care of second one here, and first in next set
        # This extra effort has to be done because you have to watch for
        # already-escaped slashes!
        if re.search(r"''", retVal) is not None:
            retVal = re.sub(r"''", r"'\\'", retVal)
        if re.search(r"'", retVal) is not None:
            retVal = re.sub(r"(?P<pre>([^\\]|\A))'", r"\1\\'", retVal)
    return retVal

# ----------------------------------------------------------------------------------------


def doQuoteEscapes(data, hasEscapes=0):
    retVal = data
    if retVal is not None:
        if re.search(r'"', retVal) is not None:
            retVal = re.sub(r'(?P<pre>([^\\]|\A))"', r'\1\\"', retVal)
        if re.search(r"''", retVal) is not None:
            retVal = re.sub(r"''", r"'\\'", retVal)
        if re.search(r"'", retVal) is not None:
            retVal = re.sub(r"(?P<pre>([^\\]|\A))'", r"\1\\'", retVal)
    return retVal

# ----------------------------------------------------------------------------------------


def doBackSlashEscapes(data):
    clen = len(data)
    retVal = ""
    for n in range(0, clen):
        if data[n] == "\\":
            if n < clen - 1:
                if data[n + 1] != "\\":
                    # make sure	prev was not "\"
                    if n > 0:
                        if data[n - 1] != "\\":
                            retVal += "\\\\"
                        else:
                            retVal += data[n]
                    else:
                        retVal += "\\\\"
                else:
                    retVal += data[n]
            else:
                retVal += data[n]
        else:
            retVal += data[n]

    return retVal

# ----------------------------------------------------------------------------------------


def doRegExpEscapes(data):
    """
    Escape periods and other regular expression chars in data
    """
    #retVal = string.replace(data, ".", "\.")
    #retVal = string.replace(retVal, "(", "\(")
    #retVal = string.replace(retVal, ")", "\)")
    if data is not None:
        retVal = re.escape(data)
    else:
        retVal = ""

    return retVal

# ----------------------------------------------------------------------------------------


def doEscapesForList(dataList):
    retVal = dataList
    if retVal is not None:
        retValNew = []
        for retValItem in retVal:
            retValItem = doEscapes(retValItem)
            retValNew.append(retValItem)
        retVal = retValNew
    return retVal


# ----------------------------------------------------------------------------------------
def sortFile(fileName, elimDups=0):
    print("Sorting %s" % fileName)
    try:
        f = open(fileName, "r")
    except:
        print("%s: %s" % sys.exc_info()[:2])
        print(log_error("Cannot	open %s" % fileName))
        raise

    try:
        lines = f.readlines()
        lines.sort()
        f.close()
    except:
        print("%s: %s" % sys.exc_info()[:2])
        print(log_error("Error reading file	%s" % fileName))
        raise

    try:
        os.remove(fileName + ".bak")
        os.rename(fileName, fileName + ".bak")
    except:
        pass

    try:
        o = open(fileName, "w")
    except:
        print("%s: %s" % sys.exc_info()[:2])
        print(log_error("Error opening file	for	output"))
        raise

    else:
        if elimDups:
            # print	"Writing File"
            lastLine = ""
            count = 0
            for line in lines:
                # print	line
                if len(line) > 0:
                    # write	except for dups!
                    if lastLine != line:
                        count += 1
                        o.write(line)
                        lastLine = line
                    else:
                        print("Omitting: ", line)
                else:
                    print("Blank Line")
        else:
            o.writelines(lines)
            count = len(lines)

        print(count, "lines	written	out	of", len(lines))
        o.close()

# ----------------------------------------------------------------------------------------
def removeTrailingPunctAndSpaces(inputStr, punctSet=[',', '.', ' ', ':', ';', ')', '\t', '"', "'"]):
    # Beginning in Python 2.2.3 you can do this
    #retVal = inputStr.rstrip(",.\t ")
    retVal = ""
    if not isEmpty(inputStr):
        retVal = inputStr.rstrip()
        if retVal is not None and len(retVal) > 0:
            while retVal[-1] in punctSet:
                retVal = retVal[:-1]
                retVal = retVal.rstrip()

    return retVal

# ----------------------------------------------------------------------------------------
def removeLeadingPunctAndSpaces(inputStr, punctSet=[',', '.', ' ', ':', ';', '(', '\t', '"', "'"]):
    # Beginning in Python 2.2.3 you can do this
    #retVal = string.rstrip(inputStr, ",.\t ")
    retVal = ""
    if not isEmpty(inputStr):
        retVal = inputStr.lstrip()
        if retVal is not None and len(retVal) > 0:
            while retVal[0:1] in punctSet:
                retVal = retVal[1:]
                retVal = retVal.lstrip()

    return retVal

# ----------------------------------------------------------------------------------------
def removeAllPunct(inputStr, punctSet=[',', '.', ':', ';', '(', ')', '\t', '"', "'"]):
    # Beginning in Python 2.2.3 you can do this
    #retVal = string.rstrip(inputStr, ",.\t ")
    retVal = ""
    if not isEmpty(inputStr):
        for n in inputStr:
            if n not in punctSet:
                retVal = retVal + n

    return retVal

# --------------------------------------------------------------------------------
# Remove Extra Spaces between Words
def remove_extra_spaces(self, s):
    """
    removeExtraSpaces(word)
    Removes extra spaces between words and lead and trail space
    """
    s = "".join(s.split())
    return s
# ----------------------------------------------------------------------------------------

def trim_punct_and_spaces(inputStr, punctSet=[',', '.', ' ', ':', ';', ')', '(', '\t', '"', "'"]):
    retVal = removeLeadingPunctAndSpaces(inputStr, punctSet)
    retVal = removeTrailingPunctAndSpaces(retVal, punctSet)
    return retVal

# ----------------------------------------------------------------------------------------
def trim(inputStr):
    """
    Trim white space from beginning and end (including CRs, etc.
    """
    m = rgxTrim.match(inputStr)
    if m is not None:
        retVal = m.group("cleanStr")
    else:
        retVal = inputStr
    return retVal

# --------------------------------------------------------------------------------
def printTopReferenceCounts(maxCount=100):
    """
    Locate Memory Leaks by looking at reference counts
    """
    pass
    for n, c in get_refcounts()[:maxCount]:
        print('%10d %s' % (n, c.__name__))

# --------------------------------------------------------------------------------
def get_refcounts():
    """
    Locate Memory Leaks by looking at reference counts
    """
    d = {}
    sys.modules
    # collect all classes
    for m in sys.modules.values():
        for sym in dir(m):
            o = getattr(m, sym)
            if type(o) is type:
                d[o] = sys.getrefcount(o)
    # sort by refcount
    pairs = [(x[1], x[0]) for x in list(d.items())]
    pairs.sort()
    pairs.reverse()
    return pairs

def log_error(actionStr, errorType=None, logStrTuple=None, displayAlso=0):

    HLError = HLErrorLog()
    return HLError.log(actionStr, errorType=errorType, logStrTuple=logStrTuple, displayAlso=displayAlso)


# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------------------------------------
def setLogFile(logFileName, versioning=True):
    from . import sciFilePath
    # open the log file, unless profile specifies screen
    if not logFileName in ['stderr', 'syserr', 'screen', 'display', 'stdout']:
        # if a log file name is given use it, no versioning
        if logFileName is not None:
            dirName = os.path.dirname(logFileName)
            fileName = os.path.basename(logFileName)
            basename, ext = os.path.splitext(fileName)
            if ext is None:
                ext = ".log"

            if versioning:
                logFileVerInfo = sciFilePath.fileNameVerSys(logFileName)
                logFileVerInfo.extension = ".log"
                logFileVerInfo.basename = logFileVerInfo.basename
                logFileName = logFileVerInfo.nextVersion()

        if logFileName is not None:
            sys.stderr = open(logFileName, "w")
        else:
            sys.stderr = sys.__stderr__
    else:
        sys.stderr = sys.__stderr__

# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# Capitalize each word per title case rules
# --------------------------------------------------------------------------------
def title_case(s, dictOfExceptions=None):

    from .opasMath import isRoman

    if dictOfExceptions is not None:
        if type(dictOfExceptions) == type({}):
            WordExceptions = dictOfExceptions

    sep = ' '
    # return string.join(map(capitalizeTitleWord, string.split(s, sep)), sep or ' ')
    extendedWhitespace = string.whitespace + "{}()[]:/&<>\""
    res = ''
    i, n = 0, len(s)
    count = 0
    while i < n:

        while i < n and s[i] in extendedWhitespace:
            res = res + s[i]
            i = i + 1
        if i == n:
            break  # no word, just white space

        j = i
        while j < n and s[j] not in extendedWhitespace:
            j = j + 1

        count = count + 1
        sword = s[i:j]

        #print "Check Word, following char: ", sword, s[j:j]
        if (len(sword) <= 2 and s[j:j] == ".") or re.search(".+\..+", sword):
            # This is likely to be an abbreviation or initial(s)
            res = res + sword
        elif isRoman(sword):
            # This is likely to be an roman numbre
            res = res + sword
        else:
            res = res + capitalizeTitleWord(sword, count)
        i = j

    # print res
    return res


# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# Capitalize each word per title case rules
# --------------------------------------------------------------------------------
def capitalizeTitleWord(s, position=None):
    #print "word: ",s
    w = s.lower()
    # look for word exceptions, but don't do it if this is the first word
    if position > 1:
        if len(w) < 4:
            # Only check if applicable, which means < 4
            if w in wordsNotCapitalized:
                # print "returning lower cased word ", w
                return w  # return lowercased word

        if w in wordExceptions or s in WordExceptions:
            #print "returning orig word ", s
            return s		# return original word!

    # is this word a roman numeral?
    # To find out, ask if it "isn't" a roman numerals
    m = re.search("([^IXVLC]+)", s)
    if m is None:
        # could be roman numeral, so return orig
        #print "roman numeral - returning orig word ", s
        return s		# return original word!

    # does this word have special characters?
    # To find out, ask if it "isn't" a roman numerals
    m = re.search("(([+$#0-9_%]+)|(.*\-$))", s)
    if m is not None:
        # special characters
        # print "Special Chars"
        return s		# return original word!

    # Else
        # Return a copy of the string s with only its first character
        # capitalized.
    return s[:1].upper() + w[1:]


# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# Capitalize each word per title case rules
# there's a better version of this above!
# --------------------------------------------------------------------------------
# def isMixedCase(s):
#	i, n = 0, len(s)
#	count = 0
#	while i < n:
#		isLowercase = string.find(string.lowercase, s[i])
#		isUppercase = string.find(string.uppercase, s[i])
#		if isLowercase and isUppercase: break
#	res = isLowerCase and isUpperCase
#	return res
#
# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# Instr
# --------------------------------------------------------------------------------
def instr(iStart, str1, str2):
    """
    Find instance of str2 in str1 and return starting index or 0 if none.
    """
    if iStart > 0:
        iStart = iStart - 1
    m = str1.find(str2, iStart)
    if m != -1:
        return m + 1
    else:
        return 0

# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# Remove an item from a list (doesn't change list)
# --------------------------------------------------------------------------------
def removeValuesFromList(the_list, val):
    return [value for value in the_list if value != val]

# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# Remove Punctuation
# --------------------------------------------------------------------------------
def removePunctuation(s, butNot=""):
    "Removes punctuation, but not spaces, '-', or '_' which may be part of names"
    retStr = s
    removeChars = "*+':;<=>?@\",.&#/()"
    for chr in removeChars:
        if butNot == "" or not instr(1, butNot, str(chr)):
            retStr = retStr.replace(chr, "")

    # print "Before: ", s, " After: ", retStr
    return retStr

# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# Remove Control Chars
# --------------------------------------------------------------------------------
def removeControlChars(s, butNot="", removeChars="\n"):
    """
    Removes special control characters such as line feeds

    	>>> testStr = '<GR:"Revised-					2010 					20 		"> '
    	>>> removeControlChars(testStr, removeChars="\t\g")
    	'<GR:"Revised-201020">'
    	>>> testStr = removeTabs(testStr)
    	>>> removeControlChars(testStr, removeChars="\g")
    	'<GR:"Revised-                                    2010                                    20              "> '
    """
    retStr = s
    for chr in removeChars:
        if butNot == "" or not instr(1, butNot, str(chr)):
            retStr = retStr.replace(chr, "")

    # print "Before: ", s, " After: ", retStr
    return retStr

# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# Remove Tabs
# --------------------------------------------------------------------------------
def removeTabs(s, tabLen=4):
    """
    Removes Tabs and spaces around it, changing to quotes (double only)

    >>> testStr = '<GR:"Revised-\t2010\t\t20"> '
    >>> removeTabs(testStr, tabLen=5)
    '<GR:"Revised-        2010            20"> '
    """
    spaces = tabLen * " "
    retStr = re.sub("\s*\t\s*", spaces, s)
    return retStr

# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# Remove Quotes
# --------------------------------------------------------------------------------
def removeDblQuotes(s):
    "Removes quotes (double only)"
    retStr = s.replace("\"", "")
    return retStr

# --------------------------------------------------------------------------------
# Remove Single Quotes
def removeSingleQuotes(s):
    "Removes single quotes"
    retStr = s.replace("\'", "")
    return retStr


# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# Remove Extra Spaces between Words
# --------------------------------------------------------------------------------
"""
removeExtraSpaces(word)

Removes extra spaces between words and lead and trail space
"""
def remove_extra_spaces(s):
    s = string.join(string.split(s))
    return s

# ==================================================================================================
# Main Routines
# ==================================================================================================


if __name__ == "__main__":
    """
	Run	Test Routines
	"""

    import sys
    import doctest
    doctest.testmod()
    print ("Done with tests.")
    sys.exit()

    selqry = r"""select task, comments from buildlog"""
    if 1:
        terms = ["daisies", "flowers", "zoo", "zoos", "doggies", "plazas", "pizzas", "men"]
        for n in terms:
            print(depluralize(n))

    if 1:
        # viewable only tests
        print(title_case("ELISABETH R. GELEERD"))
        print("'%s'" % trim(" \n\n    this is a test  \n\n  "))

    assert doEscapes("'these'") == r"\'these\'", doEscapes("'these'")
    assert doEscapes("\'these\'") == r"\'these\'"
    assert doEscapes("This or 'these'") == r"This or \'these\'"
    assert doEscapes("This ''or'' \'these\'") == r"This \'\'or\'\' \'these\'", doEscapes("This ''or'' \'these\'")
    a = ['item1', 'item 2', 'items 1 2 3']
    assert doEscapes(repr(a)) == r"[\'item1\', \'item 2\', \'items 1 2 3\']", doEscapes(repr(a))

    assert removeTrailingPunctAndSpaces(" these ") == " these"
    assert removeTrailingPunctAndSpaces(" these ,") == " these"
    assert removeTrailingPunctAndSpaces(" these ,)") == " these"
    assert removeLeadingPunctAndSpaces(" these ") == "these "
    assert removeLeadingPunctAndSpaces(" (these ") == "these "
    assert removeLeadingPunctAndSpaces(", (these ") == "these "
    assert removeLeadingPunctAndSpaces("  (these ") == "these "
    assert removeLeadingPunctAndSpaces("(  these ") == "these "
    assert removeLeadingPunctAndSpaces("( , these ") == "these "
    assert trim_punct_and_spaces("( , these , :)") == "these"
    assert trim_punct_and_spaces("(1997)") == "1997"

    # test other functions
    assert isEmpty("&PD;") == 0, "Is Empty Failed"
    assert isEmpty("dog gone it") == 0, "Is Empty Failed"
    assert isEmpty("") == 1, "Is Empty Failed"

    assert atoiNotEmpty("23") == 23, "atoiNotEmpty Failed"
    assert atoiNotEmpty("1") == 1, "atoiNotEmpty Failed"
    assert atoiNotEmpty("2") == 2, "atoiNotEmpty Failed"
    assert remove_letter_prefix_and_suffix("2s") == ("", "2", "s"), remove_letter_prefix_and_suffix("2s")
    assert remove_letter_prefix_and_suffix("ae3so") == ("ae", "3", "so"), remove_letter_prefix_and_suffix("ae3so")
    assert remove_letter_prefix_and_suffix("ae4s-o") == ("ae", "4", "s-o"), remove_letter_prefix_and_suffix("ae4s-o")
    assert remove_letter_prefix_and_suffix("ae4-o") == ("ae", "4", "-o"), remove_letter_prefix_and_suffix("ae4-o")
    assert atoiNotEmpty("2s") == 2, "atoiNotEmpty Failed"

    assert isLowerCase("abcddedewewefe") == True
    assert isLowerCase("Abcddedewewefe") == False
    assert isLowerCase("12cddedewewefe") == True
    assert isUpperCase("abcddedewewefe") == False
    assert isUpperCase("ABCDDEDEWEWEFE") == True
    assert isUpperCase("12CDDEDEWEWEFE") == True

    print("All assertions tested.  Any errors displayed above.")
