---
name: review-conversation
description: Review a conversation/session — "how could we have reached this outcome faster/better?" Surfaces one lesson for the user and flags general interaction patterns that wasted time, proposing skill edits. Triggered manually.
---
## Purpose

1. Help the user find lessons to think/work faster and better in the future.
2. Find sensible edits for claude skills. 

## Methodology

Look for where we wasted time or had significant updates. Then for each:
1. Clarify for our specific case: What was our mistake?
2. Identify the generalized lesson that would've avoided it. (Possibly sanity-check that it seems indeed like a generally good lesson rather than possibly having equally large downsides.)
3. Propose how to do better in the future. How the user could change or claude skills could improve.
	1. Not every claude imperfection needs to be captured in a skill. Bloating skills has significant disadvantages. Evaluate whether the lesson is likely important for a large fraction of skill invocations.

## Notes

If it's not that clear yet whether the output was actually good, have lower confidence in whether the lesson you draw from the path there seem good, and let that affect decisions whether to really update a skill.
