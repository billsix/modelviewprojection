# Plan: ch13 fixes

**Status:** planned. **Type:** book asset/figure. **Effort:** trivial.
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
