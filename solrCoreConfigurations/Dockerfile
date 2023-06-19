FROM solr:latest

ENV SOLR_JAVA_MEM="-Xms512m -Xmx512m"

COPY data/ /var/solr/data/

USER root
RUN chown -R solr /var/solr/data
USER solr

EXPOSE 8983

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["solr-foreground"]