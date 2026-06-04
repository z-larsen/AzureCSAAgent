# Skill: Azure Identity & Access Posture

Assess the identity and access posture of an Azure tenant across two data planes: the **Azure RBAC plane** (role assignments, custom roles, managed identities — queryable via Azure Resource Graph) and the **Microsoft Entra ID plane** (Conditional Access, PIM, MFA, risky users, guest governance — queryable via Microsoft Graph, NOT ARG). This skill complements `azure-rbac` (which picks the right role) and `entra-app-registration` (which registers apps) by giving the full identity *posture* picture.

## Data Source Reality (read this first)

Identity assessment spans two planes with different query tools. Be explicit about which plane each finding comes from:

| Plane | What lives here | How to query | Available to this agent? |
|-------|-----------------|--------------|--------------------------|
| **Azure RBAC** | Role assignments, role definitions, classic admins, managed identities | ARG `authorizationresources` + `microsoft.managedidentity/*` | ✅ Yes (ARM MCP / `azure-mcp/role`) |
| **Microsoft Entra ID** | Conditional Access, PIM, MFA registration, risky users/sign-ins, guests, app consent, legacy auth | Microsoft Graph (`az ad`, Graph PowerShell, or a Graph MCP) | ⚠️ Only via `az` CLI fallback — ARG cannot see this |

When an Entra-plane check is requested and no Graph access is configured, say so plainly and provide the exact `az` / `Get-Mg*` command the user can run, rather than guessing.

## Trigger Phrases
- "identity assessment"
- "identity posture"
- "Entra ID review"
- "Conditional Access review"
- "PIM assessment"
- "MFA coverage"
- "review role assignments" (broad scope — defer to `azure-rbac` for a single role pick)
- "privileged access review"
- "guest user audit"
- "service principal hygiene"
- "managed identity audit"
- "Zero Trust identity"
- "legacy authentication"
- "orphaned role assignments"

## Assessment Areas

### 1. Privileged Role Assignments (Azure RBAC plane — ARG)
- All assignments of high-privilege roles: Owner, Contributor, User Access Administrator, Role Based Access Control Administrator
- **Standing privileged access** — Owner/UAA assigned permanently (should be PIM-eligible, not active)
- Privileged roles assigned at management group / subscription scope (broad blast radius)
- Count of distinct principals holding Owner across the tenant (privilege sprawl)
- Human users vs service principals vs managed identities holding privileged roles

### 2. Role Assignment Hygiene (Azure RBAC plane — ARG)
- **Orphaned assignments** — role assignments to principals (`principalType`) that no longer resolve (deleted users/SPs leave dangling GUIDs)
- **Guest user assignments** — external (`#EXT#`) identities with Azure RBAC roles, and at what scope
- **Classic administrators** — Co-Administrators / Service Administrators still present (legacy, should be removed)
- Assignments at resource scope that duplicate inherited assignments (redundant grants)
- Direct user assignments vs group-based (group-based is preferred for manageability)

### 3. Custom Role Sprawl (Azure RBAC plane — ARG)
- All custom role definitions, their actions, and assignable scopes
- **Over-broad custom roles** — custom roles with wildcard `*` actions (defeats least privilege)
- Custom roles that duplicate a built-in role (unnecessary maintenance)
- Unused custom roles (defined but never assigned)

### 4. Managed Identities & Service Principals (Azure RBAC plane — ARG)
- All user-assigned managed identities and which resources reference them
- **Orphaned user-assigned MIs** — not attached to any resource
- System-assigned vs user-assigned usage patterns
- Service principals holding privileged Azure roles (where the SP is also queryable in ARG via role assignments)
- Recommend managed identities over service principals with secrets wherever a workload runs in Azure

### 5. Conditional Access Coverage (Entra plane — Graph/CLI)
- Are there CA policies requiring MFA for all users? For admins specifically?
- **Policies in report-only mode** that were never promoted to enforced
- Coverage gaps — users/apps excluded from MFA policies
- Legacy authentication blocked? (basic auth bypasses MFA entirely)
- Device compliance / managed-device requirements for privileged access
- Note: requires Graph — provide `az ad` or `Get-MgIdentityConditionalAccessPolicy` commands if no Graph MCP

### 6. Privileged Identity Management (Entra plane — Graph/CLI)
- Are privileged roles PIM-eligible (just-in-time) rather than permanently active?
- Activation requirements — MFA on activation, approval, justification, max duration
- Permanent active assignments to Global Administrator, Privileged Role Administrator (highest risk)
- Access reviews configured for privileged roles?

### 7. MFA & Authentication Methods (Entra plane — Graph/CLI)
- MFA registration coverage across the user base
- Phishing-resistant methods (FIDO2, Windows Hello, certificate-based) vs SMS/voice
- Security defaults enabled (tenants without CA) vs CA-based controls
- Users with no strong auth method registered

### 8. Guest & External Identity Governance (Entra plane — Graph/CLI)
- Guest (B2B) user count and last sign-in activity (stale guests)
- External collaboration settings — who can invite guests
- Guests holding Azure RBAC roles (cross-reference with Area 2)
- Access reviews for guest access

### 9. Application & Consent Hygiene (Entra plane — Graph/CLI)
- App registrations with **expiring or expired client secrets/certificates**
- Over-privileged app permissions (high-risk Graph scopes granted, e.g. `Directory.ReadWrite.All`)
- User consent settings — can users consent to apps themselves (consent phishing risk)?
- Stale enterprise applications with no recent sign-ins

## Follow-Up Questions

Before concluding an identity assessment, confirm intent and the data-plane reality:

### Scope & Data Access
- "Do you have Microsoft Graph access configured (a Graph MCP, or can I generate `az ad` commands)? Several checks — CA, PIM, MFA — live in Entra and aren't visible to Resource Graph."
- "Is this a single-subscription review or tenant-wide privileged-access posture?"

### Privileged Access Intent
- "I found [N] permanent Owner assignments at subscription scope — is PIM eligibility planned, or is standing access an accepted risk?"
- "Classic administrators still exist — are those still needed, or can we remove them?"

### Identity Governance Maturity
- "Are you using group-based RBAC assignments, or direct user grants? Direct grants are harder to govern at scale."
- "I see [N] guest users with role assignments — is there an access-review process for external identities?"

## Risk Classification

| Severity | Examples |
|----------|---------|
| **Critical** | Owner/Global Admin permanently active with no MFA, legacy auth not blocked, user consent to apps unrestricted, expired secrets on a privileged app still in use |
| **High** | No PIM (all privileged access standing), no CA MFA policy for admins, classic administrators present, custom roles with wildcard actions, orphaned privileged assignments |
| **Medium** | Direct user RBAC assignments instead of groups, stale guests with roles, user-assigned MIs orphaned, report-only CA policies never enforced |
| **Low** | Redundant inherited assignments, unused custom roles, SMS-based MFA instead of phishing-resistant methods |

## Output Format
Generate a report with:
- **Identity Posture Summary** — privileged principal count, MFA/PIM/CA status at a glance, data-plane coverage note (what was queryable vs Graph-only)
- **Privileged Access** — standing vs eligible, blast-radius scope, sprawl metrics
- **RBAC Hygiene** — orphaned assignments, guest grants, classic admins, custom role findings
- **Entra Controls** — CA coverage, PIM, MFA, legacy auth (or a clear "requires Graph" note with the exact commands to run)
- **Findings** — prioritized by severity (Critical → Low) with specific principal/role names and scopes
- **Recommendations** — least-privilege + Zero Trust aligned, each with a Microsoft Learn reference
- **References** — links to Entra ID security operations, Zero Trust, and PIM Learn docs

Save to `outputs/<customer>/identity-assessment.md`
