#!/bin/bash
# Push public code to GitHub, stripping private dev files.
# Azure DevOps keeps everything. GitHub gets only public files.
#
# Usage: ./push-github.sh [branch]
#   branch defaults to main

set -e

BRANCH=${1:-main}

if ! git remote get-url github &>/dev/null; then
  echo "ERROR: 'github' remote not configured."
  echo "Run: git remote add github https://github.com/dband-drm/drm-cli.git"
  exit 1
fi

git diff --quiet && git diff --cached --quiet || { echo "ERROR: uncommitted changes — commit or stash before pushing to GitHub"; exit 1; }

ORIG_BRANCH=$(git rev-parse --abbrev-ref HEAD)
TEMP_BRANCH="github-export-$(date +%s)"

trap 'git checkout "$ORIG_BRANCH" 2>/dev/null; git branch -D "$TEMP_BRANCH" 2>/dev/null' EXIT

PRIVATE=(
  "CLAUDE.md"
  "ai/implementAI.md"
  "ai/npm"
  "push-github.sh"
)

echo "Creating temporary export branch: $TEMP_BRANCH"
git checkout -b "$TEMP_BRANCH"

echo "Removing private files..."
for f in "${PRIVATE[@]}"; do
  git rm --cached --ignore-unmatch -r "$f" -q
done

git commit -m "chore: strip private files for GitHub" --allow-empty

echo "Pushing to GitHub..."
git push github "$TEMP_BRANCH:$BRANCH" --force-with-lease

echo "Done — GitHub $BRANCH is up to date (private files excluded)."
