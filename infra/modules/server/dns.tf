data "aws_route53_zone" "video_previews" {
  name         = "pep-web.org"
  private_zone = false
}

resource "aws_route53_record" "assets_alias" {
  zone_id = data.aws_route53_zone.video_previews.zone_id
  name    = "test.pep-web.org"
  type    = "A"

  alias {
    name                   = aws_lb.server.dns_name
    zone_id                = aws_lb.server.zone_id
    evaluate_target_health = true
  }
}
