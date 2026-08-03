import json

daily = [
 # date, channel, gross, pubrev, wins, hb_wins, imps_paid
 ("2026-07-01","Rubicon",113025.54,74526.59,457492897,75080385,133080682),
 ("2026-07-02","Rubicon",118116.51,77576.28,490567762,76727060,137077313),
 ("2026-07-03","Rubicon",105063.56,69561.65,479823041,72516036,132615376),
 ("2026-07-04","Rubicon",106338.70,70305.94,470627422,72361145,128810501),
 ("2026-07-05","Rubicon",113521.20,75552.88,483376361,76299600,139041777),
 ("2026-07-06","Rubicon",113483.84,74770.67,531942910,78546975,140328969),
 ("2026-07-07","Rubicon",112354.04,74691.42,553715139,81841558,145470097),
 ("2026-07-08","Rubicon",110134.75,72682.95,514394968,78611239,140884286),
 ("2026-07-09","Rubicon",113892.58,74211.20,513258696,80405885,139437709),
 ("2026-07-10","Rubicon",118815.69,78205.16,545021106,83868551,142175930),
 ("2026-07-10","MagniteDirect",0.82,0.28,3487,62,2369),
 ("2026-07-11","Rubicon",123737.81,80841.03,544324034,84789404,148702254),
 ("2026-07-11","MagniteDirect",4.27,1.39,31208,716,19754),
 ("2026-07-12","Rubicon",121252.07,79464.76,543184336,85122379,157589919),
 ("2026-07-12","MagniteDirect",35.07,11.03,129933,1227,87673),
 ("2026-07-13","Rubicon",119688.32,78821.25,524787529,82848906,152031575),
 ("2026-07-13","MagniteDirect",78.25,25.48,221909,3618,134642),
 ("2026-07-14","Rubicon",124919.75,81897.76,522625970,84967081,147605662),
 ("2026-07-14","MagniteDirect",245.21,77.62,310835,4401,208330),
 ("2026-07-15","Rubicon",122049.48,79164.21,518390908,83150392,145301314),
 ("2026-07-15","MagniteDirect",226.98,71.69,293298,3768,220910),
 ("2026-07-16","Rubicon",119443.60,76971.55,515344723,80101671,150400703),
 ("2026-07-16","MagniteDirect",284.32,91.47,423728,7807,303054),
 ("2026-07-17","Rubicon",122599.20,79769.63,518418567,82553056,150391211),
 ("2026-07-17","MagniteDirect",549.53,175.30,888605,37215,407250),
 ("2026-07-18","Rubicon",120324.90,78875.07,534327750,85601048,144609637),
 ("2026-07-18","MagniteDirect",778.22,258.46,1893818,118725,655173),
 ("2026-07-19","Rubicon",124728.48,81049.57,562209365,92177974,151701219),
 ("2026-07-19","MagniteDirect",450.39,157.28,2001794,149799,722760),
 ("2026-07-20","Rubicon",120074.77,78215.35,533872699,88342629,156600160),
 ("2026-07-20","MagniteDirect",515.40,183.48,2385521,161543,960623),
 ("2026-07-21","Rubicon",129865.46,83834.69,528333915,86943361,157666858),
 ("2026-07-21","MagniteDirect",546.91,197.04,2019885,140530,920505),
 ("2026-07-22","Rubicon",127190.37,80058.04,539952869,84947399,152877743),
 ("2026-07-22","MagniteDirect",570.80,204.12,2008459,128055,866253),
 ("2026-07-23","Rubicon",127262.95,79522.61,566270427,81410883,150688911),
 ("2026-07-23","MagniteDirect",371.90,128.94,1316802,50581,524657),
 ("2026-07-24","Rubicon",125252.00,79178.60,561639401,83104355,149096732),
 ("2026-07-24","MagniteDirect",485.45,171.48,1747906,62725,763216),
 ("2026-07-25","Rubicon",130968.90,84023.34,563759078,84051173,151265051),
 ("2026-07-25","MagniteDirect",428.46,153.22,1765907,55147,804849),
 ("2026-07-26","Rubicon",131170.73,83195.63,557208843,84288079,158768819),
 ("2026-07-26","MagniteDirect",566.14,204.40,2391786,59452,1008349),
 ("2026-07-27","Rubicon",126271.58,79732.62,550025079,82847818,158897984),
 ("2026-07-27","MagniteDirect",550.52,194.88,2917482,60421,1160731),
 ("2026-07-28","Rubicon",126798.52,80533.37,568741720,84322086,159518332),
 ("2026-07-28","MagniteDirect",832.74,301.11,4043868,87746,1657009),
 ("2026-07-29","Rubicon",121636.19,76037.12,566457300,81396390,155590247),
 ("2026-07-29","MagniteDirect",1063.64,400.94,5488298,181404,1975774),
 ("2026-07-30","Rubicon",120800.22,0,566878538,80169090,0),
 ("2026-07-30","MagniteDirect",1267.05,0,8164164,465027,0),
 ("2026-07-31","Rubicon",120698.50,0,550827329,81182589,0),
 ("2026-07-31","MagniteDirect",1297.53,0,8098805,589735,0),
 ("2026-08-01","Rubicon",117426.44,0,518214856,78807429,0),
 ("2026-08-01","MagniteDirect",1565.88,0,8134219,817806,0),
 ("2026-08-02","Rubicon",115661.68,74184.90,539631219,81902853,154121054),
 ("2026-08-02","MagniteDirect",1592.81,841.52,8593263,798855,2848590),
]
DAILY = {}
for d,ch,g,pr,w,hw,ip in daily:
    DAILY.setdefault(ch,{})[d] = {"g":g,"pr":pr,"w":w,"hw":hw,"ip":ip}

pivot = json.load(open("/Users/jperez/Desktop/Seedtag/notebooks/magnite_direct_tracking/pub_pivot.json"))

KPI = {
  "rubicon_july_gross": 3731480.21,
  "md_gross_since_launch": 14308.28,
  "wr_rubicon": 0.154045,
  "wr_md": 0.061070,
  "cpm_rubicon": 0.527363,
}

SQL_DAILY = """-- @user:juanperez@seedtag.com @skill:barbi
SELECT date, channel_id,
  SUM(revenue_st_eur) AS gross_eur,
  SUM(publisher_revenue_eur) AS pub_rev_eur,
  SUM(wins) AS wins, SUM(hb_wins) AS hb_wins,
  SUM(imps_paid) AS imps_paid
FROM st_datalakehouse.analytics.etl_ssp_supply_funnel_daily_local
WHERE date BETWEEN DATE '2026-07-01' AND DATE '2026-08-02'
  AND channel_id IN ('MagniteDirect','Rubicon')
GROUP BY 1,2 ORDER BY 1,2"""

SQL_KPI = """-- @user:juanperez@seedtag.com @skill:barbi
SELECT channel_id,
  SUM(CASE WHEN date BETWEEN DATE '2026-07-01' AND DATE '2026-07-31' THEN revenue_st_eur ELSE 0 END) AS gross_july,
  SUM(revenue_st_eur) AS gross_total,
  SUM(publisher_revenue_eur) AS pub_rev_total,
  IF(SUM(wins)=0, NULL, SUM(hb_wins)*1.0/SUM(wins)) AS win_rate,
  IF(SUM(imps_paid)=0, NULL, SUM(publisher_revenue_eur)*1000.0/SUM(imps_paid)) AS cpm
FROM st_datalakehouse.analytics.etl_ssp_supply_funnel_daily_local
WHERE date BETWEEN DATE '2026-07-01' AND DATE '2026-08-02'
  AND channel_id IN ('MagniteDirect','Rubicon')
GROUP BY 1"""

SQL_PIVOT = """-- @user:juanperez@seedtag.com @skill:barbi
WITH both_pubs AS (
  SELECT publisher_name
  FROM st_datalakehouse.analytics.etl_ssp_supply_funnel_daily_local
  WHERE date BETWEEN DATE '2026-07-01' AND DATE '2026-08-02'
    AND channel_id IN ('MagniteDirect','Rubicon')
  GROUP BY 1
  HAVING SUM(CASE WHEN channel_id='MagniteDirect' THEN revenue_st_eur ELSE 0 END) > 0
     AND SUM(CASE WHEN channel_id='Rubicon' THEN revenue_st_eur ELSE 0 END) > 0
)
SELECT f.publisher_name, f.channel_id, f.date,
  SUM(f.revenue_st_eur) AS gross_eur,
  IF(SUM(f.imps_paid)=0, NULL, SUM(f.publisher_revenue_eur)*1000.0/SUM(f.imps_paid)) AS cpm,
  IF(SUM(f.wins)=0, NULL, SUM(f.hb_wins)*1.0/SUM(f.wins)) AS win_rate
FROM st_datalakehouse.analytics.etl_ssp_supply_funnel_daily_local f
JOIN both_pubs b ON f.publisher_name = b.publisher_name
WHERE f.date BETWEEN DATE '2026-07-01' AND DATE '2026-08-02'
  AND f.channel_id IN ('MagniteDirect','Rubicon')
GROUP BY 1,2,3 ORDER BY 1,2,3"""

def tooltip(sql):
    esc = sql.replace("&","&amp;").replace("<","&lt;")
    return f'''<span class="info-wrap"><span class="info-icon">i</span><div class="info-tooltip"><div class="tooltip-header"><span class="tooltip-label">SQL Query</span><button class="copy-btn" onclick="copyQuery(this)">&#128203; Copy to clipboard</button></div><pre class="sql-pre">{esc}</pre></div></span>'''

LOGO32 = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="32" height="32" aria-label="Seedtag" class="logo"><circle cx="50" cy="50" r="50" fill="#FF6B7C"/><circle cx="50" cy="27" r="10" fill="white"/><path d="M50,54 C47,47 16,49 15,65 C14,79 35,84 50,79Z" fill="white"/><path d="M50,54 C53,47 84,49 85,65 C86,79 65,84 50,79Z" fill="white"/></svg>'
LOGO20 = LOGO32.replace('width="32" height="32"','width="20" height="20"')

html = f"""<!DOCTYPE html>
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
    <div class="subtitle">Analytics Team · 2026-07-01 → 2026-08-02 · All products (OMP + PMP) · EUR</div>
  </div>
</header>

<div class="kpi-row">
  <div class="kpi-card"><div class="label">Rubicon Gross — July 2026</div><div class="value">€3,731,480.21</div><div class="note">Latest full month</div></div>
  <div class="kpi-card highlight"><div class="label">MagniteDirect Gross since launch</div><div class="value">€14,308.28</div><div class="note">Live since 2026-07-10</div></div>
  <div class="kpi-card"><div class="label">Win Rate — Rubicon</div><div class="value">15.4%</div><div class="note">Jul 1 – Aug 2</div></div>
  <div class="kpi-card"><div class="label">Win Rate — MagniteDirect</div><div class="value">6.1%</div><div class="note">Since launch</div></div>
  <div class="kpi-card"><div class="label">CPM — Rubicon</div><div class="value">€0.53</div><div class="note">Jul 1 – Aug 2</div></div>
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
<h2>1 · Evolution by channel {tooltip(SQL_DAILY)}</h2>
<div class="chart-box"><div style="position:relative;height:320px"><canvas id="revChart"></canvas></div></div>
<p class="summary-line">Rubicon delivered €3.73M Gross in July; MagniteDirect ramped from under €1/day at launch to ~€1.6k/day by early August — the log scale keeps both visible.</p>
<div class="chart-box"><div style="position:relative;height:280px"><canvas id="ratioChart"></canvas></div></div>
<p class="summary-line">Rubicon's Win Rate holds around 15% with CPM near €0.53; MagniteDirect's Win Rate is climbing towards ~10% as volume ramps, with a lower blended CPM so far (€0.24 cumulative).</p>
<p class="data-footer">Source: Daily supply funnel — Magnite channels only (Rubicon &amp; MagniteDirect), all products, 1 Jul – 2 Aug 2026, revenue in EUR.</p>
</section>

<section>
<h2>2 · MagniteDirect daily ramp since launch {tooltip(SQL_DAILY)}</h2>
<div class="chart-box"><div style="position:relative;height:320px"><canvas id="rampChart"></canvas></div></div>
<p class="summary-line">Since going live on 10 Jul, MagniteDirect Gross has grown steadily to ~€1.6k/day, with Win Rate improving from &lt;2% to ~10% as more supply is activated.</p>
<p class="data-footer">Source: Daily supply funnel — MagniteDirect channel only, all products, 10 Jul – 2 Aug 2026, revenue in EUR.</p>
</section>

<section>
<h2>3 · Publisher head-to-head (both channels) {tooltip(SQL_PIVOT)}</h2>
<div class="pivot-wrap"><table class="report-table" id="pivotTable"></table></div>
<p class="summary-line" id="pivotSummary"></p>
<p class="data-footer">Source: Daily supply funnel — publishers with Gross Revenue on both Rubicon and MagniteDirect, all products, 1 Jul – 2 Aug 2026, revenue in EUR. Rows sorted by MagniteDirect Gross; MagniteDirect rows tinted coral; — = no data / provisional (impressions lag).</p>
</section>

<footer class="report-footer">{LOGO20}<span>Analytics Team · Magnite Connection Health — Rubicon vs MagniteDirect · 2026-07-01 → 2026-08-02</span></footer>

<script>
const DAILY = {json.dumps(DAILY)};
const PIVOT = {json.dumps(pivot)};
const DATES = Array.from({{length:33}}, (_,i)=>{{const d=new Date(Date.UTC(2026,6,1+i));return d.toISOString().slice(0,10);}});
const MD_DATES = DATES.filter(d=>d>='2026-07-10');
const COLORS = ['#5476FF','#E866F4','#948A8A','#67C8FE','#FFA071','#A36AFF','#F4D56D'];

function copyQuery(btn) {{
  const pre = btn.closest('.info-tooltip').querySelector('.sql-pre');
  navigator.clipboard.writeText(pre.textContent.trim()).then(()=>{{
    btn.textContent='\\u2713 Copied!'; btn.classList.add('copied');
    setTimeout(()=>{{btn.textContent='\\ud83d\\udccb Copy to clipboard'; btn.classList.remove('copied');}},2000);
  }}).catch(()=>{{ btn.textContent='\\u26a0 Copy failed';
    setTimeout(()=>{{btn.textContent='\\ud83d\\udccb Copy to clipboard';}},2000); }});
}}

const fmtEUR = v => v==null?'—':'€'+v.toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}});
const fmtPct = v => v==null?'—':(v*100).toFixed(1)+'%';

function get(ch,d,k) {{ const r=DAILY[ch]&&DAILY[ch][d]; return r?r[k]:null; }}
function winRate(ch,d) {{ const r=DAILY[ch]&&DAILY[ch][d]; if(!r||!r.w) return null; return r.hw/r.w; }}
function cpm(ch,d) {{ const r=DAILY[ch]&&DAILY[ch][d]; if(!r||!r.ip) return null; return r.pr*1000/r.ip; }}

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

// Chart 1: Gross & Publisher Revenue per channel, log scale bars
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

// Chart 2: Win rate / CPM companion lines
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

// Chart 3: MagniteDirect daily ramp
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

// Pivot table
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

out='/Users/jperez/Desktop/Seedtag/notebooks/magnite_direct_tracking/magnite_connection_health_2026-08-03.html'
open(out,'w').write(html)
print('written', out, len(html))
