#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326
# Disable many annoying pylint messages, warning me about variable naming for example.
# yes, in my Solr code I'm caught between two worlds of snake_case and camelCase.

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2022.0925/v0.0.1" 
__status__      = "Development"

programNameShort = "opasEndnoteExport"

import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

print(
    f""" 
    {programNameShort} - Open Publications-Archive Server (OPAS) - Google Endnote Exporter
    
        Create Endnote file from opas articles
        
        Example Invocation:
                $ python {programNameShort}.py --recordsperfile=8000 --maxrecords=200000 --bucket pep-web-google
                
        Help for option choices:
         -h, --help  List all help options
    """
)

from lxml import objectify

sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')

import localsecrets
import opasFileSupport
import opasAPISupportLib
import opasPySolrLib

# import inspect
# from inspect import cleandoc

import logging
logger = logging.getLogger(programNameShort)

from optparse import OptionParser
from datetime import date
today = date.today()
current_year = today.year

"""
   From http://sti15.com/bib/formats/refer.html

   Standard tags

   H
   Header commentary which is printed before the reference.
   A
   Author's name. Authors should be listed in order, with the senior author first. Names are given in "First Last" format. If the name contains a suffix, it should be appended at the end with a comma, e.g. "Jim Jones, Jr.". For books with an editor but no author, the editor can go in the author field with a suffix of "ed", "eds", or something similar.
   Q
   Corporate author. Some sources also say to put foreign authors who have no clear last name in this field, but others claim the name here should be that of a non-person. Last time I checked, foreign authors were still people.
   T
   Title of the article or book.
   S
   Title of the series.
   J
   Journal containing the article.
   B
   Book containing article.
   R
   Report, paper, or thesis type.
   V
   Volume.
   N
   Number with volume.
   E
   Editor of book containing article.
   P
   Page number(s).
   I
   Issuer. This is the publisher.
   C
   City where published. This is the publishers address.
   D
   Date of publication. The year should be specified in full, and the month name rather than number should be used.
   O
   Other information which is printed after the reference.
   K
   Keywords used by refer to help locate the reference.
   L
   Label used to number references when the -k flag of refer is used.
   X
   Abstract. This is not normally printed in a reference.    
   
   Example with multiple authors
   %T Observations on Research Regarding the 'Symbiotic Syndrome' of Infantile Psychosis
   %J Psychoanal. Q.
   %A Mahler, Margaret S.
   %A Furer, Manuel
   %0 Journal Article  (Book or Book Section)
   %V 29
   %D 1960
   %P 317-327

   
"""

DOCUMENT_ITEM_FIELDS ="""
    art_id, 
    art_info_xml, 
    meta_xml, 
    art_citeas_xml, 
    art_title, 
    art_subtitle, 
    art_authors_xml,
    art_authors_citation_list,
    art_sourcecode, 
    art_sourcetype, 
    art_sourcetitleabbr, 
    art_sourcetitlefull,
    art_vol,
    art_year, 
    art_pgrg,
    art_pgcount,
    art_qual,
    file_classification, 
    score
"""

def val_or_emptystr(obj, default=""):
    ret_val = ""
    try:
        if obj is not None:
            ret_val = f"{obj}"
    except Exception as e:
        print (f"Exception: {e}")

    return ret_val

def find_or_emptystr(elem, find_target: str, default=""):
    ret_val = ""
    try:
        node = elem.find(find_target)
        if node is not None:
            ret_val = ''.join(node.itertext())
    except Exception as e:
        print (f"Exception: {e}")
    else:
        if ret_val is None:
            ret_val = ""

    return ret_val


def pep_endnote_generator(path=None, source_type="journal", source_code=None, fs=None,
                          size=None, max_records=None, clear_sitemap=None,
                          path_is_root_bucket=False):
    """
    Generate the EndNote file for the source type (journal, videos, or books).
    Optionally (mainly for testing) restrict to a specific source code.
    """
    journal_info = opasAPISupportLib.metadata_get_source_info(src_type=source_type)
    #journal_codes = [doc.PEPCode for doc in journal_info.sourceInfo.responseSet]
    jinfo = [(doc.PEPCode, doc) for doc in journal_info.sourceInfo.responseSet]
    journal_info_dict = dict(sorted(jinfo, key=lambda PEPCode: PEPCode[0]))
    endnote_text = ""
    for journal_code in journal_info_dict.keys():
        print (f"Writing metadata for {journal_code}")
        volume_info = opasPySolrLib.metadata_get_volumes(source_code=journal_code)
        volumes = [(vol.year, vol.vol, vol) for vol in volume_info.volumeList.responseSet]
        for volume in volumes:
            try:
                print (f"\tWriting endNote data for {journal_code}.{volume[0]}")
                contents = opasPySolrLib.metadata_get_contents(pep_code=journal_code, year=volume[0], vol=volume[1])
                contents = contents.documentList.responseSet
                # walk through the articles for the source code.
                for artinfo in contents:
                    try:
                        doclistitem = artinfo
                        artinfo = objectify.fromstring(doclistitem.documentInfoXML)
                        attrib = artinfo.attrib
                        art_sourcetitleabbr = val_or_emptystr(doclistitem.sourceTitleAbbr)
                        art_sourcetitlefull = val_or_emptystr(doclistitem.sourceTitle)
                        art_title = artinfo.arttitle
                        art_title_text = find_or_emptystr(artinfo, "arttitle")
                        if art_title_text == "":
                            print (doclistitem.documentID, " - No title text")
                        else:
                            art_subtitle = find_or_emptystr(artinfo, "artsub")
                            if art_subtitle != "":
                                art_title_text += f": {art_subtitle}"
                        
                        art_vol = artinfo.artvol
                        art_year = artinfo.artyear
                        auts = artinfo.artauth
                        publisher = journal_info_dict[journal_code].publisher
                        issn = journal_info_dict[journal_code].ISSN
                        aut_count = 0
                        art_sourcetype = ""
                        art_pgrg = f"{doclistitem.pgStart} - {doclistitem.pgEnd}"
                        author_lines = ""
                        try:
                            author_line = ""
                            aut_count += 1
                            for a in auts.aut:
                                nlast = find_or_emptystr(a, "nlast")
                                given_names = find_or_emptystr(a, "nfirst")
                                given_middle_name = find_or_emptystr(a, "nmid")
                                if given_names != "" and given_middle_name != "":
                                    given_names += f", {given_middle_name}"
                                #nsuffix = find_or_emptystr(a, "nsuffix")
                                #suffix_add = ""

                                if nlast != "":
                                    authname = nlast + ", " + given_names
                                else:
                                    continue

                                author_line = f"%A {authname}"
                                author_lines += "\n" + author_line
                                    
                            
                                
                        except Exception as e:
                            pass
                           
                        article_entry= f"""
%T {art_title}
%J {art_sourcetitlefull}
{author_lines}
%0 {art_sourcetype}
%V {art_vol}
%D {art_year}
%P {art_pgrg}
%E NA  book editor (we don't store this in Solr as a field)
"""
            
                    except Exception as e:
                        try:
                            logger.error (f"Error: {e} for {doclistitem.documentID}")
                            endnote_text += article_entry
                        except:
                            pass # ok, skip article
                    else:
                        endnote_text += article_entry

                    # article info end
                    
            except Exception as e:
                logger.error(f"Error: {e}")
                
    # done...write output file 
    outputFileName = f"{options.outfilebase + str(current_year)}.refer"
    msg = f"\t...Writing endnote file to {outputFileName}"
    if fs is not None:
        success = fs.create_text_file(outputFileName, data=endnote_text, path=path, path_is_root_bucket=path_is_root_bucket)
        if success:
            if options.display_verbose: # Writing endnote file
                print (msg)
        else:
            print (f"\t...There was a problem writing {outputFileName}.")
    else:
        print (f"\t...There was a problem writing {outputFileName}. Filesystem not supplied")
            
# -------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    options = None
    parser = OptionParser(usage="%prog [options] - PEP Google Endnote Export Generator", version=f"%prog ver. {__version__}")
    parser.add_option("-l", "--loglevel", dest="logLevel", default=logging.ERROR,
                      help="Level at which events should be logged (DEBUG, INFO, WARNING, ERROR")
    parser.add_option("-c", "--clear", dest="clearmetadata", action="store_true", default=False,
                      help="Clear prior metadata files (delete files in path/bucket matching metadata.*)")
    parser.add_option("--verbose", action="store_true", dest="display_verbose", default=False,
                      help="Display status and operational timing info as load progresses.")
    parser.add_option("-t", "--test", dest="testmode", action="store_true", default=False,
                      help="Run Doctests.  Will run a small sample of records and total output")
    parser.add_option("-r", "--recordsperfile", dest="recordsperfile", type="int", default=8000,
                      help="Max Number of records per file")
    parser.add_option("-m", "--maxrecords", dest="maxrecords", type="int", default=200000,
                      help="Max total records to be exported")
    parser.add_option("-b", "--bucket", "--path", dest="bucket", type="string", default=localsecrets.GOOGLE_METADATA_PATH,
                      help="Bucket or Local Path to write sitemap files on local system or S3 (on AWS must be a bucket)")
    parser.add_option("--rb", "--isrootbucket", dest="isrootbucket", action="store_false", 
                      help="True if the pathspecified is the bucketname on AWS")
    parser.add_option("--awsbucket", dest="aws_bucket", type="string", default=localsecrets.GOOGLE_METADATA_PATH, 
                      help="The name of the root (bucket) on AWS")
    parser.add_option("--outputfilebase", dest="outfilebase", type="string", default="endnoteexp", 
                      help="The name of the output file")
    

    (options, args) = parser.parse_args()
    if options.testmode:
        import doctest
        doctest.testmod()
        print ("Fini. Tests complete.")
    else:
        fs = opasFileSupport.FlexFileSystem(key=localsecrets.S3_KEY, secret=localsecrets.S3_SECRET, root=options.aws_bucket)
        path_is_root_bucket = options.bucket == options.aws_bucket
        print ("Writing EndNote data to file.")
        pep_endnote_generator(path=options.bucket, fs=fs, source_type="journal", path_is_root_bucket=path_is_root_bucket)
        pep_endnote_generator(path=options.bucket, fs=fs, source_type="video", path_is_root_bucket=path_is_root_bucket)
        print ("Finished!")

    sys.exit()
