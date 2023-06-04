"""Simple program to output Thesaurus for Solr from our original Thesaurus input file PEP-Web.

   First version 2015-05-15 nrs

"""

import io

textOut = ""

with io.open(r"X:\_Design\Thesaurus\final PEP thesaurus file.csv", 'r', encoding='utf8') as fi:
    text = fi.readlines()

thesDict = {}

for n in text:
    parsed = n.split(",")
    #Make a dictionary of it
    try:
        thesDict[parsed[0]].append(parsed[1])
    except KeyError:
        thesDict[parsed[0]] = [parsed[1]]

fi.close()

outText = ""
countLines = 0

for key, equivList in thesDict.items():
    outLine = key + ","
    outLine += ",".join(equivList) + "\n"
    outText += outLine
    countLines += 1

# process Unicode text

with io.open(r".\PEPSolrThesaurus.txt", 'w', encoding='utf8') as fo:
    fo.write(outText)

fo.close()

print ("Finished!  %s thesaurus lines written to output file." % countLines)
