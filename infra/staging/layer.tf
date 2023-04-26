data "archive_file" "zip_source" {
  type        = "zip"
  source_dir  = "../app"
  output_path = "opas.zip"
}

resource "null_resource" "build_libs_package" {
  triggers = {
    src_hash = "${data.archive_file.zip_source.output_sha}"
  }

  provisioner "local-exec" {
    working_dir = "../app"
    command     = <<-EOT
      mkdir python
      cp -r libs/ python/
      cp ../requirements.txt python/
      cd python
      pip install -r requirements.txt -t .
      cd ..
      zip -r libs-package.zip python/
      rm -rf python/
    EOT
  }
}

module "libs_lambda_layer" {
  depends_on = [
    null_resource.build_libs_package,
  ]

  source = "terraform-aws-modules/lambda/aws"

  create_package          = false
  ignore_source_code_hash = true
  create_layer            = true

  layer_name          = "opas-libs-${var.env}"
  description         = "OPAS libs and Python deps"
  compatible_runtimes = ["python3.7"]

  local_existing_package = "../app/libs-package.zip"
}
