# Skill: Landing Zone Migration (Deployment-Model Modernization)

Design and de-risk the migration of an *existing Azure estate* from a legacy or ad-hoc deployment model (flat/standalone subscriptions, classic/ASM remnants, hand-built "ClickOps" environments, or an early non-CAF design) into a modern **Cloud Adoption Framework landing zone**. The defining value of this skill is honesty about what *can't* cleanly migrate: it leads with the **migrate-vs-redeploy decision**, surfaces the gotchas before they bite, and maps a sequenced cutover. This is Azure-to-Azure modernization — for cross-cloud (AWS/GCP→Azure) use `azure-cloud-migrate`; for the assessment of the current state use `landing-zone-assessment`; for building the target IaC use `azure-iac-avm`.

## Trigger Phrases
- "migrate to a landing zone"
- "move to CAF landing zone"
- "modernize our subscription structure"
- "migrate from flat to hub-spoke"
- "adopt Azure Landing Zones"
- "subscription reorganization"
- "move resources to new subscription"
- "landing zone migration"
- "brownfield landing zone"
- "should we migrate or redeploy"

## Workflow

### 1. Assess current state (delegate, then build on it)
- Run `landing-zone-assessment` first to capture the as-is: management groups (or absence), subscription sprawl, networking topology, policy/governance gaps, identity model, tagging
- Inventory every workload and its resources, dependencies, data gravity, and criticality
- Capture the target CAF design (delegate the architecture to `azure-enterprise-infra-planner` if not already defined)

### 2. The migrate-vs-redeploy decision (run this per resource/workload)
For each workload, classify into **Move**, **Redeploy**, or **Rebuild**. Do not assume everything can be moved.

| Verdict | When | How |
|---------|------|-----|
| **Move** (relocate as-is) | Resource type supports subscription/RG move, region stays the same, no SKU/feature lock | `az resource move` / portal move, then re-parent under the new mgmt group/sub |
| **Redeploy** (IaC re-create in target, migrate data) | Region must change, resource can't be moved, or it's cleaner to land it fresh under AVM | Stand up target via IaC, migrate data/config, cutover, decommission source |
| **Rebuild** (re-architect) | Legacy/classic resource, deprecated SKU, or the workload needs modernization anyway | New architecture in the landing zone; treat as a mini-project |

### 3. Gotchas — surface these early (this is the point of the skill)
**Resource move limitations**
- Not all resource types support move; some support RG-move but not subscription-move. Always verify the specific type against Microsoft Learn's "move support" matrix before promising a move.
- **Region is immutable** — moving a resource does NOT change its region. "Move to a new region" always means redeploy + data migration, never a move.
- Moves are **operations with downtime/locks** — the source and target RGs are locked during the move; plan a maintenance window.
- Dependent resources often must move **together** (e.g. a VM with its disks, NICs, and sometimes its VNet) — partial moves fail validation.

**Networking gotchas**
- **VNets can't change region**; re-IP'ing or re-homing into a hub-spoke usually means new VNets + workload redeploy or careful peering bridge during transition
- **IP address overlap** between the old flat VNets and the new hub/spoke address plan will block peering — reconcile the address plan first
- Private endpoints, private DNS zone links, and NSG/UDR associations don't always survive a move cleanly — re-validate DNS resolution and routing post-move
- Peering and gateway connections may need to be torn down and re-established

**Identity & RBAC gotchas**
- **RBAC role assignments do NOT follow a resource on subscription move** — they're scoped to the old hierarchy; re-apply at the new scope
- Managed identities: system-assigned identities get a **new principal ID** if the resource is redeployed (not moved) — anything that granted that identity access must be re-granted
- Key Vault access policies / RBAC and any hardcoded resource IDs break when IDs change

**PaaS-specific gotchas**
- Some PaaS services can't be moved across subscriptions at all (verify per service); some lose features or require the same region
- Data services: moving the resource ≠ moving with zero downtime — plan replication/cutover (geo-replica → failover, backup/restore, or export/import)
- Resource locks and Azure Policy `deny` assignments at the target scope can silently block the landing — check target guardrails first

**Governance gotchas**
- Policies at the **target** management group may **deny** resources that were fine in the source (e.g. allowed-locations, required-tags, SKU restrictions) — a workload can fail to land because the new guardrails reject it; remediate the resource or stage policy in audit-then-enforce
- Cost/billing: subscription moves can change billing scope, reservations/savings-plan coverage, and tag-based cost allocation — flag the FinOps impact

### 4. When to recommend AGAINST migrating
Be the voice that says "don't." Recommend redeploy/rebuild instead of move when:
- The resource type doesn't support the move you need, or the **region has to change**
- The resource is classic/ASM or on a deprecated SKU (modernize, don't relocate the debt)
- The move's downtime/risk exceeds the cost of a clean redeploy
- Re-IP/address-plan reconciliation makes an in-place move more fragile than a fresh landing
- The workload is slated for modernization anyway — fold the migration into the rebuild

### 5. Sequencing & cutover
- **Platform first** — stand up the landing zone (mgmt groups, policy in audit mode, hub networking, identity, management) via `azure-iac-avm` before moving any workload
- **Wave plan** — order workloads by dependency and risk; pilot with a low-risk, low-dependency workload to validate the runbook
- **Parallel-run where possible** — build target, replicate data, validate, then cutover (DNS/traffic switch), keep source as rollback until verified
- **Promote policy from audit → enforce** only after workloads have landed and been remediated
- Per-wave runbook: pre-checks (move-support, policy, RBAC, DNS) → execute → validate (connectivity, identity, data integrity) → rollback criteria → decommission source

### 6. Visualize the target landing zone
Produce a diagram of the target so stakeholders can see it. Pick the engine that gives the most **accurate and visually appealing** result for the audience:
- **Polished architecture view (preferred for stakeholders)** — use the global `d2-gen-azure` skill to render D2 with official Azure icons; this gives the cleanest, most presentation-ready hub-spoke/vWAN and management-group visuals
- **Quick inline preview** — use the `renderMermaidDiagram` tool for a fast in-chat sketch while iterating; `azure-resource-visualizer` also produces Mermaid at resource-group scope
- **What to draw, regardless of engine:**
  - **Management-group / subscription hierarchy** — Tenant Root → Platform (Identity, Connectivity, Management) + Landing Zones (Corp, Online) → subscriptions
  - **Hub-spoke / vWAN topology** — hub (firewall, gateways, shared services) with spokes, peering, on-prem links
- Annotate the diagram with the migration waves (which workload lands where, in which wave)

## Follow-Up Questions
- "For each workload — does it need to change region? If yes, that's a redeploy, not a move, full stop."
- "Do the existing VNet address ranges overlap with the new hub-spoke plan? Overlap has to be resolved before any peering."
- "What downtime can each workload tolerate? That decides move-in-place vs parallel-run-and-cutover."
- "Are there classic/ASM resources or deprecated SKUs in scope? I'd flag those for rebuild rather than relocation."
- "What policies will the target management group enforce? Some current resources may be denied at the new scope."

## Risk Classification
| Severity | Examples |
|----------|---------|
| **Critical** | Planning an in-place "move" that actually requires a region change, moving a workload into a target scope whose policy will deny it, assuming RBAC follows the resource on a subscription move |
| **High** | VNet address overlap with the new hub-spoke plan, classic/ASM resources slated for relocation instead of rebuild, data services moved without a tested cutover/rollback |
| **Medium** | Private DNS / routing not re-validated post-move, reservation/billing-scope impact unaccounted for, missing pilot wave before bulk migration |
| **Low** | Tag re-application after move, cosmetic naming inconsistencies carried over from the source |

## Output Format
- **Current vs Target** — as-is summary and the CAF target design
- **Migration Disposition Matrix** — every workload classified Move / Redeploy / Rebuild with the reason
- **Gotcha Register** — the specific risks that apply to *this* estate (region locks, move-unsupported types, address overlap, policy denies, RBAC re-apply), each with mitigation
- **Wave Plan & Runbook** — sequenced waves, per-wave pre-checks/validate/rollback, cutover approach
- **Target Diagram** — Mermaid mgmt-group hierarchy + hub-spoke topology, annotated with waves
- **Recommendations** — including explicit "do NOT migrate / redeploy instead" calls where warranted, each with a Microsoft Learn reference
- **References** — CAF landing zone, Azure resource move support matrix, subscription/region constraints

Save to `outputs/<customer>/landing-zone-migration.md`
