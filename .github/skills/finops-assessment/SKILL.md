# Skill: FinOps Assessment

Assess an Azure environment's FinOps maturity and cost optimization opportunities.

## Trigger Phrases
- "finops assessment"
- "cost optimization review"
- "where are we wasting money"
- "commitment discount analysis"
- "tag coverage for cost allocation"

## Assessment Areas

### 1. Tag Coverage for Cost Allocation
Query all resources and evaluate tag coverage for CAF allocation tags:
- CostCenter, BusinessUnit, ApplicationName, WorkloadName, OpsTeam, Environment
- Calculate coverage percentage per tag
- Identify resource types with worst coverage

### 2. Commitment Discounts (RIs & Savings Plans)
- Query Advisor recommendations for reservation and savings plan opportunities
- Assess current utilization of existing commitments
- Estimate potential savings from new commitments

### 3. Idle & Orphaned Resources
- Unattached disks, orphaned NICs, empty resource groups
- Public IPs not attached to anything
- App Service Plans with 0 apps
- Stopped VMs still incurring storage costs

### 4. Right-Sizing Opportunities
- Query Advisor for right-sizing recommendations
- Categorize by service type and estimated savings
- Cross-reference with actual resource metrics where possible

### 5. Azure Hybrid Benefit
- Windows VMs without AHB enabled
- SQL resources without AHB
- Calculate potential savings from enabling AHB

### 6. Cost Governance Maturity
- Are budgets configured? At what scope?
- Are cost alerts set up?
- Is there a cost management export pipeline?
- FinOps Toolkit deployment status

## Output Format
Generate a report with:
- **Executive Summary** — total estimated monthly savings opportunity
- **Quick Wins** — things fixable in < 1 day (orphaned resources, AHB, tag gaps)
- **Medium Term** — commitment purchases, right-sizing (1-4 weeks)
- **Strategic** — cost allocation model, FinOps Toolkit deployment, chargeback automation
- **FinOps Maturity Rating** — Crawl / Walk / Run per FinOps capability
- **References** — links to FinOps Toolkit docs, Microsoft Learn cost optimization guides

Save to `outputs/<customer>/finops-assessment.md`
