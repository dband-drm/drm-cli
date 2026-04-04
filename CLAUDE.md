# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

DRM-cli is a **Data Release Management** CLI tool (developed by d-band) for managing and deploying database releases across multiple platforms (MSSQL, PostgreSQL, Oracle). It supports both SQLite and JSON as the internal DRM database backend.

## Two-Tier Architecture

This repo contains two distinct operating contexts:

### 1. Installer (repo root)
Scripts that install/upgrade/uninstall DRM onto a target machine:
- `install.py` — interactive installer; copies `drm/` content and `modules/` to a target path, creates the DRM DB and `drm_deploy.config`
- `uninstall.py` — removes the installed DRM directory
- `install.config` — version and configuration defaults used during installation
- `upgrade/` — version migration configs (`main.config` lists versions; `1.1.0.config` etc. define per-version changes)

### 2. Deployed DRM instance (installed at target path)
After installation, the deployed instance contains:
- `drm/drm_deploy.py` — main deploy entrypoint (run from installed path, not this repo)
- `drm/drm_crypto.py` — encryption/password management
- `modules/` — copied from this repo's `modules/` during install

The `drm/` folder in this repo is the **template** that gets copied to the install target.

## Running the CLIs

**Install DRM** (from repo root, interactive):
```bash
python3 install.py
# With args: python3 install.py -f /path/to/install -d sqlite -p mykey
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
python3 uninstall.py -f /path/to/drm --F
```

**Node.js wrapper** (wraps Python, exposes `drm-cli` binary):
```bash
npm install
node index.js verify
```

Add `--trace` to any Python script for DEBUG-level logging.

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
- `installation_type`: `"sqlite"` or `"json"` — determines which parser is used everywhere
- `db_secured`: boolean — whether the DB and connection strings are encrypted
- `security_text`: encrypted sentinel string used to validate the encryption key at runtime
- `locations`: optional paths for `sqlpackage` and `sqlcmd` binaries

## Logging

Logger modes (set via `DRM_LOGGER_MODE` env var): `0`=install, `1`=deploy, `2`=crypto, `3`=uninstall. All functions decorated with `@drm_logger.log_decorator(logger)` which auto-masks params named `password`, `encryption_key`, `connection_string`, `command`, etc.

WSL2 compatibility: `getpass.getuser()` and hostname lookups fall back to environment variables (`USER`, `USERNAME`, `HOSTNAME`, `COMPUTERNAME`) throughout the codebase.

## DB Schema Source of Truth

`init_drm_db/drm_db_schema.json` — canonical schema definition. `init_drm_db/drm_db_data.json` — seed data. These are copied to the installed DRM's `db/` folder and kept in sync during upgrades.
