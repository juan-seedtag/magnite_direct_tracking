# Magnite Connection Health — daily dashboard

Self-contained HTML dashboard comparing the **Rubicon** (reseller) and **MagniteDirect**
(direct, live since 2026-07-10) pipes, rebuilt every day at **11:00 Europe/Madrid** by
GitHub Actions ([.github/workflows/update-dashboard.yml](.github/workflows/update-dashboard.yml)).

- `index.html` / `magnite_connection_health_latest.html` — latest dashboard (regenerated daily).
- `scripts/update_dashboard.py` — queries Trino (`analytics.etl_ssp_supply_funnel_daily_local`,
  all products, EUR, window 2026-07-01 → latest closed day) and renders the page.

## Required GitHub secrets

Set these under **Settings → Secrets and variables → Actions**:

| Secret | Value |
|---|---|
| `TRINO_HOST` | Trino coordinator host (no scheme) |
| `TRINO_PORT` | Port (optional, default 443) |
| `TRINO_USER` | Service account user |
| `TRINO_PASSWORD` | Password for basic auth — **or** set `TRINO_JWT` instead |
| `TRINO_JWT` | JWT token (optional alternative to password) |
| `TRINO_CATALOG` | Optional, default `st_datalakehouse` |

The interactive session used Seedtag SSO via the de-toolbox MCP server; CI cannot do SSO,
so it needs a service account (ask Data Engineering for one scoped read-only to
`st_datalakehouse.analytics`).

## Viewing

Enable **GitHub Pages** (Settings → Pages → deploy from `main`, root) and the dashboard
will be served at `https://juan-seedtag.github.io/magnite_direct_tracking/`.

Run manually anytime from the **Actions** tab (`workflow_dispatch`) or locally:

```bash
pip install -r requirements.txt
TRINO_HOST=... TRINO_USER=... TRINO_PASSWORD=... python scripts/update_dashboard.py
```
