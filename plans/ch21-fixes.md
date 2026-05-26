# Plan: ch21 (OpenGL 3.3 Core) — write the missing chapter prose

**Status:** planned. **Type:** book content (largest gap in 16→end). **Effort:** large.
**Source:** ch19–21 drift audit. Corroborated by TODO.org ("Ch 21 Do much better").

## Context
ch21 is effectively **unfinished**: it has the scaffolding (Objective, How to
Execute, keyboard table, a "Description" heading, an empty "The Event Loop"
heading at ~86-88) but **almost no explanatory prose** — just a sequence of
`literalinclude`s of `demo21/demo21.py` and its four shader files. None of the
core 3.3-Core concepts the chapter introduces are explained.

## Work
1. **Fix the broken demo first** — `demo21/demo21.py` is missing `import sys` /
   `import os` (see `tasks/archive/fix-demo-code-bugs.md`). The chapter ships
   non-running code until that lands.
2. **Write prose** for the concepts the includes show, in Bill's voice, connected
   back to ch20:
   - `compile_program()` / shader compilation + linking;
   - VAO and VBO creation and the `all_vaos`/`all_vbos` tracking lists;
   - attribute setup and `glUniformMatrix4fv` / the `mvpMatrix` uniform;
   - the `pyMatrixStack` API used here: `MatrixStack` enum
     (model/view/projection/modelview/modelviewprojection), `push_matrix(stack)`
     context manager, `set_to_identity_matrix`, `rotate_x/y/z`, `translate`,
     `perspective`, `multiply` (`src/modelviewprojection/pyMatrixStack.py`);
   - fill in the empty "The Event Loop" section.
   TODO.org also asks to "connect with 20 — draw VBO, draw VAO, give shader
   variables names similar to 20" — diagrams are part of doing this well.
3. This is genuine authoring, not a fix — **plan the prose outline with Bill**
   before writing; he may want it split with a future ch22 (TODO.org sketches a
   ch22 = ch21 + color-as-uniform).

## Verification
- demo21 import fix verified per `tasks/archive/fix-demo-code-bugs.md`.
- Bill renders via `make html` and reviews the new prose for voice/accuracy.
</content>
