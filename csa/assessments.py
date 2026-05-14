"""Assessment runner — orchestrates advisory assessments by type."""

from pathlib import Path
from datetime import datetime, timezone

from rich.console import Console

from csa.arg_client import execute_query

console = Console()


def _rows(results: dict, key: str) -> list:
    """Safely get data rows from a query result."""
    entry = results.get(key, {})
    if "error" in entry or not isinstance(entry.get("data"), list):
        return []
    return entry["data"]


def _count(results: dict, key: str) -> int:
    """Safely get row count from a query result."""
    entry = results.get(key, {})
    if "error" in entry:
        return 0
    return entry.get("count", 0)


# ── Network Analysis Engine ───────────────────────────────────────

HIGH_RISK_PORTS = {"3389", "22", "445", "1433", "1434", "3306", "5432", "27017", "9200", "6379", "23", "21"}

LEARN_URLS = {
    "nsg_best_practices": "https://learn.microsoft.com/azure/virtual-network/network-security-group-how-it-works",
    "nsg_rules": "https://learn.microsoft.com/azure/virtual-network/manage-network-security-group#work-with-security-rules",
    "udr": "https://learn.microsoft.com/azure/virtual-network/virtual-networks-udr-overview",
    "private_endpoints": "https://learn.microsoft.com/azure/private-link/private-endpoint-overview",
    "private_dns": "https://learn.microsoft.com/azure/dns/private-dns-overview",
    "ddos": "https://learn.microsoft.com/azure/ddos-protection/ddos-protection-overview",
    "bastion": "https://learn.microsoft.com/azure/bastion/bastion-overview",
    "firewall": "https://learn.microsoft.com/azure/firewall/overview",
    "firewall_policy": "https://learn.microsoft.com/azure/firewall/policy-rule-sets",
    "expressroute_redundancy": "https://learn.microsoft.com/azure/expressroute/designing-for-high-availability-with-expressroute",
    "vpn_active_active": "https://learn.microsoft.com/azure/vpn-gateway/vpn-gateway-highlyavailable",
    "hub_spoke": "https://learn.microsoft.com/azure/architecture/networking/architecture/hub-spoke",
    "vwan": "https://learn.microsoft.com/azure/virtual-wan/virtual-wan-about",
    "lb_basic_retirement": "https://learn.microsoft.com/azure/load-balancer/load-balancer-basic-upgrade-guidance",
    "pip_basic_retirement": "https://learn.microsoft.com/azure/virtual-network/ip-services/public-ip-basic-upgrade-guidance",
    "appgw_waf": "https://learn.microsoft.com/azure/web-application-firewall/ag/ag-overview",
    "nat_gateway": "https://learn.microsoft.com/azure/nat-gateway/nat-overview",
    "network_watcher": "https://learn.microsoft.com/azure/network-watcher/network-watcher-overview",
    "ip_planning": "https://learn.microsoft.com/azure/cloud-adoption-framework/ready/azure-best-practices/plan-for-ip-addressing",
    "vnet_peering": "https://learn.microsoft.com/azure/virtual-network/virtual-network-peering-overview",
    "front_door": "https://learn.microsoft.com/azure/frontdoor/front-door-overview",
    "traffic_manager": "https://learn.microsoft.com/azure/traffic-manager/traffic-manager-overview",
    "dns_private_resolver": "https://learn.microsoft.com/azure/dns/dns-private-resolver-overview",
    "forced_tunneling": "https://learn.microsoft.com/azure/vpn-gateway/about-forced-tunneling",
    "service_endpoints": "https://learn.microsoft.com/azure/virtual-network/virtual-network-service-endpoints-overview",
    "nsg_flow_logs": "https://learn.microsoft.com/azure/network-watcher/nsg-flow-logs-overview",
    "traffic_analytics": "https://learn.microsoft.com/azure/network-watcher/traffic-analytics",
    "connection_monitor": "https://learn.microsoft.com/azure/network-watcher/connection-monitor-overview",
    "accelerated_networking": "https://learn.microsoft.com/azure/virtual-network/accelerated-networking-overview",
    "vnet_custom_dns": "https://learn.microsoft.com/azure/virtual-network/virtual-networks-name-resolution-for-vms-and-role-instances",
    "storage_network_rules": "https://learn.microsoft.com/azure/storage/common/storage-network-security",
    "keyvault_network": "https://learn.microsoft.com/azure/key-vault/general/network-security",
    "vwan_routing": "https://learn.microsoft.com/azure/virtual-wan/about-virtual-hub-routing",
    "packet_capture": "https://learn.microsoft.com/azure/network-watcher/packet-capture-overview",
    "ip_flow_verify": "https://learn.microsoft.com/azure/network-watcher/ip-flow-verify-overview",
    "next_hop": "https://learn.microsoft.com/azure/network-watcher/next-hop-overview",
    "subnet_delegation": "https://learn.microsoft.com/azure/virtual-network/subnet-delegation-overview",
}


def _analyze_network(results: dict) -> list[dict]:
    """Analyze network query results and return structured findings."""
    findings = []

    def add(severity, category, title, detail, recommendation, learn_key=None):
        finding = {
            "severity": severity,
            "category": category,
            "title": title,
            "detail": detail,
            "recommendation": recommendation,
        }
        if learn_key and learn_key in LEARN_URLS:
            finding["reference"] = LEARN_URLS[learn_key]
        findings.append(finding)

    # ── Topology Detection ────────────────────────────────────
    has_firewall = _count(results, "firewalls") > 0
    has_vwan = _count(results, "virtual_wan") > 0
    has_peerings = _count(results, "vnet_peerings") > 0
    has_vpn = _count(results, "vpn_gateways") > 0
    has_er = _count(results, "expressroute_circuits") > 0

    vnet_count = 0
    vnet_rows = _rows(results, "vnet_details")
    if vnet_rows:
        vnet_names = set()
        for r in vnet_rows:
            vnet_names.add(r.get("vnetName", ""))
        vnet_count = len(vnet_names)

    if has_vwan:
        topology = "Virtual WAN"
    elif has_firewall and has_peerings:
        topology = "Hub-Spoke (with Azure Firewall)"
    elif has_peerings:
        topology = "Hub-Spoke (no central firewall detected)"
    elif vnet_count > 1:
        topology = "Multiple isolated VNets (no peering)"
    elif vnet_count == 1:
        topology = "Single VNet"
    else:
        topology = "No VNets detected"

    add("Info", "Topology", f"Network topology: {topology}",
        f"Detected {vnet_count} VNet(s), {_count(results, 'vnet_peerings')} peering(s), "
        f"{'Azure Firewall present' if has_firewall else 'no Azure Firewall'}, "
        f"{'vWAN deployed' if has_vwan else 'no vWAN'}.",
        "Review the detected topology against your target architecture.",
        "hub_spoke" if not has_vwan else "vwan")

    # No central firewall in multi-VNet environment
    if vnet_count > 1 and not has_firewall and not has_vwan:
        add("High", "Routing", "No central firewall or NVA detected",
            f"{vnet_count} VNets with peering but no Azure Firewall for centralized traffic inspection.",
            "Deploy Azure Firewall (or a third-party NVA) in the hub VNet for east-west and north-south traffic inspection. "
            "Route all traffic through the firewall using UDRs with 0.0.0.0/0 → NVA next-hop.",
            "firewall")

    # ── NSG: Overly Permissive Rules ──────────────────────────
    permissive_rules = _rows(results, "nsg_any_rules")
    if permissive_rules:
        high_risk = []
        for rule in permissive_rules:
            port = str(rule.get("destinationPort", rule.get("destinationPortRange", "")))
            if port in HIGH_RISK_PORTS or port == "*":
                high_risk.append(rule)

        if high_risk:
            names = ", ".join(set(f"{r.get('name', '?')}/{r.get('ruleName', '?')}" for r in high_risk[:5]))
            add("Critical", "Security", f"{len(high_risk)} NSG rule(s) expose high-risk ports to the internet",
                f"Rules allowing inbound 0.0.0.0/0 to high-risk ports (RDP, SSH, SQL, SMB, etc.): {names}",
                "Remove or scope these rules to specific source IP ranges immediately. Use Azure Bastion for remote access instead of exposing RDP/SSH.",
                "nsg_best_practices")

        non_high_risk = [r for r in permissive_rules if r not in high_risk]
        if non_high_risk:
            add("High", "Security", f"{len(non_high_risk)} NSG rule(s) allow inbound from any source",
                f"Rules with sourceAddressPrefix '*' allowing inbound traffic on non-management ports.",
                "Review each rule and restrict source addresses to known IP ranges or service tags.",
                "nsg_rules")

    # ── NSG: Subnets without NSG ──────────────────────────────
    no_nsg = _rows(results, "subnets_without_nsg")
    if no_nsg:
        subnet_list = ", ".join(f"{r.get('vnetName', '?')}/{r.get('subnetName', '?')}" for r in no_nsg[:8])
        add("High", "Security", f"{len(no_nsg)} workload subnet(s) have no NSG attached",
            f"Subnets without network security groups: {subnet_list}{'...' if len(no_nsg) > 8 else ''}",
            "Attach an NSG to every workload subnet. NSGs provide the first layer of network security. "
            "Even a default-deny NSG is better than no NSG.",
            "nsg_best_practices")

    # ── NSG: Unassociated ─────────────────────────────────────
    orphan_nsgs = _rows(results, "nsgs_unassociated")
    if orphan_nsgs:
        add("Low", "Hygiene", f"{len(orphan_nsgs)} NSG(s) not attached to any subnet or NIC",
            f"Unassociated NSGs: {', '.join(r.get('name', '?') for r in orphan_nsgs[:5])}",
            "Review and delete unused NSGs to reduce clutter and avoid confusion during troubleshooting.",
            "nsg_best_practices")

    # ── Routing: Subnets without Route Table ──────────────────
    no_rt = _rows(results, "subnets_without_route_table")
    if no_rt and has_firewall:
        subnet_list = ", ".join(f"{r.get('vnetName', '?')}/{r.get('subnetName', '?')}" for r in no_rt[:8])
        add("High", "Routing", f"{len(no_rt)} subnet(s) have no route table (forced tunneling gap)",
            f"Subnets using default system routes despite a firewall being present: {subnet_list}{'...' if len(no_rt) > 8 else ''}",
            "Attach a UDR with 0.0.0.0/0 → Virtual Appliance (firewall IP) to force all internet-bound traffic through the firewall. "
            "Without this, traffic bypasses the firewall via default system routes.",
            "forced_tunneling")
    elif no_rt:
        add("Medium", "Routing", f"{len(no_rt)} subnet(s) have no route table",
            f"Subnets using only default system routes: {', '.join(r.get('subnetName', '?') for r in no_rt[:8])}",
            "Consider whether custom routes are needed for traffic inspection, forced tunneling, or NVA integration.",
            "udr")

    # ── Routing: BGP propagation disabled ─────────────────────
    route_tables = _rows(results, "route_tables")
    bgp_disabled = [r for r in route_tables if r.get("disableBgp") is True]
    if bgp_disabled and (has_vpn or has_er):
        add("Medium", "Routing", f"{len(bgp_disabled)} route table(s) have BGP propagation disabled",
            f"Route tables with disableBgpRoutePropagation=true: {', '.join(r.get('name', '?') for r in bgp_disabled[:5])}. "
            f"This prevents VPN/ExpressRoute learned routes from being injected into these subnets.",
            "Verify this is intentional. If subnets need connectivity to on-premises via VPN/ExpressRoute, "
            "enable BGP propagation. Common in forced-tunneling scenarios where you only want UDR routes.",
            "udr")

    # ── Public Exposure ───────────────────────────────────────
    pip_rows = _rows(results, "public_ip_details")
    if pip_rows:
        unattached = [r for r in pip_rows if not r.get("attached")]
        basic_pips = [r for r in pip_rows if str(r.get("sku", "")).lower() == "basic"]
        no_ddos = [r for r in pip_rows if r.get("attached") and not r.get("ddosProtection")]

        if unattached:
            add("Medium", "Hygiene", f"{len(unattached)} unattached public IP(s)",
                f"Public IPs not associated with any resource: {', '.join(r.get('name', '?') for r in unattached[:5])}",
                "Delete unattached public IPs to reduce attack surface and cost (~$3.65/month each).",
                "ddos")

        if basic_pips:
            add("High", "Security", f"{len(basic_pips)} Basic SKU public IP(s) detected",
                f"Basic SKU public IPs: {', '.join(r.get('name', '?') for r in basic_pips[:5])}. "
                "Basic SKU is being retired and lacks zone redundancy and DDoS integration.",
                "Upgrade all Basic SKU public IPs to Standard SKU. Basic SKU retirement is underway.",
                "pip_basic_retirement")

        if no_ddos and len(pip_rows) > 0:
            add("Medium", "Security", f"{len(no_ddos)} public IP(s) without DDoS protection",
                "Public IPs attached to resources but without DDoS Protection enabled.",
                "Enable Azure DDoS Protection on VNets with internet-facing workloads.",
                "ddos")

    # ── NICs with direct public IPs ───────────────────────────
    direct_pip = _rows(results, "nics_with_public_ip")
    if direct_pip:
        add("High", "Security", f"{len(direct_pip)} VM NIC(s) have direct public IPs",
            f"VMs directly exposed to the internet via NIC public IP. "
            f"NICs: {', '.join(r.get('nicName', '?') for r in direct_pip[:5])}",
            "Remove public IPs from VM NICs. Use Azure Bastion for management access, "
            "Load Balancer or Application Gateway for application traffic.",
            "bastion")

    # ── Load Balancers ────────────────────────────────────────
    lbs = _rows(results, "load_balancers")
    basic_lbs = [r for r in lbs if str(r.get("sku", "")).lower() == "basic"]
    if basic_lbs:
        add("Critical", "Security", f"{len(basic_lbs)} Basic SKU Load Balancer(s) detected",
            f"Basic Load Balancers: {', '.join(r.get('name', '?') for r in basic_lbs)}. "
            "Basic SKU is being retired, has no SLA, no zone redundancy, and no NSG enforcement on backend pools.",
            "Upgrade to Standard SKU Load Balancer immediately. Basic LB retirement deadline is approaching.",
            "lb_basic_retirement")

    # ── Application Gateway / WAF ─────────────────────────────
    appgws = _rows(results, "application_gateways")
    no_waf = [r for r in appgws if not r.get("wafEnabled")]
    if no_waf:
        add("High", "Security", f"{len(no_waf)} Application Gateway(s) without WAF enabled",
            f"Application Gateways not running WAF: {', '.join(r.get('name', '?') for r in no_waf[:5])}",
            "Enable WAF v2 on internet-facing Application Gateways to protect against OWASP Top 10 attacks.",
            "appgw_waf")

    # ── Firewall Configuration ────────────────────────────────
    fw_policies = _rows(results, "firewall_policies")
    alert_only = [r for r in fw_policies if str(r.get("threatIntelMode", "")).lower() == "alert"]
    if alert_only:
        add("Medium", "Security", f"{len(alert_only)} firewall policy(ies) with threat intel in Alert-only mode",
            f"Policies: {', '.join(r.get('name', '?') for r in alert_only[:5])}. "
            "Alert mode logs known malicious traffic but does not block it.",
            "Set threat intelligence mode to 'Deny' to actively block traffic from known malicious IPs and FQDNs.",
            "firewall_policy")

    no_dns_proxy = [r for r in fw_policies if not r.get("dnsProxy")]
    if no_dns_proxy and fw_policies:
        add("Medium", "DNS", f"{len(no_dns_proxy)} firewall policy(ies) without DNS proxy enabled",
            "DNS proxy must be enabled on Azure Firewall for FQDN-based network rules and private endpoint DNS resolution through the firewall.",
            "Enable DNS proxy on firewall policies. This is required for FQDN filtering in network rules "
            "and for proper DNS resolution when private endpoints are accessed through the firewall.",
            "firewall_policy")

    # ── Hybrid Connectivity Redundancy ────────────────────────
    vpn_gws = _rows(results, "vpn_gateways")
    single_vpn = [r for r in vpn_gws if not r.get("activeActive")]
    if single_vpn:
        add("High", "Reliability", f"{len(single_vpn)} VPN Gateway(s) not in active-active mode",
            f"VPN Gateways in active-standby: {', '.join(r.get('name', '?') for r in single_vpn[:5])}. "
            "Active-standby means a single tunnel failure causes an outage during failover (~10-30 seconds).",
            "Enable active-active mode for production VPN Gateways to eliminate single points of failure.",
            "vpn_active_active")

    er_circuits = _rows(results, "expressroute_circuits")
    if len(er_circuits) == 1:
        c = er_circuits[0]
        add("High", "Reliability", "Single ExpressRoute circuit (no redundancy)",
            f"Only one ExpressRoute circuit detected: {c.get('name', '?')} "
            f"({c.get('serviceProvider', '?')} / {c.get('peeringLocation', '?')} / {c.get('bandwidthMbps', '?')} Mbps). "
            "A single circuit is a single point of failure for hybrid connectivity.",
            "Deploy a second ExpressRoute circuit in a different peering location for disaster recovery. "
            "Consider ExpressRoute + VPN as backup if a second circuit is not feasible.",
            "expressroute_redundancy")

    # ── Private Connectivity ──────────────────────────────────
    pe_rows = _rows(results, "private_endpoint_details")
    if pe_rows:
        failed = [r for r in pe_rows if str(r.get("connectionState", "")).lower() not in ("approved", "")]
        if failed:
            add("High", "Connectivity", f"{len(failed)} private endpoint(s) not in Approved state",
                f"Private endpoints with connection issues: {', '.join(r.get('name', '?') for r in failed[:5])}",
                "Review and approve pending private endpoint connections. Rejected or disconnected endpoints cannot route traffic.",
                "private_endpoints")

    # ── Private DNS ───────────────────────────────────────────
    pdns = _rows(results, "private_dns_zones")
    pdns_links = _rows(results, "private_dns_vnet_links")
    if pe_rows and not pdns:
        add("High", "DNS", "Private endpoints exist but no Private DNS Zones found",
            f"{len(pe_rows)} private endpoint(s) deployed without corresponding Private DNS Zones. "
            "DNS resolution will fail unless custom DNS is configured.",
            "Create Private DNS Zones for each private endpoint service (e.g., privatelink.blob.core.windows.net) "
            "and link them to VNets that need to resolve private endpoint addresses.",
            "private_dns")
    elif pdns and not pdns_links:
        add("High", "DNS", "Private DNS Zones exist but no VNet links found",
            "Private DNS Zones are created but not linked to any VNet. DNS queries from VNets will not use these zones.",
            "Link Private DNS Zones to all VNets that need private endpoint resolution.",
            "private_dns")

    # ── IP Address Overlap ────────────────────────────────────
    ip_rows = _rows(results, "ip_address_overlap")
    if len(ip_rows) > 1:
        seen_prefixes = {}
        overlaps = []
        for r in ip_rows:
            prefix = r.get("addressPrefix", "")
            vnet = r.get("vnetName", "")
            if prefix in seen_prefixes:
                overlaps.append((prefix, seen_prefixes[prefix], vnet))
            seen_prefixes[prefix] = vnet

        if overlaps:
            detail_parts = [f"{p} used by {v1} and {v2}" for p, v1, v2 in overlaps[:5]]
            add("Critical", "IP Planning", f"{len(overlaps)} IP address space overlap(s) detected",
                f"Overlapping address prefixes: {'; '.join(detail_parts)}. "
                "Overlapping address spaces prevent VNet peering and VPN connectivity.",
                "Re-address one of the overlapping VNets. Plan IP address spaces using a centralized IPAM strategy "
                "to prevent future conflicts.",
                "ip_planning")

    # ── DDoS Plan Coverage ────────────────────────────────────
    ddos = _rows(results, "ddos_plans")
    if not ddos and pip_rows:
        attached_pips = [r for r in pip_rows if r.get("attached")]
        if attached_pips:
            add("Medium", "Security", "No DDoS Protection Plan found",
                f"{len(attached_pips)} public IP(s) in use without an Azure DDoS Protection Plan.",
                "Deploy Azure DDoS Network Protection on VNets with internet-facing workloads. "
                "Note: DDoS Protection costs ~$2,944/month but covers up to 100 public IPs.",
                "ddos")

    # ── Bastion ───────────────────────────────────────────────
    bastions = _rows(results, "bastion_hosts")
    if not bastions and direct_pip:
        add("High", "Security", "No Azure Bastion deployed but VMs have direct public IPs",
            "VMs are exposed to the internet for remote access without Bastion as a secure alternative.",
            "Deploy Azure Bastion to eliminate the need for public IPs on VMs. "
            "Bastion provides secure RDP/SSH through the Azure portal without exposing management ports.",
            "bastion")

    # ── Network Watcher ───────────────────────────────────────
    watchers = _rows(results, "network_watchers")
    watcher_regions = set(r.get("location", "") for r in watchers)
    resource_regions = set()
    for r in _rows(results, "vnet_details"):
        resource_regions.add(r.get("location", ""))
    missing_regions = resource_regions - watcher_regions
    if missing_regions:
        add("Low", "Observability", f"Network Watcher missing in {len(missing_regions)} region(s)",
            f"Regions with VNets but no Network Watcher: {', '.join(sorted(missing_regions))}",
            "Enable Network Watcher in all regions with network resources. Required for NSG flow logs, "
            "connection troubleshoot, IP flow verify, next hop, and packet capture.",
            "network_watcher")

    # ── NAT Gateway ───────────────────────────────────────────
    nats = _rows(results, "nat_gateways")
    if not nats and vnet_count > 0 and not has_firewall:
        add("Medium", "Connectivity", "No NAT Gateway and no Azure Firewall for outbound",
            "Workloads rely on default outbound access for internet connectivity. "
            "Azure is retiring default outbound access for new VMs.",
            "Deploy NAT Gateway on subnets that need outbound internet access, "
            "or route through Azure Firewall for centralized outbound control.",
            "nat_gateway")

    # ── vWAN Hub Routing State ────────────────────────────────
    vwan_hubs = _rows(results, "virtual_wan_hubs")
    failed_hubs = [h for h in vwan_hubs if str(h.get("routingState", "")).lower() not in ("provisioned", "")]
    if failed_hubs:
        add("Critical", "Routing", f"{len(failed_hubs)} vWAN Hub(s) with routing issues",
            f"Hubs not in 'Provisioned' routing state: {', '.join(h.get('name', '?') for h in failed_hubs)}",
            "Investigate vWAN Hub routing failures. This will affect all connected VNets and branches.",
            "vwan")

    # ── VNet Peering State ────────────────────────────────────
    peerings = _rows(results, "vnet_peerings")
    disconnected = [p for p in peerings if str(p.get("peerState", "")).lower() != "connected"]
    if disconnected:
        names = ", ".join(f"{p.get('vnetName', '?')}/{p.get('peeringName', '?')}" for p in disconnected[:5])
        add("Critical", "Connectivity", f"{len(disconnected)} VNet peering(s) not in Connected state",
            f"Disconnected peerings: {names}. Traffic between these VNets is blocked.",
            "Peerings must be created on both sides and both must show 'Connected'. "
            "Delete and recreate the peering if it is stuck in 'Disconnected' or 'Initiated' state.",
            "vnet_peering")

    # ── VNet Peering: Gateway Transit / Forwarded Traffic ─────
    for p in peerings:
        if p.get("allowGatewayTransit") and not p.get("useRemoteGateways"):
            pass  # hub side — expected
        if p.get("useRemoteGateways") and not has_vpn and not has_er:
            add("Medium", "Connectivity", f"Peering '{p.get('peeringName', '?')}' uses remote gateways but no gateway detected",
                f"VNet {p.get('vnetName', '?')} peering has useRemoteGateways=true, "
                "but no VPN or ExpressRoute gateway was found in the remote hub.",
                "Verify the hub VNet has a gateway deployed. Without one, useRemoteGateways causes connectivity failures.",
                "vnet_peering")

    # ── NSG Flow Logs ─────────────────────────────────────────
    flow_logs = _rows(results, "nsg_flow_logs")
    all_nsgs = _rows(results, "nsg_full_rules")
    nsg_names_with_flow = set()
    for fl in flow_logs:
        target = fl.get("targetNsg", "")
        if target:
            nsg_names_with_flow.add(target.split("/")[-1] if "/" in target else target)
    disabled_flow = [fl for fl in flow_logs if not fl.get("enabled")]

    if all_nsgs and not flow_logs:
        nsg_count = len(set(r.get("name", "") for r in all_nsgs))
        add("High", "Observability", f"No NSG flow logs configured ({nsg_count} NSGs present)",
            "NSG flow logs are not enabled on any NSG. Without flow logs, you have no visibility "
            "into allowed/denied traffic flows for troubleshooting or compliance.",
            "Enable NSG flow logs on all NSGs. Use Version 2 for throughput data. "
            "Enable Traffic Analytics for centralized visualization and anomaly detection.",
            "nsg_flow_logs")
    elif disabled_flow:
        add("Medium", "Observability", f"{len(disabled_flow)} NSG flow log(s) are disabled",
            f"Flow logs exist but are disabled: {', '.join(fl.get('name', '?') for fl in disabled_flow[:5])}",
            "Re-enable disabled flow logs. Disabled flow logs provide no traffic visibility.",
            "nsg_flow_logs")

    # ── Traffic Analytics ─────────────────────────────────────
    no_ta = [fl for fl in flow_logs if fl.get("enabled") and not fl.get("trafficAnalytics")]
    if no_ta:
        add("Medium", "Observability", f"{len(no_ta)} flow log(s) without Traffic Analytics",
            "Flow logs are enabled but Traffic Analytics is not. Traffic Analytics provides "
            "aggregated flow visualizations, threat detection, and bandwidth trending.",
            "Enable Traffic Analytics on all flow logs for centralized network visibility.",
            "traffic_analytics")

    # ── Flow Log Version ──────────────────────────────────────
    v1_logs = [fl for fl in flow_logs if fl.get("enabled") and str(fl.get("version", "1")) == "1"]
    if v1_logs:
        add("Low", "Observability", f"{len(v1_logs)} flow log(s) using Version 1 format",
            "Version 1 flow logs lack throughput (bytes) data needed for capacity planning and billing analysis.",
            "Upgrade to Version 2 flow logs for per-flow byte and packet counts.",
            "nsg_flow_logs")

    # ── Connection Monitor ────────────────────────────────────
    conn_mons = _rows(results, "connection_monitors")
    inactive_mons = [m for m in conn_mons if str(m.get("monitoringStatus", "")).lower() != "running"]
    if inactive_mons:
        add("Low", "Observability", f"{len(inactive_mons)} Connection Monitor(s) not running",
            f"Monitors: {', '.join(m.get('name', '?') for m in inactive_mons[:5])}",
            "Review and restart inactive Connection Monitors. They provide continuous reachability "
            "and latency monitoring between endpoints.",
            "connection_monitor")

    # ── DNS: Private DNS Resolver ─────────────────────────────
    resolvers = _rows(results, "dns_resolvers")
    if has_vpn or has_er:
        # Hybrid environment — resolver is important
        if not resolvers and pdns:
            add("High", "DNS", "No Private DNS Resolver in hybrid environment",
                "VPN/ExpressRoute gateways detected with Private DNS Zones but no Azure DNS Private Resolver. "
                "On-premises DNS servers cannot resolve Azure Private DNS Zone records without a resolver "
                "or DNS forwarder in Azure.",
                "Deploy an Azure DNS Private Resolver with inbound endpoints so on-premises DNS can forward "
                "privatelink.* queries to Azure for resolution. Without this, on-premises clients cannot "
                "reach private endpoints by FQDN.",
                "dns_private_resolver")
    if resolvers:
        failed_resolvers = [r for r in resolvers if str(r.get("state", "")).lower() != "succeeded"]
        if failed_resolvers:
            add("Critical", "DNS", f"{len(failed_resolvers)} DNS Resolver(s) in failed state",
                f"Resolvers: {', '.join(r.get('name', '?') for r in failed_resolvers)}. "
                "A failed resolver means DNS forwarding is broken for all dependent VNets.",
                "Investigate and reprovision the failed DNS Resolver. Check subnet delegation and NIC state.",
                "dns_private_resolver")

    # ── DNS Forwarding Rules ──────────────────────────────────
    fwd_rules = _rows(results, "dns_forwarding_rules")
    disabled_rules = [r for r in fwd_rules if str(r.get("state", "")).lower() == "disabled"]
    if disabled_rules:
        add("Medium", "DNS", f"{len(disabled_rules)} DNS forwarding rule(s) are disabled",
            f"Disabled forwarding rules: {', '.join(r.get('ruleName', '?') for r in disabled_rules[:5])}. "
            "DNS queries for these domains will not be forwarded to the target DNS servers.",
            "Enable or delete disabled forwarding rules. Disabled rules can cause unexpected "
            "DNS resolution behavior when clients expect forwarding to occur.",
            "dns_private_resolver")

    # ── Custom DNS on VNets ───────────────────────────────────
    custom_dns = _rows(results, "vnets_custom_dns")
    if custom_dns and resolvers:
        add("Info", "DNS", f"{len(custom_dns)} VNet(s) using custom DNS servers alongside DNS Resolver",
            f"VNets with custom DNS: {', '.join(r.get('name', '?') for r in custom_dns[:5])}. "
            "When both custom DNS and Azure DNS Private Resolver are present, ensure the DNS chain is correct: "
            "VNet custom DNS → Resolver inbound endpoint → Azure DNS.",
            "Verify the DNS resolution chain. Custom DNS servers should conditionally forward "
            "privatelink.* and other Azure zones to the DNS Private Resolver inbound endpoint.",
            "vnet_custom_dns")
    elif custom_dns and not resolvers and (has_vpn or has_er):
        add("Medium", "DNS", f"{len(custom_dns)} VNet(s) using custom DNS (no Azure DNS Resolver)",
            f"VNets with custom DNS pointing to on-prem or IaaS DNS: {', '.join(r.get('name', '?') for r in custom_dns[:5])}. "
            "Without an Azure DNS Private Resolver, privatelink.* zones must be forwarded to 168.63.129.16 "
            "from a DNS forwarder VM in Azure.",
            "Consider migrating from IaaS DNS forwarders to Azure DNS Private Resolver for better "
            "reliability, scalability, and lower management overhead.",
            "dns_private_resolver")

    # ── Private DNS Zone VNet Link Gaps ───────────────────────
    if pdns_links and vnet_count > 1:
        links_per_zone = {}
        for link in pdns_links:
            zone = link.get("zoneName", link.get("name", ""))
            links_per_zone[zone] = links_per_zone.get(zone, 0) + 1
        under_linked = {z: c for z, c in links_per_zone.items() if c < vnet_count}
        if under_linked and len(under_linked) > 0:
            examples = ", ".join(f"{z} ({c}/{vnet_count} VNets)" for z, c in list(under_linked.items())[:5])
            add("Medium", "DNS", f"{len(under_linked)} Private DNS Zone(s) not linked to all VNets",
                f"Zones with incomplete VNet links: {examples}. "
                "VNets without links cannot resolve private endpoint FQDNs in those zones.",
                "Link each Private DNS Zone to all VNets that need to resolve those records. "
                "In hub-spoke, link zones to both hub and spoke VNets.",
                "private_dns")

    # ── vWAN Hub Connections ──────────────────────────────────
    vwan_conns = _rows(results, "vwan_connections")
    no_internet_sec = [c for c in vwan_conns if not c.get("enableInternetSecurity")]
    if no_internet_sec and has_firewall:
        add("High", "Security", f"{len(no_internet_sec)} vWAN connection(s) without internet security enabled",
            f"Connections: {', '.join(c.get('connectionName', '?') for c in no_internet_sec[:5])}. "
            "Internet security must be enabled to route internet-bound traffic through the secured hub (firewall).",
            "Enable 'Internet Security' on all vWAN hub connections to ensure internet traffic "
            "is inspected by the hub's Azure Firewall or security NVA.",
            "vwan_routing")

    # ── vWAN Route Table Health ───────────────────────────────
    vwan_rts = _rows(results, "vwan_hub_route_tables")
    failed_rts = [rt for rt in vwan_rts if str(rt.get("provisioningState", "")).lower() != "succeeded"]
    if failed_rts:
        add("Critical", "Routing", f"{len(failed_rts)} vWAN hub route table(s) in failed state",
            f"Route tables: {', '.join(rt.get('tableName', '?') for rt in failed_rts)}. "
            "Failed route tables mean traffic cannot be routed through the hub.",
            "Investigate and reprovision failed route tables. Check for dependent resource conflicts.",
            "vwan_routing")

    # ── Accelerated Networking ────────────────────────────────
    no_an = _rows(results, "nic_accelerated_networking")
    if no_an:
        add("Low", "Performance", f"{len(no_an)} NIC(s) without Accelerated Networking",
            f"NICs attached to VMs without Accelerated Networking: {', '.join(r.get('name', '?') for r in no_an[:5])}",
            "Enable Accelerated Networking on supported VM sizes for lower latency, reduced jitter, "
            "and decreased CPU utilization. Most D/E/F-series VMs support it.",
            "accelerated_networking")

    # ── IP Forwarding on NICs (unexpected NVAs) ───────────────
    ip_fwd = _rows(results, "nic_ip_forwarding")
    if ip_fwd:
        add("Info", "Routing", f"{len(ip_fwd)} NIC(s) with IP forwarding enabled",
            f"NICs: {', '.join(r.get('name', '?') for r in ip_fwd[:5])}. "
            "IP forwarding is required for NVAs, firewalls, and load balancers but should not be "
            "enabled on regular workload NICs.",
            "Verify each NIC with IP forwarding is intentionally acting as an NVA/forwarder. "
            "Disable IP forwarding on NICs that are not routing traffic.",
            "udr")

    # ── PaaS Network Exposure ─────────────────────────────────
    open_storage = _rows(results, "storage_network_rules")
    if open_storage:
        add("High", "Security", f"{len(open_storage)} Storage Account(s) allow access from all networks",
            f"Storage accounts with defaultAction=Allow: {', '.join(r.get('name', '?') for r in open_storage[:5])}. "
            "These are accessible from the public internet without network restrictions.",
            "Set defaultAction to 'Deny' and add VNet rules, private endpoints, or IP rules for authorized access. "
            "Use private endpoints for zero-trust network access to storage.",
            "storage_network_rules")

    open_kv = _rows(results, "keyvault_network_open")
    if open_kv:
        add("High", "Security", f"{len(open_kv)} Key Vault(s) allow access from all networks",
            f"Key Vaults with no network restrictions: {', '.join(r.get('name', '?') for r in open_kv[:5])}",
            "Restrict Key Vault network access and use private endpoints. Key Vaults contain secrets, "
            "certificates, and keys that should not be exposed to the public internet.",
            "keyvault_network")

    open_sql = _rows(results, "sql_firewall_allow_azure")
    if open_sql:
        add("Medium", "Security", f"{len(open_sql)} SQL Server(s) with 'Allow Azure services' firewall rule",
            f"SQL Servers: {', '.join(r.get('serverName', '?') for r in open_sql[:5])}. "
            "The 0.0.0.0 rule allows any Azure service (including other tenants) to connect.",
            "Remove the 'Allow Azure services' rule and use private endpoints or VNet service endpoints instead. "
            "This rule opens access to ALL Azure IP addresses, not just your tenant.",
            "service_endpoints")

    # ── Network Watcher: Packet Capture / Troubleshooting Readiness ─
    if watchers and not conn_mons:
        add("Info", "Observability", "No Connection Monitors configured",
            "Network Watcher is deployed but no Connection Monitors exist. Connection Monitor provides "
            "continuous end-to-end connectivity and latency monitoring.",
            "Set up Connection Monitors for critical paths (e.g., app tier → database, hub → spoke, "
            "Azure → on-premises). Use for proactive alerting before users report issues.",
            "connection_monitor")

    if watchers:
        add("Info", "Observability", "Network diagnostic tools available",
            f"Network Watcher deployed in {len(watchers)} region(s). Available tools: "
            "IP Flow Verify (NSG rule hit), Next Hop (routing decision), Connection Troubleshoot "
            "(end-to-end path test), Packet Capture (deep inspection), Topology (visual map).",
            "Use IP Flow Verify to test whether an NSG allows or denies specific traffic. "
            "Use Next Hop to validate routing. Use Packet Capture for deep traffic inspection. "
            "These are your primary CLI/Portal diagnostic tools — no agents required.",
            "packet_capture")

    # Sort by severity
    severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}
    findings.sort(key=lambda f: severity_order.get(f["severity"], 5))

    return findings


def _format_findings_md(findings: list[dict]) -> str:
    """Format findings as markdown for the report."""
    if not findings:
        return "\n## Analysis\n\nNo significant findings detected.\n"

    lines = ["\n## Network Analysis & Recommendations\n"]

    # Summary counts
    counts = {}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    summary_parts = []
    for sev in ["Critical", "High", "Medium", "Low", "Info"]:
        if sev in counts:
            summary_parts.append(f"**{sev}:** {counts[sev]}")
    lines.append("| " + " | ".join(summary_parts) + " |\n")

    current_severity = None
    for f in findings:
        if f["severity"] != current_severity:
            current_severity = f["severity"]
            icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🔵", "Info": "ℹ️"}.get(current_severity, "")
            lines.append(f"\n### {icon} {current_severity}\n")

        lines.append(f"#### [{f['category']}] {f['title']}\n")
        lines.append(f"**Finding:** {f['detail']}\n")
        lines.append(f"**Recommendation:** {f['recommendation']}\n")
        if "reference" in f:
            lines.append(f"**Reference:** [{f['reference']}]({f['reference']})\n")

    return "\n".join(lines)


def _format_findings_console(findings: list[dict]):
    """Print findings to the console with rich formatting."""
    if not findings:
        console.print("\n  [green]No significant findings detected.[/green]\n")
        return

    console.print()
    console.rule("[bold cyan]Network Analysis & Recommendations[/bold cyan]")
    console.print()

    counts = {}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    summary = "  "
    for sev, color in [("Critical", "red"), ("High", "dark_orange"), ("Medium", "yellow"), ("Low", "blue"), ("Info", "dim")]:
        if sev in counts:
            summary += f"[{color}]{sev}: {counts[sev]}[/{color}]  "
    console.print(summary)
    console.print()

    current_severity = None
    for f in findings:
        if f["severity"] != current_severity:
            current_severity = f["severity"]
            color = {"Critical": "red", "High": "dark_orange", "Medium": "yellow", "Low": "blue", "Info": "dim"}.get(current_severity, "white")
            console.print(f"  [bold {color}]── {current_severity} ──[/bold {color}]")

        console.print(f"    [bold][{f['category']}][/bold] {f['title']}")
        console.print(f"    [dim]Finding:[/dim] {f['detail']}")
        console.print(f"    [green]Recommendation:[/green] {f['recommendation']}")
        if "reference" in f:
            console.print(f"    [blue]Ref:[/blue] {f['reference']}")
        console.print()

# Common ARG queries used across assessments
QUERIES = {
    "resource_count": "Resources | summarize count() by type | order by count_ desc | take 20",
    "untagged_resources": """
        Resources
        | where tags == '{}' or isnull(tags)
        | summarize count() by type
        | order by count_ desc
    """,
    "public_ips": """
        Resources
        | where type == 'microsoft.network/publicipaddresses'
        | extend attached = isnotnull(properties.ipConfiguration.id)
        | summarize total=count(), unattached=countif(not(attached))
    """,
    "orphaned_disks": """
        Resources
        | where type == 'microsoft.compute/disks'
        | where isnull(managedBy)
        | project name, resourceGroup, subscriptionId, sku=properties.sku.name, sizeGb=properties.diskSizeGB
    """,
    "nsg_any_rules": """
        Resources
        | where type == 'microsoft.network/networksecuritygroups'
        | mv-expand rule = properties.securityRules
        | where rule.properties.sourceAddressPrefix == '*' and rule.properties.access == 'Allow' and rule.properties.direction == 'Inbound'
        | project name, resourceGroup, ruleName=rule.name, destinationPort=rule.properties.destinationPortRange
    """,
    "vms_no_ahb": """
        Resources
        | where type == 'microsoft.compute/virtualmachines'
        | where properties.storageProfile.imageReference.publisher == 'MicrosoftWindowsServer'
        | where properties.licenseType != 'Windows_Server' or isnull(properties.licenseType)
        | project name, resourceGroup, subscriptionId, vmSize=properties.hardwareProfile.vmSize
    """,
    "advisor_cost": """
        advisorresources
        | where type == 'microsoft.advisor/recommendations'
        | where properties.category == 'Cost'
        | summarize count() by impact=tostring(properties.impact)
    """,
    "management_groups": """
        ResourceContainers
        | where type == 'microsoft.management/managementgroups'
        | project name, displayName=properties.displayName, parent=properties.details.parent.displayName
    """,
    "vnets": """
        Resources
        | where type == 'microsoft.network/virtualnetworks'
        | project name, resourceGroup, location, addressSpace=properties.addressSpace.addressPrefixes, subnets=array_length(properties.subnets)
    """,
    "private_endpoints": """
        Resources
        | where type == 'microsoft.network/privateendpoints'
        | extend targetService = tostring(properties.privateLinkServiceConnections[0].properties.groupIds[0])
        | summarize count() by targetService
    """,
    # ── Landing Zone queries ──────────────────────────────────────
    "subscription_inventory": """
        ResourceContainers
        | where type == 'microsoft.resources/subscriptions'
        | project name, subscriptionId, state=properties.state,
                  spendingLimit=properties.subscriptionPolicies.spendingLimit,
                  quotaId=properties.subscriptionPolicies.quotaId
    """,
    "resource_providers": """
        Resources
        | extend provider = tostring(split(type, '/')[0])
        | summarize resourceCount=count() by provider
        | order by resourceCount desc
    """,
    "policy_assignments": """
        policyresources
        | where type == 'microsoft.authorization/policyassignments'
        | extend scope = tostring(properties.scope)
        | extend policyType = iff(isnotnull(properties.policyDefinitionId), 
            iff(properties.policyDefinitionId contains 'policySetDefinitions', 'Initiative', 'Policy'), 'Unknown')
        | extend enforcement = tostring(properties.enforcementMode)
        | project name, displayName=properties.displayName, policyType, enforcement, scope
    """,
    "role_assignments": """
        authorizationresources
        | where type == 'microsoft.authorization/roleassignments'
        | extend principalType = tostring(properties.principalType)
        | extend roleId = tostring(properties.roleDefinitionId)
        | extend scope = tostring(properties.scope)
        | summarize count() by principalType
    """,
    "role_assignment_details": """
        authorizationresources
        | where type == 'microsoft.authorization/roleassignments'
        | extend principalType = tostring(properties.principalType)
        | extend scope = tostring(properties.scope)
        | extend scopeLevel = iff(scope matches regex @'^/providers/Microsoft.Management/managementGroups/', 'ManagementGroup',
            iff(scope matches regex @'^/subscriptions/[^/]+$', 'Subscription',
            iff(scope matches regex @'^/subscriptions/[^/]+/resourceGroups/[^/]+$', 'ResourceGroup', 'Resource')))
        | summarize count() by principalType, scopeLevel
    """,
    "diagnostic_settings": """
        Resources
        | where type in~ ('microsoft.compute/virtualmachines', 'microsoft.network/virtualnetworks',
            'microsoft.keyvault/vaults', 'microsoft.sql/servers', 'microsoft.storage/storageaccounts',
            'microsoft.web/sites', 'microsoft.containerservice/managedclusters')
        | summarize totalResources=count() by type
    """,
    "log_analytics_workspaces": """
        Resources
        | where type == 'microsoft.operationalinsights/workspaces'
        | project name, resourceGroup, location, 
                  sku=properties.sku.name, 
                  retentionDays=properties.retentionInDays
    """,
    "security_center": """
        securityresources
        | where type == 'microsoft.security/securescores'
        | project name, currentScore=properties.score.current, maxScore=properties.score.max,
                  percentage=properties.score.percentage
    """,
    "security_assessments": """
        securityresources
        | where type == 'microsoft.security/assessments'
        | extend status = tostring(properties.status.code)
        | summarize count() by status
    """,
    "vnet_peerings": """
        Resources
        | where type == 'microsoft.network/virtualnetworks'
        | mv-expand peering = properties.virtualNetworkPeerings
        | project vnetName=name, peeringName=peering.name,
                  peerState=peering.properties.peeringState,
                  remoteVnet=peering.properties.remoteVirtualNetwork.id,
                  allowForwarding=peering.properties.allowForwardedTraffic,
                  allowGatewayTransit=peering.properties.allowGatewayTransit
    """,
    "route_tables": """
        Resources
        | where type == 'microsoft.network/routetables'
        | extend routeCount = array_length(properties.routes)
        | project name, resourceGroup, location, routeCount,
                  disableBgp=properties.disableBgpRoutePropagation
    """,
    "network_watchers": """
        Resources
        | where type == 'microsoft.network/networkwatchers'
        | project name, resourceGroup, location, 
                  provisioningState=properties.provisioningState
    """,
    "key_vaults": """
        Resources
        | where type == 'microsoft.keyvault/vaults'
        | project name, resourceGroup, location,
                  enablePurgeProtection=properties.enablePurgeProtection,
                  enableSoftDelete=properties.enableSoftDelete,
                  enableRbacAuthorization=properties.enableRbacAuthorization,
                  networkAcls=properties.networkAcls.defaultAction
    """,
    "resource_locks": """
        Resources
        | where type == 'microsoft.authorization/locks'
        | extend lockLevel = tostring(properties.level)
        | summarize count() by lockLevel
    """,
    "resources_by_location": """
        Resources
        | summarize count() by location
        | order by count_ desc
    """,
    "tag_coverage": """
        Resources
        | extend tagCount = bag_keys(tags)
        | extend hasOwner = tags contains 'owner' or tags contains 'Owner'
        | extend hasEnv = tags contains 'environment' or tags contains 'Environment' or tags contains 'env'
        | extend hasCostCenter = tags contains 'costcenter' or tags contains 'CostCenter' or tags contains 'cost-center'
        | summarize totalResources=count(), 
                    withTags=countif(array_length(tagCount) > 0),
                    withOwner=countif(hasOwner),
                    withEnv=countif(hasEnv),
                    withCostCenter=countif(hasCostCenter)
    """,
    # ── Deep Network queries ──────────────────────────────────────
    "vnet_details": """
        Resources
        | where type == 'microsoft.network/virtualnetworks'
        | mv-expand subnet = properties.subnets
        | project vnetName=name, resourceGroup, location,
                  addressSpace=properties.addressSpace.addressPrefixes,
                  subnetName=subnet.name,
                  subnetPrefix=subnet.properties.addressPrefix,
                  nsg=subnet.properties.networkSecurityGroup.id,
                  routeTable=subnet.properties.routeTable.id,
                  delegations=subnet.properties.delegations,
                  serviceEndpoints=subnet.properties.serviceEndpoints,
                  privateEndpointNetworkPolicies=subnet.properties.privateEndpointNetworkPolicies
    """,
    "nsg_full_rules": """
        Resources
        | where type == 'microsoft.network/networksecuritygroups'
        | mv-expand rule = properties.securityRules
        | project nsgName=name, resourceGroup,
                  ruleName=rule.name, priority=rule.properties.priority,
                  direction=rule.properties.direction, access=rule.properties.access,
                  protocol=rule.properties.protocol,
                  srcAddr=rule.properties.sourceAddressPrefix,
                  srcPorts=rule.properties.sourcePortRange,
                  dstAddr=rule.properties.destinationAddressPrefix,
                  dstPorts=rule.properties.destinationPortRange
        | order by nsgName asc, toint(priority) asc
    """,
    "nsgs_unassociated": """
        Resources
        | where type == 'microsoft.network/networksecuritygroups'
        | where isnull(properties.subnets) or array_length(properties.subnets) == 0
        | where isnull(properties.networkInterfaces) or array_length(properties.networkInterfaces) == 0
        | project name, resourceGroup, location
    """,
    "subnets_without_nsg": """
        Resources
        | where type == 'microsoft.network/virtualnetworks'
        | mv-expand subnet = properties.subnets
        | where isempty(subnet.properties.networkSecurityGroup)
        | where subnet.name !in~ ('GatewaySubnet', 'AzureFirewallSubnet', 'AzureFirewallManagementSubnet', 'AzureBastionSubnet', 'RouteServerSubnet')
        | project vnetName=name, subnetName=subnet.name, subnetPrefix=subnet.properties.addressPrefix,
                  resourceGroup, location
    """,
    "subnets_without_route_table": """
        Resources
        | where type == 'microsoft.network/virtualnetworks'
        | mv-expand subnet = properties.subnets
        | where isempty(subnet.properties.routeTable)
        | where subnet.name !in~ ('GatewaySubnet', 'AzureBastionSubnet')
        | project vnetName=name, subnetName=subnet.name, subnetPrefix=subnet.properties.addressPrefix,
                  resourceGroup, location
    """,
    "application_gateways": """
        Resources
        | where type == 'microsoft.network/applicationgateways'
        | project name, resourceGroup, location,
                  sku=properties.sku.name, tier=properties.sku.tier,
                  capacity=properties.sku.capacity,
                  wafEnabled=properties.webApplicationFirewallConfiguration.enabled,
                  sslPolicy=properties.sslPolicy.policyType,
                  frontendPorts=array_length(properties.frontendPorts),
                  httpListeners=array_length(properties.httpListeners),
                  backendPools=array_length(properties.backendAddressPools),
                  probes=array_length(properties.probes)
    """,
    "load_balancers": """
        Resources
        | where type == 'microsoft.network/loadbalancers'
        | project name, resourceGroup, location,
                  sku=properties.sku.name,
                  frontendIPs=array_length(properties.frontendIPConfigurations),
                  backendPools=array_length(properties.backendAddressPools),
                  rules=array_length(properties.loadBalancingRules),
                  probes=array_length(properties.probes),
                  inboundNatRules=array_length(properties.inboundNatRules)
    """,
    "firewalls": """
        Resources
        | where type == 'microsoft.network/azurefirewalls'
        | project name, resourceGroup, location,
                  sku=properties.sku.name, tier=properties.sku.tier,
                  threatIntelMode=properties.threatIntelMode,
                  firewallPolicy=properties.firewallPolicy.id,
                  ipConfigurations=array_length(properties.ipConfigurations)
    """,
    "firewall_policies": """
        Resources
        | where type == 'microsoft.network/firewallpolicies'
        | project name, resourceGroup, location,
                  tier=properties.sku.tier,
                  threatIntelMode=properties.threatIntelMode,
                  dnsProxy=properties.dnsSettings.enableProxy,
                  childPolicies=array_length(properties.childPolicies),
                  ruleCollectionGroups=array_length(properties.ruleCollectionGroups)
    """,
    "vpn_gateways": """
        Resources
        | where type == 'microsoft.network/virtualnetworkgateways'
        | where properties.gatewayType == 'Vpn'
        | project name, resourceGroup, location,
                  sku=properties.sku.name,
                  vpnType=properties.vpnType,
                  activeActive=properties.activeActive,
                  enableBgp=properties.enableBgp,
                  bgpAsn=properties.bgpSettings.asn,
                  generation=properties.vpnGatewayGeneration
    """,
    "expressroute_gateways": """
        Resources
        | where type == 'microsoft.network/virtualnetworkgateways'
        | where properties.gatewayType == 'ExpressRoute'
        | project name, resourceGroup, location,
                  sku=properties.sku.name
    """,
    "expressroute_circuits": """
        Resources
        | where type == 'microsoft.network/expressroutecircuits'
        | project name, resourceGroup, location,
                  serviceProvider=properties.serviceProviderProperties.serviceProviderName,
                  peeringLocation=properties.serviceProviderProperties.peeringLocation,
                  bandwidthMbps=properties.serviceProviderProperties.bandwidthInMbps,
                  sku=sku.name, tier=sku.tier,
                  circuitProvisioningState=properties.circuitProvisioningState,
                  serviceProviderState=properties.serviceProviderProvisioningState,
                  globalReachEnabled=properties.globalReachEnabled
    """,
    "expressroute_peerings": """
        Resources
        | where type == 'microsoft.network/expressroutecircuits'
        | mv-expand peering = properties.peerings
        | project circuitName=name,
                  peeringType=peering.properties.peeringType,
                  state=peering.properties.state,
                  primaryPrefix=peering.properties.primaryPeerAddressPrefix,
                  secondaryPrefix=peering.properties.secondaryPeerAddressPrefix,
                  vlanId=peering.properties.vlanId,
                  peerAsn=peering.properties.peerASN
    """,
    "virtual_wan": """
        Resources
        | where type == 'microsoft.network/virtualwans'
        | project name, resourceGroup, location,
                  type_=properties.type,
                  allowBranchToBranch=properties.allowBranchToBranchTraffic,
                  allowVnetToVnet=properties.allowVnetToVnetTraffic,
                  virtualHubs=array_length(properties.virtualHubs)
    """,
    "virtual_wan_hubs": """
        Resources
        | where type == 'microsoft.network/virtualhubs'
        | project name, resourceGroup, location,
                  addressPrefix=properties.addressPrefix,
                  sku=properties.sku,
                  routingState=properties.routingState,
                  virtualWan=properties.virtualWan.id
    """,
    "dns_zones": """
        Resources
        | where type == 'microsoft.network/dnszones'
        | project name, resourceGroup,
                  recordCount=properties.numberOfRecordSets,
                  nameServers=properties.nameServers
    """,
    "private_dns_zones": """
        Resources
        | where type == 'microsoft.network/privatednszones'
        | project name, resourceGroup,
                  recordCount=properties.numberOfRecordSets,
                  vnetLinks=properties.numberOfVirtualNetworkLinks,
                  autoRegistration=properties.numberOfVirtualNetworkLinksWithRegistration
    """,
    "private_dns_vnet_links": """
        Resources
        | where type == 'microsoft.network/privatednszones/virtualnetworklinks'
        | project zoneName=tostring(split(id, '/')[8]), linkName=name,
                  resourceGroup,
                  registrationEnabled=properties.registrationEnabled,
                  vnetId=properties.virtualNetwork.id,
                  linkState=properties.virtualNetworkLinkState
    """,
    "private_endpoint_details": """
        Resources
        | where type == 'microsoft.network/privateendpoints'
        | extend targetResource = tostring(properties.privateLinkServiceConnections[0].properties.privateLinkServiceId)
        | extend targetGroup = tostring(properties.privateLinkServiceConnections[0].properties.groupIds[0])
        | extend connectionState = tostring(properties.privateLinkServiceConnections[0].properties.privateLinkServiceConnectionState.status)
        | extend subnetId = tostring(properties.subnet.id)
        | project name, resourceGroup, location, targetResource, targetGroup, connectionState, subnetId
    """,
    "public_ip_details": """
        Resources
        | where type == 'microsoft.network/publicipaddresses'
        | project name, resourceGroup, location,
                  sku=sku.name,
                  allocationMethod=properties.publicIPAllocationMethod,
                  ipAddress=properties.ipAddress,
                  attached=isnotnull(properties.ipConfiguration.id),
                  attachedTo=properties.ipConfiguration.id,
                  ddosProtection=properties.ddosSettings.protectionMode,
                  zones=zones
    """,
    "ddos_plans": """
        Resources
        | where type == 'microsoft.network/ddosprotectionplans'
        | project name, resourceGroup, location,
                  protectedVnets=array_length(properties.virtualNetworks)
    """,
    "bastion_hosts": """
        Resources
        | where type == 'microsoft.network/bastionhosts'
        | project name, resourceGroup, location,
                  sku=sku.name,
                  scaleUnits=properties.scaleUnits,
                  enableTunneling=properties.enableTunneling,
                  enableShareableLink=properties.enableShareableLink
    """,
    "front_doors": """
        Resources
        | where type in~ ('microsoft.network/frontdoors', 'microsoft.cdn/profiles')
        | project name, resourceGroup, location, type,
                  sku=sku.name
    """,
    "traffic_managers": """
        Resources
        | where type == 'microsoft.network/trafficmanagerprofiles'
        | project name, resourceGroup,
                  routingMethod=properties.trafficRoutingMethod,
                  monitorStatus=properties.monitorConfig.profileMonitorStatus,
                  endpoints=array_length(properties.endpoints)
    """,
    "nat_gateways": """
        Resources
        | where type == 'microsoft.network/natgateways'
        | project name, resourceGroup, location,
                  sku=sku.name,
                  idleTimeoutMinutes=properties.idleTimeoutInMinutes,
                  publicIps=array_length(properties.publicIpAddresses),
                  publicPrefixes=array_length(properties.publicIpPrefixes),
                  subnets=array_length(properties.subnets)
    """,
    "service_endpoints": """
        Resources
        | where type == 'microsoft.network/virtualnetworks'
        | mv-expand subnet = properties.subnets
        | mv-expand endpoint = subnet.properties.serviceEndpoints
        | where isnotnull(endpoint)
        | project vnetName=name, subnetName=subnet.name,
                  service=endpoint.service, locations=endpoint.locations
    """,
    "nics_with_public_ip": """
        Resources
        | where type == 'microsoft.network/networkinterfaces'
        | mv-expand ipConfig = properties.ipConfigurations
        | where isnotnull(ipConfig.properties.publicIPAddress)
        | project nicName=name, resourceGroup,
                  vmId=properties.virtualMachine.id,
                  publicIp=ipConfig.properties.publicIPAddress.id,
                  subnetId=ipConfig.properties.subnet.id
    """,
    "ip_address_overlap": """
        Resources
        | where type == 'microsoft.network/virtualnetworks'
        | mv-expand prefix = properties.addressSpace.addressPrefixes
        | project vnetName=name, resourceGroup, location, addressPrefix=tostring(prefix)
        | order by addressPrefix asc
    """,
    "network_resource_inventory": """
        Resources
        | where type startswith 'microsoft.network/'
        | summarize count() by type
        | order by count_ desc
    """,
    # ── DNS Resolution & Resolver ─────────────────────────────
    "dns_resolvers": """
        Resources
        | where type == 'microsoft.network/dnsresolvers'
        | project name, resourceGroup, location,
                  state=properties.provisioningState,
                  vnetId=properties.virtualNetwork.id
    """,
    "dns_forwarding_rulesets": """
        Resources
        | where type == 'microsoft.network/dnsforwardingrulesets'
        | project name, resourceGroup, location,
                  resolverOutbound=properties.dnsResolverOutboundEndpoints
    """,
    "dns_forwarding_rules": """
        Resources
        | where type == 'microsoft.network/dnsforwardingrulesets/forwardingrules'
        | project rulesetName=tostring(split(id, '/')[8]), ruleName=name,
                  domain=properties.domainName,
                  state=properties.forwardingRuleState,
                  targetDns=properties.targetDnsServers
    """,
    # ── Custom DNS Configuration ──────────────────────────────
    "vnets_custom_dns": """
        Resources
        | where type == 'microsoft.network/virtualnetworks'
        | where isnotnull(properties.dhcpOptions) and array_length(properties.dhcpOptions.dnsServers) > 0
        | project name, resourceGroup, location,
                  dnsServers=properties.dhcpOptions.dnsServers
    """,
    # ── Flow Logs & Traffic Analytics ─────────────────────────
    "nsg_flow_logs": """
        Resources
        | where type == 'microsoft.network/networkwatchers/flowlogs'
        | project name, resourceGroup, location,
                  targetNsg=properties.targetResourceId,
                  enabled=properties.enabled,
                  retentionDays=properties.retentionPolicy.days,
                  retentionEnabled=properties.retentionPolicy.enabled,
                  trafficAnalytics=properties.flowAnalyticsConfiguration.networkWatcherFlowAnalyticsConfiguration.enabled,
                  storageAccount=properties.storageId,
                  version=properties.format.version
    """,
    # ── Connection Monitor ────────────────────────────────────
    "connection_monitors": """
        Resources
        | where type == 'microsoft.network/networkwatchers/connectionmonitors'
        | project name, resourceGroup, location,
                  monitoringStatus=properties.monitoringStatus,
                  autoStart=properties.autoStart,
                  endpoints=array_length(properties.endpoints),
                  testGroups=array_length(properties.testGroups)
    """,
    # ── vWAN Effective Routes ─────────────────────────────────
    "vwan_hub_route_tables": """
        Resources
        | where type == 'microsoft.network/virtualhubs/hubroutetables'
        | project hubName=tostring(split(id, '/')[8]), tableName=name,
                  resourceGroup, location,
                  routes=array_length(properties.routes),
                  labels=properties.labels,
                  provisioningState=properties.provisioningState
    """,
    "vwan_connections": """
        Resources
        | where type == 'microsoft.network/virtualhubs/hubvirtualnetworkconnections'
        | project hubName=tostring(split(id, '/')[8]), connectionName=name,
                  resourceGroup,
                  remoteVnet=properties.remoteVirtualNetwork.id,
                  enableInternetSecurity=properties.enableInternetSecurity,
                  routingConfig=properties.routingConfiguration
    """,
    # ── Subnet Delegation ─────────────────────────────────────
    "subnet_delegations": """
        Resources
        | where type == 'microsoft.network/virtualnetworks'
        | mv-expand subnet = properties.subnets
        | mv-expand delegation = subnet.properties.delegations
        | where isnotnull(delegation)
        | project vnetName=name, subnetName=subnet.name,
                  subnetPrefix=subnet.properties.addressPrefix,
                  serviceName=delegation.properties.serviceName
    """,
    # ── NIC Effective Config ──────────────────────────────────
    "nic_ip_forwarding": """
        Resources
        | where type == 'microsoft.network/networkinterfaces'
        | where properties.enableIPForwarding == true
        | project name, resourceGroup,
                  vmId=properties.virtualMachine.id,
                  ipForwarding=properties.enableIPForwarding
    """,
    # ── Accelerated Networking ────────────────────────────────
    "nic_accelerated_networking": """
        Resources
        | where type == 'microsoft.network/networkinterfaces'
        | where properties.enableAcceleratedNetworking != true
        | extend vmId = tostring(properties.virtualMachine.id)
        | where isnotempty(vmId)
        | project name, resourceGroup,
                  acceleratedNetworking=properties.enableAcceleratedNetworking
    """,
    # ── PaaS Firewall Rules (service-level network ACLs) ──────
    "storage_network_rules": """
        Resources
        | where type == 'microsoft.storage/storageaccounts'
        | where properties.networkAcls.defaultAction == 'Allow'
        | project name, resourceGroup, location,
                  defaultAction=properties.networkAcls.defaultAction,
                  bypass=properties.networkAcls.bypass
    """,
    "sql_firewall_allow_azure": """
        Resources
        | where type == 'microsoft.sql/servers'
        | mv-expand rule = properties.firewallRules
        | where rule.properties.startIpAddress == '0.0.0.0' and rule.properties.endIpAddress == '0.0.0.0'
        | project serverName=name, resourceGroup, ruleName=rule.name
    """,
    "keyvault_network_open": """
        Resources
        | where type == 'microsoft.keyvault/vaults'
        | where properties.networkAcls.defaultAction == 'Allow' or isnull(properties.networkAcls.defaultAction)
        | project name, resourceGroup, location,
                  defaultAction=properties.networkAcls.defaultAction,
                  publicAccess=properties.publicNetworkAccess
    """,
}


def run_assessment(scope: str, assessment_type: str, output_dir: str, tee: bool = True):
    """Run an assessment and generate a report."""
    skill_map = {
        "general": None,
        "finops": "finops-assessment",
        "landing-zone": "landing-zone-assessment",
        "network": "network-review",
        "waf": "well-architected-review",
    }

    console.print(f"\n[bold green]Azure CSA Assessment[/bold green]")
    console.print(f"  Scope: {scope}")
    console.print(f"  Type:  {assessment_type}")
    console.print(f"  Output: {output_dir}/\n")

    skill_name = skill_map.get(assessment_type)
    if skill_name:
        console.print(f"[dim]⚙  Loading skill: {skill_name}...[/dim]")
    else:
        console.print(f"[dim]⚙  Running general assessment (no specific skill)...[/dim]")

    console.print(f"[dim]🔍 Querying Azure Resource Graph...[/dim]\n")

    subscriptions = [scope] if "-" in scope and len(scope) == 36 else None

    queries_to_run = {
        "general": ["resource_count", "untagged_resources", "public_ips", "advisor_cost", "resources_by_location"],
        "finops": ["resource_count", "untagged_resources", "orphaned_disks", "vms_no_ahb", "advisor_cost", "tag_coverage"],
        "landing-zone": [
            "subscription_inventory", "management_groups", "resource_count", "resource_providers",
            "resources_by_location", "policy_assignments", "role_assignments", "role_assignment_details",
            "vnets", "vnet_peerings", "route_tables", "nsg_any_rules", "private_endpoints", "network_watchers",
            "log_analytics_workspaces", "security_center", "security_assessments",
            "key_vaults", "resource_locks", "tag_coverage", "untagged_resources",
        ],
        "network": [
            "network_resource_inventory",
            "vnet_details", "vnet_peerings", "ip_address_overlap",
            "subnets_without_nsg", "subnets_without_route_table",
            "nsg_full_rules", "nsg_any_rules", "nsgs_unassociated",
            "route_tables", "nat_gateways",
            "public_ip_details", "nics_with_public_ip", "ddos_plans",
            "firewalls", "firewall_policies",
            "application_gateways", "load_balancers", "front_doors",
            "vpn_gateways", "expressroute_gateways", "expressroute_circuits", "expressroute_peerings",
            "virtual_wan", "virtual_wan_hubs", "vwan_hub_route_tables", "vwan_connections",
            "private_endpoint_details", "private_endpoints", "service_endpoints",
            "dns_zones", "private_dns_zones", "private_dns_vnet_links",
            "dns_resolvers", "dns_forwarding_rulesets", "dns_forwarding_rules", "vnets_custom_dns",
            "nsg_flow_logs", "connection_monitors",
            "nic_ip_forwarding", "nic_accelerated_networking", "subnet_delegations",
            "storage_network_rules", "sql_firewall_allow_azure", "keyvault_network_open",
            "bastion_hosts", "traffic_managers", "network_watchers",
        ],
        "waf": ["resource_count", "public_ips", "nsg_any_rules", "orphaned_disks", "advisor_cost",
                "security_center", "security_assessments", "key_vaults", "resource_locks"],
    }

    selected = queries_to_run.get(assessment_type, queries_to_run["general"])
    results = {}

    for query_name in selected:
        console.print(f"  🔍 {query_name}...", end=" ")
        try:
            result = execute_query(QUERIES[query_name], subscriptions)
            results[query_name] = result
            console.print(f"[green]{result['count']} rows[/green]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            results[query_name] = {"error": str(e)}

    # Write results to output
    console.print(f"\n[dim]📝 Generating report...[/dim]")

    # Run analysis for network assessments
    findings = []
    if assessment_type == "network":
        console.print(f"[dim]📊 Analyzing results against best practices...[/dim]")
        findings = _analyze_network(results)

    out_path = Path(output_dir) / f"{assessment_type}-assessment.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    report_lines = []
    report_lines.append(f"# Azure CSA Assessment — {assessment_type.title()}\n")
    report_lines.append(f"**Scope:** `{scope}`\n")
    report_lines.append(f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")

    # Add findings section before raw data for network assessments
    if findings:
        report_lines.append(_format_findings_md(findings))
        report_lines.append("\n---\n")
        report_lines.append("## Raw Query Data\n")

    for name, data in results.items():
        section_title = name.replace('_', ' ').title()
        report_lines.append(f"## {section_title}\n")
        if "error" in data:
            report_lines.append(f"> Error: {data['error']}\n")
        else:
            report_lines.append(f"Rows returned: {data['count']}\n")
            report_lines.append(f"```json\n{data['data']}\n```\n")

    report_text = "\n".join(report_lines)

    with open(out_path, "w") as f:
        f.write(report_text)

    if tee:
        # Print analysis findings first for network assessments
        if findings:
            _format_findings_console(findings)

        console.print()
        console.rule(f"[bold cyan]{assessment_type.title()} Assessment Results[/bold cyan]")
        console.print()
        for name, data in results.items():
            section_title = name.replace('_', ' ').title()
            console.print(f"  [bold yellow]── {section_title} ──[/bold yellow]")
            if "error" in data:
                console.print(f"    [red]Error: {data['error']}[/red]")
            else:
                console.print(f"    Rows: [green]{data['count']}[/green]")
                if isinstance(data['data'], list):
                    for row in data['data'][:10]:
                        console.print(f"    {row}")
                    if data['count'] > 10:
                        console.print(f"    [dim]... and {data['count'] - 10} more rows[/dim]")
                else:
                    console.print(f"    {data['data']}")
            console.print()

    console.print(f"[bold green]✓ Report saved to {out_path}[/bold green]")
