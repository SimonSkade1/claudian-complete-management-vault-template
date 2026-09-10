---
name: document-chat
description: Log the conversation into a note ("DC") instead of the chat, mainly for TTS. Trigger only on explicit invocation or when the user writes "DC on" / "DC 1".
---

# document-chat

The user reads **only the DC note, not the chat** (they listen via TTS). So: full answers go into the DC; the chat reply is a stub (a few words is fine). Anything they must see — including questions you need to ask them — goes into the DC.

## Target (first arg)

1. **I** (internal): log into the attached note (`<current_note>`).
2. **E** (external): create `DC - <sensible title>.md` in the attached note's folder, append a `[[wikilink]]` to it at the end of the attached note, log there.
3. **make-DC**: rename the attached note so its name starts with `DC - ` (then update wikilinks pointing to the old name — grep for it), and log into it like I.
4. Fallbacks: no attached note, or it sits in the vault root → create the DC note in `tasks-and-notes/` instead. No arg at all → I if a note is attached, else E.
5. Any DC file in `tasks-and-notes/` (whether created via E or converted via make-DC) gets frontmatter `status: note` — keeps it out of the base's Do view.

## Format

Starting a log in a file: leave **5 blank lines** after the existing content (or at the top of a new file, below frontmatter — even if the file is empty), then the heading `# document chat <n>`, where n = count of existing "document chat" headings in that file + 1. The blank space is room for the user to write above the log later.

Then append exchanges, separated by one blank line:

```markdown
## User

{verbatim message; include editor/browser selections as a blockquote}

## Claude

{your full answer}
```

Append-only: never reorder existing content or touch existing frontmatter.

## Mid-chat start

1. `whole-chat`: first transcribe the conversation so far, then continue live.
2. `future-only`: log from now on; put *(log starts mid-conversation)* right under the heading.

## Toggles

1. Arg `1`: log only this prompt + answer, then switch off.
2. "DC off" → stop logging. "DC on" → resume into the same target (or start fresh if none exists yet this chat). "DC 1" while off → log just that one exchange, stay off.

## Behavior while on

Work exactly like a normal chat — create and edit other notes, run tools, everything as usual. The DC is the chat *log*, not the workspace: for work done elsewhere, the Claude entry just notes it briefly (e.g. "wrote the comparison to [[X]]"). Since entries get read aloud, prefer flowing prose over tables/dense markdown in DC answers when the content allows. Don't announce that you logged something — just do it.
