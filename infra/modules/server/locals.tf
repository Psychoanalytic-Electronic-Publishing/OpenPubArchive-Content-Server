locals {
  app_sha1        = sha1(join("", [for f in fileset(path.cwd, "../../app/**") : filesha1(f)]))
  dockerfile_sha1 = filesha1("../../Dockerfile")
}

locals {
  content_hash = substr(sha1("${local.app_sha1}-${local.dockerfile_sha1}-${data.aws_s3_object.localsecrets.etag}"), 0, 8)
  image_tag = "server-${local.content_hash}"
  container_name = "server"
}
