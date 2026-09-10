---
name: webresearch-format
description: The vault's citation format for web-research outputs. Apply whenever writing up web-research results — bibliographies, resource lists, "sources" sections, or knowledge notes citing or summarizing specific external material (in chat or in the vault), including when research is delegated to subagents/workflows. Not needed for answers that cite no sources.
---

# Web-research citation format

## Format

Every cited resource — in bibliographies and in inline mentions:

**[Title](URL)** (type; date; ⭐stars if repo) — 1–2 sentence takeaway.

1. Embed the link in the title. Never a bare URL after the title, never an unlinked title.
2. Publication date immediately after the title: `YYYY-MM-DD` if the page shows it, `YYYY-MM` otherwise; for dateless living docs write "living doc" or "date unverified". For repos, creation date (`created YYYY-MM-DD`) usually serves as the date.
3. GitHub repos additionally get stars right after the date, rounded to ~3 significant figures (⭐25.1k).
4. A type label (paper, docs, repo, blog post…) when not obvious from context.

Examples of good citations

1. **[Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)** (Anthropic engineering, 2025-11-26) — compaction doesn't suffice; rebuild context each session from on-disk artifacts.
2. **[beads](https://github.com/gastownhall/beads)** (created 2025-10-12; ⭐25.1k) — git-adjacent issue graph as agent task queue.

(Resources I asked specifically about should likely have more detailed summaries, but the title and metadata should be printed the same.)

## Notes

1. Dates come from the page itself (or arXiv/GitHub metadata), not from memory or training data. Feel free to curl from github API.

## Delegation

6. If you use subagents for webresearch, tell them to invoke this skill.
