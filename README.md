# Magnite Connection Health — RETIRED, moved to the dashboards framework

**Since 2026-10-26 this dashboard lives in
[seedtag/analytics-ai → dashboards/magnite-connection-health](https://github.com/seedtag/analytics-ai/tree/main/dashboards/magnite-connection-health)**
and is served by the Seedtag Dashboards portal:

https://script.google.com/a/macros/seedtag.com/s/AKfycbwz-lpJ3p1V4cV9lWqOLe6m6Nw8NSYxhDdK3BmdqICc1FgciytDhuLcLXqOaaAyJPBX/exec?app=magnite-connection-health

The old share link (legacy portal `?fileId=1MHf06N5zivDTeb3ECWJkZA-UNAXv070w`) now
serves a page that forwards there.

## Why it moved

This repo was a standalone script that baked every row into one HTML and
overwrote a Drive file read by the legacy portal. The page grew ~1.5 MB/day
(publisher-grain rows for an ever-longer window) and reached **52 MB on
2026-10-25**; the legacy portal reads files with `DriveApp.getBlob()`, which
refuses anything over 50 MB, so the link went dark. Committing that file daily
had also taken this repo to 933 MB of GitHub's 1 GB limit.

In the framework the page is static, the launch-to-date totals travel in a
~4 MB `data.json`, and the publisher-grain detail is split into one lazy part
per ISO week that the page fetches only when a publisher is selected or an
editorial group is expanded. The queries, the HB-family guard, the suspect-date
guard and the missing-partition snapshots are the same rules, ported to
`transform.py` (the snapshot now lives in the framework's `_state.json`).

## What is left here

- `scripts/update_dashboard.py` still builds the old single-file page locally
  (`python scripts/update_dashboard.py`) — useful only for a side-by-side
  check. The scheduled workflow was removed; nothing refreshes from here.
- `data/date_snapshots.json.gz` — the last partition snapshot the old job kept.

History before the migration: see the git log (the daily `Daily dashboard
refresh` commits are the old job overwriting `index.html`).
