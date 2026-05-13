"""Azure Resource Graph client — query execution against live Azure environments."""

import json
import os

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

console = Console()

ARG_SYSTEM_PROMPT = """You are an Azure Resource Graph (ARG) query expert. Given a natural language question about Azure resources, generate a valid KQL query that answers it.

Rules:
- Output ONLY the KQL query, no explanation, no markdown fences
- Use the Resources, ResourceContainers, or advisorresources tables as appropriate
- Use proper KQL syntax: where, extend, project, summarize, mv-expand, join
- For networking: microsoft.network/virtualnetworks, microsoft.network/virtualwan, microsoft.network/virtualhubs, etc.
- For compute: microsoft.compute/virtualmachines, microsoft.compute/disks
- For storage: microsoft.storage/storageaccounts
- Always include useful columns like name, resourceGroup, location, subscriptionId
- Limit results to 100 rows max unless the user asks for aggregations
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
        console.print("[yellow]No LLM backend configured.[/yellow]")
        console.print("[dim]Set AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_DEPLOYMENT (uses DefaultAzureCredential)[/dim]")
        console.print("[dim]  or AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY[/dim]")
        console.print("[dim]  or OPENAI_API_KEY[/dim]")
        return None, None


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


def ask(question: str):
    """Convert a natural language question to an ARG query, execute it, and provide CSA analysis."""
    console.print(f"\n[bold cyan]Question:[/bold cyan] {question}")

    # Generate KQL from natural language
    kql = _generate_kql(question)
    if not kql:
        return

    console.print(f"\n[bold yellow]Generated KQL:[/bold yellow]")
    console.print(Syntax(kql, "sql", theme="monokai", padding=1))

    # Confirm before executing
    console.print()
    run = console.input("[bold]Execute this query? [Y/n]:[/bold] ").strip().lower()
    if run in ("n", "no"):
        console.print("[dim]Skipped.[/dim]")
        return

    # Execute
    try:
        result = execute_query(kql)
        console.print(f"\n[green]Returned {result['count']} rows[/green]\n")
        if isinstance(result["data"], list) and result["data"]:
            _print_table(result["data"])
            # Analyze results with CSA expertise
            _analyze_results(question, kql, result["data"])
        elif result["data"]:
            console.print(result["data"])
        else:
            console.print("[dim]No results returned.[/dim]")
    except Exception as e:
        console.print(f"[red]Query failed: {e}[/red]")


def _generate_kql(question: str) -> str | None:
    """Use Azure OpenAI or OpenAI to generate KQL from a question."""
    client, model = _get_openai_client()
    if not client:
        return None

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": ARG_SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            temperature=0,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        console.print(f"[red]LLM error generating KQL: {e}[/red]")
        return None


def _analyze_results(question: str, kql: str, data: list[dict]):
    """Run a second LLM pass to analyze ARG results with CSA expertise."""
    client, model = _get_openai_client()
    if not client:
        return

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

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=1500,
            stream=True,
        )

        # Collect streamed chunks then render as markdown
        full_text = ""
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                full_text += chunk.choices[0].delta.content

        console.print(Markdown(full_text))
        console.print()
    except Exception as e:
        console.print(f"[red]Analysis error: {e}[/red]")


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
