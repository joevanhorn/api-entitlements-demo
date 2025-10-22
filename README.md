# API Entitlements Demo

Automated SCIM 2.0 connector demonstrating entitlement management with Okta, deployed via Terraform and GitHub Actions.

## 🎯 What This Demonstrates

This project shows how to:
- ✅ **Discover entitlements** from a cloud application
- ✅ **Provision users** with specific roles via Okta
- ✅ **Manage role assignments** dynamically
- ✅ **Simulate API calls** to your cloud app
- ✅ **Deploy infrastructure** automatically with Terraform

## AWS Setup (Prerequisites)

Before you can deploy this demo, you need to set up AWS infrastructure and permissions. Follow these steps using the AWS Console.

### 1. Register/Configure a Domain in Route53

You need a domain name for your SCIM server. You can either:
- **Register a new domain** through Route53
- **Transfer an existing domain** to Route53
- **Use a subdomain** from an existing Route53 hosted zone

#### Option A: Register New Domain

1. Sign in to the [AWS Console](https://console.aws.amazon.com)
2. Search for **Route53** in the top search bar
3. In the left navigation, click **Registered domains**
4. Click **Register domain**
5. Search for your desired domain (e.g., `demo-entitlements-lowerdecks.com`)
6. Select an available domain and click **Add to cart**
7. Click **Continue**
8. Fill in contact information and complete registration
9. Wait for registration to complete (can take up to 3 days)
10. A hosted zone will be automatically created

#### Option B: Use Existing Domain/Subdomain

1. Sign in to the [AWS Console](https://console.aws.amazon.com)
2. Search for **Route53** in the top search bar
3. In the left navigation, click **Hosted zones**
4. You should see your existing hosted zone(s) listed

#### Get Your Zone ID:

1. In **Route53 → Hosted zones**, find your domain
2. Click on the domain name to view details
3. Look for the **Hosted zone ID** at the top right (format: `Z1234567890ABC`)
4. **Copy this ID** - you'll need it for GitHub Secrets

**Save the Hosted Zone ID** somewhere safe!

---

### 2. Create S3 Bucket for Terraform State

Terraform needs a place to store its state file. Create a versioned S3 bucket:

#### Create the Bucket

1. In the AWS Console, search for **S3**
2. Click **Create bucket**
3. **Bucket name:** Choose a globally unique name (e.g., `yourname-scim-terraform-state`)
   - Bucket names must be unique across all of AWS
   - Use lowercase letters, numbers, and hyphens only
4. **AWS Region:** Select `us-east-1` (US East N. Virginia)
5. **Object Ownership:** Leave as default (ACLs disabled)
6. **Block Public Access settings:** Leave all checkboxes **checked** (block all public access)
7. **Bucket Versioning:** Select **Enable**
8. **Default encryption:** Select **Enable** with **Server-side encryption with Amazon S3 managed keys (SSE-S3)**
9. Click **Create bucket**

**Important:** After creating the bucket, update `terraform/backend.tf` with your bucket name:

```hcl
terraform {
  backend "s3" {
    bucket = "yourname-scim-terraform-state"  # Change this to your bucket name!
    key    = "scim-demo/terraform.tfstate"
    region = "us-east-1"
  }
}
```

**Save your bucket name** - you'll reference it later in the IAM policy!

---

### 3. Create GitHub Actions IAM Role (OIDC)

This role allows GitHub Actions to deploy to your AWS account securely without storing long-lived credentials.

#### Step 3a: Create the OIDC Identity Provider

1. In the AWS Console, search for **IAM**
2. In the left navigation, click **Identity providers**
3. Click **Add provider**
4. **Provider type:** Select **OpenID Connect**
5. **Provider URL:** Enter `https://token.actions.githubusercontent.com`
6. Click **Get thumbprint**
7. **Audience:** Enter `sts.amazonaws.com`
8. Click **Add provider**

**Note:** If you see an error that the provider already exists, that's fine - skip to Step 3b.

#### Step 3b: Create the IAM Role

1. Still in **IAM**, click **Roles** in the left navigation
2. Click **Create role**
3. **Trusted entity type:** Select **Web identity**
4. **Identity provider:** Select `token.actions.githubusercontent.com` from the dropdown
5. **Audience:** Select `sts.amazonaws.com`
6. Click **Next**

#### Step 3c: Attach Permissions Policies (Temporary - We'll Add Custom Policy Later)

1. For now, search for and select **PowerUserAccess** (we'll refine this later)
2. Click **Next**
3. **Role name:** Enter `GitHub-Actions`
4. **Description:** Enter `Role for GitHub Actions to deploy SCIM demo`
5. Click **Create role**

#### Step 3d: Edit Trust Relationship to Restrict to Your Repository

1. Find your newly created **GitHub-Actions** role in the roles list and click on it
2. Click the **Trust relationships** tab
3. Click **Edit trust policy**
4. Replace the entire JSON with the following (update the placeholders):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_AWS_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
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

**Replace these values:**
- `YOUR_AWS_ACCOUNT_ID`: Your 12-digit AWS account ID (find it by clicking your name in top-right → Account)
- `YOUR_GITHUB_USERNAME`: Your GitHub username (e.g., `joevanhorn`)

5. Click **Update policy**

#### Step 3e: Create Custom Permissions Policy

Now let's replace PowerUserAccess with specific permissions needed for this demo.

1. Still on the **GitHub-Actions** role page, click the **Permissions** tab
2. Find **PowerUserAccess** in the list and click the **X** to detach it
3. Click **Add permissions** → **Create inline policy**
4. Click the **JSON** tab
5. Paste the following policy (update YOUR_BUCKET_NAME):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EC2Permissions",
      "Effect": "Allow",
      "Action": [
        "ec2:RunInstances",
        "ec2:TerminateInstances",
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceStatus",
        "ec2:DescribeInstanceAttribute",
        "ec2:CreateSecurityGroup",
        "ec2:DeleteSecurityGroup",
        "ec2:DescribeSecurityGroups",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:AuthorizeSecurityGroupEgress",
        "ec2:RevokeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupEgress",
        "ec2:CreateKeyPair",
        "ec2:DeleteKeyPair",
        "ec2:DescribeKeyPairs",
        "ec2:DescribeImages",
        "ec2:DescribeVolumes",
        "ec2:CreateTags",
        "ec2:DeleteTags",
        "ec2:DescribeTags",
        "ec2:DescribeVpcs",
        "ec2:DescribeSubnets",
        "ec2:DescribeAvailabilityZones"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IAMPermissions",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:GetRole",
        "iam:DeleteRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRolePolicy",
        "iam:ListRolePolicies",
        "iam:ListAttachedRolePolicies",
        "iam:CreateInstanceProfile",
        "iam:GetInstanceProfile",
        "iam:DeleteInstanceProfile",
        "iam:AddRoleToInstanceProfile",
        "iam:RemoveRoleFromInstanceProfile",
        "iam:PassRole",
        "iam:TagRole",
        "iam:TagInstanceProfile",
        "iam:ListInstanceProfilesForRole"
      ],
      "Resource": "*"
    },
    {
      "Sid": "Route53Permissions",
      "Effect": "Allow",
      "Action": [
        "route53:GetHostedZone",
        "route53:ListHostedZones",
        "route53:ChangeResourceRecordSets",
        "route53:ListResourceRecordSets",
        "route53:GetChange"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchLogsPermissions",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DeleteLogGroup",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:PutRetentionPolicy",
        "logs:TagLogGroup"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3StatePermissions",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::YOUR_BUCKET_NAME",
        "arn:aws:s3:::YOUR_BUCKET_NAME/*"
      ]
    }
  ]
}
```

**Replace** `YOUR_BUCKET_NAME` with the S3 bucket name you created in Step 2 (appears twice in the policy).

6. Click **Next**
7. **Policy name:** Enter `TerraformSCIMDeployment`
8. Click **Create policy**

#### Step 3f: Get the Role ARN

1. Still on the **GitHub-Actions** role page
2. Look at the **Summary** section at the top
3. Find **ARN** and copy the entire value (e.g., `arn:aws:iam::123456789012:role/GitHub-Actions`)
4. **Save this ARN** - you'll need it for GitHub Secrets!

---

### 4. Gather Information for GitHub Secrets

Before moving to the Quick Start, collect these values:

| Secret Name | How to Get It | Example |
|-------------|---------------|---------|
| `AWS_ROLE_ARN` | From Step 3f above | `arn:aws:iam::123456789012:role/GitHub-Actions` |
| `DOMAIN_NAME` | Your Route53 domain | `demo-entitlements-lowerdecks.com` |
| `ROUTE53_ZONE_ID` | From Step 1 above | `Z1234567890ABC` |
| `SCIM_AUTH_TOKEN` | Generate a secure token | See below |

#### Generate SCIM_AUTH_TOKEN:

Choose one of these methods to generate a secure random token:

**Option 1: Use an Online UUID Generator**
1. Visit https://www.uuidgenerator.net/
2. Click **Generate** to create a UUID
3. Copy the generated UUID (e.g., `a1b2c3d4-e5f6-7890-abcd-ef1234567890`)

**Option 2: Use a Password Generator**
1. Visit https://passwordsgenerator.net/
2. Set length to **32 characters**
3. Enable: Lowercase, Uppercase, Numbers
4. Click **Generate Password**
5. Copy the generated password

**Option 3: Create Your Own**
- Use any combination of letters and numbers
- Make it at least 20 characters long
- Example: `mySecureToken2024Demo123`

**Save this token** - you'll need it for GitHub Secrets and to configure Okta later!

---

### Verification

Before proceeding to Quick Start, verify:

- ✅ You have a Route53 hosted zone and its Zone ID
- ✅ You've created an S3 bucket for Terraform state
- ✅ You've updated `terraform/backend.tf` with your bucket name
- ✅ You've created the GitHub-Actions IAM role with proper permissions
- ✅ You have all four values ready for GitHub Secrets

---

### Estimated AWS Costs

- **First 12 months:** FREE (AWS Free Tier covers t2.micro EC2)
- **After Free Tier:** ~$8-10/month for t2.micro
- **Route53 Hosted Zone:** $0.50/month
- **Domain Registration:** $3-12/year (depending on TLD)
- **S3 State Storage:** ~$0.01/month (negligible)

**Total estimated cost after free tier:** ~$10-15/month

---

### Troubleshooting AWS Setup

**Problem:** "Entity already exists" when creating OIDC provider
- **Solution:** The provider already exists, skip to step 3b

**Problem:** "Access Denied" when running AWS CLI commands
- **Solution:** Ensure your AWS credentials have admin permissions or the necessary IAM permissions

**Problem:** Can't find my Route53 Zone ID
- **Solution:** Run `aws route53 list-hosted-zones` and look for your domain

**Problem:** Terraform state bucket access denied
- **Solution:** Verify the S3 permissions in your GitHub-Actions IAM role policy include your bucket name

---

Now you're ready to proceed to the Quick Start section!

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

For assistance with this demo, reach out to Joe Van Horn on Slack if you are an Okta employee, or via linkedin if you are not. 
