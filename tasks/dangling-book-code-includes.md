# 25 book code listings are silently EMPTY — dangling `literalinclude` anchors

**Status:** proposed — **direction DECIDED by Bill 2026-07-19, not started.** All three
parts below live in this one task; nothing has been changed yet.

## Decisions (Bill, 2026-07-19)

1. **Do not fix the 5 name-mismatched anchors ad hoc** — they are part of this task.
2. **Add the anchor checker** (was "option E") — also part of this task.
3. **For the 20 gacalc-moved includes: add `doc-region` markers to gacalc**, and have
   **mvp's Dockerfile pull a tagged gacalc release from GitHub into the image**, so the
   book generates its listings from those markers.
4. **Clarified 2026-07-19 — BOTH sources are wanted, on purpose, and this is not a
   contradiction:**
   - **PyPI wheel stays the runtime dependency** (`requirements.txt`) — what the code
     imports.
   - **The SOURCE is acquired separately from GitHub at the same tag** — because the book
     needs readable source files with `doc-region` markers, and **a wheel is not something
     `literalinclude` can point at**.

   An earlier draft of this doc framed these as competing options ("GitHub tag *or* PyPI
   artifact?"). That was a misreading: they serve two different jobs — runtime import
   versus documentation input — and wanting both is the correct design, not a redundancy.

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
- **gacalc is a separate repo.** `literalinclude` takes a relative path; reaching
  `/foo/opt/geometricalgebra/src/...` is not portable for anyone else building the book.
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
`Vector2`/`Vector3`; the PyPI artifact does not. **Either satisfies "pull a tagged
release" and both are version-pinned** — the git tag gives the repo (markers in
hand-written files land directly), the PyPI artifact gives generated code for free.
**Worth confirming with Bill which he intended**, since he said "from github" — see Open
questions.

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

## Recommendation

**Do the anchor checker first, then the 5 mismatches, then the gacalc work.**

1. **E — the anchor checker.** Whatever is decided about content, the book should never
   again silently drop a listing. This is a small script and it pays for itself
   immediately.
2. **Cause 2 (5 includes: ch01, ch03, ch16) — just fix them.** The code exists, only the
   anchor names disagree; this is a mechanical, low-risk fix that restores 5 listings.
3. **Cause 1 (20 includes) is a pedagogy decision, not a technical one** — it is really
   the question "now that the vector math lives in gacalc, should this book still show its
   source?". I lean **A for the hand-written pieces** (`translate`, `uniform_scale`,
   `InvertibleFunction` — genuinely part of the course's argument) and **C for the
   generated classes** (`Vector2`/`Vector3` are generated code; showing the generated
   source is arguably worse teaching than describing the interface). But this needs Bill.

## Open questions

*(Question 1 is RESOLVED — see decision 4: both sources, for two different jobs.)*

1. **How does the image obtain the gacalc SOURCE — `git clone --branch v<X>` plus a
   generator run, or the PyPI sdist?** **Now measured** (see the assessment section): the
   sdist contains the hand-written *and* generated modules, so it needs **no generator
   run**, while a git clone does. Both satisfy decision 4 ("source, separately from the
   runtime wheel"). Recommend the **sdist** on simplicity — unless the book should track
   the *repo* rather than a published release, in which case git is right despite the
   extra step. **Bill's call; he asked for github specifically.**
2. **How should the book reach the gacalc source?** `literalinclude` paths are relative to
   the `.rst`. Copy/symlink gacalc's source into the docs tree at build time, or a
   `conf.py` hook? Needs a spike.
3. **Pin exactly?** `requirements.txt` currently says `gacalc>=0.0.10` (a floor, not a
   pin). With the book's listings coming from a pinned git tag, a floating runtime pin
   means **the book and the code can be different versions** with nothing to catch it.
   Recommend a single `ARG GACALC_VERSION` driving both the `gacalc==` pin and the
   `v$GACALC_VERSION` tag — see the assessment section. This is the one thing that makes
   the two-source design safe rather than drift-prone.
