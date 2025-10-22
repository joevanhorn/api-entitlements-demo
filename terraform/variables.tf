variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "domain_name" {
  description = "Domain name for the SCIM server"
  type        = string
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID for the domain"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "ssh_key_name" {
  description = "SSH key pair name for EC2 access"
  type        = string
  default     = ""
}

variable "allowed_ssh_cidr" {
  description = "CIDR blocks allowed to SSH to the instance"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "scim_auth_token" {
  description = "Bearer token for SCIM authentication"
  type        = string
  sensitive   = true
}

variable "scim_basic_user" {
  description = "Basic auth username for SCIM"
  type        = string
  sensitive   = true
}

variable "scim_basic_pass" {
  description = "Basic auth password for SCIM"
  type        = string
  sensitive   = true
}

variable "app_version" {
  description = "Application version hash - used to force instance replacement when code changes"
  type        = string
  default     = "initial"
}
