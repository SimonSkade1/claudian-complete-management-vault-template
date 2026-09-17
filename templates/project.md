<%*
/* Folder template for projects/ — see INDEX_projects. Two entry paths:
   1. Auto-trigger on file creation (RunMode.OverwriteFile=2): fills files created EMPTY (Obsidian UI
      click-create); files created WITH content (Claude/scripts/sync) are echoed back untouched so
      complete files are never clobbered — Claude writes complete files itself.
   2. Manual insertion (Insert Template modal = RunMode.AppendActiveFile=1, or any non-auto run mode):
      emits only the parts the active file is still MISSING, based on the CURRENT filename — so it also
      fixes notes where the auto-trigger fired while the note was still "Untitled" (before rename). Put
      the cursor at end-of-file and insert; frontmatter is skipped if already present, so it won't
      duplicate. On an empty file it writes the whole structure.
   Emitted frontmatter = status/parent (the only two properties in projects/); for goal AND knowledge
   files (^(\d[a-c]?)?[,-]) `parent:` is pre-filled with the previously open note if that is a goal note.
   Goal files additionally get the empty VNA sections (-VNA task-file structure). */
const AUTO_CREATE = tp.config.run_mode === 2; // RunMode.OverwriteFile = the on-creation folder trigger
const existing = tp.file.content;
if (AUTO_CREATE && existing.trim() !== "") {
    tR += existing;                                       // protect Claude/script/sync writes
} else {
    const GOAL = /^(\d[a-c]?)?,/;
    const KNOW = /^(\d[a-c]?)?-/;
    const isGoal = GOAL.test(tp.file.title);
    if (!/^---\r?\n/.test(existing)) {                     // add frontmatter only if none yet
        let parent = "";
        if (isGoal || KNOW.test(tp.file.title)) {
            const self = tp.file.path(true);
            const prev = app.workspace.getLastOpenFiles().find(p => p !== self && p.endsWith(".md"));
            const base = prev ? prev.split("/").pop().slice(0, -3) : "";
            if (GOAL.test(base)) parent = `"[[${base}]]"`;
        }
        tR += "---\nstatus:\nparent: " + parent + "\n---\n";
    }
    if (isGoal && !/#\s*Goal clarification/.test(existing)) // add VNA sections only if not already there
        tR += "\n# Goal clarification\n\n# Subtasks\n\n# Notes\n";
}
%>