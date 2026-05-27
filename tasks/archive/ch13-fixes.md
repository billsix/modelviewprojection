# Plan: ch13 fixes

**Status:** complete
**Completed:** 2026-05-27 — root cause was a *shared* Graphviz Cayley diagram: ch12 & ch13 both rendered `_static/demo11.png` (generated from `demo11.dot`). Fix (per Bill's "each demo gets its own copy"): created `demo12.dot`/`demo13.dot` as identical copies of `demo11.dot`, added `demo12.png`/`demo13.png` to `_static/Makefile`'s `graphs:` target, and repointed `ch12:66`→`demo12.png`, `ch13:63`→`demo13.png`. Each chapter now has an independently-editable `.dot` source. (PNGs regenerate in Bill's build — `texExpToPng`/`dot` not in this container.)
**Type:** book asset/figure.
**Source:** ch13–15 drift audit (verified).

## Finding + change (`book/docs/ch13.rst`)
- **Line 63 — wrong figure.** `.. figure:: _static/demo11.png` with `:alt: Demo
  13` (and a Demo-13 caption). The chapter shows the **demo11** screenshot. Either
  the path should point at a `demo13.png` (which does not currently exist in
  `_static/`) or the figure is genuinely meant to be demo11's and the alt/caption
  are wrong. **Confirm with Bill** which: if a demo13 screenshot is intended,
  it needs to be generated (a display-capture step Bill does); if reusing
  demo11's image is intentional, fix the alt/caption to say so.

## Verification
- `ls book/docs/_static/demo13.png` (currently missing).
- Bill confirms intended image via `make html` preview.
</content>
