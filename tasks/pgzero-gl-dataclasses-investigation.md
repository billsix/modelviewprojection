# Investigate dataclasses + `__post_init__` for the pgzero_gl renderer classes

**Status:** proposed — needs go-ahead (do NOT investigate yet; the maintainer wants to discuss first)
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

## Open questions

1. **Scope:** just the texture class(es) the maintainer flagged, or all pgzero_gl GL-resource wrappers? *Recommend
   surveying all wrappers but recommending conversions conservatively, class by class.*
2. **`frozen` dataclasses?** GL wrappers usually mutate (bind state, resize) — *recommend non-frozen with `eq=False`
   for handle-bearing types; revisit per class.*
