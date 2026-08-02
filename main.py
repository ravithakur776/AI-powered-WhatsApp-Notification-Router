"""Main CLI entrypoint for the AI WhatsApp Notification Router hackathon entry."""

import argparse
import asyncio
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import track

from data.loader import DatasetLoader
from src.context.graph_builder import ContextGraphBuilder
from src.router import NotificationRouter
from src.utils.logger import logger
from src.utils.metrics import metrics_collector
from eval.dataset_eval import run_full_dataset_evaluation
from eval.generate_report import generate_markdown_report

console = Console()


def print_banner():
    banner = """
[bold cyan]====================================================================[/bold cyan]
[bold green]   🤖 AI-POWERED WHATSAPP NOTIFICATION ROUTER (HACKATHON EDITION)   [/bold green]
[bold cyan]====================================================================[/bold cyan]
[dim]Architected for Ultra-Low Latency, Multimodal RAG, and Explainable Routing[/dim]
    """
    console.print(banner)


async def run_live_demo():
    print_banner()
    console.print("\n[bold yellow]🔄 Loading Dataset & Initializing Multimodal Router Pipeline...[/bold yellow]")
    
    loader = DatasetLoader()
    ctx_builder = ContextGraphBuilder(loader)
    router = NotificationRouter(ctx_builder)

    console.print(f"[bold green]✓ Loaded {len(loader.messages)} WhatsApp Messages into In-Memory Feature Store.[/bold green]\n")

    table = Table(title="🟢 Live Routing Decisions Summary", show_header=True, header_style="bold magenta")
    table.add_column("Message ID", style="cyan", width=12)
    table.add_column("Sender / Group", style="white", width=22)
    table.add_column("Action", style="bold", width=10)
    table.add_column("Type", style="dim", width=18)
    table.add_column("Confidence", justify="right", width=12)
    table.add_column("Latency", justify="right", width=10)
    table.add_column("Route", style="yellow", width=12)

    results = []
    for msg in loader.messages:
        out, latency, is_fast = await router.route_message(msg)

        # Style Action
        action_style = "bold green" if out.action == "notify" else ("bold yellow" if out.action == "digest" else "bold red")
        action_str = f"[{action_style}]{out.action.upper()}[/{action_style}]"

        sender_label = f"{msg.sender_id}"
        if msg.group_id:
            sender_label += f" ({msg.group_id})"

        route_type = "[bold cyan]FAST PATH[/bold cyan]" if is_fast else "[magenta]DEEP PATH[/magenta]"
        
        table.add_row(
            out.message_id,
            sender_label,
            action_str,
            out.message_type,
            f"{out.confidence * 100:.1f}%",
            f"{latency:.1f}ms",
            route_type
        )

        results.append({
            "output": out,
            "latency": latency,
            "is_fast": is_fast,
            "content": ctx_builder.loader.messages
        })

    console.print(table)

    # Detailed Inspect Panel for Top Decisions
    console.print("\n[bold cyan]🔍 Detailed Explainability & Evidence Log Sample:[/bold cyan]")
    for res in results[:3]:
        out = res["output"]
        panel_content = (
            f"[bold]Action:[/bold] {out.action.upper()}\n"
            f"[bold]Message Type:[/bold] {out.message_type}\n"
            f"[bold]Reason:[/bold] {out.reason}\n"
            f"[bold]Confidence:[/bold] {out.confidence * 100:.1f}%\n"
            f"[bold]Evidence Message IDs:[/bold] {out.evidence_message_ids}\n"
            f"[bold]Latency:[/bold] {res['latency']:.2f}ms ({'Fast Path' if res['is_fast'] else 'Deep Path'})"
        )
        console.print(Panel(panel_content, title=f"Message {out.message_id}", border_style="cyan"))

    # Print Summary Metrics
    summary = metrics_collector.get_summary()
    console.print("\n[bold green]📊 Metrics & Performance Telemetry:[/bold green]")
    console.print(json.dumps(summary, indent=2))


async def main():
    parser = argparse.ArgumentParser(description="AI WhatsApp Notification Router CLI")
    parser.add_argument("--demo", action="store_true", help="Run interactive visual CLI demo")
    parser.add_argument("--eval", action="store_true", help="Run full evaluation suite and generate Markdown report")
    args = parser.parse_args()

    if args.eval:
        console.print("[bold yellow]Running full evaluation benchmark suite...[/bold yellow]")
        report_data = await run_full_dataset_evaluation()
        generate_markdown_report(report_data)
        console.print("[bold green]✓ Evaluation completed and report generated at eval/EVALUATION_REPORT.md[/bold green]")
    else:
        await run_live_demo()


if __name__ == "__main__":
    asyncio.run(main())
