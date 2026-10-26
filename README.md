# Magnite Connection Health — daily dashboard

Self-contained HTML dashboard comparing the **Rubicon** (reseller) and **MagniteDirect**
(direct, live since 2026-07-10) pipes, rebuilt every day at **11:00 Europe/Madrid** by
GitHub Actions ([.github/workflows/update-dashboard.yml](.github/workflows/update-dashboard.yml)).

- `index.html` — the built dashboard: regenerated daily, published to Drive, never committed (see Viewing).
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
| `DRIVE_SA` | Full contents of the Drive service-account JSON (`~/.config/seedtag/prj-jdpa-*.json`) — same value as publisher_pnl's `DRIVE_SA` secret |

Each run also uploads `magnite_connection_health.html` to Google Drive, into the
**Magnite Direct Tracking** subfolder of the same shared root folder publisher_pnl
uses (override with `DRIVE_ROOT_FOLDER_ID` / `DRIVE_SUBFOLDER` / `DRIVE_FILENAME` env vars).

If the token ever needs recreating: `python scripts/trino_client.py --login`
(requires `credentials.json`), then update the secret.

## Viewing

**Google Drive is the only place the dashboard is published.** GitHub Pages was
never enabled (the API 404s and the `github.io` URL returns 404) — the line that
used to be here described a setup step nobody ran.

`index.html` is **gitignored and not committed**: it is a build artifact that the
run uploads straight to Drive. It had reached 52 MB and grew ~1.5 MB/day, which
took the repo to 933 MB of GitHub's 1 GB limit and tripped the 50 MB per-file
warning on every push. Same approach as
[source_truth_v2](https://github.com/juan-seedtag/source_truth_v2), whose
`/output/` is gitignored and whose repo is 4 MB.

`data/date_snapshots.json.gz` *is* committed — CI reads it to backfill missing
warehouse partitions, and `SNAPSHOT_DAYS` caps it at ~390 KB.

Run manually anytime from the **Actions** tab (`workflow_dispatch`) or locally:

```bash
pip install -r requirements.txt
TRINO_HOST=... TRINO_USER=... TRINO_PASSWORD=... python scripts/update_dashboard.py
```
