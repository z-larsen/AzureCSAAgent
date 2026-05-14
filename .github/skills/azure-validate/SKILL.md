# Skill: Azure Pre-Deployment Validation

Run pre-deployment validation checks on Azure configuration, infrastructure templates (Bicep or Terraform), RBAC assignments, and managed identity permissions.

## Trigger Phrases
- "validate my deployment"
- "check deployment readiness"
- "run preflight checks"
- "verify configuration"
- "validate Bicep"
- "validate Terraform"
- "test before deploying"
- "troubleshoot deployment errors"
- "what-if analysis"
- "check role assignments"
- "review managed identity permissions"

## Validation Checks

### 1. Template Validation
- **Bicep**: `bicep build` to check syntax and compilation
- **Terraform**: `terraform validate` and `terraform plan`
- **ARM**: Template schema validation
- Parameter completeness and default values

### 2. What-If Analysis
- `az deployment group what-if` for Bicep/ARM templates
- `terraform plan` for Terraform configurations
- Review expected resource changes before deployment
- Identify potential destructive operations

### 3. RBAC & Identity Validation
- Verify deploying identity has sufficient permissions
- Check managed identity role assignments in templates
- Validate scope of role assignments (least privilege)
- Cross-reference required vs assigned permissions

### 4. Configuration Checks
- Required app settings and connection strings present
- Key Vault references resolvable
- Container image tags exist in registry
- DNS records configured correctly
- SSL certificates valid and not expired

### 5. Resource Dependencies
- Dependent resources exist (VNets, subnets, Key Vaults)
- Resource names available (globally unique names)
- Region supports required resource types and SKUs
- Quota availability for planned resources

### 6. Network Readiness
- Private endpoints configured correctly
- DNS zones and records in place
- NSG rules allow required traffic
- Subnet delegation configured for target services

## Validation Workflow
1. **Load deployment plan** — read infrastructure templates and configuration
2. **Run template validation** — syntax and compilation checks
3. **Execute what-if** — preview resource changes
4. **Verify RBAC** — check role assignments in templates and on deploying identity
5. **Check dependencies** — verify all prerequisites exist
6. **Record proof** — document all checks run and their results
7. **Report** — pass/fail summary with remediation for failures

## Output Format
- **Validation Summary** — pass/fail per check category
- **Failed Checks** — detailed error messages and remediation steps
- **What-If Results** — expected resource changes
- **Approval Gate** — ready to deploy or blocked
