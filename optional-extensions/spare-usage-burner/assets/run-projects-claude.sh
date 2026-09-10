#!/usr/bin/env bash
# Spare-usage burner: launches a headless vna-controller session over
# projects-claude/ in the last ~18h before the weekly usage limit resets
# (Wed 08:00 Europe/Berlin), aiming to end the week near 99% weekly usage.
#
# Slots (Europe/Berlin): Tue 12:00 / Tue 18:00 / Wed 00:00 / Wed 06:00.
#   target = 99 − n·B_5H_PCT, n = launches still to come after this one (3/2/1/0).
#   B_5H_PCT = guessed weekly-% that one 5h-window-limited session burns
#   (hand-tuned guess, integer; no runtime estimation by design).
# Every session additionally stops at MAX_5H_PCT of the 5-hour window.
# Docs: tasks-and-notes/projects-claude routine.md
set -uo pipefail

# systemd user services don't source ~/.profile; make claude findable.
export PATH="$HOME/.local/bin:$HOME/.local/share/claude/versions:/usr/local/bin:/usr/bin:/bin:$PATH"
export LC_ALL=C   # dot-decimal parsing of usage percentages

# claude -p kills the session after 600s of idle-waiting on background tasks by
# default — fatal for vna-controller runs, which wait on subagent workflows
# (bit us 2026-09-01: session died at 13min). 0 = wait indefinitely;
# SESSION_TIMEOUT remains the runaway backstop.
export CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS="${CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS:-0}"

VAULT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$VAULT"

CLAUDE_BIN="$(command -v claude || true)"
if [[ -z "$CLAUDE_BIN" ]]; then
  echo "ERROR: claude CLI not found on PATH. PATH=$PATH" >&2
  exit 127
fi

# --- Config (env-overridable) -------------------------------------------------
B_5H_PCT="${B_5H_PCT:-12}"        # guessed weekly-% per 5h-capped session (integer)
MAX_5H_PCT="${MAX_5H_PCT:-99}"    # 5-hour-window ceiling, every slot
TARGET_PCT="${TARGET_PCT:-}"      # set to override the computed weekly target
SESSION_TIMEOUT="${SESSION_TIMEOUT:-64800}"  # 18h wall-clock backstop (runaway guard)
LOG_DIR="${PC_RUNNER_LOG_DIR:-$HOME/.local/state/projects-claude-runner}"
DRY_RUN="${DRY_RUN:-0}"           # 1 = print slot/target/prompt, launch nothing
# ------------------------------------------------------------------------------

mkdir -p "$LOG_DIR"
exec 9>"$LOG_DIR/.lock"
flock -n 9 || { echo "previous spare-usage session still running; skipping this slot"; exit 0; }

# --- Which slot is this? (Europe/Berlin; weekly reset Wed 08:00) --------------
dow="$(TZ=Europe/Berlin date +%u)"    # 1=Mon … 7=Sun
hour="$(TZ=Europe/Berlin date +%-H)"
n=""
if   [[ "$dow" -eq 2 && "$hour" -ge 12 && "$hour" -lt 18 ]]; then n=3
elif [[ "$dow" -eq 2 && "$hour" -ge 18 ]];                   then n=2
elif [[ "$dow" -eq 3 && "$hour" -lt 6 ]];                    then n=1
elif [[ "$dow" -eq 3 && "$hour" -ge 6 && "$hour" -lt 8 ]];   then n=0
fi
if [[ -z "$n" && -z "$TARGET_PCT" ]]; then
  # Keeps Persistent=true catch-up fires (after machine downtime) from burning to
  # 99% on a Thursday. Manual off-window runs: set TARGET_PCT explicitly.
  echo "outside launch windows (Berlin Tue 12:00–Wed 08:00) and no TARGET_PCT set; exiting"
  exit 0
fi
target="${TARGET_PCT:-$((99 - ${n:-0} * B_5H_PCT))}"

RUN_LOG="$LOG_DIR/run-$(date -u +%Y%m%dT%H%M%SZ).log"
exec > >(tee -a "$RUN_LOG") 2>&1
echo "$(date -u +%FT%TZ) slot n=${n:-manual} target=${target}% (B_5H_PCT=$B_5H_PCT, 5h cap ${MAX_5H_PCT}%)"

# --- Pre-check current usage (fail closed) ------------------------------------
if ! usage_out="$(bash .claude/scripts/check-claude-usage.sh 2>&1)"; then
  echo "usage check failed:"; printf '%s\n' "$usage_out"; exit 1
fi
w7="$(printf '%s\n' "$usage_out" | sed -n 's/^7-day window:[[:space:]]*\([0-9.]*\)%.*/\1/p' | head -1)"
h5="$(printf '%s\n' "$usage_out" | sed -n 's/^5-hour window:[[:space:]]*\([0-9.]*\)%.*/\1/p' | head -1)"
echo "current usage: 5h=${h5:-?}% 7d=${w7:-?}%"
if [[ -z "$w7" ]]; then
  echo "could not parse 7-day usage from check-claude-usage output; aborting"; exit 1
fi
w7_int="$(printf '%.0f' "$w7")"; h5_int="$(printf '%.0f' "${h5:-0}")"
if (( w7_int >= target )); then
  echo "7-day usage already ≥ target (${w7}% ≥ ${target}%); nothing to burn"; exit 0
fi
if (( h5_int >= MAX_5H_PCT )); then
  echo "5-hour window already ≥ ${MAX_5H_PCT}%; skipping this slot"; exit 0
fi

# --- Compose prompt -----------------------------------------------------------
# The static prompt (policy + task sentence) is an editable md template sent
# verbatim after a dynamic header — edit the template, not this script.
PROMPT_FILE="${PROMPT_FILE:-$VAULT/non-markdown/projects-claude-session-prompt.md}"
if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "ERROR: prompt template missing: $PROMPT_FILE"; exit 1
fi
PROMPT="[Scheduled spare-usage session, slot n=${n:-manual}] Usage target: work until ${target}% of the 7-day window, or until you reach ${MAX_5H_PCT}% of the 5h window limit.

$(cat "$PROMPT_FILE")"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "--- DRY RUN — would launch: fable, effort max, permission-mode auto, timeout ${SESSION_TIMEOUT}s ---"
  printf '%s\n' "$PROMPT"
  echo "--- claude: $("$CLAUDE_BIN" --version 2>&1) ---"
  exit 0
fi

session_log="$LOG_DIR/session-$(date -u +%Y%m%dT%H%M%SZ)-n${n:-manual}.log"
echo "launching claude (fable, effort max, permission-mode auto); session log: $session_log"
timeout "$SESSION_TIMEOUT" "$CLAUDE_BIN" -p \
  --permission-mode auto \
  --settings non-markdown/headless-task-settings.json \
  --model fable --effort max \
  "$PROMPT" >"$session_log" 2>&1
rc=$?
echo "$(date -u +%FT%TZ) session exit=$rc"
echo "usage after:"
bash .claude/scripts/check-claude-usage.sh 2>/dev/null | grep -E '^(5-hour|7-day) window:' || true
exit 0
