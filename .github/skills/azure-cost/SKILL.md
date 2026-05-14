# Skill: Azure Cost Management

Query historical costs, forecast future spending, and identify optimization opportunities across Azure subscriptions.

## Trigger Phrases
- "how much am I spending"
- "Azure costs"
- "cost breakdown"
- "cost by service"
- "show my bill"
- "forecast spending"
- "projected costs"
- "optimize costs"
- "reduce spending"
- "find cost savings"
- "orphaned resources"
- "rightsize VMs"
- "cost by tag"
- "cost spike"
- "budget alert"

## Assessment Areas

### 1. Cost Query & Analysis
- Current month spend vs previous month
- Cost breakdown by service, resource group, location, or tag
- Top cost drivers (resources and meters)
- Cost trends over time (3-month, 6-month)
- Amortized vs actual cost views

### 2. Cost Forecasting
- Projected end-of-month cost
- Budget vs actual tracking
- Trend-based forecasting using Cost Management API

### 3. Cost Optimization
Identify waste and savings opportunities:

#### Idle & Orphaned Resources
- Unattached managed disks
- Orphaned NICs and public IPs
- App Service Plans with 0 apps
- Stopped VMs still incurring storage costs
- Empty resource groups

#### Right-Sizing
- Advisor right-sizing recommendations
- Over-provisioned VMs and databases
- Premium SKUs in dev/test environments

#### Commitment Discounts
- Reservation and Savings Plan opportunities from Advisor
- Current commitment utilization rates
- Estimated savings from new commitments

#### Azure Hybrid Benefit
- Windows VMs without AHB enabled
- SQL resources without AHB
- Potential savings calculation

#### Architectural Patterns
- Premium SKUs without justification
- Dev/test running on production SKUs
- Missing auto-scaling (always-on at peak capacity)

### 4. Cost Governance
- Budget configuration and alerting
- Cost Management export pipelines
- Tag coverage for cost allocation (CostCenter, BusinessUnit, Environment)
- FinOps maturity indicators

## Scope Reference
| Scope | Path |
|-------|------|
| Subscription | `/subscriptions/<id>` |
| Resource Group | `/subscriptions/<id>/resourceGroups/<name>` |
| Management Group | `/providers/Microsoft.Management/managementGroups/<id>` |

## Output Format
- **Executive Summary** — total spend, month-over-month change, estimated savings
- **Quick Wins** — fixable in < 1 day (orphaned resources, AHB, tags)
- **Medium-Term** — requires planning (right-sizing, reservations)
- **Strategic** — architectural changes for long-term savings
