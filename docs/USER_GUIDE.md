# User Guide: Azure CA Policy Management

This guide provides detailed instructions on how to use the CA Policy Management tool, from requesting a new policy to deploying it to Azure AD.

## Table of Contents
1. [Overview](#overview)
2. [Requesting a New Policy](#requesting-a-new-policy)
3. [ Creating a Policy (for Admins)](#creating-a-policy-for-admins)
4. [Validation Workflow](#validation-workflow)
5. [Deployment Workflow](#deployment-workflow)
6. [Compliance & Best Practices](#compliance--best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The CA Policy Management tool allows you to manage Azure Conditional Access policies using a **GitOps** approach. Every change is version-controlled, validated by automated tests, and deployed through a secure CI/CD pipeline.

---

## Requesting a New Policy

Business requestors should use the [JIRA Request Template](../templates/jira/ca-policy-request.md).

1. **Copy the template** content into a new JIRA ticket.
2. **Fill in all mandatory fields** (Request Type, Targets, Justification, etc.).
3. **Submit the ticket** to the IAM/Security team.

---

## Creating a Policy (for Admins)

Admins convert JIRA requests into YAML policy files using the provided templates.

### 1. Select a Template
Choose the appropriate scenario from the `templates/admin/` directory:
- `mfa-enforcement.yaml`
- `block-legacy-auth.yaml`
- `require-compliant-device.yaml`
- `location-restriction.yaml`
- `app-specific-control.yaml`

### 2. Configure the Policy
Rename the file and fill in the values:
- **Name**: Follow the convention `en-<env>-ca-<scope>-<control>-<nnn>`
- **Metadata**: Add the JIRA ticket ID and justification.
- **Conditions**: Define who (users/groups) and what (apps/locations) are affected.
- **Controls**: Define the enforcement (e.g., `mfa`, `block`).

### 3. Move to Policies Directory
Place the file in `policies/prd/` (Production) or `policies/tst/` (Testing).

---

## Validation Workflow

Once you create a Pull Request (PR) with your new policy:

1. **Naming Check**: Verifies the filename matches the standard.
2. **Compliance Check**: Ensures mandatory exclusions (like break-glass accounts) are present.
3. **Conflict Check**: Detects if your policy overlaps with existing ones.
4. **Best Practices**: Suggests security improvements.

The GitHub Action will comment directly on your PR with a **Validation Report**. You must fix all **CRITICAL** and **HIGH** errors before merging.

---

## Deployment Workflow

1. **Merge to Main**: Once the PR is approved and checks pass, merge it to `main`.
2. **Auto-Deployment**: GitHub Actions will trigger a deployment run.
3. **Dry-Run**: By default, the tool performs a "Dry-Run" to show you what *would* happen in Azure.
4. **Live Deployment**: To go live, an IAM admin must trigger or uncomment the production deployment step in the workflow (or run the `--no-dry-run` command locally with appropriate permissions).

---

## Compliance & Best Practices

The tool enforces several safety gates:
- **Break-Glass Safety**: Policies *must* exclude the emergency access group.
- **Admin MFA**: Any policy targeting admins *must* require MFA.
- **Legacy Auth**: Policies targeting legacy protocols *must* use the `block` control.

---

## Troubleshooting

- **Validation Failed**: Check the PR comments or run `python -m ca_manager validate --check all --path policies/` locally.
- **Merge Blocked**: Ensure all status checks are green.
- **Azure Login Failed**: Verify OIDC secrets (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`) in GitHub.

---

For technical setup details, see [AZURE_SETUP.md](./AZURE_SETUP.md).
