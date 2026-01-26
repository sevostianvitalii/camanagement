# Azure Conditional Access Policy Management

Policy-as-Code tool for Azure Conditional Access management with GitHub/GitLab integration.

## Features

- ✅ **Naming convention enforcement** — `en-<env>-ca-<scope>-<control>-<nnn>`
- ✅ **Compliance validation** — Break-glass exclusions, Microsoft best practices
- ✅ **Conflict detection** — Overlaps, redundancy, coverage gaps
- ✅ **Auto-metadata population** — Tags and descriptions from policy YAML
- ✅ **GitHub + GitLab support** — Both CI/CD platforms
- ✅ **OIDC authentication** — Secretless Azure access

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Validate Policies

```bash
# Validate all policies
python -m ca_manager validate --check all --path policies/

# Validate specific checks
python -m ca_manager validate --check naming --path policies/
python -m ca_manager validate --check compliance --path policies/
```

### Deploy Policies

```bash
# Dry run (validate only)
python -m ca_manager deploy --path policies/ --dry-run

# Deploy to Azure AD
python -m ca_manager deploy --path policies/
```

## Documentation

- **[Detailed User Guide](./docs/USER_GUIDE.md)** — Start here! How to request and create policies.
- [Azure Setup Guide](./docs/AZURE_SETUP.md) — How to configure OIDC and permissions.
- [Workflow Testing](./docs/WORKFLOW_TEST.md) — How to verify the CI/CD pipeline.
- [Templates Guide](./templates/README.md) — Overview of available policy templates.

## Deployment

Once Azure is configured:

```bash
# Deploy in dry-run mode (default)
python -m ca_manager deploy --path policies/

# Deploy to Azure AD (live)
python -m ca_manager deploy --path policies/ --no-dry-run
```

**CI/CD Deployment:**
- **GitHub Actions:** Merge to `main` triggers deployment
- **GitLab CI:** Merge to `main` triggers deployment
- Both use OIDC authentication (no secrets stored in git!)

## Project Structure (Detailed)

```
ca-policy-management/
├── policies/          # YAML policy definitions
│   ├── prd/          # Production policies
│   └── tst/          # Test environment policies
├── baseline/         # Validation rules
├── src/ca_manager/   # Python package
├── tests/            # Unit tests
└── .github/workflows # CI/CD pipelines
```

## Policy File Format

Each CA policy is defined in YAML:

```yaml
name: en-prd-ca-admins-mfa-001
displayName: "Admin MFA Enforcement - Production"
state: enabled

metadata:
  owner: "iam-team@example.com"
  ticketId: "JIRA-1234"
  justification: "Enforce MFA for all admin accounts"

conditions:
  users:
    includeGroups:
      - "AAD-Admins-Global"
    excludeGroups:
      - "AAD-BreakGlass-Accounts"

grantControls:
  operator: "OR"
  builtInControls:
    - "mfa"
```

## CI/CD Integration

### GitHub Actions

Automatically validates on PR and deploys on merge to main.

### GitLab CI

Validates on MR and deploys on merge to main.

## License

MIT
