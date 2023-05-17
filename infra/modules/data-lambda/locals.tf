locals {
  config_sha1                   = sha1(join("", [for f in fileset(path.cwd, "../../app/config/*") : filesha1(f)]))
  libs_sha1                     = sha1(join("", [for f in fileset(path.cwd, "../../app/libs/*") : filesha1(f)]))
  opasDataLoader_sha1           = sha1(join("", [for f in fileset(path.cwd, "../../app/opasDataLoader/*") : filesha1(f)]))
  opasDataUpdateStat_sha1       = sha1(join("", [for f in fileset(path.cwd, "../../app/opasDataUpdateStat/*") : filesha1(f)]))
  opasEndnoteExport_sha1        = sha1(join("", [for f in fileset(path.cwd, "../../app/opasEndnoteExport/*") : filesha1(f)]))
  opasGoogleMetadataExport_sha1 = sha1(join("", [for f in fileset(path.cwd, "../../app/opasGoogleMetadataExport/*") : filesha1(f)]))
  opasPushSettings_sha1         = sha1(join("", [for f in fileset(path.cwd, "../../app/opasPushSettings/*") : filesha1(f)]))
  opasSiteMapper_sha1           = sha1(join("", [for f in fileset(path.cwd, "../../app/opasSiteMapper/*") : filesha1(f)]))
  lambda_sha1                   = sha1(join("", [for f in fileset(path.cwd, "../../lambda/data-utility/*") : filesha1(f)]))
  dockerfile_sha1               = filesha1("../../lambda/Dockerfile")
  name                          = "${var.stack_name}-data-lambda-${var.env}"
}

resource "random_uuid" "container" {
  keepers = {
    localsecrets_etag             = data.aws_s3_object.localsecrets.etag
    config_sha1                   = local.config_sha1
    libs_sha1                     = local.libs_sha1
    opasDataLoader_sha1           = local.opasDataLoader_sha1
    opasDataUpdateStat_sha1       = local.opasDataUpdateStat_sha1
    opasEndnoteExport_sha1        = local.opasEndnoteExport_sha1
    opasGoogleMetadataExport_sha1 = local.opasGoogleMetadataExport_sha1
    opasPushSettings_sha1         = local.opasPushSettings_sha1
    opasSiteMapper_sha1           = local.opasSiteMapper_sha1
    lambda_sha1                   = local.lambda_sha1
    dockerfile_sha1               = local.dockerfile_sha1
  }
}

locals {
  container_name = "data-lambda-${random_uuid.container.result}"
}
