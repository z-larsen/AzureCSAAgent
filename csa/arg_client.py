"""Azure Resource Graph client — query execution against live Azure environments."""

import json
import os
import re

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from csa.progress import StepTracker
from csa.tokens import session as token_session

console = Console()

ARG_SYSTEM_PROMPT = """You are a senior Azure Cloud Solution Architect and Azure Resource Graph expert.

Given a natural language question about Azure resources, generate one or more valid KQL queries that help answer it. You are advisory — provide strategic guidance alongside the queries.

Response format:
- For simple, single-resource questions: output ONLY the KQL query (no markdown fences, no explanation)
- For complex or multi-faceted questions (migrations, assessments, architecture reviews): output multiple numbered queries with a brief heading for each, plus short advisory notes explaining the migration/assessment strategy. Use markdown headings (### 1. Title) and wrap each query in ``` fences.

CRITICAL — ARG property access rules:
- Resource properties are ALWAYS nested under `properties.` — never use bare field names
- CORRECT: properties.provisioningState, properties.addressSpace.addressPrefixes
- WRONG: provisioningState, addressSpace (these will fail with Operator_FailedToResolveEntity)
- Top-level columns that do NOT need `properties.` prefix: id, name, type, location, resourceGroup, subscriptionId, tenantId, kind, managedBy, sku, plan, tags, identity, zones
- To access nested objects, use dot notation: properties.ipConfigurations[0].properties.subnet.id
- Use `tostring()` or `todynamic()` when extracting nested values for projection
- Use `extend` to create friendly column names from deep paths before `project`

CRITICAL — mv-expand rules (arrays like securityRules, subnets, ipConfigurations):
- After `mv-expand`, the expanded element is a dynamic object — access its fields with dot notation from the alias
- After `mv-expand rule = properties.securityRules`, the inner fields are:
  rule.name, rule.properties.priority, rule.properties.access, rule.properties.direction, rule.properties.protocol
  NOT: securityRules.name, securityRules.properties.priority (unless you named the alias "securityRules")
- EVERY field you use in `project` MUST first be aliased with `extend`
  WRONG: project name, rule.properties.priority
  RIGHT: extend ruleName = rule.name, priority = rule.properties.priority | project name, ruleName, priority
- NSG security rules example:
  mv-expand rule = properties.securityRules
  | extend ruleName = rule.name, priority = toint(rule.properties.priority), access = tostring(rule.properties.access), direction = tostring(rule.properties.direction), protocol = tostring(rule.properties.protocol)
  | project nsgName = name, ruleName, priority, access, direction, protocol, resourceGroup, location, subscriptionId
- Subnets example:
  mv-expand subnet = properties.subnets
  | extend subnetName = tostring(subnet.name), subnetPrefix = tostring(subnet.properties.addressPrefix)
  | project vnetName = name, subnetName, subnetPrefix, resourceGroup, location, subscriptionId

Common resource patterns:
- Private endpoints: properties.privateLinkServiceConnections[0].properties.privateLinkServiceId, properties.customDnsConfigs (not customDnsConfigurations)
- VMs: properties.hardwareProfile.vmSize, properties.storageProfile.osDisk.osType
- VNets: properties.addressSpace.addressPrefixes, properties.subnets
- NICs: properties.ipConfigurations
- NSGs: properties.securityRules (use mv-expand pattern above)
- Disks: properties.diskSizeGB, properties.diskState

General rules:
- Use the Resources, ResourceContainers, or advisorresources tables as appropriate
- Use proper KQL syntax: where, extend, project, summarize, mv-expand, join
- Always include useful columns like name, resourceGroup, location, subscriptionId
- Limit results to 100 rows max unless the user asks for aggregations
- In `project`, NEVER use dotted paths like `properties.x.y` directly — always `extend` an alias first, then project the alias
  WRONG: project name, properties.addressSpace.addressPrefixes
  RIGHT: extend vnetPrefixes = tostring(properties.addressSpace.addressPrefixes) | project name, vnetPrefixes
- When using mv-expand on arrays, always extend aliases before project
- Wrap dynamic/array values in tostring() when projecting them

COST OPTIMIZATION — When the user asks about cost savings, FinOps, saving money, or reducing spend:
Generate a COMPREHENSIVE set of queries covering ALL three pillars of cost optimization:

1. **Rate optimization** (buy cheaper):
   - Azure Advisor cost recommendations: advisorresources | where type == "microsoft.advisor/recommendations" | where properties.category == "Cost"
     These contain: impactedField, impactedValue, shortDescription.solution, extendedProperties (savingsAmount, annualSavingsAmount, currentSku, targetSku, reservationScope, lookbackPeriod)
   - Advisor recommendations include: Reserved Instance purchases, VM right-sizing (with actual utilization %), shutdown candidates, savings plan suggestions
   
2. **Usage optimization** (use less):
   - Advisor "right-size or shutdown" recommendations have CPU utilization data in extendedProperties (MaxCpuP95, avgCpuP95)
   - Unattached/idle resources: managed disks with diskState == "Unattached", NICs not attached to VMs, public IPs not associated
   - App Service plans with 0 apps
   - Idle/stopped VMs still allocated (powerState != "deallocated" but low utilization per Advisor)
   
3. **Architecture optimization** (design better):
   - Over-provisioned resources (Advisor right-size recommendations)
   - Resources in premium tiers that could use standard (e.g., Premium SSD → Standard SSD per Advisor)
   - Storage accounts: check for lifecycle management policies, access tier opportunities

Key advisorresources query patterns:
```
advisorresources
| where type == "microsoft.advisor/recommendations"
| where properties.category == "Cost"
| extend impactedResource = tostring(properties.impactedValue),
         impact = tostring(properties.impact),
         problem = tostring(properties.shortDescription.problem),
         solution = tostring(properties.shortDescription.solution),
         savingsAmount = tostring(properties.extendedProperties.savingsAmount),
         annualSavings = tostring(properties.extendedProperties.annualSavingsAmount),
         savingsCurrency = tostring(properties.extendedProperties.savingsCurrency)
| project impactedResource, problem, solution, impact, savingsAmount, annualSavings, savingsCurrency, resourceGroup, subscriptionId
```

For right-sizing specifically:
```
advisorresources
| where type == "microsoft.advisor/recommendations"
| where properties.category == "Cost"
| where properties.shortDescription.problem has "right-size" or properties.shortDescription.problem has "underutilized"
| extend vm = tostring(properties.impactedValue),
         currentSku = tostring(properties.extendedProperties.currentSku),
         targetSku = tostring(properties.extendedProperties.targetSku),
         maxCpu = tostring(properties.extendedProperties.MaxCpuP95),
         avgCpu = tostring(properties.extendedProperties.avgCpuP95),
         savings = tostring(properties.extendedProperties.savingsAmount)
| project vm, currentSku, targetSku, maxCpu, avgCpu, savings, resourceGroup, subscriptionId
```

ALWAYS include the Advisor cost recommendations query when the topic is cost savings — it's the single most valuable data source because it contains actual utilization metrics and dollar amounts.
"""

ANALYSIS_SYSTEM_PROMPT = """You are a senior Azure Cloud Solution Architect with 25 years of experience.

Given a user's question and the Azure Resource Graph query results, provide a concise, actionable analysis. Your response should:

1. **Current State** — Summarize what the data shows about their environment
2. **Key Findings** — Call out anything notable: risks, misconfigurations, gaps, or strengths
3. **Recommendations** — Specific, prioritized next steps they should take
4. **Migration/Implementation Path** — If the question involves migration or new deployment, outline the phases

Keep it practical and direct. Use bullet points. Reference specific resources from the results by name.
Do NOT repeat the raw data. Do NOT pad with generic Azure marketing language.
If the data is insufficient to fully answer the question, say what additional queries or investigations would help.
"""


def get_client() -> ResourceGraphClient:
    credential = DefaultAzureCredential()
    return ResourceGraphClient(credential)


def _get_openai_client():
    """Return an (OpenAI-compatible client, deployment/model name) tuple, or (None, None)."""
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    azure_key = os.environ.get("AZURE_OPENAI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

    if endpoint:
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


def _extract_error(exc: Exception) -> str:
    """Pull a short, readable message from verbose Azure SDK exceptions."""
    msg = str(exc)
    # Azure errors nest "(Code) Message" patterns — grab the innermost InvalidQuery
    if "InvalidQuery" in msg:
        # Find the last "Query is invalid" message
        for line in msg.split("\n"):
            if "Query is invalid" in line:
                return "Query is invalid. Check column names and KQL syntax."
        return "InvalidQuery — check column names, aliases, and KQL syntax."
    # Truncate verbose Azure error chains
    if len(msg) > 300:
        first_line = msg.split("\n")[0][:300]
        return first_line
    return msg


def execute_query(query: str, subscriptions: list[str] | None = None) -> dict:
    """Execute an ARG query and return raw results."""
    client = get_client()
    request = QueryRequest(
        query=query,
        subscriptions=subscriptions or [],
    )
    response = client.resources(request)
    return {
        "count": response.count,
        "total_records": response.total_records,
        "data": response.data,
    }


def _extract_queries(response: str) -> list[dict]:
    """Extract individual KQL queries from a multi-query LLM response.

    Returns a list of dicts with 'title' and 'kql' keys.
    """
    queries = []
    # Find all fenced code blocks (```...```)
    blocks = re.findall(r"```(?:\w*)\n(.*?)```", response, re.DOTALL)
    if not blocks:
        return queries

    # Try to pair each block with a preceding heading
    lines = response.split("\n")
    block_idx = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("```") and block_idx < len(blocks):
            # Look backward for a heading
            title = f"Query {block_idx + 1}"
            for j in range(i - 1, max(i - 5, -1), -1):
                if lines[j].strip().startswith("#"):
                    title = re.sub(r"^#+\s*", "", lines[j].strip())
                    break
            queries.append({"title": title, "kql": blocks[block_idx].strip()})
            block_idx += 1
    return queries


def ask(question: str, history: list[dict] | None = None) -> str | None:
    """Convert a natural language question to an ARG query, execute it, and provide CSA analysis.

    Args:
        question: Natural language question about Azure resources.
        history: Conversation history (list of role/content dicts) for follow-up context.

    Returns:
        A brief summary of what was found (for appending to history), or None.
    """
    tracker = StepTracker("query")
    history = history or []

    console.print(f"\n[bold cyan]Question:[/bold cyan] {question}")

    # Generate KQL from natural language
    tracker.started("kql-generation")
    kql_response = _generate_kql(question, history)
    if not kql_response:
        return None
    tracker.progress("LLM generated KQL")
    tracker.done("kql-generation")

    # Check if the response contains multiple fenced queries (complex/advisory response)
    queries = _extract_queries(kql_response)

    if queries:
        # Multi-query advisory response — show plan, single Y/n, consolidated analysis
        console.print()
        console.print(Panel.fit("[bold yellow]Query Plan[/bold yellow]", border_style="yellow"))
        for idx, q in enumerate(queries):
            console.print(f"  [cyan]{idx + 1}.[/cyan] {q['title']}")
        console.print(f"\n  [dim]{len(queries)} queries will be executed against your environment[/dim]")

        # Estimate cost: ~1500 tokens per analysis call input, ~800 output
        from csa.tokens import _PRICING, _DEFAULT_PRICING
        model = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        pricing = _PRICING.get(model, _DEFAULT_PRICING)
        est_input = len(queries) * 200 + 2000  # queries are cheap, analysis is the big one
        est_output = 1500
        est_cost = (est_input * pricing["input"] + est_output * pricing["output"]) / 1_000_000
        console.print(f"  [dim]Estimated cost: ~${est_cost:.4f} ({model})[/dim]")

        console.print()
        run = console.input("[bold]Run all queries? [Y/n]:[/bold] ").strip().lower()
        if run in ("n", "no"):
            console.print("[dim]Skipped.[/dim]")
            return

        # Execute all queries, collect results
        all_results = []
        for idx, q in enumerate(queries):
            label = f"[{idx + 1}/{len(queries)}] {q['title']}"
            tracker.started("arg-execute")
            tracker.status(label)
            result = _execute_query_safe(question, q["kql"], tracker)
            if result and result["data"]:
                all_results.append({
                    "title": q["title"],
                    "kql": q["kql"],
                    "data": result["data"],
                    "count": result["count"],
                })
                console.print(f"  [green]✓[/green] {q['title']} — {result['count']} rows")
            else:
                console.print(f"  [yellow]⚠[/yellow] {q['title']} — no results")

        # Consolidated analysis across all results
        analysis_text = None
        if all_results:
            console.print()
            tracker.started("csa-analysis")
            tracker.status("running consolidated CSA analysis")
            analysis_text = _analyze_multi_results(question, all_results, history)
            tracker.progress("analysis complete")
            tracker.done("csa-analysis")

        tracker.summary()
        # Build history summary
        titles = [q["title"] for q in queries]
        summary = f"Ran {len(queries)} queries: {', '.join(titles)}."
        if analysis_text:
            # Keep first 500 chars of analysis for context
            summary += f" Analysis: {analysis_text[:500]}"
        return summary

    # Single-query response — original flow
    kql = kql_response
    console.print(f"\n[bold yellow]Generated KQL:[/bold yellow]")
    console.print(Syntax(kql, "sql", theme="monokai", padding=1))

    # Confirm before executing
    console.print()
    run = console.input("[bold]Execute this query? [Y/n]:[/bold] ").strip().lower()
    if run in ("n", "no"):
        console.print("[dim]Skipped.[/dim]")
        return

    analysis_text = _execute_and_analyze(question, kql, tracker, history)
    tracker.summary()
    summary = f"Queried Azure with KQL. "
    if analysis_text:
        summary += f"Analysis: {analysis_text[:500]}"
    return summary


def _execute_query_safe(question: str, kql: str, tracker: StepTracker) -> dict | None:
    """Execute a KQL query with auto-retry. Returns result dict or None."""
    try:
        result = execute_query(kql)
        tracker.done("arg-execute", f"{result['count']} rows")
        return result
    except Exception as e:
        error_msg = _extract_error(e)
        fixed_kql = _retry_kql(question, kql, error_msg)
        if not fixed_kql:
            tracker.done("arg-execute", "failed")
            return None
        try:
            result = execute_query(fixed_kql)
            tracker.done("arg-execute", f"{result['count']} rows (retried)")
            return result
        except Exception:
            tracker.done("arg-execute", "retry failed")
            return None


def _execute_and_analyze(question: str, kql: str, tracker: StepTracker, history: list[dict] | None = None) -> str | None:
    """Execute a single KQL query with auto-retry and optional CSA analysis."""
    tracker.started("arg-execute")
    try:
        result = execute_query(kql)
        tracker.progress(f"query returned {result['count']} rows")
    except Exception as e:
        error_msg = _extract_error(e)
        tracker.status("query error — attempting auto-fix")
        fixed_kql = _retry_kql(question, kql, error_msg)
        if not fixed_kql:
            console.print(f"[red]Could not fix query: {error_msg}[/red]")
            return
        kql = fixed_kql
        tracker.progress("LLM corrected KQL")
        console.print(f"\n[bold yellow]Corrected KQL:[/bold yellow]")
        console.print(Syntax(kql, "sql", theme="monokai", padding=1))
        try:
            result = execute_query(kql)
            tracker.progress(f"retry returned {result['count']} rows")
        except Exception as e2:
            console.print(f"[red]Retry also failed: {_extract_error(e2)}[/red]")
            return

    tracker.done("arg-execute", f"{result['count']} rows")

    console.print(f"\n[green]✓ Returned {result['count']} rows[/green]\n")
    if isinstance(result["data"], list) and result["data"]:
        _print_table(result["data"])
        tracker.started("csa-analysis")
        tracker.status("running CSA analysis on results")
        analysis_text = _analyze_results(question, kql, result["data"], history)
        tracker.progress("analysis complete")
        tracker.done("csa-analysis")
        return analysis_text
    elif result["data"]:
        console.print(result["data"])
    else:
        console.print("[dim]No results returned.[/dim]")
    return None


def _generate_kql(question: str, history: list[dict] | None = None) -> str | None:
    """Use Azure OpenAI or OpenAI to generate KQL from a question."""
    client, model = _get_openai_client()
    if not client:
        return None

    messages = [{"role": "system", "content": ARG_SYSTEM_PROMPT}]
    # Include conversation history for follow-up context
    if history:
        messages.extend(history[-10:])  # last 10 exchanges to stay in context window
    messages.append({"role": "user", "content": question})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
            max_tokens=2000,
        )
        token_session.record(response.usage, model, "KQL generation")
        return response.choices[0].message.content.strip()
    except Exception as e:
        console.print(f"[red]LLM error generating KQL: {e}[/red]")
        return None


def _retry_kql(question: str, failed_kql: str, error_msg: str) -> str | None:
    """Ask the LLM to fix a failed KQL query based on the error message."""
    client, model = _get_openai_client()
    if not client:
        return None

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": ARG_SYSTEM_PROMPT},
                {"role": "user", "content": question},
                {"role": "assistant", "content": failed_kql},
                {"role": "user", "content": f"That query failed with this error:\n{error_msg}\n\nFix the query. Remember: resource properties must be accessed via `properties.` prefix (e.g. properties.provisioningState, not provisioningState). Output ONLY the corrected KQL."},
            ],
            temperature=0,
            max_tokens=500,
        )
        token_session.record(response.usage, model, "KQL retry")
        return response.choices[0].message.content.strip()
    except Exception as e:
        console.print(f"[red]LLM error during retry: {e}[/red]")
        return None


def _analyze_results(question: str, kql: str, data: list[dict], history: list[dict] | None = None) -> str | None:
    """Run a second LLM pass to analyze ARG results with CSA expertise."""
    client, model = _get_openai_client()
    if not client:
        return None

    # Truncate data for context window — send up to 30 rows
    sample = data[:30]
    data_summary = json.dumps(sample, indent=2, default=str)
    if len(data) > 30:
        data_summary += f"\n\n... ({len(data) - 30} additional rows not shown)"

    user_msg = f"""**User's Question:** {question}

**KQL Query Used:**
```kql
{kql}
```

**Query Results ({len(data)} rows):**
```json
{data_summary}
```

Analyze these results and provide your CSA assessment."""

    console.print()
    console.print(Panel.fit("[bold magenta]CSA Analysis[/bold magenta]", border_style="magenta"))

    messages = [{"role": "system", "content": ANALYSIS_SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-6:])  # recent context for follow-ups
    messages.append({"role": "user", "content": user_msg})

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=1500,
            stream=True,
            stream_options={"include_usage": True},
        )

        # Collect streamed chunks then render as markdown
        full_text = ""
        usage = None
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                full_text += chunk.choices[0].delta.content
            if hasattr(chunk, "usage") and chunk.usage:
                usage = chunk.usage

        console.print(Markdown(full_text))
        console.print()
        token_session.record(usage, model, "CSA analysis")
        return full_text
    except Exception as e:
        console.print(f"[red]Analysis error: {e}[/red]")
        return None


def _analyze_multi_results(question: str, results: list[dict], history: list[dict] | None = None) -> str | None:
    """Run a single consolidated LLM analysis across multiple query results."""
    client, model = _get_openai_client()
    if not client:
        return None

    # Build a combined data summary — limit each query to 15 rows to fit context
    sections = []
    for r in results:
        sample = r["data"][:15]
        data_str = json.dumps(sample, indent=2, default=str)
        if len(r["data"]) > 15:
            data_str += f"\n... ({len(r['data']) - 15} additional rows not shown)"
        sections.append(
            f"### {r['title']} ({r['count']} rows)\n"
            f"```kql\n{r['kql']}\n```\n"
            f"```json\n{data_str}\n```"
        )

    combined = "\n\n".join(sections)

    user_msg = f"""**User's Question:** {question}

The following queries were executed against the user's Azure environment:

{combined}

Provide a **single consolidated assessment** that:
1. Synthesizes findings across ALL query results — do not analyze each query separately
2. Orders recommendations by **priority** (critical risks first, then improvements, then nice-to-haves)
3. Identifies gaps, risks, and strengths in their current environment
4. Provides a clear **action plan** with specific next steps
5. If the question involves migration or transformation, outline phases with dependencies

Be direct and actionable. Reference specific resources by name from the results."""

    console.print()
    console.print(Panel.fit("[bold magenta]Consolidated CSA Analysis[/bold magenta]", border_style="magenta"))

    messages = [{"role": "system", "content": ANALYSIS_SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": user_msg})

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=3000,
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

        console.print(Markdown(full_text))
        console.print()
        token_session.record(usage, model, "Consolidated analysis")
        return full_text
    except Exception as e:
        console.print(f"[red]Analysis error: {e}[/red]")
        return None


def _print_table(rows: list[dict]):
    """Render a list of dicts as a Rich table."""
    if not rows:
        return
    columns = list(rows[0].keys())
    table = Table(show_lines=False, border_style="dim")
    for col in columns:
        table.add_column(col, style="cyan", overflow="fold")
    for row in rows[:50]:
        table.add_row(*[str(row.get(col, "")) for col in columns])
    console.print(table)
    if len(rows) > 50:
        console.print(f"[dim]... {len(rows) - 50} more rows not shown[/dim]")
