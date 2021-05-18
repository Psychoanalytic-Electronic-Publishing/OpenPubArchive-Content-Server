#!/bin/sh

cp solrCoreConfigurations/data/pepwebdocs/conf/masterPEPWebDocsSchema.xml solrCoreConfigurations/data/pepwebdocs/conf/schema.xml
cp solrCoreConfigurations/data/pepwebauthors/conf/masterPEPWebAuthorsSchema.xml solrCoreConfigurations/data/pepwebauthors/conf/schema.xml
cp solrCoreConfigurations/data/pepwebglossary/conf/masterPEPWebGlossarySchema.xml solrCoreConfigurations/data/pepwebglossary/conf/schema.xml
echo "Done!"

