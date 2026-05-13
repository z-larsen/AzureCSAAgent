# Skill: Landing Zone Assessment

Assess an Azure environment's alignment with the Cloud Adoption Framework (CAF) Azure Landing Zone architecture.

## Trigger Phrases
- "assess this landing zone"
- "how does this environment align with CAF"
- "landing zone review"
- "enterprise-scale assessment"

## Assessment Checklist

Run these ARG queries and cross-reference against CAF guidance:

### 1. Management Group Structure
Query management group hierarchy. Compare against CAF recommended structure:
- Root MG → Platform (Identity, Management, Connectivity) + Landing Zones (Corp, Online) + Decommissioned + Sandbox

### 2. Subscription Organization
- Are subscriptions organized by workload/environment or dumped flat?
- Are there dedicated platform subscriptions (Connectivity, Identity, Management)?

### 3. Policy Coverage
- Query policy assignments at each MG level
- Check for CAF baseline policies (allowed locations, required tags, denied resource types)
- Look for custom policies vs built-in

### 4. Network Topology
- Hub-spoke or Virtual WAN?
- Is there a central connectivity subscription?
- DNS zones — centralized or scattered?
- Private endpoint DNS resolution chain

### 5. Identity
- PIM enabled?
- Custom RBAC roles — how many, are they scoped correctly?
- Service principal sprawl

### 6. Logging & Monitoring
- Is there a central Log Analytics workspace?
- Are diagnostic settings configured across subscriptions?
- Defender for Cloud coverage

## Output Format
Generate a report with:
- **Current State** — what exists today (grounded in ARG query results)
- **CAF Alignment Score** — per area (Management Groups, Network, Identity, Governance, Security)
- **Gaps** — what's missing or misconfigured
- **Recommendations** — prioritized by impact (Critical → Informational)
- **References** — links to specific Microsoft Learn pages

Save to `outputs/<customer>/landing-zone-assessment.md`
