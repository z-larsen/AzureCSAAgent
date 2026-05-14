# Skill: Azure Kubernetes Service (AKS)

Plan, assess, and configure production-ready AKS clusters — covering Day-0 decisions, SKU selection, networking, security, observability, and operations.

## Trigger Phrases
- "create AKS cluster"
- "plan AKS configuration"
- "AKS networking"
- "choose AKS SKU"
- "AKS Automatic vs Standard"
- "secure AKS"
- "AKS observability"
- "AKS cost optimization"
- "AKS spot nodes"
- "AKS cluster autoscaler"
- "AKS upgrade strategy"

## Assessment Areas

### 1. SKU Selection
- **AKS Automatic** (recommended default): curated experience with best practices for security, reliability, and performance. Node Auto-Provisioning handles scaling.
- **AKS Standard**: full control over node pools, networking, and configuration. More overhead to manage.
- Choose Standard only when specific custom requirements aren't supported by Automatic.

### 2. Networking (Day-0 Decisions — hard to change later)

#### Pod IP Model
| Model | Description | Use When |
|-------|-------------|----------|
| Azure CNI Overlay (recommended) | Pod IPs from private overlay range, not VNet-routable | Most workloads, scales well |
| Azure CNI (VNet-routable) | Pod IPs directly from VNet | Pods must be addressable from VNet/on-prem |

#### Dataplane & Network Policy
- **Azure CNI powered by Cilium** (recommended): eBPF-based, high-performance network policies and observability

#### Egress
- Static Egress Gateway for stable outbound IPs
- UDR + Azure Firewall for restricted egress

#### Ingress
- App Routing addon with Gateway API (recommended default)
- Istio service mesh for advanced traffic management, mTLS
- Application Gateway for Containers for L7 + WAF

#### DNS
- Enable LocalDNS on all node pools for reliable resolution

### 3. Security
- Microsoft Entra ID for control plane, Workload Identity for pods
- Azure Key Vault via Secrets Store CSI Driver
- Azure Policy + Deployment Safeguards
- Encryption at rest (etcd) and in transit (node-to-node)
- Image policy: signed, approved images via Azure Policy + Ratify
- Prefer Azure Container Registry
- Namespace isolation with network policies

### 4. Observability
- Managed Prometheus + Container Insights + Grafana
- Diagnostic Settings for control plane logs and audit logs
- Application Insights for application-level telemetry
- Resource Health Center and AppLens detectors

### 5. Upgrades & Patching
- Configure maintenance windows for controlled timing
- Enable auto-upgrades for control plane and node OS
- Consider LTS versions for enterprise stability (Premium tier)
- AKS Fleet Manager for staged rollouts across environments

### 6. Cost Optimization
- Spot node pools for fault-tolerant workloads
- Cluster autoscaler tuning (scale-down delay, utilization thresholds)
- Right-size node pools based on workload resource requests
- AKS cost analysis add-on for namespace-level cost visibility
- Reserved Instances for baseline node capacity

## Output Format
- **Cluster Configuration** — recommended settings with rationale
- **Day-0 vs Day-1** — what must be decided upfront vs can be enabled later
- **Architecture Diagram** — Mermaid diagram of cluster topology
- **CLI Commands** — `az aks create` with recommended parameters
- **References** — Microsoft Learn links for each configuration choice
