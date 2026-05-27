# Plan: fix "method" vs "function" wording (cross-cutting)

**Status:** complete
**Completed:** 2026-05-27 — `rotate_around` "method"→"function" (ch08:65,128; ch09:80); `modelspace_to_ndc`→`modelspace_to_ndc_fn` (ch16:184,234,486); `camera_space_to_ndc_space_fn`→`cs_to_ndc_space_fn` (ch16:231, ch17:310). Verified the names against the code (`cs_to_ndc_space_fn` is the mathutils function the ch17 `literalinclude` pulls; `modelspace_to_ndc_fn` is the FunctionStack method the demos call). Left "method chaining" (ch09:73, ch16:232) alone — legitimate term.
**Type:** book prose (terminology).
**Found during:** ch08/09, ch10, ch16 audits. A recurring stale framing.

## Context
The transforms (`translate`, `rotate`, `rotate_around`, `scale_non_uniform_2d`,
`uniform_scale`, …) are **module-level functions** returning `InvertibleFunction`s
(`mathutils.py`). Several chapters call them "methods" — leftover from an earlier
API where they may have hung off `Vector`. (ch05's version of this is already in
`tasks/archive/ch05-translate-section-fixes.md`; this plan covers ch08–16.)

## Edits (verify exact lines; they may shift)
- `ch08.rst:65` — "making a **method** to rotate" → "function".
- `ch08.rst:128` — "add a rotate around **method**" → "function".
- `ch09.rst:80` — 'we fixed it by writing a "rotate_around" **method**' → "function".
- `ch16.rst:184` — 'through the "modelspace_to_ndc" **method**' — two problems:
  it's a **method on `FunctionStack`** named **`modelspace_to_ndc_fn`** (note the
  `_fn` suffix), not `modelspace_to_ndc`. Fix the name and keep "method" (this one
  *is* a method). 
- `ch16.rst:231` and `ch17.rst:310` — prose names
  `camera_space_to_ndc_space_fn`, but the mathutils function is
  **`cs_to_ndc_space_fn`** (`mathutils.py:1003`). **Verify against the demo
  first** — the chapter may define a local wrapper with the longer name; if so,
  this is fine and only the cross-reference target matters.

## Verification
- `grep -nE "method" book/docs/ch08.rst book/docs/ch09.rst` to confirm the hits.
- For the name refs: `grep -rn "camera_space_to_ndc_space_fn\|modelspace_to_ndc\b\|cs_to_ndc_space_fn" src/ book/docs/` to confirm which name the code actually uses before editing.
- Prose-only → no test/lint impact; Bill renders via `make html`.
</content>
