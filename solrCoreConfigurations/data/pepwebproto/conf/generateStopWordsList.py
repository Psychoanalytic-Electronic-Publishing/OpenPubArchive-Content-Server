"""Simple program to output stopwords for Solr in multiple languages for PEP-Web.

   First version 2015-05-15 nrs

"""

from stop_words import get_stop_words
import io

stopWords = get_stop_words('en')
stopWords += get_stop_words('german')
stopWords += get_stop_words('french')
stopWords += get_stop_words('italian')
stopWords += get_stop_words('spanish')
print "%s stopwords loaded!" % len(stopWords)

fp = io.open("./generatedStopwordList.txt", "w", encoding='utf-8')

for n in stopWords:
    fp.write(n + u'\n')

fp.close()
print "Finished!"

#from stop_words import safe_get_stop_words

#stop_words = safe_get_stop_words('german')