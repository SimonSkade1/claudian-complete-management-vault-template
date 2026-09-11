# Claudian complete-management vault template

A complete Obsidian vault template for managing your work — tasks, goals, notes, automation — with Claude Code available inside Obsidian via the [Claudian](https://github.com/YishenTu/claudian) plugin. The structure is plain Obsidian and works without Claude; the Claude layer adds delegation and scheduled maintenance on top. How the vault is organized and what the parts do: **[SYSTEM.md](SYSTEM.md)**.

This template is a snapshot (September 2026) of a live, evolving system — treat it as a starting point to reshape with your own Claude, not as an upstream that syncs.

## Setup

Phase 1 is yours — installs and logins Claude can't do. Phase 2 is one instruction.

### Phase 1

1. Get the files: **Use this template** on GitHub, then clone your copy (or clone/download directly). The folder itself becomes your vault. Any location works; `~/workspace` matches the shipped scheduling units as-is (anywhere else is a one-line path edit, covered in [SETUP.md](SETUP.md)).
2. Install [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and log in — Claudian requires a working local Claude Code installation. The scheduled automation assumes a subscription (Pro/Max) login: its usage gates read the plan-usage API.
3. Open the folder as a vault in Obsidian — a current version; Bases needs Obsidian ≥1.9, Claudian ≥1.13.
4. Install three community plugins (Settings → Community plugins): **Claudian**, **Templater**, **Hidden Folders Access**. Claude writes their configuration in phase 2 but cannot install them.
5. Trust the workspace: run `claude` once in a terminal at the vault root and accept the trust dialog, then exit. (Claude Code ignores the vault's permission allowlists until the folder is trusted.)

### Phase 2

6. Open a Claudian chat and say: **"Read SETUP.md and finish the setup."** Claude then works through [SETUP.md](SETUP.md) itself: git init + initial commit, plugin configuration, scheduling the automation, and personalizing `CLAUDE.md`.
