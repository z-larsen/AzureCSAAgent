"""CLI entrypoint for the Azure CSA agent."""

import random
from importlib.metadata import version as pkg_version

import typer
from rich.console import Console
from rich.panel import Panel

from csa.tokens import session as token_session

console = Console()

try:
    __version__ = pkg_version("azure-csa-agent")
except Exception:
    __version__ = "1.1.0"

BANNER = r"""
[bold cyan] █████╗ ███████╗██╗   ██╗██████╗ ███████╗     ██████╗███████╗ █████╗ [/bold cyan]
[bold cyan]██╔══██╗╚══███╔╝██║   ██║██╔══██╗██╔════╝    ██╔════╝██╔════╝██╔══██╗[/bold cyan]
[bold cyan]███████║  ███╔╝ ██║   ██║██████╔╝█████╗      ██║     ███████╗███████║[/bold cyan]
[bold cyan]██╔══██║ ███╔╝  ██║   ██║██╔══██╗██╔══╝      ██║     ╚════██║██╔══██║[/bold cyan]
[bold cyan]██║  ██║███████╗╚██████╔╝██║  ██║███████╗    ╚██████╗███████║██║  ██║[/bold cyan]
[bold cyan]╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝     ╚═════╝╚══════╝╚═╝  ╚═╝[/bold cyan]
[bold cyan]                 █████╗  ██████╗ ███████╗███╗   ██╗████████╗            [/bold cyan]
[bold cyan]                ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝            [/bold cyan]
[bold cyan]                ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║               [/bold cyan]
[bold cyan]                ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║               [/bold cyan]
[bold cyan]                ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║               [/bold cyan]
[bold cyan]                ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝               [/bold cyan]
""" + f"""
[bold white]☁  Cloud Solution Architect Agent[/bold white]  [dim]v{__version__}[/dim]
"""

HELP_TEXT = """
[bold yellow]Try something like:[/bold yellow]
  [green]"help me reduce costs by $500 this month"[/green]
  [green]"review my network and help me better secure it"[/green]
  [green]"deploy a hub-spoke network with firewall in Bicep"[/green]

[bold yellow]Commands:[/bold yellow]
  [green]assess <subscription-id>[/green]                General assessment
  [green]assess <subscription-id> -t finops[/green]      FinOps & cost optimization
  [green]deploy <description>[/green]                    Generate Bicep/Terraform IaC
  [green]clear[/green]                                   Clear conversation history
  [green]exit[/green]                                    Quit
"""

_GREETING_PHRASES = [
    "What are we working on today?",
    "How can I help?",
    "What's on your mind?",
    "What can I help you with?",
]

app = typer.Typer(
    name="azure-csa",
    help="Senior Azure CSA Agent — advisory assessments grounded in live Azure data.",
    invoke_without_command=True,
)


def _check_llm_backend():
    """Check for LLM env vars at startup and offer to configure if missing."""
    import os

    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if endpoint or openai_key:
        deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        source = f"{endpoint} ({deployment})" if endpoint else "OpenAI API"
        console.print(f"[green]\u2713 LLM backend:[/green] [dim]{source}[/dim]")
        return

    console.print("[yellow]\u26a0  No LLM backend configured.[/yellow] [dim]Natural language queries won't work without one.[/dim]")
    console.print()
    console.print("[bold]To enable, paste one of these into your terminal before running azure-csa:[/bold]")
    console.print()
    console.print("  [cyan]# Option 1: Azure OpenAI (recommended — uses your az login credentials)[/cyan]")
    console.print('  [white]$env:AZURE_OPENAI_ENDPOINT = "https://<your-resource>.openai.azure.com"[/white]')
    console.print('  [white]$env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o"[/white]  [dim]# optional, defaults to gpt-4o[/dim]')
    console.print()
    console.print("  [cyan]# Option 2: Azure OpenAI with API key[/cyan]")
    console.print('  [white]$env:AZURE_OPENAI_ENDPOINT = "https://<your-resource>.openai.azure.com"[/white]')
    console.print('  [white]$env:AZURE_OPENAI_API_KEY = "<your-key>"[/white]')
    console.print()
    console.print("  [cyan]# Option 3: OpenAI directly[/cyan]")
    console.print('  [white]$env:OPENAI_API_KEY = "<your-key>"[/white]')
    console.print()
    console.print("[dim]Pre-built assessments (assess command) work without an LLM.[/dim]")
    console.print()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Launch the Azure CSA agent."""
    if ctx.invoked_subcommand is not None:
        return

    console.print(Panel(BANNER, border_style="cyan", padding=(0, 2)))
    _check_llm_backend()
    console.print(HELP_TEXT)
    console.print(f"[dim]{random.choice(_GREETING_PHRASES)}[/dim]\n")

    conversation_history: list[dict] = []

    while True:
        try:
            user_input = console.input("[bold cyan]azure-csa>[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            token_session.print_session_summary()
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            token_session.print_session_summary()
            console.print("[dim]Goodbye.[/dim]")
            break

        # Parse interactive input
        parts = user_input.split(maxsplit=1)
        cmd = parts[0].lower()

        if cmd == "assess" and len(parts) > 1:
            _parse_assess(parts[1])
        elif cmd == "deploy" and len(parts) > 1:
            _run_deploy(parts[1].strip('"').strip("'"), conversation_history)
        elif cmd == "query" and len(parts) > 1:
            _run_query(parts[1].strip('"').strip("'"), conversation_history)
        elif cmd in ("help", "?"):
            console.print(HELP_TEXT)
        elif cmd == "clear":
            conversation_history.clear()
            console.print("[dim]Conversation history cleared.[/dim]")
        else:
            # Detect IaC intent in natural language and route accordingly
            iac_keywords = ["deploy", "bicep", "terraform", "infrastructure", "iac",
                           "provision", "arm template", "landing zone template",
                           "generate bicep", "generate terraform", "hub-spoke",
                           "verified module", "avm"]
            if any(kw in user_input.lower() for kw in iac_keywords):
                _run_deploy(user_input, conversation_history)
            else:
                _run_query(user_input, conversation_history)


def _parse_assess(args_str: str):
    """Parse assess arguments from interactive input."""
    import shlex
    from csa.assessments import run_assessment

    tokens = shlex.split(args_str)
    scope = tokens[0]
    assessment_type = "general"
    output_dir = "outputs"

    i = 1
    while i < len(tokens):
        if tokens[i] in ("-t", "--type") and i + 1 < len(tokens):
            assessment_type = tokens[i + 1]
            i += 2
        elif tokens[i] in ("-o", "--output") and i + 1 < len(tokens):
            output_dir = tokens[i + 1]
            i += 2
        else:
            i += 1

    run_assessment(scope=scope, assessment_type=assessment_type, output_dir=output_dir, tee=True)


def _run_query(question: str, history: list[dict] | None = None):
    """Run a natural language query."""
    from csa.arg_client import ask

    summary = ask(question, history)
    if history is not None and summary:
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": summary})


def _run_deploy(request: str, history: list[dict] | None = None):
    """Generate IaC from a natural language request."""
    from csa.iac import generate

    summary = generate(request, history)
    if history is not None and summary:
        history.append({"role": "user", "content": request})
        history.append({"role": "assistant", "content": summary})


@app.command()
def assess(
    scope: str = typer.Argument(help="Subscription ID or management group ID to assess"),
    assessment_type: str = typer.Option(
        "general",
        "--type", "-t",
        help="Assessment type: general, finops, landing-zone, network, waf",
    ),
    output_dir: str = typer.Option(
        "outputs",
        "--output", "-o",
        help="Output directory for assessment report",
    ),
    tee: bool = typer.Option(
        True,
        "--tee/--no-tee",
        help="Display results in terminal in addition to saving the report",
    ),
):
    """Run an advisory assessment against an Azure scope."""
    from csa.assessments import run_assessment

    run_assessment(scope=scope, assessment_type=assessment_type, output_dir=output_dir, tee=tee)


@app.command()
def query(
    question: str = typer.Argument(help="Natural language question about your Azure environment"),
):
    """Ask a natural language question — generates and runs an ARG query."""
    from csa.arg_client import ask

    ask(question)


if __name__ == "__main__":
    app()
