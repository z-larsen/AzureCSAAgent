# Skill: Network Architecture Review

Assess Azure networking topology, connectivity, and security posture.

## Trigger Phrases
- "network review"
- "networking assessment"
- "connectivity architecture"
- "DNS review"
- "private endpoint audit"

## Assessment Areas

### 1. Topology Discovery
- Query all VNets, subnets, peerings, and VPN/ExpressRoute gateways
- Map hub-spoke or Virtual WAN topology
- Identify orphaned or isolated VNets (no peering, no gateway)

### 2. Private Endpoint & DNS
- Query all private endpoints across subscriptions
- Check for corresponding Private DNS Zones
- Identify services still using public endpoints that should be private
- DNS resolution chain: Private DNS Zone → VNet link → conditional forwarder

### 3. Network Security
- NSG rules audit — are there overly permissive rules (0.0.0.0/0, Any-Any)?
- Azure Firewall or NVA presence in hub
- DDoS Protection Plan coverage
- WAF (Web Application Firewall) on Application Gateways and Front Door

### 4. Hybrid Connectivity
- ExpressRoute circuits — location, bandwidth, redundancy
- VPN Gateways — SKU, active-active configuration
- On-premises IP range overlap detection

### 5. Cross-Region
- Global peering vs regional isolation
- Traffic Manager / Front Door for multi-region workloads
- Data residency implications

## Output Format
Generate a report with:
- **Topology Diagram Description** — text-based description of discovered topology
- **Findings** — prioritized by risk (Critical: public endpoints, overly permissive NSGs; High: missing DNS zones; Medium: suboptimal SKUs)
- **Recommendations** — with specific Microsoft Learn references
- **Quick Reference** — IP ranges, VNet sizes, subnet allocations discovered

Save to `outputs/<customer>/network-review.md`
