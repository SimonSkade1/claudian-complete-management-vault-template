<%*
/* STARTUP TEMPLATE — applies the folder templates to newly created EMPTY notes, and nothing else.

   Why this exists: Templater's own "Trigger Templater on new file creation" does two things — it fills
   empty new files with their folder template, AND it executes every Templater command found inside any
   newly created NON-empty note (files written by Claude or scripts, files arriving through sync): code
   execution from note content, and quoted template code gets mangled. No Templater setting switches that
   second branch off. So this vault keeps Templater's trigger OFF (this script turns it off if it finds
   it on) and does the empty-file part itself.

   Setup (per device): Templater settings → Startup templates → add this file. Nothing else.
   Config: FOLDER_TEMPLATES below is the ONLY folder → template mapping in use (deepest matching folder
   wins; "/" = whole vault). Templater's own "Folder templates" list is ignored — its settings UI is
   hidden anyway while the trigger is off.
   "Empty" = nothing but whitespace after the frontmatter (Templater's rule), so frontmatter-only notes
   from the Bases "New" button still get their template. Only the trusted template file is executed —
   the content of the new note never is.
   Fails closed: on any error, or if Templater's internals change, no template is applied and a Notice
   says so. Relies on Templater internals: templater.write_template_to_file, .files_with_pending_templates,
   plugin.save_settings, event_handler.update_trigger_file_on_creation (checked with Templater 2.20.5). */
const FOLDER_TEMPLATES = {
    "tasks-and-notes": "templates/task.md",
    "projects": "templates/project.md",
};

const { TFile, TFolder, Notice, normalizePath, getFrontMatterInfo } = tp.obsidian;
const NAME = "startup-folder-templates";
const warn = (msg) => { console.error(`[${NAME}] ${msg}`); new Notice(`${NAME}: ${msg}`, 15000); };
const plugin = app.plugins.plugins["templater-obsidian"];
const templater = plugin?.templater;

if (typeof templater?.write_template_to_file !== "function" || !(templater.files_with_pending_templates instanceof Set)) {
    warn("Templater internals changed — folder templates are NOT applied until this script is fixed.");
} else {
    // 1. Keep Templater's own creation trigger off: it executes commands inside non-empty new notes.
    if (plugin.settings.trigger_on_file_creation) {
        plugin.settings.trigger_on_file_creation = false;
        await plugin.save_settings();
        if (typeof plugin.event_handler?.update_trigger_file_on_creation === "function") plugin.event_handler.update_trigger_file_on_creation();
        else warn("could not unregister Templater's creation trigger — restart Obsidian.");
        new Notice(`${NAME}: turned Templater's "Trigger on new file creation" off (it runs code found inside new notes). Empty new notes still get their folder template.`, 15000);
    }

    // 2. Own handler: folder template for EMPTY new notes only.
    const templateFor = (folder) => {
        for (let f = folder; f instanceof TFolder; f = f.parent)
            if (FOLDER_TEMPLATES[f.path]) return FOLDER_TEMPLATES[f.path];
    };
    const onCreate = async (file) => {
        try {
            if (!(file instanceof TFile) || file.extension !== "md") return;
            if (plugin.settings.trigger_on_file_creation) return;   // re-enabled by hand: Templater fills empty files itself — don't apply twice
            const tf = normalizePath(plugin.settings.templates_folder || "/");
            if (tf !== "/" && (file.path + "/").startsWith(tf + "/")) return;
            const templatePath = templateFor(file.parent);
            if (!templatePath) return;
            await new Promise((resolve) => setTimeout(resolve, 300));    // Templater's grace period: lets create-then-write flows finish
            if (templater.files_with_pending_templates.has(file.path)) return;   // tp.file.create_new & co. fill the file themselves
            if (app.vault.getAbstractFileByPath(file.path) !== file) return;      // deleted meanwhile
            const content = await app.vault.read(file);
            if (content.slice(getFrontMatterInfo(content).contentStart).trim() !== "") return;   // NON-EMPTY: never touched, never executed
            const template = app.vault.getAbstractFileByPath(normalizePath(templatePath));
            if (!(template instanceof TFile)) return warn(`template "${templatePath}" not found (FOLDER_TEMPLATES).`);
            await templater.write_template_to_file(template, file);
        } catch (e) {
            warn(`failed for ${file?.path}: ${e?.message ?? e}`);
        }
    };
    app.workspace.onLayoutReady(() => {   // the vault's initial-load "create" events are over by then
        if (plugin.__folderTemplatesRef) app.vault.offref(plugin.__folderTemplatesRef);   // idempotent if this script runs twice
        plugin.__folderTemplatesRef = app.vault.on("create", onCreate);
        plugin.registerEvent(plugin.__folderTemplatesRef);   // removed automatically when Templater unloads
    });
}
%>
