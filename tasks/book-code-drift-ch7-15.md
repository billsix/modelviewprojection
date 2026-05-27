# Task: book ↔ code drift in chapters 7–15

**Status:** audited 2026-05-27 (5 Explore agents + direct verification of all
code-level claims). Per-finding plans live in `plans/`; this is the index.
Same method as `book-code-drift-ch1-6.md`: doc-region wiring is intact across
7–15 (no broken labels), so drift is prose / captions / hand-written code / a few
real code bugs.

## Cross-cutting (span multiple chapters)
| Finding | Plan |
|---|---|
| `e_1`/`e_2`/`e_3` natural basis used in every demo, explained nowhere (ch07–15 all hit) | [`../plans/book-explain-natural-basis.md`](../plans/book-explain-natural-basis.md) |
| ✅ Module-level transforms called "methods" in prose (ch08:65,128; ch09:80) — DONE | [`archive/fix-method-vs-function-wording.md`](archive/fix-method-vs-function-wording.md) |
| ✅ mathutils LaTeX-repr bugs + "Note invertible" typos (all scale inverses → `\frac`; lines 629/728) — DONE | [`archive/fix-mathutils-latex-and-error-strings.md`](archive/fix-mathutils-latex-and-error-strings.md) |
| ✅ `is_clockwise` self-recursion (`mathutils.py:705`) — DONE | [`archive/fix-is-clockwise-recursion.md`](archive/fix-is-clockwise-recursion.md) |
| ✅ demo code bugs: `demo14.py:42 zero = Vector3D.e_3()` — DONE | [`archive/fix-demo-code-bugs.md`](archive/fix-demo-code-bugs.md) |
| Reused `doc-region` label "define vector class" pulls Vector1D not Vector3D (manifests in ch14; also ch05/06) | [`../plans/ch14-fixes.md`](../plans/ch14-fixes.md) |

## Per-chapter
| Chapter | Findings (verified unless noted) | Plan |
|---|---|---|
| ch07 | ✅ `theta`→`\theta` LaTeX typo :203 — DONE (the `.. TODO` at :58-59 is a hidden RST comment, left per Bill) | [`archive/ch07-fixes.md`](archive/ch07-fixes.md) |
| ch08/09 | only the "method"→"function" wording | (method-vs-function plan above) |
| ch10 | `camera.x/y`→`camera.position_ws` (:363,:381); broken method-API code blocks (~:149-216, incl. missing `)`); typos (:120,:131,:257) | [`../plans/ch10-fixes.md`](../plans/ch10-fixes.md) |
| ch11/12 | no chapter-specific drift beyond the basis omission (above) | — |
| ch13 | ✅ figure `_static/demo11.png` shown for a Demo-13 chapter (:63) — DONE (per-chapter `demo13.dot`) | [`archive/ch13-fixes.md`](archive/ch13-fixes.md) |
| ch14 | caption missing `.py` (:133); doc-region label collision (above); grammar/pronoun (:102,:227,:229,:322) | [`../plans/ch14-fixes.md`](../plans/ch14-fixes.md) |
| ch15 | depth-buffer prose describes the "before" state in the "after" chapter (~:128-133); lowercase sentence starts | [`../plans/ch15-fixes.md`](../plans/ch15-fixes.md) |

## Notes
- Line numbers are as of 2026-05-27; match on surrounding text when editing.
- Constraints unchanged: I can edit + `git add`, **no commits**, **no doc build**
  (`texExpToPng` absent), **no GL run**. See `tasks/codebase-overview.md`.
</content>
