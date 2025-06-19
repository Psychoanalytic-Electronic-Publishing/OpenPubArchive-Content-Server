locals {
  dockerfile_sha1 = filesha1("../../solrCoreConfigurations/Dockerfile")
  container_name = "solr-${var.build_id}"
}
