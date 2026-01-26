# Policy Templates

This directory contains templates for creating and requesting Conditional Access policies.

## For IAM Administrators

Use the templates in `admin/` to quickly deploy new policies:

| Template | Use Case |
|----------|----------|
| [`mfa-enforcement.yaml`](admin/mfa-enforcement.yaml) | Require MFA for specific user groups |
| [`block-legacy-auth.yaml`](admin/block-legacy-auth.yaml) | Block legacy authentication protocols |
| [`require-compliant-device.yaml`](admin/require-compliant-device.yaml) | Require Intune-compliant devices |
| [`location-restriction.yaml`](admin/location-restriction.yaml) | Restrict access by location |
| [`app-specific-control.yaml`](admin/app-specific-control.yaml) | Apply controls to specific applications |

### How to Use

1. Copy the appropriate template to `policies/<env>/`
2. Replace all `<PLACEHOLDER>` values
3. Rename the file following the naming convention
4. Create a PR and wait for validation

### Naming Convention
```
en-<env>-ca-<scope>-<control>-<nnn>
```
- **env**: `prd`, `tst`, `dev`
- **scope**: `admins`, `allusers`, `externals`, `app-<name>`
- **control**: `mfa`, `block`, `compliant`, `location`, etc.
- **nnn**: Sequence number (001-999)

---

## For Business Requestors

Use the JIRA template in `jira/` to request new policies:

- [`ca-policy-request.md`](jira/ca-policy-request.md) — Copy this into your JIRA ticket

The IAM team will review your request and implement the appropriate policy.
