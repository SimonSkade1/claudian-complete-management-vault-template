<%*
/* Folder template for tasks-and-notes/. Fills only files created EMPTY (Obsidian UI); files created
   with any content (Claude, scripts, sync) are echoed back untouched. */
const existing = tp.file.content;
tR += existing.trim() !== "" ? existing : "---\nowner:\nnext_action_by:\nstatus:\npriority:\nproject:\nnot_before:\nsubscribers:\n---\n";
%>