# Add `amsmath` to texExpToPng's preamble (inlinetex bmatrix/align math fails)

**Status:** proposed — needs go-ahead. Created 2026-07-22. Found while confirming the book renders
after the gacalc-0.0.13 bump. **Pre-existing**, unrelated to gacalc/find_normal.

## Symptom

`make html` emits ~9 (count varies with the inlinetex PNG cache; up to ~27 on a fully cold cache):

```
ERROR: inlinetex: texExpToPng failed (exit 1). latex='\[ ... \begin{bmatrix} ... \]'. stderr='latex command failed'
```

The failing expressions are the matrix/aligned math in **ch04 / ch06 / (rotation) ch14** — anything
using `\begin{bmatrix}`, `\begin{align*}`, or `\text{}`. Simple inline math (`$x^2$`) renders fine.
These `\[...\]` blocks silently fall back to nothing in the built HTML.

## Root cause (verified in the container)

`texExpToPng`'s hardcoded LaTeX preamble **lacks `\usepackage{amsmath}`**. Proof:

- `texExpToPng --exp "$x^2$" ...` → `PNG successfully created` (rc=0).
- Manual `latex` on a standalone doc **without** amsmath → `! LaTeX Error: Environment bmatrix
  undefined.` (rc=1). **With** `\usepackage{amsmath}` → rc=0, including a real failing book
  expression (`bmatrix` + `\vec` + `\text`).

`texExpToPng` is a **compiled binary** (built in the Dockerfile's `BUILD_DOCS` block from a SHA-pinned
clone of `github.com/billsix/tex-expression-to-png`, currently `fbbd9a3f…`). Its options are only
`--exp/--file/--size/--output/--bg/--fg` — **no `--package`/`--preamble` hook**. The `inlinetex`
Sphinx extension (`book/docs/_ext/inlinetex.py`) just calls `texExpToPng --file <expr>`; it passes the
expression into the document *body*, so it cannot inject a `\usepackage` into the preamble. **So this
must be fixed in texExpToPng itself, not in mvp.**

## Fix

1. In **`github.com/billsix/tex-expression-to-png`**, add `\usepackage{amsmath}` (and `amssymb` for
   good measure) to the LaTeX preamble the tool emits, and push the GitHub mirror.
2. Bump the SHA-pin in mvp's **`Dockerfile`** (`BUILD_DOCS` block: `git checkout fbbd9a3f…`) to the
   new commit, and rebuild the image. (Same SHA-pinned scheme `multivariate-math` uses; see the
   `CLAUDE.md` "texExpToPng is built from a SHA-pinned git clone" note.)
3. Confirm the tool still carries the `--bg/--fg` dvipng flags mvp relies on (the reason the current
   SHA was pinned).

**Alternative if upstream can't change:** rework `inlinetex.py` to build its own full LaTeX document
(with an amsmath preamble) → `latex`/`dvipng` directly, bypassing `texExpToPng` for multi-line math.
Bigger change; only if the upstream preamble fix is blocked.

## Verify

Rebuild the image with the bumped SHA; clean `make html`; no `inlinetex: texExpToPng failed` errors,
and the ch04/ch06/ch14 matrix/aligned math renders as PNGs.

## Relationships

- Sibling findings: `tasks/fix-editable-install-system-flag.md`,
  `tasks/demo01-import-region-empty.md`.
- Context: `tasks/archive/2026/07/22/dual-coefficient-cleanup.md`.
