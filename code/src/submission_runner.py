"""Submission Runner for executing the Notification Router pipeline and producing HackerRank-compliant output.csv."""

import os
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from config.settings import DATA_DIR
from data.loader import DatasetLoader
from src.context.graph_builder import ContextGraphBuilder
from src.router import NotificationRouter
from src.utils.logger import logger
from src.utils.metrics import metrics_collector

console = Console()


def validate_submission_csv(csv_path: Path, expected_message_count: int) -> bool:
    """Validates output.csv against HackerRank submission criteria.
    
    Criteria:
    1. Schema columns: message_id, action, message_type, reason, confidence, evidence_message_ids
    2. action is one of notify/digest/mute
    3. confidence is float between 0 and 1
    4. evidence_message_ids is string (semicolon separated or 'none')
    """
    logger.info(f"Validating submission CSV at {csv_path}...")

    if not csv_path.exists():
        raise FileNotFoundError(f"Submission CSV not found at {csv_path}")

    df = pd.read_csv(csv_path).fillna("")

    expected_columns = ["message_id", "action", "message_type", "reason", "confidence", "evidence_message_ids"]
    if list(df.columns) != expected_columns:
        raise ValueError(f"Invalid CSV columns! Found {list(df.columns)}, expected {expected_columns}")

    if len(df) != expected_message_count:
        raise ValueError(f"Mismatch in message count! Found {len(df)} rows, expected {expected_message_count}")

    valid_actions = {"notify", "digest", "mute"}

    for idx, row in df.iterrows():
        msg_id = str(row["message_id"]).strip()
        action = str(row["action"]).strip().lower()
        msg_type = str(row["message_type"]).strip()
        reason = str(row["reason"]).strip()
        evidence = str(row["evidence_message_ids"]).strip()

        try:
            confidence = float(row["confidence"])
        except ValueError:
            raise ValueError(f"Row {idx} (Message {msg_id}): Confidence '{row['confidence']}' is not a valid float!")

        if action not in valid_actions:
            raise ValueError(f"Row {idx} (Message {msg_id}): Invalid action '{action}'. Must be one of {valid_actions}")

        if not (0.0 <= confidence <= 1.0):
            raise ValueError(f"Row {idx} (Message {msg_id}): Confidence {confidence} out of range [0, 1]!")

        if not msg_id or not msg_type or not reason:
            raise ValueError(f"Row {idx} (Message {msg_id}): Missing mandatory text field (msg_id, message_type, or reason)!")

        if evidence != "none" and not evidence:
            raise ValueError(f"Row {idx} (Message {msg_id}): Invalid evidence format '{evidence}'. Expected 'none' or semicolon-separated string.")

    logger.info(f"✓ Submission CSV validation PASSED for {len(df)} records.")
    return True


class SubmissionRunner:
    """HackerRank submission runner executing end-to-end pipeline and generating output.csv."""

    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir

    async def run_submission(self, output_csv_path: Path = Path("output.csv")) -> Path:
        console.print("[bold yellow]🚀 Initializing HackerRank Submission Pipeline...[/bold yellow]")
        
        # 1. Load Datasets
        loader = DatasetLoader(self.data_dir)
        ctx_builder = ContextGraphBuilder(loader)
        router = NotificationRouter(ctx_builder)

        console.print(f"[bold green]✓ Loaded {len(loader.messages)} messages from {self.data_dir}[/bold green]")

        records: List[Dict[str, Any]] = []
        action_counts = {"notify": 0, "digest": 0, "mute": 0}

        console.print("[bold yellow]🔄 Running complete 5-layer hybrid routing pipeline...[/bold yellow]")

        # 2. Process every message
        for msg in loader.messages:
            output, latency_ms, is_fast_path = await router.route_message(msg)

            # Format evidence IDs: semicolon separated string or "none"
            if output.evidence_message_ids:
                evidence_str = ";".join(output.evidence_message_ids)
            else:
                evidence_str = "none"

            records.append({
                "message_id": output.message_id,
                "action": output.action,
                "message_type": output.message_type,
                "reason": output.reason,
                "confidence": round(output.confidence, 4),
                "evidence_message_ids": evidence_str
            })

            if output.action in action_counts:
                action_counts[output.action] += 1

        # 3. Generate output.csv
        df = pd.DataFrame(records, columns=[
            "message_id", "action", "message_type", "reason", "confidence", "evidence_message_ids"
        ])
        
        output_csv_path = Path(output_csv_path).resolve()
        df.to_csv(output_csv_path, index=False)
        console.print(f"[bold green]✓ Generated {output_csv_path} ({len(df)} records)[/bold green]")

        # 4. Validate output.csv
        validate_submission_csv(output_csv_path, len(loader.messages))
        console.print("[bold green]✓ Output CSV validation 100% SUCCESSFUL![/bold green]")

        # 5. Print Summary Statistics
        self._print_summary_statistics(df, action_counts, metrics_collector.get_summary())

        return output_csv_path

    def _print_summary_statistics(self, df: pd.DataFrame, action_counts: Dict[str, int], metrics_summary: Dict[str, Any]):
        total = len(df)
        table = Table(title="📊 Submission Summary Statistics", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="bold white")
        table.add_column("Value", style="bold green")

        table.add_row("Total Messages Processed", str(total))
        table.add_row("NOTIFY Action Count", f"{action_counts['notify']} ({action_counts['notify']/total*100:.1f}%)")
        table.add_row("DIGEST Action Count", f"{action_counts['digest']} ({action_counts['digest']/total*100:.1f}%)")
        table.add_row("MUTE Action Count", f"{action_counts['mute']} ({action_counts['mute']/total*100:.1f}%)")
        table.add_row("Fast Path Ratio", f"{metrics_summary.get('fast_path_ratio', 0.0)*100:.1f}%")
        table.add_row("Deep Path Ratio", f"{metrics_summary.get('deep_path_ratio', 0.0)*100:.1f}%")
        table.add_row("P50 Latency", f"{metrics_summary.get('p50_latency_ms', 0.0)} ms")
        table.add_row("P90 Latency", f"{metrics_summary.get('p90_latency_ms', 0.0)} ms")
        table.add_row("Mean Confidence Score", f"{df['confidence'].mean()*100:.1f}%")

        console.print(table)
