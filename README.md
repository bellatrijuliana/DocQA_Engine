# DocQA Case Engine v2.0

A personal project I built to solve a real problem I faced in QA work, manually writing test cases is slow and inconsistent. **DocQA Case Engine** automates test case generation from raw requirements text using a **local LLM (Ollama)**, applies **Risk-Based Testing (RBT)** to prioritize what matters most, and produces a clean HTML report dashboard.

v2.0 is a full upgrade from v1.0, replacing static manual input with an AI-powered pipeline.

---

## Why I Built This

Writing test cases by hand from requirements documents is tedious and error-prone. I wanted a tool that could:
- Take raw requirements or user stories as input
- Automatically generate meaningful test cases using an LLM
- Assess risk levels so I know where to focus testing effort
- Produce a report I could actually share with a team

This project is my attempt to combine QA engineering knowledge with AI tooling, built entirely with local models so it works offline and stays private.

---

## What's New in v2.0

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Generate test cases | Manual (`requirements_data.py`) | **Auto from raw text via LLM** |
| Risk assessment | Manual / static | **LLM assesses probability & impact** |
| Risk-based expansion | ❌ | **LLM generates extra test cases for High/Critical areas** |
| Input interface | CLI only | **CLI + Web UI** |
| LLM engine | ❌ | **Ollama (local, model-agnostic)** |

---

## Features

- **LLM-Powered Intake** : paste raw requirements or user stories, LLM generates structured test cases automatically
- **Risk Engine** : LLM assesses each test case's probability of failure and business impact, assigns risk scores
- **Risk-Based Expansion** : automatically generates additional test cases in Critical/High risk areas
- **Curator CLI** : review test cases ordered by risk priority (Critical → High → Medium → Low)
- **HTML Report** : generates a visual risk matrix dashboard you can open in any browser
- **SQLite Storage** : lightweight local database, no setup required
- **Model-Agnostic** : works with any Ollama-supported model (llama3.2, mistral, gemma3, etc.)
- **Offline & Private** : runs entirely on local machine, no data sent to external APIs

---

## Tech Stack

| Technology | Description |
|------------|-------------|
| Python 3.8+ | Core language |
| Ollama | Local LLM runner (llama3.2 / mistral / gemma3) |
| SQLite | Local database for test case storage |
| Flask | Web UI backend (`web/app.py`) |
| HTML/CSS | Report generation & web interface |

---

## Project Structure

```
DocQACase/
├── data/
│   └── docQA_case.db              # SQLite database
├── src/
│   ├── config.py                  # Centralized config (model, timeout)
│   ├── ollama_client.py           # Ollama API wrapper
│   ├── setup_db.py                # DB schema setup with risk columns
│   ├── llm_intake.py              # Raw input → LLM → test cases
│   ├── risk_engine.py             # RBT assess + expand
│   ├── curator_cli.py             # Risk-aware review UI
│   ├── generate_html_report.py    # Risk matrix dashboard generator
│   ├── generator_engine.py        # BVA/Flow logic (core engine)
│   ├── requirements_data.py       # Manual input fallback
│   └── view_case.py               # Quick case viewer
├── web/
│   ├── app.py                     # Flask web app
│   └── templates/index.html       # Web UI
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

1. **Python 3.8+**
2. **Ollama** — install from [https://ollama.ai](https://ollama.ai)
3. Pull your preferred model:
   ```bash
   ollama pull llama3.2   # Recommended
   # or
   ollama pull mistral
   # or
   ollama pull gemma3
   ```
4. Start Ollama:
   ```bash
   ollama serve
   ```

### Installation

```bash
git clone https://github.com/bellatrijuliana/docqa-case-engine.git
cd docqa-case-engine
pip install -r requirements.txt
```

### Configuration

Edit `src/config.py`:
```python
OLLAMA_MODEL = "llama3.2"     # Match the model you pulled
OLLAMA_TIMEOUT = 120           # Increase if your model is slow
```

---

## Workflow

```
Raw Requirements Text
        ↓
  [llm_intake.py]  →  LLM generates test cases + initial risk assessment
        ↓
  [risk_engine.py] →  Re-assess risks, expand High/Critical areas
        ↓
 [curator_cli.py]  →  Human review by priority (Critical first)
        ↓
[generate_html_report.py] → Risk matrix dashboard (test_report.html)
```

### Step-by-step

```bash
# 1. Initialize database
python src/setup_db.py

# 2. Input requirements → LLM generates test cases
python src/llm_intake.py

# 3. Risk assessment & expansion (recommended)
python src/risk_engine.py

# 4. Review test cases by priority
python src/curator_cli.py

# 5. Generate HTML report
python src/generate_html_report.py
```

---

## Database Schema (v2.0 additions)

New columns in `test_scenarios`:

| Column | Type | Description |
|--------|------|-------------|
| `risk_level` | TEXT | Critical / High / Medium / Low / Unassessed |
| `risk_score` | INTEGER | probability × impact (max 25) |
| `probability_of_failure` | INTEGER | 1–5 |
| `business_impact` | INTEGER | 1–5 |
| `risk_reasoning` | TEXT | LLM's explanation for the risk score |
| `source` | TEXT | manual / bva_engine / llm_intake / llm_rbt |
| `llm_model` | TEXT | Ollama model used to generate the case |

---

## Troubleshooting

**Ollama not detected**
```
❌ Ollama tidak bisa diakses di http://localhost:11434
```
→ Make sure `ollama serve` is running in a separate terminal.

**Timeout**
```
⏱️ Timeout setelah 120s
```
→ Increase `OLLAMA_TIMEOUT` in `config.py`, or use a smaller model (e.g. `gemma3:2b`).

**Invalid JSON response**
→ Try a more capable model — `llama3.2` handles structured JSON output more reliably than smaller models.

---

## Roadmap

- [x] LLM-powered test case generation
- [x] Risk-Based Testing engine
- [x] HTML report dashboard
- [ ] Web UI (in progress)
- [ ] Export to Excel / CSV
- [ ] Multi-requirement batch processing

---

## What I Learned

- Integrating a **local LLM** (Ollama) into a Python application
- Designing a **prompt engineering** workflow for structured JSON output
- Applying **Risk-Based Testing** methodology programmatically
- Building a multi-step **CLI pipeline** with SQLite persistence
- The value of keeping AI tooling **local and private**

---

*A personal project born out of real QA work, built to make test case generation smarter, faster, and risk-aware.*
