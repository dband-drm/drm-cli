Run a guided DRM deployment with dryrun confirmation.

Arguments: `$ARGUMENTS` (format: `<connection> <release>`, e.g. `staging 2.0.0`)

Steps:
1. Parse `$ARGUMENTS` to extract the connection name (first word) and release ID (remaining words). If either is missing, ask the user to provide them.
2. Run the dryrun first:
   ```
   node /home/mumr/mycode/DRM-cli/index.js deploy -c <connection> -r <release> --dryrun
   ```
   Capture and display the full output to the user.
3. Ask the user: "Dryrun complete. Proceed with actual deployment? (yes/no)"
4. If yes, run the deployment:
   ```
   node /home/mumr/mycode/DRM-cli/index.js deploy -c <connection> -r <release> --deploy
   ```
   Display the full output and report success or failure clearly.
5. If no, confirm the deployment was cancelled.

If the commands fail with an encryption error, tell the user to re-run with the `-p <key>` flag or set the `DRM_SECRET` environment variable.
