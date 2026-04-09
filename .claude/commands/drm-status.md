Show the current DRM installation status and recent deployment history.

Steps:
1. Read `~/.drm-cli.json` to get the installed DRM path (`drm_path`). If the file does not exist, tell the user DRM is not installed and suggest running `drm-cli install`.
2. Read `<drm_path>/drm_deploy.config` (JSON file) and extract:
   - `installation_info.drm_version` (or `drm_version`)
   - `installation_info.installation_type` (sqlite or json)
   - `installation_info.db_secured` (boolean)
   - `config.db_file_name` (default: `drm_db`)
   - `config.sqlite_file_ext` (default: `sqlite`)
   - Derive the DB path: `<drm_path>/db/<db_file_name>.<sqlite_file_ext>`
3. Query the DRM SQLite database at the derived path using:
   ```
   python3 -c "
   import sqlite3, json, sys
   conn = sqlite3.connect(sys.argv[1])
   conn.row_factory = sqlite3.Row
   counts = conn.execute('SELECT (SELECT COUNT(*) FROM releases WHERE is_active=1) as releases, (SELECT COUNT(*) FROM connections WHERE is_active=1) as connections').fetchone()
   recent = conn.execute('SELECT r.name as release, c.name as connection, d.start_time, ds.name as status FROM deployments d JOIN releases r ON r.id=d.release_id JOIN connections c ON c.id=d.connection_id JOIN deployment_statuses ds ON ds.id=d.deployment_status_id ORDER BY d.start_time DESC LIMIT 5').fetchall()
   print(json.dumps({'counts': dict(counts), 'recent': [dict(r) for r in recent]}))
   conn.close()
   " <derived_db_path>
   ```
4. Display a formatted status summary:
   - DRM path, version, type, secured flag
   - Active release and connection counts
   - Table of last 5 deployments (release, connection, time, status)
