# Deployment Guide: Azure Web App with CI/CD

This guide provides step-by-step instructions for deploying the AI Tech Career Path Finder to Azure Web App (Free Tier) with Azure Blob Storage and GitHub Actions CI/CD.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Azure Resources Setup](#azure-resources-setup)
3. [GitHub Repository Setup](#github-repository-setup)
4. [Configure GitHub Secrets](#configure-github-secrets)
5. [Deploy to Azure](#deploy-to-azure)
6. [Verify Deployment](#verify-deployment)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Azure account (free tier is sufficient)
- GitHub account
- Azure CLI installed (optional but recommended)
- Git installed

---

## Azure Resources Setup

### Step 1: Create Azure Resources

#### 1.1 Create Resource Group

```bash
# Login to Azure
az login

# Create resource group
az group create \
  --name ai-career-path-rg \
  --location eastus
```

#### 1.2 Create Storage Account

```bash
# Create storage account (must be globally unique)
az storage account create \
  --name aicareerpath<your-unique-id> \
  --resource-group ai-career-path-rg \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2 \
  --access-tier Hot \
  --allow-blob-public-access false

# Create containers for uploads and generated files
az storage container create \
  --name uploads \
  --account-name aicareerpath<your-unique-id> \
  --auth-mode login

az storage container create \
  --name generated \
  --account-name aicareerpath<your-unique-id> \
  --auth-mode login
```

**Alternative: Using Azure Portal**
1. Go to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource" → "Storage account"
3. Fill in the details:
   - **Subscription**: Your subscription
   - **Resource group**: Create new → `ai-career-path-rg`
   - **Storage account name**: `aicareerpath<your-unique-id>`
   - **Region**: East US
   - **Performance**: Standard
   - **Redundancy**: LRS (Locally-redundant storage)
4. Review + Create
5. After creation, go to the storage account
6. Click "Containers" → "+ Container"
7. Create two containers: `uploads` and `generated`

#### 1.3 Create Azure OpenAI Resource

**Note**: Azure OpenAI requires approval. If you don't have access, you can use OpenAI API directly.

```bash
# Create Azure OpenAI resource
az cognitiveservices account create \
  --name ai-career-openai \
  --resource-group ai-career-path-rg \
  --kind OpenAI \
  --sku S0 \
  --location eastus

# Deploy GPT-4o model
az cognitiveservices account deployment create \
  --name ai-career-openai \
  --resource-group ai-career-path-rg \
  --deployment-name gpt-4o \
  --model-name gpt-4o \
  --model-version "2024-05-13" \
  --model-format OpenAI \
  --sku-capacity 1 \
  --sku-name "Standard"
```

#### 1.4 Create Azure Web App (Free Tier)

```bash
# Create App Service Plan (Free Tier)
az appservice plan create \
  --name ai-career-path-plan \
  --resource-group ai-career-path-rg \
  --sku F1 \
  --is-linux

# Create Web App
az webapp create \
  --resource-group ai-career-path-rg \
  --plan ai-career-path-plan \
  --name ai-career-path-app-<your-unique-id> \
  --runtime "PYTHON:3.11" \
  --startup-file "startup.sh"
```

**Alternative: Using Azure Portal**
1. Go to Azure Portal → "Create a resource" → "Web App"
2. Fill in the details:
   - **Resource Group**: `ai-career-path-rg`
   - **Name**: `ai-career-path-app-<your-unique-id>`
   - **Publish**: Code
   - **Runtime stack**: Python 3.11
   - **Operating System**: Linux
   - **Region**: East US
3. Under "Pricing plans", select **F1 (Free)**
4. Review + Create

---

### Step 2: Configure Azure Web App Settings

#### 2.1 Enable Managed Identity

```bash
# Enable system-assigned managed identity
az webapp identity assign \
  --resource-group ai-career-path-rg \
  --name ai-career-path-app-<your-unique-id>

# Get the principal ID
PRINCIPAL_ID=$(az webapp identity show \
  --resource-group ai-career-path-rg \
  --name ai-career-path-app-<your-unique-id> \
  --query principalId \
  --output tsv)
```

**Portal Method**:
1. Go to your Web App → Settings → Identity
2. System assigned → Status: On → Save
3. Copy the Object (principal) ID

#### 2.2 Grant Storage Access to Web App

```bash
# Get storage account ID
STORAGE_ID=$(az storage account show \
  --name aicareerpath<your-unique-id> \
  --resource-group ai-career-path-rg \
  --query id \
  --output tsv)

# Assign Storage Blob Data Contributor role
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Storage Blob Data Contributor" \
  --scope $STORAGE_ID
```

**Portal Method**:
1. Go to Storage Account → Access Control (IAM)
2. Click "+ Add" → "Add role assignment"
3. Select "Storage Blob Data Contributor"
4. Click Next → Select members
5. Search for your Web App name
6. Select and Review + assign

#### 2.3 Configure Application Settings

```bash
# Get Azure OpenAI endpoint and key
OPENAI_ENDPOINT=$(az cognitiveservices account show \
  --name ai-career-openai \
  --resource-group ai-career-path-rg \
  --query properties.endpoint \
  --output tsv)

OPENAI_KEY=$(az cognitiveservices account keys list \
  --name ai-career-openai \
  --resource-group ai-career-path-rg \
  --query key1 \
  --output tsv)

# Set application settings
az webapp config appsettings set \
  --resource-group ai-career-path-rg \
  --name ai-career-path-app-<your-unique-id> \
  --settings \
    AZURE_OPENAI_ENDPOINT="$OPENAI_ENDPOINT" \
    AZURE_OPENAI_API_KEY="$OPENAI_KEY" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o" \
    AZURE_OPENAI_API_VERSION="2024-12-01-preview" \
    USE_MANAGED_IDENTITY="true" \
    AZURE_STORAGE_ACCOUNT_NAME="aicareerpath<your-unique-id>" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
    WEBSITE_HTTPLOGGING_RETENTION_DAYS="7"
```

**Portal Method**:
1. Go to Web App → Configuration → Application settings
2. Click "+ New application setting" for each:
   - `AZURE_OPENAI_ENDPOINT`: Your OpenAI endpoint
   - `AZURE_OPENAI_API_KEY`: Your OpenAI key
   - `AZURE_OPENAI_DEPLOYMENT_NAME`: `gpt-4o`
   - `AZURE_OPENAI_API_VERSION`: `2024-12-01-preview`
   - `USE_MANAGED_IDENTITY`: `true`
   - `AZURE_STORAGE_ACCOUNT_NAME`: `aicareerpath<your-unique-id>`
   - `SCM_DO_BUILD_DURING_DEPLOYMENT`: `true`
3. Click "Save"

---

## GitHub Repository Setup

### Step 3: Create and Configure GitHub Repository

#### 3.1 Initialize Git Repository

```bash
cd c:\Users\losts\Desktop\path-finder

# Initialize git if not already done
git init

# Add all files
git add .

# Create .gitignore to exclude sensitive files
git commit -m "Initial commit with Azure deployment configuration"
```

#### 3.2 Create GitHub Repository

1. Go to [GitHub](https://github.com) and create a new repository
2. Name it: `ai-career-path-finder`
3. Don't initialize with README (we already have files)
4. Click "Create repository"

#### 3.3 Push to GitHub

```bash
# Add remote
git remote add origin https://github.com/<your-username>/ai-career-path-finder.git

# Push code
git branch -M main
git push -u origin main
```

---

## Configure GitHub Secrets

### Step 4: Set up GitHub Secrets for CI/CD

#### 4.1 Get Azure Web App Publish Profile

```bash
# Download publish profile
az webapp deployment list-publishing-profiles \
  --resource-group ai-career-path-rg \
  --name ai-career-path-app-<your-unique-id> \
  --xml
```

**Portal Method**:
1. Go to your Web App in Azure Portal
2. Click "Get publish profile" in the toolbar
3. Download the `.PublishSettings` file
4. Open it in a text editor and copy all content

#### 4.2 Add Secrets to GitHub

1. Go to your GitHub repository
2. Click "Settings" → "Secrets and variables" → "Actions"
3. Click "New repository secret"
4. Add the following secrets:

**Secret 1: AZURE_WEBAPP_PUBLISH_PROFILE**
- Name: `AZURE_WEBAPP_PUBLISH_PROFILE`
- Value: Paste the entire publish profile XML content

**Secret 2: AZURE_WEBAPP_NAME**
- Name: `AZURE_WEBAPP_NAME`
- Value: `ai-career-path-app-<your-unique-id>`

---

## Deploy to Azure

### Step 5: Trigger GitHub Actions Deployment

#### Option 1: Automatic Deployment (on push to main)

Simply push any changes to the `main` branch:

```bash
git add .
git commit -m "Trigger deployment"
git push origin main
```

#### Option 2: Manual Deployment

1. Go to your GitHub repository
2. Click "Actions" tab
3. Select "Deploy to Azure Web App" workflow
4. Click "Run workflow" → "Run workflow"

#### Monitor Deployment

1. Go to "Actions" tab in GitHub
2. Click on the running workflow
3. Monitor the build and deploy steps
4. Wait for all steps to complete (usually 3-5 minutes)

---

## Verify Deployment

### Step 6: Test Your Application

#### 6.1 Check Health Endpoint

```bash
curl https://ai-career-path-app-<your-unique-id>.azurewebsites.net/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "AI Tech Career Path Finder"
}
```

#### 6.2 Open in Browser

Navigate to: `https://ai-career-path-app-<your-unique-id>.azurewebsites.net`

#### 6.3 Test Full Functionality

1. Fill out the questionnaire
2. Upload a resume (optional)
3. Generate career plan
4. Download PDF
5. Check Azure Storage containers for uploaded files

#### 6.4 Verify Azure Blob Storage

```bash
# List files in uploads container
az storage blob list \
  --container-name uploads \
  --account-name aicareerpath<your-unique-id> \
  --auth-mode login \
  --output table

# List files in generated container
az storage blob list \
  --container-name generated \
  --account-name aicareerpath<your-unique-id> \
  --auth-mode login \
  --output table
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Application Not Starting

**Symptoms**: 503 Service Unavailable

**Solutions**:
1. Check logs:
   ```bash
   az webapp log tail \
     --resource-group ai-career-path-rg \
     --name ai-career-path-app-<your-unique-id>
   ```
2. Verify `startup.sh` has correct permissions
3. Check Application Settings are configured correctly

#### Issue 2: Azure Blob Storage Access Denied

**Symptoms**: 403 Forbidden when uploading files

**Solutions**:
1. Verify Managed Identity is enabled
2. Check role assignment (Storage Blob Data Contributor)
3. Verify `AZURE_STORAGE_ACCOUNT_NAME` is correct
4. Check `USE_MANAGED_IDENTITY=true` in app settings

#### Issue 3: Azure OpenAI Errors

**Symptoms**: 401 Unauthorized or model not found

**Solutions**:
1. Verify `AZURE_OPENAI_ENDPOINT` is correct
2. Check `AZURE_OPENAI_API_KEY` is valid
3. Confirm `AZURE_OPENAI_DEPLOYMENT_NAME` matches your deployment
4. Ensure API version is correct

#### Issue 4: GitHub Actions Failing

**Symptoms**: Deployment fails in GitHub Actions

**Solutions**:
1. Verify secrets are set correctly:
   - `AZURE_WEBAPP_PUBLISH_PROFILE`
   - `AZURE_WEBAPP_NAME`
2. Check publish profile hasn't expired
3. Review workflow logs in GitHub Actions tab

#### Issue 5: PDF Generation Fails

**Symptoms**: Error when downloading PDF

**Solutions**:
1. Check if `generated` container exists
2. Verify write permissions to blob storage
3. Check application logs for specific errors

### View Application Logs

#### Method 1: Azure CLI
```bash
az webapp log tail \
  --resource-group ai-career-path-rg \
  --name ai-career-path-app-<your-unique-id>
```

#### Method 2: Azure Portal
1. Go to Web App → Monitoring → Log stream
2. View real-time logs

#### Method 3: Download Logs
```bash
az webapp log download \
  --resource-group ai-career-path-rg \
  --name ai-career-path-app-<your-unique-id> \
  --log-file app-logs.zip
```

---

## Updating the Application

### Making Changes

1. Make changes to your code locally
2. Test locally:
   ```bash
   python main.py
   ```
3. Commit and push:
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```
4. GitHub Actions will automatically deploy

### Rollback to Previous Version

```bash
# List deployments
az webapp deployment list \
  --resource-group ai-career-path-rg \
  --name ai-career-path-app-<your-unique-id>

# Rollback to specific deployment
az webapp deployment source rollback \
  --resource-group ai-career-path-rg \
  --name ai-career-path-app-<your-unique-id>
```

---

## Cost Optimization

### Free Tier Limits

- **App Service (F1)**: 60 CPU minutes/day, 1 GB RAM
- **Storage (LRS)**: First 5 GB free, then $0.02/GB/month
- **Azure OpenAI**: Pay per token usage

### Recommendations

1. Use Managed Identity (no key rotation costs)
2. Set up lifecycle management for old files in blob storage
3. Monitor usage with Azure Cost Management
4. Consider scaling up only when needed

---

## Security Best Practices

1. ✅ Never commit `.env` file to Git
2. ✅ Use Managed Identity instead of connection strings
3. ✅ Keep all secrets in GitHub Secrets or Azure Key Vault
4. ✅ Regularly rotate API keys
5. ✅ Enable HTTPS only (automatic on Azure Web Apps)
6. ✅ Use private blob storage containers
7. ✅ Implement rate limiting if needed
8. ✅ Monitor application for unusual activity

---

## Additional Resources

- [Azure App Service Documentation](https://docs.microsoft.com/azure/app-service/)
- [Azure Blob Storage Documentation](https://docs.microsoft.com/azure/storage/blobs/)
- [Azure OpenAI Documentation](https://docs.microsoft.com/azure/cognitive-services/openai/)
- [GitHub Actions Documentation](https://docs.github.com/actions)
- [Managed Identity Documentation](https://docs.microsoft.com/azure/active-directory/managed-identities-azure-resources/)

---

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review application logs
3. Check GitHub Actions workflow logs
4. Verify all Azure resources are running
5. Confirm all secrets and settings are configured

---

**Congratulations!** 🎉 Your AI Tech Career Path Finder is now deployed to Azure with CI/CD enabled!
