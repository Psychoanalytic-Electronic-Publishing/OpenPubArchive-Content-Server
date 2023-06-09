data "aws_route53_zone" "pep_web" {
  name         = "pep-web.org"
  private_zone = false
}

resource "aws_route53_record" "api_alias" {
  zone_id = data.aws_route53_zone.pep_web.zone_id
  name    = var.api_domain
  type    = "A"

  alias {
    name                   = aws_lb.server.dns_name
    zone_id                = aws_lb.server.zone_id
    evaluate_target_health = true
  }
}
