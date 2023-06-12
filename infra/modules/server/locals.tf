locals {
  app_sha1        = sha1(join("", [for f in fileset(path.cwd, "../../app/*") : filesha1(f)]))
  dockerfile_sha1 = filesha1("../../Dockerfile")
}

resource "random_uuid" "container" {
  keepers = {
    localsecrets_etag = data.aws_s3_object.localsecrets.etag
    app_sha1          = local.app_sha1
    dockerfile_sha1   = local.dockerfile_sha1
  }
}

locals {
  container_name = "server-${random_uuid.container.result}"
}
