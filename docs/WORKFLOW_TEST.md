# GitHub Actions Workflow Test Guide

## ✅ Test Policy Created and Pushed

**Branch:** `test/verify-workflow`  
**Policy:** `en-prd-ca-allusers-compliant-device-001.yaml`  
**Status:** All validations passed locally ✅

---

## Next Steps: Create Pull Request and Verify Workflow

### Step 1: Create Pull Request on GitHub

1. **Go to:** https://github.com/sevostianvitalii/camanagement/pull/new/test/verify-workflow

   OR

2. **Navigate manually:**
   - Go to https://github.com/sevostianvitalii/camanagement
   - You should see a yellow banner: "test/verify-workflow had recent pushes"
   - Click **"Compare & pull request"**

3. **Fill in PR details:**
   - **Title:** `test: verify GitHub Actions validation workflow`
   - **Description:**
     ```
     ## Testing GitHub Actions Workflow
     
     This PR adds a test policy to verify the automated validation pipeline.
     
     **New Policy:**
     - Name: `en-prd-ca-allusers-compliant-device-001`
     - Scope: All employees
     - Control: Compliant device requirement
     - State: Report-only mode
     
     **Expected Workflow Checks:**
     - ✅ Validate naming conventions
     - ✅ Validate compliance rules
     - ✅ Check Microsoft best practices
     - ✅ Detect conflicts
     ```

4. **Click:** "Create pull request"

---

### Step 2: Watch GitHub Actions Run

Once the PR is created, GitHub Actions will automatically start:

1. **Go to the PR page**
2. **Scroll down to "Checks" section** - You should see:
   ```
   ⏳ Validate Policies / validate (pull_request)
   ```

3. **Click "Details"** to watch the workflow run in real-time

4. **Expected workflow steps:**
   ```
   ✅ Checkout code
   ✅ Set up Python
   ✅ Install dependencies
   ✅ Validate naming conventions
   ✅ Validate compliance
   ✅ Check Microsoft best practices
   ✅ Detect conflicts
   ✅ Comment on PR (with validation report)
   ```

---

### Step 3: Review Validation Report Comment

After the workflow completes (~1-2 minutes), the bot will post a comment on your PR with:

- ✅ **Naming validation results** (table showing all policies)
- ⚠️ **Compliance issues** (if any)
- ℹ️ **Best practice recommendations**
- 🔍 **Conflict detection results**

**Expected output:** 
- Your new test policy should show as **✅ Valid**
- The existing `en-prd-ca-externals-block-legacy-001` policy will show compliance warnings (this is intentional for testing)

---

### Step 4: Verify All Checks Passed

Look for the green checkmark at the top of the PR:

```
✅ All checks have passed
```

Even though there are compliance warnings, the workflow should pass because:
- The warnings are from the **existing** test policy (not the new one)
- Your new policy follows all rules correctly

---

### Step 5: Merge the PR (Optional)

If you want to test the deployment workflow:

1. **Click "Merge pull request"**
2. **Confirm merge**
3. **Watch the deploy workflow run:**
   - Go to: **Actions** tab → **CA Policy Validation and Deployment**
   - The latest run should show both:
     - ✅ **validate** job (from the PR)
     - 🚀 **deploy** job (triggers after merge to main)

4. **Expected deploy job steps:**
   ```
   ✅ Checkout code
   ✅ Set up Python
   ✅ Install dependencies
   ✅ Azure OIDC Login
   ✅ Deploy policies (dry-run)
   ```

**Note:** Deployment is in **dry-run mode** by default (safe for testing)

---

## Troubleshooting

### Issue: Workflow doesn't start automatically

**Solution:**
- Check if the workflow file is in the main branch (it should be)
- Verify GitHub Actions is enabled: **Settings** → **Actions** → **General**
- Ensure the workflow file syntax is correct

### Issue: "Azure OIDC Login" step fails

**Possible causes:**
1. **Missing secrets:** Check Settings → Secrets and variables → Actions
   - `AZURE_CLIENT_ID`
   - `AZURE_TENANT_ID`
   - `AZURE_SUBSCRIPTION_ID`

2. **OIDC not configured:** Verify federated credential in Azure AD App Registration

3. **Permissions not granted:** Check API permissions have admin consent

### Issue: No validation report comment posted

**Solution:**
- Check if the workflow has permission to comment
- Go to **Settings** → **Actions** → **General** → **Workflow permissions**
- Ensure "Read and write permissions" is selected

---

## What You Should See (Screenshots)

### 1. PR with Checks Running
```
🟡 Some checks haven't completed yet
   ⏳ Validate Policies
      Details
```

### 2. All Checks Passed
```
✅ All checks have passed
   ✅ Validate Policies
```

### 3. Bot Comment Example
```
## CA Policy Validation Report

### Naming Validation
✅ All policies follow naming convention

### Compliance Check
⚠️ en-prd-ca-externals-block-legacy-001
  - HIGH: Scope 'externals' requires control 'mfa'

✅ en-prd-ca-allusers-compliant-device-001
  - No issues found
```

---

## Success Criteria

Your workflow test is successful if:

✅ GitHub Actions workflow starts automatically on PR  
✅ All validation steps complete without errors  
✅ Validation report is posted as a comment  
✅ New test policy shows no violations  
✅ PR shows green checkmark "All checks have passed"  

---

## Clean Up (After Testing)

Once you've verified everything works:

```bash
# Delete the test branch locally
git checkout main
git branch -D test/verify-workflow

# Delete the remote branch (or do it via GitHub UI)
git push origin --delete test/verify-workflow
```

---

## Next Steps After Successful Test

1. ✅ **Workflow validated** - CI/CD pipeline working
2. 📝 **Create real policies** - Start defining your actual CA policies
3. 🔄 **Follow the workflow:**
   - Create branch → Add/modify policy → Create PR → Review → Merge
4. 🚀 **Enable live deployment** (when ready):
   - Uncomment deployment lines in `.github/workflows/ca-validate-deploy.yml`
