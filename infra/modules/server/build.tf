resource "null_resource" "build_server_image" {
  triggers = {
    content_hash = local.content_hash
  }

  provisioner "local-exec" {
    working_dir = "../../"
    command     = <<-EOT
      aws s3 cp s3://pep-configuration/${var.env}/localsecrets.py app/config/localsecrets.py
      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${var.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com
      if aws ecr describe-images --repository-name=${var.repository_name} --image-ids=imageTag=${local.image_tag} --region ${var.aws_region} 2>/dev/null; then
        echo "Image ${local.image_tag} already exists in ECR, skipping build"
      else
        echo "Building new image ${local.image_tag}"
        docker build --platform linux/amd64 \
          --label "build_id=${var.build_id}" \
          --label "content_hash=${local.content_hash}" \
          -t ${local.image_tag} -f ./Dockerfile .
        docker tag ${local.image_tag} ${var.repository_url}:${local.image_tag}
        docker push ${var.repository_url}:${local.image_tag}
        
        # Also tag with BUILD_ID for reference
        docker tag ${local.image_tag} ${var.repository_url}:build-${var.build_id}
        docker push ${var.repository_url}:build-${var.build_id}
      fi
      rm -rf app/config/localsecrets.py
    EOT
  }
}
