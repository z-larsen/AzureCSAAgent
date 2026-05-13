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
        "general": ["resource_count", "untagged_resources", "public_ips", "advisor_cost"],
        "finops": ["resource_count", "untagged_resources", "orphaned_disks", "vms_no_ahb", "advisor_cost"],
        "landing-zone": ["management_groups", "resource_count", "untagged_resources", "vnets"],
        "network": ["vnets", "public_ips", "nsg_any_rules", "private_endpoints"],
        "waf": ["resource_count", "public_ips", "nsg_any_rules", "orphaned_disks", "advisor_cost"],
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
