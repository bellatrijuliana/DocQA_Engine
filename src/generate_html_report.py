# ============================================================
# generate_html_report.py — DocQA Case Engine v2.0
# Generate HTML dashboard dengan Risk Matrix & coverage stats.
# ============================================================

import sqlite3
import os
import sys
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DB_PATH, REPORT_OUTPUT_PATH
from setup_db import get_connection


def fetch_data() -> dict:
    conn = get_connection()

    scenarios = [dict(r) for r in conn.execute("SELECT * FROM test_scenarios").fetchall()]
    features  = [dict(r) for r in conn.execute("SELECT * FROM features").fetchall()]

    stats = {
        "total":    len(scenarios),
        "approved": sum(1 for s in scenarios if s["status"] == "Approved"),
        "pending":  sum(1 for s in scenarios if s["status"] == "Pending"),
        "rejected": sum(1 for s in scenarios if s["status"] == "Rejected"),
    }

    risk_dist = defaultdict(int)
    for s in scenarios:
        risk_dist[s.get("risk_level", "Unassessed")] += 1

    source_dist = defaultdict(int)
    for s in scenarios:
        source_dist[s.get("source", "manual")] += 1

    type_dist = defaultdict(int)
    for s in scenarios:
        type_dist[s.get("test_type", "Unknown")] += 1

    # Risk matrix data (probability x impact grid)
    matrix = defaultdict(int)
    for s in scenarios:
        p = s.get("probability_of_failure", 0)
        i = s.get("business_impact", 0)
        if p and i:
            matrix[(p, i)] += 1

    conn.close()
    return {
        "scenarios": scenarios,
        "features": features,
        "stats": stats,
        "risk_dist": dict(risk_dist),
        "source_dist": dict(source_dist),
        "type_dist": dict(type_dist),
        "matrix": {f"{k[0]},{k[1]}": v for k, v in matrix.items()},
    }


def render_risk_badge(risk_level: str) -> str:
    colors = {
        "Critical":   "#ef4444",
        "High":       "#f97316",
        "Medium":     "#eab308",
        "Low":        "#22c55e",
        "Unassessed": "#6b7280",
    }
    color = colors.get(risk_level, "#6b7280")
    return f'<span style="background:{color};color:white;padding:2px 8px;border-radius:12px;font-size:0.75rem;font-weight:600">{risk_level}</span>'


def render_status_badge(status: str) -> str:
    colors = {
        "Approved": "#22c55e",
        "Pending":  "#6b7280",
        "Rejected": "#ef4444",
    }
    color = colors.get(status, "#6b7280")
    return f'<span style="background:{color};color:white;padding:2px 8px;border-radius:12px;font-size:0.75rem">{status}</span>'


def escape_html(text: str) -> str:
    """Escape HTML special chars untuk konten di dalam atribut/tag."""
    return (str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("\n", "<br>"))


def render_scenarios_table(scenarios: list) -> str:
    rows = ""
    for i, s in enumerate(sorted(scenarios, key=lambda x: -(x.get("risk_score") or 0))):
        sid = f"row_{i}"
        precond   = escape_html(s.get("preconditions", "") or "-")
        steps     = escape_html(s.get("test_steps", "") or "-")
        expected  = escape_html(s.get("expected_result", "") or "-")
        reasoning = escape_html(s.get("risk_reasoning", "") or "-")
        prob      = s.get("probability_of_failure", 0)
        impact    = s.get("business_impact", 0)

        rows += f"""
        <tr class="summary-row" onclick="toggleDetail(\'{sid}\')" style="cursor:pointer">
            <td style="max-width:160px">
                <span style="color:#64748b;font-size:0.7rem;margin-right:6px" id="icon_{sid}">▶</span>
                {s.get("feature_name","")}
            </td>
            <td style="max-width:300px">{s.get("scenario_title","")}</td>
            <td style="font-size:0.78rem;color:#94a3b8">{s.get("test_type","")}</td>
            <td style="text-align:center">{render_risk_badge(s.get("risk_level","Unassessed"))}</td>
            <td style="text-align:center;font-weight:700">{s.get("risk_score",0)}</td>
            <td style="text-align:center">{render_status_badge(s.get("status","Pending"))}</td>
            <td style="text-align:center;font-size:0.75rem;color:#6b7280">{s.get("source","manual")}</td>
        </tr>
        <tr class="detail-row" id="{sid}" style="display:none">
            <td colspan="7" style="padding:0;border-bottom:2px solid #334155">
                <div class="detail-panel">
                    <div class="detail-grid">
                        <div class="detail-block">
                            <div class="detail-label">📋 Preconditions</div>
                            <div class="detail-content">{precond}</div>
                        </div>
                        <div class="detail-block">
                            <div class="detail-label">🧪 Test Steps</div>
                            <div class="detail-content">{steps}</div>
                        </div>
                        <div class="detail-block">
                            <div class="detail-label">✅ Expected Result</div>
                            <div class="detail-content">{expected}</div>
                        </div>
                        <div class="detail-block">
                            <div class="detail-label">⚠️ Risk Reasoning</div>
                            <div class="detail-content">{reasoning}</div>
                        </div>
                    </div>
                    <div class="detail-meta">
                        <span>Probability of Failure: <strong>{prob}/5</strong></span>
                        <span style="margin:0 12px">·</span>
                        <span>Business Impact: <strong>{impact}/5</strong></span>
                        <span style="margin:0 12px">·</span>
                        <span>Risk Score: <strong>{s.get("risk_score",0)}/25</strong></span>
                        <span style="margin:0 12px">·</span>
                        <span>LLM Model: <strong>{s.get("llm_model") or "-"}</strong></span>
                    </div>
                </div>
            </td>
        </tr>"""
    return rows


def render_matrix_cell(count: int, prob: int, impact: int) -> str:
    score = prob * impact
    if score >= 20:
        bg = "#ef4444"
    elif score >= 12:
        bg = "#f97316"
    elif score >= 6:
        bg = "#eab308"
    else:
        bg = "#22c55e"

    opacity = min(0.3 + (count * 0.2), 1.0) if count else 0
    style = f"background:{'rgba(0,0,0,0.05)' if not count else bg};opacity:{max(opacity, 0.08) if count else 0.08}"

    return f'<td style="{style};width:60px;height:60px;text-align:center;font-weight:600;border-radius:6px">' \
           f'{"" if not count else count}</td>'


def generate_report(output_path: str = None) -> str:
    output_path = output_path or REPORT_OUTPUT_PATH
    data = fetch_data()
    st   = data["stats"]
    rd   = data["risk_dist"]
    sd   = data["source_dist"]
    td   = data["type_dist"]
    mx   = data["matrix"]
    now  = datetime.now().strftime("%d %B %Y, %H:%M")

    approval_pct = round((st["approved"] / st["total"] * 100) if st["total"] else 0)

    # Risk matrix rows (probability Y: 5→1, impact X: 1→5)
    matrix_rows = ""
    for prob in range(5, 0, -1):
        matrix_rows += f'<tr><td style="text-align:right;padding-right:8px;font-weight:600;color:#6b7280">{prob}</td>'
        for impact in range(1, 6):
            count = mx.get(f"{prob},{impact}", 0)
            matrix_rows += render_matrix_cell(count, prob, impact)
        matrix_rows += "</tr>"

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DocQA Case Engine — Test Report</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }}
  .header {{ background: linear-gradient(135deg, #1e293b, #0f172a); border-bottom: 1px solid #334155; padding: 32px 40px; }}
  .header h1 {{ font-size: 1.8rem; font-weight: 700; color: #f1f5f9; }}
  .header p {{ color: #94a3b8; margin-top: 4px; font-size: 0.9rem; }}
  .container {{ max-width: 1400px; margin: 0 auto; padding: 32px 40px; }}
  .grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 32px; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 32px; }}
  .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 24px; }}
  .stat-card .label {{ color: #94a3b8; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; }}
  .stat-card .value {{ font-size: 2.5rem; font-weight: 700; margin-top: 8px; }}
  .stat-card .sub {{ color: #64748b; font-size: 0.8rem; margin-top: 4px; }}
  .section-title {{ font-size: 1rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 16px; }}
  .risk-bar {{ display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }}
  .risk-bar .label {{ width: 90px; font-size: 0.85rem; }}
  .risk-bar .bar-wrap {{ flex: 1; background: #334155; border-radius: 4px; height: 8px; }}
  .risk-bar .bar {{ height: 8px; border-radius: 4px; transition: width 0.3s; }}
  .risk-bar .count {{ font-size: 0.8rem; color: #64748b; width: 30px; text-align: right; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
  th {{ padding: 10px 12px; text-align: left; color: #64748b; font-weight: 600; border-bottom: 1px solid #334155; font-size: 0.75rem; text-transform: uppercase; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #1e293b; vertical-align: top; word-break: break-word; }}
  tr:hover td {{ background: #1a2744; }}
  .matrix-table td, .matrix-table th {{ width: 64px; height: 64px; text-align: center; border: none; }}
  .progress-ring {{ color: #3b82f6; font-size: 1.1rem; font-weight: 700; }}
  .tag {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: 600; margin: 2px; }}
  .scrollable {{ max-height: 480px; overflow-y: auto; }}
  .scrollable::-webkit-scrollbar {{ width: 6px; }} 
  .scrollable::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 3px; }}
  .summary-row:hover td {{ background: #1a2744; }}
  .detail-row td {{ background: #131f35 !important; }}
  .detail-panel {{ padding: 20px 24px 16px; }}
  .detail-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 14px; }}
  .detail-block {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 14px 16px; }}
  .detail-label {{ font-size: 0.72rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; }}
  .detail-content {{ font-size: 0.83rem; color: #cbd5e1; line-height: 1.65; white-space: pre-wrap; }}
  .detail-meta {{ font-size: 0.78rem; color: #64748b; padding-top: 10px; border-top: 1px solid #1e293b; }}
  .detail-meta strong {{ color: #94a3b8; }}
  .footer {{ text-align: center; padding: 32px; color: #334155; font-size: 0.8rem; }}
</style>
</head>
<body>

<div class="header">
  <h1>📋 DocQA Case Engine — Test Report</h1>
  <p>Generated: {now} &nbsp;·&nbsp; Risk-Based Testing Report v2.0</p>
</div>

<div class="container">

  <!-- Stat Cards -->
  <div class="grid-4">
    <div class="card stat-card">
      <div class="label">Total Test Cases</div>
      <div class="value" style="color:#3b82f6">{st['total']}</div>
    </div>
    <div class="card stat-card">
      <div class="label">Approved</div>
      <div class="value" style="color:#22c55e">{st['approved']}</div>
      <div class="sub">{approval_pct}% approval rate</div>
    </div>
    <div class="card stat-card">
      <div class="label">Pending Review</div>
      <div class="value" style="color:#94a3b8">{st['pending']}</div>
    </div>
    <div class="card stat-card">
      <div class="label">Rejected</div>
      <div class="value" style="color:#ef4444">{st['rejected']}</div>
    </div>
  </div>

  <div class="grid-2">
    <!-- Risk Distribution -->
    <div class="card">
      <div class="section-title">Risk Distribution</div>
      {''.join([
        '<div class="risk-bar">'
        f'<div class="label" style="color:{color}">{level}</div>'
        f'<div class="bar-wrap"><div class="bar" style="width:{round(count/st["total"]*100) if st["total"] else 0}%;background:{color}"></div></div>'
        f'<div class="count">{count}</div>'
        '</div>'
        for level, count, color in [
            ("Critical",   rd.get("Critical",   0), "#ef4444"),
            ("High",       rd.get("High",       0), "#f97316"),
            ("Medium",     rd.get("Medium",     0), "#eab308"),
            ("Low",        rd.get("Low",        0), "#22c55e"),
            ("Unassessed", rd.get("Unassessed", 0), "#6b7280"),
        ]
      ])}
    </div>

    <!-- Source & Type Distribution -->
    <div class="card">
      <div class="section-title">Test Case Sources</div>
      {''.join([
        '<div class="risk-bar">'
        f'<div class="label" style="color:#94a3b8">{ {"manual":"Manual","bva_engine":"BVA Engine","llm_intake":"LLM Intake","llm_rbt":"LLM RBT"}.get(src, src) }</div>'
        f'<div class="bar-wrap"><div class="bar" style="width:{round(count/st["total"]*100) if st["total"] else 0}%;background:#3b82f6"></div></div>'
        f'<div class="count">{count}</div>'
        '</div>'
        for src, count in sd.items()
      ])}

      <div class="section-title" style="margin-top:20px">Test Types</div>
      <div style="display:flex;flex-wrap:wrap;gap:6px">
        {''.join([
          f'<span class="tag" style="background:#1e3a5f;color:#93c5fd">{t}: {c}</span>'
          for t, c in td.items()
        ])}
      </div>
    </div>
  </div>

  <!-- Risk Matrix -->
  <div class="card" style="margin-bottom:32px">
    <div class="section-title">Risk Matrix (Probability × Business Impact)</div>
    <div style="display:flex;align-items:flex-start;gap:24px;margin-top:8px">
      <div>
        <div style="font-size:0.75rem;color:#64748b;writing-mode:vertical-rl;transform:rotate(180deg);text-align:center;height:300px;display:flex;align-items:center">
          Probability of Failure →
        </div>
      </div>
      <div>
        <table class="matrix-table" style="border-collapse:separate;border-spacing:4px">
          {matrix_rows}
          <tr>
            <td></td>
            {''.join([f'<td style="text-align:center;font-weight:600;color:#6b7280;height:24px">{i}</td>' for i in range(1,6)])}
          </tr>
          <tr>
            <td></td>
            <td colspan="5" style="text-align:center;color:#64748b;font-size:0.75rem;padding-top:4px">Business Impact →</td>
          </tr>
        </table>
      </div>
      <div style="margin-left:16px">
        <div style="font-size:0.75rem;color:#64748b;margin-bottom:8px">Legend</div>
        {''.join([
          f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px"><div style="width:16px;height:16px;background:{c};border-radius:3px"></div><span style="font-size:0.8rem;color:#94a3b8">{l}</span></div>'
          for l, c in [("Critical (≥20)", "#ef4444"), ("High (≥12)", "#f97316"), ("Medium (≥6)", "#eab308"), ("Low (<6)", "#22c55e")]
        ])}
      </div>
    </div>
  </div>

  <!-- Test Case Table -->
  <div class="card">
    <div class="section-title">All Test Scenarios (sorted by risk score)</div>
    <div class="scrollable">
      <table>
        <thead>
          <tr>
            <th>Feature</th>
            <th>Scenario</th>
            <th>Type</th>
            <th style="text-align:center">Risk</th>
            <th style="text-align:center">Score</th>
            <th style="text-align:center">Status</th>
            <th style="text-align:center">Source</th>
          </tr>
        </thead>
        <tbody>
          {render_scenarios_table(data['scenarios'])}
        </tbody>
      </table>
    </div>
  </div>

</div>

<script>
function toggleDetail(id) {{
  var row = document.getElementById(id);
  var icon = document.getElementById('icon_' + id);
  if (row.style.display === 'none') {{
    row.style.display = 'table-row';
    icon.textContent = '▼';
    icon.style.color = '#3b82f6';
  }} else {{
    row.style.display = 'none';
    icon.textContent = '▶';
    icon.style.color = '#64748b';
  }}
}}
</script>
<div class="footer">DocQA Case Engine v2.0 · Risk-Based Testing Report · {now}</div>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Report generated: {output_path}")
    return output_path


if __name__ == "__main__":
    print("Generating HTML report...")
    path = generate_report()
    print(f"   Buka: file://{os.path.abspath(path)}")