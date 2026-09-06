# Investigate dataclasses + `__post_init__` for the pgzero_gl renderer classes

**Status:** DONE 2026-09-05 — decided by the maintainer and implemented in all six tightened
games (see "Decision" below); archived. The shared shim under `src/modelviewprojection/pgzero_gl/`
is untouched (step 3 of the inline initiative decides its fate).
**Priority:** 6
**Difficulty:** 3

## BLUF

Several classes in the `pgzero_gl` renderer (textures, and likely buffer/framebuffer/GL-resource wrappers) look
like they're mostly *data + a bit of derived setup* written out as hand-rolled `__init__`s — a shape Python
`@dataclass` (with `__post_init__` for the GL-side setup and validation) expresses more cleanly. This task is to
**investigate** where a dataclass conversion genuinely helps, where it doesn't (or would be wrong), and to bring a
concrete recommendation back **before changing anything**. "Done" = a written recommendation (which classes to
convert, which to leave, and the mechanism) that the maintainer approves or declines.

## Context

**Where to look:** `src/modelviewprojection/pgzero_gl/renderer.py` and `renderer_gl1.py` (the maintainer called it
"pgl_zero"; the package is **`pgzero_gl`**). Start with the texture class(es) the maintainer flagged, then the
neighbouring GL-resource wrappers.

**Not yet started** — this doc is a placeholder created 2026-09-03 at the maintainer's request; the actual code
read happens at investigation time.

**The house rule that governs this (read before recommending):** the personal conventions' *"What earns pulling
code into its own function / abstraction"* and *"An externally-defined name always wins over a naming convention"*
— a dataclass is worth it for *naming a data shape + removing boilerplate*, not for its own sake. In particular:

- **`__post_init__` is a Python-defined name** (like a dunder) — the naming rules don't apply to it; match it exactly.
- **Where a dataclass fits:** a class that is a bag of fields set in `__init__`, plus some derived/validated state.
  `@dataclass` gives the field list, `__init__`, `__repr__`, and `__eq__` for free; `__post_init__` holds the
  "allocate the GL texture / validate dimensions / compute derived fields" step. Cleaner and less error-prone.
- **Where it does NOT fit (call these out explicitly, don't force it):** classes whose identity is behaviour not
  data; classes holding an **unhashable/mutable GL handle** where dataclass `eq`/`frozen` semantics would mislead
  (a GL texture id compared by value is wrong — likely want `eq=False` or identity semantics); classes with
  non-trivial constructor logic that isn't "set fields then derive"; anything where `@dataclass`'s generated
  `__init__` fights an ordering/validation requirement. A dataclass with `eq=False`/`frozen=False` that exists only
  to shorten `__init__` may or may not be worth the import — judge per class.

## What the investigation should produce

1. An inventory of the pgzero_gl classes that are candidates (name, file:line, current `__init__` shape).
2. Per candidate: convert / leave, the mechanism (`@dataclass`, `field(default_factory=…)`, `__post_init__` for GL
   setup, `eq=False` for handle-bearing types), and the concrete before/after boilerplate delta.
3. The classes to explicitly **leave alone**, with the reason (per the "don't force it" list above).
4. Whether any GL-resource lifecycle (allocate in `__post_init__`, free in a `__del__`/context manager) interacts
   badly with dataclass semantics — a real footgun to check, not assume.

## General discussion (for the conversation the maintainer wants) — see the chat message; summarized here

Dataclasses suit the "typed record with a little derived setup" shape and remove `self.x = x` boilerplate, a real
win for GL wrapper classes that carry width/height/format/handle. `__post_init__` is the right home for the
GL-side allocation + validation that a plain field assignment can't do. The main caution is **value-equality on a
GL handle** (default dataclass `__eq__`/`__hash__` compares fields, which is wrong for an opaque resource id — use
`eq=False`) and **lifecycle** (a dataclass that allocates a GL object in `__post_init__` still needs explicit
freeing). So: likely yes for the plain data-shape classes, with `eq=False` where a handle is involved, and no for
the behaviour-heavy ones.

## Input from the boing tightening pilot (2026-09-05, Fable) — for the discussion

Not implemented (this task's shape question is the maintainer's to decide); recorded so the
discussion starts from the read code. In the inlined games the classes are `Image` (resources
section) and `Renderer` / `Renderer1x` (renderer sections); the shared shim has the same three.

- **`Image` — recommend `@dataclass(slots=True, eq=False)` + `__post_init__`.** It is exactly the
  "path in, derived pixels/size out, GL handle later" shape: fields `path: str`, then
  `rgba`/`width`/`height` as `field(init=False)` computed in `__post_init__` (the Pillow decode +
  `convert("RGBA")` with its palette-transparency comment), `_tex: int | None =
  field(default=None, init=False)` uploaded lazily in `gl_texture()`. `eq=False` because two
  images with equal pixels are not the same texture, and a generated `__eq__` on numpy arrays
  would raise anyway. `from_rgba` (used only by `text.py`'s glyph renderer, in the games that keep
  `text`) becomes a classmethod that builds an `Image` without a path — give `path` a `None`
  default or split the decode into a helper both paths call. Lifecycle: nothing frees textures
  today (process exit does); a dataclass changes nothing there. boing stripped `from_rgba`/
  `get_width`/`get_height` (dead) but left the class hand-rolled pending this decision.
- **`Renderer` / `Renderer1x` — recommend leaving them as plain classes.** Their `__init__` is
  not "set fields then derive"; it is a GL setup *sequence* (compile + link a program, query
  uniforms, build VAOs/VBOs, set blend state) whose order matters and whose "fields" are GL
  handles. A dataclass with everything `init=False` would only move that sequence into
  `__post_init__` under a misleading field list. What DID help: stripping the methods a game never
  calls (boing dropped the flat-colour primitives and the primitives VAO/VBO) and typing the
  interface as a structural `SpriteRenderer` Protocol (both pipelines satisfy it; see
  `tasks/reference/code-the-classics-tightening.md` §1.6 for why not by subclassing).
- **The shader's flat-colour branch** (`uUseTex`/`uTint`) is kept in boing even though it only
  draws sprites — a renderer decision for here, not a tightening one.

## Decision (maintainer, 2026-09-05) and implementation

The maintainer proposed the shape: a hand-rolled `__init__` that computes many attributes from
one or two inputs becomes a **dataclass of the resulting state built by a factory function**, and
related instance variables are grouped into their own named dataclasses. Implemented by
`tasks/adhoc/codetheclassics-tighten-games/renderer_dataclasses.py` (idempotent codemod, run on
boing, boing_gl1, cavern, myriapod, bunner, soccer):

- `Uniforms` (the seven uniform locations, was `u_*`), `GLBuffer` (a VAO + its VBO, was
  `quad_vao`/`quad_vbo` and `prim_vao`/`prim_vbo`), `Renderer` as
  `@dataclass(slots=True, eq=False)` of `width, height, ortho, program, uniforms, quad[, prim]`
  plus the per-frame `fb_width`/`fb_height` (`init=False`, set in `__post_init__`), and
  `make_renderer(width, height)` doing the GL work in the SAME call order as the old `__init__`
  (`_link_program`, `_make_buffer` name the phases). `eq=False` because handles compared by
  value are meaningless; not frozen because the framebuffer size is updated every frame.
- `Renderer1x` (boing_gl1) likewise, with its own `make_renderer`, so the two boing files keep
  the same window line.
- `Image` as a dataclass of `rgba` + lazy `_tex`, with `width`/`height` as properties (no
  redundant fields); `load_image(path)` and `image_from_rgba(arr)` are the factories; the
  `images` loader takes `load_image`.
- Proven: frame 180 byte-identical for all six games against their pre-restructure versions,
  bunner's debug overlay (the `rect` primitive) byte-identical with the flag forced on, ty clean.

## Open questions — superseded by the decision above

1. **Scope:** just the texture class(es) the maintainer flagged, or all pgzero_gl GL-resource wrappers? *Recommend
   surveying all wrappers but recommending conversions conservatively, class by class.*
2. **`frozen` dataclasses?** GL wrappers usually mutate (bind state, resize) — *recommend non-frozen with `eq=False`
   for handle-bearing types; revisit per class.*
