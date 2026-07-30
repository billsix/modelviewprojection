# Plan: type-hint pass for SuperBible v4 + v7 ports

Apply the same two-stage typing pass that McNopper just received to
`/mvp/ports/openglsuperbiblev4/` (101 .py files, chapt01–22) and
`/mvp/ports/openglsuperbiblev7/` (83 .py files).

**Status:** not started.

**Read first:** [`notes-glus-c-to-python-typing.md`](notes-glus-c-to-python-typing.md)
— C-to-Python type table, where to annotate / skip, and the footguns I
already hit on McNopper. The bulk of the methodology is there; this
plan is just the v4/v7-specific delta.

## Scope

- **v4:** `/mvp/ports/openglsuperbiblev4/_common.py` plus every
  `chapt*/<demo>/*.py`. Source for type hints is the C++ in
  `/superbible/Examples/Src/Chapter*/<demo>/<demo>.cpp` — find the
  closest `.cpp` per demo and read the variable declarations.
- **v7:** `/mvp/ports/openglsuperbiblev7/_common.py`, the helper modules
  (`_vmath.py`, `_ktx.py`, `_sb6m.py`, `_sb7.py`, `_colors.py`), and
  every `<demo>/*.py`. Source: `/superbiblev7/src/<demo>/<demo>.cpp`
  (and the shared header `/superbiblev7/include/sb7.h` for framework
  types).

## Method

For each port (do v4 first, then v7):

### Pass 1 — function signatures

Walk every `def` in `_common.py` and the demo files. Add types to
parameters and return types. Should already be 80% covered from prior
work; fill in the gaps. Use `Optional[X]` for parameters that default
to `None`, `Sequence[float]` / `np.ndarray` for vectors, `Vec3` / `Vec4`
type aliases (mirror McNopper's `_common.py` convention) for the common
3- and 4-vector cases.

### Pass 2 — local variables

Inside function bodies, annotate the first assignment of each name when
the type adds clarity. Use the C-to-Python type table from the notes.
Skip loop counters, single-letter math intermediates, trivial-literal
RHS. Don't use `Any`.

For v7 specifically, the `vmath` types in `_vmath.py` are already
defined; use them (`_vmath.vec3`, `_vmath.mat4`) rather than raw
`np.ndarray` where the original C++ used `vmath::vec3` / `vmath::mat4`.

## Workflow per port

1. **Inventory.** `find <port> -name '*.py' | wc -l` and
   `wc -l <port>/_common.py <port>/**/*.py` to size the job.
2. **Function-signature pass.** Do `_common.py` by hand. Then dispatch
   the per-demo files to a subagent with the same prompt template used
   for McNopper (in the McNopper conversation transcript) — substitute
   the v4/v7 path and the v4/v7-specific framework callbacks.
3. **Compile-check.** `for f in ...; do python -c "import py_compile;
   py_compile.compile('$f', doraise=True)"; done`. Errors must be 0.
4. **Local-variable pass.** Same shape: hand-do `_common.py` plus the
   `_vmath.py` / `_ktx.py` / `_sb6m.py` / `_sb7.py` helpers, then
   dispatch demos to a subagent with the C++-type-table reference and
   the "where to skip" list. Reuse the McNopper subagent prompt; swap
   the GLUS table for the C++-equivalent (`vmath::vec3 → np.ndarray`,
   `GLuint → int`, etc.).
5. **Compile-check** again.
6. **Sanity-check** by reading 3 random demo files and confirming the
   diff looks like the McNopper diff did — readable, not noisy.

## Framework-callback signatures

These are the equivalents of McNopper's `init / reshape / update / panel`.
Give the subagent the per-port set so it doesn't have to derive them.

### v4 (chapt-style)

Most v4 demos use the chapter-specific framework. Common shapes:
- `def setup_rc() -> None:` (RenderContext setup)
- `def render_scene() -> None:` (per-frame draw)
- `def change_size(w: int, h: int) -> None:` (reshape)
- `def shutdown_rc() -> None:`
- `def key_handler(window: Any, key: int, scancode: int, action: int, mods: int) -> None:`

But the actual entry points vary by chapter — the chapt19 demos look
different from chapt05. Read the `_common.py` callback registry first
to confirm.

### v7

Per the v7 framework gotchas notes
([`notes-v7-port-framework-gotchas.md`](notes-v7-port-framework-gotchas.md)):
- `def startup(self) -> None:`
- `def render(self, current_time: float) -> None:`
- `def shutdown(self) -> None:`
- `def on_key(self, key: int, action: int) -> None:`
- `def on_resize(self, w: int, h: int) -> None:`

Demos are class-based in v7; annotate `self.<field>` first assignments
(usually inside `startup`).

## Done when

- All `.py` files in both ports compile (`py_compile`) clean.
- Spot-check 3 demos per port — annotations match the C++ source's
  variable types and don't make the code less readable.
- No `Any` used except for glfw window handles inside `run_demo`-style
  closures.
- Memory note `feedback_python_types_for_ports.md` updated (or written)
  if any v4/v7-specific footguns turn up that aren't already in the
  GLUS notes file.

## Don't

- Don't change runtime behavior, even slightly.
- Don't refactor while typing — stash any "this should be a dataclass"
  observations as a *separate* follow-up plan.
- Don't run mypy. PyOpenGL has no stubs and the noise will drown the
  signal.
- Don't add types you can't justify from the C++ source or local
  context.
