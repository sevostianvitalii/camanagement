"""Conflict detection between policies"""

from typing import List, Dict


def detect_conflicts(policies: List[dict]) -> List[Dict[str, any]]:
    """
    Detect conflicts between policies.
    
    Args:
        policies: List of policy dicts
    
    Returns:
        List of conflict reports with type, severity, affected policies
    """
    conflicts = []
    
    # 1. Overlapping conditions with different controls
    conflicts.extend(detect_overlapping_conditions(policies))
    
    # 2. Redundant policies
    conflicts.extend(detect_redundant_policies(policies))
    
    # 3. Coverage gaps would require Azure AD data (not available in static validation)
    
    return conflicts


def detect_overlapping_conditions(policies: List[dict]) -> List[Dict]:
    """
    Find policies with overlapping user/app conditions but different controls.
    
    Args:
        policies: List of policy dicts
    
    Returns:
        List of conflict dicts
    """
    conflicts = []
    
    for i, policy1 in enumerate(policies):
        for policy2 in policies[i+1:]:
            if policies_overlap(policy1, policy2):
                # Check if controls are different
                controls1 = set(policy1.get('grantControls', {}).get('builtInControls', []))
                controls2 = set(policy2.get('grantControls', {}).get('builtInControls', []))
                
                if controls1 != controls2:
                    conflicts.append({
                        'type': 'overlapping-conditions',
                        'severity': 'high',
                        'policies': [policy1['name'], policy2['name']],
                        'description': (
                            f"Policies target similar users but have different controls: "
                            f"{controls1} vs {controls2}"
                        )
                    })
    
    return conflicts


def detect_redundant_policies(policies: List[dict]) -> List[Dict]:
    """
    Find policies with identical conditions and controls.
    
    Args:
        policies: List of policy dicts
    
    Returns:
        List of conflict dicts
    """
    conflicts = []
    
    for i, policy1 in enumerate(policies):
        for policy2 in policies[i+1:]:
            if are_policies_identical(policy1, policy2):
                conflicts.append({
                    'type': 'redundant-policy',
                    'severity': 'medium',
                    'policies': [policy1['name'], policy2['name']],
                    'description': "Policies have identical conditions and controls"
                })
    
    return conflicts


def policies_overlap(p1: dict, p2: dict) -> bool:
    """
    Check if two policies have overlapping conditions.
    
    Args:
        p1, p2: Policy dicts
    
    Returns:
        True if policies overlap
    """
    # Compare includeGroups
    groups1 = set(p1.get('conditions', {}).get('users', {}).get('includeGroups', []))
    groups2 = set(p2.get('conditions', {}).get('users', {}).get('includeGroups', []))
    
    # Check for group overlap
    if groups1.intersection(groups2):
        return True
    
    # Compare includeUsers
    users1 = set(p1.get('conditions', {}).get('users', {}).get('includeUsers', []))
    users2 = set(p2.get('conditions', {}).get('users', {}).get('includeUsers', []))
    
    # Check for user overlap or "All" users
    if users1.intersection(users2) or ('All' in users1 or 'All' in users2):
        return True
    
    return False


def are_policies_identical(p1: dict, p2: dict) -> bool:
    """
    Check if two policies are identical (same conditions and controls).
    
    Args:
        p1, p2: Policy dicts
    
    Returns:
        True if policies are identical
    """
    # Compare user conditions
    users1 = p1.get('conditions', {}).get('users', {})
    users2 = p2.get('conditions', {}).get('users', {})
    
    if (
        set(users1.get('includeGroups', [])) != set(users2.get('includeGroups', [])) or
        set(users1.get('excludeGroups', [])) != set(users2.get('excludeGroups', [])) or
        set(users1.get('includeUsers', [])) != set(users2.get('includeUsers', []))
    ):
        return False
    
    # Compare application conditions
    apps1 = p1.get('conditions', {}).get('applications', {}).get('includeApplications', [])
    apps2 = p2.get('conditions', {}).get('applications', {}).get('includeApplications', [])
    
    if set(apps1) != set(apps2):
        return False
    
    # Compare grant controls
    controls1 = set(p1.get('grantControls', {}).get('builtInControls', []))
    controls2 = set(p2.get('grantControls', {}).get('builtInControls', []))
    
    if controls1 != controls2:
        return False
    
    return True


def detect_coverage_gaps(policies: List[dict], all_groups: List[str]) -> List[Dict]:
    """
    Detect Azure AD groups not covered by any policy.
    
    Note: This requires Azure AD group data, so it's run during deployment,
    not during static validation.
    
    Args:
        policies: List of policy dicts
        all_groups: All Azure AD groups from tenant
    
    Returns:
        List of coverage gap reports
    """
    covered_groups = set()
    
    # Collect all groups covered by policies
    for policy in policies:
        include_groups = policy.get('conditions', {}).get('users', {}).get('includeGroups', [])
        covered_groups.update(include_groups)
    
    # Find uncovered groups (exclude service accounts and system groups)
    uncovered = []
    for group in all_groups:
        if group not in covered_groups and not _is_system_group(group):
            uncovered.append(group)
    
    if uncovered:
        return [{
            'type': 'coverage-gap',
            'severity': 'medium',
            'description': f"Groups without CA policy coverage: {', '.join(uncovered)}"
        }]
    
    return []


def _is_system_group(group_name: str) -> bool:
    """Check if group is a system/service group that should be excluded from coverage checks"""
    exclude_patterns = [
        'Service-',
        'System-',
        'Sync-',
        'BreakGlass',
        'Emergency',
        'AAD-Device'
    ]
    return any(pattern in group_name for pattern in exclude_patterns)
