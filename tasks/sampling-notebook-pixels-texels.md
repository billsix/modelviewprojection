# Notebook: the image-sampling problem (virtual pixels & texels)

**Status:** blocked
**Priority:** 6
**Difficulty:** 3
**Started:** 2026-08-27 (William Emerison Six <billsix@gmail.com>)
**Blocked on:** maintainer answers the Open questions below (book location; PIL/numpy vs GL; relation to
existing texturing demos).
**Recheck:** the Open questions below are answered (maintainer-gated; `/recheck-blocked` surfaces it).

## Goal

Maintainer's idea, verbatim: *"Make a notebook example which shows the problem of sampling for images,
with virtual pixels, and virtual texels, have them at first be an image scaling, with one to one, then
have a scaling non-one to one. Then have a rotation, then have a rotation and a scaling."*

A notebook building up the image-sampling problem: 1:1 scaling → non-1:1 scaling → rotation → rotation +
scaling, with virtual pixels and texels.

## Context (investigation 2026-08-27)

- No existing task covers sampling/texel/mipmap; nothing archived on it.
- How to add a notebook (reference): `tasks/reference/book-figures-and-images.md §3` +
  `tasks/reference/notebook-sphinx-integration.md` — jupytext `py:percent` file in `notebooksrc/`, wired
  into `index.rst` toctree; the `.ipynb` is a gitignored build artifact. Existing notebooks:
  `notebooksrc/{framebuffer,ndc,plot2d}.py`. demo22/22a already teach texturing.

## Plan (draft — after questions)

- [ ] Add `src/modelviewprojection/notebooksrc/<sampling>.py`, building the 4 stages; wire into the
      toctree at the chapter neighborhood chosen in Q1.

## Open questions

1. **Where in the book / toctree** does it go (which chapter neighborhood)?
2. **Pure PIL/numpy** (like the framebuffer notebook) or **GL-textured**?
3. **Relationship to the existing texturing demos** (demo22a)?
