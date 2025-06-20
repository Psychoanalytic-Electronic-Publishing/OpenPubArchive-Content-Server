locals {
  dockerfile_sha1 = filesha1("../../solrCoreConfigurations/Dockerfile")
  content_hash = substr(sha1(local.dockerfile_sha1), 0, 8)
  image_tag = "solr-${local.content_hash}"
  container_name = "solr"
}
