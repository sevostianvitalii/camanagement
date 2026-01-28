# GitLab Setup Guide for CA Policy Management Tool

Complete step-by-step guide to configure your GitLab project for automated Conditional Access policy validation and deployment.

---

## Prerequisites

- GitLab account (GitLab.com or self-hosted with GitLab 15.7+)
- Project Maintainer or Owner role
- **Azure AD configured** — Complete [AZURE_SETUP.md](./AZURE_SETUP.md) first
- Git installed locally
- Basic familiarity with GitLab CI/CD

---

## Part 1: Project Setup

### Step 1: Create or Import Project

**Option A: Create new project**

1. Go to GitLab → **New project** → **Create blank project**
2. Configure:
   - **Project name:** `ca-policy-management`
   - **Visibility:** Private (recommended)
3. Click **Create project**
4. Clone it locally:
   ```bash
   git clone https://gitlab.com/your-username/ca-policy-management.git
   cd ca-policy-management
   ```

**Option B: Import existing repository**

1. Go to GitLab → **New project** → **Import project**
2. Select source (GitHub, URL, etc.)
3. Clone your project:
   ```bash
   git clone https://gitlab.com/your-username/ca-policy-management.git
   cd ca-policy-management
   ```

### Step 2: Verify Project Structure

Ensure your project contains:

```
ca-policy-management/
├── .gitlab-ci.yml                     # GitLab CI pipeline
├── policies/
│   ├── prd/                           # Production policies
│   └── tst/                           # Test policies
├── baseline/
│   ├── compliance-rules.yaml          # Compliance validation rules
│   ├── naming-convention.yaml         # Naming standards
│   └── best-practices.yaml            # Microsoft best practices
├── src/ca_manager/                    # Python package
├── requirements.txt
└── README.md
```

---

## Part 2: Configure CI/CD Variables

### Step 3: Add Project Variables

GitLab CI uses OIDC to authenticate with Azure. You need to add these variables:

1. Go to your project on GitLab
2. Navigate to **Settings** → **CI/CD** → **Variables**
3. Click **Add variable**

Add the following variables:

| Variable Name | Value | Flags | Where to Find |
|---------------|-------|-------|---------------|
| `AZURE_CLIENT_ID` | Your Azure App Registration's Application (client) ID | ✅ Protected<br>✅ Masked | Azure Portal → App Registration → Overview |
| `AZURE_TENANT_ID` | Your Azure Directory (tenant) ID | ✅ Protected<br>✅ Masked | Azure Portal → App Registration → Overview |

**Configuration for each variable:**
- **Type:** Variable
- **Environment scope:** All (or specific environments)
- **Protect variable:** ✅ Checked (only available in protected branches)
- **Mask variable:** ✅ Checked (hidden in job logs)
- **Expand variable reference:** ❌ Unchecked

**Example:**
- Key: `AZURE_CLIENT_ID`
- Value: `12345678-1234-1234-1234-123456789abc`
- Flags: Protected ✅, Masked ✅

---

## Part 3: Verify Azure OIDC Federation

### Step 4: Confirm Federated Credential Configuration

Ensure your Azure App Registration has the correct federated credential for GitLab:

1. Go to **Azure Portal** → **App registrations** → Your app
2. Navigate to **Certificates & secrets** → **Federated credentials**
3. Verify you have a credential configured:
   - **Federated credential scenario:** Other issuer
   - **Issuer:** `https://gitlab.com`
   - **Subject identifier:** `project_path:your-group/your-project:ref_type:branch:ref:main`
   - **Audience:** `https://gitlab.com`

**Example subject identifier:**
```
project_path:mycompany/iam-team/ca-policy-management:ref_type:branch:ref:main
```

**If not configured**, follow [AZURE_SETUP.md Part 3: Option B](./AZURE_SETUP.md#option-b-gitlab-ci-workload-identity-federation) to set it up.

---

## Part 4: Verify Pipeline Configuration

### Step 5: Review .gitlab-ci.yml

Your `.gitlab-ci.yml` should be configured for OIDC authentication:

```yaml
.azure_oidc:
  id_tokens:
    AZURE_OIDC_TOKEN:
      aud: api://AzureADTokenExchange
```

The `deploy_policies` job should extend this and use the token:

```yaml
deploy_policies:
  stage: deploy
  extends: .azure_oidc
  script:
    - export ARM_CLIENT_ID="${AZURE_CLIENT_ID}"
    - export ARM_TENANT_ID="${AZURE_TENANT_ID}"
    - export ARM_OIDC_TOKEN="${AZURE_OIDC_TOKEN}"
```

**Note:** The `AZURE_OIDC_TOKEN` is automatically provided by GitLab when you configure `id_tokens` in your pipeline.

---

## Part 5: Test the Pipeline

### Step 6: Create a Test Policy

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
     justification: "Testing GitLab CI pipeline"
   
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

### Step 7: Create Merge Request

1. Go to GitLab and create a Merge Request from `test-policy` to `main`
2. The pipeline should automatically trigger
3. Navigate to **CI/CD** → **Pipelines** to view the run

**Expected pipeline jobs:**
```
validate:
  ✅ Validate naming conventions
  ✅ Validate compliance rules
  ✅ Check Microsoft best practices
  ✅ Detect conflicts
```

### Step 8: Review Pipeline Output

Click on the pipeline run to view detailed job logs:
- Check **validate_policies** job for validation results
- Review any warnings or errors
- Verify all compliance checks pass

### Step 9: Test Deployment (Optional)

After validation passes:

1. Merge the Merge Request to `main`
2. The deployment pipeline will trigger automatically
3. Navigate to **CI/CD** → **Pipelines** → Select the deployment run

**Expected deployment jobs:**
```
deploy_policies:
  ✅ Install dependencies
  ✅ Export OIDC token
  ✅ Deploy policies (dry-run or live)
```

---

## Part 6: Merge Request Settings (Recommended)

### Step 10: Configure Merge Request Approvals

Protect your `main` branch and enforce validation:

1. Go to **Settings** → **Merge requests**
2. Configure:
   - ✅ **Enable "Delete source branch" option by default**
   - ✅ **Pipelines must succeed**
   - ✅ **All threads must be resolved**

### Step 11: Enable Protected Branches

1. Go to **Settings** → **Repository** → **Protected branches**
2. Protect `main` branch:
   - **Allowed to merge:** Maintainers (or specific role)
   - **Allowed to push:** No one (force MR workflow)
   - ✅ **Require approval from code owners**
   - ✅ **Allowed to force push:** No one

---

## Part 7: Switch to Live Deployment

### Step 12: Enable Production Deployment

**⚠️ IMPORTANT:** Only do this after testing in dry-run mode!

Edit `.gitlab-ci.yml` in the `deploy_policies` job:

**Current configuration (dry-run):**
```yaml
script:
  - |
    echo "Running dry-run deployment..."
    python -m ca_manager deploy --path policies/ --dry-run
    
    # Uncomment below for actual deployment
    # echo "Deploying policies to Azure AD..."
    # python -m ca_manager deploy --path policies/ --no-dry-run
```

**To enable live deployment, uncomment:**
```yaml
script:
  - |
    echo "Deploying policies to Azure AD..."
    python -m ca_manager deploy --path policies/ --no-dry-run
```

Commit and push the change.

---

## Troubleshooting

### Issue: Pipeline doesn't trigger

**Cause:** `.gitlab-ci.yml` is missing or rules don't match your changes.

**Solution:**
1. Ensure `.gitlab-ci.yml` exists in repository root
2. Verify the file is on the correct branch (`main`)
3. Check `rules:` section includes your changed paths:
   ```yaml
   rules:
     - changes:
         - policies/**/*.yaml
         - policies/**/*.yml
   ```
4. Manually trigger pipeline: **CI/CD** → **Pipelines** → **Run pipeline**

---

### Issue: "OIDC token not found" or "AZURE_OIDC_TOKEN is empty"

**Cause:** `id_tokens` not configured in `.gitlab-ci.yml`.

**Solution:**
Ensure your pipeline has the `.azure_oidc` configuration:
```yaml
.azure_oidc:
  id_tokens:
    AZURE_OIDC_TOKEN:
      aud: api://AzureADTokenExchange
```

And your job extends it:
```yaml
deploy_policies:
  extends: .azure_oidc
```

---

### Issue: "Failed to exchange OIDC token for Azure token"

**Cause:** Federated credential subject identifier doesn't match.

**Solution:**
1. Get your exact project path from GitLab URL (e.g., `myorg/iam-team/ca-policy-management`)
2. Verify subject identifier in Azure:
   ```
   project_path:myorg/iam-team/ca-policy-management:ref_type:branch:ref:main
   ```
3. Ensure it exactly matches (case-sensitive, including slashes)
4. Verify audience is `https://gitlab.com`

**Debug:** Add this to your pipeline script to see the actual claims:
```yaml
script:
  - echo "OIDC Token Claims:"
  - echo $AZURE_OIDC_TOKEN | cut -d'.' -f2 | base64 -d | jq
```

---

### Issue: "Variables are protected and not available"

**Cause:** Pipeline running on unprotected branch, but variables are protected.

**Solution:**
- **Option 1:** Uncheck "Protected" flag on variables (less secure)
- **Option 2:** Make your branch protected:
  - **Settings** → **Repository** → **Protected branches**
  - Add your branch pattern (e.g., `test-*`)

---

### Issue: Authentication fails with "invalid_client"

**Cause:** Variables are incorrect or masked improperly.

**Solution:**
1. Re-check `AZURE_CLIENT_ID` and `AZURE_TENANT_ID` values
2. Ensure no extra spaces or line breaks were copied
3. Verify values match your Azure App Registration
4. Try creating new variables (delete old ones first)

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
- Use OIDC federation (no long-lived secrets in GitLab)
- Enable protected branches for `main`
- Require MR approvals before merging policy changes
- Use **Protected** and **Masked** flags for variables
- Start new policies in `enabledForReportingButNotEnforced` state
- Review pipeline logs before merging

### ❌ Don't:
- Store Azure client secrets in variables (use OIDC instead)
- Skip validation by pushing directly to `main`
- Deploy policies without testing in report-only mode first
- Remove break-glass exclusions from policies
- Use unmasked variables for sensitive data
- Bypass MR approvals for "quick fixes"

---

## Next Steps

After GitLab is configured:

1. **Review Pipeline Logs:** Check the Pipelines tab for any warnings
2. **Create Your First Policy:** Use templates from `templates/` directory
3. **Test Validation:** Create an MR and verify all checks pass
4. **Deploy to Azure:** Merge MR and verify policy appears in Azure Portal
5. **Monitor Azure AD:** Check sign-in logs to verify policy behavior

---

## Quick Reference

### GitLab Project Links
- **Pipelines:** `https://gitlab.com/your-group/ca-policy-management/-/pipelines`
- **Variables:** `https://gitlab.com/your-group/ca-policy-management/-/settings/ci_cd`
- **Protected Branches:** `https://gitlab.com/your-group/ca-policy-management/-/settings/repository`
- **Merge Requests:** `https://gitlab.com/your-group/ca-policy-management/-/merge_requests`

### Common Commands
```bash
# Create test policy branch
git checkout -b test-policy

# Validate locally before pushing
python -m ca_manager validate --check all --path policies/

# View recent pipelines (requires GitLab CLI)
glab ci list

# View pipeline logs
glab ci view
```

### OIDC Token Debugging
Add to your pipeline script to debug OIDC token:
```yaml
script:
  - echo "Decoding OIDC token claims..."
  - echo $AZURE_OIDC_TOKEN | cut -d'.' -f2 | base64 -d | jq .
```

Expected claims should include:
- `iss`: `https://gitlab.com`
- `sub`: `project_path:your-group/your-project:ref_type:branch:ref:main`
- `aud`: `api://AzureADTokenExchange`

---

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review pipeline job logs in the **CI/CD** tab
3. Verify all prerequisites in [AZURE_SETUP.md](./AZURE_SETUP.md) are complete
4. Test OIDC token generation by adding debug commands

**Pipeline Logs Location:**  
GitLab → Your project → CI/CD → Pipelines → Select pipeline → Click job name for detailed logs

**Azure AD Audit Logs:**  
Azure Portal → Azure Active Directory → Monitoring → Audit logs
