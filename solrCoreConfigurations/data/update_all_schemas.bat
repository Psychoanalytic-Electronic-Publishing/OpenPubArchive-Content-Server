c:
cd C:\solr-8.0.0\server\solr
rem can't do this because the script fails when there are no solr instances running.  Just do it manually
rem solr stop -all
rem use paths rather than wildcards just to be careful

del pepwebdocs\conf\managed-schema
del pepwebrefs\conf\managed-schema
del pepwebauthors\conf\managed-schema
del pepwebglossary\conf\managed-schema

copy pepwebdocs\conf\masterPEPWebDocsSchema.xml pepwebdocs\conf\schema.xml
copy pepwebrefs\conf\masterPEPWebRefsSchema.xml pepwebrefs\conf\schema.xml
copy pepwebauthors\conf\masterPEPWebAuthorsSchema.xml pepwebauthors\conf\schema.xml
copy pepwebglossary\conf\masterPEPWebGlossarySchema.xml pepwebglossary\conf\schema.xml

echo Now start Solr and let Solr create the managed-schema
timeout /t 5
