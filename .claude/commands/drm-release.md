List and inspect DRM releases.

Arguments: `$ARGUMENTS` (optional release ID for detail view, e.g. `42`)

Steps:
1. Read `~/.drm-cli.json` to get `drm_path`. If missing, tell the user DRM is not installed.
2. Query the DRM SQLite database at `<drm_path>/db/drm_db.sqlite`:

   **If no argument provided** — list all releases with last deployment status:
   ```python
   python3 -c "
   import sqlite3, json, sys
   conn = sqlite3.connect(sys.argv[1])
   conn.row_factory = sqlite3.Row
   rows = conn.execute('''
     SELECT r.id, r.name, r.is_active,
       (SELECT ds.name FROM deployments d
        JOIN deployment_statuses ds ON ds.id=d.deployment_status_id
        WHERE d.release_id=r.id ORDER BY d.start_time DESC LIMIT 1) as last_status,
       (SELECT d.start_time FROM deployments d WHERE d.release_id=r.id ORDER BY d.start_time DESC LIMIT 1) as last_deployed
     FROM releases r ORDER BY r.id
   ''').fetchall()
   print(json.dumps([dict(r) for r in rows]))
   conn.close()
   " <drm_path>/db/drm_db.sqlite
   ```
   Display as a table: ID | Name | Active | Last Status | Last Deployed

   **If a release ID is given** — show full detail for that release:
   - Release metadata (id, name, is_active)
   - All solutions associated with it (join through release_solutions or similar)
   - All connections it has been deployed to and their last status
   - Deployment history (last 10 deployments for this release)

3. At the end, suggest next steps:
   - `/drm-plan <connection> <release>` to preview a deployment
   - `/drm-deploy <connection> <release>` to deploy
