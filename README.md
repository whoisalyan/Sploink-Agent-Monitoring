# Sploink Agent Monitoring System

A robust monitoring system for AI agents that detects behavioral issues such as execution loops, intent drift, and failures in real-time.

## 🚀 Setup Instructions

### 1. Prerequisites
- Python 3.8+
- pip

### 2. Install Dependencies
```bash
pip install flask flask-sqlalchemy aiosqlite asgiref requests
```

### 3. Run the Dashboard
```bash
python app.py
```
The dashboard will be available at `http://localhost:5000`.

### 4. Run the Agent Simulator
Open a new terminal and run:
```bash
# Available scenarios: normal, loop, drift, failure
python agent.py --scenario loop
```

---

## 🏗️ Architecture Overview

The system is built with a focus on high-concurrency ingestion and robust behavioral analysis.

- **Backend**: Flask (Python) utilizing `async` handlers for event ingestion to handle high-frequency bursts.
- **Database**: SQLite with **WAL (Write-Ahead Logging)** mode enabled to allow concurrent reads and writes without locking.
- **Frontend**: Single-page-like dashboard using **Flask Jinja2 Templates** and **Vanilla CSS** with a premium dark-mode aesthetic.
- **Deduplication**: Events are uniquely identified by `(session_id, step, timestamp)`, ensuring idempotency even if the agent retries or sends duplicate packets.

---

## 🧠 Detection Logic

The monitoring layer in `detection.py` uses practical heuristics rather than simple string matching:

### 1. Loop Detection
Uses a **sliding window sequence matcher**. It looks for repeating patterns of `action` types and evaluates the **similarity ratio** of the `input` data using `difflib.SequenceMatcher`. If the sequence repeats and inputs are >= 70% similar, a loop is flagged.

### 2. Drift Detection
Monitors the **distribution of action types** over the session's lifetime. It compares the action frequency of the first half vs. the second half of the session. If the distribution shifted significantly (calculated via absolute difference of probabilities), behavioral drift is detected.

### 3. Failure Detection
Checks for both **consecutive failures** (the agent is stuck) and the overall **failure rate** (the agent is unreliable). Thresholds are set to 3 consecutive failures or a 40% failure rate.

---

## ⚖️ Trade-offs

- **SQLite vs Postgres**: Chose SQLite for its zero-config setup and performance at this scale. For massive multi-agent systems, Postgres would be preferred for better row-level locking.
- **Async vs Task Queue**: Used Flask's async handlers for ingestion simplicity. In a production environment, events would be pushed to Redis/RabbitMQ and processed by background workers to decouple ingestion from analysis.
- **Heuristic vs LLM Analysis**: Used sequence matching and action distribution for detection speed. While an LLM could provide deeper semantic analysis of drift, heuristics are more cost-effective and provide immediate real-time feedback.