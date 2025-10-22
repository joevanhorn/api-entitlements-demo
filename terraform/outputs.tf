output "dashboard_url" {
  description = "URL to access the SCIM dashboard"
  value       = "https://${var.domain_name}"
}

output "scim_base_url" {
  description = "SCIM base URL for Okta configuration"
  value       = "https://${var.domain_name}/scim/v2"
}

output "public_ip" {
  description = "Public IP address of the SCIM server"
  value       = aws_eip.scim_server.public_ip
}

output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.scim_server.id
}

output "domain_name" {
  description = "Domain name for the SCIM server"
  value       = var.domain_name
}

output "ssh_command" {
  description = "SSH command to connect to the server"
  value       = var.ssh_key_name != "" ? "ssh -i ${var.ssh_key_name}.pem ubuntu@${var.domain_name}" : "SSH key not configured"
}

output "app_version" {
  description = "Current application version deployed"
  value       = var.app_version
}
