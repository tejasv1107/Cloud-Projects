output "kb_docs_bucket" {
  value       = aws_s3_bucket.kb_docs.id
  description = "S3 bucket for RAG source documents"
}

output "finetune_bucket" {
  value       = aws_s3_bucket.finetune.id
  description = "S3 bucket for fine-tuning data + outputs"
}

output "knowledge_base_id" {
  value       = aws_bedrockagent_knowledge_base.main.id
  description = "Pass this as KB_ID env var to the Streamlit app"
}

output "data_source_id" {
  value       = aws_bedrockagent_data_source.s3_docs.id
  description = "Use for start-ingestion-job command"
}

output "opensearch_collection_endpoint" {
  value = aws_opensearchserverless_collection.kb.collection_endpoint
}

output "next_steps" {
  value = <<-EOT

    ============================================================
    Next steps:
    ============================================================
    1. Upload RAG PDFs to the docs bucket:
         aws s3 cp guideline.pdf s3://${aws_s3_bucket.kb_docs.id}/

    2. Trigger KB ingestion:
         aws bedrock-agent start-ingestion-job \
           --knowledge-base-id ${aws_bedrockagent_knowledge_base.main.id} \
           --data-source-id ${aws_bedrockagent_data_source.s3_docs.id} \
           --region ${var.aws_region}

    3. On your existing EC2, set env vars and run:
         export KB_ID=${aws_bedrockagent_knowledge_base.main.id}
         export AWS_REGION=${var.aws_region}
         streamlit run app.py --server.address 0.0.0.0 --server.port 8501
    ============================================================
  EOT
}
