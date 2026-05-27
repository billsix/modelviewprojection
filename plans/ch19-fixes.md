# Plan: ch19 (fixed-function GL) fixes

**Status:** PARTIAL — the stray "with-statement" comment in demo19.py (:264-266) rewritten to describe the real `glPushMatrix`/`glPopMatrix`, fixed & staged 2026-05-27. Still open: `glPushStack/PopStack`→`glPush/PopMatrix` (:59,:60 — part of the GL-names batch #2) and the `.. TODO - mention 2 stacks` comment (:201, RST comment / not rendered — **needs Bill's call**: write or delete). **Type:** book prose + demo comment.
**Source:** ch19–21 drift audit.

## Findings + changes
1. **`ch19.rst:59` and `:60` — wrong GL function names.** Prose says
   "**glPushStack**" / "**glPopStack**"; the real fixed-function calls (and what
   demo19.py uses) are **`glPushMatrix`** / **`glPopMatrix`**. Fix both.
2. **`demo19.py:264-266` (shown via literalinclude) — copy-pasted comment that
   describes code that isn't there.** The comment talks about "the **with**
   statement … automatically popped off of the stack," but demo19 is
   fixed-function and uses raw `glPushMatrix`/`glPopMatrix`, **no `with`**. The
   comment was lifted from a `pyMatrixStack`/`push_matrix` demo (demo21-era).
   Rewrite the comment to describe the actual push/pop, or remove it. (Edit is in
   the .py source, since the comment is `literalinclude`d into the chapter.)
3. **`ch19.rst:201` — visible TODO marker.** `.. TODO - mention 2 stacks`
   (modelview + projection). Either write the two-stacks note or remove the
   marker. (TODO.org ch19 also wants inlined-code comments moved into rst prose —
   larger, track separately.)

## Verification
`grep -n "glPushStack\|glPopStack\|TODO" book/docs/ch19.rst` → empty after; reread
the demo19 comment block. Prose/comment only — but note the demo19 comment edit
changes what ch19 displays, so Bill confirms via `make html`.
</content>
