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
node index.js uninstall
# or: python3 uninstall.py -f /path/to/drm --F
```

Add `--trace` to any command for DEBUG-level logging.

---

## How the install path is persisted

Running `drm-cli install -f /path` saves the path to `~/.drm-cli.json`. Subsequent `deploy`, `crypto`, and `uninstall` commands load it automatically. Pass `-f` to any command to override.

---

## Project structure

```
DRM-cli/
├── install.py            # Interactive installer
├── uninstall.py          # Uninstaller
├── install.config        # Version + config defaults (current: 1.1.0)
├── index.js              # Node.js CLI wrapper (drm-cli binary)
├── setup-env.js          # npm setup script — checks Python, runs install.py
├── package.json
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
│   ├── sqlite.py         # SQLite utilities
│   ├── mssql.py          # MSSQL execution engine
│   ├── postgresql.py     # PostgreSQL execution engine
│   ├── oracle.py         # Oracle execution engine
│   └── ...
├── init_drm_db/
│   ├── drm_db_schema.json  # Canonical DB schema
│   └── drm_db_data.json    # Seed data
└── upgrade/              # Version migration configs
    ├── main.config       # Lists available upgrade versions
    └── 1.1.0.config      # Per-version change definitions
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
