# Process Tasks

> Kept as a plain reference file rather than a skill, to keep the skill listing lean. Invoked headless by the task runner (`non-markdown/run-claude-tasks.sh`, hourly via `workspace-process-tasks.timer`), which points Claude at this file with a task path. Can also be followed manually when the user asks to process the Claude task queue.

A task is delegated to Claude when its frontmatter `next_action_by` is a model name (`opus`, `fable`, `sonnet`, `haiku`, or `claude`), status is empty/`active`/`inbox`, and `not_before` is absent or ≤ today. The queue is the **Do** view of [[claude.base]]; the runner and its docs are described in [[claude-task-runner]] (tasks-and-notes/).

## Single-task mode (headless)

When invoked with a vault-relative task path (the runner does this), process exactly that task and nothing else. You are then running headless. If the machine you are on lacks something the task needs (e.g. a mirrored server copy of the vault without `.git` or code repos), don't attempt a partial job — note in the task what machine/resource it needs and hand it back (step 4 below).

## Queue mode (interactive)

Query the queue and process every listed task in order (priority desc):

```bash
python3 .claude/scripts/query-base.py claude.base Do --paths
```

(With the Obsidian app running, `obsidian base:query path="claude.base" view="Do" format=paths` works too.)

## Protocol per task

1. **Read the full task note** plus wikilinked context. The body carries the instructions; often the filename is the whole instruction.
2. **Do the work.** Results go into the task note itself unless the note says otherwise; larger artifacts go where the note directs (or `projects/` knowledge notes if clearly warranted).
3. **Summarize at the top of the body** (above results/original text):

   ```markdown
   ## Done by claude (<model>, YYYY-MM-DD)

   What was done and what the user should check.
   ```

4. **Hand back via frontmatter:** set `next_action_by: me` and `status: review`. Use `status: done` only when the result is trivially verifiable and needed no judgment (vault CLAUDE.md rule).
5. **If blocked** (missing info, needs a decision, needs the laptop): write what's needed into the note and hand back exactly as in step 4. Never leave a task in the queue unchanged — the runner treats that as a failed run and force-hands it back.
