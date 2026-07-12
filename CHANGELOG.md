# Changelog

All notable changes to `drm-cli` are documented here.

---

## [1.2.1] — 2026-07-13

### Changed
- Expanded npm keywords for better discoverability
- Added CHANGELOG

---

## [1.2.0] — 2026-04-25

### Added
- **AI integration** — MCP server (`drm-cli mcp`) and natural-language agent (`drm-cli agent`) for AI-driven release management
- Multi-database parallel deployment support
- AES encryption for connection credentials (`drm-cli crypto`)
- CI/CD pipeline integration (GitHub Actions, Azure DevOps)

### Changed
- npm package renamed to `@d-band-drm/drm-cli` (scoped org package)
- Improved dry-run output formatting

### Supported databases
MSSQL · PostgreSQL · Oracle

---

## [1.1.0] — 2026-01-01

### Added
- PostgreSQL support
- Oracle support
- `--align` flag: align target DB to a specific release state without full redeploy
- SQLite and JSON backend options for the DRM internal database

### Changed
- Expanded `drm-cli install` options (`-d`, `-p`, `--trace` flags)
- Improved error reporting for failed deployments

---

## [1.0.0] — 2025-01-01

### Initial release
- Core database release management CLI (`drm-cli deploy`)
- MSSQL support
- `--dryrun` mode: generate deployment scripts without executing
- `--deploy` mode: generate and execute scripts
- AES-encrypted credential storage
- `drm-cli install` / `drm-cli uninstall` lifecycle management
