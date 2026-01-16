# src/generator_engine.py
import sqlite3
import datetime
import random # Digunakan untuk simulasi data dummy jika diperlukan
from requirements_data import requirements

# ==============================================================================
# LOGIC HANDLER 1: BOUNDARY VALUE ANALYSIS (BVA)
# Cocok untuk: Input Validation (Credit Card, SWIFT, Crypto, Coupon)
# Output: Positive, Negative, & Edge Cases
# ==============================================================================
def generate_bva_scenarios(req):
    scenarios = []
    field = req['params']['field']
    min_l = req['params'].get('min_len')
    max_l = req['params'].get('max_len')
    risk = req['risk']

    # --- A. POSITIVE TESTING (Valid Boundaries) ---
    scenarios.append({
        "obj": f"[BVA] Verify {field} accepts minimum valid length ({min_l} chars)",
        "step": f"1. Enter {field} with exactly {min_l} characters.\n2. Submit.",
        "exp": "System accepts the input successfully.",
        "risk": risk,
        "type": "Positive"
    })
    
    if min_l != max_l: # Hanya buat max test jika min != max
        scenarios.append({
            "obj": f"[BVA] Verify {field} accepts maximum valid length ({max_l} chars)",
            "step": f"1. Enter {field} with exactly {max_l} characters.\n2. Submit.",
            "exp": "System accepts the input successfully.",
            "risk": risk,
            "type": "Positive"
        })

    # --- B. NEGATIVE TESTING (Invalid Boundaries) ---
    # Case: Min - 1
    if min_l > 0:
        scenarios.append({
            "obj": f"[BVA] Verify {field} rejects input below minimum ({min_l - 1} chars)",
            "step": f"1. Enter {field} with {min_l - 1} characters.\n2. Submit.",
            "exp": f"System shows validation error: 'Minimum length is {min_l}'.",
            "risk": risk,
            "type": "Negative"
        })
    
    # Case: Max + 1
    scenarios.append({
        "obj": f"[BVA] Verify {field} rejects input above maximum ({max_l + 1} chars)",
        "step": f"1. Enter {field} with {max_l + 1} characters.\n2. Submit.",
        "exp": f"System shows validation error: 'Maximum length is {max_l}'.",
        "risk": risk,
        "type": "Negative"
    })

    # --- C. EDGE CASES (Empty & Special Chars) ---
    scenarios.append({
        "obj": f"[Edge] Verify {field} handling of Empty/Blank input",
        "step": f"1. Leave {field} field blank.\n2. Submit.",
        "exp": "System shows 'Required Field' error.",
        "risk": "MEDIUM", # Biasanya validasi kosong risk-nya medium
        "type": "Negative"
    })

    # Tambahan khusus untuk field angka (seperti Kartu Kredit)
    if "Card Number" in field or "SWIFT" in field:
         scenarios.append({
            "obj": f"[Edge] Verify {field} rejects Special Characters/Symbols",
            "step": f"1. Enter {field} containing symbols (@, #, $).\n2. Submit.",
            "exp": "System rejects non-alphanumeric input.",
            "risk": "HIGH",
            "type": "Negative"
        })

    return scenarios


# ==============================================================================
# LOGIC HANDLER 2: DEPENDENCY LOGIC CHECK
# Cocok untuk: Cart Logic, Discount Stacking, Legal Checkbox
# Output: Condition Met (Pos) vs Condition Not Met (Neg)
# ==============================================================================
def generate_dependency_scenarios(req):
    scenarios = []
    condition = req['params']['dependency']
    action = req['params']['action']
    risk = req['risk']

    # --- A. POSITIVE FLOW (Pre-requisite Met) ---
    scenarios.append({
        "obj": f"[Logic] Verify '{action}' is ALLOWED when {condition} is TRUE",
        "step": f"1. Ensure condition '{condition}' is met.\n2. Perform action: {action}.",
        "exp": "Action proceeds successfully / Button is Enabled.",
        "risk": risk,
        "type": "Positive"
    })

    # --- B. NEGATIVE FLOW (Pre-requisite NOT Met) ---
    scenarios.append({
        "obj": f"[Logic] Verify '{action}' is BLOCKED when {condition} is FALSE",
        "step": f"1. Ensure condition '{condition}' is NOT met.\n2. Try to perform action: {action}.",
        "exp": "Action is blocked / Button is Disabled / Error message shown.",
        "risk": risk,
        "type": "Negative"
    })

    return scenarios


# ==============================================================================
# LOGIC HANDLER 3: FUNCTIONAL FLOW & INTEGRATION
# Cocok untuk: PayPal, Wise, Western Union (3rd Party Integrations)
# Output: Happy Path & System Failure Simulation
# ==============================================================================
def generate_functional_flow(req):
    scenarios = []
    desc = req['params']['description']
    risk = req['risk']

    # --- A. HAPPY PATH (Standard Flow) ---
    scenarios.append({
        "obj": f"[Flow] Verify Standard Success Flow: {req['name']}",
        "step": f"1. Select Payment Method.\n2. {desc}",
        "exp": "System directs user to the correct page/generates correct data.",
        "risk": risk,
        "type": "Positive"
    })

    # --- B. EDGE CASE (Integration Failure) ---
    # Khusus untuk payment gateway, kita harus tes timeout/down
    scenarios.append({
        "obj": f"[Edge] Verify handling of Timeout/API Error for {req['name']}",
        "step": "1. Simulate 3rd Party API Timeout (or Network Disconnect).\n2. Attempt to proceed.",
        "exp": "System handles error gracefully (Show 'Retry' button, do not crash).",
        "risk": "HIGH", # Error handling selalu High Risk
        "type": "Negative"
    })

    return scenarios


# ==============================================================================
# MAIN ENGINE EXECUTION
# ==============================================================================
def run_engine():
    # 1. Connect DB
    db_path = 'data/docQA_case.db' # Pastikan folder 'data' ada
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    print(f"--- STARTING LEAN TEST ENGINE ---")
    print(f"--- Reading Requirements Source... ---")
    
    generated_count = 0

    for req in requirements:
        # Insert Feature Info
        c.execute("INSERT OR IGNORE INTO features VALUES (?, ?, ?, ?)", 
                  (req['id'], req['name'], req['type'], req['risk']))
        
        # ROUTER LOGIC: Pilih handler berdasarkan 'type'
        batch_scenarios = []
        
        if req['type'] == 'input_validation':
            batch_scenarios = generate_bva_scenarios(req)
        
        elif req['type'] == 'logic_check':
            batch_scenarios = generate_dependency_scenarios(req)
        
        elif req['type'] == 'functional_flow':
            batch_scenarios = generate_functional_flow(req)
        
        else:
            # Fallback jika tipe tidak dikenali
            batch_scenarios.append({
                "obj": f"Verify {req['name']}",
                "step": "Perform standard test.",
                "exp": "Pass",
                "risk": "LOW",
                "type": "Positive"
            })

        # INJECTION LOOP
        for sc in batch_scenarios:
            # Menambahkan indikator [Type] di depan objective agar mudah dibaca di report
            full_objective = f"({sc['type']}) {sc['obj']}"
            
            c.execute('''
                INSERT INTO test_scenarios 
                (feature_id, test_objective, test_steps, expected_result, risk_level, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (req['id'], full_objective, sc['step'], sc['exp'], sc['risk'], datetime.datetime.now()))
            generated_count += 1

    conn.commit()
    conn.close()
    print(f"--- SUCCESS: Generated {generated_count} Test Cases in < 1 Second. ---")
    print(f"--- Data saved to {db_path} ---")

if __name__ == "__main__":
    run_engine()