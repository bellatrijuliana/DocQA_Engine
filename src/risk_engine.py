# ============================================================
# risk_engine.py — DocQA Case Engine v2.0
# Risk-Based Testing engine:
#   1. assess_all()    → LLM re-evaluasi risk semua test case
#   2. expand_risks()  → generate test case tambahan di area High/Critical
# ============================================================

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    DB_PATH, OLLAMA_MODEL, MIN_RISK_TO_EXPAND,
    MAX_GENERATED_CASES_PER_FEATURE, RISK_THRESHOLD
)
from ollama_client import generate_json, check_ollama_connection
from setup_db import get_connection
from llm_intake import calculate_risk_level


# ── Risk Level ordering ───────────────────────────────────────
RISK_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "unassessed": 0}


def _should_expand(risk_level: str) -> bool:
    """Cek apakah risk level ini perlu di-expand test cases-nya."""
    threshold = RISK_ORDER.get(MIN_RISK_TO_EXPAND.lower(), 3)
    current = RISK_ORDER.get(risk_level.lower(), 0)
    return current >= threshold


# ── 1. ASSESS RISK ────────────────────────────────────────────

ASSESS_SYSTEM_PROMPT = """You are a senior QA risk analyst.
Evaluate software test cases for risk in the context of production software.
Respond ONLY with valid JSON. No explanation or markdown."""


def _build_assess_prompt(scenario: dict) -> str:
    return f"""Re-evaluate the risk of this test scenario:

Feature: {scenario['feature_name']}
Scenario: {scenario['scenario_title']}
Type: {scenario['test_type']}
Steps: {scenario['test_steps']}
Expected Result: {scenario['expected_result']}

Assess:
- probability_of_failure: How likely is this area to have a bug? (1=very unlikely, 5=very likely)
- business_impact: If this test fails in production, how bad is it for the business? (1=trivial, 5=critical)
- risk_reasoning: 1-2 sentence explanation of your assessment

Return ONLY this JSON:
{{
  "probability_of_failure": 3,
  "business_impact": 4,
  "risk_reasoning": "Explanation here"
}}"""


def assess_all(feature_id: int = None, force_reassess: bool = False) -> dict:
    """
    LLM re-evaluasi risk semua test case (atau satu feature tertentu).
    
    Args:
        feature_id:     Jika diisi, hanya assess feature ini.
        force_reassess: Jika True, reassess bahkan yang sudah ada risk score-nya.
    
    Returns:
        dict: { assessed: int, skipped: int, errors: int }
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM test_scenarios WHERE 1=1"
    params = []

    if feature_id:
        query += " AND feature_id = ?"
        params.append(feature_id)

    if not force_reassess:
        query += " AND (risk_level = 'Unassessed' OR risk_score = 0)"

    scenarios = cursor.execute(query, params).fetchall()
    conn.close()

    if not scenarios:
        print("ℹ️  Tidak ada test case yang perlu di-assess.")
        return {"assessed": 0, "skipped": 0, "errors": 0}

    print(f"\n🔍 Assessing risk untuk {len(scenarios)} test case...")
    print(f"   Model: {OLLAMA_MODEL}\n")

    stats = {"assessed": 0, "skipped": 0, "errors": 0}

    for i, sc in enumerate(scenarios, 1):
        sc_dict = dict(sc)
        print(f"   [{i}/{len(scenarios)}] {sc_dict['scenario_title'][:55]}...", end=" ", flush=True)

        prompt = _build_assess_prompt(sc_dict)
        result = generate_json(prompt, system_prompt=ASSESS_SYSTEM_PROMPT)

        if not result:
            print("❌ (LLM error)")
            stats["errors"] += 1
            continue

        prob = int(result.get("probability_of_failure", 1))
        impact = int(result.get("business_impact", 1))
        reasoning = result.get("risk_reasoning", "")
        risk_level, risk_score = calculate_risk_level(prob, impact)

        conn = get_connection()
        conn.execute("""
            UPDATE test_scenarios
            SET probability_of_failure = ?,
                business_impact = ?,
                risk_reasoning = ?,
                risk_level = ?,
                risk_score = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (prob, impact, reasoning, risk_level, risk_score, sc_dict["id"]))
        conn.commit()
        conn.close()

        print(f"✅ {risk_level} (score: {risk_score})")
        stats["assessed"] += 1

    print(f"\n📊 Assessment selesai: {stats['assessed']} assessed, {stats['errors']} errors")
    return stats


# ── 2. EXPAND HIGH/CRITICAL RISK AREAS ───────────────────────

EXPAND_SYSTEM_PROMPT = """You are a senior QA engineer specializing in risk-based testing.
Generate additional test cases that specifically target high-risk areas.
Respond ONLY with valid JSON. No explanation or markdown."""


def _build_expand_prompt(feature_name: str, high_risk_cases: list[dict]) -> str:
    cases_summary = "\n".join([
        f"- [{tc['risk_level']}] {tc['scenario_title']}: {tc['risk_reasoning']}"
        for tc in high_risk_cases[:10]
    ])

    return f"""These HIGH/CRITICAL risk scenarios were identified for feature: {feature_name}

{cases_summary}

Based on these risk areas, generate additional test cases that:
1. Cover corner cases these high-risk scenarios might miss
2. Test failure recovery (what happens AFTER the feature fails)
3. Test concurrent/race conditions if applicable
4. Test security edge cases if applicable
5. Test data integrity scenarios

Generate up to 8 additional test cases.

Return ONLY this JSON:
{{
  "additional_cases": [
    {{
      "scenario_title": "Descriptive title",
      "test_type": "Negative|Edge Case|Boundary",
      "preconditions": "What must be true before the test",
      "test_steps": "Step 1: ...\\nStep 2: ...",
      "expected_result": "Expected behavior",
      "probability_of_failure": 4,
      "business_impact": 5,
      "risk_reasoning": "Why this additional case is important"
    }}
  ]
}}"""


def expand_risks(feature_id: int = None) -> dict:
    """
    Generate test case tambahan di area High/Critical risk.

    Args:
        feature_id: Jika diisi, hanya expand feature ini.

    Returns:
        dict: { features_expanded: int, cases_added: int }
    """
    conn = get_connection()

    # Ambil fitur-fitur yang punya High/Critical cases
    query = """
        SELECT DISTINCT feature_id, feature_name
        FROM test_scenarios
        WHERE risk_level IN ('Critical', 'High')
        AND source != 'llm_rbt'
    """
    params = []
    if feature_id:
        query += " AND feature_id = ?"
        params.append(feature_id)

    features = conn.execute(query, params).fetchall()
    conn.close()

    if not features:
        print("ℹ️  Tidak ada area High/Critical yang perlu di-expand.")
        return {"features_expanded": 0, "cases_added": 0}

    print(f"\n🚨 Expanding risk areas untuk {len(features)} fitur...\n")
    stats = {"features_expanded": 0, "cases_added": 0}

    for feat in features:
        feat_id = feat["feature_id"]
        feat_name = feat["feature_name"]

        print(f"   📌 Feature: {feat_name}")

        # Ambil semua High/Critical cases untuk fitur ini
        conn = get_connection()
        high_risk = conn.execute("""
            SELECT * FROM test_scenarios
            WHERE feature_id = ? AND risk_level IN ('Critical', 'High')
            ORDER BY risk_score DESC
        """, (feat_id,)).fetchall()
        conn.close()

        high_risk_dicts = [dict(r) for r in high_risk]
        print(f"      {len(high_risk_dicts)} High/Critical cases ditemukan")

        prompt = _build_expand_prompt(feat_name, high_risk_dicts)
        result = generate_json(prompt, system_prompt=EXPAND_SYSTEM_PROMPT)

        if not result or "additional_cases" not in result:
            print(f"      ⚠️ LLM tidak memberikan hasil untuk feature ini")
            continue

        additional = result["additional_cases"]
        added = 0

        conn = get_connection()
        for tc in additional:
            prob = int(tc.get("probability_of_failure", 1))
            impact = int(tc.get("business_impact", 1))
            risk_level, risk_score = calculate_risk_level(prob, impact)

            conn.execute("""
                INSERT INTO test_scenarios (
                    feature_id, feature_name, scenario_title, test_type,
                    preconditions, test_steps, expected_result,
                    risk_level, risk_score, probability_of_failure, business_impact,
                    risk_reasoning, source, llm_model, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'llm_rbt', ?, 'Pending')
            """, (
                feat_id, feat_name,
                tc.get("scenario_title", "RBT Expanded Case"),
                tc.get("test_type", "Edge Case"),
                tc.get("preconditions", ""),
                tc.get("test_steps", ""),
                tc.get("expected_result", ""),
                risk_level, risk_score, prob, impact,
                tc.get("risk_reasoning", ""),
                OLLAMA_MODEL,
            ))
            added += 1

        conn.commit()
        conn.close()

        print(f"      ✅ {added} test case baru ditambahkan (source: llm_rbt)")
        stats["features_expanded"] += 1
        stats["cases_added"] += added

    print(f"\n✅ Expand selesai: {stats['cases_added']} test case baru di {stats['features_expanded']} fitur")
    return stats


# ── CLI ───────────────────────────────────────────────────────
def run_cli():
    print("\n" + "=" * 60)
    print("  DocQA Case Engine v2.0 — Risk Engine")
    print("=" * 60)

    if not check_ollama_connection():
        print("\n❌ Ollama tidak aktif. Jalankan: ollama serve")
        sys.exit(1)

    print("\nPilih mode:")
    print("  1. Assess risk semua test case yang belum dinilai")
    print("  2. Expand test case di area High/Critical risk")
    print("  3. Keduanya (assess dulu, lalu expand)")

    choice = input("\nPilihan (1/2/3): ").strip()

    if choice == "1":
        assess_all()
    elif choice == "2":
        expand_risks()
    elif choice == "3":
        print("\n[Step 1/2] Assessing risk...")
        assess_all()
        print("\n[Step 2/2] Expanding High/Critical areas...")
        expand_risks()
    else:
        print("❌ Pilihan tidak valid.")
        sys.exit(1)

    print("\n➡️  Langkah selanjutnya:")
    print("   python src/curator_cli.py           ← review test cases")
    print("   python src/generate_html_report.py  ← buat laporan HTML")


if __name__ == "__main__":
    run_cli()