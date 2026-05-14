# Skill: Azure Storage Services

Assess and advise on Azure Storage — Blob Storage, File Shares, Queue Storage, Table Storage, and Data Lake, including access tiers, redundancy, and lifecycle management.

## Trigger Phrases
- "blob storage"
- "file shares"
- "queue storage"
- "table storage"
- "data lake"
- "storage account"
- "access tiers"
- "hot cool cold archive"
- "storage redundancy"
- "lifecycle management"
- "upload files"
- "download blobs"

## Storage Services
| Service | Use When |
|---------|----------|
| Blob Storage | Objects, files, backups, static content |
| File Shares | SMB file shares, lift-and-shift from on-prem |
| Queue Storage | Async messaging, task queues |
| Table Storage | NoSQL key-value (consider Cosmos DB for more features) |
| Data Lake | Big data analytics, hierarchical namespace |

## Storage Account Tiers
| Tier | Use Case | Performance |
|------|----------|-------------|
| Standard (GPv2) | General purpose, backup | Milliseconds |
| Premium | Block blobs, file shares, or page blobs | Sub-millisecond |

## Blob Access Tiers
| Tier | Access Frequency | Storage Cost | Access Cost |
|------|-----------------|--------------|-------------|
| Hot | Frequent | Higher | Lower |
| Cool | Infrequent (30+ days) | Lower | Higher |
| Cold | Rare (90+ days) | Lower still | Higher still |
| Archive | Rarely (180+ days) | Lowest | Rehydration required |

## Redundancy Options
| Type | Durability | Availability | Use Case |
|------|------------|-------------|----------|
| LRS | 11 nines | Single datacenter | Dev/test, recreatable data |
| ZRS | 12 nines | Zone-redundant | Regional HA |
| GRS | 16 nines | Cross-region | Disaster recovery |
| GZRS | 16 nines | Zone + cross-region | Best durability |

## Assessment Guidance
When reviewing storage architecture:
- **Tier selection**: Match access tier to actual access patterns (check metrics)
- **Redundancy**: Production workloads should use ZRS minimum, GRS/GZRS for critical data
- **Lifecycle management**: Automate tier transitions based on last access time
- **Security**: Private endpoints for storage accounts, disable public blob access
- **Encryption**: Customer-managed keys for compliance requirements
- **Network**: Service endpoints vs private endpoints — prefer private endpoints
- **Performance**: Premium tier for latency-sensitive workloads
- **Cost**: Archive tier for long-term retention, but factor in rehydration costs

## Output Format
- **Current Configuration** — storage accounts with tier, redundancy, access settings
- **Optimization Recommendations** — tier changes, redundancy upgrades, lifecycle policies
- **Security Findings** — public access, network rules, encryption
- **Cost Impact** — estimated savings from tier or redundancy changes
- **References** — Microsoft Learn storage documentation
