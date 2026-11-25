# EOD refresh, incident response and rollback

The **research study is frozen at 31 December 2025**. It does not change when market data refreshes. The EOD workflow runs at 00:15 UTC Tuesday–Saturday, after 18:00 New York on the preceding US business date in either daylight-saving state. Treasury can publish late; the workflow records the returned source date and does not manufacture a new date on holidays.

`scripts/refresh_market.py` fetches the official annual par CSV, validates complete core tenors, ordered unique dates, finite values, positive bootstrapped DFs and par repricing. A date regression is rejected. Candidate `data/latest.json` is atomically replaced only after validation. `data/health.json` records each attempt. Failure never overwrites the prior successful market snapshot. The dashboard labels a source date over four calendar days old as stale; that heuristic is a display rule, not a Treasury holiday calendar.

## Manual refresh and failure challenge

```bash
python scripts/refresh_market.py
python -m unittest discover -s tests -p test_operations.py -v
```

For a reproducible local simulation, pass `--year 2025 --csv data/raw/treasury_par_2025.csv --directory outputs/market-test`. This is a simulated receipt from the supplied source bytes, not a new live fetch. Never copy a simulated receipt over a deployed current-market receipt without labelling the source clock.

The workflow commits market/health receipts separately and does not rebuild research. With branch-based GitHub Pages, ordinary GitHub Actions bot pushes may not trigger a Pages build. The page fetches the receipt from the raw `main` branch so users can read the latest receipt independently of a static deployment. A minute-based query key avoids a previously cached placeholder at the raw-file CDN. On a network/CORS failure, it explicitly retains the frozen study and shows that current receipt retrieval is unavailable.

## Incident response

1. Inspect the failed Actions job and `data/health.json`; distinguish source failure from schema, missing tenor, regression or calibration failure.
2. Confirm the hash of `data/latest.json` matches the last successful receipt if a source fetch failed. Do not replace missing rates with zero.
3. Re-run the workflow after the source recovers. Do not alter research parameters to make a market refresh pass.
4. For a convention or engine bug, create a new research version, rebuild affected artifacts and document economic impact. Preserve the prior release and its negative results.

## Rollback

For a bad market receipt, restore `data/latest.json` from a known good Git revision, commit the restoration with an explanatory message and verify source date/health in the dashboard. For a bad static release, revert the release commit or redeploy the prior tagged revision through Pages. Re-run CI. The failure tests exercise atomic retention; a dry-run rollback exercise copies a saved receipt aside, injects failure, restores it and verifies exact bytes in a temporary directory. No destructive rollback of published history is automatic.

No keys or trading accounts are used. Refresh permissions are limited to repository contents. No claim of a streaming quote feed, prospective investment process or actual fund operation is made.
