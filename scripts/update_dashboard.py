#!/usr/bin/env python3
"""Regenerate the Magnite Connection Health dashboard from Trino.

Runs in GitHub Actions (or locally). Auth follows the publisher_pnl pattern:
Google OAuth token in ~/.config/seedtag/token.json (or ./token.json, written
from the GOOGLE_TOKEN secret in CI), auto-refreshed on every request.

Single dataset, per the validated reference query: daily grain x channel x
editorial group x publisher x source type x ad unit, scoped to publishers with
MagniteDirect activity in the window. All KPIs/charts/tables are computed
client-side so the four filters (editorial group, publisher, source type,
ad unit) apply to every section.

Missing warehouse partitions are backfilled from data/date_snapshots.json
(written on every run from the dates that ARE present) and flagged as
"pending warehouse restore" — never rendered as zeros.

Output: index.html at repo root; --upload also upserts it to Google Drive.
"""
import json
import os
import sys
import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trino_client import run_trino_query

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = Path(os.getenv("SEEDTAG_CONFIG_DIR", Path.home() / ".config" / "seedtag"))
DRIVE_SA_JSON = os.getenv("DRIVE_SA_JSON", "prj-jdpa-560863a21518.json")
DRIVE_ROOT_FOLDER_ID = os.getenv("DRIVE_ROOT_FOLDER_ID", "1TAFpUwZLeat4wNWPYeQGayLE56UMfBvl")
DRIVE_SUBFOLDER = os.getenv("DRIVE_SUBFOLDER", "Magnite Direct")
DRIVE_FILENAME = os.getenv("DRIVE_FILENAME", "index.html")

TABLE = "st_datalakehouse.analytics.etl_ssp_supply_funnel_daily_local"
WINDOW_START = dt.date(2026, 7, 1)
MD_LAUNCH = dt.date(2026, 7, 10)
TAG = "-- @user:juanperez@seedtag.com @skill:barbi"
SNAPSHOT_PATH = PROJECT_ROOT / "data" / "date_snapshots.json"

# HB-family source types: their effective win is the on-page header-auction
# win (hb_wins); every other source delivers from the SSP win itself.
HB_FAMILY = ("HeaderBidding", "PrebidServer", "Tam", "Gob")


def pack(r, base_date):
    """Row -> compact array; layout documented in the JS header comment."""
    d_idx = (dt.date.fromisoformat(str(r["date"])[:10]) - base_date).days
    return [
        d_idx,
        1 if r["channel_id"] == "MagniteDirect" else 0,
        r["editorial_group_name"] or "",
        r["source_type"] or "",
        r["adunit_type"] or "",
        r["publisher_name"] or "",
        round(float(r["gross_revenue_eur"] or 0), 2),
        round(float(r["omp_gross_revenue_eur"] or 0), 2),
        round(float(r["publisher_revenue_eur"] or 0), 2),
        int(r["bids"] or 0),
        int(r["wins"] or 0),
        int(r["hb_wins"] or 0),
        int(r["imps_sold"] or 0),
        int(r["imps_paid"] or 0),
    ]


def main():
    madrid_now = dt.datetime.now(ZoneInfo("Europe/Madrid"))
    end = madrid_now.date() - dt.timedelta(days=1)  # latest closed day (T-1)
    start = WINDOW_START
    d1, d2 = start.isoformat(), end.isoformat()
    hb_list = ",".join(f"'{s}'" for s in HB_FAMILY)

    sql_main = f"""{TAG}
WITH magnite_publishers AS (
  SELECT DISTINCT publisher_name
  FROM {TABLE}
  WHERE date BETWEEN DATE '{d1}' AND DATE '{d2}'
    AND channel_id = 'MagniteDirect'
    AND source_type IS DISTINCT FROM 'Beachfront'
)
SELECT
  f.date, f.channel_id, f.editorial_group_name, f.publisher_name, f.source_type, f.adunit_type,
  SUM(f.bids) AS bids,
  SUM(f.wins) AS wins,
  SUM(f.hb_wins) AS hb_wins,
  SUM(f.imps_sold) AS imps_sold,
  SUM(f.imps_paid) AS imps_paid,
  SUM(f.revenue_st_eur) AS gross_revenue_eur,
  SUM(f.publisher_revenue_eur) AS publisher_revenue_eur,
  SUM(CASE WHEN f.product_short_code LIKE 'O%' THEN f.revenue_st_eur ELSE 0 END) AS omp_gross_revenue_eur,
  -- Win Rate = HB wins / SSP wins — HB-family sources only, NULL elsewhere
  IF(SUM(CASE WHEN f.source_type IN ({hb_list}) THEN f.wins ELSE 0 END) = 0, NULL,
     SUM(CASE WHEN f.source_type IN ({hb_list}) THEN f.hb_wins ELSE 0 END) * 1.0 /
     SUM(CASE WHEN f.source_type IN ({hb_list}) THEN f.wins ELSE 0 END)) AS win_rate,
  -- Imp Rate = impressions sold / SSP wins — non-HB (Tag-family) sources only, NULL elsewhere
  IF(SUM(CASE WHEN f.source_type NOT IN ({hb_list}) THEN f.wins ELSE 0 END) = 0, NULL,
     SUM(CASE WHEN f.source_type NOT IN ({hb_list}) THEN f.imps_sold ELSE 0 END) * 1.0 /
     SUM(CASE WHEN f.source_type NOT IN ({hb_list}) THEN f.wins ELSE 0 END)) AS imp_rate,
  SUM(CASE WHEN f.product_short_code LIKE 'O%' THEN f.revenue_st_eur ELSE 0 END) * 1000.0
  / NULLIF(SUM(f.bids), 0) AS rpm_per_bid_eur,
  IF(SUM(f.imps_paid) = 0, NULL,
     SUM(f.publisher_revenue_eur) * 1000.0 / SUM(f.imps_paid)) AS cpm_eur
FROM {TABLE} f
WHERE f.date BETWEEN DATE '{d1}' AND DATE '{d2}'
  AND f.channel_id IN ('Rubicon', 'MagniteDirect')
  AND f.source_type IS DISTINCT FROM 'Beachfront'
  AND f.publisher_name IN (SELECT publisher_name FROM magnite_publishers)
GROUP BY 1, 2, 3, 4, 5, 6"""

    print("querying supply funnel (daily x all dimensions, MagniteDirect publishers)...", flush=True)
    rows = run_trino_query(sql_main)
    print(f"  {len(rows)} rows", flush=True)

    B = [pack(r, start) for r in rows]

    # HB-family guard: any hb_wins outside the CASE list means the effective
    # win-rate numerator is wrong — fail loudly so the list gets extended.
    stray = sorted({r["source_type"] for r in rows
                    if int(r["hb_wins"] or 0) > 0 and r["source_type"] not in HB_FAMILY})
    if stray:
        raise SystemExit(f"New HB-style source_type(s) with hb_wins > 0: {stray} — "
                         f"extend HB_FAMILY in scripts/update_dashboard.py")

    # ---- missing-partition handling ------------------------------------
    all_dates = [(start + dt.timedelta(days=i)).isoformat()
                 for i in range((end - start).days + 1)]
    present = {all_dates[r[0]] for r in B}
    snapshots = {}
    if SNAPSHOT_PATH.exists():
        snapshots = json.loads(SNAPSHOT_PATH.read_text())
    pending, restored = [], []
    for d in all_dates:
        if d in present:
            continue
        if d in snapshots:
            B.extend(snapshots[d])
            restored.append(d)
        pending.append(d)
    for d in present:  # refresh the snapshot from live data
        snapshots[d] = [r for r in B if all_dates[r[0]] == d]
    SNAPSHOT_PATH.parent.mkdir(exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(snapshots))
    if pending:
        print(f"  missing partitions: {pending} (restored from snapshot: {restored})", flush=True)

    html = render_html(
        B=B, d1=d1, d2=d2,
        n_days=(end - start).days + 1,
        md_launch=MD_LAUNCH.isoformat(),
        sql_main=sql_main,
        pending=pending, restored=restored,
        generated=madrid_now.strftime("%Y-%m-%d %H:%M %Z"),
    )
    with open("index.html", "w") as f:
        f.write(html)
    print("written index.html", len(html))

    if "--upload" in sys.argv:
        upload_to_gdrive(Path("index.html"))


def _resolve_sa_path():
    p = Path(DRIVE_SA_JSON)
    if p.exists():
        return p
    for cand in (PROJECT_ROOT / DRIVE_SA_JSON, CONFIG_DIR / DRIVE_SA_JSON):
        if cand.exists():
            return cand
    return None


def upload_to_gdrive(html_path):
    from drive_upload import upload_to_drive

    sa = _resolve_sa_path()
    if sa is None:
        print(f"  x Drive upload skipped — service account JSON not found: {DRIVE_SA_JSON}")
        return
    print(f"Uploading to Google Drive (folder '{DRIVE_SUBFOLDER}')...")
    url = upload_to_drive(
        service_account_json_path=str(sa),
        root_folder_id=DRIVE_ROOT_FOLDER_ID,
        subfolder_name=DRIVE_SUBFOLDER,
        filename=DRIVE_FILENAME,
        file_path=str(html_path),
    )
    print(f"  Shareable link: {url}")


def render_html(**kw):
    def tooltip(sql):
        esc = sql.replace("&", "&amp;").replace("<", "&lt;")
        return (
            '<span class="info-wrap"><span class="info-icon">i</span><div class="info-tooltip">'
            '<div class="tooltip-header"><span class="tooltip-label">SQL Query</span>'
            '<button class="copy-btn" onclick="copyQuery(this)">&#128203; Copy to clipboard</button></div>'
            f'<pre class="sql-pre">{esc}</pre></div></span>'
        )

    LOGO32 = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="32" height="32" '
              'aria-label="Seedtag" class="logo"><circle cx="50" cy="50" r="50" fill="#FF6B7C"/>'
              '<circle cx="50" cy="27" r="10" fill="white"/>'
              '<path d="M50,54 C47,47 16,49 15,65 C14,79 35,84 50,79Z" fill="white"/>'
              '<path d="M50,54 C53,47 84,49 85,65 C86,79 65,84 50,79Z" fill="white"/></svg>')
    LOGO20 = LOGO32.replace('width="32" height="32"', 'width="20" height="20"')

    hbfam_js = json.dumps(list(HB_FAMILY))
    wr_note = ("Win Rate applies to header-bidding sources only (hb_wins/wins). Tag-style sources have "
               "no on-page auction — their efficiency metric is Imp Rate (imps_sold/wins). The two are "
               "different funnel steps and not comparable to each other.")
    pending_banner = ""
    if kw["pending"]:
        restored = set(kw["restored"])
        parts = [d + (" (restored from prior snapshot)" if d in restored else " (no snapshot available)")
                 for d in kw["pending"]]
        pending_banner = ('<li><strong>Pending warehouse restore:</strong> the warehouse is currently missing '
                          'partitions for ' + ", ".join(parts) +
                          ' — figures for those dates are held from the last good snapshot, never zeroed, '
                          'and are marked * in the charts.</li>')

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Magnite Connection Health — Rubicon vs MagniteDirect</title>
<script>(function(){{const s=localStorage.getItem('seedtag-theme')||'auto';document.documentElement.setAttribute('data-theme',s);}})();</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<style>
:root {{
  --bg:#EBE6E4; --surface:#FFFFFF; --surface-2:#F7F4F2; --border:#D4D0CE;
  --text:#2F2E2E; --text-muted:#5E5C5B; --text-subtle:#8D8A89;
  --accent:#FF6B7C; --accent-ink:#FFFFFF; --kpi-strong:#000000;
  --info-green:#238636; --tooltip-bg:#0D1117; --tooltip-border:#30363D; --tooltip-text:#E6EDF3;
  color-scheme: light;
}}
html[data-theme="dark"] {{
  --bg:#2F2E2E; --surface:#5E5C5B; --surface-2:#4A4847; --border:#8D8A89;
  --text:#EBE6E4; --text-muted:#D4D0CE; --text-subtle:#BCB8B6;
  --accent:#FF6B7C; --accent-ink:#2F2E2E; --kpi-strong:#FFFFFF; color-scheme: dark;
}}
@media (prefers-color-scheme: dark) {{
  html[data-theme="auto"] {{
    --bg:#2F2E2E; --surface:#5E5C5B; --surface-2:#4A4847; --border:#8D8A89;
    --text:#EBE6E4; --text-muted:#D4D0CE; --text-subtle:#BCB8B6;
    --accent-ink:#2F2E2E; --kpi-strong:#FFFFFF; color-scheme: dark;
  }}
}}
body {{ background:var(--bg); color:var(--text);
  font-family:'Instrument Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  font-feature-settings:'ss01','cv11'; margin:0; transition:background 200ms ease,color 200ms ease; }}
h1 {{ font-family:'Instrument Serif',Georgia,'Times New Roman',serif; font-weight:400; letter-spacing:-0.01em; }}
h2,h3,h4 {{ font-family:'Instrument Sans',sans-serif; font-weight:600; }}
.report-header {{ display:flex; align-items:center; gap:16px; padding:24px 32px; border-bottom:1px solid var(--border); }}
.report-header h1 {{ margin:0; font-size:28px; }}
.report-header .subtitle {{ color:var(--text-subtle); font-size:13px; margin-top:2px; }}
footer.report-footer {{ margin-top:48px; padding:16px 32px; border-top:1px solid var(--border);
  color:var(--text-subtle); font-size:12px; display:flex; align-items:center; gap:8px; }}
#theme-toggle {{ position:fixed; top:16px; right:16px; width:36px; height:36px; display:inline-flex;
  align-items:center; justify-content:center; background:var(--surface); color:var(--text);
  border:1px solid var(--border); border-radius:50%; cursor:pointer; z-index:10000;
  box-shadow:0 2px 8px rgba(0,0,0,0.08); transition:background 200ms ease,color 200ms ease,transform 150ms ease; }}
#theme-toggle:hover {{ transform:scale(1.05); }}
#theme-toggle .icon-moon {{ display:none; }}
html[data-theme="dark"] #theme-toggle .icon-sun {{ display:none; }}
html[data-theme="dark"] #theme-toggle .icon-moon {{ display:inline; }}
@media (prefers-color-scheme: dark) {{
  html[data-theme="auto"] #theme-toggle .icon-sun {{ display:none; }}
  html[data-theme="auto"] #theme-toggle .icon-moon {{ display:inline; }}
}}
#last-update {{ position:fixed; top:16px; right:64px; height:36px; display:inline-flex; align-items:center;
  gap:6px; padding:0 14px; background:var(--surface); color:var(--text-muted); border:1px solid var(--border);
  border-radius:18px; font-size:12px; z-index:10000; box-shadow:0 2px 8px rgba(0,0,0,0.08); white-space:nowrap; }}
#last-update strong {{ color:var(--text); font-weight:600; }}
@media (max-width:640px) {{ #last-update {{ display:none; }} }}
.sticky-top {{ position:sticky; top:0; z-index:5000; background:var(--bg); border-bottom:1px solid var(--border);
  box-shadow:0 4px 14px rgba(0,0,0,0.08); padding-bottom:10px; }}
.filter-bar {{ display:flex; flex-wrap:wrap; gap:20px; align-items:center; padding:16px 32px 0; }}
.filter-bar label {{ font-size:12px; text-transform:uppercase; letter-spacing:0.04em; color:var(--text-subtle); margin-right:8px; }}
.filter-bar select {{ background:var(--surface); color:var(--text); border:1px solid var(--border);
  border-radius:8px; padding:7px 10px; font-family:'Instrument Sans',sans-serif; font-size:13px; min-width:190px; }}
.kpi-block {{ padding:16px 32px 0; }}
.kpi-channel {{ font-size:13px; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; margin:8px 0 8px; color:var(--text-muted); }}
.kpi-channel.md {{ color:var(--accent); }}
.kpi-row {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:16px; margin-bottom:8px; }}
.kpi-card {{ background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:14px 18px; }}
.kpi-card.highlight {{ border:2px solid var(--accent); }}
.kpi-card .label {{ color:var(--text-subtle); font-size:12px; text-transform:uppercase; letter-spacing:0.04em; }}
.kpi-card .value {{ color:var(--kpi-strong); font-size:24px; font-weight:600; margin-top:4px; }}
.kpi-note {{ font-size:12px; color:var(--text-subtle); margin:4px 0 0; }}
section {{ padding:8px 32px; }}
.caveats {{ background:var(--surface); border:1px solid var(--border); border-left:4px solid var(--accent);
  border-radius:8px; padding:12px 18px; margin:16px 32px 8px; font-size:13px; color:var(--text-muted); }}
.caveats ul {{ margin:6px 0 0 18px; padding:0; }}
.caveats li {{ margin:3px 0; }}
.chart-box {{ background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:16px; margin:12px 0; }}
.summary-line {{ font-size:13px; color:var(--text-muted); margin:8px 0 2px; }}
.data-footer {{ font-style:italic; font-size:12px; color:var(--text-subtle); margin:2px 0 20px; }}
.tbl-actions {{ display:flex; gap:8px; margin:8px 0; }}
.tbl-actions button {{ background:var(--surface); color:var(--text); border:1px solid var(--border);
  border-radius:8px; padding:6px 14px; font-size:12px; font-family:'Instrument Sans',sans-serif; cursor:pointer; }}
.tbl-actions button:hover {{ background:var(--surface-2); }}
.info-wrap {{ display:inline-block; position:relative; vertical-align:middle; margin-left:6px; cursor:default; }}
.info-wrap::after {{ content:''; position:absolute; bottom:-10px; left:-6px; right:-6px; height:10px; }}
.info-icon {{ display:inline-flex; align-items:center; justify-content:center; width:17px; height:17px;
  border-radius:50%; background:var(--info-green); color:#fff; font-size:11px; font-weight:700;
  font-style:normal; line-height:1; cursor:help; user-select:none; }}
.info-tooltip {{ display:none; position:absolute; z-index:9999; top:calc(100% + 8px); left:0;
  background:var(--tooltip-bg); border:1px solid var(--tooltip-border); border-radius:8px;
  width:600px; max-width:92vw; box-shadow:0 8px 30px rgba(0,0,0,0.6); overflow:hidden; }}
.info-wrap:hover .info-tooltip {{ display:block; }}
.tooltip-header {{ background:#161B22; padding:8px 12px; display:flex; align-items:center;
  justify-content:space-between; border-bottom:1px solid var(--tooltip-border); }}
.tooltip-label {{ color:#8B949E; font-size:11px; font-family:monospace; }}
.copy-btn {{ background:var(--info-green); color:#fff; border:none; border-radius:5px; padding:4px 10px; font-size:11px; cursor:pointer; }}
.copy-btn.copied {{ background:#1a7f37; }}
.sql-pre {{ margin:0; padding:12px; color:var(--tooltip-text); font-size:11px; font-family:'Courier New',monospace;
  white-space:pre-wrap; word-break:break-word; max-height:260px; overflow-y:auto; background:transparent; }}
.pivot-wrap {{ overflow-x:auto; border:1px solid var(--border); border-radius:12px; background:var(--surface); max-height:640px; overflow-y:auto; }}
table.report-table {{ width:100%; border-collapse:collapse; background:var(--surface); font-size:12px; }}
table.report-table th, table.report-table td {{ padding:6px 10px; border-bottom:1px solid var(--border); text-align:right; white-space:nowrap; }}
table.report-table th {{ background:var(--surface-2); color:var(--text-muted); font-size:11px; text-transform:uppercase; letter-spacing:0.04em; position:sticky; top:0; z-index:2; }}
table.report-table td.pub, table.report-table th.pub {{ text-align:left; position:sticky; left:0; background:var(--surface); z-index:1; }}
table.report-table th.pub {{ background:var(--surface-2); z-index:3; }}
table.report-table td.chan {{ text-align:left; }}
table.report-table td.met {{ text-align:left; color:var(--text-subtle); }}
table.report-table tr.eg-first td {{ border-top:2px solid var(--border); }}
tr.md-row td, tr.md-row td.pub {{ background:color-mix(in srgb, var(--accent) 6%, var(--surface)); }}
tr.sub-row td.pub {{ padding-left:28px; color:var(--text-muted); }}
.eg-toggle {{ cursor:pointer; user-select:none; font-weight:600; }}
.eg-toggle .arrow {{ display:inline-block; width:14px; color:var(--text-subtle); }}
</style>
</head>
<body>
<div id="last-update" title="When this page was last rebuilt from Trino (data through {kw['d2']})">Data updated: <strong>{kw['generated']}</strong></div>
<button id="theme-toggle" aria-label="Toggle dark mode" title="Toggle dark mode">
  <svg class="icon-sun" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>
  <svg class="icon-moon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
</button>
<header class="report-header">
  {LOGO32}
  <div>
    <h1>Magnite Connection Health — Rubicon vs MagniteDirect</h1>
    <div class="subtitle">Analytics Team · {kw['d1']} → {kw['d2']} · All products (OMP + PMP) · EUR · Publishers with MagniteDirect activity only</div>
  </div>
</header>

<div class="sticky-top">
<div class="filter-bar">
  <div><label for="f-eg">Editorial Group</label><select id="f-eg"><option value="">All editorial groups</option></select></div>
  <div><label for="f-pub">Publisher</label><select id="f-pub"><option value="">All publishers</option></select></div>
  <div><label for="f-st">Source Type</label><select id="f-st"><option value="">All source types</option></select></div>
  <div><label for="f-au">Ad Unit Type</label><select id="f-au"><option value="">All ad unit types</option></select></div>
</div>

<div class="kpi-block">
  <div class="kpi-channel md">MagniteDirect</div>
  <div class="kpi-row" id="kpi-md"></div>
  <div class="kpi-channel">Rubicon</div>
  <div class="kpi-row" id="kpi-rub"></div>
  <p class="kpi-note">{wr_note} RPM = OMP Gross × 1000 / SSP bids (per 1,000 bids). CPM = Publisher Revenue × 1000 / publisher-reported impressions. Window: {kw['d1']} – {kw['d2']} (MagniteDirect since {kw['md_launch']}), scoped to MagniteDirect publishers and filtered by the selections above.</p>
</div>
</div>

<div class="caveats">
  <strong>Structural caveats</strong>
  <ul>
    {pending_banner}
    <li><strong>Requests / Bid Rate cannot be split by channel</strong> — bid-input events carry no channel, so channel-level demand volume is measured in bids and bid inputs are never used here.</li>
    <li><strong>{wr_note}</strong></li>
    <li><strong>Publisher-reported impressions lag ~3 days</strong> — CPM for the most recent days is provisional; missing values render as —, never as 0.</li>
  </ul>
</div>

<section>
<h2>1 · Evolution by channel {tooltip(kw['sql_main'])}</h2>
<div class="chart-box"><div style="position:relative;height:320px"><canvas id="revChart"></canvas></div></div>
<p class="summary-line" id="s1Summary"></p>
<div class="chart-box"><div style="position:relative;height:280px"><canvas id="ratioChart"></canvas></div></div>
<p class="summary-line">Win Rate (HB) and Imp Rate (Tag) per channel (left axis) and CPM (dashed, right axis). {wr_note} Recent CPM points are provisional due to the impression-reporting lag.</p>
<p class="data-footer">Source: Daily supply funnel — Magnite channels only, publishers with MagniteDirect activity, all products, {kw['d1']} – {kw['d2']}, revenue in EUR. Respects the filters above. Dates marked * are pending warehouse restore.</p>
</section>

<section>
<h2>2 · Daily ramp since MagniteDirect launch — vs Rubicon {tooltip(kw['sql_main'])}</h2>
<div class="chart-box"><div style="position:relative;height:320px"><canvas id="rampChart"></canvas></div></div>
<p class="summary-line" id="s2Summary"></p>
<p class="data-footer">Source: Daily supply funnel — Rubicon &amp; MagniteDirect, publishers with MagniteDirect activity, all products, {kw['md_launch']} – {kw['d2']}, revenue in EUR (log scale). {wr_note} Respects the filters above.</p>
</section>

<section>
<h2>3 · Editorial group / publisher head-to-head {tooltip(kw['sql_main'])}</h2>
<div class="tbl-actions"><button onclick="setExpandAll('pivot',true)">Expand all</button><button onclick="setExpandAll('pivot',false)">Collapse all</button></div>
<div class="pivot-wrap"><table class="report-table" id="pivotTable"></table></div>
<p class="summary-line" id="pivotSummary"></p>
<p class="data-footer">Source: Daily supply funnel — publishers with MagniteDirect activity, on both Magnite channels, all products, {kw['d1']} – {kw['d2']}, revenue in EUR. Main rows = editorial groups (click to expand publishers); MagniteDirect rows tinted coral; — = no data / provisional (impressions lag).</p>
</section>

<section>
<h2>4 · Funnel health by editorial group {tooltip(kw['sql_main'])}</h2>
<div class="tbl-actions"><button onclick="setExpandAll('funnel',true)">Expand all</button><button onclick="setExpandAll('funnel',false)">Collapse all</button></div>
<div class="pivot-wrap"><table class="report-table" id="funnelTable"></table></div>
<p class="summary-line" id="funnelSummary"></p>
<p class="data-footer">Source: Daily supply funnel — publishers with MagniteDirect activity, all products (OMP-only revenue also shown), {kw['d1']} – {kw['d2']}, revenue in EUR. Funnel order: bid inputs → bids → wins → (HB only: hb wins → hb inserts) → imps sold. {wr_note} Main rows = editorial group × channel (click to expand publishers); slice with the filters at the top.</p>
</section>

<footer class="report-footer">{LOGO20}<span>Analytics Team · Magnite Connection Health — Rubicon vs MagniteDirect · {kw['d1']} → {kw['d2']}</span></footer>

<script>
// Row layout: [dIdx, isMD, eg, st, adunit, pub, gross, ompGross, pubRev, bids, wins, hbWins, impsSold, impsPaid]
const B = {json.dumps(kw['B'])};
const N_DAYS = {kw['n_days']};
const DATES = Array.from({{length:N_DAYS}}, (_,i)=>{{const d=new Date(Date.UTC({int(kw['d1'][:4])},{int(kw['d1'][5:7])-1},{int(kw['d1'][8:10])}+i));return d.toISOString().slice(0,10);}});
const PENDING = new Set({json.dumps(kw['pending'])});
const LABELS = DATES.map(d=>PENDING.has(d)?d+' *':d);
const MD_LAUNCH='{kw['md_launch']}';
const MD_IDX = DATES.map((d,i)=>d>=MD_LAUNCH?i:-1).filter(i=>i>=0);
const COLORS = ['#5476FF','#E866F4','#948A8A','#67C8FE','#FFA071','#A36AFF','#F4D56D'];
const CH=['Rubicon','MagniteDirect'];
const HB_FAMILY=new Set({hbfam_js});
const M={{g:0,og:1,pr:2,bids:3,wins:4,hw:5,is:6,ip:7}};
const B0=6;  // index of first measure

function copyQuery(btn) {{
  const pre = btn.closest('.info-tooltip').querySelector('.sql-pre');
  navigator.clipboard.writeText(pre.textContent.trim()).then(()=>{{
    btn.textContent='\\u2713 Copied!'; btn.classList.add('copied');
    setTimeout(()=>{{btn.textContent='\\ud83d\\udccb Copy to clipboard'; btn.classList.remove('copied');}},2000);
  }}).catch(()=>{{ btn.textContent='\\u26a0 Copy failed';
    setTimeout(()=>{{btn.textContent='\\ud83d\\udccb Copy to clipboard';}},2000); }});
}}

const fmtEUR=v=>v==null?'—':'€'+v.toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}});
const fmtPct=v=>v==null?'—':(v*100).toFixed(1)+'%';
const fmtInt=v=>v==null?'—':v.toLocaleString('en-US');
const div=(n,d)=>d?n/d:null;
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');

// ---------- filters ----------
const selEG=document.getElementById('f-eg'), selST=document.getElementById('f-st'),
      selAU=document.getElementById('f-au'), selPUB=document.getElementById('f-pub');
{{
  const fill=(sel,idx)=>{{
    [...new Set(B.map(r=>r[idx]).filter(Boolean))].sort((a,b)=>a.localeCompare(b))
      .forEach(v=>sel.insertAdjacentHTML('beforeend','<option value="'+esc(v)+'">'+esc(v)+'</option>'));
  }};
  fill(selEG,2); fill(selST,3); fill(selAU,4); fill(selPUB,5);
}}
function filt(rows){{
  const eg=selEG.value, st=selST.value, au=selAU.value, pub=selPUB.value;
  return rows.filter(r=>(!eg||r[2]===eg)&&(!st||r[3]===st)&&(!au||r[4]===au)&&(!pub||r[5]===pub));
}}

// zero-filled accumulator; family-split fields feed the two rate metrics:
// hbW/hbHW = wins/hb_wins on HB-family rows -> Win Rate (HB) = hbHW/hbW
// tagW/tagIS = wins/imps_sold on non-HB rows -> Imp Rate (Tag) = tagIS/tagW
function zeroAcc(){{return {{g:0,og:0,pr:0,bids:0,wins:0,hw:0,is:0,ip:0,hbW:0,hbHW:0,tagW:0,tagIS:0}};}}
function addTo(acc,row){{
  for(const k in M) acc[k]+=row[B0+M[k]]||0;
  if(HB_FAMILY.has(row[3])){{ acc.hbW+=row[B0+M.wins]||0; acc.hbHW+=row[B0+M.hw]||0; }}
  else {{ acc.tagW+=row[B0+M.wins]||0; acc.tagIS+=row[B0+M.is]||0; }}
}}

// ---------- KPI cards ----------
function renderKPIs(){{
  const acc=[zeroAcc(),zeroAcc()];
  filt(B).forEach(r=>addTo(acc[r[1]],r));
  [['kpi-md',1],['kpi-rub',0]].forEach(([id,ci])=>{{
    const a=acc[ci];
    const cards=[
      ['Gross Revenue',fmtEUR(a.g)],
      ['Bids',fmtInt(a.bids||null)],
      ['Win Rate (HB)',fmtPct(div(a.hbHW,a.hbW))],
      ['Imp Rate (Tag)',fmtPct(div(a.tagIS,a.tagW))],
      ['CPM (EUR)',a.ip?'€'+(a.pr*1000/a.ip).toFixed(2):'—'],
      ['RPM per 1,000 bids (EUR)',a.bids?'€'+(a.og*1000/a.bids).toFixed(4):'—'],
    ];
    document.getElementById(id).innerHTML=cards.map(c=>
      '<div class="kpi-card'+(ci===1?' highlight':'')+'"><div class="label">'+c[0]+'</div><div class="value">'+c[1]+'</div></div>').join('');
  }});
}}

// ---------- charts ----------
function themeOpts() {{
  const css=getComputedStyle(document.documentElement);
  return {{ text:css.getPropertyValue('--text').trim(),
           muted:css.getPropertyValue('--text-subtle').trim(),
           border:css.getPropertyValue('--border').trim() }};
}}
function baseOpts(t) {{
  return {{ responsive:true, maintainAspectRatio:false, animation:false,
    plugins:{{ legend:{{labels:{{color:t.text,font:{{family:'Instrument Sans'}}}}}},
             tooltip:{{titleFont:{{family:'Instrument Sans'}},bodyFont:{{family:'Instrument Sans'}}}} }} }};
}}
const charts=[];

function dailySeries(){{
  const d=[Array.from({{length:N_DAYS}},zeroAcc),Array.from({{length:N_DAYS}},zeroAcc)];
  filt(B).forEach(r=>addTo(d[r[1]][r[0]],r));
  return d;
}}

let revChart, ratioChart, rampChart;
function buildCharts(){{
  const t=themeOpts();
  const D=dailySeries();
  const gap=(i,v)=>PENDING.has(DATES[i])&&!v?null:(v||null);
  const revData={{labels:LABELS,datasets:[
    {{type:'line',label:'Rubicon Bids',data:DATES.map((_,i)=>gap(i,D[0][i].bids)),borderColor:COLORS[2],backgroundColor:COLORS[2],yAxisID:'y2',pointRadius:2,tension:0.25}},
    {{type:'line',label:'MagniteDirect Bids',data:DATES.map((_,i)=>gap(i,D[1][i].bids)),borderColor:COLORS[6],backgroundColor:COLORS[6],yAxisID:'y2',pointRadius:2,tension:0.25}},
    {{label:'Rubicon Gross',data:DATES.map((_,i)=>gap(i,D[0][i].g)),backgroundColor:COLORS[0]}},
    {{label:'Rubicon Publisher Rev',data:DATES.map((_,i)=>gap(i,D[0][i].pr)),backgroundColor:COLORS[3]}},
    {{label:'MagniteDirect Gross',data:DATES.map((_,i)=>gap(i,D[1][i].g)),backgroundColor:COLORS[1]}},
    {{label:'MagniteDirect Publisher Rev',data:DATES.map((_,i)=>gap(i,D[1][i].pr)),backgroundColor:COLORS[5]}}
  ]}};
  const ratioData={{labels:LABELS,datasets:[
    {{label:'Rubicon Win Rate (HB)',data:DATES.map((_,i)=>div(D[0][i].hbHW,D[0][i].hbW)),borderColor:COLORS[0],backgroundColor:COLORS[0],yAxisID:'y',pointRadius:2,tension:0.25}},
    {{label:'MagniteDirect Win Rate (HB)',data:DATES.map((_,i)=>div(D[1][i].hbHW,D[1][i].hbW)),borderColor:COLORS[1],backgroundColor:COLORS[1],yAxisID:'y',pointRadius:2,tension:0.25}},
    {{label:'Rubicon Imp Rate (Tag)',data:DATES.map((_,i)=>div(D[0][i].tagIS,D[0][i].tagW)),borderColor:COLORS[2],backgroundColor:COLORS[2],yAxisID:'y',pointRadius:2,tension:0.25}},
    {{label:'MagniteDirect Imp Rate (Tag)',data:DATES.map((_,i)=>div(D[1][i].tagIS,D[1][i].tagW)),borderColor:COLORS[6],backgroundColor:COLORS[6],yAxisID:'y',pointRadius:2,tension:0.25}},
    {{label:'Rubicon CPM',data:DATES.map((_,i)=>D[0][i].ip?D[0][i].pr*1000/D[0][i].ip:null),borderColor:COLORS[3],backgroundColor:COLORS[3],yAxisID:'y2',borderDash:[5,4],pointRadius:2,tension:0.25}},
    {{label:'MagniteDirect CPM',data:DATES.map((_,i)=>D[1][i].ip?D[1][i].pr*1000/D[1][i].ip:null),borderColor:COLORS[5],backgroundColor:COLORS[5],yAxisID:'y2',borderDash:[5,4],pointRadius:2,tension:0.25}}
  ]}};
  const rampData={{labels:MD_IDX.map(i=>LABELS[i]),datasets:[
    {{type:'bar',label:'MagniteDirect Gross (EUR)',data:MD_IDX.map(i=>gap(i,D[1][i].g)),backgroundColor:'#FF6B7C',yAxisID:'y'}},
    {{type:'bar',label:'Rubicon Gross (EUR)',data:MD_IDX.map(i=>gap(i,D[0][i].g)),backgroundColor:COLORS[0],yAxisID:'y'}},
    {{type:'line',label:'MagniteDirect Win Rate (HB)',data:MD_IDX.map(i=>div(D[1][i].hbHW,D[1][i].hbW)),borderColor:COLORS[1],backgroundColor:COLORS[1],yAxisID:'y2',pointRadius:2,tension:0.25}},
    {{type:'line',label:'Rubicon Win Rate (HB)',data:MD_IDX.map(i=>div(D[0][i].hbHW,D[0][i].hbW)),borderColor:COLORS[2],backgroundColor:COLORS[2],yAxisID:'y2',pointRadius:2,tension:0.25}},
    {{type:'line',label:'MagniteDirect Imp Rate (Tag)',data:MD_IDX.map(i=>div(D[1][i].tagIS,D[1][i].tagW)),borderColor:COLORS[5],backgroundColor:COLORS[5],yAxisID:'y2',borderDash:[5,4],pointRadius:2,tension:0.25}},
    {{type:'line',label:'Rubicon Imp Rate (Tag)',data:MD_IDX.map(i=>div(D[0][i].tagIS,D[0][i].tagW)),borderColor:COLORS[6],backgroundColor:COLORS[6],yAxisID:'y2',borderDash:[5,4],pointRadius:2,tension:0.25}}
  ]}};

  if(!revChart){{
    let o=baseOpts(t);
    o.scales={{x:{{ticks:{{color:t.muted}},grid:{{color:t.border}}}},
      y:{{type:'logarithmic',ticks:{{color:t.muted,callback:v=>'€'+Number(v).toLocaleString()}},grid:{{color:t.border}},title:{{display:true,text:'EUR (log scale)',color:t.muted}}}},
      y2:{{type:'logarithmic',position:'right',ticks:{{color:t.muted,callback:v=>Number(v).toLocaleString()}},grid:{{drawOnChartArea:false}},title:{{display:true,text:'Bids (log scale)',color:t.muted}}}}}};
    revChart=new Chart(document.getElementById('revChart'),{{type:'bar',data:revData,options:o}}); charts.push(revChart);
    o=baseOpts(t);
    o.scales={{x:{{ticks:{{color:t.muted}},grid:{{color:t.border}}}},
      y:{{position:'left',ticks:{{color:t.muted,callback:v=>(v*100).toFixed(0)+'%'}},grid:{{color:t.border}},title:{{display:true,text:'Rate',color:t.muted}}}},
      y2:{{position:'right',ticks:{{color:t.muted,callback:v=>'€'+v.toFixed(2)}},grid:{{drawOnChartArea:false}},title:{{display:true,text:'CPM (EUR)',color:t.muted}}}}}};
    ratioChart=new Chart(document.getElementById('ratioChart'),{{type:'line',data:ratioData,options:o}}); charts.push(ratioChart);
    o=baseOpts(t);
    o.scales={{x:{{ticks:{{color:t.muted}},grid:{{color:t.border}}}},
      y:{{type:'logarithmic',position:'left',ticks:{{color:t.muted,callback:v=>'€'+Number(v).toLocaleString()}},grid:{{color:t.border}},title:{{display:true,text:'Gross Revenue (EUR, log scale)',color:t.muted}}}},
      y2:{{position:'right',ticks:{{color:t.muted,callback:v=>(v*100).toFixed(0)+'%'}},grid:{{drawOnChartArea:false}},title:{{display:true,text:'Rate',color:t.muted}}}}}};
    rampChart=new Chart(document.getElementById('rampChart'),{{data:rampData,options:o}}); charts.push(rampChart);
  }} else {{
    revChart.data=revData; ratioChart.data=ratioData; rampChart.data=rampData;
    charts.forEach(c=>c.update('none'));
  }}

  const li=N_DAYS-1;
  const pendNote=PENDING.size?' Dates marked * are pending warehouse restore.':'';
  document.getElementById('s1Summary').textContent=
    'Latest closed day ('+DATES[li]+'): Rubicon '+fmtEUR(D[0][li].g||null)+' Gross vs MagniteDirect '+fmtEUR(D[1][li].g||null)+' (MagniteDirect publishers only).'+pendNote;
  const wr=div(D[1][li].hbHW,D[1][li].hbW), wrR=div(D[0][li].hbHW,D[0][li].hbW);
  document.getElementById('s2Summary').textContent=
    'MagniteDirect Gross on '+DATES[li]+': '+fmtEUR(D[1][li].g||null)+(wr!=null?' with a '+(wr*100).toFixed(1)+'% Win Rate (HB)':'')
    +(wrR!=null?' (Rubicon: '+(wrR*100).toFixed(1)+'%)':'')+'.'+pendNote;
}}

// ---------- expand/collapse ----------
const expanded={{pivot:new Set(),funnel:new Set()}};
function toggleEG(tbl,key){{ const s=expanded[tbl]; s.has(key)?s.delete(key):s.add(key); (tbl==='pivot'?renderPivot:renderFunnel)(); }}
function setExpandAll(tbl,on){{
  const s=expanded[tbl]; s.clear();
  if(on) (tbl==='pivot'?pivotKeys():funnelKeys()).forEach(k=>s.add(k));
  (tbl==='pivot'?renderPivot:renderFunnel)();
}}

// ---------- Section 3: pivot (eg -> publisher, x channel x metric, columns = dates) ----------
function pivotAgg(){{
  const eg={{}}, pub={{}}, egTot={{}};
  filt(B).forEach(r=>{{
    const kEg=r[2]||'(none)', kPub=r[5];
    const day=r[0], ci=r[1];
    for(const [store,key] of [[eg,kEg],[pub,kEg+'\\u0000'+kPub]]){{
      if(!store[key]) store[key]=[Array.from({{length:N_DAYS}},zeroAcc),Array.from({{length:N_DAYS}},zeroAcc)];
      addTo(store[key][ci][day],r);
    }}
    egTot[kEg]=(egTot[kEg]||0)+(ci===1?r[B0+M.g]:0);
  }});
  return {{eg,pub,egTot}};
}}
let pivotCache=null;
function pivotKeys(){{ return Object.keys(pivotCache.eg); }}
const PIVOT_METRICS=[
  ['Gross Revenue',a=>a.g?fmtEUR(a.g):(a.g===0?'—':fmtEUR(a.g))],
  ['Bids',a=>a.bids?fmtInt(a.bids):'—'],
  ['CPM',a=>a.ip?'€'+(a.pr*1000/a.ip).toFixed(2):'—'],
  ['Win Rate (HB)',a=>a.hbW?fmtPct(a.hbHW/a.hbW):'—'],
  ['Imp Rate (Tag)',a=>a.tagW?fmtPct(a.tagIS/a.tagW):'—'],
];
function hasData(perDay){{ return perDay.some(a=>a.g||a.wins||a.ip); }}
function pivotRows(label,perCh,subCls){{
  let h='', labelDone=false, firstRow=true;
  ['MagniteDirect','Rubicon'].forEach(ch=>{{
    const ci=ch==='MagniteDirect'?1:0;
    if(!hasData(perCh[ci])) return;
    PIVOT_METRICS.forEach((m,mi)=>{{
      const cls=[subCls, (!subCls&&firstRow)?'eg-first':'', ci===1?'md-row':''].filter(Boolean).join(' ');
      h+='<tr class="'+cls+'">';
      h+='<td class="pub">'+(labelDone?'':label)+'</td>';
      labelDone=true; firstRow=false;
      h+='<td class="chan">'+(mi===0?ch:'')+'</td><td class="met">'+m[0]+'</td>';
      for(let i=0;i<N_DAYS;i++) h+='<td>'+m[1](perCh[ci][i])+'</td>';
      h+='</tr>';
    }});
  }});
  return h;
}}
function renderPivot(){{
  pivotCache=pivotAgg();
  const {{eg,pub,egTot}}=pivotCache;
  const order=Object.keys(eg).sort((a,b)=>(egTot[b]||0)-(egTot[a]||0));
  let h='<thead><tr><th class="pub">Editorial group / publisher</th><th style="text-align:left">Channel</th><th style="text-align:left">Metric</th>';
  LABELS.forEach(d=>h+='<th>'+d.slice(5)+'</th>');
  h+='</tr></thead><tbody>';
  order.forEach(k=>{{
    const isOpen=expanded.pivot.has(k);
    const label='<span class="eg-toggle" onclick="toggleEG(\\'pivot\\','+JSON.stringify(k).replace(/"/g,'&quot;')+')"><span class="arrow">'+(isOpen?'\\u25be':'\\u25b8')+'</span>'+esc(k)+'</span>';
    h+=pivotRows(label,eg[k],'');
    if(isOpen){{
      Object.keys(pub).filter(pk=>pk.startsWith(k+'\\u0000'))
        .sort((a,b)=>{{
          const gm=x=>pub[x][1].reduce((s,acc)=>s+acc.g,0)+pub[x][0].reduce((s,acc)=>s+acc.g,0);
          return gm(b)-gm(a);
        }})
        .forEach(pk=>{{ h+=pivotRows(esc(pk.split('\\u0000')[1]),pub[pk],'sub-row'); }});
    }}
  }});
  h+='</tbody>';
  document.getElementById('pivotTable').innerHTML=h;
  document.getElementById('pivotSummary').textContent=
    order.length+' editorial groups with MagniteDirect activity (after filters), sorted by MagniteDirect Gross Revenue. Click a group to expand its publishers.';
}}

// ---------- Section 4: funnel (eg x channel -> publisher) ----------
function funnelAgg(){{
  const eg={{}}, pub={{}};
  filt(B).forEach(r=>{{
    const kEg=(r[2]||'(none)')+'\\u0001'+r[1];
    const kPub=kEg+'\\u0000'+r[5];
    for(const [store,key] of [[eg,kEg],[pub,kPub]]){{
      if(!store[key]) store[key]=zeroAcc();
      addTo(store[key],r);
    }}
  }});
  return {{eg,pub}};
}}
let funnelCache=null;
function funnelKeys(){{ return Object.keys(funnelCache.eg); }}
function funnelCells(a){{
  return '<td>'+fmtInt(a.bids)+'</td><td>'+fmtInt(a.wins)+'</td><td>'+fmtInt(a.hw)+'</td><td>'+fmtInt(a.is)+'</td><td>'+fmtInt(a.ip)+'</td>'
    +'<td>'+fmtEUR(a.g)+'</td><td>'+fmtEUR(a.pr)+'</td><td>'+fmtEUR(a.og)+'</td>'
    +'<td>'+(a.hbW?fmtPct(a.hbHW/a.hbW):'—')+'</td>'
    +'<td>'+(a.tagW?fmtPct(a.tagIS/a.tagW):'—')+'</td>'
    +'<td>'+(a.bids?'€'+(a.og*1000/a.bids).toFixed(4):'—')+'</td>'
    +'<td>'+(a.ip?'€'+(a.pr*1000/a.ip).toFixed(2):'—')+'</td>';
}}
function renderFunnel(){{
  funnelCache=funnelAgg();
  const {{eg,pub}}=funnelCache;
  const order=Object.keys(eg).sort((a,b)=>eg[b].g-eg[a].g);
  let h='<thead><tr><th class="pub">Editorial group / publisher</th><th style="text-align:left">Channel</th>'
    +'<th>Bids</th><th>Wins</th><th>HB Wins</th><th>Imps Sold</th><th>Imps Paid</th>'
    +'<th>Gross Rev (EUR)</th><th>Publisher Rev (EUR)</th><th>OMP Gross (EUR)</th>'
    +'<th>Win Rate (HB)</th><th>Imp Rate (Tag)</th><th>RPM per 1,000 bids (EUR)</th><th>CPM (EUR)</th></tr></thead><tbody>';
  order.forEach(k=>{{
    const [egName,ciS]=k.split('\\u0001');
    const ci=+ciS;
    const isOpen=expanded.funnel.has(k);
    const label='<span class="eg-toggle" onclick="toggleEG(\\'funnel\\','+JSON.stringify(k).replace(/"/g,'&quot;')+')"><span class="arrow">'+(isOpen?'\\u25be':'\\u25b8')+'</span>'+esc(egName)+'</span>';
    h+='<tr class="eg-first '+(ci===1?'md-row':'')+'"><td class="pub">'+label+'</td><td class="chan">'+CH[ci===1?1:0]+'</td>'+funnelCells(eg[k])+'</tr>';
    if(isOpen){{
      Object.keys(pub).filter(pk=>pk.startsWith(k+'\\u0000'))
        .sort((a,b)=>pub[b].g-pub[a].g)
        .forEach(pk=>{{
          const pn=pk.split('\\u0000')[1];
          h+='<tr class="sub-row '+(ci===1?'md-row':'')+'"><td class="pub">'+esc(pn)+'</td><td class="chan"></td>'+funnelCells(pub[pk])+'</tr>';
        }});
    }}
  }});
  h+='</tbody>';
  document.getElementById('funnelTable').innerHTML=h;
  const nMD=order.filter(k=>k.split('\\u0001')[1]==='1').length;
  document.getElementById('funnelSummary').textContent=
    order.length+' editorial-group \\u00d7 channel rows ('+nMD+' on MagniteDirect, after filters), sorted by Gross Revenue; raw funnel counts (bids, wins, hb wins, imps sold, imps paid) shown so every ratio can be audited.';
}}

// ---------- wiring ----------
function renderAll(){{ renderKPIs(); buildCharts(); renderPivot(); renderFunnel(); }}
[selEG,selST,selAU,selPUB].forEach(s=>s.addEventListener('change',renderAll));
renderAll();

function rethemeCharts() {{
  const t=themeOpts();
  charts.forEach(c=>{{
    Object.values(c.options.scales).forEach(s=>{{
      if(s.ticks) s.ticks.color=t.muted;
      if(s.grid&&s.grid.color!==undefined) s.grid.color=t.border;
      if(s.title) s.title.color=t.muted;
    }});
    c.options.plugins.legend.labels.color=t.text;
    c.update('none');
  }});
}}
new MutationObserver(rethemeCharts).observe(document.documentElement,{{attributes:true,attributeFilter:['data-theme']}});
document.getElementById('theme-toggle').addEventListener('click',()=>{{
  const html=document.documentElement;
  const cur=html.getAttribute('data-theme')||'auto';
  const next=cur==='auto'?'light':cur==='light'?'dark':'auto';
  html.setAttribute('data-theme',next); localStorage.setItem('seedtag-theme',next);
}});
</script>
</body>
</html>"""


if __name__ == "__main__":
    sys.exit(main())
