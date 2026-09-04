# Bitnami retired all free AMIs from AWS on 2026-06-10 (owner 679593333241),
# so "bitnami-solr-*" no longer resolves. This instance never runs Solr -
# it only mounts EFS once via user_data and is then stopped (see
# aws_ec2_instance_state.stop below) - so use Amazon Linux 2023 via the
# SSM public parameter, which always points at the latest AMI.
data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}
locals {
  efs_mount_point = "/mnt/solr"
}

resource "aws_instance" "efs_interface" {
  ami                    = data.aws_ssm_parameter.al2023.value
  instance_type          = "t2.nano"
  vpc_security_group_ids = [aws_security_group.solr.id]
  key_name               = "${var.stack_name}-pep-${var.env}"
  subnet_id              = data.aws_subnets.private.ids[0]

  user_data = <<-EOF
                #cloud-config
                package_update: true
                package_upgrade: true
                runcmd:
                - yum install -y amazon-efs-utils nfs-utils
                - mkdir -p "${local.efs_mount_point}"
                - test -f "/sbin/mount.efs" && printf "\n${module.efs.id}:/ ${local.efs_mount_point} efs tls,_netdev\n" >> /etc/fstab || printf "\n${module.efs.id}.efs.${var.aws_region}.amazonaws.com:/ ${local.efs_mount_point} nfs4 nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport,_netdev 0 0\n" >> /etc/fstab
                - test -f "/sbin/mount.efs" && grep -ozP 'client-info]\nsource' '/etc/amazon/efs/efs-utils.conf'; if [[ $? == 1 ]]; then printf "\n[client-info]\nsource=liw\n" >> /etc/amazon/efs/efs-utils.conf; fi;
                - retryCnt=15; waitTime=30; while true; do mount -a -t efs,nfs4 defaults; if [ $? = 0 ] || [ $retryCnt -lt 1 ]; then echo File system mounted successfully; break; fi; echo File system not available, retrying to mount.; ((retryCnt--)); sleep $waitTime; done;
                EOF

  tags = {
    Name  = "${var.stack_name}-solr-efs-interface-${var.env}"
    stack = var.stack_name
    env   = var.env
  }
}

resource "aws_ec2_instance_state" "stop" {
  instance_id = aws_instance.efs_interface.id
  state       = "stopped"
}
