# now loading this separately in individual modules, so mostviewedcache and mostcitedcache are not loaded when only msgdb is needed
# it's a small amount of data anyway.
#import opasMessageLib
#msgdb = opasMessageLib.messageDB()

#import opasWhatsNewCache
#whatsnewdb = opasWhatsNewCache.whatsNewDB()

#import opasCacheMostViewed
#mostviewedcache = opasCacheMostViewed.mostViewedCache()

#import opasCacheMostCited
#mostcitedcache = opasCacheMostCited.mostCitedCache()