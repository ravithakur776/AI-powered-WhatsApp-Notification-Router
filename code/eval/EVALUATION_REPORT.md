# 📊 AI WhatsApp Notification Router - Evaluation Report

> **System Performance & Benchmarking Metrics**  
> Generated automatically by the Evaluation Suite.

---

## 🚀 Key Performance Indicators (KPIs)

- **Total Messages Evaluated**: `6`
- **Classification Accuracy**: `83.33%`
- **Macro F1 Score**: `0.6000`
- **Fast-Path Bypass Rate**: `83.3%` *(Routed in <5ms without LLM)*
- **P50 Latency**: `0.52 ms`
- **P90 Latency**: `1.62 ms`
- **P99 Latency**: `2.05 ms`

---

## 🎯 Per-Class Precision & Recall

| Class | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
| **NOTIFY** | `0.6667` | `1.0000` | `0.8000` | `2.0` |
| **DIGEST** | `0.0000` | `0.0000` | `0.0000` | `1.0` |
| **MUTE** | `1.0000` | `1.0000` | `1.0000` | `3.0` |

---

## ⚡ Latency & Cost Breakdown

| Route Path | Avg Latency | Traffic Share | Primary Engine |
| :--- | :--- | :--- | :--- |
| **Fast Path Engine** | `0.9 ms` | `83.3%` | Sub-5ms Heuristic / Rule Filter |
| **Deep Path LLM Engine** | `0.31 ms` | `16.7%` | Gemini 2.5/3.0 Flash + RAG Vector Search |
