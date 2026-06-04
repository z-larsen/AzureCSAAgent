# Skill: Azure Data Platform Review

Assess the posture of Azure data services — Azure SQL (Database & Managed Instance), Cosmos DB, PostgreSQL/MySQL Flexible Server, and Azure Cache for Redis — across reliability, security, cost, and performance. This skill focuses on the *data tier* specifically: tier/SKU right-sizing, high availability and geo-replication, backup and retention, encryption (TDE/CMK), and network exposure. For broad architecture trade-offs use `well-architected-review`; for active database incidents use `azure-diagnostics`.

## Trigger Phrases
- "data platform review"
- "database assessment"
- "SQL review" / "Azure SQL posture"
- "Cosmos DB review"
- "PostgreSQL review" / "MySQL review"
- "Redis review"
- "database backup audit"
- "database HA review"
- "database security review"
- "database right-sizing"
- "data tier assessment"
- "geo-replication review"

## Assessment Areas

### 1. Inventory & Tier/SKU Posture
- All data resources by type: `microsoft.sql/servers/databases`, `microsoft.sql/managedinstances`, `microsoft.documentdb/databaseaccounts`, `microsoft.dbforpostgresql/flexibleservers`, `microsoft.dbformysql/flexibleservers`, `microsoft.cache/redis`
- Service tier / SKU per resource (Basic/Standard/Premium, General Purpose/Business Critical/Hyperscale, vCore vs DTU)
- **Right-sizing signals** — Basic/Standard tiers in production, oversized provisioned throughput, idle databases
- Serverless vs provisioned (Azure SQL serverless, Cosmos serverless) — is the consumption model matched to the workload pattern?
- Deprecated tiers / legacy single-server (PostgreSQL/MySQL Single Server is retired — flag for Flexible Server migration)

### 2. High Availability & Resilience
- **Zone redundancy** — is it enabled where the tier and region support it? (Business Critical, Premium, zone-redundant Flexible Server)
- **Azure SQL** — failover groups, active geo-replication, auto-failover configuration
- **Cosmos DB** — multi-region writes, regions configured, automatic failover, consistency level vs availability trade-off
- **PostgreSQL/MySQL Flexible** — HA mode (zone-redundant vs same-zone vs none), standby state
- **Redis** — tier (Premium for zone redundancy/persistence), zone configuration
- Single-region / single-zone deployments hosting critical data (single point of failure)

### 3. Backup, Retention & Recovery
- **Azure SQL** — point-in-time restore window, long-term retention (LTR) policy presence, backup storage redundancy (LRS/ZRS/GRS)
- **Cosmos DB** — backup mode (periodic vs continuous), retention, point-in-time restore capability
- **PostgreSQL/MySQL Flexible** — backup retention days, geo-redundant backup enabled?
- Resources relying only on default short backup windows for business-critical data
- Documented/implied RPO/RTO vs what the backup configuration actually delivers

### 4. Encryption & Data Protection
- **Transparent Data Encryption (TDE)** — enabled (default yes for SQL, but verify), service-managed vs customer-managed key (CMK)
- **Customer-managed keys** — where compliance requires CMK, is it configured, and is the Key Vault access durable (no single-key SPOF)?
- Cosmos DB / PostgreSQL / MySQL encryption-at-rest key model (service vs customer-managed)
- TLS enforcement — minimum TLS version, "require secure transport" on PostgreSQL/MySQL
- Azure SQL auditing and Microsoft Defender for SQL enablement

### 5. Network Exposure (cross-reference `network-review`)
- **Public network access** — data services with `publicNetworkAccess = Enabled` open to the internet
- **"Allow Azure services"** firewall rule on SQL (0.0.0.0 → all Azure IPs tenant-wide, not just yours) — high risk
- Private endpoint coverage — which data services have private endpoints vs which are firewall-only or fully public
- Firewall rule sprawl — overly broad IP ranges, `0.0.0.0/0` allow rules
- VNet integration / VNet rules for Flexible Servers

### 6. Performance & Configuration Hygiene
- **Cosmos DB throughput** — manual provisioned vs autoscale; autoscale recommended for variable workloads to avoid over-provisioning
- Azure SQL — read scale-out usage, Hyperscale for very large databases, in-memory/columnstore where applicable
- Redis — eviction policy, maxmemory-reserved, clustering for scale
- Connection pooling / PgBouncer (PostgreSQL Flexible built-in) for connection-heavy workloads
- Maintenance window configuration (controlled vs system-managed)

## Follow-Up Questions

Before concluding a data platform review, confirm intent:

### Workload Criticality
- "Which of these databases are production-critical? That drives whether the lack of geo-replication or zone redundancy is a real finding or acceptable for dev/test."
- "What's your target RPO/RTO for the critical data tier? I'll check whether the current backup/HA config actually meets it."

### Cost vs Resilience Trade-off
- "I see Business Critical / Premium tiers on what look like non-prod databases — is that intentional, or a right-sizing opportunity?"
- "Cosmos DB throughput is manually provisioned at [X] RU/s — is the workload steady, or would autoscale cut cost on variable traffic?"

### Security & Compliance
- "Several databases have public network access enabled — is private endpoint migration planned, or is there a network control I'm not seeing?"
- "Do you have a compliance requirement for customer-managed keys, or is service-managed encryption acceptable?"

### Modernization
- "Any PostgreSQL/MySQL Single Server instances are on a retired platform — is Flexible Server migration on the roadmap?"

## Risk Classification

| Severity | Examples |
|----------|---------|
| **Critical** | Production database with public access + "Allow Azure services" enabled, no geo-replication on tier-1 data, retired Single Server still in production, no Defender for SQL on internet-exposed databases |
| **High** | Business-critical database with no zone redundancy where supported, no long-term backup retention, default short PITR window on critical data, TLS not enforced |
| **Medium** | Over-provisioned tiers in non-prod, manual Cosmos throughput on variable workloads, firewall-only (no private endpoint) on sensitive data, service-managed keys where CMK is expected |
| **Low** | Suboptimal Redis eviction policy, no maintenance window control, missing read scale-out where it would help |

## Output Format
Generate a report with:
- **Data Platform Summary** — resource inventory by engine, tier distribution, HA/backup/encryption status at a glance
- **Resilience** — zone redundancy, geo-replication, backup/retention vs implied RPO/RTO
- **Security** — encryption model, network exposure, auditing/Defender coverage
- **Cost & Right-Sizing** — over-provisioned tiers, throughput model recommendations
- **Findings** — prioritized by severity (Critical → Low) with specific resource names and engines
- **Recommendations** — each with a Microsoft Learn reference (per-engine reliability & security guides)
- **References** — Azure SQL / Cosmos DB / PostgreSQL Flexible / Redis best-practice Learn docs, Well-Architected data guidance

Save to `outputs/<customer>/data-platform-review.md`
