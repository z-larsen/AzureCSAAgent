# Skill: Network Architecture Review

Deep-dive Azure networking assessment covering topology, connectivity, security, DNS, hybrid, and troubleshooting. This is the agent's primary expertise area.

## Trigger Phrases
- "network review"
- "networking assessment"
- "connectivity architecture"
- "DNS review"
- "private endpoint audit"
- "network troubleshooting"
- "connectivity issues"
- "routing problem"
- "firewall review"
- "ExpressRoute assessment"
- "VPN review"
- "vWAN assessment"
- "NSG audit"
- "subnet planning"
- "IP overlap"

## Assessment Areas

### 1. Network Resource Inventory
- Query all networking resources by type (microsoft.network/*)
- Establish the full scope before diving into specifics
- Identify the networking pattern in use (hub-spoke, vWAN, flat, hybrid)

### 2. VNet Topology & IP Planning
- All VNets with address spaces, subnets, locations
- **IP address overlap detection** — sort all VNet prefixes and flag duplicates or overlaps that will break peering or VPN
- Subnet sizing — are subnets over-provisioned or too small for growth?
- VNet peering state — connected, disconnected, peering direction, gateway transit settings, forwarded traffic
- Isolated VNets — no peering, no gateway, no VPN (potential orphans)
- Resources per subnet — identify empty subnets or subnets nearing IP exhaustion

### 3. Network Security (NSG Deep Dive)
- **Full rule audit** — every NSG rule with priority, direction, protocol, source/dest, ports
- **Overly permissive rules** — source 0.0.0.0/0 or * with Allow inbound (critical finding)
- **High-risk ports exposed** — RDP (3389), SSH (22), SMB (445), SQL (1433), management ports open to internet
- **Unassociated NSGs** — NSGs not attached to any subnet or NIC (cleanup candidates)
- **Subnets without NSGs** — workload subnets missing NSG protection (excludes GatewaySubnet, AzureFirewallSubnet, AzureBastionSubnet, RouteServerSubnet)
- **NSG flow logs** — check if flow logs are enabled for traffic visibility
- Priority analysis — conflicting or shadowed rules

### 4. Routing & Traffic Control
- **Route tables** — all UDRs with route count, BGP propagation status
- **Subnets without route tables** — subnets that may be using default system routes when they should have forced tunneling or NVA next-hops
- **NAT Gateways** — outbound connectivity pattern, associated subnets, public IP count
- **Azure Firewall** — SKU, tier, threat intelligence mode, DNS proxy settings, firewall policies
- **Firewall policies** — policy hierarchy (parent/child), rule collection groups, threat intel mode
- **Forced tunneling gaps** — subnets with internet-bound traffic not routed through a firewall or NVA

### 5. Public Exposure Assessment
- **All public IPs** — SKU (Basic vs Standard), allocation method, zone redundancy, DDoS settings
- **Unattached public IPs** — public IPs not associated with any resource (cost waste + attack surface)
- **NICs with public IPs** — VMs directly exposed to internet (should they be behind a load balancer or Bastion?)
- **DDoS Protection Plans** — coverage of VNets, or lack thereof
- **Application Gateways** — SKU, WAF enabled/disabled, SSL policy, listener/backend/probe counts
- **Load Balancers** — SKU (Basic is a problem), frontend IPs, backend pools, health probes, NAT rules
- **Front Door / CDN** — profiles, SKU, global load balancing presence
- **Bastion Hosts** — SKU, scale units, tunneling and shareable link settings

### 6. Hybrid & Cross-Region Connectivity
- **VPN Gateways** — SKU, VPN type (route-based vs policy-based), active-active, BGP ASN, generation
- **ExpressRoute Gateways** — SKU, associated VNet
- **ExpressRoute Circuits** — provider, peering location, bandwidth, SKU/tier, provisioning state, Global Reach
- **ExpressRoute Peerings** — peering type (Private, Microsoft), state, address prefixes, VLAN, peer ASN
- **Virtual WAN** — type (Standard vs Basic), branch-to-branch, VNet-to-VNet settings
- **Virtual WAN Hubs** — address prefixes, routing state, associated vWAN
- **Traffic Manager** — routing method, monitor status, endpoint count
- **Redundancy** — single ExpressRoute circuit (no resilience), single VPN gateway (not active-active)

### 7. Private Connectivity & Service Endpoints
- **Private Endpoints** — target resource, group (blob, sql, vault, etc.), connection state, subnet placement
- **Private endpoint coverage** — which PaaS resources are NOT using private endpoints when they should be?
- **Service Endpoints** — which subnets have service endpoints enabled, for which services
- **Private endpoints vs service endpoints** — flag cases where both are used for the same service (private endpoints are preferred)

### 8. DNS Architecture
- **Public DNS Zones** — record counts, name servers
- **Private DNS Zones** — record counts, VNet link count, auto-registration settings
- **Private DNS VNet Links** — which VNets are linked to which DNS zones, registration enabled
- **DNS resolution chain** — Private DNS Zone → VNet link → conditional forwarder (for hybrid)
- **Missing DNS zones for private endpoints** — private endpoints without corresponding privatelink.* DNS zones
- **Split-brain DNS** — public and private zones for the same domain

### 9. Connectivity Troubleshooting Patterns
When a user reports connectivity issues, follow this diagnostic sequence:

1. **Source to destination mapping** — identify source resource, destination resource, protocol, port
2. **Path analysis** — trace the network path: subnet → NSG (inbound/outbound) → route table → NVA/firewall → peering/gateway → destination NSG → destination
3. **NSG rule evaluation** — check both source and destination NSGs for allow/deny at the specific port/protocol
4. **Route verification** — check UDRs for next-hop overrides, BGP propagation status
5. **DNS resolution** — verify the destination resolves correctly (private DNS zone linked? conditional forwarder in place?)
6. **Firewall/NVA rules** — if traffic routes through a firewall, check application and network rule collections
7. **Service-specific checks** — storage firewalls, Key Vault network ACLs, SQL firewall rules, App Service access restrictions
8. **Cross-VNet** — peering state, allow forwarded traffic, allow gateway transit settings
9. **Hybrid** — VPN tunnel status, ExpressRoute circuit state, BGP learned routes
10. **Network Watcher** — recommend IP flow verify, next hop, connection troubleshoot, packet capture

### 10. Network Watcher Coverage
- **Network Watchers** — one should exist per region where you have resources
- Regions with resources but no Network Watcher (gap)
- Recommend enabling connection monitor, flow logs, and Traffic Analytics

## Risk Classification

| Severity | Examples |
|----------|---------|
| **Critical** | NSG allows 0.0.0.0/0 inbound on RDP/SSH, Basic SKU load balancer in production, no DDoS plan on internet-facing VNets, VMs with direct public IPs and no NSG |
| **High** | Subnets without NSGs, single ExpressRoute circuit (no redundancy), VPN gateway not active-active, no firewall/NVA in hub, IP address space overlap between VNets |
| **Medium** | Missing private DNS zones for private endpoints, subnets without route tables, unattached public IPs, unassociated NSGs, Basic SKU public IPs |
| **Low** | Network Watcher missing in a region, service endpoints where private endpoints preferred, oversized subnets, no Bastion (using direct RDP) |

## Output Format
Generate a report with:
- **Network Topology Summary** — pattern detected (hub-spoke/vWAN/flat), VNet count, peering map
- **IP Address Space** — all VNet prefixes sorted, overlap flags
- **Security Posture** — NSG coverage %, critical rule findings, firewall presence
- **Connectivity Architecture** — hybrid connections, gateways, redundancy assessment
- **Private Connectivity** — private endpoint coverage, DNS zone health
- **Findings** — prioritized by severity (Critical → Low) with specific resource names
- **Recommendations** — with Microsoft Learn references for each
- **Troubleshooting Checklist** — common connectivity failure points to verify

Save to `outputs/<customer>/network-review.md`
