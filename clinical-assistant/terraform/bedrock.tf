# ============================================================
# Bedrock Knowledge Base (RAG)
# Note: The OpenSearch index must exist BEFORE the KB is created.
# Use the opensearch provider or create the index manually via a
# local-exec / null_resource script after the collection is ready.
# ============================================================

# Wait for OpenSearch collection + create index via null_resource
# This is a common pattern since the aws provider cannot create OpenSearch indices
resource "null_resource" "create_oss_index" {
  depends_on = [
    aws_opensearchserverless_collection.kb,
    aws_opensearchserverless_access_policy.kb
  ]

  triggers = {
    collection_id = aws_opensearchserverless_collection.kb.id
  }

  provisioner "local-exec" {
    command = <<-EOT
      python3 ${path.module}/scripts/create_oss_index.py \
        --endpoint ${aws_opensearchserverless_collection.kb.collection_endpoint} \
        --region ${var.aws_region} \
        --index-name ${local.name_prefix}-index
    EOT
  }
}

resource "aws_bedrockagent_knowledge_base" "main" {
  name     = "${local.name_prefix}-kb"
  role_arn = aws_iam_role.bedrock_kb.arn

  knowledge_base_configuration {
    type = "VECTOR"
    vector_knowledge_base_configuration {
      embedding_model_arn = "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.embedding_model_id}"
    }
  }

  storage_configuration {
    type = "OPENSEARCH_SERVERLESS"
    opensearch_serverless_configuration {
      collection_arn    = aws_opensearchserverless_collection.kb.arn
      vector_index_name = "${local.name_prefix}-index"
      field_mapping {
        vector_field   = "bedrock-knowledge-base-default-vector"
        text_field     = "AMAZON_BEDROCK_TEXT_CHUNK"
        metadata_field = "AMAZON_BEDROCK_METADATA"
      }
    }
  }

  depends_on = [null_resource.create_oss_index]
}

resource "aws_bedrockagent_data_source" "s3_docs" {
  knowledge_base_id = aws_bedrockagent_knowledge_base.main.id
  name              = "${local.name_prefix}-s3-docs"

  data_source_configuration {
    type = "S3"
    s3_configuration {
      bucket_arn = aws_s3_bucket.kb_docs.arn
    }
  }

  vector_ingestion_configuration {
    chunking_configuration {
      chunking_strategy = "FIXED_SIZE"
      fixed_size_chunking_configuration {
        max_tokens         = 512
        overlap_percentage = 20
      }
    }
  }
}
