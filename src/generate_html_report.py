import sqlite3
import pandas as pd
import webbrowser
import os

def generate_html():
    # 1. Koneksi Database
    db_path = 'data/docQA_case.db'
    conn = sqlite3.connect(db_path)

    # 2. Query Data (Ambil data yang diperlukan)
    query = '''
    SELECT 
        feature_id AS "Feature ID",
        risk_level AS "Risk Level",
        review_status AS "Status",
        test_objective AS "Test Scenario",
        expected_result AS "Expected Result",
        reviewed_by AS "QA Reviewer"
    FROM test_scenarios 
    ORDER BY 
        CASE risk_level
            WHEN 'CRITICAL' THEN 1
            WHEN 'HIGH' THEN 2
            WHEN 'MEDIUM' THEN 3
            WHEN 'LOW' THEN 4
        END ASC
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("Data kosong. Jalankan generator dulu.")
        return

    # 3. Statistik Ringkas (Untuk Header Laporan)
    total_cases = len(df)
    critical_count = len(df[df['Risk Level'] == 'CRITICAL'])
    pending_count = len(df[df['Status'] == 'Pending'])
    
    # 4. Styling dengan Pandas (Memberi warna pada baris)
    # Kita tidak ubah data, cuma styling HTML-nya nanti via CSS class
    
    # 5. Membuat Template HTML (CSS + Struktur)
    # Ini adalah "Wajah" laporan Anda.
    html_template = f"""
    <html>
    <head>
        <title>DocQA Engine - Custom Test Case Management </title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #f4f4f9; }}
            h1 {{ color: #333; }}
            .summary-box {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 30px; display: flex; gap: 40px; }}
            .stat {{ text-align: center; }}
            .stat-number {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
            .stat-label {{ font-size: 14px; color: #7f8c8d; text-transform: uppercase; }}
            
            table {{ border-collapse: collapse; width: 100%; box-shadow: 0 2px 15px rgba(0,0,0,0.1); background: white; border-radius: 8px; overflow: hidden; }}
            th {{ background-color: #009879; color: #ffffff; text-align: left; padding: 12px 15px; }}
            td {{ padding: 12px 15px; border-bottom: 1px solid #dddddd; }}
            tr:nth-of-type(even) {{ background-color: #f3f3f3; }}
            tr:last-of-type {{ border-bottom: 2px solid #009879; }}
            
            /* Warna khusus untuk Risk Level */
            td:nth-child(2) {{ font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>DocQA Report</h1>
        <p>Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary-box">
            <div class="stat">
                <div class="stat-number">{total_cases}</div>
                <div class="stat-label">Total Scenarios</div>
            </div>
            <div class="stat">
                <div class="stat-number" style="color: #e74c3c;">{critical_count}</div>
                <div class="stat-label">Critical Risks</div>
            </div>
            <div class="stat">
                <div class="stat-number" style="color: #f39c12;">{pending_count}</div>
                <div class="stat-label">Pending Review</div>
            </div>
        </div>

        {df.to_html(index=False, border=0, classes='table')}
        
    </body>
    </html>
    """

    # 6. Simpan ke File HTML
    output_file = "test_case.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_template)

    print(f"✅ Test Case Management HTML berhasil dibuat: {output_file}")
    
    # 7. Auto-Open (Otomatis buka di Browser)
    webbrowser.open('file://' + os.path.realpath(output_file))

if __name__ == "__main__":
    generate_html()