# Magnite Connection Health — daily dashboard

Self-contained HTML dashboard comparing the **Rubicon** (reseller) and **MagniteDirect**
(direct, live since 2026-07-10) pipes, rebuilt every day at **11:00 Europe/Madrid** by
GitHub Actions ([.github/workflows/update-dashboard.yml](.github/workflows/update-dashboard.yml)).

- `index.html` / `magnite_connection_health_latest.html` — latest dashboard (regenerated daily).
- `scripts/update_dashboard.py` — queries Trino (`analytics.etl_ssp_supply_funnel_daily_local`,
  all products, EUR, window 2026-07-01 → latest closed day) and renders the page.

## Required GitHub secrets

Same auth pattern as [publisher_pnl](https://github.com/juan-seedtag/publisher_pnl):
Google OAuth against `trino-users.seedt.ag`, auto-refreshed on every request
(`scripts/trino_client.py`). Set these under **Settings → Secrets and variables → Actions**:

| Secret | Value |
|---|---|
| `GOOGLE_TOKEN` | Full contents of `~/.config/seedtag/token.json` |
| `TRINO_USER` | Your Seedtag email (e.g. `juanperez@seedtag.com`) |

If the token ever needs recreating: `python scripts/trino_client.py --login`
(requires `credentials.json`), then update the secret.

## Viewing

Enable **GitHub Pages** (Settings → Pages → deploy from `main`, root) and the dashboard
will be served at `https://juan-seedtag.github.io/magnite_direct_tracking/`.

Run manually anytime from the **Actions** tab (`workflow_dispatch`) or locally:

```bash
pip install -r requirements.txt
TRINO_HOST=... TRINO_USER=... TRINO_PASSWORD=... python scripts/update_dashboard.py
```
