# Skill: Well-Architected Review

Conduct a Well-Architected Framework (WAF) review of an Azure workload, grounded in live environment data and official Microsoft guidance.

## Trigger Phrases
- "well-architected review"
- "WAF assessment"
- "reliability review"
- "security review"
- "architecture review"

## Pillars

### Reliability
- Availability zones usage across compute, storage, databases
- Load balancer and Traffic Manager configuration
- Backup and disaster recovery (ASR, geo-replication)
- SLA composition across dependent services
- Single points of failure

### Security
- Network segmentation (NSGs, Azure Firewall rules)
- Private endpoint adoption vs public endpoints
- Managed identity usage vs service principal/key-based auth
- Defender for Cloud secure score and recommendations
- Key Vault integration for secrets management

### Cost Optimization
- Defer to the FinOps Assessment skill for detailed cost analysis
- Focus on architectural cost patterns: over-provisioned tiers, premium SKUs without justification, dev/test environments running production SKUs

### Operational Excellence
- IaC coverage (are resources deployed via templates or portal?)
- Monitoring and alerting (diagnostic settings, action groups)
- Tagging strategy implementation
- Deployment automation (CI/CD pipelines)

### Performance Efficiency
- SKU appropriateness for workload requirements
- Caching strategy (Redis, CDN)
- Database tier selection and DTU/vCore utilization
- Auto-scaling configuration

## Output Format
Generate a report with:
- **Per-Pillar Scorecard** — Red / Amber / Green per pillar
- **Top 5 Findings** — the most impactful issues across all pillars
- **Detailed Findings** — grouped by pillar, with severity and recommendations
- **Architecture Decision Records** — for any major recommendations
- **References** — links to WAF pillar-specific guidance on Microsoft Learn

Save to `outputs/<customer>/waf-review.md`
