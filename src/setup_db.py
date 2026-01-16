import sqlite3

def init_db():
    conn = sqlite3.connect('data/docQA_case.db')
    cursor = conn.cursor()

# Table Features
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS features (
            feature_id TEXT PRIMARY KEY,
            feature_name TEXT,
            category TEXT,
            base_risk TEXT
        )                             
    ''')

# Table Test Scenarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_scenarios (
            tc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature_id TEXT,
            test_objective TEXT,
            test_steps TEXT,
            expected_result TEXT,
            risk_level TEXT,
            review_status TEXT DEFAULT 'Pending',
            reviewed_by TEXT DEFAULT NULL,
            created_at DATETIME,
            FOREIGN KEY(feature_id) REFERENCES features(feature_id)
        )
    ''')
   
    conn.commit()
    conn.close()

    print("Database and Schema initialized successfully.")

if __name__ == "__main__":
    init_db()   