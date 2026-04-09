Analyze DRM-generated SQL scripts and deployment JSON for safety, impact, and best practices.

Arguments: `$ARGUMENTS` (optional: install path, uuid, or `<connection> <release>`, e.g. `dev 11` or `/home/mumr/drm_installed/drm`)

Steps:

1. **Resolve install path:**
   - If `$ARGUMENTS` starts with `/`, use it as the DRM install path.
   - Otherwise read `~/.drm-cli.json` for `drm_path`.

2. **Find files to analyze** in `<drm_path>/bin/`:
   - If a UUID or connection/release filter is given, match files by that pattern.
   - Otherwise use the **most recently modified** `{DryRun|Deploy|Align}_{uuid}_C*_R*.json` file (the deployment record, not a SQL file).
   - Find all `.sql` files sharing the same UUID as the selected JSON.
   - **Per-DB variant scripts:** DRM may generate one base script (`_S{n}-P{n}-{Project}-{DB}.sql`) plus per-DB variants (`_S{n}-P{n}-{Project}-{DB2}.sql`, etc.) for databases that failed and were retried individually. Group them by project — analyze the **base script** (earliest by modification time or smallest) and note how many per-DB variants exist.

3. **Read the deployment JSON** to extract context:
   - Type (DryRun/Deploy/Align), release name, connection, databases targeted, status, timestamp.
   - Note any failed tries and their error messages — these often explain what the SQL does.

4. **Read each SQL file** and perform the following analysis:

   ### A. What will be updated
   List every DDL/DML operation found:
   - Tables created / altered / dropped
   - Columns added / modified / removed
   - Indexes created / dropped
   - Stored procedures / views / functions created or altered
   - Data changes (INSERT / UPDATE / DELETE)
   - SQLCMD variables used (`$(varname)`) — flag these; if not set at runtime, they substitute as empty strings
   - Use a table: Object | Operation | Details

   **Schema marker pattern:** If the script only creates and immediately drops the same schema object (e.g. `CREATE SCHEMA x` then `DROP SCHEMA x`), classify it as a no-op idempotent marker — no risk.

   ### B. Dangerous operations ⚠️
   Flag any of the following with severity:

   | Severity | Pattern | Risk |
   |---|---|---|
   | 🔴 HIGH | `DROP TABLE`, `DROP COLUMN`, `TRUNCATE` | Irreversible data loss |
   | 🔴 HIGH | `TRUNCATE` before `CREATE TABLE` without wrapping transaction | TRUNCATE can't be rolled back if CREATE fails — data permanently lost |
   | 🔴 HIGH | `ALTER COLUMN` changing type/nullability | May fail or truncate data |
   | 🟡 MEDIUM | `CREATE TABLE` without `IF NOT EXISTS` / existence check | Fails if object exists — causes retry loops |
   | 🟡 MEDIUM | `DROP INDEX`, `DROP CONSTRAINT` | May break queries or integrity |
   | 🟡 MEDIUM | `UPDATE` / `DELETE` without WHERE | Mass data change |
   | 🟡 MEDIUM | SQLCMD variables (`$(var)`) with no fallback | Silent empty-string substitution if unset |
   | 🟢 LOW | `ADD COLUMN NOT NULL` without default | May fail on non-empty tables |
   | 🟢 LOW | Large `ALTER TABLE` on production | Locking risk |

   If no dangerous operations found, state "No destructive operations detected ✅"

   ### C. Best practice review
   Check and report:
   - [ ] Does the script use transactions / rollback on error?
   - [ ] Are `TRUNCATE` / destructive ops inside a transaction so they can be rolled back?
   - [ ] Are there `PRINT` statements for progress tracking?
   - [ ] Does it set `NOEXEC ON` guard (SQLCMD mode)?
   - [ ] Are `CREATE` statements guarded with existence checks (`IF object_id() IS NULL`) to prevent retry failures?
   - [ ] Are SQLCMD variables documented/defaulted?
   - [ ] Are constraints deferred or temporarily disabled during bulk changes?
   - [ ] Are indexes rebuilt after bulk inserts?
   - [ ] Is `SET NOCOUNT ON` used for performance?

   ### D. Pre-deployment checklist
   Based on findings, generate a checklist:
   - [ ] Back up affected databases before deploying
   - [ ] (if TRUNCATE) Verify data is no longer needed or already backed up
   - [ ] (if TRUNCATE before CREATE without transaction) Wrap in explicit transaction to allow rollback
   - [ ] (if ALTER COLUMN) Test against a copy of production data first
   - [ ] (if SQLCMD variables) Confirm all `$(var)` values are set in the deployment environment
   - [ ] (if no existence check on CREATE) Add `IF object_id('TableX') IS NULL` guard to prevent retry failures
   - [ ] Run dryrun on all target environments before deploying to prod
   - [ ] Review generated script manually before executing on production

5. **Summary**
   - Scripts: filenames, sizes, target DB(s), number of per-DB variants
   - Risk level: 🔴 HIGH / 🟡 MEDIUM / 🟢 LOW / ✅ SAFE
   - One-line verdict: e.g. "Safe to deploy — schema-only additions, no data loss risk."
   - If retries occurred during the deployment: explain root cause from the SQL patterns found

6. **Next steps:**
   - `/drm-deploy <connection> <release>` to execute the deployment
   - `/drm-flow` to review previous deployment history
