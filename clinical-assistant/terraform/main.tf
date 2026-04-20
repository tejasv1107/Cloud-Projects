terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
    opensearch = {
      source  = "opensearch-project/opensearch"
      version = "~> 2.2"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project   = "clinical-assistant"
      Owner     = "jotaro"
      ManagedBy = "terraform"
      CostCenter = "bits-assignment"
    }
  }
}

data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  name_prefix = "${var.project_name}-${var.environment}"
}
