# GitHub Setup Guide for CA Policy Management Tool

Complete step-by-step guide to configure your GitHub repository for automated Conditional Access policy validation and deployment.

---

## Prerequisites

- GitHub account with repository admin access
- **Azure AD configured** — Complete [AZURE_SETUP.md](./AZURE_SETUP.md) first
- Git installed locally
- Basic familiarity with GitHub Actions

---

## Part 1: Repository Setup

### Step 1: Create or Fork Repository

**Option A: Start from scratch**

1. Create a new repository on GitHub
2. Clone it locally:
   ```bash
   git clone https://github.com/your-username/ca-policy-management.git
   cd ca-policy-management
   ```

**Option B: Fork existing project**

1. Fork the CA Policy Management repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/ca-policy-management.git
   cd ca-policy-management
   ```

### Step 2: Verify Repository Structure

Ensure your repository contains:

```
ca-policy-management/
├── .github/
│   └── workflows/
│       └── ca-validate-deploy.yml    # GitHub Actions workflow
├── policies/
│   ├── prd/                          # Production policies
│   └── tst/                          # Test policies
├── baseline/
│   ├── compliance-rules.yaml         # Compliance validation rules
│   ├── naming-convention.yaml        # Naming standards
│   └── best-practices.yaml           # Microsoft best practices
├── src/ca_manager/                   # Python package
├── requirements.txt
└── README.md
```

---

## Part 2: Configure GitHub Secrets

### Step 3: Add Repository Secrets

GitHub Actions uses OIDC to authenticate with Azure. You need to add these secrets:

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

Add the following secrets:

| Secret Name | Value | Where to Find |
|-------------|-------|---------------|
| `AZURE_CLIENT_ID` | Your Azure App Registration's Application (client) ID | Azure Portal → App Registration → Overview |
| `AZURE_TENANT_ID` | Your Azure Directory (tenant) ID | Azure Portal → App Registration → Overview |
| `AZURE_SUBSCRIPTION_ID` | Your Azure subscription ID (optional) | Run `az account show --query id -o tsv` |

**Example:**
- Secret name: `AZURE_CLIENT_ID`
- Secret value: `12345678-1234-1234-1234-123456789abc`

> **Note:** `AZURE_SUBSCRIPTION_ID` is optional for this tool since we only interact with Microsoft Graph API, not Azure Resource Manager.

---

## Part 3: Verify Azure OIDC Federation

### Step 4: Confirm Federated Credential Configuration

Ensure your Azure App Registration has the correct federated credential for GitHub:

1. Go to **Azure Portal** → **App registrations** → Your app
2. Navigate to **Certificates & secrets** → **Federated credentials**
3. Verify you have a credential configured:
   - **Federated credential scenario:** GitHub Actions deploying Azure resources
   - **Organization:** Your GitHub username or organization
   - **Repository:** Your repository name
   - **Entity type:** Branch
   - **Based on selection:** `main` (or your default branch)

**If not configured**, follow [AZURE_SETUP.md Part 3: Option A](./AZURE_SETUP.md#option-a-github-actions-workload-identity-federation) to set it up.

---

## Part 4: Test the Workflow

### Step 5: Create a Test Policy

1. Create a new branch:
   ```bash
   git checkout -b test-policy
   ```

2. Create a test policy file `policies/tst/en-tst-ca-test-mfa-001.yaml`:
   ```yaml
   name: en-tst-ca-test-mfa-001
   displayName: "Test MFA Policy"
   state: enabledForReportingButNotEnforced
   
   metadata:
     owner: "your-email@example.com"
     ticketId: "TEST-001"
     justification: "Testing GitHub Actions workflow"
   
   conditions:
     users:
       includeUsers:
         - "All"
       excludeGroups:
         - "AAD-BreakGlass-Accounts"
   
   grantControls:
     operator: "OR"
     builtInControls:
       - "mfa"
   ```

3. Commit and push:
   ```bash
   git add policies/tst/en-tst-ca-test-mfa-001.yaml
   git commit -m "test: Add test MFA policy"
   git push origin test-policy
   ```

### Step 6: Create Pull Request

1. Go to GitHub and create a Pull Request from `test-policy` to `main`
2. The workflow should automatically trigger
3. Navigate to **Actions** tab to view the run

**Expected workflow steps:**
```
✅ Checkout code
✅ Set up Python
✅ Install dependencies
✅ Validate naming conventions
✅ Validate compliance
✅ Check Microsoft best practices
✅ Detect conflicts
✅ Comment on PR (validation report)
```

### Step 7: Verify Validation Report

The workflow will automatically comment on your PR with a validation report. Review it for:
- ✅ Naming convention compliance
- ✅ Baseline compliance (break-glass exclusions)
- ✅ Best practices adherence
- ⚠️ Any warnings or conflicts

### Step 8: Test Deployment (Optional)

After the validation passes:

1. Merge the Pull Request to `main`
2. The deployment workflow will trigger automatically
3. Check **Actions** tab → **Deploy to Azure** job

**Expected deployment steps:**
```
✅ Checkout code
✅ Set up Python
✅ Install dependencies
✅ Azure OIDC Login
✅ Deploy policies (dry-run or live)
```

---

## Part 5: Branch Protection Rules (Recommended)

### Step 9: Enable Branch Protection

Protect your `main` branch to enforce validation before deployment:

1. Go to **Settings** → **Branches**
2. Click **Add branch protection rule**
3. Configure:
   - **Branch name pattern:** `main`
   - ✅ **Require a pull request before merging**
   - ✅ **Require status checks to pass before merging**
     - Select: `Validate Policies`
   - ✅ **Require conversation resolution before merging**
   - ✅ **Do not allow bypassing the above settings**

---

## Part 6: Switch to Live Deployment

### Step 10: Enable Production Deployment

**⚠️ IMPORTANT:** Only do this after testing in dry-run mode!

Edit `.github/workflows/ca-validate-deploy.yml`:

**Current configuration (dry-run):**
```yaml
- name: Deploy policies (dry-run)
  if: false # Disable dry-run to prioritize live deployment
  run: |
    python -m ca_manager deploy --path policies/ --dry-run
```

**To enable live deployment, the workflow already has:**
```yaml
- name: Deploy policies (live)
  run: |
    python -m ca_manager deploy --path policies/ --no-dry-run
  env:
    AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
    AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
```

The live deployment is already active. If you want dry-run first, change `if: false` to `if: true` in the dry-run step.

---

## Troubleshooting

### Issue: Workflow doesn't trigger

**Cause:** Workflow file is missing or triggers are misconfigured.

**Solution:**
1. Ensure `.github/workflows/ca-validate-deploy.yml` exists
2. Verify the file is on the correct branch (`main`)
3. Check the `on:` section includes your trigger paths
4. Try pushing a change to a monitored file (e.g., `policies/**/*.yaml`)

---

### Issue: "Error: Unable to get ACTIONS_ID_TOKEN_REQUEST_TOKEN"

**Cause:** OIDC permissions not configured in workflow.

**Solution:**
Ensure your workflow has these permissions:
```yaml
permissions:
  id-token: write
  contents: read
  pull-requests: write
```

---

### Issue: "AADSTS70021: No matching federated identity record found"

**Cause:** Federated credential in Azure doesn't match your repository/branch.

**Solution:**
1. Verify federated credential in Azure App Registration
2. Ensure **Organization** matches your GitHub username/org exactly
3. Ensure **Repository** matches your repo name exactly
4. Ensure **Entity type** is "Branch" and branch is `main` (or your default)

---

### Issue: "Authentication failed" in deployment step

**Cause:** Secrets are incorrect or not set.

**Solution:**
1. Verify `AZURE_CLIENT_ID` and `AZURE_TENANT_ID` in GitHub Secrets
2. Ensure values match your Azure App Registration (no typos)
3. Check that federated credential is properly configured in Azure

---

### Issue: "Policy.ReadWrite.ConditionalAccess permission denied"

**Cause:** Azure App Registration doesn't have proper Graph API permissions.

**Solution:**
1. Go to Azure Portal → App Registration → API permissions
2. Verify `Policy.ReadWrite.ConditionalAccess` is granted
3. Click **Grant admin consent** if status shows "Not granted"
4. Wait 5-10 minutes for permissions to propagate

---

## Security Best Practices

### ✅ Do:
- Use OIDC federation (no long-lived secrets in GitHub)
- Enable branch protection on `main`
- Require PR reviews before merging policy changes
- Start new policies in `enabledForReportingButNotEnforced` state
- Review validation reports before merging

### ❌ Don't:
- Store Azure client secrets in repository secrets (use OIDC instead)
- Skip validation by pushing directly to `main`
- Deploy policies without testing in report-only mode first
- Remove break-glass exclusions from policies
- Bypass PR reviews for "quick fixes"

---

## Next Steps

After GitHub is configured:

1. **Review Workflow Logs:** Check the Actions tab for any warnings
2. **Create Your First Policy:** Use templates from `templates/` directory
3. **Test Validation:** Create a PR and verify all checks pass
4. **Deploy to Azure:** Merge PR and verify policy appears in Azure Portal
5. **Monitor Azure AD:** Check sign-in logs to verify policy behavior

---

## Quick Reference

### GitHub Links
- **Actions:** `https://github.com/your-username/ca-policy-management/actions`
- **Secrets:** `https://github.com/your-username/ca-policy-management/settings/secrets/actions`
- **Branch Protection:** `https://github.com/your-username/ca-policy-management/settings/branches`

### Common Commands
```bash
# Create test policy branch
git checkout -b test-policy

# Validate locally before pushing
python -m ca_manager validate --check all --path policies/

# View workflow runs
gh run list  # Requires GitHub CLI

# View latest workflow run logs
gh run view --log
```

---

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review workflow logs in the **Actions** tab
3. Verify all prerequisites in [AZURE_SETUP.md](./AZURE_SETUP.md) are complete
4. Test authentication locally with `az login`

**Workflow Logs Location:**  
GitHub → Your repository → Actions → Select workflow run → Click job for detailed logs
