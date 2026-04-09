# NPM Publish Guide — drm-cli

## Status
- Package name `drm-cli` is **available** on npm (confirmed 2026-04-05)
- Current version: `1.0.0`
- Repo: https://github.com/dband-drm/drm-cli

## Pre-publish Checklist

### 0. Remove generated Python caches (do this before every publish)
```bash
find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null; true
```

### 1. Verify what will be published
```bash
npm publish --dry-run
# Expected: ~38 files, ~68.9 kB packed
```
Expected included files (from `package.json` `files` array):
- `index.js` — main CLI entry
- `setup-env.js` — npm setup script
- `install.py`, `uninstall.py` — Python installers
- `install.config` — version and config defaults
- `drm/` — deployed DRM template (drm_deploy.py, drm_crypto.py, modules/)
- `modules/` — all Python modules (deploy.py, builder.py, etc.)
- `upgrade/` — version migration configs
- `init_drm_db/` — schema and seed data
- `mcp-server.js` — MCP server
- `agent.js` — AI agent
- `.mcp.json` — MCP registration

Excluded by `.npmignore`:
- `venv/` — Python virtual environment
- `log/` — runtime logs
- `.claude/` — Claude Code skills (local dev only)
- `__pycache__/`, `*.pyc` — compiled Python
- `.env`, `*.log`
- `node_modules/`, `.git/`

### 2. Ensure README is complete
```bash
head -50 README.md   # verify install and usage instructions are clear
```

### 3. Login to npm
```bash
npm login
# Enter: username, password, email, OTP
```
To publish under the `dband` org scope instead:
```bash
# Change package.json "name" to "@dband/drm-cli"
npm login --scope=@dband
```

### 4. Publish
```bash
npm publish --access public
```
For scoped package:
```bash
npm publish --access public   # scoped packages require --access public
```

### 5. Verify
```bash
npm info drm-cli
npm install -g drm-cli
drm-cli --help
```

## Post-publish

### Tag the release
```bash
git tag v1.0.0
git push origin v1.0.0
```

### Update README badge
Add to README.md:
```markdown
[![npm version](https://badge.fury.io/js/drm-cli.svg)](https://badge.fury.io/js/drm-cli)
```

### Future versions
```bash
# Bump version
npm version patch   # 1.0.0 → 1.0.1
npm version minor   # 1.0.0 → 1.1.0
npm version major   # 1.0.0 → 2.0.0

# Then publish
npm publish --access public
git push --tags
```

## npm Scripts Reference
```bash
npm run setup   # runs setup-env.js (checks Python, installs DRM)
npm run agent   # node agent.js
npm run mcp     # node mcp-server.js
```
