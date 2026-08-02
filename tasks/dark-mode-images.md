# Dark-mode-friendly images for the furo HTML book

**Status:** research complete — **direction decided (best fidelity)**, implementation not started
**Created:** 2026-08-02

## Decision (Bill, 2026-08-02): best fidelity

Go with **proper dual light/dark assets**, not the CSS-invert approximation. That means
option **A** (furo `only-light`/`only-dark`) applied to *all* generated images, including
dual-rendering the colored matplotlib/gnuplot plots with a dark style — accept the higher
effort (dual generation + wiring both variants into the directives, or an automation layer)
in exchange for correct dark renders. The CSS-`invert` route (option B) is **not** the
chosen path; it stays documented below only as the rejected cheaper alternative. Photos are
still excluded (option D's photo handling: a light matte/border, no per-photo dark
variants — unless a specific photo warrants one). Implementation is a separate future
effort; this task now scopes *that* work.

Reference: the image toolchains this task restyles are documented in
`tasks/reference/book-figures-and-images.md` (texExpToPng math, matplotlib
`generate_plots.py`, graphviz `dot`, `inlinetex`).

## Goal / problem (Bill)

The furo HTML theme renders in **light or dark** mode (follows the browser's
`prefers-color-scheme`). In **light** mode the generated images blend in fine. In **dark**
mode the images have a **white background with black text/lines**, so they show as a harsh
white box with dark content against furo's dark page (whose body text is white). Make the
images look right in dark mode too — or determine whether that's feasible.

## Current state (findings, 2026-08-02)

- **Image inventory referenced by the book:** 73 PNG, 57 SVG, 2 JPG, 1 GIF.
- **Where they come from:**
  - **Generated, monochrome line-art (the easy wins):**
    - `_static/*.tex` → **36 texExpToPng math PNGs** (display math figures).
    - `_static/*.dot` → **29 graphviz PNGs** (Cayley graphs etc.).
    - **Inline math** via the `:inlinetex:` role — many small PNGs embedded throughout the
      prose (`_ext/inlinetex.py` calls `texExpToPng` with **no `--fg`/`--bg`**, so they use
      texExpToPng's defaults — black content, and they are *not* covered by the current CSS
      hack below, so they're already a dark-mode problem in prose, not just the figures).
  - **Generated, colored:** matplotlib **SVGs** from
    `src/modelviewprojection/plotsforbook/generate_plots.py`
    (`fig.savefig(..., format="svg")` with **no `facecolor`/`transparent`**, so a white
    background + black axes are baked into the SVG); plus gnuplot `rotate*.svg`.
  - **Real photos / screenshots (must NOT be inverted):** ~35 under
    `_static/screenshots/`, plus licensed photos/diagrams under `_static/cc0/…`,
    `_static/ccbysa*/…` (Wikipedia images, `depthbuffer.jpg`, `Animhorse.gif`, …).
- **The current workaround IS the problem.** `book/docs/_static/custom.css` is three lines:
  ```css
  svg, img[src$=".svg"] { background-color: white !important; }
  ```
  It forces a white background behind every SVG so the black content is visible — which is
  exactly the "white box in dark mode" you're seeing. It also only targets SVGs, so the
  math/graphviz **PNGs** aren't even handled.

## Feasibility verdict

**Feasible.** Every generated image comes from a script we control (texExpToPng,
graphviz `dot`, matplotlib), so we can restyle or dual-generate them; the photos are the
only images we can't restyle, and those are a minority we simply exclude. The realistic
question is *which* approach — a cheap CSS filter vs. proper dual light/dark assets — trading
effort against fidelity on the *colored* plots.

## Options

### A. Furo's native `only-light` / `only-dark` dual images (highest fidelity)
Furo officially supports two copies of an image, shown per theme:
```rst
.. image:: foo-light.svg
   :class: only-light
.. image:: foo-dark.svg
   :class: only-dark
```
- **Pros:** correct, purpose-built dark renders (real dark styling, not a filter); works
  for colored plots and even photos (if you make dark variants).
- **Cons:** must **generate a dark variant of every generated image** (matplotlib dark
  style, texExpToPng/`dot` with light fg on transparent), *and* edit **~130 `image`/`figure`
  directives** to emit both variants — or build an automation layer/custom directive to do
  it. High effort. Photos would still need hand-made dark variants or get left alone.

### B. CSS `filter` invert in dark mode, scoped to line-art (cheapest)
Replace the white-bg hack with a dark-mode rule that inverts monochrome content:
```css
@media (prefers-color-scheme: dark) {
  /* or scope via furo's [data-theme="dark"] */
  .book-invertible { filter: invert(1) hue-rotate(180deg); background: transparent; }
}
```
- **Pros:** ~1 hour. **Monochrome math (texExpToPng, inline + display) and graphviz line
  diagrams invert perfectly** — black becomes white on the dark page, no white box.
- **Cons:** **colored matplotlib plots** invert imperfectly (`hue-rotate(180deg)`
  approximates the original hues but isn't exact); **photos/screenshots must be excluded**
  (an inverted photo looks like a film negative). Needs a way to tag which images are
  "invertible" — a CSS class (cleanest, but touches directives) or a selector that excludes
  the `screenshots/` + `cc*/` paths (no directive edits, but path-fragile).

### C. Regenerate with transparent background + theme-neutral colors (medium)
`savefig(transparent=True)` + mid-gray axes/text; texExpToPng with a neutral fg; a color
that reads on both light and dark.
- **Pros:** one asset per image; no per-theme switching.
- **Cons:** compromises contrast on *both* themes (gray is never as crisp as black-on-light
  or white-on-dark); still needs regeneration of all generated images.

### D. Hybrid (recommended)
- **Monochrome generated images** — texExpToPng math (inline + the 36 display) and the 29
  graphviz PNGs: **CSS invert in dark mode** (option B). Perfect result, trivial effort.
- **Colored matplotlib/gnuplot plots** — either accept the invert+hue-rotate approximation
  (cheap) or **dual-generate** just these few with a matplotlib dark style (option A, but
  only for the handful of colored plots, not all 130 images).
- **Photos/screenshots** — exclude from any filter; optionally add a small light matte/padding
  or thin border so their edges aren't jarring against the dark page.

This gets ~65 of the generated images (all the monochrome ones, including pervasive inline
math) fixed for near-zero effort, and confines the real work to the small set of colored
plots.

## Proposed steps (for the recommended hybrid — pending decision)

Nothing done yet — awaiting go-ahead + open questions.

1. **Decide the tagging mechanism** (open question 2): a `book-invertible` CSS class added
   to the generated-image directives, vs. a path-based selector excluding `screenshots/`
   and `cc*/`. (Class is robust; path-selector avoids editing directives.)
2. **Replace `custom.css`'s white-bg hack** with a dark-mode `filter: invert(1)
   hue-rotate(180deg)` rule scoped to the invertible set, keyed off furo's dark theme
   (`[data-theme="dark"]` and/or `@media (prefers-color-scheme: dark)`).
3. **Make texExpToPng output transparent** (so invert has no box to fight): confirm/So set
   inlinetex + the `_static/Makefile` `texExpToPng` calls emit a transparent background
   (the pinned texExpToPng supports `--bg Transparent`/`--fg`), then let CSS invert give
   white math on dark.
4. **Colored plots** (open question 3): either leave them to the invert approximation, or
   add `transparent=True` + a dark-styled second render and wire `only-light`/`only-dark`
   for just those.
5. **Verify** in a nested `make html`: open representative pages in both light and dark
   (toggle `data-theme`), check math legibility, plot colors, and that no screenshot got
   inverted.

## Open questions

1. **Effort appetite** — cheap-and-good-enough (hybrid D: invert everything monochrome,
   approximate the colored plots) or best-fidelity (dual-generate colored plots too)?
   Recommended: hybrid D; revisit dual-gen only if a specific plot looks wrong.
2. **Tagging** — add a `book-invertible` class to generated-image directives (robust, edits
   directives), or a path-based CSS selector excluding photos (no edits, path-fragile)?
   Recommended: path-based to start (zero directive churn), tighten later if needed.
3. **Colored matplotlib plots** — accept invert+hue-rotate, or dual-generate a dark
   matplotlib style for just those? Recommended: accept the approximation first; look at the
   result before investing in dual-gen.
4. **Photos** — leave as-is, or add a light matte/border so the white edge isn't harsh in
   dark mode? Recommended: small matte/border, no per-photo dark variants.

## Sources

- Furo images (`only-light`/`only-dark`): https://pradyunsg.me/furo/reference/images/
- Furo dark-mode discussion (different images per mode):
  https://github.com/pradyunsg/furo/discussions/131
- Furo colors / theming: https://pradyunsg.me/furo/customisation/colors/
