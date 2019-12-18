rem can't do this because the script fails when there are no solr instances running.  Just do it manually
rem solr stop -all
rem use paths rather than wildcards just to be careful

del solrCoreConfigurations\data\pepwebdocs\conf\managed-schema
del solrCoreConfigurations\data\pepwebdocparas\conf\managed-schema
del solrCoreConfigurations\data\pepwebrefs\conf\managed-schema
del solrCoreConfigurations\data\pepwebauthors\conf\managed-schema
del pepwebglossary\conf\managed-schema

copy solrCoreConfigurations\data\pepwebdocs\conf\masterPEPWebDocsSchema.xml solrCoreConfigurations\data\pepwebdocs\conf\schema.xml
copy solrCoreConfigurations\data\pepwebdocparas\conf\masterPEPWebDocParasSchema.xml solrCoreConfigurations\data\pepwebdocparas\conf\schema.xml
copy solrCoreConfigurations\data\pepwebrefs\conf\masterPEPWebRefsSchema.xml solrCoreConfigurations\data\pepwebrefs\conf\schema.xml
copy solrCoreConfigurations\data\pepwebauthors\conf\masterPEPWebAuthorsSchema.xml solrCoreConfigurations\data\pepwebauthors\conf\schema.xml
copy solrCoreConfigurations\data\pepwebglossary\conf\masterPEPWebGlossarySchema.xml solrCoreConfigurations\data\pepwebglossary\conf\schema.xml

echo Now start Solr and let Solr create the managed-schema
timeout /t 5
