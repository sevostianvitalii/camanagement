"""Microsoft Graph client for Conditional Access policies"""

import asyncio
import os
from typing import Any

from azure.identity import AzureCliCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.conditional_access_policy import ConditionalAccessPolicy
from msgraph.generated.models.conditional_access_condition_set import ConditionalAccessConditionSet
from msgraph.generated.models.conditional_access_grant_controls import ConditionalAccessGrantControls
from msgraph.generated.models.conditional_access_session_controls import ConditionalAccessSessionControls
from msgraph.generated.models.conditional_access_users import ConditionalAccessUsers
from msgraph.generated.models.conditional_access_applications import ConditionalAccessApplications
from msgraph.generated.models.conditional_access_platforms import ConditionalAccessPlatforms
from msgraph.generated.models.conditional_access_policy_state import ConditionalAccessPolicyState

from ca_manager.models import ConditionalAccessPolicy as PolicyModel


class AzureGraphClient:
    """Client for interacting with MS Graph Conditional Access API"""

    def __init__(self):
        # Use AzureCliCredential to leverage the session established by azure/login@v2
        self.credential = AzureCliCredential()
        # Explicitly request the required scopes for Conditional Access policies
        scopes = ["https://graph.microsoft.com/.default"]
        self.client = GraphServiceClient(self.credential, scopes)

    async def deploy_policy(self, policy_data: PolicyModel, dry_run: bool = True) -> str:
        """
        Deploy or update a Conditional Access policy.
        Returns the action taken (created/updated/skipped).
        """
        # 1. Check if policy exists by displayName
        existing_policies = await self.client.identity.conditional_access.policies.get()
        target_policy = None
        
        if existing_policies and existing_policies.value:
            for p in existing_policies.value:
                if p.display_name == policy_data.displayName:
                    target_policy = p
                    break

        # 2. Build policy object
        # Map our models to Graph SDK models
        graph_policy = ConditionalAccessPolicy(
            display_name=policy_data.displayName,
            state=ConditionalAccessPolicyState(policy_data.state),
            conditions=ConditionalAccessConditionSet(
                users=ConditionalAccessUsers(
                    include_groups=policy_data.conditions.users.includeGroups or None,
                    exclude_groups=policy_data.conditions.users.excludeGroups or None,
                    include_users=policy_data.conditions.users.includeUsers or None,
                    exclude_users=policy_data.conditions.users.excludeUsers or None,
                ),
                applications=ConditionalAccessApplications(
                    include_applications=policy_data.conditions.applications.includeApplications or None,
                    exclude_applications=policy_data.conditions.applications.excludeApplications or None,
                ),
                platforms=ConditionalAccessPlatforms(
                    include_platforms=policy_data.conditions.platforms.includePlatforms or None,
                    exclude_platforms=policy_data.conditions.platforms.excludePlatforms or None,
                ),
                client_app_types=policy_data.conditions.clientAppTypes or None,
            ),
            grant_controls=ConditionalAccessGrantControls(
                operator=policy_data.grantControls.operator,
                built_in_controls=policy_data.grantControls.builtInControls or None,
            ),
        )

        if dry_run:
            return f"{'Update' if target_policy else 'Create'} (DRY-RUN)"

        try:
            if target_policy:
                # Update existing
                await self.client.identity.conditional_access.policies.by_conditional_access_policy_id(target_policy.id).patch(graph_policy)
                return f"UPDATED (ID: {target_policy.id})"
            else:
                # Create new
                result = await self.client.identity.conditional_access.policies.post(graph_policy)
                return f"CREATED (ID: {result.id})"
        except Exception as e:
            error_str = str(e)
            # Check for license-related errors
            if "AccessDenied" in error_str and "scopes are missing" in error_str:
                raise RuntimeError(
                    f"LICENSE ERROR: Conditional Access requires Azure AD Premium P1 or P2.\n"
                    f"Your tenant appears to have Azure AD Basic/Free which does not include "
                    f"Conditional Access features.\n\n"
                    f"Solutions:\n"
                    f"  1. Upgrade to Azure AD Premium P1 (~$6/user/month)\n"
                    f"  2. Start a free 30-day trial of Azure AD Premium P2\n"
                    f"  3. Use Microsoft 365 E3/E5 which includes Premium licenses\n\n"
                    f"Original error: {error_str}"
                )
            raise RuntimeError(f"Failed to deploy policy '{policy_data.displayName}': {error_str}")


def run_deploy_policy(policy_data: PolicyModel, dry_run: bool = True) -> str:
    """Synchronous wrapper for deploy_policy"""
    client = AzureGraphClient()
    return asyncio.run(client.deploy_policy(policy_data, dry_run))
