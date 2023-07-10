locals {
  app_sha1        = sha1(join("", [for f in fileset(path.cwd, "../../app/**") : filesha1(f)]))
  dockerfile_sha1 = filesha1("../../Dockerfile")
}

locals {
  container_name = "server"
}
