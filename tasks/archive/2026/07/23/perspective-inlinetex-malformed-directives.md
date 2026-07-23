# Two malformed `.. inlinetex::` directives in `perspective.rst` (content leaks past the math)

**Status:** complete
**Completed:** 2026-07-23 (both directives fixed in `book/docs/perspective.rst`; verified — 0
`inlinetex` failures, book down to 1 warning). **No math changed** — purely structural (merge/indent).

## Outcome (what shipped)

- **#1 (`perspective.rst:143`)**: merged the split `\[ LHS \]  = RHS` into one display expression
  `\[ (\vec f_3;nearZ_c)([…]) = \begin{bmatrix}…\end{bmatrix} * \begin{bmatrix}…\end{bmatrix} \]`
  (the premature `\]` + 2-space `= \begin{bmatrix}` are gone; all content is now ≥ 4-space indented so
  the options parse). Matrix values/operators untouched; render pixel-checked — the equation is intact.
- **#2 (`perspective.rst:602`)**: de-indented the trailing `..` derivation-notes/GLSL comment from
  5 spaces to **column 0**, so it's a top-level RST comment *outside* the inlinetex directive (the
  directive body now ends at `\end{align*}`). The comment content (still indented) is unchanged/hidden.
- **Verified:** clean book build → `texExpToPng failed` count **2 → 0**; "build succeeded, 1 warning"
  (the remaining one is demo01, tracked separately).

The change is uncommitted (Bill commits). Original diagnosis below.

Created 2026-07-22; recreated 2026-07-23 (the original was an untracked doc lost to a `git clean -fdx`
during book-build verification — recreated from the diagnosis). Found while verifying the book renders
after the texExpToPng `varwidth`+`xcolor` fixes: those cleared **25 of 27** `inlinetex` failures;
these **2** remain and are **book-authoring bugs**, not a texExpToPng issue.

## Symptom

A clean `make html` (image pinned at texExpToPng `67da442`) reports exactly two
`inlinetex: texExpToPng failed (exit 1)` errors, both in `book/docs/perspective.rst`. Their captured
`latex=` isn't just the intended expression — it includes the directive's `:class:`/`:align:` option
lines and/or a trailing `.. // …` comment block, which is invalid LaTeX.

## Root cause — RST directive-content indentation

A `.. inlinetex::` body is every line indented relative to the `..` marker (col 0); docutils dedents
the body by its **minimum** indent. If part of the expression is *under*-indented, or a following
block is *still indented* (so it's swallowed as body), the options / trailing prose land in the LaTeX
handed to texExpToPng → it fails.

### #1 — `perspective.rst:143` (two problems)

```
.. inlinetex::
    :class: no-scale             <- options + expr at 4 spaces
    ...
    \[
    (\vec{f}_{3} ; nearZ_c) ( \begin{bmatrix} ... \end{bmatrix})
    \]

  = \begin{bmatrix}              <- continuation at only 2 spaces
        ...
                   \end{bmatrix}
```
- **Indent:** the `  = \begin{bmatrix} …` continuation is at **2 spaces** while the rest is at **4**.
  Min-indent becomes 2, so the `:class:`/`:align:`/`:figclass:` options (at 4) dedent to 2 and stop
  being parsed as options — they become part of the LaTeX body.
- **LaTeX:** even fixed up, `\[ … \]  = \begin{bmatrix}` is malformed — the `= [matrix]` sits in
  **text mode** after the display-math `\]` closes. The whole equation
  (`(f₃;nearZ)([…]) = [matrix] * […]`) needs to be **one** math expression.
- **Fix:** consolidate into a single, consistently-4-space-indented expression — one
  `\[ (\vec f_3; nearZ_c)([…]) = \begin{bmatrix} … \end{bmatrix} * \begin{bmatrix} … \end{bmatrix} \]`
  (or an `align*`). Bill's call on the exact layout.

### #2 — `perspective.rst:602` (trailing comment swallowed)

```
.. inlinetex::
    :class: no-scale
    ...
    \begin{align*}
    ...
    \end{align*}

     ..                          <- RST comment, indented 5 spaces
        //  clipSpace.z = A* c.z + B * 1.0 …   <- 8-space GLSL/derivation notes
        ...
        mat4 camera_space_to_clip_space = transpose(mat4( …
```
- The `..` comment block (derivation notes + GLSL) is indented **5/8 spaces**, i.e. still *inside*
  the inlinetex body — so texExpToPng receives `\begin{align*}…\end{align*}\n\n ..\n    //…\n    mat4 …`
  → invalid LaTeX.
- The `align*` itself renders fine (verified); the **only** problem is the swallowed comment.
- **Fix:** de-indent the `.. // …` notes block to **column 0** (a top-level RST comment, outside the
  directive) so the inlinetex body is just the `align*`.

## Verify

After each fix: clean `make html`; the two `perspective.rst` `inlinetex` errors are gone and the
intended math renders. No new warnings.

## Not in scope

- The texExpToPng preamble fixes (`standalone[varwidth]` + `xcolor`) are **done**, pushed as
  `67da442`, and pinned in the Dockerfile — they render all *valid* display/colored math
  (pixel-verified). See `github.com/billsix/texExpToPng` `tasks/archive/2026/07/22/support-display-math.md`.
- The demo01 empty doc-region warning → `tasks/demo01-import-region-empty.md`.
- The `--system` editable-install bug (clean builds skip SVG regen) → `tasks/archive/2026/07/23/fix-editable-install-system-flag.md`.

## Relationships

- Sibling book-render findings: `tasks/demo01-import-region-empty.md`,
  `tasks/archive/2026/07/23/fix-editable-install-system-flag.md`.
- Context: the gacalc-0.0.13 bump whose book-render check surfaced all of this
  (`tasks/archive/2026/07/22/dual-coefficient-cleanup.md`).
