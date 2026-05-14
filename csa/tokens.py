"""Session token usage and cost tracking for Azure OpenAI / OpenAI calls."""

from rich.console import Console
from rich.table import Table

console = Console()

# GPT-4o pricing (per 1M tokens)
# Azure OpenAI and OpenAI use the same rates for gpt-4o
_PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
}
_DEFAULT_PRICING = {"input": 2.50, "output": 10.00}  # assume gpt-4o


class TokenTracker:
    """Accumulates token usage across a session and computes estimated cost."""

    def __init__(self):
        self.calls: list[dict] = []
        self.total_input = 0
        self.total_output = 0
        self.model = None

    def record(self, usage, model: str | None = None, label: str = ""):
        """Record token usage from an OpenAI response.

        Args:
            usage: The usage object from response (has prompt_tokens, completion_tokens).
            model: The model/deployment name for pricing lookup.
            label: Human-readable label for this call (e.g., "KQL generation").
        """
        if not usage:
            return

        input_tokens = getattr(usage, "prompt_tokens", 0) or 0
        output_tokens = getattr(usage, "completion_tokens", 0) or 0

        if model:
            self.model = model
        self.total_input += input_tokens
        self.total_output += output_tokens

        pricing = _PRICING.get(self.model or "", _DEFAULT_PRICING)
        cost = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000

        self.calls.append({
            "label": label,
            "input": input_tokens,
            "output": output_tokens,
            "cost": cost,
        })

        console.print(
            f"  [dim]tokens: {input_tokens:,} in / {output_tokens:,} out"
            f"  (~${cost:.4f})[/dim]"
        )

    def print_session_summary(self):
        """Print a session cost summary table on exit."""
        if not self.calls:
            return

        pricing = _PRICING.get(self.model or "", _DEFAULT_PRICING)
        total_cost = (
            self.total_input * pricing["input"]
            + self.total_output * pricing["output"]
        ) / 1_000_000

        console.print()
        table = Table(
            title="Session Token Usage",
            border_style="dim",
            show_lines=False,
        )
        table.add_column("Call", style="cyan")
        table.add_column("Input", style="green", justify="right")
        table.add_column("Output", style="yellow", justify="right")
        table.add_column("Cost", style="white", justify="right")

        for call in self.calls:
            table.add_row(
                call["label"],
                f"{call['input']:,}",
                f"{call['output']:,}",
                f"${call['cost']:.4f}",
            )

        table.add_section()
        table.add_row(
            "[bold]Total[/bold]",
            f"[bold]{self.total_input:,}[/bold]",
            f"[bold]{self.total_output:,}[/bold]",
            f"[bold]${total_cost:.4f}[/bold]",
        )

        console.print(table)
        model_name = self.model or "gpt-4o"
        console.print(f"[dim]Pricing: {model_name} @ ${pricing['input']}/M input, ${pricing['output']}/M output[/dim]")


# Global session tracker
session = TokenTracker()
