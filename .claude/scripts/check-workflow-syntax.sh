#!/usr/bin/env bash
# Syntax-check a Workflow script. Workflow scripts run inside an async wrapper
# (top-level `return` is legal there but not in plain ESM), so we strip the
# `export const meta` prefix, wrap the body in an async function, and let node
# parse it. Checks syntax only - runtime globals (agent, parallel, ...) are fine.
set -euo pipefail
f="${1:?usage: check-workflow-syntax.sh <script.mjs>}"
tmp="$(mktemp --suffix=.mjs)"
trap 'rm -f "$tmp"' EXIT
{
  echo 'async function __workflow_check__() {'
  sed 's/^export const meta/const meta/' "$f"
  echo '}'
} > "$tmp"
node --check "$tmp" && echo "OK: $f parses"
