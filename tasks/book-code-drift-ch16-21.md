# Task: book ↔ code drift in chapters 16–21 + perspective

**Status:** audited 2026-05-27 (Explore agent + direct verification). Per-finding
plans in `plans/`; this is the index. doc-region wiring intact; drift is prose /
captions / content gaps / a code bug. The later chapters (esp. ch21) are not just
drifted but **unfinished**.

## Cross-cutting
| Finding | Plan |
|---|---|
| `e_1`/`e_2`/`e_3` natural basis unexplained (ch16–18 use it heavily) | [`../plans/book-explain-natural-basis.md`](../plans/book-explain-natural-basis.md) |
| ✅ Wrong code names in prose: `modelspace_to_ndc`→`modelspace_to_ndc_fn` (ch16:184,234,486); `camera_space_to_ndc_space_fn`→`cs_to_ndc_space_fn` (ch16:231, ch17:310) — DONE | [`archive/fix-method-vs-function-wording.md`](archive/fix-method-vs-function-wording.md) |
| ✅ `demo21/demo21.py` missing `import sys`/`import os` (ships broken via ch21) — DONE | [`archive/fix-demo-code-bugs.md`](archive/fix-demo-code-bugs.md) |

## Per-chapter
| Chapter | Findings (verified unless noted) | Plan |
|---|---|---|
| ch16 | caption missing `.py` (:194); name refs (above); broken/short sentence ~:267 (TODO.org) | [`../plans/ch16-fixes.md`](../plans/ch16-fixes.md) |
| ch17 | "fixed in demo17"→demo18 (:41); `push_transformation` context manager + `rotate_x/y/z` introduced in code but unexplained; diagrams (TODO.org) | [`../plans/ch17-fixes.md`](../plans/ch17-fixes.md) |
| ch18 | captions say `demo18.py` on mathutils includes (:248,:262); "ration"→"ratio" (:225); f1/f2/f3 + `Callable` unexplained (TODO.org) | [`../plans/ch18-fixes.md`](../plans/ch18-fixes.md) |
| ch19 | ✅ `glPushStack`/`glPopStack`→`glPushMatrix`/`glPopMatrix` (:59,:60) + demo19 `with`-block comment (:264-266) — DONE (the `.. TODO` at :201 is a hidden RST comment, left per Bill) | [`archive/ch19-fixes.md`](archive/ch19-fixes.md) |
| ch20 | GLSL builtins misspelled: `gl_Modelview_matrix`/`glProjectionMatrix`→`gl_ModelViewMatrix`/`gl_ProjectionMatrix` (:122-123); thin prose (TODO.org) | [`../plans/ch20-fixes.md`](../plans/ch20-fixes.md) |
| ch21 | **unfinished** — scaffolding only, no explanatory prose; empty "Event Loop" (~:86-88); depends on demo21 import fix | [`../plans/ch21-fixes.md`](../plans/ch21-fixes.md) |
| perspective.rst | standalone math prose (no literalincludes); one stray `// TODO -- proof of monotonicity` (:675). No other drift found. | (fold into a future perspective pass) |

## Out of scope (noted, not planned here)
- `demo22a`/`demo23`/`demo24` (pyramid/litjet/sphereworld) exist in `src/` with
  **no chapters** and aren't in the toctree (stops at ch21). Curriculum gap, not
  drift — track separately if Bill wants chapters for them.

## Notes
Line numbers as of 2026-05-27; match on text. Constraints per
`tasks/codebase-overview.md` (no commits / doc build / GL run here).
</content>
