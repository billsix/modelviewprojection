# `mathutils.fn_stack` is a module-level mutable global — research a fix

**Status:** **DONE 2026-07-19 — fixed via F (add the missing top-level `__init__.py`),
in BOTH repos.** The root cause was a packaging omission, not the global itself.
**Created:** 2026-07-19
**Found by:** a doctest that passed under one runner and failed under another (see
Symptom). Not currently biting production code.

## The problem

`mathutils.py` holds a single module-level mutable global:

```python
fn_stack = FunctionStack()          # mathutils.py:521
```

`push_transformation` reads and mutates it implicitly:

```python
@contextlib.contextmanager
def push_transformation(f):
    try:
        fn_stack.push(f)            # <- the global, not a parameter
        yield fn_stack
    finally:
        fn_stack.pop()
```

**A module-level mutable global silently becomes *two* objects if the module is imported
under two different names.** Then one writer and one reader can disagree, with no error:

```
same module object?  False
same fn_stack?       False
depth via A (pushed): 1
depth via B (reader): 0   <-- silently wrong
```

Reproduce:

```python
import sys
import modelviewprojection.mathutils as a
sys.modules.pop("modelviewprojection.mathutils")
import modelviewprojection.mathutils as b
a is b, a.fn_stack is b.fn_stack        # (False, False)
```

Double-import is not exotic. It happens whenever a module is reachable by two names —
`python path/to/mod.py` alongside `import pkg.mod`, a test runner that imports by file
path, `python -m doctest file.py`, a `sys.path` entry pointing inside the package.

## Symptom that surfaced it (2026-07-19)

A doctest for `push_transformation` that read `fn_stack` directly **passed** under
`doctest.run_docstring_examples` and **failed** under both `pytest --doctest-modules` and
`python -m doctest`: the latter two import the file under a second module name, so
`push_transformation` pushed onto one module's `fn_stack` while the example read the
other's, printing `0` where `2` was expected.

**Worked around, not fixed.** The doctest now reads the object the context manager
*yields* (`with push_transformation(...) as stack:`), which does not depend on module
identity. The underlying global is untouched. See `mathutils.push_transformation`.

## Why this is NOT simply "remove the global"

**The global is deliberate pedagogy and it is in the book.** `fn_stack = FunctionStack()`
sits inside the `doc-region define function stack class` region, which ch16
`literalinclude`s. The whole point of `FunctionStack` is to be the Python analogue of
OpenGL's matrix stack — and OpenGL's stack *is* an implicit global you push and pop
against. Making it an explicit parameter would teach a different thing than the API the
chapter is explaining.

**Blast radius, measured 2026-07-19:** 20 direct `fn_stack` references across
`demos/demo16.py` (12), `demo17.py` (4), `demo18.py` (4), plus 17 `push_transformation`
call sites. All teaching-facing.

## Severity: low, and worth stating honestly

- **Nothing in the codebase currently double-imports `mathutils`.** The full suite passes
  (74 tests, container).
- The failure mode is **silent** rather than loud, which is the real argument for fixing
  it — a wrong transform stack renders a subtly wrong image, it does not raise.
- The same fragility class was just fixed for a different global in this repo (the
  plotting `axes`, now a `ContextVar` — see
  `tasks/archive/2026/07/19/plotting-global-axes-design.md`). Consistency is an argument,
  **but the two cases are not identical** — see Option C.

## Options to research

**A. Do nothing; document the constraint.** Add a comment at the definition saying
`mathutils` must never be imported under two names, and why. Cost: zero. Leaves a silent
failure mode armed. Honest if we decide the risk is genuinely negligible.

**B. Make the global canonical via `sys.modules`.** Bind `fn_stack` on first import so a
second import reuses it. Cost: small, ugly, and it fights the language rather than
removing the sharp edge. Probably rejected, listed for completeness.

**C. `ContextVar`, mirroring the `axes` fix.** Same shape as the plotting fix: a private
`ContextVar` plus an accessor. **Caveat that makes this NOT a copy-paste of that fix:**
`axes` had a natural single owner (`create_graphs`) and read-only consumers, whereas
`fn_stack` is *pushed and popped by the very API being taught*, and `FunctionStack` is a
book-visible class. A `ContextVar` also changes semantics under threads/async — arguably
correct, but it is a behaviour change to teaching code, not just a refactor.

**D. Pass the stack explicitly.** The textbook-correct answer, and the one that breaks the
pedagogy: 37 teaching-facing call sites gain a parameter, and the analogy to OpenGL's
implicit stack is lost. Almost certainly wrong for this book — recorded so it is not
re-proposed.

**E. Make the double-import *loud* instead of silent.** Detect at import time that
`mathutils` already exists in `sys.modules` under another name and raise. Cost: small.
Does not remove the global, but converts a silent wrong-render into an immediate error —
which may be the best value-for-effort given severity is low.


## Research findings (2026-07-19, all by experiment)

**Q2 — does any real path double-import `mathutils`? NO.**
- Every import in `src` and `tests` is the canonical `modelviewprojection.mathutils`.
  **No bare `import mathutils` anywhere.**
- `mathutils.py` has **no `__main__` block**, so it is never run as a script.
- The three consumers (`demos/demo16/17/18.py`) all use
  `from modelviewprojection.mathutils import (...)` — the package name, one copy.
- So the bug has **no live trigger in production code.** The only ways to hit it:
  (a) `python -m doctest src/.../mathutils.py` — a dev/test invocation that imports the
  file under a second key; this is exactly how it surfaced, and it is **already worked
  around** (the doctest reads the yielded stack, not the global); (b) a hypothetical future
  bare `import mathutils`.

**Q1 — does option E (loud guard) have false positives? NO. Proven with a prototype:**

| scenario | guard fires? | correct? |
|---|---|---|
| normal single import | no | ✓ |
| `importlib.reload` (replaces in-place, 1 sys.modules key) | no | ✓ |
| real bare-vs-package double import | **yes** | ✓ |

The guard scans `sys.modules` at import time for another module with the same `__file__`
under a different key, and raises `ImportError` if found. It cannot see the *artificial*
`sys.modules.pop` + reimport case (the orphan is no longer in `sys.modules`), but that
path does not occur in practice; it catches the realistic bare-vs-package and
`-m doctest` shapes.

**Placement:** `fn_stack = FunctionStack()` is at line 689, the ch16 book region ends at
line 690, so a guard appended after that (or at end of file) is **outside** the listing —
students never see it.

## Recommendation (firmed after research)

**E — add the loud import guard, ~8 lines, outside the book region.** It is now proven to
work and to have no false positives, it is cheap, and it converts the one nasty failure
mode (a silently wrong transform stack → a subtly wrong rendered image) into an immediate
`ImportError`. The pedagogy objection is fully mitigated by placing it past line 690.

**Honest counter-argument for A (comment only):** there is **no live trigger** today, so E
guards a future foot-gun, not a present bug. If the ~8 lines of defensive code in a
teaching file are unwelcome even when invisible to the book, a comment at the definition
is the minimalist honest alternative. **C (ContextVar) and D (explicit param) stay
rejected** — see above; both perturb the taught API for a bug with no live trigger.

## Implementation of E revealed the truth (2026-07-19) — E is DEAD

Implemented E (the loud import guard) exactly as researched. It **broke the doctest
suite**: 12 of mathutils' 16 doctests failed with the guard's own `ImportError`.

**Why — and it overturns the Q2 research above.** `pytest --doctest-modules` imports
`mathutils.py` under the **bare** name `mathutils` (not `modelviewprojection.mathutils`),
because **the top-level `src/modelviewprojection/__init__.py` is MISSING** — so pytest's
`importmode=prepend` names the module by basename. Each doctest's
`from modelviewprojection.mathutils import ...` is then a **second, canonical** import.
So **pytest double-imports `mathutils` on every run** — it always has; it was harmless only
because no doctest reads the module-global `fn_stack` (they read the yielded object).

My Q2 conclusion ("no path double-imports mathutils") was **wrong**: I grepped source for a
bare `import mathutils` and found none, but the double-import comes from *pytest's import
machinery + the missing `__init__.py*`, not from source. Instrumentation (running the real
gate) found what the isolated prototype could not.

**E cannot work:** the harmless pytest double-import and a harmful one have *identical*
`sys.modules` signatures (`mathutils` + `modelviewprojection.mathutils`), so the guard
cannot distinguish them. E was reverted; the tree is back to green.

## F. Add the missing top-level `__init__.py` — the actual root-cause fix

`src/modelviewprojection/` has **no `__init__.py`**, while every subpackage
(`cayley/`, `util/`, `framebuffer/`) has one — an inconsistency, almost certainly an
oversight. With it added:

- pytest imports `mathutils` as the canonical `modelviewprojection.mathutils` (verified via
  pytest's own `resolve_pkg_root_and_module_name`) — **one copy, no split, the fn_stack
  fragility is gone at the root**, not detected or documented around.
- Full container suite passes (96 tests); `ty` unchanged (11).
- One empty file; consistent with the subpackages.

**Open concern before committing F:** adding `__init__.py` converts `modelviewprojection`
from an implicit namespace package (PEP 420) to a regular package. That could affect
setuptools packaging — **needs a `make dist` / install check** before it lands. It is a
packaging change, so it needs Bill's go-ahead per this task's rules.

## Outcome (2026-07-19)

**F landed in mvp AND gacalc.** Both had **no top-level `__init__.py`** (mvp's
subpackages had theirs; gacalc is flat with none), so `setuptools.find_packages(where=
"src")` returned **`[]`** in both and pytest imported modules under bare names — a
double-import on every run.

- **mvp:** added `src/modelviewprojection/__init__.py`. Suite 96, `ty` 11, wheel builds
  and contains all 66 modules. The double-import that surfaced this whole task is gone
  (pytest now imports `modelviewprojection.mathutils` canonically).
- **gacalc:** added `src/gacalc/__init__.py`. Same structural bug confirmed (`find_packages
  -> []`, bare `base` is not `gacalc.base`). It did **not** bite there — gacalc has no
  mutable module-global singleton like `fn_stack` — but the fix is identical and equally
  correct. Wheel builds through the `build_py` codegen hook (all generated modules +
  `__init__` present); suite 286, `ty` clean.

**No guard, no ContextVar, no comment needed.** The global `fn_stack` stays exactly as
taught; removing the double-import at the packaging root fixes the fragility for real.

**Both `__init__.py` files are uncommitted** (Bill commits). Empty files, matching the
subpackage convention.

## Historical open questions (resolved)

1. **F, E, or A?** — **F** (add `src/modelviewprojection/__init__.py`): removes the
   double-import at the root, fixes the bug rather than guarding it, one empty file, suite
   green. Recommended. **E** is dead (breaks the suite). **A** (comment only) remains the
   do-nothing fallback. Not B/C/D.
2. **F is a packaging change** — run `make dist` + a fresh install to confirm the
   namespace→regular-package switch doesn't break the build, before landing it.
