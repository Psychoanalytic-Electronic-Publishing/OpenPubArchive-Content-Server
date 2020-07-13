

# Setup a Solr instance. The timeout is optional.
# #TODO
# switched from pysolr to solrpy for authentication feature...but solrpy has a few bugs and doesn't
# seem to be updated anymore.  And pysolr is, and works, per usage in solrXMLWebLoad.py.  So perhaps
# this should be switched back.
# solr = pysolr.Solr('http://localhost:8983/solr/pepwebproto', timeout=10)
# This is the old way -- should switch to class Solr per https://pythonhosted.org/solrpy/reference.html
#
#from solrq import Q
import solrpy as solr
# import opasConfig
from localsecrets import SOLRUSER, SOLRPW, SOLRURL

# These are the solr database names used
SOLR_DOCS = "pepwebdocs"
# SOLR_DOCPARAS = "pepwebdocparas"  # For testing workaround for paragraph search
# SOLR_REFS = "pepwebrefs"
SOLR_AUTHORS = "pepwebauthors"
SOLR_GLOSSARY = "pepwebglossary"

if SOLRUSER is not None:
    solr_docs = solr.SolrConnection(SOLRURL + SOLR_DOCS, http_user=SOLRUSER, http_pass=SOLRPW)
    solr_docs_term_search = solr.SearchHandler(solr_docs, "/terms")
    #not used anymore
    #solr_refs = solr.SolrConnection(SOLRURL + opasConfig.SOLR_REFS, http_user=SOLRUSER, http_pass=SOLRPW)
    solr_gloss = solr.SolrConnection(SOLRURL + SOLR_GLOSSARY, http_user=SOLRUSER, http_pass=SOLRPW)
    solr_authors = solr.SolrConnection(SOLRURL + SOLR_AUTHORS, http_user=SOLRUSER, http_pass=SOLRPW)
    solr_authors_term_search = solr.SearchHandler(solr_authors, "/terms")
    solr_like_this = solr.SearchHandler(solr_authors, "/mlt")

else:
    solr_docs = solr.SolrConnection(SOLRURL + SOLR_DOCS)
    solr_docs_term_search = solr.SearchHandler(solr_docs, "/terms")
    #not used anymore
    #solr_refs = solr.SolrConnection(SOLRURL + opasConfig.SOLR_REFS)
    solr_gloss = solr.SolrConnection(SOLRURL + SOLR_GLOSSARY)
    solr_authors = solr.SolrConnection(SOLRURL + SOLR_AUTHORS)
    solr_authors_term_search = solr.SearchHandler(solr_authors, "/terms")

# define cores for ExtendedSearch
EXTENDED_CORES = {
    "pepwebdocs": solr_docs,
    "pepwebgloss": solr_gloss,
    "pepwebauthors": solr_authors,
    "pepwebauthors_terms": solr_authors_term_search,
}
