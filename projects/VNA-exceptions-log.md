---
status:
parent:
---

Append-only log of VNA exceptions (see [[-VNA task-file structure]] → Exceptions). The controller appends one entry per exception at the bottom. Entries should capture decent detail — enough that a later review understands what happened without re-reading all involved files.

Entry format (one `##` heading per exception):

```
## YYYY-MM-DD · [[,raising task]]
1. Parent: [[,parent task]]
2. Attempted: what was tried / how far the agent got
3. Blocked because: why proceeding seemed like wasted effort; what decision/information is needed
4. Resolution: what the re-planning task decided — resumed / cancelled / replaced (+link) / escalated further (filled in when resolved)
```

(no entries yet)
