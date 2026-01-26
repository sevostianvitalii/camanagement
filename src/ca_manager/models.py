"""Pydantic models for CA policy structure"""

from typing import Optional
from pydantic import BaseModel, Field


class PolicyMetadata(BaseModel):
    """Metadata for CA policy"""
    owner: str
    createdBy: str
    ticketId: str
    justification: str
    expirationDate: Optional[str] = None


class UserConditions(BaseModel):
    """User conditions for CA policy"""
    includeGroups: list[str] = Field(default_factory=list)
    excludeGroups: list[str] = Field(default_factory=list)
    includeUsers: list[str] = Field(default_factory=list)
    excludeUsers: list[str] = Field(default_factory=list)


class ApplicationConditions(BaseModel):
    """Application conditions for CA policy"""
    includeApplications: list[str] = Field(default_factory=list)
    excludeApplications: list[str] = Field(default_factory=list)


class LocationConditions(BaseModel):
    """Location conditions for CA policy"""
    includeLocations: list[str] = Field(default_factory=list)
    excludeLocations: list[str] = Field(default_factory=list)


class PlatformConditions(BaseModel):
    """Platform conditions for CA policy"""
    includePlatforms: list[str] = Field(default_factory=list)
    excludePlatforms: list[str] = Field(default_factory=list)


class Conditions(BaseModel):
    """All conditions for CA policy"""
    users: UserConditions = Field(default_factory=UserConditions)
    applications: ApplicationConditions = Field(default_factory=ApplicationConditions)
    locations: LocationConditions = Field(default_factory=LocationConditions)
    platforms: PlatformConditions = Field(default_factory=PlatformConditions)
    clientAppTypes: list[str] = Field(default_factory=list)
    signInRiskLevels: list[str] = Field(default_factory=list)
    userRiskLevels: list[str] = Field(default_factory=list)


class GrantControls(BaseModel):
    """Grant controls for CA policy"""
    operator: str = "OR"
    builtInControls: list[str] = Field(default_factory=list)
    customAuthenticationFactors: list[str] = Field(default_factory=list)
    termsOfUse: list[str] = Field(default_factory=list)


class SignInFrequency(BaseModel):
    """Sign-in frequency session control"""
    value: Optional[int] = None
    type: Optional[str] = None


class PersistentBrowser(BaseModel):
    """Persistent browser session control"""
    mode: Optional[str] = None


class CloudAppSecurity(BaseModel):
    """Cloud app security session control"""
    isEnabled: bool = False
    cloudAppSecurityType: Optional[str] = None


class SessionControls(BaseModel):
    """Session controls for CA policy"""
    signInFrequency: SignInFrequency = Field(default_factory=SignInFrequency)
    persistentBrowser: PersistentBrowser = Field(default_factory=PersistentBrowser)
    cloudAppSecurity: CloudAppSecurity = Field(default_factory=CloudAppSecurity)


class ConditionalAccessPolicy(BaseModel):
    """Complete CA policy model"""
    name: str
    displayName: str
    state: str  # enabled, disabled, enabledForReportingButNotEnforced
    metadata: PolicyMetadata
    conditions: Conditions
    grantControls: GrantControls
    sessionControls: SessionControls = Field(default_factory=SessionControls)


class NamingRules(BaseModel):
    """Naming convention rules loaded from baseline/naming-rules.yaml"""
    pattern: str
    environments: list[str]
    scopes: list[str]
    controls: list[str]
    numberRange: dict[str, int]


class ComplianceRules(BaseModel):
    """Compliance rules loaded from baseline/compliance-rules.yaml"""
    requiredExclusions: dict
    scopeRequirements: dict
    allowedStates: list[str]


class BestPractice(BaseModel):
    """Single best practice check"""
    id: str
    name: str
    severity: str
    check: str
    remediation: str
