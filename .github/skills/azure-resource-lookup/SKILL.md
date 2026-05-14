# Skill: Azure Resource Lookup

List, find, and discover Azure resources of any type across subscriptions and resource groups using Azure Resource Graph (ARG).

## Trigger Phrases
- "list my resources"
- "what resources do I have"
- "show my VMs"
- "list web apps"
- "find storage accounts"
- "resource inventory"
- "show resources by tag"
- "orphaned resources"
- "count resources by type"
- "cross-subscription lookup"

## Capabilities

### Resource Discovery
- Query any resource type across all subscriptions in a single ARG query
- Filter by resource type, location, resource group, tags, or properties
- Cross-subscription queries without switching context
- Count and aggregate resources by type, location, or tag

### Common Query Patterns

#### List All Resources by Type
```kql
resources
| where type =~ 'microsoft.compute/virtualmachines'
| project name, resourceGroup, location, properties.hardwareProfile.vmSize
```

#### Find Resources Missing Tags
```kql
resources
| where tags !has 'CostCenter' or tags !has 'Environment'
| summarize count() by type
| order by count_ desc
```

#### Orphaned Resource Discovery
```kql
// Unattached disks
resources
| where type =~ 'microsoft.compute/disks'
| where managedBy == ''
| project name, resourceGroup, sku.name, properties.diskSizeGB
```

#### Cross-Subscription Inventory
```kql
resources
| summarize count() by subscriptionId, type
| order by count_ desc
```

### Resource Type Coverage
- Virtual Machines, VMSS, Availability Sets
- App Service, Function Apps, Container Apps
- Storage Accounts, Cosmos DB, SQL Databases
- VNets, NSGs, Load Balancers, Application Gateways
- Key Vaults, Managed Identities
- AKS Clusters, Container Registries
- Any resource type queryable via ARG

## Output Format
- Table format with resource name, type, resource group, location
- Include key properties relevant to the resource type
- Summarize totals at the end
- Flag any anomalies (orphaned resources, misconfigured state)

## Prerequisites
- Reader access on target subscriptions
- Azure Resource Graph access (default for any Reader role)
