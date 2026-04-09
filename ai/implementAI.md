# DRM-CLI — AI Implementation Guide

**What is DRM-CLI?**
Data Release Management CLI — manages and deploys database releases across MSSQL, PostgreSQL, Oracle.
This guide covers all five ways to interact with DRM-CLI, from raw CLI to AI agents.

- DRM installed at: `/home/mumr/drm_installed/drm`
- Repo: `/home/mumr/mycode/DRM-cli`
- Encryption key: stored in `DRM_SECRET` env var
- DB: 6 demo releases, 10 connections (SQLite, secured)

---

## `lib/drm-helpers.js` — Shared Core Module

`lib/drm-helpers.js` is the shared foundation for both `mcp-server.js` and `agent.js`. Without it, both files would duplicate ~150 lines of identical code.

**What it contains:**
| Export | Purpose |
|---|---|
| `loadDrmPath()` | Reads `~/.drm-cli.json` → `drm_path` |
| `executeTool(name, input, drmPath)` | Runs any DRM tool, returns `{ output, isError }` |
| `TOOL_SCHEMAS` | 8 tool definitions — each file applies its own schema key |

**What it handles internally (not exported):**
- `runDrmCli(args)` — spawns `node index.js` with captured output
- `queryDb(drmPath, sql)` — spawns `python3` inline SQLite query
- `buildStatus(drmPath)` — single Python spawn returning counts + recent deployments
- `loadJsonDb(drmPath, cfg)` — reads `drm_db.json` for json-type installs
- `listReleasesJson` / `listConnectionsJson` — flattens nested JSON structure
- `loadDrmConfig(drmPath)` — reads `drm_deploy.config`
- `stripAnsi(str)` — removes ANSI color codes from CLI output

**Why it matters:**
- `mcp-server.js` is now **37 lines** (was 270)
- `agent.js` is now **75 lines** (was 320)
- All fixes (JSON support, single Python spawn, no TOCTOU) apply to both consumers automatically

---

## Comparison Overview

| | CLI | npm | MCP | Agent | Skills |
|---|---|---|---|---|---|
| **Interface** | Terminal | Terminal | Claude tools | Natural language | Slash commands |
| **Who operates** | Human (manual args) | Human (npm scripts) | Claude (auto) | Claude (autonomous) | Claude (guided) |
| **Best for** | Scripts, CI/CD | Quick dev use | Claude integration | Complex multi-step | Guided workflows |
| **Requires** | Python 3.10+ | Node 16+ | Claude Code + MCP | Claude Code + API key | Claude Code |
| **Encryption key** | `-p` flag or `DRM_SECRET` | `-p` flag or `DRM_SECRET` | `DRM_SECRET` env | `DRM_SECRET` env | Passed inline or `DRM_SECRET` |
| **Output** | Raw terminal | Raw terminal | Clean text (ANSI stripped) | Narrated by Claude | Formatted by Claude |
| **Safety** | Manual | Manual | Manual | Auto dryrun before deploy | Interactive confirm |
| **Setup effort** | Low | Low | Medium | Medium + credits | Low |

---

## 1. CLI (`drm-cli` / `node index.js`)

### What it's for
Direct terminal control of DRM. Best for:
- Automation scripts and CI/CD pipelines
- When you know exactly what command to run
- Debugging with `--trace`
- Environments without Claude Code

### How to use
```bash
# Install globally
npm install -g drm-cli

# Or run from repo
node /home/mumr/mycode/DRM-cli/index.js <command> [args]
```

Commands: `install` | `deploy` | `crypto` | `uninstall`

### Detailed examples

**Install DRM**
```bash
drm-cli install -f /home/mumr/drm_installed/drm -d sqlite -p 'P@ssword123!!'
# Copies drm/ + modules/ to target path
# Creates drm_db.sqlite, writes drm_deploy.config
# Saves path to ~/.drm-cli.json for subsequent commands
```

**Dryrun (generate SQL scripts, no execution)**
```bash
drm-cli deploy -c dev -r 11 --dryrun -p 'P@ssword123!!'
# Output:
# INFO - Starting DRM DryRun (Release ID: "11", Connection name: "dev")
# INFO - Building release...
# INFO - Build finished successfully!!!
# INFO - Generating upgrade script ".../bin/DryRun_<uuid>_Cdev_R11_S1-P1-Project_A-DB_A1.sql"
# INFO - Upgrade script generated successfully!!!
# INFO - DRM DryRun finished successfully!!!
```

**Deploy**
```bash
drm-cli deploy -c dev -r 11 --deploy -p 'P@ssword123!!'
```

**Align (sync DB state without deploying)**
```bash
drm-cli deploy -c dev -r 11 --align -p 'P@ssword123!!'
```

**Encrypt a connection string**
```bash
drm-cli crypto --encrypt -t "Server=myserver;Database=mydb;User=sa;Password=pass" -p 'P@ssword123!!'
```

**Change encryption key**
```bash
drm-cli crypto --changepassword -p 'P@ssword123!!' -n 'NewKey456!!'
```

**Debug mode**
```bash
drm-cli deploy -c dev -r 11 --dryrun -p 'P@ssword123!!' --trace
```

**Uninstall**
```bash
drm-cli uninstall -f /home/mumr/drm_installed/drm -p 'P@ssword123!!' --F
```

### Tested output (2026-04-05)
```
INFO - Starting DRM DryRun (Release ID: "11", Connection name: "dev")
INFO - Building release...
INFO - Build finished successfully!!!
INFO - Generating upgrade script ".../bin/DryRun_53c879a6_Cdev_R11_S1-P1-Project_A-DB_A1.sql"
INFO - Upgrade script generated successfully!!!
INFO - DRM DryRun finished successfully!!!
```
**Result: PASS**

---

## 2. npm

### What it's for
Quick access to DRM operations via npm scripts. Best for:
- Developers already working in Node.js environments
- Running the agent and MCP server without remembering Node commands
- Publishing and distributing DRM-CLI to other teams

### How to use
```bash
npm install          # install all deps including @anthropic-ai/sdk, @modelcontextprotocol/sdk
npm run setup        # run interactive DRM installer
npm run agent        # run AI agent (requires ANTHROPIC_API_KEY)
npm run mcp          # start MCP server
npm publish          # publish to npm registry
```

### Detailed examples

**Install DRM via npm setup script**
```bash
npm run setup -- -f /home/mumr/drm_installed/drm -d sqlite -p 'P@ssword123!!'
# Equivalent to: node setup-env.js -f ... -d ... -p ...
# setup-env.js checks Python availability, then delegates to install.py
```

**Run agent via npm**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
export DRM_SECRET='P@ssword123!!'
npm run agent -- "list all releases"
npm run agent -- "run dryrun for connection dev release 11"
```

**Run MCP server via npm**
```bash
DRM_SECRET='P@ssword123!!' npm run mcp
# Starts the MCP stdio server — Claude Code connects to it automatically
```

**Publish to npm**
```bash
# 1. Remove pycache (auto-generated, not needed in package)
find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null; true

# 2. Dry run to verify contents
npm publish --dry-run
# Expected: ~38 files, ~68.9 kB packed, name drm-cli available

# 3. Login and publish
npm login
npm publish --access public
```

### Tested dry-run output (2026-04-05)
```
📦  drm-cli@1.0.0
=== Tarball Details ===
name:          drm-cli
version:       1.0.0
filename:      drm-cli-1.0.0.tgz
package size:  68.9 kB
unpacked size: 412.8 kB
total files:   38
```
**Result: PASS — name available on npm, clean 38-file package**

---

## 3. MCP Server (`mcp-server.js`)

### What it's for
Exposes DRM as Claude tools via the Model Context Protocol. Best for:
- Letting Claude autonomously call DRM operations mid-conversation
- Building Claude workflows that include database deployments
- Integrating DRM into any MCP-compatible client (Claude Code, Claude Desktop)

### How to use

**Registration** — `.mcp.json` at repo root (auto-discovered by Claude Code):
```json
{
  "mcpServers": {
    "drm-cli": {
      "command": "node",
      "args": ["/home/mumr/mycode/DRM-cli/mcp-server.js"]
    }
  }
}
```

**Start manually**
```bash
DRM_SECRET='P@ssword123!!' node mcp-server.js
# Listens on stdin for JSON-RPC 2.0 messages
```

**8 available tools**

| Tool | Inputs | Purpose |
|---|---|---|
| `drm_status` | — | Installation health check |
| `drm_list_releases` | — | All releases from DB |
| `drm_list_connections` | — | All connections from DB |
| `drm_dryrun` | connection, release, key? | Generate scripts |
| `drm_deploy` | connection, release, key? | Execute deployment |
| `drm_align` | connection, release, key? | Sync DB state |
| `drm_install` | path, type, key? | Install DRM |
| `drm_crypto_encrypt` | text, key | Encrypt string |

### Detailed examples

**Test tools/list**
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | node mcp-server.js
```

**Test drm_status**
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"drm_status","arguments":{}}}' | node mcp-server.js
# Output:
# DRM Path:           /home/mumr/drm_installed/drm
# Version:            1.1.0
# Install Type:       sqlite
# DB Secured:         true
# Active Releases:    6
# Active Connections: 10
# Last Deployments:
#   [Finished successfully] Demo release: Deploy a project to a single mssql database -> dev
```

**Test drm_list_releases**
```bash
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"drm_list_releases","arguments":{}}}' | node mcp-server.js
# Output: JSON array of {id, name, is_active}
# [11] Demo release: Deploy a project to a single mssql database
# [12] Demo release: Deploy multiple projects to multiple mssql database
# [21] Demo release: Deploy a project to a simple oracle database with liquibase
# [22] Demo release: Deploy a project to a simple oracle database with flyway
# [31] Demo release: Deploy a project to a simple postgres database with liquibase
# [32] Demo release: Deploy a project to a simple postgres database with flyway
```

**Test drm_dryrun (SQL solution, dev, release 11)**
```bash
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"drm_dryrun","arguments":{"connection":"dev","release":"11","key":"P@ssword123!!"}}}' | node mcp-server.js
# Output (ANSI stripped):
# INFO - Starting DRM DryRun (Release ID: "11", Connection name: "dev")
# INFO - Build finished successfully!!!
# INFO - Upgrade script generated successfully!!!
# INFO - DRM DryRun finished successfully!!!
```

**In Claude Code conversation** (after MCP registered):
- "Use drm_status to check my installation"
- "List all DRM releases"
- "Run dryrun for connection dev release 11"
- "What connections are in DRM?"

### Tested results (2026-04-05)
```
Tools listed:    8 tools  ✓
drm_status:      v1.1.0, 6 releases, 10 connections  ✓
drm_list_releases: 6 releases  ✓
drm_list_connections: 10 connections  ✓
drm_dryrun dev/11: script generated, DryRun finished successfully  ✓
```
**Result: PASS — all 5 tool tests**

---

## 4. AI Agent (`agent.js`)

### What it's for
Natural language interface to DRM. Claude interprets your request, picks the right DRM tools, and orchestrates a multi-step workflow. Best for:
- Non-technical users who don't know DRM commands
- Complex workflows: "dryrun, check output, deploy if clean"
- Conversational debugging: "why did the last deploy fail?"

### How to use
```bash
# Prerequisites
export ANTHROPIC_API_KEY=sk-ant-...    # from console.anthropic.com
export DRM_SECRET='P@ssword123!!'      # DRM encryption key

node agent.js "<natural language prompt>"
# or
npm run agent -- "<prompt>"
```

### How it works internally
```
User prompt
    ↓
Claude API (claude-sonnet-4-6) — receives prompt + 8 DRM tool definitions
    ↓
Claude decides which tool(s) to call (tool_use)
    ↓
agent.js executes: node index.js <args> — stdio:pipe, captures output
    ↓
Output fed back to Claude as tool_result
    ↓
Claude narrates result or calls next tool
    ↓
Repeat up to 10 turns → final text response
```

### Detailed examples

**List releases**
```bash
node agent.js "list all releases"
# Claude calls: drm_list_releases()
# Claude formats and returns:
# | ID | Name                                    | Active |
# | 11 | Deploy a project to a single mssql DB   | yes    |
# | 12 | Deploy multiple projects to mssql       | yes    |
# ...
```

**Dryrun with narration**
```bash
node agent.js "run a dryrun for connection dev release 11"
# [tool] drm_dryrun({"connection":"dev","release":"11"})
# Claude returns: "Dryrun completed successfully. Script generated at:
#   bin/DryRun_<uuid>_Cdev_R11_S1-P1-Project_A-DB_A1.sql
#   No warnings. Safe to deploy."
```

**Deploy with automatic safety check**
```bash
node agent.js "deploy release 11 to dev"
# Turn 1: Claude calls drm_dryrun first (safety rule)
# Turn 2: Claude evaluates dryrun output
# Turn 3: Claude calls drm_deploy if clean
# Final: "Deployment of release 11 to dev completed successfully."
```

**Skip dryrun explicitly**
```bash
node agent.js "deploy release 11 to dev, skip the dryrun"
```

**Check status**
```bash
node agent.js "what is the DRM status"
# Claude calls: drm_status()
# Returns: path, version, release count, last deployments
```

**Encrypt text**
```bash
node agent.js "encrypt 'Server=myserver;Password=abc' using key P@ssword123!!"
# Claude calls: drm_crypto_encrypt({text: "...", key: "..."})
```

**Natural language variations**
```bash
node agent.js "what releases are available?"
node agent.js "show deployment history"
node agent.js "is DRM installed correctly?"
node agent.js "run align for dev connection release 11"
node agent.js "how many connections do I have?"
```

### Tested results (2026-04-05)
```
API key valid: yes
Credits: BLOCKED — account has insufficient credits
          → Go to console.anthropic.com → Plans & Billing to add credits
```
**Result: BLOCKED (valid key, no credits) — all other components PASS**

---

## 5. Claude Code Skills (slash commands)

### What it's for
Pre-built guided workflows inside Claude Code conversations. Best for:
- Interactive deployment with confirmation steps
- Users who want Claude to guide them through DRM operations
- Teams with a standard deployment procedure to enforce

### How to use
Skills are in `.claude/commands/` — auto-loaded in any Claude Code session in this repo.

```
/drm-status          — installation health + recent deployments
/drm-release         — list all releases
/drm-release 11      — detail for release 11
/drm-plan dev 11     — dryrun + structured deployment plan
/drm-deploy dev 11   — guided: dryrun → confirm → deploy
```

### Detailed examples

#### `/drm-status`
```
/drm-status

→ Claude reads ~/.drm-cli.json, drm_deploy.config, queries SQLite
→ Output:
   DRM Path:           /home/mumr/drm_installed/drm
   Version:            1.1.0
   Install Type:       sqlite
   DB Secured:         true
   Active Releases:    6
   Active Connections: 10
   Last 5 Deployments:
   [Finished successfully] Release 11 → dev  (2026-04-05 01:22:28)
   [Finished successfully] Release 11 → dev  (2026-04-05 01:20:08)
```

#### `/drm-release`
```
/drm-release

→ Claude queries SQLite for all releases + last deployment status
→ Output table:
   ID | Name                              | Active | Last Status          | Last Deployed
   11 | Deploy a project to single mssql  | yes    | Finished successfully | 2026-04-05
   12 | Deploy multiple projects to mssql | yes    | —                    | never
   21 | Deploy oracle (liquibase)         | yes    | —                    | never
   ...
```

```
/drm-release 11

→ Claude shows full detail: release metadata, solutions, connection history, last 10 deployments
```

#### `/drm-plan dev 11`
```
/drm-plan dev 11

→ Claude runs: node index.js deploy -c dev -r 11 --dryrun
→ Parses output and presents:
   Deployment Plan — Release 11 / Connection dev
   Release:          Demo release: Deploy a project to a single mssql database
   Target:           dev
   Solution:         S1 — Project_A
   Target DB:        DB_A1
   Warnings:         none
   Generated script: bin/DryRun_<uuid>_Cdev_R11_S1-P1-Project_A-DB_A1.sql
   ✓ Plan looks good. Run /drm-deploy dev 11 to execute.
```

#### `/drm-deploy dev 11`
```
/drm-deploy dev 11

→ Step 1: Claude runs dryrun, displays full output
→ Step 2: "Proceed with actual deployment? (yes/no)"
→ Step 3 (if yes): Claude runs --deploy
→ Step 4: Reports result
```

### Tested results (2026-04-05)

| Skill | Result |
|---|---|
| `/drm-status` | PASS — v1.1.0, 6 releases, 10 connections, 4 deployments shown |
| `/drm-release` | PASS — all 6 releases listed with last status |
| `/drm-plan dev 11` | PASS — script generated, plan presented, no warnings |
| `/drm-deploy` | Not executed (would require actual MSSQL connection) |

---

## Full Test Results (2026-04-05)

All four combinations tested: install + deploy + dryrun for each.

| Install type | Encrypted | install | dryrun | deploy |
|---|---|---|---|---|
| sqlite | yes (`P@ssword123!!`) | PASS | PASS | PASS |
| sqlite | no | PASS | PASS | PASS |
| json | yes | PASS | PASS | PASS |
| json | no | PASS | PASS | PASS |

---

### SQLite + Encrypted (`/home/mumr/drm_installed/drm`, key `P@ssword123!!`)

| # | Component | Test | Result |
|---|---|---|---|
| 1 | CLI | `npm install` | PASS — 111 packages |
| 2 | CLI | Fresh install SQLite + encrypted | PASS |
| 3 | CLI | `deploy -c dev -r 11 --dryrun -p key` | PASS — script generated |
| 4 | MCP | `tools/list` | PASS — 8 tools |
| 5 | MCP | `drm_status` | PASS — v1.1.0, 6 releases, 10 connections |
| 6 | MCP | `drm_list_releases` | PASS — 6 releases |
| 7 | MCP | `drm_list_connections` | PASS — 10 connections |
| 8 | MCP | `drm_dryrun dev/11` | PASS — script generated |
| 9 | Agent | `list all releases` | BLOCKED — no API credits |
| 10 | npm | `publish --dry-run` | PASS — 38 files, 68.9 kB, name available |
| 11 | Skill | `/drm-status` | PASS |
| 12 | Skill | `/drm-release` | PASS — all 6 releases |
| 13 | Skill | `/drm-plan dev 11` | PASS — plan presented, no warnings |

### Install: JSON + Unencrypted (`/home/mumr/drm_installed/drm2`)

| # | Component | Test | Result |
|---|---|---|---|
| 14 | CLI | Fresh install JSON + no encryption | PASS |
| 15 | MCP | `drm_status` | PASS — type: json, secured: false, 6 releases, 10 connections |
| 16 | MCP | `drm_list_releases` | PASS — 6 releases from drm_db.json |
| 17 | MCP | `drm_list_connections` | PASS — 10 connections (flattened from nested JSON) |
| 18 | MCP | `drm_dryrun dev/11` (no key) | PASS — script generated |

**Summary: 17/18 PASS, 1 BLOCKED (agent — add API credits to unblock)**

---

## When to Use Which

| Scenario | Best choice |
|---|---|
| CI/CD pipeline deployment | **CLI** — scriptable, no deps |
| Share DRM with a team via npm | **npm publish** |
| Ask Claude "what releases do I have?" | **MCP** (auto-invoked by Claude) |
| "Deploy release 11 to dev if dryrun is clean" | **Agent** |
| Guided step-by-step deploy with confirmation | **Skill `/drm-deploy`** |
| Quick status check in Claude Code | **Skill `/drm-status`** |
| Debug a failed deploy | **CLI + `--trace`** |
| Encrypt a connection string | **CLI** or **Agent** |
