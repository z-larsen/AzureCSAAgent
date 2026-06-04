# Skill: IaC Scaffolding with Azure Verified Modules

Scaffold infrastructure-as-code that is built on **Azure Verified Modules (AVM)** — Microsoft's curated, tested, WAF-aligned module library — for both Bicep and Terraform. This skill governs *how* the agent generates IaC: it asks the user's language preference when it isn't obvious, prefers AVM modules over hand-rolled resources, composes custom IaC on top of AVM, and handles greenfield (new landing zone) and brownfield (existing/imported estate) differently. Pairs with `azure-enterprise-infra-planner` (which decides the *architecture*) and `azure-validate` (which checks the result before deploy).

The agent has the tools to do this well: `bicep/list_avm_metadata`, `azure_get_azure_verified_module`, `bicep/get_az_resource_type_schema`, `bicep/get_bicep_best_practices`, `azure-mcp/azureterraformbestpractices`, and `bicep/get_bicep_file_diagnostics`. Use them — don't guess module names or versions.

## Trigger Phrases
- "scaffold IaC" / "generate Bicep" / "generate Terraform"
- "Azure Verified Modules" / "AVM"
- "build a landing zone with IaC"
- "convert this design to Bicep/Terraform"
- "use verified modules"
- "module structure" / "IaC repo structure"
- "import existing resources to Terraform/Bicep"
- "brownfield IaC"

## Step 0 — Ask the language preference (when not obvious)
Before scaffolding, determine Bicep vs Terraform. Infer first, then confirm:
- **Infer** from the repo: existing `*.bicep`/`bicepconfig.json` → Bicep; `*.tf`/`backend.hcl`/`.terraform` → Terraform; existing `azure.yaml`/azd → Bicep-leaning.
- **If ambiguous, ask** — and frame the trade-off so the user chooses well:
  - **Bicep** — Azure-native, no state file to manage, day-0 support for new resource types, tight `what-if`, best when the estate is Azure-only and the team is Microsoft-centric.
  - **Terraform** — multi-cloud, mature module/registry ecosystem, explicit state (and state-management burden), strong for teams already standardized on HashiCorp or spanning clouds.
- Respect an existing repo convention even if you'd personally pick the other; don't mix both for the same workload without a reason.

## Part A — Azure Verified Modules (AVM) foundation

### 1. What AVM is and why to prefer it
- AVM = Microsoft-owned, tested, versioned modules that bake in WAF best practices, sane defaults, diagnostic settings, RBAC, and private-endpoint support
- Two flavors:
  - **Resource modules** — one well-architected resource (e.g. a storage account, key vault, VNet) with all the knobs and good defaults
  - **Pattern modules** — multi-resource architectures (e.g. hub-spoke, a landing-zone vending pattern) composed from resource modules
- Prefer AVM over hand-rolled resources unless a needed property isn't yet exposed (then wrap or extend, don't abandon AVM)

### 2. Finding and pinning modules
- Discover with `bicep/list_avm_metadata` / `azure_get_azure_verified_module`; confirm the resource type with `bicep/get_az_resource_type_schema`
- **Always pin versions** — Bicep: pull from the public registry `br/public:avm/res/<service>/<resource>:<version>`; Terraform: `source = "Azure/avm-res-<service>-<resource>/azurerm"` with an explicit `version`
- Never float to latest in production IaC — pin and bump deliberately

### 3. Composing custom IaC on top of AVM (the key pattern)
- Treat AVM modules as building blocks; your repo is the *composition layer* that wires them together with your naming, tagging, networking, and policy decisions
- Pass org standards down as inputs: naming convention, required tags, Log Analytics workspace id (for diagnostic settings), private DNS zone ids, RBAC assignments
- Add a thin local module only for genuinely org-specific glue AVM doesn't cover — keep it minimal so AVM upgrades stay easy
- Centralize shared values (workspace id, DNS zones, mgmt group ids) so spokes/workloads consume them consistently

## Part B — Greenfield: new landing zone
- For full **Azure Landing Zone** scaffolding, start from the accelerators rather than from scratch:
  - **Bicep** — ALZ Bicep / the AVM ALZ pattern modules (management groups, policies, hub networking, subscription vending)
  - **Terraform** — the AVM ALZ Terraform modules (`Azure/avm-ptn-alz`, management-group + policy modules, `caf-enterprise-scale` lineage)
- Layer the platform: management groups + policy → connectivity (hub/vWAN) → identity → management (Log Analytics, automation) → then workload (application) landing zones via subscription vending
- Repo structure: separate state/deployment boundaries per layer (platform vs each landing zone), shared modules referenced by version

## Part C — Brownfield: existing estate
Brownfield is where IaC projects get painful — set expectations honestly.
- **Import, don't recreate** — bring existing resources under IaC management without destroying them:
  - **Terraform** — `import` blocks (or `terraform import`); generate config, then reconcile drift; expect manual cleanup of the generated HCL
  - **Bicep** — decompile existing ARM (`bicep/decompile_arm_template_file`) as a starting point; Bicep has no native stateful import, so you target existing resources and rely on `what-if` to confirm no destructive change
- **Drift reconciliation** — run `what-if` / `plan` and read it carefully; the goal is a *no-op* plan against current state before you change anything
- **Gotchas:** generated/decompiled code is rarely clean (hardcoded values, missing modularization); secrets and data-plane config often aren't represented; some properties are read-only post-create. Budget time to refactor imported code toward AVM rather than freezing the raw export.
- Migration path: import as-is → get a clean no-op plan → incrementally refactor resources to AVM modules one at a time, validating with `what-if`/`plan` at each step

## Part D — Validate before declaring done
- Bicep: `bicep build` + `bicep/get_bicep_file_diagnostics` + `az deployment ... what-if`
- Terraform: `terraform validate` + `terraform plan`
- Hand off to `azure-validate` for the full pre-deployment preflight (RBAC, identity permissions, destructive-change review)

## Follow-Up Questions
- "Bicep or Terraform? I see [signals] in the repo — want me to follow that, or do you have a different preference for this work?"
- "Greenfield landing zone or are we bringing an existing estate under IaC? Brownfield means import + drift reconciliation, which changes the approach."
- "Do you have org standards I should thread through the AVM modules — naming convention, required tags, central Log Analytics workspace, private DNS zones?"
- "For brownfield: are you OK with a phased refactor toward AVM, or do you need everything under management first and cleanup later?"

## Output Format
- **Language decision** — Bicep or Terraform, with the one-line rationale
- **Module plan** — which AVM resource/pattern modules, pinned versions, and the composition/glue layer
- **Repo structure** — folder/layer layout (platform vs landing zones vs workloads), state boundaries
- **Scaffolded IaC** — generated files using pinned AVM modules with org inputs threaded through
- **Brownfield plan** (if applicable) — import sequence, drift-reconciliation steps, phased AVM-refactor path
- **Validation** — the exact build/plan/what-if commands to run, then hand to `azure-validate`
- **References** — AVM registry pages, ALZ accelerator docs, Bicep/Terraform best-practice Learn links

Save scaffolded code under the user's repo; save the plan to `outputs/<customer-or-topic>/iac-scaffold-plan.md`
