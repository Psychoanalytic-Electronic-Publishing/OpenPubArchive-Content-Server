c:
cd C:\solr-8.0.0\server\solr
rem can't do this because the script fails when there are no solr instances running.  Just do it manually
rem solr stop -all
rem use paths rather than wildcards just to be careful
rem pepwebproto\conf\schema.xml
rem pepwebrefsproto\conf\schema.xml
rem pepwebauthors\conf\schema.xml
rem pepwebglossary\conf\schema.xml

del pepwebproto\conf\managed-schema
del pepwebrefsproto\conf\managed-schema
del pepwebauthors\conf\managed-schema
del pepwebglossary\conf\managed-schema

copy pepwebproto\conf\master_pep_schema.xml pepwebproto\conf\schema.xml
copy pepwebrefsproto\conf\masterPEPRefsDbSchema.xml pepwebrefsproto\conf\schema.xml
copy pepwebauthors\conf\masterPEPWebAuthorsSchema.xml pepwebauthors\conf\schema.xml
copy pepwebglossary\conf\masterPEPWebGlossarySchema.xml pepwebglossary\conf\schema.xml

echo Now start Solr and let Solr create the managed-schema
timeout /t 5
