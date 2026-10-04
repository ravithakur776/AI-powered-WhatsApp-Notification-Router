# 🤖 AI-Powered WhatsApp Notification Router (HackerRank AI Hackathon)

An ultra-low latency, multimodal, explainable AI routing engine that classifies incoming WhatsApp messages into **`notify`**, **`digest`**, or **`mute`**.

---

## 🌟 Key Architectural Features

1. **Two-Tier Cascading Engine**:
   - **Fast-Path Engine (<5ms)**: Uses deterministic heuristics to instantly route security OTPs, emergency SOS alerts, and explicitly muted contacts/groups without LLM overhead.
   - **Deep-Path Engine**: Escalates complex, ambiguous messages to a multimodal RAG reasoning agent (Gemini / Whisper / EasyOCR) using Pydantic JSON schemas.
2. **Multimodal Processing**:
   - Audio voice note transcription powered by `faster-whisper`.
   - Visual OCR extracted from media attachments via `EasyOCR` / Multimodal Vision.
3. **Vector RAG History Context**:
   - Semantic retrieval using `sentence-transformers` (`all-MiniLM-L6-v2`) to pull relevant past user actions and output exact `evidence_message_ids`.
4. **Strict Output Schema Enforcement**:
   - 100% Pydantic V2 validated output payload (`message_id`, `action`, `message_type`, `reason`, `confidence`, `evidence_message_ids`).

---

## 📁 System Architecture & Directory Structure

```
AI-powered WhatsApp Notification Router/
├── config/                  # Enums, thresholds, and environment settings
├── data/                    # Dataset loader & synthetic CSV generator
├── src/
│   ├── schemas/             # Pydantic input, output, and context models
│   ├── multimodal/          # Async OCR and Speech-to-Text extraction
│   ├── context/             # In-memory feature store & vector RAG
│   ├── router/              # Fast-path, Deep-path, and Guardrail engines
│   └── utils/               # Structured loguru logging & telemetry metrics
├── eval/                    # Benchmarking harness & report generator
├── tests/                   # Pytest suite
└── main.py                  # CLI and Rich visual terminal dashboard
```

---

## 🚀 Quickstart & Execution Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Interactive Live Terminal Dashboard
```bash
python main.py --demo
```

### 3. Run Benchmark Evaluation Suite
```bash
python main.py --eval
```

### 4. Run Pytest Suite
```bash
pytest tests/
```

---

## 📊 Evaluation Output Schema

```json
{
  "message_id": "M_1001",
  "action": "notify",
  "message_type": "security_otp",
  "reason": "Time-sensitive authentication OTP detected. Requires immediate user notification.",
  "confidence": 0.99,
  "evidence_message_ids": ["H_01"]
}
