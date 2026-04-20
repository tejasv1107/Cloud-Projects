# Bucket for RAG source documents (medical guidelines PDFs)
resource "aws_s3_bucket" "kb_docs" {
  bucket = "${local.name_prefix}-kb-docs-${local.account_id}"
}

resource "aws_s3_bucket_versioning" "kb_docs" {
  bucket = aws_s3_bucket.kb_docs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "kb_docs" {
  bucket                  = aws_s3_bucket.kb_docs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "kb_docs" {
  bucket = aws_s3_bucket.kb_docs.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Bucket for fine-tuning datasets and output
resource "aws_s3_bucket" "finetune" {
  bucket = "${local.name_prefix}-finetune-${local.account_id}"
}

resource "aws_s3_bucket_public_access_block" "finetune" {
  bucket                  = aws_s3_bucket.finetune.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "finetune" {
  bucket = aws_s3_bucket.finetune.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
