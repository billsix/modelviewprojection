# Plan: migrate Sphinx LaTeX (`.. math::` + `:math:`) to inlinetex

**Status:** ✅ **done 2026-05-10.** All three phases landed and verified.
- Phase 1: `inlinetex_role` added to `book/docs/_ext/inlinetex.py`. Calls
  `docutils.utils.unescape(text, restore_backslashes=True)` to recover
  backslashes that docutils consumes during inline-text parsing —
  without this, `\times` arrived as `\x00times` and texExpToPng errored
  out, marking the role as `class="problematic"` in HTML output. Bug
  caught and fixed during the post-build eyeball.
- Phase 2: 44 `.. math::` blocks migrated across ch04, ch06, ch07, ch09,
  ch10, ch16, perspective.rst. Heuristic wrap rules: bare single-line
  → `$ ... $`; `\begin{split}` → wrapped in `equation*`; multi-paragraph
  → joined into `align*` rows; `&`-aligned multi-line → `align*`; other
  multi-line → `\[...\]`.
- Phase 3: 84 `:math:` inline roles → `:inlinetex:` across mathhomework1,
  perspective, ch07, ch02 (mechanical regex replacement).

## Why

EPUB output of the book renders `.. math::` and `:math:` (Sphinx's
standard LaTeX, served via mathjax/imgmath) incorrectly — that is the
original reason the texExpToPng pipeline exists. With the
`plans/sphinx-inline-tex-extension.md` work landed (ch02 migrated, both
phases done 2026-05-10), the same machinery can be used for the rest of
the chapters. End state: zero `.. math::` directives or `:math:` roles in
`book/docs/*.rst`; everything goes through the texExpToPng path that's
known to render correctly in EPUB.

## Inventory (2026-05-10)

```
.. math:: blocks (43 total)
  perspective.rst  14
  ch07.rst         12
  ch16.rst          6
  ch06.rst          3
  ch09.rst          3
  ch10.rst          3
  ch04.rst          2

:math: inline roles (84 total)
  spread across ch07, mathhomework1, ch02, perspective, others
```

## Phases

### Phase 1 — extend the extension with an inline role

The existing `inlinetex` directive is block-only. Inline `:math:` use
needs a *role*, which emits an inline-image node so it flows with
surrounding paragraph text.

Add to `book/docs/_ext/inlinetex.py`:

```python
def inlinetex_role(name, rawtext, text, lineno, inliner,
                   options=None, content=None):
    # Wrap inline content in $...$, hash, render via texExpToPng,
    # emit nodes.image with classes=['inlinetex-inline'].
```

Wire via `app.add_role("inlinetex", inlinetex_role)` in `setup()`.

Rendering details:
- Always wraps the role content in `$ ... $` (inline math context).
- Same hash strategy as the directive (sha1 of normalized `$ ...
  $`-wrapped content + size); identical inline expressions dedupe; an
  inline `$ x $` and a block `$ x $` end up at the *same* hash because
  the bytes fed to texExpToPng are identical — that's fine, the same
  PNG fits both contexts.
- Default size remains `inlinetex_default_size` (300). If inline images
  read too large against body text, add CSS in `_static/custom.css`
  (`.inlinetex-inline { vertical-align: middle; height: 1.2em; }`) — do
  this only if it actually looks wrong; don't preempt.

Smoke test: add 2-3 `:inlinetex:` examples to one existing chapter
(e.g., a sentence in `intro.rst`) and confirm rendering before mass
migration. Delete the smoke-test sentence afterward.

### Phase 2 — migrate `.. math::` blocks (43 sites)

Mechanical, but with a wrapping heuristic:

| Body shape | Wrap in `.. inlinetex::` body as |
|---|---|
| Single line, no `&` or `\\` | `$ <content> $` |
| Has `&` or `\\` (align/multi-row) | `\vbox{\n  \begin{align*}\n<indented body>\n  \end{align*}\n}` |
| Already starts with `\begin{` (matrix etc.) | wrap in `$ ... $` (math mode) |

Pattern matches the existing ch02 convention (`ch02_math_06.tex`,
`_08`, `_09`, `_11`, `_21` use `\vbox{ \begin{align*} ... \end{align*}
}`; the rest use `$ ... $`).

Approach:
1. Hand-migrate one block from each shape group (single-line, align,
   bmatrix-heavy) and confirm the rendered PNG matches the prior Sphinx
   math rendering well enough.
2. Then run a one-shot Python script over the remaining 40 blocks.
3. Build, eyeball each migrated chapter.

Affected files: `ch04.rst`, `ch06.rst`, `ch07.rst`, `ch09.rst`,
`ch10.rst`, `ch16.rst`, `perspective.rst`.

### Phase 3 — migrate `:math:` inline roles (84 sites)

Pure regex replacement: `` :math:`<expr>` `` → `` :inlinetex:`<expr>` ``.
No content transformation; the role does the `$ ... $` wrapping
internally.

Verify on `mathhomework1.rst` (21 sites — the highest-volume single
file) before bulk migration. Confirm visual parity across at least one
block-of-text where multiple inline expressions are dense.

## Open questions

- **Build cost.** First build after Phase 2+3 will trigger ~120 new
  texExpToPng invocations. Each runs `latex + dvipng` so the first
  build adds maybe 2-5 minutes. After that, hash-cached. Acceptable.
- **Inline alignment.** Until we see actual EPUB and HTML output,
  unclear whether default size (300) and zero CSS will look right
  inline. Don't preempt; fix only if it looks wrong.
- **Roles inside other roles.** `:math:` is sometimes used inside
  parenthetical phrases or near punctuation; the inline-image
  replacement should flow naturally. Worst case: add a tiny CSS
  margin.

## Out of scope

- MyST notebook math in `.ipynb` files (different rendering pipeline,
  notebook output is image-embedded already).
- Math in `glossary.rst` term definitions (none currently).
- The 35 `.dot`-embedded LaTeX images (Cayley graph node labels) —
  those go through graphviz, not Sphinx, and remain on the
  `_static/Makefile` pipeline.

## Files touched (estimated)

| Path | Change |
|---|---|
| `book/docs/_ext/inlinetex.py` | + ~40 lines for role |
| 7 chapter `.rst` files | 43 block replacements |
| Multiple `.rst` files | 84 inline replacements |
| `book/docs/_static/inlinetex/` | ~120 new hashed PNGs |

Estimated effort: ~3 hours including verification builds.
