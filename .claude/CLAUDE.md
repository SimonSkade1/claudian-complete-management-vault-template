## User

(This section is about you, the vault owner — replace it. A few lines calibrate Claude's answers: name, what you're working toward, background/expertise per field so it can skip basics. You'll probably add more notes about yourself here over time; longer-lived profile/setup facts go into the `about-me` skill instead.)

## Communication preferences

(Defaults this system was built around — edit to taste.)

1. Write concisely.
2. Praise is useless, criticism is useful.
3. If you know numbers about sth state them instead of describing vaguely. (E.g. "has 50k+ stars on github" is better than "is popular".)
4. Focus on the asked question. Don't write "relevance to the user's work" sections - just stick with the object-level topic of the conversation; the user is tracking why they asked.
5. Always use numbered lists instead of bullet points. If you write multiple lists in a single response, continue the numbering of the new list after where you left off in the previous list. Restart from 1 after each prompt.
6. Answer simple/straightforward questions quickly. (Ideally sense whether it's the kind of question where the user stays in the chat and waits or the kind where you do the task and they do sth else in the meantime.)
7. On hard/large tasks, roughly minimize the number of times the user needs to send a prompt to give you instructions or feedback. (E.g. batch questions.) (In contrast, having the user ask multiple questions is fine - rather multiple clearly targeted concise bits than a wall of text.)
8. The user sometimes queues or sends new prompts without having read your last answer, so don't be surprised if you e.g. already gave the relevant information; the user reads the chat chronologically so you don't necessarily need to re-explain in detail.

## Thinking advice

9. Except for small tasks, try to understand the goal.
10. Mission first. Optimize for finding the best solution in reality, not for doing what the user expects. Feel free to take a better approach (and then tell the user) or suggest alternative approaches, especially if you have enough context about what the user wants.

## Microskills

11. "C" (for "concise"): Answer especially concisely.
	1. If the user types "C on" continue doing so until they type "C off".
12. "F" (for "fast"): Answer roughly instantly.
	1. Same on/off rule as for concise.
13. "forkmode": Launch a fork-type subagent to do the given task.
14. "forkmode-plan": Launch a forked planning subagent that outputs 1) a plan how to do the task and how to split it (usually serially) across subagents, and 2) for each subagent which should be launched directly (which may often be just one) the input prompt it should take. The main agent can then just create the forked subagent(s) and tell them which task without needing to copy the input prompt(s) (because they already have that from the fork).

## Rules

1. **Always do relatively long/context-intensive tasks in forkmode.**
	1. (The goal is to not trash your context with information that isn't relevant for future tasks (or that could've been strongly compressed). Take this into account when deciding whether to use forkmode.)
	2. "nofork" disables this rule for one prompt, and "forkmode off" for the rest of the session.
	3. This rule should be ignored when loading other subagent orchestration skills. The orchestrator here should always be the main session agent itself and the subagents then should be non-forked by default.
	4. For follow-ups, usually don't use sendMessage. (It may be ok in a few cases but it's expensive caching-wise). Do yourself or dispatch a new fork.
	5. For tasks where the user iterates with you significantly (e.g. fixing bugs or improving a document), lean a bit more towards doing tasks yourself or at least have decent context about the project.
2. Subagents should never spawn further subagents themselves unless nesting is explicitly asked for.
3. Don't use deepresearch unless asked for it.
4. For coding repos in external-projects, `git pull` at the start of a session, and make sure you always commit and push changes.

## Vault

Folder structure:

1. archive — not for projects or tasks; frozen/reference-only material.
2. auto-review — daily/weekly/monthly/... summaries of work that happened in this vault. (The git repo in the vault is just for that, never commit here for anything else.)
3. external-projects — code projects and other repos; each keeps its own git history and is ignored by the vault repo (see `external-projects/INDEX_external-projects.md`).
4. non-markdown — non-markdown files (scripts, automation config, media) that don't clearly fit into a particular projects folder.
5. optional-extensions — opt-in add-ons, one subfolder each (setup doc + assets); install one by pointing Claude at its SETUP.md.
6. posts — drafts, published posts, and dropped posts.
7. projects — goal and knowledge notes (plus misc "other" files). The filename marker sets the type: `,` = goal (e.g. `,create X.md`; a question is just a goal aimed at an answer), `-` = knowledge/reference (e.g. `-atlas.md`), no marker = other/misc. Frontmatter: `parent` (wikilink to the single parent file if clear parent exist; always set for subgoals). For goal files there's also `status`: the most important options are empty (means the goal is open/TODO), `review` (needs review), `done`, and others will be self-explanatory or known from context.
8. tasks-and-notes — mostly one-off tasks and notes. `status` frontmatter (used to structure me.base): empty, `in-progress`, `inbox`, `review`, `note`, `note-archived`, `done`, `archived`.
9. templates

In the tasks-and-notes bases (me.base, claude.base): Empty `priority` (1–10) sorts as 5.
After you did a task or completed a goal, set status to `done` if you are confident your work doesn't need to be checked, else `review`.

INDEX_<folder_name>.md files provide more info on how files in a folder are structured.

## Other notes

If you see text in curly brackets "{}", those are usually notes from the user.

Never edit this CLAUDE.md file uninstructed, though you may suggest changes to the user.
