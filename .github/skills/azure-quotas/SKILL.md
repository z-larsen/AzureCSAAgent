# Skill: Azure Quotas & Service Limits

Check and manage Azure quotas and usage across resource providers for deployment planning, capacity validation, and region selection.

## Trigger Phrases
- "check quotas"
- "service limits"
- "current usage"
- "request quota increase"
- "quota exceeded"
- "validate capacity"
- "regional availability"
- "vCPU limit"
- "how many vCPUs available"
- "provisioning limits"

## Key Concepts

**Azure quotas** (service limits) are the maximum number of resources deployable in a subscription. They:
- Prevent accidental over-provisioning
- Represent available capacity per region
- Can be increased (adjustable) or are fixed (non-adjustable)
- Requesting increases is **free** — you only pay for resources used

## Quota Types
| Type | Adjustability | Examples |
|------|--------------|---------|
| Adjustable | Can increase via Portal/CLI | VM vCPUs, Public IPs, Storage accounts |
| Non-adjustable | Fixed limits | Subscription-wide hard limits |

## Core Workflow

### 1. Install Extension
```bash
az extension add --name quota
```

### 2. List Quotas for a Provider
```bash
az quota list --scope /subscriptions/<id>/providers/<Provider>/locations/<region>
```

### 3. Check Specific Quota Usage
```bash
az quota usage show --resource-name <quota-name> --scope /subscriptions/<id>/providers/<Provider>/locations/<region>
```

### 4. Request Quota Increase
```bash
az quota create --resource-name <quota-name> --scope <scope> --limit-object value=<new-limit> limit-object-type=LimitValue
```

## Important: Resource Name Mapping
There is **no 1:1 mapping** between ARM resource types and quota resource names. Always:
1. List all quotas for the provider
2. Match by `localizedValue` (human-readable description)
3. Use the `name` field in subsequent commands

| ARM Resource Type | Quota Resource Name |
|-------------------|---------------------|
| `Microsoft.Compute/virtualMachines` | `standardDSv3Family`, `cores` |
| `Microsoft.Network/publicIPAddresses` | `PublicIPAddresses` |
| `Microsoft.App/managedEnvironments` | `ManagedEnvironmentCount` |

## Common Scenarios

### Pre-Deployment Capacity Check
Before deploying, verify the target region has sufficient quota for:
- VM family vCPUs
- Public IPs
- Storage accounts
- Load balancers
- Any service-specific limits

### Region Selection by Capacity
Compare quota availability across regions to find the best deployment target.

### Troubleshooting Quota Errors
When deployment fails with `QuotaExceeded`:
1. Identify the specific quota that was exceeded
2. Check current usage vs limit
3. Either request an increase or choose a different region/SKU

## Output Format
- **Current Usage** — table of quotas with usage vs limit
- **Capacity Assessment** — sufficient / at risk / exceeded
- **Recommendations** — increase requests needed or alternative regions
