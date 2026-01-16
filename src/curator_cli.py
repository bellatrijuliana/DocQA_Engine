# curator_cli.py
import sqlite3
import datetime
import os

# Warna untuk tampilan Terminal yang lebih profesional
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def review_session():
    conn = sqlite3.connect('data/docQA_case.db')
    c = conn.cursor()

    clear_screen()
    print(f"{Colors.HEADER}=== LEAN TEST ENGINE: QUALITY CURATOR INTERFACE ==={Colors.ENDC}")
    
    # 1. Identifikasi Reviewer
    reviewer_name = input("Enter your name (e.g., 'Radit'): ").strip()
    if not reviewer_name:
        reviewer_name = "QA_Admin"

    # 2. Fetch Pending Scenarios (Prioritas: Critical & High duluan)
    # Kita urutkan berdasarkan Custom Order: Critical > High > Medium > Low
    query = '''
        SELECT tc_id, feature_id, test_objective, test_steps, expected_result, risk_level 
        FROM test_scenarios 
        WHERE review_status = 'Pending'
        ORDER BY 
            CASE risk_level
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3
                WHEN 'LOW' THEN 4
            END ASC
    '''
    c.execute(query)
    pending_items = c.fetchall()
    total_items = len(pending_items)

    if total_items == 0:
        print(f"\n{Colors.GREEN}No pending scenarios! All caught up.{Colors.ENDC}")
        return

    print(f"\nFound {Colors.BOLD}{total_items} pending scenarios{Colors.ENDC}. Starting review session...\n")

    # 3. Interactive Loop
    processed_count = 0
    
    for item in pending_items:
        tc_id, f_id, obj, steps, exp, risk = item
        
        # Visualisasi Risk Level
        risk_color = Colors.FAIL if risk in ['CRITICAL', 'HIGH'] else Colors.BLUE
        
        print("-" * 60)
        print(f"Scenario [{processed_count + 1}/{total_items}] | ID: {tc_id}")
        print(f"Feature  : {f_id}")
        print(f"Risk     : {risk_color}{risk}{Colors.ENDC}")
        print(f"Objective: {Colors.BOLD}{obj}{Colors.ENDC}")
        print(f"Steps    : {steps}")
        print(f"Expected : {exp}")
        print("-" * 60)

        # Input Action
        while True:
            action = input(f"{Colors.WARNING}Action? [A]pprove / [R]eject / [S]kip / [Q]uit: {Colors.ENDC}").upper()
            
            if action == 'A':
                c.execute('''
                    UPDATE test_scenarios 
                    SET review_status='Approved', reviewed_by=?, created_at=? 
                    WHERE tc_id=?
                ''', (reviewer_name, datetime.datetime.now(), tc_id))
                print(f"{Colors.GREEN}>>> APPROVED.{Colors.ENDC}")
                conn.commit()
                processed_count += 1
                break
            
            elif action == 'R':
                # Opsional: Bisa menambahkan kolom 'rejection_reason' di masa depan
                c.execute('''
                    UPDATE test_scenarios 
                    SET review_status='Rejected', reviewed_by=?, created_at=? 
                    WHERE tc_id=?
                ''', (reviewer_name, datetime.datetime.now(), tc_id))
                print(f"{Colors.FAIL}>>> REJECTED.{Colors.ENDC}")
                conn.commit()
                processed_count += 1
                break
                
            elif action == 'S':
                print(">>> Skipped.")
                break # Pindah ke item berikutnya tanpa update DB
            
            elif action == 'Q':
                print("\nExiting session...")
                conn.close()
                return
            
            else:
                print("Invalid command.")

    print(f"\n{Colors.HEADER}Session Complete. Processed {processed_count} scenarios.{Colors.ENDC}")
    conn.close()

if __name__ == "__main__":
    review_session()