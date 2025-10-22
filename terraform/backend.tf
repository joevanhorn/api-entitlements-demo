terraform {
  backend "s3" {
    # IMPORTANT: Change this to your unique bucket name!
    bucket         = "okta-entitlements-opp"
    key            = "api-entitlements-demo/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    
    # Optional: Add DynamoDB table for state locking
    # dynamodb_table = "terraform-state-lock"
  }
  
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "API Entitlements Demo"
      Repository  = "api-entitlements-demo"
      ManagedBy   = "Terraform"
      Environment = var.environment
      Owner       = "joevanhorn"
    }
  }
}
