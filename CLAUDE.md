# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

DRM-cli is a **Data Release Management** CLI tool (developed by d-band) for managing and deploying database releases across multiple platforms (MSSQL, PostgreSQL, Oracle). It supports both SQLite and JSON as the internal DRM database backend.

It also ships an **MCP server**, **AI agent**, and **Claude Code skills** for AI-assisted deployments.

## Repository Structure

```
DRM-cli/
├── index.js              # Node.js CLI wrapper — exposes drm-cli binary
├── setup-env.js          # npm setup script — checks Python, delegates to install.py
├── install.py            # Installer entrypoint
├── uninstall.py          # Uninstaller
├── install.config        # Version and config defaults
├── .mcp.json             # MCP auto-discovery for Claude Code
├── drm/                  # Template copied to install target
│   ├── drm_deploy.py     # Deploy entrypoint (run from installed path)
│   └── drm_crypto.py     # Crypto entrypoint (run from installed path)
├── modules/              # Python modules copied to install target
├── upgrade/              # Version migration configs
├── init_drm_db/          # DB schema + seed data source of truth
├── .claude/commands/     # Claude Code slash commands (skills)
│   ├── drm-deploy.md
│   ├── drm-status.md
│   ├── drm-plan.md
│   └── drm-release.md
└── ai/                   # AI layer — MCP server, agent, shared helpers
    ├── lib/
    │   └── drm-helpers.js    # Shared core: loadDrmPath, executeTool, TOOL_SCHEMAS
    ├── mcp/
    │   └── mcp-server.js     # MCP server — 8 DRM tools via StdioServerTransport
    ├── agent/
    │   └── agent.js          # AI agent — natural language → DRM operations
    ├── npm/
    │   └── npm-publish.md    # npm publish guide
    └── implementAI.md        # Full AI integration guide
```

## Two-Tier Architecture

### 1. Installer (repo root)
Scripts that install/upgrade/uninstall DRM onto a target machine:
- `install.py` — interactive installer; copies `drm/` content and `modules/` to a target path, creates the DRM DB and `drm_deploy.config`
- `uninstall.py` — removes the installed DRM directory
- `install.config` — version and configuration defaults used during installation
- `upgrade/` — version migration configs (`main.config` lists versions; `1.2.0.config` etc. define per-version changes)

### 2. Deployed DRM instance (installed at target path)
After installation, the deployed instance contains:
- `drm/drm_deploy.py` — main deploy entrypoint (run from installed path, not this repo)
- `drm/drm_crypto.py` — encryption/password management
- `modules/` — copied from this repo's `modules/` during install

The `drm/` folder in this repo is the **template** that gets copied to the install target.

## Running the CLIs

**Install DRM** (from repo root):
```bash
# Interactive (will prompt for key)
python3 install.py
# With args — SQLite + encrypted
python3 install.py -f /path/to/install -d sqlite -p mykey
# JSON + unencrypted (pipe empty key + confirm)
printf '\nY\n' | python3 install.py -f /path/to/install -d json
```

**Deploy a release** (from installed DRM path):
```bash
python3 drm_deploy.py -c <connection_name> -r <release_id> --dryrun
python3 drm_deploy.py -c <connection_name> -r <release_id> --deploy
python3 drm_deploy.py -c <connection_name> -r <release_id> --align
```

**Crypto operations** (from installed DRM path):
```bash
python3 drm_crypto.py --encrypt -t "text to encrypt"
python3 drm_crypto.py --changepassword -p oldkey -n newkey
```

**Uninstall**:
```bash
python3 uninstall.py -f /path/to/drm -p mykey --F
```

**Node.js wrapper** (wraps Python, exposes `drm-cli` binary after `npm install -g`):
```bash
npm install
node index.js install -f /path/to/install -d sqlite -p mykey
node index.js deploy  -c <connection_name> -r <release_id> --dryrun [-p mykey]
node index.js deploy  -c <connection_name> -r <release_id> --deploy [-p mykey]
node index.js deploy  -c <connection_name> -r <release_id> --align  [-p mykey]
node index.js crypto  --encrypt -t "text to encrypt" -p mykey
node index.js crypto  --changepassword -p oldkey -n newkey
node index.js uninstall [-p mykey]
```

`setup-env.js` is an npm `setup` script entry point — it checks Python availability and forwards args directly to `install.py`:
```bash
npm run setup -- -f /path/to/install -d sqlite -p mykey
```

The install path is saved to `~/.drm-cli.json` after `install`; subsequent commands (`deploy`, `crypto`, `uninstall`) load it automatically. Use `-f` to override.

Add `--trace` to any command for DEBUG-level logging.

## AI Layer

### MCP Server (`ai/mcp/mcp-server.js`)
Exposes 8 DRM tools to Claude via MCP stdio transport. Auto-discovered by Claude Code via `.mcp.json`.

```bash
DRM_SECRET=mykey node ai/mcp/mcp-server.js   # start manually
npm run mcp                                   # via npm
```

Tools: `drm_status`, `drm_list_releases`, `drm_list_connections`, `drm_dryrun`, `drm_deploy`, `drm_align`, `drm_install`, `drm_crypto_encrypt`

Test manually:
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | node ai/mcp/mcp-server.js
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"drm_status","arguments":{}}}' | node ai/mcp/mcp-server.js
```

### AI Agent (`ai/agent/agent.js`)
Natural language interface. Requires `ANTHROPIC_API_KEY`.

```bash
ANTHROPIC_API_KEY=sk-ant-... DRM_SECRET=mykey node ai/agent/agent.js "list all releases"
ANTHROPIC_API_KEY=sk-ant-... DRM_SECRET=mykey node ai/agent/agent.js "run dryrun for connection dev release 11"
npm run agent -- "deploy release 11 to dev"
```

Model: `claude-sonnet-4-6`. Max 10 turns. Always runs `drm_dryrun` before `drm_deploy` unless user skips.

### Claude Code Skills (`.claude/commands/`)
Available as slash commands in any Claude Code session in this repo:

| Skill | Usage | What it does |
|---|---|---|
| `/drm-status` | `/drm-status` | Installation health + last 5 deployments |
| `/drm-release` | `/drm-release [id]` | List releases or detail one |
| `/drm-plan` | `/drm-plan <conn> <rel>` | Dryrun + structured plan |
| `/drm-deploy` | `/drm-deploy <conn> <rel>` | Guided: dryrun → confirm → deploy |

### Shared Core (`ai/lib/drm-helpers.js`)
Both `ai/mcp/mcp-server.js` and `ai/agent/agent.js` import from here. Do not duplicate this logic.

Exports: `loadDrmPath()`, `executeTool(name, input, drmPath)`, `TOOL_SCHEMAS`

Internal: `runDrmCli`, `queryDb`, `buildStatus`, `loadJsonDb`, `loadDrmConfig`, `stripAnsi`, `isSqliteInstall`, `sqliteDbFile`

**Handles both install types:**
- SQLite: queries DB via inline Python (`DB_SCRIPT`, `STATUS_SCRIPT`)
- JSON: reads `drm_db.json` and flattens nested structure

**Encryption:** The `-p key` flag is forwarded to CLI calls. Set `DRM_SECRET` env var to avoid passing key explicitly.

## Key Modules

| Module | Purpose |
|---|---|
| `modules/installer_scratch.py` | Fresh install logic: copy files, create DB, write config |
| `modules/installer_upgrade.py` | Upgrade logic: diff and apply schema/data/config/folder changes |
| `modules/deploy.py` | Deploy/DryRun/Align release execution |
| `modules/builder.py` | Reads release definition from DRM DB, builds deploy plan into `bin/deploy.drmpac` |
| `modules/validator.py` | Validates release before deploy |
| `modules/drm_logger.py` | Logging setup with JSON/rotating file handlers; `log_decorator` for all methods; masks sensitive params |
| `modules/crypto.py` | AES encryption/decryption for DB and connection strings |
| `modules/auth.py` | Password policy validation and verification against `security_text` in config |
| `modules/init_db.py` | Creates the DRM SQLite database schema and seeds initial data |
| `modules/sqlite.py` | SQLite connection and query utilities |
| `modules/parser_json_sqlite.py` | Converts JSON schema/data to SQLite DDL/DML |
| `modules/parser_sqlite_json.py` | Reads SQLite schema/data back to JSON |
| `modules/parser_json_json.py` | JSON-to-JSON operations (compare tables, alter, insert, update, delete) |
| `modules/mssql.py`, `postgresql.py`, `oracle.py` | Target DB execution engines |
| `modules/liquibase.py`, `flyway.py`, `sqlpackage.py` | Third-party migration tool wrappers |

## Configuration File (`drm_deploy.config`)

Created during install; lives at the root of the installed DRM path. Key fields:
- `drm_version`: e.g. `"1.2.0"`
- `installation_info.installation_type`: `"sqlite"` or `"json"` — determines which parser is used everywhere
- `installation_info.db_secured`: boolean — whether the DB and connection strings are encrypted
- `installation_info.security_text`: encrypted sentinel string used to validate the encryption key at runtime
- `config.db_file_name` + `config.data_file_ext`: derive the JSON DB filename (e.g. `drm_db.json`)
- `locations`: optional paths for `sqlpackage`, `sqlcmd`, `flyway`, `psql` binaries

## Install Path Config (`~/.drm-cli.json`)

Written by `index.js install`. Read by `index.js` (deploy/crypto/uninstall) and by `ai/lib/drm-helpers.js` (MCP/agent).

```json
{ "drm_path": "/path/to/drm" }
```

## Logging

Logger modes (set via `DRM_LOGGER_MODE` env var): `0`=install, `1`=deploy, `2`=crypto, `3`=uninstall. All functions decorated with `@drm_logger.log_decorator(logger)` which auto-masks params named `password`, `encryption_key`, `connection_string`, `command`, etc.

WSL2 compatibility: `getpass.getuser()` and hostname lookups fall back to environment variables (`USER`, `USERNAME`, `HOSTNAME`, `COMPUTERNAME`) throughout the codebase.

## DB Schema Source of Truth

`init_drm_db/drm_db_schema.json` — canonical schema definition. `init_drm_db/drm_db_data.json` — seed data. These are copied to the installed DRM's `db/` folder and kept in sync during upgrades.

## Test Installs

All four combinations verified: install + dryrun + deploy.

| Path | Type | Encrypted | Key |
|---|---|---|---|
| `/path/to/drm` | sqlite | yes | `<your-key>` |
| `/path/to/drm2` | json | no | — |
| `/path/to/drm3` | sqlite | no | — |
| `/path/to/drm4` | json | yes | `<your-key>` |
