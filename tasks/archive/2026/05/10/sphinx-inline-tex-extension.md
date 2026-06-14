# Plan: Sphinx extension for inline LaTeX → PNG

**Status:** ✅ **done 2026-05-10.** Both phases landed and verified
end-to-end on a clean Sphinx build:
- Phase 1: extension at `book/docs/_ext/inlinetex.py`, wired into
  `conf.py`, smoke-test page exercised cache invalidation and dedup.
- Phase 2: 22 `ch02_math_NN.tex` figures migrated to inline `..
  inlinetex::` blocks in `ch02.rst`; Makefile's `cayleyImages` list
  trimmed; orphan `.tex` files git-rm'd. Clean build produced 23 unique
  hashed PNGs and HTML succeeded with the same 34 pre-existing warnings.
- Smoke-test page (`book/docs/inlinetex_smoketest.rst` + its index.rst
  entry) removed after verification — ch02 itself now exercises the
  directive heavily, so the sandbox is no longer load-bearing.

## Goal

Let chapter authors write LaTeX expressions *inline in `.rst`* and have the
Sphinx build call the existing `texExpToPng` tool to render each expression
into a PNG, then emit a normal `image`/`figure` node referencing the
generated file.

End state — author writes:

```rst
.. inlinetex::
   :align: center
   :class: no-scale

   $ f_{nickel}^{penny}(x) = 5 \times x $
```

…and Sphinx renders the same image that today requires a hand-maintained
`_static/ch02_math_01.tex` plus an entry in `_static/Makefile`'s `cayleyImages`
list.

## Why this beats the current setup

Current pipeline (see `book/docs/_static/Makefile`):
1. Author creates `_static/foo.tex` with the LaTeX.
2. Author adds `foo.png` to either `graphs:` or `cayleyImages:` in the
   `_static/Makefile`.
3. `make` runs `texExpToPng --file foo.tex --size 300 --output foo.png`.
4. Author writes `.. figure:: _static/foo.png …` in the chapter `.rst`.

That's four touchpoints per equation, two of which are bookkeeping
(making up a unique filename, remembering to add it to the Makefile list).
For the 22 `ch02_math_NN` direct-use images this is tolerable; for any new
chapter that wants similar treatment it's a wall.

The extension reduces this to one touchpoint: write the LaTeX in the `.rst`.
Filenames are content-hashed (so identical expressions dedupe automatically
and there are no naming collisions), and the Makefile no longer needs a
hand-maintained list for these.

**Out of scope of this proposal:** the Cayley-graph PNGs currently embedded
in `.dot` files (`p1ToNDC`, `cToW`, etc., 35 of them). Those go through
graphviz, not directly into Sphinx, so they keep their current `.tex` files
and Makefile entries. This extension only replaces the 22 direct-use cases
(today's `ch02_math_NN` series) and any future direct-use equations.

## Design

### The directive

Name: `inlinetex` (lowercase, single word — matches Sphinx convention).

Body: the LaTeX expression, exactly as it would appear in the current
`.tex` files (i.e., wrapped in `$ … $` for `texExpToPng`).

Options (subset of `.. figure::` options, passed through to the emitted
node so existing styling continues to work):
- `:size:` — int, default 300. Forwarded to `texExpToPng --size`.
- `:align:` — left | center | right
- `:alt:` — alt text
- `:class:` — CSS class (e.g., `no-scale`)
- `:figclass:` — applied if we emit a figure wrapper
- `:caption:` — optional; if present, emit a `figure` node, else a bare
  `image` node. (Caption-less is the ch02 pattern.)

Implementation: subclass `docutils.parsers.rst.Directive`. In `run()`:
1. Read the directive content (the LaTeX body).
2. Compute the output filename (see below).
3. If the file does not exist, generate it via `texExpToPng`.
4. Build a docutils `image` node (or `figure` wrapping `image`) pointing at
   the generated path, copy through the relevant options, return it.

### Filename strategy (hash-based)

```
_static/inlinetex/<sha1(content + size).hexdigest()[:12]>.png
```

- SHA-1 truncated to 12 hex chars is comfortable: ~2^48 hashes before any
  realistic collision risk for a few hundred equations.
- Hash includes `size` so two callers requesting different sizes for the
  same LaTeX get different files.
- Hash input is the *normalized* content string (strip leading/trailing
  whitespace, collapse internal whitespace runs to a single space) so that
  cosmetic indentation changes in `.rst` don't bust the cache.
- Filename is opaque — never grep'd by humans. The directive logs
  `<expression>` → `<hash>.png` mappings if you want to debug.

### Where PNGs live

`book/docs/_static/inlinetex/` — a new subdirectory, isolated from the
hand-managed `_static/*.tex` and `_static/*.dot` files. Sphinx picks it up
automatically because `_static` is already in `html_static_path`.

Add `_static/inlinetex/` to `.gitignore` so generated PNGs don't pollute
`git status`. The cache is regenerated on demand at build time, so it's
safe to wipe.

### When generation runs

Inside `Directive.run()` itself — synchronous, on the first encounter of a
new hash. Reasons:
- Simple to implement (no `builder-inited` hook, no env collection).
- Build feedback is local: a failing LaTeX expression fails *that
  directive*, not "later, somewhere."
- Sphinx already parallelizes file reads across workers; per-equation
  cost is bounded by `texExpToPng` startup, which we'd pay anyway.

If perf becomes an issue, swap to a two-phase model later (collect during
read, generate in `builder-inited`). Don't optimize prematurely.

### Caching

The cache *is* the on-disk PNG. Skip the subprocess if the target file
already exists; otherwise run `texExpToPng`. No metadata sidecars, no
Makefile timestamps to reason about — the hash *is* the cache key, and a
hash-named file existing means it's already correct.

To force regeneration, delete `_static/inlinetex/` (or just the offending
file). To bust the cache for a specific equation, edit the LaTeX (the hash
changes, a fresh file is generated, the old file becomes garbage —
periodic `make clean-inlinetex` target can sweep it).

### Error handling

If `texExpToPng` exits non-zero, raise `self.severe("texExpToPng failed
on expression: …\nstderr: …")` so the build fails loudly with the actual
LaTeX text in the error. Don't fall back to silently-broken images.

If `/usr/local/bin/texExpToPng` isn't on `$PATH` at all (e.g., someone's
trying to build outside the container), emit a single warning at
`builder-inited` listing how to install it. The directive then no-ops to
a `[texExpToPng unavailable: <expr>]` literal block so the build still
finishes.

## Phased execution

This plan is **two phases**, with a hard boundary in between. Phase 1 lands
the extension without touching any existing chapter output; Phase 2
migrates ch02 onto the new mechanism. Verify Phase 1 (HTML output, build
performance, cache behavior) before starting Phase 2 — don't bundle them
into a single PR.

```
Phase 1 (extension + smoke test) ─── verify ──→ Phase 2 (migrate ch02_math_NN)
                                         ↑
                                   bail-out point: if rendered output
                                   doesn't match the existing PNGs or
                                   the inline .rst form reads worse,
                                   stop here. Phase 1 still earns its
                                   keep for new equations.
```

### Phase 1 — land the extension (no chapter regressions possible)

1. **Scaffold the extension.** Create `book/docs/_ext/inlinetex.py` with
   the standard `setup(app): app.add_directive('inlinetex', InlineTex)`
   shape. (Directory is a sibling of `conf.py` — the existing
   `sys.path.insert(0, os.path.abspath("."))` in `conf.py` makes a
   `_ext/` import work without further setup, but explicit is better:
   add `sys.path.insert(0, os.path.abspath("./_ext"))` at the top.)

2. **Implement the directive.** ~80 lines. Key pieces:
   - `has_content = True`, `final_argument_whitespace = True`.
   - `option_spec` with the figure-style options listed above.
   - Hash → path computation, idempotent generation guard, `subprocess.run`
     calling `texExpToPng --file <tmp> --size <N> --output <path>`. (Write
     content to a `tempfile.NamedTemporaryFile(suffix='.tex')` so we
     don't depend on the `--expr` flag — the existing `--file` flag is
     proven and matches the Makefile rule.)
   - Build `nodes.image` (uri = `_static/inlinetex/<hash>.png`,
     `alt = options.get('alt', content)`), wrap in `nodes.figure` only
     when `:caption:` was given.

3. **Wire into `conf.py`.** Append `"inlinetex"` to `extensions`. The
   existing `html_static_path = ["_static"]` already covers the new
   subdirectory; no other config change.

4. **Update `.gitignore`.** Add `book/docs/_static/inlinetex/`.

5. **Smoke test.** Add ONE `.. inlinetex::` block in `intro.rst` or
   `miscellany.rst`. Build the docs (`make html`). Verify:
   - `_static/inlinetex/<hash>.png` was created.
   - The HTML page renders the image.
   - A second build doesn't regenerate the file (mtime unchanged).
   - A change to the directive content produces a new hash, new file.

**Phase 1 done when:** smoke-test block renders correctly and the cache
behavior is confirmed. None of the existing 22 `ch02_math_NN` figures
have been touched, none of the existing `.tex` files or Makefile entries
have changed.

### Verification gate (before Phase 2)

Before migrating ch02, side-by-side compare one `ch02_math_NN.png` (built
the old way via `_static/Makefile`) against the same expression rendered
through `.. inlinetex::`:

- Image dimensions / DPI match (or at least look indistinguishable in the
  rendered HTML).
- Antialiasing / font rendering match.
- File size is in the same order of magnitude.

If any of those diverge enough to be visible on the page, fix them in the
extension (likely a missing `texExpToPng` flag) before Phase 2. If the
inline `.rst` form turns out to be harder to read in source than separate
`.tex` files, **stop here** — Phase 1 still pays for itself on new
equations and the existing ch02 setup keeps working untouched.

### Phase 2 — migrate ch02_math_NN (mechanical, reversible)

6. **Migrate ch02.** Replace each `_static/ch02_math_NN.tex` + `.. figure::
   _static/ch02_math_NN.png` block in `ch02.rst` with an inline
   `.. inlinetex::` block carrying the same LaTeX content.

7. **Trim the Makefile.** Drop all 22 `ch02_math_NN.png` entries from
   `_static/Makefile`'s `cayleyImages` list. The `%.png: %.tex` pattern
   rule itself stays — the 35 dot-embedded equations still need it.

8. **Delete the orphan `.tex` files.** `git rm
   book/docs/_static/ch02_math_{01..22}.tex`. (And the now-stale
   `ch02_math_NN.png` files in `_static/`, since the new ones live under
   `_static/inlinetex/<hash>.png`.)

9. **Verify.** Build docs, eyeball ch02. If anything looks off, `git
   revert` of the Phase 2 commit fully restores the old setup — Phase 1's
   extension is untouched.

**Phase 2 done when:** ch02 renders identically to before, no
`ch02_math_NN.tex` files remain, the Makefile's `cayleyImages` list is 35
entries shorter.

## Open questions

- **Math role vs. directive?** A custom *role* (`:tex:` …) would let
  authors write inline `:tex:`$f(x)=…$`` `` mid-sentence. Worth doing,
  but a second iteration — needs the role to emit an inline-image node
  and tune sizing for inline use. The block directive is the higher-value
  piece.
- **Should we let `:size:` default come from `conf.py`?** E.g.,
  `inlinetex_default_size = 300`. Cheap to add. Probably yes for symmetry
  with `imgmath_font_size`.
- **Dark-mode rendering.** Furo theme has dark mode; `texExpToPng`
  presumably outputs black-on-transparent. Unrelated to this extension
  (the existing `_static/*.png` files have the same property), but worth
  noting if Bill ever wants dark-mode-aware equations.
- **Container assumption.** Plan assumes builds happen inside the
  modelviewprojection container where `texExpToPng` is at
  `/usr/local/bin/`. If RTD builds need to work, we'd need to either
  install `texExpToPng` there or have a fallback (e.g., `imgmath`).
  Currently `on_rtd` is detected in `conf.py` but unused — a short
  branch (`if on_rtd: skip texExpToPng, fall back to imgmath`) handles
  this.

## Out of scope

- The 35 `.dot`-embedded equations (`p1ToNDC`, `cToW`, etc.). Graphviz
  references them by filename inside `<IMG SRC="…"/>` HTML labels — that
  workflow stays as-is.
- gnuplot plots and `generate_plots_for_book` SVGs.
- Replacing `imgmath` / `mathjax` for the `:math:` role. Different use
  case (rendered MathJax in HTML, no PNG file).

## Files touched (estimated)

| Path | Change |
|------|--------|
| `book/docs/_ext/inlinetex.py` | NEW (~80 lines) |
| `book/docs/conf.py` | +2 lines (`sys.path` + `extensions` append) |
| `.gitignore` | +1 line |
| `book/docs/intro.rst` (or other) | +1 smoke-test block |
| `book/docs/_static/Makefile` | unchanged in step 4; trimmed in step 5 |

Estimated effort:
- **Phase 1:** ~2 hours including the smoke test.
- **Verification gate:** ~15 min (one side-by-side render comparison).
- **Phase 2:** ~30 min, mechanical (mostly find/replace in `ch02.rst` and
  deletion of files / Makefile entries).
