# Skill: Azure AI Foundry, Tokenomics & Automation Advisory

Mentor and architect on Azure AI initiatives — Microsoft Foundry (project/hub) architecture, model deployment models, **tokenomics** (cost and throughput economics of LLM workloads), RAG and agent patterns, responsible-AI controls, and a structured **Automation Opportunity Assessment** for deciding whether a task is worth automating and with what (Logic Apps, Functions, or an AI agent). The agent has the `azure-mcp/foundry` and `azure-mcp/foundryextensions` tools and Microsoft Learn for grounding current models, SKUs, and pricing — always verify model names, quotas, and prices against Learn before quoting numbers.

## Trigger Phrases
- "AI architecture" / "design an AI solution"
- "Azure AI Foundry" / "Foundry project" / "AI hub"
- "deploy a model" / "model deployment options"
- "tokenomics" / "token cost" / "LLM cost model"
- "PTU vs pay-as-you-go" / "provisioned throughput"
- "RAG architecture" / "retrieval augmented generation"
- "AI agent design" / "agentic workflow"
- "content safety" / "responsible AI"
- "is this automatable" / "should we automate this"
- "automation opportunity" / "can this be automated"
- "GPT cost estimate" / "tokens per month"

## Part A — Foundry & AI Solution Architecture

### 1. Foundry Resource Topology
- **Foundry project vs hub** — when a single project suffices vs a hub with multiple projects sharing connections, compute, and governance
- Connections — Azure OpenAI/Foundry Models, AI Search, Storage, Key Vault, and how they're shared
- Network isolation — public, managed VNet, or private endpoints (private is the enterprise default for regulated workloads)
- Identity — managed identity for the project to reach Search/Storage/Key Vault (avoid keys)
- Region selection — model availability varies by region; verify the target model is offered where the project lives

### 2. Model Deployment Models (the core decision)
| Option | When to use | Cost model | Trade-off |
|--------|-------------|------------|-----------|
| **Serverless / Standard (pay-as-you-go)** | Variable or low/spiky traffic, prototypes, multi-model experimentation | Per-token (input + output) | No latency/throughput guarantee; subject to shared quota and 429s |
| **Provisioned Throughput (PTU)** | Steady, high-volume, latency-sensitive production | Fixed hourly per PTU (reserve monthly/yearly for discount) | Pay for reserved capacity whether used or not; must size correctly |
| **Managed compute (real-time endpoint)** | Open/custom models, fine-tuned weights you host | Per-VM-hour (GPU SKU) | You own scaling, patching, idle cost |
| **Batch** | Async, non-interactive bulk jobs | Discounted per-token | Not for interactive latency |

- Always ask: *steady or spiky traffic? latency-sensitive? open or frontier model? fine-tuned?* — those four answers pick the deployment model.

### 3. RAG & Knowledge Architecture
- Chunking strategy, embedding model choice, vector store (AI Search vs Cosmos DB vs PostgreSQL pgvector)
- Hybrid (vector + keyword) + semantic ranker for retrieval quality
- Grounding to reduce hallucination; citation surfacing
- Data freshness / indexing pipeline (push vs pull, incremental)

### 4. Agentic Patterns
- Single-agent vs multi-agent orchestration; tool/function calling
- Foundry Agent Service vs self-hosted (Semantic Kernel / Agent Framework)
- State, memory, and thread management; human-in-the-loop checkpoints
- Evaluation and tracing (groundedness, relevance, safety) — continuous eval in production

### 5. Responsible AI & Governance
- Azure AI Content Safety (prompt shields, jailbreak detection, protected material, groundedness)
- Data residency and "your data stays yours" posture; no-training guarantees
- Prompt/response logging vs privacy; PII handling
- Cost guardrails (quota, budget alerts on the AI resource)

## Part B — Tokenomics (cost & throughput economics)

This is where most AI projects get budgeting wrong. Walk the user through the math explicitly.

### 1. Cost Model Fundamentals
- Cost = **(input tokens × input price) + (output tokens × output price)** per call; output is usually 3–4× the input price — output length dominates cost
- Estimate tokens: ~4 characters/token (English); a RAG call = system prompt + retrieved context + user query (input) + completion (output). Context injection is often the silent cost driver.
- Monthly cost ≈ calls/month × (avg input tokens × in-price + avg output tokens × out-price)

### 2. PTU vs Pay-as-you-go Break-even
- PTU is fixed hourly capacity; PAYG is per-token. Break-even = the sustained TPM at which PTU's hourly cost ÷ effective tokens-per-hour beats the PAYG per-token rate.
- Rule of thumb: **high, steady utilization → PTU wins; spiky or < ~50% duty cycle → PAYG wins.** Reserve PTU (monthly/annual) only once steady-state demand is proven.
- Always model both lines and show the crossover; recommend starting PAYG, instrumenting real token usage, then sizing PTU from observed P95 throughput.

### 3. Throughput Planning (TPM / RPM)
- Quota is enforced as **tokens-per-minute (TPM)** and **requests-per-minute (RPM)**; a deployment can 429 on either
- Size TPM from: peak concurrent users × calls/user/min × tokens/call
- Mitigations for 429s: retry-with-backoff, multiple deployments + load balancing (APIM as AI gateway), PTU for guaranteed throughput, smaller/cheaper model for cheap paths

### 4. Cost Reduction Levers (in order of impact)
1. **Right-size the model** — use a smaller/cheaper model for simple tasks; reserve frontier models for hard ones (model routing)
2. **Cut output tokens** — constrain `max_tokens`, ask for terse output, stream
3. **Trim context** — better retrieval (fewer, higher-relevance chunks) beats dumping more context
4. **Cache** — prompt caching / semantic caching at the gateway for repeated queries
5. **Batch** the async, non-interactive workloads for the discount
6. **PTU** once volume is steady and proven

### 5. Deliverable: a token cost model
When asked to estimate, produce a small table: scenario (low/expected/high) × calls/month × avg in/out tokens × unit prices → monthly cost, plus the PTU break-even point and the top 3 levers to pull. Verify current prices via Microsoft Learn / `azure-mcp/pricing` first.

## Part C — Automation Opportunity Assessment

Use this whenever a recurring task surfaces in conversation ("could this be automated?"). Run the decision framework, don't just say yes.

### 1. Qualify the task (the five questions)
- **Frequency** — how often does it run? (rare one-offs rarely pay back automation)
- **Volume & time** — how long does it take manually × how many times = annual hours
- **Determinism** — is it rule-based (deterministic) or judgment-based (probabilistic)?
- **Stability** — does the process change often? (volatile processes break brittle automation)
- **Risk/blast radius** — what's the cost of the automation doing it wrong unattended?

### 2. Pick the right automation tool
| Task shape | Recommended approach |
|------------|----------------------|
| Deterministic, event/schedule-driven, system-to-system glue | **Logic Apps** (low-code connectors) or **Power Automate** |
| Deterministic, custom code, compute logic | **Azure Functions** (serverless) |
| Infra provisioning / config | **IaC** (Bicep/Terraform) + pipeline — defer to `azure-iac-avm` |
| Judgment, language understanding, unstructured input | **AI agent** (Foundry Agent Service / Agent Framework) |
| Hybrid (mostly rules + a judgment step) | Functions/Logic Apps **with an AI call** at the judgment point — usually the most cost-effective |

### 3. The ROI gut-check
- Annual hours saved × loaded hourly rate − (build cost + run cost + maintenance) = net value
- **Recommend NOT automating** when: low frequency, high process volatility, high error-cost with no human-in-loop, or build cost exceeds a ~12-month payback. Say so plainly — a good mentor protects the user from automating the wrong thing.
- Prefer the **simplest tool that works** — don't reach for an AI agent when a Logic App connector does it deterministically and cheaper.

### 4. Output
- A one-page automation brief: task, frequency/volume, automatability verdict, recommended tool + why, rough build effort, estimated run cost (including tokenomics if AI is involved), and a go/no-go recommendation.

## Follow-Up Questions
- "Is the traffic steady or spiky, and is it latency-sensitive? That decides PAYG vs PTU before we touch model choice."
- "What's the expected calls/month and rough input/output length? I'll build a token cost model and show the PTU break-even."
- "For this automation — how often does it run and what's the cost if it gets it wrong unattended? That decides Logic App vs Function vs AI agent vs leave-it-manual."
- "Does this need a frontier model, or would a smaller/cheaper model handle most of the load with routing?"

## Output Format
- **AI Architecture** — Foundry topology, deployment-model decision, RAG/agent pattern, RAI controls, network posture
- **Tokenomics** — token cost model (low/expected/high), PTU break-even, throughput (TPM/RPM) sizing, prioritized cost levers
- **Automation Brief** (when applicable) — automatability verdict + recommended tool + ROI gut-check + go/no-go
- **References** — Microsoft Learn links (Foundry, model deployment, content safety, pricing) — verify current pricing before quoting

Save to `outputs/<customer-or-topic>/ai-foundry-advisory.md`
