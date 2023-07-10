locals {
  config_sha1                   = sha1(join("", [for f in fileset(path.cwd, "../../app/config/*") : filesha1(f)]))
  libs_sha1                     = sha1(join("", [for f in fileset(path.cwd, "../../app/libs/*") : filesha1(f)]))
  opasDataLoader_sha1           = sha1(join("", [for f in fileset(path.cwd, "../../app/opasDataLoader/*") : filesha1(f)]))
  opasDataUpdateStat_sha1       = sha1(join("", [for f in fileset(path.cwd, "../../app/opasDataUpdateStat/*") : filesha1(f)]))
  opasEndnoteExport_sha1        = sha1(join("", [for f in fileset(path.cwd, "../../app/opasEndnoteExport/*") : filesha1(f)]))
  opasGoogleMetadataExport_sha1 = sha1(join("", [for f in fileset(path.cwd, "../../app/opasGoogleMetadataExport/*") : filesha1(f)]))
  opasPushSettings_sha1         = sha1(join("", [for f in fileset(path.cwd, "../../app/opasPushSettings/*") : filesha1(f)]))
  opasSiteMapper_sha1           = sha1(join("", [for f in fileset(path.cwd, "../../app/opasSiteMapper/*") : filesha1(f)]))
  fargate_sha1                  = sha1(join("", [for f in fileset(path.cwd, "../../dataUtility/*") : filesha1(f)]))
}

locals {
  container_name = "data-utility"
}
