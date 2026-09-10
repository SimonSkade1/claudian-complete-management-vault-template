Please start by running `bash .claude/scripts/check-claude-usage.sh`; re-run it roughly every 30–60 min and before/after large subagent batches (subagent usage counts toward the same windows). Your stop signals are the usage numbers in the header above, never wall-clock — running for hours is fine.

Model policy — classify each task before delegating: opus-should (modular, bounded, and simple enough that fable's marginal benefit is negligible) → always opus. fable-must (difficult novel thinking, strategy) → always fable. fable-should (everything in between) → fable by default; this category flips: once fable's per-model weekly window is at/above your 7-day target, fable-should tasks go to opus, and goals whose next task is fable-must are stopped. Keep working everything else — the fable mark is a flip trigger, not a stop.

Wind-down (when a stop signal nears, or only stopped work remains): stop spawning subagents, finish or hand off current work (handoff skill), set statuses.

please load the vna-controller skill and run the protocol with projects-claude-overview as your root
