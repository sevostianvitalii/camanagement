"""CLI interface for CA Policy Manager"""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import yaml

from ca_manager.validators import (
    validate_policy_name,
    validate_compliance,
    validate_best_practices,
    detect_conflicts,
    load_naming_rules,
    load_compliance_rules,
    load_best_practices,
)

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def main():
    """Azure Conditional Access Policy Manager - Policy-as-Code Tool"""
    pass


@main.command()
@click.option(
    '--check',
    type=click.Choice(['naming', 'compliance', 'best-practices', 'conflicts', 'all']),
    required=True,
    help='Type of validation to perform'
)
@click.option(
    '--path',
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help='Path to policies directory'
)
@click.option(
    '--baseline-path',
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path.cwd() / "baseline",
    help='Path to baseline configuration directory (defaults to ./baseline)'
)
def validate(check: str, path: Path, baseline_path: Path):
    """Validate policies against baseline rules"""
    console.print(Panel(
        f"[bold blue]Validating policies in {path}[/bold blue]",
        title="CA Policy Validation"
    ))
    
    # Find all policy YAML files
    policy_files = list(path.rglob("*.yaml")) + list(path.rglob("*.yml"))
    
    if not policy_files:
        console.print("[yellow]No policy files found[/yellow]")
        return
    
    console.print(f"Found {len(policy_files)} policy file(s)\n")
    
    # Load policies
    policies = []
    for policy_file in policy_files:
        with open(policy_file, 'r') as f:
            policy_data = yaml.safe_load(f)
            policies.append(policy_data)
    
    # Run validations
    has_errors = False
    has_info = False
    
    if check in ['naming', 'all']:
        has_errors |= _validate_naming(policies, baseline_path)
    
    if check in ['compliance', 'all']:
        has_errors |= _validate_compliance_rules(policies, baseline_path)
    
    if check in ['best-practices', 'all']:
        has_info |= _validate_best_practices_rules(policies, baseline_path)
    
    if check in ['conflicts', 'all']:
        # Conflicts are considered high/medium priority but we'll mark as info for now
        # unless severity is high
        _validate_conflicts(policies)
    
    # Summary
    if has_errors:
        console.print("\n[bold red]❌ Validation failed with errors[/bold red]")
        console.print("[red]Please fix the naming or compliance violations before merging.[/red]")
        raise click.exceptions.Exit(code=1)
    else:
        if has_info:
            console.print("\n[bold yellow]⚠️  Validation passed with recommendations[/bold yellow]")
            console.print("[yellow]Review the best practice suggestions above.[/yellow]")
        else:
            console.print("\n[bold green]✅ All validations passed[/bold green]")


def _validate_naming(policies: list, baseline_path: Path) -> bool:
    """Validate naming conventions"""
    console.print("[bold]Checking naming conventions...[/bold]")
    
    naming_rules = load_naming_rules(baseline_path)
    has_errors = False
    
    table = Table(title="Naming Validation Results")
    table.add_column("Policy Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Error", style="red")
    
    for policy in policies:
        policy_name = policy.get('name', '')
        is_valid, error_msg = validate_policy_name(policy_name, naming_rules)
        
        if is_valid:
            table.add_row(policy_name, "✅ Valid", "")
        else:
            table.add_row(policy_name, "❌ Invalid", error_msg)
            has_errors = True
    
    console.print(table)
    console.print()
    return has_errors


def _validate_compliance_rules(policies: list, baseline_path: Path) -> bool:
    """Validate compliance rules"""
    console.print("[bold]Checking compliance rules...[/bold]")
    
    compliance_rules = load_compliance_rules(baseline_path)
    has_errors = False
    
    for policy in policies:
        violations = validate_compliance(policy, compliance_rules)
        
        if violations:
            console.print(f"\n[yellow]Policy: {policy['name']}[/yellow]")
            for severity, message in violations:
                if severity == 'critical':
                    console.print(f"  [bold red]🚨 CRITICAL:[/bold red] {message}")
                    has_errors = True
                elif severity == 'high':
                    console.print(f"  [red]⚠️  HIGH:[/red] {message}")
                    has_errors = True
                else:
                    console.print(f"  [yellow]ℹ️  {severity.upper()}:[/yellow] {message}")
    
    if not has_errors:
        console.print("[green]✅ All policies comply with baseline rules[/green]")
    
    console.print()
    return has_errors


def _validate_best_practices_rules(policies: list, baseline_path: Path) -> bool:
    """Validate Microsoft best practices"""
    console.print("[bold]Checking Microsoft best practices...[/bold]")
    
    best_practices = load_best_practices(baseline_path)
    has_warnings = False
    
    for policy in policies:
        recommendations = validate_best_practices(policy, best_practices)
        
        if recommendations:
            console.print(f"\n[yellow]Policy: {policy['name']}[/yellow]")
            for bp_id, severity, remediation in recommendations:
                if severity == 'critical':
                    console.print(f"  [bold red]🚨 {bp_id}:[/bold red] {remediation}")
                elif severity == 'high':
                    console.print(f"  [red]⚠️  {bp_id}:[/red] {remediation}")
                else:
                    console.print(f"  [yellow]ℹ️  {bp_id}:[/yellow] {remediation}")
                has_warnings = True
    
    if not has_warnings:
        console.print("[green]✅ All policies follow Microsoft best practices[/green]")
    
    console.print()
    return has_warnings


def _validate_conflicts(policies: list) -> bool:
    """Detect conflicts between policies"""
    console.print("[bold]Detecting conflicts between policies...[/bold]")
    
    conflicts = detect_conflicts(policies)
    has_conflicts = False
    
    if conflicts:
        for conflict in conflicts:
            console.print(f"\n[red]⚠️  {conflict['type'].upper()}:[/red]")
            console.print(f"  Severity: {conflict['severity']}")
            console.print(f"  Description: {conflict['description']}")
            if 'policies' in conflict:
                console.print(f"  Affected: {', '.join(conflict['policies'])}")
            has_conflicts = True
    
    if not has_conflicts:
        console.print("[green]✅ No conflicts detected[/green]")
    
    console.print()
    return has_conflicts


@main.command()
@click.option(
    '--path',
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help='Path to policies directory'
)
@click.option(
    '--dry-run/--no-dry-run',
    default=True,
    help='If true, validate but do not apply changes'
)
def deploy(path: Path, dry_run: bool):
    """Deploy policies to Azure AD"""
    console.print(Panel(
        f"[bold green]Deploying policies from {path}[/bold green]\nDry run: {dry_run}",
        title="CA Policy Deployment"
    ))
    
    if dry_run:
        console.print("[yellow]⚠️  DRY RUN MODE - No changes will be applied[/yellow]\n")
    
    # Find all policy YAML files
    policy_files = list(path.rglob("*.yaml")) + list(path.rglob("*.yml"))
    
    if not policy_files:
        console.print("[yellow]No policy files found[/yellow]")
        return
    
    console.print(f"Found {len(policy_files)} policy file(s) to deploy\n")
    
    # TODO: Implement Azure AD deployment
    console.print("[yellow]⚠️  Deployment to Azure AD not yet implemented[/yellow]")
    console.print("This will use Microsoft Graph API with OIDC authentication")


if __name__ == '__main__':
    main()
