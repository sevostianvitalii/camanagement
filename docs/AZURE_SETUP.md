# Azure Setup Guide for CA Policy Management Tool

Complete step-by-step guide to configure Azure AD for OIDC authentication with GitHub Actions and GitLab CI.

---

## Prerequisites

- Azure AD tenant with Global Administrator or Application Administrator role
- Access to Azure Portal (https://portal.azure.com)
- GitHub repository or GitLab project set up

---

## Part 1: Create Azure AD App Registration

### Step 1: Create the App Registration

1. Go to **Azure Portal** → **Azure Active Directory** → **App registrations**
2. Click **+ New registration**
3. Configure:
   - **Name:** `CA-Policy-Manager-OIDC`
   - **Supported account types:** "Accounts in this organizational directory only (Single tenant)"
   - **Redirect URI:** Leave blank for now
4. Click **Register**

### Step 2: Note Important IDs

After creation, go to the **Overview** page and copy these values:

```bash
Application (client) ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Directory (tenant) ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

**Save these!** You'll need them for CI/CD configuration.

---

## Part 2: Configure API Permissions

### Step 3: Add Microsoft Graph Permissions

1. In your app registration, go to **API permissions**
2. Click **+ Add a permission**
3. Select **Microsoft Graph** → **Application permissions**
4. Search and add these permissions:
   - `Policy.ReadWrite.ConditionalAccess`
   - `Directory.Read.All`
5. Click **Add permissions**
6. Click **✓ Grant admin consent for [Your Tenant]**
7. Confirm the consent

**Verify:** All permissions should show a green checkmark under "Status"

---

## Part 3: Set Up OIDC Federation

### Option A: GitHub Actions (Workload Identity Federation)

#### Step 4A: Create Federated Credential for GitHub

1. In your app registration, go to **Certificates & secrets**
2. Click **Federated credentials** tab
3. Click **+ Add credential**
4. Select **GitHub Actions deploying Azure resources**
5. Configure:
   - **Organization:** Your GitHub username/org (e.g., `myorg`)
   - **Repository:** Repository name (e.g., `ca-policy-management`)
   - **Entity type:** Select **Branch**
   - **Based on selection:** `main` (or your default branch)
   - **Credential details → Name:** `github-main-branch`
6. Click **Add**

#### Step 5A: Add GitHub Secrets

1. Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**
2. Add these repository secrets:
   - `AZURE_CLIENT_ID`: Your Application (client) ID
   - `AZURE_TENANT_ID`: Your Directory (tenant) ID
   - `AZURE_SUBSCRIPTION_ID`: Your Azure subscription ID

**Get subscription ID:**
```bash
az account show --query id -o tsv
```

---

### Option B: GitLab CI (Workload Identity Federation)

#### Step 4B: Create Federated Credential for GitLab

1. In your app registration, go to **Certificates & secrets**
2. Click **Federated credentials** tab
3. Click **+ Add credential**
4. Select **Other issuer**
5. Configure:
   - **Issuer:** `https://gitlab.com`
   - **Subject identifier:** `project_path:your-group/your-project:ref_type:branch:ref:main`
     - Replace `your-group/your-project` with your GitLab project path
   - **Credential details → Name:** `gitlab-main-branch`
   - **Audience:** `https://gitlab.com`
6. Click **Add**

**Example subject identifier:**
```
project_path:mycompany/iam-team/ca-policy-management:ref_type:branch:ref:main
```

#### Step 5B: Add GitLab CI/CD Variables

1. Go to your GitLab project → **Settings** → **CI/CD** → **Variables**
2. Add these variables:
   - `AZURE_CLIENT_ID`: Your Application (client) ID (Protected ✓, Masked ✓)
   - `AZURE_TENANT_ID`: Your Directory (tenant) ID (Protected ✓, Masked ✓)

---

## Part 4: Test Authentication Locally (Optional)

### Step 6: Test with Azure CLI

```bash
# Install Azure CLI if not already installed
# https://docs.microsoft.com/en-us/cli/azure/install-azure-cli

# Login with your user account
az login --tenant YOUR_TENANT_ID

# Test Graph API access
az rest --method GET \
  --url 'https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies' \
  --headers "Content-Type=application/json"
```

If successful, you should see a JSON response with your existing CA policies (or an empty array if none exist).

---

## Part 5: Verify CI/CD Pipeline

### Step 7A: Test GitHub Actions

1. Push the CA policy management code to your GitHub repository
2. Create a test policy file in `policies/prd/`
3. Create a Pull Request
4. Check **Actions** tab - the validation workflow should run
5. Merge the PR to trigger deployment (dry-run by default)

**Expected workflow:**
```
✅ Validate naming conventions
✅ Validate compliance
✅ Check Microsoft best practices
✅ Detect conflicts
✅ Azure OIDC Login
✅ Deploy policies (dry-run)
```

### Step 7B: Test GitLab CI

1. Push the CA policy management code to your GitLab repository
2. Create a test policy file in `policies/prd/`
3. Create a Merge Request
4. Check **CI/CD** → **Pipelines** - validation should run
5. Merge the MR to trigger deployment (dry-run by default)

---

## Part 6: Enable Production Deployment

### Step 8: Switch from Dry-Run to Live Deployment

**IMPORTANT:** Only do this after testing dry-run mode!

#### For GitHub Actions:

Edit `.github/workflows/ca-validate-deploy.yml`:

```yaml
# Uncomment these lines in the deploy job:
- name: Deploy policies (live)
  run: |
    python -m ca_manager deploy --path policies/ --no-dry-run
  env:
    AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
```

#### For GitLab CI:

Edit `.gitlab-ci.yml`:

```yaml
# Uncomment these lines in deploy_policies job:
# echo "Deploying policies to Azure AD..."
# python -m ca_manager deploy --path policies/ --no-dry-run
```

Commit and push the changes.

---

## Part 7: Break-Glass Account Setup

### Step 9: Create Break-Glass Group

1. Go to **Azure Portal** → **Azure Active Directory** → **Groups**
2. Click **+ New group**
3. Configure:
   - **Group type:** Security
   - **Group name:** `AAD-BreakGlass-Accounts`
   - **Members:** Add your emergency access accounts
4. Click **Create**

5. Update your baseline compliance rules to reference this group (already configured in `baseline/compliance-rules.yaml`)

---

## Troubleshooting

### Issue: "Insufficient privileges to complete the operation"

**Solution:** Ensure you granted admin consent for the API permissions in Step 3.

### Issue: "AADSTS700016: Application not found"

**Solution:** Verify the `AZURE_CLIENT_ID` secret matches your App Registration's Application ID.

### Issue: "Failed to exchange OIDC token"

**Solution:**
1. Check the federated credential's subject identifier matches your repo/branch
2. Ensure the credential is for the correct branch (main vs master)
3. Verify `AZURE_TENANT_ID` is correct

### Issue: "Policy.ReadWrite.ConditionalAccess not granted"

**Solution:** 
1. Re-grant admin consent in **API permissions**
2. Wait 5-10 minutes for Azure to propagate permissions

---

## Security Best Practices

### ✅ Do:
- Use OIDC federation (no long-lived secrets)
- Rotate break-glass account passwords regularly
- Start new policies in report-only mode
- Review all policies before enabling enforcement
- Keep baseline rules in version control

### ❌ Don't:
- Store client secrets in git (use OIDC instead)
- Grant unnecessary API permissions
- Deploy directly to production without testing
- Disable break-glass account exclusions
- Skip PR/MR reviews for policy changes

---

## Next Steps

After Azure is configured:

1. **Test validation:** Create a test policy and validate locally
2. **Test CI/CD:** Push a policy via PR/MR and verify the pipeline runs
3. **Deploy test policy:** Merge a report-only policy to test deployment
4. **Monitor Azure AD:** Check Azure Portal to verify policy was created
5. **Enable enforcement:** After testing, change policy state to `enabled`

---

## Quick Reference

### Azure Portal Links
- **App Registrations:** https://portal.azure.com/#view/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/~/RegisteredApps
- **Conditional Access:** https://portal.azure.com/#view/Microsoft_AAD_ConditionalAccess/ConditionalAccessBlade/~/Policies
- **Azure AD Groups:** https://portal.azure.com/#view/Microsoft_AAD_IAM/GroupsManagementMenuBlade/~/AllGroups

### CLI Commands
```bash
# List CA policies
az rest --method GET --url 'https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies'

# Get specific policy
az rest --method GET --url 'https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies/{policy-id}'

# List groups
az ad group list --query "[].{Name:displayName, Id:id}" -o table
```

---

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review Azure AD audit logs for detailed error messages
3. Verify all IDs/secrets are correct and not expired
4. Ensure your user account has sufficient permissions

**Azure AD Audit Logs:**  
Azure Portal → Azure Active Directory → Monitoring → Audit logs
