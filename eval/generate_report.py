"""Generates Markdown evaluation summary report for the Hackathon Judge."""

import json
from pathlib import Path


def generate_markdown_report(report_data: dict, output_path: str = "eval/EVALUATION_REPORT.md"):
    perf = report_data.get("performance_metrics", {})
    acc = report_data.get("accuracy_benchmark", {})
    
    md_content = f"""# 📊 AI WhatsApp Notification Router - Evaluation Report

> **System Performance & Benchmarking Metrics**  
> Generated automatically by the Evaluation Suite.

---

## 🚀 Key Performance Indicators (KPIs)

- **Total Messages Evaluated**: `{report_data.get('total_messages', 0)}`
- **Classification Accuracy**: `{acc.get('accuracy', 0.0) * 100:.2f}%`
- **Macro F1 Score**: `{acc.get('macro_f1', 0.0):.4f}`
- **Fast-Path Bypass Rate**: `{perf.get('fast_path_ratio', 0.0) * 100:.1f}%` *(Routed in <5ms without LLM)*
- **P50 Latency**: `{perf.get('p50_latency_ms', 0.0)} ms`
- **P90 Latency**: `{perf.get('p90_latency_ms', 0.0)} ms`
- **P99 Latency**: `{perf.get('p99_latency_ms', 0.0)} ms`

---

## 🎯 Per-Class Precision & Recall

| Class | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
"""
    per_class = acc.get("per_class_metrics", {})
    for cls_name, metrics in per_class.items():
        md_content += f"| **{cls_name.upper()}** | `{metrics['precision']:.4f}` | `{metrics['recall']:.4f}` | `{metrics['f1_score']:.4f}` | `{metrics['support']}` |\n"

    md_content += """
---

## ⚡ Latency & Cost Breakdown

| Route Path | Avg Latency | Traffic Share | Primary Engine |
| :--- | :--- | :--- | :--- |
"""
    md_content += f"| **Fast Path Engine** | `{perf.get('fast_path_avg_latency_ms', 0.0)} ms` | `{perf.get('fast_path_ratio', 0.0)*100:.1f}%` | Sub-5ms Heuristic / Rule Filter |\n"
    md_content += f"| **Deep Path LLM Engine** | `{perf.get('deep_path_avg_latency_ms', 0.0)} ms` | `{perf.get('deep_path_ratio', 0.0)*100:.1f}%` | Gemini 2.5/3.0 Flash + RAG Vector Search |\n"

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        f.write(md_content)

    print(f"Report generated at {output_path}")


if __name__ == "__main__":
    mock_data = {
        "total_messages": 6,
        "performance_metrics": {
            "fast_path_ratio": 0.5,
            "deep_path_ratio": 0.5,
            "p50_latency_ms": 3.2,
            "p90_latency_ms": 145.0,
            "p99_latency_ms": 210.0,
            "fast_path_avg_latency_ms": 2.1,
            "deep_path_avg_latency_ms": 150.0
        },
        "accuracy_benchmark": {
            "accuracy": 1.0,
            "macro_f1": 1.0,
            "per_class_metrics": {
                "notify": {"precision": 1.0, "recall": 1.0, "f1_score": 1.0, "support": 2},
                "digest": {"precision": 1.0, "recall": 1.0, "f1_score": 1.0, "support": 2},
                "mute": {"precision": 1.0, "recall": 1.0, "f1_score": 1.0, "support": 2}
            }
        }
    }
    generate_markdown_report(mock_data)
