# Azure CSA Agent

A senior Azure Cloud Solution Architect agent that runs advisory assessments against live Azure environments using Azure Resource Graph, with optional natural language query support powered by Azure OpenAI.

```
 █████╗ ███████╗██╗   ██╗██████╗ ███████╗
██╔══██╗╚══███╔╝██║   ██║██╔══██╗██╔════╝
███████║  ███╔╝ ██║   ██║██████╔╝█████╗
██╔══██║ ███╔╝  ██║   ██║██╔══██╗██╔══╝
██║  ██║███████╗╚██████╔╝██║  ██║███████╗
╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝

 ☁  Cloud Solution Architect Agent
 Advisory Only  │  WAF Aligned
```

## What it does

- **Pre-built assessments** — Run general, FinOps, network, landing zone, and WAF assessments against any subscription
- **Natural language queries** — Ask questions in plain English ("show me untagged VMs"), get KQL generated, executed, and analyzed
- **CSA analysis** — After running queries, a second LLM pass provides structured findings, risks, and recommendations
- **VS Code chat mode** — Use as a Copilot chat mode with Azure MCP Server for interactive architecture conversations

## Three ways to use it

| Path | LLM Provider | Dependencies | Cost |
|------|-------------|--------------|------|
| [**VS Code Chat Mode**](#path-1-vs-code-chat-mode) | GitHub Copilot | Copilot license + MCP extension | Included with Copilot |
| [**CLI — Assessments only**](#path-2-cli--assessments-only) | None | Python 3.11+ + `az login` | Free |
| [**CLI — Full natural language**](#path-3-cli--full-natural-language) | Azure OpenAI (your deployment) | Python 3.11+ + `az login` + Azure OpenAI resource | ~$0.01/query |

---

## Path 1: VS Code Chat Mode

Use the agent as a GitHub Copilot chat mode with full Azure Resource Graph access. No Azure OpenAI deployment needed — Copilot provides the LLM.

### Prerequisites

- [VS Code](https://code.visualstudio.com/) with [GitHub Copilot](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot) extension
- [Azure MCP Server](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azure-mcp-server) extension (provides ARG query tools)
- Azure CLI authenticated: `az login`

### Setup

1. Clone the repo:

   ```bash
   git clone https://github.com/z-larsen/AzureCSAAgent.git
   ```

2. Open the folder in VS Code

3. Install the **Azure MCP Server** extension from the VS Code marketplace

4. The chat mode appears automatically in the Copilot chat mode picker — select **Azure CSA**

### What you get

- Interactive chat with a senior Azure CSA persona
- Live ARG queries against your environment (generate → validate → execute)
- Microsoft Learn documentation search and fetch
- Built-in skills for FinOps, Landing Zone, Network, and WAF assessments
- Assessment reports saved to `outputs/`

---

## Path 2: CLI — Assessments only

Run pre-built assessment queries from the terminal. No LLM needed — uses hardcoded KQL queries against Azure Resource Graph.

### Prerequisites

- Python 3.11+
- Azure CLI authenticated: `az login`

### Install

```bash
git clone https://github.com/z-larsen/AzureCSAAgent.git
cd AzureCSAAgent
pip install -e .
```

### Usage

Launch the interactive REPL:

```bash
azure-csa
```

Run assessments by type:

```
azure-csa> assess <subscription-id>
azure-csa> assess <subscription-id> -t finops
azure-csa> assess <subscription-id> -t network
azure-csa> assess <subscription-id> -t landing-zone
azure-csa> assess <subscription-id> -t waf
```

Or run directly without the REPL:

```bash
azure-csa assess <subscription-id> -t finops -o outputs
```

### Assessment types

| Type | What it checks |
|------|----------------|
| `general` | Resource inventory, untagged resources, public IPs, Advisor cost recommendations |
| `finops` | Resource counts, orphaned disks, VMs without Azure Hybrid Benefit, Advisor cost recs |
| `network` | VNets, public IPs, NSG rules (overly permissive), private endpoints |
| `landing-zone` | Management group hierarchy, resource counts, tagging, VNet topology |
| `waf` | Resource inventory, public IPs, NSG rules, orphaned disks, Advisor cost recs |

Reports are saved as markdown to `outputs/<type>-assessment.md`.

---

## Path 3: CLI — Full natural language

Ask questions in plain English. The agent generates KQL, shows it for confirmation, executes against ARG, displays results, and then provides a structured CSA analysis.

### Prerequisites

- Everything from [Path 2](#path-2-cli--assessments-only)
- An Azure OpenAI resource with a GPT-4o deployment

### Deploy Azure OpenAI

1. Create the resource and deploy a model:

   ```bash
   # Create a resource group (or use an existing one)
   az group create --name rg-azure-csa --location centralus

   # Create the Azure OpenAI resource
   az cognitiveservices account create \
     --name <your-openai-name> \
     --resource-group rg-azure-csa \
     --location centralus \
     --kind OpenAI \
     --sku S0 \
     --custom-domain <your-openai-name>

   # Deploy GPT-4o
   az cognitiveservices account deployment create \
     --name <your-openai-name> \
     --resource-group rg-azure-csa \
     --deployment-name gpt-4o \
     --model-name gpt-4o \
     --model-version 2024-11-20 \
     --model-format OpenAI \
     --sku-capacity 10 \
     --sku-name GlobalStandard
   ```

2. Grant yourself access (uses your `az login` identity — no API keys needed):

   ```bash
   # Get your user ID and the resource ID
   USER_ID=$(az ad signed-in-user show --query id -o tsv)
   RESOURCE_ID=$(az cognitiveservices account show \
     --name <your-openai-name> \
     --resource-group rg-azure-csa \
     --query id -o tsv)

   # Assign the role
   az role assignment create \
     --assignee $USER_ID \
     --role "Cognitive Services OpenAI User" \
     --scope $RESOURCE_ID
   ```

   > **Note:** RBAC propagation can take up to 10 minutes.

3. Set environment variables:

   ```bash
   # Linux/macOS
   export AZURE_OPENAI_ENDPOINT=https://<your-openai-name>.openai.azure.com
   export AZURE_OPENAI_DEPLOYMENT=gpt-4o

   # Windows (PowerShell)
   $env:AZURE_OPENAI_ENDPOINT = "https://<your-openai-name>.openai.azure.com"
   $env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o"

   # Windows (CMD)
   set AZURE_OPENAI_ENDPOINT=https://<your-openai-name>.openai.azure.com
   set AZURE_OPENAI_DEPLOYMENT=gpt-4o
   ```

### Usage

```
azure-csa> show me untagged resources by type
azure-csa> I need to do a network review in order to deploy a vWAN
azure-csa> query "which VMs are not using Azure Hybrid Benefit"
azure-csa> what public IPs are unattached
```

The flow for each query:

1. **Generates KQL** from your question (shown with syntax highlighting)
2. **Asks for confirmation** before executing
3. **Displays results** in a formatted table
4. **CSA Analysis** — a second LLM pass provides: Current State, Key Findings, Recommendations, and Migration/Implementation Path

### Authentication

The agent uses `DefaultAzureCredential` for both ARG queries and Azure OpenAI. This means your `az login` session handles everything — no API keys in environment variables.

If you prefer an API key instead:

```bash
export AZURE_OPENAI_ENDPOINT=https://<your-openai-name>.openai.azure.com
export AZURE_OPENAI_API_KEY=<your-key>
```

---

## Project structure

```
├── .github/
│   ├── copilot-instructions.md        # Global Copilot context
│   ├── agents/
│   │   └── azure-csa.agent.md         # VS Code subagent definition
│   ├── prompts/
│   │   └── azure-csa.prompt.md        # VS Code chat mode
│   └── skills/
│       ├── finops-assessment/         # FinOps maturity & cost optimization
│       ├── landing-zone-assessment/   # CAF landing zone alignment
│       ├── network-review/            # Network topology & security
│       └── well-architected-review/   # WAF five-pillar review
├── csa/
│   ├── __init__.py
│   ├── arg_client.py                  # ARG client + natural language → KQL + analysis
│   ├── assessments.py                 # Pre-built assessment runner
│   └── cli.py                         # Interactive CLI with REPL
├── tests/
│   └── test_assessments.py
├── pyproject.toml
└── .gitignore
```

## VS Code skills reference

The chat mode includes skills for structured assessments. These are automatically available when using the VS Code chat mode:

| Skill | Purpose |
|-------|---------|
| `finops-assessment` | FinOps maturity, cost optimization, tag coverage, commitment discounts |
| `landing-zone-assessment` | CAF alignment, management group structure, policy coverage |
| `network-review` | VNet topology, private endpoints, DNS, NSG audit, hybrid connectivity |
| `well-architected-review` | All five WAF pillars with per-pillar scorecards |

The chat mode also picks up 14 additional Azure skills (compliance, diagnostics, kubernetes, cost, etc.) when available in the user's VS Code environment.

## License

MIT
