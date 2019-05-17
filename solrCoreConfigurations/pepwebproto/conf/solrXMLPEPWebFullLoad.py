""" solrXMLPEPWebFullLoad

This module imports *documents* from PEP's processed XML form (bEXP_ARCH1)
   into a Solr database.

Example Invocation:

        $ python solrXMLPEPWebFullLoad.py

        Use -h for help on arguments.

Todo:
    * Need to add code to only do "new" files to save build time
    * I always use "core" when it may be better to refer to collection.
      Just a potential doc issue, but in some case core is actually more accurate.

Initial Release: Neil R. Shapiro 2019-05-15 (python 2.7)

Revisions:
    2019-05-16: Addded command line options to specify a different path for PEPSourceInfo.json
                Added error logging using python's built-in logging library default INFO level


"""
# Disable many annoying pylint messages, warning me about variable naming for example.
# yes, in my Solr code I'm caught between two worlds of snake_case and camelCase.

# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004

import re
import os
import time
import sys
import logging
from datetime import datetime
from optparse import OptionParser

# If on Python 2.X
#from __future__ import print_function
import json
import pysolr
from lxml import etree

#TODO: Move common support functions (and potentially all of common interest) to separate include script (library)
class ExitOnExceptionHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        if record.levelno in (logging.ERROR, logging.CRITICAL):
            raise SystemExit(-1)

def elementsToStrings(elementNode, xPathDef):
    """
    Return a list of XML tagged strings from the nodes in the specified xPath

    Example:
    strList = elementsToStrings(treeRoot, "//aut[@listed='true']")

    """
    retVal = [etree.tostring(n, with_tail=False) for n in elementNode.xpath(xPathDef)]
    return retVal

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
    except KeyError, err:
        pass  # this is ok, just means the attribute is not present.
    except Exception, err:
        print "getElementAttr Error: ", err
        raise Exception

    return retVal

def findSubElementText(elementNode, subElementName):
    """
    Text for elements with only CDATA underneath

    subElementName should not be a path
    """
    retVal = ""
    try:
        retVal = [etree.tostring(n, with_tail=False) for n in elementNode.findall(subElementName)]
    except Exception, err:
        print "findSubElementText Error: ", err
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
    """
    Load a database of info about the PEP Sources
    including full name of source, abbreviated name, issn, etc.

    Read as is since this JSON file can be simply and quickly exported
    from the pepsourceinfo view (based on issn table) in the mySQL pepa1db
    database used (and populated) in data processing from KBD3 to PEP_ARCH1

    Currently, we can use the "PEPSourceInfo export" export definition
      stored in mysql.

    """

    #
    #
    #
    retVal = {}
    with open(journalInfoFile) as f:
        journalInfo = json.load(f)

    # turn it into a in-memory dictionary indexed by jrnlcode;
    # in 2019, note that there are only 111 records
    for n in journalInfo["RECORDS"]:
        retVal[n["pepsrccode"]] = n

    return retVal


def main():
    """
    PEP Full Text Data loader
    """

    print """PEP Solr Full Text Data Loader
             Load articles, extract references from the bibliography, and
             add to Solr database

             Use -h option to see command line options and version number
        """

    scriptSourcePath = os.path.dirname(os.path.realpath(__file__))
    programNameShort = "OPASXMLFullLoad"

    parser = OptionParser(usage="%prog [options] - PEP Solr Full Text Data Loader", version="%prog ver. 0.1.16")
    parser.add_option("-c", "--corename", dest="coreName", default="pepwebproto",
                      help="the Solr corename (holding the collection) to connect to, i.e., where to send data, e.g., 'pepwebproto'")
    parser.add_option("-d", "--dataroot", dest="rootFolder", default=r"C:\solr-8.0.0\server\solr\pepwebproto\sampledata\_PEPA1",
                      help="Root folder path where input data is located")
    parser.add_option("-l", "--loglevel", dest="logLevel", default=logging.INFO,
                      help="Level at which events should be logged")
    parser.add_option("-r", "--resetcoredata",
                      action="store_true", dest="resetCoreData", default=False,
                      help="reset the data in the collection/core")
    parser.add_option("-s", "--sourcodedb", dest="sourceCodeDBPath", default=None,
                      help="Folder where PEPSourceInfo.json is located (simple source info DB in JSON)")
    parser.add_option("-u", "--url",
                      dest="solrURL", default="http://localhost:8983/solr/",
                      help="Base URL of Solr api (without core)", metavar="URL")

    # TODO: later; even odd starting page numbers selectivity will allow us to run two instances at a time, and the processes will work on different files, for shorter process times.
    #parser.add_option("-e", "--even", dest="evenFiles", default=0,
                      #help="Only do files where the starting page is even")
    #parser.add_option("-o", "--odd", dest="evenFiles", default=0,
                      #help="Only do files where the starting page is odd")


    (options, args) = parser.parse_args()

    logFilename = programNameShort + "_" + datetime.today().strftime('%Y-%m-%d') + ".log"
    processingErrorCount = 0
    processingWarningCount = 0
    processedFilesCount = 0
    logging.basicConfig(handlers=[ExitOnExceptionHandler()], filename=logFilename, level=options.logLevel)
    logger = logging.getLogger(programNameShort)
    logger.info('Started at %s', datetime.today().strftime('%Y-%m-%d %H:%M:%S"'))

    solrAPIURL = options.solrURL + options.coreName  # e.g., http://localhost:8983/solr/pepwebproto'

    if options.sourceCodeDBPath is None:
        options.sourceCodeDBPath = options.rootFolder

    print "Input data Root: ", options.rootFolder
    print "Solr Core: ", options.coreName
    print "Reset Core Data: ", options.resetCoreData
    print "Solr solrAPIURL: ", solrAPIURL
    print "Logfile: ", logFilename

    time_start = time.time()
    # get a list of all the XML files

    # import data about the PEP codes for journals and books.
    #  Codes are like APA, PAH, ... and special codes like ZBK000 for a particular book
    pepSourceCodeDBName = r'PEPSourceInfo.json'
    sourceInfoDB = {}
    try:
        # param specified path, or by default, same as database
        sourceInfoDB = readSourceInfoDB(os.path.join(options.sourceCodeDBPath, pepSourceCodeDBName))
    except IOError:
        # try where the script is running from instead.
        logger.info("%s not found in %s. Trying base installation path.", pepSourceCodeDBName, options.sourceCodeDBPath)
        try:
            sourceInfoDB = readSourceInfoDB(os.path.join(scriptSourcePath, pepSourceCodeDBName))
        except IOError:
            logger.fatal("%s not found in %s.", pepSourceCodeDBName, scriptSourcePath)

    # Setup a Solr instance. The timeout is optional.
    solr = pysolr.Solr(solrAPIURL, timeout=1)

    # Reset core's data if requested (mainly for early development)
    if options.resetCoreData:
        solr.delete(q='*:*')

    # find all processed XML files where build is (bEXP_ARCH1) in path
    # glob.glob doesn't unfortunately work to do this in Py2.7.x
    pat = r"(.*)\(bEXP_ARCH1\)\.(xml|XML)$"
    filePatternMatch = re.compile(pat)
    filenames = []
    countFiles = 0
    for root, d_names, f_names in os.walk(options.rootFolder):
        for f in f_names:
            #TODO: Check file date against last import date for that file, and if not newer, skip
            #TODO: If newer, write filename to a database, maybe along with art_id, and file mod date/time so it can be skipped next time if not modified.
            #TODO: We also need a "rebuild" option in the command line, to bypass the date skipping (but not the recording)

            if filePatternMatch.match(f):
                countFiles += 1
                filenames.append(os.path.join(root, f))

    print "Ready to import full-text records from %s files at path: %s" % (countFiles, options.rootFolder)
    bibTotalReferenceCount = 0
    for n in filenames:
        f = open(n)
        fileXMLContents = f.read()

        # get file basename without build (which is in paren)
        base = os.path.basename(n)
        art_id = os.path.splitext(base)[0]
        m = re.match(r"(.*)\(.*\)", art_id)
        # Note: We could also get the art_id from the XML, but since it's also important
        # the file names are correct, we'll do it here.  Also, it "could" have been left out
        # of the artinfo (attribute), whereas the filename is always there.
        art_id = m.group(1)
        # all IDs to upper case.
        art_id = art_id.upper()

        # import into lxml
        root = etree.fromstring(fileXMLContents)
        pepxml = root[0]

        # let's just double check artid!
        try:
            artIDFromFile = pepxml.xpath('//artinfo/@id')[0]
            artIDFromFile = artIDFromFile.upper()

            if artIDFromFile != art_id:
                logger.warn("File name ID tagged and artID disagree.  %s vs %s", art_id, artIDFromFile)
                processingWarningCount += 1
        except Exception, err:
            logger.warn("Issue reading file's article id. (%s)", err)
            processingWarningCount += 1

        # Article data
        #<!-- Common fields -->
        #<!-- Article front matter fields -->
        #---------------------------------------------
        art_pepsrccode = pepxml.xpath("//artinfo/@j")[0]
        try:
            art_pepsourcetitleabbr = sourceInfoDB[art_pepsrccode].get("sourcetitleabbr")
            art_pepsourcetitlefull = sourceInfoDB[art_pepsrccode].get("sourcetitlefull")
            art_pepsourcetype = sourceInfoDB[art_pepsrccode].get("pep_class")  # journal, book, video...

        except KeyError, err:
            art_pepsourcetitleabbr = ""
            art_pepsourcetitlefull = ""
            art_pepsourcetype = ""
            logger.warn("Error: PEP Source Code %s not found in db (%s).  Use the 'PEPSourceInfo export' after fixing the issn table in MySQL DB", art_pepsrccode, options.rootFolder + pepSourceCodeDBName)

        except Exception, err:
            logger.error("Error: Problem with this files source info. File skipped. (%s)", err)
            processingErrorCount += 1
            continue

        #art_vol = pepxml.xpath('//artinfo/artvol/node()')
        #art_year = pepxml.xpath('//artinfo/artyear/node()')
        # ----------------------------------------------------------------
        title = findSubElementXML(pepxml, "arttitle")
        if title != None and title != "":
            # remove tags:
            title = ''.join(etree.fromstring(title).itertext())
        subtitle = findSubElementXML(pepxml, 'artsub')
        if subtitle == "":
            pass
        elif subtitle is None:
            subtitle = ""
        else:
            subtitle = ''.join(etree.fromstring(subtitle).itertext())
            subtitle = ": " + subtitle
        title = title + subtitle
        # ----------------------------------------------------------------

        # ToDo: I think I should add an author ID to bib aut too.  But that will have
        #  to wait until I rebuild everything in January.
        #---------------------------------------------
        art_authors = pepxml.xpath('//artinfo/artauth/aut[@listed="true"]/@authindexid')
        #---------------------------------------------
        #---------------------------------------------
        #Or doesn't seem to work in xpath in lxml
        headings = elementsToStrings(pepxml, "//h1")
        headings += elementsToStrings(pepxml, "//h2")
        headings += elementsToStrings(pepxml, "//h3")
        headings += elementsToStrings(pepxml, "//h4")
        headings += elementsToStrings(pepxml, "//h5")
        headings += elementsToStrings(pepxml, "//h6")
        #---------------------------------------------

        #---------------------------------------------
        # We need to completely rethink books, but as placeholders now.
        # not found in pep
        #---------------------------------------------

        art_citeas = """<p class="citeas"><span class="authors">%s</span> (<span class="year">%s</span>) <span class="title">%s</span>. <span class="sourcetitle">%s</span> <span class="pgrg">%s</span>:<span class="pgrg">%s</span></p>""" \
                         %                   (", ".join(art_authors),
                                              getSingleSubnodeText(pepxml, 'artyear'),
                                              title,
                                              art_pepsourcetitlefull,
                                              getSingleSubnodeText(pepxml, 'artvol'),
                                              getSingleSubnodeText(pepxml, "artpgrg"))

        #<!-- biblio section fields -->
        #Note: currently, this does not include footnotes or biblio include tagged data in document (binc)
        bib_references = pepxml.xpath("/pepkbd3//be")

        bib_reference_count = len(bib_references)
        bibTotalReferenceCount += bib_reference_count
        print "File %s has %s references." % (base, bib_reference_count)
        bib_refentries_struct = {}
        for ref in bib_references:
            bib_articletitle = getSingleSubnodeText(ref, "t")
            bib_sourcetitle = getSingleSubnodeText(ref, "j")
            bib_publishers = getSingleSubnodeText(ref, "bp")
            bib_bookyearofpublication = getSingleSubnodeText(ref, "bpd")
            bib_yearofpublication = getSingleSubnodeText(ref, "y")
            if bib_publishers != "":
                bib_sourcetype = "book"
            else:
                bib_sourcetype = "journal"
            if bib_sourcetype == "book":
                if bib_yearofpublication == "":
                    bib_yearofpublication = bib_bookyearofpublication
                if bib_bookyearofpublication == "":
                    bib_bookyearofpublication = bib_yearofpublication
                if bib_sourcetitle == "":
                    bib_sourcetitle = bib_sourcetitle  # book title
                    if bib_articletitle == "":
                        bib_articletitle = getSingleSubnodeText(ref, "bst")  # book title
                        bib_sourcetitle = ""

            bib_author_name_list = [(etree.tostring(x, with_tail=False)) for x in ref.findall("a")]
            bib_authors = '; '.join(bib_author_name_list)

            # A json structure will be stored in a single field in Solr with the reference field breakdown, as well
            #   as the full-text of the reference tagged.  Otherwise, these data fields would not be stored
            #   together on a reference by reference basis: all the bib_sourcetititles, for example, would be in
            #   one field as a list, the bib_articletitles in another, etc.  This "subrecord" of sorts holds them
            #   together, though as far as I know, they will not be individually addressable by Solr.

            bib_refentries_struct[getElementAttr(ref, "id")] = {
                "bib_ref_rx" : getElementAttr(ref, "rx"),
                "bib_sourcetype" : bib_sourcetype,
                "bib_articletitle" : bib_articletitle,
                "bib_sourcetitle" : bib_sourcetitle,
                "bib_yearofpublication" : bib_yearofpublication,
                "bib_pgrg" : getSingleSubnodeText(ref, "pp"),
                "bib_volume" : getSingleSubnodeText(ref, "v"),
                "bib_authors" : bib_authors,
                "bib_bookyearofpublication" : bib_bookyearofpublication,
                "bib_bookpublisher" : getSingleSubnodeText(ref, "bp"),
                "text": etree.tostring(ref, with_tail=False)
            }


        if bib_refentries_struct == {}:
            bib_refentries_struct = ""

        art_lang = pepxml.xpath('//@lang')
        if art_lang == []:
            art_lang = ['EN']

        # Now lets add the article record to Solr
        # this build of the schema now has all XML data fields indicated in the field name
        # the snake_case works better for Solr; as a result, a bit of it thus creeps into this python code, but
        # I still prefer to use camelCase.  Unfortunately, lint is unhappy I use both :)

        processedFilesCount += 1

        try:
            response_update = solr.add([
                {
                    "id": art_id,                   # important: note this is unique id for every reference
                    "art_id": art_id,
                    "art_title_xml": elementsToStrings(pepxml, "//arttitle"),
                    "art_subtitle_xml": elementsToStrings(pepxml, "//artsubtitle"),
                    "title": title,
                    "art_pepsrccode": art_pepsrccode,
                    "art_pepsourcetitleabbr": art_pepsourcetitleabbr,
                    "art_pepsourcetitlefull": art_pepsourcetitlefull,
                    "art_pepsourcetype": art_pepsourcetype,
                    "art_authors": art_authors,
                    "art_authors_unlisted": pepxml.xpath('//artinfo/artauth/aut[@listed="false"]/@authindexid'),
                    "art_authors_xml": elementsToStrings(pepxml, "//aut"),
                    "art_year": pepxml.xpath('//artinfo/artyear/node()'),
                    "art_vol": getSingleSubnodeText(pepxml, 'artvol'),
                    "art_pgrg": getSingleSubnodeText(pepxml, "artpgrg"),
                    "art_iss": pepxml.xpath('//artissue/node()'),
                    "art_doi": pepxml.xpath("//artinfo/@doi"),
                    "art_lang": art_lang,                       # list
                    "art_issn": pepxml.xpath('//artinfo/@ISSN'),
                    "art_origrx": pepxml.xpath('//artinfo/@origrx'),
                    "art_qual": pepxml.xpath("//artinfo/artqual/@rx"),
                    "art_kwds": pepxml.xpath("//artinfo/artkwds/node()"),
                    "art_type": pepxml.xpath("//artinfo/@arttype"),
                    "art_newsecnm": pepxml.xpath("//artinfo/@newsecnm/node()"),
                    "art_citeas_xml": art_citeas,
                    "bib_entries_json":bib_refentries_struct,  # hmm, I wonder if we should type suffix other fields?
                    "authors": art_authors,         # for common names convenience
                    "author_bio_xml": elementsToStrings(pepxml, "//nbio"),
                    "author_aff_xml": elementsToStrings(pepxml, "//autaff"),
                    "bk_title_xml": elementsToStrings(pepxml, "//artbkinfo/bktitle"),
                    "bk_alsoknownas_xml": elementsToStrings(pepxml, "//artbkinfo/bkalsoknownas"),
                    "bk_editors_xml": elementsToStrings(pepxml, "//bkeditors"),
                    "bk_seriestitle_xml": elementsToStrings(pepxml, "//bkeditors"),
                    "bk_pubyear": pepxml.xpath("//bkpubyear/node()"),
                    "caption_text_xml": elementsToStrings(pepxml, "//caption"),
                    "caption_title_xml": elementsToStrings(pepxml, "//ctitle"),
                    "headings_xml": headings,
                    "references_xml": elementsToStrings(pepxml, "/pepkbd3//be"),
                    "abstracts_xml": elementsToStrings(pepxml, "///abs"),
                    "summaries_xml": elementsToStrings(pepxml, "///summaries"),
                    "terms_xml": elementsToStrings(pepxml, "//impx[@type='TERM2']"),
                    "terms_highlighted_xml": elementsToStrings(pepxml, "//b") + elementsToStrings(pepxml, "//i"),
                    "dialogs_spkr": pepxml.xpath("//dialog/spkr/node()"),
                    "dialogs_xml": elementsToStrings(pepxml, "//dialog"),
                    "dreams_xml": elementsToStrings(pepxml, "//dream"),
                    "notes_xml": elementsToStrings(pepxml, "//note"),
                    "panels_spkr": elementsToStrings(pepxml, "//panel/spkr"),
                    "panels_xml": elementsToStrings(pepxml, "//panel"),
                    "poems_src": pepxml.xpath("//poem/src/node()"),
                    "poems_xml": elementsToStrings(pepxml, "//poem"),
                    "quotes_spkr": pepxml.xpath("//quote/spkr/node()"),
                    "quotes_xml": elementsToStrings(pepxml, "//quote"),
                    "meta_xml": elementsToStrings(pepxml, "//meta"),
                    "text_xml": fileXMLContents,
                }])
        except Exception, err:
            processingErrorCount += 1
            logger.error("Solr call exception %s", err)


            # print response_update
        f.close()

        if processingErrorCount > 900:
            print "Processed File Count: %s" % processedFilesCount
            logger.exception("File processing error count > 100.  Stopping data load.")


    solr.commit()
    time_end = time.time()

    msg = "Finished! Imported %s documents with %s references. Elapsed time: %s secs" % (len(filenames), bibTotalReferenceCount, time_end-time_start)
    print msg
    logger.info(msg)
    if processingWarningCount + processingErrorCount > 0:
        print "  Issues found.  Warnings: %s, Errors: %s.  See log file %s" % (processingWarningCount, processingErrorCount, logFilename)

# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    main()
