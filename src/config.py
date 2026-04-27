# ============================================================
# config.py — DocQA Case Engine v2.0
# Centralized configuration. Edit here, affects all modules.
# ============================================================

# --- Ollama Settings ---
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "gemma3:1b"
OLLAMA_TIMEOUT = 180

# --- Database ---
DB_PATH = "data/docQA_case.db"

# --- Risk Thresholds ---
# Risk Score = (Probability of Failure * Business Impact)
# Max = 25 (5x5)
RISK_THRESHOLD = {
    "critical": 20,   # Score >= 20
    "high":     12,   # Score >= 12
    "medium":    6,   # Score >= 6
    # Below 6 = Low
}

# --- LLM Generation Settings ---
MAX_GENERATED_CASES_PER_FEATURE = 15   # Batas test case per fitur dari LLM
MIN_RISK_TO_EXPAND = "high"            # Minimum risk level untuk auto-expand test cases
                                        # Options: "critical", "high", "medium"

# --- Curator CLI ---
REVIEW_RISK_LEVELS = ["critical", "high","medium"]  # Risk level yang wajib di-review manual

# --- HTML Report ---
REPORT_OUTPUT_PATH = "test_report.html"