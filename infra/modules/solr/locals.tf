locals {
  dockerfile_sha1 = filesha1("../../solrCoreConfigurations/Dockerfile")
}

resource "random_uuid" "container" {
  keepers = {
    dockerfile_sha1 = local.dockerfile_sha1
  }
}

locals {
  container_name = "solr-${random_uuid.container.result}"
}
