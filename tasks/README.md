# Tasks — modelviewprojection

Lightweight session task tracker (per the global `~/.claude/CLAUDE.md` convention:
one `tasks/<slug>.md` per task, check this dir at session start). Detailed specs
for many items live in `plans/` — this list points into them rather than
duplicating. **Ports work is parked** at Bill's request (still tracked under
`plans/ports-*.md`).

Start here for orientation: [`codebase-overview.md`](codebase-overview.md) —
structure, the InvertibleFunction/Cayley-graph abstraction, the demo arc, the
container/build pipeline, and what I can/can't do in this container.

## Book ↔ code drift audit (whole book)

Three trackers, one per chapter range; doc-region wiring is intact throughout, so
findings are prose / captions / hand-written code / a handful of real code bugs.

| Range | Tracker | Per-finding plans |
|------|---------|-------------------|
| ch1–6 | [`book-code-drift-ch1-6.md`](book-code-drift-ch1-6.md) | natural-basis, is_clockwise, ch05-section, ch02/03-typos |
| ch7–15 | [`book-code-drift-ch7-15.md`](book-code-drift-ch7-15.md) | ch07, ch10, ch13, ch14, ch15 + cross-cutting below |
| ch16–21 + perspective | [`book-code-drift-ch16-21.md`](book-code-drift-ch16-21.md) | ch16, ch17, ch18, ch19, ch20, ch21 + cross-cutting below |

**Cross-cutting plans (span ranges):**
✅ [`archive/book-explain-natural-basis.md`](archive/book-explain-natural-basis.md) (headline — DONE; e_1/e_2/e_3 now introduced 2D in ch05, 3D in ch14) ·
✅ [`archive/fix-method-vs-function-wording.md`](archive/fix-method-vs-function-wording.md) (DONE) ·
✅ [`archive/fix-mathutils-latex-and-error-strings.md`](archive/fix-mathutils-latex-and-error-strings.md) (DONE) ·
✅ [`archive/fix-is-clockwise-recursion.md`](archive/fix-is-clockwise-recursion.md) (DONE) ·
✅ [`archive/fix-demo-code-bugs.md`](archive/fix-demo-code-bugs.md) (DONE — demo14 `zero`, demo21 imports) ·
✅ [`archive/ch05-translate-section-fixes.md`](archive/ch05-translate-section-fixes.md) (DONE) ·
✅ [`archive/ch02-ch03-prose-typos.md`](archive/ch02-ch03-prose-typos.md) (DONE)

**Verified code bugs surfaced by the audit (highest value):** `is_clockwise`
recursion · `uniform_scale`/`scale_non_uniform` LaTeX-repr · "Note invertible"
typos · `demo14.py:42 zero = Vector3D.e_3()` · `demo21.py` missing `sys`/`os`.

## Other active (non-port)

| Task | Status | Doc |
|------|--------|-----|
| **Extract duplicated demo helpers** into per-concept modules (teach-once-then-import) | in progress — `shading.py` ✅, `windowing.py` (`on_key`) ✅, `clipping.py` (`draw_in_square_viewport`) ✅; `set_mvp_uniforms` variant deferred | [`../plans/extract-duplicated-demo-helpers.md`](../plans/extract-duplicated-demo-helpers.md) |
| **Separate data generation from rendering** in SuperBible ports (precompute trig into `_primitives` builders) | conversions COMPLETE (~30 demos: sphere/torus/ground/cone + dynamic-tess dirty-flag); only leave-alone set remains; pending Bill's visual verification | [`extract-data-generation.md`](extract-data-generation.md) |
| **Cube-map sphere reflection doesn't track the camera** (ch09 port bug) | not started — investigate + fix | [`cubemap-reflection-static.md`](cubemap-reflection-static.md) |
| **Make shadow-map depth values visually distinguishable** (ch14/ch18 debug view) | not started — investigated; plan ready, approach TBD w/ Bill | [`shadowmap-depth-discrimination.md`](shadowmap-depth-discrimination.md) |
| **Move keyboard render-options to imgui** (mode toggles/shader-select/etc. → checkboxes/combos) | not started — recent-commit set inventoried; coordinate w/ ports-ux Phase 3 | [`ports-render-options-to-imgui.md`](ports-render-options-to-imgui.md) |
| De-duplicate per-demo `handle_inputs` (the camera-walk / paddle-move sub-blocks) | investigation task (not started) | [`../plans/dedup-handle-inputs.md`](../plans/dedup-handle-inputs.md) |
| Investigate `_face_normal` taking/returning `Vector3D` (vs the current tuple in/out) | investigation task (not started) | [`../plans/face-normal-vector3d-io.md`](../plans/face-normal-vector3d-io.md) |
| Confirm PDF + EPUB build green after inlinetex migration | blocked-on-Bill (needs build container) | [`finish-pdf-epub-build.md`](finish-pdf-epub-build.md) |
| Curriculum math: planar-shadow matrix in `pyMatrixStack` | planned | [`../plans/planar-shadow-matrix.md`](../plans/planar-shadow-matrix.md) |
| Curriculum math: `rotate_around_axis` in `pyMatrixStack` (decomposed, not Rodrigues) | planned | [`../plans/rotate-around-axis.md`](../plans/rotate-around-axis.md) |
| demo22 light-radius imgui slider | planned | [`../plans/demo22-light-radius-imgui.md`](../plans/demo22-light-radius-imgui.md) |

## Backlog (from root `TODO.org`, not yet broken out)

- Rename `rotate`/`translate`/`scale` → `R`/`T`/`S` notation (imports + code + book), and add an explanation of `I` (identity) and `T`/`R`/etc.
- Modernized demos `demo22a`/`demo23`/`demo24` (pyramid/litjet/sphereworld) exist in `src/` but have **no book chapters** (toctree stops at `ch21`).
- Many per-chapter prose/diagram improvements (ch1–22) enumerated in `TODO.org`.

## Conventions in this repo
- `plans/` = durable detailed specs + dated `HANDOFF-*.md` session notes.
- `tasks/` (here) = the lightweight cross-session tracker.
- I can edit code/docs and `git add` to stage; **no commits** (Bill GPG-signs
  outside the container), **no graphical/GL runs**, **no doc build** (no
  `texExpToPng` locally).
</content>
