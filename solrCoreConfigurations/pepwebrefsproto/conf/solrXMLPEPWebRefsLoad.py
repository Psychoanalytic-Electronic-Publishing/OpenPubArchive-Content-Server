""" solrXMLPEPWebRefsLoad

This module imports references from PEP's processed XML form (bEXP_ARCH1)
   into a Solr database.

It currently doesn't use any arguments, because the prototype paths and
  PEP specific build info are in assigned variables that are not expected ot
  change once the setup is done.

  This includes:
    dir1 = r"C:\solr-8.0.0\server\solr\pepwebproto\sampledata\_PEPA1"
    pepSourceCodeDBName = r'\PEPSourceInfo.json'
    solr = pysolr.Solr('http://localhost:8983/solr/pepwebrefsproto', timeout=1)

Example Invocation:

        $ python solrXMLPEPRefsLoad.py

Todo:
    * Need to add code to only do "new" files to save build time

"""
# Disable many annoying pylint messages, warning me about variable naming for example.
# yes, in my Solr code I'm caught between two worlds of snake_case and camelCase.

# pylint: disable=C0321,C0103,C0301,E1101,C0303

import re
import os
import time
import sys

# If on Python 2.X
#from __future__ import print_function
import json
import pysolr
from lxml import etree
from optparse import OptionParser

def xml_text_only(elem):
    '''Return inner text of element with tags stripped'''
    etree.strip_tags(elem, '*')
    inner_text = elem.text
    if inner_text:
        return inner_text.strip()
    return None

def getSingleSubnodeText(elementNode, subelementName):
    retVal = ""

    try:
        retVal = elementNode.xpath('%s/node()' % subelementName)
        retVal = retVal[0]
    except ValueError, err: # try without node
        retVal = elementNode.xpath('%s' % subelementName)
        retVal = retVal[0]
    except IndexError, err:
        retVal = elementNode.xpath('%s' % subelementName)
    except Exception, err:
        print "getSingleSubnodeText Error: ", err

    if retVal == []:
        retVal = ""
    return retVal

def getElementAttr(elementNode, attrName):
    retVal = ""
    try:
        retVal = elementNode.attrib[attrName]
    except Exception, err:
        retVal = ""

    return retVal

def findSubElementText(elementNode, subElementName):
    """
    Text for elements with only CDATA underneath
    """
    retVal = ""
    try:
        retVal = elementNode.find(subElementName).text
    except Exception, err:
        retVal = ""

    return retVal

def findSubElementXML(elementNode, subElementName):
    """
    Text for elements with nested tags
    """
    retVal = ""
    try:
        retVal = etree.tostring(elementNode.find(subElementName), with_tail=False)
    except Exception, err:
        retVal = ""

    return retVal

def readSourceInfoDB(journalInfoFile):
    # journal info "database" in json
    # Read as is since this JSON file can be simply and quickly exported
    # from the issn table in mySQL used in data conversion
    retVal = {}
    with open(journalInfoFile) as f:
        journalInfo = json.load(f)

    # turn it into a in-memory dictionary indexed by jrnlcode;
    # in 2019, note that there are only 111 records
    for n in journalInfo["RECORDS"]:
        retVal[n["pepsrccode"]] = n

    return retVal

def main():
    print """PEP Bibliography section loader...
             Load articles, extract references from the bibliography, and
             add to Solr database

             Ver 0.1.13 - nrs 2019-05-13
        """

    parser = OptionParser(usage="%prog [options] - PEP Solr Reference Text Data Loader", version="%prog ver. 0.1.13")
    parser.add_option("-u", "--url",
                      dest="solrURL", default="http://localhost:8983/solr/",
                      help="Base URL of Solr api (without core), e.g., http://localhost:8983/solr/", metavar="URL")
    parser.add_option("-r", "--resetcoredata",
                      action="store_true", dest="resetCoreData", default=False,
                      help="reset the data in the core (collection)")
    parser.add_option("-d", "--dataroot", dest="rootFolder", default=r"C:\solr-8.0.0\server\solr\pepwebproto\sampledata\_PEPA1",
                      help="Root folder path where input data is located")
    parser.add_option("-c", "--corename", dest="coreName", default="pepwebrefsproto",
                      help="the Solr corename (holding the collection) to connect to, i.e., where to send data, e.g., 'pepwebrefsproto'")


    (options, args) = parser.parse_args()

    solrAPIURL = options.solrURL + options.coreName  # e.g., http://localhost:8983/solr/pepwebproto'

    print "Input data Root: ", options.rootFolder
    print "Solr Core: ", options.coreName
    print "Reset Core Data: ", options.resetCoreData
    print "Solr solrAPIURL: ", solrAPIURL

    time_start = time.time()

    # get a list of all the XML files
    # import data about the PEP codes for journals and books.
    #  Codes are like APA, PAH, ... and special codes like ZBK000 for a particular book
    pepSourceCodeDBName = r'\PEPSourceInfo.json'
    sourceInfoDB = readSourceInfoDB(options.rootFolder + pepSourceCodeDBName)

    # Setup a Solr instance. The timeout is optional.
    solr = pysolr.Solr(solrAPIURL, timeout=1)

    # Reset core's data if requested (mainly for early development)
    if options.resetCoreData:
        solr.delete(q='*:*')

    # find all processed XML files where build is (bEXP_ARCH1) in path
    # glob.glob doesn't unfortunately work to do this in Py2.7.x
    pat = r"(.*)\(bEXP_ARCH1\)\.(xml|XML)"
    filePatternMatch = re.compile(pat)
    filenames = []
    for root, d_names, f_names in os.walk(options.rootFolder):
        for f in f_names:
            if filePatternMatch.match(f):
                filenames.append(os.path.join(root, f))

    print "Ready to import reference records from %s files at path: %s" % (len(filenames), options.rootFolder)
    bibTotalReferenceCount = 0
    for n in filenames:
        f = open(n)
        fileXMLContents = f.read()

        # get file basename without build (which is in paren)
        base = os.path.basename(n)
        art_id = os.path.splitext(base)[0]
        m = re.match(r"(.*)\(.*\)", art_id)
        art_id = m.group(1)
        # all IDs to upper case.
        art_id = art_id.upper()

        # import into lxml
        root = etree.fromstring(fileXMLContents)
        pepxml = root[0]

        # Containing Article data
        #<!-- Common fields -->
        #<!-- Article front matter fields -->
        art_pepsrccode = pepxml.xpath("//artinfo/@j")[0]
        try:
            art_pepsourcetitleabbr = sourceInfoDB[art_pepsrccode].get("sourcetitleabbr")
            art_pepsourcetitlefull = sourceInfoDB[art_pepsrccode].get("sourcetitlefull")
            art_pepsourcetype = sourceInfoDB[art_pepsrccode].get("pep_class")  # journal, book, video...

        except KeyError, err:
            art_pepsourcetitleabbr = ""
            art_pepsourcetitlefull = ""
            art_pepsourcetype = ""
            print "Error: PEP Source Code %s not found in db (%s).  Use the 'PEPSourceInfo export' after fixing the issn table in MySQL DB" % (art_pepsrccode, options.rootFolder + pepSourceCodeDBName)

        except Exception, err:
            print err
            sys.exit(-1)

        art_vol = pepxml.xpath('//artinfo/artvol/node()')
        art_year = pepxml.xpath('//artinfo/artyear/node()')
        art_title = findSubElementXML(pepxml, "arttitle")
        if art_title != None and art_title != "":
            # remove tags:
            art_title = ''.join(etree.fromstring(art_title).itertext())
        art_subtitle = findSubElementXML(pepxml, 'artsub')
        if art_subtitle == "":
            pass
        elif art_subtitle == None:
            art_subtitle = ""
        else:
            art_subtitle = ''.join(etree.fromstring(art_subtitle).itertext())
            art_subtitle = ": " + art_subtitle

        art_title = art_title + art_subtitle
        art_type = pepxml.xpath("//artinfo/@arttype")
        art_pgrg = findSubElementText(pepxml, "artpgrg")
        art_lang = pepxml.xpath('//pepkbd3/@lang')
        # ToDo: I think I should add an author ID to bib aut too.  But that will have
        #  to wait until I rebuild everything in January.
        art_authors = pepxml.xpath('//artinfo/artauth/aut[@listed="true"]/@authindexid')
        art_authors = ", ".join(art_authors)
        # Usually we put the abbreviated title here, but that won't always work here.

        art_citeas = """<p class="citeas"><span class="authors">%s</span> (<span class="year">%s</span>) <span class="title">%s</span>. <span class="sourcetitle">%s</span> <span class="pgrg">%s</span>:<span class="pgrg">%s</span></p>""" \
            %                   (art_authors,
                                 art_year[0],
                                 art_subtitle,
                                 art_pepsourcetitlefull,
                                 getSingleSubnodeText(pepxml, 'artvol'),
                                 getSingleSubnodeText(pepxml, "artpgrg"))


        #<!-- biblio section fields -->
        #Note: currently, this does not include footnotes or biblio include tagged data in document (binc)
        bib_references = pepxml.xpath("/pepkbd3//be")
        bib_reference_count = len(bib_references)
        bibTotalReferenceCount += bib_reference_count
        print("File %s has %s references." % (base, bib_reference_count))
        for ref in bib_references:
            bib_refentry = etree.tostring(ref, with_tail=False)
            bib_ref_id = getElementAttr(ref, "id")
            refid = art_id + "." + bib_ref_id
            bib_ref_rx = getElementAttr(ref, "rx")
            bib_articletitle = findSubElementText(ref, "t")
            bib_sourcetitle = findSubElementText(ref, "j")
            bib_publishers = findSubElementText(ref, "bp")
            if bib_publishers != "":
                bib_sourcetype = "book"
            else:
                bib_sourcetype = "journal"
            if bib_sourcetype == "book":
                bib_yearofpublication = findSubElementText(ref, "bpd")
                if bib_sourcetitle == None or bib_sourcetitle == "":
                    bib_sourcetitle = findSubElementText(ref, "bst")  # book title
                bib_articletitle = findSubElementText(ref, "t")
            else:
                bib_yearofpublication = findSubElementText(ref, "y")

            bib_pgrg = findSubElementText(ref, "pp")
            bib_volume = findSubElementText(ref, "v")

            bib_author_name_list = [etree.tostring(x, with_tail=False) for x in ref.findall("a")]
            bib_authors = '; '.join(bib_author_name_list)
            author_list = [xml_text_only(x) for x in ref.findall("a")]
            author_list = '; '.join(author_list)

            response_update = solr.add([
                {
                    "id": refid,                   # important: note this is unique id for every reference
                    "art_id":art_id,
                    "art_title":art_title,
                    "art_pepsrccode":art_pepsrccode,
                    "art_pepsourcetitleabbr":art_pepsourcetitleabbr,
                    "art_pepsourcetitlefull":art_pepsourcetitlefull,
                    "art_pepsourcetype":art_pepsourcetype,
                    "art_authors":art_authors,
                    "art_year":art_year,
                    "art_vol":art_vol,
                    "art_pgrg":art_pgrg,
                    "art_lang":art_lang,
                    "art_citeas_xml":art_citeas,
                    "text": bib_refentry,          # this is xml, against my naming, but if I create a text_xml, I also need a text because that's the default unfielded search
                    "reference_xml":bib_refentry,
                    "authors":author_list,         # for common names convenience
                    "title":bib_articletitle,
                    "bib_authors_xml":bib_authors,
                    "bib_ref_id":bib_ref_id,
                    "bib_ref_rx":bib_ref_rx,
                    "bib_articletitle":bib_articletitle,
                    "bib_sourcetype":bib_sourcetype,
                    "bib_sourcetitle":bib_sourcetitle,
                    "bib_pgrg":bib_pgrg,
                    "bib_year":bib_yearofpublication,
                    "bib_volume":bib_volume,
                    "bib_publisher":bib_publishers
                }])

        f.close()

    solr.commit()
    time_end = time.time()

    print "Finished! Imported %s documents with %s references. Elapsed time: %s secs" % (len(filenames), bibTotalReferenceCount, time_end-time_start)
# run it!
main()
