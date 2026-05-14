# Skill: Azure Diagnostics & Troubleshooting

Debug Azure production issues using Azure Monitor, resource health, activity logs, and systematic triage.

## Trigger Phrases
- "debug production issue"
- "troubleshoot app service"
- "app service high CPU"
- "troubleshoot container apps"
- "troubleshoot functions"
- "troubleshoot AKS"
- "pod crashloop"
- "node not ready"
- "analyze logs"
- "KQL query"
- "image pull failure"
- "cold start issues"
- "health probe failures"
- "resource health"
- "root cause analysis"
- "deployment failure"

## Quick Diagnosis Flow

1. **Identify symptoms** — What's failing? Error messages, user impact
2. **Check resource health** — Is the Azure platform healthy?
3. **Review activity log** — What changed recently? (deployments, config changes)
4. **Analyze metrics** — CPU, memory, request count, error rates, latency
5. **Investigate logs** — Application logs, platform logs, diagnostic logs

## Service-Specific Troubleshooting

### App Service
- High CPU / memory — check App Service Plan tier and scaling
- Deployment failures — check deployment logs and slot swap status
- Slow responses — check application insights, dependency calls
- TLS/custom domain issues — certificate binding and DNS validation
- 5xx errors — check application logs and platform diagnostics

### Azure Functions
- Invocation failures — check function host logs and binding configuration
- Timeouts — verify function timeout settings vs plan limits
- Cold start — check plan type (Consumption vs Premium)
- Missing app settings — validate Key Vault references and connection strings
- Scaling issues — monitor concurrent executions and plan limits

### Container Apps
- Image pull failures — check ACR access, managed identity, image tag
- Cold starts — container startup time, health probe configuration
- Port mismatches — ingress target port vs container EXPOSE port
- Scaling issues — check revision scaling rules and min/max replicas

### AKS
- kubectl cannot connect — API server access, kubeconfig, network policies
- Pod pending — insufficient resources, node pool scaling, taints/tolerations
- CrashLoopBackOff — check container logs, resource limits, readiness probes
- Node not ready — check node conditions, VM health, disk pressure
- CoreDNS failures — check kube-system pods, DNS configuration
- Upgrade failures — check PDB, node surge settings, version compatibility

### Networking
- Connectivity issues — NSG rules, route tables, firewall rules, DNS resolution
- Private endpoint access — DNS zone configuration, VNet link status
- Load balancer health — probe status, backend pool membership
- ExpressRoute/VPN — circuit provisioning, BGP peering, gateway health

## Common Diagnostic Commands
```bash
# Check resource health
az resource show --ids <RESOURCE_ID>

# View activity log
az monitor activity-log list -g <RG> --max-events 20

# Container Apps logs
az containerapp logs show --name <APP> -g <RG> --follow

# App Insights query
az monitor app-insights query --apps <AI_NAME> -g <RG> \
  --analytics-query "traces | where timestamp > ago(1h) | order by timestamp desc | take 50"
```

## Output Format
- **Diagnosis Summary** — symptoms, root cause, and confidence level
- **Evidence** — logs, metrics, and configuration findings
- **Remediation Steps** — ordered by priority, with CLI commands
- **Prevention** — what to configure to avoid recurrence
- **References** — Microsoft Learn troubleshooting guides
