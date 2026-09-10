#!/usr/bin/env bash
# update-external-ignores.sh — Regenerate the managed block in .gitignore that
# ignores every external-projects subfolder containing its own git repo
# (avoids gitlink noise in the vault repo; their history lives in their own git).
#
# Referenced by the comment above the block in .gitignore. Run manually after
# cloning a new repo into external-projects/, or let the daily-review wrapper
# run it before each snapshot.

set -euo pipefail
cd "$(dirname "$0")/.."

GITIGNORE=".gitignore"
START="# >>> external-projects (auto-generated)"
END="# <<< external-projects"

if ! grep -qxF "$START" "$GITIGNORE" || ! grep -qxF "$END" "$GITIGNORE"; then
  echo "ERROR: managed block markers not found in $GITIGNORE" >&2
  exit 1
fi

# Scan up to depth 4 — repos can sit below a wrapper folder
# (e.g. external-projects/some-project/code/.git).
entries=""
while IFS= read -r h; do
  entries+="/${h}/"$'\n'
done < <(find external-projects -mindepth 2 -maxdepth 4 -name .git -printf '%h\n' | sort)

awk -v start="$START" -v end="$END" -v entries="$entries" '
  $0 == start { print; printf "%s", entries; skip=1; next }
  $0 == end   { skip=0 }
  !skip       { print }
' "$GITIGNORE" > "$GITIGNORE.tmp" && mv "$GITIGNORE.tmp" "$GITIGNORE"
