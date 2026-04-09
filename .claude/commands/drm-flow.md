Review DRM deployment flow history and summarise what happened.

Arguments: `$ARGUMENTS` (optional: install path or `<connection> <release>` filter, e.g. `/home/mumr/drm_installed/drm` or `dev 11`)

Steps:

1. **Resolve install path:**
   - If `$ARGUMENTS` starts with `/`, use it as the DRM install path.
   - Otherwise read `~/.drm-cli.json` for `drm_path`.
   - If unavailable, tell the user DRM is not installed.

2. **Find deployment JSON files** in `<drm_path>/bin/`:
   - Pattern: `{DryRun|Deploy|Align}_{uuid}_C{conn}_R{release}.json`
   - **Important:** match only files ending in `_R{release}.json` (no additional suffix) — SQL files like `_R12_S2-P2-Project_B-DB_B1.sql` share the same prefix but are not deployment records.
   - List all matching `.json` files sorted by modification time (newest first), limit 20.
   - If `$ARGUMENTS` contains a connection or release filter (e.g. `dev 11`), only include files matching `_Cdev_` and/or `_R11.json`.

3. **Parse each JSON file** and extract:
   - `deployment_type_name` (DryRun / Deploy / Align)
   - `release_name`, `connection_name`
   - `start_time`, `end_time` — compute overall duration in seconds
   - `deployment_status_name`
   - `error_message` (if any)
   - `deployments_tries[]` — each try has `try_num`, `start_time`, `end_time`, `deployment_status_name`, and nested solutions → projects

4. **Present a flow summary table** (newest first):

   | # | Type | Release | Connection | Start | Duration | Status |
   |---|---|---|---|---|---|---|
   | 1 | Deploy | R12 | dev | 2026-04-09 02:28 | 147s | ✅ Finished successfully |
   | 2 | DryRun | R12 | dev | 2026-04-09 02:23 | 27s | ✅ Finished successfully |

5. **For each deployment, show the detail tree** (newest first):

   Show each try with its own status. Per-project status icons:
   - ✅ `Finished successfully`
   - ❌ `Failed` — show error message inline
   - ⏭ `Already deployed` — skipped, already up to date
   - ⏳ `Pending` — was queued but never ran

   ```
   ▶ Deploy  R12 / dev  [2026-04-09 02:28:26 → 02:30:53]  ✅  (147s)
     └─ Try 1  ❌  (38s)
        └─ DRM mssql demo solution  ❌
           ├─ Project_B → DB_B1  ✅
           ├─ Project_B → DB_B2  ✅
           ├─ Project_C → DB_C3  ❌  "TableC" already exists (line 4)
           └─ Project_C → DB_C5  ❌  "TableC" already exists (line 4)
     └─ Try 2  ❌  (82s)
        └─ DRM mssql demo solution  ❌
           ├─ Project_B → DB_B1  ⏭  Already deployed
           ├─ Project_C → DB_C3  ✅
           └─ Project_C → DB_C8  ❌  "TableC" already exists (line 4)
     └─ Try 3  ✅  (25s)
        └─ DRM mssql demo solution  ✅
           ├─ Project_B → DB_B1  ⏭  Already deployed
           ├─ Project_C → DB_C8  ✅
           └─ Project_C → DB_C1  ⏳  Pending
   ```

   **Error message condensing:** strip the full file path from error messages; show only the meaningful part (e.g. `"TableC" already exists, line 4`).

6. **Overall summary:**
   - Total deployments shown, breakdown by type (DryRun / Deploy / Align)
   - Success rate (overall deployment status, not per-try)
   - Number of retries used (e.g. "3 tries") and why retries were needed
   - Any DBs that remained Pending after all tries — highlight these
   - Most recently deployed release and connection

7. **Next steps:**
   - `/drm-analyze` to review the SQL generated in the last deployment
   - `/drm-deploy <connection> <release>` to run a new deployment
