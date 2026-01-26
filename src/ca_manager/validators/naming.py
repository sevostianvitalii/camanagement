"""Naming convention validator"""

import re
from typing import Tuple
from pathlib import Path
import yaml

from ca_manager.models import NamingRules


def load_naming_rules(baseline_path: Path) -> NamingRules:
    """Load naming rules from baseline YAML file"""
    rules_file = baseline_path / "naming-rules.yaml"
    with open(rules_file, 'r') as f:
        data = yaml.safe_load(f)
    return NamingRules(**data)


def extract_components(policy_name: str, pattern: str) -> dict[str, str]:
    """
    Extract components from policy name using regex pattern.
    
    Args:
        policy_name: Policy name (e.g., "en-prd-ca-admins-mfa-001")
        pattern: Regex pattern with named groups
    
    Returns:
        Dict of component names to values
    """
    compiled_pattern = re.compile(pattern)
    match = compiled_pattern.match(policy_name)
    
    if not match:
        return {}
    
    return match.groupdict()


def validate_policy_name(policy_name: str, rules: NamingRules) -> Tuple[bool, str]:
    """
    Validate policy name against naming convention.
    
    Args:
        policy_name: Policy filename (e.g., "en-prd-ca-admins-mfa-001")
        rules: Naming rules from baseline config
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    compiled_pattern = re.compile(rules.pattern)
    match = compiled_pattern.match(policy_name)
    
    if not match:
        return False, f"Policy name '{policy_name}' does not match pattern"
    
    # Extract components
    components = match.groupdict()
    env = components.get('env', '')
    scope = components.get('scope', '')
    control = components.get('control', '')
    number_str = components.get('number', '0')
    
    try:
        number = int(number_str)
    except ValueError:
        return False, f"Invalid policy number: '{number_str}'"
    
    # Validate environment
    if env not in rules.environments:
        return False, f"Invalid environment '{env}'. Allowed: {', '.join(rules.environments)}"
    
    # Validate scope (handle app-* wildcard)
    if not scope.startswith('app-') and scope not in rules.scopes:
        return False, f"Invalid scope '{scope}'. Allowed: {', '.join(rules.scopes)} or app-*"
    
    # Validate control
    if control not in rules.controls:
        return False, f"Invalid control '{control}'. Allowed: {', '.join(rules.controls)}"
    
    # Validate number range
    min_num = rules.numberRange['min']
    max_num = rules.numberRange['max']
    if not (min_num <= number <= max_num):
        return False, f"Policy number {number} out of range [{min_num}-{max_num}]"
    
    return True, ""


def extract_scope_from_name(policy_name: str) -> str:
    """
    Extract scope from policy name.
    
    Example: "en-prd-ca-admins-mfa-001" -> "admins"
    """
    parts = policy_name.split('-')
    if len(parts) >= 5:
        # Handle both regular scopes and app-* scopes
        if parts[3] == "app" and len(parts) >= 6:
            return f"app-{parts[4]}"
        return parts[3]
    return ""
