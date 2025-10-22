# API Entitlements Demo

Automated SCIM 2.0 connector demonstrating entitlement management with Okta, deployed via Terraform and GitHub Actions.

## 🎯 What This Demonstrates

This project shows how to:
- ✅ **Discover entitlements** from a cloud application
- ✅ **Provision users** with specific roles via Okta
- ✅ **Manage role assignments** dynamically
- ✅ **Simulate API calls** to your cloud app
- ✅ **Deploy infrastructure** automatically with Terraform

## 🚀 Quick Start

### Prerequisites

1. **AWS Account** with SSO access
2. **GitHub Account**
3. **Route53 Domain** configured in AWS
4. **Okta Developer Account** (free at https://developer.okta.com)

### Setup

1. **Clone this repository**
   ```bash
   git clone https://github.com/joevanhorn/api-entitlements-demo.git
   cd api-entitlements-demo
   ```

2. **Configure GitHub Secrets**
   
   Go to: Settings → Secrets and variables → Actions → New repository secret
   
   Add these secrets:
   - `AWS_ROLE_ARN` - Your AWS IAM role ARN for GitHub Actions
   - `DOMAIN_NAME` - Your domain (e.g., `demo.yourdomain.com`)
   - `ROUTE53_ZONE_ID` - Your Route53 hosted zone ID
   - `SCIM_AUTH_TOKEN` - Secure token for SCIM API (e.g., `demo-token-12345`)

3. **Update S3 Bucket Name**
   
   Edit `terraform/backend.tf` and change:
   ```hcl
   bucket = "joevanhorn-scim-terraform-state"  # Change this!
   ```
   
   Create the bucket:
   ```bash
   aws s3 mb s3://YOUR-UNIQUE-BUCKET-NAME
   aws s3api put-bucket-versioning \
     --bucket YOUR-UNIQUE-BUCKET-NAME \
     --versioning-configuration Status=Enabled
   ```

4. **Deploy!**
   ```bash
   git add .
   git commit -m "Initial setup"
   git push origin main
   ```

The GitHub Action will automatically deploy your infrastructure!

## 📍 Accessing Your Demo

After deployment (check GitHub Actions for status):

- **Dashboard**: `https://your-domain.com`
- **SCIM API**: `https://your-domain.com/scim/v2`
- **Health Check**: `https://your-domain.com/health`

## 🔧 Configure in Okta

1. **Okta Admin Console** → **Applications** → **Browse App Catalog**
2. Search: `SCIM 2.0 Test App (Header Auth)`
3. **Add Integration**
4. **Provisioning** → **Configure API Integration**
5. Settings:
   ```
   SCIM Base URL: https://your-domain.com/scim/v2
   Authorization Header: Authorization
   Header Value: Bearer YOUR-TOKEN
   ```
6. **Test API Credentials** → Should succeed!
7. **Enable provisioning features**

## 🎭 Available Roles

The demo includes 5 sample entitlements:
- **Administrator** - Full system access
- **Standard User** - Basic access
- **Read Only** - View only access
- **Support Agent** - Customer support access
- **Billing Manager** - Billing and payment access

## 🏗️ Infrastructure

- **EC2**: t2.micro instance (AWS Free Tier eligible)
- **Route53**: DNS management
- **Caddy**: Automatic HTTPS certificates
- **Python Flask**: SCIM server

## 📊 Monitoring

**View Logs:**
```bash
# SSH to your instance
ssh ubuntu@YOUR-IP

# View setup logs
tail -f /var/log/user-data.log

# View SCIM service logs
sudo journalctl -u scim-demo -f

# View Caddy logs
sudo journalctl -u caddy -f
```

**Quick Status:**
```bash
ssh ubuntu@YOUR-IP 'scim-status'
```

## 🗑️ Cleanup

To destroy all AWS resources:

1. GitHub → **Actions** → **Destroy SCIM Demo**
2. Click **Run workflow**
3. Type `destroy` to confirm
4. Click **Run workflow**

## 💰 Cost

- **First year**: FREE (AWS Free Tier)
- **After**: ~$8-10/month for t2.micro
- **Domain**: $3-12/year depending on TLD

## 🛠️ Development

**Local Testing:**
```bash
cd app
python3 demo_scim_server.py
# Access at http://localhost:5000
```

**Terraform Plan:**
```bash
cd terraform
terraform init
terraform plan
```

## 📚 Documentation

- [Okta SCIM Documentation](https://developer.okta.com/docs/guides/scim/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [SCIM 2.0 Specification](https://datatracker.ietf.org/doc/html/rfc7644)

## 🤝 Contributing

Feel free to open issues or submit pull requests!

## 📝 License

MIT License - feel free to use this for your own demos and projects.

## 🔗 Links

- **Repository**: https://github.com/joevanhorn/api-entitlements-demo
- **Author**: Joe VanHorn

---

Made with ❤️ to demonstrate SCIM entitlement management
