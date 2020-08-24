
## OpenPubArchive - Open Publications Archive Software (OPAS) Change log

**2020.0823** - Implemented CRUD code for new ClientConfiguration endpoints. Built tests.
           
- Note: despite using client_id as header variable, the actual variable should be client-id.
- Fixed an error trapping bug in MostCited where an error occurs, and e.reason is None, which caused it's own error.

**2020.0821** - Error trapping work.  TermCounts now checks the field against the schema to see that
          it exists, and gives an exception if not.
		  
    Example:
       GET /v2/Database/TermCounts/?termlist=mother&termfield=textme HTTP/1.1" 400 Bad Request

**2020.0820** - Finished draft implementation of access checks with PaDS.  

- This now checks for all returned documentListItem data in a search; the goal is to allow the client to know in advance what items the user can view in full-text.
           
- For endpoints that return documentListItems (search based), and where indicated, if the caller requests a limit above the server setting for opasConfig.MAX_LIMIT_SETTING_FOR_ACCESS_INFO_RETURN (default = 100)  individual document permissions in the return set will not be checked  or returned in the document item records.  
	- This will speed up cases where  a large number of records are retrieved, for example, to build a summary table of most cited or most viewed articles.  If the request would return full-text however, the document access settings are always checked and accessLimited fields  will be included in the return set.

**2020.0819** - Added Administrative Global config settings endpoints for the client app
           
- Fixed mostcited and mostviewed endpoints, which were not updated to the search_text_qs  calls and were not incorporating all the parameters (noteably text)
- Updated calls to solr to route Documents and Abstracts directly through the newer search_text_qs call.  
- prep_document_download still calls Solr directly for now.Fixed full document hits in context, which were missing because it's necessary to increase the hl.fragment size when looking to pull up HIC for the document...and that parameter wasn't getting set correctly in the changeover.

**2020.0818** - Header values now accepted:
- apimode = debug (adds extra data for diagnostic purposes)
- client-session - Session ID from client, e.g., as received by PaDS

	- For now at least, you can still use the regular login method if your account is on the server.
			client-id in the header is the API client ID, e.g., 1 for pep-easy, 2 for the new pep-web,
			3 for pads directly.  The api_client_key is now tied to client-id (client_id in Python)
			which for now, is in localsecrets rather than the DB

- AdvancedSearch updates
    - core is now supported.
    - returnFieldSet added to solrQuerySpec.
    - returnfields in AdvancedSearch is based on the returnFieldSet
	      - it can be DEFAULT, TOC, META or None (sets as Default) 

**2020.0817** - Create new endpoint for term search

-  Change endpoints with bodies to POST
-  Remove termlist from main v2 search endpoints (eliminating the "body" issue for them)

**2020.0814** - Abstract return only when requested in search, and no longer fills in the document field with the
abstract, that was a convenience so apps could ignore abstract, but adds lots of data.

There was an error, so if the document was accesslimited, abstract always was returned,
even if not requested in the search.)

- XML return of the abstract is now supported in search, and a field is added to allow that.
- The XML is a fragment...you can add your own front matter with the documentInfoXML field which is currently always returned. Very easy to turn that and the abstract into a pepkbd3 compliant document with the returned data, and I think it's better to give the client the choice here.  (Also added to the new SmartSearch endpoint.)

**2020.0811** - Was using the PEPlib library just for locator recognition, but that was a lot of code baggage for so little, so did it in a different but even more effective way: rather than using the extensive patterns there for PEP recognition,  looks up the correctly formatted locator in the Solr index to ensure it's really a PEP locator.

**2020.0810** - Metadata volumes now uses a Solr pivot rather than the relational DB (rDB) tables.  This ensures
the data returned is in sync with the actual database (since deletions can be done in the Solr db
 don't propagate to the rDB, they can be out of sync.)

- SolrLoad now adds the source year to the biblio record table; this means the join with the articles
table isn't necessary to build the citation counts by interval.  However, the joined views are
significantly faster than the single table grouping views, so the predefined views for
vw_stat_cited_in_last_5_years, vw_stat_cited_in_last_10_years, and vw_stat_cited_in_last_20_years
still use the articles table anyway.  Note this only affects solr db loads in either case since the
query data for citations is kept in the solr docs core.

**2020.0805** - Adjustments to restrict return data for offsite articles, since those aren't allowed
to display text, and the change on 08/04 to the way they're loaded in solrxmlload now treats
them (mostly) as regular articles so they may be searched.

- Mapped search_text to search_text_qs eliminating the redundant functionality
that was due to the "evolution" in the code.
	- (search_text is parameterized, and search_text_qs uses a querySpec).

**2020.0802** - Smartsearch module candidate in place.  Passes tests, but needs user stress testing.  Likely not robust in that way.

**2020.0721** - Changed several instances of calls to Logging to module level Logger (misuse of library)

- Try a new smartsearch approach - lookup in Solr to determine
word semantics.

**2020.0718** - Initial implementation of smarttext parameter and smartsearch module

**2020.0714** - Preliminary new AWS alpha...passes all tests, but need to go through the list of scheduled
updates before finalizing.  Still, checking it in to Github.
- fix bug in mostviews, lastcalyear is 0, not 5 (now both)

**2020.0709** - Added facet return info to document and abstract return, to allow term clouds for
the current document.

**2020.0705** - Inline documentation updates

**2020.0702** - Get MoreLikeThis changed completely.  
- Now all you have to do, in more calls, is set
 similarcount > 0 and similarDocs will be included in the similarityMatch field of the results.
           
- Also, changed getAbstract code to use search_text, so you can now get MoreLikeThis for
an abstract when retrieving it.

**2020.0611** - Optimizing code...example: checking for file_classification when search_text and search_text_qs do it for you and return  only the abstract anyway.
           
- Tested masterPEPWebDocsSchema changes by regenerating local Solr database.

- Note: art_lang is now a string, not a list.  Temporary code injected to handle online case where solr database is not
yet in sync.

**2020.0611** - Added opas_version to status return.  Lucene version moved to non-admin return.

- Changed most_viewed to use new Solr data instead of database.
```
           #  Note: field names now changed to solr std:
           #
           # downloads_lastweek                art_views_lastweek
           # downloads_lastmonth               art_views_last1mos
           # downloads_last6months             art_views_last6mos
           # downloads_last12months            art_views_last12mos
           # downloads_lastcalyear             art_views_lastcalyear
           # 
```
- Switching most (if not all) calls from search_text to search_text_qs which uses solrQuerySpec as the input model rather than parameters.  Note it's important for hl_fragsize to be set properly!
           
- Removed need to enter old password to change password--this is admin only function (and for 'stage' really)

**2020.0610** - Reconsidering child method for paras; slight advantage in search for long paras; very big complications for general querying though.  May not be worth it.  Reading in para context elements at top level.  For testing, we'll offer both methods of search.        
 
- Added abstract parameter to search endpoints, to request that abstracts are returned with
results.  Prior to this, you had to do a documents/abstract call to get the abstract for any
doc.

**2020.0609** - Working on Problems with the way termlist query is implemented handling mixed level query

**2020.0608** - Fix passthrough of requested document format (was being ignored)

- Added case insensitivity to format (though must all be same case, not mixed)

**2020.0604** - fixes to extended because returnfields was moved to solrqueryspec.

- constrained extended core selection to predefined cores in opasconfig (dev in progress)
faceting mincount added and defaulted to 1

**2020.0602** - fixes to v1 endpoints to work properly with the current alpha of PEP-Easy

- (added back in datetype, and handled special before case)
- Set search_analysis_v1 to return term list, making it a requirement that
any v1 UI would need a change, but that really only means PEP-Easy, which has
been adjusted in other ways anyway.

**2020.0601** - Added art_views_* to stat field returned in documentListItems (and of course to the standard list of fields 
returned by Solr for all but ExtendedSearch).

**2020.0530** - Fix to format of datetimechar in api_docviews.  Pysql was complaining about the utc format I was saving.
- Abstract views are no longer logged as docviews since we don't count them and they add a lot of rows to the table.
- Finished implementing PDFOriginal download feature (was not fully built).  Tested, working ok.
- TestDownload succeeds, must run the full test since test_1 ... depends on test_0_login.
- In the process of uploading full set to S3.

**2020.0527** - Added AdvancedQuery methods to specify SolrQuerySpec to API as a Request Body Parameter, and allow 
the individual query parameters to the arguments in SolrQuerySpec.  I thought this might be useful
to do in the other calls, but really, the other calls take the query parameters and build the
SolrQuerySpec for the caller; SolrQuerySpec is more for entering the primary Solr Query and Filter specs
directly.

**2020.0506** - Added some additional types to document item return (and models) that I had
           #   assumed would be ok for clients to get from the XML or Sourceinfo, but
           #   in fact, for producing a list of results, that could be desirable to have
           #   in the document info returned at the article level.
           # Also: Starting to add parameter checks.  I decided it's beneficial
           #   for the server to return an error rather than 0 results if one of the parameters
           #   is not specified correctly.
           # Along with that, added norm_val which will allow some parameters to be
           #   shortened to the minimum unique letters, for example, journals, books videos
           #   as j, b, v.  The advantage is that if the mininum is met, the client could
           #   get the rest of the letters wrong, and it will work.
           # Added testing for the above.
           # Still more of the above to do.

**2020.0505** - Cleaning up parameters, and starting to work on normalization and documentation
           - Moved opasConfig.py to config folder from libs.  Makes more sense.

**2020.0504** Added core to the new endpoint WordWheel and updated documentation for it
           - Settings for cores moved to config_cores, currently in under lib/configLib
           -   perhaps this would be good to get into the config folder (some trouble trying)

**2020.0503** Found error when issuing meta call for sources when pepcode was missing for a book
           # in the api_productbase table.  Fixed it (and missing data for IPL) and created a test
           # test_8b2_meta_all_sources to check all the source codes.
           - Also: documentID wasn't being filled in due to error in the dict lookup.  Fixed.

**2020.0502** Added endpoint WordWheel and supporting function in opasAPISupportLib to collect
           # a termlist from specified field.  Uses solr.SearchHandler(solr_docs, "/terms")

**2020.0430** Added a sort clause to the database query behind the metadata/volume return so
           # the data comes back better organized.
           - Fixed it so metadata/sourcetype/sourcecode gets everything if you use * for each

**2020.0423** Changed excerpting in SolrXMLPEPWebLoad to remove words in the trailing sentence 
of the excerpt to the preceding punctuation mark. Excluding ", which does mean 
sometimes there's an unclosed quote at the end of a sentence ending in .", but
the alternative was worse, since it left fragments where the quote wasn't at the
end of the sentence.

The limits which determine excerpt size can be configured in OpasConfig.
```
MIN_EXCERPT_CHARS = 480
MAX_EXCERPT_CHARS = 2000
MAX_EXCERPT_PARAS = 10
```
Min means it will even go past a pb if there are less chars than 480.

**2020.0419**  Fixed endpoint function names to match endpoints (easier to find when programming) 
           Added endpoint summary to replace what the descriptive function names were doing

           - A few bug fixes.
           - Added facet return in responseInfo if facefields specified in endpoint params 
             or SolrQuery input.

**2020.0418**  More fixes to parse_search_query_parameters() regarding sort
           and a solr query param which was offset=0 rather than start=offset
           in database_get_whats_new()

**2020.0417**  Added API_KEY code, only applied to documentation functions now, and mainly as an
           example, since docs is not marked as protected right now.

           BasicLogin is now working.  Extracted common setup after login code
           to login_setup_user_session, so next it can be moved to other login endpoints.

**2020.0408**  Changes to fix bug and complete implementation (it wasn't fully implemented).
           Added endpoint for openAPI (will add key next)
           All tests pass (though need more tests!)

**2020.0401**  In opasAPISupportLib.py lib: 

             Set it so user-agent is optional in session settings, in case client doesn't supply 
             it (as PaDS didn't)

**2020.0330**   Updates to endpoint documentation headers for live documentation

            /v2/Database/TermCounts

**2020.0325**   Removed deprecated response_model_skip_defaults and replaced with 
            response_model_exclude_unset per FastAPI change to be consistent with
            pydantic

**2020.0318**   Add new endpoints which may be temporary convenience functions because
            we will be moving authentication and authorization to another separate
            API server (e.g., PaDS).  But these will allow me to more easily manage 
            subscriptions in the meanwhile.

            Added:
			
                /v2/Admin/ChangeUserPassword/
				
                /v2/Admin/SubscribeUser/
				
            Tested database with RDS/MySQL and it's working as configured.

**2020.0314**   Removed journal paran min length of 2, since sometimes it's empty!

2020.0313   Updated schemaMap.py to include p_bib for biblios

### Alpha       Released as Alpha3

**2020.0311.1** Setup html conversion to substutute current server domain + api call
            for image src.  Changed xslt file as well.
             

**2020.0222.1** Fix for PDF downloads, document declaration was causing errors and .
            utf char conversions which caused errors.
            
			Also added running head and copyright notice.
            
			Still needs css formatting applied and banner if
            we want it (path issue right now)

**2020.0215.1** Partial fix for nested pb in files, like Bion, W. R. (1962).  Those were showing complete data when an excerpt (it has no abstract) was being generated.
            
			solved by an excerpting XSLT file which gets rid of the p tags and all other tags other than the pb, then translates to html.
            
			But this translation needs a lot more work due to lack of formatting (and perhaps more.)
            
			TODO MORE

**2020.0114.1** Fixed problem with Documents/Documents on a secondary request, added check there with embargo and authentication info.

**2020.0113.1** Changed timestamp to file_last_modified in get_what's new so it's not just when the file is uploaded, but rather when it's edited (processed)
            
			updated endpoint documentation

            Added code to search_text so (abstract_xml, summaries_xml, and text_xml) are only returned when abstract_requested is set, and only text_xml from
            that set is returned when just full_text_requested is set in the call to search_text.
            
			Added parameters to most downloaded to meet PEP-Web like functionality for filtering.  Note that you can't do most downloaded with Solr data, only
            with the mySQL recording of downloads.
            

**2020.0112.1** Added Glossary search convenience function
            
			Finished endpoint constant names
            
			Changed query parameters journal to sourcecode for v2 endpoints
            
			Added sourcetype to endpoints.  An easier way to specify all books, videos, or journals.  Was already in database.

**2020.0111.1** Endpoint parameter documentation changed to 'constant' names from opasConfig

**2020.0108.1** - Fixed accesslimited return values, and optimized columns in search_text by adding a param for requesting full-text or abstracts.  When abstracts aren't needed, neither is full-text.  Saves a lot of time when returning 25 or more search results!
             
	- TODO: What to do about the new multiple "routes" and complex query generation for marking hits in a document?                    
		- Option 1: Allow those routes in the Doc routine so it's just up to the client to send whatever back.  That's essentially what's currently done via the Search URL param.  The client has the record of what was sent.

**2020.0107.1** - Reorganized the schema and models for clarity. Still thinking about renaming all the art_ prefixed schema elements to doc_.
- Fixed interaction with PEP-Easy by properly filling out the accesslimited model attributes
               
- Added p_ to all parent_tag names because the marking engine was picking up those names from the query
and marking them when found in text.  So for example Doc is not a good name anymore.  Prefixed all
with p_ and that shouldn't match anywhere
               
- Although the original goal was to implement the v1 API, that tied my hands and made the code less
manageable in the long run.  So I decided to remmove any V1 API feature (endpoint or parameter) that wasn't used by PEPEasy,
               
- I have kept some unused endpoints though because I think they have vakue in v2.
               
- To make it clear to the vendors bidding on the Client project what the "best/future" API is, I created
a v2 for every v1 endpoint, and other than leaving v1 endpoints in a v1 category, all the other endpoint
groups now refer to v2.
               
- Added preliminary functions to allow friendly names for parent tags.  The API converts them to the p_ equivalent
  and converts the p_ equiv. back to friendly names for query analysis display.  This also allows
  multiple names to be substituted for a friendly name.  For example:
  doc is now translated to a group of three tags (the doc is everything but the references.
  Here's the current list:
```
                     "doc" : "(p_body OR p_summaries OR p_appxs)",
                     "headings": "(p_heading)",
                     "quotes": "(p_quote)",
                     "dreams": "(p_dream)",
                     "poems": "(p_poem)",
                     "notes": "(p_note)",
                     "dialogs": "(p_dialog)",
                     "panels": "(p_panel)",
                     "captions": "(p_captions)",
                     "biblios": "(p_bib)",
                     "appendixes": "(p_appxs)",
                     "summaries": "(p_summaries)",
```
			It's not certain yet, whether we can keep this feature.

**2020.0103.1** - fixed session_id cookie for non-logged in users
              
- Added experimental body parameter to allow field level specification of query.  Not sure
that will work out because the url parameter search is needed to communicate the last query to doc retrieval with
hits marked (the server repeats the search)

**2019.1231.1** - Fixed journal logo case of logo suffix to Logo to match files in xslt file.  Also, there was a .logo where sent back to the client which is wrong.

- added db url for admins in status
			   
- fixes to query analysis and terms
			   
- fixes to solrXMLPEPWebLoad programs to allow tunneling for remote SQL server (or Bitnami SQL install)

**2019.1229.1** - Tested and corrected termcounts endpoint.
- Updated status to give more server info for the admin.

**2019.1227.1** - Image config S3 work for the production system.

**2019.1222.1** - Added v2 endpoints:
               
- termcount endpoint
               
- advancedsearch
			   
- search (replaced v1 search with more minimal one matching pepEasy requirements)
               
- update v2 search as a more general (and yet more optimized search)

**2019.1221.1** - pepwebdocs Schema optimization pass 2.  Needs a pass 3!

**2019.1220.1** - pepwebdocs Schema added nested documents, supporting schema changes.

**2019.1214.1** - Added experimental "prefix switches" to opasQueryHelper to allow proximity selection via "p>" (or now just "p " at the beginning of string.

**2019.1213.1** - Added S3 access via s3fs library - working well for images.  Downloads still needs work because
               while it downloads, it doesn't trigger browser to download to user's choice of locations.

**2019.1207.1** - Search analysis reenabled and being tested...may be problems from pepeasy

**2019.1205.1** - Added opasQueryHelper with QueryTextToSolr to parse form text query fields and translate to Solr syntax

**2019.1204.3** - modified cors to use regex opion. Define regex in localsecrets CORS_REGEX

**2019.1204.1** - modified cors origin list to try *. instead of just . origins [didn't work]

**2019.1203.1** - authentication parameter default (None) error slipped in!  But important, it blocked abstracts showing.

**2019.1202.2** - Fixed text_server_ver return

**2019.1202.1** - Fixed password encoding for create user. Parameterized some settings.
              
- Tuned mostcited to retrieve fewer records which is what was making it slow.
           
- Continued working on term search fixes...not done! #TODO

**2019-1128.1** - Added SSH support to allow communicating with AWS mySQL offsite.

**2019.1130.1** - Updated FastAPI/Starlette/Pydantic.  Removed EmailStr import which was just there to prevent warnings on older versions.
                - Added additional fields, some admin only, to get_server_status (now shows versions)
           
**2019.1019.1** - This and the other modules have now been (mostly) converted from camelCase to snake_case
for the sake of other Python programmers using the source.  This does lead to some consistency issues, because you do end up with a mix of camelCase given the API and some libraries using it.  I'm not a big fan of snake_case but trying to do it in the most consistent way possible :)

**2019.0904.1** - Started conversion to snake_case...

**2019.0816.1** - Figured out that I need to return the same model in case of error. 
               Responseinfo has errors which is a struct with error messages.
               Setting resp.status_code returns the error code.
 
               EXAMPLE in get_the_author_index_entries_for_matching_author_names
                       Returns the error correctly when Solr is not running.
                       USE THAT AS A TEMPLATE.

               TODO: This now needs to be done to each end point.

**2019.0617.4** - Changed functions under decorators to snake case since the auto doc uses those as sentences!

**2019.0617.1** - First version with 6 endpoints, 5 set up for Pydantic and one not yet converted - nrs
