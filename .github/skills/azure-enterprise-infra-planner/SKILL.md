# Skill: Azure Enterprise Infrastructure Planner

Architect enterprise Azure infrastructure from workload descriptions — networking, identity, security, compliance, and multi-resource topologies aligned with the Well-Architected Framework.

## Trigger Phrases
- "plan Azure infrastructure"
- "architect Azure landing zone"
- "design hub-spoke network"
- "plan multi-region DR topology"
- "set up VNets firewalls and private endpoints"
- "design enterprise networking"
- "plan disaster recovery"
- "subscription-scope deployment"

## Assessment Areas

### 1. Requirements Gathering
- Workload type and expected scale
- Compliance and regulatory requirements
- Availability and DR requirements (RPO/RTO)
- Network connectivity needs (hybrid, multi-region, internet-facing)
- Identity and access control model
- Cost constraints

### 2. Network Architecture
- Hub-spoke vs Virtual WAN topology selection
- VNet address space planning (avoid overlaps with on-prem)
- Subnet sizing and delegation requirements
- DNS architecture (Azure DNS Private Zones, Private Resolver)
- Firewall placement and policy design
- ExpressRoute / VPN Gateway sizing
- Private endpoint strategy for PaaS services

### 3. Identity & Access
- Entra ID integration model
- RBAC design at management group, subscription, and resource group levels
- Managed identity strategy for workloads
- PIM configuration for privileged roles
- Conditional Access policies

### 4. Security & Compliance
- Network segmentation and micro-segmentation
- Defender for Cloud plan enablement
- Azure Policy assignments for governance guardrails
- Key Vault architecture (centralized vs per-workload)
- Encryption at rest and in transit

### 5. Resilience & DR
- Availability zone usage across services
- Cross-region failover design
- Backup strategy (Azure Backup, geo-replication)
- SLA composition across dependent services
- Traffic Manager / Front Door for global load balancing

### 6. Operations
- Monitoring and alerting architecture (Log Analytics, Application Insights)
- Diagnostic settings standardization
- Tagging strategy for cost allocation and governance
- Automation and IaC approach (Bicep or Terraform)

## Output Format
- **Architecture Decision Records** — key decisions with rationale
- **Resource List** — all resources with SKU, location, and dependencies
- **Network Diagram** — Mermaid diagram of topology
- **WAF Alignment** — per-pillar assessment of the design
- **IaC Recommendations** — Bicep or Terraform structure
- **References** — Microsoft Learn links for each design choice
