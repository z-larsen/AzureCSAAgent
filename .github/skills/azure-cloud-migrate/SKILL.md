# Skill: Azure Cloud Migration Assessment

Assess and plan cross-cloud workload migrations to Azure — covering Lambda→Functions, Beanstalk/Heroku/App Engine→App Service, Fargate/Kubernetes/Cloud Run/Spring Boot→Container Apps.

## Trigger Phrases
- "migrate to Azure"
- "AWS to Azure"
- "migrate Lambda to Functions"
- "migrate Beanstalk"
- "migrate Heroku"
- "migrate App Engine"
- "Cloud Run migration"
- "Fargate to Container Apps"
- "Kubernetes to Container Apps"
- "Spring Boot to Container Apps"
- "cross-cloud migration"
- "migration assessment"

## Migration Scenarios

| Source | Target Azure Service |
|--------|---------------------|
| AWS Lambda | Azure Functions |
| AWS Elastic Beanstalk | Azure App Service |
| Heroku | Azure App Service |
| Google App Engine | Azure App Service |
| AWS Fargate (ECS) | Azure Container Apps |
| Kubernetes (GKE/EKS/Self-hosted) | Azure Container Apps |
| GCP Cloud Run | Azure Container Apps |
| Spring Boot (Azure Spring Apps/VMs) | Azure Container Apps |

## Assessment Workflow

### 1. Source Analysis
- Inventory source workload: compute, storage, networking, identity
- Map source services to Azure equivalents
- Identify dependencies and integration points
- Catalog environment variables, secrets, and configuration
- Scan source code for hardcoded hostnames/ports that need migration

### 2. Compatibility Assessment
- Runtime and language version compatibility
- Trigger/event source mapping (e.g., SQS→Service Bus, S3→Blob Storage)
- Authentication model differences (IAM roles→Managed Identity)
- Networking model differences (VPC→VNet, security groups→NSGs)
- Storage and database migration requirements

### 3. Migration Complexity Rating
| Complexity | Criteria |
|-----------|---------|
| Low | Direct 1:1 service mapping, minimal code changes |
| Medium | Some service mapping differences, moderate code changes |
| High | Significant architecture differences, major code refactoring |

### 4. Migration Plan
- Phased migration approach (lift-and-shift → modernize)
- Testing strategy for each phase
- Rollback plan
- Estimated effort per component
- Network connectivity during migration (hybrid period)

### 5. Key Migration Patterns
- **Kubernetes DNS**: `http://service:port` doesn't resolve in Container Apps — use env-var-driven URL injection
- **IAM to RBAC**: Map IAM policies to Azure RBAC role assignments
- **Secrets**: Migrate from source secret manager to Azure Key Vault
- **Event Sources**: Map cloud-specific triggers to Azure equivalents

## Output Format
- **Assessment Report** — source inventory, target mapping, complexity rating
- **Migration Plan** — phased approach with effort estimates
- **Risk Register** — identified risks and mitigation strategies
- **Architecture Diagram** — before/after Mermaid diagrams
- **References** — Microsoft Learn migration guides per scenario
