"""Compliance validator for CA policies"""

from pathlib import Path

import yaml

from ca_manager.models import BestPractice, ComplianceRules
from ca_manager.validators.naming import extract_scope


def load_compliance_rules(baseline_path: Path) -> ComplianceRules:
    """Load compliance rules from baseline config"""
    rules_file = baseline_path / "compliance-rules.yaml"
    with open(rules_file) as f:
        data = yaml.safe_load(f)
    return ComplianceRules(**data)


def load_best_practices(baseline_path: Path) -> list[BestPractice]:
    """Load Microsoft best practices from baseline config"""
    bp_file = baseline_path / "ms-best-practices.yaml"
    with open(bp_file) as f:
        data = yaml.safe_load(f)
    return [BestPractice(**bp) for bp in data.get("bestPractices", [])]


def validate_compliance(policy: dict, rules: ComplianceRules) -> list[tuple[str, str]]:
    """
    Validate policy against compliance rules.
    """
    violations = []

    # Check state
    if policy.get("state") not in rules.allowedStates:
        violations.append(("critical", f"State '{policy.get('state')}' is not allowed"))

    # Check exclusions
    violations.extend(_check_exclusions(policy, rules))

    # Check scope requirements
    violations.extend(_check_scope_requirements(policy, rules))

    return violations


def _check_exclusions(policy: dict, rules: ComplianceRules) -> list[tuple[str, str]]:
    """Verify mandatory exclusions (break-glass accounts)"""
    violations = []
    excluded_groups = policy.get("conditions", {}).get("users", {}).get("excludeGroups", [])
    for req_group in rules.requiredExclusions.get("groups", []):
        if req_group not in excluded_groups:
            violations.append(("critical", f"Must exclude mandatory group '{req_group}'"))
    return violations


def _check_scope_requirements(policy: dict, rules: ComplianceRules) -> list[tuple[str, str]]:
    """Check requirements specific to the policy scope"""
    violations = []
    scope = extract_scope(policy.get("name", ""))

    # Handle base scopes (extract 'admins' from 'app-admins' if needed)
    base_scope = scope
    if scope.startswith("app-"):
        base_scope = "app"

    reqs = rules.scopeRequirements.get(base_scope) or rules.scopeRequirements.get(scope)
    if not reqs:
        return violations

    # Check mandatory controls
    controls = policy.get("grantControls", {}).get("builtInControls", [])
    for mandatory in reqs.get("mandatoryControls", []):
        if mandatory not in controls:
            violations.append(("high", f"Scope '{scope}' requires control '{mandatory}'"))

    # Check forbidden client app types
    client_types = policy.get("conditions", {}).get("clientAppTypes", [])
    for forbidden in reqs.get("forbiddenClientAppTypes", []):
        if forbidden in client_types:
            violations.append(
                ("high", f"Client app type '{forbidden}' is forbidden for scope '{scope}'")
            )

    return violations


def validate_best_practices(
    policy: dict, practices: list[BestPractice]
) -> list[tuple[str, str, str]]:
    """
    Validate policy against Microsoft best practices.
    """
    recommendations = []
    for practice in practices:
        if _is_violation(policy, practice):
            recommendations.append((practice.id, practice.severity, practice.remediation))
    return recommendations


def _is_violation(policy: dict, practice: BestPractice) -> bool:
    """Check if a policy violates a specific best practice"""
    # BP001: Required exclusions
    if practice.id == "BP001":
        excluded = policy.get("conditions", {}).get("users", {}).get("excludeGroups", [])
        return "AAD-BreakGlass-Accounts" not in excluded

    # BP002: Block legacy auth
    if practice.id == "BP002":
        client_types = policy.get("conditions", {}).get("clientAppTypes", [])
        if "other" in client_types or "exchangeActiveSync" in client_types:
            return "block" not in policy.get("grantControls", {}).get("builtInControls", [])

    # BP003: New policies should start in report-only
    if practice.id == "BP003":
        return policy.get("state") == "enabled" and policy.get("metadata", {}).get(
            "ticketId", ""
        ).startswith("NEW")

    # BP004: MFA for admins
    if practice.id == "BP004":
        scope = extract_scope(policy.get("name", ""))
        if scope == "admins":
            return "mfa" not in policy.get("grantControls", {}).get("builtInControls", [])

    # BP006: Compliant device for externals
    if practice.id == "BP006":
        scope = extract_scope(policy.get("name", ""))
        if scope == "externals":
            return "compliantDevice" not in policy.get("grantControls", {}).get(
                "builtInControls", []
            )

    return False
