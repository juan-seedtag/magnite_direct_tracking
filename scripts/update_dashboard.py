#!/usr/bin/env python3
"""Regenerate the Magnite Connection Health dashboard from Trino.

Runs in GitHub Actions (or locally). Connection settings come from env vars:
  TRINO_HOST      (required)
  TRINO_PORT      (default 443)
  TRINO_USER      (required)
  TRINO_PASSWORD  (basic auth) or TRINO_JWT (JWT auth) — one of the two
  TRINO_CATALOG   (default st_datalakehouse)
  TRINO_HTTP_SCHEME (default https)

Output: index.html (and magnite_connection_health_latest.html) at repo root.
"""
import json
import os
import sys
import datetime as dt
from zoneinfo import ZoneInfo

import trino
from trino.auth import BasicAuthentication, JWTAuthentication

TABLE = "st_datalakehouse.analytics.etl_ssp_supply_funnel_daily_local"
WINDOW_START = dt.date(2026, 7, 1)
MD_LAUNCH = dt.date(2026, 7, 10)
TAG = "-- @user:juanperez@seedtag.com @skill:barbi"


def get_conn():
    host = os.environ["TRINO_HOST"]
    user = os.environ["TRINO_USER"]
    if os.environ.get("TRINO_JWT"):
        auth = JWTAuthentication(os.environ["TRINO_JWT"])
    else:
        auth = BasicAuthentication(user, os.environ["TRINO_PASSWORD"])
    return trino.dbapi.connect(
        host=host,
        port=int(os.environ.get("TRINO_PORT", "443")),
        user=user,
        catalog=os.environ.get("TRINO_CATALOG", "st_datalakehouse"),
        http_scheme=os.environ.get("TRINO_HTTP_SCHEME", "https"),
        auth=auth,
    )


def run(cur, sql):
    cur.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def latest_full_month(end):
    """Last complete calendar month ending on or before `end`."""
    nxt = end + dt.timedelta(days=1)
    if nxt.month != end.month:
        first = end.replace(day=1)
        return first, end
    first_this = end.replace(day=1)
    last_prev = first_this - dt.timedelta(days=1)
    return last_prev.replace(day=1), last_prev


def main():
    madrid_now = dt.datetime.now(ZoneInfo("Europe/Madrid"))
    end = madrid_now.date() - dt.timedelta(days=1)  # latest closed day (T-1)
    start = WINDOW_START
    m_first, m_last = latest_full_month(end)
    month_label = m_first.strftime("%B %Y")

    d1, d2 = start.isoformat(), end.isoformat()

    sql_daily = f"""{TAG}
SELECT date, channel_id,
  SUM(revenue_st_eur) AS gross_eur,
  SUM(publisher_revenue_eur) AS pub_rev_eur,
  SUM(wins) AS wins, SUM(hb_wins) AS hb_wins,
  SUM(imps_paid) AS imps_paid
FROM {TABLE}
WHERE date BETWEEN DATE '{d1}' AND DATE '{d2}'
  AND channel_id IN ('MagniteDirect','Rubicon')
GROUP BY 1,2 ORDER BY 1,2"""

    sql_kpi = f"""{TAG}
SELECT channel_id,
  SUM(CASE WHEN date BETWEEN DATE '{m_first}' AND DATE '{m_last}' THEN revenue_st_eur ELSE 0 END) AS gross_month,
  SUM(revenue_st_eur) AS gross_total,
  SUM(publisher_revenue_eur) AS pub_rev_total,
  IF(SUM(wins)=0, NULL, SUM(hb_wins)*1.0/SUM(wins)) AS win_rate,
  IF(SUM(imps_paid)=0, NULL, SUM(publisher_revenue_eur)*1000.0/SUM(imps_paid)) AS cpm
FROM {TABLE}
WHERE date BETWEEN DATE '{d1}' AND DATE '{d2}'
  AND channel_id IN ('MagniteDirect','Rubicon')
GROUP BY 1"""

    sql_pivot = f"""{TAG}
WITH both_pubs AS (
  SELECT publisher_name
  FROM {TABLE}
  WHERE date BETWEEN DATE '{d1}' AND DATE '{d2}'
    AND channel_id IN ('MagniteDirect','Rubicon')
  GROUP BY 1
  HAVING SUM(CASE WHEN channel_id='MagniteDirect' THEN revenue_st_eur ELSE 0 END) > 0
     AND SUM(CASE WHEN channel_id='Rubicon' THEN revenue_st_eur ELSE 0 END) > 0
)
SELECT f.publisher_name, f.channel_id, f.date,
  SUM(f.revenue_st_eur) AS gross_eur,
  IF(SUM(f.imps_paid)=0, NULL, SUM(f.publisher_revenue_eur)*1000.0/SUM(f.imps_paid)) AS cpm,
  IF(SUM(f.wins)=0, NULL, SUM(f.hb_wins)*1.0/SUM(f.wins)) AS win_rate
FROM {TABLE} f
JOIN both_pubs b ON f.publisher_name = b.publisher_name
WHERE f.date BETWEEN DATE '{d1}' AND DATE '{d2}'
  AND f.channel_id IN ('MagniteDirect','Rubicon')
GROUP BY 1,2,3 ORDER BY 1,2,3"""

    conn = get_conn()
    cur = conn.cursor()
    print("querying daily aggregates...", flush=True)
    daily_rows = run(cur, sql_daily)
    print(f"  {len(daily_rows)} rows", flush=True)
    print("querying KPIs...", flush=True)
    kpi_rows = run(cur, sql_kpi)
    print("querying publisher pivot...", flush=True)
    pivot_rows = run(cur, sql_pivot)
    print(f"  {len(pivot_rows)} rows", flush=True)

    DAILY = {}
    for r in daily_rows:
        d = str(r["date"])[:10]
        DAILY.setdefault(r["channel_id"], {})[d] = {
            "g": round(float(r["gross_eur"] or 0), 2),
            "pr": round(float(r["pub_rev_eur"] or 0), 2),
            "w": int(r["wins"] or 0),
            "hw": int(r["hb_wins"] or 0),
            "ip": int(r["imps_paid"] or 0),
        }

    kpi = {r["channel_id"]: r for r in kpi_rows}
    rub, md = kpi.get("Rubicon", {}), kpi.get("MagniteDirect", {})

    pubs = {}
    for r in pivot_rows:
        k = r["publisher_name"]
        pubs.setdefault(k, {"MagniteDirect": {}, "Rubicon": {}})
        d = str(r["date"])[:10]
        cpm = r["cpm"]
        wr = r["win_rate"]
        pubs[k][r["channel_id"]][d] = {
            "g": round(float(r["gross_eur"]), 2),
            "c": round(float(cpm), 4) if cpm is not None else None,
            "w": round(float(wr), 4) if wr is not None else None,
        }
    totals = {k: sum(v["g"] for v in ch["MagniteDirect"].values()) for k, ch in pubs.items()}
    order = sorted(totals, key=totals.get, reverse=True)
    pivot = {"order": order, "pubs": pubs}

    fmt_eur = lambda v: "€{:,.2f}".format(v)
    fmt_pct = lambda v: "—" if v is None else "{:.1f}%".format(float(v) * 100)

    n_days = (end - start).days + 1
    dates_js = f"Array.from({{length:{n_days}}}, (_,i)=>{{const d=new Date(Date.UTC({start.year},{start.month-1},{start.day}+i));return d.toISOString().slice(0,10);}})"

    html = render_html(
        DAILY=DAILY, pivot=pivot,
        d1=d1, d2=d2, dates_js=dates_js,
        md_launch=MD_LAUNCH.isoformat(),
        month_label=month_label,
        kpi_rub_month=fmt_eur(float(rub.get("gross_month") or 0)),
        kpi_md_total=fmt_eur(float(md.get("gross_total") or 0)),
        kpi_wr_rub=fmt_pct(rub.get("win_rate")),
        kpi_wr_md=fmt_pct(md.get("win_rate")),
        kpi_cpm_rub="—" if rub.get("cpm") is None else "€{:.2f}".format(float(rub["cpm"])),
        sql_daily=sql_daily, sql_pivot=sql_pivot,
        generated=madrid_now.strftime("%Y-%m-%d %H:%M %Z"),
    )
    for name in ("index.html", "magnite_connection_health_latest.html"):
        with open(name, "w") as f:
            f.write(html)
    print("written index.html /", "magnite_connection_health_latest.html", len(html))


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
.kpi-row {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; padding:24px 32px; }}
.kpi-card {{ background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:16px 20px; }}
.kpi-card.highlight {{ border:2px solid var(--accent); }}
.kpi-card .label {{ color:var(--text-subtle); font-size:12px; text-transform:uppercase; letter-spacing:0.04em; }}
.kpi-card .value {{ color:var(--kpi-strong); font-size:26px; font-weight:600; margin-top:4px; }}
.kpi-card .note {{ color:var(--text-subtle); font-size:12px; margin-top:4px; }}
section {{ padding:8px 32px; }}
.caveats {{ background:var(--surface); border:1px solid var(--border); border-left:4px solid var(--accent);
  border-radius:8px; padding:12px 18px; margin:8px 32px; font-size:13px; color:var(--text-muted); }}
.caveats ul {{ margin:6px 0 0 18px; padding:0; }}
.caveats li {{ margin:3px 0; }}
.chart-box {{ background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:16px; margin:12px 0; }}
.summary-line {{ font-size:13px; color:var(--text-muted); margin:8px 0 2px; }}
.data-footer {{ font-style:italic; font-size:12px; color:var(--text-subtle); margin:2px 0 20px; }}
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
table.report-table tr.pub-first td {{ border-top:2px solid var(--border); }}
tr.md-row td {{ background:color-mix(in srgb, var(--accent) 6%, var(--surface)); }}
tr.md-row td.pub {{ background:color-mix(in srgb, var(--accent) 6%, var(--surface)); }}
</style>
</head>
<body>
<button id="theme-toggle" aria-label="Toggle dark mode" title="Toggle dark mode">
  <svg class="icon-sun" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>
  <svg class="icon-moon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
</button>
<header class="report-header">
  {LOGO32}
  <div>
    <h1>Magnite Connection Health — Rubicon vs MagniteDirect</h1>
    <div class="subtitle">Analytics Team · {kw['d1']} → {kw['d2']} · All products (OMP + PMP) · EUR · Updated {kw['generated']}</div>
  </div>
</header>

<div class="kpi-row">
  <div class="kpi-card"><div class="label">Rubicon Gross — {kw['month_label']}</div><div class="value">{kw['kpi_rub_month']}</div><div class="note">Latest full month</div></div>
  <div class="kpi-card highlight"><div class="label">MagniteDirect Gross since launch</div><div class="value">{kw['kpi_md_total']}</div><div class="note">Live since {kw['md_launch']}</div></div>
  <div class="kpi-card"><div class="label">Win Rate — Rubicon</div><div class="value">{kw['kpi_wr_rub']}</div><div class="note">{kw['d1']} – {kw['d2']}</div></div>
  <div class="kpi-card"><div class="label">Win Rate — MagniteDirect</div><div class="value">{kw['kpi_wr_md']}</div><div class="note">Since launch</div></div>
  <div class="kpi-card"><div class="label">CPM — Rubicon</div><div class="value">{kw['kpi_cpm_rub']}</div><div class="note">{kw['d1']} – {kw['d2']}</div></div>
</div>

<div class="caveats">
  <strong>Structural caveats</strong>
  <ul>
    <li><strong>Requests / Bid Rate / RPM cannot be split by channel</strong> — bid inputs are recorded before a channel is assigned, so channel-level demand volume is measured in bids.</li>
    <li><strong>Win Rate reads 0% on non-header-bidding integrations</strong> (e.g. elconfidencial.com) — judge those publishers on revenue, CPM and delivery instead.</li>
    <li><strong>Publisher-reported impressions lag ~3 days</strong> — CPM for the most recent days is provisional; missing values render as —, never as 0.</li>
  </ul>
</div>

<section>
<h2>1 · Evolution by channel {tooltip(kw['sql_daily'])}</h2>
<div class="chart-box"><div style="position:relative;height:320px"><canvas id="revChart"></canvas></div></div>
<p class="summary-line" id="s1Summary"></p>
<div class="chart-box"><div style="position:relative;height:280px"><canvas id="ratioChart"></canvas></div></div>
<p class="summary-line">Win Rate (solid, left axis) and CPM (dashed, right axis) per channel; recent CPM points are provisional due to the impression-reporting lag.</p>
<p class="data-footer">Source: Daily supply funnel — Magnite channels only (Rubicon &amp; MagniteDirect), all products, {kw['d1']} – {kw['d2']}, revenue in EUR.</p>
</section>

<section>
<h2>2 · MagniteDirect daily ramp since launch {tooltip(kw['sql_daily'])}</h2>
<div class="chart-box"><div style="position:relative;height:320px"><canvas id="rampChart"></canvas></div></div>
<p class="summary-line" id="s2Summary"></p>
<p class="data-footer">Source: Daily supply funnel — MagniteDirect channel only, all products, {kw['md_launch']} – {kw['d2']}, revenue in EUR.</p>
</section>

<section>
<h2>3 · Publisher head-to-head (both channels) {tooltip(kw['sql_pivot'])}</h2>
<div class="pivot-wrap"><table class="report-table" id="pivotTable"></table></div>
<p class="summary-line" id="pivotSummary"></p>
<p class="data-footer">Source: Daily supply funnel — publishers with Gross Revenue on both Rubicon and MagniteDirect, all products, {kw['d1']} – {kw['d2']}, revenue in EUR. Rows sorted by MagniteDirect Gross; MagniteDirect rows tinted coral; — = no data / provisional (impressions lag).</p>
</section>

<footer class="report-footer">{LOGO20}<span>Analytics Team · Magnite Connection Health — Rubicon vs MagniteDirect · {kw['d1']} → {kw['d2']}</span></footer>

<script>
const DAILY = {json.dumps(kw['DAILY'])};
const PIVOT = {json.dumps(kw['pivot'])};
const DATES = {kw['dates_js']};
const MD_DATES = DATES.filter(d=>d>='{kw['md_launch']}');
const COLORS = ['#5476FF','#E866F4','#948A8A','#67C8FE','#FFA071','#A36AFF','#F4D56D'];

function copyQuery(btn) {{
  const pre = btn.closest('.info-tooltip').querySelector('.sql-pre');
  navigator.clipboard.writeText(pre.textContent.trim()).then(()=>{{
    btn.textContent='\\u2713 Copied!'; btn.classList.add('copied');
    setTimeout(()=>{{btn.textContent='\\ud83d\\udccb Copy to clipboard'; btn.classList.remove('copied');}},2000);
  }}).catch(()=>{{ btn.textContent='\\u26a0 Copy failed';
    setTimeout(()=>{{btn.textContent='\\ud83d\\udccb Copy to clipboard';}},2000); }});
}}

function get(ch,d,k) {{ const r=DAILY[ch]&&DAILY[ch][d]; return r?r[k]:null; }}
function winRate(ch,d) {{ const r=DAILY[ch]&&DAILY[ch][d]; if(!r||!r.w) return null; return r.hw/r.w; }}
function cpm(ch,d) {{ const r=DAILY[ch]&&DAILY[ch][d]; if(!r||!r.ip) return null; return r.pr*1000/r.ip; }}
const fmtEUR = v => v==null?'—':'€'+v.toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}});

function themeOpts() {{
  const css=getComputedStyle(document.documentElement);
  return {{ text:css.getPropertyValue('--text').trim(),
           muted:css.getPropertyValue('--text-subtle').trim(),
           border:css.getPropertyValue('--border').trim() }};
}}
const t0=themeOpts();
function baseOpts() {{
  return {{ responsive:true, maintainAspectRatio:false,
    plugins:{{ legend:{{labels:{{color:t0.text,font:{{family:'Instrument Sans'}}}}}},
             tooltip:{{titleFont:{{family:'Instrument Sans'}},bodyFont:{{family:'Instrument Sans'}}}} }} }};
}}
const charts=[];

{{
const opt=baseOpts();
opt.scales={{ x:{{ticks:{{color:t0.muted}},grid:{{color:t0.border}},stacked:false}},
  y:{{type:'logarithmic',ticks:{{color:t0.muted,callback:v=>'€'+Number(v).toLocaleString()}},grid:{{color:t0.border}},title:{{display:true,text:'EUR (log scale)',color:t0.muted}}}} }};
charts.push(new Chart(document.getElementById('revChart'),{{type:'bar',data:{{labels:DATES,datasets:[
  {{label:'Rubicon Gross',data:DATES.map(d=>get('Rubicon',d,'g')),backgroundColor:COLORS[0]}},
  {{label:'Rubicon Publisher Rev',data:DATES.map(d=>{{const v=get('Rubicon',d,'pr');return v||null;}}),backgroundColor:COLORS[3]}},
  {{label:'MagniteDirect Gross',data:DATES.map(d=>get('MagniteDirect',d,'g')),backgroundColor:COLORS[1]}},
  {{label:'MagniteDirect Publisher Rev',data:DATES.map(d=>{{const v=get('MagniteDirect',d,'pr');return v||null;}}),backgroundColor:COLORS[5]}}
]}},options:opt}}));
}}

{{
const opt=baseOpts();
opt.scales={{ x:{{ticks:{{color:t0.muted}},grid:{{color:t0.border}}}},
  y:{{position:'left',ticks:{{color:t0.muted,callback:v=>(v*100).toFixed(0)+'%'}},grid:{{color:t0.border}},title:{{display:true,text:'Win Rate',color:t0.muted}}}},
  y2:{{position:'right',ticks:{{color:t0.muted,callback:v=>'€'+v.toFixed(2)}},grid:{{drawOnChartArea:false}},title:{{display:true,text:'CPM (EUR)',color:t0.muted}}}} }};
charts.push(new Chart(document.getElementById('ratioChart'),{{type:'line',data:{{labels:DATES,datasets:[
  {{label:'Rubicon Win Rate',data:DATES.map(d=>winRate('Rubicon',d)),borderColor:COLORS[0],backgroundColor:COLORS[0],yAxisID:'y',pointRadius:2,tension:0.25}},
  {{label:'MagniteDirect Win Rate',data:DATES.map(d=>winRate('MagniteDirect',d)),borderColor:COLORS[1],backgroundColor:COLORS[1],yAxisID:'y',pointRadius:2,tension:0.25}},
  {{label:'Rubicon CPM',data:DATES.map(d=>cpm('Rubicon',d)),borderColor:COLORS[3],backgroundColor:COLORS[3],yAxisID:'y2',borderDash:[5,4],pointRadius:2,tension:0.25}},
  {{label:'MagniteDirect CPM',data:DATES.map(d=>cpm('MagniteDirect',d)),borderColor:COLORS[5],backgroundColor:COLORS[5],yAxisID:'y2',borderDash:[5,4],pointRadius:2,tension:0.25}}
]}},options:opt}}));
}}

{{
const opt=baseOpts();
opt.scales={{ x:{{ticks:{{color:t0.muted}},grid:{{color:t0.border}}}},
  y:{{position:'left',ticks:{{color:t0.muted,callback:v=>'€'+Number(v).toLocaleString()}},grid:{{color:t0.border}},title:{{display:true,text:'Gross Revenue (EUR)',color:t0.muted}}}},
  y2:{{position:'right',ticks:{{color:t0.muted,callback:v=>(v*100).toFixed(0)+'%'}},grid:{{drawOnChartArea:false}},title:{{display:true,text:'Win Rate',color:t0.muted}}}} }};
charts.push(new Chart(document.getElementById('rampChart'),{{data:{{labels:MD_DATES,datasets:[
  {{type:'bar',label:'MagniteDirect Gross (EUR)',data:MD_DATES.map(d=>get('MagniteDirect',d,'g')),backgroundColor:'#FF6B7C',yAxisID:'y'}},
  {{type:'line',label:'Win Rate',data:MD_DATES.map(d=>winRate('MagniteDirect',d)),borderColor:COLORS[0],backgroundColor:COLORS[0],yAxisID:'y2',pointRadius:2,tension:0.25}}
]}},options:opt}}));
}}

{{
const lastD=DATES[DATES.length-1];
const mdLast=get('MagniteDirect',lastD,'g'), rubLast=get('Rubicon',lastD,'g');
document.getElementById('s1Summary').textContent=
  'Latest closed day ('+lastD+'): Rubicon '+fmtEUR(rubLast)+' Gross vs MagniteDirect '+fmtEUR(mdLast)+' — the log scale keeps both channels visible.';
const wrLast=winRate('MagniteDirect',lastD);
document.getElementById('s2Summary').textContent=
  'MagniteDirect Gross on '+lastD+': '+fmtEUR(mdLast)+(wrLast!=null?' with a '+(wrLast*100).toFixed(1)+'% Win Rate':'')+'.';
}}

{{
const tbl=document.getElementById('pivotTable');
const metrics=[['Gross Revenue','g',v=>v==null?'—':'€'+v.toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}})],
               ['CPM','c',v=>v==null?'—':'€'+v.toFixed(2)],
               ['Win Rate','w',v=>v==null?'—':(v*100).toFixed(1)+'%']];
let h='<thead><tr><th class="pub">Publisher</th><th style="text-align:left">Channel</th><th style="text-align:left">Metric</th>';
DATES.forEach(d=>h+='<th>'+d.slice(5)+'</th>');
h+='</tr></thead><tbody>';
PIVOT.order.forEach(pub=>{{
  ['MagniteDirect','Rubicon'].forEach((ch,ci)=>{{
    metrics.forEach((m,mi)=>{{
      const cls=(ci===0&&mi===0?'pub-first ':'')+(ch==='MagniteDirect'?'md-row':'');
      h+='<tr class="'+cls+'">';
      h+='<td class="pub">'+(ci===0&&mi===0?pub:'')+'</td>';
      h+='<td class="chan">'+(mi===0?ch:'')+'</td><td class="met">'+m[0]+'</td>';
      const days=PIVOT.pubs[pub][ch]||{{}};
      DATES.forEach(d=>{{ const r=days[d]; h+='<td>'+(r? m[2](r[m[1]]) : '—')+'</td>'; }});
      h+='</tr>';
    }});
  }});
}});
h+='</tbody>';
tbl.innerHTML=h;
document.getElementById('pivotSummary').textContent=
  PIVOT.order.length+' publishers are live on both channels; the biggest MagniteDirect contributor is '+PIVOT.order[0]+'.';
}}

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
