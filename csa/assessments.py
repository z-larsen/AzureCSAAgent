"""Assessment runner — orchestrates advisory assessments by type."""

from pathlib import Path

from rich.console import Console

from csa.arg_client import execute_query

console = Console()

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
        "network": ["vnets", "vnet_peerings", "public_ips", "nsg_any_rules", "private_endpoints",
                     "route_tables", "network_watchers"],
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
    out_path = Path(output_dir) / f"{assessment_type}-assessment.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    report_lines = []
    report_lines.append(f"# Azure CSA Assessment — {assessment_type.title()}\n")
    report_lines.append(f"**Scope:** `{scope}`\n")

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
