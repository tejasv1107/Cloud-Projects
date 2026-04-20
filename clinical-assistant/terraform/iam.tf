# ============================================================
# IAM Role for Bedrock Knowledge Base
# ============================================================
resource "aws_iam_role" "bedrock_kb" {
  name = "${local.name_prefix}-bedrock-kb-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "bedrock.amazonaws.com"
      }
      Action = "sts:AssumeRole"
      Condition = {
        StringEquals = {
          "aws:SourceAccount" = local.account_id
        }
        ArnLike = {
          "aws:SourceArn" = "arn:aws:bedrock:${var.aws_region}:${local.account_id}:knowledge-base/*"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "bedrock_kb_model" {
  name = "bedrock-model-access"
  role = aws_iam_role.bedrock_kb.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["bedrock:InvokeModel"]
      Resource = [
        "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.embedding_model_id}"
      ]
    }]
  })
}

resource "aws_iam_role_policy" "bedrock_kb_s3" {
  name = "s3-docs-access"
  role = aws_iam_role.bedrock_kb.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:ListBucket"]
        Resource = [aws_s3_bucket.kb_docs.arn]
      },
      {
        Effect = "Allow"
        Action = ["s3:GetObject"]
        Resource = ["${aws_s3_bucket.kb_docs.arn}/*"]
      }
    ]
  })
}

resource "aws_iam_role_policy" "bedrock_kb_aoss" {
  name = "aoss-access"
  role = aws_iam_role.bedrock_kb.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["aoss:APIAccessAll"]
      Resource = [aws_opensearchserverless_collection.kb.arn]
    }]
  })
}

# EC2 IAM role is not managed by Terraform since the user is using
# a pre-existing EC2 instance. The IAM user/role being used on the EC2
# needs bedrock:InvokeModel, bedrock:Retrieve, bedrock:RetrieveAndGenerate
# permissions - see docs/ec2-iam-policy.json for the required policy.
