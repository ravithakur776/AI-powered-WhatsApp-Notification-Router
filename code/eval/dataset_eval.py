"""Dataset evaluation script processing messages asynchronously and generating evaluation logs."""

import asyncio
import json
import time
from pathlib import Path
from data.loader import DatasetLoader
from src.context.graph_builder import ContextGraphBuilder
from src.router import NotificationRouter
from src.utils.logger import logger
from src.utils.metrics import metrics_collector
from eval.benchmark import RouterBenchmark


async def run_full_dataset_evaluation(output_path: str = "eval/predictions.json") -> dict:
    """Processes all dataset messages, saves predictions, and prints performance summary."""
    logger.info("Initializing dataset loader & router pipeline...")
    loader = DatasetLoader()
    ctx_builder = ContextGraphBuilder(loader)
    router = NotificationRouter(ctx_builder)

    results = []
    ground_truth = []

    # Map implicit ground truths from dataset rules for synthetic evaluation benchmarking
    for msg in loader.messages:
        # Define synthetic benchmark ground truths
        if "otp" in msg.content.lower() or "verification" in msg.content.lower():
            expected = "notify"
        elif "spammer" in msg.sender_id.lower() or "crypto" in msg.content.lower():
            expected = "mute"
        elif msg.group_id == "G_99" or ctx_builder.feature_store.is_group_muted_by_user(msg.group_id, msg.receiver_id):
            expected = "mute"
        elif "memory leak" in msg.content.lower():
            expected = "notify"
        elif "sale" in msg.content.lower():
            expected = "mute"
        else:
            expected = "digest"
        
        ground_truth.append({"message_id": msg.message_id, "expected_action": expected})

    logger.info(f"Starting batch evaluation for {len(loader.messages)} messages...")
    start_all = time.perf_counter()

    for msg in loader.messages:
        output, latency, is_fast_path = await router.route_message(msg)
        results.append({
            "message_id": output.message_id,
            "action": output.action,
            "message_type": output.message_type,
            "reason": output.reason,
            "confidence": output.confidence,
            "evidence_message_ids": output.evidence_message_ids,
            "latency_ms": round(latency, 2),
            "is_fast_path": is_fast_path
        })

    total_time = (time.perf_counter() - start_all) * 1000
    
    # Save predictions file
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Saved {len(results)} prediction results to {output_path}")

    # Compute Benchmark Metrics
    eval_metrics = RouterBenchmark.evaluate_predictions(results, ground_truth)
    summary_metrics = metrics_collector.get_summary()

    report = {
        "total_messages": len(results),
        "total_batch_time_ms": round(total_time, 2),
        "avg_time_per_message_ms": round(total_time / len(results), 2) if results else 0.0,
        "performance_metrics": summary_metrics,
        "accuracy_benchmark": eval_metrics
    }

    return report


if __name__ == "__main__":
    report = asyncio.run(run_full_dataset_evaluation())
    print(json.dumps(report, indent=2))
