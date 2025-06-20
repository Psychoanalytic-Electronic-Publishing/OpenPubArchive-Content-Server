locals {
  config_sha1                   = sha1(join("", [for f in fileset(path.cwd, "../../app/config/**") : filesha1(f)]))
  libs_sha1                     = sha1(join("", [for f in fileset(path.cwd, "../../app/libs/**") : filesha1(f)]))
  opasDataLoader_sha1           = sha1(join("", [for f in fileset(path.cwd, "../../app/opasDataLoader/**") : filesha1(f)]))
  opasDataUpdateStat_sha1       = sha1(join("", [for f in fileset(path.cwd, "../../app/opasDataUpdateStat/**") : filesha1(f)]))
  opasEndnoteExport_sha1        = sha1(join("", [for f in fileset(path.cwd, "../../app/opasEndnoteExport/**") : filesha1(f)]))
  opasGoogleMetadataExport_sha1 = sha1(join("", [for f in fileset(path.cwd, "../../app/opasGoogleMetadataExport/**") : filesha1(f)]))
  opasPushSettings_sha1         = sha1(join("", [for f in fileset(path.cwd, "../../app/opasPushSettings/**") : filesha1(f)]))
  opasSiteMapper_sha1           = sha1(join("", [for f in fileset(path.cwd, "../../app/opasSiteMapper/**") : filesha1(f)]))
  opasDatabaseArchival_sha1     = sha1(join("", [for f in fileset(path.cwd, "../../app/opasDatabaseArchival/**") : filesha1(f)]))
  fargate_sha1                  = sha1(join("", [for f in fileset(path.cwd, "../../dataUtility/**") : filesha1(f)]))
}

locals {
  content_hash = substr(sha1(join("", [
    local.config_sha1,
    local.libs_sha1,
    local.opasDataLoader_sha1,
    local.opasDataUpdateStat_sha1,
    local.opasEndnoteExport_sha1,
    local.opasGoogleMetadataExport_sha1,
    local.opasPushSettings_sha1,
    local.opasSiteMapper_sha1,
    local.opasDatabaseArchival_sha1,
    local.fargate_sha1,
    data.aws_s3_object.localsecrets.etag
  ])), 0, 8)
  image_tag = "data-utility-${local.content_hash}"
  container_name = "data-utility"
}
