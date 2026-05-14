# Skill: Azure Reliability Assessment

Assess and improve the reliability posture of Azure workloads — zone redundancy, storage redundancy, health probes, multi-region failover, and single points of failure.

## Trigger Phrases
- "assess reliability"
- "check reliability"
- "zone redundant"
- "multi-region failover"
- "high availability"
- "disaster recovery"
- "single points of failure"
- "reliability posture"
- "availability zones"

## Assessment Areas

### 1. Zone Redundancy
- Compute: are VMs, VMSS, App Service Plans, AKS node pools zone-redundant?
- Databases: zone-redundant SQL, Cosmos DB multi-region writes
- Storage: ZRS vs LRS redundancy
- Networking: zone-redundant load balancers, gateways, firewalls
- Identify resources in regions that support AZs but don't use them

### 2. Storage Redundancy
- Storage account redundancy tier (LRS, ZRS, GRS, GZRS)
- Managed disk redundancy for OS and data disks
- Database backup storage redundancy
- Cross-cutting: any storage dependency on LRS in production

### 3. Health Probes & Monitoring
- Load balancer health probe configuration
- Application Gateway health probes
- Front Door health probes for global endpoints
- Traffic Manager endpoint monitoring
- Container Apps health probe settings

### 4. Multi-Region Failover
- Is the workload deployed to multiple regions?
- Global load balancer in front (Front Door, Traffic Manager)
- Database geo-replication or multi-region writes
- Storage GRS/GZRS with read-access secondary
- DNS failover strategy
- RPO/RTO alignment with business requirements

### 5. Single Points of Failure
- Single-instance resources without redundancy
- Single-region deployments for critical workloads
- Dependencies on non-redundant services
- Unprotected management endpoints

### 6. Backup & Recovery
- Azure Backup policy coverage
- Backup frequency and retention alignment with RPO
- Tested recovery procedures (last DR drill date)
- Geo-redundant backup vaults

## Reliability Checklist Output
Present findings as a feature-pivoted table:
```
Reliability Feature              Status      Resources
─────────────────────────────────────────────────────────────
Zone redundancy (compute)        🟢/🟡/🔴    vm-prod-01, aks-cluster-01
Zone-redundant storage           🟢/🟡/🔴    storprod01, sqldb-main
Health probes                    🟢/🟡/🔴    lb-frontend, agw-main
Multi-region failover            🟢/🟡/🔴    app-frontend, api-backend
```

## Output Format
- **Reliability Summary** — overall posture with feature-pivoted checklist
- **Critical Gaps** — single points of failure and immediate risks
- **Remediation Plan** — staged improvements ordered by impact
- **References** — Microsoft Learn reliability guidance per service
