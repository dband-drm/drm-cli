# NPM Publish Guide — drm-cli

## Publish Flow

```
Azure DevOps (develop)
    ↓  git push github main
GitHub (source of truth)
    ↓  create GitHub Release  →  tag v1.x.x
GitHub Actions (.github/workflows/publish.yml)
    ↓  npm publish automatically
npmjs.com  →  drm-cli@1.x.x
```

---

## Part 1 — One-Time Setup (do once)

### 1.1 npm account
Create an account at https://www.npmjs.com if you don't have one.

### 1.2 Generate npm token
Via npmjs.com (recommended):
1. npmjs.com → avatar → **Access Tokens** → **Generate New Token** → **Granular Access Token**
2. Name: `drm-cli-publish`
3. Expiration: **90 days** (max allowed — set a calendar reminder to rotate every 90 days)
4. Packages: **All packages** (drm-cli doesn't exist on npm yet — restrict after first publish)
5. Permissions: **Read and write**
6. Copy the token — it won't be shown again

> After first publish: rotate to a new token restricted to `drm-cli` only.

### 1.3 Add token to GitHub repo
In the GitHub repo (`github.com/dband-drm/drm-cli`):
- Settings → Secrets and variables → Actions → New repository secret
- Name: `NPM_TOKEN`
- Value: the token from step 1.2

### 1.4 Confirm workflow file is present
```bash
cat .github/workflows/publish.yml   # must exist in the repo
```
The workflow triggers on GitHub Release published, verifies the tag matches `package.json` version, then runs `npm publish`.

### 1.5 Add GitHub as a second remote (Azure DevOps stays as origin)
```bash
git remote add github https://github.com/dband-drm/drm-cli.git
git remote -v
# origin   https://drmteam.visualstudio.com/DRM/_git/DRM-cli  (push/fetch)
# github   https://github.com/dband-drm/drm-cli.git           (push/fetch)
```

### 1.6 Authenticate with GitHub

**Option A — SSH key (recommended, no password prompts):**
```bash
# Generate key
ssh-keygen -t ed25519 -C "levin.alexey@gmail.com"
# Copy public key
cat ~/.ssh/id_ed25519.pub
```
Then: GitHub → Settings → SSH and GPG keys → New SSH key → paste public key.
```bash
# Switch remote to SSH
git remote set-url github git@github.com:dband-drm/drm-cli.git
# Test
ssh -T git@github.com
```

**Option B — HTTPS with personal access token:**

Classic token:
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Scope: ✅ `repo` only
3. Set on remote:
```bash
git remote set-url github https://<token>@github.com/dband-drm/drm-cli.git
```

Fine-grained token (more secure):
1. GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Repository access: `dband-drm/drm-cli`
3. Permissions: **Contents** → Read and write
4. Same `git remote set-url` command above

### 1.7 Push to GitHub for the first time
Private files (CLAUDE.md, implementAI.md, npm-publish.md, push-github.sh) are stripped automatically:
```bash
./push-github.sh main
```

---

## Part 2 — Release Checklist (before each publish)

### 2.1 Bump version
```bash
npm version patch   # 1.1.0 → 1.1.1  (bug fixes)
npm version minor   # 1.1.0 → 1.2.0  (new features)
npm version major   # 1.1.0 → 2.0.0  (breaking changes)
```
This updates `package.json` and creates a local git tag.

### 2.2 Verify the npm package
```bash
npm pack --dry-run
# Expected: 39 files, ~69 kB packed
```
Expected files: `index.js`, `setup-env.js`, `install.py`, `uninstall.py`, `install.config`,
`drm/`, `modules/*.py`, `upgrade/`, `init_drm_db/`, `.mcp.json`, `ai/lib/`, `ai/mcp/`, `ai/agent/`

Excluded: `__pycache__/`, `ai/npm/`, `ai/implementAI.md`, `log/`, `.claude/`, `node_modules/`

### 2.3 Check for private data
```bash
git grep -l "/home/" -- '*.md' '*.js' '*.py'   # should return nothing
git grep -l "password\|secret" -- '*.md'        # review any hits
```

### 2.4 Update CHANGELOG or release notes (optional)
Document what changed in this version.

---

## Part 3 — Push to Both Remotes

```bash
# Push to Azure DevOps (primary — includes all files)
git push origin <branch>

# Push to GitHub (strips private files automatically)
./push-github.sh

# Push version tag to GitHub (triggers nothing yet — the Release in Part 4 does)
git push github --tags
```

---

## Part 4 — Publish via GitHub Release

### Option A — GitHub UI
1. Go to `github.com/dband-drm/drm-cli` → **Releases** → **Draft a new release**
2. Tag: `v1.1.0` (must match `package.json` version exactly, with `v` prefix)
3. Title: `v1.1.0 — <short description>`
4. Add release notes
5. Click **Publish release**
6. Watch **Actions** tab → `Publish to npm` workflow runs automatically

### Option B — GitHub CLI
```bash
gh release create v1.1.0 \
  --title "v1.1.0 — AI layer + MCP server" \
  --notes "Added MCP server, AI agent, and Claude Code skills"
# Actions workflow fires automatically
```

### Verify the workflow succeeded
```bash
gh run list --workflow=publish.yml --limit 5
# or watch at: github.com/dband-drm/drm-cli/actions
```

---

## Part 5 — Verify Published Package

```bash
# Check npm registry
npm info drm-cli

# Install and test
npm install -g drm-cli
drm-cli --version
drm-cli --help
```

---

## Version Reference

| Command | Effect | When to use |
|---|---|---|
| `npm version patch` | 1.1.0 → 1.1.1 | Bug fixes, minor corrections |
| `npm version minor` | 1.1.0 → 1.2.0 | New features, backwards compatible |
| `npm version major` | 1.1.0 → 2.0.0 | Breaking changes |

Current: `1.1.0`

## npm Scripts Reference
```bash
npm run setup   # check Python + install DRM (runs setup-env.js)
npm run mcp     # start MCP server (node ai/mcp/mcp-server.js)
npm run agent   # start AI agent  (node ai/agent/agent.js)
```
