locals {
  options = {
    responses = {
      200 = {
        description = "200 response",
        headers = {
          Access-Control-Allow-Origin = {
            schema = {
              type = "string"
            }
          },
          Access-Control-Allow-Methods = {
            schema = {
              type = "string"
            }
          },
          Access-Control-Allow-Credentials = {
            schema = {
              type = "string"
            }
          },
          Access-Control-Allow-Headers = {
            schema = {
              type = "string"
            }
          }
        },
        content = {}
      }
    },
    x-amazon-apigateway-integration = {
      responses = {
        default = {
          statusCode = 200,
          responseParameters = {
            "method.response.header.Access-Control-Allow-Credentials" = "'true'",
            "method.response.header.Access-Control-Allow-Methods"     = "'OPTIONS,POST,GET'",
            "method.response.header.Access-Control-Allow-Headers"     = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent,client-session,client-id,x-pep-auth'",
            "method.response.header.Access-Control-Allow-Origin"      = "'${var.cors_origin}'"
          }
          responseTemplates = {
            "application/json" = ""
          }
        }
      },
      requestTemplates = {
        "application/json" = "{statusCode:200}"
      },
      passthroughBehavior = "when_no_match",
      contentHandling     = "CONVERT_TO_TEXT",
      type                = "mock"
    }
  }
}
