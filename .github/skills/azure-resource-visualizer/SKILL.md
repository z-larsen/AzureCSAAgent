# Skill: Azure Resource Visualizer

Analyze Azure resource groups and generate Mermaid architecture diagrams showing relationships between resources.

## Trigger Phrases
- "create architecture diagram"
- "visualize my resources"
- "show resource relationships"
- "generate Mermaid diagram"
- "diagram my resource group"
- "architecture visualization"
- "resource topology"
- "map my infrastructure"

## Workflow

### 1. Resource Group Selection
- If not specified, list available resource groups and ask the user to select
- Validate the resource group exists before proceeding

### 2. Resource Discovery & Analysis
Query all resources in the resource group and capture:
- Resource name and type
- SKU/tier information
- Location/region
- Network settings (VNets, subnets, private endpoints)
- Identity (managed identities, RBAC)
- Dependencies and connections

### 3. Relationship Mapping
Identify connections between resources:
- **Network**: VNet peering, subnet assignments, NSGs, private endpoints
- **Data flow**: Apps → Databases, Functions → Storage
- **Identity**: Managed identities connecting to resources
- **Configuration**: App Settings → Key Vault references, connection strings
- **Dependencies**: Parent-child relationships

### 4. Diagram Construction
Create a Mermaid diagram using `graph TB` or `graph LR`:
- Group by layer: Network, Compute, Data, Security, Monitoring
- Include SKUs and tiers in node labels
- Label all connections with data flow descriptions
- Use subgraphs for logical grouping
- `-->` for data flow, `-.->` for optional connections, `==>` for critical paths

### 5. Output
Generate a markdown file with:
- Header: resource group name, subscription, region
- Summary: architecture overview (2-3 paragraphs)
- Resource inventory table
- Mermaid architecture diagram
- Relationship details and data flow explanations
- Observations and recommendations

## Important
- Never include secret values (keys, connection strings) in diagrams
- Use placeholder names to represent secrets
- Only use information discoverable via ARG and resource properties
