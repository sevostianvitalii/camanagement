"""Compliance rules validator"""

from typing import List, Tuple
from pathlib import Path
import yaml

from ca_manager.models import ComplianceRules, BestPractice
from ca_manager.validators.naming import extract_scope_from_name


def load_compliance_rules(baseline_path: Path) -> ComplianceRules:
    """Load compliance rules from baseline YAML file"""
    rules_file = baseline_path / "compliance-rules.yaml"
    with open(rules_file, 'r') as f:
        data = yaml.safe_load(f)
    return ComplianceRules(**data)


def load_best_practices(baseline_path: Path) -> List[BestPractice]:
    """Load Microsoft best practices from baseline YAML file"""
    practices_file = baseline_path / "ms-best-practices.yaml"
    with open(practices_file, 'r') as f:
        data = yaml.safe_load(f)
    return [BestPractice(**bp) for bp in data.get('bestPractices', [])]


def validate_compliance(policy: dict, rules: ComplianceRules) -> List[Tuple[str, str]]:
    """
    Validate policy against compliance rules.
    
    Args:
        policy: Policy data as dict
        rules: Compliance rules from baseline
    
    Returns:
        List of (severity, error_message) tuples
    """
    violations = []
    
    # Check required exclusions (break-glass accounts)
    excluded_groups = policy.get('conditions', {}).get('users', {}).get('excludeGroups', [])
    for required_group in rules.requiredExclusions.get('groups', []):
        if required_group not in excluded_groups:
            violations.append((
                'critical',
                f"Missing required exclusion group: '{required_group}'"
            ))
    
    # Extract scope from policy name
    scope = extract_scope_from_name(policy['name'])
    
    # Check scope-specific requirements
    if scope in rules.scopeRequirements:
        scope_rules = rules.scopeRequirements[scope]
        
        # Check mandatory controls
        if 'mandatoryControls' in scope_rules:
            policy_controls = policy.get('grantControls', {}).get('builtInControls', [])
            for required_control in scope_rules['mandatoryControls']:
                if required_control not in policy_controls:
                    violations.append((
                        'high',
                        f"Scope '{scope}' requires control '{required_control}'"
                    ))
        
        # Check forbidden states
        if 'forbiddenStates' in scope_rules:
            if policy['state'] in scope_rules['forbiddenStates']:
                violations.append((
                    'high',
                    f"State '{policy['state']}' is forbidden for scope '{scope}'"
                ))
        
        # Check forbidden client app types
        if 'forbiddenClientAppTypes' in scope_rules:
            policy_client_app_types = policy.get('conditions', {}).get('clientAppTypes', [])
            for forbidden_type in scope_rules['forbiddenClientAppTypes']:
                if forbidden_type in policy_client_app_types:
                    violations.append((
                        'high',
                        f"Client app type '{forbidden_type}' is forbidden for scope '{scope}'"
                    ))
        
        # Check minimum controls
        if 'minimumControls' in scope_rules:
            policy_controls = policy.get('grantControls', {}).get('builtInControls', [])
            min_controls = scope_rules['minimumControls']
            if len(policy_controls) < min_controls:
                violations.append((
                    'medium',
                    f"Scope '{scope}' requires at least {min_controls} control(s)"
                ))
    
    # Check policy state
    if policy['state'] not in rules.allowedStates:
        violations.append((
            'medium',
            f"Policy state '{policy['state']}' not in allowed states: {rules.allowedStates}"
        ))
    
    return violations


def validate_best_practices(policy: dict, practices: List[BestPractice]) -> List[Tuple[str, str, str]]:
    """
    Validate policy against Microsoft best practices.
    
    Args:
        policy: Policy data as dict
        practices: List of best practice checks
    
    Returns:
        List of (id, severity, recommendation) tuples
    """
    recommendations = []
    
    for bp in practices:
        # Evaluate each best practice check
        if bp.id == 'BP001':  # Exclude break-glass
            excluded_groups = policy.get('conditions', {}).get('users', {}).get('excludeGroups', [])
            if 'AAD-BreakGlass-Accounts' not in excluded_groups:
                recommendations.append((bp.id, bp.severity, bp.remediation))
        
        elif bp.id == 'BP002':  # Block legacy auth
            if 'block-legacy' in policy['name']:
                client_app_types = policy.get('conditions', {}).get('clientAppTypes', [])
                if 'other' not in client_app_types:
                    recommendations.append((bp.id, bp.severity, bp.remediation))
        
        elif bp.id == 'BP003':  # Report-only mode for new policies
            # This would be checked during deployment, not validation
            pass
        
        elif bp.id == 'BP004':  # MFA for admins
            if 'admins' in policy['name']:
                controls = policy.get('grantControls', {}).get('builtInControls', [])
                if 'mfa' not in controls:
                    recommendations.append((bp.id, bp.severity, bp.remediation))
        
        elif bp.id == 'BP005':  # All users requires exclusions
            include_users = policy.get('conditions', {}).get('users', {}).get('includeUsers', [])
            exclude_groups = policy.get('conditions', {}).get('users', {}).get('excludeGroups', [])
            if 'All' in include_users and not exclude_groups:
                recommendations.append((bp.id, bp.severity, bp.remediation))
        
        elif bp.id == 'BP006':  # Compliant device for externals
            if 'externals' in policy['name']:
                controls = policy.get('grantControls', {}).get('builtInControls', [])
                if 'compliantDevice' not in controls and 'domainJoinedDevice' not in controls:
                    recommendations.append((bp.id, bp.severity, bp.remediation))
        
        elif bp.id == 'BP007':  # Sign-in frequency for high-risk
            user_risk = policy.get('conditions', {}).get('userRiskLevels', [])
            if 'high' in user_risk:
                sign_in_freq = policy.get('sessionControls', {}).get('signInFrequency', {})
                if not sign_in_freq.get('value'):
                    recommendations.append((bp.id, bp.severity, bp.remediation))
    
    return recommendations
