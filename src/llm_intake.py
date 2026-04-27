# ============================================================
# llm_intake.py — DocQA Case Engine v2.0
# Parse raw requirements → generate test cases via Ollama LLM.
# Bisa dipanggil dari CLI atau dari web (app.py).
# ============================================================

import sqlite3
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DB_PATH, OLLAMA_MODEL, MAX_GENERATED_CASES_PER_FEATURE
from ollama_client import generate_json, check_ollama_connection
from setup_db import get_connection


# ── System Prompt untuk LLM ──────────────────────────────────
SYSTEM_PROMPT = """You are an expert QA Engineer specializing in test case design.
Your job is to analyze software requirements and generate comprehensive test cases.

You MUST respond ONLY with valid JSON. No explanation, no markdown, no preamble.
Follow the exact schema provided in every prompt."""


def build_intake_prompt(requirements_text: str, feature_name: str) -> str:
    return f"""Analyze this software requirement and generate test cases.

FEATURE NAME: {feature_name}

REQUIREMENTS:
{requirements_text}

Generate up to {MAX_GENERATED_CASES_PER_FEATURE} test cases covering:
1. Positive scenarios (happy path)
2. Negative scenarios (invalid input, error handling)
3. Boundary Value Analysis (min, max, min-1, max+1 for any numeric/length fields)
4. Edge cases (empty, null, special characters, concurrent access, etc.)

For Risk-Based Testing, also consider:
- Business criticality of each scenario
- Probability this area could fail
- Impact if this feature breaks in production

Return ONLY this JSON structure:
{{
  "feature_name": "{feature_name}",
  "parsed_summary": "1-2 sentence summary of what this feature does",
  "test_cases": [
    {{
      "scenario_title": "Short descriptive title",
      "test_type": "Positive|Negative|Boundary|Edge Case",
      "preconditions": "What must be true before the test",
      "test_steps": "Step 1: ...\nStep 2: ...\nStep 3: ...",
      "expected_result": "What should happen if the feature works correctly",
      "probability_of_failure": 3,
      "business_impact": 4,
      "risk_reasoning": "Why this scenario has this risk level"
    }}
  ]
}}

Rules:
- probability_of_failure: integer 1-5 (1=very unlikely, 5=very likely to fail)
- business_impact: integer 1-5 (1=trivial, 5=critical business impact)
- scenario_title must be unique and descriptive
- test_steps must be actionable steps a tester can follow
- Return ONLY valid JSON, nothing else"""


def calculate_risk_level(probability: int, impact: int) -> tuple[str, int]:
    """Hitung risk level dan score dari probability dan impact."""
    score = probability * impact
    if score >= 20:
        return "Critical", score
    elif score >= 12:
        return "High", score
    elif score >= 6:
        return "Medium", score
    else:
        return "Low", score


def save_to_database(
    parsed_data: dict,
    raw_input: str,
    source: str = "cli",
    model: str = None,
) -> tuple[int, int]:
    """
    Simpan test cases ke database.
    Returns: (feature_id, jumlah test case tersimpan)
    """
    model = model or OLLAMA_MODEL
    conn = get_connection()
    cursor = conn.cursor()

    feature_name = parsed_data.get("feature_name", "Unknown Feature")
    parsed_summary = parsed_data.get("parsed_summary", "")
    test_cases = parsed_data.get("test_cases", [])

    # Upsert feature
    cursor.execute("""
        INSERT INTO features (name, description)
        VALUES (?, ?)
        ON CONFLICT(name) DO UPDATE SET description = excluded.description
    """, (feature_name, parsed_summary))

    cursor.execute("SELECT id FROM features WHERE name = ?", (feature_name,))
    feature_id = cursor.fetchone()["id"]

    # Log requirements input
    cursor.execute("""
        INSERT INTO requirements_log
            (raw_input, feature_name, parsed_summary, cases_generated, llm_model, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (raw_input, feature_name, parsed_summary, len(test_cases), model, source))

    # Simpan tiap test case
    saved = 0
    for tc in test_cases:
        prob = int(tc.get("probability_of_failure", 1))
        impact = int(tc.get("business_impact", 1))
        risk_level, risk_score = calculate_risk_level(prob, impact)

        def to_str(val):
            """Konversi list/dict dari LLM ke string yang aman untuk SQLite."""
            if isinstance(val, list):
                return "\n".join(str(item) for item in val)
            if isinstance(val, dict):
                return str(val)
            return str(val) if val is not None else ""

        cursor.execute("""
            INSERT INTO test_scenarios (
                feature_id, feature_name, scenario_title, test_type,
                preconditions, test_steps, expected_result,
                risk_level, risk_score, probability_of_failure, business_impact,
                risk_reasoning, source, llm_model, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
        """, (
            feature_id,
            feature_name,
            to_str(tc.get("scenario_title", "Untitled")),
            to_str(tc.get("test_type", "Positive")),
            to_str(tc.get("preconditions", "")),
            to_str(tc.get("test_steps", "")),
            to_str(tc.get("expected_result", "")),
            risk_level,
            risk_score,
            prob,
            impact,
            to_str(tc.get("risk_reasoning", "")),
            "llm_intake",
            model,
        ))
        saved += 1

    conn.commit()
    conn.close()
    return feature_id, saved


def process_requirements(
    requirements_text: str,
    feature_name: str,
    source: str = "cli",
    model: str = None,
) -> dict:
    """
    Main function: proses requirements text → generate & simpan test cases.

    Args:
        requirements_text: Raw requirements / user story
        feature_name:      Nama fitur
        source:            'cli' atau 'web'
        model:             Override model Ollama

    Returns:
        dict dengan keys: success, feature_id, cases_saved, parsed_data, error
    """
    model = model or OLLAMA_MODEL

    if not check_ollama_connection():
        return {
            "success": False,
            "error": f"Ollama tidak bisa diakses. Pastikan `ollama serve` sudah berjalan.",
        }

    print(f"\n🤖 Menggunakan model: {model}")
    print(f"📋 Memproses fitur: {feature_name}")
    print("⏳ Generating test cases... (mungkin 15-60 detik)")

    prompt = build_intake_prompt(requirements_text, feature_name)
    parsed = generate_json(prompt, system_prompt=SYSTEM_PROMPT, model=model)

    if not parsed:
        return {
            "success": False,
            "error": "LLM tidak mengembalikan response yang valid. Coba lagi atau gunakan model lain.",
        }

    if "test_cases" not in parsed:
        return {
            "success": False,
            "error": f"Response tidak sesuai format. Keys ditemukan: {list(parsed.keys())}",
        }

    feature_id, cases_saved = save_to_database(
        parsed_data=parsed,
        raw_input=requirements_text,
        source=source,
        model=model,
    )

    return {
        "success": True,
        "feature_id": feature_id,
        "cases_saved": cases_saved,
        "parsed_data": parsed,
        "error": None,
    }


# ── CLI Interface ─────────────────────────────────────────────
def run_cli():
    print("\n" + "=" * 60)
    print("  DocQA Case Engine v2.0 — LLM Requirements Intake")
    print("=" * 60)

    if not check_ollama_connection():
        print("\n❌ Ollama tidak ditemukan!")
        print("   1. Install Ollama: https://ollama.ai")
        print("   2. Jalankan: ollama serve")
        print(f"   3. Pull model: ollama pull {OLLAMA_MODEL}")
        sys.exit(1)

    print(f"\n✅ Ollama aktif. Model: {OLLAMA_MODEL}")
    print("\nMasukkan nama fitur yang akan di-test:")
    feature_name = input("  Feature Name: ").strip()

    if not feature_name:
        print("❌ Feature name tidak boleh kosong.")
        sys.exit(1)

    print("\nPaste requirements / user story di bawah ini.")
    print("(Ketik 'END' di baris baru untuk selesai)\n")

    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        except EOFError:
            break

    requirements_text = "\n".join(lines).strip()

    if not requirements_text:
        print("❌ Requirements tidak boleh kosong.")
        sys.exit(1)

    result = process_requirements(
        requirements_text=requirements_text,
        feature_name=feature_name,
        source="cli",
    )

    if result["success"]:
        parsed = result["parsed_data"]
        print(f"\n✅ Berhasil!")
        print(f"   Feature ID  : {result['feature_id']}")
        print(f"   Test Cases  : {result['cases_saved']} tersimpan ke database")
        print(f"   Summary     : {parsed.get('parsed_summary', '-')}")

        print("\n📊 Risk Distribution:")
        cases = parsed.get("test_cases", [])
        risk_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for tc in cases:
            prob = int(tc.get("probability_of_failure", 1))
            impact = int(tc.get("business_impact", 1))
            level, _ = calculate_risk_level(prob, impact)
            risk_counts[level] = risk_counts.get(level, 0) + 1

        for level, count in risk_counts.items():
            bar = "█" * count
            print(f"   {level:<10}: {bar} ({count})")

        print("\n➡️  Langkah selanjutnya:")
        print("   python src/risk_engine.py    ← expand test cases di area High/Critical")
        print("   python src/curator_cli.py    ← review & approve test cases")
        print("   python src/generate_html_report.py  ← buat laporan HTML")
    else:
        print(f"\n❌ Gagal: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    run_cli()