Run a DRM dryrun and present a structured deployment plan.

Arguments: `$ARGUMENTS` (format: `<connection> <release>`, e.g. `prod 3.1.0`)

Steps:
1. Parse `$ARGUMENTS` to extract connection name (first word) and release ID (remaining). If either is missing, ask the user.
2. Run the dryrun:
   ```
   node index.js deploy -c <connection> -r <release> --dryrun
   ```
3. Parse and summarise the output into a structured deployment plan:
   - **Release**: name/ID being deployed
   - **Target connection**: the connection name
   - **Solutions included**: list any solution names or script files mentioned in output
   - **Target databases**: any database names mentioned
   - **Warnings**: any WARNING lines from the output
   - **Generated scripts**: paths under `bin/` if mentioned
4. Present the plan clearly as a checklist or table.
5. If the dryrun succeeded with no warnings, say "Plan looks good. Run `/drm-deploy <connection> <release>` to execute."
6. If there are warnings or errors, highlight them and suggest fixes before deploying.
