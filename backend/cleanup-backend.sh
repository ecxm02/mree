#!/usr/bin/env bash
set -euo pipefail

# Clean up Windows-only scripts and redundant files in backend
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

TO_DELETE=(
  "reindex-pinyin.ps1"
  "deploy-to-pi.ps1"
  "update-remote.ps1"
  "app/database_old.py"
  "app/database_new.py"
)

for f in "${TO_DELETE[@]}"; do
  if [ -e "$f" ]; then
    echo "Deleting: $f"
    git rm -f "$f" 2>/dev/null || rm -f "$f"
  fi
done

echo "✅ Backend cleanup complete"
