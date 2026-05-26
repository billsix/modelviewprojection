# Plan: ch20 (first shader) fixes

**Status:** planned. **Type:** book prose. **Effort:** small.
**Source:** ch19–21 drift audit.

## Findings + changes (`book/docs/ch20.rst`)
1. **Lines 122-123 — misspelled GLSL builtins.** Prose says
   "**gl_Modelview_matrix**" and "**glProjectionMatrix**"; the actual
   fixed-function GLSL builtins (and what `demo20/triangle.vert` uses) are
   **`gl_ModelViewMatrix`** and **`gl_ProjectionMatrix`**. Fix the names to match
   the shader source exactly (verify against `demo20/triangle.vert`/`.frag`).
2. **TODO.org ch20: "Do much better. Draw diagrams. Explain better" and "Don't
   put commented code in inline code."** ch20 is thin; the shader-pipeline intro
   deserves real prose + a diagram, and any explanatory comments currently inside
   the `literalinclude`d code should move into rst prose. Larger content work —
   scope with Bill.

## Verification
`grep -nE "gl_Modelview_matrix|glProjectionMatrix" book/docs/ch20.rst` → empty
after; cross-check the corrected names appear verbatim in
`src/modelviewprojection/demo20/triangle.vert`. Bill renders via `make html`.
</content>
