# Task: book ↔ code drift in chapters 16–21 + perspective

**Status:** audited 2026-05-27 (Explore agent + direct verification). This is the
self-contained tracker — per-chapter fix detail is folded in below (the old
`ch16-fixes.md … ch21-fixes.md` satellites were archived 2026-06-14). doc-region
wiring intact; drift is prose / captions / content gaps / a code bug. The later
chapters (esp. ch21) are not just drifted but **unfinished**.

## Cross-cutting
| Finding | Plan |
|---|---|
| ✅ `e_1`/`e_2`/`e_3` natural basis unexplained — DONE (2D ch05, 3D ch14) | [`archive/book-explain-natural-basis.md`](archive/2026/05/26/book-explain-natural-basis.md) |
| ✅ Wrong code names in prose: `modelspace_to_ndc`→`modelspace_to_ndc_fn` (ch16:184,234,486); `camera_space_to_ndc_space_fn`→`cs_to_ndc_space_fn` (ch16:231, ch17:310) — DONE | [`archive/fix-method-vs-function-wording.md`](archive/2026/05/26/fix-method-vs-function-wording.md) |
| ✅ `demo21/demo21.py` missing `import sys`/`import os` (ships broken via ch21) — DONE | [`archive/fix-demo-code-bugs.md`](archive/2026/05/26/fix-demo-code-bugs.md) |

## Per-chapter
| Chapter | Findings (verified unless noted) | Plan |
|---|---|---|
| ch16 | caption missing `.py` (:194); name refs (above); broken/short sentence ~:267 (TODO.org) | see **ch16 detail** below |
| ch17 | "fixed in demo17"→demo18 (:41); `push_transformation` context manager + `rotate_x/y/z` introduced in code but unexplained; diagrams (TODO.org) | see **ch17 detail** below |
| ch18 | captions say `demo18.py` on mathutils includes (:248,:262); "ration"→"ratio" (:225); f1/f2/f3 + `Callable` unexplained (TODO.org) | see **ch18 detail** below |
| ch19 | ✅ `glPushStack`/`glPopStack`→`glPushMatrix`/`glPopMatrix` (:59,:60) + demo19 `with`-block comment (:264-266) — DONE (the `.. TODO` at :201 is a hidden RST comment, left per Bill) | [`archive/ch19-fixes.md`](archive/2026/05/26/ch19-fixes.md) |
| ch20 | GLSL builtins misspelled: `gl_Modelview_matrix`/`glProjectionMatrix`→`gl_ModelViewMatrix`/`gl_ProjectionMatrix` (:122-123); thin prose (TODO.org) | see **ch20 detail** below |
| ch21 | **unfinished** — scaffolding only, no explanatory prose; empty "Event Loop" (~:86-88); depends on demo21 import fix | see **ch21 detail** below |
| perspective.rst | standalone math prose (no literalincludes); one stray `// TODO -- proof of monotonicity` (:675). No other drift found. | (fold into a future perspective pass) |

## Per-chapter detail (folded from ch16/17/18/20/21-fixes.md)

### ch16 (jump to 3D) — `book/docs/ch16.rst`
**Status:** PARTIAL — caption :194 (`+.py`) fixed & staged 2026-05-27; the name
refs (:184/:231) done in the (archived) method-vs-function plan. Still open: the
broken/short sentence ~:267 (**needs Bill's wording**).
1. **Line 194 — caption missing `.py`.** `:caption: src/modelviewprojection/mathutils`
   → `…/mathutils.py`.
2. **Line 184 — wrong name.** "through the `modelspace_to_ndc` method" — the
   FunctionStack method is **`modelspace_to_ndc_fn`**. → done in
   `tasks/archive/.../fix-method-vs-function-wording.md`; noted for completeness.
3. **Line 231 — `camera_space_to_ndc_space_fn`** vs mathutils **`cs_to_ndc_space_fn`**
   → also in the method-vs-function plan (verify whether a local wrapper uses the
   long name before changing).
4. **Line ~267 — broken/short sentence** (TODO.org: "Fix spacing on line 267").
   Sentence ends mid-clause ("…the current space"). Finish / fix spacing. Confirm
   wording with Bill.
Verification: `grep -n "modelspace_to_ndc\b\|mathutils$" book/docs/ch16.rst`; read
line 267 in context.

### ch17 (camera rotation) — `book/docs/ch17.rst`
**Status:** PARTIAL — wrong demo ref :41 ("demo17"→"demo18") fixed & staged
2026-05-27. Still open: explain `push_transformation` + `rotate_x/y/z` (2/3) and
the diagrams (4).
1. **Line 41 — wrong demo reference.** "fixed in demo17" but perspective arrives
   in **demo18** → "fixed in demo18".
2. **Content gap: `push_transformation` context manager unexplained.** demo17
   switches from demo16's manual `fn_stack.push()`/`pop()` to
   `with push_transformation(...):` (demo17.py ~248-309) — a pedagogical shift the
   prose never introduces. Add an explanation where the first `with` block appears.
3. **Content gap: `rotate_x`/`rotate_y`/`rotate_z` unexplained.** Used in demo17
   (imports ~35-37) but never named in prose. Introduce them by name.
4. **Diagrams (TODO.org): "Fix two diagrams" + "Add third diagram."** Camera-rotation
   geometry wants a diagram. Asset work — coordinate with Bill.

### ch18 (perspective / stack) — `book/docs/ch18.rst`
**Status:** PARTIAL — "ration"→"ratio" (:225) done; `:262` perspective-include
caption fixed (`demo18.py`→`mathutils.py`); the `:248` Vector-class include was
**removed entirely** by the doc-region relabel (see archived `ch14-fixes.md`),
replaced with a one-line `Vector3D` reference. Still open: f1/f2/f3 + `Callable` (3).
1. **Lines 248 and 262 — wrong captions.** Both `literalinclude`s pull from
   `mathutils.py` (Vector class @248, `perspective` @262) but `:caption:` said
   `src/modelviewprojection/demo18.py` → set to `…/mathutils.py`. (Same recurring
   caption bug as ch05.)
2. **Line 225 — typo.** "aspect **ration**" → "aspect **ratio**".
3. **Content gap (TODO.org): f1/f2/f3 + `Callable`.** Event-loop sections
   (~266-287) use bare `f1`/`f2`/`f3` with no explanation; TODO.org asks to
   "Explain Callable, make example." Add the detail / a `Callable` example.

### ch20 (first shader) — `book/docs/ch20.rst`
**Status:** PARTIAL — item 1 (GLSL builtin names) fixed & staged 2026-05-27:
`gl_ModelViewMatrix`, `gl_ProjectionMatrix`, `gl_Color`, `gl_FrontColor`,
`gl_BackColor` now match `demo20/triangle.vert`. Left `glColor3f`/`glUseProgram`
(real C API) and `glVertex` (×3 — reads as the C draw call; **confirm with Bill**
whether the shader builtin `gl_Vertex` was meant). Still open: item 2.
1. **Lines 122-123 — misspelled GLSL builtins.** Prose said "gl_Modelview_matrix"
   and "glProjectionMatrix"; correct builtins (what `demo20/triangle.vert` uses)
   are **`gl_ModelViewMatrix`** and **`gl_ProjectionMatrix`**.
2. **TODO.org ch20: "Do much better. Draw diagrams. Explain better" + "Don't put
   commented code in inline code."** ch20 is thin; shader-pipeline intro deserves
   real prose + a diagram, and explanatory comments inside `literalinclude`d code
   should move into rst prose. Larger content work — scope with Bill.
Verification: `grep -nE "gl_Modelview_matrix|glProjectionMatrix" book/docs/ch20.rst`
→ empty after; cross-check corrected names appear verbatim in `demo20/triangle.vert`.

### ch21 (OpenGL 3.3 Core) — write the missing chapter prose
**Status:** planned. **Type:** book content (largest gap in 16→end). **Effort:** large.
Corroborated by TODO.org ("Ch 21 Do much better").

ch21 is effectively **unfinished**: scaffolding (Objective, How to Execute,
keyboard table, a "Description" heading, an empty "The Event Loop" heading ~86-88)
but **almost no explanatory prose** — just a sequence of `literalinclude`s of
`demo21/demo21.py` and its four shader files. None of the core 3.3-Core concepts
are explained.

Work:
1. **Fix the broken demo first** — `demo21/demo21.py` is missing `import sys` /
   `import os` (done; see archived `fix-demo-code-bugs.md`). The chapter shipped
   non-running code until that landed.
2. **Write prose** for the concepts the includes show, in Bill's voice, connected
   back to ch20: `compile_program()` / shader compilation + linking; VAO/VBO
   creation and the `all_vaos`/`all_vbos` tracking lists; attribute setup and
   `glUniformMatrix4fv` / the `mvpMatrix` uniform; the `pyMatrixStack` API used
   here (`MatrixStack` enum model/view/projection/modelview/modelviewprojection,
   `push_matrix(stack)` context manager, `set_to_identity_matrix`, `rotate_x/y/z`,
   `translate`, `perspective`, `multiply` — `src/modelviewprojection/pyMatrixStack.py`);
   fill in the empty "The Event Loop" section. TODO.org also asks to "connect with
   20 — draw VBO, draw VAO, give shader variables names similar to 20" — diagrams
   are part of doing this well.
3. This is genuine authoring, not a fix — **plan the prose outline with Bill**
   before writing; he may want it split with a future ch22 (TODO.org sketches
   ch22 = ch21 + color-as-uniform).

## Out of scope (noted, not planned here)
- `demo22a`/`demo23`/`demo24` (pyramid/litjet/sphereworld) exist in `src/` with
  **no chapters** and aren't in the toctree (stops at ch21). Curriculum gap, not
  drift — track separately if Bill wants chapters for them.

## Notes
Line numbers as of 2026-05-27; match on text. Constraints per
`tasks/codebase-overview.md` (no commits / doc build / GL run here).
</content>
