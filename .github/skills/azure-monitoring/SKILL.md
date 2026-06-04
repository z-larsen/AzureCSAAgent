# Skill: Azure Monitoring & Observability Strategy

Proactively assess and design an Azure observability strategy — Log Analytics workspace topology, diagnostic settings coverage, the Azure Monitor Agent (AMA) and Data Collection Rules, alerting and action groups, Application Insights, and dashboards/workbooks. This is the *proactive design* counterpart to `azure-diagnostics` (which is *reactive* live-incident troubleshooting). If the user is debugging an active fire, use `azure-diagnostics`; if they're building or auditing their monitoring foundation, use this skill.

## Trigger Phrases
- "monitoring strategy"
- "observability assessment"
- "Log Analytics workspace design"
- "diagnostic settings coverage"
- "are we monitoring everything"
- "alerting strategy"
- "alert coverage review"
- "Azure Monitor design"
- "AMA migration" / "Azure Monitor Agent"
- "data collection rules"
- "Application Insights review"
- "monitoring gaps"
- "logging architecture"
- "what should we alert on"

## Assessment Areas

### 1. Log Analytics Workspace Topology
- All Log Analytics workspaces — location, SKU/pricing tier, retention, daily cap
- **Workspace sprawl** — many small workspaces vs a centralized design (centralized is usually preferred for cross-resource queries and RBAC simplicity)
- **Orphaned workspaces** — no resources sending data, no recent ingestion
- Retention configuration — default 30 days vs compliance-driven longer retention; archive tier usage
- Workspace placement relative to the resources sending to it (cross-region egress cost)
- Sentinel-enabled workspaces (security data) vs operational workspaces — are they intentionally separated?

### 2. Diagnostic Settings Coverage (the core gap audit)
- **Resources WITHOUT diagnostic settings** — the single most common observability gap. Query resource types that support diagnostics and flag those with none configured.
- Diagnostic settings destinations — Log Analytics vs Storage vs Event Hub; are logs actually queryable or just archived?
- Categories enabled — are the *useful* log categories on, or just metrics?
- Key resource types to verify: Key Vault, NSGs, Application Gateway, Firewall, SQL, Storage, App Service, AKS, Front Door, Load Balancer
- **Activity Log** — is it exported to a workspace for long-term query and alerting?

### 3. Azure Monitor Agent (AMA) & Data Collection Rules
- VMs/VMSS with the Azure Monitor Agent installed vs without (coverage gap)
- **Legacy Log Analytics agent (MMA/OMS) still in use** — deprecated; flag for migration to AMA
- Data Collection Rules (DCRs) — what's being collected, association coverage
- Data Collection Endpoints (DCEs) — present where required (private-link or specific regions)
- VM Insights / Container Insights enablement

### 4. Alerting & Action Groups
- **Metric alerts, log (scheduled query) alerts, activity log alerts** — inventory and scope
- **Resources/subscriptions with NO alerts** — silent blind spots
- **Action Groups** — do alerts actually notify someone? Action groups with no receivers are dead-ends
- Alert severity hygiene — everything Sev0, or a sensible severity model?
- Alert processing rules — suppression during maintenance windows
- Recommended baseline alerts present? (service health, resource health, budget/cost, key resource availability)
- **Service Health alerts** — configured to catch Azure platform incidents and planned maintenance?

### 5. Application Insights
- App Insights resources — workspace-based (current) vs classic (deprecated, flag for migration)
- Which apps are instrumented vs not — coverage gap for web apps, Functions, Container Apps
- Sampling configuration (cost vs fidelity trade-off)
- Availability tests configured for critical endpoints?
- Connected to the same workspace as platform logs (correlation benefit)?

### 6. Dashboards, Workbooks & Visualization
- Azure Workbooks in use — operational, security, cost
- Shared dashboards vs ad-hoc queries
- Azure Managed Grafana presence (if used)
- Gaps where a workbook would give the team standing visibility

### 7. Cost & Data Volume Governance
- Log Analytics ingestion volume and the resulting cost (ingestion is the #1 monitoring cost driver)
- Commitment tiers — is a capacity reservation cheaper than pay-as-you-go at current volume?
- Basic Logs / Auxiliary Logs tier for high-volume, low-query-frequency tables
- Tables with high ingestion but low query value (candidates for filtering at the DCR or transformation stage)
- Daily cap configured to prevent runaway cost (vs risk of dropping data)?

## Follow-Up Questions

Before concluding a monitoring assessment, confirm intent:

### Architecture Intent
- "You have [N] Log Analytics workspaces — is the distribution intentional (e.g. per-team RBAC, data sovereignty), or is consolidation worth exploring?"
- "Is Microsoft Sentinel in play? That changes whether security and operational data should share a workspace."

### Coverage & Priorities
- "I found [N] resources with no diagnostic settings — which workloads are business-critical so we prioritize their logging first?"
- "Are you still running the legacy MMA/OMS agent anywhere? It's deprecated and should move to AMA."

### Alerting Maturity
- "Several subscriptions have no alerts at all — is monitoring handled by an external tool (Datadog, Dynatrace), or is this a genuine gap?"
- "Do your alerts route to an action group with real receivers, or are some firing into the void?"

### Cost Posture
- "What's your monthly Log Analytics ingestion cost? At your volume a commitment tier or Basic Logs may cut it significantly."

## Risk Classification

| Severity | Examples |
|----------|---------|
| **Critical** | Business-critical resources with no diagnostic settings and no alerts, no Service Health alerts, action groups with no receivers (alerts go nowhere) |
| **High** | Legacy MMA/OMS agent still deployed, classic Application Insights (deprecated), Activity Log not exported, no resource health alerts on key workloads |
| **Medium** | Workspace sprawl with no consolidation rationale, default 30-day retention on compliance-relevant logs, critical web apps uninstrumented |
| **Low** | No commitment tier despite high ingestion, no shared workbooks, oversized retention on low-value tables |

## Output Format
Generate a report with:
- **Observability Summary** — workspace topology, diagnostic-settings coverage %, alert coverage, agent modernization status
- **Coverage Gaps** — resources with no diagnostics, no alerts, or uninstrumented (the actionable list)
- **Agent & Data Collection** — AMA vs legacy agent, DCR coverage
- **Alerting Posture** — alert inventory, action group health, baseline alert presence
- **Cost** — ingestion volume, tier recommendation, retention optimization
- **Findings** — prioritized by severity (Critical → Low) with specific resource names
- **Recommendations** — each with a Microsoft Learn reference (Azure Monitor best practices, AMA migration, alert design)
- **References** — Azure Monitor best practices, Well-Architected Operational Excellence pillar

Save to `outputs/<customer>/monitoring-assessment.md`
