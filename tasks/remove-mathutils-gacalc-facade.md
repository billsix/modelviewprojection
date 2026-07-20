# Remove the gacalc re-export facade from `mathutils.py`

**Status:** **DONE 2026-07-20.** Facade removed; all callers, doctests, and book examples
import gacalc directly; `mathutils` keeps only its mvp-local helpers.

**Created:** 2026-07-20
**Requested by:** Bill, 2026-07-20 — "get rid of that reexporting; anything that can
reference gacalc as-is should import it directly, there's no reason for the facade.
Obviously, stuff that's not reexported stays, the module should still exist."

## Goal

`src/modelviewprojection/mathutils.py` is a **facade**: it re-exports ~17 gacalc names
*and* defines mvp-specific graphics math. Drop the pass-through re-exports — every caller
that uses a gacalc thing should `import` it **from gacalc directly**. Keep the mvp-local
helpers in `mathutils.py`; **the module still exists** (for those).

## What is re-exported (delete these imports + `__all__` entries), and their gacalc home

| name(s) | import directly from |
|---|---|
| `Vector1` | `gacalc.g1` |
| `Vector2`, `Bivector2` | `gacalc.g2` |
| `Vector3` | `gacalc.g3` |
| `MultiVectorBase` | `gacalc.base` |
| `InvertibleFunction`, `Linearity`, `compose`, `inverse`, `identity`, `translate`, `uniform_scale`, `scale_non_uniform`, `to_matrix`, `plane_rotation`, `compose_intermediate_fns`, `compose_intermediate_fns_and_fn` | `gacalc.transforms` |

**DECIDED (Bill, 2026-07-20): import the whole function/transform layer from
`gacalc.transforms`, NOT from `gacalc.functions`.** So `InvertibleFunction`, `Linearity`,
`compose`, `inverse`, `identity` (defined in `gacalc.functions` but re-exported by
`gacalc.transforms`) come from `gacalc.transforms`, same as `translate`/`uniform_scale`/etc.
Only the value types split by module: `MultiVectorBase` ← `gacalc.base`, `Vector1` ←
`gacalc.g1`, `Vector2`/`Bivector2` ← `gacalc.g2`, `Vector3` ← `gacalc.g3`.

## What STAYS in `mathutils.py` (mvp-local, built on gacalc — do not move)

`rotate`, `rotate_around`, `rotate_x`, `rotate_y`, `rotate_z`, `cosine`, `sine`, `abs_sin`,
`find_normal`, `plane_equation`, `distance_to_plane`, `ortho`, `perspective`,
`cs_to_ndc_space_fn`, `FunctionStack`, `push_transformation`, `fn_stack`. These import the
gacalc pieces they need (e.g. `rotate` uses `plane_rotation`, `Vector2`) — internally,
`mathutils.py` imports from gacalc like any other consumer.

## Scope (measured 2026-07-20)

- **35 files** import from `modelviewprojection.mathutils`. Each needs its import line
  split: gacalc names → `from gacalc.<mod> import …`; mvp-local names → keep
  `from modelviewprojection.mathutils import …`.
- Most-used re-exports via the facade: `Vector3` (~13), `Vector2` (~7), `translate` (~4),
  `identity`, plus `Bivector2`/`InvertibleFunction`/`compose`/etc. (audit all 35; the quick
  grep undercounts multi-line imports).
- **The book too.** ch05 etc. show doctests/examples like
  `from modelviewprojection.mathutils import Vector2, translate`. Per Bill's rule, those
  should import gacalc directly as well — and it is now *consistent* with the doc-region
  work, since the book already shows `Vector2`/`translate` **from gacalc's source**.

## Mechanical shape

`from modelviewprojection.mathutils import Vector2, rotate, translate` becomes

```python
from gacalc.g2 import Vector2
from gacalc.transforms import translate
from modelviewprojection.mathutils import rotate  # mvp-local
```

An AST-based rewrite over the 35 files is feasible (split each mathutils import by the
table above), but each file should be eyeballed — some import a name that is mvp-local
*and* gacalc names in one statement.

## Verification

1. `make format` (ruff + ty) clean — no unused imports left behind in `mathutils.py`.
2. Full suite green (container), incl. doctests.
3. Book builds (the example imports still run as doctests where applicable).
4. Grep proof: no remaining `from modelviewprojection.mathutils import <gacalc-name>`
   anywhere; `mathutils.py` no longer imports gacalc names it does not itself use.

## Open questions

1. ~~functions vs transforms for the function layer~~ **DECIDED: `gacalc.transforms`** for
   the whole function/transform layer (Bill, 2026-07-20). See the table note above.
2. **Update the book's example/doctest imports to gacalc too?** Recommend yes (Bill's rule +
   consistency with the doc-region listings), but it changes teaching-facing import lines, so
   confirm.
3. **Keep `MultiVectorBase` re-exported?** It is used as the polymorphic type in several mvp
   signatures; still should import from `gacalc.base` directly per the rule. No exception
   needed — listed only because it is the one name most tempting to keep for brevity.


## Outcome (2026-07-20)

- **34 caller import statements** rewritten across src + tests: gacalc names → their module
  (`gacalc.g2`/`g3`/`base` + `gacalc.transforms` for the function/transform layer), mvp-local
  names kept on `mathutils`.
- **Doctests** (src + book) updated the same way — 4 src files, plus ch05/ch10 examples.
- **`mathutils.py`** `__all__` trimmed to the mvp-local helpers; ruff stripped the 6
  now-unused re-export-only imports (`Vector1`, `identity`, `to_matrix`, `uniform_scale`,
  both `compose_intermediate_fns*`); the internally-used gacalc imports stay. Module docstring
  + comments updated ("NOT a re-export facade").
- **Question 2 (book imports): YES, done** — per Bill's rule.
- **Bonus rot found + fixed in ch10 examples** (they predated the migration and are displayed,
  not doctested, so the rot went unnoticed): `Vector2.e_1()` → `Vector2.e_1` (×8, it is a
  constant not a method), `scale_non_uniform_2d` → `scale_non_uniform` (×4, the real name),
  `.isclose(` → `.is_close(` (×4).
- **One doctest caught the change**: `FunctionStack.modelspace_to_ndc_fn` had relied on the
  module namespace for `uniform_scale` (no import line); added explicit gacalc imports.

**Verified:** 0 facade imports / module-style facade access anywhere (src/tests/book);
suite 96 green (doctests import from gacalc); ruff clean; ty unchanged (11, third-party
stubs); book builds (only the pre-existing `texExpToPng` LaTeX errors remain, unrelated).
