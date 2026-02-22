# Loha Infrastructure - Terraform

Terraform configuration for AWS infrastructure with remote state management.

## 📁 Directory Structure

```
infrastructure/
├── init/                   # Bootstrap: Creates S3 + DynamoDB for state (run once)
│   └── terraform.tf
├── app/                    # Application infrastructure (S3 bucket + IAM)
│   ├── terraform.tf        # Provider + empty backend block
│   ├── main.tf             # Application resources
│   ├── backend-dev.hcl     # Dev backend config (state key + DynamoDB lock)
│   ├── backend-prod.hcl    # Prod backend config (state key + DynamoDB lock)
│   └── config/
│       ├── dev.tfvars      # Dev variables (CORS origins, etc.)
│       └── prod.tfvars     # Prod variables
└── README.md
```

## 🚀 Setup Instructions

### Step 1: Initialize State Storage (Run Once)

First, create the S3 bucket and DynamoDB table for storing Terraform state:

```bash
cd infrastructure/init
terraform init
terraform apply
```

This creates:

- ✅ S3 bucket: `loha-terraform-state` (stores all Terraform state files)
- ✅ DynamoDB table: `loha-terraform-locks` (prevents concurrent modifications)

**Note:** The init state is stored locally in `init/terraform.tfstate`. Keep this file safe!

### Step 2: Deploy Application Infrastructure

The `app/` directory uses the S3 bucket from `init/` to store its state remotely. Dev and prod have **separate state files**.

#### Deploy Dev Environment

```bash
cd infrastructure/app
terraform init -backend-config=backend-dev.hcl
terraform plan  -var-file=config/dev.tfvars
terraform apply -var-file=config/dev.tfvars
```

#### Deploy Prod Environment

```bash
cd infrastructure/app
terraform init -backend-config=backend-prod.hcl -reconfigure
terraform plan  -var-file=config/prod.tfvars
terraform apply -var-file=config/prod.tfvars
```

**Important:**

- Always specify both the backend config AND the tfvars file
- Use `-reconfigure` when switching between environments

## 📦 What Gets Created

### Init Resources (One-time):

- **S3 Bucket:** `loha-terraform-state` - Stores Terraform state files
- **DynamoDB Table:** `loha-terraform-locks` - Prevents concurrent modifications

### App Resources (Per Environment):

- **S3 Bucket:** `loha-{env}-bucket` - Application file storage
- **IAM User:** `loha-{env}-backend-user` - Backend access
- **IAM Policy:** S3 access permissions
- **IAM Access Keys:** Authentication credentials

## 🗂️ State File Organization

```
Local:
infrastructure/init/terraform.tfstate     ← Bootstrap state (kept locally)

S3: loha-terraform-state/
└── app/
    ├── dev/terraform.tfstate             ← Dev state (backend-dev.hcl)
    └── prod/terraform.tfstate            ← Prod state (backend-prod.hcl)
```

**How it works:**

- The `init/` state is stored locally (only run once, commit the file)
- The `app/` state is stored in S3, **completely separated per environment**
- `-backend-config` selects which environment's state to use
- DynamoDB table `loha-terraform-locks` prevents concurrent apply conflicts

## 🔐 Get Credentials

After deploying:

```bash
cd infrastructure/app

# View outputs
terraform output

# Get sensitive credentials
terraform output -raw backend_access_key_id
terraform output -raw backend_secret_access_key
```

Add to your backend `.env`:

```env
AWS_ACCESS_KEY_ID=<backend_access_key_id output>
AWS_SECRET_ACCESS_KEY=<backend_secret_access_key output>
AWS_STORAGE_BUCKET_NAME=<s3_bucket_name output>   # e.g. loha-dev-bucket
AWS_S3_REGION_NAME=ap-southeast-1
```

## 🔄 Common Operations

### Work with Dev Environment

```bash
cd infrastructure/app

# Initialize for dev (first time or after switching)
terraform init -backend-config=backend-dev.hcl -reconfigure

# Deploy/update dev
terraform plan  -var-file=config/dev.tfvars
terraform apply -var-file=config/dev.tfvars
```

### Work with Prod Environment

```bash
cd infrastructure/app

# Initialize for prod (first time or after switching)
terraform init -backend-config=backend-prod.hcl -reconfigure

# Deploy/update prod
terraform plan  -var-file=config/prod.tfvars
terraform apply -var-file=config/prod.tfvars
```

### View Current State

```bash
cd infrastructure/app
terraform show
```

### Update Infrastructure

```bash
cd infrastructure/app
terraform plan -var-file="dev.tfvars"    # Preview changes
terraform apply -var-file="dev.tfvars"   # Apply changes
```

### Destroy an Environment

```bash
cd infrastructure/app
terraform destroy -var-file="dev.tfvars"   # or prod.tfvars
```

## 💰 Costs

### Init Resources (Always Running):

- S3 State Bucket: ~$0.01/month (minimal storage)
- DynamoDB Locks Table: ~$0.00/month (pay per request)

### App Resources (Per Environment):

- Dev: ~$0.10 - $1/month (minimal usage)
- Prod: $1 - $50/month (depends on usage)

See [S3 Pricing Details](https://aws.amazon.com/s3/pricing/) for more info.

## 🔒 Security Features

- ✅ Remote state encrypted at rest (AES256)
- ✅ Remote state encrypted in transit (HTTPS)
- ✅ **Separate state files for dev and prod** (complete isolation via `backend-dev.hcl` / `backend-prod.hcl`)
- ✅ DynamoDB state locking (prevents concurrent corruption)
- ✅ All S3 buckets block public access
- ✅ App S3 bucket CORS configured per environment
- ✅ Separate IAM users per environment
- ✅ Versioning enabled for state recovery

## ⚠️ Important Notes

### Dev and Prod are Fully Isolated

- Each environment has its **own S3 state file** (`app/dev/` vs `app/prod/`)
- Each environment has its **own DynamoDB lock entry**
- Deploying prod never touches dev resources
- You can run both environments simultaneously

## 🧹 Cleanup Everything

To completely remove all infrastructure:

```bash
# 1. Destroy app resources
cd infrastructure/app
terraform destroy -var-file=config/dev.tfvars   # or config/prod.tfvars

# 2. Destroy init resources (removes state storage)
cd infrastructure/init
terraform destroy
```

⚠️ **Warning:** Destroying init removes the state bucket. Make sure app is destroyed first!

## 🆘 Troubleshooting

### Error: "Error acquiring the state lock"

Someone else is running terraform or a previous run crashed.

**Solution:**

1. Check DynamoDB table `loha-terraform-locks`
2. Delete the stuck lock item manually
3. Re-run terraform

### Error: "Backend initialization required"

**Solution:**

```bash
cd infrastructure/app
terraform init -reconfigure
```

### Error: "No valid credential sources found"

**Solution:**

```bash
aws configure
```

### Forgot which environment you're in

**Solution:**

```bash
# Check current backend configuration
terraform show
# Or reinitialize with the correct backend
terraform init -backend-config=backend-dev.hcl -reconfigure
```

## 📝 Workflow Recommendations

### For Solo Development:

1. Use current setup (simpler, cost-effective)
2. Deploy dev during development
3. Deploy prod when ready to release
4. Keep both environments in separate AWS accounts if budget allows

### For Team Development:

1. Restructure into separate directories (Option 1 above)
2. Use separate state files for dev/prod
3. Consider CI/CD pipelines for deployment
4. Use AWS Organizations for account separation

## 🔗 Related Documentation

- [Terraform S3 Backend](https://www.terraform.io/docs/language/settings/backends/s3.html)
- [Backend NestJS Integration](../backend/S3_INTEGRATION.md)
- [AWS S3 Pricing](https://aws.amazon.com/s3/pricing/)
