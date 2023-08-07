FROM solr:latest

ENV SOLR_JAVA_MEM="-Xms512m -Xmx512m"

EXPOSE 8983

USER solr

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["solr-foreground"]