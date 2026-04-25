# DRM-cli

**Data Release Management CLI** — a unified tool by d-band for managing and deploying database releases across MSSQL, PostgreSQL, and Oracle. Supports SQLite and JSON as the internal DRM database backend.

---

## Requirements

- Python >= 3.10
- Node.js >= 16 (for the `drm-cli` npm wrapper)

---

## Installation

### Option A — Node.js wrapper (recommended)

```bash
npm install
npm run setup -- -f /path/to/install -d sqlite -p mykey
```

Or install globally to get the `drm-cli` binary:

```bash
npm install -g .
drm-cli install -f /path/to/install -d sqlite -p mykey
```

### Option B — Python directly

```bash
python3 install.py
# with args:
python3 install.py -f /path/to/install -d sqlite -p mykey
```

**Install options:**

| Flag | Description |
|------|-------------|
| `-f` | Target install path |
| `-d` | DB backend: `sqlite` or `json` |
| `-p` | Encryption key (omit for unencrypted) |
| `--trace` | Enable DEBUG logging |

After install, the target path contains `drm_deploy.py`, `drm_crypto.py`, `modules/`, and `drm_deploy.config`.

---

## Usage

### Deploy a release

```bash
# Via Node wrapper (uses saved install path):
node index.js deploy -c <connection_name> -r <release_id> --dryrun
node index.js deploy -c <connection_name> -r <release_id> --deploy
node index.js deploy -c <connection_name> -r <release_id> --align

# Via Python (run from installed DRM path):
python3 drm_deploy.py -c <connection_name> -r <release_id> --dryrun
```

| Flag | Description |
|------|-------------|
| `-c` | Connection name (defined in DRM DB) |
| `-r` | Release ID |
| `--dryrun` | Generate scripts only, do not execute |
| `--deploy` | Generate and execute scripts |
| `--align` | Align target DB to release state |
| `-f` | Override saved DRM install path |
| `-p` | Encryption key |

### Crypto operations

```bash
node index.js crypto --encrypt -t "text to encrypt" -p mykey
node index.js crypto --changepassword -p oldkey -n newkey

# Via Python:
python3 drm_crypto.py --encrypt -t "text to encrypt"
python3 drm_crypto.py --changepassword -p oldkey -n newkey
```

### Uninstall

```bash
node index.js uninstall [-p mykey]
# or: python3 uninstall.py -f /path/to/drm -p mykey --F
```

Add `--trace` to any command for DEBUG-level logging.

---

## AI Layer

DRM-CLI ships three AI integration modes, all sharing `ai/lib/drm-helpers.js` as the core.

### MCP Server

Exposes 8 DRM tools to Claude Code via MCP auto-discovery (`.mcp.json`):

```bash
npm run mcp                  # start via npm
DRM_SECRET=mykey npm run mcp # with encryption key
```

Test:
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | node ai/mcp/mcp-server.js
```

### AI Agent

Natural language → DRM operations. Requires `ANTHROPIC_API_KEY`:

```bash
ANTHROPIC_API_KEY=sk-ant-... DRM_SECRET=mykey node ai/agent/agent.js "list all releases"
ANTHROPIC_API_KEY=sk-ant-... DRM_SECRET=mykey node ai/agent/agent.js "run dryrun for connection dev release 11"
npm run agent -- "deploy release 11 to dev"
```

### Claude Code Skills

Available as slash commands in any Claude Code session in this repo:

| Skill | What it does |
|---|---|
| `/drm-status` | Installation health + last 5 deployments |
| `/drm-release [id]` | List releases or detail one |
| `/drm-plan <conn> <rel>` | Dryrun + structured plan |
| `/drm-deploy <conn> <rel>` | Guided: dryrun → confirm → deploy |

---

## How the install path is persisted

Running `drm-cli install -f /path` saves the path to `~/.drm-cli.json`. Subsequent `deploy`, `crypto`, and `uninstall` commands load it automatically. Pass `-f` to any command to override.

---

## Project structure

```
DRM-cli/
├── install.py            # Interactive installer
├── uninstall.py          # Uninstaller
├── install.config        # Version + config defaults (current: 1.2.0)
├── index.js              # Node.js CLI wrapper (drm-cli binary)
├── setup-env.js          # npm setup script — checks Python, runs install.py
├── package.json
├── .mcp.json             # MCP auto-discovery for Claude Code
├── drm/                  # Template copied to install target
│   ├── drm_deploy.py     # Deploy entrypoint
│   └── drm_crypto.py     # Encryption management
├── modules/              # Copied to install target
│   ├── deploy.py         # Deploy/DryRun/Align execution
│   ├── builder.py        # Builds deploy plan → bin/deploy.drmpac
│   ├── validator.py      # Pre-deploy validation
│   ├── crypto.py         # AES encryption/decryption
│   ├── auth.py           # Password policy validation
│   ├── drm_logger.py     # Logging + sensitive-param masking
│   ├── mssql.py          # MSSQL execution engine
│   ├── postgresql.py     # PostgreSQL execution engine
│   ├── oracle.py         # Oracle execution engine
│   └── ...
├── init_drm_db/
│   ├── drm_db_schema.json  # Canonical DB schema
│   └── drm_db_data.json    # Seed data
├── upgrade/              # Version migration configs
│   ├── main.config       # Lists available upgrade versions
│   └── 1.2.0.config      # Per-version change definitions
└── ai/                   # AI layer
    ├── lib/drm-helpers.js    # Shared core (MCP + agent)
    ├── mcp/mcp-server.js     # MCP server — 8 tools
    ├── agent/agent.js        # Natural language agent
    └── npm/npm-publish.md    # npm publish guide
```

---

## Configuration (`drm_deploy.config`)

Generated at the install path during setup. Key fields:

| Field | Description |
|-------|-------------|
| `installation_type` | `"sqlite"` or `"json"` |
| `db_secured` | Whether DB and connection strings are encrypted |
| `security_text` | Encrypted sentinel for key validation at runtime |
| `locations` | Optional paths to `sqlpackage`/`sqlcmd` binaries |

---

## Upgrading

```bash
python3 install.py -f /path/to/existing/drm
```

The installer detects the installed version and applies incremental migrations defined in `upgrade/`.

---

## Contribute

Open issues and pull requests on the project repository. Follow existing module patterns — all functions should use the `@drm_logger.log_decorator(logger)` decorator and avoid hardcoding platform-specific paths.
