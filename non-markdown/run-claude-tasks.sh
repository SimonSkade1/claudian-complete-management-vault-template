#!/usr/bin/env bash
# Headless Claude task runner: processes tasks delegated via
# next_action_by (opus/fable/sonnet/haiku/claude) from the claude.base Do
# queue — one claude instance per task, serially, gated on plan usage.
# Docs: tasks-and-notes/claude-task-runner.md
set -uo pipefail

# systemd user services don't source ~/.profile; make claude findable.
export PATH="$HOME/.local/bin:$HOME/.local/share/claude/versions:/usr/local/bin:/usr/bin:/bin:$PATH"

VAULT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$VAULT"

CLAUDE_BIN="$(command -v claude || true)"
if [[ -z "$CLAUDE_BIN" ]]; then
  echo "ERROR: claude CLI not found on PATH. PATH=$PATH" >&2
  exit 127
fi

# --- Config (env-overridable) ------------------------------------------------
MAX_5H="${MAX_5H:-70}"                    # skip when 5h-window utilization ≥ this %
MAX_7D="${MAX_7D:-85}"                    # ... 7-day window
MAX_7D_MODEL="${MAX_7D_MODEL:-80}"        # ... model bucket (7d opus / 7d sonnet)
TASK_TIMEOUT="${TASK_TIMEOUT:-3600}"      # hard per-task wall clock (seconds)
MAX_TASKS_PER_RUN="${MAX_TASKS_PER_RUN:-0}"  # 0 = unlimited
LOG_DIR="${CLAUDE_TASKS_LOG_DIR:-$HOME/.local/state/claude-task-runner}"
# ------------------------------------------------------------------------------

mkdir -p "$LOG_DIR"
exec 9>"$LOG_DIR/.lock"
flock -n 9 || { echo "another run is in progress; exiting"; exit 0; }

HELPER=".claude/scripts/claude-task-helper.py"
queue() { python3 .claude/scripts/query-base.py claude.base Do --paths 2>/dev/null; }

mapfile -t QUEUE < <(queue)
if [[ ${#QUEUE[@]} -eq 0 ]]; then
  # Queue empty: exit silently, zero token cost (no claude launch, no log file).
  exit 0
fi

RUN_LOG="$LOG_DIR/run-$(date -u +%Y%m%dT%H%M%SZ).log"
exec > >(tee -a "$RUN_LOG") 2>&1
echo "$(date -u +%FT%TZ) queue: ${#QUEUE[@]} task(s)"

count=0
for path in "${QUEUE[@]}"; do
  [[ -f "$path" ]] || { echo "SKIP (gone): $path"; continue; }
  # Re-verify membership: an earlier task this run may have changed things.
  queue | grep -qxF "$path" || { echo "SKIP (no longer queued): $path"; continue; }

  model="$(python3 "$HELPER" get "$path" next_action_by)"
  case "$model" in
    opus|fable|sonnet|haiku) MODEL_ARGS=(--model "$model") ;;
    claude)                  MODEL_ARGS=() ;;
    *) echo "SKIP (unrecognized model '$model'): $path"; continue ;;
  esac
  EFFORT_ARGS=(--effort max)
  [[ "$model" == "haiku" ]] && EFFORT_ARGS=()   # haiku doesn't support effort

  if ! gate_out="$(python3 "$HELPER" gate "$model" \
      --max-5h "$MAX_5H" --max-7d "$MAX_7D" --max-7d-model "$MAX_7D_MODEL")"; then
    echo "STOP usage gate: $gate_out"
    break
  fi

  slug="$(basename "$path" .md | tr -cs 'A-Za-z0-9' '-' | cut -c1-60)"
  task_log="$LOG_DIR/task-$(date -u +%Y%m%dT%H%M%SZ)-${slug}.log"
  echo "$(date -u +%FT%TZ) [$model] $path"
  echo "  gate: $gate_out"

  timeout "$TASK_TIMEOUT" "$CLAUDE_BIN" -p \
    --dangerously-skip-permissions \
    --settings non-markdown/headless-task-settings.json \
    "${MODEL_ARGS[@]}" "${EFFORT_ARGS[@]}" \
    "Read .claude/references/process-tasks.md and follow it for exactly this task: $path" >"$task_log" 2>&1
  rc=$?
  echo "  exit=$rc log=$task_log"

  # Failure guard: if the task is still in the queue the run didn't complete
  # the protocol (crash/timeout/limit). Hand back to the user; no retry loops.
  if queue | grep -qxF "$path"; then
    echo "  still queued after run -> handing back for review"
    python3 "$HELPER" mark-failed "$path" "exit=$rc, log=$(basename "$task_log")"
  fi

  count=$((count + 1))
  if [[ "$MAX_TASKS_PER_RUN" -gt 0 && "$count" -ge "$MAX_TASKS_PER_RUN" ]]; then
    echo "STOP MAX_TASKS_PER_RUN=$MAX_TASKS_PER_RUN reached"
    break
  fi
done

echo "$(date -u +%FT%TZ) done ($count task(s) processed)"
