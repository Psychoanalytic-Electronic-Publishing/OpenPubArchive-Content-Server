c:
cd C:\solr-8.0.0\server\solr\pepwebproto\conf
rem can't do this because the script fails when there are no solr instances running.  Just do it manually
rem solr stop -all
del schema.xml
del managed-schema
copy master_pep_schema.xml schema.xml
echo Now start Solr and let Solr create the managed-schema
timeout /t 5