# Skill: Microsoft Entra ID App Registration

Guide app registration, OAuth 2.0 authentication setup, and MSAL integration in Microsoft Entra ID (formerly Azure AD).

## Trigger Phrases
- "create app registration"
- "register Azure AD app"
- "configure OAuth"
- "set up authentication"
- "add API permissions"
- "generate service principal"
- "MSAL example"
- "Entra ID setup"
- "Azure AD authentication"
- "client credentials flow"
- "managed identity vs app registration"

## Key Concepts
| Concept | Description |
|---------|-------------|
| App Registration | Configuration allowing an app to use Microsoft identity platform |
| Application (Client) ID | Unique identifier for the application |
| Tenant ID | Unique identifier for the Azure AD tenant |
| Client Secret | Password for confidential clients |
| Redirect URI | URL where auth responses are sent |
| API Permissions | Access scopes the app requests |
| Service Principal | Identity created in tenant when app is registered |

## Application Types
| Type | Use Case | Auth Flow |
|------|----------|-----------|
| Web Application | Server-side apps, APIs | Authorization Code |
| Single Page App (SPA) | JavaScript/React/Angular | Auth Code with PKCE |
| Mobile/Native App | Desktop, mobile | Auth Code with PKCE |
| Daemon/Service | Background services | Client Credentials |

## Registration Workflow

### 1. Register the Application
- Portal: Entra ID → App registrations → New registration
- CLI: `az ad app create --display-name "<name>"`
- Choose supported account types (single-tenant, multi-tenant)

### 2. Configure Authentication
- Web Apps: redirect URIs, ID tokens
- SPAs: redirect URIs, PKCE
- Services: no redirect URI needed (client credentials)

### 3. Configure API Permissions
Common Microsoft Graph permissions:
- `User.Read` — read user profile
- `User.ReadWrite.All` — read/write all users
- `Directory.Read.All` — read directory data
- `Mail.Send` — send mail as user

### 4. Create Client Credentials
- **Client Secret**: quick setup, must rotate regularly
- **Certificate**: recommended for production (stronger security)
- **Federated Identity**: for workload identity federation (no secrets)
- Store secrets in Key Vault, never in code or config files

### 5. Implement OAuth Flow
- Use MSAL libraries for all platforms
- Prefer managed identity over app registration when running in Azure
- Use DefaultAzureCredential for multi-environment support

## Assessment Guidance
When reviewing an environment's app registrations:
- Check for apps with excessive API permissions
- Identify apps with expired or soon-to-expire secrets/certificates
- Find apps with no owner assigned
- Look for unused app registrations (no sign-in activity)
- Verify multi-tenant apps have appropriate consent policies
- Check for apps using client secrets instead of certificates or federated credentials

## Output Format
- **Registration Details** — client ID, tenant ID, redirect URIs
- **Authentication Configuration** — flow type, token settings
- **Permission Summary** — granted permissions with admin consent status
- **Security Recommendations** — credential type, rotation, least privilege
