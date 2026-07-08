# India Macro Tracker

A daily-refreshed dashboard of 61 Indian macro series across 10 categories, each compared to
its previous period, the same period last year, and its trailing 12-period average.

```
BLUEPRINT.md                 the full plan: sources, access, calendar, architecture
dashboard.html               the dashboard (self-contained; open in any browser)
data/data.json               the data layer the page renders (regenerated on refresh)
pipeline/
  catalog.py                 all 69 series + 4 composite indices: source, freq, rollup rule, up-is-good
  generate_data.py           comparison engine (currently emits flagged sample data)
  template.html              page template (data injected at build time)
  build_dashboard.py         data.json + template -> dashboard.html
  refresh.py                 daily entry point (fetchers -> data -> page)
  fetchers/                  one module per source; wire these to go live
.github/workflows/refresh.yml   daily cron (19:45 & 09:15 IST)
```

Refresh manually: `python3 pipeline/refresh.py --sample` (or without the flag once fetchers
are wired). Add a series: append to `catalog.py`, map it in a fetcher, done — the page,
rollups and freshness table pick it up automatically.

## Go-live on GitHub Pages (one-time, ~5 minutes)

1. Create a GitHub account (or use the firm's) and a new repository, e.g. `india-macro-tracker`.
   Public repo = simplest (all data here is public-domain macro stats). Private repo also works —
   note Pages URLs from private repos are still publicly reachable unless on GitHub Enterprise.
2. Push this folder to the repo (or hand Claude a fine-grained personal access token with
   Contents: read/write + Workflows + Pages: read/write on that one repo, and it will be done for you):

       git init && git add -A && git commit -m "initial"
       git branch -M main
       git remote add origin https://github.com/<user>/india-macro-tracker.git
       git push -u origin main

3. Repo Settings -> Pages -> Source: "Deploy from a branch" -> Branch: main, folder: / (root). Save.
4. Repo Settings -> Actions -> General -> Workflow permissions: "Read and write permissions". Save.
5. Done. The tracker is live at  https://<user>.github.io/india-macro-tracker/
   GitHub Actions refreshes it daily at 19:45 & 09:15 IST (see .github/workflows/refresh.yml);
   your team just bookmarks the URL. Optional: add SLACK_WEBHOOK_URL as an Actions secret for alerts.

Runbook notes: if a fetcher fails, the workflow still publishes with last good data and the tile
shows its last period (staleness visible in the freshness table). MoSPI/NSDL may occasionally
block GitHub's datacenter IPs — if a fetcher 403s persistently, run the refresh from any
India-friendly runner (self-hosted or a small VM) instead.
