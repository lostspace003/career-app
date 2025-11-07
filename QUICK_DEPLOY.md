# 1 Azure Deployment Quick Reference

## Quick Setup Commands

### 1. Create Azure Resources (5 minutes)

```bash
# Variables (customize these)
RG_NAME="ai-career-path-rg"
LOCATION="eastus"
STORAGE_NAME="aicareerpath$(date +%s)"  # Adds timestamp for uniqueness
WEBAPP_NAME="ai-career-path-app-$(date +%s)"
OPENAI_NAME="ai-career-openai"

# Login and create resource group
az login
az group create --name $RG_NAME --location $LOCATION

# Create storage account
az storage account create \
  --name $STORAGE_NAME \
  --resource-group $RG_NAME \
  --location $LOCATION \
  --sku Standard_LRS \
  --allow-blob-public-access false

# Create containers
az storage container create --name uploads --account-name $STORAGE_NAME --auth-mode login
az storage container create --name generated --account-name $STORAGE_NAME --auth-mode login

# Create App Service Plan (Free Tier)
az appservice plan create \
  --name ai-career-path-plan \
  --resource-group $RG_NAME \
  --sku F1 \
  --is-linux

# Create Web App
az webapp create \
  --resource-group $RG_NAME \
  --plan ai-career-path-plan \
  --name $WEBAPP_NAME \
  --runtime "PYTHON:3.11" \
  --startup-file "startup.sh"

# Enable Managed Identity
az webapp identity assign --resource-group $RG_NAME --name $WEBAPP_NAME

# Grant Storage Access
PRINCIPAL_ID=$(az webapp identity show --resource-group $RG_NAME --name $WEBAPP_NAME --query principalId -o tsv)
STORAGE_ID=$(az storage account show --name $STORAGE_NAME --resource-group $RG_NAME --query id -o tsv)
az role assignment create --assignee $PRINCIPAL_ID --role "Storage Blob Data Contributor" --scope $STORAGE_ID
```

### 2. Configure Web App Settings

```bash
# Get OpenAI credentials (if using Azure OpenAI)
OPENAI_ENDPOINT="https://your-openai-resource.openai.azure.com/"
OPENAI_KEY="your-openai-key"

# Set application settings
az webapp config appsettings set \
  --resource-group $RG_NAME \
  --name $WEBAPP_NAME \
  --settings \
    AZURE_OPENAI_ENDPOINT="$OPENAI_ENDPOINT" \
    AZURE_OPENAI_API_KEY="$OPENAI_KEY" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o" \
    AZURE_OPENAI_API_VERSION="2024-12-01-preview" \
    USE_MANAGED_IDENTITY="true" \
    AZURE_STORAGE_ACCOUNT_NAME="$STORAGE_NAME" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true"
```

### 3. Setup GitHub Repository

```bash
# In your project directory
git init
git add .
git commit -m "Initial commit with Azure deployment"

# Create repo on GitHub, then:
git remote add origin https://github.com/<your-username>/ai-career-path-finder.git
git branch -M main
git push -u origin main
```

### 4. Configure GitHub Secrets

```bash
# Get publish profile
az webapp deployment list-publishing-profiles \
  --resource-group $RG_NAME \
  --name $WEBAPP_NAME \
  --xml > publish-profile.xml

# View your webapp name
echo $WEBAPP_NAME
```

Then in GitHub:
1. Go to Settings → Secrets → Actions
2. Add `AZURE_WEBAPP_PUBLISH_PROFILE` (content from publish-profile.xml)
3. Add `AZURE_WEBAPP_NAME` (value from $WEBAPP_NAME)

### 5. Deploy

```bash
# Push to trigger deployment
git push origin main
```

---

## Useful Commands

### View Logs
```bash
az webapp log tail --resource-group $RG_NAME --name $WEBAPP_NAME
```

### Restart App
```bash
az webapp restart --resource-group $RG_NAME --name $WEBAPP_NAME
```

### Check App URL
```bash
echo "https://$WEBAPP_NAME.azurewebsites.net"
```

### List Blob Files
```bash
az storage blob list --container-name uploads --account-name $STORAGE_NAME --auth-mode login --output table
az storage blob list --container-name generated --account-name $STORAGE_NAME --auth-mode login --output table
```

### Test Health Endpoint
```bash
curl https://$WEBAPP_NAME.azurewebsites.net/health
```

### Delete All Resources (cleanup)
```bash
az group delete --name $RG_NAME --yes --no-wait
```

---

## GitHub Secrets Required

| Secret Name | Description | How to Get |
|------------|-------------|------------|
| `AZURE_WEBAPP_PUBLISH_PROFILE` | Deployment credentials | `az webapp deployment list-publishing-profiles` |
| `AZURE_WEBAPP_NAME` | Web app name | Your chosen webapp name |

---

## Azure App Settings Required

| Setting | Example Value | Required |
|---------|--------------|----------|
| `AZURE_OPENAI_ENDPOINT` | `https://....openai.azure.com/` | Yes |
| `AZURE_OPENAI_API_KEY` | `sk-...` | Yes |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | `gpt-4o` | Yes |
| `AZURE_OPENAI_API_VERSION` | `2024-12-01-preview` | Yes |
| `USE_MANAGED_IDENTITY` | `true` | Yes |
| `AZURE_STORAGE_ACCOUNT_NAME` | `aicareerpath123` | Yes |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | Yes |

---

## Verification Checklist

- [ ] Resource group created
- [ ] Storage account created with `uploads` and `generated` containers
- [ ] Web App created (F1 tier)
- [ ] Managed Identity enabled
- [ ] Storage role assignment completed
- [ ] App settings configured
- [ ] GitHub repository created
- [ ] GitHub secrets configured
- [ ] First deployment successful
- [ ] Health endpoint returns 200
- [ ] Web app loads in browser
- [ ] Can generate career plan
- [ ] Files appear in blob storage

---

## Common URLs

- **Your App**: `https://<WEBAPP_NAME>.azurewebsites.net`
- **Health Check**: `https://<WEBAPP_NAME>.azurewebsites.net/health`
- **Azure Portal**: https://portal.azure.com
- **GitHub Actions**: `https://github.com/<username>/ai-career-path-finder/actions`

---

## Troubleshooting One-Liners

```bash
# Check if app is running
curl -I https://$WEBAPP_NAME.azurewebsites.net

# View last 50 log lines
az webapp log tail --resource-group $RG_NAME --name $WEBAPP_NAME --lines 50

# Check managed identity
az webapp identity show --resource-group $RG_NAME --name $WEBAPP_NAME

# Verify role assignment
az role assignment list --assignee $PRINCIPAL_ID --all

# Test blob access
az storage blob list --container-name uploads --account-name $STORAGE_NAME --auth-mode login
```
