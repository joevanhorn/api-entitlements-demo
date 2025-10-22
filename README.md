# API Entitlements Demo - SCIM Connector

A production-ready SCIM 2.0 server that demonstrates automated user provisioning and entitlements management between Okta and your cloud applications.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Okta                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  SCIM Provisioning Agent                             │  │
│  │  • Creates/Updates/Deactivates Users                 │  │
│  │  • Assigns Roles & Entitlements                      │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS (SCIM 2.0)
                         │ Basic Auth / Bearer Token
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    AWS Cloud                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Route53                                             │  │
│  │  dev.demo-entitlements-lowerdecks.com → Elastic IP   │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                   │
│  ┌──────────────────────▼───────────────────────────────┐  │
│  │  EC2 Instance (Ubuntu 22.04)                         │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  Caddy (Reverse Proxy + HTTPS)                 │  │  │
│  │  │  • Auto SSL/TLS (Let's Encrypt)                │  │  │
│  │  │  • HTTPS termination                           │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  Flask SCIM Server                             │  │  │
│  │  │  • User provisioning endpoints                 │  │  │
│  │  │  • Role/entitlements management               │  │  │
│  │  │  • In-memory data store                       │  │  │
│  │  │  • Web dashboard                              │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Features

- **SCIM 2.0 Compliant**: Full implementation of SCIM protocol for user provisioning
- **Dual Authentication**: Support for both Basic Auth and Bearer Token authentication
- **Auto HTTPS**: Automatic SSL/TLS certificate management via Let's Encrypt
- **Live Dashboard**: Real-time monitoring of provisioning activities
- **Entitlements Management**: Role-based access control with 5 pre-configured roles
- **Infrastructure as Code**: Complete Terraform automation
- **CI/CD Ready**: GitHub Actions workflow for automated deployments

## 📋 Prerequisites

### Required Accounts
- AWS Account with appropriate permissions
- GitHub account
- Okta developer/admin account (optional, for full provisioning setup)
- Anthropic API key (if using Claude Code CLI)

### Local Development Tools
- Git
- Python 3.9+
- Terraform 1.6+
- AWS CLI v2
- Node.js 18+ (for Claude Code CLI)

### Domain Requirements
- A registered domain name (managed in Route53 or transferred to Route53)
- Route53 hosted zone for your domain

---

## 🔧 Setup Instructions

### Part 1: AWS Infrastructure Setup

#### Step 1: Create AWS OIDC Provider for GitHub Actions

This allows GitHub Actions to authenticate to AWS without storing long-lived credentials.

**Via AWS Console:**

1. Go to **IAM** → **Identity Providers**
2. Click **Add provider**
3. Configure:
   - **Provider type**: OpenID Connect
   - **Provider URL**: `https://token.actions.githubusercontent.com`
   - **Audience**: `sts.amazonaws.com`
4. Click **Add provider**

**Via AWS CLI:**

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

#### Step 2: Create IAM Role for GitHub Actions

**Create Trust Policy** (`github-trust-policy.json`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_USERNAME/api-entitlements-demo:*"
        }
      }
    }
  ]
}
```

**Replace:**
- `YOUR_ACCOUNT_ID` with your AWS account ID
- `YOUR_GITHUB_USERNAME` with your GitHub username

**Create the Role:**

```bash
# Create the role
aws iam create-role \
  --role-name GitHubActions-SCIM-Deploy \
  --assume-role-policy-document file://github-trust-policy.json

# Attach necessary policies
aws iam attach-role-policy \
  --role-name GitHubActions-SCIM-Deploy \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess

# For Route53 (if using separate account/permissions)
aws iam attach-role-policy \
  --role-name GitHubActions-SCIM-Deploy \
  --policy-arn arn:aws:iam::aws:policy/AmazonRoute53FullAccess
```

**Get the Role ARN:**
```bash
aws iam get-role --role-name GitHubActions-SCIM-Deploy --query 'Role.Arn' --output text
```

Save this ARN - you'll need it for GitHub Secrets.

#### Step 3: Set Up Route53 Domain

**If you already have a domain in Route53:**

```bash
# Get your hosted zone ID
aws route53 list-hosted-zones --query 'HostedZones[*].[Name,Id]' --output table
```

**If you need to create a new hosted zone:**

```bash
aws route53 create-hosted-zone \
  --name demo-entitlements-lowerdecks.com \
  --caller-reference $(date +%s)
```

Save the **Zone ID** (format: `Z1234567890ABC`).

#### Step 4: Create SSH Key Pair (Optional)

For SSH access to your EC2 instance:

```bash
aws ec2 create-key-pair \
  --key-name scim-demo-key \
  --query 'KeyMaterial' \
  --output text > scim-demo-key.pem

chmod 400 scim-demo-key.pem
```

---

### Part 2: GitHub Repository Setup

#### Step 1: Fork or Clone Repository

```bash
git clone https://github.com/joevanhorn/api-entitlements-demo.git
cd api-entitlements-demo
```

#### Step 2: Configure GitHub Secrets

Go to your repository: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add the following secrets:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `AWS_ROLE_ARN` | IAM Role ARN from Step 2 | `arn:aws:iam::123456789012:role/GitHubActions-SCIM-Deploy` |
| `DOMAIN_NAME` | Your domain/subdomain | `dev.demo-entitlements-lowerdecks.com` |
| `ROUTE53_ZONE_ID` | Route53 hosted zone ID | `Z1234567890ABC` |
| `SCIM_AUTH_TOKEN` | Bearer token for SCIM auth | `sk_prod_abc123xyz789...` (generate a secure random string) |
| `SCIM_BASIC_USER` | Basic auth username | `okta_scim_user` |
| `SCIM_BASIC_PASS` | Basic auth password | `secure_password_here` |

**Generate Secure Tokens (Python):**

```python
import secrets

# Generate SCIM Bearer Token
print("SCIM_AUTH_TOKEN:", secrets.token_urlsafe(32))

# Generate Basic Auth Password
print("SCIM_BASIC_PASS:", secrets.token_urlsafe(24))
```

**Optional Okta Secrets** (for automated Okta configuration):

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `OKTA_ORG_NAME` | Your Okta org name | `dev-12345` |
| `OKTA_BASE_URL` | Okta base URL | `okta.com` or custom domain |
| `OKTA_API_TOKEN` | Okta API token | Created in Okta Admin Console |

#### Step 3: Update Terraform Variables (Optional)

Edit `terraform/variables.tf` if you want to customize:
- Instance type (default: `t3.micro`)
- Allowed SSH CIDR blocks
- AWS region

---

### Part 3: Deploy Infrastructure

#### Option A: Automatic Deployment (GitHub Actions)

**Trigger deployment by pushing to main:**

```bash
git add .
git commit -m "Initial deployment"
git push origin main
```

**Or trigger manually:**
1. Go to **Actions** tab in GitHub
2. Select **Deploy SCIM Demo** workflow
3. Click **Run workflow**

Monitor the deployment progress in the Actions tab.

#### Option B: Manual Deployment (Local)

```bash
cd terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan \
  -var="domain_name=dev.demo-entitlements-lowerdecks.com" \
  -var="route53_zone_id=YOUR_ZONE_ID" \
  -var="scim_auth_token=YOUR_TOKEN" \
  -var="scim_basic_user=YOUR_USER" \
  -var="scim_basic_pass=YOUR_PASS"

# Apply configuration
terraform apply
```

#### Step 4: Verify Deployment

After deployment completes (10-15 minutes):

**Check the dashboard:**
```
https://dev.demo-entitlements-lowerdecks.com
```

**Test health endpoint:**
```bash
curl https://dev.demo-entitlements-lowerdecks.com/health
```

**Test SCIM authentication:**
```bash
# Bearer Token
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://dev.demo-entitlements-lowerdecks.com/scim/v2/ServiceProviderConfig

# Basic Auth
curl -u username:password \
  https://dev.demo-entitlements-lowerdecks.com/scim/v2/ServiceProviderConfig
```

---

### Part 4: Configure Okta Integration

#### Step 1: Create SCIM Application in Okta

1. **Okta Admin Console** → **Applications** → **Applications**
2. Click **Browse App Catalog**
3. Search for **"SCIM 2.0 Test App (Header Auth)"**
4. Click **Add Integration**
5. Configure:
   - **Application label**: "Entitlements Demo"
   - Click **Done**

#### Step 2: Configure Provisioning

1. Go to **Provisioning** tab
2. Click **Configure API Integration**
3. Check **"Enable API integration"**
4. Configure:
   - **SCIM Base URL**: `https://dev.demo-entitlements-lowerdecks.com/scim/v2`
   - **Authentication Mode**: HTTP Header or Basic Authentication
   
   **For Basic Auth:**
   - Username: `YOUR_SCIM_BASIC_USER`
   - Password: `YOUR_SCIM_BASIC_PASS`
   
   **For Bearer Token:**
   - Header: `Authorization`
   - Value: `Bearer YOUR_SCIM_AUTH_TOKEN`

5. Click **Test API Credentials**
6. Click **Save**

#### Step 3: Enable Provisioning Features

1. Go to **Provisioning** → **To App**
2. Click **Edit**
3. Enable:
   - ✅ **Create Users**
   - ✅ **Update User Attributes**
   - ✅ **Deactivate Users**
4. Click **Save**

#### Step 4: Configure Attribute Mappings

1. Go to **Provisioning** → **To App** → **Attribute Mappings**
2. Verify/configure mappings:
   - `userName` → `user.userName`
   - `givenName` → `user.firstName`
   - `familyName` → `user.lastName`
   - `email` → `user.email`
   - `active` → `user.status`

#### Step 5: Assign Users

1. Go to **Assignments** tab
2. Click **Assign** → **Assign to People**
3. Select users to provision
4. Assign roles in the application:
   - Administrator
   - Standard User
   - Read Only
   - Support Agent
   - Billing Manager

---

## 🖥️ Local Development

### Running the SCIM Server Locally

```bash
# Clone the repository
git clone https://github.com/joevanhorn/api-entitlements-demo.git
cd api-entitlements-demo

# Set environment variables
export SCIM_AUTH_TOKEN="your-token-here"
export SCIM_BASIC_USER="admin"
export SCIM_BASIC_PASS="password"

# Install dependencies
pip install flask requests

# Run the server
python demo_scim_server.py
```

Access the dashboard at: `http://localhost:5000`

### Testing SCIM Endpoints Locally

```bash
# List users
curl -u admin:password http://localhost:5000/scim/v2/Users

# Create a user
curl -X POST http://localhost:5000/scim/v2/Users \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
    "userName": "john.doe@example.com",
    "name": {
      "givenName": "John",
      "familyName": "Doe"
    },
    "emails": [{
      "value": "john.doe@example.com",
      "primary": true
    }],
    "active": true
  }'
```

### Using Claude Code CLI

Install and set up:

```bash
# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Set API key
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Navigate to repo
cd api-entitlements-demo

# Use Claude Code
claude-code "add rate limiting to the SCIM endpoints"
```

---

## 📊 Available Roles & Entitlements

The demo includes 5 pre-configured roles:

| Role | ID | Permissions |
|------|------|-------------|
| **Administrator** | `role_admin` | `read`, `write`, `delete`, `admin`, `manage_users` |
| **Standard User** | `role_user` | `read`, `write` |
| **Read Only** | `role_readonly` | `read` |
| **Support Agent** | `role_support` | `read`, `write`, `support`, `view_tickets` |
| **Billing Manager** | `role_billing` | `read`, `billing`, `invoices`, `payments` |

Roles are assigned through Okta and synchronized via SCIM to your cloud application.

---

## 🔍 Monitoring & Troubleshooting

### SSH Access

```bash
ssh -i scim-demo-key.pem ubuntu@dev.demo-entitlements-lowerdecks.com
```

### View Logs

```bash
# SCIM service logs
sudo journalctl -u scim-demo -f

# Caddy logs (HTTPS/reverse proxy)
sudo journalctl -u caddy -f

# Cloud-init logs (server setup)
sudo tail -f /var/log/user-data.log

# Check service status
sudo systemctl status scim-demo
sudo systemctl status caddy
```

### Common Issues

#### 1. Let's Encrypt Rate Limit

**Error**: `HTTP 429 urn:ietf:params:acme:error:rateLimited`

**Solution**: Use a subdomain (e.g., `v2.demo-entitlements-lowerdecks.com`)

```bash
# Update GitHub secret DOMAIN_NAME to new subdomain
# Redeploy
```

#### 2. Health Check Timeout

**Symptoms**: GitHub Actions workflow times out waiting for health check

**Solutions**:
```bash
# SSH into server
ssh -i scim-demo-key.pem ubuntu@YOUR_IP

# Check if services are running
sudo systemctl status scim-demo caddy

# Check certificate status
sudo journalctl -u caddy | grep certificate

# Test locally
curl -k https://localhost/health
```

#### 3. SCIM Connection Test Fails in Okta

**Symptoms**: Okta shows "Unable to connect to SCIM endpoint"

**Check:**
1. Verify SCIM Base URL is correct
2. Verify authentication credentials match GitHub secrets
3. Check security group allows HTTPS (port 443)
4. Test with curl:
   ```bash
   curl -u username:password \
     https://dev.demo-entitlements-lowerdecks.com/scim/v2/ServiceProviderConfig
   ```

#### 4. Users Not Provisioning

**Check:**
1. Provisioning features are enabled in Okta
2. Users are assigned to the application
3. View SCIM server logs:
   ```bash
   sudo journalctl -u scim-demo -f
   ```
4. Check dashboard for activity:
   ```
   https://dev.demo-entitlements-lowerdecks.com
   ```

---

## 🗂️ Repository Structure

```
api-entitlements-demo/
├── .github/
│   └── workflows/
│       └── deploy.yml           # CI/CD pipeline
├── terraform/
│   ├── main.tf                  # AWS infrastructure
│   ├── variables.tf             # Input variables
│   ├── outputs.tf               # Output values
│   └── user-data.sh             # EC2 initialization script
├── demo_scim_server.py          # SCIM server implementation
├── README.md                    # This file
└── .gitignore
```

---

## 🔐 Security Considerations

### Production Recommendations

1. **Rotate Credentials**: Regularly rotate SCIM authentication credentials
2. **Restrict SSH Access**: Limit `allowed_ssh_cidr` in Terraform variables
3. **Use Secrets Manager**: Store credentials in AWS Secrets Manager instead of environment variables
4. **Enable CloudWatch**: Set up monitoring and alerting
5. **Use RDS**: Replace in-memory storage with RDS database
6. **Enable VPC**: Deploy in private subnet with NAT gateway
7. **WAF**: Add AWS WAF for additional protection
8. **Rate Limiting**: Implement rate limiting on SCIM endpoints

### Current Security Features

✅ **HTTPS Only**: Automatic SSL/TLS via Let's Encrypt
✅ **Dual Authentication**: Bearer token and Basic Auth support
✅ **IMDSv2**: EC2 metadata service v2 enforced
✅ **Encrypted EBS**: Root volume encryption enabled
✅ **IAM Roles**: No long-lived AWS credentials
✅ **Security Groups**: Minimal port exposure

---

## 📚 API Documentation

### SCIM Endpoints

**Base URL**: `https://dev.demo-entitlements-lowerdecks.com/scim/v2`

#### Service Provider Configuration
```
GET /ServiceProviderConfig
```

#### Resource Types
```
GET /ResourceTypes
```

#### Schemas
```
GET /Schemas
```

#### Users

**List Users**
```
GET /Users?startIndex=1&count=100
```

**Get User**
```
GET /Users/{id}
```

**Create User**
```
POST /Users
Content-Type: application/json

{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "user@example.com",
  "name": {
    "givenName": "Jane",
    "familyName": "Doe"
  },
  "emails": [{
    "value": "user@example.com",
    "primary": true
  }],
  "active": true
}
```

**Update User (PUT)**
```
PUT /Users/{id}
Content-Type: application/json

{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "user@example.com",
  "active": false
}
```

**Patch User**
```
PATCH /Users/{id}
Content-Type: application/json

{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [{
    "op": "replace",
    "value": {
      "active": false
    }
  }]
}
```

**Delete User**
```
DELETE /Users/{id}
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📝 License

This project is provided as-is for demonstration purposes.

---

## 🆘 Support

For issues and questions:
- Open an issue on GitHub
- Check the troubleshooting section above
- Review logs on the EC2 instance

---

## 🎯 Next Steps

After successful deployment:

1. ✅ **Test SCIM provisioning** with a test user in Okta
2. ✅ **Monitor the dashboard** to see real-time provisioning activity
3. ✅ **Configure production database** (replace in-memory storage)
4. ✅ **Set up monitoring** (CloudWatch, alerts)
5. ✅ **Review security settings** for production use
6. ✅ **Document your application's API** that will receive the provisioned user data

---

## 📞 Resources

- [SCIM 2.0 RFC](https://datatracker.ietf.org/doc/html/rfc7644)
- [Okta SCIM Documentation](https://developer.okta.com/docs/concepts/scim/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Caddy Server Documentation](https://caddyserver.com/docs/)
- [Let's Encrypt Rate Limits](https://letsencrypt.org/docs/rate-limits/)

---

**Repository**: https://github.com/joevanhorn/api-entitlements-demo

**Dashboard**: https://dev.demo-entitlements-lowerdecks.com

**Built with**: Python, Flask, Terraform, AWS, Caddy, Let's Encrypt
