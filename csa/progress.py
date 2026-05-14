"""Progress display — shows sub-agent/step status in the terminal."""

import time
from rich.console import Console

console = Console()


class StepTracker:
    """Track and display progress of multi-step agent operations."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.tool_calls = 0
        self._start_time = time.time()

    def started(self, step_name: str):
        """Show that a sub-step or sub-agent has started."""
        console.print(f"[green]-> started:[/green]  [bold]{step_name}[/bold]")

    def progress(self, detail: str | None = None):
        """Increment tool call counter and optionally show detail."""
        self.tool_calls += 1
        msg = f"[dim] * progress: {self.tool_calls} tool calls executed[/dim]"
        if detail:
            msg = f"[dim] * progress: {self.tool_calls} tool calls executed — {detail}[/dim]"
        console.print(msg)

    def done(self, step_name: str, detail: str | None = None):
        """Show that a sub-step or sub-agent has completed."""
        check = "[bold green]v[/bold green]"
        msg = f"{check} [green]{step_name} done[/green]"
        if detail:
            msg += f": [dim]{detail}[/dim]"
        console.print(msg)

    def status(self, message: str):
        """Show a status/info line."""
        console.print(f"[dim] * {message}[/dim]")

    def summary(self):
        """Print final summary line."""
        elapsed = time.time() - self._start_time
        console.print(
            f"\n[bold cyan]▸[/bold cyan] {self.agent_name} completed "
            f"[green]{self.tool_calls} tool calls[/green] in "
            f"[cyan]{elapsed:.1f}s[/cyan]"
        )
