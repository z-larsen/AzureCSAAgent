"""Infrastructure as Code generator — Bicep and Terraform using Azure Verified Modules."""

import json
import os
import re

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

from csa.progress import StepTracker
from csa.tokens import session as token_session

console = Console()

IAC_SYSTEM_PROMPT = """You are a senior Azure Cloud Solution Architect and Infrastructure as Code expert with deep expertise in both Bicep and Terraform.

You generate production-grade, deployment-ready IaC code using Azure Verified Modules (AVM) wherever possible.

## Azure Verified Modules (AVM)

AVM is Microsoft's official library of pre-built, tested, and supported modules for deploying Azure resources.

### Bicep AVM
- Registry: `br/public:avm/res/<provider>/<resource>:<version>`
- Browse: https://aka.ms/AVM/bicep
- Pattern: `module <name> 'br/public:avm/res/<provider>/<resource>:<version>' = { params }`
- Always use the latest stable version
- Key modules:
  - `br/public:avm/res/network/virtual-network` — VNets with subnets, peering, NSGs
  - `br/public:avm/res/network/network-security-group` — NSGs with rules
  - `br/public:avm/res/network/private-endpoint` — Private endpoints
  - `br/public:avm/res/network/firewall` — Azure Firewall
  - `br/public:avm/res/network/bastion-host` — Azure Bastion
  - `br/public:avm/res/compute/virtual-machine` — VMs
  - `br/public:avm/res/container-service/managed-cluster` — AKS
  - `br/public:avm/res/web/site` — App Service / Function Apps
  - `br/public:avm/res/sql/server` — Azure SQL
  - `br/public:avm/res/storage/storage-account` — Storage accounts
  - `br/public:avm/res/key-vault/vault` — Key Vault
  - `br/public:avm/res/operational-insights/workspace` — Log Analytics
  - `br/public:avm/res/insights/diagnostic-setting` — Diagnostic settings
  - `br/public:avm/ptn/` — Pattern modules for common architectures (hub-spoke, etc.)

### Terraform AVM
- Registry: `registry.terraform.io/Azure/<resource>/azurerm`
- Browse: https://aka.ms/AVM/terraform
- Pattern: `module "<name>" { source = "Azure/<resource>/azurerm" version = "<version>" }`
- Key modules:
  - `Azure/avm-res-network-virtualnetwork/azurerm` — VNets
  - `Azure/avm-res-network-networksecuritygroup/azurerm` — NSGs
  - `Azure/avm-res-compute-virtualmachine/azurerm` — VMs
  - `Azure/avm-res-containerservice-managedcluster/azurerm` — AKS
  - `Azure/avm-res-web-site/azurerm` — App Service
  - `Azure/avm-res-sql-server/azurerm` — Azure SQL
  - `Azure/avm-res-storage-storageaccount/azurerm` — Storage
  - `Azure/avm-res-keyvault-vault/azurerm` — Key Vault
  - `Azure/avm-ptn-hubnetworking/azurerm` — Hub networking pattern

## Code Generation Rules

1. **Always use AVM modules** when available — never write raw resource blocks for resources that AVM covers
2. **Parameterize everything** — no hardcoded values for names, locations, SKUs, address spaces, or secrets
3. **Include outputs** — expose key resource IDs, FQDNs, connection strings, and endpoints
4. **Follow naming conventions** — use the `namingPrefix` or `name` parameter pattern: `${prefix}-${resourceType}-${environment}`
5. **Security by default**:
   - Enable diagnostic settings on all resources
   - Use managed identity over keys/passwords
   - Enable private endpoints where applicable
   - Set minimum TLS versions
   - Enable encryption at rest and in transit
   - Use NSGs on all subnets
6. **Tag everything** — accept a `tags` parameter and propagate to all resources
7. **Use proper file structure**:
   - Bicep: `main.bicep` + `main.bicepparam` (or `parameters.json`)
   - Terraform: `main.tf` + `variables.tf` + `outputs.tf` + `providers.tf` + `terraform.tfvars.example`
8. **Include deployment commands** in a comment block at the top
9. **Separate environments** — use parameters/variables for dev/staging/prod differentiation
10. **Resource dependencies** — explicitly define dependencies where implicit ordering isn't sufficient

## Output Format

Return your response as markdown with:
1. A brief architecture overview (2-3 sentences)
2. Each file in a separate fenced code block with the filename as the info string:
   ```bicep filename="main.bicep"
   // code here
   ```
3. Deployment instructions at the end

If the user hasn't specified Bicep or Terraform, default to Bicep.
If the user's request is ambiguous, ask clarifying questions about:
- Environment (dev/staging/prod)
- Region
- Networking requirements (address spaces, peering)
- Compliance requirements
- Expected workload characteristics
"""

IAC_ANALYSIS_PROMPT = """You are reviewing the user's existing Azure environment data from Azure Resource Graph to generate IaC that matches or improves upon their current setup.

Given the ARG query results and the user's request, generate IaC code that:
1. Captures the existing architecture accurately
2. Applies best practices and improvements where noted
3. Uses Azure Verified Modules (AVM)
4. Parameterizes all environment-specific values

Reference specific resources from the results by name and configuration."""


def _get_openai_client():
    """Return an (OpenAI-compatible client, deployment/model name) tuple."""
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    azure_key = os.environ.get("AZURE_OPENAI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

    if endpoint:
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider
        from openai import AzureOpenAI

        if azure_key:
            client = AzureOpenAI(azure_endpoint=endpoint, api_key=azure_key, api_version="2024-10-21")
        else:
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
            )
            client = AzureOpenAI(azure_endpoint=endpoint, azure_ad_token_provider=token_provider, api_version="2024-10-21")
        return client, deployment

    elif openai_key:
        from openai import OpenAI
        return OpenAI(api_key=openai_key), "gpt-4o"

    else:
        console.print("[yellow]No LLM backend configured. Run [bold]azure-csa[/bold] for setup instructions.[/yellow]")
        return None, None


def _extract_files(response: str) -> list[dict]:
    """Extract individual files from fenced code blocks in the LLM response.

    Looks for patterns like:
      ```bicep filename="main.bicep"
      ```hcl filename="main.tf"
      ### `main.bicep` followed by a code block
    """
    files = []

    # Pattern 1: ```lang filename="name"
    pattern1 = re.findall(
        r'```(\w+)\s+filename="([^"]+)"\n(.*?)```',
        response,
        re.DOTALL,
    )
    for lang, name, content in pattern1:
        files.append({"name": name, "lang": lang, "content": content.strip()})

    if files:
        return files

    # Pattern 2: heading with filename then code block
    pattern2 = re.findall(
        r'(?:###?\s*`?([^`\n]+\.\w+)`?\s*\n+```(\w+)\n(.*?)```)',
        response,
        re.DOTALL,
    )
    for name, lang, content in pattern2:
        files.append({"name": name.strip(), "lang": lang, "content": content.strip()})

    if files:
        return files

    # Pattern 3: just code blocks with lang hints
    blocks = re.findall(r'```(bicep|hcl|terraform|json)\n(.*?)```', response, re.DOTALL)
    ext_map = {"bicep": ".bicep", "hcl": ".tf", "terraform": ".tf", "json": ".json"}
    for i, (lang, content) in enumerate(blocks):
        ext = ext_map.get(lang, ".txt")
        # Try to infer name from content
        name = f"file{i + 1}{ext}"
        if ext == ".bicep":
            if "param " in content and "resource" not in content:
                name = "main.bicepparam"
            elif i == 0:
                name = "main.bicep"
        elif ext == ".tf":
            if "variable " in content and "resource" not in content and "module" not in content:
                name = "variables.tf"
            elif "output " in content and "resource" not in content:
                name = "outputs.tf"
            elif "terraform {" in content or "provider " in content:
                name = "providers.tf"
            elif i == 0:
                name = "main.tf"
        elif ext == ".json" and "parameters" in content:
            name = "parameters.json"
        files.append({"name": name, "lang": lang, "content": content.strip()})

    return files


def generate(request: str, history: list[dict] | None = None, env_context: str = "") -> str | None:
    """Generate IaC code from a natural language request.

    Args:
        request: What to deploy (e.g., "hub-spoke network with firewall").
        history: Conversation history for follow-up context.
        env_context: Optional ARG data about the user's current environment.

    Returns:
        Summary string for conversation history.
    """
    tracker = StepTracker("iac")
    history = history or []
    client, model = _get_openai_client()
    if not client:
        return None

    console.print(f"\n[bold cyan]IaC Request:[/bold cyan] {request}")

    # Build messages
    system_prompt = IAC_SYSTEM_PROMPT
    if env_context:
        system_prompt += f"\n\n## Current Environment Context\n{env_context}"

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history[-10:])
    messages.append({"role": "user", "content": request})

    # Generate IaC
    tracker.started("iac-generation")
    tracker.status("generating infrastructure code")

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=8000,
            stream=True,
            stream_options={"include_usage": True},
        )

        full_text = ""
        usage = None
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                full_text += chunk.choices[0].delta.content
            if hasattr(chunk, "usage") and chunk.usage:
                usage = chunk.usage

        token_session.record(usage, model, "IaC generation")
        tracker.done("iac-generation")

    except Exception as e:
        console.print(f"[red]LLM error: {e}[/red]")
        tracker.done("iac-generation", "failed")
        return None

    # Extract files from the response
    files = _extract_files(full_text)

    if files:
        # Determine output directory
        output_dir = "outputs/iac"
        os.makedirs(output_dir, exist_ok=True)

        console.print()
        console.print(Panel.fit("[bold green]Generated Files[/bold green]", border_style="green"))

        for f in files:
            filepath = os.path.join(output_dir, f["name"])
            # Create subdirectories if needed
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else output_dir, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as fh:
                fh.write(f["content"] + "\n")
            console.print(f"  [green]✓[/green] {filepath}")
            console.print(Syntax(f["content"], f["lang"], theme="monokai", padding=1, line_numbers=True))
            console.print()

        console.print(f"[bold green]{len(files)} files written to {output_dir}/[/bold green]\n")
    else:
        # No parseable files — just display the full response as markdown
        console.print()
        console.print(Panel.fit("[bold green]Infrastructure as Code[/bold green]", border_style="green"))
        console.print(Markdown(full_text))
        console.print()

    tracker.summary()

    # Build history summary
    file_names = [f["name"] for f in files] if files else []
    summary = f"Generated IaC: {request}."
    if file_names:
        summary += f" Files: {', '.join(file_names)}"
    return summary
