"""Naming convention validator for CA policies"""

import re
from pathlib import Path

import yaml

from ca_manager.models import NamingRules


def load_naming_rules(baseline_path: Path) -> NamingRules:
    """Load naming rules from baseline config"""
    rules_file = baseline_path / "naming-rules.yaml"
    with open(rules_file) as f:
        data = yaml.safe_load(f)
    return NamingRules(**data)


# Constants for naming convention parts (legacy fixed index fallback)
PART_INDEX_ENV = 1
PART_INDEX_SCOPE = 3
PART_INDEX_APP_NAME = 4
MIN_PARTS_FOR_SCOPE = 5
MIN_PARTS_FOR_APP_SCOPE = 6


def validate_policy_name(policy_name: str, rules: NamingRules) -> tuple[bool, str]:
    """
    Validate policy name against naming convention using regex pattern.
    """
    match = re.match(rules.pattern, policy_name)
    if not match:
        return False, f"Name does not match pattern: {rules.pattern}"

    components = match.groupdict()
    env = components.get("env")
    control = components.get("control")
    number_str = components.get("number", "0")
    scope = extract_scope(policy_name, rules.pattern)

    # Validate components
    error = None
    if not env or env not in rules.environments:
        error = f"Invalid environment '{env}'. Allowed: {', '.join(rules.environments)}"
    elif not _is_valid_scope(scope, rules.scopes):
        error = f"Invalid scope '{scope}'. Allowed: {', '.join(rules.scopes)}"
    elif not control or control not in rules.controls:
        error = f"Invalid control '{control}'. Allowed: {', '.join(rules.controls)}"
    else:
        try:
            number = int(number_str)
            if not (rules.numberRange["min"] <= number <= rules.numberRange["max"]):
                error = f"Policy number {number} out of range [{rules.numberRange['min']}-{rules.numberRange['max']}]"
        except ValueError:
            error = f"Invalid policy number: '{number_str}'"

    if error:
        return False, error

    return True, ""


def _is_valid_scope(scope: str, allowed_scopes: list[str]) -> bool:
    """Check if scope is valid or an app-* wildcard"""
    return scope in allowed_scopes or scope.startswith("app-")


def extract_scope(policy_name: str, pattern: str | None = None) -> str:
    """
    Extract scope from policy name.

    Tries to use the regex pattern first, falls back to fixed indices.
    """
    if pattern:
        match = re.match(pattern, policy_name)
        if match:
            groupdict = match.groupdict()
            if "scope" in groupdict:
                return groupdict["scope"]

    # Fallback to fixed parts
    parts = policy_name.split("-")
    if len(parts) >= MIN_PARTS_FOR_SCOPE:
        if parts[PART_INDEX_SCOPE] == "app" and len(parts) >= MIN_PARTS_FOR_APP_SCOPE:
            return f"app-{parts[PART_INDEX_APP_NAME]}"
        return parts[PART_INDEX_SCOPE]

    return "unknown"
