# 25 book code listings are silently EMPTY — dangling `literalinclude` anchors

**Status:** **substantially DONE 2026-07-20.** Checker done; local mismatches done; gacalc
markers released (0.0.11); **sdist wired into the Docker build and all 42 directives
repointed/resolved.** Book build is green (checker passes, Sphinx has no gacalc-anchor
warnings). Remaining is refinement, not blocking — see "What was done" below.

## What was done 2026-07-20 (the sdist wiring + linking)

**Docker build pulls the gacalc sdist (docs-only):**
- `Dockerfile`: `ARG GACALC_VERSION=0.0.11`; a RUN step fetches the sdist from the PyPI JSON
  API and unpacks its `src/gacalc/*.py` to `/opt/gacalc-src` (docs-only, never imported).
- `entrypoint.sh`: before the book build, copies `/opt/gacalc-src/*.py` into
  `book/docs/_gacalc_src/` (gitignored), then runs `check_doc_regions.py`, then `make html`.
- `requirements.txt`: pinned `gacalc==0.0.11` (the runtime wheel, same version as the source).
- **`_gacalc_src` is gitignored**; the check moved INTO the container (entrypoint + a
  container-based `make check-regions`) because the gacalc source only exists in the image,
  not on the host -- the old host-side `html: check-regions` prerequisite was removed.

**18 of the 21 directives repointed to gacalc regions** (target -> `_gacalc_src/<mod>.py`,
anchor -> gacalc region name; captions -> `gacalc/<mod>.py`):
- Hand-written cluster (clean granularity match): `translate`, `uniform_scale`,
  `InvertibleFunction`, `__call__`, `inverse` -> `functions.py`/`transforms.py` sig/body
  regions. The book already split some into signature+body directives, which lined up with
  gacalc's split exactly.
- Generated: `Vector2`/`Vector3` class -> `Vector2 declaration`/`Vector3 declaration`;
  add/subtract/mul -> the whole `Vector2 __add__`/`__sub__`/`__mul__` method regions.
- All verified rendering real gacalc code in a Sphinx build.

**3 directives had no gacalc equivalent -> removed with a light prose touch-up:**
- ch05 "vector2d basis" / ch14 "vector3d basis": gacalc does not mark basis constants
  (`Vector2.e_1` etc. are post-class assignments); the concept is taught in the surrounding
  prose, so the empty listing was replaced by naming the constants inline. (This is exactly
  the "black-box" treatment the book read recommended for the data types.)
- ch06 "translate test": the test moved to gacalc with the code; reworded the lead-in
  sentence so it no longer references a listing.

### Known imperfections (refinement, not blocking)
- **Generated method sig/body pairs collapsed — FIXED 2026-07-20 (Option 1).** The book
  split `add`/`subtract`/`mul` into a signature + a body directive, but gacalc's generated
  regions are whole-method only, so both pointed at the same region and the method rendered
  twice. Consolidated each pair to a single directive in ch06 (removed 3 duplicate
  `literalinclude` blocks); each method now renders once. (Option 2 -- splitting generated
  methods sig/body in the generator -- was declined: the sig/body split earns its keep for
  the InvertibleFunction cluster, not a dataclass's arithmetic.)
- **`Vector2D` vs `Vector2` naming drift.** The prose still says `Vector2D` in places while
  the now-included gacalc source says `Vector2`. Pre-existing migration tension, not
  addressed here.
- **basis listings dropped** rather than shown -- if a basis listing is wanted back, gacalc
  would need to mark the basis constants (a future release).
- **ch01 "import first module"** still warns in Sphinx -- a pre-existing empty-region issue
  in `demo01.py`, unrelated to gacalc; the substring-based checker does not catch it (it is
  an adjacent begin/end with no lines between).

## Decisions (Bill, 2026-07-19)

1. **Do not fix the 5 name-mismatched anchors ad hoc** — they are part of this task.
2. **Add the anchor checker** (was "option E") — also part of this task.
3. **For the 20 gacalc-moved includes: add `doc-region` markers to gacalc** (DONE, released
   in gacalc **0.0.11**), and have **mvp's Docker build pull the gacalc source into the
   image** so the book can `literalinclude` those markers.
4. **BOTH artifacts are wanted, on purpose — for two different jobs, and BOTH from PyPI:**
   - **PyPI wheel = the runtime dependency** (`requirements.txt`, `gacalc==0.0.11`) — what
     the code imports.
   - **PyPI sdist = the docs-only source** — pulled into the image *purely* so Sphinx has
     real files to `literalinclude`; nothing imports it, it is never on `sys.path`. **A
     wheel is not something `literalinclude` can point at**, but the sdist unpacks to the
     real `.py` files (hand-written *and* generated, markers baked in).

   **UPDATED 2026-07-20 — sdist from PyPI is the primary approach, NOT a GitHub clone**
   (Bill's decision). An earlier draft said "pull a tagged release from GitHub"; that is
   dropped. The sdist gives everything the book needs with **no `git clone`, no generator
   run in the image** (see the Sourcing section). Both wheel and sdist come from the same
   PyPI version, driven by one `ARG GACALC_VERSION`, so the book can never document a
   different version than the code runs.

**Created:** 2026-07-19
**Found while:** splitting doc-regions for `mathutils.py` doctests; a verification pass
over every `literalinclude` in the book turned these up as a pre-existing set.

## The problem

25 `literalinclude` directives name a `doc-region` anchor that **does not exist in the
target file**. Sphinx warns and renders **nothing** — so the chapter has a caption and
surrounding prose explaining code that is simply *not there*. Confirmed by building the
book and inspecting the HTML: no oversized blocks, no error page, just missing listings.

```
book/docs/ch05.rst:94:  WARNING: start-after pattern not found: doc-region-begin define vector2d class
book/docs/ch06.rst:497: WARNING: start-after pattern not found: doc-region-begin define add
book/docs/ch14.rst:127: WARNING: start-after pattern not found: doc-region-begin define vector3d class
...
```

**The build still succeeds** (`build succeeded, 61 warnings`), which is exactly why this
went unnoticed — it is a warning, not an error, and the page renders fine minus the code.

## Scale

| chapter | dangling includes |
|---|---|
| `ch06.rst` | **15** |
| `ch14.rst` | 3 |
| `ch03.rst` | 2 |
| `ch05.rst` | 2 |
| `ch01.rst` | 1 |
| `ch16.rst` | 1 |
| `mathhomework1.rst` | 1 |

`ch06` is the worst: it has **15 dangling includes and only 6 code blocks rendered in
total**. That chapter teaches `__add__` / `__subtract__` / `translate` / the
`InvertibleFunction` class — and shows almost none of it.

## Two distinct causes

**1. The code moved to the `gacalc` repo (20 of 25).** ch05/ch06/ch14/mathhomework1 point
at `src/modelviewprojection/mathutils.py` for `define vector2d class`, `define add`,
`define translate`, `define uniform scale`, `define vector3d class`,
`begin define invertible function`, etc. Those all moved out to **gacalc**, and
`mathutils.py` now merely re-exports them. **gacalc has zero `doc-region` markers** — the
anchors do not exist there either, so nothing can currently be included from it.

**LOCAL MISMATCHES HANDLED 2026-07-20.** The "5 local" turned out to be:
- **ch01 `import first module`** — already resolved (demo01.py has both markers); the old
  Sphinx warning was stale. No change needed.
- **ch03 `square viewport` / `set to gray`** — FIXED. demo03.py had `begin square viewport`
  closed by `end set to gray`; split into the two regions ch03 shows (the function
  signature, then the clear-to-gray lines). Verified the rendered content matches the
  prose.
- **ch16 `function stack examples definitions`** — FIXED. The example the chapter wants is
  `test_function_stack_push_pop` in `tests/test_mathutils.py`, which existed unmarked;
  wrapped it in the region.
- **ch06 `translate test`** — NOT a local mismatch after all. `translate` moved to gacalc
  and its dedicated test went with it, so there is no local code to point at. This is
  **gacalc-blocked** like the other 20, OR needs a decision (point ch06 at gacalc's
  translate test, or drop the directive). Folded into the gacalc-dependent set below.

Checker now reports **42 unresolved** (was 46); the remaining 42 are all gacalc-dependent
(40 moved-to-gacalc + ch06's 2 `translate test`).

**2. Mismatched begin/end names (5 of 25).** ch03 asks for `doc-region-end square
viewport`, but `demos/demo03.py` closes that region with `doc-region-end set to gray`, and
ch03's next include asks for `doc-region-begin set to gray` which is only an *end* marker.
Same class of bug in ch01 and ch16. These are **local and cheap to fix** — the code is
right there, only the anchor names disagree.

## The complication for cause 1

Restoring those listings is not just "add markers in gacalc":

- **`Vector2` / `Vector3` live in `src/gacalc/g2.py` and `g3.py`, which are GENERATED and
  gitignored.** Markers there would have to be emitted by
  `tools/gen_specialized.py`, and the book would be including a file that does not exist
  in a fresh checkout until `make generate` runs.
- **gacalc is a separate repo.** `literalinclude` takes a relative path; reaching a sibling
  `geometricalgebra` checkout (`github.com/billsix/geometricalgebra`) by absolute path is not
  portable for anyone else building the book.
  `translate` / `uniform_scale` (`transforms.py`) and `InvertibleFunction`
  (`functions.py`) are hand-written, so markers are easy — but the *path* problem applies
  to them too.

## Options

**A. Restore by including from gacalc.** Add `doc-region` markers to gacalc's hand-written
modules (and teach the generator to emit them for `g2.py`/`g3.py`), then point the book at
an installed-package path. Highest fidelity — listings auto-sync again. Costs: cross-repo
coupling, a path that must resolve for every reader, and generator work for the
generated classes.

**B. Inline the code into the book as plain `code-block`s.** Hand-copied snippets. Cheap
and portable; loses auto-sync, so the book can drift from the library silently — which is
the failure mode this book has fought before (`book-code-drift-ch7-15.md`).

**C. Rewrite the prose so the chapters teach the concept without showing that source.**
Point readers at gacalc for the implementation. Least churn to the build, most writing.

**D. Delete the dead directives and leave the chapters as-is.** Removes the warnings and
changes nothing visible (they already render nothing). Honest bookkeeping, zero
pedagogical gain — the chapters stay incomplete.

**E. (Orthogonal, do regardless.) Make this failure loud.** A missing anchor must not be a
silent warning. Either build with `-W` for these specific warnings, or add a small
`make check-includes` that greps every `literalinclude` anchor against its target and
exits nonzero. Cheap, and it is the reason 25 of these accumulated unnoticed.

**CHECKER BUILT 2026-07-19 (`tools/check_doc_regions.py`, `make check-regions`).**
Assertions #1 (resolve) and #2 (prefix) are implemented and wired; #3 (content lockfile)
is deferred until the marker-ID scheme is chosen (`emit-doc-region-markers`). The prefix
part is **green** — the 4 live `define rotate` collisions were fixed by renaming the bare
`define rotate` marker to `define rotate 2d` (in `mathutils.py` and its ch07 anchor). The
resolve part is **red on the 46 anchors below** — which is the rest of THIS task (the
dangling includes); `make check-regions` now quantifies them precisely and will go green as
they are fixed.

**Scope grew 2026-07-19 — the checker must assert THREE things, not one.** Two further
failure modes were found by experiment while designing gacalc's marker scheme
(`geometricalgebra/tasks/emit-doc-region-markers.md`):

1. **Anchor resolves** — the original job; catches the 25 empty listings.
2. **No anchor is a PREFIX of another in the same file.** Sphinx matches the first line
   *containing* the anchor text, so `…-magnitude` silently renders the contents of
   `…-magnitude-signature`. Verified with a real Sphinx build: **wrong code, no warning.**
   gacalc's markers avoid this by construction (fixed-length SHA1 slugs cannot be prefixes
   of one another), but mvp's own hand-written markers do not, so the check is still
   needed here.
3. **Region content matches a lockfile** (`anchor -> sha1(region content)`). This is the
   cross-repo drift guard: a pinned gacalc version stops the *version* moving, but nothing
   currently tells the book that the *code inside a published region* changed. A changed
   hash gets reviewed and re-locked deliberately. Prototyped over the 12 real regions in
   `mathutils.py`.

## Sourcing gacalc for the book — findings that change the shape of part 3

Measured 2026-07-19 against the actual image, because the choice of *where* the book reads
gacalc from decides how much work part 3 is.

**mvp already installs a pinned gacalc release, and it already contains the generated
modules.**

- `requirements.txt:3` pins `gacalc>=0.0.10`; the image has **gacalc 0.0.10 from PyPI** at
  `/venv/lib64/python3.14/site-packages/gacalc`.
- That install **includes `g1.py`, `g2.py`, `g3.py`, `scalar.py`** — gacalc's sdist/wheel
  bakes the generated modules in at build time, so they are real files on disk.

**This matters because a GitHub tag and a PyPI release are NOT equivalent here.** The
generated modules are **gitignored** in gacalc, so:

| source | has `g2.py`/`g3.py`? | extra work in the image |
|---|---|---|
| PyPI sdist/wheel (**already installed**) | **yes**, baked in at build | none |
| `git clone --branch v0.0.10` from GitHub | **no** — gitignored | must run gacalc's generator (`make generate`; 𝒢₃ takes ~30s, needs numpy+sympy) |

So a GitHub tag checkout needs a generator run in the image before the book can include
`Vector2`/`Vector3`; the PyPI sdist does not. **DECIDED 2026-07-20: the PyPI sdist**
(see Decision 4 / Open question 1) — it carries the generated code for free, so no git
clone and no generator run in the image.

**Independent of that choice, the markers must be emitted by the generator** for the
generated classes: `g2.py`/`g3.py` are build artifacts, so hand-editing them is always
wrong. Marker emission belongs in `tools/gen_specialized.py`. Markers in
`transforms.py` / `functions.py` (hand-written) are ordinary edits.

### Is "wheel for runtime, source for docs" clean? — assessment

**Yes, with one condition.** Separating the two is standard and sound: the wheel is a
build artifact for *importing*, the repo is the source of truth for *reading*. Sphinx
cannot include code out of an installed wheel in any readable way, so the book needs a
real source tree regardless.

**The condition: one version string must drive both.** Otherwise the book documents a
different version than the code runs, silently — the exact failure class this whole task
exists to fix. Today `requirements.txt:3` says `gacalc>=0.0.10`, a **floor, not a pin**, so
pip may install 0.0.11 while the Dockerfile clones `v0.0.10` and the book teaches the old
code. **Fix: pin `gacalc==<X>` and derive the git tag from that same `<X>`** (a single
`ARG GACALC_VERSION` in the Dockerfile feeding both the pip pin and the `git clone
--branch v$GACALC_VERSION`). With that, the arrangement is clean.

**One gacalc-specific wrinkle to design around:** a **git tag has no `g2.py`/`g3.py`** —
they are generated and gitignored. `Vector2`/`Vector3` are exactly what ch05/ch14 want to
show, so the git route needs a generator run in the image (`make generate`; ~30s for 𝒢₃,
needs numpy+sympy), and its output must match what the installed wheel contains. gacalc's
existing `make check-generated` determinism guard is what makes that safe to rely on.

**The PyPI *sdist* is a source tarball that already contains everything — VERIFIED
2026-07-19.** Fetched `gacalc-0.0.10.tar.gz` (84 kB) straight from the PyPI JSON API and
listed it:

```
base.py  functions.py  g1.py  g2.py  g3.py  gn.py  nbplotutils.py  scalar.py  transforms.py
```

**Both halves are there: the hand-written modules (`transforms.py`, `functions.py`,
`base.py`) AND the generated ones (`g1.py`, `g2.py`, `g3.py`, `scalar.py`).** So the sdist
gives readable source, at an exactly-pinned version, **with no generator run needed** —
gacalc's build bakes the generated modules in, exactly as its `CLAUDE.md` claims.
(`tools/` is *not* shipped, which is fine: nothing needs to regenerate.)

This is worth weighing against the git-clone route recorded in decision 4, because it is
strictly less machinery for the same result:

| | git clone `v<X>` | PyPI sdist `==<X>` |
|---|---|---|
| hand-written source | yes | yes |
| generated `g2.py`/`g3.py` (ch05/ch14 need these) | **no** — gitignored | **yes**, baked in |
| generator run in the image | **required** (~30s 𝒢₃, needs numpy+sympy) | none |
| version identical to the installed wheel | same tag, rebuilt | **same release artifact** |

**It does not contradict decision 4** — it is still "source acquired separately from the
runtime wheel", which was the actual requirement. It only changes *where* the source comes
from. **Caveat, and the reason this is not a unilateral call:** the sdist is a published
artifact, not the git history — if the intent is for the book to track the repo (e.g. to
show something `tools/` generates, or to build docs from an unreleased commit), the git
clone is the right answer despite the extra step.

**One caveat on fetching it:** plain `pip download --no-binary :all:` **hangs building
metadata** (it tries to install build deps). Fetch the tarball directly from the PyPI JSON
API instead — that is how this was verified.

**One unsolved detail for either route:** Sphinx `literalinclude` takes a path relative to
the `.rst` (a leading `/` means relative to the source dir), so pointing at
`/venv/lib64/.../site-packages/gacalc/` or a `/gacalc` checkout is not portable. Likely
needs a build step that copies or symlinks the gacalc source into the docs tree, or a
`conf.py` hook. **Needs a spike before committing to the design.**

## Recommendation / plan (updated 2026-07-20)

1. **Anchor checker — DONE.** `tools/check_doc_regions.py` + `make check-regions`, wired
   into the book build so a broken anchor now halts it loudly.
2. **The 5 "local mismatches" — DONE.** ch01 was already fine; ch03 + ch16 fixed; ch06's
   `translate test` turned out to be gacalc-moved (not local). Count 46 → 42.
3. **gacalc markers — DONE, released in 0.0.11.**
4. **Remaining, and it needs one decision from Bill:** the white/black-box call — which of
   the 42 gacalc-moved includes to **white-box** (include the source from the sdist) vs
   **black-box** (replace the directive with a sentence + a pointer to gacalc). The book
   read (see `tasks/archive/.../` and the ch06 analysis) points to: white-box the ch06
   `InvertibleFunction` cluster (`translate`, `uniform_scale`, `InvertibleFunction` /
   `__call__` / `inverse` — the course narrates this code); black-box the ch05/ch14 data
   types (`Vector2`/`Vector3`, add/subtract/mul — the author already says "don't stress
   about the implementation").
5. **Then the mechanics:** pin `gacalc==0.0.11`, add `ARG GACALC_VERSION` driving both the
   pip pin and the **sdist** source-pull into the image, wire the sdist source into the
   docs tree so `literalinclude` can reach it, and repoint (white-box) or delete
   (black-box) each of the 42 directives. Checker/book build then goes green.

## Open questions

*(Question 1 RESOLVED 2026-07-20 — sdist from PyPI, no GitHub. See below.)*

1. ~~How does the image obtain the gacalc source — git clone or PyPI sdist?~~ **DECIDED
   (Bill, 2026-07-20): the PyPI sdist.** `pip download --no-binary :all:
   gacalc==$GACALC_VERSION` (or a direct fetch from the PyPI JSON API) unpacks to the full
   source — hand-written *and* generated modules, markers baked in — with **no `git clone`
   and no generator run in the image**. The only things a GitHub clone would add (git
   history, branches, `tools/`, tests) are things the book does not need for
   doc-referencing. Verified against the 0.0.10 sdist; 0.0.11 (the marker release) confirmed
   to carry the markers.
2. **How should the book reach the gacalc source?** `literalinclude` paths are relative to
   the `.rst`. Copy/symlink gacalc's source into the docs tree at build time, or a
   `conf.py` hook? Needs a spike.
3. **Pin exactly?** `requirements.txt` currently says `gacalc>=0.0.10` (a floor, not a
   pin). With the book's listings coming from a pinned git tag, a floating runtime pin
   means **the book and the code can be different versions** with nothing to catch it.
   Recommend a single `ARG GACALC_VERSION` driving both the `gacalc==` pin and the
   `v$GACALC_VERSION` tag — see the assessment section. This is the one thing that makes
   the two-source design safe rather than drift-prone.
