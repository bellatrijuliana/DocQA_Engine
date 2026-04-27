# DocQA Case Engine v2.0

Upgrade dari v1.0 dengan integrasi **LLM lokal (Ollama)** dan **Risk-Based Testing**.

---

## Yang Baru di v2.0

| Fitur | v1.0 | v2.0 |
|---|---|---|
| Generate test case | Manual (requirements_data.py) | **Auto dari raw input teks via LLM** |
| Risk assessment | Manual / static | **LLM menilai probability & impact** |
| Risk-based expansion | ❌ | **LLM generate test case tambahan di area High/Critical** |
| Input interface | CLI saja | **CLI + Web UI** |
| LLM engine | ❌ | **Ollama (local, model-agnostic)** |

---

## Prerequisites

1. **Python 3.8+**
2. **Ollama** — install dari [https://ollama.ai](https://ollama.ai)
3. Pull model pilihan:
   ```bash
   ollama pull llama3.2   # Rekomendasi
   # atau
   ollama pull mistral
   # atau
   ollama pull gemma3
   ```
4. Jalankan Ollama:
   ```bash
   ollama serve
   ```

---

## Konfigurasi

Edit `src/config.py`:
```python
OLLAMA_MODEL = "llama3.2"     # Ganti sesuai model yang kamu pull
OLLAMA_TIMEOUT = 120           # Naikkan jika model lambat
```

---

## Instalasi

```bash
pip install -r requirements.txt
```

---

## Workflow v2.0

### Step 1 — Inisialisasi Database
```bash
python src/setup_db.py
```

### Step 2 — Input Requirements via CLI
```bash
python src/llm_intake.py
```
Paste requirements/user story kamu → LLM langsung generate test cases + risk assessment awal.

### Step 3 — Risk Engine (opsional tapi direkomendasikan)
```bash
python src/risk_engine.py
```
Pilih:
- **Option 1**: LLM re-assess risk semua test case
- **Option 2**: LLM generate test case tambahan di area High/Critical
- **Option 3**: Keduanya

### Step 4 — Curator Review
```bash
python src/curator_cli.py
```
Review prioritas: Critical → High → Medium → Low

### Step 5 — Generate Report
```bash
python src/generate_html_report.py
```
Buka `test_report.html` di browser.

---

## Project Structure v2.0

```
DocQACase/
│
├── data/
│   └── docQA_case.db              # SQLite database
│
├── src/
│   ├── config.py                  # [BARU] Konfigurasi terpusat
│   ├── ollama_client.py           # [BARU] Wrapper Ollama API
│   ├── setup_db.py                # [UPGRADE] Schema + risk columns
│   ├── llm_intake.py              # [BARU] Raw input → LLM → test cases
│   ├── risk_engine.py             # [BARU] RBT assess + expand
│   ├── curator_cli.py             # [UPGRADE] Risk-aware review UI
│   ├── generate_html_report.py    # [UPGRADE] Risk matrix dashboard
│   ├── generator_engine.py        # [TETAP] BVA/Flow logic
│   ├── requirements_data.py       # [TETAP] Manual fallback
│   └── view_case.py               # [TETAP] Quick viewer
│
├── web/                           # Web UI (coming next)
│   ├── app.py
│   └── templates/index.html
│
├── requirements.txt
└── README.md
```

---

## Database Schema v2.0

Tabel `test_scenarios` — kolom baru:

| Kolom | Tipe | Deskripsi |
|---|---|---|
| `risk_level` | TEXT | Critical / High / Medium / Low / Unassessed |
| `risk_score` | INTEGER | probability × impact (max 25) |
| `probability_of_failure` | INTEGER | 1–5 |
| `business_impact` | INTEGER | 1–5 |
| `risk_reasoning` | TEXT | Penjelasan LLM |
| `source` | TEXT | manual / bva_engine / llm_intake / llm_rbt |
| `llm_model` | TEXT | Model Ollama yang digunakan |

---

## Troubleshooting

**Ollama tidak terdeteksi**
```
❌ Ollama tidak bisa diakses di http://localhost:11434
```
→ Pastikan `ollama serve` sudah berjalan di terminal lain.

**Timeout**
```
⏱️ Timeout setelah 120s
```
→ Naikkan `OLLAMA_TIMEOUT` di `config.py`, atau gunakan model yang lebih kecil (misal `gemma3:2b`).

**Response bukan JSON valid**
→ Coba model yang lebih kuat (llama3.2 lebih reliable untuk structured output daripada model kecil).