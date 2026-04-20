variable "aws_region" {
  description = "AWS region - use us-east-1 for widest Bedrock model availability"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "clinical-asst"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "my_ip_cidr" {
  description = "Your public IP in CIDR format (unused now EC2 is external, kept for flexibility)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "embedding_model_id" {
  description = "Bedrock embedding model for KB"
  type        = string
  default     = "amazon.titan-embed-text-v2:0"
}
