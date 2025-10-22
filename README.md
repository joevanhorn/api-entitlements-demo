# API Entitlements Demo

Automated SCIM 2.0 connector demonstrating entitlement management with Okta, deployed via Terraform and GitHub Actions.

---

## 🎯 What This Demonstrates

This project shows how to:

✅ Discover entitlements from a cloud application  
✅ Provision users with specific roles via Okta  
✅ Manage role assignments dynamically  
✅ Simulate API calls to your cloud app  
✅ Deploy infrastructure automatically with Terraform  
✅ Demonstrate **both Bearer Token and Basic Auth** provisioning flows

---

## 🔐 Authentication Options

The demo now supports **two authentication modes** for SCIM 2.0 integration with Okta:

| Mode | Okta App Template | Environment Variables | Recommended Use |
|------|-------------------|------------------------|------------------|
| **Basic Auth** | SCIM 2.0 Test App (Basic Auth) | `SCIM_BASIC_USER`, `SCIM_BASIC_PASS` | ✅ Recommended |
| **Bearer Token (Header Auth)** | SCIM 2.0 Test App (Header Auth) | `SCIM_AUTH_TOKEN` | Legacy / for testing via `curl` |

Both modes are automatically supported — you can test or configure either in Okta without code changes.

---

## ⚙️ AWS Setup (Prerequisites)

Follow the same AWS setup steps from the original version:

- Route53 domain and hosted zone
- Versioned S3 bucket for Terraform state
- GitHub Actions IAM role using OIDC
- AWS Role ARN stored as a GitHub Secret

> ✅ Ensure your Route53 domain, hosted zone ID, S3 backend, and GitHub Actions IAM role are configured before continuing.

---

## 🚀 Quick Start

### Prerequisites
- AWS Account with SSO access  
- GitHub Account  
- Route53 Domain configured in AWS  
- Okta Developer Account (free at [developer.okta.com](https://developer.okta.com))  

### Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/joevanhorn/api-entitlements-demo.git
cd api-entitlements-demo
```

#### 2. Configure GitHub Secrets
Go to: **Settings → Secrets and variables → Actions → New repository secret**

Add the following secrets:

| Secret | Description |
|--------|--------------|
| `AWS_ROLE_ARN` | Your AWS IAM role ARN for GitHub Actions |
| `DOMAIN_NAME` | Your Route53 domain (e.g., demo.yourdomain.com) |
| `ROUTE53_ZONE_ID` | Route53 hosted zone ID |
| `SCIM_AUTH_TOKEN` | Bearer token for SCIM API |
| `SCIM_BASIC_USER` | Basic Auth username (e.g., `scim`) |
| `SCIM_BASIC_PASS` | Basic Auth password (secure value) |

#### 3. Deploy via GitHub Actions
Commit and push changes:
```bash
git add .
git commit -m "Deploy SCIM demo with Basic Auth support"
git push origin main
```

The workflow **Deploy SCIM Demo** will automatically:
- Deploy EC2 + Caddy + Flask app  
- Inject `.env` with your SCIM credentials  
- Create Route53 DNS record  
- Output your Dashboard and API URLs in the GitHub Actions summary

---

## 📍 Accessing Your Demo

| Component | URL Example |
|------------|--------------|
| Dashboard | `https://your-domain.com` |
| SCIM API | `https://your-domain.com/scim/v2` |
| Health Check | `https://your-domain.com/health` |

---

## 🔧 Configure in Okta

### Option A — Basic Auth (Recommended)
1. In Okta Admin Console → **Applications → Browse App Catalog**
2. Search: **SCIM 2.0 Test App (Basic Auth)**
3. Add Integration → Configure Provisioning → **Enable API Integration**
4. Settings:
   - SCIM Base URL: `https://your-domain.com/scim/v2`
   - Username: `scim`
   - Password: *(your `SCIM_BASIC_PASS` value)*
5. Click **Test API Credentials** → ✅ Should succeed!
6. Enable features:
   - ☑ Create Users  
   - ☑ Update User Attributes  
   - ☑ Deactivate Users  

### Option B — Bearer Token (Legacy)
1. In Okta Admin Console → **SCIM 2.0 Test App (Header Auth)**
2. SCIM Base URL: `https://your-domain.com/scim/v2`
3. Authorization Header: `Authorization`
4. Header Value: `Bearer YOUR_SCIM_AUTH_TOKEN`
5. Test API Credentials → ✅ Should succeed!

---

## 🎭 Available Roles

The demo includes 5 sample entitlements (roles):

| Role | Description |
|------|--------------|
| Administrator | Full system access |
| Standard User | Basic access |
| Read Only | View only access |
| Support Agent | Customer support access |
| Billing Manager | Billing and payment access |

---

## 🧱 Infrastructure

- EC2: t2.micro (AWS Free Tier eligible)  
- Route53: DNS management  
- Caddy: Automatic HTTPS certificates  
- Python Flask: SCIM server (Flask + dotenv)  
- `.env`: Injected environment variables with all SCIM credentials  

---

## 🧪 Manual Testing

```bash
# Check SCIM config (no auth needed)
curl -i https://your-domain.com/scim/v2/ServiceProviderConfig

# Test Basic Auth
curl -i -u "scim:<password>" https://your-domain.com/scim/v2/Users?startIndex=1&count=2

# Test Bearer Token
curl -i -H "Authorization: Bearer <token>" https://your-domain.com/scim/v2/Users?startIndex=1&count=2
```

Expected:  
`HTTP/1.1 200 OK` and a valid SCIM ListResponse.

---

## 📊 Monitoring

```bash
# SSH into instance
ssh ubuntu@<your-public-ip>

# View setup logs
sudo tail -f /var/log/user-data.log

# View SCIM service logs
sudo journalctl -u scim-demo -f

# View Caddy logs
sudo journalctl -u caddy -f
```

Quick status:
```bash
ssh ubuntu@<your-ip> 'scim-status'
```

---

## 🗑️ Cleanup

Destroy all AWS resources:
```bash
terraform destroy -auto-approve
```
Or trigger **Destroy SCIM Demo** from GitHub Actions.

---

## 💰 Estimated Cost

| Component | Cost (Monthly) |
|------------|----------------|
| EC2 (t2.micro) | ~$8–10 |
| Route53 Hosted Zone | $0.50 |
| Domain Registration | $3–12 / year |
| S3 State Storage | ~$0.01 |
| **Total** | **~$10–15/month** |

---

## 🛠️ Local Development

```bash
cd app
pip install Flask python-dotenv
python3 demo_scim_server.py
```
Access at:  
`http://localhost:5000/scim/v2`

---

## 📚 References

- [Okta SCIM 2.0 Documentation](https://developer.okta.com/docs/concepts/scim/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [SCIM 2.0 Specification](https://datatracker.ietf.org/doc/html/rfc7644)

---

## 🤝 Contributing

Pull requests are welcome — please open an issue first to discuss proposed changes.

---

## 📝 License

MIT License — freely usable for demos, training, or internal enablement.

---

## 🔗 Links

- **Repository:** [joevanhorn/api-entitlements-demo](https://github.com/joevanhorn/api-entitlements-demo)  
- **Author:** Joe Van Horn  
- For assistance: reach out via Slack (Okta employees) or LinkedIn
