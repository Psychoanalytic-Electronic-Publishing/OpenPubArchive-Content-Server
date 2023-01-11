# -*- coding: UTF-8 -*-

import sys
import re
import logging
logger = logging.getLogger(__name__)

__version__="1.00"

"""
Munger - A made-up concept where a demarcator is used to delimit a special string with parts

An older Scilab Inc. string library Converted from Python 2 with just a bit of usage in
  PEP OPAS.

"""
demarcator = "#"
    
#--------------------------------------------------------------------------------
def converseTerm(term, default=None):
    """
    Straighten out a comma based term.  If there's no difference in the convere,
      then return whatever is set for the default (normally None)


    >>> converseTerm("Seduction, Scene of")
    'Scene of Seduction'
    >>> converseTerm("Seduction, Scene of, Part 2")
    'Part 2 Scene of Seduction'
    >>> converseTerm("Scene of Seduction (see Theory of Seduction)")
    
    """
    retVal = None
    if "," in term:
        retVal = ' '.join(x.strip() for x in reversed(term.split(',')))

    return retVal

#--------------------------------------------------------------------------------
def isMunged(testStr):
    """
    See if this string is munged

    >>> isMunged("#Scene of Seduction Theory of Seduction#")
    True
    >>> isMunged("#Scene of Seduction## Theory of Seduction#")
    True
    >>> isMunged("Scene of Seduction; Theory of Seduction")
    False

    """
    if testStr[0] == "#" and testStr[-1] == "#":
        return True
    elif testStr[0] == "#":
        raise ValueError("Term may only be partly munged!")
    else:
        return False

#--------------------------------------------------------------------------------
def makeTermList(strTerm = None, separatorPattern = "\/|;", removeParentheticalPattern="\(.*\)" ):
    """
    Splits the term into a list based on a separatorPattern.
    If removeParentheticalPattern is not == None, then parenthesized material is removed.

    >>> makeTermList("Scene of Seduction (see whatever); Theory of Seduction")
    ['Scene of Seduction', 'Theory of Seduction']
    >>> makeTermList(u"Scene of Seduction; Theory of Seduction")
    ['Scene of Seduction', 'Theory of Seduction']
    >>> makeTermList(u"SELFOBJECT, BAD")
    ['SELFOBJECT, BAD']
    >>> result = makeTermList("Scene of Seduction (see whatever); Theory of Seduction")
    >>> termData1 = result[0]
    >>> termData2 = result[1]

    """
    retVal = []

    if isMunged(strTerm):
        retVal = unMungeToTermList(strTerm)
    else:
        termNoParen = ";".join(re.split(removeParentheticalPattern, strTerm))
        # slash or semicolon based
        retVal = list(filter(None, [x.strip() for x in re.split(separatorPattern, termNoParen)]))

    return retVal

#--------------------------------------------------------------------------------
def mungeStr(termStr):
    """
    Munge the term by splitting it so it can be searched different ways


    >>> mungeStr("SELFOBJECT, BAD")
    '#SELFOBJECT, BAD##BAD SELFOBJECT#'
    >>> mungeStr("Scene of Seduction; Theory of Seduction")
    '#Scene of Seduction##Theory of Seduction#'
    >>> mungeStr("Scene of Seduction / Theory of Seduction")
    '#Scene of Seduction##Theory of Seduction#'
    >>> mungeStr("Scene of Seduction; Theory of Seduction")
    '#Scene of Seduction##Theory of Seduction#'
    >>> mungeStr('#Scene of Seduction##Theory of Seduction#')
    '#Scene of Seduction##Theory of Seduction#'

    """
    retVal = makeTermList(termStr)
    retVal2 = []
    for n in retVal:
        if "," in n:
            reverseN = converseTerm(n)
            if reverseN not in retVal:
                retVal2.append(reverseN)

    retVal += retVal2
    retVal = mungeTermList(retVal)
    return retVal

#--------------------------------------------------------------------------------
def mungeTermList(termList):
    """
    Munge the list


    >>> originalStr = r"#MAHLER, MARGARET S##MARGARET S MAHLER#"
    >>> umT = unMungeToTermList(originalStr)
    >>> mungedL = mungeTermList(umT)
    >>> mungedL           #doctest: +NORMALIZE_WHITESPACE
    '#MAHLER, MARGARET S##MARGARET S MAHLER#'
    >>> termL = unMungeToTermList(mungedL)
    >>> mungeTermList(termL)
    '#MAHLER, MARGARET S##MARGARET S MAHLER#'

    >>> termL = unMungeToTermList("#dog##eat##dog#")
    >>> mungeTermList(termL)
    '#dog##eat##dog#'


    """
    retVal = "".join([demarcator + x.strip() + demarcator for x in termList])
    return retVal
    
#--------------------------------------------------------------------------------
def unMungeToTermList(mungedTerm, demarcPattern=demarcator):
    """
    unMunge the term so it can be searched different ways
    Returns a list of terms


    >>> unMungeToTermList("#dog##eat##dog#")
    ['dog', 'eat', 'dog']
    >>> unMungeToTermList("#dog## eat ##dog#")
    ['dog', 'eat', 'dog']
    >>> termL = unMungeToTermList("#DÉJÀ VU##Déjà Raconté#")
    >>> print (termL[0])
    DÉJÀ VU
    """

    retVal = list(filter(None, [x.strip() for x in mungedTerm.split(demarcPattern)]))

    return retVal

#--------------------------------------------------------------------------------
def unMungeTerm(mungedTerm, demarcPattern=demarcator):
    """
    unMunge the term so it can be searched different ways
    Returns a unicode string where terms are separated by ";"


    >>> originalStr = r"#MAHLER, MARGARET S##MARGARET S MAHLER#"
    >>> umT = unMungeTerm(originalStr)
    >>> umT
    'MAHLER, MARGARET S; MARGARET S MAHLER'
    >>> mungeStr(umT)
    '#MAHLER, MARGARET S##MARGARET S MAHLER#'
    >>> unMungeTerm("#dog##eat##dog#")
    'dog; eat; dog'

    >>> unMungeTerm("#dog## eat ##dog#")
    'dog; eat; dog'

    >>> unMungeTerm("dog eat dog")
    'dog eat dog'

    """

    retVal = unMungeToTermList(mungedTerm, demarcPattern)
    retVal = "; ".join(retVal)

    return retVal

#==================================================================================================
# Main Routines
#==================================================================================================

if __name__ == "__main__":
    """
	Run Test Routines
	"""

    import doctest
    doctest.testmod()
    print ("Fini. Tests complete.")
    sys.exit()