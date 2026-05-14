# Skill: Azure RBAC & Role Assignments

Find the right Azure RBAC role for an identity with least privilege access, assess current role assignments, and identify security gaps.

## Trigger Phrases
- "what role should I assign"
- "least privilege role"
- "RBAC role for"
- "role to read blobs"
- "role for managed identity"
- "custom role definition"
- "assign role to identity"
- "review role assignments"
- "RBAC audit"
- "excessive permissions"

## Capabilities

### Role Selection (Least Privilege)
- Find the minimal built-in role that matches desired permissions
- Recommend built-in roles over custom when possible
- If no built-in role matches, guide custom role definition

### Common Role Mappings
| Need | Recommended Role |
|------|-----------------|
| Read all resources | Reader |
| Manage VMs only | Virtual Machine Contributor |
| Read blob data | Storage Blob Data Reader |
| Write blob data | Storage Blob Data Contributor |
| Read Key Vault secrets | Key Vault Secrets User |
| Deploy resources | Contributor (scope carefully) |
| Assign roles to others | User Access Administrator |
| Full access | Owner (avoid at broad scopes) |

### RBAC Assessment
- Audit current role assignments at subscription scope
- Identify users with Owner/Contributor at subscription level
- Find service principals with excessive permissions
- Check for classic administrator roles still in use
- Verify managed identity role assignments are scoped correctly

### Custom Role Definitions
- Define custom roles with minimum required permissions
- Scope custom roles to specific resource types
- Include `Microsoft.Authorization/roleAssignments/write` only when role management is needed

## Prerequisites for Granting Roles
To assign RBAC roles, you need:
- **User Access Administrator** (least privilege for role assignment only)
- **Owner** (full access including role assignment)
- **Custom Role** with `Microsoft.Authorization/roleAssignments/write`

## Output Format
- Recommended role with justification
- CLI command to assign the role
- Bicep snippet for IaC integration
- Security considerations and scope recommendations
