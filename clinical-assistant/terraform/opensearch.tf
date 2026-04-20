# ============================================================
# WARNING: OpenSearch Serverless minimum is 2 OCUs (~$350/month)
# Destroy this immediately after demo recording
# ============================================================

resource "aws_opensearchserverless_security_policy" "encryption" {
  name = "${local.name_prefix}-enc"
  type = "encryption"
  policy = jsonencode({
    Rules = [{
      Resource     = ["collection/${local.name_prefix}-kb"]
      ResourceType = "collection"
    }]
    AWSOwnedKey = true
  })
}

resource "aws_opensearchserverless_security_policy" "network" {
  name = "${local.name_prefix}-net"
  type = "network"
  policy = jsonencode([{
    Rules = [
      {
        Resource     = ["collection/${local.name_prefix}-kb"]
        ResourceType = "collection"
      },
      {
        Resource     = ["collection/${local.name_prefix}-kb"]
        ResourceType = "dashboard"
      }
    ]
    AllowFromPublic = true
  }])
}

resource "aws_opensearchserverless_access_policy" "kb" {
  name = "${local.name_prefix}-access"
  type = "data"
  policy = jsonencode([{
    Rules = [
      {
        Resource     = ["collection/${local.name_prefix}-kb"]
        Permission   = ["aoss:*"]
        ResourceType = "collection"
      },
      {
        Resource     = ["index/${local.name_prefix}-kb/*"]
        Permission   = ["aoss:*"]
        ResourceType = "index"
      }
    ]
    Principal = [
      aws_iam_role.bedrock_kb.arn,
      data.aws_caller_identity.current.arn
    ]
  }])
}

resource "aws_opensearchserverless_collection" "kb" {
  name = "${local.name_prefix}-kb"
  type = "VECTORSEARCH"

  depends_on = [
    aws_opensearchserverless_security_policy.encryption,
    aws_opensearchserverless_security_policy.network
  ]
}
