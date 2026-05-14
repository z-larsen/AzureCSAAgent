# Skill: Azure Compliance & Security Auditing

Run compliance and security audits across an Azure environment using Azure Resource Graph, Azure Policy, and Key Vault expiration checks.

## Trigger Phrases
- "compliance scan"
- "security audit"
- "Azure best practices review"
- "Key Vault expiration check"
- "expired certificates or secrets"
- "compliance assessment"
- "policy compliance"
- "security posture"

## Assessment Areas

### 1. Azure Policy Compliance
- Query policy assignments at management group, subscription, and resource group scopes
- Check for non-compliant resources and their policy definitions
- Identify CAF baseline policies (allowed locations, required tags, denied resource types)
- Custom policies vs built-in — coverage and effectiveness

### 2. Defender for Cloud
- Secure score across subscriptions
- Defender plan enablement per service (Servers, SQL, Storage, Key Vault, App Service, etc.)
- Unresolved recommendations by severity
- Regulatory compliance dashboard status (CIS, NIST, PCI-DSS)

### 3. Key Vault Expiration Monitoring
- Keys, secrets, and certificates approaching expiration (30, 60, 90 day windows)
- Items without expiration dates set (compliance risk)
- Expired items still in use
- Rotation policies configured vs missing

### 4. Resource Configuration Hygiene
- Orphaned resources (unattached disks, unused NICs, idle IPs)
- Resources without diagnostic settings
- Resources without locks on critical infrastructure
- Deprecated SKUs or API versions in use

### 5. Identity & Access
- Service principals with excessive permissions
- Stale service principals (no recent sign-in)
- Users with Owner role at subscription scope
- Missing PIM configuration for privileged roles

### 6. Network Security Posture
- Resources with public endpoints that should be private
- NSGs with overly permissive inbound rules
- Missing DDoS protection on public-facing VNets
- Defer to the Network Review skill for deep network analysis

## Output Format
Generate a report with:
- **Compliance Summary** — overall posture score and trend
- **Critical Findings** — immediate action required
- **High Priority** — resolve within days
- **Medium Priority** — plan for next sprint
- **Low Priority** — track during regular maintenance
- **References** — links to Microsoft Learn remediation guidance

## Prerequisites
- Reader access on target subscriptions
- Key Vault Reader for expiration checks
- Security Reader for Defender for Cloud data
