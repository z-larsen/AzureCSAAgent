"""CLI entrypoint for the Azure CSA agent."""

from importlib.metadata import version as pkg_version

import typer
from rich.console import Console
from rich.panel import Panel

console = Console()

try:
    __version__ = pkg_version("azure-csa-agent")
except Exception:
    __version__ = "1.0.3"

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
[bold yellow]Commands:[/bold yellow]
  [green]assess <subscription-id>[/green]                General assessment
  [green]assess <subscription-id> -t finops[/green]      FinOps & cost optimization
  [green]assess <subscription-id> -t network[/green]     Networking review
  [green]assess <subscription-id> -t landing-zone[/green] Landing zone alignment
  [green]assess <subscription-id> -t waf[/green]         Well-Architected review
  [green]query "show untagged resources"[/green]         Natural language ARG query
  [green]exit[/green]                                    Quit

[dim]Or just type in natural language...[/dim]
"""

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

    while True:
        try:
            user_input = console.input("[bold cyan]azure-csa>[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            console.print("[dim]Goodbye.[/dim]")
            break

        # Parse interactive input
        parts = user_input.split(maxsplit=1)
        cmd = parts[0].lower()

        if cmd == "assess" and len(parts) > 1:
            _parse_assess(parts[1])
        elif cmd == "query" and len(parts) > 1:
            _run_query(parts[1].strip('"').strip("'"))
        elif cmd in ("help", "?"):
            console.print(HELP_TEXT)
        else:
            # Treat everything else as a natural language query
            _run_query(user_input)


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


def _run_query(question: str):
    """Run a natural language query."""
    from csa.arg_client import ask

    ask(question)


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
