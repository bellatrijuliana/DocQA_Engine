# ============================================================
# setup_db.py — DocQA Case Engine v2.0
# Inisialisasi database + schema upgrade dengan risk columns.
# Aman dijalankan ulang (tidak menghapus data existing).
# ============================================================

import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def setup_database():
    print("=" * 55)
    print("  DocQA Case Engine v2.0 — Database Setup")
    print("=" * 55)

    conn = get_connection()
    cursor = conn.cursor()

    # ── Tabel: features ─────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS features (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL UNIQUE,
            description     TEXT,
            module          TEXT,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ Tabel 'features' siap.")

    # ── Tabel: test_scenarios ────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_scenarios (
            id                     INTEGER PRIMARY KEY AUTOINCREMENT,
            feature_id             INTEGER REFERENCES features(id),
            feature_name           TEXT,
            scenario_title         TEXT NOT NULL,
            test_type              TEXT,
            preconditions          TEXT,
            test_steps             TEXT,
            expected_result        TEXT,
            status                 TEXT DEFAULT 'Pending',
            risk_level             TEXT DEFAULT 'Unassessed',
            risk_score             INTEGER DEFAULT 0,
            probability_of_failure INTEGER DEFAULT 0,
            business_impact        INTEGER DEFAULT 0,
            risk_reasoning         TEXT,
            source                 TEXT DEFAULT 'manual',
            llm_model              TEXT,
            created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ Tabel 'test_scenarios' siap.")

    # ── Tabel: requirements_log ──────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requirements_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_input       TEXT NOT NULL,
            feature_name    TEXT,
            parsed_summary  TEXT,
            cases_generated INTEGER DEFAULT 0,
            llm_model       TEXT,
            source          TEXT DEFAULT 'cli',
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ Tabel 'requirements_log' siap.")

    # ── Upgrade: tambah kolom baru jika DB berasal dari v1.0 ─
    # Mencakup 'status' karena v1.0 mungkin belum punya kolom ini.
    new_columns = [
        ("test_scenarios", "status",                  "TEXT DEFAULT 'Pending'"),
        ("test_scenarios", "risk_level",              "TEXT DEFAULT 'Unassessed'"),
        ("test_scenarios", "risk_score",              "INTEGER DEFAULT 0"),
        ("test_scenarios", "probability_of_failure",  "INTEGER DEFAULT 0"),
        ("test_scenarios", "business_impact",         "INTEGER DEFAULT 0"),
        ("test_scenarios", "risk_reasoning",          "TEXT"),
        ("test_scenarios", "source",                  "TEXT DEFAULT 'manual'"),
        ("test_scenarios", "llm_model",               "TEXT"),
        ("test_scenarios", "updated_at",              "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ]

    existing_cols = {
        row[1] for row in cursor.execute("PRAGMA table_info(test_scenarios)")
    }

    upgraded = 0
    for table, col, col_def in new_columns:
        if col not in existing_cols:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")
            upgraded += 1

    if upgraded:
        print(f"🔄 Schema upgrade: {upgraded} kolom baru ditambahkan.")
    else:
        print("ℹ️  Schema sudah up-to-date.")

    # ── Commit ALTER sebelum buat index ──────────────────────
    # PENTING: index harus dibuat setelah kolom hasil ALTER di-commit,
    # karena SQLite tidak selalu mengenali kolom baru dalam transaksi yang sama.
    conn.commit()

    # ── Index untuk performa query ───────────────────────────
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_risk_level
        ON test_scenarios(risk_level)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_status
        ON test_scenarios(status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_source
        ON test_scenarios(source)
    """)

    conn.commit()
    conn.close()

    print("\n✅ Database siap di:", DB_PATH)
    print("=" * 55)


if __name__ == "__main__":
    setup_database()