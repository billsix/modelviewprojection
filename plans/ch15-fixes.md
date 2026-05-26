# Plan: ch15 (depth buffer) fixes

**Status:** planned. **Type:** book prose. **Effort:** small.
**Source:** ch13–15 drift audit.

## Findings + changes (`book/docs/ch15.rst`)
1. **Lines ~128-133 — context drift.** This passage reads as if depth buffering
   has *not* been applied ("the square should not be visible… this is because…")
   — it appears copied from ch14:282-302, which describes the *problem*. ch15 is
   the chapter that *enables* depth buffering to *fix* that problem, so the prose
   should describe what depth buffering now resolves, not restate the bug as
   present. Rewrite to match ch15's "after" state. **Confirm intended narrative
   with Bill** (he knows the demo14→15 before/after framing).
2. **Capitalization.** Same passage starts sentences lowercase: "the square…",
   "this is because…" → capitalize.

## Verification
Prose only. Read ch14:282-302 and ch15:128-133 side by side to confirm the
ch15 copy is stale. Bill renders via `make html`.
</content>
