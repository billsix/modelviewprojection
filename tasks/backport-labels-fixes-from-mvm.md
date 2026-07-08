# Backport two `_labels.py` fixes from multivariate-math's port

**Status:** proposed — needs go-ahead
**Created:** 2026-07-08

## Context

multivariate-math ported `mathdemos/_labels.py` on 2026-07-08 and fixed two
latent bugs in it; mvp's original still has both. Small, surgical backports
to `src/modelviewprojection/mathdemos/_labels.py` (mvm's copy at
`multivariate-math/src/crossproduct/_labels.py` is the reference).

## The two fixes

1. **`Image.FLIP_TOP_BOTTOM` → `Image.Transpose.FLIP_TOP_BOTTOM`**
   (`_load_texture`). The module-level transpose constants were removed in
   Pillow 10, so on a current Pillow the first texture load raises
   `AttributeError` — i.e. the labels silently stop working the next time
   the image's Pillow moves forward. The `Image.Transpose` enum exists since
   Pillow 9.1.
2. **Save/restore the caller's VAO + array-buffer bindings** in
   `begin()`/`end()` instead of `glBindVertexArray(0)` in `end()`.
   In mvm this was a real crash (its renderer keeps ONE VAO bound for the
   program's lifetime; unbinding it made the next frame's first
   `glVertexAttribPointer` raise GL_INVALID_OPERATION). mvp's `_pipeline`
   binds a VAO per draw so it doesn't bite today — but the renderer
   clobbering global GL state it didn't own is wrong regardless, and any
   future caller with mvm-style persistent bindings would hit it.
   The fix: `begin()` stashes `GL_VERTEX_ARRAY_BINDING` and
   `GL_ARRAY_BUFFER_BINDING`; `end()` rebinds them.
   Also nice-to-have from the port: the `TEXEXP is None` guard in
   `_generate()` (ty cleanliness).

## Gate

`make image` (defaults) + Bill running the mathdemos crossproduct on a
display (labels still render, no GL errors across frames).
