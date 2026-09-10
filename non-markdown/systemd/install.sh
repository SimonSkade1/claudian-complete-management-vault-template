#!/usr/bin/env bash
# Link + enable the systemd user units directly from the vault (the vault
# copies stay the single source of truth; rerun after editing them, followed
# by `systemctl --user daemon-reload`). Linux-only — on macOS/Windows ask
# Claude to set up launchd / Task Scheduler equivalents for the wrapper scripts.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

# Nightly review pipeline (daily review + every-2nd-day vault cleanup)
systemctl --user link --force "$HERE/daily-review.service"
systemctl --user enable --now --force "$HERE/daily-review.timer"

# Optional: hourly Claude task runner — uncomment to enable
#systemctl --user link --force "$HERE/workspace-process-tasks.service"
#systemctl --user enable --now --force "$HERE/workspace-process-tasks.timer"

systemctl --user daemon-reload
systemctl --user list-timers --no-pager | head -6
