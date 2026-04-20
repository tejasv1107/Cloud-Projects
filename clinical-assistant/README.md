# Clinical Documentation Assistant

## Overview

AI-powered clinical documentation assistant with three NLP sub-tasks unified around healthcare workflows:

1. **Text Summarization** — Compare base Claude Haiku 4.5 vs fine-tuned Nova Micro on clinical notes
2. **Named Entity Recognition** — Extract medications, conditions, procedures, vitals as structured JSON
3. **Retrieval-Augmented Q&A** — Answer questions grounded in indexed CDC/WHO/NIH medical guidelines

**Domain:** Healthcare · **Category:** NLP · **Platform:** Amazon Bedrock

## Architecture

![alt text](<API Assignment.drawio (1).png>)

## Tech Stack

| Layer | Technology |
|-------|------------|
| Reasoning + RAG generation | Claude Haiku 4.5 |
| Fine-tuning target | Amazon Nova Micro |
| Embeddings | Titan Text Embeddings V2 |
| Vector store | OpenSearch Serverless |
| RAG orchestration | Bedrock Knowledge Bases |
| Frontend | Streamlit |
| Compute | EC2 t3.medium |
| IaC | Terraform |

## Project Structure

```
clinical-assistant/
├── terraform/              # Infrastructure as Code
│   ├── main.tf
│   ├── s3.tf
│   ├── iam.tf
│   ├── opensearch.tf
│   ├── bedrock.tf
│   ├── ec2.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── scripts/
│       └── create_oss_index.py
├── app/                    # Streamlit application
│   ├── app.py
│   └── requirements.txt
├── finetune/               # Fine-tuning pipeline
│   ├── prepare_dataset.py  # MTSamples → Nova JSONL
│   ├── run_finetune.py     # Launch Bedrock customization job
│   └── manage_throughput.py # Create/delete Provisioned Throughput
├── RUNBOOK.md              # Step-by-step execution guide
└── README.md
```

## Quick Start

See `RUNBOOK.md` for detailed steps.

```bash
# 1. Deploy infrastructure
cd terraform
terraform init && terraform apply

# 2. Upload RAG documents
aws s3 cp guidelines.pdf s3://$(terraform output -raw kb_docs_bucket)/

# 3. Trigger KB ingestion
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id $(terraform output -raw knowledge_base_id) \
  --data-source-id $(terraform output -raw data_source_id)

# 4. SSH to EC2, run streamlit
# 5. Fine-tune (see finetune/)
```

## Datasets

- **MTSamples** — https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions (free, fine-tuning)
- **CDC Guidelines** — https://www.cdc.gov/ (PDFs for RAG)
- **WHO Publications** — https://www.who.int/publications (PDFs for RAG)

## Cost

**Expected: $45-75** for a complete execution cycle with careful cleanup.

