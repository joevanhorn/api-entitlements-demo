output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.scim_server.id
}

output "public_ip" {
  description = "Public IP address of the server"
  value       = aws_eip.scim_server.public_ip
}

output "domain_name" {
  description = "Domain name for the SCIM server"
  value       = var.domain_name
}

output "dashboard_url" {
  description = "URL for the web dashboard"
  value       = "https://${var.domain_name}"
}

output "scim_base_url" {
  description = "SCIM Base URL to configure in Okta"
  value       = "https://${var.domain_name}/scim/v2"
}

output "scim_health_url" {
  description = "Health check endpoint"
  value       = "https://${var.domain_name}/health"
}

output "ssh_command" {
  description = "SSH command to connect to the server"
  value       = "ssh ubuntu@${aws_eip.scim_server.public_ip}"
}

output "ssm_command" {
  description = "AWS Systems Manager command to connect"
  value       = "aws ssm start-session --target ${aws_instance.scim_server.id}"
}

output "log_command" {
  description = "Command to view server setup logs"
  value       = "ssh ubuntu@${aws_eip.scim_server.public_ip} 'tail -f /var/log/user-data.log'"
}

output "okta_configuration" {
  description = "Okta SCIM configuration values"
  value = {
    scim_base_url      = "https://${var.domain_name}/scim/v2"
    auth_header_name   = "Authorization"
    auth_header_value  = "Bearer ${var.scim_auth_token}"
    unique_identifier  = "userName"
  }
  sensitive = true
}
