# src/view_case.py
import sqlite3
import pandas as pd # Sekarang kita pakai ini

def show_report():
    # 1. Koneksi ke Database
    db_path = 'data/docQA_case.db'
    conn = sqlite3.connect(db_path)

    # 2. Setting agar tampilan tabel tidak terpotong di terminal
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    pd.set_option('display.max_colwidth', 50) # Membatasi panjang teks agar rapi

    print("\n=== LEAN TEST ENGINE: REPORT DASHBOARD (POWERED BY PANDAS) ===")

    # 3. Query Data (Pandas otomatis mengubahnya jadi Tabel)
    # Kita ambil kolom yang penting-penting saja
    query = '''
    SELECT 
        tc_id, 
        feature_id, 
        risk_level, 
        review_status, 
        test_objective 
    FROM test_scenarios 
    ORDER BY 
        CASE risk_level
            WHEN 'CRITICAL' THEN 1
            WHEN 'HIGH' THEN 2
            WHEN 'MEDIUM' THEN 3
            WHEN 'LOW' THEN 4
        END ASC
    '''
    
    # Magic-nya Pandas: SQL langsung jadi DataFrame (Tabel)
    df = pd.read_sql_query(query, conn)

    # 4. Tampilkan
    if df.empty:
        print("No data found.")
    else:
        print(df)
        
        # Bonus: Hitung statistik sederhana
        print("\n--- Summary Stats ---")
        print(df['risk_level'].value_counts()) # Menghitung jumlah per Risk Level
        print("\nReview Status:")
        print(df['review_status'].value_counts()) # Menghitung berapa Pending/Approved

    conn.close()

if __name__ == "__main__":
    show_report()