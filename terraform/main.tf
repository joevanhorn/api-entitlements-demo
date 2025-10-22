# Data source: Latest Ubuntu 22.04 LTS AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
  
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Security Group for SCIM Server
resource "aws_security_group" "scim_server" {
  name_prefix = "scim-demo-"
  description = "Security group for SCIM entitlements demo server"
  
  # SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidr
    description = "SSH access"
  }
  
  # HTTP (redirects to HTTPS)
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP (redirects to HTTPS)"
  }
  
  # HTTPS
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS for SCIM API and dashboard"
  }
  
  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }
  
  tags = {
    Name = "scim-demo-security-group"
  }
  
  lifecycle {
    create_before_destroy = true
  }
}

# IAM Role for EC2 (allows SSM access)
resource "aws_iam_role" "scim_server" {
  name_prefix = "scim-demo-ec2-"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Name = "scim-demo-ec2-role"
  }
}

# Attach SSM policy for Session Manager access
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.scim_server.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "scim_server" {
  name_prefix = "scim-demo-"
  role        = aws_iam_role.scim_server.name
  
  tags = {
    Name = "scim-demo-instance-profile"
  }
}

# Elastic IP for stable address
resource "aws_eip" "scim_server" {
  domain = "vpc"
  
  tags = {
    Name = "scim-demo-elastic-ip"
  }
}

# EC2 Instance
resource "aws_instance" "scim_server" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = var.ssh_key_name != "" ? var.ssh_key_name : null
  vpc_security_group_ids = [aws_security_group.scim_server.id]
  iam_instance_profile   = aws_iam_instance_profile.scim_server.name
  
  # User data script for server initialization
  # IMPORTANT: app_version is included to force replacement when Python code changes
  user_data = templatefile("${path.module}/user-data.sh", {
    domain_name      = var.domain_name
    scim_auth_token  = var.scim_auth_token
    scim_basic_user  = var.scim_basic_user
    scim_basic_pass  = var.scim_basic_pass
    github_repo      = "joevanhorn/api-entitlements-demo"
    app_version      = var.app_version
  })
  
  user_data_replace_on_change = true
  
  root_block_device {
    volume_size = 8
    volume_type = "gp3"
    encrypted   = true
  }
  
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }
  
  tags = {
    Name        = "scim-demo-server"
    AppVersion  = var.app_version
  }
  
  lifecycle {
    ignore_changes = [ami]
  }
}

# Associate Elastic IP with Instance
resource "aws_eip_association" "scim_server" {
  instance_id   = aws_instance.scim_server.id
  allocation_id = aws_eip.scim_server.id
}

# Route53 DNS Record
resource "aws_route53_record" "scim_server" {
  zone_id = var.route53_zone_id
  name    = var.domain_name
  type    = "A"
  ttl     = 300
  records = [aws_eip.scim_server.public_ip]
}

# CloudWatch Log Group (optional - for future logging)
resource "aws_cloudwatch_log_group" "scim_server" {
  name              = "/aws/ec2/scim-demo"
  retention_in_days = 7
  
  tags = {
    Name = "scim-demo-logs"
  }
}
