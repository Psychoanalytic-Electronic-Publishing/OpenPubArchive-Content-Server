# -*- coding: UTF-8 -*-
# Copyright Neil R. Shapiro

"""
AuthorID class and support routines.

Includes isAuthorID function which uses the authorID class to recognize an authorID.

This module adapted from a much older module used in PEPXML to compile PEP instances since 200x!

  ** Slowly being adopted to opas **

"""
import sys, os.path

PROJECT_ROOT = os.path.abspath(os.path.join(
                  os.path.dirname(__file__), 
                  os.pardir)
)
sys.path.append(PROJECT_ROOT)

import re
import opasGenSupportLib as opasgenlib

PUNCTSETNOPERIOD = [',', ' ', ':', ';', ')', '(', '\t', '"', "'"]

autLocator = re.compile(r"""((\[)?
                            ([\"\'])?
                            (?P<queryID>(group|field\:)\s*)?
                            ([\"\']?)
                            (?P<oldstyleID>TOA\.)?
                            (?P<authorID>
                                (?P<nlast>((de|van|von)\s)?[A-Z\&\#\;0-9\-]+?\.?)
                                (\,\s*)
                                (?P<nfirst>[A-Z\&\#\;0-9\-]+\.?)
                            )
                            ([\"\'])?
                            ([\"\'])?
                            (\])?)""", re.VERBOSE | re.IGNORECASE)


#--------------------------------------------------------------------------------
def getStandardAuthorID(nlast, nfirst=None, nmid=None, nsufx=None, quoteSafe=0):
    """
    Compute a standardized authorID from the name paramaters.

    >>> getStandardAuthorID(nfirst="Arnold", nmid="Frankiin", nlast="Goldberg")
    'Goldberg, Arnold F.'

    >>> getStandardAuthorID(nfirst="Arnold", nlast="Goldberg")
    'Goldberg, Arnold'

    >>> getStandardAuthorID(nfirst="A", nmid="Frankiin", nlast="Goldberg")
    'Goldberg, A. F.'

    >>> getStandardAuthorID(nfirst="A.", nmid="Frankiin", nlast="Goldberg")
    'Goldberg, A. F.'

    >>> getStandardAuthorID(nlast="")
    'Anonymous'
    """

    if nlast == None or nlast == "":
        retVal = "Anonymous"
    else:
        retVal = opasgenlib.trimPunctAndSpaces(nlast, punct_set="!\u2019\u2018\"#$%&'*+,-./:;=?@[\]^_`{|}~")  # exception for parentheses, since sometimes we need them, e.g. McLoughlin (Akashadevi), Claudia

        # compute rest of it
        if nfirst != None:
            # don't remove period, it could be there because it's a "GIVEN" name from T&F
            nfirst = opasgenlib.trimPunctAndSpaces(nfirst, punct_set=PUNCTSETNOPERIOD)
            if len(nfirst) == 1 and nfirst[0] != ".":
                nfirst += "."

            if nfirst != "":
                retVal += ", " + nfirst

        if nmid != None and nmid != '':
            retVal += " " + opasgenlib.trimPunctAndSpaces(nmid[0:1]) + "."

        if nsufx != None:
            nsufx = opasgenlib.trimPunctAndSpaces(nsufx)
            if nsufx.lower() in ["jr", "sr", "esq"]:
                nsufx += "."

            retVal += " " + nsufx

        if retVal != None:

            # double any single quotes (used as apostrophes)
            if quoteSafe == 1:
                retVal = retVal.replace("'", "''") # fixed for Unicode compatibility

    return retVal

#--------------------------------------------------------------------------------
def decompileAuthorIDString(idString):
    """
    Return a dictionary with the parsed author components from an author id
    """
    retVal = {}
    # decompile the id (based on lastname, firstname or initial id)
    m = autLocator.match(idString)
    if m != None:
        retVal = m.groupdict()
    else:
        raise Exception("Unknown Author ID format")
    return retVal

#--------------------------------------------------------------------------------
def isAuthorIDString(idString):
    """
    Return True if the format of the string matches an author id

    >>> isAuthorIDString("Tuckett, D")
    True
    >>> isAuthorIDString("Tuckett")
    False
    """
    if not opasgenlib.is_empty(idString):
        if not isinstance(idString, str):  # supports string and unicode
            idString = repr(idString)
        #print "IDString: ", idString
        m = autLocator.match(idString)
        if m == None:
            retVal = False
        else:
            retVal = True
    else:
        print("Empty idString to isAuthorID")
        retVal = False

    return retVal

#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------
if __name__ == "__main__":
    """
	Run Locator test routines
	"""

    import doctest
    doctest.testmod()
    sys.exit()
