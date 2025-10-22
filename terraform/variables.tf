variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "demo"
}

variable "domain_name" {
  description = "Domain name for SCIM server (e.g., demo.yourdomain.com)"
  type        = string
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID for your domain"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "scim_auth_token" {
  description = "SCIM authentication bearer token"
  type        = string
  sensitive   = true
  default     = "demo-token-12345"
}

variable "ssh_key_name" {
  description = "Optional SSH key pair name for EC2 access"
  type        = string
  default     = ""
}

variable "allowed_ssh_cidr" {
  description = "CIDR blocks allowed to SSH (0.0.0.0/0 = anywhere)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
