# Task: book ↔ code drift in chapters 7–15

**Status:** audited 2026-05-27 (5 Explore agents + direct verification of all
code-level claims). This is the self-contained tracker — per-chapter fix detail
is folded in below (the old `tasks/ch15-fixes.md` satellite was archived
2026-06-14). Same method as `book-code-drift-ch1-6.md`: doc-region wiring is
intact across 7–15 (no broken labels), so drift is prose / captions /
hand-written code / a few real code bugs.

## Cross-cutting (span multiple chapters)
| Finding | Plan |
|---|---|
| ✅ `e_1`/`e_2`/`e_3` natural basis used in every demo, explained nowhere — DONE (introduced 2D in ch05, 3D in ch14) | [`archive/book-explain-natural-basis.md`](archive/2026/05/26/book-explain-natural-basis.md) |
| ✅ Module-level transforms called "methods" in prose (ch08:65,128; ch09:80) — DONE | [`archive/fix-method-vs-function-wording.md`](archive/2026/05/26/fix-method-vs-function-wording.md) |
| ✅ mathutils LaTeX-repr bugs + "Note invertible" typos (all scale inverses → `\frac`; lines 629/728) — DONE | [`archive/fix-mathutils-latex-and-error-strings.md`](archive/2026/05/26/fix-mathutils-latex-and-error-strings.md) |
| ✅ `is_clockwise` self-recursion (`mathutils.py:705`) — DONE | [`archive/fix-is-clockwise-recursion.md`](archive/2026/05/26/fix-is-clockwise-recursion.md) |
| ✅ demo code bugs: `demo14.py:42 zero = Vector3D.e_3()` — DONE | [`archive/fix-demo-code-bugs.md`](archive/2026/05/26/fix-demo-code-bugs.md) |
| ✅ Reused `doc-region` label "define vector class" pulls Vector1D not Vector3D (manifests in ch14; also ch05/06) — DONE | [`archive/ch14-fixes.md`](archive/2026/05/26/ch14-fixes.md) |

## Per-chapter
| Chapter | Findings (verified unless noted) | Plan |
|---|---|---|
| ch07 | ✅ `theta`→`\theta` LaTeX typo :203 — DONE (the `.. TODO` at :58-59 is a hidden RST comment, left per Bill) | [`archive/ch07-fixes.md`](archive/2026/05/26/ch07-fixes.md) |
| ch08/09 | only the "method"→"function" wording | (method-vs-function plan above) |
| ch10 | ✅ DONE — `camera.x/y`→`camera.position_ws` (:363,:381); the broken method-API blocks (~:149-216) rewritten to runnable `e_1`/`e_2` doctests; typos (:120,:131,:257) | [`archive/ch10-fixes.md`](archive/2026/05/26/ch10-fixes.md) |
| ch11/12 | no chapter-specific drift beyond the basis omission (above) | — |
| ch13 | ✅ figure `_static/demo11.png` shown for a Demo-13 chapter (:63) — DONE (per-chapter `demo13.dot`) | [`archive/ch13-fixes.md`](archive/2026/05/26/ch13-fixes.md) |
| ch14 | ✅ DONE — caption `+.py` (:133); doc-region relabel (split into vector1d/2d/3d; ch05→2D, ch14→3D, others reference); grammar/pronoun (:102,:227,:229,:322) | [`archive/ch14-fixes.md`](archive/2026/05/26/ch14-fixes.md) |
| ch15 | depth-buffer prose describes the "before" state in the "after" chapter (~:128-133); lowercase sentence starts | see **ch15 detail** below |

## ch15 detail (depth buffer) — folded from ch15-fixes.md
**Status:** planned. **Type:** book prose. **Effort:** small.

Changes in `book/docs/ch15.rst`:
1. **Lines ~128-133 — context drift.** This passage reads as if depth buffering
   has *not* been applied ("the square should not be visible… this is because…")
   — it appears copied from ch14:282-302, which describes the *problem*. ch15 is
   the chapter that *enables* depth buffering to *fix* that problem, so the prose
   should describe what depth buffering now resolves, not restate the bug as
   present. Rewrite to match ch15's "after" state. **Confirm intended narrative
   with Bill** (he knows the demo14→15 before/after framing).
2. **Capitalization.** Same passage starts sentences lowercase ("the square…",
   "this is because…") → capitalize.

Verification: prose only. Read ch14:282-302 and ch15:128-133 side by side to
confirm the ch15 copy is stale. Bill renders via `make html`.

## Notes
- Line numbers are as of 2026-05-27; match on surrounding text when editing.
- Constraints unchanged: I can edit + `git add`, **no commits**, **no doc build**
  (`texExpToPng` absent), **no GL run**. See `tasks/codebase-overview.md`.
</content>
