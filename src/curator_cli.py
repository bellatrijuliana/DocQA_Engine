# ============================================================
# curator_cli.py — DocQA Case Engine v2.0
# Interactive CLI untuk review, approve, reject test cases.
# Prioritas: Critical → High → Medium → Low → Unassessed
# ============================================================

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import REVIEW_RISK_LEVELS
from setup_db import get_connection


# ── Warna terminal (ANSI) ─────────────────────────────────────
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    GREEN  = "\033[92m"
    BLUE   = "\033[94m"
    CYAN   = "\033[96m"
    GRAY   = "\033[90m"
    WHITE  = "\033[97m"
    BG_RED = "\033[41m"


RISK_COLOR = {
    "Critical":   C.RED + C.BOLD,
    "High":       C.YELLOW + C.BOLD,
    "Medium":     C.CYAN,
    "Low":        C.GREEN,
    "Unassessed": C.GRAY,
}

SOURCE_LABEL = {
    "manual":     "Manual",
    "bva_engine": "BVA Engine",
    "llm_intake": "LLM Intake",
    "llm_rbt":    "LLM RBT Expand",
}


def print_header():
    print(C.BOLD + "\n" + "═" * 65)
    print("   DocQA Case Engine v2.0 — Quality Curator")
    print("═" * 65 + C.RESET)


def print_scenario(sc: dict, current: int, total: int):
    risk = sc.get("risk_level", "Unassessed")
    score = sc.get("risk_score", 0)
    prob = sc.get("probability_of_failure", 0)
    impact = sc.get("business_impact", 0)
    source = SOURCE_LABEL.get(sc.get("source", "manual"), sc.get("source", "-"))
    color = RISK_COLOR.get(risk, C.GRAY)

    print(f"\n{C.GRAY}[{current}/{total}]{C.RESET}  "
          f"{color}◆ {risk.upper()} RISK{C.RESET}  "
          f"{C.GRAY}Score: {score}/25  (P:{prob} × I:{impact}){C.RESET}  "
          f"{C.GRAY}Source: {source}{C.RESET}")

    print("─" * 65)
    print(f"{C.BOLD}Feature  :{C.RESET} {sc.get('feature_name', '-')}")
    print(f"{C.BOLD}Title    :{C.RESET} {sc.get('scenario_title', '-')}")
    print(f"{C.BOLD}Type     :{C.RESET} {sc.get('test_type', '-')}")

    if sc.get("preconditions"):
        print(f"\n{C.BOLD}Preconditions:{C.RESET}")
        print(f"  {sc['preconditions']}")

    if sc.get("test_steps"):
        print(f"\n{C.BOLD}Test Steps:{C.RESET}")
        for line in sc["test_steps"].split("\n"):
            if line.strip():
                print(f"  {line}")

    if sc.get("expected_result"):
        print(f"\n{C.BOLD}Expected Result:{C.RESET}")
        print(f"  {sc['expected_result']}")

    if sc.get("risk_reasoning"):
        print(f"\n{C.BOLD}Risk Reasoning:{C.RESET}")
        print(f"  {C.GRAY}{sc['risk_reasoning']}{C.RESET}")

    print("─" * 65)


def print_summary():
    conn = get_connection()
    rows = conn.execute("""
        SELECT risk_level, status, COUNT(*) as count
        FROM test_scenarios
        GROUP BY risk_level, status
        ORDER BY
            CASE risk_level
                WHEN 'Critical' THEN 1
                WHEN 'High'     THEN 2
                WHEN 'Medium'   THEN 3
                WHEN 'Low'      THEN 4
                ELSE 5
            END
    """).fetchall()

    total = conn.execute("SELECT COUNT(*) FROM test_scenarios").fetchone()[0]
    approved = conn.execute("SELECT COUNT(*) FROM test_scenarios WHERE status = 'Approved'").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM test_scenarios WHERE status = 'Pending'").fetchone()[0]
    rejected = conn.execute("SELECT COUNT(*) FROM test_scenarios WHERE status = 'Rejected'").fetchone()[0]
    conn.close()

    print(f"\n{C.BOLD}📊 Database Summary:{C.RESET}")
    print(f"   Total     : {total}")
    print(f"   {C.GREEN}Approved  : {approved}{C.RESET}")
    print(f"   {C.GRAY}Pending   : {pending}{C.RESET}")
    print(f"   {C.RED}Rejected  : {rejected}{C.RESET}")

    print(f"\n{C.BOLD}Risk Distribution:{C.RESET}")
    risk_totals: dict[str, int] = {}
    for row in rows:
        rl = row["risk_level"]
        risk_totals[rl] = risk_totals.get(rl, 0) + row["count"]

    for level in ["Critical", "High", "Medium", "Low", "Unassessed"]:
        count = risk_totals.get(level, 0)
        color = RISK_COLOR.get(level, C.GRAY)
        bar = "█" * min(count, 30)
        print(f"   {color}{level:<12}{C.RESET}: {bar} ({count})")


def run_curator(risk_filter: list[str] = None, feature_id: int = None):
    """
    Jalankan curator session.

    Args:
        risk_filter: List risk level yang akan di-review.
                     Default: semua Pending.
        feature_id:  Filter ke satu feature tertentu.
    """
    print_header()
    print_summary()

    # Build query
    query = "SELECT * FROM test_scenarios WHERE status = 'Pending'"
    params = []

    if risk_filter:
        placeholders = ",".join("?" * len(risk_filter))
        query += f" AND risk_level IN ({placeholders})"
        params.extend(risk_filter)

    if feature_id:
        query += " AND feature_id = ?"
        params.append(feature_id)

    query += """
        ORDER BY
            CASE risk_level
                WHEN 'Critical' THEN 1
                WHEN 'High'     THEN 2
                WHEN 'Medium'   THEN 3
                WHEN 'Low'      THEN 4
                ELSE 5
            END,
            risk_score DESC
    """

    conn = get_connection()
    scenarios = conn.execute(query, params).fetchall()
    conn.close()

    if not scenarios:
        print(f"\n{C.GREEN}✅ Tidak ada test case Pending untuk di-review!{C.RESET}")
        return

    print(f"\n{C.BOLD}📋 {len(scenarios)} test case siap di-review{C.RESET}")

    if risk_filter:
        filter_str = ", ".join(risk_filter)
        print(f"   Filter risk: {filter_str}")

    print(f"\nKontrol: {C.GREEN}[A]{C.RESET} Approve  "
          f"{C.RED}[R]{C.RESET} Reject  "
          f"{C.YELLOW}[S]{C.RESET} Skip  "
          f"{C.BLUE}[Q]{C.RESET} Quit\n")

    approved = rejected = skipped = 0

    for i, sc in enumerate(scenarios, 1):
        sc_dict = dict(sc)
        print_scenario(sc_dict, i, len(scenarios))

        while True:
            choice = input(f"\n{C.BOLD}Action [A/R/S/Q]:{C.RESET} ").strip().upper()

            if choice in ("A", "R", "S", "Q"):
                break
            print(f"  {C.GRAY}Tekan A (Approve), R (Reject), S (Skip), atau Q (Quit){C.RESET}")

        if choice == "Q":
            print(f"\n{C.YELLOW}Session dihentikan.{C.RESET}")
            break
        elif choice == "A":
            conn = get_connection()
            conn.execute(
                "UPDATE test_scenarios SET status = 'Approved', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (sc_dict["id"],)
            )
            conn.commit()
            conn.close()
            print(f"  {C.GREEN}✅ Approved{C.RESET}")
            approved += 1
        elif choice == "R":
            conn = get_connection()
            conn.execute(
                "UPDATE test_scenarios SET status = 'Rejected', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (sc_dict["id"],)
            )
            conn.commit()
            conn.close()
            print(f"  {C.RED}✗ Rejected{C.RESET}")
            rejected += 1
        elif choice == "S":
            print(f"  {C.GRAY}→ Skipped{C.RESET}")
            skipped += 1

    print(f"\n{'─' * 65}")
    print(f"  Session selesai:")
    print(f"  {C.GREEN}Approved : {approved}{C.RESET}")
    print(f"  {C.RED}Rejected : {rejected}{C.RESET}")
    print(f"  {C.GRAY}Skipped  : {skipped}{C.RESET}")
    print(f"{'─' * 65}")

    print(f"\n➡️  Langkah selanjutnya:")
    print(f"   python src/generate_html_report.py  ← buat laporan HTML")


# ── CLI ───────────────────────────────────────────────────────
if __name__ == "__main__":
    print_header()
    print("\nMode review:")
    print("  1. Review semua Pending (semua risk level)")
    print("  2. Review Critical & High saja (prioritas)")
    print("  3. Review berdasarkan feature tertentu")

    mode = input("\nPilihan (1/2/3): ").strip()

    if mode == "1":
        run_curator()
    elif mode == "2":
        run_curator(risk_filter=["Critical", "High"])
    elif mode == "3":
        conn = get_connection()
        features = conn.execute(
            "SELECT DISTINCT feature_id, feature_name FROM test_scenarios WHERE status = 'Pending'"
        ).fetchall()
        conn.close()

        if not features:
            print("Tidak ada Pending test case.")
            sys.exit(0)

        print("\nFeature tersedia:")
        for f in features:
            print(f"  [{f['feature_id']}] {f['feature_name']}")

        feat_id = input("\nMasukkan Feature ID: ").strip()
        try:
            run_curator(feature_id=int(feat_id))
        except ValueError:
            print("❌ ID tidak valid.")
            sys.exit(1)
    else:
        print("❌ Pilihan tidak valid.")
        sys.exit(1)